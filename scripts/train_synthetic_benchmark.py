"""Build a reproducible *synthetic-only* flood-risk benchmark for ClimateTwin.

This script exists for UI demonstrations, software regression tests, and method
ablations.  It never overwrites the deployed model and its metrics must not be
reported as field validation or real-world accuracy.
"""
from __future__ import annotations

import json
import pickle
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
OUT_DATA = ROOT / "data" / "simulated" / "chennai_synthetic_flood_benchmark_v1.csv"
OUT_MODEL = ROOT / "backend" / "app" / "models" / "synthetic_benchmark_rf_v1.pkl"
OUT_METRICS = ROOT / "docs" / "synthetic_benchmark" / "metrics.json"
OUT_CARD = ROOT / "docs" / "synthetic_benchmark" / "dataset_card.md"
SEED = 20261017

FEATURES = [
    "rainfall_daily", "rainfall_3d_sum", "rainfall_5d_sum", "rainfall_7d_sum",
    "temp_mean", "temp_max", "temp_min", "dew_point_mean", "wind_speed_mean",
    "POONDI", "CHOLAVARAM", "REDHILLS", "CHEMBARAMBAKKAM", "total_reservoir_level",
]


def sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(values, -30, 30)))


def make_dataset() -> pd.DataFrame:
    """Generate daily time series with an explicit, documented data-generating process."""
    rng = np.random.default_rng(SEED)
    dates = pd.date_range("2014-01-01", "2022-12-31", freq="D")
    day = dates.dayofyear.to_numpy()
    # Northeast-monsoon signal peaking in late October/November, plus background rain.
    monsoon = np.exp(-0.5 * ((day - 315) / 38) ** 2)
    background = rng.gamma(shape=0.65, scale=2.1, size=len(dates))
    storm_probability = 0.018 + 0.22 * monsoon
    storms = rng.random(len(dates)) < storm_probability
    storm_depth = storms * rng.gamma(shape=2.0, scale=20.0 + 30.0 * monsoon)
    rainfall = np.clip(background + storm_depth, 0, 280)

    temperature = 29.0 + 2.7 * np.sin(2 * np.pi * (day - 100) / 365.25) - 0.8 * monsoon + rng.normal(0, 0.75, len(dates))
    humidity = np.clip(67 + 21 * monsoon + 0.10 * rainfall + rng.normal(0, 5, len(dates)), 35, 99)
    dew_point = temperature - (100 - humidity) / 5.0
    wind = np.clip(2.8 + 1.5 * monsoon + rng.gamma(1.2, 0.8, len(dates)), 0.3, 14)

    # Storage follows rain recharge, bounded physical capacities, and seasonal demand.
    capacities = np.array([3231.0, 1081.0, 3300.0, 3645.0])
    storage = np.zeros((len(dates), 4), dtype=float)
    storage[0] = capacities * np.array([0.58, 0.49, 0.61, 0.54])
    split = np.array([0.27, 0.10, 0.31, 0.32])
    for index in range(1, len(dates)):
        recharge = rainfall[index] * split * (2.8 + 1.2 * monsoon[index])
        demand = capacities * (0.0019 + 0.0005 * (1 - monsoon[index]))
        storage[index] = np.clip(storage[index - 1] + recharge - demand + rng.normal(0, 14, 4), 0, capacities)

    frame = pd.DataFrame({
        "date": dates,
        "rainfall_daily": rainfall,
        "temp_mean": temperature,
        "temp_max": temperature + rng.uniform(2.4, 5.3, len(dates)),
        "temp_min": temperature - rng.uniform(2.0, 4.0, len(dates)),
        "dew_point_mean": dew_point,
        "wind_speed_mean": wind,
        "POONDI": storage[:, 0],
        "CHOLAVARAM": storage[:, 1],
        "REDHILLS": storage[:, 2],
        "CHEMBARAMBAKKAM": storage[:, 3],
    })
    for window in (3, 5, 7):
        frame[f"rainfall_{window}d_sum"] = frame["rainfall_daily"].rolling(window, min_periods=1).sum()
    frame["total_reservoir_level"] = storage.sum(axis=1)

    # Latent flood process: antecedent rainfall plus high storage and wind. Noise
    # intentionally prevents a perfectly learnable target.
    storage_fraction = frame["total_reservoir_level"] / capacities.sum()
    latent = (
        -6.7
        + 0.024 * frame["rainfall_7d_sum"]
        + 0.012 * frame["rainfall_daily"]
        + 4.0 * storage_fraction
        + 0.11 * frame["wind_speed_mean"]
        + rng.normal(0, 0.85, len(frame))
    )
    frame["synthetic_event_probability"] = sigmoid(latent)
    frame["synthetic_flood_event"] = (rng.random(len(frame)) < frame["synthetic_event_probability"]).astype(int)
    frame["data_provenance"] = "SYNTHETIC_SIMULATION_V1"
    return frame[["date", *FEATURES, "synthetic_event_probability", "synthetic_flood_event", "data_provenance"]]


