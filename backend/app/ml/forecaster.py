"""
Forecaster probabilístico de consumo para contadores agregados (Fase B).

LightGBM con regresión cuantílica (P05/P50/P95): predice el rango de consumo
esperado de cada intervalo de 15 min condicionado a calendario, covariables
(ocupación, temperatura) e historia ROBUSTA del propio contador.

Decisión de diseño clave — historia robusta, no lags crudos: como features de
historial se usan MEDIANAS del mismo intervalo horario en los últimos 14 días
(y de totales diarios en 7 días), no el valor de ayer. Una mediana resiste
varios días de fuga sin inflar la predicción — si usáramos lag-96, al segundo
día de fuga el modelo "aprendería" la fuga como normal y el residuo
desaparecería.

Entrenamiento (split POR CONTADOR, solo filas normales de contadores train):
    python -m app.ml.forecaster

Artefactos → app/ml/forecaster_artifacts/ (boosters + forecaster_config.json
con los contadores de test y los parámetros CUSUM ajustados en train).
"""
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "aggregated_meters_dataset.csv"
COV_PATH = BASE_DIR / "data" / "aggregated_meters_covariates.csv"
ARTIFACTS_DIR = Path(__file__).resolve().parent / "forecaster_artifacts"

STEPS_PER_DAY = 96
QUANTILES = (0.05, 0.50, 0.95)
TEST_METER_FRACTION = 0.25
SPLIT_SEED = 42

FEATURE_COLS = [
    "hour_sin", "hour_cos", "dow_sin", "dow_cos", "is_weekend",
    "meter_type_code", "units", "occupancy", "temp_c",
    "slot_median_14d", "slot_iqr_14d", "day_total_median_7d_step",
]


def split_meters(meter_ids: list) -> tuple:
    rng = np.random.RandomState(SPLIT_SEED)
    ids = sorted(meter_ids)
    rng.shuffle(ids)
    n_test = max(1, int(len(ids) * TEST_METER_FRACTION))
    return ids[n_test:], ids[:n_test]  # (train, test)


def build_meter_features(g: pd.DataFrame, cov_g: pd.DataFrame) -> pd.DataFrame:
    """
    Features para UN contador. g: timestamp, consumption_l, is_leak (15 min,
    continuo). cov_g: covariables diarias de ese contador.
    """
    g = g.sort_values("timestamp").reset_index(drop=True)
    n_days = len(g) // STEPS_PER_DAY
    assert n_days * STEPS_PER_DAY == len(g), "serie no alineada a días completos"

    ts = pd.to_datetime(g["timestamp"])
    out = pd.DataFrame({
        "timestamp": ts,
        "y": g["consumption_l"].values,
        "is_leak": g["is_leak"].values if "is_leak" in g else 0,
        "date": ts.dt.strftime("%Y-%m-%d"),
    })
    out["hour_sin"] = np.sin(2 * np.pi * ts.dt.hour / 24)
    out["hour_cos"] = np.cos(2 * np.pi * ts.dt.hour / 24)
    out["dow_sin"] = np.sin(2 * np.pi * ts.dt.dayofweek / 7)
    out["dow_cos"] = np.cos(2 * np.pi * ts.dt.dayofweek / 7)
    out["is_weekend"] = (ts.dt.dayofweek >= 5).astype(int)

    # --- Historia robusta: matriz (días x 96) y medianas móviles desplazadas 1 día ---
    y_mat = out["y"].values.reshape(n_days, STEPS_PER_DAY)
    ym = pd.DataFrame(y_mat)
    slot_median = ym.rolling(28, min_periods=7).median().shift(1).values
    slot_q75 = ym.rolling(28, min_periods=7).quantile(0.75).shift(1).values
    slot_q25 = ym.rolling(28, min_periods=7).quantile(0.25).shift(1).values
    out["slot_median_14d"] = slot_median.ravel()
    out["slot_iqr_14d"] = (slot_q75 - slot_q25).ravel()

    day_tot = pd.Series(y_mat.sum(axis=1))
    day_med7 = day_tot.rolling(14, min_periods=5).median().shift(1)
    out["day_total_median_7d_step"] = np.repeat(day_med7.values / STEPS_PER_DAY, STEPS_PER_DAY)

    # --- Covariables diarias ---
    cov_g = cov_g.set_index("date")
    out["occupancy"] = out["date"].map(cov_g["occupancy"]).astype(float)
    out["temp_c"] = out["date"].map(cov_g["temp_c"]).astype(float)
    out["units"] = float(cov_g["units"].iloc[0])
    out["meter_type_code"] = 0 if cov_g["meter_type"].iloc[0] == "hotel" else 1

    return out


def load_and_featurize() -> tuple:
    """Carga dataset+covariables y construye features por contador."""
    df = pd.read_csv(DATA_PATH)
    cov = pd.read_csv(COV_PATH)
    frames = {}
    for meter_id, g in df.groupby("household_id"):
        frames[meter_id] = build_meter_features(g, cov[cov["household_id"] == meter_id])
    return frames


