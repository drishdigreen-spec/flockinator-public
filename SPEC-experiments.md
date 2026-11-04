# Experiments specification: persistent swarm campaign

Status: **draft for owner review**, revised 16 October 2026 for a host-coordinated persistent world with a LilyGo command interface and portable engine.
Module: `experiments`, using the existing module boundaries in
[reconnaissance-swarm-experiment.md](docs/design/reconnaissance-swarm-experiment.md).
This specifies one integrated campaign/game loop and its existing firmware/UI
adapters. It does not approve a separate autonomous agent-runtime implementation.

## Objective

Turn the looping HUD presentation into a persistent, playable resource-management
simulation. The player uses the LilyGo Flockinator remote as the commander interface to
choose one or more available nodes for individual missions while maintaining
reserves for new requests. The player does not steer an aircraft or operate its
camera frame by frame. Each physical
panel continues to represent one independent simulated aircraft.

Success means choices have lasting consequences: incomplete charge limits a
sortie; travel consumes energy; an unsuccessful search can end in a useful safe
return; recovered nodes recharge; losses reduce the available pool. Several
missions may coexist using disjoint sets of nodes. Resetting an animation,
reconnecting the controller or issuing a new mission must not refill batteries,
revive losses or cancel other missions.

The world uses fictional sectors, abstract travel costs and synthetic events.
Difficulty settings are game parameters, not calibrated aircraft, weapon,
real-world sensor or mission-planning models. The first version needs no GPU or
external inference service.

The same fictional campaign should be playable through a browser without owning
the physical flock, and usable as an interactive companion to the research paper.
Browser play adds a commander interface, sixteen virtual panel views and a debrief;
the physical display remains an optional presentation/experiment adapter.

## Assumptions proposed for approval

- The Mac initially hosts the authoritative campaign coordinator. LilyGo is the
  player's command surface; its sleep, refresh or reconnection does not pause
  the running backend. Pause is an explicit acknowledged command. This supersedes
  the earlier LilyGo-authority and Pause-before-Sleep proposal.
- A Raspberry Pi is the intended self-contained Linux deployment option. A future
  ESP32 controller can first provide hardware/network access, with hosting the
  portable game core optional after profiling. Neither a GPU nor an inference
  service is required to run this fictional game or manage the flock.
- Each node has a scenario-defined launch/home position, independent of its
  physical position in the panel grid. The requested fictional layout places
  sixteen launch positions along a line, 500 m apart: 7.5 km between endpoints.
  The label-to-position mapping is explicit in the scenario. RTB means that
  node's own home; the 4×4 hardware layout is not the world map.
- All 16 nodes begin a new campaign available and fully charged unless a saved
  scenario explicitly specifies otherwise. There are no automatically chosen
  reserve nodes; reserves arise from the player's selections.
- Model individual fitted and spare battery packs. Pack count and swap allowance
  are separate scenario settings. Two/three-pack presets are available; three
  swaps without waiting for a pack to recharge require four initially charged
  packs including the fitted one. Returning never creates an unlimited new pack.
- Partially charged nodes can be dispatched when eligible. Selecting or
  inspecting one does not interrupt charging; accepting a launch does. Charging
  a removed spare can continue while its associated node flies another sortie.
- Player-selected automatic swap on RTB uses an available pack and takes service
  time. Otherwise the fitted pack recharges. When no replacement is available,
  the node waits for charging; a landing is not an instant energy refill.
- Automatic RTB remains the default. The player may explicitly override it for
  an active assignment, accepting possible loss from simulated depletion. That
  override does not carry forward to another mission or affect management.
- LOST combines simulated KIA, MIA and airborne battery-depletion losses on the
  campaign interface. Preserve the underlying cause in details and the event log.
  KIA/depletion losses persist; MIA can be resolved only by an explicit scenario
  event. A management reconnection alone cannot resolve or create a game loss.
  A flat battery on a node safely at home is a charging condition, not LOST.
- The existing repeating demonstration remains a separately selected mode.
  Campaign mode does not automatically start a fresh sortie after an ending.
- Ordinary objective completion can be followed by RTB. The existing KILL
  countdown/blackout is an expendable-sortie ending, not the universal outcome
  whenever an objective is completed.

## Player loop

1. Orders arrive on the LilyGo with a fictional grid location, expiry, known
   leads and permitted objective. Show scenario distance from each node's
   distributed home/current sector, plus availability and charge. The player
   chooses the participants; the software does not select an optimal combat force.
   Separate confirmed facts from uncertain reports.
2. The player selects a subset of nodes. Show each node's simulation charge,
   home sector, current assignment and an understandable readiness indication.
   Show a coarse travel-cost band and expected opportunity to search, not a
   recommendation for real-world force allocation or flight routing.
3. Launch sends an explicit assignment to those nodes. Acknowledged acceptance
   and subsequently observed execution are separate UI facts. Never silently
   substitute another node if one rejects the command.
4. Nodes progress through takeoff, travel and search. A seeded statistical game
   model generates discovery and classification events using participating nodes,
   fictional proximity and accumulated observation time. Additional independent
   observations can help, with diminishing benefit; forwarded copies cannot.
   The player can add eligible reinforcements to the same mission or cancel it.
   Existing participants retain their charge, observations and progress.
5. A node returns by default when its game energy budget requires it, the player
   recalls/aborts it, or the assignment is finished. No finding is a valid result.
   Return and landing consume energy. An explicit in-flight player override can
   continue the search despite the warning; the simulation can then lose the node.
6. Landing starts the selected ground-service policy: swap an available pack after
   its service delay, or recharge the fitted pack. Removed packs enter the local
   recharge queue and remain identifiable. The node can become eligible again
   before reaching full charge. New requests may arrive during service/charging.
7. Crash, fictional hostile-event loss or exhaustion can remove a node from
   availability. A last-known sector is retained as a dated, uncertain lead;
   loss does not prove that a particular contact caused it or confirm a target.
8. The campaign continues until the player ends/resets it or cannot service more
   requests. If only charging nodes remain, wait for recovery rather than
   incorrectly declaring the campaign over. Pending missions may still expire.

## State semantics

Campaign mode has exactly three primary labels. This supersedes the earlier
five-label proposal for campaign mode; the deployed demonstration remains unchanged
until a separately verified campaign rollout.

| Overview | Campaign meaning | Eligible for MISSION GO? |
|---|---|---|
| READY | At home, unassigned; charge and service readiness are separate fields | Only with sufficient fitted charge, completed service and fresh hardware reports |
| OM | Accepted active assignment, including approval, takeoff, search, return or landing | No new concurrent assignment; mission recall/abort remains available |
| LOST | Simulated KIA, unresolved MIA or aircraft lost through airborne depletion | No; visibly crossed out and excluded from selection |

READY means not currently assigned, not necessarily fully charged or immediately
launchable. A READY card can therefore show a recharge countdown and remain
unselectable until eligible. A flat pack on a safely landed node does not destroy
that node. Charging/swapping is a secondary condition, not a fourth primary label.

