# Ledger

## Coder gate
Before editing, compare the assignment with the Blueprint and this Ledger.
Verify the current code state and relevant claims.
If the assignment assumes unfinished work is complete, contradicts the
Blueprint, or expands scope, report the conflict before dependent edits.
Otherwise proceed with the assigned milestone.

## Current milestone
CPM Convergence Step 2a: CPM-owned canonical authority adapter, offline qualification only.
Done = canonical bootstrap, provider-shaped facade (`generation_descriptor`, `query_many`),
migrated health, provenance mapping, expected-generation freshness and Suite 1
snapshot/signature parity, proven under Python 3 and 2.7.5 with no runnable CPM created.
**Status: complete and checked; awaiting review.**

## Current state
`master` at `bc09e95` (Step 2a), on top of `2a5285e` (Step 2 investigation) and `a52098e` (Step 1).
Step 2a code: `cpm/convergence/cpm_authority_adapter.py` and `tests/test_cpm_authority_adapter.py`.
There is no uncommitted work in `cpm/`. Frozen G18AN (`3326024d…`), the shared package, the
Normalizer snapshot (`1f4ec5a2…`), `tools/` and the canonical Master are unchanged.

## Verified
- Step 2a suite: 205/205 on Python 3.10 and on embedded 2.7.5; digests identical (`02cf2200…`).
  Step 1 suite: 196/196 on both.
- Bootstrap: the MAINMENU formula matches the Normalizer's (verbatim extraction) and the package
  bootstrap on 4 fixtures. Origin, module, API, build and `get_broker` failures fail closed.
- Health (R3 decision): canonical admission + requested-view validation only. A small valid Master
  (16 occurrences) is healthy. Corrupt or stale sidecars (`SidecarMissing`) and Uncovered requests
  are unavailable. MasterUnknown is genuine absence; conflict is not absence.
- Failures always raise `CpmAuthorityUnavailable` / `CpmGenerationMismatch`, never absence.
  Afterwards: no outstanding lease, no open provider, and no view in adapter state or tracebacks.
- Snapshot, pure-row, `semantic_snapshot_for_model_row` and Fit-warning results are identical
  whether fed by the adapter or by the G18AN oracle (plus hand-audited conflicts).
- 8 perturbations on scratch copies were all detected.

## Unresolved
- **Suite 1: PASS (offline, synthetic fixtures).** Real-SFM live-model parity (§21), Suites 2–4
  and gates C7–C10 are untested.
- G18AN signature values are interpreter-specific because they hash `repr()`: 2.7.5 `04e437b4…`,
  3.10 `7b63cbda…`. The 2.7.5 value is authoritative for SFM.
- **R13 (owner decision needed):** location and form of the G18AN-derived runnable CPM candidate.
  This blocks Step 2b.
- R6: behavior of late helpers that still reach the global provider. Open until a runtime route exists.
- R1: UI behavior for a stale scope is unspecified (Step 2b).
- Negative fixtures surface as `SidecarMissing`, not a more specific class. This is fail-closed;
  the messaging is still to be decided.
- `verify_py27_equivalence.py` is not runnable as-is. It was left unmodified; the two-interpreter
  digest technique is used instead.
- R3: CLOSED.

## Next
Milestone complete. Awaiting review and the R13 decision before Step 2b. Step 2b scope:
runnable candidate; adapter injected into `render → prod_scope`; migrated health predicate;
reroute `prod_current_provider_descriptor` and `prod_probe_semantic_provider`; stale-scope UI;
parity shortcut and TXT/AUTO unreachable; R6 fail-closed rule.

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
