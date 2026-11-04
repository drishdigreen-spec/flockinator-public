"""One authenticated command per node, followed by independent readback."""
import concurrent.futures
import json
import secrets
import time
from mission_commands import command
from node_commissioner.protocol import validate_status

def dispatch(start, scenario, goal, seconds, repeat, rows, clients, *, run=None, start_at=None):
    run=run or secrets.randbits(32) or 1
    def one(i):
        client=clients[i]
        if client is None: return False
        try:
            before=client.request('GET','/v1/status',timeout=3)
            validate_status(before,rows[i]['factory_base_mac'],rows[i]['label'])
            mission=before.get('mission',{})
            if mission.get('source')!='scripted_simulation': return False
            node_run=run if start else mission.get('run')
            if type(node_run) is not int: return False
            delay = 3000 if start else 0
            if start and start_at is not None:
                delay = round((start_at - time.time()) * 1000)
                if delay < 0:
                    return False  # Too late to join this common start.
            body=command(start,node_run,scenario=scenario,goal=goal,seconds=seconds,repeat=repeat,delay_ms=delay)
            reply=client.request('POST','/v1/control',body,timeout=5)
            if reply.get('ok') is not True: return False
            deadline=time.monotonic()+8
            while time.monotonic()<deadline:
                after=client.request('GET','/v1/status',timeout=3)
                validate_status(after,rows[i]['factory_base_mac'],rows[i]['label'])
                state=after.get('mission',{})
                matches=state.get('run')==node_run
                if matches and (bool(state.get('running') or state.get('waiting')) if start else not state.get('running') and not state.get('waiting')):
                    return True
                time.sleep(.3)
            return False
        except Exception:
            return False
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        results=list(pool.map(one,range(16)))
    return run,results
