# Flockinator mission control

Open <http://127.0.0.1:8782/> on Vivek or Drishdi. Vivek owns the scripted
world and stores the selected run, its start time and dispatch result in
`~/.local/share/flockinator/mission.json`. Drishdi reaches the same
service through a loopback SSH forward. A browser can join mid-mission.
The world keeps time when all browsers close or the Korvo is unplugged.

Pick a scenario, goal, flight segment and repeat setting. **Start mission**
starts a new run with a ten-second lead for the physical panels. **Stop fleet**
ends the host run and asks each reachable panel to stop its current mission.
The result lists how many panels verified the command. An offline panel can
miss a command. A new Start synchronizes the reachable fleet again.

The map and phase labels use the firmware's scripted timeline and camera
geometry. Panel health is independently polled over authenticated HTTP.
The Korvo's mission map now receives this host world through its existing USB
protocol. Its firmware still labels positions as node-reported. Its start/stop
buttons submit to the same controller as the browser. Physical touch and
speaker output require inspection at the device.

Mixed outcomes with a 64-second flight segment repeats every 127 seconds.
The panel firmware limits each run to 24 hours, including repeating runs.
Start a new run for the next day's demo.

## Operations

Three per-user macOS LaunchAgents resume the setup after login. On Vivek,
`internal.flockinator.mission-host` runs a local copy of the Python host and
compiled world library in `~/.local/share/flockinator/mission-host/`.
`internal.flockinator.drishdi-prop` forwards Drishdi's loopback port 8782
to Vivek over SSH. Their logs are in `~/Library/Logs/Flockinator/`.
On Drishdi, `internal.flockinator.usb-prop` runs the USB client from
`~/.local/share/flockinator/prop/`, with logs alongside it. The client finds
the Korvo's USB serial number and checks the factory MAC before transmitting.
It reconnects after USB or network loss. Fleet credentials stay on Vivek.

To run from the repository on a controller with its provisioned roster, stop
the installed host first and run the following from the repository root.

```sh
c++ -std=c++17 -O2 -fPIC -shared tools/mission-host/world.cpp -o /tmp/flock-world.so
uv run --project tools/node-commissioner python tools/mission-host/host.py --library /tmp/flock-world.so
```

On a separate USB host with loopback port 8782 forwarded to the controller,
run `uv run --with pyserial python prop.py` using the prop script from this
directory. An explicit `--port` overrides USB adapter discovery. Only one
USB bridge can own the prop at a time.

Run isolated host tests with
`uv run --project tools/node-commissioner python -m unittest discover -s tools/mission-host`.

## Mission planner

Open **Open mission planner** from mission control or visit
<http://127.0.0.1:8782/planner>. Set the search focus, place friendly and
enemy contacts, and choose a tree-line fan or search grid. To plot a custom
route, select a unit and add waypoint tiles in order. The keyboard controls
and numeric tile inputs offer the same placement actions as the map.

A rehearsal advances one board turn per second. One move costs one energy
point, including a diagonal. Units reserve the cost of a direct trip home
plus three landing points. Each searching unit sees its tile and the four
adjacent tiles and gets one independent draw per contact. Foliage changes
both the sighting odds and the chance of assigning the correct label.
A high-priority single report can request a second observer within its
return budget. Contact outcomes are recorded by the director. The controls
use fictional tiles, points and exercise odds.

Plans, exercise draws and rehearsal clocks are saved beside the live mission
as `mission.planner.json`. Two operators see the same rehearsal. Revising a
stale copy prompts a refresh. Planned routes run on the web board. The
physical panels and Korvo follow the live scripted mission.

### Random boards and exercise journals

**Generate scenario** draws zero to 24 contacts, terrain cover, pattern, focus,
pack size and fleet size. Enter the same scenario seed to regenerate that
board. **Use a new draw** rerolls the sightings on the current board. Beyond
return range means a direct round trip to the contact tile would consume the
three-point landing reserve. An adjacent tile can still offer a sighting.

Rehearsals started with the journal-enabled host appear under **Exercise
memory**. Each ZIP contains a JSONL event stream per participating unit and
a separate director manifest with scenario truth. Compare rule versions,
seeds, routes, independent reports, simulated message IDs, reserve decisions
and no-sighting scans. UTC event times follow the exercise clock across
pauses. The rules remain fixed within a run. No model training takes place.

The host checkpoints active exercises and preserves completed and interrupted
runs in `~/.local/share/flockinator/mission.planner-journals/`. Physical SD
delivery uses the **0.10.2-journal** node firmware. The host retries closed
exercises for reachable, compatible panels. Each card holds its unit's JSONL
under `/JOURNALS/<sha256>.jsonl`. The dashboard lists a unit as verified only
after authenticated retrieval and byte comparison. The receipt identifies the
panel, run, digest and byte length. To retrieve a card file again, run
`uv run --project tools/node-commissioner python tools/mission-host/read_card.py RECEIPT NEW_OUTPUT.jsonl`
from the repository root. The JSONL records describe the host-run exercise.
Message events represent the simulated relay, and decision records describe
the rule and observed inputs.

## Demonstrating communication and learning

**Open Korvo lab** on the mission-control home page goes directly to the
ESP32-S31 when its USB heartbeat supplies a current Wi-Fi address. Drishdi
uses its browser as the large display. The controller screen also shows the
address for independent use. See [Korvo 0.8.0](../../firmware/korvo-monitor/README.md).

Open the [host reference lab](http://127.0.0.1:8782/lab) on either Mac.
The lab uses host-side experimental traffic and has no panel control endpoint.
A seed reproduces the private clues, team tasks and intervention draws.
Download the evidence to retain the search inputs, scores for every test
round, per-unit paired decisions, and the communication and learning settings.

Start with seed 11 and **Scrambled**. The same trained listeners receive the
same number of packets, but different payloads. Inspect A1 on turn one to
see which peer symbols changed its choice. Next compare the two rows tested
on a clear link. That comparison holds the test channel fixed and changes
what was available during training. Try **Muted** to establish the local-only
baseline and **Half lost** to change packet availability.

The sample recovery task and the planner replay answer different questions.
The former tests learned decoding of assigned vocabularies in four teams of
four. The latter tests the contribution of the planner's existing verification
relay under fixed rules. The lab does not implement emergent language or
on-device learning. See the [experiment review](../../docs/design/communication-learning-demo.md).
