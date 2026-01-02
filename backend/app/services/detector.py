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
        # Step 2: Data Scaling
        df_processed[cols] = self.scaler.transform(df_processed[cols])
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

        #Packing results for the frontend

        return {
            "status": "success",
            "total_sequences": len(X),
            "anomalies_detected": int(np.sum(anomalies)),
            "percentage_anomalies": round((np.sum(anomalies) / len(X)) * 100, 2),
            "mse_values": mse.tolist(),
            "threshold": threshold,
            "is_leak": bool(np.sum(anomalies) > 5)
        }
detector_service = LeakDetectorService()