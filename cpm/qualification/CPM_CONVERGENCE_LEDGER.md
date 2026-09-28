# Ledger

## Coder gate
Before editing, compare the assignment with the Blueprint and this Ledger.
Verify the current code state and relevant claims.
If the assignment assumes unfinished work is complete, contradicts the
Blueprint, or expands scope, report the conflict before dependent edits.
Otherwise proceed with the assigned milestone.

## Current milestone
CPM Convergence Step 2b: first runnable converged CPM source.
Done =
- canonical adapter wired into `render → prod_scope`;
- migrated health;
- `prod_current_provider_descriptor` / `prod_probe_semantic_provider` rerouted;
- historical route unreachable from production;
- §13 stale-generation rule plumbed;
- R6 late helpers fail closed;
- all offline-qualified.

**Status: complete and checked (offline); awaiting review.**

## Current state
`master`, Step 2b = two commits on top of `f351dc8`:
- `bcfa036`: byte-identical derivation of `cpm/app/SFM_Character_Preset_Manager.py` from G18AN
  (SHA `3326024d…`), with LF pinned.
- `7dea7d2`: the wiring commit: `cpm/app/SFM_Character_Preset_Manager.py`,
  `cpm/convergence/tests/test_cpm_app_canonical_route.py`, and this Ledger. A Ledger-only
  follow-up records this SHA.

Unchanged: the baseline, the shared package, the Normalizer snapshot, and `cpm/convergence/*.py`.

## Verified (offline only)
- Step 2b suite: 83/83 on Python 3.10 and on embedded 2.7.5; digests identical (`4faa7dc6…`).
  Step 1: 196/196; Step 2a: 205/205, both interpreters.
- Bounded derivation: vs the baseline, only 7 top-level definitions changed:
  - `prod_probe_semantic_provider`, `prod_current_provider_descriptor`;
  - `prod_live_bindings_for_cached_scope`, `prod_character_record`, `prod_ensure_character`;
  - `prod_scope`;
  - `ProdWindow`, in which only `guard`, `render`, `semantic_provider_ready` and the
    shortcut-binding method changed, plus 2 new methods.

  12 `prod_cpm_*`/`ProdCpm*` names were added; nothing was removed.
- Static reachability from `StartProdTool` + `ProdWindow`: none of the historical provider, TXT/AUTO,
  development-sidecar or parity-route names are reachable. The one exempt edge is
  `semantic_snapshot_for_model_row`'s `provider=None` default, which `prod_scope` never uses.
  The parity shortcut is unbound; its handler is retained.
- Route: health comes from canonical admission and the requested view. A small Master is healthy.
  Bootstrap, import, API, build and corrupt-sidecar failures give `unavailable`, as does Uncovered.
  Absence, conflict and unavailable stay distinct. Scope rows and signature equal the baseline
  pipeline, and the persisted capture fields are unchanged.
- §13: stale generation rejects before mutation. The scope is discarded, and one rebuild is
  scheduled through `select_model` (deferred while busy). The rebuilt scope is current. The rejected
  action is never replayed, and a new user action is required.
- No lease or open provider after any step; `render` drops the probe adapter.
- `prod_cpm_import_adapter` (child interpreter) loads only from the `sys.executable` MAINMENU and
  refuses a same-named module from elsewhere.
- 8 app perturbations on scratch copies were all detected.

## Unresolved
- **Real-SFM qualification not run** (§21). Nothing is deployed. Runtime latency is unmeasured:
  - live vocabulary is enumerated twice per selection;
  - a full Master hash runs on each readiness check.
- **R6 consequence (by design, blocks product use until Steps 3–4):** these fail closed with
  `ProdCpmAuthorityNotMigrated`, before any durable write:
  - Body/Expression **Save** (`prod_ensure_character`);
  - **Review/Reclassify** (`prod_set_override` / `prod_clear_override`);
  - the **Clothing Fit** unmatched-target warning query.

  Update and Apply reach no fail-closed helper. Note R9: their postcommit/abort identity checks now
  observe the Master fresh; this is a Step 3 item.
- **Interim runtime layout (untested, L owns final):** the app imports `cpm_authority_adapter` +
  `cpm_compat_v1_projection` from `<game>/usermod/scripts/sfm/mainmenu/ChadChan3D`.
- Stale-scope **UI presentation** is undecided. The rebuild reuses the existing `select_model`
  status behavior, so the rejection notice may be replaced by the rebuild's own status; the copy and
  disabled/refresh indication are not chosen.
- Suite 1: PASS offline. Suites 2–4 and C7–C10 are not run.
- G18AN signatures are interpreter-specific (`repr()`); the 2.7.5 value is authoritative.
- Negative fixtures surface as `SidecarMissing`; messaging is undecided.
- `verify_py27_equivalence.py` was left unmodified; the two-interpreter technique is used instead.
- The app inherits the baseline's hardcoded Public Documents log path and repository URL unchanged.
- R3: CLOSED. **R13: CLOSED:** canonical source `cpm/app/SFM_Character_Preset_Manager.py`, oracle
  `cpm/baseline/`, infrastructure `cpm/convergence/`, no disposable app copies, layout deferred to L.

## Next
Milestone complete. Awaiting review. The Blueprint's next step is Step 3 (CPM Operation Authority
Context). It lifts the R6 fail-closed refusals for Save and Review, and moves Update/Apply late
verification (R9) and post-prompt authorization onto the operation context. It is not started.

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
