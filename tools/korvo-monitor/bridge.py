"""Authenticated fleet polling and mission control for the Korvo over USB."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import fcntl
from pathlib import Path
import re
import sys
import time
import urllib.error
import serial

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/node-commissioner'))
from mission_projection import project
from mission_dispatch import dispatch
from node_commissioner.credentials import management_key
from node_commissioner.network import NetworkClient
from node_commissioner.protocol import validate_status

KORVO = '00:11:22:33:44:55'

def status_frame(index, status, mac, label):
    if not isinstance(status, dict):
        raise ValueError("Invalid status object")
    validate_status(status, mac, label)
    version = status.get('firmware')
    if not isinstance(version, str) or not re.fullmatch(r'[A-Za-z0-9._-]{1,16}', version):
        raise ValueError('Invalid firmware version')
    numbers = [status.get('uptime_ms'), status.get('free_internal')]
    if any(type(n) is not int or not 0 <= n <= limit
           for n, limit in zip(numbers, (0xFFFFFFFF * 1000 + 999, 0xFFFFFFFF))):
        raise ValueError('Invalid status counters')
    return f'F1 {index} 1 {version} {numbers[0]//1000} {numbers[1]//1024}\n'.encode()

def poll(index, row, client):
    state = 2
    if client is not None:
        try:
            status = client.request('GET', '/v1/status', timeout=3)
            health=status_frame(index, status, row['factory_base_mac'], row['label'])
            try:
                world=project(index,status,row['factory_base_mac'],row['label'])
                if world:
                    x,y,_=world['position']; freshness={'LIVE':1,'RESYNC':2,'STALE':0}[world['freshness']]
                    health+=f'P2 {index} {round(x*10)} {round(y*10)} {round(world["heading"])} {freshness} {int(world["running"])} {world["state"]}\n'.encode()
            except (ValueError, TypeError, KeyError):
                pass
            return health
        except urllib.error.HTTPError:
            pass  # Authentication/server error is not proof that a node is offline.
        except (urllib.error.URLError, TimeoutError, OSError):
            state = 0
        except (ValueError, TypeError, KeyError, AttributeError):
            pass
    return f'F1 {index} {state} - 0 0\n'.encode()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', default='/dev/cu.usbserial-20130')
    parser.add_argument('--seconds', type=float, default=0, help='Bounded validation run; zero runs until interrupted')
    args = parser.parse_args()
    lock_path = Path.home()/'.cache/flockinator-korvo/bridge.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        nodes = {r['label']: r for r in csv.DictReader((ROOT/'docs/inventory/nodes.csv').open())}
        addresses = {r['label']: r['ipv4'] for r in csv.DictReader((ROOT/'docs/inventory/network.csv').open())}
        rows = [nodes[f'{r}{c}'] for r in 'ABCD' for c in range(1,5)]
        clients = []
        for row in rows:
            try:
                clients.append(NetworkClient(addresses[row['label']], row['factory_base_mac'], management_key(row['factory_base_mac'])))
            except (ValueError, KeyError):
                print(f"{row['label']}: credential/configuration unavailable", flush=True)
                clients.append(None)
        port = serial.Serial(port=None, baudrate=115200, timeout=.05, write_timeout=2)
        port.dtr=False; port.rts=False; port.port=args.port
        with port:
            deadline=time.monotonic()+12
            while time.monotonic()<deadline:
                line=port.read_until(b'\n', 512).strip()
                if any(tag in line for tag in (b'feedback:', b'controls:', b'overview_layout')):
                    print(line.decode(errors='replace'), flush=True)
                if line == f'KORVO1 {KORVO}'.encode():
                    break
            else:
                raise RuntimeError('Expected Korvo identity not received; no telemetry sent')
            print(f'Connected to Korvo {KORVO}; fleet status and mission control', flush=True)
            started=time.monotonic()
            due=[0.0]*16; pending={}; received=bytearray(); request=None; job=None
            with ThreadPoolExecutor(max_workers=16) as pool:
                while not args.seconds or time.monotonic()-started < args.seconds:
                    now=time.monotonic()
                    for i in range(16):
                        if request is None and job is None and i not in pending and now>=due[i]:
                            pending[i]=pool.submit(poll, i, rows[i], clients[i])
                    for i, future in list(pending.items()):
                        if future.done():
                            frame=future.result()
                            port.write(frame)
                            print(frame.decode().strip(), flush=True)
                            del pending[i]; due[i]=now+5
                    if request is not None and job is None and not pending:
                        rid, start, scenario, goal, seconds, repeat = request
                        port.write(f'R1 {rid} 0 0 16\n'.encode())
                        job=pool.submit(dispatch, bool(start), scenario, goal, seconds, bool(repeat), rows, clients)
                        request=None
                    if job is not None and job.done():
                        run, results=job.result()
                        port.write(f'R1 {rid} 1 {sum(results)} {16-sum(results)}\n'.encode())
                        print(f'mission run={run} verified={sum(results)} failed={16-sum(results)} labels={",".join(rows[i]["label"] for i,ok in enumerate(results) if not ok) or "none"}',flush=True)
                        job=None
                        due=[0.0]*16
                    # Drain diagnostic output so it cannot fill the serial receive buffer.
                    received.extend(port.read(4096))
                    while b'\n' in received:
                        line, _, received = received.partition(b'\n')
                        match=re.fullmatch(rb'MC1 ([0-9]{1,10}) ([01]) ([0-2]) ([0-2]) (64|96) ([01])',line.strip())
                        if match:
                            print('USB '+line.decode(errors='replace').strip(), flush=True)
                        if match and request is None and job is None:
                            request=tuple(int(v) for v in match.groups())
                        if any(tag in line for tag in (b'monitor: received=', b'feedback:', b'controls:', b'mission:', b'overview_layout')):
                            print(line.decode(errors='replace').strip(), flush=True)
                    if len(received) > 4096:
                        received.clear()
                    time.sleep(.05)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
