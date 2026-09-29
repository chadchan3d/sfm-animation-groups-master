# Ledger

## Coder gate
Before editing, compare the assignment with the Blueprint and this Ledger.
Verify the current code state and relevant claims.
If the assignment assumes unfinished work is complete, contradicts the
Blueprint, or expands scope, report the conflict before dependent edits.
Otherwise proceed with the assigned milestone.

## Current milestone
R14: isolate CPM's diagnostic ctypes prototypes (owner-approved), then deploy for the Session 1
completion pass. **Status: corrected and checked offline; deployed. R14 is PENDING real-SFM
confirmation (not CLOSED).**

## Current state
`master` at the Ledger commit that follows `2b8222a` (the R14 product fix), on top of `a033bd8`.

Files changed in `2b8222a`:
- `cpm/app/SFM_Character_Preset_Manager.py`: in `prod_resource_snapshot`, kernel32/psapi/user32
  now come from new, cached CPM-private `WinDLL` handles (`prod_private_windll`), never from the
  shared `ctypes.windll`;
- `cpm/convergence/tests/test_cpm_app_r14_ctypes_isolation.py` (new);
- `test_cpm_app_canonical_route.py`: adds `R14_CHANGED_TOP` to the cumulative bounded-edit set.

**App hashes:** old `945eab6c…af8a`, new `664a660c7b896d62ba6cab4c27427a0c6a12de9e29912e7b88526ccc2d8b178b`.
The new app is deployed to the Session 1 location, replacing only the app copy. The deployed
adapter, projection, probe v2 (`0722610a…`) and Normalizer (`1f4ec5a2…`) are unchanged.

Also unchanged: the baseline (`3326024d…`), the shared package, the adapter/projection and the
Master.

## Verified
- **R14 offline:**
  - **Embedded Python 2.7.5 (32-bit, SFM's architecture): 18/18.**
    - The pre-fix baseline `prod_resource_snapshot` mutates the shared prototypes and makes the
      verbatim Normalizer `contextualizer_process_memory_sample` return `ok=False`. This
      reproduces the field evidence.
    - The corrected app leaves every shared prototype untouched, and the Normalizer sample stays
      `ok=True`, even while the shared prototypes are polluted.
    - The logged fields are identical and numeric.
    - No authority, lease, scene or persistence names are touched.
    - Only `prod_resource_snapshot` changed beyond the convergence edits.
  - **Python 3.10 (64-bit): 15/15.** The second-consumer checks are not applicable there, because
    the Normalizer's un-prototyped calls only work in a 32-bit process.
  - No cross-interpreter digest applies, since the check sets differ by design.
  - The suite fails 15/18 against the app with the fix reverted.
  - **Process-global ctypes mutation: eliminated offline.**
- **Regression (Python 3.10 = 2.7.5, digests identical):**

  | Suite | Checks | Digest |
  |---|---|---|
  | Step 1 | 196 | `e72e3c84…` |
  | Step 2a | 205 | `02cf2200…` |
  | Step 2b | 83 | `f969a89b…` (new: the bounded set now includes R14) |
  | Step 3 | 108 | `a2d6d0d3…` |
  | Step 4 | 95 | `d065ae69…` |
  | Gates | 152 | `a9a3ef5f…` |

- **Session 1 first-run evidence is preserved** (R14 changes only diagnostic DLL handles):
  - PASS: startup, canonical path, historical route unused;
  - PASS: idle lease/provider;
  - PASS: Body Save; Expression Save/Update;
  - PASS: native Apply + Undo; no-op Apply; Expression Apply;
  - PASS: C10 same-process broker; sequential coexistence;
  - measured: latency and retention.

## Unresolved
- **R14:** PENDING real-SFM confirmation. Completion runbook §1 requires Normalizer `mem_ok=True`
  with CPM open.
- **Session 1 completion still needs** (`COMPLETION_RUNBOOK.md`):
  1. simultaneous coexistence + R14 telemetry + process memory (§1);
  2. Body Update (§2);
  3. Review/Reclassify, which needs a healthy-miss model and otherwise stays PENDING, fixture
     unavailable (§3);
  4. Clothing Fit + Undo, which needs a target with extra flexes and otherwise stays PENDING,
     fixture unavailable (§4).
- **Session 1 roll-up:**

  | Area | Status |
  |---|---|
  | Normal operation | PARTIAL |
  | Native Apply + Undo | PASS |
  | Fit + Undo | PENDING (fixture) |
  | C10 | PASS |
  | Coexistence | PARTIAL |
  | Resource/latency | PARTIAL |
- **Product identity strings** are unchanged from G18AN (K/L). The probe's timing leaves one
  test-only cached view.
- **Reserved for later:** Sessions 2–3 and the forced Apply/Fit rollback failures.
- Stale-scope UI and `SidecarMissing` messaging: undecided. Cleanup, K, L: not started.
- R3, R6, R9, R13: CLOSED. Offline: Suites 1–4 PASS; C7–C10 PASS.

## Next
Operator: run `real_sfm_qualification/cpm_session1/COMPLETION_RUNBOOK.md` with the redeployed
app. Its §1 closes coexistence and confirms R14 in one pass. Return the probe JSONL, the CPM log
and the Normalizer log. No Session 2 work.

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
