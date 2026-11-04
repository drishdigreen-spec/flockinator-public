"""Interrupt an identified console transfer; verify A1's running slot survives."""
import json
import subprocess
import time
from pathlib import Path
from node_commissioner.console import ConsoleClient
from node_commissioner.credentials import management_key
from node_commissioner.network import NetworkClient
from node_commissioner.provisioning_backend import _GUARDED_ESPTOOL

root = Path(__file__).resolve().parents[3]
evidence = root / 'docs/validation/cluster-deployment/console-interruption'
evidence.mkdir(exist_ok=False)
node_mac = '00:11:22:33:44:55'
node = NetworkClient('192.168.1.10', node_mac, management_key(node_mac))
before = node.request('GET', '/v1/status')
(evidence/'node-before.json').write_text(json.dumps(before, indent=2)+'\n')
manifest = json.loads((root/'firmware/node-platform/releases/0.4.1-bringup/manifest.json').read_text())
client = ConsoleClient('/dev/cu.usbmodem201101')
try:
    client.identify()
    for _ in range(30):
        status = client.request('status')
        if status['nodes'][0]['observed'] and status['nodes'][0]['age_ms'] < 10000:
            break
        time.sleep(1)
    else:
        raise RuntimeError('No fresh A1 health')
    old_boot = status['boot_id']
    client.request('deploy', label='A1', name='node-0.4.1.bin', image_sha256=manifest['esp_image_sha256'])
    for _ in range(60):
        status = client.request('status')
        if 65536 <= status['offset'] < status['total']:
            break
        assert status['busy']
        time.sleep(1)
    else:
        raise RuntimeError('No partial transfer to interrupt')
    (evidence/'partial-transfer.json').write_text(json.dumps(status, indent=2)+'\n')
finally:
    client.close()

# Read-only ROM flash-ID operation resets the identified console. No firmware,
# partitions, credentials or card contents are written by this operation.
wrapper = _GUARDED_ESPTOOL.replace('"32MB"','"16MB"').replace('33554432','16777216').replace('not 32 MB','not 16 MB')
with (evidence/'console-reset.log').open('x') as log:
    subprocess.run(['uv','run','--no-project','--with','esptool==4.9.0','python','-c',wrapper,
                    '/dev/cu.usbmodem201101','00:11:22:33:44:55',json.dumps(['flash_id'])],
                   stdout=log,stderr=subprocess.STDOUT,check=True)
print('Console reset during partial transfer; waiting for receiver timeout', flush=True)
time.sleep(25)
after = node.request('GET','/v1/status')
(evidence/'node-after.json').write_text(json.dumps(after,indent=2)+'\n')
assert after['app_sha256'] == before['app_sha256']
assert after['boot_count'] == before['boot_count'] and after['ota_state'] == 2
assert not after['commissioning_link']['transfer_active']
assert after['commissioning_link']['transfer_timeouts'] > before['commissioning_link']['transfer_timeouts']
client = ConsoleClient('/dev/cu.usbmodem201101')
try:
    client.identify()
    for _ in range(30):
        current = client.request('status')
        if current['nodes'][0]['observed']:
            break
        time.sleep(1)
    (evidence/'console-reconciled.json').write_text(json.dumps(current,indent=2)+'\n')
    assert current['boot_id'] != old_boot and not current['busy']
    assert current['nodes'][0]['image_sha256'] == after['app_sha256']
    assert not current['nodes'][0]['deployment_verified']
finally:
    client.close()
print('PASS: previous valid image retained; timeout released writer; console shows actual build', flush=True)
