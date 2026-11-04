# Security preparation

- No API keys, tokens, private keys, or credential stores are included.
- Secrets must be supplied via environment/private stores, never committed.
- Report vulnerabilities privately to the maintainers; do not open public
  issues containing credentials, device keys, or network details.
- Pre-publish checklist: run a secret scanner (gitleaks/detect-secrets) on
  this tree, review `git log` (fresh history only), and re-check inventory files.

## Scanner review (preparation run)

`detect-secrets` flagged only: SHA-256/digest strings in CAD and firmware
manifests, cryptographic test vectors in `firmware/shared/commissioning/tests/`
and related unit tests, and synthetic password fixtures in commissioner
tests. Each category was inspected by file class; no real API key, token,
private key, Wi-Fi credential, or per-node management key was found.
Re-run the scanner on the final tree and review any *new* file classes,
not just the count.
