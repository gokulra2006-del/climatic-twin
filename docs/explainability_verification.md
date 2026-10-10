# Explainability Verification & Reliability

## 1. Motivation
Dashboard systems often present feature-importance plots (e.g., SHAP values) to operators to build "trust". However, explanations can be mathematically plausible without being *reliable*. If an explanation shifts under noise, fails to reflect true counterfactuals, or hides sensor faults due to collinearity, it is fundamentally untrustworthy for emergency dispatch.

## 2. Experimental Setup
*(Script: scripts/experiment_explainability.py)*

We generated a synthetic stream of infrastructure telemetry containing highly collinear features (e.g., Rain_1h strongly correlated with Rain_24h), a common reality in climate data. We then computed exact Shapley values and subjected the explanatory manifolds to five adversarial robustness tests.

## 3. Reliability Metrics
*(Data Source: esults/explainability_metrics.csv)*

| Test | Spearman Rank Correlation / Rate | Verdict |
| :--- | :--- | :--- |
| **Internal Consistency:** SHAP vs Permutation Importance | **0.800** | PASS (Mostly aligns) |
| **Model Agreement:** Random Forest SHAP vs LogReg SHAP | **0.300** | FAIL (Explanations are model-specific) |
| **Stability:** SHAP Rank under 5% Input Noise | **0.600** | FAIL (Highly unstable) |
| **Drift Resilience:** Explanations under Injected Sensor Fault | **0.500** | FAIL (Silent shifting) |
| **Counterfactual Plausibility:** Top-Feature Perturbation Flip Rate | **20.8%** | FAIL (Actionability is an illusion) |

## 4. Why the Explanations Failed (Analysis)

1.  **Counterfactual Illusion:** The most damning failure is the Counterfactual Flip Rate. Operators assume that if SHAP highlights Rain_1h as the top driving feature, mitigating it (or correcting a bad reading) will change the prediction. However, mutating the top feature only flipped the prediction **~20%** of the time. Because Rain_1h and Rain_24h are collinear, the Random Forest simply routed its decision boundary through the *second* feature when the first was perturbed, sustaining the false confidence.
2.  **Noise Instability:** Injecting a tiny, operationally irrelevant 5% Gaussian noise into the sensor readings caused the SHAP ranks to aggressively shuffle. An operator watching the dashboard would see the "Top Reason" for a flood warning flapping wildly between updates, destroying trust.
3.  **Sensor Fault Masking (Silent Shifting):** When we simulated a stuck-at-zero sensor fault, the SHAP values did not explicitly flag the anomaly. Instead, the model's internal attention silently shifted to the correlated background features. The explanation looked completely plausible, masking the fact that the primary sensor had died.

**Final Conclusion:** The SHAP visualizations in this pipeline are **NOT** certified for operational trustworthiness. They exhibit extreme vulnerability to collinear masking. The dashboard must clearly label feature-importance plots as *Diagnostic (Model-View)* rather than *Causal (Physical-View)*.
