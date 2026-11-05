"""Shared observation-identity vocabulary: Kulira injector -> fleet scorer.

Converges on the scorer's cycle-07 stage-1 auth model (tools/fleet-score):
a report is a *discovery* event carrying auth_status in
{direct_verified, hearsay_relayed, unverified, forged_rejected} and,
for relayed reports, claimed_sender = the originator (never the relay).
Only direct_verified sightings vote; forwarded copies are hearsay and
never add an independent sighting.
"""
from __future__ import annotations

def to_journal_events(reports) -> list[dict]:
    events = []
    for r in reports:
        if r.get("verified") is False:
            status = "forged_rejected"
        elif r.get("forwarded"):
            status = "hearsay_relayed"
        elif r.get("verified") is True:
            status = "direct_verified"
        else:
            status = "unverified"
        events.append({
            "event": "discovery",
            "unit": r["reporter"],
            "claimed_sender": r.get("originator", r["reporter"]),
            "sighting_id": r["sighting_id"],
            "reported_label": r.get("claim"),
            "auth_status": status,
        })
    return events

def direct_sighting_ids(events) -> set:
    return {e["sighting_id"] for e in events if e.get("auth_status") == "direct_verified"}
