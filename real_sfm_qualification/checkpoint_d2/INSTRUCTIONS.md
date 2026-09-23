# Checkpoint D2-2 — Integrated (Post-Integration) All-Shots Equivalence Run (corrected)

## D2-2 CORRECTION NOTICE (2026-09-22)

D2-1's real run proved full **runtime/equivalence PASS**: all 44 mechanical checks, all six comparisons
(A-F), a clean authority lifecycle, and native-protection evidence all passed, with zero anomalies. The
Normalizer itself did not fail. **Preserve these findings permanently** — see LEDGER.md's D2-1 row.

But the **qualification artifact** failed. The complete D2 artifact write reached temp-file verification,
then: `temp file reopen/reparse verification failed: MemoryError()`. The SFM process was already around
3.43GB working set. Root cause: D2-1's writer attempted to persist a full ~9MB duplicate copy of D2's own
85+85 raw captured fingerprints purely to prove equivalence to D1 — unnecessary, since D2 already computes
qualified semantic fingerprints and per-target hashes, and D1's own complete historical raw artifact
remains separately preserved and SHA-pinned.

A degraded fallback survived and was externally parseable, but a real semantic defect was also found in
it: the authoritative summary correctly said `OVERALL_PASS=False`, but the degraded fallback JSON itself
contained `overall_pass: true`. Root cause (confirmed by direct code review): `degraded_report =
dict(report)` took a **snapshot** of the live `report` object at a point where `report["overall_pass"]`
could still hold a stale `True` value from an earlier (successful) write attempt — the correction to
`False` ran only *after* that snapshot had already been written to disk. A degraded/fallback artifact must
never claim qualification PASS.

**What changed in D2-2:**

