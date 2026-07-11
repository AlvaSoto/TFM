"""
Tests de autenticación multi-tenant. Todas las rutas (tenants.json,
.secret_key) se redirigen a tmp_path vía monkeypatch: nunca tocan
backend/data/ real, así que el modo abierto de la demo no se ve afectado
por ejecutar esta suite.
"""
import time

import pytest

from app.core import tenants as T


@pytest.fixture(autouse=True)
def isolated_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "TENANTS_PATH", tmp_path / "tenants.json")
    monkeypatch.setattr(T, "SECRET_PATH", tmp_path / ".secret_key")
    yield


def test_open_mode_when_no_tenants_file():
    assert T.load_tenants() == []
    assert T.auth_enabled() is False


def test_create_tenant_generates_unique_hashed_credentials():
    creds = T.create_tenant("hotel_x", "Hotel X", email="ops@hotelx.com")
    assert creds["tenant_id"] == "hotel_x"
    assert len(creds["password"]) >= 12
    assert len(creds["api_key"]) >= 20

    tenant = T.get_tenant("hotel_x")
    assert tenant is not None
    assert tenant["password_sha256"] != creds["password"]  # nunca en claro
    assert T.auth_enabled() is True


def test_create_tenant_rejects_duplicate_id():
    T.create_tenant("dup", "Dup Co")
    with pytest.raises(ValueError):
        T.create_tenant("dup", "Otro nombre")


def test_verify_password_accepts_correct_rejects_wrong():
    creds = T.create_tenant("hotel_y", "Hotel Y")
    tenant = T.get_tenant("hotel_y")
    assert T.verify_password(tenant, creds["password"]) is True
    assert T.verify_password(tenant, "clave-incorrecta") is False


def test_tenant_by_api_key_resolves_owner():
    creds = T.create_tenant("gestora_z", "Gestora Z")
    found = T.tenant_by_api_key(creds["api_key"])
    assert found is not None
    assert found["id"] == "gestora_z"
    assert T.tenant_by_api_key("clave-inventada") is None


def test_token_roundtrip_valid():
    T.create_tenant("hotel_w", "Hotel W")
    token = T.issue_token("hotel_w")
    tenant = T.validate_token(token)
    assert tenant is not None
    assert tenant["id"] == "hotel_w"


def test_token_tampering_is_rejected():
    T.create_tenant("hotel_v", "Hotel V")
    token = T.issue_token("hotel_v")
    tampered = token[:-4] + "abcd"
    assert T.validate_token(tampered) is None


def test_token_expiry_is_enforced(monkeypatch):
    T.create_tenant("hotel_u", "Hotel U")
    monkeypatch.setattr(T, "TOKEN_TTL_SECONDS", -1)  # ya caducado al emitirlo
    token = T.issue_token("hotel_u")
    assert T.validate_token(token) is None


def test_token_for_deleted_tenant_is_rejected(tmp_path):
    T.create_tenant("hotel_temp", "Hotel Temp")
    token = T.issue_token("hotel_temp")
    # Simula borrado del tenant (fichero reescrito sin él)
    T.TENANTS_PATH.write_text('{"tenants": []}')
    assert T.validate_token(token) is None
