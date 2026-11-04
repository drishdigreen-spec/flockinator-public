"""Identified LilyGo setup, private roster provisioning and SD image delivery."""
import argparse
import csv
import json
import re
import math
import sys
import time
import uuid
from pathlib import Path
import serial
from .credentials import load_wifi, management_key
from .image import verify_image
from .protocol import valid_mac

ROOT = Path(__file__).resolve().parents[3]
CONSOLE_MAC = '00:11:22:33:44:55'


def check_name(name):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,62}', name):
        raise ValueError('Invalid confined image name')
    return name


class ConsoleClient:
    def __init__(self, port, mac=CONSOLE_MAC, serial_port=None):
        if not valid_mac(mac):
            raise ValueError('Invalid console MAC')
        self.mac = mac
        self._rx_buffer = bytearray()
        if serial_port is None:
            self.port = serial.Serial(port=None, baudrate=115200, timeout=0.2, write_timeout=3)
            self.port.dtr = self.port.rts = False
            self.port.port = port
            self.port.open()
        else:
            self.port = serial_port

    def close(self):
        self.port.close()

    def request(self, op, timeout=15, **fields):
        if set(fields) & {'v', 'id', 'target', 'op'}:
            raise ValueError('Reserved request field')
        request_id = uuid.uuid4().hex
        raw = json.dumps(dict(v=1, id=request_id, target=self.mac, op=op, **fields), separators=(',', ':')).encode() + b'\n'
        if len(raw) > 2048:
            raise ValueError('Console frame too large')
        self.port.write(raw)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            # Keep unread bytes across requests: a USB packet can contain a
            # reply, several log lines, and the start of the next line.
            while b'\n' in self._rx_buffer:
                end = self._rx_buffer.index(b'\n') + 1
                if end > 32768:
                    self._rx_buffer.clear()
                    raise ValueError('Oversized console response')
                line = bytes(self._rx_buffer[:end])
                del self._rx_buffer[:end]
                try:
                    reply = json.loads(line)
                except (ValueError, UnicodeError):
                    continue
                if not isinstance(reply, dict) or reply.get('request_id', reply.get('id')) != request_id:
                    continue
                if reply.get('v') != 1 or reply.get('base_mac') != self.mac:
                    raise ValueError('Console identity mismatch')
                if reply.get('ok') is not True:
                    # Device error codes only, never request/credential contents.
                    error = reply.get('error', 'rejected')
                    if not isinstance(error, str) or not re.fullmatch(r'[A-Za-z0-9_ -]{1,80}', error):
                        error = 'rejected'
                    raise ValueError(f'Console rejected operation: {error}')
                return reply
            if len(self._rx_buffer) > 32768:
                self._rx_buffer.clear()
                raise ValueError('Oversized console response')
            # readline() on unbuffered pyserial performs one OS read per byte.
            # Drain available USB data in bounded blocks; wait for one byte only
            # when there is nothing queued, respecting the port's short timeout.
            count = min(4096, max(1, self.port.in_waiting))
            self._rx_buffer.extend(self.port.read(count))
        raise TimeoutError(f'No correlated {op} reply from identified console')

    def identify(self):
        # A USB open may reset the console; only retry read-only identification.
        for attempt in range(3):
            try:
                return self.request('status', timeout=10)
            except TimeoutError:
                if attempt == 2:
                    raise

    def setup(self):
        self.identify()
        wifi = load_wifi()
        self.request('wifi', **wifi)
        del wifi
        registered = []
        with (ROOT/'docs/inventory/nodes.csv').open(newline='') as source:
            rows = list(csv.DictReader(source))
        for row in rows:
            mac = row['factory_base_mac']
            if not mac:
                continue
            self.request('register', label=row['label'], mac=mac, key=management_key(mac).hex())
            registered.append(dict(label=row['label'], mac=mac))
        return dict(registered=registered, wifi_provisioned=True)

    def upload(self, image, expected_sha, name=None, *, progress=None):
        image = Path(image)
        embedded = verify_image(image, expected_sha)
        name = check_name(name or image.name)
        identity = self.identify()
        recoverable = identity.get('upload_status_supported') is True
        boot = identity.get('boot_id')
        total = image.stat().st_size
        def upload_offset():
            for attempt in range(3):
                try:
                    state = self.request('image_status', timeout=3)
                    break
                except TimeoutError:
                    if attempt == 2:
                        raise
            if (state.get('boot_id') != boot or state.get('active') is not True
                    or state.get('name') != name or state.get('size') != total
                    or state.get('sha256') != expected_sha or type(state.get('offset')) is not int):
                raise ValueError('Console upload session changed; refusing to retry writes')
            return state['offset']
        try:
            self.request('image_begin', name=name, size=total, sha256=expected_sha)
        except TimeoutError:
            if not recoverable or upload_offset() != 0:
                raise
        offset = 0
        if progress is not None:
            progress(dict(name=name, offset=offset, total=total))
        with image.open('rb') as source:
            while chunk := source.read(512):
                for attempt in range(3):
                    try:
                        reply = self.request('image_chunk', timeout=3 if recoverable else 15, offset=offset, data=chunk.hex())
                        break
                    except TimeoutError:
                        if not recoverable:
                            raise
                        observed = upload_offset()
                        if observed == offset + len(chunk):
                            reply = dict(offset=observed)
                            break
                        if observed != offset:
                            raise ValueError('Console reported an unexpected upload offset')
                        if attempt == 2:
                            raise
                offset += len(chunk)
                if reply.get('offset') != offset:
                    raise ValueError('Console acknowledged an unexpected image offset')
                if progress is not None:
                    progress(dict(name=name, offset=offset, total=total))
        result = self.request('image_end', timeout=60)
        if result.get('image_sha256') != embedded:
            raise ValueError('Console stored image digest does not match the uploaded image')
        return dict(name=name, bytes=offset, file_sha256=expected_sha, image_sha256=embedded, device=result)

    def select_image(self, name):
        """Select an existing SD image and verify the resulting handheld choice."""
        name = check_name(name)
        before = self.identify()
        boot = before.get('boot_id', '')
        if not isinstance(boot, str) or not re.fullmatch(r'[0-9a-f]{32}', boot):
            raise ValueError('Console cannot identify its boot session')
        selected = self.request('image_select', name=name, timeout=60)
        digest = selected.get('image_sha256', '')
        if selected.get('image') != name or not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError('Console did not confirm the selected image')
        after = self.request('status')
        if after.get('boot_id') != boot:
            raise RuntimeError('Console rebooted while selecting the image; selection is unverified')
        if after.get('image') != name or after.get('image_sha256') != digest:
            raise ValueError('Console selected image readback does not match')
        return dict(selected=True, name=name, image_sha256=digest,
                    file_sha256=selected.get('file_sha256'), console_boot_id=boot)

    def deploy(self, label, name, image_sha256, *, timeout=900, poll_interval=1, progress=None):
        """Wait for a fresh, valid node boot in this console's current boot session.

        A timeout or interruption leaves the controller's operation running; it
        never means that the node was rolled back or that deployment succeeded.
        The serial connection stays open throughout, avoiding a reset between
        the accepted command and its verification.
        """
        if not re.fullmatch(r'[A-D][1-4]', label) or not re.fullmatch(r'[0-9a-f]{64}', image_sha256):
            raise ValueError('Invalid deployment target or digest')
        name = check_name(name)
        if not math.isfinite(timeout) or not 0 < timeout <= 3600:
            raise ValueError('Deployment timeout must be within 0..3600 seconds')
        if not math.isfinite(poll_interval) or not 0.1 <= poll_interval <= 10:
            raise ValueError('Poll interval must be within 0.1..10 seconds')

        def selected(snapshot):
            nodes = snapshot.get('nodes')
            if not isinstance(nodes, list):
                raise ValueError('Console returned no node roster')
            matches = [node for node in nodes if isinstance(node, dict) and node.get('label') == label]
            if len(matches) != 1:
                raise ValueError('Console returned an ambiguous target identity')
            node = matches[0]
            if node.get('registered') is not True or not isinstance(node.get('mac'), str) or not valid_mac(node['mac']):
                raise ValueError('Target has no registered identity')
            if type(node.get('boots')) is not int or not 0 <= node['boots'] <= 0xffffffff:
                raise ValueError('Target boot counter is unavailable')
            return node

        before = self.identify()
        console_boot = before.get('boot_id', '')
        if not isinstance(console_boot, str) or not re.fullmatch(r'[0-9a-f]{32}', console_boot):
            raise ValueError('Console cannot identify its boot session')
        node_before = selected(before)
        mac, previous_boots = node_before['mac'], node_before['boots']
        if before.get('busy') is not False:
            raise ValueError('Console is already busy')
        if (node_before.get('observed') is not True or node_before.get('health') not in ('Healthy', 'Warning')
                or type(node_before.get('age_ms')) is not int or not 0 <= node_before['age_ms'] < 30000
                or node_before.get('receiver_version') != 1):
            raise ValueError('Target does not have fresh receiver-ready health')

        started = time.monotonic()
        deadline = started + timeout
        accepted = self.request('deploy', timeout=min(15, timeout), label=label, name=name, image_sha256=image_sha256)
        request_id = accepted.get('request_id', accepted.get('id'))
        if not isinstance(request_id, str) or not request_id:
            raise ValueError('Deployment acceptance was not correlated')
        last_progress = None
        while time.monotonic() < deadline:
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                break
            try:
                current = self.request('status', timeout=min(15, remaining))
            except TimeoutError:
                continue
            if current.get('boot_id') != console_boot:
                raise RuntimeError('Console rebooted during deployment; completion is unverified')
            node = selected(current)
            if node['mac'] != mac:
                raise RuntimeError('Target identity changed during deployment; completion is unverified')
            stage = current.get('deployment')
            if not isinstance(stage, str) or len(stage) > 80:
                raise ValueError('Invalid deployment progress')
            offset, total = current.get('offset'), current.get('total')
            if type(offset) is not int or type(total) is not int or not 0 <= offset <= total <= 8*1024*1024:
                raise ValueError('Invalid deployment byte accounting')
            update = dict(label=label, mac=mac, stage=stage, offset=offset, total=total)
            if progress is not None and update != last_progress:
                progress(update)
                last_progress = update
            if stage.startswith('Failed:'):
                raise RuntimeError('Controller reported deployment failure: ' + re.sub(r'[^A-Za-z0-9 :/_-]', '?', stage))
            fresh = (node.get('observed') is True and node.get('health') == 'Healthy'
                     and type(node.get('age_ms')) is int and 0 <= node['age_ms'] < 30000)
            verified = (fresh and node.get('deployment_verified') is True
                        and node.get('image_sha256') == image_sha256 and node.get('ota_state') == 2
                        and node.get('receiver_version') == 1 and node['boots'] != previous_boots
                        and current.get('busy') is False and 0 < total == offset)
            if verified:
                return dict(verified=True, label=label, mac=mac, name=name,
                            image_sha256=image_sha256, console_mac=self.mac, console_boot_id=console_boot,
                            deployment_request_id=request_id, before_boots=previous_boots,
                            after_boots=node['boots'], elapsed_seconds=round(time.monotonic()-started, 3),
                            status=current)
            if current.get('busy') is False:
                raise RuntimeError('Deployment ended without a verified fresh boot of the expected image')
            remaining = deadline-time.monotonic()
            if remaining > 0:
                time.sleep(min(poll_interval, remaining))
        raise TimeoutError(f'Deployment to {label} was accepted but not verified within {timeout:g} seconds')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--mac', default=CONSOLE_MAC)
    parser.add_argument('--output', type=Path)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ['status', 'setup']:
        sub.add_parser(command)
    upload = sub.add_parser('image')
    upload.add_argument('--image', type=Path, required=True)
    upload.add_argument('--sha256', required=True)
    upload.add_argument('--name')
    select = sub.add_parser('select')
    select.add_argument('--name', required=True)
    deploy = sub.add_parser('deploy')
    deploy.add_argument('--label', required=True)
    deploy.add_argument('--name', required=True)
    deploy.add_argument('--image-sha256', required=True)
    deploy.add_argument('--timeout', type=float, default=900, help='Seconds to wait for a verified boot (default: 900)')
    args = parser.parse_args()
    client = ConsoleClient(args.port, args.mac)
    try:
        if args.command == 'status':
            result = client.identify()
        elif args.command == 'setup':
            result = client.setup()
        elif args.command == 'select':
            result = client.select_image(args.name)
        elif args.command == 'image':
            last_bucket = -1
            def show_upload(update):
                nonlocal last_bucket
                percent = update['offset'] * 100 // update['total']
                if percent // 5 != last_bucket:
                    last_bucket = percent // 5
                    print(f"{update['name']}: {percent}% ({update['offset']}/{update['total']} bytes)", file=sys.stderr)
            result = client.upload(args.image, args.sha256, args.name, progress=show_upload)
        else:
            def show_progress(update):
                stage = re.sub(r'[^A-Za-z0-9 :/_-]', '?', update['stage'])
                print(f"{update['label']}: {stage} ({update['offset']}/{update['total']} bytes)", file=sys.stderr)
            result = client.deploy(args.label, args.name, args.image_sha256,
                                   timeout=args.timeout, progress=show_progress)
        rendered = json.dumps(result, indent=2)+'\n'
        if args.output:
            with args.output.open('x') as out:
                out.write(rendered)
        print(rendered, end='')
    finally:
        client.close()


if __name__ == '__main__':
    main()
