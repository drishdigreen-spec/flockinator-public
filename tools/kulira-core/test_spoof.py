import pytest
from kulira_core.spoof import ExperimentMessage, ReceiverValidator, SpoofGenerator

KEYS={"B2": b"b"*32, "C1": b"c"*32}

def test_authentic_message_accepted():
    v=ReceiverValidator(KEYS); m=ExperimentMessage.sign("B2", KEYS["B2"], recipient="C1", kind="observation", payload="beacon@5,5", seq=1, nonce="n1")
    assert v.accept(m)=="accepted"

def test_forged_sender_rejected():
    v=ReceiverValidator(KEYS); g=SpoofGenerator(seed=3)
    m=g.forge("B2", recipient="C1", payload="beacon@9,9", seq=1, nonce="x")
    assert v.accept(m)=="rejected:bad_tag"

def test_replay_rejected():
    v=ReceiverValidator(KEYS); m=ExperimentMessage.sign("B2", KEYS["B2"], recipient="C1", kind="observation", payload="x", seq=1, nonce="n1")
    assert v.accept(m)=="accepted" and v.accept(m)=="rejected:replay"

def test_wrong_recipient_rejected():
    v=ReceiverValidator(KEYS); m=ExperimentMessage.sign("B2", KEYS["B2"], recipient="C1", kind="observation", payload="x", seq=1, nonce="n1")
    m2=ExperimentMessage(m.sender,m.recipient,m.kind,m.payload,m.seq,"zz",m.tag)
    assert ReceiverValidator(KEYS, own_label="D4").accept(m)=="rejected:wrong_target"

def test_duplicate_label_conflict():
    v=ReceiverValidator(KEYS); v.register_label_mac("B2","02:00:00:00:00:02")
    with pytest.raises(ValueError, match="conflict"): v.register_label_mac("B2","02:00:00:00:00:99")

def test_spoof_schedule_deterministic():
    g=SpoofGenerator(seed=42); a=[g.forge("B2",recipient="C1",payload="p",seq=i,nonce=str(i)).tag for i in range(3)]
    g2=SpoofGenerator(seed=42); b=[g2.forge("B2",recipient="C1",payload="p",seq=i,nonce=str(i)).tag for i in range(3)]
    assert a==b
