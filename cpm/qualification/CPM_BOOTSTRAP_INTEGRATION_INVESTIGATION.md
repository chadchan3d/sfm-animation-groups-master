# CPM Bootstrap Integration Investigation (Step 2, investigation only)

**Repository:** `chadchan3d/sfm-animation-groups-master`, branch `master`, written against
`a52098e` ("Implement CPM cpm_compat_v1 projection foundation").
**Scope:** architectural discovery only. No code, no runtime qualification, no production wiring.
**Source inspected:** frozen `cpm/baseline/SFM_CSP_G18AN_SaveNewCopy.py` (SHA-256
`3326024d…66b3e`, unchanged). All line numbers below refer to that file. Shared package references
point to `tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/`.
**Governing documents:** handoff §11, §12, §14, §15, §20, §22 and adversarial review §3, §5, §6C, §8.
Where this document and those differ, those govern.

The question this investigation answers:

> Where can CPM replace its current semantic acquisition path with `cpm_compat_v1` without
> changing existing CPM behavior?

Short answer: `prod_scope()` already accepts an injected `provider` object and uses only two methods
on it. A provider-shaped CPM authority adapter can be injected there without changing
`semantic_snapshot_for_model_row()`, the snapshot, the signature or the pure scope. That is the
earliest safe seam. It is **not** sufficient on its own: identity checks and several late helpers
bypass the injected provider and call the process-global `get_semantic_provider()` directly. Those
call sites must be rerouted in the same wiring step (for scope identity) or in Step 3 (for the
Operation Authority Context).

---

## 1. Current CPM flow

### 1.1 Entry and provider ownership

```text
StartProdTool()                                   (module bottom)
  └─ ProdWindow(qt_parent())                      class @28097
       └─ render(identity)                        @30503  (model selection / refresh)
            ├─ prod_probe_semantic_provider()     @18612
            │    └─ get_semantic_provider()       @3339   process-global singleton
            │         └─ acquire_semantic_provider_for_mode(SEMANTIC_PROVIDER_FORCE_MODE = "SIDECAR")  @3301
            │              └─ SidecarSemanticProvider()                     @2298
            │                   ├─ g18an_verified_sidecar_paths()           @1914  hashes the Master once
            │                   ├─ g18an_import_frozen_sidecar_provider()   @2079  development discovery
            │                   └─ resident handle ("one-handle-per-adapter-lifetime")
            │    └─ prod_semantic_provider_health_from_descriptor()  @18517
            └─ prod_scope(identity)               @20136   (only when health == "healthy")
```

`get_semantic_provider()` caches the provider in `_SEMANTIC_PROVIDER` (@1849) and returns the same
object on every later call. `invalidate_semantic_provider()` (@3391) exists but **has no callers**.

### 1.2 Semantic snapshot and scope construction

```text
prod_scope(identity, provider=None)                        @20136
  ├─ prod_resolve(identity)                    → live model row (DME)
  ├─ provider = provider or get_semantic_provider()
  ├─ provider_descriptor = provider.generation_descriptor()
  ├─ semantic_snapshot_for_model_row(row, provider)         @3885
  │    ├─ p01_all_supported_flex_bindings(animset)          live FLEX vocabulary
  │    ├─ literals = sorted(set(binding literals))          exact live literals
  │    ├─ descriptor.get("valid") check
  │    ├─ answers = provider.query_many(literals)           @2590
  │    │    └─ per literal: p01_ascii_fold → handle.lookup_fold(utf-8) → _answer_from_result  @2496
  │    ├─ semantic_snapshot_from_live_vocabulary(bindings, answers)  @3769
  │    │    classification: face / body-morphs / other / master-miss / master-conflict /
  │    │    authority-unavailable; counts incl. folded_resolved (uses match_kind)
  │    └─ semantic_snapshot_signature(semantic)             @3865   sha256(repr(rows)); excludes occurrence_count
  ├─ prod_load_character(identity)             → model-local Review overrides (applies_when == master-miss)
  └─ scope = {                                               schema "csp-semantic-scope-pure-v1"
       identity, authority{provider_generation, provider_sha256,
                           semantic_policy_revision, override_revision},
       provider_descriptor (full dict copy), live_signature,
       semantic{rows (prod_pure_semantic_row), counts},
       expression{literal→binding descriptor}, body{…},
       unresolved, conflicts, overrides, excluded }
     prod_scope_pure_assert(scope)                           @19167
```

