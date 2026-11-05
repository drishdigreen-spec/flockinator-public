# Flagship result: communication helps, corruption hurts more than silence

The clearest causal result currently in the public repository,
reproduced by Kulira from the existing host experiment
(`tools/mission-host/coordination_lab.py`, `field-signals-v1`)
on public main, 2026-11-05. Evidence:
`validation/kulira/flagship-communication-001.json` (per-seed).

## Result (seeds 0-15, held-out rounds)

Team success = at least 3 of 4 agents in a team choose the
correct sector; 4 teams x 32 held-out rounds per seed
(128 team tasks per seed per condition, 2,048 per condition -
team tasks within a seed are not independent experiments).

| Condition (train Clear throughout) | Team-task success |
|---|---|
| Clear peer messages | **72.9%** |
| Private cues only (muted, no peer messages) | **56.6%** |
| Scrambled peer messages | **33.6%** |

## What this does and does not show

- Informative peer messages improve this task over private cues
  alone (+16.3 points, mean of seed rates). This is the closest
  existing measurement to the paired-gain question, with one
  registered caveat: the muted baseline receives *no* peer
  messages by design, so its information budget differs - the
  comparison isolates message value, not communication at
  matched information.
- Corrupted messages are worse than silence (-23.0 points vs
  private cues): a swarm that listens to a liar underperforms a
  swarm that cannot listen at all. That asymmetry is the
  empirical motivation for the Kulira trust series.
- Host simulation only. Nothing here is on-node learning,
  physical-swarm advantage, or rescue capability.

## Reproduce

```sh
uv run --project tools/mission-host python -c "
import sys; sys.path.insert(0,'tools/mission-host')
from coordination_lab import learning_comparison
for seed in range(16):
    r=learning_comparison(seed,'Scrambled')
    print(seed, [(x['train'],x['test'],round(x['recoveries']/x['tasks'],4)) for x in r['rows']], round(r['solo']['recoveries']/r['solo']['tasks'],4))
"
```

Training and held-out streams are separate; evaluation memories
are frozen. Per-seed paired differences are in the evidence JSON;
pooled percentages alone hide seed variance and should not be
quoted without it.
