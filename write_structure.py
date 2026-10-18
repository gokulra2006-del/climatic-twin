import os

files = {}

files["requirements.txt"] = '''numpy==1.26.4
pandas==2.2.1
scikit-learn==1.4.1.post1
scipy==1.12.0
torch==2.2.1
networkx==3.2.1
pytest==8.1.1
fastapi==0.110.0
uvicorn==0.27.1
paho-mqtt==2.0.0
shap==0.45.0
'''

files["Dockerfile"] = '''FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/app
CMD ["python", "scripts/evaluate_baselines.py"]
'''

files["Makefile"] = '''.PHONY: install test smoke-test run-all baseline enkf gnn_lstm uncertainty cascade compound dca faults transfer human

install:
	pip install -r requirements.txt

test:
	pytest backend/tests/

smoke-test:
	python scripts/experiment_compound_risk.py

baseline:
	python scripts/evaluate_baselines.py

enkf:
	python scripts/experiment_enkf.py

gnn_lstm:
	python scripts/experiment_gnn_lstm.py

uncertainty:
	python scripts/experiment_uncertainty.py

cascade:
	python scripts/experiment_cascade.py

compound:
	python scripts/experiment_compound_risk.py

dca:
	python scripts/experiment_dca.py

faults:
	python scripts/experiment_fault_tolerance.py

transfer:
	python scripts/experiment_city_transfer.py

human:
	python scripts/experiment_human_factors.py

run-all: baseline enkf gnn_lstm uncertainty cascade compound dca faults transfer human
'''

files[".github/workflows/ci.yml"] = '''name: CI Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python 3.12
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run Pytest Suite
      run: |
        pytest backend/tests/
    - name: Smoke Test (Compound Risk)
      run: |
        python scripts/experiment_compound_risk.py
'''

files["MODEL_CARDS.md"] = '''# Model Cards

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
'''

files["ETHICS.md"] = '''# Privacy & Ethics Statement

## 1. Data Privacy
This repository processes aggregate, anonymized environmental and infrastructure telemetry. No Personally Identifiable Information (PII) is stored. Synthetic simulators used for missing grid telemetry are mathematically isolated and strictly explicitly labeled to prevent passing generated data off as physical historical records.

## 2. Resource Allocation Bias
The Impact-Based Warning engine incorporates an Equity-Weighted Priority Score mapping vulnerabilities to risk. Care must be taken to regularly audit the ulnerability and service_criticality constants assigned to infrastructure classes (e.g., ensuring residential sectors are not structurally down-weighted in favor of commercial districts).

## 3. Automation and Human-in-the-Loop (HITL)
Models in this framework are strictly Decision-Support Systems. They compute expected utilities and decision curves to *recommend* actions, but cannot actuate physical infrastructure (e.g., redirecting grid power) without human authorization. The Scenario-Replay analytics suite explicitly tracks Alert Fatigue to prevent automation complacency.
'''

files["docs/API.md"] = '''# REST API Documentation

*   **GET /** : System Health Check
*   **POST /predict** : Ingests a JSON payload containing raw features [rain, temp, wind, reservoir] and returns the forecasted GNN-LSTM quantiles (P10, P50, P90).
*   **POST /cascade/whatif** : Submits an intervention graph edge-mask (e.g., "Pump A Offline"). Returns the $\Delta$ in expected failure probability across the graph via Monte Carlo simulation.
*   **GET /alerts/active** : Returns the real-time DCA-optimized Impact Warnings containing Equity Priority Scores and Recommended Actions.
'''

files["README.md"] = '''# ClimateTwin: Urban Multi-Hazard Early Warning

A journal-grade, fully reproducible computational pipeline for urban digital twin infrastructure, compound climate risk, and causal cascading failure modeling.

## 🚀 Quickstart & Reproducibility

### 1. Installation
Using Docker:
`ash
docker build -t climatetwin .
docker run -it climatetwin
`
Or locally:
`ash
pip install -r requirements.txt
`

### 2. Run the Full Experimental Suite
You can reproduce every metric, table, and ablation study directly using the Makefile:
`ash
make run-all
`
*Note: All experimental CSVs and latex metrics are output to the docs/ folder.*

### 3. Individual Table Reproducibility
*   **Table 1: Baseline Metrics & Chronological Splits:** make baseline
*   **Table 2: EnKF Sensor Dropout vs Nudging:** make enkf
*   **Table 3: GNN-LSTM Quantile Ablations:** make gnn_lstm
*   **Table 4: Bayesian Cascade & Sensitivity:** make cascade
*   **Table 5: Compound Risk Interaction Weights:** make compound
*   **Figure 1: Decision Curve Analysis (Utility):** make dca
*   **Figure 2: Transfer Learning (City A to B):** make transfer
*   **Table 6: Fault Tolerance Degradation:** make faults
*   **Table 7: NASA-TLX Cognitive Workload:** make human

## 📊 Global Random Seeds & Data Integrity
All models utilize standard chronological boundaries enforced by ackend/app/core/reproducibility.py. Random operations trace back to a global seed=42.

## 📜 Legal
Review ETHICS.md and MODEL_CARDS.md prior to deployment.
'''

for file_path, content in files.items():
    os.makedirs(os.path.dirname(os.path.join(r"C:\Users\gokul\Desktop\PROJECTS\climatetwin", file_path)) or ".", exist_ok=True)
    with open(os.path.join(r"C:\Users\gokul\Desktop\PROJECTS\climatetwin", file_path), "w", encoding="utf-8") as f:
        f.write(content)

print("Successfully wrote all journal-grade project structure files.")
