"""Ten-minute hardware observation, including deliberate A1 absence/recovery."""
import json
import subprocess
import time
from pathlib import Path
from node_commissioner.console import ConsoleClient
from node_commissioner.credentials import management_key
from node_commissioner.network import NetworkClient

root = Path(__file__).resolve().parents[3]
evidence = root / 'docs/validation/commissioning-link/live-soak'
evidence.mkdir(exist_ok=False)
hold_code = r'''
import esptool,time
from esptool.cmds import detect_chip
esp=detect_chip(port='/dev/cu.usbmodem201301',baud=115200,connect_attempts=3)
identified=False
try:
    mac=':'.join(f'{b:02X}' for b in esp.read_mac())
    if esp.CHIP_NAME!='ESP32-S3' or mac!='00:11:22:33:44:55':
        raise SystemExit('Unexpected node; no hold performed')
    identified=True
    print('A1 identified; holding ROM for115 seconds without flash writes',flush=True)
    time.sleep(115)
finally:
    if identified:esp.hard_reset()
    esp._port.close()
'''
client = ConsoleClient('/dev/cu.usbmodem201101')
node_mac='00:11:22:33:44:55'
node=NetworkClient('192.168.1.10',node_mac,management_key(node_mac))
process=None
observations=[]
try:
    initial=client.identify()
    before=node.request('GET','/v1/status')
    (evidence/'node-before.json').write_text(json.dumps(before,indent=2)+'\n')
    boot=initial['boot_id']
    started=time.monotonic()
    with (evidence/'samples.jsonl').open('x') as log, (evidence/'deliberate-node-absence.log').open('x') as absence_log:
        while time.monotonic()-started<600:
            elapsed=time.monotonic()-started
            if elapsed>=60 and process is None:
                process=subprocess.Popen(['uv','run','--no-project','--with','esptool==4.9.0','python','-c',hold_code],stdout=absence_log,stderr=subprocess.STDOUT)
            status=client.request('status')
            assert status['boot_id']==boot,'Unexpected console reset'
            assert status['serial_write_failures']==0
            observed=status['nodes'][0]
            sample=dict(elapsed_seconds=round(elapsed,2),console=status)
            log.write(json.dumps(sample)+'\n');log.flush();observations.append(sample)
            print(json.dumps(dict(seconds=int(elapsed),health=observed['health'],age_ms=observed['age_ms'],boots=observed['boots'],free=status['free_internal'],radio_drops=status.get('rx_queue_overflows'))),flush=True)
            time.sleep(5)
    assert process is not None and process.wait(timeout=5)==0
    after=node.request('GET','/v1/status')
    (evidence/'node-after.json').write_text(json.dumps(after,indent=2)+'\n')
    states={sample['console']['nodes'][0]['health'] for sample in observations}
    assert {'Healthy','Stale','Offline'}<=states,states
    assert observations[-1]['console']['nodes'][0]['health']=='Healthy'
    assert after['app_sha256']==before['app_sha256'] and after['boot_count']==before['boot_count']+1
    assert after['ota_state']==2
    settled=[sample['console']['free_internal'] for sample in observations if sample['elapsed_seconds']>30]
    report=dict(result='PASS',seconds=time.monotonic()-started,samples=len(observations),health_states=sorted(states),console_boot_id=boot,console_heap_min=min(settled),console_heap_max=max(settled),console_heap_first=settled[0],console_heap_last=settled[-1],expected_node_restarts=1,actual_node_restarts=after['boot_count']-before['boot_count'],scope='Radio and automatic e-paper refresh; physical touch/sleep/wake acceptance remains manual')
    assert settled[-1]>=settled[0]-4096,'Console retained heap declined more than4KB'
    (evidence/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
finally:
    client.close()
    if process is not None and process.poll() is None:
        # Do not kill the helper in ROM; its finally must reset the node.
        print('ROM helper still running; leave it to restore A1 automatically',flush=True)