Hardware connectivity remains independent. Stale telemetry displays `--` with a
link warning and disables dispatch. It cannot invent LOST or imply current READY.
These are simulation batteries, not measured ESP32 power or the remote battery.
Show actual hardware health with its own icon/text and retain measured diagnostics.

Mission outcome is a separate record: completed, no finding, inconclusive,
recalled, expired or failed. A completed mission does not imply KIA; a surviving
node can return. A mistaken friendly/hostile classification is a distinct game
error recorded against the evidence available at that time, not silently changed
into a correct decision in the replay.

Keep existing detailed HUD states and motion variants for presentation. Battery,
assignment and campaign events drive transitions; a timeline no longer picks a
random predetermined ending. Visual loops can repeat without consuming or
reversing state transitions. Terminal animations are followed by persistent
campaign status, not revival after the five-second blank screen.

## Energy, observations and outcomes

- Use a bounded simulation charge value. Travel, search and return consume it;
  charging replenishes a particular pack. A pack at home can recharge while its
  associated aircraft is away. Swap transfers the identity and existing charge
  of another pack; it does not create energy. Scenario pacing is adjustable,
  including normal elapsed-time play and accelerated demonstration play.
- Show the player the game budget before launch. Reject a launch that cannot
  meet the configured game return allowance. The newly requested in-flight
  override is a separate deliberate player action, never a silent launch bypass.
- Default automatic recall uses the remaining return allowance. Uncertainty and
  scripted disruptions may still cause failure; the UI must not promise that a
  predicted return is guaranteed. A player override suspends automatic recall
  for the selected assignment only; subsequent manual RTB remains available but
  cannot restore spent energy or promise arrival. Detailed balancing values remain to be tuned
  in a preview, not presented as physical aircraft performance.
- A longer search can reveal more synthetic observations while spending energy.
  Increasing participation must not guarantee discovery or correct classification.
- Track observation origin, mission, sector, time, uncertainty and expiry.
  Distinguish local observations, relayed claims and simulator ground truth.
  Friendly blue and hostile red markings remain the established visual language;
  unverified contacts must remain distinguishable from confirmed classifications.
- Use seeded fictional event draws and a recorded event order. Preserve results
  when replaying or reconnecting; do not reroll losses to obtain a preferred result.
- For this increment, cooperation and adversarial evidence are synthetic game
  events generated statistically rather than a fixed ending selected at launch.
  Real distributed inference and autonomous evidence evaluation belong to the
  later `agent-runtime` work. Report the decision source as statistical/rules,
  scripted or inference-backed; do not relabel a random draw as inference.

## Distance display and distributed launch positions

In campaign HUD mode, replace the current `SIM` corner text with a `D` plus two-character
**distance from this node's launch position**, in whole kilometres. It is current
straight-line separation in the fictional world, not accumulated distance flown,
distance to the mission objective, or distance from a shared fleet headquarters.

- At launch/home: `D00`.
- At 14 km fictional separation: `D14`. This is a formatting example, not a
  validated operating range for a quadcopter.
- Display completed whole kilometres: 0–999 m is `D00`, 1,000–1,999 m is `D01`.
  Keep metre precision in the model; do not round the energy/world state to match
  the two-digit readout. A loitering aircraft need not constantly gain distance.
- Unknown position: `D--`. Values outside the two-digit domain: `D++`, with the
  actual scenario value available on the remote; never wrap to `D00` or silently
  clamp a larger distance to `D99`.
- On return the readout follows separation from that node's home, reaching `D00`
  on arrival. Mission reassignment and reinforcement do not redefine home.
- Keep the digits inside the TX/RX border and clear of node identity, sensor mode,
  compass and status. Terminal blackout/static can hide them according to the
  existing animation rules; do not display a changing distance on a frozen feed.

The remote card continues to show **distance to the selected mission**, explicitly
labelled separately from the HUD's **HOME km** interpretation. Node details can
show both with finer precision and a scenario-estimated return time. Displaying
rounded kilometres alone is not sufficient to establish a return-time estimate.
Use only fictional game positions/timing; no measured aircraft telemetry is implied.

Keep a persistent `CAMPAIGN SIMULATION` label on the remote and browser/presenter
view, plus a `HUD distance: km from own launch` legend. The user's removal of the
per-panel SIM text does not change the provenance of the generated imagery/data.
This is a pending campaign presentation change, not a claim that the running
0.8.1 demonstration already has position telemetry.

Orders may originate anywhere along the fictional line of launch positions. The
scenario author controls the playable world and abstract travel/endurance presets;
mission eligibility uses those game settings. Do not derive a realistic flight
radius from “quadcopter” or “6S,” and do not publish calibrated battlefield range,
return-reserve or target-search endurance calculations as part of this game.

A scenario can offer a deliberately expendable/one-way game option, with its cost
shown before selection. It may grant an authored additional-search allowance and
consume the assigned node if the expendable ending completes. This neither
confirms discovery nor guarantees correct classification. More independent
observers can improve aggregate game outcomes; uncertainty and chance remain.

**One-way does not inherently mean twice the loiter time.** Do not bake a universal
2× multiplier into an alleged physical model. If the owner chooses a double-loiter
arcade preset, label that as an explicit balancing rule. Keep it separate from the
existing in-flight battery-warning override. Manual abort/RTB remains available
before an irreversible ending, subject to the remaining fictional energy; an
accepted return request is not a guarantee of recovery.

## Statistical game contract

Keep discovery, classification and mission outcome as separate random processes
with visible uncertainty. Finding a contact is not automatically identifying it
correctly, and an identification is not automatically a completed mission.

The configurable game inputs are:

- Number of active observers participating in this mission and fictional sector.
  Nodes flying an unrelated assignment do not grant a global discovery bonus.
- Proximity bands in the fictional world. Aircraft still travelling do not count
  as already observing the requested sector.
- Accumulated valid observation time. Dead, returning, disconnected-in-scenario
  or otherwise non-observing participants stop adding new observations.
- Authored scene difficulty, synthetic camera-mode cues and independent evidence.
  Shared occlusion, ambiguous contacts and common-mode errors can correlate reports.

The qualitative rule is diminishing benefit from additional useful observers,
better fictional proximity and longer observation. Neither more nodes nor more
time guarantees a finding or correct classification. Difficulty, correlation,
false-positive and false-negative rates are tunable game parameters. No numerical
real-world detection curves, force-allocation solver, target-recognition system
or autonomous weapon-engagement policy is part of this contract.

Accumulate observation opportunities by simulation time, independent of animation
FPS, radio polling or screen refresh. A repeatable seed plus stable event identities
must reproduce a campaign; taps, reconnects and duplicate messages cannot reroll
its outcomes. Reinforcements add future opportunities after arriving, not retroactive
credit. Expired observations remain historical evidence rather than fresh certainty.