`prod_scope()` drops the snapshot's `provider` and `animset` references, so the published scope is
pure, detached Python data. That matches handoff §11.

### 1.3 Where compatibility decisions are made

`prod_scope_matches_identity(scope, identity)` (@19527) is the single compatibility predicate. It
compares:

- model path, checksum and Animation Set name;
- `scope.authority.provider_generation` vs `prod_current_provider_descriptor()["provider_generation"]`;
- `scope.authority.provider_sha256` vs the current descriptor's `source_sha256`;
- `semantic_policy_revision` vs `PROD_SEMANTIC_POLICY` (@18494);
- `override_revision` vs the on-disk character profile.

`prod_current_provider_descriptor()` (@19109) is `get_semantic_provider().generation_descriptor()`,
so **every compatibility decision goes through the global provider**, not through the scope's
injected provider.

Callers: `prod_live_bindings_for_cached_scope` @19650, `prod_set_override` @20396,
`prod_clear_override` @20523, and `ProdWindow` methods `semantic_provider_ready` @29560,
`apply_scope_to_ui` @30987, `review_reclassify` @31784, `review_decision` @31879, `save_kind` @31999,
`update_kind` @32221 and `open_details` @34160.

Preset exact-set compatibility (membership and representation) is separate. It uses the scope's
`body`/`expression` descriptors and `live_signature`, and does not change in this migration.

### 1.4 Authority touchpoints after scope construction

| Helper | Line | Authority access | Reached from |
|---|---|---|---|
| `prod_live_bindings_for_cached_scope` | @19644 | calls `prod_scope_matches_identity`; **returns `"provider": get_semantic_provider()`** @19776 | `prod_save` @26272, `prod_update_preset` @26641, `prod_apply` @27273 and postcommit @27598, `prod_verify_apply_abort_baseline` @27053, `prod_body_source` @27742, `prod_body_source_live_from_baseline` @27816 |
| `prod_character_record` | @20065 | `prod_provider_capture(get_semantic_provider())` @20100 | `prod_ensure_character` |
| `prod_ensure_character` | @20120 | `prod_provider_capture(get_semantic_provider())` @20131 | `prod_save` @26421, `prod_set_override` @20420, `prod_clear_override` @20538 |
| preset `capture_provider` | @26375, @26682 | `prod_provider_capture(scope["provider_descriptor"])`, **from the scope (already detached)** | Save, Update |
| `p03_unmapped_relevant_controls` | @7225 | `source_scope["provider"].query_many(target literals)` @7260 | `g11a_safe_plan` @16455 ← `fit_stage` plan @33268 and post-stage verify @33356 |
| `prod_scope` rebuilds | — | global provider | `prod_save`/`prod_update_preset`/`prod_apply`/`prod_body_source` when `scope is None`; `prod_set_override` @20392, `prod_clear_override` @20519, `review_reclassify` @31808, `review_decision` @31906 |

Fit threads a live provider object through its data. `prod_body_source()` (@27733) returns pure
data with no provider. `prod_body_source_live_from_baseline()` (@27809) then re-adds
`"provider": live["provider"]` (the global provider) for each stage. `g11a_safe_plan()` passes it to
`p03_unmapped_relevant_controls()`, which queries **target vocabulary outside the selected scope**.
This matches review §3.

### 1.5 Prompt ordering (Save/Update)

- `save_kind` @31992: `prod_scope_matches_identity` @31999 runs **before** the name prompt @32018,
  and `prod_save` @32031 runs after it.
- `update_kind` @32214: `prod_scope_matches_identity` @32221 runs **before** the confirmation
  `QMessageBox.exec_()` @32294.

