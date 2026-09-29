# Ledger

## Coder gate
Before editing, compare the assignment with the Blueprint and this Ledger.
Verify the current code state and relevant claims.
If the assignment assumes unfinished work is complete, contradicts the
Blueprint, or expands scope, report the conflict before dependent edits.
Otherwise proceed with the assigned milestone.

## Current milestone
CPM Convergence Step 3: CPM Operation Authority Context (§14). Save, Update, Apply and
Review/Reclassify authorize post-prompt and consume a detached context; Fit is untouched.
**Status: complete and checked (offline); awaiting review.**

## Current state
`master` at the Ledger commit that follows `1bb2e51` (Step 3 code), on top of `b4da338`.

Files changed in `1bb2e51`:
- `cpm/app/SFM_Character_Preset_Manager.py`;
- `cpm/convergence/tests/test_cpm_app_operation_context.py` (new);
- `cpm/convergence/tests/test_cpm_app_canonical_route.py` (bounded-derivation expectations made
  cumulative for Step 3).

Unchanged: the baseline, the shared package, the Normalizer, and `cpm/convergence/*.py`.

## Verified (offline only)
Test results (Python 3.10 = embedded 2.7.5; digests identical):

| Suite | Checks | Digest |
|---|---|---|
| Step 3 | 108/108 | `4391bf76…` |
| Step 2b | 83/83 | `5ec417c9…` |
| Step 2a | 205/205 | `02cf2200…` |
| Step 1 | 196/196 | `e72e3c84…` |

- **Context:** `prod_cpm_authorize_operation` checks the scope's SHA with
  `verify_current_generation`, using the scope's own vocabulary. It returns plain data only:
  - SHA and compatibility identity;
  - provider capture and runtime API/build;
  - contract/consumer/policy identity;
  - membership;
  - the persistence capture (G18AN 4-field shape).

  Objects, generators, closures and adapters are refused. Leases and providers are back at
  baseline after every path.
- **Save (Body/Expression):** authorizes after the prompt returns, once, before any write. No
  authority access after the first write. The character capture comes from the context; the
  preset capture is unchanged. **R6 refusal lifted.**
- **Update:** same ordering; still succeeds (not fail-closed).
- **G1→G2 during a Save/Update prompt:** stale rejection with no durable write; one rebuild
  under G2; no replay.
- **Apply (R9):**
  - Under G2, the pinned postcommit readback and `prod_abort_apply_and_verify` run with 0 authority
    opens and verify against the pinned membership.
  - Membership drift is rejected.
  - Statically: one authorization before `StartUndo`; all 3 late checks pinned; no reacquisition.
- **Review:**
  - Authorizes while the scope is still selected; writes only after authorization; resolved and
    conflict literals are refused. **R6 refusal lifted.**
  - The rebuild is a separate fresh acquisition.
  - Stale generation keeps the §13 rebuild.
- **Reclassify:** the durable clear succeeds under G1. When G2 then resolves the literal, it
  reports the edit and the new classification separately (no raise, not forced back to Review).
  The returns-to-Review flow is unchanged.
- No historical provider call on any path. 8 Step 3 perturbations were all detected.

## Unresolved
- **Suite 3: PASS (offline).** All six §20 proofs hold. Apply is covered by running its exact
  postcommit and abort helpers plus static routing of `prod_apply`. `prod_apply`'s native Undo
  transaction itself was **not executed** offline, so it needs real SFM.
- **R6:** the Save and Review refusals are lifted. The Clothing Fit unmatched-target query
  intentionally stays fail-closed (Step 4). Any caller without a context still refuses.
- **R9:** CLOSED offline. Apply late verification uses the pinned context.
- **Operation baselines:** Apply's native baselines (`built`, `scale_plan`) stay in the existing
  Apply-owned structures, not in the context. They hold live-verification data by design; the
  context carries the authority facts.
- **Provisional copy (owner review):** Reclassify's new status "Classification cleared.", used
  when newer authority now classifies the flex.
- **Stale-scope UI presentation:** undecided (unchanged from 2b).
- **Step 4 (Fit):** not started. **K, L:** not started.
- **Real-SFM (§21), Suites 2 and 4, C7–C10:** not run. Nothing deployed.
- **Latency:** unmeasured. Each semantic action now adds one expected-generation acquisition,
  normally a full cache hit.
- Interim runtime layout (untested; L owns the final layout): CPM modules in the MAINMENU
  `ChadChan3D` directory.
- G18AN signatures are interpreter-specific; the 2.7.5 value is authoritative.
- Negative fixtures surface as `SidecarMissing`; messaging is undecided.
- `verify_py27_equivalence.py` was left unmodified.
- Inherited log path and repository URL are unchanged.
- R3: CLOSED. R13: CLOSED (`cpm/app/SFM_Character_Preset_Manager.py`).

## Next
Milestone complete. Awaiting review. Per the Blueprint the next step is Step 4 (Clothing Fit per
target: target vocabulary, `Gfit`, stage lease through verification). It is not started.

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
