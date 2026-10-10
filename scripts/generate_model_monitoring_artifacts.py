"""
Generate Research Artifacts, Plots & Documentation for Model Drift & Monitoring (Phase Next)
ClimateTwin Chennai Project
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

base_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin"
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from backend.app.core.model_monitoring import model_monitoring_engine

def generate_artifacts():
    print("=== Generating Model Drift & Monitoring Research Artifacts ===")
    
    docs_monitoring_dir = os.path.join(base_dir, "docs", "model_monitoring")
    plots_dir = os.path.join(base_dir, "docs", "plots")
    os.makedirs(docs_monitoring_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)
    
    health = model_monitoring_engine.get_comprehensive_model_health("7d")
    
    # 1. feature_drift_results.json
    f_path = os.path.join(docs_monitoring_dir, "feature_drift_results.json")
    with open(f_path, "w") as f:
        json.dump({
            "generated_at": health["timestamp"],
            "window": "7d",
            "aggregate_psi": health["feature_drift"]["aggregate_psi"],
            "status": health["feature_drift"]["status"],
            "top_drifting_features": health["feature_drift"]["top_drifting_features"],
            "all_features": health["feature_drift"]["all_features"]
        }, f, indent=2)
    print("Saved feature_drift_results.json")
    
    # 2. prediction_drift_results.json
    p_path = os.path.join(docs_monitoring_dir, "prediction_drift_results.json")
    with open(p_path, "w") as f:
        json.dump({
            "generated_at": health["timestamp"],
            "prediction_drift": health["prediction_drift"],
            "concept_drift": health["concept_drift"]
        }, f, indent=2)
    print("Saved prediction_drift_results.json")
    
    # 3. retraining_readiness.json
    r_path = os.path.join(docs_monitoring_dir, "retraining_readiness.json")
    with open(r_path, "w") as f:
        json.dump({
            "generated_at": health["timestamp"],
            "retraining_readiness": health["retraining_readiness"],
            "temporal_drift": health["temporal_drift"],
            "data_quality_gate": health["data_quality"],
            "uncertainty": health["uncertainty_trend"]
        }, f, indent=2)
    print("Saved retraining_readiness.json")
    
    # 4. model_registry.json
    m_path = os.path.join(docs_monitoring_dir, "model_registry.json")
    with open(m_path, "w") as f:
        json.dump({
            "champion_model": health["champion_model"],
            "candidate_model": health["candidate_model"]
        }, f, indent=2)
    print("Saved model_registry.json")
    
    # 5. model_health_report.md
    report_path = os.path.join(docs_monitoring_dir, "model_health_report.md")
    report_content = f"""# ClimateTwin Model Health, Drift & Retraining Intelligence Report
**Generated:** {health["timestamp"]}  
**Current Champion Model:** {health["champion_model"]["model_version"]}  
**Model Status:** `{health["model_status"]}`  
**Retraining Readiness Score:** `{health["retraining_readiness"]["readiness_score"]}/100` (`{health["retraining_readiness"]["recommendation"]}`)

---

## 1. Executive Summary & NOVA Intelligence
{health["nova_summary"]["briefing"]}

**Scientific Retraining Decision:**
> {health["retraining_readiness"]["reason"]}

---

## 2. Multi-Window Temporal Drift Analysis
| Temporal Horizon | Drift Status | Aggregate PSI | Sample Size | Interpretation |
| :--- | :--- | :--- | :--- | :--- |
| **24 Hours** | `{health["temporal_drift"]["24h_status"]}` | {health["temporal_drift"]["details"]["24h"]["aggregate_psi"]} | {health["temporal_drift"]["details"]["24h"]["sample_size"]} | Short-term meteorological variation |
| **7 Days** | `{health["temporal_drift"]["7d_status"]}` | {health["temporal_drift"]["details"]["7d"]["aggregate_psi"]} | {health["temporal_drift"]["details"]["7d"]["sample_size"]} | Weekly catchment state stability |
| **30 Days** | `{health["temporal_drift"]["30d_status"]}` | {health["temporal_drift"]["details"]["30d"]["aggregate_psi"]} | {health["temporal_drift"]["details"]["30d"]["sample_size"]} | Multi-week climatic baseline shift |

**Temporal Classification:** `{health["temporal_drift"]["pattern"]}`  
*{health["temporal_drift"]["interpretation"]}*

---

