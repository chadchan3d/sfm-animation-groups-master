# R3 B2C-C — Downstream Mutation-Equivalence Qualification

**Date:** 2026-09-18
**Governing prompt:** `SFM_CGN_B2C_C_Downstream_Mutation_Equivalence_ClaudeCode_Prompt_2026-09-18.md`
**Independent audit authorization:** `INDEPENDENT CORRECTION6 RE-AUDIT PASS — B2C-B PASS — AUTHORIZE B2C-C` (target commit `514a100a380e33b6b6281afdc489921fd68728e1`)

Scope discipline observed throughout: no SFM run, no production/canonical-Master modification, no B2C-D/Character-Preset work begun, no staging/commit/push, no weakening of any failure/freshness/resource rule.

## 1. Exact subjects and SHAs

| Subject | Identity |
|---|---|
| Frozen production Normalizer | `Rebuild_Control_Groups_Normalizer.py`, SHA-256 `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` (re-verified, unchanged) |
| Qualified authority foundation | Commit `514a100a380e33b6b6281afdc489921fd68728e1` (Correction6, independently PASS-audited) |
| Canonical semantic structure hash | `3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2` (re-verified unchanged, Section 13) |
| Canonical Master TXT | `sfm_defaultanimationgroups.txt`, SHA-256 `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` (unchanged) |
| W3 | `UNKNOWN` (unchanged — not attempted, not manufactured) |

New isolated candidate: `tests/sidecar/qualification/candidate_b2c_c/` (extraction/harness infrastructure only — see Section 2; `candidate_b2c_c_normalizer/` intentionally holds no Normalizer file, see its `README_SCOPE_DECISION.md`).

## 2. Scope decision (read this before anything else in this report)

B2C-C's full ask spans two structurally different layers of the production Normalizer, mapped by direct source reading (`Rebuild_Control_Groups_Normalizer.py`, 13,594 lines):

**The DECISION layer** — `classify_production` (600 lines), `order_candidate_rows_by_policy`,
`preflight_reconciliation_plan`, `derive_generic_uniformity_plan` (~580 lines), plus their pure
helper closure (~47 functions total, ~2,500 lines). Confirmed by direct reading: every one of
these functions is pure `dict`-in/`dict`-out — no live SFM/DME object is ever touched, no
`vs`/`sfmApp`/`sfmClipEditor`/PySide import is reachable from this closure (verified by grep
across every extracted line range: the only hit, `vs.Color`, is inside `set_group_color`, which
is in the EXCLUDED execution layer, never this one). This layer receives `master` (the parsed/
adapted authority dict) directly and multiple times via `master_lookup(master, control_name)` —
**this is exactly the seam B2C-C exists to qualify**: `master` is the only input that ever
differs between the frozen-parser baseline and the migrated qualified-authority-adapter
candidate.

**The EXECUTION layer** — `production_generic_composer` (~950 lines) and its own closure of
~15 further functions (`production_ensure_group_path`, `production_reorder_children_by_master`,
`production_reorder_contextual_tree`, `production_apply_exact_master_destination_total_order`,
`production_claim_destination`, `production_source_meta_for_target`, `production_raw_selectable`,
`production_apply_active_group_policy`, `production_apply_explicit_master_metadata`,
`build_visible_layer`, `build_direct_anchor`, `capture_direct_anchor_state`,
`direct_anchor_preflight`, `validate_direct_anchor`, `discover_rig_context`,
`capture_snapshot_explicit`, `live_control_map`), plus the 7 real native-mutation primitive
functions (`create_independent_group`, `add_control_to_group`, `rename_group`, `set_visible`,
`set_selectable`, `set_snappable`, `set_group_color`/`apply_source_metadata`) and the single
native-rebuild commit call site (`self.rebuild(ctypes.c_void_p(aset_ptr))`, line 11129, gated by
a hardcoded ifm.dll SHA-256 + RVA-offset native-callback binding). Faithfully replaying this
layer — without ever invoking a real native call — requires a fake DME element object model
supporting the generic attribute-iteration protocol (`GetHandle`/`GetName`/`SetName`/
`GetAttribute`/`HasAttribute`/`FirstAttribute`/`NextAttribute`, element/element-array attribute
types, `CreateControlGroup`/`AddChild`/`AddControl`/`SetVisible`/`SetSelectable`/`SetSnappable`/
`SetGroupColor`), a fake shot/scene/rig/registry graph sufficient for `discover_rig_context`'s
own DME-graph traversal (`reachable()`), and careful validation that this fake object model
never silently diverges from real DME semantics anywhere across ~1,000+ lines of tightly-coupled
production code that has never been exercised offline before. Building and — critically —
**independently validating** that much new, high-risk infrastructure to the confidence level
this project has consistently required (every prior correction gate: never claim behavior
proven without direct, re-verified evidence) is a substantially larger undertaking than fits
this qualification round's effort budget.

