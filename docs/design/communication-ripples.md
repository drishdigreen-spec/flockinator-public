# Visible communication ripples

Owner direction, 2 November 2026: reproduce communication as ripples or visible
animations between nodes. This follows the deployed independent Patternflow
playlist and is the next cooperative-animation experiment.

Communication events drive the visualisation: a scheduled or attempted send is
not reported as delivery. A receiver's accepted event produces its own arrival
animation; an application acknowledgement lets the sender mark receipt. An
unacknowledged message fades as an attempt, rather than inventing a successful
link. Record actual sender, recipient, sequence, receive time and expiry.

For panel output, animate a pulse toward the panel edge facing the neighbour;
the receiving panel starts a ripple at its corresponding edge. Retain the
underlying Patternflow pattern and the existing 25% brightness/50% hard cap.
Each panel remains independent. Panel gaps do not contain controllable pixels.

For separate physical LED paths, publish the same observed event stream to a
dedicated lighting controller. The current lighting-controller design records no
selected controller/strips. Physical propagation on those paths requires that
hardware and a confirmed section-to-node map. Do not claim an illuminated path
exists merely because a panel draws an edge cue.

Keep experimental peer messages separate from commissioning authentication and
OTA. Bound queues, lifetime, duplicate suppression and response rate; do not
forward endlessly or let experiment traffic starve management. Synthetic
communication fixtures, if used in host tests, remain explicitly labelled.

Owner selected existing panel faces first. Implementation uses the same logical
coordinates as the existing world renderer: A–D left-to-right, 1–4 top-to-bottom.
Physical mounting orientation still requires visual acceptance; direction labels
must be corrected if the installed layout differs.

## First implementation: generated neighbour pulse exchange

Release 0.12.0-patternflow-ripples retains the 34-pattern random playlist and
adds real UDP pulse/acknowledgement exchanges between Manhattan neighbours.
Every node chooses one neighbour every 3.5–6.5 seconds. Amber departure cues mean
the local UDP stack accepted a send, cyan ripples mean the receiver accepted a
pulse, and green edge marks mean a matching application acknowledgement arrived
within 1.2 seconds. No retries or recursive forwarding occur. Unacknowledged
sends expire and increment a timeout counter. Playback uses local time; visual
travel is a schematic effect, not a measurement of packet propagation time.

Transport: UDP port 49170, sixteen-byte explicitly encoded RPL1 frames. Fields:
magic[4], kind[1] (pulse=1/ack=2), sender index[1], target index[1], reserved zero[1],
boot nonce u32le[4], sequence u32le[4]. ACK echoes the pulse boot nonce and sequence.
Exact framing, neighbour geometry, target, source IP and port are checked. The
address roster comes from docs/inventory/network.csv. Duplicate/out-of-order
sequence numbers within a known sender boot are rejected. A new sender boot
replaces its remembered sequence; this is not cryptographic replay protection.
ACK acceptance additionally binds the outstanding peer/session/sequence and local
deadline. At most eight packets are processed per main tick; each peer's accepted
pulse rate is capped at ten per second, and eight overlay events have finite
1.6-second lifetimes. Socket setup retries have five-second backoff.

These are explicitly generated experimental peer messages, not evidence of
emergent decisions or a visualisation of every existing management exchange.
Roster checking is not authentication: same-LAN spoofing is outside this first
experiment's trust model. The service has no maintenance, OTA or storage authority.
No firmware keys, credentials or private control commands are sent over this
channel. It runs only in the experimental Patternflow build and yields during
maintenance. Telemetry distinguishes sends, accepted receives, acknowledgements,
timeouts, duplicates, rejection, socket/send errors, active pattern and render
cost; no send callback is treated as a received message.