There is no authority check after the prompt returns, which matches review §5. Current source already
has an `operation_context` parameter in `prod_save`/`prod_update_preset`/`prod_apply`, validated by
`prod_validate_context_token` @19375. That is a **scene/model-instance** token, not an authority
context.

### 1.6 Development and diagnostic authority paths reachable from `ProdWindow`

- Parity shortcut `G18AN_PARITY_SHORTCUT` (`Ctrl+Shift+P`, bound @28601) calls
  `g18an_decision_parity_for_row` @28841 (defined @3174). That constructs its own
  `MasterTxtSemanticProvider` **and** a second `SidecarSemanticProvider`, and runs `prod_scope`,
  preset decisions and `g18an_clothing_decisions` against both.
- `semantic_provider_runtime_stats()` is read in operation logging (@29083, @29257, @30831).
- `acquire_semantic_provider_for_mode("AUTO")` contains a silent TXT fallback (@3317–3331). It is
  unreachable while `SEMANTIC_PROVIDER_FORCE_MODE = SIDECAR` (@1128), but it remains in the file.
- Older windows (`CharacterPresetWindow`, `G09AGenericWindowRoute`, `G11AProductionWindow`) and
  `p02_complete_scope` (@4344, which also calls `get_semantic_provider()`) are instantiated only by
  their own `Run*` entry functions. They are not instantiated by `ProdWindow`.

### 1.7 Centralization verdict

| Question | Finding |
|---|---|
| Centralized? | **Acquisition** is centralized in one singleton (`get_semantic_provider`). **Consumption** is not: 6 production-route call sites reach the singleton directly, plus one provider object threaded through Fit data. |
| Duplicated? | Yes. `prod_scope` accepts an injected provider, but identity checks, live-binding checks and character-record writes ignore it and use the global. |
| Mixed with UI? | Yes. `ProdWindow.render` probes provider health and builds the scope inline. `semantic_provider_ready` runs the identity predicate. `save_kind`/`update_kind` run it around modal prompts. |
| Mixed with mutation? | Yes. `prod_live_bindings_for_cached_scope` runs inside Apply (pre-mutation, postcommit readback and abort verification) and returns the global provider. |

---

## 2. Proposed insertion seam

### 2.1 Future state

```text
ProdWindow (UI)                                 unchanged widgets and flow
  │
CPM semantic model                              prod_scope / semantic_snapshot_* / prod_scope_matches_identity
  │   (unchanged classification, snapshot, signature, pure scope)
  │
CPM authority adapter  (NEW, CPM-owned, outside the shared package)
  │   provider-shaped facade: generation_descriptor(), query_many(literals)
  │   canonical bootstrap; fold request; acquire → lease → validate → interpret → release
  │   stable descriptor mapping; compatibility identity; expected_generation pinning
  │
cpm_compat_v1 projection                        cpm/convergence/cpm_compat_v1_projection.py (Step 1, done)
  │
canonical broker                                runtime.get_broker(...).acquire_or_reuse_views(...)
```

### 2.2 Earliest safe replacement point

**`prod_scope(identity, provider=<CPM authority adapter>)`**, called from `ProdWindow.render`
@30534.

Why it is safe:

- `semantic_snapshot_for_model_row()` uses the provider only through `generation_descriptor()`
  (`valid` check) and `query_many(literals)`, which returns `{literal: answer}` in the seven-key
  G18AN answer shape.
- The Step 1 interpreter already reconstructs that exact shape (Suite 1: exact parity with
  `_answer_from_result` for Hit/MasterUnknown, and hand-audited parity for conflict).
- Snapshot classification, `semantic_snapshot_signature()`, the Review override merge and
  `prod_scope_pure_assert()` run unchanged on the answers.
- `prod_scope()` keeps only a descriptor **dict** copy and never the provider object, so the scope
  stays pure. The adapter's lease can therefore be released inside `query_many` before it returns,
  satisfying handoff §12 (no lease survives into UI idle).

Why it is not sufficient on its own (it must be paired with rerouting):