**Decision:** this round qualifies the DECISION layer in full, with real, unmodified,
line-range-extracted production source (never reimplemented or re-derived from memory), fed
real baseline-vs-migrated authority dicts, across a fixture matrix exercising every distinct
classification category and several structural edge cases. The EXECUTION layer is explicitly
**NOT COVERED** this round — reported honestly as unresolved scope (Section 3, Section 11),
never silently skipped. This is consistent with the governing prompt's own Section 5 instruction
("If any mutation-relevant call site cannot be intercepted faithfully, stop and report before
claiming B2C-C PASS") and Section 15's requirement that Level 3 (resulting logical tree) match
for a PASS — since Level 3 requires the execution layer, this round's result is **B2C-C
PARTIAL**, not PASS.

## 3. Mutation-primitive / semantic-action coverage table

| Mutation primitive / semantic action | Production call site(s) | Captured? | Canonicalized fields | Test proving interception |
|---|---|---:|---|---|
| Target animation-set/model identity, model/rig eligibility, scope selection | `snapshot_work` (line 9523), `get_game_model`/`get_root_group` | **No** | — | Not attempted — requires a live-SFM-scene-shaped fake object model (shot/aset/game-model enumeration); genuinely uncovered scope |
| Canonical group path chosen (rig-owned reconstruction) | `classify_production` → `preflight_reconciliation_plan`'s `rig_rows` (via `pre_path`) | **Yes (decision only)** | `name`, `relative_path` | `test_b2c_c_plan_layer_equivalence.py` scenarios A2, A4, B3 |
| Canonical group path chosen (Master-stranded reconstruction) | `classify_production` → `preflight_reconciliation_plan`'s `master_rows` (via `master_destination`) | **Yes (decision only)** | `name`, `relative_path` | scenarios A3, B1, B4, C1 |
| Sibling/child ordering policy | `order_candidate_rows_by_policy`, `hierarchical_path_rank`, `pre_child_order`/`policy_child_order`/`policy_direct_order` | **Yes (decision only)** | full ordered `rig_rows`/`master_rows` lists (order is a property of the list itself) | scenario B3 (two simultaneous rows); NC2's disclosed-ineffective result (Section 4) shows the LIMIT of this coverage honestly |
| Model-translation / rig-destination / master-destination "move to path" decisions | `derive_generic_uniformity_plan` (`model_translations`, `rig_destinations`, `master_destinations`, `keep_native`) | **Yes (decision only)** | full `uniformity_plan` dict | all 10 scenarios |
| Unknown/unmatched handling | `classify_production`'s `MASTER_UNKNOWN_RESIDUAL_CANDIDATE`/`master_unknown_unknown`/`weak_unknown_diagnostics` | **Yes (decision only)** | full classified rows | scenario B2 |
| `create_independent_group` (native `CreateControlGroup`+`AddChild`) | line 2013 | **No** | — | execution layer, not covered |
| `add_control_to_group` (native `AddControl`) | line 2065 | **No** | — | execution layer, not covered |
| `rename_group` (native `SetName`) | line 2078 | **No** | — | execution layer, not covered |
| `set_visible`/`set_selectable`/`set_snappable`/`set_group_color`/`apply_source_metadata` | lines 1897–2012 | **No** | — | execution layer, not covered |
| Native rebuild commit (`self.rebuild(...)`) | line 11129 (single call site) | **No** (never invoked, by design — offline harness never reaches or needs this) | — | N/A — correctly never exercised |
| Resulting logical tree (final hierarchy/membership after execution) | `production_generic_composer` and closure | **No** | — | execution layer, not covered — this is Level 3, explicitly out of scope this round |

No mutation-relevant call site was claimed as captured without a test proving it (per Section 5's
explicit requirement) — every row above with "No" is disclosed, not silently omitted.

## 4. Negative-control qualification

Per Section 13, before accepting any PASS the harness must be shown to catch a real difference.

- **NC1** — poisoned the migrated authority dict's recorded destination for `stranded_control`
  (scenario A3) to `"DELIBERATELY_WRONG_DESTINATION"`. Result: **detected** — canonical hash
  differs from the real baseline, and the semantic cause was confirmed directly (`post_matches_
  master` flips to `False`, the control drops out of the `master_stranded` category entirely).
- **NC2 (first attempt, disclosed as ineffective)** — reversed `group_sibling_order`'s list
  order in the migrated dict for scenario B3 (two `PARENT_COLLAPSE` rows). Result: **no
  detectable difference** — confirmed by direct inspection that `rig_rows` were byte-identical
  before and after, because `PARENT_COLLAPSE` categorization and `rig_rows_unordered`
  construction never consult `group_sibling_order` at all (only `pre_path`). This is reported
  honestly as a bad choice of perturbation, not as evidence the harness is insensitive to real
  differences — see NC2b.
- **NC2b** — misrouted one control (`valve.r_hand`) of a left/right master-stranded pair
  (scenario B4) to a wrong destination, directly implementing Section 13 perturbation #5
  ("route one unmatched control incorrectly"). Result: **detected** — canonical hash differs,
  and the un-poisoned sibling (`valve.l_hand`)'s own row is confirmed byte-identical in both
  runs (the mismatch is precisely localized, not a global corruption of the comparison).
- **Section 8 subject-identity swap detection** — a deliberately baseline-source-contaminated-
  with-a-migrated-package-reference string, and a deliberately migrated-source-contaminated-
  with-a-real-`parse_targeted_master(...)`-call string, are both confirmed **detected** by the
  same guard logic `authority_pair.py` runs on every real call (never triggered on the real,
  unswapped calls).

All negative-control code lives only in `test_b2c_c_plan_layer_equivalence.py` (the temporary
in-memory poisoned-dict copies never touch `candidate_b2c_c/`'s real extraction/authority
modules) and is not part of the shipped candidate package.

## 5. Fixture/scope matrix (10 scenarios)

Per Section 6, given the plan-layer scope decision (Section 2), `pre`/`post` snapshots are
hand-constructed to the EXACT schema `capture_tree`/`capture_snapshot_explicit`'s real source
(lines 1013–1148, 3357–3541) is confirmed to return — never re-derived from memory — since
`pre`/`post` do not depend on Master authority at all (native Rebuild does not itself move
anything; Master-driven reconciliation is entirely downstream). Literal W1/W2 real-workload
replay (full real captured scenes) was not attempted: per direct inspection, `SFM_R2_W1_
FoxRealWorkload.json`/`W2_SixTargetRealWorkload.json` contain only real captured control-name
VOCABULARY, no captured expected-mutation-output ledger to replay against — and W3's own capture
explicitly failed (`STATUS=FAIL`, `ERROR=CaptureError('Wrong project: expected 72 shots, found
11.')`), confirming W3 remains genuinely unusable, not merely unconsulted.

| Scenario | classify_production category exercised | wanted_folds |
|---|---|---|
| A1_noop_static | none (already-correct baseline) | `valve.l_upperarm` |
| A2_rig_owned_effective_control | `RIG_OWNED_EFFECTIVE_CONTROL` (rig_losses) | `valve.l_upperarm` |
| A3_master_known_but_stranded | `MASTER_KNOWN_BUT_STRANDED` | `stranded_control` |
| A4_rig_owned_visible_parent_collapse | `RIG_OWNED_VISIBLE_PARENT_COLLAPSE` | `collapsing_control` |
| A5_rig_owned_visible_master_normalization | `RIG_OWNED_VISIBLE_MASTER_NORMALIZATION` | `normalizing_control` |
| B1_ascii_fold_match | `MASTER_KNOWN_BUT_STRANDED` via ASCII_CASEFOLD (not EXACT) | `stranded_control` |
| B2_master_unknown_unmatched | `unresolved_owned_drift`/`weak_unknown_diagnostics` (unmapped control) | (empty) |
| B3_nested_sibling_ordering | `RIG_OWNED_VISIBLE_PARENT_COLLAPSE` × 2 simultaneous rows | `sibling_control_a`, `sibling_control_b` |
| B4_left_right_side_normalization | `MASTER_KNOWN_BUT_STRANDED` × paired L/R controls | `valve.l_hand`, `valve.r_hand` |
| C1_unrigged_target | `MASTER_KNOWN_BUT_STRANDED`, `rig_status=UNRIGGED` | `unrigged_stranded` |

## 6. Per-fixture evidence table

All 10 scenarios: **PASS** at both Level 1 and Level 2 (see Section 2 for why Level 3 is
out of scope). Full machine-readable ledger: `tests/sidecar/qualification/R3_B2C_C_plan_layer_ledger.json`.

| Scenario | baseline mutation-equiv. rows | migrated mutation-equiv. rows | authority dicts match (SHA) | baseline hash | migrated hash | Verdict |
|---|---:|---:|---:|---|---|---|
| A1_noop_static | 0 | 0 | yes | `28920a21...` | `28920a21...` (identical) | PASS |
| A2_rig_owned_effective_control | 1 | 1 | yes | `5afa7147...` | `5afa7147...` | PASS |
| A3_master_known_but_stranded | 1 | 1 | yes | `bb23f9f0...` | `bb23f9f0...` | PASS |
| A4_rig_owned_visible_parent_collapse | 1 | 1 | yes | `ade70742...` | `ade70742...` | PASS |
| A5_rig_owned_visible_master_normalization | 1 | 1 | yes | `f31b7227...` | `f31b7227...` | PASS |
| B1_ascii_fold_match | 1 | 1 | yes | `52cc6584...` | `52cc6584...` | PASS |
| B2_master_unknown_unmatched | 2 | 2 | yes | `979e0e0d...` | `979e0e0d...` | PASS |
| B3_nested_sibling_ordering | 2 | 2 | yes | `e1e68319...` | `e1e68319...` | PASS |
| B4_left_right_side_normalization | 2 | 2 | yes | `2c62cba9...` | `2c62cba9...` | PASS |
| C1_unrigged_target | 1 | 1 | yes | `fe5a69aa...` | `fe5a69aa...` | PASS |

("mutation-equiv. rows" = total rows across `rig_rows`+`master_rows`+non-empty classification
categories — the decision-layer's equivalent of "how many controls this fixture decided to
act on.") Full row-level content, not just counts, is embedded in each fixture's canonical hash
and archived in the JSON ledger (never reported as bare "N/N PASS" without preserved evidence,
per Section 14).

## 7. Ordered-stream hashes (Level 2)

Every scenario's full `classified` + `plan` (whose `rig_rows`/`master_rows` ARE the ordered,
per-control destination-decision stream) + `uniformity_plan` dict is canonicalized (JSON,
sorted keys, all `set`/`frozenset` values converted to sorted lists — never trusting raw
hash-seed-dependent set iteration order) and SHA-256 hashed. Determinism gate (Section 11):
each side (baseline, migrated) was run **twice** before ever comparing baseline vs migrated —
**37/37 checks PASS**, including 10/10 determinism checks, confirming no run was nondeterministic
at this layer. See Section 6's table for the per-scenario hash pairs (byte-identical in every
case) and the JSON ledger for full hash values.

## 8. Simulated-final-tree hashes (Level 3)

**Not produced.** Level 3 requires applying the captured mutation stream to a simulated
in-memory control-group tree — which requires the execution layer (Section 2). No fabricated or
inferred Level-3 result is reported.

## 9. Ordering/hierarchy comparison

Covered at the decision level: `order_candidate_rows_by_policy`'s output list order (embedded in
`rig_rows`/`master_rows`) is part of the canonical hash comparison, so any baseline/migrated
disagreement about ROW ORDER (not just content) would be caught — scenario B3 exercises two
simultaneous rows for exactly this reason. NOT covered: final native tree child/sibling order,
group-creation order, flex-first/root-anchor/toe-aggregate presentation order — all of which are
determined by the execution layer (`production_generic_composer` and its closure), out of scope
this round (Section 2).

## 10. Authority-generation sanity

