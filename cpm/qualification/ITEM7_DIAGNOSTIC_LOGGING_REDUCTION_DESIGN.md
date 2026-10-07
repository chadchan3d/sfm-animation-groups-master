# CPM item 7 — diagnostic/development logging reduction (design)

**Design status: APPROVED FOR BOUNDED IMPLEMENTATION.**
**Implementation status: NOT STARTED.**

| | |
|---|---|
| Scope | Handoff §22 item 7 — remove unnecessary diagnostic/development logging (`docs/qualification/CPM_CONVERGENCE_INTEGRATION_HANDOFF.md`) |
| Governing starting checkpoint | `7b69b520a2472d3700ce347a1d2a59bc98e926f2` |
| Starting app SHA-256 | `1e8668717f9a4a1def0900c6b51e20cb9a7676cc365244eab5c31233f133eeeb` (`cpm/app/SFM_Character_Preset_Manager.py`, the item-6 offline-qualified candidate) |
| Provenance | Astra initial design → Claude adversarial review → Astra reconciliation; owner approved the reconciled revision. This records how the design was produced; it is not a new authority hierarchy. |
| Supersedes | Astra's initial item-7 design and the earlier uncommitted item-7 design investigation |
| Status authority | `cpm/qualification/CPM_CONVERGENCE_LEDGER.md` |

This document preserves Astra's reconciled item-7 design as the authoritative item-7 design. Its
technical decisions are reproduced unchanged; only formatting was normalized (workstation file
links and paths are given repository-relative, with the line numbers they cited at `7b69b52`). The
first-person voice below is Astra's reconciliation.

---

# Item-7 Diagnostic/Development Logging Reduction Design — Reconciled Revision

**Final design: retain the proposed logging reduction, narrow containment at the two product-sensitive locations, and make preservation and qualification mechanically checkable.**

One additional correction is necessary: preserve the original non-`Exception` startup failure when Python 2’s exception state has been changed by a contained diagnostic failure.

This revision supersedes the earlier item-7 design. It specifies future implementation only. No production files, tests, Ledger entries or deployment were changed. Item 8 has not begun.

## 1. Authority, synchronization and reconciliation result

I reverified:

| Authority | Result |
|---|---|
| Repository | `chadchan3d/sfm-animation-groups-master` (repository root) |
| HEAD | `7b69b520a2472d3700ce347a1d2a59bc98e926f2` |
| Item-6 app SHA-256 | `1e8668717f9a4a1def0900c6b51e20cb9a7676cc365244eab5c31233f133eeeb` |
| Item 6 | COMPLETE — offline qualification PASS |
| Item 7 | Not implemented |
| Item 8 | Not started |
| K/L | Not started |

The Ledger (`cpm/qualification/CPM_CONVERGENCE_LEDGER.md`) remains the status authority.

The design direction survives Claude’s review. The corrections principally concern containment, proof precision and evidence interpretation—not logging policy or authority architecture.

Two qualifications to Claude’s findings:

- I independently reproduce **88 wrapped callsites across 53 qualified emitting owners**, not 54. The explicit inventory below controls.
- Python 2 exception-state contamination is not always merely a traceback limitation. At `StartProdTool`’s final bare re-raise, it can change the exception that escapes. I reproduced that behavior using SFM’s **actual Python 2.7.5**.

No production candidate was constructed or qualified during this reconciliation.

## 2. Governing boundary and D1–D6

The purpose remains a release-appropriate diagnostic surface that preserves item-8 evidence without retaining unnecessary development instrumentation.

| Decision | Final disposition |
|---|---|
| **D1 — timing removal** | Remove the verified unused timing machinery, including inside Save/Update/Apply. This removes diagnostic-only failure paths while preserving intended product semantics and operation ordering. |
| **D2 — Q1 capture parity** | Retain disabled. Preserve comparisons, raises, context checks, branch and false default. Remove only its timing instrumentation. |
| **D3 — obsolete force/shortcut reporting** | Remove the startup report and its three exclusively used constants. Keep the inert window attribute. |
| **D4 — item-6 proof** | Run the historical test with checkpoint-compatible dependencies in a detached worktree. Do not repin it. Add an independent item-7 reconstruction proof. |
| **D5 — breadcrumbs** | Retain scope boundaries, selected-model context, operational outcomes and failures. Remove detailed UI/library progress and successful per-item dumps. No replacement breadcrumb is needed. |
| **D6 — item-8 contract** | Retain the existing proposed contract with the Python 2, product-coupled readiness, exact-build harness and measurement qualifications below. |

The three reporting-constant removals explicitly supersede item 6’s temporary RETAIN decision. Nothing else here reopens item 6.

## 3. Final exact REMOVE inventory

### 3.1 Timing machinery

Remove these definitions:

```text
prod_perf_seconds
prod_perf_log
astra_perf_timing
prod_action_timing
```

Remove:

```text
PROD_PERF_LOGGING
import time
```

Remove all **77 standalone timing calls**:

- 27 `prod_perf_log`;
- 26 `prod_action_timing`;
- 24 `astra_perf_timing`.

Remove their **72 exclusively used `time.time()` assignments**.

The exact affected owners are:

