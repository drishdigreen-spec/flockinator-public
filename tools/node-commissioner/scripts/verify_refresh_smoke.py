"""Verify final UI-only firmware keeps live health without unchanged refreshes."""
import argparse
import json
import time
from pathlib import Path
from node_commissioner.console import ConsoleClient

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--version',required=True)
parser.add_argument('--evidence-name',required=True)
args=parser.parse_args()
assert Path(args.evidence_name).name==args.evidence_name
root=Path(__file__).resolve().parents[3]
evidence=root/'docs/validation/commissioning-link'/args.evidence_name
evidence.mkdir(exist_ok=False)
client=ConsoleClient('/dev/cu.usbmodem201101')
raw=bytearray()
original_read=client.port.read
def read(size):
    data=original_read(size)
    raw.extend(data)
    return data
client.port.read=read
samples=[]
try:
    first=client.identify()
    assert first['version']==args.version
    assert first['image']=='node-0.4.2.bin'
    assert first['image_sha256']=='e809c0a2da43e4d7780116c89828961187e2fe8e1e19c590324826bf6087ff9d'
    started=time.monotonic()
    settled_refreshes=None
    with (evidence/'samples.jsonl').open('x') as log:
        while time.monotonic()-started<120:
            current=client.request('status')
            elapsed=time.monotonic()-started
            count=raw.count(b'refresh:done')
            if elapsed>30 and settled_refreshes is None:
                settled_refreshes=count
            assert current['boot_id']==first['boot_id']
            assert current['serial_write_failures']==0
            assert current['rx_queue_overflows']==0
            if elapsed>15:
                assert current['nodes'][0]['health']=='Healthy'
                assert current['nodes'][0]['age_ms']<10000
            sample=dict(elapsed_seconds=elapsed,completed_refreshes=count,console=current)
            samples.append(sample);log.write(json.dumps(sample)+'\n');log.flush()
            print(json.dumps(dict(seconds=int(elapsed),refreshes=count,health=current['nodes'][0]['health'],free=current['free_internal'])),flush=True)
            time.sleep(5)
    assert settled_refreshes is not None and settled_refreshes>=1
    assert raw.count(b'refresh:done')==settled_refreshes,'Unchanged overview kept refreshing'
    renders=[]
    for line in raw.decode(errors='replace').splitlines():
        if line.startswith('ui:render '):
            renders.append(dict(part.split('=',1) for part in line.split()[1:]))
    assert len(renders)>=6,'Insufficient instrumented display observations'
    settled_renders=[r for r in renders if int(r['sample_ms'])>30000]
    assert settled_renders and all(r['page']=='0' and r['a1_health']=='Healthy' and r['refresh']=='0' for r in settled_renders),'Display did not retain stable Healthy overview'
    assert samples[-1]['console']['nodes'][0]['boots']==samples[3]['console']['nodes'][0]['boots']
    report=dict(result='PASS',seconds=time.monotonic()-started,total_refreshes=settled_refreshes,refreshes_after_settling=0,render_observations=renders,console_version=first['version'],image_selection_persisted=first['image'],scope='Unchanged overview and live A1 health; manual touch/Refresh/sleep remain separate acceptance')
    (evidence/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
except Exception as error:
    report=dict(result='FAIL',console_version=args.version,reason=str(error),samples=len(samples),total_refreshes=raw.count(b'refresh:done'))
    (evidence/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    raise
finally:
    client.close()
    (evidence/'serial.log').write_bytes(raw)
