# Contributing

Build with uv for Python (`uv sync --project tools/<tool>`) and the pinned
ESP-IDF/PlatformIO toolchains in each firmware README. Run the focused tests
beside any code you touch. Never commit credentials, device keys, private
node inventory (MAC/IP bindings), raw device backups, or journals derived
from real nodes - use synthetic fixtures. Firmware changes need a one-node
canary before any fleet claim.
