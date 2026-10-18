# Synthetic Flood-Risk Benchmark v1

**Status:** Synthetic benchmark only; not a replacement for field validation.

This reproducible daily dataset contains simulated rainfall, rolling rainfall, weather and four-reservoir storage features for 2014--2022. The event label is sampled from a documented latent risk function with deliberate noise. Chronological train/validation/test periods prevent future-year leakage.

## Permitted use

- Regression tests, UI demos, model comparison and ablation experiments.
- Training sandbox models that remain isolated from the deployed live model.

## Prohibited claims

- Do not call its scores Chennai field accuracy, flood validation, depth validation, or warning effectiveness.
- Do not replace a production model with this artifact.
