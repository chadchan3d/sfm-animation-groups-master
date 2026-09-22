# Checkpoint A — Bootstrap / Installed-Authority Smoke Test

## What this checkpoint proves

Whether the production-integrated shared-authority package actually resolves and acquires
correctly from a **real running SFM process**, using the real installed layout — nothing more.

## Does this test mutate the scene?

**No.** Zero scene mutation, zero native Rebuild, zero group/control creation or modification.
The script never touches `vs.g_pDataModel` and never imports `vs`/`sfmApp`/`sfmClipEditor` at all.
It only: derives paths, imports the authority package, reads the canonical Master file (read-only),
constructs a broker, acquires and releases one small detached projection, and writes a text report.
A source review confirming this is at the bottom of this document.

## Should you save anything?

**No. Do not save the SFM project after running this script.**

## Operator instructions

1. **RESTART SFM FIRST.**
2. **DO NOT SAVE the previous experimental state; restart SFM to discard it.**
3. Start SFM normally. You do not need to open or load any particular project — this script does
   not read or require an open document.
4. Run the script named **`Checkpoint_A_Bootstrap_Smoke_Test`**, using the exact same menu location
   and invocation method you already use to run the existing "Rebuild Control Groups" script (same
   menu, same click-to-run action) — just select this new script's entry instead. It has been placed
   in the same folder as the existing script:
   `usermod\scripts\sfm\mainmenu\ChadChan3D\Checkpoint_A_Bootstrap_Smoke_Test.py`

   If you do not see a new menu entry for it, **stop here and tell me exactly what you do see** (the
   existing menu structure, whether the existing Rebuild Control Groups entry is visible, etc.) —
   do not guess at an alternate way to run it.
5. Wait for it to finish. It should complete quickly (well under a second of real work) — there is no
   native Rebuild, no scene walk, nothing scene-scale involved.
6. Return the exact contents of this file:
   `C:\Users\Public\Documents\sfm_checkpoint_a_bootstrap_smoke.txt`

   Also tell me whether SFM showed any error dialog or console traceback beyond what is in that
   file (there should not be one — the script wraps its own risky section in a handler — but report
   it exactly if you see one).
7. Close SFM without saving, or leave it open — either is fine, since nothing was mutated. If you
   plan to continue to a later checkpoint immediately, restart SFM first per the standing rule above.

## Exact expected output artifact

A single text file at `C:\Users\Public\Documents\sfm_checkpoint_a_bootstrap_smoke.txt`, containing
one `[PASS]`/`[FAIL]` line per check, ending with a line of the form `RESULT: N/N ALL PASS` (or
`SOME FAILED`).

## Mechanical PASS/FAIL criteria (decided before execution)

**Checkpoint A PASSES only if every one of the following checks reports `[PASS]`** in the returned
file (there should be roughly 17 checks total; exact list below, since the harness decides this
mechanically — you do not need to interpret anything, just return the file):

- `game_root.derived_without_exception`
- `mainmenu_dir.exists_on_disk`
- `authority_package_dir.exists_on_disk`
- `sidecar_package_dir.exists_on_disk`
- `import.sfm_master_authority_productionized_runtime`
- `authority_runtime.origin_matches_installed_package_dir`
- `authority_runtime.api_version_matches_expected`
- `authority_runtime.build_id_matches_expected`
- `authority_runtime.is_canonical`
- `master_path.exists_on_disk`
- `master_sha256.matches_expected_canonical`
- `broker.constructed`
- `shipped_root.exists_on_disk`
- `acquisition.detached_view_returned`
- `projection.has_expected_keys`
- `projection.semantic_generation_matches_live_master_sha`
- `provider.closed_before_return`
- `lease.acquired`
- `lease.released_cleanly`
- `provider.zero_open_after_release`
- `checkpoint_a.completed_without_unhandled_exception`

**Any single `[FAIL]` line means Checkpoint A FAILS.** Do not interpret partial success as
acceptable — return the file exactly as written and I will determine what the specific failure
means (deployment/layout issue vs. something else) before proposing any next step.

## Identities this checkpoint is pinned against

- Accepted integration commit: `68f1188e7dcb3fdd34d384396bf5d7a14acf7d25`
- Production Normalizer SHA-256 (unrelated to this script, cited for context only — this script does
  not read or execute the Normalizer): `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Accepted authority package base: `cf06ba4ec2080e17d5132ed15f641c143a4137b1`
- Required `RUNTIME_API_VERSION`: `1.0.0-b2a`
- Required `RUNTIME_BUILD_ID`: `package-boundary-corrected-2026-09-22`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Checkpoint A script SHA-256: `b3fa5cd7c0a437b50668e448bdf925bdf1d7fc587ab33e77e0df277d391c2f1e`

## Prerequisite deployment step already performed (2026-09-22)

Before this checkpoint could be meaningful, a compiled sidecar had to actually exist at
`usermod\cfg\sfm_shared_authority\` — nothing had published one yet. With explicit approval, one was
published from the live installed canonical Master (confirmed byte-identical to the accepted SHA
above) using the accepted, unmodified `tools/sfm_master_sidecar/publisher.py`:

- Generation: `sfm_master_0_bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b.sfmsidecar`
- Manifest `source_sha256`: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` (matches)
- 124,728 folds, 128,555 occurrences, 42 real groups (43rd is the internal synthetic wrapper)
- A direct, offline (non-SFM) pre-flight acquisition against this exact published artifact was run
  and confirmed successful before asking you to run this checkpoint in real SFM.

This is a new, previously-nonexistent subdirectory under the game's own `usermod\cfg\`; nothing
existing was overwritten, and the canonical Master itself was only read, never modified.

## Source review: why this script cannot mutate the Master, project, or Normalizer

Direct grep of the deployed script for every file-open/write call found exactly one write operation
(to the output report path above) and one read operation (the canonical Master, opened `"rb"`,
read-only). `vs`, `sfmApp`, and `sfmClipEditor` are never imported. No call to `self.rebuild`,
`SetVisible`, `AddControl`, `CreateControlGroup`, `RemoveChild`, `AddChild`, or any other native
mutation primitive appears anywhere in the file. No `Save`/`SaveAs`-family call appears anywhere in
the file. The frozen production Normalizer (`Rebuild_Control_Groups_Normalizer.py`) is never
imported, read, or referenced by this script at all.