def score(model, x: pd.DataFrame, y: pd.Series) -> dict:
    probability = model.predict_proba(x)[:, 1]
    prediction = (probability >= 0.5).astype(int)
    calibration_bins = np.linspace(0, 1, 11)
    bin_index = np.clip(np.digitize(probability, calibration_bins) - 1, 0, 9)
    ece = 0.0
    for bucket in range(10):
        mask = bin_index == bucket
        if mask.any():
            ece += float(mask.mean()) * abs(float(probability[mask].mean()) - float(y.iloc[mask].mean()))
    return {
        "roc_auc": round(float(roc_auc_score(y, probability)), 4),
        "pr_auc": round(float(average_precision_score(y, probability)), 4),
        "f1": round(float(f1_score(y, prediction, zero_division=0)), 4),
        "precision": round(float(precision_score(y, prediction, zero_division=0)), 4),
        "recall": round(float(recall_score(y, prediction, zero_division=0)), 4),
        "brier": round(float(brier_score_loss(y, probability)), 4),
        "ece": round(float(ece), 4),
    }


def input_stress_test(model, x_test: pd.DataFrame) -> dict:
    """Probe safe, input-only robustness; no real-world performance claim is made."""
    rng = np.random.default_rng(SEED + 1)
    reference_probability = model.predict_proba(x_test)[:, 1]
    medians = x_test.median()

    missing = x_test.copy()
    missing_mask = rng.random(missing.shape) < 0.20
    missing = missing.mask(missing_mask, axis=0).fillna(medians)
    missing_probability = model.predict_proba(missing)[:, 1]

    heavy_rain = x_test.copy()
    rain_columns = ["rainfall_daily", "rainfall_3d_sum", "rainfall_5d_sum", "rainfall_7d_sum"]
    heavy_rain[rain_columns] = heavy_rain[rain_columns] * 1.35
    rain_probability = model.predict_proba(heavy_rain)[:, 1]

    return {
        "purpose": "Input sensitivity checks only. These are not field-validation metrics.",
        "missing_telemetry_20pct": {
            "method": "Randomly mask 20% of feature values and median-impute using the evaluation window.",
            "valid_prediction_rate": 1.0,
            "mean_absolute_probability_shift": round(float(np.mean(np.abs(missing_probability - reference_probability))), 4),
            "alert_rate_at_0_5": round(float(np.mean(missing_probability >= 0.5)), 4),
        },
        "heavy_rain_plus_35pct": {
            "method": "Increase rainfall and antecedent-rainfall inputs by 35%; labels are intentionally not reused.",
            "mean_probability_change": round(float(np.mean(rain_probability - reference_probability)), 4),
            "alert_rate_at_0_5": round(float(np.mean(rain_probability >= 0.5)), 4),
            "baseline_alert_rate_at_0_5": round(float(np.mean(reference_probability >= 0.5)), 4),
        },
    }


