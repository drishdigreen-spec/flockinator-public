"""File/embedded-digest checks for the pinned unencrypted ESP-IDF app format.

This is an integrity check against a trusted build manifest, not a signature or
replacement for ESP-IDF's image/target validation at activation.
"""
import hashlib
from pathlib import Path


def verify_image(path: Path, expected_sha256: str) -> str:
    size = path.stat().st_size
    if not 56 <= size <= 8 * 1024 * 1024:
        raise ValueError("Image size is outside the reviewed OTA slot")
    data = path.read_bytes()
    if data[0] != 0xE9 or hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("Image does not match the trusted build manifest")
    image_digest = hashlib.sha256(data[:-32]).digest()
    if data[-32:] != image_digest:
        raise ValueError("Embedded ESP image digest mismatch")
    return image_digest.hex()
