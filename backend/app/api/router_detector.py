from fastapi import APIRouter, HTTPException
from app.repository.data_loader import data_loader
from app.services.detector import detector_service  

router = APIRouter()

@router.get("/households")
def list_households():
    """
    Endpoint to list all household IDs in the dataset
    """
    try:
        household_ids = data_loader.get_all_household_ids()
        return {"household_ids": household_ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/analyse/{household_id}")
def analyse_household(household_id: str):
    """
    1. Seek for the household data in the dataset
    2. Process the data through the LeakDetectorService
    3. Return the analysis results
    """
    try:
        df = data_loader.get_household_data(household_id)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for household_id: {household_id}")
        result = detector_service.analyse_household(df)
        return {
            "household_id": household_id,
            "analysis_result": result,
            "raw_data": df[["timestamp", "consumption_l"]].to_dict(orient="records")
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))