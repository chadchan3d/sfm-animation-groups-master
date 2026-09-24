# Process-Lifetime Attempt Guard Checkpoint — Instructions

## Why this exists

F2-R1-R3 established, with real-SFM evidence, that legitimate same-process reinvocation of the Rebuild
Control Groups Normalizer is not reliably sustainable (`F2-R1 FAIL — LEGITIMATE SAME-PROCESS REINVOCATION
IS NOT RELIABLY SUSTAINABLE`; see `../LEDGER.md`'s F2-R1 row and `../F1_FINAL_DISPOSITION_REVIEW.md`'s
2026-09-24 update). Astra's independent F release-disposition review authorized implementing a
one-resource-consuming-attempt-per-SFM-process guard directly in production
(`audit_external_runtime/Rebuild_Control_Groups_Normalizer.py`), which has now been implemented as a
gate-only change (204 pure-addition lines; zero deletions; git diff --stat confirmed). **This checkpoint has
NOT been run against real SFM.** It is prepared for the operator to run.

## What the guard does (for context — do not re-derive this while running the checkpoint)

- **Refusal boundary** (`StartRebuildControlGroups()`, before `_choose_scope()`): if a process-attempt
  marker is already present on `main_window`, the command refuses immediately with a message telling the
  operator to save, restart SFM, reopen the session, and run the Normalizer again. Zero scope-control
  collection, work inventory, discovery, provider/broker acquisition, native Rebuild, production-run
  construction, or production-log truncation occurs on this path (the log is only opened later, inside
  `RebuildControlGroupsProductionRun.start()`, never reached from a refused invocation).
- **Arming boundary** (`RebuildControlGroupsProductionRun.start()`, immediately before
  `collect_scope_master_wanted_folds()`): a final recheck, then install, then verification of the marker —
  as one uninterrupted sequence of plain function calls, no intervening Qt event-loop yield — happens right
  before substantial scope traversal begins. A dialog cancel or any bounded rejection earlier in `start()`
  (e.g. "No SFM document is open") never reaches this point, so the process allowance stays unused.
- **Once armed, never cleared in this process**: the marker is a separate `QtCore.QObject`, parented
  directly to `main_window` (independent of the temporary `RUN_LOCK_NAME` active-run marker, which a
  different object owns and which IS released when a run finishes). Nothing in the file ever calls
  `deleteLater()`/`setParent(None)` on it or clears its keepalive reference — confirmed by source-position
  and identifier-count checks in `test_process_attempt_guard_regression.py` (52/52 PASS). Only real process
  exit removes it.
- Applies identically to both **Rebuild Selected Shot(s)** and **Rebuild All Shots**, and to every ordering
  of those scopes, since the guard sits above the scope-dispatch point entirely.

## Offline qualification already performed (before this checkpoint was prepared)

- `test_process_attempt_guard_regression.py` (SHA-256
  `e100cda274bfdbf3341ed865fcd2754b7892b565f0a122a9b7216e1b30dc374e`) — **52/52 PASS** under the real
  embedded Python 2.7.5. Covers all 16 items from the implementation contract: behavioral tests against
  real `QtCore.QObject` instances (fresh-absent, install-then-present, exact objectName, no accumulation
  across repeated lookups, no scene/authority payload retained, same-invocation `gc.collect()` survival,
  fail-closed on lookup/install/verify errors using real PySide subclassing where a plain Python fake would
  not reach the real code path) plus static source-position proofs against the actual deployed production
  script text (arm call site uniqueness and position, bounded-rejection-before-arming, refusal-before-
  `_choose_scope()`, recheck-before-install, no event-loop yield between install and traversal, the marker
  is never referenced by any cleanup path, exactly one log-truncating `open()` call exists and it is
  unreachable from refusal, `StartRebuildControlGroups()`'s own text never references substantial-work
  identifiers).
