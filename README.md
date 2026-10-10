# ClimateTwin: Urban Multi-Hazard Early Warning

## Research status

ClimateTwin is a research prototype and reproducible evaluation workflow. It is not a field-validated or fully operational municipal digital twin. Results must be interpreted according to the real, proxy, and synthetic data labels in the experiment artifacts.

The literature-grounded research-gap analysis is available at [`docs/research_gap_literature_analysis.md`](docs/research_gap_literature_analysis.md).

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
