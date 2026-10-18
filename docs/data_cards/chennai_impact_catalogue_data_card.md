# Data Card: Chennai Urban Historical Impact Catalogue (v1.0)

## 1. Overview & Provenance
The **Chennai Urban Historical Impact Catalogue** is a curation-ready workspace for spatial and temporal impact records within Greater Chennai Corporation (GCC) administrative limits. The bundled records are synthetic demonstrations; they must not be treated as verified incident evidence.

- **Primary Geolocation:** Greater Chennai ($12.85^\circ\text{N} - 13.25^\circ\text{N}$, $80.00^\circ\text{E} - 80.35^\circ\text{E}$).
- **Temporal Coverage:** Curation target: 2015 to present. No bundled demonstration record establishes coverage of a real event.
- **Curator:** ClimateTwin Urban Research Platform.
- **Data Version:** 0.1.0-demo; replace bundled records with independently verified source records before evaluation.

---

## 2. Evidence Status Taxonomy & Strict Labelling
To prevent academic overclaiming, all records in the catalogue are explicitly tagged with one of four evidence statuses:

| Evidence Status | Definition | Example Source |
| :--- | :--- | :--- |
| `historical_real` | Direct empirical measurement or documented government commission audit report. | NDMA 2015 Audit Report, TN PWD Sluice Gate Log. |
| `proxy` | Inferred from correlated municipal operations or public utility outage feeds. | TANGEDCO feeder tripping log, CMWSSB supply bulletin. |
| `synthetic` | Computationally generated using physical threshold rules for stress-testing. | Synthetic hydrodynamic threshold exceedance. |
| `unverified` | Citizen report or news wire report lacking official engineering coordinates. | Social media SOS coordinates during cyclone landfall. |

---

## 3. Allowed Impact Types
1. `waterlogging`: Surface inundation >150 mm causing vehicular stalling.
2. `road_closure`: Complete arterial impassability verified by traffic police or satellite imagery.
3. `flood_extent`: Multi-hectare contiguous overland flooding.
4. `reservoir_overflow`: Sluice gate emergency discharge or embankment overtopping.
5. `power_outage`: Substation inundation or preventative high-voltage feeder trip.
6. `hospital_access_disruption`: Road access severed to tertiary medical centers.
7. `drainage_failure`: Siltation, pump lift station mechanical failure, or tidal lock.

---

## 4. Known Biases & Missingness
- **Reporting Bias:** Historical documentation is heavily skewed toward South Chennai (Adyar, Velachery, OMR) due to higher density of tech corridors and media coverage. North Chennai zones (Tondiarpet, Manali) historically exhibit higher missingness in digitized municipal archives.
- **Temporal Granularity:** Event start times derived from municipal press briefings may have a $\pm 2\text{ hour}$ reporting lag relative to physical hydrological onset.

---

## 5. Usage Policy & License
- **Permitted Use:** Academic evaluation, research benchmarking, and digital twin warning verification.
- **Prohibited Use:** Direct real-time civil defense evacuation orders without independent field confirmation.
- **License:** Open Database License (ODbL) for public municipal records; CC-BY-NC 4.0 for curated metadata.
