"""Authenticated avatar controls; does not alter node identity or storage."""
import argparse
import csv
import json
from pathlib import Path
from .network import NetworkClient
from .credentials import management_key

def state_command(activity='idle', attention='calm', mood='neutral', ttl=60):
    if activity not in ('sleeping','idle','listening','processing','waiting','speaking') or attention not in ('calm','attentive','urgent') or mood not in ('neutral','curious','content','frightened'):
        raise ValueError('Unknown display state')
    if type(ttl) is not int or not 1 <= ttl <= 300:
        raise ValueError('TTL must be 1–300 seconds')
    if activity=='sleeping' and (attention!='calm' or mood=='frightened'):
        raise ValueError('Sleeping requires calm attention and no fear')
    return dict(op='display_state',activity=activity,attention=attention,mood=mood,ttl=ttl)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--label',required=True);p.add_argument('--address')
    p.add_argument('--activity',default='idle');p.add_argument('--attention',default='calm');p.add_argument('--mood',default='neutral');p.add_argument('--ttl',type=int,default=60)
    mode=p.add_mutually_exclusive_group();mode.add_argument('--auto',action='store_true');mode.add_argument('--demo',action='store_true');mode.add_argument('--random',action='store_true',help='Autonomous random expressions until auto, another state/demo, or reboot');mode.add_argument('--profile',choices=['doom-calm','doom-injury-test'])
    args=p.parse_args()
    inventory=Path(__file__).resolve().parents[3]/'docs/inventory/network.csv'
    rows=[r for r in csv.DictReader(inventory.open()) if r['label']==args.label and r['role']=='node']
    if len(rows)!=1:raise ValueError('Unknown/ambiguous fleet label')
    r=rows[0];mac=r['dhcp_reservation_mac'];client=NetworkClient(args.address or r['ipv4'],mac,management_key(mac))
    before=client.request('GET','/v1/status')
    if before.get('label')!=args.label:raise ValueError('Identity mismatch')
    command=dict(op='display_auto') if args.auto else dict(op='display_random') if args.random else dict(op='display_demo') if args.demo else dict(op='display_profile',profile=args.profile) if args.profile else state_command(args.activity,args.attention,args.mood,args.ttl)
    result=client.request('POST','/v1/control',json.dumps(command,separators=(',',':')).encode())
    if not result.get('ok'):raise RuntimeError(result.get('error','Display request failed'))
    print(json.dumps(dict(label=args.label,command=command,result=result)))
if __name__=='__main__':main()
