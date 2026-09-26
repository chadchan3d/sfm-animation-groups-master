# Checkpoint J — Native Protected-Handle Qualification

## Purpose

Prove, in real SFM, the actual Windows sharing semantics of production's existing Master-protection
handle (`native_master_protect_acquire` / `native_master_protect_release`,
`Rebuild_Control_Groups_Normalizer.py` lines ~356-413): a short-lived `CreateFileW` handle opened with
`GENERIC_READ` / `FILE_SHARE_READ` only (never `FILE_SHARE_WRITE`, never `FILE_SHARE_DELETE`) /
`OPEN_EXISTING`, held across the protected Master hash check (`assert_master_stable` ->
`sha256_stream`), native Rebuild (`self.rebuild`), and contextual reconciliation
(`production_generic_composer`), released in `run_target_transaction`'s own `finally`
(`Rebuild_Control_Groups_Normalizer.py` lines ~11837-12465).

This checkpoint does **not** modify production. It `exec()`s the pinned, SHA-256-verified production
bytes into a fresh namespace (the same technique every earlier checkpoint in this project already uses —
see Checkpoint O2/Checkpoint I) and monkey-patches five call points in that IN-MEMORY namespace only. Every
wrapper calls the ORIGINAL function/method with the SAME arguments and returns its SAME, unmodified return
value — only recording timing/matrix metadata around the call. See the checkpoint script's own docstring
and `J_MECHANICAL_GATES.md` for the full instrumentation design.

**Round 1 correction**: `self.rebuild` is wrapped via an **instance-attribute** patch, located immediately
after `exec()` returns via the same `main_window.findChildren(QtCore.QObject)` + `objectName() ==
RUN_LOCK_NAME` technique every earlier checkpoint's own wait-loop already uses — **never** a class-level
`prepare_native_callback` patch (which reproduces the exact defect documented in
`checkpoint_o2_r1/O2_R1_NATIVE_TIMING_CORRECTION.md` for Checkpoint O2's own original native-Rebuild wrap:
production's own top-level code synchronously constructs the run instance and assigns the real
`self.rebuild` *before `exec()` itself returns*, so a class-level patch installed afterward is always too
late).

**Round 2 correction**: a raised exception in this script's own outer control flow, after `exec()` has
already returned, is **not** a safety mechanism — by that point production has already constructed the run
and scheduled its Qt-deferred target callback via the ambient SFM Qt event loop, which this script neither
owns nor can stop merely by raising in its own frame. The real prevention mechanism is now
`install_run_target_transaction_guard()`: a class-level wrap of `run_target_transaction` itself, installed
as the **first** post-exec instrumentation action, which raises **inside production's own real call chain**
— never calling the original method at all — for as long as `instrumentation_ready` is not `True`.
`instrumentation_ready` only becomes `True` after run-instance discovery, the `self.rebuild` instance wrap,
all four module-level wraps, **and** the exact workload-identity gates below have all succeeded. The
workload itself (fixture, project, shot, target, Clip Editor selection, run instance scope, production's own
completed log) is now mechanically pinned at three independent layers — see below — so a correct protection
matrix observed on any *other* workload cannot reach `J_PASS`.

**Round 3 corrections** (narrow, architecture-preserving): (1) the J1 baseline probe matrix must ALSO have
every successfully-opened handle actually closed (`matrix_all_probe_handles_closed()`) — a hard
pre-production gate, since a leaked baseline WRITE/DELETE probe handle could itself conflict with
production's own subsequent protection handle. (2) Production's own protected path/generation is now
mechanically bound to the canonical Master: `run_instance.master_path`/`run_instance.master_hash` (both real
instance attributes, set synchronously inside `derive_paths()` before `exec()` returns) must match the
canonical Master path/SHA-256 exactly, and the final verdict independently re-confirms the one successful
`protect_acquire` event's own path and `state["protected_path"]` are that SAME canonical path
(`protected_path_is_canonical_master`) — closing the gap where the file this harness hashed and the file
production actually protected were only assumed to be the same. (3) `validate_event_order()` now uses
PURELY ORDINAL (append-list-index) positions, never wall-clock timestamps, and requires each kind to occur
**exactly once** (not merely "at least once, first match wins"). (4) `run_instance.work` is now a HARD
requirement (exactly one shot/target record) — an earlier "if available, soft pass when empty" allowance is
removed, since production's own `start()` always constructs `self.work` synchronously before `exec()`
returns for this exact workload.

