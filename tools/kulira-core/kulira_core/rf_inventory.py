"""kulira-rf (passive only): gadget inventory. No transmission, ever,
from this module - it enumerates and records, so a scenario can only
name a gadget that has been identified here first.
"""
from __future__ import annotations
import glob, subprocess

def parse_hackrf_info(text: str) -> dict:
    if "No HackRF boards found" in text:
        return {"present": False}
    board = None
    for line in text.splitlines():
        if "Board ID Number" in line and "(" in line:
            board = line.split("(", 1)[1].rstrip(")")
    return {"present": "Found HackRF" in text, "board": board}

def inventory_entry(path: str, kind: str, identified: bool, model: str | None = None) -> dict:
    return {"path": path, "kind": kind, "model": model,
            "status": "identified" if identified else "unidentified",
            "tx_authorised": False}

def enumerate_usb_serial() -> list[dict]:
    return [inventory_entry(p, "usb-serial", identified=False)
            for p in sorted(glob.glob("/dev/cu.usbserial-*"))]

def probe_hackrf(runner=subprocess.run) -> dict:
    try:
        r = runner(["hackrf_info"], capture_output=True, text=True, timeout=10)
        return parse_hackrf_info((r.stdout or "") + (r.stderr or ""))
    except Exception:
        return {"present": False}
