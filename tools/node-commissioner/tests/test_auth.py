import hashlib
import hmac
import pytest
from node_commissioner.network import auth_headers
MAC="00:11:22:33:44:55"
CHALLENGE={"v":1,"base_mac":MAC,"nonce":"12"*16,"next_counter":7,"configured":True}

def test_signature_binds_target_method_path_counter_and_body():
    body=b"tone"; key=bytes.fromhex("0b"*32)
    headers=auth_headers(key,CHALLENGE,MAC,"POST","/v1/control",body)
    expected=f"v1\n{'12'*16}\n7\n{MAC}\nPOST\n/v1/control\n{hashlib.sha256(body).hexdigest()}".encode()
    assert headers["X-Flock-Signature"]==hmac.new(key,expected,hashlib.sha256).hexdigest()
    assert auth_headers(key,CHALLENGE,MAC,"POST","/v1/control",b"next_page")!=headers
    assert auth_headers(key,CHALLENGE,MAC,"GET","/v1/status",b"")!=headers

def test_wrong_target_unconfigured_or_malformed_challenge_rejected():
    for change in ({"base_mac":"02:00:00:00:00:02"},{"configured":False},{"nonce":"x"},{"next_counter":0}):
        with pytest.raises(ValueError): auth_headers(b"x"*32,CHALLENGE|change,MAC,"GET","/v1/status",b"")

def test_key_never_appears_in_headers():
    secret=b"z"*32
    headers=auth_headers(secret,CHALLENGE,MAC,"POST","/v1/control",b"tone")
    assert secret.hex() not in str(headers)
