# Checkpoint F1-R2 — Scene-Resident vs. Per-Run Native-Retention Attribution

## Why this exists

F1-2's confirmed evidence showed production's own **All-Shots command 3**
growing ~227.32 MiB private / losing ~222.44 MiB free VAS / ~105.88 MiB
largest-contiguous-block **within its own single production run** (its own
`CP0_COMMAND_START` vs its own `FINAL_REPORT_ENTRY`) — this is
production-internal, not harness-caused (F1-2 had already eliminated the
harness's own whole-85-target capture that F1-R1 identified). Command 4
then produced no completed record at all. A production-internal static
audit (`../checkpoint_f1_2/F1-2_PRODUCTION_INTERNAL_STATIC_AUDIT.md`)
traced the primary candidate — `self.work`'s own live `aset`/`game_model`
native DME references, held for the whole command by architectural
necessity — but could not, by static reading alone, determine whether the
growth is:

- **(A) SCENE_RESIDENT** — the first All-Shots run legitimately makes the
  scene itself bigger/more complex; this growth would already be baked
  into a saved, reloaded copy.
- **(B) PER_RUN_NATIVE_RETENTION** — growth that is an artifact of running
  Rebuild itself, that would recur on every run regardless of prior
  normalization state.
- **(C) MIXED** — both contribute.

F1-R2 is a two-phase diagnostic designed to separate these empirically.

## THIS IS AN INTENTIONAL EXCEPTION TO "DO NOT SAVE"

Phase 1 performs a genuine `Save As` to a **new** file. **It never
overwrites or re-saves the original disposable qualification fixture.**
The save target is computed from the original fixture's own directory
(via `vs.g_pDataModel.GetFileName()`) plus a fixed new filename
(`F1_R2_NORMALIZED_DIAGNOSTIC_COPY.sfm`); the script explicitly refuses to
call the native save API at all if the computed target path would ever
equal the original path (verified by an offline regression test using
injected fakes — see below).

## Phase 1 — create normalized diagnostic copy

Script: `Checkpoint_F1_R2_Phase1_Create_Normalized_Copy.py`

1. From a fresh SFM process, open the **original** disposable
   qualification fixture.
2. Run the script. It records idle process memory/VAS, then runs
   production **All Shots once** with the lightest possible harness — no
   external whole-85 semantic capture, no D1/D2-scale verification, only
   production resource checkpoints, authority lifecycle, provenance (SHA
   checks), and a bounded structural witness (totals/counts only).
3. Requires production completion; records `FINAL_REPORT_ENTRY`
   memory/VAS (parsed from production's own log, same technique as
   F1-R1/F1-2).
4. Saves the resulting normalized scene to
   `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.sfm` (same directory as the
   original), via `vs.g_pDataModel.SaveToFile(new_path, None, "binary",
   format_name, root)` — a real Save-As call with an arbitrary target
   path, confirmed against the bundled `vs/datamodel.py` SWIG stub and a
   real usage example in `sdktools/python/global/Scripts/
   cleanEmptyControls.py`.
5. Records the saved file's path, size, and save success/failure.
6. Writes evidence incrementally (rolling `write_json_atomic()` after
   every phase within this script), so a crash does not lose everything.
7. **Do not run Phase 2 from this same SFM process.**

## Phase 2 — fresh-process normalized-copy retest

Script: `Checkpoint_F1_R2_Phase2_Normalized_Copy_Retest.py`

1. **Fully restart SFM.**
2. Open **only** the normalized diagnostic copy Phase 1 created — never
   the original fixture.
3. Run the script. It records this fresh process's own idle memory/VAS,
   and reads Phase 1's own evidence file back from disk (if present) to
   compute the **serialized/resident** comparison automatically.
4. Records fixture identity/counts via the same bounded witness (totals
   should match 85/78/163/15/22/21 — same targets, now normalized).
5. Runs production **All Shots once** again, against the already-
   normalized scene, with the same lightweight evidence discipline as
   Phase 1. Records `CP0_COMMAND_START`/`FINAL_REPORT_ENTRY` (working
   set, private/pagefile, free VAS, largest free block) — the **per-run**
   comparison component.
6. Requires production internal gates and clean authority lifecycle.
7. **Only after** that run, performs the **one** full external 85-
   eligible/78-excluded semantic verification: aggregate must equal
   `299cbba30634da1a4949ed7b14187b813260c533dced3d1e71149ede98c124e7`, 85
   eligible identities exact, 78 exclusions exact, no drift.
8. **Does not run another production command after the heavyweight final
   verification.**

## Required comparison (computed by Phase 2, reported raw — not auto-classified)

- **Serialized/resident component**: Phase 2's own fresh-process idle
  baseline (after loading the normalized copy) minus Phase 1's own idle
  baseline (before its first All-Shots run, against the original
  fixture). Large ⇒ growth is baked into the saved scene itself.
- **Per-run component**: Phase 2's own production `CP0_COMMAND_START` vs
  `FINAL_REPORT_ENTRY`. Large (comparable to F1-2's original ~227 MiB) ⇒
  native/allocator per-run retention, since this run is against an
  already-normalized (idempotent) scene.

**The script deliberately does not compute a classification verdict
itself** — no arbitrary percentage threshold is hardcoded. It reports the
raw numeric deltas; `SCENE_RESIDENT_DOMINANT` / `PER_RUN_NATIVE_RETENTION_
DOMINANT` / `MIXED` / `INCONCLUSIVE` is applied by the reviewing analyst
from those numbers, explained numerically, once the real run's evidence
is returned.

## Operator instructions (exact sequence)

**Phase 1:**
1. From a fresh SFM process, open the **original** disposable
   qualification fixture (never a copy).
2. Run `Checkpoint_F1_R2_Phase1_Create_Normalized_Copy`.
3. Choose **All Shots** in the real dialog that appears.
4. Wait for completion. The script saves the new diagnostic copy itself —
   no manual Save action needed.
5. Return the three Phase 1 output files (see below).
6. **Fully restart SFM** (do not run Phase 2 in this same process).

**Phase 2:**
7. Open **only** the new file `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.sfm` —
   never the original fixture.
8. Run `Checkpoint_F1_R2_Phase2_Normalized_Copy_Retest`.
9. Choose **All Shots** in the real dialog that appears.
10. Wait for completion.
11. Return the three Phase 2 output files.
12. **DO NOT SAVE after Phase 2. Restart SFM afterward.**

## Output artifacts

Phase 1:
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r2_phase1_result.json`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r2_phase1_result_summary.txt`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r2_phase1_production_log.txt`

Phase 2:
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r2_phase2_result.json`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r2_phase2_result_summary.txt`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r2_phase2_production_log.txt`

## Static audit performed alongside preparation

`../checkpoint_f1_2/F1-2_PRODUCTION_INTERNAL_STATIC_AUDIT.md` (written
before this diagnostic's scripts) traces production's own
`RebuildControlGroupsProductionRun`'s per-shot/per-target state for
anything whose lifetime scales with completed targets/shots and survives
through `FINAL_REPORT_ENTRY`: `self.work` (built once via
`snapshot_work()`, never shrunk) holds live native `aset`/`game_model` DME
references for every eligible target simultaneously, for the whole
command — architecturally necessary, not itself a bug, but the direct
candidate for whichever hypothesis (A/B/mixed) F1-R2's own empirical
comparison points to. Every other candidate attribute
(`production_terminal_results`, `production_mixed_direct_by_target`, the
per-target pair-sets, `gate_mdl_cache`) was traced and found bounded/small.
No production code was changed based on this audit alone.

## Offline verification performed before deployment

(1) Both scripts syntax-checked under the real embedded Python 2.7.5,
PASS. (2) New regression `test_f1_r2_diagnostic_regression.py` (SHA-256
`99a6f08da9955c4199f82ae0efac1fb936034de54fd8859e0b6ae1a6b21a78dd`) proves,
using **injected fake `sfmApp`/`vs` modules** (no real SFM environment
available offline): the core safety invariant of
`save_normalized_diagnostic_copy()` — it calls the native `SaveToFile` API
exactly once when the computed target path correctly differs from the
original fixture's path (and the original file's bytes remain provably
unchanged afterward), and **never calls it at all** when the computed
target would equal the original path (an adversarial case constructed
deliberately), reporting a clean refusal instead. Also proves a native
`SaveToFile` failure is reported cleanly, not swallowed or misreported as
success. The shared `CONTEXTUALIZER_RESOURCE_CHECKPOINT` parser exactly
reproduces F1-2's own confirmed command-3 deltas (private `+238366720`,
free VAS `-233242624`, largest free `-111017984`) from the real log-line
values. The Phase 1↔Phase 2 comparison arithmetic (serialized/resident
delta, per-run delta) is verified correct against worked examples.
**30/30 PASS** under the real embedded Python 2.7.5. Not yet run against
real SFM.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256 (invoked
  twice, once per phase): `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Required final All-Shots aggregate hash: `299cbba30634da1a4949ed7b14187b813260c533dced3d1e71149ede98c124e7`
- Phase 1 script SHA-256: `860c2c3f0b211ec1dbbae384f8249ead5f5530b54eab3f8fbf9de083e67b9ccd`
- Phase 2 script SHA-256: `03249bad2a7f86cfbdc6e226edeb72ea6f15f9769b135d1ad46cc6a6e4ce4f80`
- Offline regression SHA-256: `99a6f08da9955c4199f82ae0efac1fb936034de54fd8859e0b6ae1a6b21a78dd`
