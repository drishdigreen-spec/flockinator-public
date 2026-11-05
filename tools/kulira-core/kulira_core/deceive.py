"""kulira-deceive: authenticated-but-false claims + belief assessment.

Identity (spoof.py) proves who sent a claim; it cannot prove the claim
is true. Deception therefore signs false payloads with a legitimate
(scenario-granted) key and measures whether the belief layer counts
forwarded copies as independent corroboration - it must not.
"""
from __future__ import annotations
import hashlib, hmac
from dataclasses import dataclass

@dataclass(frozen=True)
class ExperimentMessage:
    sender: str; recipient: str; kind: str; payload: str; seq: int; nonce: str; tag: str
    @classmethod
    def sign(cls, sender, key, recipient, kind, payload, seq, nonce):
        msg = f"{sender}|{recipient}|{kind}|{payload}|{seq}|{nonce}".encode()
        return cls(sender, recipient, kind, payload, seq, nonce, hmac.new(key, msg, hashlib.sha256).hexdigest())

class DeceptionGenerator:
    def __init__(self, seed: int = 0): self.seed = seed
    def false_observation(self, sender, key, recipient, claim, seq, nonce):
        return ExperimentMessage.sign(sender, key, recipient, "observation", claim, seq, nonce)

def corroboration_count(reports) -> int:
    """Independent sightings only: distinct sighting ids, not reporters."""
    return len({sighting for _node, _claim, sighting in reports})

def assess_belief(reports, min_independent: int = 2) -> dict:
    n = corroboration_count(reports)
    return {"believed": n >= min_independent, "independent": n,
            "reporters": sorted({node for node, _c, _s in reports})}
