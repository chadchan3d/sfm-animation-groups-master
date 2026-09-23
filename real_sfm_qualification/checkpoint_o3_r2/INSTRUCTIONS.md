# Checkpoint O3-R2 — Discovery Cost Split Measurement

## Purpose

O3-R1 concluded `MORE_MEASUREMENT_REQUIRED` for the sole remaining optimization candidate (outer native
POST → composer-before discovery substitution, "Option C": reuse only the expensive whole-scene
`reachable()` traversal, freshly re-execute every discovery-derived validation read in the same order
before composer writes). The specific unresolved question:

> Of the measured ~0.17–0.19 s per `discover_rig_context()` call, how much belongs to the reusable
> whole-scene traversal versus fresh validation Option C must retain?

This checkpoint answers that question by observationally splitting `discover_rig_context()`'s own
internal cost into phases, using the exact, unmodified production code path. **Option C is not
implemented here.** See `O3_R2_DISCOVERY_PHASE_MAP.md` for the phase-to-source-line mapping and
`O3_R2_MEASUREMENT_CONTRACT.md` for the full reporting schema and decision thresholds.

This is still measurement/proof only. **Do not save afterward.**

## Sequence

1. **RESTART SFM FIRST.**
2. **DO NOT SAVE the previous experimental state; restart SFM to discard it.**
3. Open the established disposable qualification fixture.
4. Select `shot3` and no other shot.
5. Run `Checkpoint_O3_R2_Discovery_Cost_Split`.
6. If the starting-fixture gate fails, the script stops on its own — no mutation occurs.
7. Choose **Selected Shots** in the first real dialog that appears (command 1, fresh state).
8. Choose **Selected Shots** again in the second real dialog (command 2, in the same continuous SFM
   process, immediately after command 1 — needed to compare fresh vs. already-normalized, matching
   O2/O2-R1's own established comparison).
9. Let the diagnostic finish, then return:
   - `sfm_checkpoint_o3r2_result.json`
   - `sfm_checkpoint_o3r2_result_summary.txt`
   - `sfm_checkpoint_o3r2_production_log_command1.txt` / `_command2.txt`
10. **DO NOT SAVE. Restart SFM afterward.**

## What this run does NOT do

- Does not run All Shots.
- Does not run F1-R2.
- Does not implement Option C or any other shortcut, cache, or early-out.
- Does not skip any capture, native Rebuild call, or composer call.
- Does not force GC between stages, change callback timing, cache DME objects across a wrapper's own
  call, reduce validation, or alter authority lifecycle.
- Does not add any new per-phase resource probe — resource measurement remains command-level only,
  reusing production's own existing `CONTEXTUALIZER_RESOURCE_CHECKPOINT` log telemetry.

## Mechanical PASS / FAIL rules

`OVERALL_PASS` requires: exact production Normalizer and canonical Master SHA-256; `shot3` present; both
commands started and completed within timeout; native guards and native-rebuild log markers PASS both
commands; `FINAL_REPORT_ENTRY` reached both commands; authority broker `READY`/canonical with zero
outstanding leases both commands; `instrumentation_installed` = True both commands; the script completes
without an unhandled exception. A discovery call that itself raises an exception is recorded (`exception`
field populated, `status` null) and the exception is re-raised unchanged — it is never suppressed or
normalized, and does not by itself fail the run.

## Decision computation (mechanical, from the measured data)

For `PRODUCTION_GENERIC_COMPOSER_PRE` (composer-before) discoveries specifically, across both targets and
both commands:

- **Current cost** = `total_discovery_elapsed_seconds`.
- **Hypothetical Option C retained cost** = every phase bucket Option C must keep (2, 4, 6, 7, 8) plus
  residual.
- **Hypothetical removable cost** = `phase_1_reachable_traversal_seconds` only.
- Classification (`removable_fraction = sum_removable / sum_total`): `OPTION_C_MATERIAL` (≥ 0.5),
  `OPTION_C_MARGINAL` (≥ 0.15 and < 0.5), `OPTION_C_IMMATERIAL` (< 0.15), `UNRESOLVED` (no composer-before
  samples captured, or `sum_total` is zero). The script computes this mechanically in its own JSON output
  (`option_c_decision` / `option_c_decision_detail`) — it does not pre-assert which bucket applies.
- **Do not define success by hitting the prior gross 0.17–0.19 s figure.** The decision is about the
  *proportion* of that cost that is removable, not about reproducing a specific absolute number.

## Important interpretation constraint

This checkpoint measures a cost *split*, not a savings *guarantee*. A high removable fraction here
establishes that Option C's theoretical ceiling remains worth pursuing toward
`READY_FOR_ASTRA_REVIEW`; it does not by itself authorize implementation, which still requires a separate,
explicit approval cycle per the Preflight Approval Gate.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256:
  `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Astra source baseline commit: `dc92623f17c6b151b7bf5f6ed4ab65cb3f1e29ea`
- O3-R2 script SHA-256: `8968b8f7c855a7b00a0db13bdb86b235657b954353cc41ff6d686631200a1431`
- O3-R2 offline mechanism test SHA-256: `8c82169e25e47e2a092c8e4ed1992506c90cc819648f3db9f2d51506c03764e7`
