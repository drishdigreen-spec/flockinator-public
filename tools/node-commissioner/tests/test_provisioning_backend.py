import json
import subprocess
import sys
import types
from pathlib import Path

import pytest

from node_commissioner.provisioning_backend import EsptoolBackend, _GUARDED_ESPTOOL
from node_commissioner.provisioning import Artifact, Package, file_digest

MAC = "00:11:22:33:44:55"


def test_status_retry_does_not_reset_slow_starting_usb_device(tmp_path, monkeypatch):
    from node_commissioner import provisioning_backend
    ticks = iter(range(20))
    monkeypatch.setattr(provisioning_backend.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(provisioning_backend.time, "sleep", lambda _: None)

    class StartingDevice:
        def __init__(self, *args): self.attempts = 0
        def close(self): pass
        def request(self, **kwargs):
            self.attempts += 1
            if self.attempts == 1:
                raise TimeoutError("Initial request arrived before USB input was ready")
            return dict(v=1, type="status", base_mac=MAC)

    backend = EsptoolBackend(port="/dev/cu.example", mac=MAC, package=None,
                             private_directory=tmp_path / "private", serial_factory=StartingDevice)
    assert backend._status_ready(timeout=4)["base_mac"] == MAC


@pytest.mark.parametrize("operation, after", [
    (["write_flash", "0", "image.bin"], "no_reset"),
    (["verify_flash", "0", "image.bin"], "hard_reset"),
    (["read_flash", "0", "8192", "backup.bin"], "hard_reset"),
])
def test_guard_uses_same_handle_and_accepts_actual_octal_32mb(monkeypatch, operation, after):
    class Port:
        closed = False
        def close(self): self.closed = True
    class Device:
        CHIP_NAME = "ESP32-S3"
        _port = Port()
        def read_mac(self): return bytes.fromhex(MAC.replace(":", ""))
        def get_security_info(self): return dict(flags=0, flash_crypt_cnt=0)
        def flash_spi_attach(self, pins): pass
        def flash_id(self): return 0x3980c2  # A1's octal JEDEC density code.
        def get_chip_revision(self): return 2
    device = Device()
    calls = []
    module = types.ModuleType("esptool")
    module.__version__ = "4.9.0"
    module.main = lambda args, esp: calls.append((args, esp))
    commands = types.ModuleType("esptool.cmds")
    commands.detect_chip = lambda **kwargs: device
    commands.DETECTED_FLASH_SIZES = {0x39: "32MB", 0x19: "32MB"}
    monkeypatch.setitem(sys.modules, "esptool", module)
    monkeypatch.setitem(sys.modules, "esptool.cmds", commands)
    monkeypatch.setattr(sys, "argv", ["guard", "/dev/cu.example", MAC, json.dumps(operation)])
    exec(_GUARDED_ESPTOOL, {})
    assert calls[0][1] is device
    # OTA metadata changes on first boot: verify every byte before allowing it.
    assert calls[0][0][calls[0][0].index("--after") + 1] == after
    assert device._port.closed
    calls.clear()
    device.read_mac = lambda: b"\0" * 6
    with pytest.raises(SystemExit, match="identity mismatch"):
        exec(_GUARDED_ESPTOOL, {})
    assert calls == []


def test_backend_has_no_constructor_io_and_logs_privately(tmp_path):
    calls = []
    def runner(args, timeout):
        calls.append(args)
        return subprocess.CompletedProcess(args, 1, stdout="private device output", stderr="")
    backend = EsptoolBackend(port="/dev/cu.example", mac=MAC, package=None,
                             private_directory=tmp_path / "private", runner=runner)
    assert calls == []
    with pytest.raises(RuntimeError) as error:
        backend._command(["flash_id"])
    assert "private device output" not in str(error.value)
    assert "esptool==4.9.0" in calls[0]
    path = next((tmp_path / "private").glob("*.log"))
    assert path.stat().st_mode & 0o077 == 0
    assert path.read_text() == "private device output"


def test_probe_nonblank_identity_requires_exact_existing_partition_layout(tmp_path):
    artifacts = []
    for offset in (0, 0x8000, 0xF000, 0x20000):
        path = tmp_path / f"{offset}.bin"
        path.write_bytes(b"table")
        artifacts.append(Artifact(path, offset, file_digest(path)))
    package = Package("test", "a" * 64, tuple(artifacts))
    actual_table = b"wrong" + b"\xff" * (4096 - 5)
    def runner(args, timeout):
        operation = json.loads(args[-1])
        if operation[0] == "read_flash":
            offset, size, destination = int(operation[1], 0), int(operation[2]), Path(operation[3])
            destination.write_bytes(actual_table if offset == 0x8000 else bytes(size))
        probe = dict(base_mac=MAC, chip="ESP32-S3", flash_bytes=33554432,
                     secure_boot=False, flash_encryption=False)
        return subprocess.CompletedProcess(args, 0, stdout="FLOCK_PROBE=" + json.dumps(probe), stderr="")
    backend = EsptoolBackend(port="/dev/cu.example", mac=MAC, package=package,
                             private_directory=tmp_path / "private", runner=runner)
    assert backend.probe()["identity_region_safe"] is False
    actual_table = b"table" + b"\xff" * (4096 - 5)
    assert backend.probe()["identity_region_safe"] is True
