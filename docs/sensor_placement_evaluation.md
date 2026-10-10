# Sensor Network Resiliency & Placement

## 1. Missing Data Recovery (Part A)
Urban sensor networks suffer from frequent telemetry dropouts (power loss, comms failure). We injected random and clustered burst missingness (\% \to 70\%$) into the data streams and evaluated five recovery strategies.

*(Data Source: esults/missing_data_recovery.csv)*

### Key Findings
1.  **Burst Vulnerability:** Simple imputation (Last-Value Hold, Linear Interpolation) completely collapsed under "burst" missingness (contiguous dropouts). RMSE spiked and False Alarms triggered heavily as the interpolator drew flat lines through hazard peaks.
2.  **EnKF & Model-Based Supremacy:** The enkf_proxy (exponential smoothing of the state space) and model_based (polynomial/ML extrapolation) maintained robust Probability of Detection (POD) even at \%$ burst missingness. By utilizing underlying variance rather than drawing straight lines, they successfully preserved the non-linear hazard boundary.
3.  **Latency Trade-off:** While statistical mean-fill took $<1 \text{ ms}$, the model-based reconstructions incurred minor processing latency. However, for operational early-warning (where lead times are $>5 \text{ hours}$), this sub-second penalty is entirely negligible.

## 2. Sensor Placement Optimization (Part B)
*⚠️ WARNING: This sensor placement ablation was conducted on a SYNTHETIC scale-free network (Barabási–Albert). The exact sensor counts hold methodological value for algorithm design, but do NOT map directly to Chennai's physical GIS layout.*

Given a fixed municipal budget, we evaluated four placement strategies:
*   **Random:** Baseline.
*   **High-Risk:** Prioritizes nodes with high historical hazard incidence.
*   **Uncertainty-Reduction:** Prioritizes nodes with the highest ensemble spread (epistemic uncertainty).
*   **Dependency-Centrality:** Prioritizes nodes with high graph betweenness (choke points in the cascade).

*(Data Source: esults/sensor_placement.csv)*

### Minimum Sensors for Target POD (>85%)
We measured the minimum network budget required to achieve a reliable \%$ network-wide POD across 20 random Monte Carlo seeds:

*   **Random Placement:** Required **~40 sensors** to cross \%$ POD.
*   **Uncertainty-Reduction:** Required **~30 sensors** (it mapped the boundaries of the network well, but occasionally missed dense urban core events).
*   **Dependency-Centrality:** Required **~20 sensors** (highly efficient at tracking cascade propagation through central nodes).
*   **High-Risk Placement:** Achieved \%$ POD with only **10 sensors**. Because extreme events in our synthetic risk distribution are heavily power-law distributed (Pareto principle), directly instrumenting the highest-risk nodes yielded massive, immediate operational returns.

### Conclusion
Deploying sensors strictly based on historical High-Risk incidence provides the greatest operational efficiency under tight municipal budgets. As budgets expand ($>30$ sensors), blending High-Risk with Dependency-Centrality optimally covers both primary hazards and secondary infrastructure cascades.
