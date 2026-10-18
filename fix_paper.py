import os
filepath = r'C:\Users\gokul\.gemini\antigravity\brain\f13ff3a2-9454-4fd2-a9a1-0612c5f6f992\paper_draft.md'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_table = \"\"\"## 2.5 Cross-City Transfer (Chennai $\\to$ Mumbai)
| Experiment | ROC AUC | F1 Score | Brier Score |
| :--- | :--- | :--- | :--- |
| Same City Baseline (Train B $\\to$ Test B) | 0.974 | 0.918 | 0.062 |
| **Domain Adaptation (Covariate Alignment)**| **0.974** | **0.916** | **0.061** |
| Post-Hoc Recalibration (50 samples) | 0.953 | 0.903 | 0.077 |
| Few-Shot Fine-Tuning (50 samples) | 0.948 | 0.842 | 0.120 |
| Zero-Shot (Train A $\\to$ Test B) | 0.972 | 0.733 | 0.364 |\"\"\"

new_table = \"\"\"## 2.5 Cross-City Transfer (Chennai $\\to$ Mumbai)
| Experiment | POD | FAR | RMSE |
| :--- | :--- | :--- | :--- |
| **Zero-Shot (Train A $\\to$ Test B)** | 0.143 | 0.961 | 0.443 |
| **After Light Re-Calibration** | 0.000 | 1.000 | 0.443 |
*Measured on Open-Meteo Historical API, BMC Disaster Management Reports, and WRD Maharashtra.*\"\"\"

content = content.replace(old_table, new_table)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)