def main() -> None:
    frame = make_dataset()
    OUT_DATA.parent.mkdir(parents=True, exist_ok=True)
    OUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    OUT_METRICS.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT_DATA, index=False)

    train = frame[frame.date.dt.year <= 2020]
    validation = frame[frame.date.dt.year == 2021]
    test = frame[frame.date.dt.year == 2022]
    x_train, y_train = train[FEATURES], train.synthetic_flood_event
    models = {
        "Logistic regression": Pipeline([
            ("scale", StandardScaler()),
            ("model", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED)),
        ]),
        "Random forest": RandomForestClassifier(
            n_estimators=350, min_samples_leaf=3, max_depth=11, class_weight="balanced", random_state=SEED, n_jobs=-1
        ),
    }
    metrics = {}
    fitted = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        fitted[name] = model
        metrics[name] = {"validation_2021": score(model, validation[FEATURES], validation.synthetic_flood_event), "test_2022": score(model, test[FEATURES], test.synthetic_flood_event)}

    champion = fitted["Random forest"]
    with OUT_MODEL.open("wb") as output:
        pickle.dump({
            "model": champion,
            "features": FEATURES,
            "model_name": "ClimateTwin Synthetic Benchmark RF v1",
            "provenance": "SYNTHETIC_SIMULATION_V1",
            "deployment_policy": "BENCHMARK_ONLY_DO_NOT_DEPLOY",
            "training_window": "2014-01-01 to 2020-12-31",
        }, output)

    payload = {
        "benchmark_name": "ClimateTwin synthetic flood-risk benchmark v1",
        "provenance": "SYNTHETIC_SIMULATION_V1",
        "seed": SEED,
        "generated_rows": int(len(frame)),
        "positive_rate": round(float(frame.synthetic_flood_event.mean()), 4),
        "split": {"train": "2014-2020", "validation": "2021", "test": "2022"},
        "models": metrics,
        "champion": "Random forest",
        "calibration": {
            "test_2022_brier": metrics["Random forest"]["test_2022"]["brier"],
            "test_2022_ece": metrics["Random forest"]["test_2022"]["ece"],
            "meaning": "Calibration results are valid only for the simulated generator and chronological synthetic test period.",
        },
        "input_stress_tests": input_stress_test(champion, test[FEATURES]),
        "reproducibility": {
            "random_seed": SEED,
            "dataset_sha256": hashlib.sha256(OUT_DATA.read_bytes()).hexdigest(),
            "model_sha256": hashlib.sha256(OUT_MODEL.read_bytes()).hexdigest(),
            "rerun_command": "backend\\venv\\Scripts\\python.exe scripts\\train_synthetic_benchmark.py",
        },
        "deployment_policy": "BENCHMARK_ONLY_DO_NOT_DEPLOY",
        "claim_boundary": "Metrics measure recovery of this script's simulated data-generating process. They do not establish accuracy for Chennai flood impacts, inundation depth, or public-warning performance.",
    }
    OUT_METRICS.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUT_CARD.write_text(
        "# Synthetic Flood-Risk Benchmark v1\n\n"
        "**Status:** Synthetic benchmark only; not a replacement for field validation.\n\n"
        "This reproducible daily dataset contains simulated rainfall, rolling rainfall, weather and four-reservoir storage features for 2014--2022. "
        "The event label is sampled from a documented latent risk function with deliberate noise. Chronological train/validation/test periods prevent future-year leakage.\n\n"
        "## Permitted use\n\n"
        "- Regression tests, UI demos, model comparison and ablation experiments.\n"
        "- Training sandbox models that remain isolated from the deployed live model.\n\n"
        "## Prohibited claims\n\n"
        "- Do not call its scores Chennai field accuracy, flood validation, depth validation, or warning effectiveness.\n"
        "- Do not replace a production model with this artifact.\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
