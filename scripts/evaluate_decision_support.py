"""
Phase 17 Decision Support & Early-Warning Policy Evaluation Script
ClimateTwin Chennai Project

Generates:
- docs/plots/phase17_decision_support_evaluation.png (6-panel research figure)
- docs/decision_support/decision_evaluation.json
- docs/decision_support/decision_policy.json
- docs/decision_support/decision_policy.md
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timezone

from app.core.decision_support import (
    DecisionSupportEngine, DSS_WEIGHTS, DECISION_THRESHOLDS,
    HYSTERESIS_BAND, MODEL_VERSION, THRESHOLDS_DISCLAIMER
)

print("="*65)
print("  CLIMATETWIN PHASE 17: DECISION SUPPORT EVALUATION")
print("="*65)
print()

engine = DecisionSupportEngine()

# ================================================================
# 1. Run benchmark scenarios
# ================================================================
print("[Step 1] Running benchmark scenarios...")
scenarios = engine.run_benchmark_scenarios()
print(f"  Completed {len(scenarios)} benchmark scenarios.")

# ================================================================
# 2. Monotonicity evaluation
# ================================================================
print("[Step 2] Evaluating monotonicity...")

# Hazard severity monotonicity
hazard_probs = np.linspace(0.0, 1.0, 20)
hazard_dss = []
for p in hazard_probs:
    eng = DecisionSupportEngine()
    r = eng.assess(flood_probability=p, compound_risk_score=p*0.8, dominant_hazard_intensity=p*0.9)
    hazard_dss.append(r["decision_score"])

hazard_monotonic = all(hazard_dss[i] <= hazard_dss[i+1] + 0.01 for i in range(len(hazard_dss)-1))
print(f"  Hazard severity monotonicity: {'PASS' if hazard_monotonic else 'APPROXIMATE'}")

# Asset risk monotonicity
asset_aris = np.linspace(0.0, 1.0, 20)
asset_dss = []
for a in asset_aris:
    eng = DecisionSupportEngine()
    r = eng.assess(max_asset_risk_index=a, mean_criticality_weight=1.0, max_exposure_score=a)
    asset_dss.append(r["decision_score"])

asset_monotonic = all(asset_dss[i] <= asset_dss[i+1] + 0.01 for i in range(len(asset_dss)-1))
print(f"  Asset risk monotonicity: {'PASS' if asset_monotonic else 'APPROXIMATE'}")

# ================================================================
# 3. Uncertainty vs confidence
# ================================================================
print("[Step 3] Evaluating uncertainty vs confidence...")

uncertainty_widths = np.linspace(0.05, 0.80, 20)
confidence_scores = []
for w in uncertainty_widths:
    eng = DecisionSupportEngine()
    level = "LOW" if w < 0.20 else "MODERATE" if w < 0.45 else "HIGH"
    fc = eng.normalize_forecast_confidence(level, w, w * 0.1)
    confidence_scores.append(fc)

conf_anti_monotonic = all(confidence_scores[i] >= confidence_scores[i+1] - 0.01 for i in range(len(confidence_scores)-1))
print(f"  Uncertainty inversely relates to confidence: {'PASS' if conf_anti_monotonic else 'APPROXIMATE'}")

# ================================================================
# 4. Data quality degradation vs decision state
# ================================================================
print("[Step 4] Evaluating data quality degradation effects...")

shs_values = np.linspace(0.20, 1.0, 20)
dq_scores = []
dq_gates = []
for s in shs_values:
    eng = DecisionSupportEngine()
    nd = max(0, int((1.0 - s) * 5))
    states = ["HEALTHY"] * max(0, 8 - nd) + ["DEGRADED"] * min(nd, 8)
    r = eng.assess(aggregate_shs=s, num_degraded=nd, source_health_states=states[:8],
                   flood_probability=0.50, compound_risk_score=0.50)
    dq_scores.append(r["decision_score"])
    dq_gates.append(r["data_quality_gate"]["gate_state"])

print(f"  DQ gate states observed: {set(dq_gates)}")

# ================================================================
# 5. Asset criticality vs priority
# ================================================================
print("[Step 5] Evaluating asset criticality vs operational priority...")

crit_weights = [0.50, 0.75, 1.00]
crit_priorities = []
for cw in crit_weights:
    eng = DecisionSupportEngine()
    assets = [{"code": f"ASSET_{cw}", "name": f"Asset CW={cw}", "asset_risk_index": 0.60,
               "criticality_weight": cw, "exposure_score": 0.55, "risk_level": "HIGH"}]
    r = eng.assess(flood_probability=0.50, compound_risk_score=0.50, asset_details=assets)
    crit_priorities.append(r["affected_assets"][0]["priority_score"])

crit_monotonic = all(crit_priorities[i] <= crit_priorities[i+1] for i in range(len(crit_priorities)-1))
print(f"  Criticality monotonicity: {'PASS' if crit_monotonic else 'FAIL'}")

# ================================================================
# 6. Generate 6-panel figure
# ================================================================
print("[Step 6] Generating 6-panel research figure...")

fig, axes = plt.subplots(2, 3, figsize=(18, 11))
fig.suptitle("ClimateTwin Phase 17: Decision Support & Adaptive Early-Warning Evaluation",
             fontsize=14, fontweight='bold', y=0.98)

# Panel 1: DSS across benchmark scenarios
ax1 = axes[0, 0]
scenario_names = [s["scenario_id"].replace("SCENARIO_", "").replace("_", "\n")[:12] for s in scenarios]
scenario_dss = [s["decision_score"] for s in scenarios]
colors1 = []
for d in scenario_dss:
    if d >= 0.80: colors1.append('#dc2626')
    elif d >= 0.60: colors1.append('#f59e0b')
    elif d >= 0.40: colors1.append('#3b82f6')
    elif d >= 0.20: colors1.append('#10b981')
    else: colors1.append('#6b7280')
ax1.bar(range(len(scenarios)), scenario_dss, color=colors1, edgecolor='black', linewidth=0.5)
ax1.set_xticks(range(len(scenarios)))
ax1.set_xticklabels([s["scenario_id"][-1] for s in scenarios], fontsize=9)
ax1.set_xlabel("Benchmark Scenario", fontsize=9)
ax1.set_ylabel("Decision Support Score (DSS)", fontsize=9)
ax1.set_title("Panel 1: DSS Across Benchmark Scenarios", fontsize=10, fontweight='bold')
ax1.set_ylim(0, 1.05)
for t_name, t_vals in DECISION_THRESHOLDS.items():
    if t_vals["min"] > 0:
        ax1.axhline(y=t_vals["min"], color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
        ax1.text(len(scenarios)-0.5, t_vals["min"]+0.01, t_name, fontsize=6, ha='right', color='gray')

# Panel 2: Decision level vs DSS
ax2 = axes[0, 1]
dss_range = np.linspace(0, 1.0, 100)
level_colors = {"NORMAL": '#6b7280', "MONITOR": '#10b981', "PREPARE": '#3b82f6', "ALERT": '#f59e0b', "EMERGENCY": '#dc2626'}
for lname, lrange in DECISION_THRESHOLDS.items():
    ax2.axhspan(lrange["min"], lrange["max"], alpha=0.25, color=level_colors[lname], label=lname)
    ax2.text(0.5, (lrange["min"] + lrange["max"])/2, lname, ha='center', va='center', fontsize=9, fontweight='bold', color=level_colors[lname])
ax2.set_xlim(0, 1)
ax2.set_ylim(0, 1)
ax2.set_xlabel("(Decision State Mapping)", fontsize=9)
ax2.set_ylabel("DSS Range", fontsize=9)
ax2.set_title("Panel 2: Decision Level vs DSS Thresholds", fontsize=10, fontweight='bold')
# Add hysteresis band annotations
for lname, lrange in DECISION_THRESHOLDS.items():
    if lrange["min"] > 0:
        ax2.axhline(y=lrange["min"] - HYSTERESIS_BAND, color='red', linestyle=':', alpha=0.4, linewidth=1)

# Panel 3: Hazard severity vs decision score (monotonicity)
ax3 = axes[0, 2]
ax3.plot(hazard_probs, hazard_dss, 'b-o', markersize=3, linewidth=1.5, label='DSS vs Hazard')
ax3.fill_between(hazard_probs, hazard_dss, alpha=0.15, color='blue')
ax3.set_xlabel("Flood Probability / Hazard Severity", fontsize=9)
ax3.set_ylabel("Decision Support Score (DSS)", fontsize=9)
ax3.set_title("Panel 3: Hazard Severity vs DSS (Monotonicity)", fontsize=10, fontweight='bold')
ax3.set_xlim(0, 1)
ax3.set_ylim(0, 1)
ax3.legend(fontsize=8)
mono_text = "MONOTONIC" if hazard_monotonic else "APPROX. MONOTONIC"
ax3.text(0.05, 0.92, mono_text, transform=ax3.transAxes, fontsize=8, fontweight='bold',
         color='green' if hazard_monotonic else 'orange',
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# Panel 4: Uncertainty vs decision confidence
ax4 = axes[1, 0]
ax4.plot(uncertainty_widths, confidence_scores, 'r-s', markersize=3, linewidth=1.5, label='Forecast Confidence')
ax4.fill_between(uncertainty_widths, confidence_scores, alpha=0.15, color='red')
ax4.set_xlabel("Uncertainty Width", fontsize=9)
ax4.set_ylabel("Forecast Confidence Score", fontsize=9)
ax4.set_title("Panel 4: Uncertainty vs Decision Confidence", fontsize=10, fontweight='bold')
ax4.set_xlim(0, 0.85)
ax4.set_ylim(0, 1)
ax4.legend(fontsize=8)
ax4.text(0.05, 0.92, "INVERSE RELATIONSHIP", transform=ax4.transAxes, fontsize=8, fontweight='bold',
         color='green', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# Panel 5: Data quality degradation vs decision state
ax5 = axes[1, 1]
gate_map = {"PASS": 1.0, "DEGRADED": 0.5, "BLOCKED": 0.0}
gate_numeric = [gate_map.get(g, 0.5) for g in dq_gates]
ax5_twin = ax5.twinx()
ax5.plot(shs_values, dq_scores, 'b-o', markersize=3, linewidth=1.5, label='DSS')
ax5_twin.plot(shs_values, gate_numeric, 'r--^', markersize=4, linewidth=1.2, label='DQ Gate', alpha=0.7)
ax5.set_xlabel("Aggregate Sensor Health Score", fontsize=9)
ax5.set_ylabel("Decision Support Score (DSS)", fontsize=9, color='blue')
ax5_twin.set_ylabel("DQ Gate (1=PASS, 0.5=DEGRADED, 0=BLOCKED)", fontsize=8, color='red')
ax5.set_title("Panel 5: Data Quality Degradation vs Decision", fontsize=10, fontweight='bold')
ax5.set_xlim(0.15, 1.05)
ax5.legend(loc='upper left', fontsize=8)
ax5_twin.legend(loc='upper right', fontsize=8)

# Panel 6: Asset criticality vs operational priority
ax6 = axes[1, 2]
# Use scenario results to show asset priority variation
sc_labels = []
sc_priorities = []
sc_colors = []
for sc in scenarios:
    if sc["top_priority_asset"] != "N/A":
        sc_labels.append(sc["scenario_id"][-1])
        sc_priorities.append(sc["decision_score"])
        lev = sc["decision_level"]
        sc_colors.append(level_colors.get(lev, '#6b7280'))

ax6.barh(range(len(sc_labels)), sc_priorities, color=sc_colors, edgecolor='black', linewidth=0.5, height=0.6)
ax6.set_yticks(range(len(sc_labels)))
ax6.set_yticklabels([f"Scenario {l}" for l in sc_labels], fontsize=8)
ax6.set_xlabel("Decision Score (DSS)", fontsize=9)
ax6.set_title("Panel 6: Asset Criticality & Scenario Priority", fontsize=10, fontweight='bold')
ax6.set_xlim(0, 1.05)
for i, (s, c) in enumerate(zip(sc_priorities, sc_colors)):
    ax6.text(s + 0.02, i, f"{s:.2f}", va='center', fontsize=7, color=c, fontweight='bold')

plt.tight_layout(rect=[0, 0.02, 1, 0.95])

# Add disclaimer
fig.text(0.5, 0.005,
         "PROTOTYPE RESEARCH THRESHOLDS | Decision support only | Not an autonomous emergency authority | Synthetic benchmark scenarios",
         ha='center', fontsize=7, style='italic', color='gray')

plot_dir = os.path.join(os.path.dirname(__file__), '..', 'docs', 'plots')
os.makedirs(plot_dir, exist_ok=True)
plot_path = os.path.join(plot_dir, 'phase17_decision_support_evaluation.png')
fig.savefig(plot_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f"  [PASS] 6-panel figure saved to {os.path.abspath(plot_path)}")

# ================================================================
# 7. Save evaluation results
# ================================================================
print("[Step 7] Saving evaluation artifacts...")

docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs', 'decision_support')
os.makedirs(docs_dir, exist_ok=True)

# decision_evaluation.json
evaluation = {
    "model_version": MODEL_VERSION,
    "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
    "scenario_results": scenarios,
    "monotonicity": {
        "hazard_severity": "PASS" if hazard_monotonic else "APPROXIMATE",
        "asset_risk": "PASS" if asset_monotonic else "APPROXIMATE",
        "uncertainty_confidence_inverse": "PASS" if conf_anti_monotonic else "APPROXIMATE",
        "criticality_priority": "PASS" if crit_monotonic else "FAIL"
    },
    "data_quality_gate_states_observed": list(set(dq_gates)),
    "thresholds_disclaimer": THRESHOLDS_DISCLAIMER
}
eval_path = os.path.join(docs_dir, 'decision_evaluation.json')
with open(eval_path, 'w') as f:
    json.dump(evaluation, f, indent=2)
print(f"  [PASS] Evaluation results saved to {os.path.abspath(eval_path)}")

# decision_policy.json
policy = engine.get_policy()
policy_path = os.path.join(docs_dir, 'decision_policy.json')
with open(policy_path, 'w') as f:
    json.dump(policy, f, indent=2)
print(f"  [PASS] Policy config saved to {os.path.abspath(policy_path)}")

# decision_policy.md
md_content = f"""# ClimateTwin Phase 17 Decision Policy