## 3. Top Drifting Environmental Features
| Feature | Training Median | Live Median | Change (%) | PSI | KS-Stat | Severity | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for d in health["feature_drift"]["top_drifting_features"]:
        report_content += f"| `{d['feature']}` | {d['training_median']} | {d['live_median']} | {d['pct_change_median']:+}% | {d['psi']} | {d['ks_statistic']} | **{d['severity']}** | `{d['status']}` |\n"

    report_content += f"""
---

## 4. Prediction Distribution & Uncertainty Drift
- **Historical Median Output Probability:** {health["prediction_drift"]["historical_median_prob"]:.4f}
- **Recent Live Median Output Probability:** {health["prediction_drift"]["live_median_prob"]:.4f}
- **Probability Shift:** {health["prediction_drift"]["probability_shift"]:+.4f}
- **Prediction Drift Severity:** `{health["prediction_drift"]["severity"]}`
- **Epistemic Variance (Ensemble Dispersion):** {health["uncertainty_trend"]["epistemic_variance_mean"]:.5f}
- **Prediction Interval Width:** {health["uncertainty_trend"]["prediction_interval_width_mean"]:.4f}
- **Model Confidence Condition:** `{health["uncertainty_trend"]["condition"]}`

---

## 5. Telemetry & Data Quality Gating (Phase 16 Integration)
- **Telemetry State:** `{health["data_quality"]["telemetry_state"]}` (Aggregate SHS: {health["data_quality"]["aggregate_score"]})
- **Degraded Telemetry Sources:** {health["data_quality"]["degraded_sources_count"]}
- **Anomalous Telemetry Sources:** {health["data_quality"]["anomalous_sources_count"]}
- **Diagnostic Result:** {health["data_quality"]["message"]}

---

## 6. Concept Drift Safeguard
- **Status:** `{health["concept_drift"]["status"]}`
- **Methodology Rationale:** {health["concept_drift"]["scientific_rationale"]}
- Verified ground-truth post-inundation survey labels are required to decouple P(Y|X) concept shifts from P(X) covariate shifts.

---

## 7. Champion vs Candidate Model Registry
- **Deployed Champion:** `{health["champion_model"]["model_version"]}`
  - Algorithm: {health["champion_model"]["algorithm"]}
  - ROC-AUC: {health["champion_model"]["validation_metrics"]["roc_auc"]} | PR-AUC: {health["champion_model"]["validation_metrics"]["pr_auc"]} | Brier: {health["champion_model"]["validation_metrics"]["brier_score"]}
- **Evaluated Candidate:** `{health["candidate_model"]["model_version"]}`
  - Algorithm: {health["candidate_model"]["algorithm"]}
  - ROC-AUC: {health["candidate_model"]["validation_metrics"]["roc_auc"]} | PR-AUC: {health["candidate_model"]["validation_metrics"]["pr_auc"]} | Brier: {health["candidate_model"]["validation_metrics"]["brier_score"]}
- **Safe Retraining Policy:** Automated model replacement is prohibited. Candidate models must demonstrate superior PR-AUC and Brier Score on chronological holdouts before deployment.
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print("Saved model_health_report.md")
    
    # 6. model_monitoring_methodology.md
    methodology_path = os.path.join(docs_monitoring_dir, "model_monitoring_methodology.md")
    methodology_content = """# ClimateTwin Model Drift & Monitoring Methodology

## 1. Population Stability Index (PSI)
For each continuous feature $X$, the historical baseline training distribution is partitioned into 10 quantile buckets $B_k$.
$$PSI = \\sum_{k=1}^{10} (A_k - E_k) \\times \\ln\\left(\\frac{A_k}{E_k}\\right)$$
where $E_k$ is the fraction of baseline observations in bucket $k$ and $A_k$ is the fraction of recent live observations in bucket $k$.
- $PSI < 0.10$: No distribution shift (HEALTHY).
- $0.10 \\le PSI < 0.25$: Moderate shift (WATCH).
- $PSI \\ge 0.25$: Substantial drift (DRIFT DETECTED).

