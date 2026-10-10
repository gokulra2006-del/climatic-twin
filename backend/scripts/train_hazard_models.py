import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Ensure models directory exists
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

N_SAMPLES = 5000
np.random.seed(42)

def generate_heatwave_data():
    """Generates synthetic data for heatwave based on Max Temp and Mean Temp."""
    temp_max = np.random.uniform(25.0, 48.0, N_SAMPLES)
    temp_mean = temp_max - np.random.uniform(2.0, 10.0, N_SAMPLES)
    dew_point = np.random.uniform(15.0, 28.0, N_SAMPLES)
    
    # Label logic based on prototypes
    labels = []
    for t_max, t_mean in zip(temp_max, temp_mean):
        prob = 0.0
        if t_max > 36.0: prob += 0.3
        if t_max > 39.0: prob += 0.3
        if t_max > 41.0: prob += 0.3
        if t_mean > 33.0: prob += 0.1
        
        # Introduce slight noise for realism
        prob += np.random.normal(0, 0.05)
        labels.append(1 if prob >= 0.5 else 0)
        
    return pd.DataFrame({
        'temp_max': temp_max,
        'temp_mean': temp_mean,
        'dew_point': dew_point
    }), np.array(labels)

def generate_drought_data():
    """Generates synthetic data for drought based on 90-day cumulative rainfall."""
    rain_90d = np.random.uniform(0.0, 800.0, N_SAMPLES)
    temp_mean_90d = np.random.uniform(26.0, 35.0, N_SAMPLES)
    
    labels = []
    baseline_90d = 300.0
    for r in rain_90d:
        deficit_ratio = max(0.0, 1.0 - (r / baseline_90d))
        prob = min(1.0, max(0.0, deficit_ratio * 1.2))
        prob += np.random.normal(0, 0.05)
        labels.append(1 if prob >= 0.5 else 0)
        
    return pd.DataFrame({
        'rain_90d': rain_90d,
        'temp_mean_90d': temp_mean_90d
    }), np.array(labels)

def generate_wildfire_data():
    """Generates synthetic data for wildfire based on temp, rain, and wind."""
    temp_max = np.random.uniform(25.0, 45.0, N_SAMPLES)
    rain_30d = np.random.uniform(0.0, 300.0, N_SAMPLES)
    wind_speed = np.random.uniform(1.0, 15.0, N_SAMPLES)
    
    labels = []
    for t, r, w in zip(temp_max, rain_30d, wind_speed):
        prob = 0.0
        if t > 35.0: prob += 0.4
        if r < 50.0: prob += 0.4
        if w > 5.0: prob += 0.2
        prob += np.random.normal(0, 0.05)
        labels.append(1 if prob >= 0.5 else 0)
        
    return pd.DataFrame({
        'temp_max': temp_max,
        'rain_30d': rain_30d,
        'wind_speed': wind_speed
    }), np.array(labels)

def generate_extreme_rain_data():
    """Generates synthetic data for extreme rainfall based on daily rain and dew point."""
    rain_daily = np.random.uniform(0.0, 300.0, N_SAMPLES)
    dew_point = np.random.uniform(15.0, 28.0, N_SAMPLES)
    
    labels = []
    for r, d in zip(rain_daily, dew_point):
        prob = 0.0
        if r > 64.5: prob += 0.5
        if r > 115.5: prob += 0.3
        if r > 204.5: prob += 0.2
        if d > 24.0: prob += 0.1
        prob += np.random.normal(0, 0.05)
        labels.append(1 if prob >= 0.5 else 0)
        
    return pd.DataFrame({
        'rain_daily': rain_daily,
        'dew_point': dew_point
    }), np.array(labels)

def train_and_save_model(X, y, model_name):
    print(f"\\n--- Training {model_name} ---")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    clf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_test)
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred, zero_division=0))
    
    model_path = os.path.join(MODELS_DIR, f"{model_name}_rf_model.pkl")
    with open(model_path, 'wb') as f:
        pickle.dump(clf, f)
    print(f"Saved {model_path}")

if __name__ == "__main__":
    print("Starting ML Model Generation for ClimateTwin Hazards...")
    
    # 1. Heatwave
    X_heatwave, y_heatwave = generate_heatwave_data()
    train_and_save_model(X_heatwave, y_heatwave, "heatwave")
    
    # 2. Drought
    X_drought, y_drought = generate_drought_data()
    train_and_save_model(X_drought, y_drought, "drought")
    
    # 3. Wildfire
    X_wildfire, y_wildfire = generate_wildfire_data()
    train_and_save_model(X_wildfire, y_wildfire, "wildfire")
    
    # 4. Extreme Rainfall
    X_extreme_rain, y_extreme_rain = generate_extreme_rain_data()
    train_and_save_model(X_extreme_rain, y_extreme_rain, "extreme_rain")
    
    print("\\nAll models generated successfully!")