```text
prod_bs_index_snapshot
prod_validate_bone_scale_map
prod_bs_index_capture_map
prod_q1_compare_body_capture
prod_capture_body_snapshot
prod_capture_bone_scale_map
prod_build_bone_scale_plan
prod_verify_bone_scale_map
prod_save
prod_update_preset
prod_apply
ProdWindow.populate.work
ProdWindow.select_model.work
ProdWindow.render
ProdWindow.refresh_preset_view
ProdWindow.save_kind.work
ProdWindow.update_kind.work
ProdWindow.apply_kind.work
ProdWindow.refresh_fit_candidates
```

The timer-local names are:

```text
t_apply
t_apply_ui
t_bone_plan
t_bone_verify
t_bones
t_current
t_enum
t_flex_prepare
t_flex_verify
t_fresh_scope
t_mutation
t_parse
t_phase
t_plan
t_post_snapshot
t_prod
t_refresh
t_render_total
t_scope
t_snapshot
t_total
t_ui_total
t_validate
t_verify
```

This authorizes deletion of the pinned assignments, not general name-based cleanup.

No timer return value is consumed. All loaded timer values feed timing helpers. No legacy timing cleanup is necessary: **no legacy edits**.

Preserve `datetime`, run identity and event timestamps.

### 3.2 Direct logging removals

Remove exactly these **46 callsites**:

| Owner | Removed record | Count |
|---|---|---:|
| `StartProdTool` | Fixed `ARCHITECTURE`, `G18AN_ANIMSET_RENAME_RESILIENCE`, `G18AN_FOREIGN_MODAL_YIELD`, `SIDECAR_STATUS`, `G18AN_WINDOW_POLICY` prose | 5 |
| `StartProdTool` | `G18AN_PROVIDER_FORCE_MODE … parity_shortcut=…` | 1 |
| `tool_window_icon` | `PROD_WINDOW_ICON status='embedded-loaded'` only | 1 |
| `prod_bs_index_capture_map` | `Q3_SCALE_CAPTURE_ACCEPT` | 1 |
| `ProdWindow.refresh_preset_view` | All `PROD_PRESET_UI` records | 10 |
| `ProdWindow.render` | Eleven detailed stages listed below | 11 |
| `ProdWindow.refresh_fit_candidates` | `CLOTHING_FIT_CANDIDATES` | 1 |
| `ProdWindow.clear_model_selection` | `PROD_MODEL_CLEAR=PASS` | 1 |
| `ProdWindow.save_kind.work` | `PROD_SAVE_POSTWRITE_REFRESH=PASS` | 1 |
| `ProdWindow.update_kind.work` | `PROD_UPDATE_POSTWRITE_REFRESH=PASS` | 1 |
| `ProdWindow.toggle_favorite.work` | `PROD_FAVORITE_UI_REFRESH=PASS` | 1 |
| `ProdWindow.delete_kind.work` | `PROD_DELETE_POSTMOVE_REFRESH=PASS` | 1 |
| `ProdWindow.open_details.work` | `PROD_DETAILS=PASS` | 1 |
| `ProdWindow.open_preset_info.work` | `PROD_PRESET_INFO=PASS` | 1 |
| `ProdWindow.open_help.work` | `PROD_HELP_OPEN=PASS` | 1 |
| `ProdWindow.operation_begin` / `operation_end` | `G18AN_OPERATION_PROVIDER_STATE` and corresponding `_ERROR` | 4 |
| `ProdWindow.render` | `G18AN_LIVE_SELECTION_PROVIDER_STATE` and `_ERROR` | 2 |
| `ProdWindow.closeEvent` | `G18AN_CLOSE_PROVIDER_STATE` and `_ERROR` | 2 |

Remove these eleven `PROD_MODEL_SWITCH_STAGE` values:

```text
body-library-begin
body-library-ready
expression-library-begin
expression-library-ready
library-meta-begin
library-meta-ready
library-validated
preset-ui-begin
preset-ui-ready
scope-ui-ready
fit-ui-ready
```

Also remove:

- The accepted-path `diagnostic = prod_bs_capture_trace_diagnostic(trace)` and following `diagnostic = None` associated exclusively with `Q3_SCALE_CAPTURE_ACCEPT`.
- `kind_label` in `refresh_preset_view`, whose consumers are all removed.
- The four complete logging-only `try/except` constructs containing the eight historical-provider-state records.

Do not remove rejection diagnostics, scale classification, native reads, validation, UI work or data used by product behavior.

### 3.3 Reporting constants

Remove:

```text
SEMANTIC_PROVIDER_MODE_SIDECAR
SEMANTIC_PROVIDER_FORCE_MODE
G18AN_PARITY_SHORTCUT
```

Keep unchanged:

```text
self.g18an_parity_shortcut = None
```

### 3.4 Exactly two payload substitutions

**`PROD_MODELS`:**

Replace its format and argument tuple with the compact equivalent:

```text
PROD_MODELS count=%d initial_index=%d
```

Remove only the `candidates=%r` field and third tuple element/list comprehension.

**Fit result:**

Replace:

```text
CLOTHING_FIT_RESULT=PASS generation=
```

with:

```text
CLOTHING_FIT_RESULT generation=
```

Preserve all remaining fields, argument expressions, accounting and placement.

This corrects an unconditional success label; it does not introduce a new success predicate.

## 4. Final RETAIN inventory

**Every callsite not explicitly removed or rewritten remains.** The lists below name the required production evidence; they do not authorize deleting an omitted legacy record.

Except for approved containment and the two payload substitutions, preserve event text, arguments and ordering.

### Sink, identity and lifecycle

