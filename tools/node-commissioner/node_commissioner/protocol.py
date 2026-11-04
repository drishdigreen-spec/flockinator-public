"""Bounded, correlated USB JSON protocol. Radio control is a separate transport."""
import json
import re


def valid_mac(mac: str) -> bool:
    return bool(re.fullmatch(r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}", mac))


def encode_request(op: str, request_id: str, target: str, **fields) -> bytes:
    if not valid_mac(target):
        raise ValueError("Expected an exact uppercase factory MAC")
    if set(fields) & {"v", "id", "op", "target"}:
        raise ValueError("Reserved protocol field")
    raw = json.dumps(dict(v=1, id=request_id, op=op, target=target, **fields), separators=(",", ":")).encode()
    if len(raw) > 1023:
        raise ValueError("Request exceeds firmware frame limit")
    return raw + b"\n"


def decode_response(raw: bytes, request_id: str) -> dict | None:
    if len(raw) > 32768:
        raise ValueError("Response exceeds host frame limit")
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeError):
        return None
    if not isinstance(result, dict) or result.get("v") != 1 or result.get("request_id") != request_id:
        return None
    return result


def validate_status(status: dict, mac: str, label: str | None = None) -> dict:
    if status.get("type") != "status" or status.get("v") != 1 or status.get("base_mac") != mac:
        raise ValueError("Device identity/protocol mismatch")
    if label is not None and status.get("label") != label:
        raise ValueError("Node label mismatch")
    return status
