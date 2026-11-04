import json
import pytest
from node_commissioner.protocol import encode_request, decode_response, validate_status
MAC="00:11:22:33:44:55"
def test_request_requires_exact_target():
    with pytest.raises(ValueError): encode_request("provision", "a", "not-a-mac", label="A1")
def test_bounded_request():
    with pytest.raises(ValueError): encode_request("provision", "a", MAC, label="x"*2000)
def test_status_must_match_device_and_label():
    s={"v":1,"type":"status","base_mac":MAC,"label":"A1","firmware":"0.1.0"}
    assert validate_status(s,MAC,"A1")==s
    with pytest.raises(ValueError): validate_status(s,MAC,"A2")
    with pytest.raises(ValueError): validate_status(s,"02:00:00:00:00:02","A1")
def test_logs_and_wrong_requests_are_not_responses():
    assert decode_response(b"I (12) driver boot", "123") is None
    assert decode_response(b'{"v":1,"request_id":"456","ok":true}',"123") is None
    assert decode_response(b'{"v":1,"request_id":"123","ok":true}',"123")["ok"] is True
def test_oversized_response_rejected():
    with pytest.raises(ValueError): decode_response(b"x"*32769,"a")
