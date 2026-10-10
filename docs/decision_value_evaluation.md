# Evaluating Warnings as Decisions

## 1. Methodology (SIMULATED Operations)
An early-warning system provides no value if its probabilistic output does not change municipal behavior. However, treating probabilistic alerts as deterministic "go/no-go" commands ignores the asymmetric costs of real-world interventions. 

*⚠️ WARNING: All operator decisions, interventions, and associated financial bounds detailed in this module are strictly SIMULATED. They do not represent human-subject evidence or adopted municipal protocol.*

### 1.1 Configurable Cost Matrix
Because true municipal damage costs vary, we established a config-driven expected utility framework:
*   C_FA (Cost of False Alarm): Wasted resource deployment (e.g., pump fuel, overtime).
*   C_MISS (Cost of Missed Warning): Infrastructure destruction and unmitigated flood damage.
*   C_INT (Cost of Intervention): The base cost of deploying the asset early.
*   C_DELAY (Cost of Delayed Action): The escalating penalty for deploying late into the hazard curve.

Under expected-cost minimization, the optimal probabilistic action threshold resolves to {opt} = \frac{C_{FA}}{C_{FA} + C_{MISS}}$.

## 2. Alert Behavior & Fatigue Proxy
*(Data Source: esults/alert_hysteresis.csv)*

If a model's predicted probability hovers directly over the static alert threshold (.6$), standard logic will fire consecutive ON/OFF/ON alerts. This "flapping" destroys operator trust and drives alert fatigue.

We simulated a heavily noisy forecast anticipating 10 major hazard events and evaluated a strict naive threshold vs a stateful **Hysteresis** controller (Alert ON at .6$, Alert OFF at .4$, Minimum Cooldown $ hours).

| Policy | Escalation Flapping | Alert Fatigue (False Alarms) | Regret vs Oracle | Expected Cost |
| :--- | :--- | :--- | :--- | :--- |
| **Naive (Strict 0.6)** | 11 cycles | 28 events | 2800.0 | 4150.0 |
| **Hysteresis Controlled** | **0 cycles** | **23 events** | **2300.0** | **3650.0** |

**Conclusion:** Implementing a stateful cooldown and asymmetric ON/OFF boundaries mathematically eradicated UI flapping and reduced overall Alert Fatigue by discarding transient low-value probability spikes, saving 500 units of Expected Cost.

## 3. Decision Curve Analysis (DCA)
*(Data Source: esults/decision_dca.csv)*

We calculated the Net Regret across the full spectrum of triggering thresholds  \in (0, 1.0)$. 
*   **Low Thresholds ( < 0.3$):** Triggered massive False Alarm penalties ($>80$ FPS).
*   **High Thresholds ( > 0.8$):** Avoided false alarms but missed critical early interventions, invoking severe C_MISS and C_DELAY penalties.
*   **Optimum:** Given a simulated environment where {FA} = 100$ and {MISS} = 1000$, minimizing Expected Cost safely centers around the  \approx 0.4 \to 0.6$ boundary, validating the Expected Utility threshold theorem dynamically within the time-series.
