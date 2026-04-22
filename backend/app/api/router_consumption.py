from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

# --- IMPORTS DE CAPA DE DATOS ---
from app.repository.data_loader import data_loader
from app.core.water_prices import REGIONAL_PRICES, FIXED_MONTHLY_FEE

# --- IMPORTS DE SERVICIOS ---
from app.services.detector import detector_service
from app.services.consumption import consumption_service
from app.services.llm_service import advisor_service

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
            # Creamos un objeto limpio
            item = {
                "id": hid,  # El ID real para la API (ej: "household_1")
                "label": f"💧 {hid}" if has_leak == 1 else hid # Lo que ve el usuario
            }
            result.append(item)
            
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
# 2. ENDPOINT PRINCIPAL (Dashboard)
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

        # 6. Asistente IA (LLM)
        ai_advice = advisor_service.generate_report(
            household_id=household_id,
            leak_data=leak_analysis,
            kpis=kpis,
            benchmark=benchmark
        )
        
        # C. Construir Respuesta JSON
        return {
            "household_id": household_id,
            "region_applied": region,
            "price_per_m3": REGIONAL_PRICES.get(region, 0),
            
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