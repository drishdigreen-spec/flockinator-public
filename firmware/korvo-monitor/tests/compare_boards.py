"""Compare the native board_model_parity executable with the desktop reference."""
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools/mission-host'))
import planner

output = subprocess.check_output([sys.argv[1]], text=True).splitlines()
assert len(output) == 100
for seed, line in enumerate(output):
    actual = json.loads(line)
    plan = planner.random_scenario(seed)
    assert actual['plan'] == plan, f'Scenario mismatch for seed {seed}'
    expected = json.loads(json.dumps(planner.simulate(plan, 46)))
    assert actual['sim'] == expected, f'Simulation mismatch for seed {seed}'
print('100 scenarios and complete simulations match the desktop reference.')
