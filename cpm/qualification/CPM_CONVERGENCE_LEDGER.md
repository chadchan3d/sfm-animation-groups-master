# Ledger

## Coder gate
Before editing, compare the assignment with the Blueprint and this Ledger.
Verify the current code state and relevant claims.
If the assignment assumes unfinished work is complete, contradicts the
Blueprint, or expands scope, report the conflict before dependent edits.
Otherwise proceed with the assigned milestone.

## Current milestone
Real-SFM Session 1: reconcile the first run, fix the test-only probe, prepare a minimal
completion pass. **Status: reconciliation complete; Session 1 PARTIAL; completion pass awaits
the operator.**

## Current state
`master` at the Ledger commit that follows `c7bccaa`. That commit holds the reconciliation, probe
v2, the completion runbook and the corrected runbook, all in `real_sfm_qualification/cpm_session1/`.
No product code changed since `cefa882`.

Qualification deployment in `ChadChan3D`:

| File | SHA-256 |
|---|---|
| App | `945eab6c…` |
| Adapter | `e96e21b5…` |
| Projection | `9b077a1b…` |
| Probe v2 (replaced v1) | `0722610a…1fe` |
| Normalizer (unchanged) | `1f4ec5a2…` |

Master `ac45e5c1…`; package API `1.0.0-b2a`, build `package-boundary-corrected-2026-09-22`.

## Verified (real SFM, 2026-09-28, one process pid 25896; see `SESSION1_RUN1_RECONCILIATION.md`)
Models: `foxmccouldwm1` (40 literals) and `mia1` (108 literals; face 58, body 46, other 4; miss 0,
conflict 0).

| Item | Status |
|---|---|
| Startup / canonical scope / historical route unused | PASS |
| Idle lease/provider: 11 probes, leases 0, open 0, opens = closes | PASS |
| Body Save (×2), Expression Save, Expression Update: authorized before the durable write | PASS |
| Native Body Apply: 6 committed; 1 authorization each, before preflight; pinned postcommit verification ok; no authority access inside the transaction | PASS |
| Body Apply Undo: Undo depth back to 59; the next Apply re-changed the same 4 sides (log-evidenced) | PASS |
| No-op Apply: Undo count unchanged; "Already matches this preset." | PASS |
| Expression Apply: committed, verified | PASS |
| **C10 same-process broker:** one broker `0x30fd2a50` served `cpm_compat_v1` and `normalizer_compat` via the production paths | **PASS** |
| Normalizer coexistence (sequential, same process): Normalizer PASS; CPM reopened afterwards and Applied | PASS |

Measured latency and retention:
- **Scope build:** 1.539 s (40 literals, cold) and 1.173 s (108 literals, new vocabulary); 0.073 s
  when reopened from cache.
- **Action authorization:** 0.019–0.024 s (cache hit).
- **Stage open + release:** 0.017–0.024 s warm; 1.224 s cold.
- **Apply total:** 0.12–0.16 s committed; 0.06 s no-op. Save 0.06–0.11 s; Update 0.056 s.
- **Retention:**
  - CPM pure scope 165,633 B (deep size, 108 literals);
  - CPM views 47,303 B (40 literals) and 123,230 B (108 literals);
  - probe view 53,002 B;
  - Normalizer view 664,507 B;
  - broker ledger retained 888,042 B.
- **Process memory:** pre-CPM working set 3.01 GB, private 3.06 GB. It could not be read after CPM
  loaded (the probe defect).

## Unresolved
- **Remaining Session 1 obligations** (see `COMPLETION_RUNBOOK.md`):
  1. Body **Update**. PENDING, operator action not performed: the second Body operation was a
     Save.
  2. **Review/Reclassify.** PENDING, fixture unavailable: no model had a Needs-review item (0
     Master-unknown).
  3. Ordinary **Clothing Fit + Undo.** PENDING, fixture unavailable: no target had flexes absent
     from the source.
  4. **Simultaneous coexistence** (CPM open while the Normalizer runs, then still usable).
     PENDING, operator action not performed: CPM was closed first.
  5. **Process-memory measurement.** PENDING, probe defect. It is fixed in probe v2 and needs a
     rerun.
- **Session 1 roll-up:**

  | Area | Status |
  |---|---|
  | Normal operation | PARTIAL |
  | Native Apply + Undo | PASS |
  | Ordinary Fit + Undo | PENDING (fixture) |
  | C10 | PASS |
  | Coexistence | PARTIAL |
  | Resource/latency | PARTIAL |
- **R14 (new; owner decision needed): process-global ctypes prototype.** CPM sets `argtypes` on
  the shared `ctypes.windll.psapi.GetProcessMemoryInfo`. This is present in the G18AN baseline, so
  it is not a convergence regression.
  - After CPM runs, the production Normalizer's memory telemetry fails: `mem_ok=False` at 15/15
    checkpoints, against `True` without CPM.
  - It is telemetry only (VAS gating OK; Normalizer PASS).
  - The fix is a small CPM product change (a private `WinDLL`); not done here.
- **Product identity strings** (window slot, log name, `PROD_VERSION`) are unchanged from G18AN
  and shared by old builds (K/L).
- **Probe's own cache view:** the probe's timing leaves one extra cached view (53 KB, no lease).
  It is test-only.
- **Reserved for later:**
  - Session 2 (G1→G2 with CPM open, and during a prompt);
  - Session 3 (queued Fit G1→G2);
  - the forced Apply and Fit rollback-verification failures.
- Stale-scope UI presentation and `SidecarMissing` messaging: undecided. Cleanup, K, L: not
  started.
- R3, R6, R9, R13: CLOSED. Offline: Suites 1–4 PASS; C7–C9 PASS; C10 now fully PASS (its offline
  part and the real-SFM same-process check).

## Next
Operator: run `real_sfm_qualification/cpm_session1/COMPLETION_RUNBOOK.md`. Items 1–2 are always
possible; items 3–4 only with valid fixtures, otherwise record them as skipped. Owner: decide
R14. No Session 2 work.

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
