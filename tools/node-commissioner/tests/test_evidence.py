import json
import pytest
from node_commissioner.evidence import save_run,redact
MAC="00:11:22:33:44:55"

def test_wrong_label_cannot_create_report(tmp_path):
    with pytest.raises(ValueError): save_run(tmp_path,"A2",MAC,{"v":1,"type":"status","base_mac":MAC,"label":"A1"},"usb")
    assert not list(tmp_path.iterdir())

def test_reports_are_unique_and_credentials_redacted(tmp_path):
    status={"v":1,"type":"status","base_mac":MAC,"label":"A1","firmware":"0.3.1","wifi":{"password":"SECRET","ssid":"PRIVATE"},"key_id":"public-id"}
    a=save_run(tmp_path,"A1",MAC,status,"usb");b=save_run(tmp_path,"A1",MAC,status,"usb")
    assert a!=b and a.exists() and b.exists()
    assert "SECRET" not in a.read_text() and "PRIVATE" not in a.read_text()
    assert "public-id" in a.read_text()
