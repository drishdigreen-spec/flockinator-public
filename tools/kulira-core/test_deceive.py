from kulira_core.deceive import DeceptionGenerator, corroboration_count, assess_belief

KEY=b"k"*32
def test_false_observation_is_authentic_but_false():
    g=DeceptionGenerator(seed=5)
    m=g.false_observation("B2", KEY, recipient="C1", claim="beacon@9,9", seq=1, nonce="n1")
    # authentic tag, false payload: validator accepts identity, belief layer must not
    assert m.payload=="beacon@9,9"

def test_forwarded_copies_are_not_independent():
    reports=[("B2","beacon@9,9","sighting-1"),("C1","beacon@9,9","sighting-1"),("D1","beacon@9,9","sighting-1")]
    assert corroboration_count(reports)==1

def test_independent_sightings_count():
    reports=[("B2","beacon@9,9","s1"),("C1","beacon@9,9","s2")]
    assert corroboration_count(reports)==2

def test_single_source_not_believed_without_threshold():
    r=assess_belief([("B2","beacon@9,9","s1")], min_independent=2)
    assert r["believed"] is False and r["independent"]==1

def test_deception_deterministic():
    g=DeceptionGenerator(seed=9); a=g.false_observation("B2",KEY,recipient="C1",claim="x",seq=1,nonce="n").tag
    g2=DeceptionGenerator(seed=9); b=g2.false_observation("B2",KEY,recipient="C1",claim="x",seq=1,nonce="n").tag
    assert a==b