The desired later agent presentation is autonomous camera changes, observation,
classification, scenario-permitted action and return. In this increment these are
non-actuating game events feeding the existing HUD. The ROE/scenario identifier
travels with the mission record and is visible to the player; it is a fictional
scenario constraint, not a specification for implementing real engagement logic.

A suspected friendly misidentification raises a **BLUE ON BLUE** warning identifying
the affected mission and reporting node(s). A warning is not confirmation that an
incident has occurred. A confirmed game incident is a separate event. The player
can cancel/recall the affected mission or send more available observers to resolve
uncertainty. The warning neither silently launches reinforcements nor alters
unrelated missions. Keep it in the event history after acknowledgement.

Validate statistical behaviour with ensembles of fixed seeds as well as single-run
replays: controlled comparisons should demonstrate the intended aggregate trends,
while individual runs can still fail. Check probability bounds, classification
error counts and uncertainty labels. Balance tests use fictional scenario presets,
not claims of battlefield prediction accuracy.

## Identification uncertainty and presentation

Contact appearance: each fictional person occupies one native 64×64 source pixel,
with separated small clusters representing groups on the ground surface. Unknown
contacts use contrasting black/white appropriate to the sensor palette; explicit
classification state supplies blue/red. Selection brackets remain separate from
the person pixels. Colour conveys the agent's current reported assessment, not
hidden world truth; camera-mode changes alone cannot classify a contact. The
browser demonstration implements this visual convention with scripted states;
probabilistic or collaborative classification remains pending campaign work.

The installed 0.8.1 HUD is procedural pixel rendering driven by scripted timelines
(`firmware/node-platform/src/display.cpp` and `include/recon_render.h`), not a
prerecorded video player. It nevertheless has no live campaign world. The new
campaign must separate world events from presentation regardless of whether a
future theme uses procedural sequences or SD-backed clips.

An animation adapter consumes state, elapsed phase, variant and current overlays.
It can loop ordinary flight/search while awaiting events, then transition on an
accepted campaign event or commander instruction. Completing a clip must not
independently confirm a contact, consume a node or complete a mission. Visual
position, charge and confidence come from the current campaign snapshot, not
baked-in video captions. Takeoff/landing/terminal sequences retain forward-only
playback; a camera-view change alone is not a new independent observation.

Represent three different things in the game record and commander view:

1. **Contact detection:** whether a contact was observed and whether that report
   remains current. An absent or stale observation is not proof of absence.
2. **Classification assessment:** the current fictional class hypothesis and its
   estimated confidence, including an explicit unknown/ambiguous outcome. Civilian
   or noncombatant contacts are not collapsed into the hostile category merely
   because they are not identified as friendly forces.
3. **Evidence quality:** independent source count, age, contradictory reports and
   whether information is observed, relayed or supplied in the briefing.

Keep hidden scenario truth distinct from these assessments. A probabilistic
confidence display is an estimate under the synthetic game model, not a claim of
real-world identification accuracy or permission to act. Where numerical estimates
have not been validated even against that model, show UNCONFIRMED / CORROBORATED /
CONFLICTING instead of inventing precise percentages. Later calibration checks
compare game estimates against repeated seeded scenario outcomes.

Additional independent perspectives or authored sensor-mode cues may resolve
ambiguity, but can also reveal a contradiction and reduce confidence. More reports
must not monotonically push a contact toward a hostile classification. Forwarded
copies, repeated frames and correlated cues cannot masquerade as independent
confirmation. Shared errors can leave several nodes confidently wrong, which is
an important experiment/debrief outcome.

For the authored game scenarios:

- “No known friendly presence” is an uncertain briefing claim with an age and
  source, not a default hostile designation or an assurance that civilians are absent.
- An IR-strobe cue can be represented as a claimed friendly indicator, with
  visibility/ambiguity defined by the scenario. Its absence cannot establish
  hostility; its presence is not an infallible identity oracle.
- A lost node or a witnessed simulated crash raises a location-tagged incident
  warning. The report must distinguish lost telemetry, observed loss and a claimed
  cause. None automatically identifies a nearby contact as hostile.
- Nearby participants can show ALERT/CHECK as game presentation, and the commander
  can request additional observation or recall. Do not encode an automatic
  pursuit/attack response from a loss report.
- Conflicting identity evidence can produce BLUE ON BLUE risk warnings. A risk
  warning, an actual game incident and the mission's allowed scenario actions
  remain separate records. Do not treat confidence alone as action authority.

Camera angles, thermal/visual modes and incident reports are synthetic evidence
fixtures in this version. No detector for weapons, muzzle flashes, uniforms or
actual people, real sensor-fusion targeting logic, or autonomous engagement rules
are implemented by this specification.

The 64×64 panel conveys uncertainty with existing CHECK/DOUBT/ALERT states and
compact observation marks. The remote's selected-mission/contact view exposes
classification estimate, independent evidence, report age and contradictions;
keep the already crowded sixteen node cards focused on readiness and resources.
Record assessment revisions and their causes so a debrief can explain a mistake
without rewriting what the commander knew at the time.

## Battery inventory and scenario clocks

Each pack has a persistent ID, owner/home location, charge and state: fitted,
available, servicing, queued or charging. No pack can be fitted to two nodes or
be charging and flying simultaneously. Losing a node loses its fitted pack;
spares remain at home but do not provide a replacement aircraft.

Scenario fields include packs per node, initial pack charges, maximum swaps per
node for the campaign (including a three-swap option), automatic-swap policy,
swap/service duration, recharge duration and available charging slots per home.
A completed swap consumes one allowance; retrying the command does not. Once the
allowance is exhausted, the fitted pack can still recharge normally. The debrief
shows pack use separately from sorties and aircraft losses.

A removed pack may need a configured service/cooldown interval before charging.
A full charger queue waits; it cannot recharge every pack simultaneously unless
that scenario provides enough slots. If an automatic swap has no available
replacement or allowance, show the waiting/charging reason. Never manufacture a
fresh pack merely because the player enabled automatic replacement.

Maintain one simulation clock with explicit playback speed. Normal speed means
one simulation second per elapsed second, not a claim of calibrated aircraft
performance. Acceleration applies to travel, search, service, charging and order
expiry together. An acknowledged Pause freezes them together. LilyGo sleep does
not pause the backend; wake obtains a fresh snapshot before enabling commands.
Backend shutdown checkpoints the campaign; backend restart restores paused for
explicit resume. Do not infer unobserved elapsed game time after power loss.

