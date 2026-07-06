"""
Almacén de lecturas REALES del piloto (SQLite).

El dataset sintético vive en CSV (demo); las lecturas que llegan por la API de
ingesta se persisten aquí. data_loader fusiona ambos orígenes, de modo que un
contador real aparece en la consola exactamente igual que uno simulado.

SQLite es deliberado para la fase de piloto: cero configuración, un fichero,
transaccional, y aguanta sin despeinarse decenas de contadores con lecturas
horarias. La migración a Postgres/Timescale es un cambio de este módulo.
"""
import sqlite3
import threading
from pathlib import Path

import pandas as pd

from app.core.simulation_config import settings

DB_PATH = settings.BASE_DIR / "data" / "pilot_readings.db"


class ReadingsStore:
    def __init__(self, db_path: Path = DB_PATH):
        self._db_path = db_path
        self._lock = threading.Lock()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS readings (
                    meter_id TEXT NOT NULL,
                    ts TEXT NOT NULL,           -- ISO 8601
                    consumption_l REAL NOT NULL, -- consumo del intervalo, en litros
                    PRIMARY KEY (meter_id, ts)
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS meter_meta (
                    meter_id TEXT PRIMARY KEY,
                    last_cumulative REAL         -- último índice acumulado visto (contadores de índice)
                )
            """)

    def _conn(self):
        return sqlite3.connect(self._db_path)

    # ------------------------------------------------------------------
    def insert_interval_batch(self, meter_id: str, rows: list) -> dict:
        """rows: [(iso_timestamp, litros_del_intervalo), ...]. Idempotente."""
        inserted = 0
        with self._lock, self._conn() as c:
            for ts, liters in rows:
                cur = c.execute(
                    "INSERT OR IGNORE INTO readings (meter_id, ts, consumption_l) VALUES (?, ?, ?)",
                    (meter_id, ts, float(liters)),
                )
                inserted += cur.rowcount
        return {"received": len(rows), "inserted": inserted, "duplicates": len(rows) - inserted}

    def insert_cumulative_batch(self, meter_id: str, rows: list) -> dict:
        """
        rows: [(iso_timestamp, índice_acumulado_en_litros), ...] ordenados.
        Convierte el índice del contador en consumo por intervalo (diferencias).
        Ignora retrocesos (vuelta de contador / sustitución): intervalo perdido.
        """
        rows = sorted(rows, key=lambda r: r[0])
        with self._lock, self._conn() as c:
            prev = c.execute(
                "SELECT last_cumulative FROM meter_meta WHERE meter_id = ?", (meter_id,)
            ).fetchone()
            last = prev[0] if prev else None

            inserted = 0
            for ts, value in rows:
                value = float(value)
                if last is not None and value >= last:
                    cur = c.execute(
                        "INSERT OR IGNORE INTO readings (meter_id, ts, consumption_l) VALUES (?, ?, ?)",
                        (meter_id, ts, value - last),
                    )
                    inserted += cur.rowcount
                last = value

            c.execute(
                "INSERT INTO meter_meta (meter_id, last_cumulative) VALUES (?, ?) "
                "ON CONFLICT(meter_id) DO UPDATE SET last_cumulative = excluded.last_cumulative",
                (meter_id, last),
            )
        return {"received": len(rows), "inserted": inserted, "duplicates": 0}

    # ------------------------------------------------------------------
    def meter_ids(self) -> list:
        with self._conn() as c:
            return [r[0] for r in c.execute("SELECT DISTINCT meter_id FROM readings")]

    def get_meter_df(self, meter_id: str) -> pd.DataFrame:
        with self._conn() as c:
            df = pd.read_sql_query(
                "SELECT ts AS timestamp, consumption_l FROM readings WHERE meter_id = ? ORDER BY ts",
                c, params=(meter_id,),
            )
        if df.empty:
            return df
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["is_leak"] = 0  # las lecturas reales no traen ground truth
        df["household_id"] = meter_id
        return df

    def status(self) -> list:
        with self._conn() as c:
            rows = c.execute(
                "SELECT meter_id, COUNT(*), MIN(ts), MAX(ts) FROM readings GROUP BY meter_id"
            ).fetchall()
        return [
            {"meter_id": m, "readings": n, "first": lo, "last": hi}
            for m, n, lo, hi in rows
        ]


readings_store = ReadingsStore()