1. `prod_scope_matches_identity()` compares against the **global** descriptor. If only the scope used
   the adapter, it would compare adapter-derived fields with a still-opened development provider.
   That mixes authorities, and it also keeps the development provider open. The wiring step must
   route `prod_current_provider_descriptor()` through the adapter's cheap freshness check.
2. `prod_probe_semantic_provider()` must obtain health from the adapter, not open the development
   provider.
3. The development parity shortcut must be unreachable from the migrated route (review §8 step 2:
   "make the old development provider unreachable … without deleting it yet").

Items 1–3 together form the minimum "canonical bootstrap + pure idle scope" wiring (handoff §22
step 2). Late helpers (§1.4) belong to Step 3 (Operation Authority Context) and Step 4 (Fit). They
must not be half-migrated in Step 2. Until Step 3 they would still resolve the global provider, so
Step 2 must decide explicitly how they behave (see Risk R6).

---

## 3. Generation identity findings

### 3.1 Where `provider_generation` comes from

`get_semantic_provider()` increments `_SEMANTIC_PROVIDER_GENERATION` (@1854) and stamps
`provider._descriptor["provider_generation"]` **only when the singleton is empty**. Nothing ever
empties it: `invalidate_semantic_provider()` has no callers. The counter is incremented only after
a successful construction.

Consequence: within one script execution, every successful provider has
**`provider_generation == 1`**, and it never changes. A Master change after the first open is
**not detected in-process at all**. The singleton keeps the SHA it hashed at construction, and
`prod_scope_matches_identity()` compares a scope against that same frozen descriptor. G18AN
currently has no in-process generation-change detection. The migration adds freshness (handoff §13)
rather than preserving an existing mechanism.

### 3.2 Where it is consumed

| Consumer | Line | Use |
|---|---|---|
| `prod_scope` | @20332 | stamps `scope.authority.provider_generation` |
| `prod_scope_matches_identity` | @19592/@19598 | compared for equality with the current descriptor |
| `prod_provider_capture` | @20051 | written into persisted records: preset `capture_provider` (@26375, @26682) and character `last_validated_provider` (@20099, @20131) |
| log lines | various | diagnostics only |

No code reads the persisted `capture_provider` or `last_validated_provider` values back for any
decision. They are write-only provenance. Handoff §17 also treats generation as capture provenance,
not a compatibility lock.

### 3.3 Implications

- The Step 1 constant `CPM_DESCRIPTOR_PROVIDER_GENERATION = 1` matches the value G18AN actually
  persists and compares in practice. Persisted records stay byte-compatible in that field.
- Equality comparisons stay stable across broker reopenings of the same Master, which is what review
  §6C requires. The generation is never mapped to a cohort, open counter or artifact ID.
- Generation **change** detection must come from Master SHA via
  `acquire_or_reuse_views(expected_generation=<scope SHA>)` (handoff §13). It does not come from the
  integer, which cannot change.
- The existing `provider_sha256` comparison in `prod_scope_matches_identity()` is where a changed
  SHA surfaces, but only if the "current descriptor" it compares against reflects a **fresh**
  observation. Under G18AN it never does. This is why a CPM adapter layer is required: the global
  descriptor must be replaced by an adapter call that performs the broker's fresh observation.
- The integer `fit_generation` on `ProdWindow` (@33120) is a callback-cancellation counter. It is
  unrelated to the semantic generation and must stay separate from `Gfit` (handoff §15).

Dependency recorded, not solved: *what `prod_scope_matches_identity()` should do when the adapter's
fresh observation reports a different SHA* (reject and trigger a rebuild per handoff §13) is a
Step 2 wiring decision. It interacts with UI state in `apply_scope_to_ui` and `semantic_provider_ready`.

---

## 4. Adapter responsibilities

### 4.1 Already solved (Step 1, `cpm_compat_v1_projection.py`)

