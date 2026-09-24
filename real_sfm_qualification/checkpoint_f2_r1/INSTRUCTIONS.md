# Checkpoint F2-R1 — Legitimate Same-Process Reinvocation Qualification

## Purpose

`F1_REPEAT_HISTORY_AUDIT.md` established that this project has never preserved a determinate outcome for
production All Shots invoked twice in one unrestarted SFM process (classification C). This checkpoint is
the ONE narrow real-SFM confirmation that follows from that finding — **it is not part of the F1
optimization search** (that search is concluded; see `F1_OPTIMIZATION_INVESTIGATION_SUMMARY.md`) and does
not reopen it. It asks a narrower, product-relevant question: does a *legitimate* supported workflow —
All Shots completes, the user returns to ordinary editing, makes one small, real, predetermined
control-group edit that genuinely warrants renormalization, then invokes All Shots again in the same
process — actually work? This is explicitly **not** an immediate unchanged All→All stress test, not a
repetition-count test, and not an optimization benchmark. **Undo is not a requirement anywhere in this
checkpoint.**

## The controlled edit (CORRECTED 2026-09-24)

See `F2_R1_CONTROLLED_EDIT_JUSTIFICATION.md` for the full evidence trail. **Correction**: the operator
cannot freely drag a control into an arbitrary existing group in SFM. The real, supported relocation
mechanism is the first-party SFM DAG-view right-click command "move to hidden group"
(`Hide_SelectedDag()`), which moves the selected control into a group literally named `Hidden` (created
with `SetVisible(False)` if it does not already exist). In short: select control `rig_hand_L` on target
`shot3/foxmccouldwm1` in the DAG view, run that real command, moving it out of its qualified group
`RigArms/LeftArm` and into `Hidden`. Verified directly against production source that a hidden rig-owned
control is not excluded from Master-driven reconciliation — see the justification document for the full
citation trail.

**If Stage 1 was already run once under the prior (incorrect `RigHelpers`-based) version of these
instructions**: that attempt is aborted, not qualification evidence. Before starting fresh, delete
`C:\Users\Public\Documents\sfm_checkpoint_f2_r1_state.json` if it exists, and restart from a fresh SFM
process and a fresh copy of the disposable fixture, per the sequence below.

## One runnable checkpoint, invoked three times

The same script, `Checkpoint_F2_R1_Legitimate_Reinvocation_Qualification.py`, is run three times total —
twice in one continuous SFM process (Stage 1, then Stage 2), and once more after a deliberate restart
(Final Verification). It automatically classifies which mode to run from a small persisted JSON state
file (`sfm_checkpoint_f2_r1_state.json`) plus an in-process Qt marker (a child `QObject` parented to
`main_window`, exactly the same cross-invocation-continuity technique this project's own `RUN_LOCK_NAME`
mechanism already relies on throughout) — the marker survives separate script invocations within the same
process but is absent after a real restart, which is exactly the signal needed to detect a protocol
violation (SFM restarted between Stage 1 and Stage 2) versus a legitimate mode transition. Any state it
cannot unambiguously classify causes it to STOP before doing anything further — it never guesses.

## Exact operator sequence

1. **RESTART SFM FIRST.**
2. **Do not save any prior experimental state.**
3. Open **only** `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx` (the accepted normalized qualification fixture) —
   never `testscripts.dmx`.
4. Run `Checkpoint_F2_R1_Legitimate_Reinvocation_Qualification`. This is Stage 1. Choose **All Shots** in
   the real production dialog that appears. **Wait for the script's own summary output before doing
   anything else** — this may take several minutes; use generous timing, the script itself waits up to 30
   minutes.
5. Confirm Stage 1's own summary reports `OVERALL_PASS=True`. Wait for complete return to normal SFM
   editing (the script exits fully; no further script activity should be running).
6. Perform **only** the specified controlled edit: in the DAG view, select control `rig_hand_L` (target
   `foxmccouldwm1`, shot `shot3`) and run the real SFM DAG right-click command **"move to hidden group"**
   (moves it into the group literally named `Hidden`, creating it with `SetVisible(False)` if it does not
   already exist). Do not make any other edit.
7. Run `Checkpoint_F2_R1_Legitimate_Reinvocation_Qualification` again, in the **same** SFM process (do
   **not** restart). This is Stage 2 (the script detects this automatically). Choose **All Shots** again
   in the real production dialog. Wait for the script's own summary output.
8. Confirm Stage 2's own summary reports `OVERALL_PASS=True`. After it returns, confirm ordinary SFM use
   still works: select a control, pose it, select a different animation set, confirm the UI responds
   normally.
9. **Save As** the disposable qualification result to exactly `F2_R1_DISPOSABLE_REINVOCATION_RESULT.dmx`
   (a **new** filename — do not overwrite `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx` or the original
   authoritative fixture).
10. **Restart SFM.**
11. Open `F2_R1_DISPOSABLE_REINVOCATION_RESULT.dmx` (the file just saved). Run
    `Checkpoint_F2_R1_Legitimate_Reinvocation_Qualification` one more time — the script detects this is
    Final Verification mode automatically (read-only; it does not invoke production again).
12. Return all output artifacts (see below).
13. Do not overwrite the authoritative fixture at any point.

## Output files to return