**Explicitly NOT tested by J**: scope (All Shots / multi-target), generation switching (that is `I`,
PASS/CLOSED), repeated/warm-path use, or vocabulary behavior. The workload is intentionally exactly ONE
target.

**Do not save afterward.**

## Workload — mechanically pinned at three independent layers

- Fixture: `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx` (already-qualified, reused; never `testscripts.dmx`),
  independently resolved via `sfmApp.GetDocumentRoot().GetFileId()` -> `vs.g_pDataModel.GetFileName()` —
  never assumed from shot names alone.
- **Layer 1 (pre-production, before `exec()`)**: exactly 15 project shots; `shot9` resolves uniquely; its
  sole animation set is exactly `krystalv21`; `sfmClipEditor.GetSelectedShots()` shows exactly one selected
  shot, canonically (native-pointer-identity) matching the resolved `shot9`. **The operator selects `shot9`
  in the Clip Editor before invoking this checkpoint** — the real scope dialog that appears when the
  checkpoint runs only chooses **Selected Shot(s) vs. All Shots**; it does not select a shot.
- **Layer 2 (post-exec, on the already-constructed run instance, before `instrumentation_ready` can become
  `True`)**: `run_instance.master_path`/`run_instance.master_hash` match the canonical Master path/SHA-256
  exactly; `run_instance.scope_mode == u"SELECTED_SHOTS"`; exactly one `run_instance.scope_shots` entry,
  canonically matching the preflight `shot9`; and `run_instance.work` is exactly one shot record (`shot9`)
  with exactly one target (`krystalv21`) — a HARD requirement, never a soft pass when empty/absent.
