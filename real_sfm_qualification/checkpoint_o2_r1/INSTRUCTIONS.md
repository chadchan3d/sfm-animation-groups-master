# Checkpoint O2-R1 — Native Timing Correction + Narrow Capture-Overlap Proof

## Purpose

O2's real-SFM run succeeded and produced real, materially useful findings — but one instrumentation
seam failed: `native_rebuild_stage_summary.call_count = 0`, despite the production log independently
proving native Rebuild executed twice and returned PASS both times. This checkpoint corrects **only**
that seam and re-runs the identical bounded workload to fill in the missing native-timing data. It does
not re-measure anything O2 already measured correctly, and does not expand scope. See
`O2_R1_NATIVE_TIMING_CORRECTION.md` for the full root-cause analysis and the fix.

This is still measurement/proof only. **Do not save afterward.**

## Sequence

1. **RESTART SFM FIRST.**
2. **DO NOT SAVE the previous experimental state; restart SFM to discard it.**
3. Open the established disposable qualification fixture.
4. Select `shot3` and no other shot.
5. Run `Checkpoint_O2_R1_Native_Timing_Correction`.
6. If the starting-fixture gate fails, the script stops on its own — no mutation occurs.
7. Choose **Selected Shots** in the first real dialog that appears (command 1, fresh state).
8. Choose **Selected Shots** again in the second real dialog (command 2, in the same continuous SFM
   process, immediately after command 1 — needed to compare native-Rebuild cost fresh vs.
   already-normalized, matching O2's own established comparison).
9. Return:
   - `sfm_checkpoint_o2r1_result.json`
   - `sfm_checkpoint_o2r1_result_summary.txt`
   - `sfm_checkpoint_o2r1_production_log_command1.txt` / `_command2.txt`
10. **DO NOT SAVE. Restart SFM afterward.**

## What this run does NOT do

- Does not run All Shots.
- Does not run F1-R2.
- Does not re-measure discovery, tree-construction, or the composer/terminal equivalence witnesses —
  those are already established from O2's own real run and preserved unchanged.
- Does not implement any shortcut, cache, or early-out.

## Mechanical PASS / FAIL / UNRESOLVED rules

`OVERALL_PASS` requires: exact production Normalizer and canonical Master SHA-256; `shot3` present; both
commands started and completed within timeout; native guards and native-rebuild log markers PASS both
commands; `FINAL_REPORT_ENTRY` reached both commands; authority broker `READY`/canonical with zero
outstanding leases both commands; **`native_rebuild_instance_wrap_installed` = True both commands**
(the specific check this correction exists to satisfy); the script completes without an unhandled
exception.

Required O2-R1 conclusions, decided from the actual numbers this run produces:

- **Native Rebuild timing**: per-target elapsed time, fresh vs. already-normalized, and whether it is
  material relative to the ~0.15s discovery-walk cost already established. Classification: `MATERIAL` /
  `IMMATERIAL` / `UNRESOLVED`.
- **Discovery**: keep `MATERIAL` unless this run's own data contradicts it.
- **Tree construction**: keep `IMMATERIAL` unless this run's own data contradicts it.
- **Composer-before overlap**: after the static proof (`O2_R1_OUTER_POST_TO_COMPOSER_BEFORE_PROOF.md`,
  already `SOURCE_EQUIVALENCE_SUPPORTED`), classify `DESIGN REVIEW JUSTIFIED` / `REJECT` /
  `MORE PROOF REQUIRED`.
- **Reconciled terminal overlap**: after the static proof
  (`O2_R1_COMPOSER_AFTER_TO_TERMINAL_PROOF.md`, already `RECONCILED_PATH_REUSE_PLAUSIBLE`), same
  three-way disposition, reconciled path only.

## Important interpretation constraint

Do not treat Rebuild→Normalizer overlap as a newly discovered optimization target — that overlap is
fundamental to the design: the Normalizer normalizes the state native Rebuild produces. The optimization
question is narrower: **within the Normalizer's required post-Rebuild pathway, are we materially
repeating discovery/capture/validation work that can be safely reused without weakening freshness or
correctness?** This run's own native-timing data feeds that question — it does not change it.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256:
  `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Astra source baseline commit: `dc92623f17c6b151b7bf5f6ed4ab65cb3f1e29ea`
- O2-R1 script SHA-256: `fe062549bbf3f0b0611ed57824b537e7edf9efa1219b5ca7f4499a8b2dc8f8f7`
- O2-R1 offline mechanism test SHA-256: `5ec33023f9187bb5abdfd991090e53f6c4e22e2c7e4ffaef052289e8d87473db`
