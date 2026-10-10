import pandas as pd
import numpy as np
import os
import pickle
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix

def train_model():
    print("Starting EDA & Model Training script...")
    base_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin"
    processed_dir = os.path.join(base_dir, "data", "processed")
    models_dir = os.path.join(base_dir, "backend", "app", "models")
    os.makedirs(models_dir, exist_ok=True)
    
    # 1. Load Datasets
    print("Loading datasets...")
    df_events = pd.read_csv(os.path.join(processed_dir, "flood_events", "chennai_flood_events.csv"))
    df_imerg = pd.read_csv(os.path.join(processed_dir, "rainfall", "imerg_chennai_daily.csv"))
    df_reservoirs = pd.read_csv(os.path.join(processed_dir, "water_level", "cmwssb_reservoir_levels.csv"))
    df_noaa = pd.read_csv(os.path.join(processed_dir, "weather", "noaa_isd_chennai_hourly.csv"))
    
    # 2. Parse Datetime Indexes
    df_imerg['time'] = pd.to_datetime(df_imerg['time'])
    df_imerg.set_index('time', inplace=True)
    
    df_reservoirs['date_standard'] = pd.to_datetime(df_reservoirs['date_standard'])
    # Aggregate duplicate dates (e.g. redundant listings)
    df_reservoirs = df_reservoirs.groupby('date_standard')[['POONDI', 'CHOLAVARAM', 'REDHILLS', 'CHEMBARAMBAKKAM']].mean()
    
    df_noaa['DATE'] = pd.to_datetime(df_noaa['DATE'])
    df_noaa.set_index('DATE', inplace=True)
    df_noaa_daily = df_noaa.resample('1D').agg({
        'temperature_c': ['mean', 'max', 'min'],
        'dew_point_c': 'mean',
        'wind_speed_ms': 'mean'
    })
    # Flatten multi-index columns
    df_noaa_daily.columns = ['temp_mean', 'temp_max', 'temp_min', 'dew_point_mean', 'wind_speed_mean']
    
    # 3. Create Target Variable (Is active flood date?)
    print("Engineering target variable...")
    # Get all date range intervals
    intervals = []
    for _, row in df_events.iterrows():
        try:
            start = pd.to_datetime(row['Start Date'])
            end = pd.to_datetime(row['End Date'])
            if pd.notna(start) and pd.notna(end):
                intervals.append((start, end))
        except Exception:
            continue
            
    # Combine IMERG and NOAA and Reservoir data into a single timeframe DataFrame
    start_date = max(df_imerg.index.min(), df_noaa_daily.index.min(), df_reservoirs.index.min())
    end_date = min(df_imerg.index.max(), df_noaa_daily.index.max(), df_reservoirs.index.max())
    print(f"Overlapping data range: {start_date.date()} to {end_date.date()}")
    
    date_range = pd.date_range(start_date, end_date, freq='D')
    features = pd.DataFrame(index=date_range)
    
    # Map target: 1 if date falls inside any flood interval, 0 otherwise
    is_flood = np.zeros(len(date_range))
    for i, dt in enumerate(date_range):
        for start, end in intervals:
            if start <= dt <= end:
                is_flood[i] = 1.0
                break
    features['flood_active'] = is_flood
    
    # 4. Align & Engineer Features
    print("Aligning features and engineering rolling indices...")
    # Add IMERG features
    features['rainfall_daily'] = df_imerg['precipitation_mm_hr']  # Already daily sum from processing script (which scaled hourly rate * 24)
    # Add rolling sums for rainfall (standard indicators for waterlogging / antecedent moisture)
    features['rainfall_3d_sum'] = features['rainfall_daily'].rolling(3, min_periods=1).sum()
    features['rainfall_5d_sum'] = features['rainfall_daily'].rolling(5, min_periods=1).sum()
    features['rainfall_7d_sum'] = features['rainfall_daily'].rolling(7, min_periods=1).sum()
    
    # Add NOAA weather features
    features = features.join(df_noaa_daily, how='left')
    
    # Add Reservoir level features
    features = features.join(df_reservoirs, how='left')
    
    # Fill any missing values with forward fill or zero
    features.ffill(inplace=True)
    features.bfill(inplace=True)
    
    # Total reservoir levels sum
    features['total_reservoir_level'] = features[['POONDI', 'CHOLAVARAM', 'REDHILLS', 'CHEMBARAMBAKKAM']].sum(axis=1)
    
    print("Engineered Feature Columns:", list(features.columns))
    print(f"Total samples: {len(features)}. Flood positive days: {int(features['flood_active'].sum())}")
    
    # 5. Model Training
    print("Training predictive classifier model...")
    X = features.drop(columns=['flood_active'])
    y = features['flood_active']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    rf.fit(X_train, y_train)
    
    # Eval
    preds = rf.predict(X_test)
    probs = rf.predict_proba(X_test)[:, 1]
    
    print("\n--- Model Evaluation Results ---")
    print(classification_report(y_test, preds))
    print("ROC-AUC Score:", roc_auc_score(y_test, probs))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, preds))
    
    # Feature importances
    importances = pd.DataFrame({
        'Feature': X.columns,
        'Importance': rf.feature_importances_
    }).sort_values('Importance', ascending=False)
    print("\nFeature Importances:")
    print(importances)
    
    # 6. Save Model Weights
    model_path = os.path.join(models_dir, "flood_rf_model.pkl")
    with open(model_path, 'wb') as f_out:
        pickle.dump({
            'model': rf,
            'features': list(X.columns),
            'eval_roc_auc': roc_auc_score(y_test, probs)
        }, f_out)
    print(f"\nModel successfully saved to {model_path}")

if __name__ == "__main__":
    train_model()
