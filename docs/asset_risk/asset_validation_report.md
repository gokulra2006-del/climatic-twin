# ClimateTwin Phase 14: Asset-Level Infrastructure Risk & Vulnerability Report

## 1. Research Motivation
Hazard predictions are operationally actionable only when tied to specific urban infrastructure assets. Phase 14 connects compound hazard states to **8 verified critical infrastructure assets** across Greater Chennai.

## 2. Mandatory Methodological Distinction
- **Hazard ($H$)**: Environmental intensity (from Phase 13 $CRS$).
- **Exposure ($E$)**: Geographic and hydrological catchment proximity.
- **Vulnerability Proxy ($V_{\text{proxy}}$)**: Topographic depression ($<10\text{m}$) and structural type sensitivity.
- **Criticality ($C$)**: Systemic urban societal importance.

$$ARI = H \cdot 0.35 + E \cdot 0.30 + V_{\text{proxy}} \cdot 0.20 + C \cdot 0.15 + \text{Cascade Bonus} \in [0.0, 1.0]$$

## 3. Prioritized Action Queue (Deluge Benchmark)
1. **Adyar River Coastal Outfall & Estuary**: ARI = 1.000 [CRITICAL] &bull; Elev: 0.0m
2. **Napier Bridge & Coastal Arterial**: ARI = 0.898 [CRITICAL] &bull; Elev: 5.1m
3. **Redhills Reservoir (Puzhal Lake)**: ARI = 0.816 [CRITICAL] &bull; Elev: 16.3m

## 4. Research Transparency & Categorization
- **OBSERVED**: NASA IMERG rainfall, CMWSSB storage levels, NOAA ISD weather.
- **DERIVED**: Copernicus DEM 30m elevations, normalized exposure indices.
- **MODEL-PREDICTED**: Random Forest flood probabilities & multi-horizon forecasts.
- **RULE-BASED**: Criticality weights & operational decision support actions.
- **TRANSPARENT PROXY**: Topographic vulnerability proxy ($V_{\text{proxy}}$).
