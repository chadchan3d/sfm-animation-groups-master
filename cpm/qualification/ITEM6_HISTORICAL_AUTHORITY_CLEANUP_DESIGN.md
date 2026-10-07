# CPM item 6 — historical development authority cleanup (design)

**Design status: APPROVED FOR BOUNDED IMPLEMENTATION.**
**Implementation status: NOT STARTED.**

| | |
|---|---|
| Scope | Handoff §22 item 6 — remove or isolate historical development authority machinery (`docs/qualification/CPM_CONVERGENCE_INTEGRATION_HANDOFF.md`) |
| Governing starting checkpoint | `823730f36dd4cdadc76bd5a61f015ebbdebf8105` |
| Pre-cleanup app SHA-256 | `9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900` (`cpm/app/SFM_Character_Preset_Manager.py`) |
| Provenance | Astra primary audit → Claude adversarial review → Astra reconciliation. This records how the design was produced; it is not a new authority hierarchy. |
| Status authority | `cpm/qualification/CPM_CONVERGENCE_LEDGER.md` |

This document preserves Astra's final reconciled design as the authoritative item-6 design. Its
technical decisions are reproduced unchanged; only formatting was normalized (workstation file
links are given as repository-relative paths, with the line numbers they cited at `823730f`). The
first-person voice below is Astra's reconciliation.

Item-6 implementation produces an **offline-qualified cleanup candidate** only. Sessions 1–4
remain valid evidence for the exact pre-cleanup app `9a78fc96…`; the cleaned bytes do not inherit
an exact-build real-SFM PASS. Post-cleanup real-SFM qualification belongs to item 8, after item 7
(§8, §9).

---

## 1. Reconciliation verdict

**READY — REVISED DESIGN**

The architecture survives. Claude identified real omissions in the implementation boundary and qualification plan, rather than a competing production authority route.

The final design is:

- Remove the obsolete provider/discovery/fallback/parity implementations from the mutable app.
- Preserve their existing frozen qualification references.
- Retain a distinguishable, refusal-only `get_semantic_provider`.
- Require an explicit provider in the active snapshot helper.
- Remove the unused whole-shot snapshot helper.
- Enforce preservation of surviving code against the **pre-cleanup app**, not merely the original G18AN baseline.
- Run the existing eight offline suites plus targeted cleanup checks.
- Record the resulting build as offline-qualified, pending post-cleanup real-SFM qualification.

No implementation or file changes were performed.

## 2. Claude findings disposition

