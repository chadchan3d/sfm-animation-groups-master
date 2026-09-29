# Ledger

## Coder gate
Before editing, compare the assignment with the Blueprint and this Ledger.
Verify the current code state and relevant claims.
If the assignment assumes unfinished work is complete, contradicts the
Blueprint, or expands scope, report the conflict before dependent edits.
Otherwise proceed with the assigned milestone.

## Current milestone
CPM Convergence Step 4: Clothing Fit per-target authority (§15), with `Gfit` and a per-target
stage lease held through post-stage verification, plus the approved Reclassify copy correction.
**Status: complete and checked (offline); awaiting review.**

## Current state
`master` at the Ledger commit that follows `f47f83c` (Step 4 code), on top of `40a2e9b`.

Files changed in `f47f83c`:
- `cpm/app/SFM_Character_Preset_Manager.py`;
- `cpm/convergence/cpm_authority_adapter.py`: new `open_stage()` / `CpmStageAuthority`;
  `cpm_compat_v1` is unchanged;
- `cpm/convergence/tests/test_cpm_app_clothing_fit.py` (new);
- `test_cpm_app_canonical_route.py`: cumulative bounded-edit expectations, and the module-dir
  override is now honored;
- `test_cpm_app_operation_context.py`: approved copy.

Unchanged: the baseline, the shared package and the Normalizer.

## Verified (offline only)
Test results (Python 3.10 = embedded 2.7.5; digests identical):

| Suite | Checks | Digest |
|---|---|---|
| Step 4 | 95/95 | `d065ae69…` |
| Step 3 | 108/108 | `a2d6d0d3…` |
| Step 2b | 83/83 | `b043eefb…` |
| Step 2a | 205/205 | `02cf2200…` |
| Step 1 | 196/196 | `e72e3c84…` |

- **Gfit:** set at Fit start from the Step 3 authorization as the Master SHA, stored as
  `fit_semantic_generation`. It is separate from the integer `fit_generation`; a stale callback
  generation is ignored without any authority access.
- **Per target:** the real `fit_selected` / `fit_stage` run one Qt turn at a time.
  - Each target is proven with `expected_generation=Gfit` over source Body membership plus the
    target's vocabulary; target-only folds are present.
  - Planning and verification use the same stage (lease count 1 during planning, mutation and
    verification).
  - The stage is released before each next target is queued (0 leases whenever a target is
    scheduled).
- **Warnings:** results through the real `p03_unmapped_relevant_controls` rule are identical via
  the stage and via the bounded adapter query, and match the hand audit: exact Body Morphs and
  Clothing only.
- **G1→G2 between targets:**
  - target 1 stays committed; target 2 has zero writes;
  - targets 2–3 are unattempted, not failed; the Fit terminates with the existing status copy;
  - the scope is rebuilt under G2; the old Fit is not resumed;
  - a new Fit runs under G2.
- **Post-stage Uncovered:** fails closed after commit (committed, verification "uncertain"), with no
  second acquisition. Foreign-modal deferral takes no authority; the proof runs at resume.
- **Rollback:** Fit's abort verification is native-only (`p03_target_matches_baseline`), so no
  semantic facts needed binding.
- No historical provider call. 8 Step 4 perturbations were all detected (app + adapter).

## Unresolved
- **Suite 4: PASS (offline).** All five §20 proofs, plus review §9's Uncovered and
  callback-cancellation items. Native Fit mapping and mutation (`g11a_safe_plan` native parts,
  `prod_apply_match`) were stubbed.
- **Real-SFM-only Fit obligations:**
  - the real native Fit transaction/Undo per target;
  - target 1's Undo validity after a G2 stop;
  - real foreign-modal timing;
  - the outstanding forced Fit rollback-verification failure gate (not exercised; still open).
- **R6:** fully lifted on product paths. The fail-closed stand-in remains only for callers without
  a stage or context.
- **Reclassify copy:** corrected as approved to "Saved classification cleared. Current authority
  now classifies this flex."
- **Stale-scope UI presentation:** undecided.
- **Real-SFM (§21), Suite 2, C7–C10:** not run. The Apply native transaction has not run offline.
  Nothing deployed.
- **Latency:** unmeasured. One stage acquisition per Fit target.
- **Cleanup:** historical authority machinery is still present (cleanup not started, by
  instruction). **K, L:** not started.
- Interim runtime layout: CPM modules in the MAINMENU `ChadChan3D` directory (untested; L owns
  the final layout).
- G18AN signatures are interpreter-specific; the 2.7.5 value is authoritative.
- Negative fixtures surface as `SidecarMissing`; messaging is undecided.
- `verify_py27_equivalence.py` was left unmodified.
- R3, R9, R13: CLOSED.

## Next
Milestone complete. Awaiting review. The Blueprint sequence next calls for its focused
qualification: Suite 2, gates C7–C10, the forced Apply/Fit rollback-verification failures, and
real-SFM §21. Then cleanup, then K. Not started.

## Checkpoints
Update this Ledger and output its complete, concise contents when:
- The milestone is complete and checked.
- Progress is blocked or requires an owner decision.
- A Blueprint conflict, scope expansion, or unmet prerequisite is found.
- Work is being paused or transferred.

State why the checkpoint occurred. Stop at milestone completion.
For blockers or conflicts, pause affected work until resolved.
The owner relays the updated Ledger to the designer, or the designer
retrieves that same version from the shared repository.

## Maintenance
Replace stale entries; keep checkpoint content about one screen.
Preserve unresolved issues. Label uncertainty and untested claims.
Keep history in Git or an archive. Routine edits do not require a
full Ledger report.
