"""Resumable commissioning, with no device I/O outside an injected backend.

A station holds the inventory lock for the entire transaction. Successful stages
are immutable, fsynced records; interrupted operations are repeated, never
inferred successful. Backends must target the selected MAC on every connection.
"""
from __future__ import annotations

import csv
import fcntl
import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from .evidence import redact
from .protocol import valid_mac, validate_status

IDENTITY_START = 0x1020000
IDENTITY_END = 0x1030000


def file_digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _immutable_json(path: Path, value: dict) -> None:
    """Publish a complete immutable record; crashes cannot leave partial JSON."""
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        _sync_directory(path.parent)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _export_record(source: Path, destination: Path) -> None:
    """Export verified evidence without hard links or overwriting prior reports.

    The private source is the atomically published authority. A power loss may
    leave an incomplete export, but cannot commit inventory: retries publish a
    fresh sequence. The journal never depends on parsing this exported copy.
    """
    with destination.open("xb") as stream:
        stream.write(source.read_bytes())
        stream.flush()
        os.fsync(stream.fileno())
    if file_digest(source) != file_digest(destination):
        raise ValueError("Evidence export integrity failure")
    _sync_directory(destination.parent)


@dataclass(frozen=True)
class Artifact:
    path: Path
    offset: int
    sha256: str


@dataclass(frozen=True)
class Package:
    """Explicit complete initial-install package, never an arbitrary flash range."""
    version: str
    app_image_sha256: str
    artifacts: tuple[Artifact, ...]
    chip: str = "ESP32-S3"
    flash_bytes: int = 33554432

    def validate(self) -> str:
        if self.chip != "ESP32-S3" or self.flash_bytes != 33554432:
            raise ValueError("Unsupported commissioning geometry")
        if not re.fullmatch(r"[0-9a-f]{64}", self.app_image_sha256):
            raise ValueError("Invalid runtime image digest")
        if {item.offset for item in self.artifacts} != {0, 0x8000, 0xF000, 0x20000} or len(self.artifacts) != 4:
            raise ValueError("Expected bootloader, partition table, OTA metadata and application offsets")
        records = []
        ranges = []
        for item in sorted(self.artifacts, key=lambda item: item.offset):
            if item.path.is_symlink() or not item.path.is_file() or file_digest(item.path) != item.sha256:
                raise ValueError("Package artifact integrity failure")
            size = item.path.stat().st_size
            end = item.offset + size
            if size == 0 or end > self.flash_bytes or item.offset < 0 or item.offset % 4096:
                raise ValueError("Invalid flash artifact range")
            # Account for flash-sector erasure, not only exact byte ranges.
            erased_end = (end + 4095) & ~4095
            if item.offset < IDENTITY_END and erased_end > IDENTITY_START:
                raise ValueError("Package would overwrite persistent identity")
            ranges.append((item.offset, erased_end))
            records.append(dict(offset=item.offset, bytes=size, sha256=item.sha256))
        if any(left[1] > right[0] for left, right in zip(ranges, ranges[1:])):
            raise ValueError("Overlapping package flash sectors")
        # Keep writes inside the established layout and out of general NVS.
        limits = {0: 0x8000, 0x8000: 0x9000, 0xF000: 0x11000, 0x20000: 0x820000}
        if any(end > limits[start] for start, end in ranges):
            raise ValueError("Artifact exceeds its commissioned partition")
        canonical = dict(version=self.version, app_image_sha256=self.app_image_sha256,
                         chip=self.chip, flash_bytes=self.flash_bytes, artifacts=records)
        return hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class Backend(Protocol):
    def probe(self) -> dict: ...
    def backup(self, destination: Path, size: int) -> None: ...
    def verify_backup(self, path: Path) -> None: ...
    def flash(self, package: Package) -> None: ...
    def verify_flash(self, package: Package) -> None: ...
    def configure(self, label: str, wifi: dict, key: bytes) -> None: ...
    def reboot(self) -> None: ...
    def status(self) -> dict: ...