```text
reset_log
log_line
OUTPUT_PATH
PROD_OUTPUT_PATH
PROD_RUN_ID
PROD_PID

G18AN_RUN
PROD_R15_MODULE
PROD_R15_WINDOW_REUSED
PROD_R15_LAUNCH_REFUSED
PROD_R15_SLOT_CLEARED
PROD_R15_STARTUP_FAILED_RESTART_REQUIRED
PROD_WINDOW_SHOWN
MAINMENU_CALLBACK_RETURNING
PROD_OPEN_FAIL
PROD_CLOSE_REQUEST
PROD_CLOSE_FINALIZED
```

Retain the tool/version startup line and separators.

### Authority and generation

```text
P01_MASTER_PATH
PROD_PROVIDER_HEALTH
PROD_PROVIDER_GATE
PROD_SELECTION_PROVIDER_GATED
PROD_PROVIDER_REVIEW_WARNING

PROD_CPM_GENERATION_CHECK_FAILED
PROD_CPM_UNMIGRATED_AUTHORITY_REFUSED
PROD_CPM_OPERATION_AUTHORIZED
PROD_CPM_OPERATION_AUTHORIZATION_REFUSED
PROD_CPM_STALE_GENERATION_REBUILD_SCHEDULED
PROD_CPM_STALE_GENERATION_REBUILD

PROD_CPM_FIT_STAGE_OPEN
PROD_CPM_FIT_STAGE_REFUSED
PROD_CPM_FIT_STAGE_RELEASED
```

### Operations, persistence and recovery

```text
PROD_OPERATION_BEGIN
PROD_OPERATION_PHASE
PROD_OPERATION_END
PROD_OPERATION_EVENT_TURN
PROD_OPERATION_BEGIN_FAIL
PROD_ACTION_ERROR

PROD_SAVE
PROD_UPDATE
PROD_APPLY
PROD_DELETE
PROD_FAVORITE_SET
PROD_OVERRIDE_SET
PROD_OVERRIDE_CLEAR
PROD_REVIEW_REFRESH
PROD_RECLASSIFY_REFRESH

PROD_APPLY_ABORT_VERIFY
PROD_CLOTHING_FIT_ABORT_VERIFY

P02_STORAGE_FAILURE_STATE
PROD_LIBRARY_ROOT_MIGRATION
PROD_LIBRARY_MALFORMED
PROD_LEGACY_SKIP
PROD_FAVORITE_CLEANUP_WARNING
PROD_DELETE_PROFILE_CLEANUP_WARNING
```

Preserve traceback emissions, subject to the interpretation limitation in §12.

`PROD_SAVE=PASS` and `PROD_UPDATE=PASS` remain: they follow actual persistence/readback work. Their names alone do not prove correctness.

### Context and scope progress

```text
PROD_MODELS
PROD_MODEL_CLEAR_BEGIN
PROD_SELECTION
PROD_LIBRARY
G18AN_ANIMSET_RENAME_RESOLVED
G18AN_ANIMSET_METADATA_REFRESH
G18AN_STALE_COMBO_NAME_REFRESH
```

Retain precisely these `PROD_MODEL_SWITCH_STAGE` values:

```text
scope-begin
scope-ready
scope-ui-unavailable
```

No new scope/UI-ready event is needed. `PROD_SELECTION` and `PROD_SELECTION_PROVIDER_GATED` already cover the corresponding publication paths.

### Fit and modal coordination

```text
CLOTHING_FIT_START
CLOTHING_FIT_START_FAIL
CLOTHING_FIT_STAGE
CLOTHING_FIT_STAGE_CANCEL_AFTER_COMMIT
CLOTHING_FIT_FAIL
CLOTHING_FIT_RESULT

G18AN_FIT_FAILURE_DIALOG
G18AN_POST_FIT_ACTION_STATE
G18AN_MODAL_WATCHER_STARTED
G18AN_MODAL_YIELD_ENTER
G18AN_MODAL_YIELD_EXIT
G18AN_MODAL_DEFER_FIT
G18AN_MODAL_RESUME_FIT
G18AN_OPERATION_BLOCKED_MODAL
```

**Important correction:** `G18AN_POST_FIT_ACTION_STATE` is product-coupled. Its `self.semantic_provider_ready()` argument can inspect authority and schedule a stale-generation rebuild. Keep the entire statement byte-identical and outside new diagnostic containment.

### Resource and diagnostic support

Preserve byte-for-byte:

```text
prod_resource_snapshot
prod_private_windll
_PROD_PRIVATE_WINDLL
```

Preserve every resource callsite and label, including all existing `Q2_*` checkpoints and:

```text
MODEL_RENDER_BEFORE_SCOPE
MODEL_RENDER_AFTER_SCOPE
```

Retain:

```text
PROD_RESOURCE
PROD_RESOURCE_NATIVE_UNAVAILABLE
Q3_SCALE_CAPTURE_REJECT
```

Retain `prod_operation_event_turn_sample`, its scheduling, `undo_state`, `same_time_refresh`, their product work and dynamic records.

Retain icon-failure records and `PROD_HELP_MASTER_LINK`.

### Historical telemetry and Q1

Preserve:

```text
_SEMANTIC_PROVIDER
_SEMANTIC_PROVIDER_OPEN_COUNT
_SEMANTIC_PROVIDER_REUSE_COUNT
_SEMANTIC_PROVIDER_INVALIDATION_COUNT
_SEMANTIC_PROVIDER_PRODUCTION_PARSE_COUNT
_SEMANTIC_PROVIDER_GENERATION
semantic_provider_runtime_stats
```