- `test_checkpoint_process_attempt_guard_dryrun.py` (SHA-256
  `cddf993ff183a4c92456040038d25dfb905faa6581a93d04aace88b33d858c10`) — **15/15 PASS** — offline-verifies
  this checkpoint script itself: it never references `StartRebuildControlGroups()`/scope-dialog machinery/
  substantial-traversal identifiers anywhere in its own source; `load_production_definitions()` extracts
  exactly the 7 pinned definitions by exact line range (never execs production's whole module body, which
  performs real `import sfmApp`/`import sfmClipEditor`/`import vs` statements only satisfiable inside a
  real SFM process) and never imports those SFM-only modules itself; `take_snapshot()` against a fresh real
  `QtCore.QObject` main window correctly reports no marker/no run-lock present and the exact real marker
  name; `main()` persists auto-numbered snapshots without ever overwriting prior history.

## Proof no execution semantics changed

`git diff --stat` against the pre-guard committed production script shows **204 insertions(+), 0
deletions(-)** — a pure addition at four insertion points (one constant block, one exception class, two
small helper functions, the refusal-boundary hook, the arming-boundary hook). `git diff --check` passes
with zero whitespace errors. Every pre-existing identifier/call-site count in the file (e.g. the single
`.deleteLater()` call, the single `) = _choose_scope()` call site) is unchanged from before the guard,
confirmed by exact-count assertions in the offline regression test.

## Real-SFM operator sequence

Uses lightweight counters/logging only. Does **not** perform another whole-session semantic capture, does
**not** repeat All Shots, and does **not** attempt to induce another crash — Selected Shots is sufficient
because the guard sits above the Selected/All dispatch point.

At each numbered **[SNAPSHOT]** step, run `Checkpoint_Process_Attempt_Guard_Qualification`. It is a pure
read-only observer — it never calls the real Normalizer itself, never opens a dialog, and performs zero
scene/provider/native work. Each run appends one auto-numbered record and reprints the full history so far.

1. **RESTART SFM FIRST.**
2. Open **only** `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx` (the accepted normalized qualification fixture) —
   never `testscripts.dmx`.