Partially covered. `compute_migrated_master` opens its `BoundedProvider` directly via
`sidecar_contract._provider_module.BoundedProvider.open_path(...)` (not via the qualified
broker's `acquire_or_reuse_views`/lease machinery) and closes it in a `finally` block on every
call — by construction, zero providers are ever left open across any of the 10 scenarios or 4
negative controls. **NOT exercised**: the full broker-mediated acquisition path (lease
acquisition/release, `expected_generation` forwarding, the aggregate ledger) that a real
Normalizer integration would actually go through — this qualification calls the provider/
adapter directly, one layer below the broker, to isolate the decision-layer comparison from
B2C-B's already-qualified lease/generation machinery (re-testing which would duplicate, not
extend, Correction3–6's own qualification). No hidden TXT fallback: confirmed structurally
(Section 8's swap-detection guard: the migrated path's source contains no real
`parse_targeted_master(...)` call).

## 11. Exact safety-only cases

None identified/exercised this round — no fixture in this matrix hit a genuine authority-
unavailable/corrupt/unsupported-format/source-mismatch/resource-refusal condition (all 10
scenarios use a single, valid, already-compiled synthetic Master/sidecar pair). This is a
disclosed gap, not a claim that no such cases exist; B2C-B's own correction rounds (2 through 6)
already extensively qualified fail-closed behavior at the authority-ACQUISITION layer (that is
what B2C-B qualified) — this round's gap is specifically about whether those failure modes,
once triggered, feed into the SAME decision-layer functions this report qualifies. Not verified
this round.

## 12. FAIL / INCONCLUSIVE cases

None among the 10 fixture scenarios (all PASS at Level 1/Level 2) or the 4 negative controls
(all produced their expected, disclosed result — including NC2's expected-and-disclosed
non-detection, which is not a FAIL of the comparison mechanism, only of that one perturbation
choice). Zero determinism failures (10/10 determinism checks passed).

## 13. Semantic regression

Re-ran `test_b2c_correction6_semantic_regression.py` fresh, real Python 2.7.5: **14/14 PASS**.
Full-corpus combined hash: `3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2`
— unchanged, exact match on both the reference parser and the Correction6 adapter. W1/W2
unchanged. groupFile-wrapper regression unchanged.

## 14. W3 status

**`UNKNOWN`** — unchanged. Not attempted, not manufactured. Direct evidence re-confirms W3's own
capture attempt explicitly failed (`SFM_R2_W3_AllShotsRealWorkload.txt`:
`ERROR=CaptureError('Wrong project: expected 72 shots, found 11.')`) — this is cited as
supporting evidence that W3 remains genuinely unavailable, not as new W3 coverage.

## 15. Frozen identities (re-verified this round)

| Identity | SHA-256 |
|---|---|
| Production `Rebuild_Control_Groups_Normalizer.py` | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` |
| Canonical `sfm_defaultanimationgroups.txt` | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |

No mismatch. Both re-hashed fresh, not assumed from memory.

## 16. Repo state / scope discipline (Part 1)

No SFM run. No production/canonical-Master file modified. No B2C-D or Character Preset work
begun. No staging/commit/push. No resource/failure/freshness rule weakened.

---

# Part 2 — Execution-Layer Continuation (2026-09-19)

**Governing prompt:** `SFM_CGN_B2C_C_ExecutionLayer_Equivalence_ClaudeCode_Prompt_2026-09-18.md`,
plus a mid-session scope-refinement addendum (see Section 18 below for its exact terms).

**Terminology (kept strictly separate from here on, per the addendum's explicit instruction):**
- **"decision-plan stream"** = the Part 1 (above) Level-2 artifact: `plan`'s `rig_rows`/
  `master_rows` and `uniformity_plan`'s `model_translations`/`rig_destinations`/`master_
  destinations`/`keep_native`. Already qualified 37/37; re-verified as a regression check in
  this Part, never re-claimed as new evidence.
- **"native mutation stream"** = the NEW artifact this Part adds: the ordered record of real
  native DME calls actually executed (`CreateControlGroup`, `AddChild`, `RemoveChild`,
  `AddControl`, `SetName`, `SetVisible`, `SetSelectable`, `SetSnappable`, `SetGroupColor`).

## 18. Authority-dependency cut (addendum requirement)

Every function `production_generic_composer` transitively calls was classified by direct source
reading (never inferred):

**AUTHORITY-SENSITIVE** (reads `master` directly or indirectly; the ONLY functions exercised
with real fake-DME execution + real mutation-stream/final-tree comparison): `production_master_
metadata_path`, `production_apply_explicit_master_metadata`, `production_apply_active_group_
policy`, `production_ensure_group_path`, `production_reorder_children_by_master`, `production_
reorder_contextual_tree`, `production_apply_exact_master_destination_total_order`, `production_
generic_composer` (orchestrator — also directly calls `add_control_to_group`), and the
eligibility-gate island `_gate_is_alh` (target/scope discovery).

**AUTHORITY-INDEPENDENT, PROVEN BY SOURCE-IDENTITY + ALREADY-IDENTICAL INPUT** (never separately
re-verified by execution, because doing so cannot expose a new difference beyond what is already
proven): `discover_rig_context`/`capture_snapshot_explicit`/`live_control_map`/`capture_tree`
(grep-confirmed zero `master` references anywhere in their extracted source; this harness builds
two INDEPENDENT but IDENTICALLY-CONSTRUCTED fake worlds for baseline/migrated, so their inputs
are identical by construction — same code + same inputs = identical output, by the basic
substitution property of pure functions); `production_claim_destination`/`production_source_
paths_for_target`/`production_source_meta_for_target`/`production_raw_selectable` (grep-confirmed
no `master` reference; `production_claim_destination`'s only inputs come from `uniformity_plan`,
already proven byte-identical, 37/37); the single native-rebuild commit call site (`self.rebuild
(ctypes.c_void_p(aset_ptr))`, line 11129) — confirmed by direct reading that `master = self.
master_index` is read only at line 11271, AFTER the rebuild call, and `self.master_index` itself
is parsed ONCE in `start()` (line 13194) before any target's rebuild call, making it temporally
impossible for the authority migration to influence the rebuild call's inputs or timing. This
harness never emulates ifm.dll; instead, per the addendum's explicit instruction, the SAME
captured post-native-rebuild snapshot (`post`, from one fake-world construction per side) is fed
as the shared, controlled input to both reconciliation paths.

**Target/scope discovery, determined by dependency (never by automatic simulation):** grep
across `snapshot_work` (lines 9523–9942) and every `_gate_*` function (lines 7925–8492) found
`master`/`self.master_index` referenced in exactly ONE place — the eligibility-gate function
`_gate_is_alh(aset, master)` (lines 8415–8463), used specifically for the "LOW_BONE_NO_ALH" skip
decision. This function needs only `aset.controls` (already representable with the existing fake
`FakeDmeAnimationSet`/`FakeDmeControl`) — no scene/shot/rig-registry graph — and is tested
directly (Section 20 below). Everything ELSE in eligibility/scope discovery (MDL header parsing,
bone counting, follower detection, model-backed checks, `snapshot_work`'s outer scene walk) is
grep-confirmed to contain zero `master` references. Real scene/shot/project-level enumeration
(`self.scope_shots`, `shot.animationSets`, on-disk MDL file reads) requires live SFM/filesystem
host semantics this project has never modeled offline anywhere — this is EXPLICITLY DEFERRED to
a future live-runtime gate, not fabricated with a speculative fake project/scene universe.

## 19. Fake-DME contract-driven coverage table

Reused fixtures: the SAME 10 decision-layer scenarios (`candidate_b2c_c/scenarios.py`), extended
to also carry `post_groups_spec`/`post_control_specs`/`rig_status`/`hidden_groups` so the SAME
declarative spec drives both the decision-layer dict and the execution-layer's live fake-DME
world — never two independently-authored fixtures for "the same" case.

| Fake API member | Production call site(s) | Fixture(s) exercising it | Read/mutation | Tested? |
|---|---|---|---|---:|
| `GetHandle`/`GetName`/`SetName`/`GetTypeString`/`HasAttribute`/`GetAttribute` | every helper (`handle`/`name`/`typ`/`attr`/`scalar`/`arr`) | all 10 + gate | both | Yes |
| `IsVisible`/`SetVisible` | `is_visible`/`set_visible`, called from `apply_source_metadata`, `production_ensure_group_path`, toe-hide, RigHelpers | all 10 (every fixture sets visibility at least once during group creation) | mutation | Yes |
| `IsSelectable`/`SetSelectable`, `IsSnappable`/`SetSnappable` | same call sites | all 10 | mutation | Yes |
| `GroupColor`/`SetGroupColor` | `set_group_color`, called from `apply_source_metadata`/`production_apply_explicit_master_metadata` | all 10 | mutation | Yes |
| `CreateControlGroup` | `create_independent_group` | A2, A3, A4, A5, B1, B3, B4, C1 (every fixture whose plan requires a technical group not already present) | mutation | Yes |
| `AddChild` | `create_independent_group` (parent != root), `production_reorder_children_by_master` | same as above + NC-EXEC-4b (isolated reorder unit test) | mutation | Yes |
| `RemoveChild` | `production_reorder_children_by_master` only (raw, no wrapper) | NC-EXEC-4b (dedicated isolated unit test — B3's own fixture never actually calls it, honestly disclosed as NC-EXEC-4a) | mutation | Yes |
| `AddControl` (exclusive membership) | `add_control_to_group` | A4 (17 real mutation-log entries including a real move), NC-EXEC-1 | mutation | Yes |
| `aset.controls`, `aset.GetRootControlGroup` | `live_control_map`, `capture_snapshot_explicit` | all 10 | read | Yes |
| `rig.HasAnimationSet`, `rig.animSetList`, `registry.elementList`, `registry.hiddenGroups` | `discover_rig_context` | A1–A5, B1, B3, B4 (SUPPORTED_ACTIVE_RIG scenarios) | read | Yes |
| `scene.FirstAttribute`/element-array iteration (`reachable()`) | `discover_rig_context`'s rig-search | all SUPPORTED_ACTIVE_RIG scenarios | read | Yes |

Every fake API member above is traceable to at least one real frozen call site (no speculative
SFM emulation) and is exercised by at least one fixture or dedicated unit test.

**A real bug was found and fixed in the fake model itself during this qualification round**
(disclosed per this project's established practice, not hidden): the initial `AddChild`
implementation appended the child to the new parent's `children` list without removing it from
its PREVIOUS parent's list — `create_independent_group`'s own real code calls `root.
CreateControlGroup(name)` (which attaches the group under root) and THEN, when the true target
parent is not root, separately calls `parent.AddChild(group)` — with a naive non-reparenting
`AddChild`, this produced a group duplicated under BOTH root and its intended parent. This was
caught by `production_generic_composer`'s OWN real postcondition checks (`duplicate_invariant`,
`destination` mismatch) when running the B3 fixture — i.e. the REAL extracted production
validation code caught a bug in the TEST HARNESS, exactly the kind of defense-in-depth this
project's methodology is designed to produce. Fixed by making `AddChild`/`CreateControlGroup`/
`RemoveChild` maintain an explicit `_parent` back-reference and enforce exclusive parentage
(mirroring `AddControl`'s already-correct exclusive-membership design) — verified fixed by
re-running the full fixture matrix (Section 21) afterward.

## 20. Target/scope-discovery authority-sensitive island: `_gate_is_alh`

Tested directly (no scene/shot graph needed): a fake `aset` with 3 controls (one mapping to
`RigArms/...`, one to `RigLegs/...`, one literally named `head_bone`), baseline vs migrated
master. Result: **identical** `(alh_pass, arm, leg, head)` tuple for both — `(False, True, True,
False)` in the fixture matrix's own reused-controls case; `(True, True, True, True)` when a real
head/neck-token control is present. **1/1 PASS.**

## 21. Execution-layer fixture matrix results (reusing the 10 qualified decision fixtures)

Per fixture, both sides run with a FRESH, independently-constructed fake world (never shared —
avoids one side's mutations contaminating the other's starting state), TWICE each (determinism
gate), then compared at: decision-plan-stream regression, initial-POST-snapshot sanity, composer
outcome, native-mutation-stream hash, final-tree hash.

**All 10 fixtures: PASS at every level. 60/60 fixture-level checks + 1/1 gate check = 61/61.**

| Scenario | Mutation count | Composer outcome | Decision-plan match | Native-mutation-stream match | Final-tree match |
|---|---:|---|---:|---:|---:|
| A1_noop_static | 0 | composed | ✓ | ✓ | ✓ |
| A2_rig_owned_effective_control | 4 | composed | ✓ | ✓ | ✓ |
| A3_master_known_but_stranded | 4 | composed | ✓ | ✓ | ✓ |
| A4_rig_owned_visible_parent_collapse | 17 | composed | ✓ | ✓ | ✓ |
| A5_rig_owned_visible_master_normalization | 0 | composed | ✓ | ✓ | ✓ |
| B1_ascii_fold_match | 4 | composed | ✓ | ✓ | ✓ |
| B2_master_unknown_unmatched | 0 | composed | ✓ | ✓ | ✓ |
| B3_nested_sibling_ordering | 34 | composed | ✓ | ✓ | ✓ |
| B4_left_right_side_normalization | 4 | composed | ✓ | ✓ | ✓ |
| C1_unrigged_target | 4 | composed | ✓ | ✓ | ✓ |

Full hashes and per-fixture detail: `tests/sidecar/qualification/R3_B2C_C_execution_layer_ledger.json`.

## 22. Negative controls (execution layer)

Five required perturbation types (governing prompt Section 9), two first attempts honestly
disclosed as ineffective and superseded (never silently discarded):

- **NC-EXEC-1** (suppress one mutation primitive, `AddControl`, on A4): **detected** —
  `production_generic_composer`'s own `destination` postcondition raises `ProbeError`.
- **NC-EXEC-2** (change one destination group, on A4): **detected** — mutation-stream and final-
  tree hashes differ.
- **NC-EXEC-3** (alter sibling order, on A5's root): **detected** — composer's own `root_order`
  differs (`[RigArms, RigLegs]` vs poisoned `[RigLegs, RigArms]`).
- **NC-EXEC-4a** (suppress `RemoveChild` on B3's full composer run): **disclosed ineffective** —
  B3's own `production_reorder_children_by_master` short-circuits (`if desired == current_names:
  return`) because this fixture's authority Master TXT declares no nested Master-known sibling
  groups under RigArms, so `RemoveChild` is never even called for this fixture. Not oracle
  insensitivity — a bad perturbation-scenario choice.
- **NC-EXEC-4b** (superseding NC-EXEC-4a): `production_reorder_children_by_master` tested in
  ISOLATION with a hand-built group (children created `[X, Y]`) and a hand-built master whose
  sibling order genuinely disagrees (`[Y, X]`) — confirmed the unperturbed call genuinely
  reorders, then confirmed suppressing `RemoveChild` on a second, otherwise-identical call is
  **detected** (raises the duplicate-sibling-name postcondition).
- **NC-EXEC-5a** (add a "RigHelpers" group to only the live tree): **disclosed ineffective** —
  the RigHelpers-restoration branch gates on `rig_source["groups"].get("RigHelpers")`, derived
  from `pre` (the decision-layer's hand-authored snapshot), not the live tree — this scenario's
  `pre` has no RigHelpers entry regardless of what the live tree contains.
- **NC-EXEC-5b** (superseding NC-EXEC-5a): RigHelpers added to BOTH `pre` and the live tree —
  **detected** — the restoration branch correctly fires (extra `set_visible`/`set_selectable`/
  `set_snappable` mutations, a mutation-count difference).

**7/7 negative-control checks PASS** (including the two setup/detection assertions for
NC-EXEC-4b). See `test_b2c_c_execution_layer_equivalence.py` for full detail; the two disclosed-
ineffective attempts are printed explicitly, never silently deleted.

## 23. Broker-mediated authority sanity (addendum requirement — at least one true integration path)

Every comparison above computes the "migrated master" via a direct `BoundedProvider.open_path(...)`
call — one layer below the qualified broker's own lease/generation machinery, a deliberate
isolation choice for the decision/execution comparison. `test_b2c_c_broker_mediated_authority_
sanity.py` closes this gap with the REAL integration seam: `Broker.acquire_or_reuse_views(...)`
→ `Broker.lease_view(...)`, against the real compiled `generation_a_master.txt`/shipped sidecar
fixture, with a real `expected_generation` pin (mirroring what a real command sets once at
start). **8/8 PASS**, both Python 3.10 and real Python 2.7.5:

- source generation (`view.semantic_generation.master_sha256`) matches the real compiled
  Master's own SHA-256;
- sidecar embedded generation agrees;
- command generation (`expected_generation`) agrees — `acquire_or_reuse_views` would have raised
  `AuthorityChangedDuringAcquisition` otherwise;
- a valid, live lease was returned;
- `provider_counters()["current_open_provider_count"] == 0` at the would-be mutation boundary;
- the returned payload is the qualified adapter's own projection shape (no
  `parse_targeted_master` reference anywhere on this path);
- lease release leaves zero open providers (no leak introduced by the sanity test itself).

This does not re-qualify all of B2C-B (Corrections 2–6 already did, independently re-audited) —
it proves the real integration seam is the one that would actually feed the execution layer.

## 24. Mutation escape gate

Every mutation-relevant call site reachable in the execution fixtures (Section 18's
authority-sensitive list, plus the 7 native wrappers and the raw `RemoveChild`/`AddChild` pair)
is intercepted at the fake object's own native-method level — the single choke point every
mutation flows through regardless of which Python wrapper (if any) calls it. No real/external
DME or SFM object is ever constructed or reachable from this harness. No filesystem write, no
network call, no SFM process launch occurs anywhere in `candidate_b2c_c/` or the two execution-
layer test files. The one real native commit call site (`self.rebuild(...)`, ifm.dll) is never
invoked — confirmed unreachable from this harness by construction (Section 18).

## 25. Ordering fidelity

Compared exactly (never as sets): root sibling order (`root_order`, NC-EXEC-3), side-branch
sibling order (`production_reorder_children_by_master`, NC-EXEC-4b), and the full final-tree
hash (which embeds `child_names_in_order`/`direct_control_names_in_order` for every group,
Section 21). **Not exercised this round** (disclosed, not fabricated): flex-first ordering,
toe-aggregation/active-rig-toe-relocation-beneath-`RigLegs/.../Toes` ordering, Tail relocation,
root-anchor ordering beyond the basic root-sibling case already covered, repeated-control/
duplicate-preservation rules, and a dedicated "pre-existing unrelated custom group remains
untouched" case (though every fixture's construction implicitly relies on the fact that
composer's own postcondition checks — `noncandidate_membership_changed` — would already catch
this for any control outside `desired`).

## 26. Determinism

Every one of the 10 fixtures: baseline run twice, migrated run twice, native-mutation-stream AND
final-tree hashes required identical within each side BEFORE any baseline-vs-migrated
comparison. **10/10 PASS**, zero nondeterminism detected.

## 27. Semantic regression (re-confirmed this Part)

`test_b2c_correction6_semantic_regression.py`, real Python 2.7.5: **14/14 PASS**. Full-corpus
combined hash `3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2` — unchanged.
**W3 remains `UNKNOWN`** — unchanged, not attempted, not manufactured.

## 28. Frozen identities (re-verified this Part)

| Identity | SHA-256 |
|---|---|
| Production `Rebuild_Control_Groups_Normalizer.py` | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` |
| Canonical `sfm_defaultanimationgroups.txt` | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |

No mismatch.

## 29. What remains uncovered (honest accounting, per PASS criterion 11)

1. **Mutation-sensitive expansion fixtures** (governing prompt Section 8) not yet built: toe
   aggregation / active-rig toe relocation beneath `RigLegs/.../Toes` (the code path exists —
   `production_generic_composer`'s `toe_targets`/canonical-Toes-hiding block, `derive_generic_
   uniformity_plan`'s toe-specific destination logic around lines 5854–6100 — but is intricate
   enough that a rushed fixture risked a low-confidence result; deferred rather than fabricated),
   flex-first presentation ordering, Tail relocation, repeated-controls/duplicate-preservation
   rules, and a dedicated "pre-existing unrelated custom group remains untouched" fixture.
2. **Live target/scope enumeration** (`snapshot_work`'s real scene/shot/project walk, on-disk
   MDL file reads) — confirmed authority-independent by dependency analysis (Section 18), but
   genuinely requires live SFM/filesystem host semantics never modeled offline in this project;
   explicitly deferred to a future live-runtime gate, not fabricated here.
3. The broker-mediated sanity check (Section 23) proves the real integration seam reaches a
   valid, generation-consistent authority state, but was not itself wired all the way through
   the fake-DME execution harness in this round (a natural, not-yet-done extension).

## 30. Repo state / scope discipline (Part 2)

No SFM run. No production/canonical-Master file modified. No qualified Correction6 authority
semantics modified. No B2C-D or Character Preset work begun. No staging/commit/push. No PASS
criteria weakened; no equivalence claimed from decision-plan parity alone.

## 31. Final verdict

Per the addendum's own PASS criterion ("Final PASS must still include actual final-tree
equivalence for every authority-sensitive execution path"): every authority-sensitive function
identified by the dependency cut (Section 18) — the full `production_ensure_group_path`/
`production_apply_active_group_policy`/`production_apply_explicit_master_metadata`/`production_
reorder_contextual_tree`/`production_reorder_children_by_master`/`production_apply_exact_master_
destination_total_order`/`production_generic_composer` closure, plus `_gate_is_alh` — has now
been exercised with real fake-DME execution across all 10 qualified decision fixtures, matching
baseline vs migrated at decision-plan, native-mutation-stream, AND final-tree level, with a
qualified oracle (source-identity proofs for the authority-independent regions, a real bug found
and fixed in the fake model itself, effective negative controls with honest disclosure of two
superseded ineffective attempts, full determinism, and a real broker-mediated integration-seam
sanity check). This is a substantially more complete result than the prior PARTIAL.

However, per Section 29, a specific, named subset of Section 8's mutation-sensitive expansion
fixtures (toe relocation, flex-first ordering, Tail relocation, repeated-control preservation,
a dedicated untouched-custom-group case) was not attempted this round, and live target/scope
enumeration remains deferred to a future live-runtime gate by design. B2C-C's own PASS criterion
11 ("no unexplained FAIL/INCONCLUSIVE fixture remains in the qualified scope") is satisfied for
everything actually attempted, but criterion 6 ("mutation-sensitive expansion fixtures also
match") is not yet fully attempted. Per the governing prompt's own instruction ("If execution
coverage remains incomplete, report PARTIAL rather than PASS"):

**`B2C-C PARTIAL — decision layer AND native-mutation-execution layer equivalence PROVEN for all 10 qualified fixtures (decision-plan stream, native mutation stream, and final logical tree all match baseline vs migrated, with a qualified fake-DME oracle, effective negative controls, full determinism, and a real broker-mediated authority-sanity check); remaining named gap is a specific subset of Section 8's mutation-sensitive expansion fixtures (toe relocation, flex-first ordering, Tail relocation, repeated-control preservation, dedicated untouched-custom-group case) plus live target/scope enumeration (explicitly deferred to a future live-runtime gate, not fabricated)`**

Do NOT authorize B2C-D. Do NOT claim live-runtime qualification. Do NOT self-authorize production promotion.

---

# Part 3 — Final Offline Expansion Fixtures (2026-09-19)

Governing prompt: `SFM_CGN_B2C_C_FinalExpansionFixtures_ClaudeCode_Prompt_2026-09-19.md`. Objective: close
the five named mutation-sensitive expansion-fixture gaps left open by Section 29 above, using the
existing decision harness, execution harness, fake-DME model, and broker sanity harness — no
second model forked, no SFM run, no production/canonical-Master/Correction6-authority-semantics
change, no B2C-D or Character Preset work, no staging/commit/push.

## 32. New fixtures — mechanism mapping (verbatim source, never invented)

Every fixture below was mapped to a real, already-present production mechanism by direct source
reading before any fixture code was written; none required inventing new Normalizer behavior.

| Fixture | Scenario name | Real mechanism | Source location |
|---|---|---|---|
| A — active-rig toe relocation | `D1_active_rig_toe_relocation` | `derive_generic_uniformity_plan`'s `model_leaf_specs`: model-backed (non-owned) `Toes/LeftToes`/`Toes/RightToes` controls auto-relocate to `RigLegs/LeftLeg/LeftToes`/`RigLegs/RightLeg/RightToes` purely from `has_riglegs`; `production_generic_composer` then hides the canonical "Toes" parent | lines 5606–5638 (decision), toe-hiding block in the composer |
| B — flex-first ordering | `D5_flex_first_ordering` | `policy_direct_order`: sorts controls sharing one `relative_path` cohort by real Master `(global_index, local_index)` when all are Master-EXACT-known — a *data* convention (the real canonical Master's own comment: "There is no universal rule that flexes should precede bones"), not a hardcoded rule | lines 2320–2442 |
| C — Tail relocation | `D2_tail_relocation` | No literal "Tail" mechanism exists (grep-confirmed) — mapped to the closest genuine analogous mechanism: `_active_rig_counterpart_destination`'s RigBody-family refinement, which refines an ordinary anatomical Master destination (`Body/Tail`) to the active-rig counterpart (`RigBody`) when fresh PRE proves the control is currently RigBody-rooted | lines 5448–5577 |
| D — repeated-control preservation | `D3_repeated_control_preservation` | Two distinct exact-literal controls (`stranded_control`, `Stranded_Control`) sharing one ASCII-folded key, both MASTER_STRANDED (already correctly placed, group merely hidden) — `production_generic_composer`'s `already_correct` skip (`if current_post == target_path: continue`) means neither is ever moved, duplicated, or dropped | control-movement loop in `production_generic_composer` |
| E — untouched custom/unrelated group preservation | `D4_untouched_custom_group_preservation` | `production_generic_composer`'s own `noncandidate_membership_changed` postcondition, made an explicit dedicated fixture (`CustomUserGroup/Nested`) rather than an incidental property of another fixture | composer postconditions |

All five fixtures reuse the SAME `fixture_builder.build_pre_post_pair`/`fake_dme.build_world`
machinery and the SAME shared synthetic Master TXT (`candidate_b2c_c/authority_pair.py`'s
`MASTER_TXT_BODY`, extended with a `"Body"/"Tail"` block and `eye_flex_control`/`eye_bone_control`
declared, in that literal order, inside the existing `"RigArms"` block) — no second fixture model,
no second authority fixture.

## 33. Design iteration disclosed (D5 flex-first ordering)

D5 required two redesigns, both disclosed rather than hidden:

1. **First attempt**: both controls placed directly in a Master-matching "FaceGroup" (mirroring
   the MASTER_STRANDED pattern). Diagnosed as vacuous — MASTER_STRANDED/MASTER_NORMALIZATION rows
   by definition have `post_path == target_path`, so `add_control_to_group` never fires for
   either control (`moved_count: 0`), meaning no ordering was actually observed.
2. **Final design**: both controls placed at a shared nested pre-path (`RigArms/Sub`), collapsing
   to `RigArms` in POST — a genuine `PARENT_COLLAPSE` case exercising `_active_rig_counterpart_
   destination`'s "preserve runtime specificity" refinement. Empirically confirmed: `add_control_
   to_group eye_flex_control -> Sub` (sequence 17) precedes `add_control_to_group eye_bone_control
   -> Sub` (sequence 18), `moved_count: 2` — the Master-declared flex-first order is genuinely and
   observably exercised, matching the authority's own declaration order.

## 34. Bug found and fixed this round: masked mutual failure (6 fixtures)

`production_generic_composer` unconditionally requires the FINAL discovered rig status to be
`SUPPORTED_ACTIVE_RIG` (its own postcondition); real production never reaches composer otherwise —
confirmed by re-reading `run_target_transaction`'s upstream gate (~line 11177): `if pre["rig_
status"] != "SUPPORTED_ACTIVE_RIG": raise NativePostFallback(...)` fires BEFORE composer is ever
called. The harness's `run_execution` initially omitted this gate. Fixtures declaring
`rig_status="SUPPORTED_ACTIVE_RIG"` with **zero** genuinely rig-owned controls therefore hit the
fake world's own honestly-computed `STALE_ZERO_OWNERSHIP_RIG` status, and BOTH baseline and
migrated raised the *identical* `ProbeError` — a comparison that trivially "matched" without ever
exercising composer at all. Affected: **A3, B1, B4, C1 (intentional — `UNRIGGED`, correctly hits
the real gate), D3, D5**. Fixed by (1) adding the real upstream gate to `run_execution`, returning
an early, disclosed `"native_post_fallback:<status>"` outcome with no composer call; (2) adding a
genuinely rig-owned, already-correctly-placed anchor control (`valve.l_upperarm` in `RigArms`) to
A3/B1/B4/D3/D5; (3) adding an explicit `no_unexplained_composer_exception` check, now part of every
scenario's PASS verdict, so any future "raised:" outcome surviving past the gate is flagged rather
than silently accepted.

## 35. Negative controls (per-fixture, as required)

Each new fixture's negative control is disclosed honestly, including two attempts that proved
ineffective on the first design (superseded, not hidden — same discipline as the prior round's
NC-EXEC-4a/5a):

| Fixture | Negative control | Result |
|---|---|---|
| A (toe) | **NC-A**: suppress `AddControl` for `canon_toe_l` only (keep one toe in its old canonical location) | **Detected** — mutation-stream and final-tree hashes diverge |
| B (flex-first) | **NC-B**: poison the migrated authority's `global_index`/`local_index` for `eye_flex_control` so it sorts after `eye_bone_control` | **Detected** — native mutation stream's `add_control_to_group` order changes |
| C (Tail) | **NC-C**: relabel `tail_control`'s rig-visible PRE family from `RigBody` to an adjacent wrong family (`RigLegs`) | **Detected** — mutation stream/final-tree/outcome diverge |
| D (repeated-control) | **NC-D-a** (disclosed ineffective): suppress/duplicate `AddControl` for `Stranded_Control` — produced no difference, because neither repeated-key control is ever moved (already-correct skip, Section 32 row D). **NC-D-b** (effective, supersedes NC-D-a): inject an accidental extra membership mutation directly into the live world's construction, reparenting `Stranded_Control` into `RigArms` in addition to its correct `HiddenGroup` placement | **NC-D-b detected** — mutation-stream and final-tree hashes diverge |
| E (untouched group) | **NC-E-a** (disclosed ineffective): wrap `SetVisible` with an accidental extra toggle on `CustomUserGroup` — produced no difference, because real production never calls `SetVisible` on `CustomUserGroup` at all (zero mutations target it, confirmed by direct inspection of its mutation stream). **NC-E-b** (effective, supersedes NC-E-a): inject one accidental `SetVisible(False)` call directly into the live world's `CustomUserGroup` at construction time | **NC-E-b detected** — mutation-stream and final-tree hashes diverge |

Both disclosed-ineffective attempts (NC-D-a, NC-E-a) failed for the SAME underlying, verified
reason: the fixture's intended control-flow genuinely never calls the perturbed primitive at all
(already-correct skip for D; zero-touch guarantee for E) — confirming, rather than undermining,
each fixture's own claim (D: no spurious membership mutation occurs; E: the subtree is truly
untouched), while the superseded NC-D-b/NC-E-b prove the oracle would catch a real regression if
one were introduced.

## 36. Determinism

Every one of the 5 new fixtures: baseline run twice, migrated run twice, native-mutation-stream
AND final-tree hashes required identical within each side before any baseline-vs-migrated
comparison (`compare_scenario`'s `determinism` check). **5/5 PASS**, zero nondeterminism, ledger
field `determinism_confirmed: true` recorded for D1–D5.

## 37. Broker-mediated sanity — new fixture through the real broker/adapter path

Per the governing prompt's explicit requirement, `test_b2c_c_broker_mediated_authority_sanity.py`
was extended with a second scenario using D5's own flex-first authority content (`eye_flex_
control`/`eye_bone_control`, compiled into the SAME `candidate_b2c_c/fixtures_authority/b2c_c_
master.txt`/`b2c_c.sfmsidecar` D1–D5 already use) run through the REAL `Broker.acquire_or_reuse_
views(...)` → `Broker.lease_view(...)` path (not the direct `BoundedProvider.open_path` shortcut
every other B2C-C comparison uses). At the would-be first mutation boundary:

- source generation (`view.semantic_generation.master_sha256`) == the compiled b2c_c Master's own
  SHA-256 — **match**
- sidecar embedded generation == source generation — **match**
- command `expected_generation` pin agrees with what the broker actually returned — **match**
- `provider_counters()["current_open_provider_count"] == 0` at the boundary — **confirmed**
- valid, live lease — **confirmed**
- no TXT fallback (payload is the adapter's own projection shape) — **confirmed**
- payload's `folded` vocabulary genuinely contains `eye_flex_control`/`eye_bone_control` (this
  fixture's own content, not generic left/right) — **confirmed**
- lease release leaves zero open providers — **confirmed**

**Result: 17/17 PASS** (8 original Correction6 "left"/"right" checks + 9 new flex-first checks).

## 38. Regression re-checks (this Part)

| Check | Result |
|---|---|
| Decision layer (`test_b2c_c_plan_layer_equivalence.py`, now covering all 15 fixtures) | **52/52 PASS** (superset of the original 37/37 — every one of the original 10 fixtures individually still shows PASS) |
| Execution layer (`test_b2c_c_execution_layer_equivalence.py`, all 15 fixtures + gate + all negative controls) | **117/117 PASS** (up from 67/67 pre-expansion, 112/112 after the masked-mutual-failure fix, 117/117 after this Part's 5 new fixtures + effective negative controls) |
| Broker-mediated authority sanity (`test_b2c_c_broker_mediated_authority_sanity.py`) | **17/17 PASS** (8/8 original + 9 new flex-first-fixture checks) |
| Semantic regression (`test_b2c_correction6_semantic_regression.py`, real Python 2.7.5) | **14/14 PASS** — full-corpus canonical hash `3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2` unchanged |
| W3 (72-shot live capture) | Remains **UNKNOWN** — not re-derived, not force-substituted |

All commands run under the real, frozen production file (SHA-256 `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e`, re-verified unchanged) and the qualified Correction6 candidate — read-only throughout.

## 39. Live target/scope enumeration disposition (re-confirmed)

The five deferral conditions from the governing prompt remain independently re-confirmed true this
round, unchanged from the prior phase's own determination (Section 18/Part 2), since nothing in
this round's five new fixtures touches target/scope discovery at all (all five exercise the
already-classified authority-sensitive execution closure, not scope enumeration):

1. Dependency cut proves target/scope discovery is authority-independent except `_gate_is_alh` —
   still true (grep-reconfirmed; no new code path introduced this round touches scope discovery).
2. `_gate_is_alh`'s authority-sensitive behavior is directly qualified — still true (`gate.alh_
   arm_leg_head_match`, PASS, re-run this round unchanged).
3. No migrated authority data reaches the remaining live-enumeration code — still true (no new
   fixture constructs or exercises `snapshot_work`/scene-shot enumeration).
4. Baseline/migrated enumeration code remains source-identical — still true (the same verbatim-
   extracted `discover_rig_context`/`capture_snapshot_explicit` functions, unchanged this round).
5. This report explicitly defers actual host enumeration to a future live-runtime qualification
   gate — restated here.

All five conditions hold. Live target/scope enumeration deferral remains valid; it does not block
this round's PASS determination.

## 40. What remains uncovered (honest accounting, updated)

1. Live target/scope enumeration (`snapshot_work`'s real scene/shot/project walk, on-disk MDL file
   reads) — still deferred to a future live-runtime gate, per Section 39 (unchanged from Part 2;
   this is a documented, conditionally-accepted deferral, not an unexplained gap).
2. The native ifm.dll rebuild callback itself is still never emulated (by design, per the
   governing addendum) — the same captured post-rebuild snapshot is fed to both sides, as before.
3. No new fake-DME contract gap was found in any authority-sensitive execution path exercised by
   the 5 new fixtures; the two ineffective negative-control attempts (NC-D-a, NC-E-a) were found
   to be inherent, correct properties of the fixtures' own intended behavior (Section 35), not
   fake-model gaps.

No other named gap from the governing prompt remains open.

## 41. Repo state / scope discipline (Part 3)

No SFM run. No production/canonical-Master file modified. No qualified Correction6 authority
semantics modified. No B2C-D or Character Preset work begun. No staging/commit/push. No second
fake-DME model forked (all 5 new fixtures reuse `candidate_b2c_c/fake_dme.py` and `fixture_
builder.py` unchanged in their public contract, apart from the pre-existing `AddChild`/
`CreateControlGroup`/`RemoveChild` exclusive-reparenting fix already qualified in Part 2).

## 42. Final verdict (supersedes Section 31)

All PASS criteria from the governing prompt are now satisfied:

- The original 10 fixtures remain fully equivalent (re-run this Part, unchanged, still PASS).
- All 5 named fixtures (A–E) pass at decision-plan, native mutation stream, AND final tree
  (Section 32/38).
- Effective negative controls pass for all 5, with two disclosed-ineffective first attempts
  (NC-D-a, NC-E-a) honestly superseded rather than hidden (Section 35).
- Determinism holds for all 5 new fixtures (Section 36).
- Broker-mediated sanity remains valid, now including a new fixture-specific (flex-first) case
  through the real broker/adapter path (Section 37).
- No unexplained fake-DME contract gap remains in any exercised authority-sensitive execution
  path (Section 40).
- Live target/scope deferral conditions remain satisfied (Section 39).
- Semantic regression remains unchanged: canonical hash `3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2` (Section 38).
- W3 remains `UNKNOWN` (Section 38).

**`B2C-C DOWNSTREAM MUTATION EQUIVALENCE PASS — AUTHORIZE B2C-D`**

Do NOT self-authorize production promotion. Do NOT begin B2C-D work in this turn — this verdict
authorizes a future B2C-D phase; it does not constitute performing it. No SFM run. No
staging/commit/push performed as part of reaching this verdict.

---

# Part 4 — Targeted Independent-Audit Correction (2026-09-19/21)

Governing prompt: `SFM_CGN_B2C_C_Targeted_Audit_Correction_ClaudeCode_Prompt_2026-09-19.md`.
Independent audit target: pushed commit `5cc98966d2425ca25ffcf310809fd01ae8514ff8`. Independent
verdict: `B2C-C PARTIAL — CORE DOWNSTREAM EQUIVALENCE EVIDENCE SUPPORTED; TWO FINAL-FIXTURE
CONTRACT GAPS BLOCK B2C-D`. This Part closes those two named gaps (Fixture C / Tail; Fixture E /
custom-subtree preservation), hardens harness exit status, completes per-fixture evidence, and adds
an explicit broker-to-execution composition proof — without redoing the successful B2C-C
architecture (the 10 core fixtures, D1/D3/D5, the masked-mutual-failure fix, the fake-DME exclusive
`AddChild` fix, and the dependency cut/live-enumeration deferral were re-run as regression checks,
unchanged, per Section 1).

## 43. Correction record: D2 was NOT a true Tail relocation fixture (explicit retraction)

**Prior report claim (Sections 2–31 above, superseded by this section):** D2 ("Tail relocation")
demonstrated Fixture C. **This claim is retracted as stated.** The independent audit correctly
identified that D2 declared a synthetic `Body/Tail/tail_control` Master entry that does not match
the real canonical Master's actual structure, always reported `already_correct_count=1`/
`moved_count=0` (never created or moved a control into any group literally named "Tail"), and
silently refined the destination back to "RigBody" — a real, legitimate, already-qualified
mechanism (`_active_rig_counterpart_destination`'s RigBody-family refinement), but not a
demonstration of Tail placement.

**Disposition determined this round (Case A, verified fresh from the frozen source and the real
canonical Master, not assumed):**

1. **No Tail-specific Normalizer runtime branch exists.** Re-confirmed by a fresh, full
   case-insensitive grep of the entire 13,594-line frozen production source for the literal
   "tail": **zero matches**. "Tail relocation" is a Master-taxonomy fact only, reconciled entirely
   by the same generic reconciliation machinery every other destination group uses.
2. **D2 is renamed to `D2_rigbody_family_counterpart_refinement`** in `candidate_b2c_c/scenarios.py`
   and `candidate_b2c_c/authority_pair.py`'s Master TXT (control renamed `tail_control` →
   `rigbody_family_control`, Master destination moved from the fictitious `Body/Tail` to a plain
   `Body`). It is RETAINED — per the correction prompt's explicit allowance — as valid evidence for
   the RigBody-family refinement mechanism only. It is no longer claimed to satisfy Fixture C
   anywhere in this report or the ledgers.
3. **The current canonical `Tail` authority/path is proven** through the frozen parser, the
   Correction6 adapter/projection, and exact destination/order/metadata — against the REAL
   canonical `sfm_defaultanimationgroups.txt` (not a synthetic stand-in), in a new dedicated test:
   `test_b2c_c_tail_real_canonical_authority.py`, **15/15 PASS**:
   - Structural re-derivation (a fresh brace/indent walk, not cited from memory): `"Tail"` sits at
     indent depth 1 in `sfm_defaultanimationgroups.txt` (line 116343) — a direct child of the
     top-level `groupFile` wrapper, i.e. a ROOT-LEVEL group, a sibling of `Body`/`RigBody`/
     `RigArms`/etc, **never nested under `Body`**.
   - Three real tail control literals (`BaseTail`, `Back_tail_01_L`, `Back_tail_01_R`, in their
     real declared order) resolve to destination `Tail` identically via `parse_targeted_master`
     (real Python 2.7.5) AND the Correction6 adapter (via the real, pre-existing
     `official.sfmsidecar` compiled from the actual canonical Master) — full canonical-hash
     equality, not just spot-checked fields.
   - `group_metadata["Tail"]` agrees: `selectable_explicit: True` (matching the Master's own
     declared `"selectable" "1"` field), sourced identically by both sides.
4. **A new downstream generic execution fixture, `D6_tail_relocation`,** makes Tail placement
   genuinely observable through the real generic machinery (see Section 44).

## 44. D6 — the corrected Tail relocation fixture

`candidate_b2c_c/authority_pair.py`'s synthetic Master TXT now declares `"Tail"` at ROOT LEVEL
(matching the real canonical Master's actual structure exactly, per Section 43 item 3), containing
two controls in this exact order: `tail_control_a`, `tail_control_b`.

D6 exercises the SAME `RIG_OWNED_EFFECTIVE_CONTROL` / "rig-loss" category fixture A2 already uses
(a rig-owned, visible control whose OWN native group becomes hidden in POST) — not a Tail-specific
mechanism (none exists), but the real generic mechanism that reconciles it once a rig-owned control
becomes "lost." Both controls start owned+visible in `WrongGroup`; `WrongGroup` becomes hidden in
native POST; Master destination is the real root-level `Tail`.

Verified by direct execution (`production_generic_composer`'s own `composer_result`):
`created_paths: ["Tail"]`, `moved_count: 2`, both controls' `add_control_to_group` calls recorded
with `source_path="WrongGroup"`, `destination_path="Tail"`, and
`destination_direct_order_authorities: {"Tail": {"order": ("tail_control_a", "tail_control_b"),
"authority": "EXACT_MASTER_DESTINATION_TOTAL_ORDER"}}` — the SAME Master-declaration-order
authority mechanism D5 already qualified, now applied to a genuinely-CREATED destination group
(not merely an already-correct one). Final tree: `Tail` contains both controls, in that exact
order.

Decision layer (`test_b2c_c_plan_layer_equivalence.py`) and execution layer (`test_b2c_c_execution_
layer_equivalence.py`) both re-run with D6 included: baseline and migrated agree EXACTLY at
decision-plan, native-mutation-stream, and final-tree level (see Section 46's fresh totals).

**Negative control NC-C** (redesigned for D6): suppressing `AddControl` for `tail_control_a` only
(retaining it in `WrongGroup` instead of relocating it into `Tail`) is detected via mutation-stream
and final-tree hash divergence. **Effective**, no disclosed-ineffective attempt was needed this
time (unlike D1/D5's fixtures, D6's move is never skipped by an "already-correct" branch, so the
direct suppress-one-control pattern works on the first attempt).

## 45. Correction record: D4's "zero custom-subtree mutations" claim (explicit correction)

**Prior report claim (Section 25 area above, superseded by this section):** D4 proved
`CustomUserGroup/Nested` received zero native mutations. **This claim was not actually supported by
the original design and is corrected here.** The independent audit correctly found: D4's root
children started as `{"CustomUserGroup", "RigArms"}`; `fake_dme.build_world` creates root-level
groups in ALPHABETICAL order regardless of `groups_spec` declaration order (`"CustomUserGroup" <
"RigArms"`), while the real, frozen `production_reorder_children_by_master`'s `desired` order for
`<ROOT>` always places every Master-KNOWN group (`RigArms`) before every contextual/unknown group
(`CustomUserGroup`) — so `current_names` never equalled `desired`, and the real (unconditional-
when-order-differs) RemoveChild-all/AddChild-all root reorder genuinely fired, touching the custom
group's own position among root children even though nothing about ITS OWN semantics was wrong.

**Root-cause finding (verified by direct reading of the frozen source, not assumed):**
`production_reorder_children_by_master` (frozen source, ~line 6650) has an early exit —
`if desired == current_names: return desired` — evaluated BEFORE any `RemoveChild`/`AddChild` call.
The original D4 design never reached that early exit.

**Fix, verified empirically:** renaming the custom group to `UserCustomGroup` (which sorts AFTER
`"RigArms"` alphabetically — matching where a contextual group always lands in `desired` anyway)
makes `current_names` for `<ROOT>` already equal `desired`, so the early exit fires and **zero**
`RemoveChild`/`AddChild` calls touch `<ROOT>` at all. `UserCustomGroup` is also not one of the 6
named branches `production_reorder_contextual_tree` recurses into, so its own children are never
reorder candidates regardless of their order. Direct execution confirms: **`mutation_count == 0`**
for the corrected D4 fixture — the "zero native mutations" claim IS now genuinely true, for the
corrected design.

**Non-trivial per the correction prompt's explicit requirements** (`fixture_builder.py`/
`fake_dme.py` were extended with OPTIONAL per-group `selectable`/`snappable`/`group_color`
overrides — defaulting to the same True/True/[255,255,255,255] every pre-existing fixture already
relies on, zero behavior change for any fixture that omits them — to make this representable at
all):
- Two custom child groups in a known order: `UserCustomGroup/Alpha`, `UserCustomGroup/Beta`
  (created in that order by the same alphabetical fake-tree construction rule).
- Two custom controls: `custom_control_alpha`, `custom_control_beta`.
- Non-default `selectable`/`snappable`/`group_color` on `UserCustomGroup` itself
  (`False`/`False`/`[11,22,33,255]`), non-default `group_color` on `Alpha`
  (`[44,55,66,255]`), non-default `visible`/`selectable` on `Beta` (`False`/`False`).

**Precise "zero mutation-log entries" proof (governing prompt Section 3, stronger than a hash-
equality check):** a dedicated check (`custom_subtree.zero_mutation_log_entries`) builds one
throwaway world from the SAME declarative spec to read out the exact real handles of
`UserCustomGroup`/`Alpha`/`Beta` and the exact control names `custom_control_alpha`/
`custom_control_beta`, then scans the ACTUAL baseline run's mutation log directly against those
handles/names — **zero matching entries**, confirmed by direct execution, not inferred from an
unrelated hash comparison (which could in principle mask a set-then-reset toggle).

**Negative controls** (both categories required by the correction prompt, honestly disclosed as
before): **NC-E-a** (disclosed ineffective — wrapping `SetVisible` with an accidental toggle;
ineffective because real production never calls `SetVisible` on `UserCustomGroup` at all, so the
wrapper is never invoked) superseded by **NC-E-b** (effective — injecting one accidental
`SetVisible(False)` call directly into the live world's `UserCustomGroup` at construction time,
detected via mutation-stream/final-tree divergence).

Group handle/child-order/metadata preservation was already covered by the pre-existing
`final_tree` hash-equality check (`D4_untouched_custom_group_preservation.final_tree`, PASS) —
now additionally reinforced by the precise zero-mutation-log-entries check above.

## 46. Fresh regression totals (this Part, real Python 2.7.5 / Windows)

| Suite | Result | Exit code |
|---|---|---|
| Decision layer (`test_b2c_c_plan_layer_equivalence.py`, now 16 named fixtures incl. D6) | **55/55 PASS** | 0 |
| Execution layer (`test_b2c_c_execution_layer_equivalence.py`) | **125/125 PASS** | 0 |
| Broker-mediated sanity (`test_b2c_c_broker_mediated_authority_sanity.py`) | **20/20 PASS** | 0 |
| Semantic regression (`test_b2c_correction6_semantic_regression.py`) | **14/14 PASS** | 0 |
| Fake-DME `AddChild` regression (`test_b2c_c_fake_dme_addchild_regression.py`) | **11/11 PASS** | 0 |
| New Tail real-canonical-authority closure (`test_b2c_c_tail_real_canonical_authority.py`) | **15/15 PASS** | 0 |
| Exit-status hardening self-test (`test_b2c_c_exit_status_self_test.py`) | **4/4 PASS** | 0 |

Canonical structure hash unchanged: `3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2`.
W3 remains `UNKNOWN`. No SFM run at any point. Frozen production Normalizer (SHA-256
`6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e`) and canonical Master (SHA-256
`ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`) re-verified unchanged.

## 47. Exit-status hardening (governing prompt Section 4)

All four RESULTS-accumulating B2C-C qualification scripts now end with:
```python
if not all(condition for _, condition in RESULTS):
    sys.exit(1)
```
`test_b2c_c_plan_layer_equivalence.py`, `test_b2c_c_execution_layer_equivalence.py`,
`test_b2c_c_broker_mediated_authority_sanity.py`, `test_b2c_c_fake_dme_addchild_regression.py`
(the two new files added this Part, `test_b2c_c_tail_real_canonical_authority.py` and
`test_b2c_c_exit_status_self_test.py`, carry the same guard from their first commit). Python 2.7
compatibility preserved (no syntax beyond what every other file already uses).

`test_b2c_c_exit_status_self_test.py` proves the guard works in BOTH directions, as real
subprocesses under the real Python 2.7.5 interpreter: a synthetic script with every check passing
exits 0; the SAME script with one check deliberately forced to fail exits non-zero; and the REAL,
already-hardened `test_b2c_c_fake_dme_addchild_regression.py`, run as a subprocess in its current
genuinely-passing state, exits 0. **4/4 PASS.**

## 48. Complete per-fixture evidence (governing prompt Section 5)

`R3_B2C_C_execution_layer_ledger.json` and `R3_B2C_C_plan_layer_ledger.json` now preserve, for
every one of the 16 named fixtures (all of D1–D6, plus the original 10 core fixtures) — NOT
replaced with only a `determinism_confirmed: true` boolean:

- a deterministic `fixture_spec_hash` (the declarative spec's own identity, independent of any
  run's output);
- `baseline_decision_plan_hash_repeat1`/`_repeat2`, `migrated_decision_plan_hash_repeat1`/`_repeat2`
  (execution-layer ledger) and `baseline_decision_hash_repeat1`/`_repeat2`,
  `migrated_decision_hash_repeat1`/`_repeat2` (plan-layer ledger);
- `baseline_native_mutation_stream_hash_repeat1`/`_repeat2`,
  `migrated_native_mutation_stream_hash_repeat1`/`_repeat2`;
- `baseline_final_tree_hash_repeat1`/`_repeat2`, `migrated_final_tree_hash_repeat1`/`_repeat2`;
- `mutation_count`, `group_count`, `control_count` (D-series), `composer_result`, `initial_post_hash`;
- `broker_mediated_sanity` flag (true only for `D5_flex_first_ordering`, per Section 49);
- `verdict` (PASS/FAIL/INCONCLUSIVE).

All 12 repeat-1/repeat-2 SHA fields the correction prompt lists are present and populated for every
fixture; back-compat unsuffixed aliases (repeat-1 values) are also kept so no existing tooling
referencing the older field names breaks.

## 49. Broker-to-execution composition proof (governing prompt Section 6)

Added to `test_b2c_c_broker_mediated_authority_sanity.py` (now **20/20 PASS**, up from 17/17), a
narrow D5 closure that does NOT re-qualify B2C-B's own lease/generation logic (already qualified,
Corrections 2–6):

1. Acquired D5's authority through the REAL broker (`Broker.acquire_or_reuse_views` →
   `Broker.lease_view`) — the SAME `flex_view` Part 3's flex-first broker checks already
   established.
2. Canonical-hashed `flex_view.payload`.
3. Canonical-hashed the direct-provider Correction6 adapter projection (`authority_pair.
   compute_migrated_master`) the ordinary D5 execution harness uses.
4. **Required exact equality — confirmed** (`broker_payload_equals_direct_provider_projection`,
   PASS): the broker-returned payload IS, byte-for-byte, the exact payload whose downstream
   behavior B2C-C already qualified.
5. Ran D5's migrated execution TWICE through the real `production_generic_composer` — once with
   the direct-provider projection, once with `flex_view.payload` directly as `master` — and
   required identical native-mutation-stream and final-tree hashes. **Both confirmed**
   (`broker_payload_execution_stream_matches`, `broker_payload_execution_tree_matches`, PASS).

## 50. What remains uncovered (honest accounting, re-updated)

1. Live target/scope enumeration — still deferred to a future live-runtime gate (Section 39/11,
   unchanged; re-confirmed this Part via a fresh grep of the eligibility-gate family: zero `master`
   references in all 7 dependencies of `_gate_is_alh`, 3 in `_gate_is_alh` itself, matching Part 2's
   original finding exactly, confirming the frozen file is unchanged).
2. The native `ifm.dll` rebuild callback is still never emulated (by design).
3. No new fake-DME contract gap was found while correcting D4/D6; the two ineffective negative-
   control attempts on the corrected fixtures (D6 needed none; D4's NC-E-a) were, once again, found
   to be inherent correct properties of the fixtures' own intended behavior, not gaps.

No other named gap from either the original Final Expansion Fixtures prompt or this targeted audit
correction prompt remains open.

## 51. Repo state / scope discipline (Part 4)

No SFM run. No production/canonical-Master file modified. No qualified Correction6 authority
semantics modified. No B2C-D or Character Preset work begun. No staging/commit/push performed
before local PASS was reached (per the governing prompt's own ordering). Existing 10 core fixtures,
D1/D3/D5, the masked-mutual-failure fix, the fake-DME `AddChild` fix, and the dependency-cut/
live-enumeration deferral were re-run as regression checks (Section 46) and NOT redesigned.

## 52. Final verdict (supersedes Section 42)

Both named gaps from the independent audit are closed:

- **Fixture C (Tail)**: D2's false claim retracted and renamed; the real canonical Master's Tail
  authority/path proven directly (frozen parser vs Correction6 adapter, 15/15 PASS); a corrected,
  observable relocation fixture (D6) built and qualified with an effective negative control.
- **Fixture E (custom-subtree preservation)**: root cause of the original design's reorder-touch
  found and explained; a corrected fixture (redesigned D4) genuinely reaches the reorder function's
  own early exit, proven by an exact handle/name-based zero-mutation-log-entries check, not just a
  hash comparison; non-trivial per the correction prompt's own requirements; effective negative
  control present (with one disclosed-ineffective first attempt, honestly documented).

Plus: harness exit status hardened and self-test-proven in both directions (Section 47); complete
per-fixture evidence (all 12 repeat-1/repeat-2 SHAs, not just a boolean) for all 16 named fixtures
(Section 48); an explicit broker-to-execution composition proof for D5 (Section 49); all previously
qualified evidence re-run as regression, unchanged (Section 46); semantic regression and canonical
hash unchanged, W3 still `UNKNOWN`.

**`B2C-C DOWNSTREAM MUTATION EQUIVALENCE PASS — AUTHORIZE B2C-D`**

This is a LOCAL result, per this project's own governance discipline (Part 2/3's own verdicts made
the same distinction) — it reflects that the two independently-identified gaps are now closed with
the SAME evidentiary rigor as the rest of B2C-C, not a claim that a further independent audit is
unnecessary or has already occurred. Do NOT self-authorize production promotion. Do NOT begin
B2C-D work in this turn.
