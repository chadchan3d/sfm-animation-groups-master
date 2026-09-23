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
PASS. (2) Regression `test_f1_r2_diagnostic_regression.py` (SHA-256
`f35f07fd10ba4523501c3940d68411954d1e228bab659ab8427160507c3e7531`,
**repaired 2026-09-23, attempt 03** after attempt 02's real-SFM reopen
failure) proves, using **injected fake `sfmApp`/`vs` modules** (no real SFM
environment available offline): the core safety invariant of
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
delta, per-run delta) is verified correct against worked examples. A
strict-binding regression (attempt 01's own repair) using a fake
`SaveToFile` that mimics the real SWIG binding's own type strictness
(rejects `unicode`, matching the exact real `TypeError` observed) —
independently confirmed, via direct replay of the pre-repair function body
against this same strict fake, that it reproduces the EXACT real failure,
and that the repaired function body passes cleanly, receiving a Python 2
`str` (not `unicode`) at the native call. **New this repair (attempt 03)**:
checks confirming the real `SAVE_AS_FILENAME` literal, extracted directly
from the Phase 1 source, ends in `.dmx` (not `.sfm`) and differs from the
known original fixture filename `testscripts.dmx`; and a machine-verified
confirmation that Phase 2 contains no runtime filename gate (no
`GetFileName()` call anywhere in its source), so it correctly required no
changes. **40/40 PASS** under the real embedded Python 2.7.5 (30 attempt-01
baseline + 5 strict-binding + 5 new extension-repair assertions). Not yet
rerun against real SFM.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256 (invoked
  twice, once per phase): `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Required final All-Shots aggregate hash: `299cbba30634da1a4949ed7b14187b813260c533dced3d1e71149ede98c124e7`
- Save-As target filename (**corrected 2026-09-23, attempt 03** -- see
  "Attempt 02 disposition and repair" below; supersedes the original
  `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.sfm`, which SaveToFile wrote
  successfully but SFM's own session loader could not reopen):
  `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx`
- Phase 1 script SHA-256 (**repaired 2026-09-23, attempt 03** -- extension
  fix only; supersedes attempt 02's own
  `d938f878608b0cbd9302620265da9c47161abfbc8382308ad504bfb6fcea5d54`,
  which itself superseded the original
  `860c2c3f0b211ec1dbbae384f8249ead5f5530b54eab3f8fbf9de083e67b9ccd`):
  `2c5daa5996b688b1d835585bf91c22f30f38386b7cdd4777862a9df679534a22`
- Phase 2 script SHA-256 (**unchanged since original preparation** -- not
  modified by either the attempt-01 or attempt-02 repair; it has no
  runtime path/filename gate for either repair to update):
  `03249bad2a7f86cfbdc6e226edeb72ea6f15f9769b135d1ad46cc6a6e4ce4f80`
- Offline regression SHA-256 (**repaired 2026-09-23, attempt 03** -- adds
  the extension-repair checks; supersedes attempt 02's own
  `aa79b9e768f7c11383923334645f0b2bda3b73f39a2dbcb63c1b4cdf792c59cb`,
  which itself superseded the original
  `99a6f08da9955c4199f82ae0efac1fb936034de54fd8859e0b6ae1a6b21a78dd`):
  `f35f07fd10ba4523501c3940d68411954d1e228bab659ab8427160507c3e7531`

## Attempt 01 disposition and repair

**F1-R2 Phase 1 attempt 01 — INCOMPLETE: SAVE-AS DIAGNOSTIC BINDING FAILURE.**
Not a production failure -- production's own All-Shots run completed cleanly
(SHA/fixture/native-guard/native-Rebuild/`FINAL_REPORT_ENTRY`/authority
checks all passed; `save.succeeded = False` was the only failed condition).
Root cause (confirmed against the SWIG stub `vs/datamodel.py` and the
proven real usage in `cleanEmptyControls.py`, not assumed): `SaveToFile`'s
`pFileName` argument is declared `char const *`, which requires a Python 2
`str` (byte-string); `target_path` was `unicode` (Python 2's `os.path.join`
promotes `str`+`unicode` -> `unicode`, and `SAVE_AS_FILENAME` is an explicit
`u"..."` literal). Repaired by encoding `target_path` to ASCII bytes
immediately before the native call only -- the destination filename,
production execution, memory/resource instrumentation, save timing, and
Phase 2 are all unchanged. See `Checkpoint_F1_R2_Phase1_Create_Normalized_
Copy.py`'s own `save_normalized_diagnostic_copy()` docstring for the full
technical account, and `test_f1_r2_diagnostic_regression.py`'s
"Strict-binding regression" section for the offline proof (a fake that
mimics the real binding's own type strictness, confirmed via direct
replay to raise the EXACT observed error against the pre-repair code, and
to pass against the repaired code).

Attempt 01's resource evidence remains valid (production ran cleanly) but
its classification remains unresolved -- the save/reopen boundary was never
reached, so no `SCENE_RESIDENT` / `PER_RUN_NATIVE_RETENTION` / `MIXED`
attribution can be made yet:

- CP0 private: 3,064,614,912 -> FINAL_REPORT_ENTRY private: 3,327,598,592
- CP0 free VAS: 527,847,424 -> FINAL free VAS: 288,116,736
- CP0 largest free block: 299,696,128 -> FINAL largest free block: 126,353,408
- After-production `gc.collect()` pagefile usage remained ~3,328,004,096

This is same-process command-interval evidence only, consistent with (but
not proof of) F1-2's own already-established finding -- do not infer a leak
from it.

## Attempt 02 disposition and repair

**F1-R2 Phase 1 attempt 02 — PRODUCTION PASS / SAVE PASS / REOPEN BOUNDARY
INVALID: NON-LOADABLE `.sfm` EXTENSION.** Not a production failure and not
a `SaveToFile` failure -- production completed cleanly and the str/unicode
repair worked: `SaveToFile` succeeded and wrote the new file. The resulting
artifact could not be reopened, because the diagnostic saved it as
`F1_R2_NORMALIZED_DIAGNOSTIC_COPY.sfm` -- SFM's own session loader expects
the disposable qualification session's own extension, `.dmx` (matching the
original fixture, `testscripts.dmx`). Repaired by changing only
`SAVE_AS_FILENAME`'s own extension from `.sfm` to `.dmx` -- same directory,
same `SaveToFile` call, same Python-2 byte-string conversion repair from
attempt 01, same production execution, same resource instrumentation, same
save timing, same existence/size checks, same original-fixture protection.
Phase 2 was inspected and confirmed to contain no runtime gate on the
currently-open document's own path or filename (no `GetFileName()` call
anywhere in its source) -- there was no literal for this repair to update,
so Phase 2 is untouched, byte-for-byte identical to its original
preparation (still SHA-256 `03249bad...`). Offline-verified: the existing
regression suite re-run in full, plus new checks confirming (1) the real
`SAVE_AS_FILENAME` literal, extracted directly from the Phase 1 source, now
ends in `.dmx`; (2) it differs from the known original fixture filename
`testscripts.dmx`; (3) the strict-binding regression (reused from attempt
01's own repair, now exercised with the `.dmx` filename) still confirms
`SaveToFile` receives a Python 2 `str`, not `unicode`; (4) Phase 2 contains
no runtime filename gate, confirmed by direct source inspection rather than
assumed. **40/40 PASS** under the real embedded Python 2.7.5. Attempt 02's
real resource evidence remains valid same-process evidence, but Phase 2
attribution remains unresolved -- the saved artifact could not be reopened
through normal SFM session loading, so the save/reopen boundary was never
reached. Attempt 03 (below) reruns Phase 1 with the extension repair in
place; if the resulting `.dmx` file reopens normally, Phase 2 proceeds and
this same evidence class will be re-collected as part of a complete
attempt.