3. **[SNAPSHOT #1 — baseline.]** Run `Checkpoint_Process_Attempt_Guard_Qualification`. Expect:
   `process_attempt_marker_present = False`, `run_lock_present = False`,
   `production_sha256_matches_expected = True`.
4. Invoke the real **Rebuild Control Groups** command from the SFM menu. When the scope dialog appears,
   click **Cancel**.
5. **[SNAPSHOT #2 — proves cancel leaves the allowance unused.]** Run the checkpoint again. Expect
   `process_attempt_marker_present = False` still (unchanged from snapshot #1), and the
   `production_log` fingerprint unchanged from snapshot #1 (no log was opened/truncated).
6. Invoke **Rebuild Control Groups** again. This time choose **Selected Shot(s)**, using the same already-
   qualified small selection this project has used in every prior Selected-Shots checkpoint (the 2-target
   selection from `C1-2`/`C2-1`/`F1-2` command 1). Let it run to completion.
7. Confirm in the normal SFM UI that the command completed successfully (its own summary/log reports
   success) and that ordinary editing — select a control, pose it, switch animation sets — still works.
8. **[SNAPSHOT #3 — proves arming occurred.]** Run the checkpoint again. Expect
   `process_attempt_marker_present = True` now (changed from snapshot #2), `run_lock_present = False` (the
   temporary run lock was released when the command finished), and record this snapshot's own
   `production_log` fingerprint as the reference point for step 11's truncation check.
9. Invoke **Rebuild Control Groups** one more time, in the **same** SFM process (do **not** restart).
10. **Confirm no scope dialog appears at all** — the command must refuse immediately with the recovery
    message ("Control Group Normalizer has already started a run in this SFM process..."). This is an
    operator-observed fact; the checkpoint script cannot itself observe whether a dialog appeared.
11. **[SNAPSHOT #4 — proves the refusal performed zero work.]** Run the checkpoint again. Expect
    `process_attempt_marker_present = True` (unchanged from snapshot #3), `run_lock_present = False` (no
    run was ever constructed), and the `production_log` fingerprint **byte-for-byte identical** to snapshot
    #3's own fingerprint (proves the refused invocation did not truncate or append to the prior log).
12. Reopen or switch to any **different** document in the same SFM process (no restart).
13. Attempt **Rebuild Control Groups** again. **Confirm it is still refused before any dialog appears.**
14. **[SNAPSHOT #5 — proves the guard is process-scoped, not session-scoped.]** Run the checkpoint again.
    Expect `process_attempt_marker_present = True` still, and the `production_log` fingerprint still
    unchanged from snapshot #3/#4.
15. **Fully restart SFM.**
16. Reopen `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx`.
17. **[SNAPSHOT #6 — proves process exit clears the guard.]** Run the checkpoint again. Expect
    `process_attempt_marker_present = False` (changed back to absent — a new process), `run_lock_present =
    False`, and `current_pid` different from every prior snapshot's own `current_pid`.
18. Run the same already-qualified small Selected Shot(s) command again and confirm it is **permitted** and
    completes normally (no refusal message).
19. **[SNAPSHOT #7 — confirms the fresh process re-arms normally.]** Run the checkpoint one final time.
    Expect `process_attempt_marker_present = True` again, in this new process.
20. Return all output artifacts (see below). Do not overwrite the authoritative fixture at any point.

## Output files to return

- `C:\Users\Public\Documents\sfm_checkpoint_process_attempt_guard_result.json` (the full snapshot history —
  overwritten/extended each run; the final run's own copy contains every prior snapshot too)
- `C:\Users\Public\Documents\sfm_checkpoint_process_attempt_guard_summary.txt`
- `C:\Users\Public\Documents\sfm_checkpoint_process_attempt_guard_state.json`
- The real Normalizer's own output artifacts from steps 6 and 18 (`sfm_rebuild_control_groups.txt` and
  whatever result/summary files that command itself produces), for independent cross-reference against the
  checkpoint's own `production_log` fingerprints.

## PASS / FAIL contract

**PASS** requires all of: snapshot #1 shows a clean baseline; snapshot #2 shows the cancel left the
allowance unused with an unchanged log fingerprint; the Selected Shots command in step 6 completes
normally; snapshot #3 shows the marker now present; step 10's refusal is directly observed (no dialog);
snapshot #4 shows the marker still present with a **byte-for-byte unchanged** log fingerprint and no run
lock; step 13's refusal still holds after a session change; snapshot #5 confirms the guard survived the
session change; after a real restart, snapshot #6 shows the marker absent and a new PID; step 18's Selected
Shots command is permitted and completes normally; snapshot #7 confirms the fresh process re-armed.

**FAIL** includes: a dialog appearing on a refused invocation; the process-attempt marker absent or missing
after step 6 (arming did not occur); the log fingerprint changing between snapshots #3, #4, or #5 (a
refusal or later work touched the log); the marker being absent after the session change in step 12–14
(guard is session-scoped instead of process-scoped, contradicting the design); the marker still present
after the real restart in snapshot #6 (guard did not clear on process exit); step 18's command being
refused (a fresh process should never be blocked); any snapshot's own `production_sha256_matches_expected`
being `False` (the deployed script drifted from the qualified candidate).

## Identities this checkpoint is pinned against

- Production Normalizer SHA-256 (guard-added candidate): `6170d2a248845281b5f5d38dfea4b9f2decf908b8e3b79e80f4ada18d2f54625`
- Production Normalizer SHA-256 (pre-guard baseline, unchanged prior pin): `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256 (unchanged, not touched by this work): `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Checkpoint script SHA-256: `c2b28a3ca847b1c15ff9c0b43d42ecd7d9ba2a43a44b63254b1529dec984c4d5`
- Guard offline regression test SHA-256: `e100cda274bfdbf3341ed865fcd2754b7892b565f0a122a9b7216e1b30dc374e`
- Checkpoint dry-run test SHA-256: `cddf993ff183a4c92456040038d25dfb905faa6581a93d04aace88b33d858c10`

## Explicit non-authorization

This checkpoint does not modify production beyond the already-implemented guard, does not reopen the F1
optimization search, and does not begin G. `F` remains `OPEN` pending this checkpoint's own real-SFM result
and independent review of the recommended admission policy recorded in `../F1_FINAL_DISPOSITION_REVIEW.md`.
