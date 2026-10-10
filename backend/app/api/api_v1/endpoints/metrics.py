from fastapi import APIRouter
from typing import Dict

router = APIRouter()

@router.get("/latency")
def get_latency_metrics() -> Dict[str, str]:
    # Placeholder for Phase 4 metrics
    return {
        "ingestion_latency_ms": "0",
        "processing_latency_ms": "0",
        "prediction_latency_ms": "0",
        "warning_latency_ms": "0",
        "end_to_end_latency_ms": "0"
    }

@router.get("/system")
def get_system_metrics() -> Dict[str, str]:
    return {
        "status": "healthy",
        "active_connections": "0"
    }
