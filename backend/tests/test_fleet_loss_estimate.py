"""
Test de la estimación de pérdida (fleet.py): exceso de consumo de los días
anómalos sobre la mediana de los días normales del propio hogar.

Importar app.services.fleet carga el dataset demo y el modelo Keras
(~10-15s la primera vez): coste real y aceptado, no un mock.
"""
import pandas as pd

from app.services.fleet import fleet_service


def _daily_df(daily_liters: dict[str, float]) -> pd.DataFrame:
    rows = []
    for date, liters in daily_liters.items():
        ts = pd.Timestamp(date)
        for h in range(24):
            rows.append({"timestamp": ts + pd.Timedelta(hours=h), "consumption_l": liters / 24})
    return pd.DataFrame(rows)


def test_estimate_loss_liters_computes_excess_over_baseline():
    df = _daily_df({
        "2026-06-01": 100, "2026-06-02": 105, "2026-06-03": 95,   # normales
        "2026-06-04": 300, "2026-06-05": 320,                      # fuga
    })
    loss = fleet_service.estimate_loss_liters(df, anomalous_days=["2026-06-04", "2026-06-05"])
    # baseline (mediana de normales) = 100; exceso = (300-100)+(320-100) = 420
    assert loss == 420.0


def test_estimate_loss_liters_zero_when_no_anomalous_days():
    df = _daily_df({"2026-06-01": 100, "2026-06-02": 110})
    assert fleet_service.estimate_loss_liters(df, anomalous_days=[]) == 0.0


def test_estimate_loss_liters_clips_negative_excess_to_zero():
    """Un día 'anómalo' que en realidad consumió MENOS que el baseline no resta pérdida."""
    df = _daily_df({
        "2026-06-01": 100, "2026-06-02": 100, "2026-06-03": 100,
        "2026-06-04": 40,  # anómalo pero por debajo del baseline
    })
    loss = fleet_service.estimate_loss_liters(df, anomalous_days=["2026-06-04"])
    assert loss == 0.0
