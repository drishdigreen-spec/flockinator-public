"""Private scripted mission host. Both HTTP clients and the USB prop use one run."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import ctypes
import json
import ipaddress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools/korvo-monitor'))
from bridge import poll, management_key, NetworkClient
from mission_commands import command
from mission_dispatch import dispatch
from mission_projection import STATES
from coordination_lab import experiment
from planner import Planner
from exercise_memory import deliver_one

LABELS = [f'{row}{col}' for row in 'ABCD' for col in range(1, 5)]
DEFAULT = dict(run=0, start_at=None, scenario=0, goal=1, seconds=64, repeat=True,
               request=None, result=None)


class MissionHost:
    def __init__(self, store, library, rows, clients):
        self.store, self.rows, self.clients = store, rows, clients
        self.planner = Planner(store.with_suffix('.planner.json'))
        self.lock = threading.Lock()
        self.wake = threading.Event()
        self.busy = False
        self.health = [None] * 16
        self.prop_seen = 0
        self.lab_ip = None
        self.journal_retry = [0.0]*16
        self.mission = json.loads(store.read_text()) if store.exists() else dict(DEFAULT)
        self.world = ctypes.CDLL(str(library)).mission_node
        self.world.argtypes = [ctypes.c_int] * 3 + [ctypes.c_bool, ctypes.c_int64,
                              ctypes.c_int, ctypes.POINTER(ctypes.c_float)]
        self.world.restype = ctypes.c_int

    def save(self, mission):
        tmp = self.store.with_suffix('.tmp')
        tmp.write_text(json.dumps(mission))
        tmp.replace(self.store)
        self.mission = mission

    def submit(self, value):
        if not isinstance(value, dict) or set(value) != {'previous', 'start', 'scenario', 'goal', 'seconds', 'repeat'}:
            raise ValueError('Invalid mission request')
        start = value['start']
        config = {key: value[key] for key in ('scenario', 'goal', 'seconds', 'repeat')}
        run = secrets.randbits(32) or 1
        command(start, run, **config)  # Same bounds as the physical control.
        with self.lock:
            if self.busy or value['previous'] != self.mission['request']:
                raise RuntimeError('Mission changed or dispatch in progress. Refresh before retrying.')
            req = secrets.token_hex(12)
            self.save(dict(config, run=run if start else self.mission['run'],
                           start_at=time.time()+10 if start else None, request=req, result=None))
            self.busy = True
            self.wake.set()
        return req

    def work(self):
        with ThreadPoolExecutor(max_workers=16) as pool:
            while True:
                with self.lock:
                    pending = self.busy
                    mission = self.mission.copy()
                if pending:
                    try:
                        _, verified = dispatch(mission['start_at'] is not None, mission['scenario'],
                            mission['goal'], mission['seconds'], mission['repeat'], self.rows,
                            self.clients, run=mission['run'], start_at=mission['start_at'])
                        result = [label for label, ok in zip(LABELS, verified) if ok]
                    except Exception as exc:
                        print(f'Dispatch failed: {type(exc).__name__}', file=sys.stderr, flush=True)
                        result = []
                    with self.lock:
                        self.save(dict(mission, result=result))
                        self.busy = False
                        self.wake.clear()
                try:
                    self.planner.checkpoint()
                    closed={p.stem:p.read_text().split(',') for p in sorted(self.planner.archive_dir.glob('*.closed'))}
                except OSError as exc:
                    print(f'Journal checkpoint failed: {exc}',file=sys.stderr,flush=True)
                    closed={}
                def read(index):
                    frame = poll(index, self.rows[index], self.clients[index])
                    health=frame.splitlines()[0].decode()
                    with self.lock:
                        self.health[index] = (time.monotonic(), health)
                    if health.split()[2:4]==['1','0.10.2-journal'] and time.monotonic()>=self.journal_retry[index]:
                        try:
                            unit=LABELS[index]
                            for run,members in closed.items():
                                if unit not in members:
                                    continue
                                if (self.planner.archive_dir/run/(unit+'.receipt')).exists():
                                    continue
                                if deliver_one(self.planner.archive_dir,run,unit,self.clients[index]):
                                    break
                            self.journal_retry[index]=time.monotonic()+5
                        except Exception as exc:
                            self.journal_retry[index]=time.monotonic()+30
                            print(f'{LABELS[index]} journal delivery: {type(exc).__name__}',file=sys.stderr,flush=True)
                list(pool.map(read, range(16)))
                self.wake.wait(2)

    def snapshot(self):
        with self.lock:
            m = self.mission.copy()
            busy, prop_seen, health = self.busy, self.prop_seen, self.health.copy()
            lab_ip=self.lab_ip
        now = time.monotonic()
        elapsed = int((time.time()-m['start_at'])*1000) if m['start_at'] is not None else -1
        limit = 86400000 if m['repeat'] else (32+m['seconds']+31)*1000
        status = ('Idle' if m['start_at'] is None else 'Starting' if elapsed < 0
                  else 'Running' if elapsed < limit else 'Finished')
        nodes = []
        for i, label in enumerate(LABELS):
            pose = (ctypes.c_float * 4)()
            # Firmware indexes across rows (A1,B1,...). USB uses A1,A2,...
            state = self.world(m['scenario'], m['goal'], m['seconds'], m['repeat'],
                               elapsed, (i % 4)*4+i//4, pose)
            h = health[i]
            nodes.append(dict(label=label, state=STATES[state], code=state, pose=list(pose),
                              health=h[1] if h and now-h[0]<15 else None))
        return dict(mission=m, status=status, elapsed=max(0,elapsed), nodes=nodes,
                    busy=busy, prop=bool(prop_seen and now-prop_seen<12),
                    controller_lab=lab_ip if now-prop_seen<12 else None)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, body, mime='application/json'):
        if mime == 'application/json':
            body = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        port = self.server.server_port
        host = self.headers.get('Host')
        return (host in (f'localhost:{port}', f'127.0.0.1:{port}')
                and self.headers.get('Origin') in (None, 'http://'+host)
                and self.headers.get('Sec-Fetch-Site') != 'cross-site')

    def do_GET(self):
        if not self.authorized():
            return self.reply(403, {'error':'Local origin required'})
        if self.path == '/api/state':
            return self.reply(200, self.server.game.snapshot())
        if self.path == '/api/planner':
            return self.reply(200, self.server.game.planner.snapshot())
        if self.path == '/api/planner/journals':
            return self.reply(200,self.server.game.planner.journals())
        if self.path.startswith('/api/planner/journals/') and self.path.endswith('.zip'):
            try:
                data=self.server.game.planner.download(self.path.rsplit('/',1)[-1][:-4])
            except FileNotFoundError:
                return self.reply(404,{'error':'Unknown exercise'})
            return self.reply(200,data,'application/zip')
        assets = {'/lab': ('lab.html','text/html'), '/lab.js': ('lab.js','text/javascript'),
                  '/lab.css': ('lab.css','text/css'), '/planner': ('planner.html','text/html'), '/planner.js': ('planner.js','text/javascript'),
                  '/planner.css': ('planner.css','text/css'), '/': ('index.html','text/html'), '/app.js': ('app.js','text/javascript'),
                  '/style.css': ('style.css','text/css')}
        if self.path not in assets:
            return self.reply(404, {'error':'Unknown path'})
        name, mime = assets[self.path]
        self.reply(200, (HERE/name).read_bytes(), mime)

    def do_POST(self):
        if not self.authorized():
            return self.reply(403, {'error':'Local origin required'})
        if self.path not in ('/api/mission','/api/prop','/api/planner','/api/lab'):
            return self.reply(404, {'error':'Unknown path'})
        if self.headers.get('Content-Type') != 'application/json':
            return self.reply(415, {'error':'JSON required'})
        try:
            size = int(self.headers.get('Content-Length', '-1'))
            if not 0 < size <= 1024:
                return self.reply(413, {'error':'Invalid request size'})
            body = json.loads(self.rfile.read(size))
            if self.path == '/api/lab':
                planner=self.server.game.planner
                with planner.lock:
                    plan=planner.plan  # Edits replace the plan atomically.
                return self.reply(200,experiment(body,plan))
            if self.path == '/api/planner':
                return self.reply(200, self.server.game.planner.submit(body))
            if self.path == '/api/prop':
                if not isinstance(body,dict) or set(body)-{'lab_ip'}:
                    raise ValueError('Invalid heartbeat')
                ip=ipaddress.IPv4Address(body['lab_ip']) if 'lab_ip' in body else None
                if ip and (not ip.is_private or ip.is_loopback or ip.is_unspecified or ip.is_link_local):
                    raise ValueError('Invalid controller address')
                with self.server.game.lock:
                    self.server.game.lab_ip=str(ip) if ip else None
                    self.server.game.prop_seen = time.monotonic()
                return self.reply(200, self.server.game.snapshot())
            req = self.server.game.submit(body)
        except (ValueError, TypeError) as exc:
            return self.reply(400, {'error':str(exc)})
        except RuntimeError as exc:
            return self.reply(409, {'error':str(exc)})
        self.reply(202, {'request':req})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--library', type=Path, required=True)
    p.add_argument('--data', type=Path, default=Path.home()/'.local/share/flockinator/mission.json')
    p.add_argument('--port', type=int, default=8782)
    args = p.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    with (ROOT/'docs/inventory/network.csv').open() as f:
        addresses = {r['label']:r['ipv4'] for r in csv.DictReader(f) if r['role']=='node'}
    with (ROOT/'docs/inventory/nodes.csv').open() as f:
        roster = {r['label']:r for r in csv.DictReader(f)}
    rows = [roster[label] for label in LABELS]
    clients = []
    for r in rows:
        try:
            mac = r['factory_base_mac']
            clients.append(NetworkClient(addresses[r['label']], mac, management_key(mac)))
        except (ValueError, KeyError):
            clients.append(None)
    args.data.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    server.game = MissionHost(args.data, args.library.resolve(), rows, clients)
    threading.Thread(target=server.game.work, daemon=True).start()
    server.serve_forever()


if __name__ == '__main__':
    main()
