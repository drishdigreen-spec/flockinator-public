"""kulira-spoof: forged/replayed experiment messages + receiver validator.

Models the fleet's expected defence (HMAC-SHA256 tag, sender/recipient
binding, nonce replay cache, duplicate-label conflict) so spoofing can
be measured: a forge without the per-node key must be rejected, a
replay must be rejected, and authentication still says nothing about
whether the payload claim is true (that is kulira-deceive's problem).
"""
from __future__ import annotations
import hashlib, hmac, random
from dataclasses import dataclass

def _tag(key: bytes, sender, recipient, kind, payload, seq, nonce) -> str:
    msg = f"{sender}|{recipient}|{kind}|{payload}|{seq}|{nonce}".encode()
    return hmac.new(key, msg, hashlib.sha256).hexdigest()

@dataclass(frozen=True)
class ExperimentMessage:
    sender: str; recipient: str; kind: str; payload: str; seq: int; nonce: str; tag: str
    @classmethod
    def sign(cls, sender, key, recipient, kind, payload, seq, nonce):
        return cls(sender, recipient, kind, payload, seq, nonce,
                   _tag(key, sender, recipient, kind, payload, seq, nonce))

class SpoofGenerator:
    """Generates forged messages without any real key (seeded)."""
    def __init__(self, seed: int = 0):
        self._rng = random.Random(seed)
    def forge(self, sender, recipient, payload, seq, nonce, kind="observation"):
        fake_key = bytes(self._rng.randrange(256) for _ in range(32))
        return ExperimentMessage.sign(sender, fake_key, recipient, kind, payload, seq, nonce)
    def replay(self, message: ExperimentMessage) -> ExperimentMessage:
        return message

class ReceiverValidator:
    def __init__(self, keys: dict[str, bytes], own_label: str | None = None):
        self.keys = dict(keys); self.own_label = own_label
        self._seen: set[tuple] = set(); self._labels: dict[str, str] = {}
    def register_label_mac(self, label: str, mac: str):
        if label in self._labels and self._labels[label] != mac:
            raise ValueError(f"duplicate label conflict: {label}")
        self._labels[label] = mac
    def accept(self, m: ExperimentMessage) -> str:
        if self.own_label is not None and m.recipient != self.own_label:
            return "rejected:wrong_target"
        key = self.keys.get(m.sender)
        if key is None:
            return "rejected:unknown_sender"
        expected = _tag(key, m.sender, m.recipient, m.kind, m.payload, m.seq, m.nonce)
        if not hmac.compare_digest(expected, m.tag):
            return "rejected:bad_tag"
        ident = (m.sender, m.seq, m.nonce)
        if ident in self._seen:
            return "rejected:replay"
        self._seen.add(ident); return "accepted"
