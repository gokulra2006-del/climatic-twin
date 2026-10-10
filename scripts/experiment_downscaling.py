import os
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.metrics import mean_squared_error, f1_score
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')

from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("Spatial_Downscaling")

def generate_spatial_field(N_assets=100, N_gauges=10):
    set_global_seed(42)
    # Domain 10km x 10km
    
    # 1. Assets and Gauges
    assets_coords = np.random.uniform(0, 10, size=(N_assets, 2))
    gauges_coords = np.random.uniform(0, 10, size=(N_gauges, 2))
    
    # 2. True Continuous Field (Rainfall)
    def true_rain(coords):
        x, y = coords[:, 0], coords[:, 1]
        # Non-linear synthetic storm
        return 100 + 40*np.sin(x) + 30*np.cos(y) + 15*np.sin(x*y/3) + np.random.normal(0, 5, len(x))
        
    assets_true_rain = true_rain(assets_coords)
    gauges_true_rain = true_rain(gauges_coords)
    
    # 3. Coarse Grid (Satellite/Reanalysis) - 2km x 2km resolution (25 cells)
    coarse_res = 2.0
    coarse_centroids = []
    coarse_vals = []
    
    for i in range(5):
        for j in range(5):
            cx, cy = i*coarse_res + 1.0, j*coarse_res + 1.0
            coarse_centroids.append([cx, cy])
            # Coarse value is roughly the true value at centroid + aggregation smoothing
            coarse_vals.append(true_rain(np.array([[cx, cy]]))[0] * 0.9) # Smoothing bias
            
    coarse_centroids = np.array(coarse_centroids)
    coarse_vals = np.array(coarse_vals)
    
    return assets_coords, assets_true_rain, gauges_coords, gauges_true_rain, coarse_centroids, coarse_vals

def downscale_nearest(assets_coords, coarse_centroids, coarse_vals):
    dists = cdist(assets_coords, coarse_centroids)
    nearest_idx = np.argmin(dists, axis=1)
    return coarse_vals[nearest_idx]

def downscale_idw(assets_coords, coarse_centroids, coarse_vals, power=2):
    dists = cdist(assets_coords, coarse_centroids)
    # Avoid division by zero
    dists[dists < 1e-6] = 1e-6
    weights = 1.0 / (dists ** power)
    weights /= weights.sum(axis=1, keepdims=True)
    return np.sum(weights * coarse_vals, axis=1)

def main():
    logger.info("Starting Coarse-to-Asset Spatial Downscaling Evaluation...")
    assets_coords, assets_true_rain, gauges_coords, gauges_true_rain, coarse_centroids, coarse_vals = generate_spatial_field()
    
    # Downscaling
    rain_nearest = downscale_nearest(assets_coords, coarse_centroids, coarse_vals)
    rain_idw = downscale_idw(assets_coords, coarse_centroids, coarse_vals)
    
    # Distance to nearest gauge for error analysis
    dists_to_gauge = np.min(cdist(assets_coords, gauges_coords), axis=1)
    
    # Errors
    err_nearest = np.abs(rain_nearest - assets_true_rain)
    err_idw = np.abs(rain_idw - assets_true_rain)
    
    # Group by distance to gauge (0-2km, 2-4km, >4km)
    dist_bins = np.digitize(dists_to_gauge, bins=[2.0, 4.0])
    bin_labels = {0: "< 2km", 1: "2-4km", 2: "> 4km"}
    
    # Impact Threshold (Hazard if Rain > 120mm)
    true_impact = (assets_true_rain > 120.0).astype(int)
    
    pred_impact_nearest = (rain_nearest > 120.0).astype(int)
    pred_impact_idw = (rain_idw > 120.0).astype(int)
    
    # Uncertainty Propagation (Assume spatial variance standard error is ~15.0mm)
    sigma_downscale = 15.0
    
    # Probability of exceeding threshold: 1 - CDF(120, mean=rain_idw, std=sigma_downscale)
    prob_impact_idw = 1.0 - norm.cdf(120.0, loc=rain_idw, scale=sigma_downscale)
    
    # 90% Confidence Interval of rainfall
    lower_90 = rain_idw - 1.645 * sigma_downscale
    upper_90 = rain_idw + 1.645 * sigma_downscale
    coverage_90 = np.mean((assets_true_rain >= lower_90) & (assets_true_rain <= upper_90))
    
    # Prepare reporting metrics
    results = []
    
    # 1. Overall Downscaling
    results.append({
        "Method": "Nearest Pixel",
        "Overall_RMSE": round(np.sqrt(mean_squared_error(assets_true_rain, rain_nearest)), 2),
        "Impact_F1": round(f1_score(true_impact, pred_impact_nearest), 3),
        "Interval_Coverage": "N/A"
    })
    results.append({
        "Method": "IDW Interpolation",
        "Overall_RMSE": round(np.sqrt(mean_squared_error(assets_true_rain, rain_idw)), 2),
        "Impact_F1": round(f1_score(true_impact, pred_impact_idw), 3),
        "Interval_Coverage": f"{coverage_90*100:.1f}%"
    })
    
    df = pd.DataFrame(results)
    
    # 2. Error vs Distance
    err_dist = []
    for b in [0, 1, 2]:
        mask = (dist_bins == b)
        err_dist.append({
            "Distance_to_Gauge": bin_labels[b],
            "Nearest_Pixel_MAE": round(np.mean(err_nearest[mask]), 2),
            "IDW_MAE": round(np.mean(err_idw[mask]), 2)
        })
    df_dist = pd.DataFrame(err_dist)
    
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\results"
    df.to_csv(os.path.join(out_dir, "downscaling_overall.csv"), index=False)
    df_dist.to_csv(os.path.join(out_dir, "downscaling_distance_error.csv"), index=False)
    
    logger.info("\n=== DOWNSCALING OVERALL ===")
    logger.info("\n" + df.to_string(index=False))
    logger.info("\n=== ERROR VS DISTANCE ===")
    logger.info("\n" + df_dist.to_string(index=False))

if __name__ == "__main__":
    main()