class Provisioning:
    def __init__(self, *, backend: Backend, inventory: Path, transaction: Path,
                 backup_root: Path, evidence_root: Path, label: str, mac: str,
                 package: Package, wifi: dict, key: bytes, skip_backup: bool = False):
        if not re.fullmatch(r"[A-D][1-4]", label) or not valid_mac(mac) or len(key) != 32:
            raise ValueError("Invalid commissioning identity/credential")
        if set(wifi) != {"ssid", "password"} or not all(isinstance(value, str) for value in wifi.values()):
            raise ValueError("Invalid Wi-Fi configuration")
        self.backend, self.inventory = backend, inventory
        self.transaction, self.backup_root, self.evidence_root = transaction, backup_root, evidence_root
        self.label, self.mac, self.package, self.wifi, self.key = label, mac, package, wifi, key
        self.key_id = hashlib.sha256(key).hexdigest()[:16]
        self.skip_backup = skip_backup
        self.events: list[dict] = []

    def _record(self, stage: str, **details) -> dict:
        event = dict(sequence=len(self.events), stage=stage,
                     at_utc=datetime.now(timezone.utc).isoformat(), **details)
        _immutable_json(self.transaction / f"{len(self.events):04d}-{stage}.json", event)
        self.events.append(event)
        return event

    def _done(self, stage: str) -> dict | None:
        return next((event for event in reversed(self.events) if event["stage"] == stage), None)

    def _probe(self) -> dict:
        probe = self.backend.probe()
        expected = {"base_mac": self.mac, "chip": self.package.chip,
                    "flash_bytes": self.package.flash_bytes,
                    "secure_boot": False, "flash_encryption": False}
        if any(type(probe.get(name)) is not type(value) or probe.get(name) != value for name, value in expected.items()):
            raise ValueError("Device identity, geometry or protection mismatch")
        if probe.get("identity_region_safe") is not True:
            # An interrupted partition-table write may make layout recognition
            # fail. Only this exact bound transaction's recorded write attempt,
            # preceded by a verified backup or recorded owner waiver, permits
            # repeating its same package.
            if not (self._done("flash_started") and
                    (self._done("backup_verified") or self._done("backup_waived"))):
                raise ValueError("Existing identity partition layout is not recognised")
        return probe

    def _read_inventory(self) -> tuple[list[str], list[dict], dict]:
        with self.inventory.open(newline="") as stream:
            reader = csv.DictReader(stream)
            rows, fields = list(reader), reader.fieldnames
        if not fields or "factory_base_mac" not in fields or "status" not in fields:
            raise ValueError("Invalid inventory schema")
        labels = [row.get("label") for row in rows]
        if labels.count(self.label) != 1 or len(set(labels)) != len(labels):
            raise ValueError("Missing or duplicate inventory label")
        row = next(row for row in rows if row["label"] == self.label)
        if row["factory_base_mac"] not in ("", self.mac) or any(
            other["label"] != self.label and other["factory_base_mac"] == self.mac for other in rows
        ):
            raise ValueError("Inventory identity conflict")
        return fields, rows, row

    def _readback(self) -> dict:
        status = validate_status(self.backend.status(), self.mac, self.label)
        if (status.get("app_sha256") != self.package.app_image_sha256
                or status.get("firmware") != self.package.version
                or status.get("flash_bytes") != self.package.flash_bytes
                or status.get("psram_sample") != "PASS"
                or status.get("identity_nvs") != "PASS"
                or status.get("network", {}).get("wifi_configured") is not True
                or status.get("maintenance", {}).get("key_id") != self.key_id
                or status.get("maintenance", {}).get("key_provisioned") is not True):
            raise ValueError("Post-reboot identity, build, core health or credential readback failed")
        return redact(status)

    def run(self) -> dict:
        digest = self.package.validate()
        # This is the same lock used by update_inventory; no other station may
        # bind a conflicting label between preflight and final inventory commit.
        with self.inventory.with_suffix(".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self._read_inventory()
            self.transaction.mkdir(parents=True, exist_ok=True, mode=0o700)
            if self.transaction.is_symlink() or self.transaction.stat().st_mode & 0o077:
                raise ValueError("Transaction directory must be private")
            self.events = [json.loads(path.read_text()) for path in sorted(self.transaction.glob("[0-9]*.json"))]
            if any(event.get("sequence") != index for index, event in enumerate(self.events)):
                raise ValueError("Invalid transaction journal sequence")
            binding = dict(label=self.label, base_mac=self.mac, package_sha256=digest, key_id=self.key_id)
            if self.events:
                if self.events[0]["stage"] != "created" or any(self.events[0].get(key) != value for key, value in binding.items()):
                    raise ValueError("Resume binding/package/credential mismatch")
            else:
                self._record("created", **binding)
            self._probe()  # Required even if the preceding invocation completed.
            self._record("target_verified")
            backup = self._done("backup_verified")
            if backup:
                path = Path(backup["path"])
                if path.is_symlink() or path.stat().st_mode & 0o077 or file_digest(path) != backup["sha256"]:
                    raise ValueError("Preserved backup integrity failure")
            elif self.skip_backup or self._done("backup_waived"):
                if not self._done("backup_waived"):
                    self._record("backup_waived", reason="owner_authorized_skip_backup")
            else:
                self.backup_root.mkdir(parents=True, exist_ok=True, mode=0o700)
                if self.backup_root.is_symlink() or self.backup_root.stat().st_mode & 0o077:
                    raise ValueError("Backup directory must be private")
                path = self.backup_root / f"{self.mac.replace(':', '-')}-{uuid4().hex}.bin"
                self._record("backup_started", path=str(path))
                self.backend.backup(path, self.package.flash_bytes)
                if path.is_symlink() or path.stat().st_size != self.package.flash_bytes or path.stat().st_mode & 0o077:
                    raise ValueError("Backup must contain the entire flash and be private")
                with path.open("rb") as stream:
                    os.fsync(stream.fileno())
                self.backend.verify_backup(path)
                backup = self._record("backup_verified", path=str(path), sha256=file_digest(path), bytes=path.stat().st_size)
            if not self._done("flash_verified"):
                self._probe()
                self.package.validate()
                self._record("flash_started")
                self.backend.flash(self.package)
                self.backend.verify_flash(self.package)
                self._record("flash_verified")
            if not self._done("configured"):
                self._record("configuration_started")
                self.backend.configure(self.label, self.wifi, self.key)
                self._record("configured")
            # Always reboot/read back on resume: historic success does not prove
            # that the currently attached device retains the commissioned state.
            self.backend.reboot()
            snapshot = self._readback()
            readback = self._record("readback_verified", snapshot=snapshot)
            evidence_dir = self.evidence_root / self.label / self.transaction.name
            evidence_dir.mkdir(parents=True, exist_ok=True)
            evidence_path = evidence_dir / f"commissioning-{readback['sequence']:04d}.json"
            authoritative_dir = self.transaction / "evidence"
            authoritative_dir.mkdir(exist_ok=True, mode=0o700)
            authoritative_path = authoritative_dir / evidence_path.name
            _immutable_json(authoritative_path, dict(schema_version=1, **binding,
                observed_at_utc=readback["at_utc"], provisioning="commissioned_for_installation",
                manual_acceptance="PENDING", backup_status="verified" if backup else "waived_by_owner",
                backup_sha256=backup["sha256"] if backup else None, snapshot=snapshot))
            _export_record(authoritative_path, evidence_path)
            fields, rows, row = self._read_inventory()
            network, sd = snapshot.get("network", {}), snapshot.get("sd", {})
            values = dict(factory_base_mac=self.mac, status="commissioned_for_installation",
                firmware_version=self.package.version, firmware_sha256=self.package.app_image_sha256,
                flash_bytes=snapshot["flash_bytes"], psram_bytes=snapshot.get("psram_bytes", ""),
                wifi_sta_mac=network.get("wifi_sta_mac", ""), espnow_mac=network.get("espnow_mac", ""),
                espnow_interface="WIFI_IF_STA", sd_capacity_bytes=sd.get("capacity_bytes", ""),
                sd_filesystem=sd.get("filesystem", ""), provisioned_at=readback["at_utc"],
                notes=f"Controller commissioned; physical acceptance pending. Evidence: {evidence_path}")
            row.update({name: value for name, value in values.items() if name in fields})
            temporary = None
            try:
                with tempfile.NamedTemporaryFile("w", dir=self.inventory.parent, delete=False, newline="") as stream:
                    temporary = stream.name
                    writer = csv.DictWriter(stream, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(rows)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self.inventory)
                _sync_directory(self.inventory.parent)
            finally:
                if temporary and os.path.exists(temporary):
                    os.unlink(temporary)
            self._record("inventory_committed", evidence=str(evidence_path))
            return dict(label=self.label, base_mac=self.mac, status="commissioned_for_installation",
                        evidence=str(evidence_path), snapshot=snapshot)