| Claude finding | Accept / Partial / Reject | Repository evidence | Design consequence |
|---|---|---|---|
| Constant-removal wording is insufficiently exact | **ACCEPT** | `FORCE_MODE` depends on `MODE_SIDECAR`; `P01_PROVIDER_KIND` depends on `KIND_MASTER_TXT`; startup reads FORCE_MODE and the parity label. Definitions (`cpm/app/SFM_Character_Preset_Manager.py` line 1129) | Replace category-level instructions with the exact inventory in §5. |
| Existing derivation tests do not prove preservation of surviving implementations | **ACCEPT** | They compare changed-name sets against G18AN, not the contents of already-changed functions. Derivation checks (`cpm/convergence/tests/test_cpm_app_canonical_route.py` line 218) | Add a pre-item-6 source-boundary manifest and content checks. |
| R14 depends on the canonical-route changed-name set | **ACCEPT** | R14 subtracts `route.EXPECTED_CHANGED_TOP - route.R14_CHANGED_TOP`. R14 check (`cpm/convergence/tests/test_cpm_app_r14_ctypes_isolation.py` line 187) | Merge the item-6 changes into that cumulative set. No R14 test edit is needed. |
| R15 must explicitly run because it exercises complete application loading/startup | **ACCEPT** | R15 executes the actual module and startup path, including Qt-backed scenarios under 2.7.5. | Require the R15 suite, including the available real-PySide mode. |
| All eight existing offline suites should run | **ACCEPT, with bounded rationale** | The route harness is reused by operation-context, Fit and convergence-gate suites; adapter/projection suites preserve the reference boundary being relied upon. | Run the existing eight suites, without broadening them into new campaigns. This replaces my underspecified selective-run wording. |
| `semantic_snapshots_for_current_shot` lacked a disposition | **ACCEPT** | It contains an implicit historical acquisition and has no callers in the inspected app/tests/real-SFM qualification sources. Helper (`cpm/app/SFM_Character_Preset_Manager.py` line 3942) | **REMOVE** the mutable-app helper. Preserve the frozen baseline copy. |
| Existing forbidden sentinels do not test the real refusal stub | **ACCEPT** | `build_namespace` substitutes a test function for `get_semantic_provider`. Substitution (`cpm/convergence/tests/test_cpm_app_canonical_route.py` line 430) | Add a test executing the actual production stub and exception definition. |
| Stub should have a distinct exception | **ACCEPT** | Existing convergence exceptions represent different failures; accidental historical invocation should be identifiable without acquiring or logging anything itself. | Add `ProdHistoricalAuthorityDisabled`, directly subclassing `RuntimeError`. |
| Real-SFM qualification “lapses” | **PARTIAL** | Sessions 1–4 qualify app `9a78fc96…`; cleanup changes its bytes. But those historical results remain valid evidence. | Do not invalidate old results; do not transfer their exact-build qualification to new bytes. Use §9 wording. |
| Capture parity and retained window attributes must not be swept into cleanup | **ACCEPT** | `PROD_Q1_INDEXED_CAPTURE_PARITY` participates in capture/Save/Update paths; `self.g18an_parity_shortcut = None` remains in initialization. | Explicitly retain both and their surrounding behavior. |
| Remote-state gap requires a designer substitution decision | **REJECT as a remaining blocker** | The authoritative local commits are available, and the relevant production/test trees match across the gap. | Resolve locally; no push or substituted audit basis is required. |
| Session 4 might add dependencies relevant to cleanup | **ACCEPT concern; resolved with a qualification caveat** | Its harness binds surviving mutation/verification functions and pins app SHA plus definition line numbers. | Preserve the historical harness. It is not a harness for the cleaned bytes without a later, separately authorized requalification update. |
| No new real-SFM campaign is needed during item 6 | **ACCEPT** | The bounded change removes dormant machinery and closes unused defaults; qualified mutation and lifecycle bodies remain preserved. | Real-SFM post-cleanup qualification stays with item 8. |

My earlier audit had inspected the whole-shot helper during source tracing but failed to give it an explicit inventory disposition. That was a reporting/design-boundary omission; it is corrected here.

## 3. State-gap resolution

The current local HEAD remains:

`823730f36dd4cdadc76bd5a61f015ebbdebf8105`

The app remains:

`9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900`

I verified:

- No changes from `eb71dad` to `823730f` in `cpm/app`, `cpm/convergence`—including its tests—or `cpm/baseline`.
- Those same trees remain unchanged from `00d0d83`.
- No working-tree changes affect the inspected product, convergence tests or governing documents.

The later Session 4 work does add a harness and its test. Its bindings concern:

- Apply/Fit predicates.
- Rollback verifiers.
- Canonical adapter acquisition counters.
- Fit stage release observation.

It does **not** depend on the historical provider functions proposed for removal.

There is nevertheless an exact-build dependency: the harness (`real_sfm_qualification/cpm_session4/CPM_S4_Rollback_Harness.py` line 55) pins `APP_SHA` and function definition lines; its validation (`real_sfm_qualification/cpm_session4/CPM_S4_Rollback_Harness.py` line 235) checks those lines. Its companion test also checks the pinned current app.

Therefore:

- Session 4’s evidence remains valid for its original build.
- The harness/test are not included in the item-6 rerun requirement.
- Do not update their historical pins during item 6.
- A later decision to reuse that harness against cleaned bytes belongs to post-cleanup qualification.

This resolves Claude’s local/remote uncertainty without changing the architectural conclusion.

## 4. Final authority inventory

The table below supersedes my first disposition table. App symbols refer to the canonical mutable application (`cpm/app/SFM_Character_Preset_Manager.py`).