Preserve:

```text
PROD_Q1_INDEXED_CAPTURE_PARITY = False
prod_q1_compare_body_capture
Q1_CAPTURE_PARITY
```

Preserve the capture branch, comparisons, raises, context checks, Save/Update parity fields and `G18AN_RUN parity_oracle=`. Only their timing instrumentation is removed.

## 5. Final DEFER inventory

Do not undertake:

- Q1 comparison removal or extraction.
- General legacy UI/helper cleanup.
- Historical telemetry removal.
- Removal of the inert shortcut attribute.
- Logging frameworks, buffering, rotation, verbosity settings or asynchronous emission.
- Further resource-instrumentation reduction.
- General event-prefix renaming.
- Separation of product work from `G18AN_POST_FIT_ACTION_STATE`.
- Refactoring `p02_safe_write_json` exception handling.
- The Session 4 Fit release-path repair.
- Stale-scope UI, `SidecarMissing` messaging or other deferred UI work.
- Product/window-slot naming.
- Item 8, K or L.

These are not automatically new mandatory milestones.

## 6. Exact containment rule and inventory

### 6.1 Selection rule

After the removals and payload substitutions:

- Wrap every surviving standalone `log_line` statement in the emitting-owner inventory below whose argument is nonconstant.
- Exclude `p02_safe_write_json` entirely.
- Exclude the complete `G18AN_POST_FIT_ACTION_STATE` statement.
- Exclude the six constant-expression callsites listed below.
- Leave R14’s resource implementation unchanged.

The wrapper is exactly:

```python
try:
    <original logging statement>
except Exception:
    pass
```

No product statements may enter it.

For `Q3_SCALE_CAPTURE_REJECT`, the protected region contains exactly:

1. Its diagnostic-construction assignment.
2. Its logging statement.

Keep `diagnostic = None` and the qualified product `raise` outside the wrapper.

### 6.2 Constant-expression exclusions

Exactly six:

```text
tool_window_icon:
    status='embedded-load-failed'
    status='embedded-null'

ProdWindow.closeEvent:
    PROD_CLOSE_FINALIZED=True

StartProdTool:
    first "=" * 120 separator
    MAINMENU_CALLBACK_RETURNING=True
    final "=" * 120 separator
```

These arguments contain no runtime-dependent formatting. The unchanged real sink remains responsible for its own I/O failures.

### 6.3 Exact emitting-owner inventory

**88 wrapped callsites across 53 qualified owners.**

Top-level owners and wrapper counts:

```text
StartProdTool                         8
p01_master_path                      1
prod_abort_apply_and_verify          1
prod_abort_fit_and_verify            1
prod_apply                           4
prod_bs_index_capture_map            1
prod_clear_override                  1
prod_cpm_authorize_operation         2
prod_cpm_open_fit_stage               2
prod_cpm_release_fit_stage            1
prod_cpm_scope_generation_stale       1
prod_cpm_unmigrated_authority         1
prod_discover                        2
prod_move_current_preset_to_trash     3
prod_operation_event_turn_sample     1
prod_prepare_library_root            2
prod_probe_semantic_provider         3
prod_q1_compare_body_capture         1
prod_r15_result                      1
prod_r15_window_decision              1
prod_resolve                         1
prod_save                            1
prod_set_favorite                    1
prod_set_override                    1
prod_update_preset                   1
same_time_refresh                    1
tool_apply_window_icon               1
tool_window_icon                     1
undo_state                           1
```

`ProdWindow` owners and counts:

```text
__init__                                  1
apply_provider_unavailable_to_ui           1
clear_model_selection                     1
closeEvent                                1
fit_finish                                1
fit_selected                              2
fit_show_partial_failure                  1
fit_stage                                 6
guard                                     4
open_master_page                          1
operation_begin                           2
operation_end                             1
operation_mark_phase                      1
poll_foreign_modal                        2
populate.work                             1
prod_cpm_request_stale_rebuild_if_needed    1
prod_cpm_run_stale_rebuild                 1
refresh_animset_display_metadata          1
reload_library_cache                      1
render                                    6
resume_scene_activity_after_foreign_modal  1
review_decision.work                      1
review_reclassify.work                     1
select_model.work                         1
```

**Correction to the table above:** `fit_selected` has **three** wrappers: `CLOTHING_FIT_START`, `CLOTHING_FIT_START_FAIL`, and its following traceback emission. Its authoritative count is **3**. Thus the totals remain **88 callsites, 53 owners**.

The manifest must reproduce these exact totals and identify individual statements by owner, event/shape and ordinal. Do not count the `ProdWindow` class container as another emitting owner.

### 6.4 Compound physical lines

At the existing compound startup lines:

- Split surviving statements onto separate lines.
- Preserve their original order.
- Preserve product expressions unchanged.
- Wrap only eligible logging statements.

In particular, window construction, slot publication, `show`, `raise_` and `activateWindow` must remain outside diagnostic wrappers.

### 6.5 The two containment exclusions

**`p02_safe_write_json`: keep the whole function byte-identical.**

Its failure log precedes a bare `raise`. Adding an inline handled exception can change which exception Python 2 re-raises. Item 7 will not refactor this persistence primitive.

**`G18AN_POST_FIT_ACTION_STATE`: keep the statement byte-identical.**

The readiness path (`cpm/app/SFM_Character_Preset_Manager.py` line 27540) performs product work. Containing it would suppress more than diagnostic failure.

