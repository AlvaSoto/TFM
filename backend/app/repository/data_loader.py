import pandas as pd
from pathlib import Path
from app.core.simulation_config import settings

class DataLoader:

    def __init__(self):
        print(f"Loading data from {settings.DATA_DIR}")
        self.df = pd.read_csv(settings.DATA_DIR)
        print("Data loaded successfully.")
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])

    def get_household_data(self, household_id: str) -> pd.DataFrame:
        """
        Returns the data for a specific household
        """
        data = self.df[self.df['household_id'] == household_id].copy()
        if data.empty:
            raise ValueError(f"No data found for household_id: {household_id}")
        return data.sort_values(by='timestamp').reset_index(drop=True)
    
    def get_all_household_ids(self) -> list:
        """
        Returns a list of all unique household IDs in the dataset
        """
        return self.df['household_id'].unique().tolist()
    
data_loader = DataLoader()
    
# if __name__ == "__main__":
#     data_loader = DataLoader()
#     household_ids = data_loader.get_all_household_ids()
#     print(f"Total households in dataset: {len(household_ids)}")
#     sample_id = household_ids[0]
#     sample_data = data_loader.get_household_data(sample_id)
#     print(f"Sample data for household {sample_id}:\n{sample_data.head()}")