import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).parent
def run_cli(*args):
    return subprocess.run([sys.executable,"-m","kulira_core.cli",*args], capture_output=True, text=True, cwd=ROOT)

def test_cli_validate_and_dry_run(tmp_path):
    scen=ROOT/"scenarios"/"false-beacon.json"
    r=run_cli("campaign","validate",str(scen)); assert r.returncode==0, r.stderr
    out=tmp_path/"run"
    r=run_cli("campaign","run",str(scen),"--dry-run","--out",str(out)); assert r.returncode==0, r.stderr
    assert (out/"report.json").exists()
    r=run_cli("campaign","report","--run",str(out)); assert r.returncode==0 and "COMPLETED" in r.stdout