These exclusions mean item 7 does **not** claim universal exception isolation for every historical log-shaped expression. It hardens the enumerated diagnostic-only surface while preserving those product-sensitive boundaries.

### 6.6 Additional Python 2 startup correction

At the existing final branch in `StartProdTool` (`cpm/app/SFM_Character_Preset_Manager.py` line 33287):

```text
if not isinstance(exc, Exception):
    raise
```

Replace only the bare re-raise with explicit re-raising of the captured exception:

```text
raise exc
```

Do not change the condition, cleanup, state transitions or ordering.

Why this is required:

- Under SFM Python 2.7.5, an inline contained diagnostic failure can replace the currently handled exception.
- The existing bare `raise` can consequently propagate that diagnostic error instead of the original `KeyboardInterrupt` or other non-`Exception` failure.
- Explicitly raising `exc` preserves the original exception object and type.

This is a logging-failure correction within the existing startup handler, not a new R15 lifecycle policy. Exact propagated traceback formatting is not preserved by this change; the original formatted diagnostic captured before logging remains unchanged.

## 7. Exact canonical-route test changes

The following sets are **increments to the existing baseline-relative inventories**, not the complete item-7 changed-function list.

### `ITEM7_CHANGED_TOP` — 20

```text
p01_master_path
prod_abort_fit_and_verify
prod_bs_index_capture_map
prod_bs_index_snapshot
prod_build_bone_scale_plan
prod_capture_body_snapshot
prod_capture_bone_scale_map
prod_discover
prod_move_current_preset_to_trash
prod_operation_event_turn_sample
prod_prepare_library_root
prod_q1_compare_body_capture
prod_resolve
prod_set_favorite
prod_validate_bone_scale_map
prod_verify_bone_scale_map
same_time_refresh
tool_apply_window_icon
tool_window_icon
undo_state
```

Merge this into **`EXPECTED_CHANGED_TOP` itself**. R14 imports that cumulative set; a detached item-7 set is insufficient.

`StartProdTool` already belongs to the cumulative changes. The explicit startup re-raise correction therefore needs no additional baseline-relative name, but must be covered by the item-7 reconstruction proof.

### `ITEM7_REMOVED_TOP` — 8

```text
prod_perf_seconds
prod_perf_log
astra_perf_timing
prod_action_timing
PROD_PERF_LOGGING
SEMANTIC_PROVIDER_MODE_SIDECAR
SEMANTIC_PROVIDER_FORCE_MODE
G18AN_PARITY_SHORTCUT
```

Require exact removals:

```text
ITEM6_REMOVED_TOP | ITEM7_REMOVED_TOP
```

### `ITEM7_CHANGED_METHODS` — 24

```text
apply_kind
apply_provider_unavailable_to_ui
clear_model_selection
delete_kind
fit_finish
fit_show_partial_failure
open_details
open_help
open_master_page
open_preset_info
operation_begin
operation_end
operation_mark_phase
poll_foreign_modal
populate
refresh_animset_display_metadata
refresh_fit_candidates
refresh_preset_view
reload_library_cache
resume_scene_activity_after_foreign_modal
save_kind
select_model
toggle_favorite
update_kind
```

Union these with the existing changed-method expectations. Preserve existing added/removed-method expectations.

For unnamed top-level statements, explicitly account for removing exactly one `import time`. Do not weaken the comparison by ignoring imports generally.

The R14 suite remains unchanged.

## 8. Exact implementation allowlist and no-touch boundary

### Allowed files

| File | Allowed purpose |
|---|---|
| Canonical app (`cpm/app/SFM_Character_Preset_Manager.py`) | Only the specified transformations |
| Canonical-route test (`cpm/convergence/tests/test_cpm_app_canonical_route.py`) | Exact cumulative inventories and explicit import removal |
| `cpm/convergence/tests/test_cpm_app_logging_cleanup.py` | New item-7 proof and qualification |
| `cpm/convergence/tests/item7_precleanup_source_manifest.json` | Pinned pre-edit transformation manifest |
| `cpm/qualification/ITEM7_DIAGNOSTIC_LOGGING_REDUCTION_DESIGN.md` | This approved design, when authorized to record it |
| `cpm/qualification/ITEM7_DIAGNOSTIC_LOGGING_REDUCTION_EVIDENCE.md` | Actual identities, results and limitations |
| Ledger (`cpm/qualification/CPM_CONVERGENCE_LEDGER.md`) | Exact-build status and explicit supersessions |

New offline outputs may be stored under one designated item-7 evidence directory. Historical outputs must not be overwritten.

### Forbidden changes

Preserve:

- Launcher and deployment.
- Frozen G18AN baseline.
- Adapter and `cpm_compat_v1` projection.
- Shared authority, broker, bootstrap, reader and lifecycle.
- Normalizer.
- Master and sidecar artifacts/generation rules.
- Preset formats.
- Classification, scope, mutation, persistence and rollback semantics.
- Authority acquisition/release boundaries.
- Fit stage-release behavior.
- R14 implementation.
- Item-6 test, manifest, design and evidence.
- Existing R15 and other convergence suites.
- Historical Sessions 1–4 harnesses, pins, reports and raw evidence.
- UI, naming and K/L work.

No deployment, hot reload or real-SFM item-8 activity is authorized here.

## 9. Exact historical item-6 proof procedure

For the future implementation campaign:

