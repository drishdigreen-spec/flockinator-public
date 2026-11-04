"""Build bounded mission requests for the existing node control API."""
import json

def command(start, run, *, seed=271828, seconds=64, scenario=0, goal=0, repeat=True, delay_ms=0):
    if type(start) is not bool or type(repeat) is not bool:
        raise ValueError('invalid mission flags')
    for value, limit in ((run, 0xffffffff), (seed, 0xffffffff), (scenario, 2), (goal, 2), (delay_ms, 60000)):
        if type(value) is not int or not 0 <= value <= limit:
            raise ValueError('invalid mission parameter')
    if type(seconds) is not int or seconds not in (64, 96):
        raise ValueError('invalid mission duration')
    return json.dumps({'op':'mission_start' if start else 'mission_stop', 'run':run,
                       'seed':seed, 'seconds':seconds, 'scenario':scenario,
                       'goal':goal, 'repeat':repeat, 'delay_ms':delay_ms}, separators=(',', ':')).encode()