| Component | File/symbol | Reachability | Present purpose | REMOVE / ISOLATE / RETAIN | Reason |
|---|---|---|---|---|---|
| Menu/private-module lifecycle | Launcher; `StartProdTool`; `prod_r15_*`; `ProdWindow` lifecycle | Production | Qualified entrypoint and isolation | **RETAIN unchanged** | Not historical authority machinery. |
| Master pathname resolution | App: `p01_master_path` | Production | Supplies the canonical adapter’s source path | **RETAIN unchanged** | Path resolution is not a second semantic provider. |
| Historical TXT authority | App: tokenizer/parser, `SemanticProvider`, `MasterTxtSemanticProvider`, class aliases | Dormant | Superseded authority implementation | **REMOVE app copies** | Frozen baseline preserves reference behavior. |
| Development discovery/loading | App: `g18p_*` discovery/hash helpers; `g18an_*` file verification/import helpers | Dormant | Finds and loads historical R1D deployment | **REMOVE app copies** | Competing executable discovery machinery has no current production purpose. |
| Historical sidecar provider | App: `SidecarSemanticProvider` and its path normalizer | Dormant | Historical provider/backing ownership | **REMOVE app copies** | Canonical broker supersedes it. |
| TXT/SIDECAR/AUTO dispatcher | App: `acquire_semantic_provider_for_mode` | Dormant | Historical acquisition and AUTO→TXT fallback | **REMOVE** | No authorized production use. |
| Historical global getter | App: `get_semantic_provider` | Disconnected legacy callers; active helper’s unused default before cleanup | Historical acquisition | **RETAIN name; replace body with refusal only** | Keeps old callsites defined without preserving acquisition or deleting unrelated UI. |
| Historical invalidator | App: `invalidate_semantic_provider` | No callers found | Manages historical singleton | **REMOVE** | No active owner remains. |
| Historical state observation | App: `_SEMANTIC_PROVIDER*`, `semantic_provider_runtime_stats` | Production diagnostics/probe | Observes inert historical state | **RETAIN unchanged** | Item 7 owns diagnostic cleanup; Session 1 probe reads this state. |
| Authority parity/self-tests | App: semantic/decision parity helpers, synthetic provider test, old health test | Dormant | Historical qualification | **REMOVE app copies; ISOLATE continued use in existing baseline/tests** | No new reference module needed. |
| Parity UI handler | App: `ProdWindow.g18an_run_decision_parity` | Unbound method | Invokes historical parity pipeline | **REMOVE** | No production callback or current oracle needs this app method. |
| Active snapshot helper | App: `semantic_snapshot_for_model_row` | Production with explicit adapter | Converts supplied authority into semantic snapshot | **RETAIN; replace only missing-provider branch** | Preserve its transformations; prohibit implicit acquisition. |
| Whole-shot snapshot helper | App: `semantic_snapshots_for_current_shot` | No callers found | Historical multi-model convenience wrapper | **REMOVE app copy** | No current purpose justifies preserving another implicit-acquisition surface. |
| Semantic transformations | App: status/match aliases, snapshot interpretation/signature, pure scope conversion | Production | Qualified consumer semantics | **RETAIN unchanged** | Inherited semantics remain active. |
| Canonical acquisition/health | App: `prod_cpm_*` authority functions; migrated health probe | Production | Canonical acquisition, authorization and health | **RETAIN unchanged** | Qualified seam. |
| Adapter/projection/shared authority | CPM adapter/projection; canonical shared package | Production | Broker-mediated authority and exact interpretation | **RETAIN unchanged** | No redesign or extra provider owner. |
| Operation Context and provenance conversion | App: authorization/context functions; `prod_provider_capture` | Production | Detached operation evidence | **RETAIN unchanged** | Prevents late authority reacquisition. |
| Refusal sentinel | App: `ProdCpmUnmigratedProvider` and its exception/helper | Production safety paths | Rejects missing-context semantic requests | **RETAIN unchanged** | It cannot acquire authority. |
| Fit helpers/stage authority | App: existing planning/warning helpers; per-target stage path | Production | Uses explicitly supplied held authority | **RETAIN unchanged** | Names such as `g11a` do not make them obsolete. |
| Old UI and scope entrypoints | App: older launchers, `p02_complete_scope`, `g11a_source` | Outside current production entry graph | Legacy implementation residue | **RETAIN in item 6; acquisition ends at refusal stub** | Avoid unrelated legacy-UI removal. |
| Capture parity | App: `PROD_Q1_INDEXED_CAPTURE_PARITY`, capture comparison helpers/branches | Qualified capture paths | Capture equivalence checking | **RETAIN unchanged** | Different purpose from authority-provider parity. |
| Frozen baseline/oracles/history | Baseline, pinned test extraction, independent conflict fixtures, historical evidence | Qualification/reference only | Reproducibility and semantic comparison | **RETAIN in existing isolated locations** | No production import/call route; no copy or move required. |

