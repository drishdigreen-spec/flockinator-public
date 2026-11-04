import csv
import errno
import hashlib
import json
import os
from pathlib import Path

import pytest

from node_commissioner.provisioning import Artifact, Package, Provisioning, file_digest

MAC = "00:11:22:33:44:55"
KEY = b"k" * 32


def test_immutable_evidence_without_hardlinks_is_complete_and_never_overwritten(tmp_path, monkeypatch):
    from node_commissioner.provisioning import _export_record
    def unsupported(*args):
        raise OSError(errno.ENOTSUP, "Volume has no hard links")
    monkeypatch.setattr(os, "link", unsupported)
    source = tmp_path / "authoritative.json"
    source.write_text('{"result":"PASS"}')
    destination = tmp_path / "report.json"
    _export_record(source, destination)
    assert json.loads(destination.read_text()) == dict(result="PASS")
    with pytest.raises(FileExistsError):
        _export_record(source, destination)
    assert json.loads(destination.read_text()) == dict(result="PASS")
    assert not list(tmp_path.glob(".pending-*"))


def test_transaction_keeps_atomic_authority_off_volume_without_hardlinks(setup, monkeypatch):
    run, device = setup
    link = os.link
    def volume_link(source, destination):
        if run.evidence_root in Path(destination).parents:
            raise OSError(errno.ENOTSUP, "External volume has no hard links")
        return link(source, destination)
    monkeypatch.setattr(os, "link", volume_link)
    result = run.run()
    exported = Path(result["evidence"])
    authority = run.transaction / "evidence" / exported.name
    assert authority.read_bytes() == exported.read_bytes()
    assert result["status"] == "commissioned_for_installation"


class Device:
    def __init__(self, package):
        self.package = package
        self.calls = []
        self.fail = None
        self.bad_readback = False
        self.mac = MAC
        self.identity_region_safe = True

    def action(self, name):
        self.calls.append(name)
        if name == self.fail:
            raise OSError("Disconnected")

    def probe(self):
        self.action("probe")
        return dict(base_mac=self.mac, chip="ESP32-S3", flash_bytes=33554432,
                    secure_boot=False, flash_encryption=False, identity_region_safe=self.identity_region_safe)

    def backup(self, path, size):
        self.action("backup")
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.truncate(size)

    def verify_backup(self, path): self.action("verify_backup")
    def flash(self, package): self.action("flash")
    def verify_flash(self, package): self.action("verify_flash")
    def configure(self, label, wifi, key): self.action("configure")
    def reboot(self): self.action("reboot")

    def status(self):
        self.action("status")
        return dict(v=1, type="status", base_mac=self.mac,
            label="A2" if self.bad_readback else "A1", app_sha256=self.package.app_image_sha256,
            firmware=self.package.version, flash_bytes=33554432, psram_bytes=16777216,
            identity_nvs="PASS", psram_sample="PASS",
            network=dict(wifi_configured=True), maintenance=dict(key_provisioned=True,
                key_id=hashlib.sha256(KEY).hexdigest()[:16]),
            panel=dict(visual_acceptance="PENDING"), sd=dict(state="NOT_PRESENT"))


@pytest.fixture
def setup(tmp_path):
    artifacts = []
    for offset in (0, 0x8000, 0xF000, 0x20000):
        path = tmp_path / f"{offset}.bin"
        path.write_bytes(b"image" * 16)
        artifacts.append(Artifact(path, offset, file_digest(path)))
    package = Package("test", "a" * 64, tuple(artifacts))
    inventory = tmp_path / "nodes.csv"
    inventory.write_text("label,factory_base_mac,status,firmware_sha256\nA1,,unprovisioned,\nA2,,unprovisioned,\n")
    device = Device(package)
    run = Provisioning(backend=device, inventory=inventory,
        transaction=tmp_path / "private" / "transaction-1", backup_root=tmp_path / "backups",
        evidence_root=tmp_path / "evidence", label="A1", mac=MAC, package=package,
        wifi=dict(ssid="private-network", password="private-password"), key=KEY)
    return run, device


def test_success_without_detachable_peripherals_and_no_secret_evidence(setup):
    run, device = setup
    result = run.run()
    assert result["status"] == "commissioned_for_installation"
    rows = list(csv.DictReader(run.inventory.open()))
    assert rows[0]["factory_base_mac"] == MAC
    assert rows[1]["status"] == "unprovisioned"
    assert device.calls.index("verify_backup") < device.calls.index("flash")
    for path in run.transaction.glob("*.json"):
        text = path.read_text()
        assert "private-network" not in text and "private-password" not in text and KEY.hex() not in text
    report = json.loads(Path(result["evidence"]).read_text())
    assert report["manual_acceptance"] == "PENDING"


def test_owner_waiver_skips_backup_but_verifies_flash_and_records_evidence(setup):
    run, device = setup
    run.skip_backup = True
    result = run.run()
    assert "backup" not in device.calls and "verify_backup" not in device.calls
    assert not run.backup_root.exists()
    assert device.calls.index("flash") < device.calls.index("verify_flash") < device.calls.index("configure")
    report = json.loads(Path(result["evidence"]).read_text())
    assert report["backup_status"] == "waived_by_owner"
    assert report["backup_sha256"] is None
    stages = [event["stage"] for event in run.events]
    assert stages.index("backup_waived") < stages.index("flash_started")


