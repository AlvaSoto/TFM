"""
Perfiles de punto de medida: metadatos legibles derivados del ID del simulador.
En producción con datos reales, esta información vendría del maestro de
contratos/activos del cliente.

Tipos soportados:
  - household_<perfil>_<nnnn>  → hogares (simulador de eventos discretos)
  - meter_hotel_<nnnn>         → hoteles/balnearios (simulador agregado)
  - meter_pueblo_<nnnn>        → pueblos/sectores DMA (simulador agregado)
"""
import re

PROFILE_LABELS = {
    "apartment_single_person": {"label": "Apartamento", "people": 1},
    "apartment_family": {"label": "Apartamento", "people": 4},
    "house_family_garden": {"label": "Casa con jardín", "people": 4},
}

_HOUSEHOLD_RE = re.compile(r"^household_(.+)_\d+$")
_METER_RE = re.compile(r"^meter_(hotel|pueblo)_\d+$")

METER_LABELS = {
    "hotel": {"label": "Hotel / Balneario", "people": None, "segment": "hotel"},
    "pueblo": {"label": "Pueblo / Sector DMA", "people": None, "segment": "pueblo"},
}


def parse_profile(household_id: str) -> dict:
    m = _METER_RE.match(household_id)
    if m:
        return {"key": m.group(1), **METER_LABELS[m.group(1)]}

    m = _HOUSEHOLD_RE.match(household_id)
    key = m.group(1) if m else household_id
    info = PROFILE_LABELS.get(key, {"label": key.replace("_", " ").title(), "people": None})
    return {"key": key, "segment": "hogar", **info}
