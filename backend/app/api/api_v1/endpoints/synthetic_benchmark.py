"""Read-only endpoint for the clearly labelled synthetic benchmark."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()
ROOT = Path(__file__).resolve().parents[5]
METRICS_PATH = ROOT / "docs" / "synthetic_benchmark" / "metrics.json"


@router.get("/summary")
def benchmark_summary():
    if not METRICS_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Synthetic benchmark has not been generated. Run scripts/train_synthetic_benchmark.py first.",
        )
    try:
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Synthetic benchmark report is unreadable.") from exc
