import json
import pytest
from node_commissioner.serial_link import SerialLink
MAC="00:11:22:33:44:55"
class Device:
    def __init__(self,**kwargs): self.lines=[]; self.port=None; self.wrong=False; self.fail=False
    def open(self): pass
    def close(self): pass
    def write(self,raw):
        if self.fail: raise OSError("unplugged")
        request=json.loads(raw)
        response={"v":1,"type":"status","request_id":request["id"],"ok":True,"base_mac":MAC if not self.wrong else "00:11:22:33:44:55","label":"A1"}
        self.lines=[b"boot log\n",json.dumps(response).encode()+b"\n"]
    def read_until(self,*args): return self.lines.pop(0) if self.lines else b""
@pytest.fixture
def link(monkeypatch):
    monkeypatch.setattr("node_commissioner.serial_link.serial.Serial",Device)
    return SerialLink("fake",MAC)
def test_skips_boot_logs_and_correlates_response(link):
    assert link.request()["label"]=="A1"
def test_wrong_device_cannot_pass(link):
    link.serial.wrong=True
    with pytest.raises(ValueError,match="identity"): link.request()
def test_disconnect_is_not_success(link):
    link.serial.fail=True
    with pytest.raises(OSError,match="unplugged"): link.request("provision",label="A1")
