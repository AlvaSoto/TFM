"""
Tests de la lógica de detección física (night_flow.py). Sin I/O, sin modelo:
rápidos y deterministas.
"""
from datetime import datetime, timedelta

import pandas as pd

from app.services.night_flow import combine_alert_level, mnf_analysis, mnf_trending


def _series(start, days, resolution_min, value_fn):
    """Construye un DataFrame timestamp/consumption_l sintético."""
    steps_per_day = 24 * 60 // resolution_min
    rows = []
    for d in range(days):
        for s in range(steps_per_day):
            ts = start + timedelta(days=d, minutes=s * resolution_min)
            rows.append({"timestamp": ts, "consumption_l": value_fn(d, ts.hour, ts.minute)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# mnf_analysis (hogares: suelo absoluto)
# ---------------------------------------------------------------------
def test_mnf_analysis_flags_continuous_night_flow():
    """Caudal que nunca baja de 5 L/15min en 4 madrugadas -> CONFIRMADA."""
    start = datetime(2026, 6, 1)

    def leaking(d, h, m):
        return 5.0 if 1 <= h <= 5 else 20.0  # suelo nocturno constante = fuga

    df = _series(start, days=6, resolution_min=15, value_fn=leaking)
    result = mnf_analysis(df)
    assert result["mnf_alert"] is True
    assert result["nights_analyzed"] >= 5
    assert len(result["mnf_days"]) >= 2


def test_mnf_analysis_no_flag_for_normal_pattern():
    """Consumo nocturno a cero (patrón humano normal) -> sin alerta."""
    start = datetime(2026, 6, 1)

    def normal(d, h, m):
        return 0.0 if 1 <= h <= 5 else 15.0

    df = _series(start, days=6, resolution_min=15, value_fn=normal)
    result = mnf_analysis(df)
    assert result["mnf_alert"] is False
    assert result["mnf_days"] == []


def test_mnf_analysis_requires_persistence_not_a_single_night():
    """Una sola noche con suelo alto no basta (MIN_NIGHTS=2): evita falsos positivos por ruido."""
    start = datetime(2026, 6, 1)

    def one_bad_night(d, h, m):
        if 1 <= h <= 5:
            return 8.0 if d == 3 else 0.0
        return 15.0

    df = _series(start, days=6, resolution_min=15, value_fn=one_bad_night)
    result = mnf_analysis(df)
    assert result["mnf_alert"] is False


def test_mnf_analysis_is_resolution_agnostic():
    """Mismo caudal por minuto, servido en 15min y en 1h: misma conclusión."""
    start = datetime(2026, 6, 1)

    def leaking_lpm(h):
        return 0.5  # L/min de fuga constante, muy por encima del umbral (~0.13 L/min)

    df_15 = _series(start, days=6, resolution_min=15, value_fn=lambda d, h, m: leaking_lpm(h) * 15)
    df_60 = _series(start, days=6, resolution_min=60, value_fn=lambda d, h, m: leaking_lpm(h) * 60)

    assert mnf_analysis(df_15)["mnf_alert"] is True
    assert mnf_analysis(df_60)["mnf_alert"] is True


# ---------------------------------------------------------------------
# mnf_trending (agregados: línea base móvil, suelo nunca cero)
# ---------------------------------------------------------------------
def test_mnf_trending_detects_step_change_against_own_baseline():
    """Un hotel con suelo nocturno estable de 40 L/15min que salta a 90: CONFIRMADA."""
    start = datetime(2026, 5, 1)

    def hotel(d, h, m):
        floor = 90.0 if d >= 35 else 40.0  # escalón tras 35 noches de baseline
        return floor if 1 <= h <= 5 else 300.0

    df = _series(start, days=42, resolution_min=15, value_fn=hotel)
    result = mnf_trending(df)
    assert result["mnf_alert"] is True
    # Los días marcados deben caer en el tramo con el escalón, no en el baseline
    assert all(d >= "2026-06-05" for d in result["mnf_days"])


def test_mnf_trending_no_alert_within_normal_variation():
    """Suelo nocturno legítimo (nunca cero) pero estable: sin alerta pese a MNF absoluto disparando."""
    start = datetime(2026, 5, 1)

    def stable_hotel(d, h, m):
        floor = 35.0 + (2.0 if d % 2 == 0 else -2.0)  # pequeña variación día a día
        return floor if 1 <= h <= 5 else 250.0

    df = _series(start, days=40, resolution_min=15, value_fn=stable_hotel)
    trending = mnf_trending(df)
    absolute = mnf_analysis(df)

    assert trending["mnf_alert"] is False
    assert absolute["mnf_alert"] is True  # confirma por qué el absoluto NO vale en agregados


# ---------------------------------------------------------------------
# combine_alert_level: CONFIRMADA = MNF solo; SOSPECHA = solo ML
# ---------------------------------------------------------------------
def test_combine_alert_level_truth_table():
    assert combine_alert_level(ml_alert=True, mnf_alert=True) == "CONFIRMADA"
    assert combine_alert_level(ml_alert=False, mnf_alert=True) == "CONFIRMADA"
    assert combine_alert_level(ml_alert=True, mnf_alert=False) == "SOSPECHA"
    assert combine_alert_level(ml_alert=False, mnf_alert=False) == "OK"