## 2. Kolmogorov-Smirnov (KS-2samp) & Wasserstein Distance
- **Two-sample Kolmogorov-Smirnov Test:** Quantifies the maximum vertical deviation between empirical CDFs $F_{hist}(x)$ and $F_{live}(x)$.
- **Wasserstein Distance (Earth Mover's Distance):** Measures the minimum work needed to transform the live distribution into the historical baseline.

## 3. Sensor Health Gating
Before declaring model drift, telemetry is gated against Phase 16 Sensor Health scores (aggregate SHS). If sensors are stuck or degraded, the system outputs `DATA QUALITY ISSUE` rather than `MODEL DRIFT`.

## 4. Multi-Horizon Temporal Separation
To prevent false alarms caused by isolated 24-hour storms, ClimateTwin evaluates 24h, 7d, and 30d rolling windows. A single storm triggers `TEMPORARY WEATHER EVENT` (WATCH), while persistent shifts across 7d and 30d trigger `PERSISTENT DISTRIBUTION DRIFT`.

## 5. Concept Drift Ground-Truth Decoupling
Without confirmed post-flood ground-truth labels, concept drift cannot be mathematically confirmed. ClimateTwin explicitly renders:
`CONCEPT DRIFT: NOT YET EVALUABLE — LIVE GROUND-TRUTH LABELS UNAVAILABLE`
preventing unscientific claims of model obsolescence based solely on unlabeled observations.
"""
    with open(methodology_path, "w", encoding="utf-8") as f:
        f.write(methodology_content)
    print("Saved model_monitoring_methodology.md")
    
    # 7. Generate Plots
    print("Generating Visualization Plots in docs/plots/ ...")
    
    # Plot 1: Model Drift Evaluation (PSI & KS-statistic across features)
    top_feats = health["feature_drift"]["top_drifting_features"]
    feat_names = [d["feature"].replace("_", " ").title() for d in top_feats]
    psi_vals = [d["psi"] for d in top_feats]
    ks_vals = [d["ks_statistic"] for d in top_feats]
    
    fig, ax1 = plt.subplots(figsize=(10, 5))
    x = np.arange(len(feat_names))
    width = 0.35
    
    rects1 = ax1.bar(x - width/2, psi_vals, width, label='Population Stability Index (PSI)', color='#3b82f6')
    rects2 = ax1.bar(x + width/2, ks_vals, width, label='KS-Statistic', color='#f59e0b')
    
    ax1.axhline(0.25, color='#ef4444', linestyle='--', label='Drift Threshold (PSI=0.25)')
    ax1.axhline(0.10, color='#10b981', linestyle=':', label='Watch Threshold (PSI=0.10)')
    
    ax1.set_ylabel('Metric Value')
    ax1.set_title('Top Drifting Environmental Features (7-Day Rolling Horizon vs Baseline)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(feat_names, rotation=15, ha='right')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "model_drift_evaluation.png"), dpi=150)
    plt.close()
    print("Saved model_drift_evaluation.png")
    
    # Plot 2: Feature Distribution Comparison (Rainfall 7D Sum & Poondi Reservoir)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    hist_rf = model_monitoring_engine.history_df['rainfall_7d_sum'].dropna()
    live_df = model_monitoring_engine.get_live_data_window('30d')
    live_rf = live_df['rainfall_7d_sum'].dropna()
    
    axes[0].hist(hist_rf, bins=30, alpha=0.5, density=True, label='Training Baseline', color='#2563eb')
    axes[0].hist(live_rf, bins=15, alpha=0.6, density=True, label='Live 30-Day Window', color='#ef4444')
    axes[0].set_title('7-Day Cumulative Rainfall Distribution (mm)')
    axes[0].set_xlabel('Rainfall (mm)')
    axes[0].set_ylabel('Density')
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    
    hist_res = model_monitoring_engine.history_df['total_reservoir_level'].dropna()
    live_res = live_df['total_reservoir_level'].dropna()
    axes[1].hist(hist_res, bins=30, alpha=0.5, density=True, label='Training Baseline', color='#2563eb')
    axes[1].hist(live_res, bins=15, alpha=0.6, density=True, label='Live 30-Day Window', color='#10b981')
    axes[1].set_title('Total Reservoir Storage Distribution (mcft)')
    axes[1].set_xlabel('Storage (mcft)')
    axes[1].set_ylabel('Density')
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "feature_distribution_comparison.png"), dpi=150)
    plt.close()
    print("Saved feature_distribution_comparison.png")
    
    # Plot 3: Uncertainty Drift
    fig, ax = plt.subplots(figsize=(9, 4.5))
    live_vars = live_df['epistemic_variance'].dropna()
    live_widths = live_df['prediction_interval_width'].dropna()
    
    ax.plot(range(len(live_widths)), live_widths, marker='o', color='#8b5cf6', label='Prediction Interval Width (P90 - P10)')
    ax.plot(range(len(live_vars)), live_vars * 10, marker='s', linestyle='--', color='#f97316', label='Epistemic Variance (x10)')
    ax.axhline(0.30, color='#ef4444', linestyle=':', label='High Uncertainty Threshold (0.30)')
    
    ax.set_title('Prediction Interval Width & Epistemic Uncertainty Trend')
    ax.set_xlabel('Rolling Observation Day')
    ax.set_ylabel('Dispersion Metric')
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "uncertainty_drift.png"), dpi=150)
    plt.close()
    print("Saved uncertainty_drift.png")
    
    # Plot 4: Model Health Timeline (24h, 7d, 30d Drift progression)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    horizons = ['24 Hours', '7 Days', '30 Days']
    psi_horizons = [
        health["temporal_drift"]["details"]["24h"]["aggregate_psi"],
        health["temporal_drift"]["details"]["7d"]["aggregate_psi"],
        health["temporal_drift"]["details"]["30d"]["aggregate_psi"]
    ]
    colors = ['#10b981' if p < 0.10 else '#f59e0b' if p < 0.25 else '#ef4444' for p in psi_horizons]
    bars = ax.bar(horizons, psi_horizons, color=colors, width=0.45)
    
    ax.axhline(0.25, color='#ef4444', linestyle='--', label='Drift Detected (>=0.25)')
    ax.axhline(0.10, color='#f59e0b', linestyle=':', label='Watch Window (>=0.10)')
    
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.3f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontweight='bold')
                    
    ax.set_title(f'Temporal Drift Horizons — Overall Pattern: {health["temporal_drift"]["pattern"]}')
    ax.set_ylabel('Aggregate PSI')
    ax.set_ylim(0, max(0.35, max(psi_horizons) * 1.25))
    ax.legend(loc='upper left')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "model_health_timeline.png"), dpi=150)
    plt.close()
    print("Saved model_health_timeline.png")
    
    print("\nAll research artifacts and plots successfully generated!")

if __name__ == "__main__":
    generate_artifacts()
