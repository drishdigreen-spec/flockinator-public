# Public release — preparation notes

This is a sanitized subset of the private Flockinator experimental repository.
Included: firmware source, host tools, browser preview, CAD models, and
experimental design/specifications. Excluded: private device inventory
(MAC/IP/serial bindings), credential references and credential stores,
raw flash/SD backups, validation evidence/logs, frozen firmware binaries,
purchased/licensed reference models and DOOM-derived assets, migration
archives, and operational handover/internal host details. All MAC addresses,
lab IPs, and home paths in retained text were replaced with example values.

Before publishing: choose a project licence (none selected yet), confirm
third-party dependency licences under `firmware/*/managed_components` are
recreated from pinned manifests (not copied here), re-run the secret scan
in `SECURITY-PREP.md`, and verify no test fixture contains a real credential
(test passwords found in commissioner tests are synthetic fixtures — confirm).
