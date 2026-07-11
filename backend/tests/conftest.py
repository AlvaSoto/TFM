"""
Red de seguridad para toda la suite: backend/data/tenants.json y
.secret_key son ESTADO REAL de la demo (si tenants.json existe, la consola
deja de estar en modo abierto para cualquiera que la arranque en local).
Ningún test debe dejarlos creados al terminar.

pilot_readings.db NO se vigila por existencia: SQLite crea el fichero en
cuanto algo abre una conexión (basta con importar la app), así que un
.db vacío es inofensivo y esperado. Lo que sí importa es que no tenga
lecturas de contadores de prueba colgando.

Cada test que necesite tenants/lecturas reales los limpia en su propio
try/finally; esto es solo el cinturón de seguridad final por si algo se cuela.
"""
import sqlite3
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_GUARDED_AUTH = ["tenants.json", ".secret_key"]


def _pilot_db_has_data() -> bool:
    db = DATA_DIR / "pilot_readings.db"
    if not db.exists():
        return False
    try:
        with sqlite3.connect(db) as c:
            return c.execute("SELECT COUNT(*) FROM readings").fetchone()[0] > 0
    except sqlite3.OperationalError:
        return False  # tabla aún no creada = sin datos


def _assert_pristine():
    leftovers = [f for f in _GUARDED_AUTH if (DATA_DIR / f).exists()]
    assert not leftovers, (
        f"Estado de piloto sin limpiar antes de la suite: {leftovers}. "
        "Borra esos ficheros de backend/data/ antes de ejecutar los tests "
        "(romperían el modo abierto de la demo)."
    )
    assert not _pilot_db_has_data(), (
        "pilot_readings.db contiene lecturas de una ejecución anterior sin "
        "limpiar. Bórralo (está vacío es inofensivo, con datos no)."
    )


@pytest.fixture(scope="session", autouse=True)
def guard_demo_state():
    _assert_pristine()
    yield
    # Red de seguridad final: si algún test dejó residuos pese a su propio
    # cleanup, no se cuelan en el repo ni rompen la demo del usuario.
    for f in _GUARDED_AUTH:
        p = DATA_DIR / f
        if p.exists():
            p.unlink()
