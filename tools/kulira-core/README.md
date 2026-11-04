# Kulira Core

Seeded, bounded, hash-logged chaos orchestrator. See `SPEC-kulira-core.md`.

## Commands (repo root, on Kulira)

The workspace is an SMB mount; keep the venv off it:

```sh
export UV_PROJECT_ENVIRONMENT="$HOME/.cache/flockinator-kulira-core/venv"
uv sync --project tools/kulira-core
$UV_PROJECT_ENVIRONMENT/bin/python -m kulira_core.cli campaign validate tools/kulira-core/scenarios/false-beacon.json
$UV_PROJECT_ENVIRONMENT/bin/python -m kulira_core.cli campaign run tools/kulira-core/scenarios/false-beacon.json --dry-run --out validation/kulira/false-beacon-001-271828
$UV_PROJECT_ENVIRONMENT/bin/python -m kulira_core.cli campaign report --run validation/kulira/false-beacon-001-271828
$UV_PROJECT_ENVIRONMENT/bin/python -m pytest tools/kulira-core -q
```

Scenarios are JSON. Live/RF runs require `authorised: true` after review;
network jamming devices are never used — interference is L1/2/3 protocol
technique on the lab network only. Dry-run emits no fleet traffic.
