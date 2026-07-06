"""
API de INGESTA del piloto: por aquí entran las lecturas de contadores reales.

Autenticación por API key (cabecera X-API-Key contra INGEST_API_KEY del .env).
Sin clave configurada, la ingesta queda deshabilitada — nunca abierta por defecto.

Dos formatos de entrada:
  1. JSON batch (para pasarelas IoT / integraciones):
     POST /api/v1/ingest/readings
     { "meter_id": "hotel_playa_principal",
       "value_type": "interval" | "cumulative",   # litros del intervalo o índice del contador
       "readings": [ {"timestamp": "2026-07-06T10:00:00", "value": 123.4}, ... ] }

  2. CSV (para gestoras que exportan ficheros):
     POST /api/v1/ingest/csv?meter_id=...&value_type=interval
     multipart con un fichero de columnas: timestamp, value
"""
import io

import pandas as pd
from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.core.simulation_config import settings
from app.repository.readings_store import readings_store

router = APIRouter()


def require_api_key(x_api_key: str = Header(default="")):
    configured = settings.INGEST_API_KEY
    if not configured:
        raise HTTPException(
            status_code=503,
            detail="Ingesta deshabilitada: configura INGEST_API_KEY en el entorno del servidor.",
        )
    if x_api_key != configured:
        raise HTTPException(status_code=401, detail="API key inválida (cabecera X-API-Key).")


class Reading(BaseModel):
    timestamp: str
    value: float


class ReadingsBatch(BaseModel):
    meter_id: str = Field(min_length=1, max_length=120)
    value_type: str = Field(default="interval", pattern="^(interval|cumulative)$")
    readings: list[Reading] = Field(min_length=1, max_length=50_000)


@router.post("/ingest/readings", dependencies=[Depends(require_api_key)])
def ingest_readings(batch: ReadingsBatch):
    try:
        rows = [(pd.to_datetime(r.timestamp).isoformat(), r.value) for r in batch.readings]
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Timestamp inválido: {e}")

    if batch.value_type == "cumulative":
        result = readings_store.insert_cumulative_batch(batch.meter_id, rows)
    else:
        result = readings_store.insert_interval_batch(batch.meter_id, rows)
    return {"meter_id": batch.meter_id, **result}


@router.post("/ingest/csv", dependencies=[Depends(require_api_key)])
async def ingest_csv(
    meter_id: str = Query(min_length=1, max_length=120),
    value_type: str = Query(default="interval", pattern="^(interval|cumulative)$"),
    file: UploadFile = File(...),
):
    raw = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(raw))
        cols = {c.lower().strip(): c for c in df.columns}
        ts_col = cols.get("timestamp") or cols.get("fecha") or list(df.columns)[0]
        val_col = cols.get("value") or cols.get("consumption_l") or cols.get("consumo") or list(df.columns)[1]
        rows = [
            (pd.to_datetime(t).isoformat(), float(v))
            for t, v in zip(df[ts_col], df[val_col])
            if pd.notna(t) and pd.notna(v)
        ]
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"CSV no interpretable: {e}")

    if not rows:
        raise HTTPException(status_code=422, detail="El CSV no contiene lecturas válidas.")

    if value_type == "cumulative":
        result = readings_store.insert_cumulative_batch(meter_id, rows)
    else:
        result = readings_store.insert_interval_batch(meter_id, rows)
    return {"meter_id": meter_id, "file": file.filename, **result}


@router.get("/ingest/status", dependencies=[Depends(require_api_key)])
def ingest_status():
    """Qué contadores reales hay y cuántas lecturas tiene cada uno."""
    return {"meters": readings_store.status()}
