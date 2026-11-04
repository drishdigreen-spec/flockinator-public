"""Connect the identified controller USB prop to the loopback mission host."""
import argparse
import fcntl
import json
import ipaddress
from pathlib import Path
import re
import time
import urllib.request
import serial
from serial.tools.list_ports import comports

IDENTITY = b'KORVO1 00:11:22:33:44:55'
USB_SERIAL = '00000000000000000000000000000000'  # example: set your controller adapter serial
BASE = 'http://127.0.0.1:8782'
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def post(path, value):
    req = urllib.request.Request(BASE+path, data=json.dumps(value).encode(),
                                 headers={'Content-Type':'application/json'})
    with opener.open(req, timeout=3) as resp:
        return json.load(resp)


def run(device):
    port = serial.Serial(port=None, baudrate=115200, timeout=.1, write_timeout=2)
    port.dtr = port.rts = False
    port.port = device
    with port:
        identity_at = 0
        deadline = time.monotonic()+12
        while time.monotonic()<deadline:
            if port.read_until(b'\n', 512).strip()==IDENTITY:
                identity_at=time.monotonic()
                break
        if not identity_at:
            raise RuntimeError('Korvo factory identity missing')
        next_poll, data, pending = 0, None, None
        confirmed = set()
        lab_ip = None
        print('Connected to identified Korvo', flush=True)
        while time.monotonic()-identity_at<12:
            if time.monotonic()>=next_poll:
                data = post('/api/prop', {'lab_ip':lab_ip} if lab_ip else {})
                active = data['status']=='Running'
                frames = []
                for index, n in enumerate(data['nodes']):
                    if n['health']:
                        frames.append(n['health'])
                    x,y,_,heading = n['pose']
                    frames.append(f'P2 {index} {round(x*10)} {round(y*10)} {round(heading)%360} {int(active)} {int(active)} {n["code"]}')
                port.write(('\n'.join(frames)+'\n').encode())
                m = data['mission']
                if pending and m['request']==pending[1] and m['result'] is not None:
                    ok = len(m['result'])
                    port.write(f'R1 {pending[0]} 1 {ok} {16-ok}\n'.encode())
                    pending = None
                elif pending and m['request']!=pending[1]:
                    pending = None  # Another client moved on; device times out as unknown.
                next_poll=time.monotonic()+1
            line=port.read_until(b'\n',512).strip()
            if line.startswith(b'LAB1 '):
                try:
                    lab_ip=str(ipaddress.IPv4Address(line[5:].decode('ascii')))
                except ValueError:
                    lab_ip=None
            if line==IDENTITY:
                identity_at=time.monotonic()
            if len(confirmed) < 16:
                receipt = re.search(rb'monitor: received=(\d+) state=1\b', line)
                if receipt:
                    confirmed.add(int(receipt[1]))
                    if confirmed == set(range(16)):
                        print('Korvo acknowledged health frames for all 16 panels', flush=True)
            match=re.fullmatch(rb'MC1 (\d{1,10}) ([01]) ([0-2]) ([0-2]) (64|96) ([01])',line)
            if match and not pending and not data['busy']:
                rid,start,scenario,goal,seconds,repeat=map(int,match.groups())
                try:
                    reply=post('/api/mission',dict(previous=data['mission']['request'],
                               start=bool(start),scenario=scenario,goal=goal,seconds=seconds,repeat=bool(repeat)))
                except urllib.error.HTTPError as exc:
                    if exc.code!=409:
                        raise
                    port.write(f'R1 {rid} 1 0 16\n'.encode())
                    continue
                pending = (rid, reply['request'])
                port.write(f'R1 {rid} 0 0 16\n'.encode())
        raise RuntimeError('Korvo stopped reporting identity')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port')
    args=parser.parse_args()
    device=args.port or next((p.device for p in comports() if p.serial_number==USB_SERIAL),None)
    if not device:
        raise SystemExit('Korvo USB adapter absent')
    lock=Path.home()/'.cache/flockinator-korvo/bridge.lock'
    lock.parent.mkdir(parents=True,exist_ok=True)
    with lock.open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run(device)
