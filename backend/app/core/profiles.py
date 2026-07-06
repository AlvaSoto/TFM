"""
Perfiles de hogar: metadatos legibles derivados del household_id del simulador
(household_<perfil>_<nnnn>). En producción con datos reales, esta información
vendría del maestro de contratos de la gestora.
"""
import re

PROFILE_LABELS = {
    "apartment_single_person": {"label": "Apartamento", "people": 1},
    "apartment_family": {"label": "Apartamento", "people": 4},
    "house_family_garden": {"label": "Casa con jardín", "people": 4},
}

_ID_RE = re.compile(r"^household_(.+)_\d+$")


def parse_profile(household_id: str) -> dict:
    m = _ID_RE.match(household_id)
    key = m.group(1) if m else household_id
    info = PROFILE_LABELS.get(key, {"label": key.replace("_", " ").title(), "people": None})
    return {"key": key, **info}
