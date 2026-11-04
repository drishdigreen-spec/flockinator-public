"""Authenticated local IPv4 maintenance transport; no environment HTTP proxy."""
import hashlib
import hmac
import ipaddress
import json
import re
import urllib.request
from .protocol import valid_mac, validate_status


def auth_headers(key: bytes, challenge: dict, mac: str, method: str, path: str, body: bytes) -> dict:
    if len(key) != 32 or not valid_mac(mac) or challenge.get("v") != 1 or challenge.get("base_mac") != mac or challenge.get("configured") is not True:
        raise ValueError("Unconfigured or wrong maintenance target")
    nonce, counter = challenge.get("nonce", ""), challenge.get("next_counter")
    if not re.fullmatch(r"[0-9a-f]{32}", nonce) or type(counter) is not int or not 1 <= counter <= 0xFFFFFFFF:
        raise ValueError("Invalid challenge")
    if method not in ("GET", "POST") or path not in ("/v1/status", "/v1/control", "/v1/update", "/v1/journal", "/v1/journal/read"):
        raise ValueError("Unsupported maintenance operation")
    digest = hashlib.sha256(body).hexdigest()
    message = f"v1\n{nonce}\n{counter}\n{mac}\n{method}\n{path}\n{digest}".encode()
    signature = hmac.new(key, message, hashlib.sha256).hexdigest()
    return {"X-Flock-Nonce": nonce, "X-Flock-Counter": str(counter), "X-Flock-Target": mac, "X-Flock-SHA256": digest, "X-Flock-Signature": signature, "Content-Type": "application/octet-stream"}


class NetworkClient:
    def __init__(self, address: str, mac: str, key: bytes):
        self.base = f"http://{ipaddress.IPv4Address(address)}"
        self.mac, self.key = mac, key
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def challenge(self) -> dict:
        with self.opener.open(self.base + "/v1/challenge", timeout=5) as response:
            return json.loads(response.read(4096))

    def request(self, method: str, path: str, body: bytes = b"", timeout: float = 30) -> dict:
        headers = auth_headers(self.key, self.challenge(), self.mac, method, path, body)
        req = urllib.request.Request(self.base + path, data=body if method == "POST" else None, headers=headers, method=method)
        with self.opener.open(req, timeout=timeout) as response:
            value = json.loads(response.read(32768))
        if path == "/v1/status":
            validate_status(value, self.mac)
        return value

    def read_journal(self, digest: str) -> bytes:
        if not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError("Invalid journal digest")
        path = "/v1/journal/read"
        body = digest.encode('ascii')
        headers = auth_headers(self.key, self.challenge(), self.mac, "POST", path, body)
        req = urllib.request.Request(self.base + path, data=body, headers=headers)
        with self.opener.open(req, timeout=10) as response:
            data = response.read(128*1024+1)
        if len(data)>128*1024 or hashlib.sha256(data).hexdigest()!=digest:
            raise ValueError("SD journal readback mismatch")
        return data
