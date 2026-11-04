"""Explicit, latest-only survey delivery over authenticated maintenance HTTP.

A local lock excludes duplicate bridges on this host. Firmware does not yet
implement cross-host controller leases; see docs/development.md before use.
"""
import argparse
import concurrent.futures
import csv
from contextlib import ExitStack, contextmanager
import fcntl
import json
from pathlib import Path
import threading
import time
import urllib.request

from node_commissioner.network import NetworkClient
from node_commissioner.credentials import management_key

ROOT = Path(__file__).resolve().parents[2]
SUPPORTED_FIRMWARE = frozenset({'0.10.0', '0.10.1'})


class BridgeError(ValueError):
    """Only fixed, non-secret diagnostic codes may be passed to this class."""


class BridgeTarget:
    def __init__(self, row, client):
        self.row, self.client = row, client
        self.index = (int(row['label'][1])-1)*4+ord(row['label'][0])-ord('A')
        self.last = None
        self.attempted = False
        self.expected_run = None
        self.report = dict(label=row['label'], sent=0, errors=0, verified=False, yielded=False)

    def deliver(self, packet):
        if self.report['yielded']:
            return
        if packet.get('n') != self.index or packet.get('op') != 'display_survey':
            raise BridgeError('snapshot_identity')
        identity = (packet['run'], packet['seq'])
        if identity == self.last:
            return
        body = json.dumps(packet, separators=(',', ':'), allow_nan=False).encode()
        if len(body) >= 512:
            raise BridgeError('snapshot_size')
        # Read immediately before delivery. After taking control, any observed
        # mode/run change permanently yields this worker until explicit restart.
        status = self.client.request('GET', '/v1/status', timeout=3)
        if (status.get('label') != self.row['label']
                or status.get('base_mac') != self.row['dhcp_reservation_mac']
                or status.get('firmware') not in SUPPORTED_FIRMWARE):
            raise BridgeError('identity_or_firmware')
        self.report.update(verified=True, status=status, status_at=time.time())
        panel = status.get('panel', {})
        survey = panel.get('survey', {})
        if self.attempted and (panel.get('source') != 'host_fictional_survey'
                or survey.get('active') is not True
                or survey.get('run') != self.expected_run):
            self.report.update(yielded=True, last_error='control_changed')
            return
        self.attempted = True
        self.expected_run = identity[0]
        result = self.client.request('POST', '/v1/control', body, timeout=3)
        if result.get('ok') is not True:
            raise BridgeError('snapshot_rejected')
        self.last = identity
        self.report.update(sent=self.report['sent']+1, last_ok=time.time(),
                           run=identity[0], seq=identity[1], last_error=None)


@contextmanager
def node_lock(mac, directory=None):
    directory = directory or Path.home()/'.local/share/flockinator/bridge-locks'
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (directory/(mac.replace(':', '-')+'.lock')).open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another local bridge owns this node') from None
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--labels', nargs='+', required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--take-control', action='store_true', help='Explicitly select survey on the named nodes')
    args = parser.parse_args()
    if not args.take_control:
        parser.error('--take-control is required; this command changes the selected display mode')
    with (ROOT/'docs/inventory/network.csv').open() as stream:
        rows = [r for r in csv.DictReader(stream) if r['role']=='node' and r['label'] in args.labels]
    if len(rows) != len(set(args.labels)) or len(args.labels) != len(set(args.labels)):
        parser.error('Unknown or duplicate labels')
    lock = threading.Lock()
    latest = dict(data=None, received=0, error='waiting_for_source')
    reports = {r['label']: dict(label=r['label'], sent=0, errors=0, verified=False) for r in rows}
    stop = threading.Event()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def read_source():
        while not stop.is_set():
            try:
                with opener.open('http://127.0.0.1:8767/api/state', timeout=2) as response:
                    value = json.loads(response.read(131072))
                if value['version'] != 2 or len(value['wire']) != 16:
                    raise ValueError('Invalid source envelope')
                with lock:
                    latest.update(data=value, received=time.monotonic(), error=None)
            except Exception as exc:
                with lock:
                    latest['error'] = type(exc).__name__
            stop.wait(.5)

    def worker(target):
        while not stop.is_set():
            try:
                with lock:
                    data, age = latest['data'], time.monotonic()-latest['received']
                if data is not None and age < 1.5:
                    target.deliver(data['wire'][target.index])
            except Exception as exc:
                target.report.update(errors=target.report['errors']+1, verified=False,
                                     last_error=str(exc) if isinstance(exc, BridgeError) else type(exc).__name__)
            with lock:
                reports[target.row['label']] = dict(target.report)
            stop.wait(.5)

    # Resolve every credential and acquire every lock before any hardware access.
    with ExitStack() as stack:
        targets = []
        for row in rows:
            mac = row['dhcp_reservation_mac']
            stack.enter_context(node_lock(mac))
            targets.append(BridgeTarget(row, NetworkClient(row['ipv4'], mac, management_key(mac))))
        args.report.parent.mkdir(parents=True, exist_ok=True)
        source = threading.Thread(target=read_source, daemon=True)
        source.start()
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(rows)) as pool:
                futures = [pool.submit(worker, target) for target in targets]
                try:
                    while not stop.is_set():
                        for future in futures:
                            if future.done():
                                future.result()
                                raise RuntimeError('Bridge worker stopped')
                        with lock:
                            value = json.dumps(dict(updated=time.time(), nodes=reports,
                                source_error=latest['error'], source_age_seconds=None if not latest['received'] else time.monotonic()-latest['received']), indent=2)
                        temp = args.report.with_suffix('.tmp')
                        temp.write_text(value)
                        temp.replace(args.report)
                        stop.wait(1)
                finally:
                    stop.set()
        except KeyboardInterrupt:
            pass
        finally:
            stop.set()
            source.join(timeout=3)


if __name__ == '__main__':
    main()
