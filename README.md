# ClimateTwin: Urban Multi-Hazard Early Warning & Evidence Review System

## Research Status & Scientific Provenance

ClimateTwin is an academic research prototype and reproducible evaluation system for urban multi-hazard modeling across Greater Chennai Corporation (GCC) limits. 

- **Traceability Guarantee:** Results must be interpreted strictly according to explicit data provenance labels: `HISTORICAL REAL`, `PROXY / DERIVED`, `SYNTHETIC DEMO`, `RULE-BASED`, and `FALLBACK`.
- **Integrity Rule:** Simulated, proxy, and synthetic test scenarios are **strictly excluded** from empirical benchmark scores (Precision, Recall, F1, Brier Score).
- **Literature Analysis:** See [`docs/research_gap_literature_analysis.md`](docs/research_gap_literature_analysis.md) and [`docs/data_cards/chennai_impact_catalogue_data_card.md`](docs/data_cards/chennai_impact_catalogue_data_card.md).

---

## 🏛️ Impact Catalogue & Evidence Review System

ClimateTwin includes an auditable evidence-confidence architecture connecting digital twin warning outputs to documented real-world municipal impact endpoints:

### 1. Evidence-Confidence Rubric (0–100 Points)
For source-backed records undergoing peer review, confidence is calculated via a transparent 5-criteria rubric:
*   **25 Points:** Authoritative Primary Source (Central Water Commission, IMD, Greater Chennai Corporation, TNSDMA, CMWSSB, WRD).
*   **20 Points:** Exact Event Date & Time (Verified onset timestamp with minute/hour precision).
*   **20 Points:** Precise Coordinates (Surveyed sub-500m coordinates or designated infrastructure asset pin).
*   **20 Points:** Independent Corroborating Source (Secondary source URL from distinct publishing agency).
*   **15 Points:** Observed Physical Impact Measurement (Flood extent $\text{km}^2$, depth $\text{m}$, road closure hours, outage duration, or gauge level).

> **Synthetic Exclusion:** Demonstration / synthetic records receive **no confidence score** (`None`) and display `"Add verified source"`. They cannot be cited in paper benchmark tables.

### 2. Official Source Intake Workflow
*   **Source Registry:** Ingests official documentation from CWC, IMD, GCC, TNSDMA, and CMWSSB.
*   **Intake Validation:** Enforces `source_url`, `source_org`, `source_ref_id`, and `access_date`.
*   **Human Curator Sign-Off:** Imported records enter as `under_review` and require curator review before `historical_real` certification.
*   **Cryptographic Provenance:** Generates SHA-256 hashes for attached PDF/image reports.
*   **Paper Appendices:** Generates exportable Markdown evidence cards and LaTeX appendix tables (`\begin{table*}...\end{table*}`).

### 3. Empirical Warning Validation & Brier Score
*   Evaluates warning predictions strictly against certified `historical_real` impact records.
*   Outputs: Precision, Recall, F1-Score, Mean Warning Lead Time, False Alarms, and Brier Score.
*   Enforces sample size integrity warnings: $N < 10$ flagged as underpowered; $N \ge 30$ required for generalized paper claims.

### 4. 2-D Hydraulic Validation Readiness
*   Checks for empirical observed flood extents ($\text{km}^2$) and surveyed depth watermarks ($\text{m}$).
*   **Mandatory boundary:** Prevents claiming 2-D hydrodynamic depth validation without observed SAR/gauge ground truth; labels current inundation outputs strictly as **DEM-constrained scenario approximations**.

---

## 🚀 Quickstart & Local Execution

### 1. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows: venv\Scripts\activate (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```
Access the application at `http://127.0.0.1:5174`.

### 3. Run Backend Test Suite
```bash
.\backend\venv\Scripts\python.exe -m pytest backend/tests/test_impact_catalogue.py backend/tests/test_evidence_rubric.py
```

---

## 📡 API Endpoints (Evidence Review & Impact Catalogue)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/impacts/` | List and filter impact records with live 0–100 rubric confidence breakdown |
| `GET` | `/api/impacts/{id}` | Retrieve record details, rubric breakdown, missing items, and provenance |
| `POST` | `/api/impacts/` | Create a new impact record (queued as `under_review`) |
| `POST` | `/api/impacts/{id}/review` | Submit curator audit decision (`approved_historical_real`, `rejected`, etc.) |
| `POST` | `/api/impacts/upload-attachment` | Upload supporting document, compute SHA-256 cryptographic hash |
| `GET` | `/api/impacts/{id}/evidence-card` | Export evidence card in JSON, Markdown, and LaTeX table row format |
| `GET` | `/api/impacts/export/appendix` | Export all verified records as a complete IEEE/Journal Appendix LaTeX table |
| `GET` | `/api/impacts/validation-readiness` | Check whether observed flood extent/depth data permit 2-D hydraulic validation |
| `GET` | `/api/impacts/evidence-sources` | List authenticated municipal and state government intake channels |
| `GET` | `/api/impacts/export/csv` | Export entire catalogue as CSV with audit and confidence metadata |
| `POST` | `/api/impacts/import/csv` | Batch import records via CSV with strict schema and source enforcement |
| `POST` | `/api/impacts/evaluate` | Run spatial-temporal matching strictly against `historical_real` ground truth |

---

## 📊 Global Random Seeds & Data Integrity
All models utilize standard chronological boundaries enforced by `backend/app/core/reproducibility.py`. Random operations trace back to a global `seed=42`.

## 📜 Legal & Ethics
Review `ETHICS.md` and `MODEL_CARDS.md` prior to deployment.
