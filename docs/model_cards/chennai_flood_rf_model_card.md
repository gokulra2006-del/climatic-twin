# Model Card: Chennai Flood Risk Classifier (Random Forest v2)
**Conference & Journal Submission Documentation (NeurIPS / Nature Climate Change Standard)**

---

## 1. Model Details
- **Architecture:** Random Forest Ensemble Classifier (Scikit-Learn, 100 Estimators, Max Depth 10)
- **Model Version:** `Chennai_Flood_RF_v2`
- **Trained Split Date:** Chronological Event Split (`2021-12-31`)
  - Train: 1980-01-01 to 2021-12-31 (Historical Monsoons, including 2015 extreme rainfall events)
  - Test / Hindcast: 2022-01-01 to 2024-12-31 (including Cyclone Michaung Dec 2023)
- **Features (14 Aligned Variables):**
  - Atmospheric (9): `rainfall_daily`, `rainfall_3d_sum`, `rainfall_5d_sum`, `rainfall_7d_sum`, `temp_mean`, `temp_max`, `temp_min`, `dew_point_mean`, `wind_speed_mean`
  - Hydro-Reservoir (5): `POONDI`, `CHOLAVARAM`, `REDHILLS`, `CHEMBARAMBAKKAM`, `total_reservoir_level`

---

## 2. Scientific Integrity & Publication Notice
> [!IMPORTANT]
> **Distinction Between Retrospective Demonstration vs Generalized Empirical Proof:**
> Historical hindcasts (e.g. 12 retrospective disaster events) yield high retrospective concordance (e.g. 81.8% precision / 75.0% recall). However, because warning thresholds were calibrated in post-hoc analysis near known events, these figures represent a **RETROSPECTIVE DEMONSTRATION & BENCHMARK**, not prospective, out-of-sample operational proof.
> 
> True empirical claims require:
> 1. Prospective real-time shadow execution without manual threshold seeding.
> 2. Independent source-verified ground-truth events ($N \ge 30$).
> 3. Observed satellite SAR inundation extent or CWC gauge depth points.

---

## 3. Uncertainty Quantification
The model couples point probability estimates with a **Conformal Prediction Interval Engine**:
- **Confidence Level:** 90% Conformal Coverage ($\alpha = 0.10$)
- **Prediction Interval:** $[\hat{p} - 1.645 \cdot \sigma, \hat{p} + 1.645 \cdot \sigma]$ bounded in $[0.0, 1.0]$
- **Epistemic Uncertainty:** Monitored via ensemble variance across trees
- **Aleatoric Uncertainty:** Monitored via input sensor quality score (SHS)

---

## 4. Retraining & Drift Safeguards
- **Population Stability Index (PSI):**
  - $\text{PSI} < 0.10$: Healthy, no action.
  - $0.10 \le \text{PSI} < 0.25$: Warning, trigger feature inspection.
  - $\text{PSI} \ge 0.25$: Drift detected; quarantine model and evaluate candidate architecture.
- **Concept Drift:** Explicitly evaluated only against verified ground-truth labels.

---

## 5. Academic Citation
```bibtex
@article{climatetwin_chennai_rf2026,
  title = {Evidence-Grounded Urban Climate Digital Twins: Hydro-Meteorological Machine Learning with Rigorous Provenance},
  author = {ClimateTwin Research Group},
  journal = {Urban Climate & Environmental Modelling},
  year = {2026}
}
```