def train_quantile_models(train_frames: dict) -> dict:
    """Entrena un booster por cuantil sobre filas normales con historia disponible."""
    full = pd.concat(train_frames.values(), ignore_index=True)
    mask = (full["is_leak"] == 0) & full["slot_median_14d"].notna()
    X = full.loc[mask, FEATURE_COLS]
    y = full.loc[mask, "y"]
    print(f"Entrenando con {len(X):,} filas normales de {len(train_frames)} contadores")

    boosters = {}
    for q in QUANTILES:
        model = lgb.LGBMRegressor(
            objective="quantile", alpha=q,
            n_estimators=400, learning_rate=0.05, num_leaves=63,
            min_child_samples=50, subsample=0.9, colsample_bytree=0.9,
            random_state=42, verbose=-1,
        )
        model.fit(X, y)
        boosters[q] = model
        print(f"  cuantil {q} entrenado")
    return boosters


def predict_quantiles(boosters: dict, feats: pd.DataFrame) -> pd.DataFrame:
    """Predice cuantiles y descarta el warm-up (días sin historia robusta)."""
    feats = feats[feats["slot_median_14d"].notna()].reset_index(drop=True)
    X = feats[FEATURE_COLS]
    out = feats[["timestamp", "date", "y", "is_leak"]].copy()
    for q, m in boosters.items():
        out[f"p{int(q * 100):02d}"] = np.asarray(m.predict(X))
    return out


# ----------------------------------------------------------------------
# CUSUM sobre residuos normalizados
# ----------------------------------------------------------------------
def cusum_days(pred: pd.DataFrame, k: float, h: float, cap_factor: float = 3.0) -> set:
    """
    Días marcados por CUSUM positivo sobre el residuo normalizado
    r = (y - P50) / max(spread, eps), con techo para acotar la cola post-fuga.
    """
    r = (pred["y"] - pred["p50"]) / np.maximum(pred["p95"] - pred["p50"], 1e-3)
    r = r.fillna(0.0)
    # Corrección de sesgo POR CONTADOR: cada contador tiene un nivel base propio
    # que el modelo global no observa (p.ej. L/habitación-noche); sin esto, el
    # CUSUM acumula el sesgo constante como si fuera una fuga. La mediana móvil
    # de 14 días de residuos pasados absorbe el sesgo pero no un escalón reciente.
    bias = r.rolling(14 * 96, min_periods=3 * 96).median().shift(1).fillna(0.0)
    r = (r - bias).values

    s = 0.0
    cap = cap_factor * h
    flagged = np.zeros(len(r), dtype=bool)
    for i, ri in enumerate(r):
        s = min(cap, max(0.0, s + ri - k))
        flagged[i] = s > h
    return set(pred.loc[flagged, "date"])


def tune_cusum(train_preds: dict, truth_days: dict) -> dict:
    """Grid-search de (k, h) maximizando F1 diario sobre los contadores de TRAIN."""
    best = {"k": 0.25, "h": 8.0, "f1": -1}
    for k in (0.15, 0.25, 0.4, 0.6, 0.9):
        for h in (4.0, 8.0, 16.0, 32.0, 48.0):
            tp = fp = fn = 0
            for mid, pred in train_preds.items():
                days = cusum_days(pred, k, h)
                truth = truth_days[mid]
                tp += len(days & truth)
                fp += len(days - truth)
                fn += len(truth - days)
            p = tp / (tp + fp) if tp + fp else 0
            r = tp / (tp + fn) if tp + fn else 0
            f1 = 2 * p * r / (p + r) if p + r else 0
            if f1 > best["f1"]:
                best = {"k": k, "h": h, "f1": round(f1, 3),
                        "precision": round(p, 3), "recall": round(r, 3)}
    return best


def main():
    ARTIFACTS_DIR.mkdir(exist_ok=True)

    print("Construyendo features por contador...")
    frames = load_and_featurize()
    train_ids, test_ids = split_meters(list(frames.keys()))
    print(f"Contadores: {len(train_ids)} train / {len(test_ids)} test")

    boosters = train_quantile_models({m: frames[m] for m in train_ids})

    # Ajuste de CUSUM en train (el test queda intacto)
    print("Ajustando CUSUM en contadores de train...")
    train_preds, truth_days = {}, {}
    for mid in train_ids:
        train_preds[mid] = predict_quantiles(boosters, frames[mid])
        truth_days[mid] = set(frames[mid].loc[frames[mid]["is_leak"] == 1, "date"])
    best = tune_cusum(train_preds, truth_days)
    print(f"CUSUM óptimo en train: k={best['k']} h={best['h']} "
          f"(F1 diario train: {best['f1']})")

    for q, m in boosters.items():
        m.booster_.save_model(str(ARTIFACTS_DIR / f"q{int(q * 100):02d}.txt"))
    (ARTIFACTS_DIR / "forecaster_config.json").write_text(json.dumps({
        "feature_cols": FEATURE_COLS,
        "quantiles": list(QUANTILES),
        "train_meters": sorted(train_ids),
        "test_meters": sorted(test_ids),
        "cusum": best,
        "data_path": str(DATA_PATH.name),
    }, indent=2))
    print(f"Artefactos guardados en {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
