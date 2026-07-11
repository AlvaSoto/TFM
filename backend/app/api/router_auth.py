"""
Autenticación de la consola (multi-tenant).

- Sin tenants configurados (data/tenants.json ausente): MODO ABIERTO — la
  consola no pide login y se comporta como la demo local de siempre.
- Con tenants: login con tenant+contraseña → token firmado (12 h) que el
  frontend envía como `Authorization: Bearer <token>`.
"""
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.core import tenants as T

router = APIRouter()


def current_tenant(authorization: str = Header(default="")) -> dict:
    """Dependencia de los endpoints de consola: resuelve el tenant activo."""
    if not T.auth_enabled():
        return T.OPEN_MODE_TENANT
    token = authorization.removeprefix("Bearer ").strip()
    tenant = T.validate_token(token) if token else None
    if not tenant:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada. Inicia sesión.")
    return tenant


class LoginRequest(BaseModel):
    tenant_id: str
    password: str


@router.get("/auth/mode")
def auth_mode():
    return {"auth_enabled": T.auth_enabled()}


@router.post("/auth/login")
def login(req: LoginRequest):
    tenant = T.get_tenant(req.tenant_id)
    if not tenant or not T.verify_password(tenant, req.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas.")
    return {
        "token": T.issue_token(tenant["id"]),
        "tenant": {"id": tenant["id"], "name": tenant["name"],
                   "branding": tenant.get("branding", {})},
    }


@router.get("/auth/me")
def me(tenant: dict = Depends(current_tenant)):
    return {"id": tenant["id"], "name": tenant["name"],
            "branding": tenant.get("branding", {}),
            "auth_enabled": T.auth_enabled()}
