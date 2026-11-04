"""Explicit, card-bound SD maintenance. Never formats on status/inspection."""
import argparse
import csv
import json
import re
import time
from pathlib import Path
from .credentials import management_key
from .network import NetworkClient
from .evidence import redact


def _identity(status, mac, label):
    if status.get('base_mac') != mac or status.get('label') != label:
        raise ValueError('SD maintenance target identity changed')
    if status.get('sd', {}).get('maintenance_supported') is not True:
        raise ValueError('Node firmware does not support SD maintenance')


def prepare(client, mac, label, *, sleep=time.sleep):
    before = client.request('GET', '/v1/status')
    _identity(before, mac, label)
    response = client.request('POST', '/v1/control', b'{"op":"sd_prepare"}')
    job = response.get('job')
    if response.get('ok') is not True or type(job) is not int or not job:
        raise ValueError('SD inspection was not accepted')
    for _ in range(30):
        sleep(1)
        current = client.request('GET', '/v1/status')
        _identity(current, mac, label)
        if any(current.get(k) != before.get(k) for k in ('boot_count', 'app_sha256')):
            raise ValueError('Node rebooted or firmware changed during inspection')
        sd = current['sd']
        if sd.get('test', {}).get('job') != job:
            continue  # Cached status may lag the accepted request by two seconds.
        phase = sd['test'].get('phase')
        if phase == 'FAILED':
            return current
        if phase != 'READY':
            continue
        previous_card = before['sd'].get('card_id')
        if previous_card and previous_card != sd.get('card_id'):
            raise ValueError('Card changed during inspection; inspect the replacement separately')
        if not re.fullmatch(r'[0-9a-f]{80}', sd.get('card_id', '')) or not re.fullmatch(r'[0-9a-f]{32}', sd.get('format_token', '')):
            raise ValueError('Missing card identity or fresh format permit')
        if sd.get('presence') != 'RESPONDING' or sd.get('sector_bytes') != 512:
            raise ValueError('Card geometry or presence is unverified')
        return current
    raise TimeoutError('SD inspection completion not observed')


def start(client, mac, label, mode, *, erase=False, sleep=time.sleep):
    if not erase or mode not in ('quick', 'full'):
        raise ValueError('Formatting requires --erase and an explicit quick/full mode')
    inspected = prepare(client, mac, label, sleep=sleep)
    sd = inspected['sd']
    if sd['test']['phase'] != 'READY':
        raise ValueError('Card did not enumerate; no erasure attempted')
    body = json.dumps(dict(op='sd_format_'+mode, card_id=sd['card_id'], token=sd['format_token']), separators=(',', ':')).encode()
    accepted = client.request('POST', '/v1/control', body)
    if accepted.get('ok') is not True or type(accepted.get('job')) is not int or not accepted['job']:
        raise ValueError('Formatting was not accepted')
    return accepted, inspected


def validate_result(status, job):
    result = status.get('sd', {}).get('test', {})
    if result.get('job') != job:
        raise ValueError('Wrong SD test job')
    if result.get('phase') == 'PASSED':
        target = result.get('target_bytes')
        if type(target) is not int or target <= 0 or result.get('written_bytes') != target or result.get('read_bytes') != target:
            raise ValueError('Incomplete extent cannot be a successful test')
    return result


def observe(client, mac, label):
    """Read current progress without replacing a permit, result or active job."""
    current = client.request('GET', '/v1/status')
    _identity(current, mac, label)
    return current


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True, choices=[r+c for r in 'ABCD' for c in '1234'])
    transport = parser.add_mutually_exclusive_group(required=True)
    transport.add_argument('--address')
    transport.add_argument('--console-port', help='Identified LilyGo USB port; relays SD commands by ESP-NOW')
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument('--format', choices=['quick', 'full'])
    operation.add_argument('--status', action='store_true', help='Only read current job/card status; do not prepare a new job')
    parser.add_argument('--erase', action='store_true', help='Explicitly authorise entire node SD reset')
    parser.add_argument('--output', type=Path, required=True, help='New evidence directory')
    parser.add_argument('--wait', type=float, default=180, help='Seconds to observe; jobs continue on the node')
    args = parser.parse_args()
    if not 0 <= args.wait <= 86400:
        parser.error('--wait must be between 0 and 86400')
    if args.erase and not args.format:
        parser.error('--erase requires --format')
    root = Path(__file__).resolve().parents[3]
    with (root/'docs/inventory/nodes.csv').open(newline='') as source:
        row = next(row for row in csv.DictReader(source) if row['label'] == args.label)
    mac = row['factory_base_mac']
    if args.console_port:
        from .console import ConsoleClient
        from .sd_console import ConsoleSdClient
        console = ConsoleClient(args.console_port)
        console.identify()
        client = ConsoleSdClient(console, mac, args.label)
    else:
        client = NetworkClient(args.address, mac, management_key(mac))
    args.output.mkdir(parents=True, exist_ok=False)
    def save(name, value):
        with (args.output/name).open('x') as f:
            json.dump(redact(value), f, indent=2); f.write('\n')
    if args.status:
        current = observe(client, mac, args.label)
        save('status.json', current)
        print(json.dumps(redact(current['sd']), indent=2))
        return
    if not args.format:
        observed = prepare(client, mac, args.label)
        save('inspection.json', observed)
        print(json.dumps(redact(observed['sd']), indent=2))
        return
    accepted, inspected = start(client, mac, args.label, args.format, erase=args.erase)
    save('inspection.json', inspected); save('accepted.json', accepted)
    job = accepted['job']; print(f'{args.label}: job {job} accepted ({args.format})', flush=True)
    deadline = time.monotonic()+args.wait
    with (args.output/'progress.jsonl').open('x') as evidence:
        while time.monotonic() < deadline:
            time.sleep(3)
            s = client.request('GET', '/v1/status'); _identity(s, mac, args.label)
            if s['sd'].get('test', {}).get('job') != job:
                continue
            result = validate_result(s, job)
            if s['sd'].get('card_id') != inspected['sd']['card_id']:
                raise ValueError('Card identity changed during maintenance')
            evidence.write(json.dumps(redact(s))+'\n'); evidence.flush()
            print(json.dumps(result), flush=True)
            if result['phase'] in ('PASSED', 'FAILED', 'INTERRUPTED'):
                save('result.json', s)
                if result['phase'] != 'PASSED':
                    raise RuntimeError('SD test did not pass; see recorded result')
                return
    print('Observation ended; job completion remains unverified. The node may still be working.', flush=True)


if __name__ == '__main__':
    main()