1. Create a detached worktree at:

   `7b69b520a2472d3700ce347a1d2a59bc98e926f2`

2. Inside it, assert these exact SHA-256 values:

| File | SHA-256 |
|---|---|
| App | `1e8668717f9a4a1def0900c6b51e20cb9a7676cc365244eab5c31233f133eeeb` |
| Item-6 cleanup test | `a3024d3404c3d3db3905218343fdf1e931a58c782e0599d810f55427467820fe` |
| Item-6 manifest | `a92647949f26f02c65497b4f0e808413edbe54af72eec8b1bee65798cdd2c6ae` |
| Canonical-route test | `29ae0e8433c9c50ee469944dbd00df340f0b517f30a4f55ce74fb0fd3bf80686` |

3. Run the untouched item-6 test **from that worktree**, under Python 2.7.5 and 3.10.

4. Unset `CPM_TEST_APP_PATH`; ensure imports resolve to that worktree’s test dependencies, not the developing item-7 tree.

5. Record outputs as **historical item-6 confirmation**, not candidate qualification.

6. Use the same verified app file as the item-7 reconstruction input. Keep the worktree until all comparisons requiring it finish.

7. Remove the temporary worktree only after confirming it contains no work that must be preserved.

The item-7 test must require an explicit reference-app path and validate its hash. It must never silently substitute the current candidate. Reproducing the qualification later requires recreating this pinned reference.

No worktree was created during this review.

## 10. Exact preservation and reconstruction method

### Manifest generation

Generate once, **before production edits**, from the verified item-6 source. Refuse a wrong hash or an existing manifest.

For each transformation record:

- qualified owner;
- transformation kind;
- event/tag, timer name or statement shape;
- ordinal within that owner;
- exact original source digest;
- relevant expected argument/statement structure.

Line numbers may be reported for navigation but must not identify transformations.

Record untouched block hashes and top-level/class-member ordering.

### Allowed reconstruction operations

Apply only:

1. Exact timing-call deletions.
2. Exact timer-assignment deletions.
3. Named definition/constant/import removals.
4. The 46 log deletions and their specified logging-only enclosing constructs.
5. The accepted-path diagnostic and `kind_label` deletions.
6. The two declared payload substitutions.
7. The 88 exact diagnostic wrappers.
8. The special rejection-diagnostic wrapper.
9. The one `StartProdTool` bare-raise → `raise exc` substitution.

No generic dead-code elimination or “ignore diagnostics” normalization.

### Comparison

Under **each interpreter separately**:

1. Parse the pinned input.
2. Apply the manifest transformations to its AST.
3. Parse the candidate.
4. Compare complete reconstructed and candidate ASTs using location-independent `ast.dump` under that same interpreter.
5. Require blocks with no approved transformation to remain byte-identical.
6. Require the excluded `G18AN_POST_FIT_ACTION_STATE` statement and all of `p02_safe_write_json` to remain byte-identical.
7. Require unchanged protected-component hashes.

Use the interpreter’s own parsed wrapper template so Python 2 and Python 3 AST node differences do not require a second semantic comparator.

Changed-block formatting may accommodate the required statement splits and indentation. Do not authorize unrelated comment edits or formatting sweeps.

### Coverage beyond the old derivation test

The reconstruction covers the entire module, including post-baseline functions such as:

```text
prod_cpm_authorize_operation
prod_cpm_open_fit_stage
prod_cpm_release_fit_stage
prod_cpm_scope_generation_stale
prod_cpm_unmigrated_authority
prod_r15_result
prod_r15_window_decision
```

Their classification as “added” in an older test must not exempt their contents from preservation.

Manifest expectations must never be regenerated from the edited candidate.

## 11. Exact item-7 qualification gates

### 11.1 Existing suites

Run all eight existing convergence suites under Python 2.7.5 and Python 3.10:

```text
test_cpm_compat_v1_projection.py
test_cpm_authority_adapter.py
test_cpm_app_canonical_route.py
test_cpm_app_operation_context.py
test_cpm_app_clothing_fit.py
test_cpm_convergence_gates.py
test_cpm_app_r14_ctypes_isolation.py
test_cpm_app_r15_namespace_isolation.py
```

Use their established phase procedures.

Require available real PySide/Qt coverage under 2.7.5 as well as model coverage. Label Python 3.10 model results accurately.

### 11.2 Preservation and closure

Require:

- Exact reconstruction equality.
- 77 timing calls and 72 timer assignments removed.
- 46 direct log removals.
- Eight named top-level removals plus explicit `import time` removal.
- Exactly 88 wrappers across the specified 53 owners.
- Exact retained-event forms and placement.
- No dangling production references to removed symbols.
- No new production import, callback, logging owner, timer or retained state.
- Continuing item-6 refusal, absence and canonical-route guarantees.

### 11.3 Diagnostic failure injection

In the new test namespace, replace `log_line` with a controlled function that raises `RuntimeError` for one selected event at a time.

Require:

- Each wrapped callsite structurally contains the emitter failure.
- Representative real product functions continue through their expected return, cleanup or failure handling.
- Successful operations retain their product results.
- Product failures retain their intended classification and recovery path.
- Mutation, persistence, authorization and release traces are unchanged except for approved diagnostics.

Also use a diagnostic argument whose `__repr__` raises. This exercises failure **before** entry to the sink.

Do not claim that no-op logger stubs bypass argument formatting: Python evaluates arguments before calling even a no-op stub. The new injection adds deliberate failing cases.