def test_backup_waiver_survives_resume_of_interrupted_partition_write(setup):
    run, device = setup
    run.skip_backup = True
    device.fail = "flash"
    with pytest.raises(OSError): run.run()
    run.skip_backup = False  # The bound journal retains the owner's decision.
    device.fail = None
    device.identity_region_safe = False
    result = run.run()
    assert result["status"] == "commissioned_for_installation"
    assert "backup" not in device.calls
    assert len([e for e in run.events if e["stage"] == "backup_waived"]) == 1


def test_backup_waiver_does_not_bypass_initial_layout_check(setup):
    run, device = setup
    run.skip_backup = True
    device.identity_region_safe = False
    with pytest.raises(ValueError, match="layout"): run.run()
    assert "flash" not in device.calls


def test_skip_backup_preserves_existing_verified_backup(setup):
    run, device = setup
    result = run.run()
    original = {p: file_digest(p) for p in run.backup_root.glob("*.bin")}
    run.skip_backup = True
    result = run.run()
    assert all(file_digest(p) == digest for p, digest in original.items())
    assert device.calls.count("backup") == 1
    assert json.loads(Path(result["evidence"]).read_text())["backup_status"] == "verified"


@pytest.mark.parametrize("stage", ["backup", "verify_backup", "flash", "verify_flash", "configure", "reboot", "status"])
def test_disconnect_does_not_commit_then_resumes_without_overwriting_backups(setup, stage):
    run, device = setup
    original = run.inventory.read_bytes()
    device.fail = stage
    with pytest.raises(OSError, match="Disconnected"):
        run.run()
    assert run.inventory.read_bytes() == original
    assert not any(event["stage"] == "inventory_committed" for event in run.events)
    backups = {path: file_digest(path) for path in run.backup_root.glob("*.bin")}
    device.fail = None
    run.run()
    assert all(file_digest(path) == digest for path, digest in backups.items())
    assert run.events[-1]["stage"] == "inventory_committed"


def test_duplicate_label_blocks_before_device_calls(setup):
    run, device = setup
    run.inventory.write_text("label,factory_base_mac,status\nA1,02:00:00:00:00:02,done\n")
    with pytest.raises(ValueError, match="conflict"):
        run.run()
    assert device.calls == []


def test_resume_rechecks_selected_physical_board_before_any_write(setup):
    run, device = setup
    device.fail = "configure"
    with pytest.raises(OSError): run.run()
    previous = list(device.calls)
    device.fail = None
    device.mac = "02:00:00:00:00:02"
    with pytest.raises(ValueError, match="mismatch"): run.run()
    assert device.calls[len(previous):] == ["probe"]


def test_resume_rejects_modified_package(setup):
    run, device = setup
    device.fail = "configure"
    with pytest.raises(OSError): run.run()
    run.package.artifacts[0].path.write_bytes(b"changed")
    device.calls.clear()
    with pytest.raises(ValueError, match="integrity"): run.run()
    assert device.calls == []


def test_backup_corruption_blocks_resume_flash(setup):
    run, device = setup
    device.fail = "flash"
    with pytest.raises(OSError): run.run()
    next(run.backup_root.glob("*.bin")).write_bytes(b"corrupt")
    device.fail = None
    device.calls.clear()
    with pytest.raises(ValueError, match="backup integrity"): run.run()
    assert "flash" not in device.calls


def test_bad_post_reboot_readback_never_counts_success(setup):
    run, device = setup
    device.bad_readback = True
    with pytest.raises(ValueError, match="label mismatch"): run.run()
    assert "unprovisioned" in run.inventory.read_text()
    assert not any(event["stage"] == "inventory_committed" for event in run.events)


def test_inventory_replace_failure_is_recoverable(setup, monkeypatch):
    run, device = setup
    original = run.inventory.read_bytes()
    with monkeypatch.context() as patch:
        patch.setattr("node_commissioner.provisioning.os.replace", lambda *args: (_ for _ in ()).throw(OSError("disk")))
        with pytest.raises(OSError): run.run()
    assert run.inventory.read_bytes() == original
    run.run()
    assert device.calls.count("backup") == 1
    assert device.calls.count("flash") == 1
    assert device.calls.count("reboot") == 2


def test_completed_resume_still_requires_live_readback(setup):
    run, device = setup
    run.run()
    device.fail = "status"
    with pytest.raises(OSError): run.run()
    assert run.events[-1]["stage"] == "target_verified"


def test_identity_partition_artifact_rejected(setup):
    run, device = setup
    object.__setattr__(run.package, "artifacts", run.package.artifacts + (Artifact(run.package.artifacts[0].path, 0x1020000, run.package.artifacts[0].sha256),))
    with pytest.raises(ValueError, match="offsets"): run.run()
    assert device.calls == []


def test_partial_partition_write_can_resume_exact_started_transaction(setup):
    run, device = setup
    device.fail = "flash"
    with pytest.raises(OSError): run.run()
    device.fail = None
    device.identity_region_safe = False
    run.run()
    assert device.calls.count("flash") == 2


def test_unrecognised_identity_layout_blocks_first_write(setup):
    run, device = setup
    device.identity_region_safe = False
    with pytest.raises(ValueError, match="not recognised"): run.run()
    assert device.calls == ["probe"]
