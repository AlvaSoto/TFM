import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model
from sklearn.metrics import classification_report, roc_auc_score

#Routes configuration
#The brain of the neuronal network
MODEL_PATH = "Azure_model_new_data/resultados/Run_Ultimate/checkpoints/best_model.keras"
#The scaler remembers the Media and the Deviation of the data used for training
SCALER_PATH = "Azure_model_new_data/resultados/Run_Ultimate/results/scaler.joblib"

DATA_PATH = "../../data/mixed_population_dataset_160_households_more_leaks.csv"

#Parameters that need to be the same as those used during training
SEQUENCE_LENGTH = 96  # Number of time steps in each input sequence
STRIDE = 2

def engineer_features(df):
    print("Starting feature engineering...")
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["household_id", "timestamp"]).reset_index(drop=True)

    for col, period in [('hour',24), ('dayofweek',7)]:
        df[f'{col}_sin'] = np.sin(2 * np.pi * getattr(df['timestamp'].dt, col) / period)
        df[f'{col}_cos'] = np.cos(2 * np.pi * getattr(df['timestamp'].dt, col) / period)

    df['is_weekend'] = (df['timestamp'].dt.dayofweek >= 5).astype(int)
    df['is_night'] = df['timestamp'].dt.hour.between(0, 5, inclusive='both').astype(int)

    grouped = df.groupby("household_id", sort=False)['consumption_l']
    for window in [4, 8, 12, 24, 48, 96]:
        rolling = grouped.rolling(window=window, min_periods=1)
        rmean = rolling.mean().reset_index(level=0, drop=True)
        rstd = rolling.std().reset_index(level=0, drop=True)
        df[f"rolling_mean_{window}"] = rmean
        df[f"rolling_std_{window}"] = rstd
        df[f"rolling_cv_{window}"] = rstd / (rmean + 1e-6)
        df[f'diff_from_rolling_mean_{window}'] = df['consumption_l'] - rmean
    df.fillna(0, inplace=True)

    for lag in [96, 96*7]:
        df[f'consumption_lag_{lag}'] = grouped.shift(lag).fillna(0)

    feature_cols = [col for col in df.columns if col not in ['timestamp', 'is_leak', 'household_id']]
    return df, feature_cols

def create_sequences(df, feature_cols):
    print("Creating sequences...")
    sequences = []
    labels = []
    
    for _, group in df.groupby("household_id"):
        group = group.sort_values("timestamp")
        values = group[feature_cols].values
        leak_flags = group["is_leak"].values
        if len(group) < SEQUENCE_LENGTH:
            continue

        num_sequences = (len(group) - SEQUENCE_LENGTH) // STRIDE + 1
        starts = np.arange(num_sequences) * STRIDE
        for s in starts:
            sequences.append(values[s:s + SEQUENCE_LENGTH])
            labels.append(int(np.max(leak_flags[s:s + SEQUENCE_LENGTH])))

    return np.stack(sequences), np.array(labels, dtype=int)
    
if __name__ == "__main__":

    print(f"Loading model from {MODEL_PATH}...")
    model = load_model(MODEL_PATH)
    print(f"Loading scaler from {SCALER_PATH}...")
    scaler = joblib.load(SCALER_PATH)
    
    # --- OJO AQUÍ: Asegúrate de que este es el CSV nuevo con más fugas ---
    # Si usas el antiguo, los resultados serán peores.
    print(f"Reading data from {DATA_PATH}...") 
    df = pd.read_csv(DATA_PATH)
    
    df, cols = engineer_features(df)
    print("Scaling the data")
    df[cols] = scaler.transform(df[cols])

    #Creating the sequences
    X, y = create_sequences(df, cols)
    print(f"Total sequences generated: {len(X)}")

    # Cortar para Test (Último 10%)
    test_split_idx = int(len(X) * 0.90)
    
    X_test = X[test_split_idx:]
    y_test = y[test_split_idx:] # <--- ESTA ES LA VARIABLE CORRECTA
    
    print(f"Testing on {len(X_test)} sequences (The Test Set)...") 

    print("The model is thinking")
    reconstructions = model.predict(X_test, batch_size=512)

    mse = np.mean(np.power(X_test - reconstructions, 2), axis=(1,2))

    threshold = np.percentile(mse, 96.0)
    print(f"Anomaly detection threshold set at: {threshold:.4f}")

    #Results
    y_pred = (mse > threshold).astype(int)

    print("\n" + "="*40)
    print("Results of the local inference:")
    
    # --- CORRECCIÓN AQUÍ: Usar y_test en lugar de y ---
    print(classification_report(y_test, y_pred, target_names=["Normal", "Fuga"]))
    print(f"ROC-AUC: {roc_auc_score(y_test, mse):.4f}")
    
    # Gráfica de error
    # --- CORRECCIÓN AQUÍ TAMBIÉN ---
    plt.figure(figsize=(10, 6))
    plt.hist(mse[y_test==0], bins=50, alpha=0.5, label='Normal', density=True)
    plt.hist(mse[y_test==1], bins=50, alpha=0.5, label='Fuga', color='red', density=True)
    plt.axvline(threshold, color='k', linestyle='--', label='Umbral')
    plt.title("Distribución del Error de Reconstrucción")
    plt.legend()
    plt.show()





    