# Security

- No credentials, API keys, device keys, private node inventory, or
  node-derived data belong in this repository. Report any accidental
  inclusion privately to the maintainers.
- Secrets are supplied at runtime (environment or a private local
  store); example files use placeholders only. Test fixtures are
  synthetic.
- Before contributing, run a secret scanner (for example
  `detect-secrets` or `gitleaks`) on your tree and review every new
  flagged file class. Digests and cryptographic test vectors are
  expected flags; real keys are not.
- Adversarial experiment tooling (Kulira) is for authorised lab use on
  your own fleet: bounded, logged, reversible, and never aimed at
  third-party networks or devices.