- fold rule (ASCII A–Z only, text internally, UTF-8 only at provider lookup);
- `cpm_compat_v1` fold-family projection builder with declared folds and scale;
- explicit Hit / FoldConflict / MasterUnknown handling, fail-closed on anything else;
- strict wrapper stripping (G18AN path representation);
- compact coverage and strict view validation (uncovered ≠ absent);
- exact-answer reconstruction in the G18AN seven-key answer shape;
- complete retained-size estimate;
- compatibility identity (Master SHA + `cpm_compat_v1` + policy revision);
- provider-capture descriptor: the four `prod_provider_capture` fields, with the cohort id only
  under diagnostics.

### 4.2 Still required (CPM runtime integration)

| Responsibility | Needed by | Notes |
|---|---|---|
| Canonical bootstrap | all | `sys.executable`-derived MAINMENU locator (the same formula as the Normalizer, with an offline equivalence check), origin, API `1.0.0-b2a`, build `package-boundary-corrected-2026-09-22`, `runtime.get_broker(...)` (handoff §16). No `execfile`, no vendored runtime. |
| Semantic vocabulary → request folds | `query_many` facade | Fold exact live literals, then call `make_request_specs` (Step 1). |
| Bounded acquisition and lease lifecycle | `query_many`, freshness checks | acquire → `lease_view` → `validate_view` → interpret → `release_view_lease` inside the call; clear the lease and view references afterwards (handoff §11). |
| Provider-shaped facade | `prod_scope`, `semantic_snapshot_for_model_row` | `generation_descriptor()` and `query_many(literals)` only. |
| Full descriptor mapping | `prod_scope` (`provider_descriptor` dict), health check | Beyond the four capture fields, the health gate reads `valid`, `provider_kind` (it must be one of the two qualified kinds, or the result is "degraded"), `occurrence_count` and `fold_family_count` (minimum thresholds). A fold-family view does not carry whole-Master counts; see R3. |
| Health / AuthorityUnavailable | `prod_probe_semantic_provider`, `render` | Broker errors map to `status="unavailable"`, never to healthy absence or Review (handoff §18). |
| Freshness check for scope identity | `prod_scope_matches_identity` | Replace the global descriptor with the adapter's `expected_generation` acquisition. It must not reopen the development provider. |
| Compatibility identity | scope identity | Step 1 function. Keep counters in diagnostics. |
| Provenance | persisted `capture_provider` / `last_validated_provider` | Same four fields and the same values (`provider_generation` = 1). |
| `expected_generation` pinning | Step 3/4 (not Step 2) | post-prompt Save/Update authorization, `Gfit`, target-vocabulary coverage. |
| Operation Authority Context | Step 3 (not Step 2) | Replaces the `"provider"` returned by `prod_live_bindings_for_cached_scope`, the `get_semantic_provider()` calls in character-record helpers, and the Fit provider threading. |

---

## 5. Integration risks

**Generation assumptions**

- **R1 — frozen-descriptor freshness.** G18AN never re-observes the Master, so current tests of "scope
  still matches" say nothing about generation change. When the adapter adds a fresh observation,
  `semantic_provider_ready()` and `apply_scope_to_ui()` can start returning False in situations
  where they never did before. UI reactions to a stale scope (rebuild, disable, status text) must be
  specified, not inherited by accident.
- **R2 — integer generation misuse.** Any temptation to map `provider_generation` to broker cohort or
  open counts would invalidate valid scopes on every reopen (review §6C). The constant must remain
  a constant.

**Semantic snapshot coupling**

- **R3 — health gate needs whole-Master statistics.** `prod_semantic_provider_health_from_descriptor`
  requires `occurrence_count` and `fold_family_count` above minimums, and a qualified
  `provider_kind`. The `cpm_compat_v1` payload holds only the requested families. Options (for the
  wiring step to decide): read the counts from the provider inside the builder (generation-invariant,
  but it widens the payload contract), obtain them from artifact identity if the package exposes
  them, or replace the gate with broker-level availability. A new `provider_kind` value would fail
  the current gate as "provider-kind-not-qualified".
