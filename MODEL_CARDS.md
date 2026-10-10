# Model Cards

## 1. Multi-Relational GNN-LSTM Forecaster
*   **Architecture:** PyTorch Multi-Relational Graph Convolutional Network (GCN) coupled with LSTM sequences. Uses Quantile Regression (Pinball Loss) with explicit ReLU non-crossing constraints.
*   **Intended Use:** Spatiotemporal multi-hazard prediction across urban topologies (drainage, power, roads).
*   **Limitations:** High sensitivity to incorrect topologies. Requires accurate domain adaptation via covariate shift alignment before deploying to new cities.
*   **Training Data:** Strict chronological splits of multi-variate climate/sensor logs.

## 2. Bayesian Causal Cascade Engine
*   **Architecture:** Beta-Binomial Bayesian Updating over a Directed Acyclic Graph (DAG) with Exponential Survival Hazards.
*   **Intended Use:** Simulating downstream infrastructure cascading failures given a primary physical hazard.
*   **Limitations:** Assumes Markovian failure properties (time-to-failure relies only on current load, ignoring cumulative fatigue).

## 3. Probabilistic Compound Risk Engine
*   **Architecture:** L2-Regularized Logistic Regression with explicit interaction terms ($, $\gamma_{ij}$).
*   **Intended Use:** Mapping raw environmental hazard probabilities to true compound Impact Probabilities.
*   **Limitations:** Rare interactions rely heavily on the regularizer prior to prevent overfitting.
