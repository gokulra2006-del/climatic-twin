# ClimateTwin Multi-Hazard & Cascading Risk Report

## 1. Research Motivation
Urban climate hazards in Chennai interact to produce severe compound infrastructure risks. Torrential monsoonal precipitation interacts directly with high reservoir storage saturation, low-elevation surface runoff, and cyclonic wind gusts.

## 2. Supported Hazards & Data Sources
- **Extreme Rainfall**: NASA GPM IMERG V07B (Observed/Derived)
- **Predictive Flood Inundation**: Random Forest Model Bundle (Predicted + Conformal UQ)
- **Reservoir Hydrological Stress**: CMWSSB Water Authority Gauges (Observed/Assimilated)
- **High Wind Hazard**: NOAA ISD Station 432790 (Observed)
- **Heat Stress / Humid Heat**: NOAA ISD Station 432790 (Derived)
- **Topographic Surface Runoff**: Copernicus DEM GLO-30 (Derived)

## 3. Mathematical Formulation (Non-Linear Compound Risk Score)
$$CRS = \sum_{h} w_h S_h + \sum_{i, j} \gamma_{ij} (S_i \cdot S_j) \in [0.0, 1.0]$$

## 4. Controlled Benchmark Scenario Results
- **Scenario A (Nominal Baseline)**: CRS = 0.122 (LOW)
- **Scenario B (Heavy Rainfall)**: CRS = 0.649 (HIGH)
- **Scenario C (Rain + Full Reservoir)**: CRS = 1.000 (CRITICAL)
- **Scenario D (Extreme Super-Storm)**: CRS = 1.000 (CRITICAL)

## 5. Research Transparency & Categorization
- **OBSERVED**: Direct sensor telemetry (NASA IMERG, NOAA ISD, CMWSSB).
- **DERIVED**: Physical indices (Dew point depression, Heat index, Runoff factor).
- **MODEL-PREDICTED**: Machine learning flood probabilities with 90% prediction intervals.
- **RULE-BASED**: Non-linear compound risk scoring ($CRS$).
- **SIMULATED**: Benchmark scenarios (Scenarios A–D).