## 5. Exact constant/alias inventory

### Remove

Exactly these named constants/aliases are in scope for removal:

- `SEMANTIC_PROVIDER_MODE_TXT`
- `SEMANTIC_PROVIDER_MODE_AUTO`
- `G18P_MASTER_SHA256`
- `G18P_SIDECAR_ARTIFACT_SHA256`
- `G18P_SIDECAR_FORMAT_SHA256`
- `G18P_R1D_VALIDATOR_SHA256`
- `G18P_R1D_PROVIDER_SHA256`
- `PROD_MASTER_HEALTH_MIN_OCCURRENCES`
- `PROD_MASTER_HEALTH_MIN_FOLD_FAMILIES`
- `P01SemanticProvider`
- `P01MasterTxtProvider`

The final two are class aliases, not semantic answer constants.

### Retain unchanged

**Load/startup and diagnostic compatibility**

- `SEMANTIC_PROVIDER_MODE_SIDECAR`
- `SEMANTIC_PROVIDER_FORCE_MODE`
- `G18AN_PARITY_SHORTCUT`
- `SEMANTIC_PROVIDER_KIND_MASTER_TXT`
- `SEMANTIC_PROVIDER_KIND_MASTER_SIDECAR`
- `P01_PROVIDER_KIND`

`P01_PROVIDER_KIND` has no surviving functional consumer after removing the historical TXT provider, but removing it and its source constant is unnecessary additional cleanup. Retaining their inert values does not retain a provider factory. The provider-kind constants are also extracted by the existing test namespace.

**Semantic contracts and aliases**

- `SEMANTIC_PROVIDER_CONTRACT`
- `SEMANTIC_PROVIDER_FOLD_POLICY`
- `SEMANTIC_PROVIDER_MASTER_FILENAME`
- `SEMANTIC_STATUS_RESOLVED`
- `SEMANTIC_STATUS_CONFLICT`
- `SEMANTIC_STATUS_ABSENT`
- `SEMANTIC_STATUS_UNAVAILABLE`
- `SEMANTIC_MATCH_EXACT`
- `SEMANTIC_MATCH_FOLDED`
- `SEMANTIC_MATCH_NONE`
- `P01_PROVIDER_CONTRACT`
- `P01_FOLD_POLICY`
- `P01_MASTER_FILENAME`
- `P01_STATUS_RESOLVED`
- `P01_STATUS_CONFLICT`
- `P01_STATUS_ABSENT`
- `P01_STATUS_UNAVAILABLE`
- `P01_MATCH_EXACT`
- `P01_MATCH_FOLDED`
- `P01_MATCH_NONE`

**Inert historical telemetry**

- `_SEMANTIC_PROVIDER`
- `_SEMANTIC_PROVIDER_OPEN_COUNT`
- `_SEMANTIC_PROVIDER_REUSE_COUNT`
- `_SEMANTIC_PROVIDER_INVALIDATION_COUNT`
- `_SEMANTIC_PROVIDER_PRODUCTION_PARSE_COUNT`
- `_SEMANTIC_PROVIDER_GENERATION`

**Explicitly outside removal**

- `PROD_Q1_INDEXED_CAPTURE_PARITY`
- `PROD_MASTER_REVIEW_WARNING_THRESHOLD`
- `PROD_MASTER_PROVIDER_WARNING_COPY`
- `PROD_MASTER_REVIEW_WARNING_COPY`
- `PROD_SEMANTIC_POLICY`
- `P01_MODEL_PATH`
- `P01_MODEL_CHECKSUM`
- `self.g18an_parity_shortcut = None`

All other constants remain unchanged. There is no general permission to remove names containing `G18`, `P01`, `provider`, `parity` or `TXT`.

## 6. Final reachability result

**Before item 6: no second production authority path was found.**

The current path remains:

```text
launcher → private CPM module → current window callbacks
  → canonical adapter/bootstrap → canonical broker
  → CPM projection/interpretation
  → detached scope or bounded operation/stage authority
```