**Stage 1:**
- `C:\Users\Public\Documents\sfm_checkpoint_f2_r1_stage1_result.json`
- `C:\Users\Public\Documents\sfm_checkpoint_f2_r1_stage1_summary.txt`
- `C:\Users\Public\Documents\sfm_checkpoint_f2_r1_stage1_production_log.txt`

**Stage 2:**
- `C:\Users\Public\Documents\sfm_checkpoint_f2_r1_stage2_result.json`
- `C:\Users\Public\Documents\sfm_checkpoint_f2_r1_stage2_summary.txt`
- `C:\Users\Public\Documents\sfm_checkpoint_f2_r1_stage2_production_log.txt`

**Final Verification:**
- `C:\Users\Public\Documents\sfm_checkpoint_f2_r1_final_verification_result.json`
- `C:\Users\Public\Documents\sfm_checkpoint_f2_r1_final_verification_summary.txt`

**Cross-invocation state (informational):**
- `C:\Users\Public\Documents\sfm_checkpoint_f2_r1_state.json`

## PASS / FAIL contract

**PASS** requires, across all three invocations: command 1 (Stage 1) All Shots completes; the script
returns control to normal SFM UI cleanly; the operator's controlled edit is confirmed present at the start
of Stage 2 (`f2r1.stage2.precondition_edit_is_present`); command 2 (Stage 2) All Shots completes in the
**same** SFM process; the controlled edit reaches its predetermined normalized state
(`f2r1.stage2.rigarms_leftarm_order_restored`); production's own native/authority evidence
(`NATIVE_GUARDS`, `NATIVE_REBUILD_RETURNED`, `FINAL_REPORT_ENTRY`) is present for both commands; no
unaccounted/incomplete command (`run_completed_cleanly` true for both); ordinary selection/posing/editing
still works afterward (operator-confirmed); saving the disposable result succeeds; the fresh-process Final
Verification independently agrees (`f2r1.final_verification.control_in_expected_group`,
`...rigarms_leftarm_order_matches_expected`). **Undo is not a PASS requirement.**

**FAIL** includes: a crash; a hang/incomplete command (the wait loop's own 1800-second timeout is
exceeded); command-accounting ambiguity (`run_started`/`run_completed_cleanly`/`total_shots_processed`
inconsistent); semantic drift; the controlled edit not normalized; inability to return to usable SFM
editing; inability to save; any authority/isolation check failure. A FAIL does **not** automatically
reopen the F1 optimization search — it means legitimate same-process later reinvocation is a demonstrated
product limitation requiring an explicit product/recovery/admission decision, separate from this
checkpoint.

## Resource telemetry captured

Per command (Stage 1 and Stage 2, each independently): private bytes, working set, free VAS, largest free
region, sampled immediately before and after the command (via the same extracted
`contextualizer_process_memory_sample`/`contextualizer_virtual_address_sample` functions every earlier
real-SFM checkpoint in this project already uses) plus a post-GC sample. No resource-admission threshold
is invented or applied — raw deltas are reported for the record, not judged against an arbitrary byte
limit; the qualification asks whether the workflow succeeds, not whether some threshold is met.

## Offline verification performed before deployment

`test_f2_r1_diagnostic_regression.py` (SHA-256
`e046dd1c493831d303d550ddd2c03f7538567ad651fe8f1f9adb76bf23179ab4`) extracts the script's own pure-Python/
Qt helper functions verbatim (by source line range) and exercises them — **50/50 PASS** under the real
embedded Python 2.7.5 — covering: the atomic-write primitives; `read_state_file()` (absent-file,
round-trip, and corrupt-file-raises-STOP cases); `marker_present()`/`set_marker()` against **real**
`QtCore.QObject` instances (PySide's QtCore is importable standalone with the embedded interpreter,
confirmed directly — no fakes needed here), including a same-marker-on-a-different-parent case simulating
a real SFM restart; `classify_invocation_mode()` across all nine reachable state/marker combinations,
including every stale/wrong-stage rejection path (Stage 1 completed in a different process; Stage 2
already completed and re-invoked in the same process; corrupt/empty state); `get_control_membership()`/
`find_target_aset()` against synthetic fake DME control-group trees, including the operator-edit
precondition state and a `None`-root-group exception path; and static design checks confirming no
`SaveToFile` call, no whole-session `capture_snapshot_explicit()` call, no direct `QTimer` scheduling, the
1800-second generous-timing constant, that Final Verification mode neutralizes the real instance and never
invokes production for real, that Undo is never referenced in any `check()` name, and that the
precondition check is structurally placed before the wait loop's own definition (confirming no event pump
could have occurred first). Not yet run against real SFM.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256: `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Expected Stage 1/2 fixture filename: `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx`
- Expected Final Verification fixture filename: `F2_R1_DISPOSABLE_REINVOCATION_RESULT.dmx`
- F2-R1 real-SFM script SHA-256: `8cfeb4f40611bfba0aed3b67ded2bd6e6f7c8841bb023a4f7fb9d52e26d41a37`
- F2-R1 offline regression test SHA-256: `e046dd1c493831d303d550ddd2c03f7538567ad651fe8f1f9adb76bf23179ab4`

## Explicit non-authorization

This checkpoint does not modify production, does not reopen the F1 optimization search, and does not
begin G. `F` remains `OPEN`; a PASS or FAIL result here returns to independent review as one more piece of
evidence for the F final disposition, per `F1_FINAL_DISPOSITION_REVIEW.md` — it does not itself close F.
