# Checkpoint F1-R6 — Fresh Streaming Discovery Parity (Two-Mode / Separate-Fresh-Process Design)

## Purpose

F1-R5 was accepted: **`PASS — TRAVERSAL/MATERIALIZATION DOMINANT`**. Even after 126 of the 250 fresh
discovery sites were reduced to isolated `reachable(scene)` traversal, ~92% of discovery-associated
private growth and ~96% of discovery-associated free-VAS loss remained — strong evidence that fresh scene
traversal/materialization is the primary actionable resource target. F1-R6 designs, offline-verifies, and
(having passed offline parity) real-SFM-tests a **fresh streaming** equivalent of `discover_rig_context()`
that avoids materializing the ~4,250-element `reachable()` list, while preserving exact semantics and
freshness. See `F1_R6_CONTRACT_AND_ALLOCATION_AUDIT.md`, `F1_R6_SWIG_ITERATION_INVESTIGATION.md`,
`F1_R6_STREAMING_DESIGN_AND_EQUIVALENCE_CONTRACT.md`, and `F1_R6_SUMMARY_AND_DECISION.md` for the full
design record.

**This is not authorization to modify production.** O3 remains closed — no cross-boundary discovery
reuse, topology caching, stale handles, or immutable-topology assumptions are introduced anywhere. Every
discovery call, legacy or candidate, performs a complete, fresh, live observation every time.

**This checkpoint does not mutate the scene at all** — no native Rebuild, no shot activation, no writes of
any kind. **Do not save afterward anyway**, per this whole project's own standing discipline.

## Design correction from the prior version of this checkpoint

The prior committed version of this script ran BOTH legacy and candidate discovery in one SFM process,
alternating which arm ran first per target to cancel first-position bias. That was rejected: F1-R4/F1-R5
established that process-retained allocator/VAS high-water survives GC, so a legacy call can permanently
raise the process's own allocation baseline before the candidate arm runs (or vice versa) — order
alternation cancels first-position bias, not shared-process cross-arm contamination.

This script is now **two-mode, one-arm-per-process**: the same MAINMENU script supports LEGACY and
STREAMING_CANDIDATE modes, selected via a real Qt dialog shown before production is touched. Each run
measures exactly one mode, in its own fresh SFM process. Semantic and resource comparison between the two
arms happens entirely **offline**, via `F1_R6_Compare_Legacy_vs_Streaming_Results.py`, after both
mode-specific JSON artifacts exist.

## Workload-multiplicity decision (explicit)

This checkpoint measures exactly **one** `discover_rig_context()` call per target — **62 calls per arm**,
not production's own real 250-site schedule (32 `COMPOSER_ENTRY_PATH` targets × 5 calls + 30
`NATIVE_POST_ONLY_STATUS_MISMATCH` targets × 3 calls, per F1-R4/F1-R5). Reproducing the exact 250-call
schedule would require knowing, per target, whether native Rebuild's own status matched and whether
`production_generic_composer()` was entered — both are downstream decisions that depend on actually running
native Rebuild, which this read-only checkpoint correctly never does. There is no valid way to assign a
target to its real 2/3/3/5-call branch without invoking native Rebuild first, and inventing or borrowing
that assignment from a different real run's own log would itself be a form of fabricated/stale state this
project's own discipline rejects. **This checkpoint therefore measures the simpler, honest quantity: one
matched, fresh, live discovery call per target, per arm.** It supports a clean per-call resource/semantic
comparison, unconfounded by call-count differences between arms. It does not itself provide command-scale
(250-call) projections — an analyst may scale its per-call deltas by F1-R4/F1-R5's own already-established
250-call real figures as a separate, explicitly-labeled step.

## Sequence — RUN A (LEGACY)

1. **RESTART SFM FIRST.**
2. **Do not save any prior experimental state.**
3. Open **only** `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx` — never the original `testscripts.dmx`. The
   script structurally refuses to proceed otherwise.
