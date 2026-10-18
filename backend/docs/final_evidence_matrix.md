# Final Evidence Matrix

| Claim | Supporting Code | Supporting Result | Data Source | Validated? | Safe Wording for Paper | Limitation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Chronological constraints prevent metric inflation. | 
eproducibility.py | aseline_metrics.csv | Real | Yes | "Strict holdout testing resulted in F1 boundary collapse, highlighting the severity of class imbalance in climate events." | F1=0 collapse requires more training history. |
| EnKF recovers accuracy during network dropouts. | enkf_assimilation.py | enkf_experiments.csv | Simulated Dropouts | Yes | "EnKF assimilation statically improved forecast continuity compared to nudging during simulated sensor dropouts." | Gaussian error assumptions in R. |
| Quantile regression achieves valid bounds. | gnn_lstm_forecaster.py | gnn_lstm_ablations.csv | Synthetic | Yes | "The ReLU-constrained pinball loss generated non-crossing P10/P50/P90 quantiles with 0 constraint violations." | Spatial topological graphs are synthetic. |
| Bayesian interactions isolate synergistic risk. | probabilistic_risk.py | compound_risk_metrics.csv | Synthetic | Yes | "The L2-regularized logistic model successfully isolated negative protective synergies between wind and localized pooling." | Rare interactions heavily regularized. |
| Domain Adaptation outperforms Zero-Shot transfer. | experiment_city_transfer.py | city_transfer_learning.csv | Synthetic | Yes | "Unsupervised covariate shift alignment restored F1 scores from 0.73 (Zero-Shot) to 0.91 during synthetic domain-shift testing." | Relies on simulated Mumbai domains. |
| Expected Utility models reduce missed warnings. | impact_warnings.py | decision_curve_analysis.csv | Simulated HITL | Yes | "Cost-asymmetric alerting thresholds eliminated 80% of missed escalations for critical assets like hospitals." | Unvalidated in physical dispatch centers. |
