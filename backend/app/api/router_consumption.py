import json

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

# --- IMPORTS DE CAPA DE DATOS ---
from app.repository.data_loader import data_loader
from app.core.water_prices import REGIONAL_PRICES, FIXED_MONTHLY_FEE
from app.core.simulation_config import settings
from app.core.profiles import parse_profile
from app.services.night_flow import mnf_analysis, combine_alert_level

# --- IMPORTS DE SERVICIOS ---
from app.services.detector import detector_service
from app.services.consumption import consumption_service
from app.services.llm_service import advisor_service
from app.services.fleet import fleet_service

router = APIRouter()

# ---------------------------------------------------------
# 1. ENDPOINTS DE UTILIDAD (Listados)
# ---------------------------------------------------------

@router.get("/households")
def list_households():
    """
    Lista las casas y marca cuáles tienen fugas reales (Ground Truth) en el CSV.
    Es instantáneo porque no ejecuta el modelo, solo lee la columna 'is_leak'.
    """
    try:
        # 1. Accedemos al DataFrame completo cargado en memoria
        df_all = data_loader.df
        
        # 2. Agrupamos por casa y miramos si el máximo de 'is_leak' es 1
        # Esto nos dice instantáneamente qué casas tienen al menos un punto de fuga
        leaks_map = df_all.groupby('household_id')['is_leak'].max()
        
        result = []
        for hid, has_leak in leaks_map.items():
            # Nota de producto: NO revelamos el ground truth en la etiqueta
            # (antes se marcaba con 💧 las casas con fuga real, delatando la respuesta).
            profile = parse_profile(hid)
            result.append({
                "id": hid,
                "label": hid,
                "profile": profile,
            })

        return {"households": result}
        
    except Exception as e:
        print(f"Error listing households: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regions", response_model=List[str])
def get_available_regions():
    """
    Endpoint to list all available regions for water pricing.
    """
    try:
        regions = list(REGIONAL_PRICES.keys())
        return regions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# 2. ENDPOINTS DE FLOTA (Vista de la gestora)
# ---------------------------------------------------------

@router.get("/fleet/overview")
def get_fleet_overview(
    region: str = Query(default="Promedio Nacional", description="Región para valorar las pérdidas en €")
):
    """
    Vista agregada para el operador de la gestora: KPIs de la flota completa
    (alertas activas, agua y dinero perdidos) y listado de hogares priorizado
    por severidad. Se sirve desde la caché de scoring (data/fleet_scores.json).
    """
    try:
        return fleet_service.get_overview(region)
    except Exception as e:
        print(f"Fleet overview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fleet/score")
def score_fleet(
    limit: int = Query(default=10, ge=1, le=200, description="Máximo de hogares pendientes a puntuar"),
    region: str = Query(default="Promedio Nacional")
):
    """
    Puntúa hasta `limit` hogares pendientes (ejecuta el modelo) y devuelve la
    vista actualizada. Para precomputar toda la flota de una vez:
    `python -m app.services.fleet`
    """
    try:
        scored = fleet_service.score_batch(limit=limit)
        overview = fleet_service.get_overview(region)
        overview["newly_scored"] = scored
        return overview
    except Exception as e:
        print(f"Fleet scoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fleet/trends")
def get_fleet_trends():
    """
    Serie diaria agregada de la red: consumo total (m³) y nº de hogares con
    anomalía cada día. Para la gráfica de red de la vista Operaciones.
    """
    try:
        return fleet_service.get_trends()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/info")
