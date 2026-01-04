import numpy as np
import pandas as pd
import joblib
from tensorflow.keras.models import load_model
from app.core.simulation_config import settings
from typing import Dict, List, Sequence, Tuple

class LeakDetectorService:
    def __init__(self):
        # Load the pre-trained model
        print(f"Loading model from {settings.MODELS_DIR}")
        #This is the trained LSTM Autoencoder model THE BRAIN
        self.model = load_model(settings.MODELS_DIR)
        print("Model loaded successfully.")
        
        # Load the scaler
        print(f"Loading scaler from {settings.SCALER_PATH}")
        # This is the translator that normalises the data before feeding it to the model
        self.scaler = joblib.load(settings.SCALER_PATH)
        print("Scaler loaded successfully.")

        # The brain works with sequences of data, so we define the length of the blocks of data the model will process
        self.sequence_length = 96  # Assuming 15-min intervals over 24 hours 96=4*24
        self.stride = 4

    def _engineer_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        print("Starting feature engineering")
        df = data.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values(["household_id", "timestamp"]).reset_index(drop=True)

        for col, period in [('hour', 24), ('dayofweek', 7)]:
            df[f'{col}_sin'] = np.sin(2 * np.pi * getattr(df['timestamp'].dt, col) / period)
            df[f'{col}_cos'] = np.cos(2 * np.pi * getattr(df['timestamp'].dt, col) / period)

        df['is_weekend'] = (df['timestamp'].dt.dayofweek >= 5).astype(int)
        # is_night: periodo donde suele haber fugas silenciosas (00:00 - 05:00)
        df['is_night'] = df['timestamp'].dt.hour.between(0, 5, inclusive="both").astype(int)

        grouped = df.groupby("household_id", sort=False)['consumption_l']

        # Ventanas Deslizantes (Captura tendencias y variabilidad)
        for window in [4, 8, 12, 24, 48, 96]:
            rolling = grouped.rolling(window=window, min_periods=1)
            rmean = rolling.mean().reset_index(level=0, drop=True)
            rstd = rolling.std().reset_index(level=0, drop=True)
            
            df[f"rolling_mean_{window}"] = rmean
            df[f"rolling_std_{window}"] = rstd
            df[f"rolling_cv_{window}"] = rstd / (rmean + 1e-6) # Coeficiente de variación
            df[f'diff_from_rolling_mean_{window}'] = df['consumption_l'] - rmean
            
        df.fillna(0, inplace=True)

        # Lags (Comparación con ayer y la semana pasada)
        for lag in [96, 96*7]:
            df[f'consumption_lag_{lag}'] = grouped.shift(lag).fillna(0)
        
        feature_cols = [col for col in df.columns if col not in ['timestamp', 'is_leak', 'household_id']]
        return df, feature_cols

    def _create_sequences(self, values):
        """
        Creating sequences with a defined length and stride for the LSTM model

        """

        sequences = []
        if len(values) < self.sequence_length:
            return np.array([])
        
        num_seq = (len(values) - self.sequence_length) // self.stride + 1
        for i in range(num_seq):
            start = i * self.stride
            end = start + self.sequence_length
            sequences.append(values[start:end])

        return np.array(sequences)
    
    def analyse_household(self, df_raw: pd.DataFrame):

        """
        Process the data for a single household and return  the predicted leak probabilities
        """

        # Step 1: Feature Engineering
        df_processed, cols = self._engineer_features(df_raw)
        # Keeping the timestamps to know when the anomalies happen
        timestamps = df_processed['timestamp'].values
        # Step 2: Data Scaling
        try:
            df_processed[cols] = self.scaler.transform(df_processed[cols])
        except Exception as e:
            return {"error": f"Scaling error: {str(e)}"}
        # Step 3: Create Sequences
        X = self._create_sequences(df_processed[cols].values)

        if len(X) == 0:
            return {"error": "Not enough data to create sequences. WE NEED AT LEAST 96 records(24h)."}
        
        # Step 4: Predict Leak Probabilities
        reconstructions = self.model.predict(X, verbose=0)
        mse = np.mean(np.power(X - reconstructions, 2), axis=(1,2))

        # Step 5: Detection (thresholding p96)
        threshold = settings.LEAK_THRESHOLD
        anomalies = (mse > threshold).astype(int)

        # Extracting which days have anomalies
        anomalous_dates = set()
        bad_indexes = np.where(anomalies == 1)[0]
        for idx in bad_indexes:
            # idx * stride + sequence_lenght -1 gives the index of the last timestamp in the sequence
            ts_index = idx * self.stride + self.sequence_length - 1
            if ts_index < len(timestamps):
                date_str = pd.to_datetime(timestamps[ts_index]).strftime("%Y-%m-%d")
                anomalous_dates.add(date_str)

        #Converting it into a sorted list
        sorted_anomalous_dates = sorted(list(anomalous_dates))

        #Calculating star/end dates for the LLM
        start_date = sorted_anomalous_dates[0] if sorted_anomalous_dates else None
        end_date = sorted_anomalous_dates[-1] if sorted_anomalous_dates else None

        num_anomalies = int(np.sum(anomalies))
        total_sequences = len(X)
        percentage_anomalies = round((num_anomalies / total_sequences) * 100, 2)
        is_leak = bool(num_anomalies > 5)  # If more than 5 anomalous sequences, flag as leak

        #Extracting leak details for the LLM
        leak_details = {
            "worst_date": None,
            "duration_hours": 0,
            "max_error": 0.0
        }

        if is_leak:
            #A. Find the moment with highest error
            max_error_index = np.argmax(mse)
            leak_details["max_error"] = round(float(mse[max_error_index]),2)

            #mapping the sequence index back to timestamp
            # The sequence 'i' ends in the index: i * stride + sequence_length - 1
            timestamps_idx = max_error_index * self.stride + self.sequence_length - 1
            if timestamps_idx < len(timestamps):
                #Convert to readable date
                date_val = pd.to_datetime(timestamps[timestamps_idx])
                leak_details["worst_date"] = date_val.strftime("%Y-%m-%d %H:%M")
            
            #B. Calculate estimated duration of the leak
            # Each anomaly detected is a window. As i use a stride of 4, each anomaly represents 1 hour of data (4 * 15min)
            # num_anomalies * 1 hour is a good estimation of the leak duration
            leak_details["duration_hours"] = num_anomalies


        #Packing results for the frontend

        return {
            "total_sequences_analyzed": total_sequences,
            "anomalies_detected": num_anomalies,
            "percentage_anomalies": percentage_anomalies,
            "mse_values": mse.tolist(),
            "threshold_used": threshold,
            "is_leak_detected": is_leak,
            "leak_details": leak_details,
            "anomalous_days": sorted_anomalous_dates,
            "leak_period": {
                "start": start_date,
                "end": end_date
            }
        }
detector_service = LeakDetectorService()