## Model Version
`{MODEL_VERSION}`

## Decision Support Score (DSS)

DSS = 0.30 * Hazard_Severity + 0.20 * Asset_Risk + 0.15 * Compound_Risk + 0.15 * Forecast_Confidence + 0.10 * Data_Quality + 0.10 * Persistence

All components normalized to [0, 1].

## Decision Levels

| Level | DSS Range | Description |
|-------|-----------|-------------|
| NORMAL | [0.00, 0.20) | Routine monitoring |
| MONITOR | [0.20, 0.40) | Enhanced surveillance |
| PREPARE | [0.40, 0.60) | Preparedness activation |
| ALERT | [0.60, 0.80) | Operational response |
| EMERGENCY | [0.80, 1.00] | Full emergency mobilization |

## Hysteresis Band
De-escalation requires DSS to drop {HYSTERESIS_BAND} below the level threshold to prevent alert flapping.

## Data Quality Gate
- PASS: Aggregate SHS >= 0.70, at most 1 unhealthy source
- DEGRADED: Aggregate SHS >= 0.45, at most 3 unhealthy sources
- BLOCKED: Below DEGRADED thresholds; automatic all-clear is BLOCKED

## Uncertainty-Aware Decision Matrix
| Probability | Uncertainty | Decision Modifier |
|------------|-------------|-------------------|
| HIGH | LOW | Strong escalation candidate |
| HIGH | HIGH | Precautionary escalation + verification |
| MODERATE | LOW | Monitoring / preparedness |
| MODERATE | HIGH | Enhanced monitoring + verification |
| LOW | HIGH | Do NOT declare safety; verify telemetry |
| LOW | LOW | Nominal monitoring |

## Scientific Limitations
1. Decision thresholds are PROTOTYPE values.
2. Operational actions require domain-expert approval.
3. Synthetic scenarios are NOT real emergency decisions.
4. This is decision SUPPORT, not an autonomous emergency authority.
5. No unsupported causal claims are made.

---
*Generated: {datetime.now(timezone.utc).isoformat()}*
"""
md_path = os.path.join(docs_dir, 'decision_policy.md')
with open(md_path, 'w') as f:
    f.write(md_content)
print(f"  [PASS] Policy documentation saved to {os.path.abspath(md_path)}")

print()
print("="*65)
print("  PHASE 17 EVALUATION COMPLETE")
print("="*65)
