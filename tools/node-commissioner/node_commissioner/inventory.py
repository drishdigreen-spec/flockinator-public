"""Locked atomic inventory bindings; unknown labels and reassignment fail closed."""
import csv
import fcntl
import os
import re
import tempfile
from pathlib import Path
from .protocol import valid_mac


def update_inventory(path: Path, label: str, mac: str, values: dict) -> None:
    if not re.fullmatch(r"[A-D][1-4]", label) or not valid_mac(mac):
        raise ValueError("Invalid label or factory MAC")
    if set(values) & {"label", "factory_base_mac"}:
        raise ValueError("Identity fields cannot be overwritten")
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with path.open(newline="") as source:
            reader = csv.DictReader(source)
            fields = reader.fieldnames
            rows = list(reader)
        matches = [r for r in rows if r["label"] == label]
        if len(matches) != 1 or len({r["label"] for r in rows}) != len(rows):
            raise ValueError("Inventory has missing/duplicate labels")
        row = matches[0]
        if row["factory_base_mac"] not in ("", mac):
            raise ValueError("Label already bound to another board")
        if any(r["label"] != label and r["factory_base_mac"] == mac for r in rows):
            raise ValueError("Board already bound to another label")
        if set(values) - set(fields):
            raise ValueError("Unknown inventory fields")
        row.update(factory_base_mac=mac, **values)
        name = None
        try:
            with tempfile.NamedTemporaryFile("w", newline="", dir=path.parent, delete=False) as temp:
                name = temp.name
                writer = csv.DictWriter(temp, fieldnames=fields)
                writer.writeheader(); writer.writerows(rows)
                temp.flush(); os.fsync(temp.fileno())
            os.replace(name, path)
        finally:
            if name and os.path.exists(name):
                os.unlink(name)
