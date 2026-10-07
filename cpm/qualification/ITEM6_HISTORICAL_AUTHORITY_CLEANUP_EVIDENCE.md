# CPM item 6 — historical authority cleanup (evidence)

**Result: COMPLETE — offline qualification PASS (2026-10-07).** This is an **offline-qualified
cleanup candidate** only; no real-SFM claim is made for the new app bytes (§6).

Design: `cpm/qualification/ITEM6_HISTORICAL_AUTHORITY_CLEANUP_DESIGN.md` (APPROVED FOR BOUNDED
IMPLEMENTATION). Implemented exactly within its §7 boundary and §11 assignment; no §10 stop
condition was met.

## 1. Starting gate (verified before editing)

| Check | Result |
|---|---|
| Branch / HEAD / `origin/master` | `master` at `9d405c897f659cc67a54077dcedb1e887d4bef27`, equal to `origin/master`; no tracked modifications |
| Blueprint | `cpm/qualification/R15_IMPLEMENTATION_BLUEPRINT.md`, frozen from `bd169401fba1c04bf24a148cd8e65748ae757912` (unchanged since `382c79b`) |
| Ledger | item 6 the active milestone, APPROVED DESIGN — IMPLEMENTATION NOT STARTED |
| Design | APPROVED FOR BOUNDED IMPLEMENTATION |
| Pre-cleanup app | `9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900` |
| `823730f` → `9d405c8` | documentation only (Ledger, design); `cpm/app`, `cpm/convergence` (incl. tests), `cpm/baseline` byte-identical |
| Inventory | all 31 removal functions/classes, the parity method and the 11 constants/aliases present exactly once; every retained constant present; `ProdHistoricalAuthorityDisabled` absent |
| Surviving references | the only surviving code reference to a removal name was `get_semantic_provider` → `acquire_semantic_provider_for_mode` (replaced); oracle suites extract from the frozen baseline, not the app |

## 2. Identities

| Artifact | Before | After |
|---|---|---|
| `cpm/app/SFM_Character_Preset_Manager.py` | `9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900` (35,906 lines) | **`1e8668717f9a4a1def0900c6b51e20cb9a7676cc365244eab5c31233f133eeeb`** (33,304 lines) |
| `cpm/convergence/tests/test_cpm_app_canonical_route.py` | `2e06bbaec84dfb8cd50d7d648dd7942a3f8f7f9ec7e9b7b071db7a5904a51962` | `29ae0e8433c9c50ee469944dbd00df340f0b517f30a4f55ce74fb0fd3bf80686` |
| `cpm/convergence/tests/test_cpm_app_authority_cleanup.py` | — (new) | `a3024d3404c3d3db3905218343fdf1e931a58c782e0599d810f55427467820fe` |
| `cpm/convergence/tests/item6_precleanup_source_manifest.json` | — (new) | `a92647949f26f02c65497b4f0e808413edbe54af72eec8b1bee65798cdd2c6ae` |

Unchanged (verified): launcher `996ca483…`, frozen baseline `3326024d…`, adapter `e96e21b5…`,
projection `9b077a1b…`, Normalizer audit copy `1f4ec5a2…`, Master `ac45e5c1…`, the shared
authority package, the other seven convergence suites, `real_sfm_qualification/` (Sessions 1–4
evidence and harnesses), the Blueprint and the handoff. No other file changed.

## 3. Pre-cleanup source manifest (preservation oracle)

- Generated **before any edit** by `test_cpm_app_authority_cleanup.py --write-manifest`, which
  refuses unless the app is exactly `9a78fc96…` and refuses to overwrite an existing manifest. Its
  SHA-256 is pinned in the test (hashed with LF line endings, so checkout conversion cannot mask a
  change); it is never regenerated from the candidate.
- Content: 642 top-level statements and 78 `ProdWindow` members in source order (kind, names,
  first-line head, SHA-256 of the block text), the `ProdWindow` header hash, and the approved
  dispositions (removal sets, changed set, added exception, snapshot-branch original/replacement,
  fixed messages). Blocks run from their start (decorators included) to the next statement with
  leading/trailing blank and comment-only lines trimmed; line numbers are not recorded. No source
  text is stored, so the manifest is not an executable app copy.
- Interpreter independence: the manifest built from the pre-cleanup bytes is byte-identical under
  Python 2.7.5 and 3.10 (the one multi-line string statement, the module docstring, is anchored at
  the region start; any other string statement fails loudly).

## 4. Dispositions applied

