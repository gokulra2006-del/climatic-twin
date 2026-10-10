# Complete Research Gap Brainstorm (16 Domains)

## Impact Labels
- **Gap Statement:** Hazard proxies (e.g. water depth) don't map to human-scale infrastructure impacts.
- **Evidence:** Literature relies on mm of rain; dispatchers need road-closure binaries.
- **Status:** Addressed
- **File/Proof:** results/impact_label_catalogue.csv
- **Solvable here?:** Yes
- **Method/Data:** Threshold-based engineering impact mapping | REAL (IMD) + SYNTHETIC topology
- **Metric:** Cohen's Kappa, Impact F1
- **Limitation:** Subjective thresholds without real dispatch logs
- **Paper Wording:** *"We map meteorological hazards to simulated operational impacts using engineering heuristics."*

## Non-stationarity
- **Gap Statement:** Static models decay under climate drift and seasonal shifts.
- **Evidence:** F1 collapses when tested on out-of-distribution monsoon data.
- **Status:** Addressed
- **File/Proof:** results/drift_adaptation_summary.csv
- **Solvable here?:** Yes
- **Method/Data:** Isotonic recalibration via KS-test trigger | SYNTHETIC trend and shift
- **Metric:** F1 recovery, Brier degradation
- **Limitation:** Tested on synthetic drift, not decadal real shifts
- **Paper Wording:** *"We demonstrate rapid recovery from synthetic distribution shifts using lightweight non-parametric recalibration."*

## Physics-AI
- **Gap Statement:** Pure ML models violate kinematic laws during extreme out-of-distribution shocks.
- **Evidence:** Neural nets predicting negative water depths.
- **Status:** Addressed
- **File/Proof:** docs/physics_constraint_evaluation.md
- **Solvable here?:** Yes
- **Method/Data:** Post-hoc deterministic clipping vs PINN loss penalty | SYNTHETIC topology
- **Metric:** Constraint violation rate, OOD RMSE
- **Limitation:** PINNs underfit; clipping is naive
- **Paper Wording:** *"We enforce physical bounding via post-hoc projection, outperforming soft-penalty physics-informed losses on extreme anomalies."*

## Sensor Placement
- **Gap Statement:** Municipalities lack budget to instrument every node optimally.
- **Evidence:** Random sensor placement yields sub-optimal detection rates.
- **Status:** Addressed
- **File/Proof:** results/sensor_placement.csv
- **Solvable here?:** Yes
- **Method/Data:** Graph Centrality vs Risk-Weighted placement | SYNTHETIC scale-free graph
- **Metric:** Target POD (85%) sensor minimums
- **Limitation:** Synthetic topology does not map directly to GIS limits
- **Paper Wording:** *"Simulations on scale-free topologies indicate that historical risk-weighted placement minimizes budget requirements for target network coverage."*

## Missing-data Recovery
- **Gap Statement:** Telemetry streams fail during extreme events (burst dropouts), crashing ML models.
- **Evidence:** Linear interpolators draw flat lines through hazard peaks.
- **Status:** Addressed
- **File/Proof:** results/missing_data_recovery.csv
- **Solvable here?:** Yes
- **Method/Data:** Model-based and EnKF-proxy state extrapolation | SYNTHETIC time series
- **Metric:** RMSE, Coverage, POD/FAR
- **Limitation:** EnKF is simulated, not a full physical data assimilation loop
- **Paper Wording:** *"State-space proxies preserve extreme event detection capabilities up to 50% burst missingness, whereas standard interpolation fails."*

## Downscaling
- **Gap Statement:** Coarse satellite grids mask sub-grid infrastructure impacts.
- **Evidence:** Interpolating 5km grids over 50m assets misses micro-extremes.
- **Status:** Addressed
- **File/Proof:** results/downscaling_overall.csv
- **Solvable here?:** Yes
- **Method/Data:** Nearest Pixel vs IDW + Variance Propagation | SYNTHETIC continuous 2D field
- **Metric:** Impact F1, Interval Coverage
- **Limitation:** Assumes constant sub-grid variance
- **Paper Wording:** *"We demonstrate that standard IDW downscaling aggressively washes out high-frequency spatial extremes, collapsing asset-level warning accuracy."*

## Action Optimization
- **Gap Statement:** Probabilistic forecasts do not natively map to asymmetric real-world financial costs.
- **Evidence:** Missing an event costs 10x more than a false alarm.
- **Status:** Partial
- **File/Proof:** results/decision_dca.csv
- **Solvable here?:** Yes (Simulated)
- **Method/Data:** Expected utility minimization and Decision Curve Analysis | SIMULATED costs
- **Metric:** Regret vs Oracle, Expected Cost
- **Limitation:** No real human operators or verified financial bounds
- **Paper Wording:** *"We evaluate warnings strictly as simulated expected-utility decisions to formalize the trade-off between intervention costs and flood damage."*

## Alert Fatigue
- **Gap Statement:** Static probability thresholds cause 'flapping' in operational UIs.
- **Evidence:** Raw thresholds triggered 11 escalation/de-escalation cycles in 4 hours.
- **Status:** Addressed
- **File/Proof:** results/alert_hysteresis.csv
- **Solvable here?:** Yes
- **Method/Data:** Stateful hysteresis and cooldown logic | SYNTHETIC probabilities
- **Metric:** Flapping count, False Positives (Fatigue Proxy)
- **Limitation:** Operator cognitive load isn't physically measured
- **Paper Wording:** *"Stateful hysteresis completely eradicates UI flapping and mathematically reduces false alarm events by suppressing transient probability spikes."*

