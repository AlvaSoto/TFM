"""
Feature engineering compartido entre entrenamiento e inferencia.

IMPORTANTE: esta es la ÚNICA implementación de las features. El detector de
producción (app/services/detector.py) y el pipeline de entrenamiento
(app/ml/train_clean.py) importan de aquí. Cualquier cambio en las features
requiere reentrenar el modelo: no modificar sin regenerar los artefactos.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

# Ventanas deslizantes en pasos de 15 min (1h, 2h, 3h, 6h, 12h, 24h)
ROLLING_WINDOWS = [4, 8, 12, 24, 48, 96]
# Lags: ayer y hace una semana
LAGS = [96, 96 * 7]

SEQUENCE_LENGTH = 96  # 24h en intervalos de 15 min


def engineer_features(data: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Transforma lecturas crudas (timestamp, household_id, consumption_l[, is_leak])
    en el dataset de trabajo del modelo.

    Devuelve (df_procesado, lista_de_columnas_de_features).
    Todas las features son computables online (solo miran al pasado), por lo
    que son seguras tanto en entrenamiento como en inferencia.
    """
    df = data.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["household_id", "timestamp"]).reset_index(drop=True)

    # Estacionalidad cíclica
    for col, period in [("hour", 24), ("dayofweek", 7)]:
        df[f"{col}_sin"] = np.sin(2 * np.pi * getattr(df["timestamp"].dt, col) / period)
        df[f"{col}_cos"] = np.cos(2 * np.pi * getattr(df["timestamp"].dt, col) / period)

    df["is_weekend"] = (df["timestamp"].dt.dayofweek >= 5).astype(int)
    # is_night: periodo donde suele haber fugas silenciosas (00:00 - 05:00)
    df["is_night"] = df["timestamp"].dt.hour.between(0, 5, inclusive="both").astype(int)

    grouped = df.groupby("household_id", sort=False)["consumption_l"]

    # Ventanas deslizantes (tendencia y variabilidad)
    for window in ROLLING_WINDOWS:
        rolling = grouped.rolling(window=window, min_periods=1)
        rmean = rolling.mean().reset_index(level=0, drop=True)
        rstd = rolling.std().reset_index(level=0, drop=True)

        df[f"rolling_mean_{window}"] = rmean
        df[f"rolling_std_{window}"] = rstd
        df[f"rolling_cv_{window}"] = rstd / (rmean + 1e-6)
        df[f"diff_from_rolling_mean_{window}"] = df["consumption_l"] - rmean

    df.fillna(0, inplace=True)

    # Lags (comparación con ayer y la semana pasada)
    for lag in LAGS:
        df[f"consumption_lag_{lag}"] = grouped.shift(lag).fillna(0)

    feature_cols = [c for c in df.columns if c not in ["timestamp", "is_leak", "household_id"]]
    return df, feature_cols


def create_sequences(
    df: pd.DataFrame,
    feature_cols: List[str],
    seq_length: int = SEQUENCE_LENGTH,
    stride: int = 2,
) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
    """
    Convierte el dataframe procesado en secuencias (N, seq_length, n_features)
    respetando los límites de cada hogar (una secuencia nunca mezcla dos hogares).

    labels[i] = 1 si algún punto de la ventana i tiene is_leak=1 (si la columna existe).
    metadata[i] contiene household_id y end_timestamp de la ventana, para poder
    mapear cada secuencia de vuelta a fechas y hogares.
    """
    sequences, labels, metadata = [], [], []
    has_labels = "is_leak" in df.columns

    for household_id, group in df.groupby("household_id"):
        group = group.sort_values("timestamp")
        values = group[feature_cols].values
        leak_flags = group["is_leak"].values if has_labels else np.zeros(len(group))
        timestamps = group["timestamp"].values

        if len(group) < seq_length:
            continue

        num_seq = (len(group) - seq_length) // stride + 1
        starts = np.arange(num_seq) * stride
        for s in starts:
            e = s + seq_length
            sequences.append(values[s:e])
            labels.append(int(np.max(leak_flags[s:e])))
            metadata.append({"household_id": household_id, "end_timestamp": timestamps[e - 1]})

    if not sequences:
        return np.empty((0, seq_length, len(feature_cols))), np.array([], dtype=int), []

    return np.stack(sequences), np.array(labels, dtype=int), metadata
