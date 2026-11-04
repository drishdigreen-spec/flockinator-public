"""Retrieve a verified rehearsal journal directly from a panel SD card."""
import argparse
import csv
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/node-commissioner'))
from node_commissioner.credentials import management_key
from node_commissioner.network import NetworkClient
from node_commissioner.protocol import validate_status


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipt',type=Path)
    parser.add_argument('output',type=Path,help='New JSONL file')
    args=parser.parse_args()
    record=json.loads(args.receipt.read_text())
    with (ROOT/'docs/inventory/network.csv').open() as f:
        row=next(r for r in csv.DictReader(f) if r['label']==record['unit'] and r['role']=='node')
    mac=row['dhcp_reservation_mac']
    if mac!=record['mac']:
        raise ValueError('Card receipt does not match inventory')
    client=NetworkClient(row['ipv4'],mac,management_key(mac))
    validate_status(client.request('GET','/v1/status'),mac,row['label'])
    data=client.read_journal(record['sha256'])
    if len(data)!=record['bytes']:
        raise ValueError('Receipt length mismatch')
    with args.output.open('xb') as f:
        f.write(data)
    print(f"Read {len(data)} verified bytes from {row['label']} SD")


if __name__=='__main__':
    main()
