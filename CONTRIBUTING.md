# Contributing

- Python uses uv (`uv sync --project tools/<tool>`); firmware uses the
  pinned toolchains in [docs/build.md](docs/build.md). Run PlatformIO
  jobs sequentially.
- Run the tests beside anything you touch; firmware changes get a
  one-node canary before any fleet claim.
- Keep documentation concise and public: project description, goals,
  methodology, and build/use instructions. No operational history,
  private inventory, or node-derived data.
- Never commit credentials, device keys, MAC/IP inventory, raw device
  backups, or journals from real nodes. Synthetic fixtures only; scan
  your tree before pushing (see [SECURITY.md](SECURITY.md)).
