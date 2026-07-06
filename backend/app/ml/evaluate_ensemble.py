"""
Evaluación honesta del ensemble a NIVEL DE DÍA contra el ground truth.

Para cada hogar puntuado (fleet_scores.json, esquema v2) compara los días
marcados por cada detector con los días de fuga reales del simulador:

  - ML  : días anómalos del LSTM Autoencoder
  - MNF : noches con caudal que nunca baja del suelo (regla física)
  - AND : ambos coinciden ese día  -> lo que respalda las alertas CONFIRMADAS
  - OR  : cualquiera de los dos    -> cobertura máxima (recall)

No carga TensorFlow: lee la caché de scoring y el CSV. Ejecutar desde backend/:
    python -m app.ml.evaluate_ensemble

Caveat conocido: las ventanas del ML abarcan 24h, así que el día siguiente al
fin de una fuga puede quedar marcado (cuenta como FP en la métrica estricta).
"""
import json
from pathlib import Path

import pandas as pd

from app.core.simulation_config import settings

BASE_DIR = Path(__file__).resolve().parents[2]
CACHE_PATH = BASE_DIR / "data" / "fleet_scores.json"
DATA_PATH = settings.DATA_DIR  # mismo dataset que sirve el backend


def day_metrics(pred_days: set, truth_days: set, all_days: set) -> tuple:
    """Devuelve (tp, fp, fn) a nivel de día para un hogar."""
    tp = len(pred_days & truth_days)
    fp = len(pred_days - truth_days)
    fn = len(truth_days - pred_days)
    return tp, fp, fn


def prf(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
            "tp": tp, "fp": fp, "fn": fn}


def evaluate_subset(scored: dict, df: pd.DataFrame, subset: set | None = None) -> tuple:
    """Métricas día-nivel agregadas; subset limita a esos household_ids."""
    totals = {k: [0, 0, 0] for k in ("ML", "MNF", "AND (confirmadas)", "OR (cobertura)")}
    n_households = 0
    households_with_leak = 0

    for hid, s in scored.items():
        if subset is not None and hid not in subset:
            continue
        g = df[df["household_id"] == hid]
        if g.empty:
            continue
        n_households += 1
        truth_days = set(g.loc[g["is_leak"] == 1, "day"])
        all_days = set(g["day"])
        if truth_days:
            households_with_leak += 1

        ml_days = set(s.get("anomalous_days", []))
        mnf_days = set(s.get("mnf_days", []))

        preds = {
            "ML": ml_days,
            "MNF": mnf_days,
            "AND (confirmadas)": ml_days & mnf_days,
            "OR (cobertura)": ml_days | mnf_days,
        }
        for name, pred in preds.items():
            tp, fp, fn = day_metrics(pred, truth_days, all_days)
            totals[name][0] += tp
            totals[name][1] += fp
            totals[name][2] += fn

    results = {name: prf(tp, fp, fn) for name, (tp, fp, fn) in totals.items()}
    return results, n_households, households_with_leak


def print_table(title: str, results: dict, n: int, with_leak: int):
    print(f"\n{title} — {n} hogares ({with_leak} con fuga real)\n")
    print(f"{'Detector':<20} {'Precision':>10} {'Recall':>8} {'F1':>7} {'TP':>6} {'FP':>6} {'FN':>6}")
    print("-" * 68)
    for name, m in results.items():
        print(f"{name:<20} {m['precision']:>10} {m['recall']:>8} {m['f1']:>7} {m['tp']:>6} {m['fp']:>6} {m['fn']:>6}")


def main():
    scores = json.loads(CACHE_PATH.read_text())
    scored = {h: s for h, s in scores.items() if s.get("schema") == 2 and "error" not in s}
    if not scored:
        print("No hay hogares con esquema v2 en la caché. Ejecuta antes: python -m app.services.fleet")
        return

    print(f"Cargando ground truth de {DATA_PATH.name}...")
    df = pd.read_csv(DATA_PATH, usecols=["timestamp", "household_id", "is_leak"])
    df["day"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d")

    # Tabla 1: flota completa
    results_all, n_all, leak_all = evaluate_subset(scored, df)
    print_table("Evaluación a nivel de DÍA — FLOTA COMPLETA", results_all, n_all, leak_all)

    # Tabla 2: SOLO hogares de test del entrenamiento (nunca vistos por el modelo)
    # -> la métrica defendible. Lee la lista del artefacto threshold.json.
    results_test = None
    if settings.THRESHOLD_ARTIFACT.exists():
        artifact = json.loads(settings.THRESHOLD_ARTIFACT.read_text())
        test_ids = set(artifact.get("test_households", []))
        if test_ids:
            results_test, n_t, leak_t = evaluate_subset(scored, df, subset=test_ids)
            print_table("SOLO HOGARES DE TEST (nunca vistos en entrenamiento)", results_test, n_t, leak_t)

    out = BASE_DIR / "data" / "ensemble_evaluation.json"
    out.write_text(json.dumps({
        "households_evaluated": n_all,
        "day_level_metrics": results_all,
        "day_level_metrics_test_households_only": results_test,
    }, indent=2))
    print(f"\nGuardado en {out}")


if __name__ == "__main__":
    main()
