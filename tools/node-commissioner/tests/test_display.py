import pytest
from node_commissioner.display import state_command

def test_state_command():
    assert state_command('listening','attentive','curious',60)==dict(op='display_state',activity='listening',attention='attentive',mood='curious',ttl=60)

@pytest.mark.parametrize('kwargs',[dict(activity='other'),dict(ttl=0),dict(ttl=True),dict(activity='sleeping',attention='urgent'),dict(activity='sleeping',mood='frightened')])
def test_invalid_state(kwargs):
    with pytest.raises(ValueError):state_command(**kwargs)
