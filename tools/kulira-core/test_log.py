import json, pytest
from kulira_core.log import AttackLog, LogError, verify_log

def make(tmp_path):
    p = tmp_path/"attacks.jsonl"
    log = AttackLog(p, clock=lambda: "2026-11-04T00:00:00Z")
    log.append("arm", {"module":"kulira-disrupt","action":"drop"})
    log.append("fire", {"module":"kulira-disrupt","action":"drop"})
    return p

def test_log_hash_chain_verifies(tmp_path):
    p = make(tmp_path)
    entries = verify_log(p)
    assert [e["seq"] for e in entries]==[1,2] and entries[1]["prev_sha256"]==entries[0]["sha256"]

def test_tampered_line_fails_loudly(tmp_path):
    p = make(tmp_path)
    lines=p.read_text().splitlines(); d=json.loads(lines[0]); d["kind"]="forged"; lines[0]=json.dumps(d)
    p.write_text("\n".join(lines)+"\n")
    with pytest.raises(LogError, match="seq 1"): verify_log(p)

def test_truncated_log_fails(tmp_path):
    p = make(tmp_path)
    p.write_text(p.read_text().splitlines()[0][:20]+"\n")
    with pytest.raises(LogError): verify_log(p)
