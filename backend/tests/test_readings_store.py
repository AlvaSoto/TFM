"""
Tests del almacén de lecturas del piloto. Cada test crea su propio SQLite
temporal (tmp_path) — nunca toca backend/data/pilot_readings.db real.
"""
import pytest

from app.repository.readings_store import ReadingsStore


@pytest.fixture
def store(tmp_path):
    return ReadingsStore(db_path=tmp_path / "test_readings.db")


def test_insert_interval_batch_is_idempotent(store):
    rows = [("2026-06-01T00:00:00", 10.0), ("2026-06-01T00:15:00", 12.0)]
    r1 = store.insert_interval_batch("meter_a", rows, tenant_id="t1")
    assert r1 == {"received": 2, "inserted": 2, "duplicates": 0}

    r2 = store.insert_interval_batch("meter_a", rows, tenant_id="t1")
    assert r2 == {"received": 2, "inserted": 0, "duplicates": 2}

    df = store.get_meter_df("meter_a")
    assert len(df) == 2  # no se duplicó nada


def test_insert_cumulative_batch_converts_index_to_deltas(store):
    rows = [
        ("2026-06-01T00:00:00", 1000.0),
        ("2026-06-01T01:00:00", 1015.0),  # +15
        ("2026-06-01T02:00:00", 1040.0),  # +25
    ]
    store.insert_cumulative_batch("meter_b", rows, tenant_id="t1")
    df = store.get_meter_df("meter_b").sort_values("timestamp")
    # El primer punto no genera consumo (no hay índice previo); los siguientes sí
    assert list(df["consumption_l"].round(1)) == [15.0, 25.0]


def test_insert_cumulative_batch_ignores_counter_rollback(store):
    """Un contador sustituido/reseteado no debe generar un consumo negativo absurdo."""
    store.insert_cumulative_batch("meter_c", [("2026-06-01T00:00:00", 5000.0)], tenant_id="t1")
    # El índice retrocede (contador cambiado): ese intervalo se descarta, no resta
    store.insert_cumulative_batch("meter_c", [("2026-06-01T01:00:00", 40.0)], tenant_id="t1")
    df = store.get_meter_df("meter_c")
    assert (df["consumption_l"] >= 0).all()
    assert len(df) == 0  # ningún delta válido aún (el segundo punto quedó como nuevo "last")


def test_claim_meter_blocks_cross_tenant_write(store):
    store.insert_interval_batch("shared_id", [("2026-06-01T00:00:00", 1.0)], tenant_id="hotel_a")
    with pytest.raises(PermissionError):
        store.insert_interval_batch("shared_id", [("2026-06-01T01:00:00", 2.0)], tenant_id="hotel_b")


def test_meter_ids_filtered_by_tenant(store):
    store.insert_interval_batch("m1", [("2026-06-01T00:00:00", 1.0)], tenant_id="tenant_x")
    store.insert_interval_batch("m2", [("2026-06-01T00:00:00", 1.0)], tenant_id="tenant_y")

    assert store.meter_ids(tenant_id="tenant_x") == ["m1"]
    assert store.meter_ids(tenant_id="tenant_y") == ["m2"]
    assert set(store.meter_ids()) == {"m1", "m2"}  # sin filtro: todos


def test_status_reports_range_and_count(store):
    rows = [(f"2026-06-01T{h:02d}:00:00", 5.0) for h in range(5)]
    store.insert_interval_batch("m1", rows, tenant_id="t1")
    status = store.status()
    assert len(status) == 1
    assert status[0]["meter_id"] == "m1"
    assert status[0]["readings"] == 5
