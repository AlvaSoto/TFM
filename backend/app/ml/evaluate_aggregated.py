"""
Evaluación Fase C: detectores para CONTADORES AGREGADOS (hoteles, pueblos/DMA)
sobre los contadores de TEST (nunca vistos por el forecaster), a nivel de día.

Compara:
  - Forecast+CUSUM : LightGBM cuantílico + CUSUM sobre residuos normalizados
  - MNF-trending   : mínimo nocturno vs su línea base móvil (mediana 14 noches)
  - AND / OR       : combinaciones

Nota: el LSTM-AE de hogares no se incluye — fue entrenado y escalado con la
distribución de hogares individuales (L/15min de una vivienda); aplicarlo a
contadores 100x mayores satura el scaler y no es una comparación informativa.

Uso (desde backend/): python -m app.ml.evaluate_aggregated
"""
import json
from pathlib import Path

import pandas as pd

from app.ml.forecaster import (
    ARTIFACTS_DIR, COV_PATH, DATA_PATH, build_meter_features,
    cusum_days, predict_quantiles,
)
from app.services.night_flow import mnf_trending

BASE_DIR = Path(__file__).resolve().parents[2]


def load_boosters():
    import lightgbm as lgb
    cfg = json.loads((ARTIFACTS_DIR / "forecaster_config.json").read_text())
    boosters = {}
    for q in cfg["quantiles"]:
        booster = lgb.Booster(model_file=str(ARTIFACTS_DIR / f"q{int(q * 100):02d}.txt"))
        boosters[q] = booster
    return boosters, cfg


class _BoosterAdapter:
    """lgb.Booster no tiene .predict con la misma firma que LGBMRegressor: adapta."""
    def __init__(self, booster):
        self._b = booster

    def predict(self, X):
        return self._b.predict(X)


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3),
            "tp": tp, "fp": fp, "fn": fn}


def main():
    boosters_raw, cfg = load_boosters()
    boosters = {q: _BoosterAdapter(b) for q, b in boosters_raw.items()}
    k, h = cfg["cusum"]["k"], cfg["cusum"]["h"]
    test_ids = cfg["test_meters"]

    df = pd.read_csv(DATA_PATH)
    cov = pd.read_csv(COV_PATH)

    detectors = ("Forecast+CUSUM", "MNF-trending", "AND (ambos)", "OR (cobertura)")
    totals = {seg: {d: [0, 0, 0] for d in detectors} for seg in ("hotel", "pueblo", "TOTAL")}
    meter_rows = []

    for mid in test_ids:
        g = df[df["household_id"] == mid]
        cov_g = cov[cov["household_id"] == mid]
        segment = cov_g["meter_type"].iloc[0]

        feats = build_meter_features(g, cov_g)
        pred = predict_quantiles(boosters, feats)
        eval_dates = set(pred["date"])  # sin el warm-up de historia

        fc_days = cusum_days(pred, k, h) & eval_dates
        mnf = mnf_trending(g)
        mnf_days = set(mnf["mnf_days"]) & eval_dates
        truth = set(feats.loc[feats["is_leak"] == 1, "date"]) & eval_dates

        preds = {
            "Forecast+CUSUM": fc_days,
            "MNF-trending": mnf_days,
            "AND (ambos)": fc_days & mnf_days,
            "OR (cobertura)": fc_days | mnf_days,
        }
        for name, p_days in preds.items():
            tp, fp, fn = len(p_days & truth), len(p_days - truth), len(truth - p_days)
            for seg in (segment, "TOTAL"):
                totals[seg][name][0] += tp
                totals[seg][name][1] += fp
                totals[seg][name][2] += fn

        meter_rows.append({
            "meter": mid, "segment": segment, "leak_days_real": len(truth),
            "fc_days": len(fc_days), "mnf_days": len(mnf_days),
            "detected_fc": bool(fc_days & truth) if truth else None,
            "detected_mnf": bool(mnf_days & truth) if truth else None,
        })

    results = {}
    for seg, dets in totals.items():
        results[seg] = {name: prf(*counts) for name, counts in dets.items()}
        print(f"\n=== {seg.upper()} — nivel día, contadores de test ===")
        print(f"{'Detector':<18} {'Precision':>10} {'Recall':>8} {'F1':>7} {'TP':>5} {'FP':>5} {'FN':>5}")
        print("-" * 62)
        for name, m in results[seg].items():
            print(f"{name:<18} {m['precision']:>10} {m['recall']:>8} {m['f1']:>7} "
                  f"{m['tp']:>5} {m['fp']:>5} {m['fn']:>5}")

    print("\n--- Detalle por contador de test ---")
    for r in meter_rows:
        status = "sin fuga real" if r["leak_days_real"] == 0 else \
            f"fuga {r['leak_days_real']}d · FC:{'✓' if r['detected_fc'] else '✗'} MNF:{'✓' if r['detected_mnf'] else '✗'}"
        print(f"  {r['meter']} ({r['segment']}): {status} · días marcados FC={r['fc_days']} MNF={r['mnf_days']}")

    out = BASE_DIR / "data" / "aggregated_evaluation.json"
    out.write_text(json.dumps({
        "cusum_params": cfg["cusum"],
        "test_meters": test_ids,
        "day_level_metrics": results,
        "per_meter": meter_rows,
    }, indent=2, default=str))
    print(f"\nGuardado en {out}")


if __name__ == "__main__":
    main()
