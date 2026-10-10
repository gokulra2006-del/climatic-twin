# Physics-Constraint Evaluation

## 1. Methodology & Physical Bounds
To prevent the machine learning forecasting models from hallucinating physically impossible states (e.g., negative water volumes, violating reservoir capacities, or breaking maximum possible kinematic flow rates), we evaluated constraint-aware forecasting.

The models were forced to bound their internal mathematical states against:
1. **Non-Negativity**: {t+1} \ge 0$.
2. **Maximum Reservoir Capacity**: {t+1} \le 100.0$.
3. **Maximum Rate of Change**: $|h_{t+1} - h_t| \le 15.0$ per timestep (kinematic limit).

## 2. Model Variants
We compared three paradigms on identical chronological splits:
*   **(a) Unconstrained ML:** Standard Quantile Regression.
*   **(b) Post-Hoc Clipped:** The unconstrained model, with boundary rules deterministically applied over the output array.
*   **(c) Physics-Informed ML (PINN):** The unconstrained model, heavily penalized by physics boundaries directly within the loss function ({total} = L_{pinball} + \lambda L_{physics}$).

*⚠️ WARNING: The underlying topological flow limits in this specific ablation were evaluated on a SYNTHETIC Topology for methodological demonstration. The boundaries show methodological value only; they do not represent real-network Chennai capacities.*

## 3. Results: Out-Of-Distribution (OOD) Extrapolation
*(Data Source: esults/physics_constraints.csv)*

| Variant | Violation Rate (Test) | OOD Violation Rate | RMSE (Test) | OOD RMSE | POD | FAR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Unconstrained | 16.8% | 62.6% | 2.50 | 13.31 | 0.96 | 0.46 |
| **Post-Hoc Clipped** | **0.0%** | **0.0%** | **1.44** | **1.60** | **0.96** | **0.12** |
| Physics-Informed | 1.8% | 29.8% | 3.33 | 8.40 | 0.65 | 0.17 |

## 4. Key Scientific Findings
1.  **Unconstrained Catastrophe during OOD:** When exposed to heavier-than-training rainfall shocks (Out-Of-Distribution), the Unconstrained model hallucinated massively, violating physical capacities .6\%$ of the time and skyrocketing the RMSE to .31$.
2.  **PINNs Struggle with Optimization:** Forcing physics strictly into the loss function ("Physics-Informed") actually *degraded* nominal performance (Test RMSE rose from .50 \to 3.33$ and POD dropped to .65$). The gradients from the boundary penalties overwhelmed the statistical pinball gradients, leading to underfitting.
3.  **Post-Hoc Clipping is Superior:** Allowing the ML model to focus purely on statistical correlation and then deterministically applying physical boundaries post-hoc was wildly superior. It mathematically eliminated violations (.0\%$), dropped False Alarms from .46 \to 0.12$, and gracefully absorbed the OOD shock (RMSE held tight at .60$).