- **Layer 3 (post-run, from production's own completed log)**: exact `scope_mode=SELECTED_SHOTS
  scope_shots=1` and exact `CONTEXTUALIZER_SCOPE_SHOT_NAMES = [u'shot9']`; exactly one
  `PRODUCTION_PRE_CAPTURE_GATE` line, for exactly `shot9`/`krystalv21`; exactly one
  `NATIVE_REBUILD_RETURNED = PASS` line.

## Sequence

1. **RESTART SFM FIRST.**
2. **DO NOT SAVE any previous experimental state; restart SFM to discard it.**
3. Open the established disposable qualification fixture (the same project every earlier checkpoint has
   used).
4. In the Clip Editor, select `shot9` and no other shot.
5. Run `Checkpoint_J_Native_Protected_Handle`.
6. If the pre-flight SHA / fixture / Clip-Editor-selection / J1-baseline-probe-and-handle-hygiene gate
   fails, the script stops on its own — no production invocation occurs. Report the failure; **restart SFM**
   before another attempt; do not re-run without understanding why.
7. Choose **Selected Shot(s)** in the real dialog that appears (this dialog chooses Selected Shot(s) vs. All
   Shots only — `shot9` itself was already selected in step 4). By the time control returns to the script,
   the command's construction/setup has already completed synchronously: the script immediately installs the
   fail-closed `run_target_transaction` guard, locates the run instance and wraps its `self.rebuild`, checks
   the exact workload-identity gates against that instance, and only then allows the real per-target
   transaction to proceed.
8. Do not alter the scene while the command runs.
9. Wait for the command to complete (the script polls the real run-lock marker itself; you do not need to
   watch the console).
10. Return the three output files (see below).
11. **DO NOT SAVE. Restart SFM afterward to discard the experimental state.**

## Output artifacts

- `C:\Users\Public\Documents\sfm_checkpoint_j_result.json` — the full evidence artifact (checks, events,
  state, context, `j_verdict`, `j_failed_checks`, `failure_phase`), written atomically.
- `C:\Users\Public\Documents\sfm_checkpoint_j_result_summary.txt` — concise, read this first.
- `C:\Users\Public\Documents\sfm_checkpoint_j_production_log.txt` — a byte-for-byte preserved copy of
  production's own log for this command.

## Mechanical PASS criteria (decided before execution — see `classify_j_verdict()` in the script itself,
offline-regressed against all 29 named gates individually forced to fail)

A HARD pre-production gate (never part of `classify_j_verdict()`'s own 29 named gates, since production is
never invoked at all if it fails) additionally requires: J1 baseline READ/WRITE/DELETE probes all succeed
AND every one of those successfully-opened probe handles was ACTUALLY closed
(`matrix_all_probe_handles_closed(baseline_matrix)`), before `exec()` is ever called.

`J_PASS` then requires all of:

1. Production's real protection acquire is called exactly once and succeeds.
2. The already-constructed run instance's `self.rebuild` is located and wrapped directly (instance-attribute
   patch), never via a too-late class-level patch.
3. That wrapper is called **exactly once**, and the native return is observed while protection was still
   active — a wrapper installed but never called (zero interceptions) is `J_FAIL`, never merely "incomplete
   evidence".
4. At least one `sha256_stream` call is confirmed against the protected live Master path, with protection
   active, occurring — by event-list ordinal position — strictly between the successful protect-acquire and
   the first native-Rebuild-enter event (the protected Master SHA check is a real gate, not unused evidence).
5. Production's own protected path/generation is mechanically bound to the canonical Master:
   `run_instance.master_path`/`run_instance.master_hash` match the canonical Master path/SHA-256 exactly, AND
   the one successful `protect_acquire` event's own recorded path AND `state["protected_path"]` both equal
   that same canonical path (`protected_path_is_canonical_master`) — the file this harness hashed and the
   file production actually protected are proven to be the same file, never merely assumed.
6. The independent access matrix at the native-Rebuild boundary shows READ succeeds and WRITE/DELETE fail
   with **exactly** `ERROR_SHARING_VIOLATION` (32) — an ambiguous/different denial code is not counted as
   equivalent, even if the baseline succeeded.
7. Native Rebuild itself returns `PASS` (production's own `NATIVE_REBUILD_RETURNED = PASS` log line).
8. The same protected-matrix condition (item 6) is demonstrated at the contextual-composer boundary.
9. The contextual composer itself returns successfully.
10. Production's real protection release is called exactly once.
11. The J3 post-release READ/WRITE/DELETE probes all succeed again.
12. Live Master SHA-256 and byte size are identical before and after the whole campaign.
13. The production command itself finishes `PASS` (`PRODUCTION_REBUILD_CONTROL_GROUPS = PASS`, no
    `= FAIL` line).
14. No probe or protection handle is ever leaked — **derived from the actual recorded `CloseHandle` result
    of every successfully-opened probe handle in every matrix used**, never a hard-coded assumption; a
    synthetic forced `CloseHandle` failure is offline-regressed to prove this gate actually fires.
15. The harness itself never mutates the Master (probe helper is `OPEN_EXISTING` + read/write/delete
    *access checks* only, never an actual write/rename/delete).
16. The required event order — using PURELY ORDINAL (append-list-index) positions, never wall-clock
    timestamps, and requiring each kind to occur EXACTLY once — holds:
    `protect_acquire < native_rebuild_enter < native_rebuild_return < composer_enter < composer_return
    < protect_release < post_release_probe_matrix` (baseline probes are, by construction, recorded before
    production executes at all; the protected-Master-SHA ordering in item 4 is proven separately, using the
    same ordinal technique, since `sha256_stream` may legitimately be called more than once).
17. The **actual loaded** authority runtime identity matches: `authority_runtime.RUNTIME_API_VERSION ==
    "1.0.0-b2a"`, `authority_runtime.RUNTIME_BUILD_ID == "package-boundary-corrected-2026-09-22"`,
    `authority_runtime.is_canonical() == True`, `authority_runtime.get_state() == "READY"` — production's
    own expectation constants are recorded only as additional corroboration, never substituted for the
    actual identity.
18. All three workload-identity layers are confirmed (Layer 1 gates the run before `exec()`; Layer 2 gates
    `instrumentation_ready`, including the master-path/hash binding and the now-mandatory `run_instance.work`
    check; Layer 3 is checked directly against production's own completed log).
19. The fail-closed `run_target_transaction` guard never actually blocked a call during this run (a blocked
    call means instrumentation/workload gates were not ready when a real transaction was attempted, which is
    itself disqualifying).

Any ambiguous access failure, unexpected access denial, missing boundary, missing release, production
failure, wrong workload, wrong protected path, or Master mutation is `J_FAIL`, with the specific failed gate
name(s) reported in `j_failed_checks` — never silently reported as PASS.

## Offline qualification already completed (see `J_MECHANICAL_GATES.md` for detail)

`test_checkpoint_j_native_protected_handle_dryrun.py` — **192/192 PASS** under the real embedded Python
2.7.5. Extracts all six reusable blocks (Win32 probe helper, module-level wrapper installer, run-instance
locator + native-rebuild instance wrap, `run_target_transaction` fail-closed guard, workload-identity gates,
event-order validator + mechanical verdict) verbatim by exact pinned line range and exercises the ACTUAL
deployed logic. Coverage includes: a real disposable-temp-file share-matrix regression with real
`CloseHandle`-result tracking and a synthetic forced `CloseHandle` failure proving the handle-hygiene gate is
genuinely derived, never hard-coded, including a J1-baseline-specific leaked-probe-handle case and a static
proof the hygiene check textually precedes the production `exec()` call; a 2000-iteration
process-handle-count regression; a historical-bug reproduction (rejected class-level patch gets zero
interceptions; the corrected instance-level mechanism gets exactly one, with argument/return-value identity
preserved); a `run_target_transaction` guard regression proving the setup-fails path calls the original
method zero times and always raises, and the setup-succeeds path calls it exactly once with identical
arguments and an unmodified return value; a full wrapper/event-order regression against a synthetic
fake-production module (never the real Normalizer) that opens/closes a REAL Windows handle, proving all five
wrap points plus the guard install and interact correctly end-to-end, including a
premature-call-is-blocked-then-succeeds-once-ready sequence; direct unit tests of every workload-identity
helper (`resolve_unique_shot`, `canonical_single_shot_match`, `work_inventory_matches_single_target` now
requiring a real match with no soft-pass on empty/absent work, `normalize_path_for_comparison()`/
`path_matches_baseline()` — case-insensitive/`..`-normalized/wrong-path/`None` cases — all three
`production_log_*` string checks, and `resolve_fixture_basename()` against a fake `sfmApp`/`vs` object
model); direct ordinal-position tests of `find_protected_master_sha256_ok()`; purely-ordinal
`validate_event_order()` regressions (a genuine list-position swap correctly fails, deliberately misleading
timestamps that contradict the correct list order are correctly ignored, and a duplicate required event is
correctly rejected); and a full adversarial matrix individually forcing each of the **29** named mechanical
gates to fail (plus an explicit `len(set(...)) == 29` count assertion), proving none is silently skipped or
miscounted. `git diff --check` confirms no whitespace/encoding issues.

**This checkpoint has NOT yet been run in real SFM and has NOT yet been deployed to the live MAINMENU
directory.** Final status at this stage:

**J PREPARED / SOURCE REVIEW REVISION 3 COMPLETE / REAL-SFM RUN NOT YET AUTHORIZED**
