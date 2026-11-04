import hashlib
import json
from argparse import Namespace
from pathlib import Path

import pytest

import node_commissioner.__main__ as cli

MAC = "00:11:22:33:44:55"


@pytest.fixture
def manifest(tmp_path):
    base = b"\xe9" + bytes(63)
    application = base + hashlib.sha256(base).digest()
    files = {"bootloader.bin": b"boot", "partitions.bin": b"partitions",
             "ota_data_initial.bin": b"\xff" * 8192, "firmware.bin": application}
    hashes = {}
    for name, data in files.items():
        (tmp_path / name).write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    value = dict(version="0.4.0", target_family="WS32", status="Integration candidate",
                 esp_image_sha256=hashlib.sha256(base).hexdigest(), artifacts_sha256=hashes,
                 file_sha256=hashes["firmware.bin"], file_bytes=len(application))
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(value))
    return path


def test_load_current_manifest_enforces_exact_offsets_and_runtime_digest(manifest):
    package = cli.load_initial_package(manifest)
    assert [item.offset for item in package.artifacts] == [0, 0x8000, 0xF000, 0x20000]
    value = json.loads(manifest.read_text())
    value["esp_image_sha256"] = "b" * 64
    manifest.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="runtime digest"):
        cli.load_initial_package(manifest)


def test_load_legacy_manifest_and_reject_rejected_release(manifest):
    value = json.loads(manifest.read_text())
    value["images"] = {name: dict(file_sha256=digest, bytes=(manifest.parent / name).stat().st_size)
                       for name, digest in value.pop("artifacts_sha256").items()}
    value["images"]["firmware.bin"]["esp_image_sha256"] = value.pop("esp_image_sha256")
    manifest.write_text(json.dumps(value))
    assert cli.load_initial_package(manifest).version == "0.4.0"
    value["status"] = "REJECTED: boot failure"
    manifest.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="cannot be initially commissioned"):
        cli.load_initial_package(manifest)


def test_missing_boot_artifact_and_corrupt_package_rejected(manifest):
    path = manifest.parent / "bootloader.bin"
    path.write_bytes(b"altered")
    with pytest.raises(ValueError, match="integrity"):
        cli.load_initial_package(manifest)
    value = json.loads(manifest.read_text())
    del value["artifacts_sha256"]["bootloader.bin"]
    manifest.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="requires a trusted digest"):
        cli.load_initial_package(manifest)


def test_wrong_family_cannot_use_node_initial_flash(manifest):
    value = json.loads(manifest.read_text())
    value["target_family"] = "LILYGO"
    manifest.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="another hardware"):
        cli.load_initial_package(manifest)


def test_cli_requires_explicit_physical_target_before_work(monkeypatch):
    calls = []
    monkeypatch.setattr(cli, "provision_target", lambda args: calls.append(args))
    with pytest.raises(SystemExit):
        cli.main(["provision", "--label", "A1", "--manifest", "manifest.json"])
    assert calls == []


def test_duplicate_binding_stops_before_credential_or_device_access(tmp_path, manifest, monkeypatch):
    inventory = tmp_path / "docs/inventory/nodes.csv"
    inventory.parent.mkdir(parents=True)
    inventory.write_text(f"label,factory_base_mac,status\nA1,{MAC},done\nA2,,unprovisioned\n")
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    def unexpected(*args, **kwargs): pytest.fail("Credentials/device accessed before rejecting duplicate")
    monkeypatch.setattr(cli, "load_wifi", unexpected)
    monkeypatch.setattr(cli, "EsptoolBackend", unexpected)
    args = Namespace(label="A2", mac=MAC, port="/dev/cu.example", manifest=manifest, transaction=None)
    with pytest.raises(ValueError, match="conflicting factory MAC"):
        cli.provision_target(args)


@pytest.mark.parametrize("skip_backup", [False, True])
def test_provision_command_wires_private_credentials_and_closes_on_failure(tmp_path, manifest, monkeypatch, skip_backup):
    inventory = tmp_path / "docs/inventory/nodes.csv"
    inventory.parent.mkdir(parents=True)
    inventory.write_text("label,factory_base_mac,status\nA1,,unprovisioned\n")
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(cli, "load_wifi", lambda: dict(ssid="private", password="secret"))
    monkeypatch.setattr(cli, "management_key", lambda mac, create: b"k" * 32)
    calls = {}
    class FakeBackend:
        def __init__(self, **kwargs): calls["backend"] = kwargs
        def close(self): calls["closed"] = True
    class FakeTransaction:
        def __init__(self, **kwargs): calls["transaction"] = kwargs
        def run(self): raise OSError("Disconnected")
    monkeypatch.setattr(cli, "EsptoolBackend", FakeBackend)
    monkeypatch.setattr(cli, "Provisioning", FakeTransaction)
    args = Namespace(label="A1", mac=MAC, port="/dev/cu.example", manifest=manifest, transaction=None, skip_backup=skip_backup)
    with pytest.raises(OSError, match="Disconnected"):
        cli.provision_target(args)
    assert calls["closed"]
    assert calls["transaction"]["skip_backup"] is skip_backup
    assert calls["transaction"]["wifi"]["password"] == "secret"
    assert calls["transaction"]["key"] == b"k" * 32
    assert calls["transaction"]["transaction"] == tmp_path / ".local/share/flockinator/commissioning/38-44-BE-CC-6E-4C/A1-initial"
    assert calls["transaction"]["backup_root"].is_relative_to(tmp_path / ".local/share/flockinator")

@pytest.mark.parametrize('invalid', ['same_boot', 'same_slot', 'pending_validation', 'wrong_digest', 'no_receiver'])
def test_wifi_reinstall_waits_for_verified_new_boot(tmp_path, monkeypatch, invalid):
    before = dict(base_mac=MAC, label='A1', boot_count=5, running_partition='ota_0',
                  app_sha256='a'*64, ota_state=2, commissioning_link=dict(receiver_version=1))
    after = dict(before, boot_count=6, running_partition='ota_1')
    wrong = dict(after)
    if invalid == 'same_boot': wrong['boot_count'] = 5
    if invalid == 'same_slot': wrong['running_partition'] = 'ota_0'
    if invalid == 'pending_validation': wrong['ota_state'] = 1
    if invalid == 'wrong_digest': wrong['app_sha256'] = 'b'*64
    if invalid == 'no_receiver': wrong['commissioning_link'] = dict(receiver_version=0)
    snapshots = iter([before, wrong, after]); reads = []
    class Client:
        def request(self, method, path, *args, **kwargs):
            if method == 'POST': return dict(ok=True)
            s = next(snapshots); reads.append(s); return s
    monkeypatch.setattr(cli, 'resolve_target', lambda args: None)
    monkeypatch.setattr(cli, 'management_key', lambda mac: b'k'*32)
    monkeypatch.setattr(cli, 'NetworkClient', lambda *args: Client())
    monkeypatch.setattr(cli, 'validate_status', lambda value, *args: value)
    monkeypatch.setattr(cli, 'verify_image', lambda *args: 'a'*64)
    monkeypatch.setattr(cli.time, 'sleep', lambda seconds: None)
    image = tmp_path/'app.bin'; image.write_bytes(b'image')
    cli.main(['update', '--mac', MAC, '--address', '192.0.2.1', '--label', 'A1',
              '--image', str(image), '--sha256', 'c'*64])
    assert reads == [before, wrong, after]