def get_system_info():
    """
    Trazabilidad del sistema: qué modelo está desplegado, con qué umbral y de
    dónde sale, sobre qué dataset opera y las métricas de la última evaluación.
    La pantalla de due diligence técnica.
    """
    try:
        import sklearn
        import tensorflow as tf

        artifact_exists = settings.THRESHOLD_ARTIFACT.exists()
        eval_path = settings.BASE_DIR / "data" / "ensemble_evaluation.json"
        evaluation = json.loads(eval_path.read_text()) if eval_path.exists() else None

        df = data_loader.df
        scored = sum(
            1 for s in fleet_service._scores.values()
            if s.get("schema") == 2 and "error" not in s
        )

        return {
            "model": {
                "path": str(settings.MODELS_DIR.relative_to(settings.BASE_DIR)),
                "architecture": "LSTM Autoencoder (secuencias 24h × 15min)",
                "threshold": detector_service.threshold,
                "threshold_source": "threshold.json (artefacto de entrenamiento)" if artifact_exists
                                    else "fallback estático (settings.LEAK_THRESHOLD)",
            },
            "ensemble": {
                "components": ["Caudal Mínimo Nocturno (regla física)", "LSTM Autoencoder (ML)"],
                "levels": {
                    "CONFIRMADA": "caudal nocturno continuo (regla física, precisión 1.0 medida)",
                    "SOSPECHA": "patrón anómalo según el modelo IA, sin confirmación física",
                    "OK": "ningún detector activo",
                },
            },
            "dataset": {
                "file": settings.DATA_DIR.name,
                "rows": int(len(df)),
                "households": int(df["household_id"].nunique()),
                "date_from": str(df["timestamp"].min().date()),
                "date_to": str(df["timestamp"].max().date()),
                "resolution": "15 min",
            },
            "fleet": {"scored": scored, "total": int(df["household_id"].nunique())},
            "versions": {"tensorflow": tf.__version__, "scikit_learn": sklearn.__version__},
            "last_evaluation": evaluation,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# 3. ENDPOINT PRINCIPAL (Dashboard)
# ---------------------------------------------------------

@router.get("/consumption/dashboard/{household_id}")
def get_consumption_dashboard(
    household_id: str,
    region: str = Query(
        default="Promedio Nacional",
        description="Region for water pricing. Defaults to 'Promedio Nacional'."
    )
):
    """
    Master Endpoint. Returns everything needed for the Frontend Dashboard:
    - Leak Analysis (ML)
    - Financial KPIs
    - Charts Data
    - Community Benchmark
    - AI Advice
    """
    try:
        # A. Cargar Datos
        df_household = data_loader.get_household_data(household_id)
        if df_household is None or df_household.empty:
            raise HTTPException(status_code=404, detail=f"No data found for household_id: {household_id}")
        
        df_region = data_loader.df # Datos globales

        # B. Ejecutar Lógica de Negocio (Servicios)

        # 1. Detección de Fugas (ML)
        # Nota: Usamos 'analyse' con 's' como en tu servicio
        leak_analysis = detector_service.analyse_household(df_household)
        
        # 2. KPIs Financieros y de Consumo
        kpis = consumption_service.get_household_kpis(df_household, region)

        # Bills history
        bills_history = consumption_service.calculate_monthly_bill_history(df_household, region=region)

        # Daily status, today vs yesterday
        daily_status = consumption_service.get_daily_status(df_household)

        # 3. Histórico para gráficas
        history = consumption_service.get_consumption_history(df_household, period="daily")

        # 4. Patrones horarios
        patterns = consumption_service.get_hourly_patterns(df_household)

        # 5. Comparativa con la comunidad
        benchmark = consumption_service.get_community_comparison(df_household, df_region)

        # 6. Estimación de pérdida basada en los datos del hogar (no en un caudal fijo)
        price_m3 = REGIONAL_PRICES.get(region, REGIONAL_PRICES["Promedio Nacional"])
        loss_liters = fleet_service.estimate_loss_liters(
            df_household, leak_analysis.get("anomalous_days", [])
        )
        loss_estimate = {
            "liters": loss_liters,
            "eur": round(loss_liters / 1000 * price_m3, 2),
            "method": "exceso sobre la mediana de días normales del propio hogar",
        }

        # 7. Asistente IA (LLM)
        ai_advice = advisor_service.generate_report(
            household_id=household_id,
            leak_data=leak_analysis,
            kpis=kpis,
            benchmark=benchmark,
            loss_estimate=loss_estimate
        )

        # 8. Ensemble: confirmación física (MNF) del diagnóstico ML
        mnf = mnf_analysis(df_household)
        ensemble = {
            "alert_level": combine_alert_level(
                leak_analysis.get("is_leak_detected", False), mnf["mnf_alert"]
            ),
            "mnf_alert": mnf["mnf_alert"],
            "mnf_days_count": len(mnf["mnf_days"]),
            "max_night_floor_l": mnf["max_night_floor_l"],
        }

        # C. Construir Respuesta JSON
        return {
            "household_id": household_id,
            "profile": parse_profile(household_id),
            "region_applied": region,
            "price_per_m3": REGIONAL_PRICES.get(region, 0),
            "loss_estimate": loss_estimate,
            "ensemble": ensemble,
            
            "ai_assistant": {
                "report": ai_advice
            },

            "leak_detection": leak_analysis,
            
            "consumption_analytics": {
                "financial_kpis": kpis,
                "bills_history": bills_history,
                "daily_status": daily_status,
                "charts": {
                    "daily_consumption": history,
                    "hourly_patterns": patterns
                },
                "community_comparison": benchmark
            }
        }

    except ValueError as ve:
        # Errores de lógica (ej: columnas faltantes)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Errores inesperados
        print(f"Server Error: {str(e)}") 
        raise HTTPException(status_code=500, detail=str(e))