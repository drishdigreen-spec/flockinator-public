"""Pinned esptool 4.9 adapter; operations remain on an identity-checked ROM handle.

No commands run at import/construction. The runner and serial factory are
injectable for tests. Original flash and all tool logs stay in private storage.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from uuid import uuid4

from .protocol import valid_mac, validate_status
from .provisioning import IDENTITY_END, IDENTITY_START, Package, file_digest
from .serial_link import SerialLink

# The check and command share the same open serial connection. Merely parsing a
# separate read-mac invocation cannot protect against a board swapped afterwards.
_GUARDED_ESPTOOL = r'''
import json, sys
import esptool
from esptool.cmds import detect_chip, DETECTED_FLASH_SIZES
if esptool.__version__ != "4.9.0":
    raise SystemExit("Unexpected esptool version")
port, expected_mac, operation = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
esp = detect_chip(port=port, baud=115200, connect_attempts=3)
try:
    actual_mac = ":".join(f"{part:02X}" for part in esp.read_mac())
    if esp.CHIP_NAME != "ESP32-S3" or actual_mac != expected_mac:
        raise SystemExit("Target identity mismatch before operation")
    security = esp.get_security_info()
    if security["flags"] & 5 or bin(security["flash_crypt_cnt"]).count("1") % 2:
        raise SystemExit("Protected device is outside the commissioning path")
    esp.flash_spi_attach(0)
    jedec = esp.flash_id()
    if DETECTED_FLASH_SIZES.get((jedec >> 16) & 0xff) != "32MB":
        raise SystemExit("Target flash geometry is not 32 MB")
    print("FLOCK_PROBE=" + json.dumps(dict(base_mac=actual_mac, chip=esp.CHIP_NAME,
        flash_bytes=33554432, secure_boot=False, flash_encryption=False,
        jedec_id=jedec, chip_revision=esp.get_chip_revision())))
    # First boot mutates OTA metadata. Stay in the loader after writing so the
    # next identity-checked verification can compare every artifact unchanged.
    after = "no_reset" if operation[0] == "write_flash" else "hard_reset"
    esptool.main(["--chip", "esp32s3", "--port", port, "--baud", "460800",
                  "--after", after, *operation], esp=esp)
finally:
    esp._port.close()
'''


def subprocess_runner(arguments: list[str], timeout: float) -> subprocess.CompletedProcess:
    return subprocess.run(arguments, capture_output=True, text=True, timeout=timeout, check=False)


class EsptoolBackend:
    def __init__(self, *, port: str, mac: str, package: Package, private_directory: Path,
                 runner=subprocess_runner, serial_factory=SerialLink):
        if not valid_mac(mac) or not port.startswith("/dev/cu."):
            raise ValueError("Expected exact factory MAC and explicit macOS USB serial port")
        self.port, self.mac, self.package = port, mac, package
        self.private_directory = private_directory
        self.runner, self.serial_factory = runner, serial_factory
        self.link = None
        self.expected_boot_after = None

    def close(self) -> None:
        if self.link is not None:
            self.link.close()
            self.link = None

    def _private_dir(self) -> None:
        self.private_directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.private_directory.is_symlink() or self.private_directory.stat().st_mode & 0o077:
            raise ValueError("Tool log directory must be private")

    def _command(self, operation: list[str], timeout: float = 120) -> str:
        self.close()
        self._private_dir()
        arguments = ["uv", "run", "--no-project", "--with", "esptool==4.9.0", "python", "-c",
                     _GUARDED_ESPTOOL, self.port, self.mac, json.dumps(operation)]
        log = self.private_directory / f"{uuid4().hex}-{operation[0]}.log"
        try:
            result = self.runner(arguments, timeout)
        except subprocess.TimeoutExpired as error:
            # Do not propagate captured output from tool exceptions into CLI logs.
            raise TimeoutError(f"Device operation timed out: {operation[0]}") from None
        output = result.stdout + result.stderr
        fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(output)
            stream.flush()
            os.fsync(stream.fileno())
        if result.returncode:
            raise RuntimeError(f"Device operation failed: {operation[0]}; private log: {log}")
        return output

    def _read_range(self, offset: int, size: int) -> bytes:
        self._private_dir()
        path = self.private_directory / f"{uuid4().hex}-probe.bin"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        try:
            self._command(["read_flash", hex(offset), str(size), str(path)])
            result = path.read_bytes()
            if len(result) != size:
                raise ValueError("Short flash probe read")
            return result
        finally:
            path.unlink(missing_ok=True)

    def probe(self) -> dict:
        output = self._command(["flash_id"])
        lines = [line.removeprefix("FLOCK_PROBE=") for line in output.splitlines() if line.startswith("FLOCK_PROBE=")]
        if len(lines) != 1:
            raise ValueError("Missing exact device probe record")
        probe = json.loads(lines[0])
        identity = self._read_range(IDENTITY_START, IDENTITY_END - IDENTITY_START)
        blank = all(byte == 255 for byte in identity)
        # Existing identity is preserved only under the same partition layout.
        # Actual label and credential compatibility is enforced by firmware.
        if not blank:
            current_table = self._read_range(0x8000, 4096)
            table = next(item for item in self.package.artifacts if item.offset == 0x8000)
            expected = table.path.read_bytes()
            blank = current_table[:len(expected)] == expected and all(byte == 255 for byte in current_table[len(expected):])
        probe["identity_region_safe"] = blank
        return probe

    def backup(self, destination: Path, size: int) -> None:
        fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        self._command(["read_flash", "0", str(size), str(destination)], timeout=900)

    def verify_backup(self, path: Path) -> None:
        self._command(["verify_flash", "0", str(path)], timeout=900)

    def flash(self, package: Package) -> None:
        package.validate()
        arguments = ["write_flash", "--flash_mode", "keep", "--flash_freq", "keep", "--flash_size", "keep"]
        for item in sorted(package.artifacts, key=lambda item: item.offset):
            arguments.extend([hex(item.offset), str(item.path)])
        self._command(arguments, timeout=300)

    def verify_flash(self, package: Package) -> None:
        arguments = ["verify_flash"]
        for item in sorted(package.artifacts, key=lambda item: item.offset):
            arguments.extend([hex(item.offset), str(item.path)])
        self._command(arguments, timeout=300)

    def _status_ready(self, timeout: float = 45) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                if self.link is None:
                    self.link = self.serial_factory(self.port, self.mac)
                status = validate_status(self.link.request(timeout=4), self.mac)
                if self.expected_boot_after is None or status.get("boot_count", -1) > self.expected_boot_after:
                    return status
            except TimeoutError:
                # Opening USB can reset this board. A missed early request is
                # retried on the same connection so startup can finish.
                pass
            except OSError:
                self.close()
            time.sleep(0.2)
        raise TimeoutError("No verified post-boot response from selected node")

    def configure(self, label: str, wifi: dict, key: bytes) -> None:
        # Verify unassigned/current identity before sending any configuration.
        self._status_ready()
        self.link.request("provision", label=label)
        self.link.request("wifi", **wifi)
        self.link.request("set_key", key=key.hex())

    def reboot(self) -> None:
        status = self._status_ready()
        self.expected_boot_after = status["boot_count"]
        self.link.request("reboot")

    def status(self) -> dict:
        return self._status_ready()
