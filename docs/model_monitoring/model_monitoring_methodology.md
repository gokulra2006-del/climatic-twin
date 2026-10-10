# ClimateTwin Model Drift & Monitoring Methodology

## 1. Population Stability Index (PSI)
For each continuous feature $X$, the historical baseline training distribution is partitioned into 10 quantile buckets $B_k$.
$$PSI = \sum_{k=1}^{10} (A_k - E_k) \times \ln\left(\frac{A_k}{E_k}\right)$$
where $E_k$ is the fraction of baseline observations in bucket $k$ and $A_k$ is the fraction of recent live observations in bucket $k$.
- $PSI < 0.10$: No distribution shift (HEALTHY).
- $0.10 \le PSI < 0.25$: Moderate shift (WATCH).
- $PSI \ge 0.25$: Substantial drift (DRIFT DETECTED).

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