Test the real `log_line` separately for open/write/flush/close failure. Do not require the six unwrapped constant records to survive an artificially replaced throwing sink; that is outside their actual sink contract.

For excluded sites, compare against item-6 behavior rather than demanding newly introduced containment.

### 11.4 Python 2 product-handler continuity

Under actual Python 2.7.5, inject failures at:

```text
PROD_OPERATION_BEGIN_FAIL
PROD_ACTION_ERROR
CLOTHING_FIT_START_FAIL
CLOTHING_FIT_FAIL
```

Require the original handler’s product actions to continue correctly.

Do not require a subsequent `traceback.format_exc()` to describe the original failure after the injected logging exception. Explicit exception objects, operation state and independent action traces are the relevant oracles.

### 11.5 Real `fit_finish` coverage

Do not use the existing harness’s `fit_finish` stub for this gate.

Execute the real:

```text
fit_finish
semantic_provider_ready
prod_cpm_request_stale_rebuild_if_needed
```

with controlled external authority/Qt collaborators and a stale scope.

Require:

- the readiness path still runs;
- stale rebuild is requested;
- the pending flag and queued callback are correct;
- no action replay is introduced;
- ordinary completion still reaches its existing operation-end path.

Include a focused fixture that isolates the final post-Fit readiness call so an earlier readiness call cannot make the test pass after accidental removal of the product-coupled statement.

A scheduling failure must retain baseline propagation behavior; the new diagnostic wrappers must not swallow it.

### 11.6 R15 startup outcomes

Reuse the R15 harness environment from the **new item-7 test**, leaving the R15 suite unchanged.

Require:

| Injected diagnostic failure | Expected candidate behavior |
|---|---|
| `G18AN_RUN` or `PROD_R15_MODULE` | Otherwise successful startup remains `created` |
| `PROD_WINDOW_SHOWN` | Successfully constructed window survives; no diagnostic-induced restart latch |
| `PROD_OPEN_FAIL` during a real ordinary startup failure | Existing construction-dependent state/cleanup completes; no stuck `STARTING` |
| Logging failure while handling a non-`Exception` `BaseException` | Original captured exception object/type escapes after existing cleanup |

Test the last row both with and without an injected logging failure.

Normal startup, reuse, refusal, close/reopen and genuine construction-failure policies remain unchanged. Diagnostic-only startup failures intentionally cease to masquerade as product startup failures.

### 11.7 Sensitivity

Deliberately altered candidates must be rejected for:

- changed product predicate;
- omitted validation or release;
- widened diagnostic handler;
- changed retained event;
- wrapped/deleted product-coupled readiness statement;
- altered `p02_safe_write_json`;
- unexpected removal;
- missing explicit startup exception preservation;
- edited post-baseline helper.

No real-SFM item-7 campaign is required. That remains item 8.

## 12. Final item-8 observability contract

Item 8 must receive the final candidate hash, preserved-component hashes, manifest identity, offline results, event inventory and these interpretation rules.

### Required evidence

| Question | Evidence |
|---|---|
| Which build/process/window ran? | Verified deployment hashes, `G18AN_RUN`, `PROD_R15_MODULE`, lifecycle events |
| Was authority available and current? | Provider-health, authorization/refusal events and independently observed scope/generation |
| Did an action mutate or persist? | Operation phases/outcomes plus scene or file observations |
| Did recovery verify? | Abort-verification records, recovery classification and independent state |
| Which Fit targets changed or stopped? | Stage events, committed state, result counters and failure accounting |
| Was ownership released? | Release records where emitted plus actual broker/stage observations |
| Did lifecycle remain sound? | Actual window/watcher/state observations and lifecycle events |
| Was historical authority unused? | Preserved globals inspected by the probe |
| What resource behavior occurred? | Retained resource checkpoints and settled observations |

### Exact additions and limitations

1. **Match the new Fit record as:**

   ```text
   CLOTHING_FIT_RESULT generation=
   ```

   Do not accept historical `CLOTHING_FIT_RESULT=PASS` as the new format.

2. **Scope-acquisition timing:** if still needed, the timestamps of `MODEL_RENDER_BEFORE_SCOPE` and `MODEL_RENDER_AFTER_SCOPE` provide a bounded elapsed interval around provider probing and scope construction.

   Report it as a **resource-event bracket**, including diagnostic overhead—not an exact equivalent of the deleted `ASTRA_PERF` timer or a directly interchangeable historical measurement.

3. **Historical harnesses remain exact-build tools.** Session 4 pins `9a78fc96…`, definition lines and an old Fit-result assertion. Do not repin those historical files. Any reuse in item 8 requires a separately authorized new revision for the new build; this does not itself mandate repeating Session 4.

4. **Python 2 traceback caveat:** following an inline contained logging failure, a subsequent traceback record may describe that logging failure. Do not infer the original product fault solely from it.

5. **Product-coupled readiness:** `G18AN_POST_FIT_ACTION_STATE` can perform authority checking and stale-rebuild scheduling. It is not a passive observation.

6. **Fit release limitation remains separate.** The existing exception path can release without `PROD_CPM_FIT_STAGE_RELEASED`. Missing output does not prove missing release. Item 7 does not repair that path.

7. Logs support qualification; they do not independently prove no mutation, no acquisition, successful rollback or absence of a lease.

8. A logging failure must not be treated as product success evidence. It may make a qualification observation inconclusive even when product behavior continued correctly.

