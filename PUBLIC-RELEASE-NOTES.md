# Public release — preparation notes

This is a sanitized subset of the private Flockinator experimental repository.
Included: firmware source, host tools, browser preview, CAD models, and
experimental design/specifications. Excluded: private device inventory
(MAC/IP/serial bindings), credential references and credential stores,
raw flash/SD backups, validation evidence/logs, frozen firmware binaries,
purchased/licensed reference models and DOOM-derived assets, migration
archives, and operational handover/internal host details. All MAC addresses,
lab IPs, and home paths in retained text were replaced with example values.

Licence: Apache-2.0 (see `LICENSE`) for original project material;
third-party components retain their own licences and are recreated from
the pinned manifests rather than vendored here, except the small
permissively-licensed sources under `firmware/korvo-monitor/main/vendor/`.
For each subsequent export: re-run the secret scan in `SECURITY-PREP.md`
and verify no test fixture contains a real credential (test passwords
found in commissioner tests are synthetic fixtures).