1. The artifact **no longer persists D2's own raw 85-target PRE/POST fingerprint dicts** (or the 78-target
   excluded witness rows) — only their already-computed per-target HASHES (the same qualified
   `per_target_hash()` D1's own compact manifest uses). The artifact shrinks from ~9MB to tens of KB.
2. A new `hash_of_hashes()` checksum lets round-trip (serialize-then-reparse) fidelity of the STORED
   per-target hash maps be verified independently, without ever needing the raw fingerprint content
   present at verification time.
3. If (and only if) a per-target mismatch is ever found, the raw semantic fingerprint for JUST the
   mismatching target(s) is preserved in `report["mismatch_diagnostics"]` as diagnostic evidence — the
   common (all-match) case stays compact; a genuine divergence still carries enough raw evidence to
   diagnose.
4. The degraded-fallback path now **explicitly forces** `degraded_report["overall_pass"] = False` and
   `degraded_report["artifact_write_verified"] = False`, independent of whatever the live `report` object
   held at snapshot time. A degraded/fallback artifact can never again claim PASS.
5. A `provenance` section (production Normalizer/Master SHA, authority API/build, D1 artifact/manifest
   SHA) and per-command timing (`command_duration_seconds`) were added, per the governing brief's explicit
   compact-artifact field list.

**Historical Normalizer invocation, fingerprint semantics, fixture/starting-state gates, runtime
comparison logic, and native-protection logic remain completely unchanged from D2-1** — this is an
evidence-persistence correction only. See "Source review" below.

## Preserved D2-1 findings (not overwritten — see LEDGER.md)

All 44 mechanical checks PASS; starting PRE exactly `eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0`;
integrated POST exactly `299cbba30634da1a4949ed7b14187b813260c533dced3d1e71149ede98c124e7`; exact D1
changed-set parity (57) and unchanged-set parity (28); 85/85 eligible POST parity; 78/78 excluded parity;
zero target additions/removals/reclassifications; broker READY/canonical; outstanding leases = 0; current
providers = 0; provider opens/closes = 1/1; native guards PASS; native Rebuild returned PASS; production
revision marker present; zero runtime anomalies. Selected-Shots and All-Shots historical-vs-integrated
equivalence are closed on the strength of these runtime findings (Checkpoint D2's own qualification
artifact needed the D2-2 correction below to actually publish them safely).

## THIS CHECKPOINT MUTATES THE SCENE

Like C2, D2 **does** mutate the disposable qualification project. It invokes the REAL, INSTALLED,
ACCEPTED, INTEGRATED production Normalizer — never a copy, never the historical baseline D1 used —
running its own real **All Shots** behavior, unmodified.

**Do not save afterward.**

## Purpose

Mechanically prove the integrated (post-Production-Normalizer-Integration) All-Shots outcome is
semantically equivalent to Checkpoint D1-3's own already-accepted historical baseline outcome — the same
role Checkpoint C2 played for Selected Shots vs C1. Unlike C2, D2 never loads D1's own full ~5.9MB JSON
artifact into memory: D1-3 itself proved this 32-bit qualification-harness process approaches its memory
ceiling (peak working set ~3.42GB during D1-3's own single-capture run), so D2 compares against a
**compact, immutable, SHA-256-pinned manifest** (~40KB, containing only per-target hashes, never D1's raw
captured data).

## 0. The compact D1 comparison manifest

`real_sfm_qualification/checkpoint_d2/build_d1_manifest.py` is an **offline, non-SFM tool**. It reads the
real, accepted Checkpoint D1-3 JSON artifact from disk, verifies its SHA-256 and internal consistency
(85 eligible + 78 excluded targets, exact 57/28 changed/unchanged split, empty target-set diff), computes
a canonical per-target hash for every eligible and excluded target (`SHA-256` of that target's own
`sort_keys=True` JSON serialization), and writes a compact manifest containing:

- the D1 artifact's own SHA-256 (`55cd0447...`);
- `d1_overall_pass` (must be `True`);
- D1's own PRE/POST aggregate hashes;
- the exact 85-target eligible key set, the exact 57-target changed set, the exact 28-target unchanged
  set;
- a per-target PRE hash and a per-target POST hash for each of the 85 eligible targets;
- the exact 78-target excluded key set, plus a per-target PRE hash and per-target POST hash for each;
- the excluded-changed set (empty);
- target-set-diff expectations (all empty: no missing/new/reclassified targets);
- fixture totals and source identities (historical baseline, production Normalizer, canonical Master
  SHA-256s at the time D1-3 ran);
- manifest format/build identity.

The manifest itself is then pinned with its own SHA-256 (`64917b46...`) and deployed alongside the D2
script at `usermod\scripts\sfm\mainmenu\ChadChan3D\_qualification_manifests\d1_comparison_manifest.json`.
D2's own runtime loads **only this 40KB file** — it never `json.load()`s D1's own full artifact. If that
full artifact is still physically present at its expected path, D2 optionally verifies its identity via a
**streaming** SHA-256 (constant memory, the file's content is never parsed) as additional provenance —
this is not required for D2 to proceed; the pinned, self-contained manifest is the load-bearing gate.

This tool has already been run once, offline, against the real accepted D1-3 artifact (21/21 internal
checks PASS, manifest reopens/reparses correctly) — see "Offline verification already performed" below.
It does not need to be rerun unless D1 itself is ever rerun and produces a new accepted artifact.

## 1. What D2 actually does (non-interactive parts)

1. Verifies the SHA-256 of the file it is **about to execute** — `cdc909a6...` — the accepted, installed,
   integrated production Normalizer.
2. Verifies the canonical Master's SHA-256 (`ac45e5c1...`).
3. Loads and integrity-verifies the compact D1 comparison manifest (SHA-256 pinned); verifies
   `d1_overall_pass`, D1's own PRE/POST hashes, and the manifest's own internal counts (85/78/57/28).
4. If the full D1-3 artifact is still physically present, verifies its identity via a streaming SHA-256
   (soft check, recorded as evidence, not hard-gated).
5. Independently re-derives the Checkpoint-B-style fixture witness fresh from the live document and
   cross-checks it against fixed structural totals (15/163/85/78/22/21) AND the manifest's own eligible/
   excluded target key sets.
6. Captures a structural PRE fingerprint of all 85 eligible targets and a lightweight structural witness
   of all 78 excluded targets, computing a per-target hash for each via the same canonical
   `per_target_hash()` the manifest builder used.
7. **Hard gate**: the integrated PRE aggregate hash must equal D1's own PRE hash exactly
   (`eac633c9...`), all 85 integrated PRE per-target hashes must match the D1 manifest's own PRE
   per-target hashes, and all 78 excluded PRE witness hashes must match the D1 manifest's own excluded PRE
   hashes. **If any check above fails, the script raises and writes its report here — it never invokes
   the production Normalizer or mutates the scene.**

## 2. What D2 needs from you (the interactive part)

After the PRE fingerprint/excluded witness are captured and the gate passes, the script executes the
installed production Normalizer. This triggers the Normalizer's own real, completely unmodified "choose
scope" dialog.

**When that dialog appears: select "All Shots" and confirm.** Do not modify or work around this dialog in
any way.

The script then waits (pumping SFM's own Qt event loop, watching for the Normalizer's own `RUN_LOCK_NAME`
completion signal) for the real, asynchronous operation to finish, before rebuilding the independent
witness fresh, capturing the POST fingerprint/excluded witness, running Comparisons A-F, capturing
shared-authority and native-protection evidence, and writing its report. **Do not interact with SFM while
it's running** — this run covers the full project and may take a while.

## Exact project to open, and required selection state

Open the **exact same disposable qualification project used for B-2/C1/C2/D1**. Selection state may
remain whatever it currently is — All-Shots scope does not depend on it, and the script does not gate on
it. What **is** required is that the project's *content* matches the original fixture exactly (Checkpoint
D1-3's own mutation must be discarded by restarting SFM without saving) — the script mechanically
verifies this via the PRE-hash gate above and aborts before touching anything if it does not match.

## Comparisons performed (A-F)

| | Comparison | What it checks |
|---|---|---|
| A | `starting_state_parity` | integrated PRE aggregate hash == D1 PRE hash, AND 85/85 individual PRE target hashes match the D1 manifest (also the hard gate) |
| B | `scope_parity` | integrated changed-target set exactly equals D1's 57-target changed set; integrated unchanged-target set exactly equals D1's 28-target unchanged set — full SET equality, never just counts |
| C | `final_state_parity` | integrated POST aggregate hash == D1's own historical POST hash (`299cbba3...`) |
| D | `per_target_parity` | ALL 85 eligible targets' POST hashes compared individually against the D1 manifest's own per-target POST hashes |
| E | `exclusion_parity` | ALL 78 excluded targets' structural witness hashes compared individually against the D1 manifest's own excluded POST hashes; expected excluded-changed set: `[]` |
| F | `target_set_parity` | no missing/new/reclassified targets (independently rebuilt witness vs. the D1 manifest's own eligible/excluded key sets) |

If a per-target mismatch occurs (Comparison D or E, or the PRE-side starting-state gate), the script does
**not** attempt to build an in-process structural diff object across all targets — it preserves only the
raw semantic fingerprint for the specific mismatching target(s) in `report["mismatch_diagnostics"]`
(D2-2). When every target matches (the expected, qualified case), this section stays empty and the
artifact stays compact — tens of KB, not megabytes.

## Shared-authority runtime evidence (same technique as Checkpoint C2)

Captured from the exec-exposed `authority_runtime` module binding the production Normalizer's own source
already imports, plus one additional, idempotent `get_broker()` call after the run to read
`provider_counters()`/`outstanding_lease_count()` — no new view or lease is acquired by this diagnostic
call. Expected after a completed command: broker `READY`, `is_canonical=True`, `outstanding_lease_count=0`,
`current_open_provider_count=0`, `total_provider_opens == total_provider_closes`. All five are gated
checks (`authority.*`) in the report.

## Native-protection evidence (same technique as Checkpoint C2)

Read from the production Normalizer's OWN existing log file (`OUTPUT_PATH`, opened `"w"` fresh by this
exact run). Checks for `"NATIVE_GUARDS = PASS"`, `"NATIVE_REBUILD_RETURNED = PASS"`, and the production
revision marker — all three are gated checks. This is **not** the later dedicated native-handle
coordination test.

## Memory evidence (diagnostic only, not a new production gate)

`report["memory_snapshots"]` reuses Checkpoint D1-3's own best-effort, stdlib-only (`ctypes`) process
memory snapshots at equivalent boundaries (start, before/after PRE capture, after the integrated run,
before/after POST capture, after POST hash, after all comparisons). Total SFM working set is **not** a
PASS/FAIL gate. What **is** gated: the script must complete without an unhandled exception (which would
catch a `MemoryError` exactly as it caught D1-2's) — "no harness MemoryError, no allocation failure, no
evidence loss" is enforced via the existing `completed_without_exception` check, not a new memory-size
threshold.

## Operator instructions

1. **RESTART SFM FIRST.**
2. **DO NOT SAVE the previous experimental state; restart SFM to discard it.**
3. Open the same disposable qualification project used for D1.
4. Run **`Checkpoint_D2_Integrated_All_Shots_Equivalence`**, the same way as the earlier checkpoints.
5. If any PRE/fixture/baseline-provenance gate fails, the script stops on its own — no mutation occurs.
6. **A real dialog will appear.** Select **"All Shots"** and confirm.
7. Give it generous time — this run covers the full project (85 targets fingerprinted twice plus 78
   structurally witnessed twice) plus the real integrated authority acquisition/release cycle.
8. Do not touch SFM again until the console output shows the final summary and the
   "DO NOT SAVE. Restart SFM..." message.
9. Return the exact contents of **both** output files:
   - `C:\Users\Public\Documents\sfm_checkpoint_d2_integrated_all_shots_result_summary.txt`
   - `C:\Users\Public\Documents\sfm_checkpoint_d2_integrated_all_shots_result.json`

   Also tell me about any error dialog or console traceback beyond what's in those files.
10. **DO NOT SAVE. Restart SFM afterward to discard the integrated mutation.**

## Output artifact paths

- `C:\Users\Public\Documents\sfm_checkpoint_d2_integrated_all_shots_result.json` (COMPACT — every check,
  Comparisons A-F, per-target hash maps (never raw fingerprints, except any mismatching target),
  provenance, authority/native/memory evidence, anomalies — tens of KB, not megabytes)
- `C:\Users\Public\Documents\sfm_checkpoint_d2_integrated_all_shots_result_summary.txt` (concise, read
  this first)

D1's own full artifact is never duplicated into D2's output, and (D2-2) neither is D2's own raw
85-target fingerprint capture — only per-target hashes, and only the raw content for any specific
mismatching target.

## Mechanical D2 PASS criteria (decided before execution)

`OVERALL_PASS` in the report requires **all** of:

- production Normalizer SHA matches the accepted integration exactly; canonical Master SHA unchanged;
- the D1 comparison manifest's own SHA-256 matches the pinned value, and its internal consistency checks
  pass (`d1_overall_pass=True`, correct 85/78/57/28 counts);
- fixture identity matches the required totals exactly, AND the live eligible/excluded target key sets
  exactly match the D1 manifest's own key sets;
- integrated PRE aggregate hash equals D1's own PRE hash exactly, AND all 85 individual PRE per-target
  hashes match the D1 manifest, AND all 78 excluded PRE witness hashes match the D1 manifest (Comparison
  A / the starting-state gate) — **a mismatch anywhere above means the script already stopped; no
  mutation occurred, and none of the checks below apply**;
- the integrated run was actually started (dialog confirmed with All Shots, not cancelled) and completed
  within the wait timeout;
- Comparisons B, C, D, E, F each report `"pass": true` (exact 57/28 set equality for B; exact aggregate
  hash equality for C; 85/85 individual equality for D; 78/78 individual equality with an empty excluded-
  changed set for E; zero missing/new/reclassified for F);
- authority lifecycle is clean (broker `READY`, canonical, zero outstanding leases, zero currently open
  providers, opens/closes balanced);
- native-protection log evidence shows both guard/rebuild markers `PASS`;
- the COMPACT JSON evidence artifact itself was written, is nonzero, reopens and reparses, contains every
  required evidence key, and its own stored per-target hash maps recompute a matching `hash_of_hashes()`
  checksum after round-trip (`artifact_write_verified=True`);
- the script completes without an unhandled exception (no harness `MemoryError`, no allocation failure);
- zero unresolved anomalies.

A degraded/fallback artifact (written only if the complete compact artifact write itself somehow still
fails) can **never** report `overall_pass=True` or `artifact_write_verified=True` — both are forced
`False` explicitly (D2-2), regardless of what the live report object held at the moment of the fallback.

If the report shows `"gate_failure": true`, that means a pre-flight, manifest-integrity, fixture, or
starting-state check failed and the script correctly stopped before touching anything.

## Source review: only artifact-persistence changed; historical/production Normalizer semantics are untouched

Direct grep of the D2 script for every file-write confirms exactly two `"wb"` (write) operations in the
entire script — the two report files listed above — and no code path opens the production Normalizer, the
canonical Master, the D1 manifest, or the D1 artifact for writing; each is opened only in `"rb"`
(read-only) mode. The historical baseline file is never referenced by this script at all. `sfm_master_
authority_productionized`/`sfm_master_sidecar` are never imported directly — only read via the module
bindings the production Normalizer's own source already imports into the isolated `exec()` namespace,
identical to Checkpoint C2's own discipline. A diff against D2-1's own bytes confines every removed/
changed line to: `REQUIRED_EVIDENCE_KEYS`/`verify_artifact_evidence()` (compact schema), the new
`hash_of_hashes()` helper, the report-field assignments around PRE/POST capture (compact hashes instead
of raw dicts, plus mismatch-diagnostic capture), new `del integrated_pre_fingerprint`/`del
integrated_post_fingerprint` statements, the `provenance`/`command_duration_seconds` additions, and the
degraded-fallback's explicit `overall_pass`/`artifact_write_verified` force-False lines. No line inside
SHA verification, `build_independent_witness()`, the fixture/starting-state gate CONDITIONS, fingerprint-
function extraction, `canonicalize_snapshot()`, `capture_all()`, the production-Normalizer `exec()` call,
the dialog wait loop, or the six comparisons' own pass/fail LOGIC was removed or altered.

## Offline verification already performed

Before D2-1's deployment: (1) `build_d1_manifest.py` run once, offline, against the real accepted D1-3
artifact — **21/21 internal checks PASS**; manifest size 39,535 bytes (vs. the D1 artifact's 5,875,753
bytes — a ~149x reduction); (2) the D2 script syntax-checked under the real embedded Python 2.7.5, PASS;
(3) every `del`-based memory-hygiene point verified by direct grep.

Before this correction's (D2-2) deployment, additionally: (4) syntax-checked under the real embedded
Python 2.7.5, PASS; (5) every NEW `del`-based memory-hygiene point (`del integrated_pre_fingerprint,
pre_excluded_witness` before the Normalizer invocation; `del integrated_post_fingerprint,
post_excluded_witness` after comparisons D/E) reconfirmed by direct grep to occur only after each raw
dict's last use; (6) `test_d2_manifest_comparator_regression.py` and `test_d2_artifact_writer_regression.py`
(SHA-pin/line ranges updated for D2-2, the latter rewritten to build and verify the new COMPACT schema
rather than the retired raw-fingerprint one) reconfirmed **23/23 PASS** and **26/26 PASS** respectively;
(7) a new regression, `real_sfm_qualification/checkpoint_d2/test_d2_compact_artifact_regression.py`,
extracts `per_target_hash`/`compute_target_hashes`/`hash_of_hashes`/`compare_hash_maps`/
`write_json_atomic`/`REQUIRED_EVIDENCE_KEYS`/`verify_artifact_evidence`, and the degraded-fallback's own
force-False code block verbatim (SHA-256 pinned) and proves, using the REAL D1-3 artifact and its own real
compact manifest: the compact artifact contains exactly 85 PRE/POST eligible hashes, 78 PRE/POST excluded
hashes, and exact 57-changed/28-unchanged target identities; all six D2 comparisons (A-F) can be
mechanically reconstructed from the compact artifact's own stored hashes and match the artifact's own
recorded results; the artifact serializes/reopens/reparses and stays under 2MB (in practice tens of KB);
`verify_artifact_evidence()` PASSES on the unmutated artifact; a deliberate mutation of one eligible
per-target hash, one excluded per-target hash, or the removal of one target's hash entirely each cause
`verify_artifact_evidence()` to correctly FAIL; and — the exact D2-1 bug, now proven fixed — the degraded-
fallback code path's own `overall_pass`/`artifact_write_verified` force-False lines produce `False` even
when fed a synthetic source `report` that itself claims `overall_pass: True` — **37/37 PASS**, all under
the real embedded Python 2.7.5. Not yet run against real SFM.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256 (the file this checkpoint executes):
  `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- D1-3's own accepted artifact SHA-256: `55cd0447f3d215afaa4fa334b1daf2d905055363972ead524672da822ed6e85f`
- D1 compact comparison manifest SHA-256: `64917b46896ced079bfc68e777d7e7c250e3875230a477ece1cb9320b0d4e42f`
- Required PRE aggregate hash (D1's own accepted value): `eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0`
- Required POST aggregate hash (D1's own accepted, historical value): `299cbba30634da1a4949ed7b14187b813260c533dced3d1e71149ede98c124e7`
- D2-2 (corrected) script SHA-256: `8ec19a30de8d0951563ce1a583ce2f3c71e4d9d8c77a55f31359653b709d0d34`
  (D2-1's superseded script SHA-256, preserved for the record: `61e45da0526ce37d56e5c04c8f9932122a8ce88855da14fc3ad5acf92b2d35ab`)
