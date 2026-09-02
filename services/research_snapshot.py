"""Read and write offline LLM analysis snapshots used by the dashboard."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


SNAPSHOT_PATH = Path(os.getenv("RESEARCH_SNAPSHOT_PATH", "data/research_snapshots/latest.json"))
ANALYSIS_FIELDS = (
    "moat_score", "moat_rationale", "moat_evidence_ids",
    "growth_forecast_pct", "growth_rationale", "growth_evidence_ids",
    "concentration_risk", "cyclicality_risk", "execution_risk",
    "risk_rationale", "risk_evidence_ids", "analysis_confidence",
    "analysis_status", "research_as_of",
)


def evidence_fingerprint(record: dict) -> str:
    evidence = [
        {
            "url": item.get("url", ""),
            "claim": item.get("claim", ""),
            "published_date": item.get("published_date", ""),
        }
        for item in record.get("evidence", [])
        if isinstance(item, dict)
    ]
    payload = {"company": record.get("company", ""), "evidence": evidence}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def load_snapshot(path: str | Path | None = None) -> dict[str, dict]:
    try:
        payload = json.loads(Path(path or SNAPSHOT_PATH).read_text(encoding="utf-8"))
        records = payload.get("records", {}) if isinstance(payload, dict) else {}
        return records if isinstance(records, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def apply_snapshot(record: dict, snapshots: dict[str, dict]) -> None:
    snapshot = snapshots.get(str(record.get("company", "")), {})
    if not isinstance(snapshot, dict) or snapshot.get("evidence_fingerprint") != evidence_fingerprint(record):
        return
    for field in ANALYSIS_FIELDS:
        if field in snapshot:
            record[field] = snapshot[field]


def snapshot_entry(record: dict) -> dict:
    entry = {field: record[field] for field in ANALYSIS_FIELDS if field in record}
    entry["evidence_fingerprint"] = evidence_fingerprint(record)
    return entry


def write_snapshot(records: dict[str, dict], path: str | Path | None = None) -> None:
    destination = Path(path or SNAPSHOT_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({"records": records}, indent=2, sort_keys=True), encoding="utf-8")