9. Fixed fields such as `pure_scope=True` remain implementation assertions, not independent measurements.

10. Fit callback `generation` and authority `gfit` remain distinct identities.

## 13. Exact-build Ledger wording

At implementation start:

> **§22 item 7 — IN PROGRESS: diagnostic/development logging reduction.**\
> Starting checkpoint: `7b69b520a2472d3700ce347a1d2a59bc98e926f2`.\
> Starting app: `1e8668717f9a4a1def0900c6b51e20cb9a7676cc365244eab5c31233f133eeeb`.\
> Item 6 remains COMPLETE with its original qualification. No item-7 deployment or post-cleanup real-SFM qualification has occurred.

Only after all required offline gates pass:

> **§22 item 7 — COMPLETE: diagnostic/development logging reduction; offline qualification PASS.**\
> Candidate app SHA-256: `<measured hash>`.\
> The approved timing/log removals, two payload corrections and bounded diagnostic-failure handling are complete. Product-coupled post-Fit readiness and `p02_safe_write_json` were preserved. Startup preserves the original non-`Exception` failure after contained diagnostic errors.\
> Historical item-6 qualification was confirmed using checkpoint-compatible dependencies. Item-7 preservation was independently proven against the pinned item-6 source.\
> Sessions 1–4 qualify only app `9a78fc96…`. The new candidate does not inherit their exact-build real-SFM PASS.\
> Candidate not deployed. Item 8 is next; K/L remain not started.

Record the reporting-constant supersession and the retained disabled Q1 decision explicitly. Preserve historical reports unchanged.

## 14. Risks and stop conditions

Stop and report if:

- Any specified count or source identity differs.
- A newly identified diagnostic argument performs required product work.
- A wrapper would contain validation, mutation, persistence, release or scheduling.
- Preservation requires ignoring an entire changed function.
- A Python 2 handler’s escaped exception or intended product outcome changes beyond the declared diagnostic corrections.
- The excluded sites cannot remain byte-identical.
- R14 or an authority/lifetime boundary changes.
- Qualification requires modifying historical pins or broadening the allowlist.
- The separate Fit release-path repair becomes necessary.
- A candidate failure is “resolved” by weakening an existing assertion.

Do not promise universal non-throwing behavior for all inherited log-shaped code. The exact containment surface and its exclusions are deliberate.

Do not claim measured user-visible speed gains from source deletion alone.

## 15. Reconciliation appendix

| Claude finding | Disposition | Final resolution |
|---|---|---|
| **1. Post-Fit readiness is product-coupled** | **ACCEPTED** | Exclude and preserve statement byte-for-byte; execute real `fit_finish` in targeted qualification. |
| **2. `p02_safe_write_json` exception state** | **ACCEPTED** | Remove from containment scope; preserve entire function. |
| **3. Python 2 traceback contamination** | **ACCEPTED WITH MODIFICATION** | Document traceback limitation, test handler continuity, and additionally preserve the original startup interrupt with explicit `raise exc`. |
| **4. Mechanical containment selection** | **ACCEPTED WITH MODIFICATION** | Adopt exact rule and 88 callsites; correct emitting-owner count to **53**. |
| **5. Exact reconstruction algorithm** | **ACCEPTED WITH MODIFICATION** | Adopt complete same-interpreter AST reconstruction plus untouched-byte checks; include the explicit startup re-raise transformation. |
| **6. R14 inventory coupling** | **ACCEPTED** | Independently verified 20/8/24 incremental sets; merge top-level changes into cumulative expectations. |
| **7. Historical dependencies** | **ACCEPTED** | Use pinned detached worktree; keep it through reconstruction qualification, then remove it safely. |
| **8. Failure injection** | **ACCEPTED WITH MODIFICATION** | Tag-selective throwing sink plus failing `repr`; clarify that no-op stubs still evaluate arguments. |
| **9. R15 diagnostic outcome changes** | **ACCEPTED WITH MODIFICATION** | Declare and test intentional startup improvements; add original-interrupt preservation. |
| **10. D1 wording and legacy clause** | **ACCEPTED** | “Removes diagnostic-only failure paths”; no legacy edits. |

The scope has not expanded into authority, persistence or lifecycle redesign. The explicit startup re-raise is the smallest additional change needed to prevent the proposed containment from substituting a diagnostic error for an original interrupt.

## 16. Final bounded coder assignment

> Implement this reconciled item-7 design from checkpoint `7b69b520a2472d3700ce347a1d2a59bc98e926f2`, beginning with the exact `1e866871…` app.
>
> First establish the pinned detached reference worktree and verify the historical identities. Generate and pin the transformation manifest before editing.
>
> Apply only the exact removals, two payload substitutions, 88 diagnostic wrappers with their exclusions, and the single explicit startup exception re-raise. Preserve Q1 disabled, all product semantics, authority boundaries, resource checkpoints, R14/R15 ownership and the separate Fit release-path behavior.
>
> Update only the allowlisted route inventories and new item-7 qualification/evidence files. Run historical item-6 confirmation with its own dependencies, all eight existing convergence suites, and the item-7 gates under Python 2.7.5 and 3.10, including available real-PySide coverage.
>
> Report exact hashes, transformation counts, actual results and limitations. Mark item 7 complete only after all required offline gates pass.
>
> Stop with an undeployed offline-qualified candidate and its item-8 observability contract. Do not deploy, begin item 8, modify historical harnesses, repair Fit release behavior, or begin K/L.
