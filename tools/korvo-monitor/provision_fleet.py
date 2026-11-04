"""Provision a roster over the identified Korvo USB link from JSON on stdin.

Output contains the session operator PIN. Redirect it to a private file.
An empty roster retrieves the PIN without changing credentials.
"""
import argparse
import fcntl
import ipaddress
import json
from pathlib import Path
import re
import sys
import time
import serial

MAC = '00:11:22:33:44:55'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    args = parser.parse_args()
    roster = json.load(sys.stdin)
    labels = {f'{r}{c}' for r in 'ABCD' for c in '1234'}
    if roster and (len(roster) != 16 or {p['label'] for p in roster} != labels):
        raise ValueError('Expected all sixteen panel identities')
    for panel in roster:
        ipaddress.IPv4Address(panel['ip'])
        if not re.fullmatch(r'(?:[0-9A-F]{2}:){5}[0-9A-F]{2}', panel['mac']):
            raise ValueError('Invalid MAC')
        if not re.fullmatch(r'[0-9a-f]{64}', panel['key']):
            raise ValueError('Invalid key')
    lock = Path.home()/'.cache/flockinator-korvo/bridge.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        port = serial.Serial(port=None, baudrate=115200, timeout=.25, write_timeout=2)
        port.dtr = port.rts = False
        port.port = args.port
        with port:
            def wait_for(prefix, seconds=20):
                end = time.monotonic()+seconds
                while time.monotonic() < end:
                    line = port.read_until(b'\n', 1024).strip()
                    if line.startswith(prefix):
                        return line
                raise RuntimeError('USB acknowledgement timed out')

            if wait_for(b'KORVO1 ', 45) != f'KORVO1 {MAC}'.encode():
                raise RuntimeError('Wrong controller identity')
            for panel in sorted(roster, key=lambda p: p['label']):
                port.write(f"FK1 {MAC} {panel['label']} {panel['ip']} {panel['mac']} {panel['key']}\n".encode())
                if wait_for(b'FK1 ') != b'FK1 OK':
                    raise RuntimeError('Controller rejected roster entry')
            port.write(f'OP1 {MAC}\n'.encode())
            reply = wait_for(b'OP1 ')
            if not re.fullmatch(rb'OP1 [0-9]{6}', reply):
                raise RuntimeError('Invalid operator PIN response')
            print(json.dumps({'provisioned': len(roster), 'pin': reply[4:].decode()}))


if __name__ == '__main__':
    main()
