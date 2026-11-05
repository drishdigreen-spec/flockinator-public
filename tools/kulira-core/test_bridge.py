from kulira_core.bridge import to_journal_events, direct_sighting_ids

def test_direct_report_maps_to_direct_verified():
    ev=to_journal_events([{"reporter":"B2","originator":"B2","sighting_id":"s1","claim":"beacon@9,9","verified":True,"forwarded":False}])
    assert ev[0]["auth_status"]=="direct_verified" and ev[0]["claimed_sender"]=="B2" and ev[0]["event"]=="discovery"

def test_forwarded_copy_is_hearsay_not_independent():
    reports=[{"reporter":"B2","originator":"B2","sighting_id":"s1","claim":"x","verified":True,"forwarded":False},
             {"reporter":"C1","originator":"B2","sighting_id":"s1","claim":"x","verified":True,"forwarded":True,"origin_turn":3}]
    ev=to_journal_events(reports)
    assert ev[1]["auth_status"]=="hearsay_relayed" and direct_sighting_ids(ev)=={"s1"}

def test_forged_is_forged_rejected_and_never_votes():
    ev=to_journal_events([{"reporter":"B2","originator":"B2","sighting_id":"s9","claim":"x","verified":False,"forwarded":False}])
    assert ev[0]["auth_status"]=="forged_rejected" and direct_sighting_ids(ev)==set()

def test_unverified_when_not_checked():
    ev=to_journal_events([{"reporter":"B2","originator":"B2","sighting_id":"s2","claim":"x","verified":None,"forwarded":False}])
    assert ev[0]["auth_status"]=="unverified"


def test_forwarded_without_origin_turn_invalid():
    import pytest
    with pytest.raises(ValueError, match="origin_turn"):
        to_journal_events([{"reporter":"C1","originator":"B2","sighting_id":"s1","claim":"x","verified":True,"forwarded":True}])

def test_malformed_report_invalid():
    import pytest
    with pytest.raises(ValueError, match="invalid report"):
        to_journal_events([{"reporter":"B2"}])

def test_scorer_metadata_preserved():
    ev=to_journal_events([{"reporter":"B2","originator":"B2","sighting_id":"s1","claim":"Friendly","verified":True,"forwarded":False,"contact":2,"tile":[8,8],"turn":4}])
    assert ev[0]["contact"]==2 and ev[0]["tile"]==[8,8] and ev[0]["turn"]==4
