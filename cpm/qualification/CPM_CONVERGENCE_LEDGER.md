# Ledger

## Coder gate
Before editing, compare the assignment with the Blueprint and this Ledger.
Verify the current code state and relevant claims.
If the assignment assumes unfinished work is complete, contradicts the
Blueprint, or expands scope, report the conflict before dependent edits.
Otherwise proceed with the assigned milestone.

## Current milestone
Offline consolidation of Blueprint §20: Suite 2 and gates C7–C10, with no product changes unless a
defect appears. **Status: complete and checked (offline); awaiting review. No product defect
found; no product code changed.**

## Current state
`master` at the Ledger commit that follows `69bbc55`. That commit adds
`cpm/convergence/tests/test_cpm_convergence_gates.py` (new, test-only) on top of `cea4d41`.
The app, the adapter/projection, the baseline, the shared package and the Normalizer are all
unchanged.

## Verified (offline only)
Gates suite: 152/152 on Python 3.10 = embedded 2.7.5, digest `a9a3ef5f…`. Check counts: Suite 2
29, C7 59, C8 29, C9 15, C10 12, plus 8 section/suite checks.

Regression (both interpreters, digests unchanged from their last records):

| Suite | Checks | Digest |
|---|---|---|
| Step 1 | 196 | `e72e3c84…` |
| Step 2a | 205 | `02cf2200…` |
| Step 2b | 83 | `b043eefb…` |
| Step 3 | 108 | `a2d6d0d3…` |
| Step 4 | 95 | `d065ae69…` |

Three gate-suite perturbations were all detected: bounded read keeps its lease; unavailable
reported as healthy; Uncovered treated as absent.

- **Suite 2 — PASS (offline).**
  - The real broker invokes the CPM builder through the seam; the provider is open only during the
    callback (opens == closes).
  - Declared = requested = covered = admission folds. Admission is observed at `Cohort`
    construction.
  - Scale is exact.
  - An unsupported result fails closed and nothing is published. An omitted-coverage view is
    rejected by CPM validation.
  - Uncovered is never absent.
  - Payload and coverage are plain data. `estimated_bytes` exceeds payload + coverage (it includes
    the envelope).
  - Bounded reads retain nothing. `open_stage` holds exactly one lease and clears it on release;
    an uncovered stage query makes no acquisition.
  - The CPM modules import no provider/selection path, and app reachability excludes historical
    authority.
- **C7 — PASS (offline)** for five failures: no valid authority, stale sidecar, expected-generation
  rejection, runtime build rejection, and adapter contract failure. Paths covered:
  - health / scope build;
  - operation authorization;
  - Save, Update and Review;
  - the Fit held-stage path.

  Each gives no scope/absent rows, no Review write, no durable or native write, no historical
  fallback, and a lease baseline of 0. The Apply entry is covered through its authorization step
  (Step 3 static routing); the native Apply transaction was not executed.
- **C8 — PASS (offline).**
  - Scope build and reauthorization each use short lease/release pairs; the pure scope survives
    release.
  - Idle holds 0 leases; every durable write happens with 0 leases; Apply late verification holds
    0.
  - Fit holds exactly 1 per target and 0 when the next target is queued.
  - Stale and stage-Uncovered failures return to baseline.
  - Release failure is durably registered for both bounded reads and the stage (the Fit stops),
    then reconciled.
- **C9 — PASS (offline)**, all 10 steps. After G2, the G1 Review overrides do not override G2's
  positive resolution (Thigh → Body Morphs) or its conflict (Ghost).
- **C10 — PASS (offline) except one item.** Verified:
  - package resolution, origin, API and build;
  - canonical module identity;
  - `get_broker` singleton;
  - wrong-origin and same-name shadow refusals;
  - bootstrap formula equal to the Normalizer's;
  - the pinned Normalizer and CPM both reach the broker only via canonical `get_broker`
    (static).

  **Pending real-SFM coexistence proof:** CPM and the running production Normalizer obtaining the
  same process broker. That code path cannot run offline without substituting the decisive
  path, so it is not asserted.

## Unresolved
- **Real-SFM obligations (none converted to PASS):**
  - the §21 sessions;
  - the C10 same-process broker check;
  - the native Apply transaction/Undo;
  - the native Fit transaction/Undo per target, and target 1's Undo validity after a G2 stop;
  - real foreign-modal timing;
  - the **forced Apply** and **forced Fit** rollback-verification failure gates;
  - latency and retained-memory measurement.

  Nothing is deployed.
- Stale-scope UI presentation: undecided. `SidecarMissing` negative-fixture messaging: undecided.
- Cleanup of historical authority machinery and diagnostics: not started (by instruction).
  **K, L:** not started.
- Interim runtime layout: CPM modules in the MAINMENU `ChadChan3D` directory (untested; L owns
  the final layout).
- G18AN signatures are interpreter-specific; the 2.7.5 value is authoritative.
- `verify_py27_equivalence.py` was left unmodified.
- R3, R6, R9, R13: CLOSED. Suites 1, 3 and 4: PASS offline.

## Next
Milestone complete. Awaiting review. The remaining pre-K work is controlled real-SFM
qualification: §21, the C10 coexistence proof, and the forced Apply/Fit rollback failures. Then
cleanup and a focused post-cleanup regression. Not started.

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
