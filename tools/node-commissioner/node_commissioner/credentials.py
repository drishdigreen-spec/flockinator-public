"""Controller-local credentials, with explicit one-time import from 1Password."""
import json
import os
from pathlib import Path
import re
import subprocess
import stat
import tempfile

REFERENCES = Path(__file__).with_name("credential-references.json")


def _vault_credential(relative: str) -> dict:
    path = Path(os.environ.get("FLOCK_CREDENTIAL_REFERENCES", REFERENCES))
    try:
        manifest = json.loads(path.read_text())
        matches = [e for e in manifest["entries"] if e["relative_path"] == relative]
        if len(matches) != 1:
            raise ValueError()
        reference = matches[0]["credential_json_ref"]
        # The references use stable vault/item IDs, with no resolved secrets.
        if not re.fullmatch(r"op://[a-z0-9]{26}/[a-z0-9]{26}/credential_json", reference):
            raise ValueError()
    except (OSError, ValueError, KeyError, TypeError):
        raise ValueError("Missing or invalid credential reference; check FLOCK_CREDENTIAL_REFERENCES") from None
    try:
        result = subprocess.run(["op", "read", reference], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError("1Password unavailable; verify CLI access to Infra") from None
    if result.returncode:
        raise ValueError("1Password read failed; verify CLI access to Infra")
    try:
        value = json.loads(result.stdout)
        if not isinstance(value, dict):
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Invalid credential JSON in 1Password") from None
    return value


LOCAL_STORE = Path.home()/".local/share/flockinator/controller-secrets/credentials.json"


def store_path() -> Path:
    return Path(os.environ.get("FLOCK_CREDENTIAL_STORE", LOCAL_STORE)).expanduser()


def _private_stat(info, directory=False):
    required = stat.S_ISDIR if directory else stat.S_ISREG
    if not required(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("Controller credential store must be user-owned and private (directory 0700, file 0600)")


def _validate_record(relative, value):
    if relative == "wifi.json":
        if (not isinstance(value, dict) or set(value) != {"ssid", "password"}
                or not all(isinstance(v, str) for v in value.values())
                or not 1 <= len(value["ssid"].encode()) <= 32
                or not 8 <= len(value["password"].encode()) <= 63):
            raise ValueError("Invalid Wi-Fi credential schema")
    else:
        match = re.fullmatch(r"nodes/([0-9A-F]{2}(?:-[0-9A-F]{2}){5})\.json", relative)
        if (not match or not isinstance(value, dict) or set(value) != {"base_mac", "key"}
                or value["base_mac"] != match[1].replace("-", ":")
                or not isinstance(value["key"], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", value["key"])):
            raise ValueError("Invalid management credential or board identity")
    return value


def _read_local(path):
    try:
        _private_stat(path.parent.lstat(), directory=True)
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd) as source:
            _private_stat(os.fstat(source.fileno()))
            if os.fstat(source.fileno()).st_size > 131072:
                raise ValueError("Oversized controller credential store")
            value = json.load(source)
        if not isinstance(value, dict) or set(value) != {"version", "credentials"} or value["version"] != 1 or not isinstance(value["credentials"], dict):
            raise ValueError("Invalid controller credential store")
        for relative, record in value["credentials"].items():
            _validate_record(relative, record)
        return value["credentials"]
    except (OSError, ValueError, TypeError, KeyError):
        raise ValueError("Invalid or insecure local controller credential store; repair it explicitly (no vault fallback)") from None


def _credential(relative: str) -> dict:
    path = store_path()
    # lexists detects broken symlinks too: they must never trigger a vault prompt.
    if os.path.lexists(path):
        records = _read_local(path)
        if relative not in records:
            raise ValueError("Credential missing from local controller store; import it explicitly")
        return records[relative]
    return _vault_credential(relative)


def write_local_store(records: dict) -> None:
    for relative, value in records.items():
        _validate_record(relative, value)
    path = store_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    _private_stat(path.parent.lstat(), directory=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as target:
            temp = Path(target.name)
            os.fchmod(target.fileno(), 0o600)
            json.dump({"version": 1, "credentials": records}, target)
            target.flush()
            os.fsync(target.fileno())
        # Atomic creation; never overwrite an existing store or follow a symlink.
        os.link(temp, path)
    except OSError:
        raise ValueError("Cannot create controller credential store; an existing store is never overwritten") from None
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def import_vault() -> int:
    if os.path.lexists(store_path()):
        raise ValueError("Local controller store already exists; it will not be overwritten")
    try:
        manifest = json.loads(Path(os.environ.get("FLOCK_CREDENTIAL_REFERENCES", REFERENCES)).read_text())
        relatives = [entry["relative_path"] for entry in manifest["entries"]]
        if not relatives or len(relatives) != len(set(relatives)):
            raise ValueError()
    except (OSError, ValueError, KeyError, TypeError):
        raise ValueError("Invalid credential reference manifest") from None
    records = {}
    for relative in relatives:
        records[relative] = _validate_record(relative, _vault_credential(relative))
    write_local_store(records)
    return len(records)


def save_wifi() -> None:
    raise ValueError("save-wifi is disabled; use an explicit controller-store import or manage the vault record")


def load_wifi() -> dict:
    value = _credential("wifi.json")
    if (set(value) != {"ssid", "password"}
            or not all(isinstance(v, str) for v in value.values())
            or not 1 <= len(value["ssid"].encode()) <= 32
            or not 8 <= len(value["password"].encode()) <= 63):
        raise ValueError("Invalid Wi-Fi credential schema")
    return value


def management_key(mac: str, create: bool = False) -> bytes:
    from .protocol import valid_mac
    if not valid_mac(mac):
        raise ValueError("Invalid factory MAC")
    # Provisioning may request create=True; always reuse the identity-bound controller/vault
    # record. Missing records require explicit credential creation, never rotation.
    value = _credential("nodes/" + mac.replace(":", "-") + ".json")
    if (set(value) != {"base_mac", "key"} or value["base_mac"] != mac
            or not isinstance(value["key"], str)
            or not re.fullmatch(r"[0-9a-fA-F]{64}", value["key"])):
        raise ValueError("Invalid management credential or board identity")
    return bytes.fromhex(value["key"])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Controller credential storage")
    parser.add_argument("command", choices=["import-vault"])
    parser.parse_args()
    try:
        count = import_vault()
    except ValueError as error:
        parser.exit(1, str(error) + "\n")
    print(f"Imported {count} credential records into the private local controller store. Routine commands now use it without 1Password.")