The historical AUTO→TXT fallback exists only behind disconnected historical acquisition. Canonical authority errors do not call it.

The active snapshot helper contains an unused historical default, but its production caller supplies an adapter. The separate whole-shot helper is uncalled.

**After item 6:**

- Historical provider/discovery/fallback implementations are absent from the mutable app.
- Old getter callsites terminate at an explicit refusal.
- The active snapshot helper requires a supplied provider.
- The unused whole-shot helper is absent.
- No production path imports a qualification implementation.
- The historical implementation remains recoverable and usable as a frozen test reference.

This resolves executable production-source ambiguity without claiming that a currently exercised fallback was repaired.

## 7. Final implementation boundary

### Allowed production file

Only:

Canonical CPM app (`cpm/app/SFM_Character_Preset_Manager.py`)

### Exact function/class removal set

Remove these app definitions:

```text
p01_ascii_fold
p01_tokenize_master
p01_parse_occurrences
SemanticProvider
MasterTxtSemanticProvider
g18p_sha256_file
g18p_sidecar_deploy_dir
g18p_find_sidecar_artifact
g18p_sidecar_dependency_discovery
g18an_find_file_by_sha
g18an_verified_sidecar_paths
g18an_import_frozen_sidecar_provider
g18an_normalize_sidecar_path
SidecarSemanticProvider
g18an_ascii_case_variant
g18an_semantic_parity_for_row
g18an_scope_decision_view
g18an_scope_signature
g18an_accepted_from_scope
g18an_flex_plan_signature
g18an_preset_decisions
g18an_clothing_plan_signature
g18an_clothing_decisions
g18an_decision_parity_for_row
acquire_semantic_provider_for_mode
invalidate_semantic_provider
p01_provider_answer_signature
p01_synthetic_provider_contract
semantic_snapshots_for_current_shot
prod_semantic_provider_health_from_descriptor
prod_provider_health_selftest
ProdWindow.g18an_run_decision_parity
```

Remove only the constants/aliases listed in §5.

### Two changed function bodies and one new exception

**`get_semantic_provider`**

- Keep its zero-argument signature.
- Add `ProdHistoricalAuthorityDisabled`, directly subclassing `RuntimeError`.
- The getter unconditionally raises that exception with a fixed message identifying disabled historical acquisition.
- No logging, imports, file access, canonical redirection, global declarations, counters or other work.
- Keep the getter forbidden in production reachability tests, with no exemptions.

The dedicated exception identifies a programming/routing violation. It must not masquerade as an ordinary current-generation authority failure.

**`semantic_snapshot_for_model_row`**

- Keep the signature.
- Replace only the `provider is None` branch’s historical acquisition with an explicit `RuntimeError` stating that a supplied authority provider is required.
- Preserve the rest of the function exactly.
- Do not move that check, change vocabulary capture, import an adapter or acquire authority.

**`ProdHistoricalAuthorityDisabled`**

- Definition only; no custom behavior.
- No inheritance from the bootstrap, operation-authority or unmigrated-context exceptions.

Explanatory comments may be corrected within the removed/replaced regions and the canonical-route comment describing the historical machinery. No general comment/log cleanup.

### Allowed test/evidence files

Existing files:

1. Canonical-route test (`cpm/convergence/tests/test_cpm_app_canonical_route.py`)
2. Convergence Ledger (`cpm/qualification/CPM_CONVERGENCE_LEDGER.md`)

New files:

3. `cpm/convergence/tests/test_cpm_app_authority_cleanup.py`
4. `cpm/convergence/tests/item6_precleanup_source_manifest.json`
5. `cpm/qualification/ITEM6_HISTORICAL_AUTHORITY_CLEANUP_EVIDENCE.md`

The JSON manifest is justified as a content-preservation oracle, not another executable app copy.

In the canonical-route test:

- Include `get_semantic_provider` and `semantic_snapshot_for_model_row` in the cumulative `EXPECTED_CHANGED_TOP`.
- Add explicit expected removal sets, including the removed method and constants.
- Account for the new exception.
- Replace historical-retention assertions with exact absence/preservation assertions.
- Remove the snapshot-default exemption.
- Keep forbidden sentinels for production no-call checks; supplement them with real-stub testing.