## Explainability
- **Gap Statement:** SHAP/feature importance plots can be mathematically plausible but unreliable.
- **Evidence:** Tree-SHAP ranks collapse under collinearity and noise.
- **Status:** Addressed
- **File/Proof:** results/explainability_metrics.csv
- **Solvable here?:** Yes
- **Method/Data:** Adversarial SHAP verification (exact Shapley) | SYNTHETIC collinear telemetry
- **Metric:** Rank correlations, Prediction flip rate
- **Limitation:** Verification is empirical, not theoretically bounded
- **Paper Wording:** *"We explicitly reject the operational trustworthiness of raw SHAP values, demonstrating severe masking and counterfactual failure under meteorological collinearity."*

## Cybersecurity
- **Gap Statement:** Cloud-connected telemetry is vulnerable to hostile injection.
- **Evidence:** Spoofed data can trigger chaotic dispatch.
- **Status:** Addressed
- **File/Proof:** results/cybersecurity_metrics.csv
- **Solvable here?:** Yes
- **Method/Data:** Local mocked defensive bus (HMAC, Nonce, Plausibility) | SIMULATED hostile payloads
- **Metric:** Detection rate, Added latency
- **Limitation:** Local simulated bus, not physical edge hardware
- **Paper Wording:** *"A local simulated harness verifies that cryptographic signing and physical plausibility bounds intercept 100% of standard injection attacks."*

## Equity
- **Gap Statement:** Warning systems ignore socio-economic vulnerability.
- **Evidence:** Standard loss functions optimize for average accuracy, masking disparate impact.
- **Status:** Open
- **File/Proof:** docs/future_work_tier3.md
- **Solvable here?:** No
- **Method/Data:** Vulnerability-weighted cost functions | Requires census and ethical clearance
- **Metric:** None
- **Limitation:** Lacks ethical review
- **Paper Wording:** *"Incorporating equity-weighted priority matrices remains critical future work pending formal ethical stakeholder review."*

## Recovery Forecasting
- **Gap Statement:** Focus is entirely on failure onset, not system restoration.
- **Evidence:** Models predict 'pump failed', not 'pump restored in 6 hours'.
- **Status:** Open
- **File/Proof:** docs/future_work_tier3.md
- **Solvable here?:** No
- **Method/Data:** Autoregressive survival models | Requires granular municipal repair logs
- **Metric:** None
- **Limitation:** Missing ground truth repair data
- **Paper Wording:** *"Forecasting the temporal trajectory of infrastructure restoration requires integration with municipal ticketing systems and is reserved for Phase 2."*

## Governance
- **Gap Statement:** Research code lacks auditability and version control for critical alerts.
- **Evidence:** No trail of which model issued a bad warning.
- **Status:** Addressed
- **File/Proof:** backend/app/core/model_registry.py
- **Solvable here?:** Yes
- **Method/Data:** Software registry with strict approval and rollback gates | INTERNAL software architecture
- **Metric:** Test pass/fail
- **Limitation:** Not deployed in a real CI/CD production pipeline
- **Paper Wording:** *"We embed model governance directly into the architecture, enabling strict versioning, warning audit logs, and instantaneous algorithmic rollback."*

## Benchmark
- **Gap Statement:** Literature claims are incomparable due to shifting datasets and leakage.
- **Evidence:** Papers use random train/test splits on time-series.
- **Status:** Addressed
- **File/Proof:** benchmark/leaderboard.csv
- **Solvable here?:** Yes
- **Method/Data:** Chronological splits isolating real vs synthetic | REAL IMD + SYNTHETIC topology
- **Metric:** Standardized metrics
- **Limitation:** Requires wider community adoption
- **Paper Wording:** *"To ensure rigorous reproducibility, we release a strictly versioned benchmark that explicitly isolates real meteorological ground-truth from synthetic topological simulations."*

## Rare Events
- **Gap Statement:** Standard metrics hide extreme failure modes in safe background data.
- **Evidence:** F1 is high, but the model completely misses the 1-in-100 year flood.
- **Status:** Addressed
- **File/Proof:** results/event_level_metrics.csv
- **Solvable here?:** Yes
- **Method/Data:** Leave-One-Event-Out validation | SYNTHETIC time-series
- **Metric:** Event-AUPRC, Median Lead Time
- **Limitation:** Evaluated on procedurally generated events
- **Paper Wording:** *"We shift validation from point-wise accuracy to Leave-One-Event-Out detection, revealing that non-linear models secure superior operational lead times despite similar raw F1 scores."*

## Decision Uncertainty
- **Gap Statement:** Deterministic warnings force operators to guess confidence bounds.
- **Evidence:** Binary outputs provide no probabilistic context.
- **Status:** Addressed
- **File/Proof:** docs/decision_value_evaluation.md
- **Solvable here?:** Yes
- **Method/Data:** Expected cost optimization curves | SIMULATED
- **Metric:** Regret
- **Limitation:** Cost matrices are approximations
- **Paper Wording:** *"We utilize probabilistic forecasting to output decision uncertainty, aligning automated alerts with the asymmetric financial risks of early municipal intervention."*

