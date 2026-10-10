# REST API Documentation

*   **GET /** : System Health Check
*   **POST /predict** : Ingests a JSON payload containing raw features [rain, temp, wind, reservoir] and returns the forecasted GNN-LSTM quantiles (P10, P50, P90).
*   **POST /cascade/whatif** : Submits an intervention graph edge-mask (e.g., "Pump A Offline"). Returns the $\Delta$ in expected failure probability across the graph via Monte Carlo simulation.
*   **GET /alerts/active** : Returns the real-time DCA-optimized Impact Warnings containing Equity Priority Scores and Recommended Actions.