### No-touch boundary

No changes to:

- Launcher or R14/R15 implementation.
- Other seven existing convergence test files.
- Adapter, projection or shared authority package.
- Normalizer.
- Master/sidecar artifacts or generation rules.
- Operation Context, Fit, mutation, rollback, persistence or classification.
- Surviving logging and product identity strings.
- Frozen Blueprint, baseline, manifest or historical evidence.
- Session 1–4 harnesses/tests/runbooks.
- Stale-scope or missing-sidecar UI.

Unexpected need to edit another file requires review, not automatic allowlist expansion.

## 8. Final targeted qualification plan

### Interpreters

- **Python 2.7.5:** production interpreter.
- **Python 3.10:** compatibility interpreter.

### Existing suites required

Run these eight existing suites under both interpreters:

| Suite | Why it belongs in item 6 |
|---|---|
| `test_cpm_compat_v1_projection.py` | Preserves the pinned semantic oracle and independent conflict expectations on which removal relies. |
| `test_cpm_authority_adapter.py` | Preserves provider-shaped compatibility, fail-closed behavior and health migration evidence. |
| `test_cpm_app_canonical_route.py` | Directly changed harness and production reachability boundary. |
| `test_cpm_app_operation_context.py` | Uses the changed route namespace; checks late-helper routing. |
| `test_cpm_app_clothing_fit.py` | Uses the same namespace; checks retained inherited helpers and stage authority. |
| `test_cpm_convergence_gates.py` | Exercises connected operation/generation/bootstrap guarantees through the shared harness. |
| `test_cpm_app_r14_ctypes_isolation.py` | Depends on the cumulative changed-name inventory and protects the private-ctypes boundary. |
| `test_cpm_app_r15_namespace_isolation.py` | Executes complete app loading/startup/lifecycle and catches alias-time failures. |

Only the canonical-route file is editable. Run R15’s real-PySide mode under 2.7.5 where available, including a successful `created` startup outcome. A mock-only run must not be reported as equivalent to that check.

This finite reuse of existing suites is preferable to inventing partial runners or editing seven suites to select cases. It does not repeat the real-SFM campaigns or complete item 8.

### New preservation proof

Generate the manifest from the exact pre-cleanup bytes **before editing**, verifying:

`9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900`

Record content hashes and ordering for:

- Top-level definitions and assignments.
- Imports and other executable top-level statements.
- Decorators/default expressions as part of their owning definitions.
- `ProdWindow` methods and remaining class-level structure.

Then enforce:

- Every untouched surviving block matches the pre-cleanup content.
- Only the exact removal set disappears.
- Only the approved exception is added.
- `ProdWindow` differs only by deletion of its parity method.
- Reversing the single approved snapshot-branch replacement reproduces the pinned pre-cleanup helper.
- The stub and new exception match their approved minimal structure.
- No unauthorized executable top-level statement or binding is introduced.

Do not merely pin names, compare to G18AN or regenerate expected hashes from the edited candidate. Ignore definition-line movement; that is an unavoidable consequence of deletion.

### Test the actual refusal boundary

Load the actual new exception/getter definitions from the candidate—not the route harness’s replacement sentinel.

Require:

- The dedicated exception and expected message.
- Zero file reads/imports/acquisitions.
- No changes to historical state/counters.
- No canonical adapter call.
- No `global` statements or mode dispatch.

Likewise execute the actual snapshot helper:

- A valid row plus `provider=None` raises the explicit missing-provider error.
- It never calls the historical stub or canonical opener.
- A supplied test adapter preserves existing descriptor/query/snapshot behavior.

### Static and runtime-offline closure checks

Require:

- No dangling references to removed definitions or aliases.
- No module-level dependency on a removed name.
- No production callback path to the refusal getter.
- No production import of baseline/test/qualification machinery.
- Canonical failure cases remain failures, not healthy absence.
- Historical state remains inert.
- Existing operation-context and Fit tests still show no late historical acquisition or idle lease/provider.

### Real SFM and item 8

No new real-SFM campaign is required during item 6.

Defer deployed-build post-cleanup behavior qualification to item 8 after item 7. Retain existing Sessions 1–4 evidence; do not rerun or repin their harnesses merely to finish item 6.

## 9. Qualification-status wording

