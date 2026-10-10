# Phase 18: Explainable AI & Risk Reasoning Report

## Objective
To add a research-grade Explainable AI (XAI) and Decision Support layer to the ClimateTwin project. This layer sits above existing validated hazard models to dynamically extract reasoning, identify drivers/protective factors, evaluate trend and data quality, and propose recommended priorities.

## Architecture

- **`backend/app/core/explainability.py`**: The core XAI engine. It processes raw feature inputs and hazard risk level outputs to determine heuristic-based drivers and mitigators. It dynamically constructs a hierarchical reasoning tree.
- **`backend/app/api/api_v1/endpoints/explainability.py`**: Exposes REST interfaces to access the generated JSON explanations.

## Capabilities Integrated
1. **Dominant Drivers & Protective Factors**: Uses logic tied directly to raw features (e.g. Temp > 35°C vs < 35°C) to surface the underlying causality of the Random Forest model's output.
2. **Change Intelligence**: Tracks deltas between current observations and the previous telemetry cycle to alert operators of accelerating dynamics.
3. **Trend Classification**: Automatically classifies conditions into trajectories (INCREASING, DECREASING, STABLE).
4. **Confidence-Aware Integration**: Embeds conformal prediction intervals into a readable "High/Moderate/Low" metric.
5. **Asset-Aware Decision Support**: Recommends operational actions based on the current hazard tier.

## Validation Results
- Executed `scripts/validate_phase18_explainability.py`.
- Successfully validated dynamic rendering of all 18 specified metrics in the JSON payload.
- Zero mutations to underlying, pre-validated Flood and Heatwave models.

## Limitations
- **Decision Support is not Autonomous**: The recommendations are heuristics and are designed strictly for domain-expert interpretation.
- **Model Reasoning Abstraction**: The explanation sits *above* the underlying Random Forest models as a transparent layer rather than exposing exact internal weights.
