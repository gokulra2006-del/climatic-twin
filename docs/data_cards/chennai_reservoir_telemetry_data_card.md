# Data Card: Chennai Major Reservoir Hydro-Telemetry Dataset (v1.0)
**Official CMWSSB / Water Resources Department (WRD) Verified Ingestion**

---

## 1. Dataset Summary
The **Chennai Major Reservoir Hydro-Telemetry Dataset** provides official daily water levels, live storage (in Million Cubic Feet - Mcft), percentage of Full Reservoir Level (FRL), and inflow/outflow rates for the 6 primary supply and flood-attenuation reservoirs serving the Chennai Metropolitan Area:
1. **Poondi Reservoir** (Kosasthalaiyar Basin) - Capacity: 3,231 Mcft, FRL: 140.00 ft (42.67 m)
2. **Cholavaram Lake** - Capacity: 1,081 Mcft, FRL: 64.50 ft (19.66 m)
3. **Red Hills (Puzhal Lake)** - Capacity: 3,300 Mcft, FRL: 50.20 ft (15.30 m)
4. **Chembarambakkam Lake** (Adyar Basin) - Capacity: 3,645 Mcft, FRL: 85.40 ft (26.03 m)
5. **Kannankottai Thervoykandigai** - Capacity: 500 Mcft, FRL: 36.61 ft (11.16 m)
6. **Veeranam Lake** (Inter-basin supply conduit) - Capacity: 1,465 Mcft, FRL: 47.50 ft (14.48 m)
- **Combined Storage Capacity:** 13,222 Mcft

---

## 2. Ingestion & Provenance Protocol
- **Primary Source:** Chennai Metropolitan Water Supply and Sewerage Board (CMWSSB) Daily Lake Level Bulletins (`https://chennaimetrowater.tn.gov.in/lake-level.html`) and Water Resources Department (WRD) Tamil Nadu.
- **Data Source Modes:**
  - `VERIFIED_GOVERNMENT_OBSERVATION`: Direct extraction from CMWSSB daily morning bulletin (06:00 IST) or CWC Water Yearbooks.
  - `SIMULATED_APPROXIMATION`: Used only in offline test harnesses when official bulletins are unavailable.
- **Integrity Rule:** In accordance with scientific reproducibility standards, simulated or synthetic reservoir levels are **never labeled as live**. Models fed with simulated telemetry are flagged with `PROVISIONAL_PROXY_INPUT`.

---

## 3. Feature Alignment for Machine Learning
The live reservoir telemetry feeds directly into the ClimateTwin Random Forest and GNN inference engines:
- `POONDI`: Live storage volume (Mcft)
- `CHOLAVARAM`: Live storage volume (Mcft)
- `REDHILLS`: Live storage volume (Mcft)
- `CHEMBARAMBAKKAM`: Live storage volume (Mcft)
- `total_reservoir_level`: Sum of 4 primary city reservoirs (Mcft)

---

## 4. Academic Citation & Quality Assurance
When citing this dataset in peer-reviewed manuscripts:
```bibtex
@dataset{chennai_cmwssb_reservoirs_2026,
  author = {{Chennai Metropolitan Water Supply and Sewerage Board}},
  title = {Daily Water Levels and Storage of Chennai City Drinking Water Reservoirs},
  year = {2026},
  publisher = {CMWSSB, Government of Tamil Nadu},
  url = {https://chennaimetrowater.tn.gov.in}
}
```
