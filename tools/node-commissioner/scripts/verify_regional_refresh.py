"""Observe regional refresh while a known A1 is briefly held in ROM and restored."""
import json
import subprocess
import time
from pathlib import Path
from node_commissioner.console import ConsoleClient
from node_commissioner.credentials import management_key
from node_commissioner.network import NetworkClient

root=Path(__file__).resolve().parents[3]
evidence=root/'docs/validation/commissioning-link/refresh-0.2.9'
evidence.mkdir(exist_ok=False)
hold_code=r'''
import esptool,time
from esptool.cmds import detect_chip
esp=detect_chip(port='/dev/cu.usbmodem201301',baud=115200,connect_attempts=3)
identified=False
try:
    mac=':'.join(f'{b:02X}' for b in esp.read_mac())
    if esp.CHIP_NAME!='ESP32-S3' or mac!='00:11:22:33:44:55':
        raise SystemExit('Unexpected node; no hold performed')
    identified=True
    print('A1 identified; holding ROM for50 seconds without flash writes',flush=True)
    time.sleep(50)
finally:
    if identified:esp.hard_reset()
    esp._port.close()
'''
client=ConsoleClient('/dev/cu.usbmodem201101')
mac='00:11:22:33:44:55'
node=NetworkClient('192.168.1.10',mac,management_key(mac))
raw=bytearray(); original_read=client.port.read
def read(size):
    data=original_read(size);raw.extend(data);return data
client.port.read=read
process=None; samples=[]
try:
    before=node.request('GET','/v1/status')
    (evidence/'node-before.json').write_text(json.dumps(before,indent=2)+'\n')
    first=client.identify()
    assert first['version']=='0.2.9-live' and first['image']=='node-0.4.2.bin'
    started=time.monotonic()
    with (evidence/'samples.jsonl').open('x') as log, (evidence/'node-absence.log').open('x') as hold_log:
        while time.monotonic()-started<150:
            elapsed=time.monotonic()-started
            if elapsed>=30 and process is None:
                process=subprocess.Popen(['uv','run','--no-project','--with','esptool==4.9.0','python','-c',hold_code],stdout=hold_log,stderr=subprocess.STDOUT)
            current=client.request('status')
            assert current['boot_id']==first['boot_id']
            assert current['serial_write_failures']==0 and current['rx_queue_overflows']==0
            sample=dict(seconds=elapsed,console=current)
            samples.append(sample);log.write(json.dumps(sample)+'\n');log.flush()
            print(json.dumps(dict(seconds=int(elapsed),health=current['nodes'][0]['health'],refreshes=raw.count(b'refresh:done'))),flush=True)
            time.sleep(5)
    assert process is not None and process.wait(timeout=5)==0
    after=node.request('GET','/v1/status')
    (evidence/'node-after.json').write_text(json.dumps(after,indent=2)+'\n')
    assert after['boot_count']==before['boot_count']+1
    assert after['app_sha256']==before['app_sha256'] and after['ota_state']==2
    states={s['console']['nodes'][0]['health'] for s in samples}
    assert {'Healthy','Stale'}<=states and samples[-1]['console']['nodes'][0]['health']=='Healthy'
    # USB open resets the console; a few already-buffered lines can precede it.
    # Keep raw evidence intact but scope timing analysis to the observed boot.
    text=raw.decode(errors='replace')
    marker='build=0.2.9-live '
    assert marker in text,'Missing boot marker for refresh attribution'
    lines=text[text.rindex(marker):].splitlines()
    regions=[dict(part.split('=',1) for part in line.split()[1:]) for line in lines if line.startswith('refresh:region ')]
    timings=[dict(part.split('=',1) for part in line.split()[1:]) for line in lines if line.startswith('refresh:timing ')]
    assert sum(r['mode']=='full' for r in regions)==1,regions
    partial=[r for r in regions if r['mode']=='regional']
    assert len(partial)>=2,regions
    assert all(0<=int(r['x'])<242 and 110<=int(r['y'])<180 and int(r['x'])+int(r['w'])<=242 and int(r['y'])+int(r['h'])<=180 for r in partial),partial
    late=[s['console']['free_internal'] for s in samples if s['seconds']>100]
    assert max(late)-min(late)<4096
    result=dict(result='PASS',version=first['version'],seconds=time.monotonic()-started,regions=regions,timings=timings,node_restarts=1,final_node_boots=after['boot_count'],health_states=sorted(states),final_heap=late[-1],optical_ghosting_and_manual_controls='PENDING_OWNER_CHECK')
    (evidence/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
except Exception as error:
    (evidence/'result.json').write_text(json.dumps(dict(result='FAIL',reason=str(error)),indent=2)+'\n')
    raise
finally:
    client.close();(evidence/'serial.log').write_bytes(raw)
    if process is not None and process.poll() is None:
        print('Leave ROM helper running so it restores A1 automatically',flush=True)
