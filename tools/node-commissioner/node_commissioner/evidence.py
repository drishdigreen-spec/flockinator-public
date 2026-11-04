"""Immutable per-run observations; manual acceptance is always a separate record."""
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from .protocol import validate_status


def redact(value):
    if isinstance(value, dict):
        return {key: ("[REDACTED]" if key.lower() in {"ssid", "password", "key", "token", "format_token", "authorization"} or "password" in key.lower() or key.lower().endswith("_key") else redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def save_run(root: Path, label: str, mac: str, snapshot: dict, source: str) -> Path:
    validate_status(snapshot, mac, label)
    now = datetime.now(timezone.utc)
    run = now.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    directory = root / label / run
    directory.mkdir(parents=True, exist_ok=False)
    path = directory / "status.json"
    payload = dict(schema_version=1, observed_at_utc=now.isoformat(), source=source, provisioning="identity_verified", manual_acceptance="PENDING", snapshot=redact(snapshot))
    with path.open("x") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")
    return path
