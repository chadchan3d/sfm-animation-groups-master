# F2-R1 Marker Persistence Probe — Instructions

## Why this exists

A real F2-R1 run showed a fresh-looking invocation, 35 minutes after a genuine Stage 1 completion,
immediately report `stage1_complete` with no in-process marker found — despite the operator reporting
they had closed SFM, deleted the state file, and started fresh. Direct inspection of the actual files on
disk showed the state file was **not** phantom: its timestamp (07:31:10) exactly matches the real Stage 1
result/summary/production-log artifacts from a genuine, successful Stage 1 run. The failing invocation's
own timestamp (08:06:08) is ~35 minutes later. This means either SFM really was restarted in that window
(and the operator's own belief about "same process" was mistaken), or F2-R1's own cross-invocation marker
mechanism — a QObject child of `main_window`, assumed to survive separate MAINMENU script invocations —
does not actually work that way. On inspection, this project's own `RUN_LOCK_NAME` technique (which F2-R1's
marker design claimed to reuse) has **never** actually been checked across two separate script invocations
anywhere in this project — every existing use checks it only within the same invocation's own wait loop.
This probe empirically tests the marker mechanism in isolation, with no Normalizer, no scene traversal, and
no fixture dependency, before another F2-R1 attempt is made.

## Sequence

1. **RESTART SFM FIRST.**
2. Open any document (or none — this probe does not read the scene at all).
3. Run `Checkpoint_F2_R1_Marker_Persistence_Probe`. This is Invocation A. It proves no marker is present,
   installs a marker whose name encodes this process's own PID, and returns.
4. Confirm Invocation A's own summary reports `OVERALL_PASS=True`.
5. Run `Checkpoint_F2_R1_Marker_Persistence_Probe` again, in the **same** SFM process (do **not** restart).
   This is Invocation B (auto-detected). It proves the marker installed by A is still present and still
   encodes A's own PID.
6. Confirm Invocation B's own summary reports `OVERALL_PASS=True`.
7. **Restart SFM.**
8. Run `Checkpoint_F2_R1_Marker_Persistence_Probe` one more time. This is Invocation C (auto-detected). It
   proves the marker is now absent and the current process's own PID differs from A's.
9. Confirm Invocation C's own summary reports `OVERALL_PASS=True`.
10. Return all three result/summary files.

## Output files to return

- `C:\Users\Public\Documents\sfm_marker_persistence_probe_result.json`
- `C:\Users\Public\Documents\sfm_marker_persistence_probe_summary.txt`
- `C:\Users\Public\Documents\sfm_marker_persistence_probe_state.json`

(each invocation overwrites the result/summary files with that invocation's own outcome — copy/rename them
after each step if you want to preserve all three, or report the console output for each step)

## What a PASS across all three invocations proves

That a `QObject` marker parented to `main_window`, installed in one MAINMENU script invocation, reliably
survives being read back in a **separate, later** invocation of the same script within one continuous SFM
process, and is reliably absent after a real restart — confirming F2-R1's own cross-invocation-continuity
mechanism is sound. **Do not proceed to another F2-R1 attempt until this probe has been run for real and
returned a clear PASS for all three invocations.** If Invocation B fails (marker not found in the same
process), that is a genuine, confirmed harness defect in the marker mechanism itself, requiring a different
cross-invocation persistence design before F2-R1 can be trusted.

## Offline verification performed before deployment

`test_marker_persistence_probe_regression.py` (SHA-256
`dbb5844defe15ee7081d17aae861debfa1fa4bb72611274fd0f3a33f4a8036e9`) extracts the probe's own pure-Python/Qt
helper functions verbatim and exercises them — **20/20 PASS** under the real embedded Python 2.7.5 —
covering `read_state()` (absent/round-trip/corrupt-raise cases), `find_probe_marker()`/
`install_probe_marker()` against **real** `QtCore.QObject` instances (including a marker-on-one-window-not-
visible-on-another case simulating a real restart), `extract_pid_from_marker_name()`, and
`classify_probe_invocation()` across all four reachable state/marker combinations. Static checks confirm
the probe never references production, never calls `SaveToFile`, and performs no scene traversal of any
kind. Not yet run against real SFM.

## Identities

- Probe script SHA-256: `fba33198b636330d9a88cd4733f526a59a87cff1e201bfcf0b0f589ca1471b7d`
- Probe offline test SHA-256: `dbb5844defe15ee7081d17aae861debfa1fa4bb72611274fd0f3a33f4a8036e9`