After successful implementation and checks, the Ledger should say:

> **§22 item 6 — COMPLETE: historical authority cleanup; offline qualification PASS.**
>
> Candidate app SHA-256: `<new SHA>`.
>
> The approved historical provider/discovery/fallback/parity machinery has been removed from the mutable app. Historical acquisition is refusal-only; semantic snapshot construction requires an explicitly supplied provider. The canonical authority seam and non-allowlisted production implementations are preserved.
>
> The eight existing offline suites and targeted item-6 checks passed under Python 2.7.5 and Python 3.10, with Qt-mode coverage recorded explicitly.
>
> Sessions 1–4 remain valid qualification evidence for pre-cleanup app `9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900`. The new app bytes have not yet received post-cleanup real-SFM qualification. This remains pending item 8 after item 7.
>
> R14/R15 remain closed. Item 7 is next; item 8, K and L have not begun.

Do not call the new app “Sessions 1–4 PASS” without identifying the inherited evidence and exact-build distinction. Conversely, do not revoke the historical PASS results.

## 10. Risks and stop conditions

Stop coder work if:

1. Starting source or relevant test identities differ from the audited checkpoint.
2. The removal set has a current production caller not accounted for here.
3. A surviving semantic, mutation, persistence, Fit or lifecycle block changes outside the approved boundary.
4. A required oracle depends on the mutable app copy rather than the preserved reference.
5. Cleanup requires modifying another production file or one of the seven no-touch suites.
6. A canonical error begins producing a semantic answer, fallback, idle lease or historical acquisition.
7. A source-preservation failure is “fixed” by refreshing expected hashes from the changed candidate.
8. Historical Session 4 pins are silently updated to label new bytes qualified.
9. A qualification failure requires changed semantics rather than correction of the cleanup implementation.

Do not hot-reload the changed app into a running SFM process. Any later deployment/use follows the established R15 restart rule.

No other unresolved design decision prevents this bounded assignment.

## 11. Final proposed coder assignment

> **Implement only handoff §22 item 6, after designer approval of this reconciled design.**
>
> Verify HEAD `823730f36dd4cdadc76bd5a61f015ebbdebf8105`, the governing Ledger/Blueprint and pre-cleanup app SHA `9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900`.
>
> Before editing, record the pre-cleanup source-boundary manifest specified in §8. It must independently preserve the exact surviving implementations and executable module structure.
>
> In the canonical CPM app only, remove the exact functions/classes/method and constants/aliases listed in §§5 and 7. Preserve the frozen baseline and all existing reference machinery; do not create another legacy-provider module.
>
> Replace `get_semantic_provider` with a zero-argument unconditional `ProdHistoricalAuthorityDisabled` refusal. Add that direct `RuntimeError` subclass with no custom behavior. The getter must perform no I/O, import, acquisition, logging or state mutation.
>
> Preserve `semantic_snapshot_for_model_row` except for replacing its missing-provider acquisition branch with an explicit refusal. Remove the unused `semantic_snapshots_for_current_shot` helper.
>
> Retain the exact constants and active inherited behavior listed in this design, including capture parity, the inert historical telemetry interface, the existing `None` shortcut attribute and the active unmigrated-provider refusal sentinel.
>
> Update only the canonical-route test among the existing suites: exact removal/addition/change inventories, no historical default exemption, and no weakened semantic assertions. Merge item-6 changed functions into the cumulative `EXPECTED_CHANGED_TOP` used by R14.
>
> Add the targeted cleanup tests. Test the real production stub and snapshot helper, not solely forbidden sentinels. Run all eight existing offline suites plus the new checks under Python 2.7.5 and Python 3.10; explicitly record R15’s Qt-mode coverage.
>
> Do not modify launcher, adapter/projection, shared authority, Normalizer, R14/R15 behavior, operation contexts, Fit, classification, persistence, mutation, surviving diagnostics or frozen evidence.
>
> Record exact source identities, dispositions, preservation results, test commands/outcomes and qualification limitations in the item-6 evidence document. Update the Ledger using the exact-build distinction in §9.
>
> Stop on any condition in §10. Do not perform item 7, absorb item 8, repin Session 4, begin K/L or decide either deferred UI question.
>
> **Stop after item 6 and provide the Ledger checkpoint.**
