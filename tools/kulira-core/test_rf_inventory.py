from kulira_core.rf_inventory import parse_hackrf_info, inventory_entry

SAMPLE="""Found HackRF
Index: 0
Serial: 0000000000000000a06063c823691a5f
Board ID Number: 2 (HackRF One)
Firmware Version: 2024.02.1 (API:1.08)
"""

def test_parse_hackrf_found():
    d=parse_hackrf_info(SAMPLE); assert d["present"] and d["board"]=="HackRF One"

def test_parse_hackrf_absent():
    assert parse_hackrf_info("No HackRF boards found.")=={"present": False}

def test_inventory_entry_requires_identification():
    e=inventory_entry(path="/dev/cu.usbserial-0001", kind="usb-serial", identified=False)
    assert e["status"]=="unidentified" and e["tx_authorised"] is False

def test_inventory_entry_identified_still_not_tx_authorised():
    e=inventory_entry(path="/dev/cu.usbserial-0001", kind="esp32", identified=True, model="ESP32-S3")
    assert e["status"]=="identified" and e["tx_authorised"] is False
