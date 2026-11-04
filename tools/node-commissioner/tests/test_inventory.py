import csv
import pytest
from node_commissioner.inventory import update_inventory
MAC="00:11:22:33:44:55"
@pytest.fixture
def table(tmp_path):
    p=tmp_path/"nodes.csv";p.write_text("label,factory_base_mac,status\nA1,,unprovisioned\nA2,,unprovisioned\n");return p
def test_unique_binding_and_unrelated_rows_preserved(table):
    update_inventory(table,"A1",MAC,{"status":"usb_verified"})
    rows=list(csv.DictReader(table.open())); assert rows[0]["factory_base_mac"]==MAC
    assert rows[1]["status"]=="unprovisioned"
    update_inventory(table,"A1",MAC,{"status":"usb_verified"})
def test_conflicts_leave_original_unchanged(table):
    update_inventory(table,"A1",MAC,{"status":"usb_verified"});old=table.read_bytes()
    with pytest.raises(ValueError): update_inventory(table,"A2",MAC,{})
    with pytest.raises(ValueError): update_inventory(table,"A1","02:00:00:00:00:02",{})
    assert old==table.read_bytes()
def test_invalid_label_never_creates_row(table):
    with pytest.raises(ValueError): update_inventory(table,"Z1",MAC,{})

def test_failed_replace_retains_previous_inventory(table,monkeypatch):
    old=table.read_bytes()
    def fail(*args): raise OSError("simulated disk failure")
    monkeypatch.setattr("node_commissioner.inventory.os.replace",fail)
    with pytest.raises(OSError): update_inventory(table,"A1",MAC,{"status":"usb_verified"})
    assert table.read_bytes()==old
