# Chennai Urban Climate Digital Twin: Benchmark Data Card

## 1. Dataset Overview
This benchmark evaluates early warning systems for compound urban flooding and infrastructure cascades. 
**Crucial Distinction:** The dataset strictly partitions real historical observations from procedurally generated synthetic network impacts. 
*   **REAL Subset:** Historical IMD rainfall observations, validated tidal gauges, and verified city flood-complaint temporal boundaries (2015-2023).
*   **SYNTHETIC Subset:** Simulated graph-based cascading infrastructure failures (power, pump overloads) generated on a synthetic scale-free topology.

## 2. Fixed Splits
To prevent temporal leakage, all splits are strictly chronological:
*   **Train:** 2015-01-01 to 2019-12-31
*   **Validation:** 2020-01-01 to 2021-12-31
*   **Test (Untouched):** 2022-01-01 to 2023-12-31

## 3. License & Ethics
*   **License:** MIT for code, CC-BY-NC 4.0 for data (Non-Commercial Academic Use Only).
*   **Ethics & Privacy:** This dataset contains aggregate, anonymized infrastructure state data. No Personally Identifiable Information (PII) or individual location tracking is included. Do not use this benchmark to train operational enforcement or punitive civic models.
