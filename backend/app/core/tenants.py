"""
Multi-tenant: registro de clientes, autenticación y contexto de datos.

Diseño para la fase piloto→primeros clientes:
  - Los tenants viven en data/tenants.json (editable a mano; migrable a BD).
  - SIN fichero de tenants: la app funciona en MODO ABIERTO (demo local),
    exactamente como hasta ahora — no rompe el flujo de desarrollo.
  - CON fichero: la consola exige login (token firmado HMAC) y cada tenant
    ve SOLO sus contadores; la ingesta identifica al tenant por su API key.

Crear un tenant:
    python -m app.core.tenants create --id hotel_costa --name "Hotel Costa" \
        --email operaciones@hotelcosta.com

Estructura de data/tenants.json:
{
  "tenants": [
    {
      "id": "hotel_costa",
      "name": "Hotel Costa del Sol",
      "password_sha256": "<hash>",           # sha256(salt + password)
      "salt": "<hex>",
      "api_key": "<clave de ingesta>",       # cabecera X-API-Key de sus dispositivos
      "report_email": "ops@hotel.com",       # destino del informe semanal
      "include_demo_dataset": false,         # true = ve también la flota sintética
      "branding": {"name": "Hotel Costa", "color": "#2a78d6"}
    }
  ]
}
"""
import base64
import hashlib
import hmac
import json
import secrets
import time
from pathlib import Path

from app.core.simulation_config import settings

TENANTS_PATH = settings.BASE_DIR / "data" / "tenants.json"
SECRET_PATH = settings.BASE_DIR / "data" / ".secret_key"
TOKEN_TTL_SECONDS = 12 * 3600  # sesión de consola: 12 h

# Tenant implícito cuando no hay fichero (modo abierto / demo local)
OPEN_MODE_TENANT = {
    "id": "demo",
    "name": "Demo",
    "include_demo_dataset": True,
    "branding": {"name": "Smart Water", "color": "#2a78d6"},
}


def _secret() -> bytes:
    """Clave de firma de tokens: env SECRET_KEY o autogenerada y persistida."""
    import os
    env = os.getenv("SECRET_KEY", "")
    if env:
        return env.encode()
    if SECRET_PATH.exists():
        return SECRET_PATH.read_bytes()
    key = secrets.token_bytes(32)
    SECRET_PATH.parent.mkdir(parents=True, exist_ok=True)
    SECRET_PATH.write_bytes(key)
    return key


def load_tenants() -> list:
    if not TENANTS_PATH.exists():
        return []
    try:
        return json.loads(TENANTS_PATH.read_text()).get("tenants", [])
    except Exception as e:
        print(f"[TENANTS] fichero ilegible ({e}); modo abierto")
        return []


def auth_enabled() -> bool:
    return len(load_tenants()) > 0


def get_tenant(tenant_id: str) -> dict | None:
    return next((t for t in load_tenants() if t["id"] == tenant_id), None)


def tenant_by_api_key(api_key: str) -> dict | None:
    if not api_key:
        return None
    return next((t for t in load_tenants() if t.get("api_key") == api_key), None)


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()


def verify_password(tenant: dict, password: str) -> bool:
    expected = tenant.get("password_sha256", "")
    return hmac.compare_digest(_hash_password(password, tenant.get("salt", "")), expected)


# ----------------------------------------------------------------------
# Tokens de sesión (HMAC firmado, sin dependencias externas)
# ----------------------------------------------------------------------
def issue_token(tenant_id: str) -> str:
    exp = int(time.time()) + TOKEN_TTL_SECONDS
    payload = f"{tenant_id}:{exp}"
    sig = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{sig}".encode()).decode()


def validate_token(token: str) -> dict | None:
    """Devuelve el tenant si el token es válido y no ha expirado; None si no."""
    try:
        payload_sig = base64.urlsafe_b64decode(token.encode()).decode()
        tenant_id, exp, sig = payload_sig.rsplit(":", 2)
        expected = hmac.new(_secret(), f"{tenant_id}:{exp}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if int(exp) < time.time():
            return None
        return get_tenant(tenant_id)
    except Exception:
        return None


# ----------------------------------------------------------------------
# CLI: crear tenants
# ----------------------------------------------------------------------
def create_tenant(tenant_id: str, name: str, email: str = "",
                  include_demo: bool = False, color: str = "#2a78d6") -> dict:
    tenants = load_tenants()
    if any(t["id"] == tenant_id for t in tenants):
        raise ValueError(f"El tenant '{tenant_id}' ya existe")

    password = secrets.token_urlsafe(12)
    salt = secrets.token_hex(8)
    tenant = {
        "id": tenant_id,
        "name": name,
        "salt": salt,
        "password_sha256": _hash_password(password, salt),
        "api_key": secrets.token_urlsafe(32),
        "report_email": email,
        "include_demo_dataset": include_demo,
        "branding": {"name": name, "color": color},
    }
    tenants.append(tenant)
    TENANTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TENANTS_PATH.write_text(json.dumps({"tenants": tenants}, indent=2, ensure_ascii=False))
    # La contraseña solo se muestra al crearla (se guarda hasheada)
    return {"tenant_id": tenant_id, "password": password, "api_key": tenant["api_key"]}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gestión de tenants")
    sub = parser.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("--id", required=True)
    c.add_argument("--name", required=True)
    c.add_argument("--email", default="")
    c.add_argument("--demo-data", action="store_true", help="El tenant ve también la flota sintética")
    c.add_argument("--color", default="#2a78d6")
    lst = sub.add_parser("list")
    args = parser.parse_args()

    if args.cmd == "create":
        creds = create_tenant(args.id, args.name, args.email, args.demo_data, args.color)
        print("Tenant creado. GUARDA ESTAS CREDENCIALES (no se vuelven a mostrar):")
        print(f"  Usuario (tenant): {creds['tenant_id']}")
        print(f"  Contraseña consola: {creds['password']}")
        print(f"  API key de ingesta: {creds['api_key']}")
    elif args.cmd == "list":
        for t in load_tenants():
            print(f"  {t['id']} — {t['name']} (demo_data={t.get('include_demo_dataset', False)})")