4. Run `Checkpoint_F1_R6_Fresh_Streaming_Discovery_Parity`.
5. In the **first** dialog that appears (this script's own mode-selection dialog, titled "F1-R6 — Select
   Discovery Arm For This Process"), choose **LEGACY**.
6. In the **second** dialog that appears (production's own real scope-choice dialog), choose **All Shots**
   — needed only so `instance.work` reflects the full 62-target scope; this script does not process
   shots/targets the way production does, it reads `instance.work` directly and never advances the real
   pipeline.
7. Wait for completion.
8. Return the output files (see below) — LEGACY variants.
9. **DO NOT SAVE.**

## Sequence — RUN B (STREAMING_CANDIDATE)

10. **Fully restart SFM.** Do not reuse the RUN A process.
11. **Do not save any prior experimental state.**
12. Open **only** `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx` again, fresh.
13. Run `Checkpoint_F1_R6_Fresh_Streaming_Discovery_Parity` again.
14. In the mode-selection dialog, choose **STREAMING_CANDIDATE** this time.
15. In production's own scope-choice dialog, choose **All Shots** again.
16. Wait for completion.
17. Return the output files — STREAMING_CANDIDATE variants.

**Do not run both modes in the same SFM process. Do not skip the restart between Run A and Run B.**

## Output files to return

**Run A (LEGACY):**
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r6_legacy_result.json`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r6_legacy_result_summary.txt`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r6_legacy_production_log.txt`

**Run B (STREAMING_CANDIDATE):**
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r6_streaming_candidate_result.json`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r6_streaming_candidate_result_summary.txt`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r6_streaming_candidate_production_log.txt`

After both runs exist, the offline comparator can be run on any machine with a Python 2.7 interpreter
(no SFM required):

```
python F1_R6_Compare_Legacy_vs_Streaming_Results.py ^
    C:\Users\Public\Documents\sfm_checkpoint_f1_r6_legacy_result.json ^
    C:\Users\Public\Documents\sfm_checkpoint_f1_r6_streaming_candidate_result.json
```

which emits:
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r6_comparison_result.json`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r6_comparison_summary.txt`

**Return all of these** — both runs' own three files each, plus the comparator's two output files.

## What this run does NOT do

- Does not call native Rebuild, activate a shot, or write anything to the scene — confirmed by static
  source check (no `self.rebuild(`/`instance.rebuild(` call, no `SetHeadTimeInSeconds(` call anywhere).
- Does not perform `capture_snapshot_explicit()`, `capture_tree()`, `production_generic_composer()`,
  or `preflight_reconciliation_plan()` — confirmed by static source check.
- Does not reopen O3 and does not implement any discovery caching, reuse, or shortcut.
- Does not save the scene.
- Does not run both arms in one process, and does not compare the two arms in-process — comparison is
  strictly offline, after both artifacts exist.

## Design summary

`discover_rig_context(shot, aset)`'s own first statement reads `shot`'s own `scene` **attribute**
directly — it does not depend on SFM's own playhead/active-shot state at all (unlike native Rebuild, which
genuinely requires shot activation, per F1-R3's own audit). This means legacy and candidate can both be
called directly against every one of the 62 real targets recorded in `instance.work`, with **zero scene
mutation and zero risk of one observation affecting the other's own state**.

**Legacy** is `discover_rig_context`, extracted unmodified from the exec()'d production namespace (never
reimplemented). **Candidate** is `discover_rig_context_streaming`, from `F1_R6_Discovery_Streaming_
Prototype.py` (deployed alongside this script), loaded into a namespace seeded with the SAME extracted
legacy helpers (`handle`, `typ`, `arr`, `scalar`, `element_ref_pairs`, `name`, `to_unicode`, `ProbeError`) —
guaranteeing the candidate calls the identical native-bound functions legacy itself uses; only the
traversal/classification fusion is new code. The prototype module is loaded (exec'd) **only** during a
STREAMING_CANDIDATE run — a LEGACY run's own resource profile is never touched by candidate module loading.

Per target, only the selected arm's `discover_rig_context` is called once. Cheap process-memory sampling
(private/working-set) brackets every individual call; the more expensive VAS (free/largest-free) scan is
taken only at low cadence (every 8th target, plus start/final/post-GC), matching this project's own
established discipline.

## Emitted evidence

Per target (per arm's own JSON file): `status`, `is_ambiguous_status`, `reachable_rig_count`,
`matching_rig_count`, `rig_handle`, `registry_handle`, `owned_handles`, `owned_names_in_order`,
`hidden_groups`, `elapsed_seconds`, `private_delta`, `working_set_delta` — a compact per-target semantic
record, never a full object dump. Aggregate (per arm): `arm_summary` (total discovery calls, total elapsed
seconds, summed private/working-set deltas, status distribution); `resource_deltas` (whole-command
before/after/post-GC deltas, for cross-reference against F1-R3/F1-R4/F1-R5's own established baselines).

The offline comparator then computes, from the two arms' own JSON files: 62/62 target identity/order
parity; per-target semantic mismatch count (must be zero); matching branch-relevant status distributions;
matching ambiguity disposition; and the derived resource metrics —
`candidate_private_reduction_bytes`, `candidate_private_reduction_ratio`,
`candidate_free_vas_improvement_bytes`, `candidate_largest_free_improvement_bytes`,
`candidate_elapsed_reduction_seconds`, `candidate_elapsed_ratio` — none of which the runtime script itself
ever computes.

## Mechanical PASS / FAIL / INCOMPLETE

**Per-arm PASS** (each run's own JSON) requires: correct production Normalizer/canonical Master SHA-256;
correct normalized-copy fixture filename (and confirmed refusal of the original fixture's filename); a
valid mode selection; the real run instance located and neutralized before any event pump; `instance.work`
present with exactly 15 shots and exactly 62 eligible targets, gate-skip counts matching the verified
expected values; all 62 targets recorded (`arm.all_62_targets_recorded`); `instance.total_shots_processed
== 0`; resource and post-GC endpoints captured; zero anomalies.

**Comparator PASS** requires: both arms' own `overall_pass == True`; 62/62 identity/order parity; zero
semantic mismatches; matching status distributions; matching ambiguity disposition; matched (62 == 62) call
counts across arms.

**FAIL** for any parity mismatch, gate/guard failure, or arm-level check failure.

**INCOMPLETE** if the exact comparison cannot be produced without dragging semantic capture or mutation
into the measurement.

## Offline verification performed before deployment

(1) All three scripts (the real-SFM checkpoint, the prototype module, and the new offline comparator)
syntax-checked under the real embedded Python 2.7.5, PASS. (2) `test_f1_r6_adversarial_parity.py` (SHA-256
`ec345eeba80bd1e086d48fcaad98e03a81caea03971fb67335e817699335bb2d`, UNCHANGED from the prior checkpoint)
compares legacy (extracted verbatim from the pinned production source) against the candidate prototype
across 21 adversarial fake-DME fixtures — **205/205 PASS, zero parity mismatches**. (3)
`test_f1_r6_realscript_regression.py` (SHA-256
`fbb6c79ff4770e05f13597542f1ba1e9d2eeebe0e6610797b3d1b8b65a3fde9a`, revised for the two-mode design)
verifies the real-SFM script's own shared atomic-write primitives (extracted verbatim) and static checks
confirming: the mode-selection dialog exists and offers exactly LEGACY/STREAMING_CANDIDATE; each mode
writes to distinct output filenames; there is no in-process cross-arm comparison function and no dual-arm
result variables; the rejected arm-order-alternation design is gone; the candidate prototype is loaded only
in the STREAMING_CANDIDATE branch; the explicit 62-vs-250 workload justification is present in the script's
own text — **32/32 PASS**. (4) `test_f1_r6_offline_comparator.py` (SHA-256
`5d155f68fa5598c6a255b7b07a2981b22376d0c506c04ace5efd549cd7cf2d8e`, NEW) exercises the comparator's own
`compare_target_records()` and `main()` against synthetic legacy/streaming JSON report pairs — a clean
62/62 match, a semantic mismatch, an identity/order mismatch, a short-target-list case, and a subprocess
smoke test confirming it runs standalone — **23/23 PASS**. All under the real embedded Python 2.7.5. Not
yet run against real SFM.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256: `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Expected normalized-copy fixture filename: `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx`
- F1-R6 real-SFM script SHA-256 (revised, two-mode design): `1de63943f6fd670a91f110f94d2b6e16f56473b95a7e40c6d41ad83df4c02eeb`
- F1-R6 prototype module SHA-256 (unchanged): `17851cd1fed519aa8134fb15c2f057c82a471b8d9b7d1f7b3ae7378edfab4cb8`
- F1-R6 offline comparator SHA-256 (NEW): `5d155f68fa5598c6a255b7b07a2981b22376d0c506c04ace5efd549cd7cf2d8e`
- F1-R6 adversarial parity test SHA-256 (unchanged): `ec345eeba80bd1e086d48fcaad98e03a81caea03971fb67335e817699335bb2d`
- F1-R6 real-script regression test SHA-256 (revised): `fbb6c79ff4770e05f13597542f1ba1e9d2eeebe0e6610797b3d1b8b65a3fde9a`
- F1-R6 offline comparator test SHA-256 (NEW): `371a6b22cb9e1a41394ba55fcd54771db296aa406bae31c889fa4cb2c237b153`

## Explicit non-authorization

Even excellent parity and resource results from this checkpoint do not themselves authorize production
implementation. Per explicit instruction, the result returns to independent review before any production
change is considered. This checkpoint does not patch production, does not touch authority/broker code, and
does not close F.
