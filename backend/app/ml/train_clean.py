"""
Pipeline de entrenamiento LIMPIO del LSTM Autoencoder.

Corrige los dos problemas metodológicos del notebook LTSM_AUTOENCODER_NEW.ipynb
que inflaban las métricas:

  1. FUGA DE DATOS EN EL SCALER: el notebook hacía scaler.fit_transform() sobre
     TODO el dataset (incluido el test y las fugas) antes del split. Aquí el
     scaler se ajusta EXCLUSIVAMENTE con las filas normales (is_leak=0) de los
     hogares de entrenamiento.

  2. SPLIT POR HOGAR: el notebook hacía split temporal con los mismos 160
     hogares en train y test, así que nunca se evaluaba la generalización a un
     hogar desconocido (el escenario real de producción). Aquí el split separa
     hogares completos: el modelo se evalúa sobre hogares que jamás ha visto.

Genera los mismos artefactos que consume el backend (best_model.keras,
scaler.joblib) más threshold.json con el umbral y las métricas honestas.

Uso:
  # Prueba rápida local (subconjunto de hogares, pocas épocas):
  python -m app.ml.train_clean --households 24 --epochs 5

  # Entrenamiento completo (en la VM con GPU):
  python -m app.ml.train_clean

Ejecutar desde backend/ con el entorno conda TFM activado.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

from app.ml.features import SEQUENCE_LENGTH, create_sequences, engineer_features


@dataclass
class CleanConfig:
    data_path: Path = Path(__file__).resolve().parents[2] / "data" / "mixed_population_dataset_160_households.csv"
    output_dir: Path = Path.home() / "TFM_Project_Runs" / "Run_Clean"

    sequence_length: int = SEQUENCE_LENGTH
    sequence_stride: int = 2

    # Split POR HOGAR (no temporal): fracción de hogares reservada para test
    test_household_fraction: float = 0.25
    validation_split: float = 0.15  # cola de las secuencias normales de train
    split_seed: int = 42

    latent_dim: int = 64
    lstm_units: tuple = (256, 128, 64)

    batch_size: int = 256
    max_epochs: int = 150
    patience: int = 15
    threshold_percentile: float = 96.0

    # Para pruebas rápidas: limitar nº de hogares (None = todos)
    max_households: int | None = None


def split_households(household_ids: list, cfg: CleanConfig) -> tuple[list, list]:
    """Split determinista de hogares completos en train/test."""
    rng = np.random.RandomState(cfg.split_seed)
    ids = sorted(household_ids)
    rng.shuffle(ids)
    n_test = max(1, int(len(ids) * cfg.test_household_fraction))
    return ids[n_test:], ids[:n_test]  # (train, test)


def build_lstm_autoencoder(input_shape, latent_dim, lstm_units):
    # Arquitectura idéntica a la del notebook para que las métricas sean comparables
    from tensorflow.keras import layers, models, optimizers

    inputs = layers.Input(shape=input_shape)
    x = inputs
    for units in lstm_units:
        x = layers.LSTM(units, return_sequences=True)(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
    x = layers.LSTM(lstm_units[-1] // 2, return_sequences=False)(x)
    x = layers.BatchNormalization()(x)
    latent = layers.Dense(latent_dim, activation="relu", name="bottleneck")(x)
    x = layers.RepeatVector(input_shape[0])(latent)
    for units in reversed(lstm_units):
        x = layers.LSTM(units, return_sequences=True)(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
    outputs = layers.TimeDistributed(layers.Dense(input_shape[1]))(x)

    model = models.Model(inputs, outputs, name="lstm_autoencoder")
    model.compile(optimizer=optimizers.Adam(1e-4), loss="mse")
    return model


def compute_reconstruction_errors(model, X, batch_size=512):
    recon = model.predict(X, batch_size=batch_size, verbose=0)
    return np.mean(np.square(X - recon), axis=(1, 2))


def main():
    import tensorflow as tf
    from tensorflow.keras import callbacks, models

    parser = argparse.ArgumentParser(description="Entrenamiento limpio del LSTM Autoencoder")
    parser.add_argument("--data", type=Path, default=None, help="Ruta al CSV del dataset")
    parser.add_argument("--output", type=Path, default=None, help="Directorio de salida")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--households", type=int, default=None, help="Limitar nº de hogares (pruebas)")
    parser.add_argument("--stride", type=int, default=None,
                        help="Stride de secuencias en entrenamiento (4 recomendado en GPUs gratuitas: mitad de datos y RAM)")
    parser.add_argument("--units", type=str, default=None,
                        help="Capas LSTM separadas por comas, p.ej. '128,64' (por defecto 256,128,64)")
    args = parser.parse_args()

    cfg = CleanConfig()
    if args.data:
        cfg.data_path = args.data
    if args.output:
        cfg.output_dir = args.output
    if args.epochs:
        cfg.max_epochs = args.epochs
    if args.households:
        cfg.max_households = args.households
    if args.stride:
        cfg.sequence_stride = args.stride
    if args.units:
        cfg.lstm_units = tuple(int(u) for u in args.units.split(","))

    tf.random.set_seed(42)
    np.random.seed(42)

    checkpoint_dir = cfg.output_dir / "checkpoints"
    results_dir = cfg.output_dir / "results"
    for p in (checkpoint_dir, results_dir):
        p.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Carga y split POR HOGAR (antes de tocar features ni scaler)
    # ------------------------------------------------------------------
    print(f"Leyendo dataset: {cfg.data_path}")
    df = pd.read_csv(cfg.data_path)

    all_ids = df["household_id"].unique().tolist()
    if cfg.max_households:
        rng = np.random.RandomState(cfg.split_seed)
        all_ids = sorted(all_ids)
        rng.shuffle(all_ids)
        all_ids = all_ids[: cfg.max_households]
        df = df[df["household_id"].isin(all_ids)]

    train_ids, test_ids = split_households(all_ids, cfg)
    print(f"Hogares: {len(train_ids)} train / {len(test_ids)} test (nunca vistos por el modelo)")

    # ------------------------------------------------------------------
    # 2. Feature engineering (idéntico en train/serve: app/ml/features.py)
    # ------------------------------------------------------------------
    df, feature_cols = engineer_features(df)

    df_train = df[df["household_id"].isin(train_ids)]
    df_test = df[df["household_id"].isin(test_ids)]

    # ------------------------------------------------------------------
    # 3. Scaler SIN FUGA: fit solo con filas normales de hogares de train
    # ------------------------------------------------------------------
    scaler = StandardScaler()
    scaler.fit(df_train.loc[df_train["is_leak"] == 0, feature_cols])

    df_train = df_train.copy()
    df_test = df_test.copy()
    df_train[feature_cols] = scaler.transform(df_train[feature_cols]).astype(np.float32)
    df_test[feature_cols] = scaler.transform(df_test[feature_cols]).astype(np.float32)

    scaler_path = results_dir / "scaler.joblib"
    joblib.dump(scaler, scaler_path)
    print(f"Scaler guardado (fit solo con train-normal): {scaler_path}")

    # ------------------------------------------------------------------
    # 4. Secuencias
    # ------------------------------------------------------------------
    X_train_all, y_train_all, _ = create_sequences(df_train, feature_cols, cfg.sequence_length, cfg.sequence_stride)
    X_test, y_test, test_meta = create_sequences(df_test, feature_cols, cfg.sequence_length, cfg.sequence_stride)

    # El autoencoder solo aprende de secuencias 100% normales
    X_train_normal = X_train_all[y_train_all == 0]
    val_size = int(len(X_train_normal) * cfg.validation_split)
    X_val = X_train_normal[-val_size:]
    X_train = X_train_normal[:-val_size]

    print(f"Secuencias — train(normal): {len(X_train):,} | val(normal): {len(X_val):,} | "
          f"test(mixto): {len(X_test):,} (fugas en test: {int(y_test.sum()):,})")

    # ------------------------------------------------------------------
    # 5. Entrenamiento
    # ------------------------------------------------------------------
    model = build_lstm_autoencoder((cfg.sequence_length, len(feature_cols)), cfg.latent_dim, list(cfg.lstm_units))

    cbs = [
        callbacks.ModelCheckpoint(filepath=checkpoint_dir / "best_model.keras",
                                  monitor="val_loss", save_best_only=True, verbose=1),
        callbacks.CSVLogger(cfg.output_dir / "training_log.csv", append=True),
        callbacks.EarlyStopping(monitor="val_loss", patience=cfg.patience, restore_best_weights=True),
        callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, verbose=1),
        callbacks.BackupAndRestore(backup_dir=str(cfg.output_dir / "backup_state")),
    ]

    model.fit(
        X_train, X_train,
        validation_data=(X_val, X_val),
        epochs=cfg.max_epochs,
        batch_size=cfg.batch_size,
        callbacks=cbs,
        shuffle=True,
        verbose=2,
    )

    # ------------------------------------------------------------------
    # 6. Umbral (validación normal) y evaluación honesta (hogares no vistos)
    # ------------------------------------------------------------------
    best_model = models.load_model(checkpoint_dir / "best_model.keras")

    val_errors = compute_reconstruction_errors(best_model, X_val)
    threshold = float(np.percentile(val_errors, cfg.threshold_percentile))
    print(f"Umbral (p{cfg.threshold_percentile} de validación normal): {threshold:.6f}")

    test_errors = compute_reconstruction_errors(best_model, X_test)
    y_pred = (test_errors >= threshold).astype(int)

    prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="binary", zero_division=0)
    metrics = {
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "roc_auc": float(roc_auc_score(y_test, test_errors)) if len(set(y_test)) > 1 else None,
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "classification_report": classification_report(y_test, y_pred, output_dict=True, zero_division=0),
    }

    # ------------------------------------------------------------------
    # 7. Artefactos: el umbral viaja SIEMPRE junto al modelo
    # ------------------------------------------------------------------
    threshold_artifact = {
        "threshold": threshold,
        "threshold_percentile": cfg.threshold_percentile,
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "data_path": str(cfg.data_path),
        "train_households": sorted(train_ids),
        "test_households": sorted(test_ids),
        "methodology": "household-split, scaler fit on train-normal only (no leakage)",
        "metrics_on_unseen_households": metrics,
    }
    (results_dir / "threshold.json").write_text(json.dumps(threshold_artifact, indent=2))

    print("=" * 60)
    print("MÉTRICAS HONESTAS (hogares nunca vistos por el modelo):")
    print(f"   ROC-AUC:   {metrics['roc_auc']}")
    print(f"   Recall:    {metrics['recall']:.3f}")
    print(f"   Precision: {metrics['precision']:.3f}")
    print(f"   F1:        {metrics['f1']:.3f}")
    print(f"Artefactos en: {cfg.output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
