# Tier 3 Capabilities: Future Work & Stubs

The following capabilities have been architecturally scoped but are intentionally marked as **Future Work (Tier 3)**. They require additional data acquisition, field validation, or ethical clearance before implementation.

## 1. Recovery & Restoration Forecasting
**Objective:** Predict the temporal trajectory of infrastructure recovery (e.g., how many hours until a flooded substation is re-energized) rather than just the onset of failure.
*   **Required Data:** Granular repair logs, municipal dispatch times, parts availability, and water-recession telemetry.
*   **Proposed Method:** Autoregressive survival models (e.g., Weibull accelerated failure time) conditioned on physical flood drainage rates.
*   **Implementation Status:** *STUBBED.* Awaiting digital-twin integration with the municipal repair-ticketing system.

## 2. Equity-Weighted Priority
**Objective:** Weight the early-warning and action-optimization objective functions by socio-economic vulnerability (e.g., prioritizing low-income or physically vulnerable wards during pump deployments).
*   **Required Data:** High-resolution demographic census data, historical damage-burden assessments, and formal ethical approval from municipal stakeholders.
*   **Proposed Method:** Formulate a constraint-based optimization function where the cost of a missed warning ({MISS}$) is scaled dynamically by a normalized Vulnerability Index (VI).
*   **Implementation Status:** *STUBBED.* Awaiting formal ethical review and verified socio-economic polygons to prevent algorithmic bias or redlining.

## 3. Action Optimization with Real Operators
**Objective:** Implement Human-in-the-Loop (HITL) reinforcement learning where actual municipal dispatchers provide reward signals based on the digital twin's operational recommendations.
*   **Required Data:** Live shadow-mode deployment in the Chennai control room, capturing real operator Accept/Reject decisions on model recommendations over a monsoon season.
*   **Proposed Method:** Offline Reinforcement Learning (e.g., Conservative Q-Learning) trained on logged operator interventions, transitioning to live RLHF (Reinforcement Learning from Human Feedback).
*   **Implementation Status:** *STUBBED.* Currently, all action optimization in this repository is mathematically simulated. Real-operator calibration requires field deployment and shadow-testing.

## 4. Real Second-City Transfer
**Objective:** Validate the domain adaptation techniques on a physical second city (e.g., Mumbai) using verified historical ground-truth.
*   **Required Data:** Physical IMD radar telemetry, confirmed flood extents, and verified infrastructure topology bounds for Mumbai.
*   **Proposed Method:** Zero-shot transfer followed by Unsupervised Covariate Alignment (whitening) and Few-Shot fine-tuning on the real target distribution.
*   **Implementation Status:** *STUBBED.* Current cross-city domain adaptation is validated against a *simulated/synthetic* Mumbai distribution. Sourcing and cleaning real cross-country data is targeted for subsequent phases.