- **R4 — descriptor dict retained in the scope.** `scope["provider_descriptor"]` is a full copy. It
  is persisted into presets through `prod_provider_capture`, and today it includes development
  fields (`source_label` artifact path, `sidecar_sha256`, `sidecar_format_sha256`). The adapter
  descriptor must not carry lease, view, provider or local-path objects (`prod_scope_pure_assert`
  forbids only certain types).
- **R5 — signature parity is still unproven on real data.** Step 1 proved answer parity. Snapshot
  and signature parity through `semantic_snapshot_from_live_vocabulary` and
  `semantic_snapshot_signature` (including `folded_resolved` counts, which depend on `match_kind`)
  is a deferred Suite 1 item. It must pass before the seam is trusted.

**Hidden authority dependencies**

- **R6 — mixed authorities during partial migration.** Until Step 3, `prod_live_bindings_for_cached_scope`
  returns `get_semantic_provider()`, and `prod_ensure_character` captures from it. If Step 2 routes
  only scope construction and identity through the adapter, any late helper that still reaches the
  global would **open the development provider** alongside the broker. Step 2 must either make that
  global resolve to an adapter-backed object (with no development open) or make those paths fail
  closed. It must not leave both live.
- **R7 — development paths reachable from the production window.** The parity shortcut builds TXT
  and development-sidecar providers directly. The AUTO-mode TXT fallback is dormant but present.
  Both must be unreachable from the migrated route (handoff §16, §18: "no silent TXT fallback").
- **R8 — resident handle lifetime.** The G18AN sidecar provider keeps its packed handle open for the
  adapter's lifetime (`_resident_handle`), which conflicts with "no idle lease or provider".
  Replacing it removes that behavior. No other code must depend on the handle staying open.

**Mutation dependencies**

- **R9 — Apply postcommit/abort verification** (@27598, @27053) re-enters the identity predicate. With
  a fresh-observation predicate, a Master change during an Apply could raise "semantic scope is
  stale" **inside readback or abort verification** of an already-committed or aborted transaction
  (review §3). Step 2 must not route these through a fresh check. Step 3 gives them the operation
  context instead.
- **R10 — Save/Update prompt ordering.** The identity check happens before the modal prompt. Adding
  freshness at the existing call site does not satisfy handoff §13, which requires authorization
  after the prompt returns. This belongs to Step 3.
- **R11 — Fit target vocabulary.** `p03_unmapped_relevant_controls` queries target literals outside the
  scope, twice per stage (plan and verify). An adapter `query_many` that silently acquires new folds
  would do so **unpinned**, violating `Gfit`. This belongs to Step 4. Until then, the Fit route must
  not get an unpinned adapter.
- **R12 — name collision.** The existing `operation_context` (a scene token) could be confused with
  the future CPM Operation Authority Context. New code should use a distinct name.

**Structural**

- **R13 — no runnable CPM candidate exists outside the frozen baseline.** G18AN must not be modified.
  Wiring therefore needs a new CPM runtime source derived from G18AN, and the handoff (§2) says no
  later runnable candidate is authoritative yet. Where that candidate lives, and how it is diffed
  against G18AN, is a decision for the reviewer before Step 2 implementation.

---

## 6. Recommended next implementation step (not implemented)

**Step 2a — offline adapter, no CPM runtime edits.** Add a CPM-owned authority adapter module under
`cpm/convergence/` that:

