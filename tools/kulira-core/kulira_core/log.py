"""Append-only hash-chained JSONL attack log."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

class LogError(ValueError): pass

def _digest(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

class AttackLog:
    def __init__(self, path, clock=lambda: "2026-11-04T00:00:00Z"):
        self.path = Path(path); self.clock = clock; self.seq = 0; self.prev = "0" * 64
        if self.path.exists() and self.path.read_text().strip():
            entries = verify_log(self.path); self.seq = len(entries); self.prev = entries[-1]["sha256"]
    def append(self, kind: str, payload: dict) -> dict:
        self.seq += 1
        entry = {"seq": self.seq, "t": self.clock(), "kind": kind, "payload": payload, "prev_sha256": self.prev}
        entry["sha256"] = _digest(entry); self.prev = entry["sha256"]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as f: f.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

def verify_log(path) -> list[dict]:
    entries, prev = [], "0" * 64
    for i, line in enumerate(Path(path).read_text().splitlines(), 1):
        try: entry = json.loads(line)
        except Exception as e: raise LogError(f"seq {i}: invalid JSON: {e}") from e
        if entry.get("seq") != i: raise LogError(f"seq {i}: sequence mismatch")
        if entry.get("prev_sha256") != prev: raise LogError(f"seq {i}: prev_sha256 mismatch")
        if entry.get("sha256") != _digest(entry): raise LogError(f"seq {i}: sha256 mismatch (tampered)")
        prev = entry["sha256"]; entries.append(entry)
    return entries
