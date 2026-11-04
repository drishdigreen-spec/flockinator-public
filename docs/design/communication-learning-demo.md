# What the communication demo can show

The [embodied platform design](embodied-experiment-platform.md) gives each
node its own observations, memory and actions and distinguishes experimental
messages from management traffic. The [campaign specification](../../SPEC-experiments.md)
adds mission outcomes such as coverage and safe return. The [audio experiment](../../SPEC-audio-flocking.md)
already proposes a valuable control: participants following a common clock can
look coordinated without having heard one another.

The deployed panel loop demonstrates a synchronized presentation. The SD
system establishes that a particular physical panel stored and returned its
unit's rehearsal records. Neither observation measures the contribution of
a message to a decision. The [communication lab](http://127.0.0.1:8782/lab)
adds two controlled comparisons.

| Question | What changes | What to inspect |
|---|---|---|
| Did a check request help the search? | Deliver or withhold the simulated request | Independently corroborated contacts against director truth, energy, coverage and safe returns |
| Does meaning matter when packet volume stays fixed? | Keep the senders and timing, replace each payload with a random symbol | The recipient's private clue, decoded symbols, choice and subsequent reward |
| Did peer experience change what the agent learned? | Expose listeners to clear or impaired messages during training, then restore the same clear test link | Correct sender–symbol mappings and team recoveries on fresh rounds without feedback |

A training round reveals the true sector after the observations. Each listener
keeps separate counts for each sender and token. Each team gets a shared
recovery when at least three of four agents choose correctly. This is
supervised receiver learning with assigned sender vocabularies. Comparing
against private cues alone establishes whether the cooperating agents benefit
on this task. It does not establish self-invented language or a general
advantage to cooperation.

### Reproducible demonstration

Seed 11 was selected to show a search decision that matters. Two check requests
raise correct corroborations from one to three at a cost of eight game energy
points. Seed 90 illustrates a null result: its single request does not change
coverage, energy or correct corroborations. Both examples keep all units safe.

In the separate learning exercise, seed 11 produces 101/128 team recoveries
with clear training and testing, 42/128 after scrambling only the test
payloads, and 42/128 with scrambled training followed by a clear test.
Private clues alone yield 73/128. These are simulation outcomes. Across
seeds 0–15, clear-trained teams recovered 1,494/2,048 samples with clear
payloads and 688/2,048 with scrambled payloads. Treat the seed as the
replication unit: agents on the same team share clues and outcomes.

### Next physical trial

Use four panels for one sample-recovery team. Give each node its private cue,
display its choice, and keep the director answer off the behavior channel until
feedback. Timestamp sends, receipts, local model updates and decisions on each
SD card. Drop selected application messages at the receiver while preserving
health and recovery traffic. Replay the same cue sequences in randomized
condition order. Retain or reset per-node learning tables explicitly between
runs. Grade on held-out rounds with learning frozen. A discrepancy between the
hardware result and the host baseline is evidence to inspect for queue loss,
timing, or unintended shared information.