1. performs the canonical bootstrap checks (locator formula with an offline equivalence test against
   the Normalizer's formula; origin, API and build checks; `runtime.get_broker`);
2. exposes the provider-shaped facade (`generation_descriptor()`, `query_many(literals)`), with
   acquire → lease → validate → interpret → release inside each call and no retained lease or view;
3. maps broker failures to the G18AN "unavailable" health shape, never to absence;
4. produces the full descriptor dict required by `prod_scope` and the health gate, with the R3
   decision made explicitly;
5. exposes a freshness check (`expected_generation` = scope SHA) for `prod_scope_matches_identity`.

Qualify it offline against G18AN by extracting `semantic_snapshot_from_live_vocabulary`,
`semantic_snapshot_signature`, `prod_pure_semantic_row` and the health function verbatim (the same
technique as Suite 1) and feeding them synthetic live-binding fixtures. This closes the deferred
snapshot/signature parity item (R5) and runs under both interpreters.

**Step 2b — wiring**, after review of 2a and the R13 decision: a G18AN-derived CPM candidate that
injects the adapter into `render → prod_scope`, reroutes `prod_current_provider_descriptor` and
`prod_probe_semantic_provider`, disables the development parity route, and applies the R6 fail-closed
rule for late helpers until Step 3.

Do not start Step 3 (Operation Authority Context), Step 4 (Fit), Stage M, Stage F, UI changes, K or
release work as part of Step 2.

---

## 7. Files and functions inspected

**Frozen baseline** (`cpm/baseline/SFM_CSP_G18AN_SaveNewCopy.py`, read-only):

- Provider: `SEMANTIC_PROVIDER_FORCE_MODE` @1128, globals @1849–1854, `g18an_verified_sidecar_paths`
  @1914, `g18an_import_frozen_sidecar_provider` @2079, `g18an_normalize_sidecar_path` @2259,
  `SidecarSemanticProvider` @2298 (`__init__`, `_resident_handle`, `generation_descriptor` @2489,
  `_answer_from_result` @2496, `query_many` @2590), `acquire_semantic_provider_for_mode` @3301,
  `get_semantic_provider` @3339, `invalidate_semantic_provider` @3391.
- Snapshot: `semantic_snapshot_from_live_vocabulary` @3769, `semantic_snapshot_signature` @3865,
  `semantic_snapshot_for_model_row` @3885.
- Production scope/identity: `prod_semantic_provider_health_from_descriptor` @18517,
  `prod_probe_semantic_provider` @18612, `prod_current_provider_descriptor` @19109,
  `prod_pure_semantic_row` @19113, `prod_scope_pure_assert` @19167, `prod_validate_context_token` @19375,
  `prod_scope_matches_identity` @19527, `prod_live_bindings_for_cached_scope` @19644,
  `prod_provider_capture` @20041, `prod_character_record` @20065, `prod_ensure_character` @20120,
  `prod_scope` @20136, `prod_set_override` @20384, `prod_clear_override` @20512.
- Operations: `prod_save` @26233, `prod_update_preset` @26554, `prod_verify_apply_abort_baseline`
  @27045, `prod_apply` @27257, `prod_body_source` @27733, `prod_body_source_live_from_baseline`
  @27809, `prod_match_candidates` @27896.
- Fit: `p03_unmapped_relevant_controls` @7225, `g11a_source` @16161, `g11a_safe_plan` @16284,
  `ProdWindow.fit_stage` @33182.
- Diagnostics: `g18an_decision_parity_for_row` @3174, `g18an_clothing_decisions` @3128,
  `semantic_provider_runtime_stats` @3430.
- UI: `ProdWindow` @28097 (`render` @30503, `semantic_provider_ready` @29549, `apply_scope_to_ui`
  @30974, `save_kind` @31992, `update_kind` @32214, `review_reclassify` @31761, `review_decision`
  @31855, `open_details` @34153, parity shortcut @28601/@28841), `StartProdTool` (module bottom).

**Shared package** (read-only): `broker.py` (`acquire_or_reuse_views`, `lease_view`,
`release_view_lease`), `views.py` (`DetachedView`, `CoverageResult`, `CoverageDescriptor`),
`descriptors.py` (`SemanticGeneration`, `ArtifactIdentity`), `runtime.py` (`RUNTIME_API_VERSION`,
`RUNTIME_BUILD_ID`, `get_broker`), `candidate_packed_provider_r3a2b.py` (`occurrence_count`,
`fold_count`, `wrapper_path`, `lookup_fold`).

**Normalizer reference** (read-only): `audit_external_runtime/Rebuild_Control_Groups_Normalizer.py`
(the `sys.executable`-derived MAINMENU locator).

**Step 1:** `cpm/convergence/cpm_compat_v1_projection.py`.