The 6S label describes cell configuration, not a unique capacity or flight time.
For example, the manufacturer's catalogue contains both
[1,600 mAh 6S](https://genstattu.com/tattu-r-line-version-6-0-1600mah-160c-6s-22-2v-sq-lipo-battery-pack-with-xt60-plug/)
and [16,000 mAh 6S](https://genstattu.com/ta-30c-16000-6s1p-as-as150.html)
packs. Therefore the game requires explicit, configurable sortie/service/recharge
presets rather than inventing a universal “6S endurance.” No operational range,
real flight routing, battery cutoff or charging-current recommendations are
specified here. Timing values remain an open presentation/balancing decision.

## Player interruption and recall override

- **Abort mission:** cancel its objective and request return for its surviving
  assigned nodes. This is not an immediate stop in mid-air, loss reset or recharge.
- **RTB selected:** request return of selected participants while others continue.
- **Continue despite battery warning:** deliberately override automatic recall for
  the selected active assignment. Before accepting, identify affected nodes and
  explain that return may be impossible and simulated aircraft may be lost.
- Keep the override visible in mission/node details. A reconnect does not silently
  enable or remove it. Expire it at assignment completion, loss or campaign reset;
  never inherit it in the next sortie. Clear it when a manual RTB is accepted.
- Commands are available throughout the controllable sortie, but cannot reverse a
  completed crash/loss or an already irreversible terminal event. Report rejection
  truthfully; “Abort sent” is not “all nodes returned.”

## Coordinated world and state machines

The campaign is a small event-driven game world, rather than a shared animation
playlist. Store fictional positions, home locations, contacts, uncertainty,
assignments, energy, battery inventories, service queues, deadlines and outcomes.
Animation is a view of those records. A variation or repeated animation cannot
change world state or reroll an outcome.

Use separate related state machines:

| Entity | Lifecycle | Persistence requirement |
|---|---|---|
| Campaign | Created → running ↔ paused → ended | Seed, simulation clock, revision and history survive restart |
| Mission request | Pending → assigned → active → resolved / expired / cancelled | Outcomes and evidence remain after participants return |
| Node | At home → assigned → outbound → observing → returning → servicing → at home; a simulated loss can end a sortie | Charge, position, assignment and loss cause do not reset between requests |
| Battery pack | Fitted / available / servicing / queued / charging | Identity, charge and ownership survive swaps and controller restart |

READY / OM / LOST remain the compact projection of node state, not the entire
internal lifecycle. Mission completion and node return are separate events. Several
active missions and incoming requests can coexist with returning/charging nodes.

Each request has an identity, issuance time, deadline, fictional sector, scenario
objective, briefing facts and uncertainty. The scenario scheduler can introduce
new requests while resources are busy. Expiry cannot revive depleted nodes or
silently redirect existing assignments. The player's choices determine the
remaining reserve and service backlog; the game does not automatically dispatch
all available nodes or refill the fleet between requests.

A bounded event queue advances the world using simulation time. Event identities
and a seeded random stream determine discovery, uncertainty, fictional hazards and
outcomes. Store per-node participation and timing so different nodes can arrive,
observe, return or become unavailable at different times. Evaluate synthetic
observations using the statistical contract above, not the number of active
animations on screen. Reinforcements affect future opportunities after arrival.

The initial game engine generates camera-mode changes, observation/classification
cues and permitted outcome animations as synthetic scenario events. It implements
no real strike calculations, aircraft guidance, target-recognition system or
weapon-engagement logic. Later inference experiments may supply bounded proposals
through the existing agent-runtime boundary; provenance stays explicit.

## Scenario briefings and commander decisions

Use military-inspired typography and a compact **fictional mission card**. Its
fields are mission ID, priority, request type, reported contact type, estimated
quantity, grid sector, bearing/range reference, uncertainty and time remaining.
An artillery-support request may be a narrative request type; this is not an
operational call-for-fire form or fire-control output.

Present a condensed five-paragraph order as five readable summary rows, each
expandable for detail. Use the familiar structure with game-specific content;
this is an adaptation, not a claim of full NATO doctrinal compliance. The
[U.S. Army reference](https://tjaglcs.army.mil/LinkClick.aspx?fileticket=-Yv035hB3rw%3D&portalid=0)
lists Situation, Mission, Execution, Sustainment, and Command and Signal.

| Briefing section | Remote summary |
|---|---|
| Situation | Fictional sector, reported activity, information age and uncertainty |
| Mission | Scenario objective, purpose, priority and remaining game time |
| Execution | Player's selected nodes, selected game option and completion/recall conditions |
| Sustainment | Selected nodes' simulated charge, available spare packs and service backlog |
| Command / Signal | Issuing game authority, mission revision, actual link freshness and acknowledgement state |

Execution distinguishes the incoming request from the player's unsubmitted plan.
Changing selection updates the resource summary but does not dispatch nodes.
Keep mission ID and revision visible when moving between briefing and selection;
require the player to review a changed order before submitting an older plan.
Show concise summaries on the briefing page rather than squeezing full prose
onto the sixteen-node overview. Provide a persistent route back to selection and
keep urgent alerts accessible. Missing information reads UNKNOWN, not an invented
fact. Game narrative communications and actual device connectivity are labelled
separately. The format adds no operational targeting or weapon instructions.

Briefings distinguish reported from confirmed information. Use UNKNOWN or an
uncertainty cue where appropriate; do not expose hidden ground truth as HQ fact.
Bearing/range must name their reference (the selected node or a stated scenario
origin), since the sixteen homes are distributed. A single unexplained range
cannot represent every node's travel. The selected-node view supplies its own
fictional travel estimate and battery/service state.

Show a new-request attention banner and retain the request in a queue. Do not
replace an active mission, steal selected nodes, dismiss a BLUE ON BLUE warning
or relaunch an aircraft simply because a new briefing arrives. Briefing flashes
are bounded; the message remains readable and retrievable after the pulse.

The intended resource choices are dispatch now versus retain a reserve, send a
small group versus spend more observers on uncertainty, wait for charging versus
risk expiry, reinforce versus recall, and choose an explicitly authored expendable
game option versus preserve aircraft. Any point-of-no-return warning refers only
to the scenario's game budget and remains distinct from validated physical range.
No allocation optimiser selects an attack plan for the player.

## Architecture and interface responsibilities

- `experiments`, initially hosted on the Mac, is the sole authority for world
  truth, simulation time, seeded draws, missions, virtual node condition/position,
  batteries, scoring and replay. Use a portable C++ core with bounded objects,
  explicit time inputs and seeded randomness, shared by native tests and the
  host service. Keep sockets, files, ESP-IDF, rendering and device drivers outside
  the core. The preview consumes service snapshots rather than independently
  advancing another authoritative world.
- `node-platform` renders the latest accepted campaign snapshot and interpolates
  ordinary visual motion locally. It acknowledges the applied campaign/revision
  and reports actual hardware health separately. It does not invent a loss,
  recharge or mission outcome while awaiting the coordinator. Preserve existing
  identity, brightness limits, diagnostics and both firmware update paths.
- `management-console` presents briefings, selections, live acknowledgements and
  status. LilyGo is a client, not a required relay for panel traffic or camera
  streams. Its SD card can retain media, update images and optional cached logs;
  a cached campaign snapshot is never an independent source of truth.
  Snapshot publication, transport, UI and persistence must have bounded work
  and explicit backpressure. Slow consumers may coalesce superseded snapshots;
  accepted commands and significant events require explicit delivery outcomes.
  Bulk SD hashing/writes cannot hold the game/radio lock.
- `flock-network` carries versioned authenticated commands and state snapshots.
  Every message identifies campaign, mission where applicable and revision.
  Separate dispatched, accepted and visibly applied state. A node has at most
  one assignment; duplicate/replayed requests cannot start another sortie.
- The coordinator owns pending reservations and resolves ambiguous acceptance
  before reuse. Per-node acknowledgements are not an atomic fleet transaction;
  partial acceptance is shown. Missing confirmations never become success merely
  because an animation timer elapsed.
- Journal meaningful state transitions and checkpoint simulation time, random
  generator state, queue, inventory and mission revisions. Use bounded checkpoint
  frequency and atomic/recoverable writes; never write every rendered frame.
  Boot restores the last consistent checkpoint paused, with any uncommitted tail
  disclosed, then reconciles node revisions. Never invent charge, revive losses,
  reroll committed events or silently advance deadlines across unknown downtime.
- While the backend is running, a missed node link does not stop the central simulation
  clock. That node's physical display is stale until reconciled; this is not an
  automatic fictional shoot-down. A lost coordinator heartbeat causes panel
  presentation to stop claiming live campaign data after its bounded lease;
  freeze/mark stale instead of independently generating divergent outcomes.
- Remote Sleep disconnects only that client. Explicit Pause/Resume must be
  acknowledged by the backend; the UI must not claim success from a local tap.
  Reconnection fetches current authority, revision and eligibility before sending
  new commands. Do not replay queued launches automatically after an outage.
- Moving the coordinator between Mac, Pi and an eventual embedded host requires
  explicit authority ownership, an epoch and reconciliation. The previous owner
  must be stopped or fenced before the replacement accepts commands; a network
  timeout alone cannot elect a second authority. Backend failure freezes live
  presentation after its lease expires and recovery restores paused.
- Existing identity, health, OTA and recovery remain available independently of
  the game service. Game reset, loss or an unavailable external GPU cannot remove
  a node's management access. Heavy inference remains a separate optional service
  with bounded requests and timeouts, not a prerequisite for management.

### Deployment and hardware adapters

Start with a native host service for development and a persistent data directory
for checkpoints, event logs and scenario assets. Package the same host service
for Linux ARM64 on the Pi, with explicit configuration and a persistent volume.
A container is a packaging option, not a requirement for the deterministic core.
Container recreation must not reset a campaign. Test replay equivalence on both
host architectures; do not rely on platform-specific floating-point behaviour or
unspecified random-number distributions for committed game outcomes.

An ESP32 deployment would recompile the core into firmware and replace the host
network/storage adapters. Do not assume the Linux container or its dependencies
will run on that board. The alternative is to retain the Pi as engine host and use
the ESP32 solely as a radio/sensor gateway; both arrangements preserve the same
client contract. Exact host build tooling and dependencies belong in the reviewed
implementation plan.

Use the existing IP network first where appropriate. ESP-NOW requires a verified
radio gateway and an explicit host-to-gateway protocol; a Mac/Pi connection alone
does not supply ESP-NOW support. Firmware changes must preserve the proven update
paths. Camera/lidar access is a separate adapter with timestamped observations;
bulk camera data must not traverse the handheld or block management messages.

`communication-lighting` consumes communication events carrying source,
destination(s), event identity and time. Its physical strip mapping, path animation
and WLED transport remain separate from campaign rules. Slow or disconnected
lighting cannot stall a game tick or change an outcome. Camera/lidar/WLED support
is an integration boundary here, not an implementation included in this draft.

The latest requested future controller is described as ESP32-S31, whereas the
earlier board was Waveshare ESP32-P4-WIFI6-POE-ETH (P4 plus C6). These are distinct:
see [Espressif S31](https://www.espressif.com/en/products/socs/esp32-s31) and
[Waveshare P4 board](https://docs.waveshare.com/ESP32-P4-WIFI6-POE-ETH).
Confirm the purchased board before selecting camera, Ethernet, radio or firmware
drivers; SoC features do not establish the connectors present on a particular PCB.

The last recorded current-console snapshot in
`docs/validation/overview-status/final-status.json` reports 180,764 bytes of free
internal heap and a 172,020-byte largest free block. This is baseline evidence,
not a campaign-capacity guarantee. Profile the remote client with sixteen nodes,
radio retries and e-paper refresh, and profile the backend separately with
overlapping requests and persistence. Moving the core onto any ESP32 requires a
separate memory, latency and driver-concurrency acceptance test.

## LilyGo interaction

The LilyGo is the Flockinator command surface. Campaign Overview is a touch-select
4×4 grid associated with the currently selected mission/order. Tapping an eligible
card toggles selection; a separate visible Details action opens its full record.
Keep a clear selected count and make the affected mission unambiguous.

Every card must expose these fields without requiring the player to inspect sixteen
separate detail pages:

| Field | Meaning |
|---|---|
| Node label and READY / OM / LOST | Campaign condition |
| Health/link indicator | Actual node report freshness and hardware health |
| Battery percentage/bar | Fitted simulation pack charge |
| Estimated distance | Fictional distance to the selected order's sector; show `--` when none is selected |
| Swaps remaining | Remaining allowance, with spare availability distinguished in details |
| Recharge/service countdown | Estimated next readiness/service time; `--` when not applicable |

Use a compact, aligned card layout with a small legend. Render with the actual
e-paper fonts to verify all sixteen cards are readable and touch targets remain
usable. Charge/countdown precision should suit decision-making rather than cause
continuous full-screen flashing; show minute-scale countdowns on Overview and a
more precise value in Details. Existing low-latency state/freshness updates remain.

LOST cards have a visible cross-out and cannot be selected. OM, stale, incompatible
and insufficient-charge/service cards also cannot be dispatched, with their reason
visible. If a selected node becomes ineligible, remove it from the pending selection
and explain why. Validate eligibility again on MISSION GO and at the recipient;
a UI selection is not a reservation or evidence of command acceptance.

**MISSION GO** launches the selected eligible nodes for the selected order. For an
already active mission, label the action as adding the selected reinforcements.
Never restart existing participants, refill batteries or reset accumulated evidence.
Accepted assignments reserve their nodes, and partial acceptance remains explicit.

The mission panel offers **Abort mission**, **RTB selected**, reinforcement selection
and the deliberate battery-warning override. Present incoming orders separately
from active missions. Pause, End and Reset remain distinct actions with persistent
resource semantics, rather than reusing demonstration Stop-all-to-READY.

**BLUE ON BLUE** uses a prominent, persistent-until-acknowledged alert banner with
an attention pulse appropriate for e-paper. Avoid a continuous full-screen flash
loop. Keep the affected mission and Abort/RTB controls accessible; acknowledging
the warning alone neither cancels the mission nor confirms an incident.

## Scoring and debrief

Show completed/expired missions, correct/incorrect classifications, safe returns,
losses by cause and available/charging counts. Retain a timeline explaining what
was known when decisions were made. Avoid a score that rewards friendly mistakes
or disguises an unconfirmed result as success. Exact score weights and difficulty
curves are preview tuning decisions. The player chooses deployment size; this
increment does not add an automatic force-allocation optimiser.

### Browser play and staged progression

The first browser client connects to the local authoritative service and supports
the complete select, brief, dispatch, recall, pause and debrief loop without a
LilyGo or physical panel. Provide a public-demo deployment profile containing only
synthetic scenarios: no device credentials, LAN discovery, firmware deployment or
access to the owner's management network. Publishing remains a separate action.

Preserve a path to a self-contained browser build of the portable core, such as
WebAssembly, subject to toolchain and replay-equivalence validation. This is an
optional later packaging target, not an assumed capability of the current preview.
An independent browser session owns its own campaign; a browser connected to the
physical installation remains a client of that installation's sole authority.
Specify background-tab pause/recovery semantics before browser-only release;
browser timer throttling must not silently change game outcomes.

Define versioned stages that introduce one concept at a time: baseline resource
management, delayed/missing reports, temporary partitions, contradictory synthetic
reports, and recovery after a simulated compromised participant. Gates use explicit
completion conditions and a debrief acknowledgement; do not quietly reset losses
or battery inventory at a stage boundary. A standalone lesson may start with its
own clearly labelled initial state. Research mode can select any stage directly.

Use a visible score breakdown for objective completion, preserved resources,
appropriate handling of uncertainty and recovery, with penalties for incorrect
decisions and unreported failures. Avoid rewarding activity or message volume by
itself. Exact weights are versioned game-balancing choices. Mark confidence and
score as game quantities, never calibrated operational effectiveness. Leaderboards,
accounts and multiplayer are outside the initial scope.

### Research companion: communication and trust robustness

Keep three separate records: hidden synthetic world truth, each agent's available
information, and the player's visible information. Only an explicit researcher
view or post-run debrief reveals hidden truth. The initial scripted game illustrates
these distinctions; it is not evidence that distributed inference is implemented.

Model communication disruption as controlled message loss, delay or partitions
inside the simulator. A synthetic rogue participant can supply authored false or
contradictory reports in a bounded scenario. Preserve provenance so repeated or
forwarded assertions remain attributable to the same source. This scope provides
no RF jamming instructions, real-system compromise or operational targeting logic.
For reusable trust benchmarks, use neutral contact labels and abstract decisions
independently of the military visual theme.

Do not assume that fewer links always produce more mistakes or that additional
peers always improve decisions: treat these as hypotheses. Compare outcomes under
declared conditions, including uncertainty, deferred decisions and recovery, rather
than baking the research conclusion into the score or probability settings.
The later agent-runtime experiment must make actual decisions from its permitted
observations; playing an authored animation does not constitute that experiment.

Research exports record scenario and policy versions, seed, initial state,
timestamped commands, source report IDs, injected fault events, state transitions
and outcomes. Separate random streams for world events and communication faults
support paired comparisons without an extra dropped message rerolling the world.
Interactive player decisions can diverge between runs; do not label those runs a
controlled comparison without accounting for that difference.

Report interpretable measures alongside game score: message delivery and latency,
time operating with stale information, incorrect decisions and abstentions, false
exclusion of honest participants, time to identify/recover from inconsistent
reports, communication cost and resource use. Define denominators, observation
windows and simulated versus measured provenance. Repeat across seeds and report
variation; one entertaining run is not a robustness result. Lower connectivity
may appropriately produce more abstentions rather than more incorrect decisions.

Export a sanitised replay bundle with a concise debrief for readers of the paper.
A replay contains enough versioned data to reproduce or explain the run; redact
real device identifiers, credentials and private network details. Measurements
from the physical mesh are a distinct dataset and cannot be inferred from the
browser's configured packet-loss parameters.

### Decision timeline and branching replay

Present the replay as a shared horizontal simulation timeline with one expandable
lane per agent, plus lanes for commander commands and communication disruptions.
Default to significant observations, received reports, decisions, state changes
and outcomes; collapse routine traffic into counts that can be expanded. Filtering
to one agent, mission or source report must retain visible references to relevant
events outside the filter rather than making their provenance disappear.

Selecting a decision opens a tree-style explanation of its recorded inputs and
result. Reports can branch to multiple recipients and decisions can combine several
reports, so the underlying representation is an event graph with shared references,
not duplicated evidence in a strict tree. Distinguish observation, transmission,
receipt and use: a sent report is not proof that it arrived or influenced a decision.
Show event time, receipt time and age where available. For physical measurements,
retain clock uncertainty; screen position alone must not imply proven causation.

The decision inspector shows the acting agent, its prior and resulting state,
available observations, source/provenance IDs, recorded confidence or uncertainty,
applicable policy version and selected action. Display a concise recorded reason
code or decision summary when available; otherwise label the reason unavailable.
Do not invent internal reasoning or imply that a post-hoc explanation is a recorded
decision trace. Alternatives appear only if recorded as evaluated; distinguish
them from user-proposed counterfactuals.

Provide play/pause, speed control, scrubbing and previous/next significant-event
controls. The time cursor synchronises agent panels, command history and the
decision inspector using saved events, without rerunning random choices. A
knowledge-at-the-time view excludes later reports and hidden truth. A separately
labelled researcher overlay can reveal injected false reports and actual synthetic
world state without rewriting what agents knew at the selected moment.

Selecting a source report highlights its recorded propagation and decisions that
explicitly reference it. Repeated forwarding retains one origin. Label these as
recorded dependencies, not proof that removing the report would change the outcome.
A counterfactual run is a separate, labelled simulation with its own run identity;
never splice its unobserved branches into the historical replay.

Use shape/text as well as colour for event types and uncertainty. Keep sixteen
lanes manageable through folding and zoom; render the detailed graph in the browser,
with only concise event summaries on LilyGo. Support a sanitised static timeline
export suitable for a paper alongside the interactive replay bundle.

### Future scenario questions: assessment, contention and scale

Recorded 16 October 2026 as research ideas, not an approved implementation or
operational decision policy. The owner proposes fictional post-action assessment,
uncertain completion and possible follow-up requests, with several simultaneous
demands competing for finite observers, time, energy and reserves.

Separate an action's completion from knowledge of its outcome. An animation
ending or a node reporting completion cannot by itself establish objective success.
Authored scenarios may leave an outcome unknown, provide delayed confirmation,
or introduce conflicting assessments. An absent assessment remains unknown rather
than automatically proving success or failure. Preserve the assessment's source,
age and uncertainty in both the commander view and replay.

Explore resource contention through abstract task and observation scenarios:
resources assigned to one activity are unavailable elsewhere; waiting consumes
time; gathering more information has a cost; reserves can preserve later options.
Use these to study the trade-off between committing resources and resolving
uncertainty. Do not turn the owner's examples about distance, remaining battery,
expendability or follow-up actions into autonomous weapon-selection, attack-timing
or strike-allocation algorithms. Such operational policies remain outside scope.

Human oversight is itself a research variable: compare visible information,
notification delay, intervention opportunities and how many concurrent decisions
a player can follow. Record which actions were authored scenario events, player
commands or actual bounded agent decisions. Faster decisions are not necessarily
better decisions, and neither speed nor scale alone establishes that autonomy is
necessary or safe. Generic delegated tasks must have explicit authority limits,
interrupt behaviour and traceable outcomes.

Keep the physical sixteen-node demonstration distinct from future virtual scale
studies. Synthetic runs with hundreds or thousands of agents could examine queue
growth, delivery delay, provenance tracking, correlated errors and recovery under
communication faults. These are optional future benchmarks, not a promise that
the current firmware, radio link or LilyGo supports those populations. Simulated
scale cannot establish real RF capacity, battlefield effectiveness or human
oversight performance without separate evidence. Use neutral labels and tasks
for reusable large-scale communication/trust benchmarks.

The replay should distinguish action, assessment request, available observations,
assessment revision and eventual outcome. This makes uncertainty and competing
resource demands visible without presenting an authored result as an inferred
one. Detailed assessment UI, policy comparisons and scaling work require their
own reviewed scope before implementation.

## Project structure and code style

Proposed portable C++ campaign model: `firmware/shared/experiments/` (new; no firmware-only dependencies).
Proposed host service and deployment packaging: `services/campaign-engine/` (new).
Existing adapters: `firmware/node-platform/`, `firmware/management-console/`.
Preview client: `previews/recon-hud/`; commissioning tooling remains in
`tools/node-commissioner/` and does not become the game service.
Evidence: `docs/validation/campaign/` (new, when implementation begins).

Use fixed limits, explicit units, monotonic time, validated enum values and
immutable render snapshots. Example contract shape, not a frozen wire layout:

```cpp
struct AssignmentIdentity {
    uint32_t campaign_id;
    uint32_t mission_id;
    uint32_t revision;
};
// A duplicate identity may confirm acceptance; it must not restart or refill.
```

Do not overload the present global run ID to mean several concurrent missions.
Specify command bytes, capability negotiation and storage migration in the
reviewed implementation plan before changing either device adapter.

## Commands and testing strategy

Existing regression/build commands, from `/Volumes/devops/flockinator`:

```sh
$HOME test --project-dir firmware/node-platform -e native
$HOME test --project-dir firmware/management-console -e native
uv run --project tools/node-commissioner python -m pytest tools/node-commissioner/tests -q
$HOME run --project-dir firmware/node-platform -e waveshare-s3
$HOME run --project-dir firmware/management-console -e lilygo-s3
```

Run firmware builds sequentially because their PlatformIO toolchains differ.
No campaign CLI exists yet. Its exact preview, replay and validation commands
belong in the implementation plan; do not present future commands as runnable.

Native tests exercise deterministic time/energy transitions, eligibility,
concurrent disjoint assignments, duplicate/stale commands, pause/resume, outcome
persistence, reboot reconciliation and charge bounds. Test finite pack inventories,
charger contention, timed swaps, swap allowances, retained spare charging,
assignment-scoped recall override, statistical replay and frame-rate independence.
UI tests cover selection,
partial acceptance and clear rejection reasons. Protocol/host tests cover identity,
capability versions, malformed payloads and truthful freshness.

## Acceptance criteria

1. Dispatch only A1/A2; the other fourteen remain available/charging as appropriate.
   Dispatch B1 on a second mission without restarting or changing A1/A2's mission.
2. Reject a second active assignment for a busy node, including concurrent and
   retried commands. An ambiguous acknowledgement never creates a duplicate sortie.
3. A no-finding sortie returns, spends energy landing and starts charging. A later
   assignment can use it partially charged when eligible, without resetting charge.
4. A KIA node remains unavailable across new missions, remote sleep/restart and
   node restart. MIA resolution is explicit and distinct from Wi-Fi reconnection.
5. A known charge/travel scenario recalls before its configured return allowance;
   a scenario with synthetic disruption can fail and records the cause. No negative
   battery values or free energy. A node link outage does not pause the active
   coordinator's clock; an acknowledged Pause does. Remote sleep does not.
6. Repeated copies of a synthetic observation never increase independent-source
   count. A last-known sector remains an uncertain lead for a follow-up request.
7. Losses and mission completion are separate: a surviving successful node returns;
   an expendable ending consumes only the assigned node. Friendly mistakes remain
   visible in the debrief rather than being rewritten as correct identification.
8. LilyGo sleep/restart leaves the backend running, including charging and expiry.
   Wake fetches fresh state and never replays an old launch. Explicit Pause freezes
   all clocks. Backend restart restores paused and reconciles before Resume;
   recovery cannot resurrect, double-charge or reroll committed events.
9. Campaign Overview uses only READY / OM / LOST, plus separate health, charge,
   selected-order distance, swaps and service/recharge fields on each card. LOST is
   crossed out and cannot enter MISSION GO. Actual freshness warnings and quiet
   refresh behaviour remain. Existing management regressions pass.
10. Validate the game loop in a preview, then one node, then several concurrent
    assignments, before fleet rollout. Save actual observations separately from
    simulated fixtures. The current live demonstration continues until that rollout.
11. With one fitted pack and three charged spares, complete three timed swaps.
    A fourth replacement is unavailable at a three-swap campaign allowance;
    ordinary charging remains possible. A two/three-pack preset must wait for
    recharge when depleted, rather than materialise a spare.
12. A removed pack charges while its node flies with another pack; a single charger
    services only one eligible pack at a time. Duplicate swap commands cannot
    consume additional allowances or fit the same pack twice.
13. Automatic replacement on RTB consumes a real available scenario pack and
    service time. Switching the policy cannot refill the fitted pack instantly.
14. A confirmed player recall override can continue a fictional search into
    depletion; it never disables manual RTB, alters another assignment, or leaks
    into the next mission. Loss and its decision history persist after reconnect.
15. Abort ends the requested objective and starts return of surviving participants;
    concurrent missions continue. Energy still falls during return. All simulation
    timers scale together and preserve event order across pause and acceleration.

16. Reinforce an active mission with a previously unassigned node: original members
    retain assignment, evidence and energy. The reinforcement contributes only
    after its fictional arrival. Duplicate launch requests create no extra observer.
17. Under controlled fictional presets, repeated seeded trials show diminishing
    aggregate benefits from additional independent observers, closer proximity and
    longer valid observation, while preserving nonzero failure/uncertainty where
    configured. An unrelated airborne node gives no discovery bonus.
18. Replaying the same event stream at different renderer and status-poll rates
    produces the same discovery/classification results. Refresh/reconnect never
    resets observation time or rerolls an outcome.
19. A suspected friendly misidentification produces an attributable BLUE ON BLUE
    alert. Cancel affects that mission only; acknowledgement does not invent an
    incident or silently abort. A confirmed incident remains a distinct record.
20. A selected node becoming LOST, busy, stale or otherwise ineligible is removed
    before dispatch. Eligibility is also checked by the recipient. Depleted packs
    safely at home show recharge status under READY rather than a false loss.

21. HUD distance uses each node's own immutable launch position. At home it is
    `00`; a fixture at 14,000 m is `14`; 500 m remains `00` with 0.5 km available
    on the remote. The field decreases during a direct fictional return, remains
    stable during a constant-radius loiter, and does not reset on reinforcement.
22. Test unknown and overflow values, every state/mode at 64×64, and coexistence
    with compass, sensor label and communication border. No corner SIM label
    remains in campaign flight frames; remote/presenter simulation provenance
    remains visible. The deployed demonstration changes only through rollout.
23. Scenario fixtures place sixteen home positions 500 m apart with 7.5 km endpoint
    separation. Two nodes observing the same fictional location may have different
    HOME distances. The remote's mission distance must not be mislabelled HOME.
24. Any authored one-way search bonus is explicit and cannot silently become a
    universal 2× endurance assumption. A failed search or mistaken classification
    remains possible with one or several observers; no success is granted merely
    because a node is committed to an expendable ending.

25. Deliver a new briefing during an active assignment. The original mission,
    selection context and reserve/charging conditions remain intact; the new
    request can independently expire or receive a disjoint selection of nodes.
26. A readable fictional briefing distinguishes reported quantity/class from
    confirmed facts and names the bearing/range reference. Its attention pulse
    does not dismiss critical warnings or prevent Abort/RTB interaction.
27. During a slow e-paper refresh, the campaign clock, radio handling and event
    ordering continue correctly. Demonstrate bounded memory/queue use and record
    tick delays, dropped/retried updates and checkpoint duration under fleet load.
28. Restart the coordinator and reconnect a stale panel. Restore the saved seed,
    campaign time and revision paused, reconcile state, and resume without duplicate
    sorties or outcomes. Display lease expiry must not create a fictional loss.
29. Trace at least one briefing through selection, partial/complete acceptance,
    observation, warning or outcome, return/loss and subsequent battery service.
    Every visible status must be attributable to a world event or an explicitly
    identified hardware observation, not a preselected animation playlist.

30. Playing, repeating, skipping or reversing an eligible visual clip cannot
    generate a discovery, refill energy, change classification or finish a mission.
    World events and commander commands alone drive those semantic transitions.
31. A no-known-friendlies briefing plus an absent strobe leaves room for unknown
    and noncombatant contacts. A lost node or crash observation alone cannot set
    an unrelated contact's identity or trigger pursuit/engagement.
32. Additional contradictory independent evidence can reduce an assessment's
    confidence. Ten forwarded copies of one report still count as one origin;
    changing camera-mode animation without a new game observation adds none.
33. Compare recorded game confidence against hidden synthetic truth across seeded
    trials. Report uncertainty/miscalibration rather than presenting invented
    percentages as validated accuracy. Preserve the commander's contemporary
    information, warnings and choices in the debrief.

34. Replay a saved synthetic campaign through native Mac and Linux ARM64 builds
    with identical semantic results. Recreate the container with its persistent
    volume and recover the saved campaign rather than starting a new one.
35. Disconnect the remote and lighting consumer independently. The backend remains
    responsive, panel snapshots progress and management stays accessible. Stop
    the backend: clients mark data stale, and no client promotes itself to authority.
36. Transfer authority between host deployments using checkpoint/revision/epoch
    validation and stop or fence the prior owner. Commands from a stale authority
    are rejected; reconnection cannot create duplicate assignments.
37. Render all five briefing summaries legibly using the LilyGo's actual fonts.
    Expand details and return to node selection without losing the selected order.
    A revised order invalidates a stale submission; editing a plan alone never
    dispatches nodes. Reported information remains distinct from scenario truth.
38. Complete a campaign through the browser with no physical hardware connected.
    The public-demo profile exposes only synthetic sessions and no hardware
    management capability. Browser and remote clients observe the same revision
    when connected to the same installation.
39. Show a stage's completion conditions, score breakdown and debrief. Progression
    cannot silently revive a lost node, refill packs or reveal hidden world truth.
40. Reproduce a synthetic fault scenario from a sanitised replay and distinguish
    source reports from forwarded copies. Export metrics independently of game
    score, with provenance and versions; identify scripted outcomes as scripted.
41. Trace a synthetic report from one origin through multiple recipients into a
    recorded decision. A dropped transmission has no receipt/use edge. Shared
    origins are not counted twice, and unknown decision reasons remain unknown.
42. Scrub to a decision made before a later correction. The agent view shows only
    then-available information; researcher truth is explicitly separate. Replaying
    or exporting the timeline cannot change saved outcomes or issue live commands.

## Boundaries and review

- Always: distinguish synthetic state from hardware facts; preserve management,
  credentials, SD media and brightness limits; use uv for Python; retain failed
  verification evidence and deterministic seeds.
- Ask first: destructive storage migration, reset of saved campaign progress, or
  changing the agreed persistent-loss/automatic-return semantics.
- Never: use an animation reset as game recovery; count forwarding as independent
  evidence; let simulated exclusion remove firmware-management access; include
  real aircraft actuation, real-world target recognition or weapon interfaces.

Review decisions requested: accept this campaign loop and the assumptions above,
including a host-first portable core, LilyGo as a client, continued play during
remote sleep and paused recovery after backend restart,
browser play with optional physical presentation, staged game progression and
separate reproducible communication/trust research records,
especially READY / OM / LOST with separate battery/health fields, statistical
fictional observations, mission reinforcement, persistent losses, finite pack
inventories and swap allowance,
dispatch from partial charge, automatic return with deliberate in-flight override,
and separating objective completion from an aircraft's expendable KILL ending.
Timing presets and the default two/three/four-pack inventory remain review choices;
no numerical aircraft endurance or recharge-time claim is implied by “6S.”
No campaign implementation or firmware deployment is authorised by this draft.

## Compact display fields — owner revision, 16 October 2026

Browser visual study 14 implements the requested presentation layout: node ID,
north arrow without N, TV/NV/BH/WH (optional IR), heading 000–359, and D00 whole km.
NR0:00 is a supplied return-deadline readout beside the state; at zero it becomes
BINGO. The lower detail row retains the battery icon and any terminal countdown.
Missing values are D-- / NR-:--; overflow is D++ / NR+:++.

The running browser uses explicitly labelled authored sample data, independent
of reversing animation playback. It does not derive safe return from distance,
battery, aircraft specifications or the animated battery icon, and these labels
do not change outcomes. Real campaign state integration remains unimplemented.
The existing node firmware is unchanged.

Future assessment presentation: an ASSESS view could show a hover/orbit and
uncertain observations after an event. Record the distinction between an event
and confirmed outcome; no additional-attack policy is implemented by this UI.
