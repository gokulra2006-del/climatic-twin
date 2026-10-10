# Coarse-to-Asset Spatial Downscaling & Uncertainty

## 1. Problem Statement
Global forecasting products (e.g., IMERG, GFS) provide rainfall arrays at incredibly coarse spatial resolutions (\times5$ km to \times25$ km). However, infrastructure impact requires asset-level precision (e.g., whether a specific 50-meter road segment will inundate).

We evaluated downscaling these coarse grids against a simulated "dense observation" ground truth field.

*⚠️ WARNING: Actual high-density rainfall radar/gauge mapping for Chennai is currently unavailable. This ablation was conducted on a strictly **SYNTHETIC** continuous 2D spatial field to demonstrate the statistical propagation technique.*

## 2. Downscaling Errors vs Distance
*(Data Source: esults/downscaling_distance_error.csv)*

We evaluated two spatial projection methods:
1.  **Nearest Pixel:** Assumes the asset experiences the exact rainfall of the encompassing coarse centroid.
2.  **IDW Interpolation (Inverse Distance Weighting):** Interpolates a blended surface from the neighboring coarse centroids.

The mean absolute error (MAE) in rainfall approximation strictly correlates with the distance from the asset to the nearest ground-truth gauge:

| Distance to Nearest Gauge | Nearest Pixel MAE | IDW Interpolation MAE |
| :--- | :--- | :--- |
| **< 2km** | 16.83 mm | 17.79 mm |
| **2-4km** | 21.32 mm | 22.26 mm |
| **> 4km** | N/A (Fully Covered) | N/A (Fully Covered) |

*Finding:* IDW smoothed the high-frequency synthetic storms too aggressively, resulting in slightly higher spatial error than simply trusting the direct localized coarse pixel. Spatial error degrades by $\approx 25\%$ when the asset is placed further than 2km from a true gauge.

## 3. Propagation to Downstream Impact
*(Data Source: esults/downscaling_overall.csv)*

How does this spatial error affect the actual binary early warning (e.g., $>120 flood threshold)?

| Method | Overall RMSE | Impact Warning F1 | 90% Interval Coverage |
| :--- | :--- | :--- | :--- |
| **Nearest Pixel** | 23.91 mm | **0.759** | N/A (Deterministic) |
| **IDW Interpolation** | 25.38 mm | 0.577 | 68.0% |

*   **Impact Warning Collapse:** The IDW smoothing dramatically reduced the ability to flag extreme asset-level threshold crossings (F1 dropped from 0.759 down to 0.577). 
*   **Uncertainty Intervals:** By propagating a .0 sub-grid variance assumption into a normal CDF, we generated probabilistic impact bounds. However, the \%$ confidence intervals only achieved **.0\%$ empirical coverage**, indicating that standard statistical variance vastly underestimates the true magnitude of sub-grid hydro-meteorological shocks. 

**Conclusion:** Using coarse grids without correcting for sub-grid variance leads to dangerously overconfident predictions. True physical radar arrays are strictly required to resolve downscaling F1 collapse.
