"""Provision the identified Korvo over its USB link; read Wi-Fi JSON from stdin."""
import argparse
import fcntl
import ipaddress
import json
from pathlib import Path
import re
import sys
import time
import serial

MAC='00:11:22:33:44:55'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',required=True)
    args=parser.parse_args()
    cfg=json.load(sys.stdin)
    ssid=cfg['ssid'].encode()
    password=cfg['password'].encode()
    if not (1<=len(ssid)<=32 and 8<=len(password)<=63) or b'\0' in ssid+password:
        raise ValueError('Invalid Wi-Fi fields')
    lock=Path.home()/'.cache/flockinator-korvo/bridge.lock'
    lock.parent.mkdir(parents=True,exist_ok=True)
    with lock.open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        port=serial.Serial(port=None,baudrate=115200,timeout=.25,write_timeout=2)
        port.dtr=port.rts=False
        port.port=args.port
        with port:
            end=time.monotonic()+70
            sent=confirmed=False
            while time.monotonic()<end:
                line=port.read_until(b'\n',512).strip()
                if not sent and line==f'KORVO1 {MAC}'.encode():
                    port.write(f'LW1 {MAC} {ssid.hex()} {password.hex()}\n'.encode())
                    sent=True
                elif line==b'LW1 REJECTED':
                    raise RuntimeError('Korvo rejected Wi-Fi provisioning')
                elif line==b'LW1 OK':
                    confirmed=True
                elif confirmed and (m:=re.search(rb'(?:Controller URL http://|LAB1 )(\d+\.\d+\.\d+\.\d+)',line)):
                    print(ipaddress.IPv4Address(m[1].decode()),flush=True)
                    return
            raise RuntimeError(f'Korvo did not report an IP (identity={sent}, saved={confirmed})')


if __name__=='__main__':
    main()
