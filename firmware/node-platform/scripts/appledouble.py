"""Ignore macOS resource-fork companions on external volumes, never source files."""
from pathlib import Path

Import("env")

# PlatformIO otherwise treats ._example.cpp as compilable C++ on this volume.
for folder in ("src", "include", "test", "managed_components"):
    for path in (Path(env.subst("$PROJECT_DIR")) / folder).rglob("._*"):
        if path.is_file():
            with path.open("rb") as stream:
                is_appledouble = stream.read(4) == b"\x00\x05\x16\x07"
            if is_appledouble:
                path.unlink()
