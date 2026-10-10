# ClimateTwin Model Health, Drift & Retraining Intelligence Report
**Generated:** 2026-09-13T15:44:08.922970+00:00  
**Current Champion Model:** ClimateTwin-Flood-RF-v2.0  
**Model Status:** `DRIFT DETECTED`  
**Retraining Readiness Score:** `70/100` (`PREPARE CANDIDATE MODEL EVALUATION`)

---

## 1. Executive Summary & NOVA Intelligence
NOVA Environmental Drift Alert: Sustained distribution shift detected across multi-day rainfall and catchment variables. Sensor data quality is confirmed healthy. Live ground-truth flood inundation labels are currently unavailable to test concept drift. Candidate model comparison pipeline should be prepared (Readiness: 70/100).

**Scientific Retraining Decision:**
> Persistent environmental distribution drift detected across weekly and monthly horizons. Data quality remains healthy. Candidate retraining is warranted once sufficient ground-truth labels are compiled.

---

## 2. Multi-Window Temporal Drift Analysis
| Temporal Horizon | Drift Status | Aggregate PSI | Sample Size | Interpretation |
| :--- | :--- | :--- | :--- | :--- |
| **24 Hours** | `INSUFFICIENT_DATA` | 0.0 | 0 | Short-term meteorological variation |
| **7 Days** | `DRIFT DETECTED` | 8.901 | 6 | Weekly catchment state stability |
| **30 Days** | `DRIFT DETECTED` | 7.3651 | 29 | Multi-week climatic baseline shift |

**Temporal Classification:** `PERSISTENT DISTRIBUTION DRIFT`  
*Sustained distribution shift across 7-day and 30-day horizons. Environmental baseline has altered.*

---

## 3. Top Drifting Environmental Features
| Feature | Training Median | Live Median | Change (%) | PSI | KS-Stat | Severity | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `rainfall_trend` | 0.0 | 0.54 | +535897.2% | 14.508 | 0.4936 | **HIGH** | `DRIFT DETECTED` |
| `rainfall_rate_1h` | 0.0 | 1.54 | +1537499.4% | 14.5068 | 0.9898 | **HIGH** | `DRIFT DETECTED` |
| `rainfall_5d_sum` | 0.0 | 44.29 | +44292297.2% | 14.3798 | 0.9791 | **HIGH** | `DRIFT DETECTED` |
| `rainfall_7d_sum` | 0.0 | 95.96 | +95961176.5% | 14.3197 | 0.9845 | **HIGH** | `DRIFT DETECTED` |
| `reservoir_storage_rate_1d` | 0.0 | 26.95 | +26948970.2% | 11.5099 | 0.6909 | **HIGH** | `DRIFT DETECTED` |

---

## 4. Prediction Distribution & Uncertainty Drift
- **Historical Median Output Probability:** 0.0441
- **Recent Live Median Output Probability:** 0.0649
- **Probability Shift:** +0.0209
- **Prediction Drift Severity:** `HIGH`
- **Epistemic Variance (Ensemble Dispersion):** 0.00757
- **Prediction Interval Width:** 0.1200
- **Model Confidence Condition:** `STABLE CONFIDENCE`

---

## 5. Telemetry & Data Quality Gating (Phase 16 Integration)
- **Telemetry State:** `NOMINAL` (Aggregate SHS: 0.95)
- **Degraded Telemetry Sources:** 0
- **Anomalous Telemetry Sources:** 0
- **Diagnostic Result:** All primary environmental telemetry sources reporting valid physical ranges.

---

## 6. Concept Drift Safeguard
- **Status:** `NOT YET EVALUABLE — LIVE GROUND-TRUTH LABELS UNAVAILABLE`
- **Methodology Rationale:** Calculating concept drift from model predictions alone confuses feature/prediction drift with concept drift.
- Verified ground-truth post-inundation survey labels are required to decouple P(Y|X) concept shifts from P(X) covariate shifts.

---

## 7. Champion vs Candidate Model Registry
- **Deployed Champion:** `ClimateTwin-Flood-RF-v2.0`
  - Algorithm: Calibrated Random Forest Classifier (Platt Sigmoid)
  - ROC-AUC: 0.9014 | PR-AUC: 0.0539 | Brier: 0.0197
- **Evaluated Candidate:** `ClimateTwin-Flood-HGB-v2.1`
  - Algorithm: HistGradientBoosting Classifier (Calibrated)
  - ROC-AUC: 0.8842 | PR-AUC: 0.0482 | Brier: 0.0221
- **Safe Retraining Policy:** Automated model replacement is prohibited. Candidate models must demonstrate superior PR-AUC and Brier Score on chronological holdouts before deployment.
