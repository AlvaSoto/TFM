"""
Test end-to-end del aislamiento multi-tenant sobre la API REAL (crea
tenants y contadores de verdad contra backend/data/). Es el test más
importante de todo el proyecto: una regresión aquí filtra datos de un
cliente a otro.

Limpieza garantizada: crea sus tenants/lecturas en backend/data/ real (no
hay forma de probar el flujo HTTP completo de otro modo, porque los routers
enlazan los singletons en tiempo de import) y los borra en el `finally`,
pase lo que pase, restaurando el modo abierto para la demo del usuario.
"""
import pandas as pd
from fastapi.testclient import TestClient

from app.api.router import app
from app.core import tenants as T

client = TestClient(app)


def _cleanup():
    for f in ("tenants.json", ".secret_key"):
        p = T.settings.BASE_DIR / "data" / f
        if p.exists():
            p.unlink()
    from app.repository.readings_store import readings_store
    with readings_store._conn() as c:
        c.execute("DELETE FROM readings WHERE meter_id LIKE 'pytest_%'")
        c.execute("DELETE FROM meter_meta WHERE meter_id LIKE 'pytest_%'")


def test_multi_tenant_isolation_end_to_end():
    try:
        c1 = T.create_tenant("pytest_hotel_a", "Hotel A (test)")
        c2 = T.create_tenant("pytest_gestora_b", "Gestora B (test)", include_demo=True)

        # 1. Sin login, la consola exige credenciales
        assert client.get("/api/v1/fleet/overview").status_code == 401

        # 2. Login incorrecto rechazado, correcto emite token
        assert client.post("/api/v1/auth/login",
                           json={"tenant_id": "pytest_hotel_a", "password": "mala"}).status_code == 401
        tok1 = client.post("/api/v1/auth/login",
                           json={"tenant_id": "pytest_hotel_a", "password": c1["password"]}).json()["token"]
        tok2 = client.post("/api/v1/auth/login",
                           json={"tenant_id": "pytest_gestora_b", "password": c2["password"]}).json()["token"]

        # 3. El tenant 1 ingiere un contador con SU api key
        ts = pd.date_range("2026-06-01", periods=48, freq="h")
        readings = [{"timestamp": t.isoformat(), "value": 100.0} for t in ts]
        r = client.post("/api/v1/ingest/readings", headers={"X-API-Key": c1["api_key"]},
                        json={"meter_id": "pytest_meter_a", "readings": readings})
        assert r.status_code == 200 and r.json()["inserted"] == 48

        # 4. Tenant 1 ve SOLO su contador; tenant 2 (con demo) NO lo ve, pero sí la flota demo
        h1 = client.get("/api/v1/households", headers={"Authorization": f"Bearer {tok1}"}).json()["households"]
        assert [h["id"] for h in h1] == ["pytest_meter_a"]

        h2 = client.get("/api/v1/households", headers={"Authorization": f"Bearer {tok2}"}).json()["households"]
        ids2 = [h["id"] for h in h2]
        assert "pytest_meter_a" not in ids2
        assert len(ids2) > 100  # ve la flota demo completa

        # 5. Tenant 2 no puede abrir el dashboard del contador del tenant 1 (404, no 403: no revela existencia)
        r = client.get("/api/v1/consumption/dashboard/pytest_meter_a",
                       headers={"Authorization": f"Bearer {tok2}"})
        assert r.status_code == 404

        # 6. La API key del tenant 2 no puede escribir en el contador del tenant 1
        r = client.post("/api/v1/ingest/readings", headers={"X-API-Key": c2["api_key"]},
                        json={"meter_id": "pytest_meter_a", "readings": readings[:1]})
        assert r.status_code == 403

        # 7. El overview de flota del tenant 1 está acotado a su propio contador
        ov1 = client.get("/api/v1/fleet/overview", headers={"Authorization": f"Bearer {tok1}"}).json()
        assert ov1["kpis"]["households_total"] == 1

        # 8. Branding propio
        me2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tok2}"}).json()
        assert me2["id"] == "pytest_gestora_b"
    finally:
        _cleanup()
