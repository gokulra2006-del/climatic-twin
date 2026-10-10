# ClimateTwin Phase 15 — Spatial Flood Inundation & Impact Mapping Report

## Executive Summary
Phase 15 connects NASA IMERG precipitation, ERA5-Land runoff, Copernicus DEM GLO-30 terrain, and Phase 10-14 machine learning & asset vulnerability into a spatially explicit **Flood Susceptibility Index (FSI)** and **Spatial Flood Impact Index (SFII)**.

## Monitored Spatial Catchment Zones

| Zone_ID | Zone_Name | Catchment | Center_Lat | Center_Lon | DEM_Elevation_m | Drainage_Outlet | Urban_Density | Historical_Vuln | Intersecting_Critical_Assets |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ZONE_ADYAR_ESTUARY | Coastal Adyar Estuary & Lowland Plain | Adyar River Basin | 13.01 | 80.25 | 14.6 | Bay of Bengal (Adyar Mouth) | HIGH | VERY_HIGH | ADYAR_OUTFALL, NAPIER_BRIDGE |
| ZONE_COOUM_CORRIDOR | Central Cooum River Urban Basin | Cooum River Basin | 13.075 | 80.245 | 8.3 | Bay of Bengal (Cooum Mouth) | CRITICAL | HIGH | CENTRAL_SUBSTATION, KILPAUK_WTP |
| ZONE_KOSASTHALAIYAR_NORTH | Northern Kosasthalaiyar & Puzhal Basin | Kosasthalaiyar River Basin | 13.18 | 80.17 | 13.0 | Ennore Creek | MODERATE | MODERATE | REDHILLS, CHOLAVARAM |
| ZONE_CHEMBARAMBAKKAM_UPSTREAM | Western Chembarambakkam Reservoir Headwaters | Adyar Upper Catchment | 13.0116 | 80.05 | 21.0 | Adyar Spillway Channel | MODERATE | HIGH_SURGE | CHEMBARAMBAKKAM |
| ZONE_POONDI_UPLANDS | Northwestern Poondi Headwaters & Uplands | Kosasthalaiyar Headwaters | 13.185 | 79.86 | 40.5 | Kosasthalaiyar River | LOW | LOW_SURFACE_POOLING | POONDI |
| ZONE_SOUTH_COASTAL_VELACHERY | South Chennai Pallikaranai & Velachery Basin | Pallikaranai Marshland Catchment | 12.96 | 80.22 | 5.3 | Buckingham Canal & Kovalam Estuary | CRITICAL | CRITICAL | ADYAR_OUTFALL |
| ZONE_NORTH_INDUSTRIAL_MANALI | North Chennai Industrial & Ennore Littoral | Buckingham Canal North Catchment | 13.2 | 80.29 | 0.5 | Ennore Estuary | HIGH | HIGH | CHOLAVARAM |
| ZONE_SOUTHWEST_TAMBARAM | Southwestern Tambaram & Guindy Urban Foothills | Adyar Middle Tributaries | 12.94 | 80.13 | 28.9 | Adyar Middle Reach | HIGH | MODERATE | CHEMBARAMBAKKAM |

## Scientific Data Provenance
- **OBSERVED**: NASA GPM IMERG V07B precipitation, CMWSSB reservoir storage.
- **SATELLITE / REANALYSIS-DERIVED**: ERA5-Land surface runoff index.
- **DERIVED**: Copernicus DEM 30m terrain susceptibility, proximity to drainage waterways.
- **MODEL-PREDICTED**: ML Random Forest flood probability & multi-horizon progression.
- **PROXY**: Relative Inundation Severity Class (LOW, MODERATE, HIGH, SEVERE). Physical water depth is NOT DIRECTLY OBSERVED.
- **RULE-BASED**: Systemic criticality and priority action policies.
