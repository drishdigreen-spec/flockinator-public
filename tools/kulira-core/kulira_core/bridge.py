"""Contract v1: Kulira injector -> fleet scorer journal events.

Input report (dict, validated at this boundary):
  reporter (str, required), sighting_id (str, required),
  originator (str, default reporter), claim (any, passed through as
  reported_label), verified (True|False|None, required key),
  forwarded (bool, default False), origin_turn (int, REQUIRED when
  forwarded - Amendment-2 hearsay contract; relay without it is invalid).
Output event (additive-only; never rename/remove fields in v1):
  {event: "discovery", unit, claimed_sender, sighting_id,
   reported_label, auth_status} with auth_status in the scorer's
  cycle-07 enum. Unknown/malformed input raises ValueError, loudly.

Shared observation-identity vocabulary: Kulira injector -> fleet scorer.

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
        if not isinstance(r, dict) or not r.get("reporter") or not r.get("sighting_id") or "verified" not in r:
            raise ValueError(f"invalid report (reporter, sighting_id, verified required): {r!r}")
        if r.get("forwarded") and not isinstance(r.get("origin_turn"), int):
            raise ValueError("forwarded report requires origin_turn (Amendment-2 hearsay contract)")
        if r.get("verified") is False:
            status = "forged_rejected"
        elif r.get("forwarded"):
            status = "hearsay_relayed"
        elif r.get("verified") is True:
            status = "direct_verified"
        else:
            status = "unverified"
        event = {
            "event": "discovery",
            "unit": r["reporter"],
            "claimed_sender": r.get("originator", r["reporter"]),
            "sighting_id": r["sighting_id"],
            "reported_label": r.get("claim"),
            "auth_status": status,
            **({"origin_turn": r["origin_turn"]} if r.get("forwarded") else {}),
        }
        # Preserve scorer discovery metadata when the report carries it
        # (fleet scorer contact_of requires contact + matching tile).
        for field in ("contact", "tile", "turn"):
            if field in r:
                event[field] = r[field]
        events.append(event)
    return events

def direct_sighting_ids(events) -> set:
    return {e["sighting_id"] for e in events if e.get("auth_status") == "direct_verified"}
