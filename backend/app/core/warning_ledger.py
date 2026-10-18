"""In-memory, provenance-aware warning ledger for retrospective evaluation.

The ledger intentionally stores only warnings explicitly exported by a model run.
It is a prototype persistence layer; production deployment should use a versioned
database table and immutable event store.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List

_warnings: List[Dict[str, Any]] = []


def add_warning(warning: Dict[str, Any]) -> Dict[str, Any]:
    record = {
        **warning,
        "warning_id": f"WRN-{len(_warnings) + 1:05d}",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    _warnings.append(record)
    return record


def list_warnings() -> List[Dict[str, Any]]:
    return list(reversed(_warnings))
