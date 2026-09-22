# Real-SFM Qualification Ledger

One row per checkpoint. Raw findings are kept separate from conclusions: this ledger records what
was run and what the mechanical result was; narrative analysis belongs in each checkpoint's own
report, not here. Failed evidence is never overwritten by a rerun — a rerun gets its own new row.

Governing identities for the whole campaign, pinned unless a specific row states otherwise:

| Identity | Value |
|---|---|
| Accepted integration commit | `68f1188e7dcb3fdd34d384396bf5d7a14acf7d25` |
| Production Normalizer SHA-256 | `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867` |
| Accepted authority package base | `cf06ba4ec2080e17d5132ed15f641c143a4137b1` |
| Required `RUNTIME_API_VERSION` | `1.0.0-b2a` |
| Required `RUNTIME_BUILD_ID` | `package-boundary-corrected-2026-09-22` |
| Canonical Master SHA-256 | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |
| Pre-integration (baseline) Normalizer SHA-256 | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` (not yet independently obtained/verified — required before Phase C) |

## Deployment actions (not checkpoints, but part of the record)

| Date | Action | Detail |
|---|---|---|
| 2026-09-22 | Published a compiled sidecar to `usermod\cfg\sfm_shared_authority\` (previously did not exist) | Source: live installed canonical Master (confirmed SHA `ac45e5c1...`); generation `sfm_master_0_bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b.sfmsidecar`; 124,728 folds, 128,555 occurrences, 42 groups. Performed via the accepted, unmodified `tools/sfm_master_sidecar/publisher.py`, with explicit operator approval (writes to the live SFM install are gated). Offline pre-flight acquisition against this exact artifact confirmed successful before Checkpoint A was handed to the operator. |
| 2026-09-22 | **Deployment correction**: deployed `sfm_master_authority_productionized\` (23 files) and `sfm_master_sidecar\` (3 files) as sibling package directories under `ChadChan3D\`, which had never been deployed at all | Triggered by Checkpoint A's first-run FAILURE (see row A-1 below): the two package directories were simply missing from the live install. Exact file set determined by import-graph/self-documentation analysis of the accepted `cf06ba4` package base (see `real_sfm_qualification/checkpoint_a/DEPLOYMENT_MANIFEST.md` for the full pre-deployment manifest with per-file SHA-256/size, the post-deployment independent verification, and the explicit inclusion/exclusion reasoning for every file). Post-deployment: every deployed file's SHA-256 independently re-verified to match the pre-deployment manifest exactly (23/23 authority files, 3/3 sidecar files, zero extra, zero missing); production Normalizer SHA-256, canonical Master SHA-256, and the published authority generation's `manifest.json` all independently reconfirmed unchanged. |

## Checkpoints

| # | Checkpoint | Script SHA-256 | Normalizer SHA | Package build/API ID | Master SHA/generation | Project/fixture | Operator action | Expected result | Actual result | PASS/FAIL | Evidence | Anomalies |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-1 | Bootstrap / installed-authority smoke test (FIRST ATTEMPT — permanent record, not overwritten) | `b3fa5cd7c0a437b50668e448bdf925bdf1d7fc587ab33e77e0df277d391c2f1e` | n/a (not read by this script) | `package-boundary-corrected-2026-09-22` / `1.0.0-b2a` | `ac45e5c1...` (live installed Master, matches canonical) | n/a (no project needed) | Restart SFM, run `Checkpoint_A_Bootstrap_Smoke_Test`, return the output file | All ~21 named checks `[PASS]`, `RESULT: N/N ALL PASS`, zero scene mutation, zero save | **FAILED at installed package discovery.** Real `sys.executable`/game-root derivation: PASS. Expected `ChadChan3D` MAINMENU directory exists: PASS. `sfm_master_authority_productionized` installed sibling directory: **MISSING**. `sfm_master_sidecar` installed sibling directory: **MISSING**. Import failed before broker construction/acquisition could even be attempted. | **FAIL** | Operator-returned contents of `C:\Users\Public\Documents\sfm_checkpoint_a_bootstrap_smoke.txt` (verbatim reported to the assistant; not separately archived as a file in this repo) | Classified as an installed-layout/deployment defect, not a source-integration defect — the accepted package implementation and Normalizer were never suspected or modified. Root cause: nothing had ever deployed the two sibling package directories to the live install at all. See the deployment-correction action above for the fix. |
| A-2 | Bootstrap / installed-authority smoke test (RERUN after deployment correction) | `b3fa5cd7c0a437b50668e448bdf925bdf1d7fc587ab33e77e0df277d391c2f1e` (same script, unchanged) | n/a (not read by this script) | `package-boundary-corrected-2026-09-22` / `1.0.0-b2a` | `ac45e5c1...` (live installed Master, matches canonical) | n/a (no project needed) | Restart SFM, run `Checkpoint_A_Bootstrap_Smoke_Test` again, return the output file | All ~21 named checks `[PASS]`, `RESULT: N/N ALL PASS`, zero scene mutation, zero save | **PENDING — awaiting operator execution** | PENDING | `C:\Users\Public\Documents\sfm_checkpoint_a_bootstrap_smoke.txt` (to be returned by operator) | none yet |

Later checkpoints (B through K, per the governing real-SFM qualification brief) are not yet prepared.
Per that brief's own Section 21 implementation order and Section 22 immediate task, Checkpoint B is
not built until Checkpoint A's evidence is returned and assessed.
