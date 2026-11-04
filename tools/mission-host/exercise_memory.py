"""Portable, versioned per-unit exercise journals and separate director truth."""
from datetime import datetime, timezone
from io import BytesIO
import hashlib
import json
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

RULESET = 'search-board-1'


def label(i):
    return f'{chr(65+i%4)}{1+i//4}'


def utc(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat(timespec='milliseconds')


def bundle(plan, phase, sim, events):
    journals = [[] for _ in sim['units']]
    segments = plan['segments']
    for entry in events:
        i, turn, event, detail = entry
        # A resume at turn T first affects the timestamp of turn T+1.
        base, start = next((s for s in reversed(segments) if s[0]<turn),segments[0])
        records = journals[i]
        records.append(dict(schema=1, source='planner_simulation', ruleset=RULESET,
                            run=plan['episode'], unit=label(i), seq=len(records)+1,
                            turn=turn, utc=utc(start+turn-base), event=event, **detail))
    manifest = dict(schema=1, ruleset=RULESET, source='planner_simulation',
                    run=plan['episode'], phase=phase, last_turn=sim['turn'],
                    started_utc=utc(segments[0][1]), units=[label(i) for i in range(len(journals))],
                    scenario={k:v for k,v in plan.items() if k not in ('revision','since','segments','contacts')},
                    ground_truth=plan['contacts'], clock_segments=segments)
    buf=BytesIO()
    with ZipFile(buf,'w',ZIP_DEFLATED) as z:
        z.writestr(ZipInfo('director.json'), json.dumps(manifest, indent=2), compress_type=ZIP_DEFLATED)
        for i,records in enumerate(journals):
            z.writestr(ZipInfo(label(i)+'.jsonl'), ''.join(json.dumps(r,separators=(',',':'))+'\n' for r in records), compress_type=ZIP_DEFLATED)
    return buf.getvalue()

def deliver_one(archive_dir, run, unit, client):
    """A receipt exists only after an independent read of the committed card file."""
    with ZipFile(archive_dir/(run+'.zip')) as z:
        name=unit+'.jsonl'
        if name not in z.namelist():
            return False
        payload=z.read(name)
    digest=hashlib.sha256(payload).hexdigest()
    reply=client.request('POST','/v1/journal',payload,timeout=10)
    if reply!={'ok':True,'sha256':digest,'bytes':len(payload)}:
        raise ValueError('Journal write not verified')
    if client.read_journal(digest)!=payload:
        raise ValueError('Journal retrieval mismatch')
    folder=archive_dir/run
    folder.mkdir(exist_ok=True)
    receipt=folder/(unit+'.receipt')
    temp=receipt.with_suffix('.tmp')
    temp.write_text(json.dumps(dict(run=run,unit=unit,mac=client.mac,sha256=digest,bytes=len(payload))))
    temp.replace(receipt)
    return True
