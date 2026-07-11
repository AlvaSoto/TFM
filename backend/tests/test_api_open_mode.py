"""
Tests end-to-end reales sobre la API en MODO ABIERTO (sin tenants.json).
Usan TestClient contra la app real, con el dataset demo y el modelo
cargados de verdad — no mocks. No crean tenants: seguros en cualquier orden.
"""
import pytest
from fastapi.testclient import TestClient

from app.api.router import app

client = TestClient(app)


def test_health_endpoint_reports_demo_dataset():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["demo_households"] > 0


def test_auth_mode_is_open_without_tenants_file():
    r = client.get("/api/v1/auth/mode")
    assert r.status_code == 200
    assert r.json() == {"auth_enabled": False}


def test_households_list_returns_profiled_entries():
    r = client.get("/api/v1/households")
    assert r.status_code == 200
    households = r.json()["households"]
    assert len(households) > 0
    first = households[0]
    assert "id" in first and "profile" in first
    assert "label" in first["profile"]
    # No debe filtrar el ground truth (regresión: antes se marcaba con 💧)
    assert not any("💧" in h["label"] for h in households)


def test_regions_endpoint_lists_spanish_regions():
    r = client.get("/api/v1/regions")
    assert r.status_code == 200
    regions = r.json()
    assert "Galicia" in regions and "Promedio Nacional" in regions


def test_fleet_overview_has_kpis_and_alert_levels():
    r = client.get("/api/v1/fleet/overview?region=Galicia")
    assert r.status_code == 200
    body = r.json()
    assert set(["households_total", "active_alerts", "estimated_loss_eur"]) <= set(body["kpis"].keys())
    if body["households"]:
        levels = {h["alert_level"] for h in body["households"]}
        assert levels <= {"CONFIRMADA", "SOSPECHA", "OK"}


def test_dashboard_end_to_end_for_a_real_household():
    hid = client.get("/api/v1/households").json()["households"][0]["id"]
    r = client.get(f"/api/v1/consumption/dashboard/{hid}?region=Madrid")
    assert r.status_code == 200
    body = r.json()

    # Contrato de la respuesta que consume el frontend
    assert body["household_id"] == hid
    assert body["ensemble"]["alert_level"] in {"CONFIRMADA", "SOSPECHA", "OK"}
    assert "loss_estimate" in body and "liters" in body["loss_estimate"]
    assert "profile" in body
    assert "leak_detection" in body
    assert "consumption_analytics" in body
    kpis = body["consumption_analytics"]["financial_kpis"]
    assert kpis["monthly_bill_estimate"]["total_bill_eur"] >= 0


def test_dashboard_404_for_unknown_household():
    r = client.get("/api/v1/consumption/dashboard/no_existe_este_id")
    assert r.status_code == 404


def test_dashboard_regional_price_changes_the_estimate():
    hid = client.get("/api/v1/households").json()["households"][0]["id"]
    r_low = client.get(f"/api/v1/consumption/dashboard/{hid}?region=Castilla y León")   # tarifa baja
    r_high = client.get(f"/api/v1/consumption/dashboard/{hid}?region=Cataluña")          # tarifa alta
    bill_low = r_low.json()["consumption_analytics"]["financial_kpis"]["monthly_bill_estimate"]["total_bill_eur"]
    bill_high = r_high.json()["consumption_analytics"]["financial_kpis"]["monthly_bill_estimate"]["total_bill_eur"]
    assert bill_high > bill_low


def test_system_info_exposes_model_traceability():
    r = client.get("/api/v1/system/info")
    assert r.status_code == 200
    body = r.json()
    assert "threshold" in body["model"] and "threshold_source" in body["model"]
    assert body["dataset"]["households"] > 0
    assert "components" in body["ensemble"]
    # Trazabilidad de ambos segmentos: hogares (LSTM+MNF) y agregados (forecaster+CUSUM)
    assert "last_evaluation" in body
    assert "last_evaluation_aggregated" in body
    if body["last_evaluation_aggregated"]:
        assert "TOTAL" in body["last_evaluation_aggregated"]["day_level_metrics"]


def test_ingest_without_key_is_rejected_when_disabled():
    r = client.post("/api/v1/ingest/readings", json={
        "meter_id": "sin_autorizar",
        "readings": [{"timestamp": "2026-06-01T00:00:00", "value": 1.0}],
    })
    # 503 si no hay ninguna clave configurada en el sistema, 401 si la hay pero es otra
    assert r.status_code in (401, 503)
