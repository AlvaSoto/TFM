import pandas as pd
from pathlib import Path
from app.core.simulation_config import settings

class DataLoader:
    """
    Sirve datos de dos orígenes de forma transparente:
      - Dataset sintético (CSV, demo): cargado en memoria al arrancar.
      - Contadores REALES del piloto (SQLite via readings_store): consultados
        bajo demanda. Un contador ingerido por la API aparece en la consola
        exactamente igual que uno simulado.
    """

    def __init__(self):
        print(f"Loading data from {settings.DATA_DIR}")
        self.df = pd.read_csv(settings.DATA_DIR)
        print("Data loaded successfully.")
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])

    def _store(self):
        # Import perezoso para evitar ciclos en el arranque
        from app.repository.readings_store import readings_store
        return readings_store

    def get_household_data(self, household_id: str) -> pd.DataFrame:
        """
        Returns the data for a specific household/meter (piloto primero, luego demo)
        """
        pilot = self._store().get_meter_df(household_id)
        if not pilot.empty:
            return pilot.sort_values(by='timestamp').reset_index(drop=True)

        data = self.df[self.df['household_id'] == household_id].copy()
        if data.empty:
            raise ValueError(f"No data found for household_id: {household_id}")
        return data.sort_values(by='timestamp').reset_index(drop=True)

    def get_all_household_ids(self) -> list:
        """
        Returns all unique IDs: contadores reales del piloto + dataset demo
        """
        pilot_ids = self._store().meter_ids()
        demo_ids = self.df['household_id'].unique().tolist()
        return pilot_ids + [d for d in demo_ids if d not in pilot_ids]
    
data_loader = DataLoader()
    
# if __name__ == "__main__":
#     data_loader = DataLoader()
#     household_ids = data_loader.get_all_household_ids()
#     print(f"Total households in dataset: {len(household_ids)}")
#     sample_id = household_ids[0]
#     sample_data = data_loader.get_household_data(sample_id)
#     print(f"Sample data for household {sample_id}:\n{sample_data.head()}")