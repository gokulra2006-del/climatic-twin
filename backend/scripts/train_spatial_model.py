import os
import sys
import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import root_mean_squared_error
import pickle
import argparse

def assemble_training_data(labels_csv=None):
    """
    Assembles training data from rainfall + DEM/terrain + observed inundation extents.
    If actual ground truth labels_csv is not provided, this script will raise an error,
    adhering to the requirement NOT to synthesize labels.
    """
    if not labels_csv or not os.path.exists(labels_csv):
        print(f"[ERROR] Ground truth data '{labels_csv}' not found.")
        print("Please provide the observed inundation extents layer (CSV/Raster) to proceed.")
        print("We do not synthesize fake labels for academic rigor.")
        sys.exit(1)
        
    print(f"Loading ground truth inundation extents from: {labels_csv}")
    df = pd.read_csv(labels_csv)
    
    # Required schema:
    # rain, runoff, flood_prob, res_fill, dem_elev, tss, hist_weight, center_lat, center_lon, compound_bonus, actual_inundation_sfii
    expected_cols = [
        "rain", "runoff", "flood_prob", "res_fill", "dem_elev", 
        "tss", "hist_weight", "center_lat", "center_lon", "compound_bonus", "actual_inundation_sfii"
    ]
    for c in expected_cols:
        if c not in df.columns:
            print(f"[ERROR] Missing required column in training data: {c}")
            sys.exit(1)
            
    return df

def train_gbt_model(df):
    print("Training Tabular Gradient Boosted Trees (GBT)...")
    
    # Spatial/Temporal holdout (simulated by splitting bottom 20% by index for time-series if sorted)
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    
    features = ["rain", "runoff", "flood_prob", "res_fill", "dem_elev", "tss", "hist_weight", "center_lat", "center_lon", "compound_bonus"]
    target = "actual_inundation_sfii"
    
    X_train, y_train = train_df[features], train_df[target]
    X_test, y_test = test_df[features], test_df[target]
    
    # Train GBT (Tabular learned model)
    model = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.05, max_depth=8, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate RMSE for depth/extent proxy
    preds = model.predict(X_test)
    rmse = root_mean_squared_error(y_test, preds)
    print(f"\n[EVALUATION] Learned GBT Model Spatial Inundation RMSE: {rmse:.4f}")
    
    # If the user also wants IoU for binary extents (SFII > 0.5):
    y_test_bin = (y_test > 0.5).astype(int)
    preds_bin = (preds > 0.5).astype(int)
    intersection = np.logical_and(y_test_bin, preds_bin).sum()
    union = np.logical_or(y_test_bin, preds_bin).sum()
    iou = intersection / union if union > 0 else 0
    print(f"[EVALUATION] Learned GBT Model Extent IoU (Threshold > 0.5): {iou:.4f}")
    
    return model

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Spatial Inundation ML Model")
    parser.add_argument("--labels", type=str, help="Path to observed inundation extents CSV")
    args = parser.parse_args()
    
    print("=== Spatial Inundation Module ML Replacement ===")
    
    df = assemble_training_data(args.labels)
    trained_model = train_gbt_model(df)
    
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "models"))
    os.makedirs(models_dir, exist_ok=True)
    out_path = os.path.join(models_dir, "spatial_gbt.pkl")
    
    with open(out_path, "wb") as f:
        pickle.dump(trained_model, f)
        
    print(f"\n[SUCCESS] Saved learned spatial model to {out_path}")
    print("To activate, set env flag: USE_LEARNED_SPATIAL_MODEL=true")
