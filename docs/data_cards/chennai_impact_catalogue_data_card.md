# Data Card: Chennai Urban Historical Impact Catalogue (v2.0)
**Conference & Journal Submission Protocol for Traceable Urban Impact Evidence**

---

## 1. Overview & Provenance
The **Chennai Urban Historical Impact Catalogue** is a versioned, peer-auditable ground-truth repository designed to connect multi-hazard digital twin warnings to documented physical municipal endpoints across the Greater Chennai Corporation (GCC) and Chennai Metropolitan Area (CMA).

- **Spatial Extent:** Greater Chennai ($12.85^\circ\text{N} - 13.25^\circ\text{N}$, $80.00^\circ\text{E} - 80.35^\circ\text{E}$), EPSG:4326.
- **Temporal Envelope:** 2015 to present (including major documented events: 2015 South India Floods, 2023 Cyclone Michaung, 2024 monsoon season).
- **Curator Protocol:** Mandatory human hydrologist / GIS curator sign-off before any record is certified as `historical_real`.
- **Integrity Rule:** Demonstration/synthetic records are strictly isolated, carry no confidence score, and are mathematically excluded from empirical performance metrics.

---

## 2. Evidence Status Taxonomy
Records are strictly classified into six mutually exclusive audit tiers:

| Evidence Status | Definition | Scientific Use Allowed |
| :--- | :--- | :--- |
| `historical_real` | Verified empirical observation documented in official government gazettes, CWC reports, or satellite SAR inundation delineations with primary source URL, page citation, and curator sign-off. | **Permitted** for empirical benchmark validation (Precision, Recall, F1, Lead Time, Brier Score). |
| `under_review` | Official or secondary intake record undergoing curator audit, source verification, or coordinate precision validation. | Restricted to exploratory analysis; excluded from publication benchmark tables until approved. |
| `proxy` | Inferred from operational municipal utility telemetry (e.g. TANGEDCO feeder tripping log, CMWSSB sluice discharge logs) without direct physical flood depth watermark. | Allowed only for sensitivity analysis; explicitly labelled PROXY. |
| `unverified` | Citizen grievance portal entries (e.g. GCC PGR) or news reports without primary engineering coordinates or official verification. | Prohibited from benchmark scoring. |
| `synthetic` | Computationally generated stress-test scenarios or bundled UI placeholders. Receives **no confidence score** ("Add verified source"). | **Strictly excluded** from all empirical benchmark metrics and paper evidence tables. |
| `rejected` | Submitted records failing provenance audit, lacking traceable URLs, or providing non-authoritative claims. | Retained in audit trail for peer-review transparency. |

---

## 3. Evidence-Confidence Rubric (0–100 Points)
For source-backed, reviewed records, confidence is determined via a deterministic 5-criteria point rubric:

$$\text{Confidence Score} = S_{\text{auth}} (25) + S_{\text{time}} (20) + S_{\text{loc}} (20) + S_{\text{corrob}} (20) + S_{\text{meas}} (15)$$

1. **Authoritative Primary Source (25 Points):**
   - Issued by an authorized government body (Central Water Commission, IMD, Greater Chennai Corporation, TNSDMA, CMWSSB, Water Resources Department, TANGEDCO).
   - Valid, permanent URL to official report or bulletin.
2. **Exact Event Date & Time (20 Points):**
   - Verified event onset timestamp with minute/hour precision documented in official dispatch log. (Broad multi-day windows without onset timing score 0 points).
3. **Precise Coordinates or Asset Landmark (20 Points):**
   - Surveyed sub-500m coordinates, arterial road stretch, or critical infrastructure asset pin. (Generic citywide centroids score 0 points).
4. **Independent Corroborating Source (20 Points):**
   - Secondary source URL from an independent agency or portal confirming event timing and spatial impact.
5. **Observed Physical Impact Measurement (15 Points):**
   - Quantified ground-truth measurement: observed flood extent ($\text{km}^2$), surveyed water depth ($\text{m}$), road closure duration ($\text{h}$), power outage duration ($\text{h}$), or gauge level ($\text{m}$).

> **Synthetic Exclusion Rule:** Synthetic records receive $\text{score} = \text{None}$ and display `"Add verified source"`. They never receive an empirical score.

---

## 4. Official Source Intake Registry
The catalogue ingests data exclusively through authenticated channels:
- **Central Water Commission (CWC):** Flood Forecasting and Warning Network Annual Reports, reservoir daily bulletins.
- **India Meteorological Department (IMD):** Station AWS precipitation, Cyclone track reports.
- **Greater Chennai Corporation (GCC):** Stormwater Drainage department field reports, ward-level pump station logs.
- **Tamil Nadu State Disaster Management Authority (TNSDMA):** Official Disaster Situation Reports (Sitreps) and emergency management records.
- **Chennai Metropolitan Water Supply and Sewerage Board (CMWSSB) / WRD:** Chembarambakkam, Poondi, Redhills lake storage logs and sluice discharge rates.
- **TANGEDCO & Emergency Logistics:** Feeder blackout logs and 108 hospital ambulance accessibility registers.

Every intake record requires:
1. Traceable URL.
2. Source Organization.
3. Reference ID or Report Page.
4. Access / Retrieval Date.
5. Cryptographic SHA-256 Document Hash (if attachment provided).

---

## 5. Model Warning Validation & Empirical Evaluation Workflow
Model-generated warnings are evaluated strictly against `historical_real` ground-truth records using spatial-temporal envelopes:

- **Spatial Radius:** Configurable ($0.1 - 50.0\text{ km}$, default $5.0\text{ km}$).
- **Time Window:** Prior warning lead time window ($0 - 6\text{ hours}$).
- **Reported Metrics:**
  - Event Detection Rate / Recall: $\frac{TP}{TP + FN}$
  - Precision: $\frac{TP}{TP + FP}$
  - $F_1\text{-Score}$: $2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$
  - Mean Warning Lead Time: $\frac{1}{TP}\sum (t_{\text{impact}} - t_{\text{warning}})$
  - Brier Score: $\frac{1}{|W|}\sum_{w=1}^{|W|} (p_w - o_w)^2$
- **Sample Size Integrity Boundaries:**
  - $N < 10$: Explicit caution displayed: `"Sample size is statistically underpowered for publication claims. Minimum recommended N >= 30."`
  - $10 \le N < 30$: Reported strictly as exploratory case-study validation.
  - $N \ge 30$: Statistically powered for conference/journal performance claims.

---

## 6. Observed Flood Extent & 2-D Hydraulic Validation Boundaries
- **Validation Readiness Check:** The platform explicitly queries whether verified satellite SAR flood extents (e.g. Sentinel-1 Copernicus EMS) and depth watermarks exist.
- **Mandatory Caveat:** If observed flood extent polygons and depth measurements are absent, the system explicitly disallows claiming "2-D hydraulic validation" in manuscripts, requiring all flood projections to be labelled strictly as **"DEM-constrained scenario approximations"**.

---

## 7. Cryptographic Document Hashing & Appendices
- All supporting evidence PDFs and field photographs are hashed using SHA-256 upon upload.
- Full provenance tables can be exported as LaTeX snippets (`\begin{table*}...\end{table*}`) or Markdown evidence cards for direct inclusion in IEEE / Elsevier conference and journal appendices.
