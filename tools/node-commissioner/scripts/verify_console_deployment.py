"""Hardware acceptance runner. Uses the identified console and private node key."""
import argparse
import json
import time
from pathlib import Path
from urllib.error import HTTPError

from node_commissioner.console import ConsoleClient
from node_commissioner.credentials import management_key
from node_commissioner.network import NetworkClient

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--package', type=Path, required=True)
parser.add_argument('--name', required=True)
parser.add_argument('--evidence', type=Path, required=True)
parser.add_argument('--expect-failure', action='store_true')
parser.add_argument('--test-writer-exclusion', action='store_true')
args = parser.parse_args()
manifest = json.loads((args.package / 'manifest.json').read_text())
client = ConsoleClient('/dev/cu.usbmodem201101')
node = NetworkClient('192.168.1.10', '00:11:22:33:44:55', management_key('00:11:22:33:44:55'))
args.evidence.mkdir(parents=True, exist_ok=False)

def save(name, value):
    (args.evidence / name).write_text(json.dumps(value, indent=2) + '\n')

try:
    before_node = node.request('GET', '/v1/status')
    save('node-before.json', before_node)
    client.identify()
    for attempt in range(30):
        before = client.request('status')
        if before['nodes'][0]['observed'] and before['nodes'][0]['age_ms'] < 10000:
            break
        time.sleep(1)
    else:
        raise RuntimeError('No fresh A1 health before deployment')
    save('console-before.json', before)
    print('Uploading image to LilyGo SD', flush=True)
    start = time.monotonic()
    last_bucket = -1
    def progress(update):
        global last_bucket
        bucket = update['offset'] * 10 // update['total']
        if bucket != last_bucket:
            last_bucket = bucket
            print(f'SD upload {bucket * 10}%', flush=True)
    uploaded = client.upload(args.package / 'firmware.bin', manifest['file_sha256'], args.name, progress=progress)
    uploaded['elapsed_seconds'] = time.monotonic() - start
    save('sd-upload.json', uploaded)
    print(json.dumps(uploaded), flush=True)
    accepted = client.request('deploy', label='A1', name=args.name, image_sha256=manifest['esp_image_sha256'])
    save('accepted.json', accepted)
    start = time.monotonic()
    writer_checked = False
    with (args.evidence / 'progress.jsonl').open('x') as log:
        while time.monotonic() - start < 900:
            status = client.request('status')
            log.write(json.dumps(status) + '\n'); log.flush()
            if status['boot_id'] != before['boot_id']:
                raise RuntimeError('Console restarted during deployment')
            print(json.dumps({k: status[k] for k in ['deployment','offset','total','busy','serial_write_failures']}), flush=True)
            if args.test_writer_exclusion and not writer_checked and 0 < status['offset'] < status['total']:
                try:
                    node.request('POST', '/v1/update', bytes(288), timeout=5)
                except HTTPError as error:
                    assert error.code == 503, error.code
                    save('writer-exclusion.json', dict(http_status=error.code, espnow_offset=status['offset'], expected='HTTP writer rejected while ESP-NOW owns update lease'))
                    writer_checked = True
                    print('Concurrent HTTP writer rejected with503', flush=True)
                else:
                    raise AssertionError('Concurrent HTTP writer was accepted')
            if not status['busy']:
                break
            time.sleep(5)
        else:
            raise TimeoutError('Deployment exceeded 15 minutes')
    save('console-after.json', status)
    assert not args.test_writer_exclusion or writer_checked
    after = node.request('GET', '/v1/status')
    save('node-after.json', after)
    assert after['label'] == 'A1' and after['base_mac'] == before_node['base_mac']
    observed = status['nodes'][0]
    if args.expect_failure:
        assert not observed['deployment_verified']
        assert after['app_sha256'] == before_node['app_sha256'] and after['ota_state'] == 2
        result = 'REJECTED_OR_ROLLED_BACK_PREVIOUS_VALID_IMAGE_RETAINED'
        if 'INVALID_CHECKSUM' in manifest.get('status', ''):
            assert after['boot_count'] == before_node['boot_count']
            assert status['offset'] == status['total'] == manifest['file_bytes']
            assert 'receiver rejected' in status['deployment']
            result = 'INVALID_ESP_CHECKSUM_REJECTED_WITHOUT_REBOOT'
    else:
        assert observed['deployment_verified'] and observed['image_sha256'] == manifest['esp_image_sha256']
        assert after['app_sha256'] == manifest['esp_image_sha256'] and after['ota_state'] == 2
        assert after['boot_count'] != before_node['boot_count']
        result = 'VERIFIED'
    summary = dict(result=result, seconds=time.monotonic()-start, version=after['firmware'], image_sha256=after['app_sha256'])
    save('result.json', summary)
    print(json.dumps(summary), flush=True)
finally:
    client.close()
