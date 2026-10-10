# Data Quality & Sensor Health Methodology (Phase 16)

### Mathematical Quality Formulations

1. **Freshness Score ($S_{\text{fresh}}$)**:
   $$S_{\text{fresh}} = \max\left(0, 1 - \frac{\text{Data Age}}{1.5 \cdot T_{\text{stale}}}\right) \in [0.0, 1.0]$$

2. **Physical Plausibility ($P_{\text{phys}}$)**:
   $$\text{Rainfall} \in [0, 500]\text{ mm}, \quad \text{Temp} \in [15, 50]^\circ\text{C}, \quad \text{Wind} \in [0, 65]\text{ m/s}$$

3. **Temporal Innovation Anomaly ($z_{\text{temporal}}$)**:
   $$z = \frac{|x_t - \mu_{\text{rolling}}|}{\sigma_{\text{rolling}} + \epsilon}, \quad \text{Anomaly} = \mathbb{I}(z > 3.5 \lor |\Delta x| > \text{ROC}_{\max})$$

4. **Composite Sensor Health Score ($SHS$)**:
   $$SHS = 0.35 \cdot S_{\text{fresh}} + 0.25 \cdot C_{\text{ratio}} + 0.20 \cdot P_{\text{phys}} + 0.10 \cdot (1 - \text{Anomaly}) + 0.10 \cdot S_{\text{stuck}} \in [0.0, 1.0]$$

5. **Quality Tiers**:
   - `EXCELLENT`: $SHS \ge 0.88$
   - `GOOD`: $0.70 \le SHS < 0.88$
   - `DEGRADED`: $0.45 \le SHS < 0.70$
   - `POOR`: $0.20 \le SHS < 0.45$
   - `UNUSABLE`: $SHS < 0.20$