**Removed from the app (exactly the design's §7 set):** `p01_ascii_fold`, `p01_tokenize_master`,
`p01_parse_occurrences`, `SemanticProvider`, `MasterTxtSemanticProvider`, `g18p_sha256_file`,
`g18p_sidecar_deploy_dir`, `g18p_find_sidecar_artifact`, `g18p_sidecar_dependency_discovery`,
`g18an_find_file_by_sha`, `g18an_verified_sidecar_paths`, `g18an_import_frozen_sidecar_provider`,
`g18an_normalize_sidecar_path`, `SidecarSemanticProvider`, `g18an_ascii_case_variant`,
`g18an_semantic_parity_for_row`, `g18an_scope_decision_view`, `g18an_scope_signature`,
`g18an_accepted_from_scope`, `g18an_flex_plan_signature`, `g18an_preset_decisions`,
`g18an_clothing_plan_signature`, `g18an_clothing_decisions`, `g18an_decision_parity_for_row`,
`acquire_semantic_provider_for_mode`, `invalidate_semantic_provider`,
`p01_provider_answer_signature`, `p01_synthetic_provider_contract`,
`semantic_snapshots_for_current_shot`, `prod_semantic_provider_health_from_descriptor`,
`prod_provider_health_selftest`, and the method `ProdWindow.g18an_run_decision_parity`.

**Removed constants/aliases (exactly §5):** `SEMANTIC_PROVIDER_MODE_TXT`,
`SEMANTIC_PROVIDER_MODE_AUTO`, `G18P_MASTER_SHA256`, `G18P_SIDECAR_ARTIFACT_SHA256`,
`G18P_SIDECAR_FORMAT_SHA256`, `G18P_R1D_VALIDATOR_SHA256`, `G18P_R1D_PROVIDER_SHA256`,
`PROD_MASTER_HEALTH_MIN_OCCURRENCES`, `PROD_MASTER_HEALTH_MIN_FOLD_FAMILIES`,
`P01SemanticProvider`, `P01MasterTxtProvider`.

**Added:** `class ProdHistoricalAuthorityDisabled(RuntimeError)` — definition (docstring) only,
placed immediately before the getter.

**Changed (two bodies only):**
- `get_semantic_provider()` — zero-argument; unconditionally raises
  `ProdHistoricalAuthorityDisabled("Historical semantic-provider acquisition is disabled; use the
  canonical CPM authority route.")`; no logging, imports, I/O, globals, counters or redirection.
- `semantic_snapshot_for_model_row(row, provider=None)` — only the `provider is None` branch:
  `provider = get_semantic_provider()` → `raise RuntimeError("Semantic snapshot requires an
  explicitly supplied authority provider.")`. Everything else is byte-identical (proven by
  reversing the replacement to the pinned pre-cleanup hash).

**Retained unchanged (as designed):** the canonical broker/bootstrap route and `prod_cpm_*`
authority functions, adapter/projection use, Operation Authority Contexts, Fit stage authority and
lifetime, `ProdCpmUnmigratedProvider` and its exception/helper, semantic transformations and
status/match aliases, `p01_master_path`, `prod_provider_capture`, the inert historical telemetry
(`_SEMANTIC_PROVIDER*`, `semantic_provider_runtime_stats`), `SEMANTIC_PROVIDER_MODE_SIDECAR`,
`SEMANTIC_PROVIDER_FORCE_MODE`, `G18AN_PARITY_SHORTCUT`, the provider-kind constants and
`P01_PROVIDER_KIND`, capture parity (`PROD_Q1_INDEXED_CAPTURE_PARITY`), the warning-copy and policy
constants, `self.g18an_parity_shortcut = None`, the old UI and scope entrypoints, R14/R15
lifecycle code and all logging/identity strings.

**Comments corrected (permitted regions only):** the comment above the provider-mode constants
(it described the removed TXT/AUTO modes) and the Step 2b canonical-route comment (it described the
historical machinery as retained). No other comment or log text changed.

**Legacy callers now ending at the refusal stub** (all unreachable from production):
`G09AGenericWindowRoute`, `G11AProductionWindow`, `g11a_source`, `p02_complete_scope`.

## 5. Qualification

Commands (from `cpm/convergence/tests`, `PYTHONDONTWRITEBYTECODE=1`): for each phased suite
`<py3.10> <suite> --phase=publish`, `<py2.7.5> <suite> --phase=suite`, `<py3.10> <suite>
--phase=compare`; R14/R15 `--phase=run` under each interpreter; the cleanup checks with no
arguments under each interpreter. Interpreters: embedded Python 2.7.5 (production, real PySide
1.2 / Qt 4.8) and Python 3.10.6.

| Suite | Pre-cleanup app (`9a78fc96…`) | Cleanup candidate (`1e866871…`) |
|---|---|---|
| `test_cpm_compat_v1_projection.py` | 3.10 196/196 · 2.7.5 196/196 · compare 3/3 | 3.10 196/196 · 2.7.5 196/196 · compare 3/3 |
| `test_cpm_authority_adapter.py` | 205/205 · 205/205 · 3/3 | 205/205 · 205/205 · 3/3 |
| `test_cpm_app_canonical_route.py` | 84/84 · 84/84 · 3/3 | **85/85 · 85/85 · 3/3** (one added check) |
| `test_cpm_app_operation_context.py` | 108/108 · 108/108 · 3/3 | 108/108 · 108/108 · 3/3 |
| `test_cpm_app_clothing_fit.py` | 95/95 · 95/95 · 3/3 | 95/95 · 95/95 · 3/3 |
| `test_cpm_convergence_gates.py` | 152/152 · 152/152 · 3/3 | 152/152 · 152/152 · 3/3 |
| `test_cpm_app_r14_ctypes_isolation.py` | 2.7.5 18/18 · 3.10 15/15 | 2.7.5 18/18 · 3.10 15/15 |
| `test_cpm_app_r15_namespace_isolation.py` | 2.7.5 345/345 (Qt real + model) · 3.10 188/188 (model) | 2.7.5 345/345 (Qt real + model) · 3.10 188/188 (model) |
| `test_cpm_app_authority_cleanup.py` (new) | — | 2.7.5 46/46 · 3.10 46/46 |

- **Qt-mode coverage:** R15 under 2.7.5 ran real PySide/Qt 4.8 (157 real-mode checks) and the Qt
  model (157). Real-mode `created` startup outcomes passed: first click, three reopen cycles, final
  reopen, modal and window-table cases. Python 3.10 ran the model only (PySide is unavailable there).
- **Canonical-route edits (design §7):** item-6 changed functions merged into the cumulative
  `EXPECTED_CHANGED_TOP` (consumed by R14, unedited); exact removal sets for top level and methods;
  the new exception accounted for; historical-retention assertions replaced by exact absence
  assertions; the snapshot-default reachability exemption removed (`EXEMPT_EDGES` empty); forbidden
  sentinels kept. No assertion was weakened.
- **New targeted checks (46):** manifest pin and approved sets; exact top-level sequence and content
  preservation; `ProdWindow` differs only by the removed method; snapshot reversal to the pinned
  hash; exception and stub structure; the **real** stub executed with instrumented builtins
  (dedicated exception, fixed message, no file/import/log/adapter activity, historical state
  untouched, repeated calls stay refusals); the **real** snapshot helper (missing provider →
  explicit `RuntimeError`, never the stub or the opener; supplied provider → results and queries
  identical to the pre-cleanup helper for valid and invalid descriptors; earlier row errors
  unchanged); closure (no name, string or comment reference to removed names, no top-level binding,
  retained constants/definitions present, module compiles); reachability (refusal stub and legacy
  entrypoints unreachable from `StartProdTool`/`ProdWindow`; canonical route reachable); no
  production import of baseline/test/qualification machinery.
- **Sensitivity (ad hoc, not committed):** six mutated candidates were each caught under both
  interpreters — an edited surviving function, a stub that acquires/logs, the restored snapshot
  default, a re-added alias, an extra removal, and an edited `ProdWindow` method.
- The Session 4 harness and its test were **not** rerun or repinned (they pin the pre-cleanup app by
  design).

## 6. Qualification status and limitations

- **Offline-qualified cleanup candidate:** app `1e8668717f9a4a1def0900c6b51e20cb9a7676cc365244eab5c31233f133eeeb`.
- Sessions 1–4 remain valid qualification evidence for pre-cleanup app
  `9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900`. The new bytes have **not**
  received post-cleanup real-SFM qualification; that remains pending item 8, after item 7.
- The candidate is not deployed. Any later deployment follows the R15 restart rule (no hot reload
  into a running SFM process).
- Not done (out of scope): item 7 diagnostic logging reduction; item 8; stale-scope UI and
  `SidecarMissing` messaging; deferred UI findings 1–6; the Session 4 Fit release-path observation;
  K and L.
