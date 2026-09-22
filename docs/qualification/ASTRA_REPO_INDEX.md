# Astra Repository Index — Navigation Map, Not a Claims Document

**Purpose:** let Astra find the right file/symbol/report fast, without reconstructing repository
history from scratch. This document asserts nothing about correctness on its own — see
`ASTRA_HOLISTIC_REVIEW_BRIEF.md` for the controlling review assignment, and Section G below for
which source wins when this index and prose evidence disagree.

Built by walking the actual repository at HEAD (`git ls-tree -r`, path/symbol greps, and reading
report headers/content) — not derived from prompt text or memory. Every path and symbol below was
checked against the live tree; see `ASTRA_HOLISTIC_REVIEW_PACKAGE_VALIDATION` note at the end of
this file for exactly what was verified before commit.

---

## A. Review target identity

| Item | Value |
|---|---|
| Repository | `chadchan3d/sfm-animation-groups-master` |
| Branch | `master` |
| Exact review HEAD | `fe22895ee80a73dab466293cedb741529902e66c` |
| B2C-B checkpoint (qualified authority, Correction6) | `514a100a380e33b6b6281afdc489921fd68728e1` |
| B2C-C correction (closes 2 independently-found fixture gaps) | `3b5aaa955bafa822da27603514271944b280654e` |
| Current documentation checkpoint (this package's own base) | `fe22895ee80a73dab466293cedb741529902e66c` |
| Frozen production Normalizer SHA-256 | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` |
| Canonical Master SHA-256 | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |

All four commit SHAs above are in a single ancestor chain: `514a100` → ... → `3b5aaa9` → ...
→ `fe22895` (HEAD).

---

## B. Fast reading order

| # | Path | Answers | Priority | Current/Historical |
|---|---|---|---|---|
| 1 | `docs/qualification/ASTRA_REPO_INDEX.md` (this file) | Where is everything? | MUST | Current |
| 2 | `docs/qualification/SFM_SIDECAR_POSTC3_CLAIMS_LEDGER.md` | What has been proven, by what evidence, with what limits, across the whole arc (Addenda 1–4)? | MUST | Current (living document) |
| 3 | `tests/sidecar/qualification/R3_B2C_C_Independent_Reaudit_3b5aaa9_Report.md` | What did the independent auditor conclude about B2C-C, and why is it closed? | MUST | Current |
| 4 | `tests/sidecar/qualification/R3_B2C_C_Downstream_Mutation_Equivalence_Report.md` | Full B2C-C decision/execution equivalence evidence, including the two corrected fixture gaps (Parts 1–4) | MUST | Current |
| 5 | `tests/sidecar/qualification/R3_B1_Lifecycle_Broker_Rebuild_Architecture_ASTRA_CORRECTED.md` | What is the broker/lifecycle/rebuild architecture and why was it designed this way? | HIGH | Current (design doc; broker/cohort/view-cache implementation now exists in `candidate_b2c_correction6/`, evolved somewhat from this design but built on it — treat implementation as source of truth per Section G) |
| 6 | `tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/__init__.py` | What does the authority package itself claim to be, and is it wired into production yet? | HIGH | Current (it self-describes as "NOT wired into either production consumer yet") |
| 7 | `docs/qualification/CPM_ASTRA_AUTHORITY_CONSUMER_DOSSIER.md` | What does the second consumer (Character Preset Manager) actually need from shared authority? | HIGH | Current (external dossier, unmodified except a short header) |
| 8 | `tests/sidecar/qualification/test_b2c_c_broker_mediated_authority_sanity.py` | Does the real broker path (not a shortcut) actually feed the qualified downstream behavior? | HIGH | Current |
| 9 | `docs/qualification/SFM_SIDECAR_POSTC3_ARCHITECTURE_AND_VERIFICATION.md` | What is `tools/sfm_master_sidecar/`'s module layout and production/qualification-only boundary? | OPTIONAL | Historical for its "qualification-only code" section (pre-dates Correction6's broker architecture, pinned to an earlier HEAD); still accurate for the `tools/sfm_master_sidecar/*.py` production-file descriptions, which are unmodified |
| 10 | `docs/qualification/R3_B2C_D_ASTRA_HANDOFF.md` | **Historical/supporting planning context written before Astra's remit was broadened; not the controlling review brief.** | OPTIONAL | Historical/supporting context only |

---

## C. Implementation responsibility map

All paths under `tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/` unless noted. This package is the **final, most-qualified copy** of the shared authority implementation; it is not yet imported by any production consumer file outside the qualification tree (its own `__init__.py` says so explicitly).

| Architectural question | Current implementation path(s) | Key symbol/function | Current evidence/report |
|---|---|---|---|
| Authored Master authority (TXT parse) | `tools/sfm_master_core.py` | `parse_master_bytes(data, source_name)` L628; `parse_master_file(path)` L745; `tokenize`/`_parse_tokens` L187/329; `ascii_fold(literal)` L81 | `test_b2c_correction6_semantic_regression.py` (frozen-parser-vs-adapter full-corpus hash) |
| Sidecar compiler/build | `tools/sfm_master_sidecar/compiler.py` | `parse_and_compile(snapshot, official_policy=False)` L91 (single production path); `capture_source_snapshot` L70; `verify_semantic_parity` L142 | `tests/sidecar/test_compiler.py`, `test_official_master_full_compile.py` |
| Sidecar validator | `tools/sfm_master_sidecar/compiler.py` | `self_validate_from_bytes(outcome)` L211, `self_validate_from_path(outcome, artifact_path)` L224 — round-trips the just-written blob through the reader and diffs; no separate validator module exists | same as above; `tools/validate_master.py` is a **separate**, source-TXT-only diagnostic (`validate(path)` L51), not a sidecar-artifact validator |
| Bounded provider | `tests/sidecar/qualification/candidate_packed_provider_r3a2b.py` | `class BoundedProvider` L197; `open_path(cls, path, expected_source_sha256, ...)` L238 (verified: matches signature exactly); `close()` L249 | Loaded by `sidecar_contract.ensure_loaded()` at `candidate_b2c_correction6/sfm_master_authority_productionized/sidecar_contract.py:37-38` — confirmed the authority package does not own its own provider, it loads this by exact path + SHA-256 |
| Source/artifact generation identity | `tools/sfm_master_sidecar/writer.py` L318 (`source_sha256=bytes.fromhex(result.source_sha256)`, embeds it at compile time); `tools/sfm_master_sidecar/reader.py` `open_generation_bytes/_path(data, expected_source_sha256)` L717/726 (verifies embedded SHA at read time); `descriptors.py` `SemanticGeneration`/`ArtifactIdentity` L14/42 (the B1 "four-identity separation") | — | `R3_B1_Lifecycle_Broker_Rebuild_Architecture_ASTRA_CORRECTED.md` (design rationale); `test_b2c_correction6_archive_reproducibility.py` |
| Resource estimator/preflight | `resource_estimator.py` | `parse_resource_shape()` L293 (reads only the fixed header + section directory, never decodes payload); `estimate_retained()` L502; `estimate_transient()` L592; `evaluate_cumulative_admission()` L678 | `test_b2c_correction6_offset_independent_preflight_memory.py`, `test_b2c_correction6_preread_floor.py` |
| Broker | `broker.py` | `class Broker` L33; `acquire_or_reuse_views(...)` L437 (the real top-level entry `normalizer_compat_adapter`/B2C-C tests call); `acquire_generation` L102; `lease_view` L375; `release_view_lease` L386; `provider_counters` L222 | `test_b2c_c_broker_mediated_authority_sanity.py` (17→20/20 PASS) |
| Cohort/view acquisition | `cohort.py` `class Cohort` L29 (one H0 observation, at most one open packed provider, deterministic close); `selection.py` `select_sidecar_candidate()` L80 (local pointer → shipped artifact → `SidecarMissing`/`RebuildRequired`, no TXT fallback anywhere) | `_open_provider_once` (cohort.py) ; `_find_and_open_matching_artifact`/`_try_local_candidate` (selection.py) | `test_b2c_correction6_durable_release_failure_cleanup.py` |
| Lease ownership/release | `views.py` | `class ViewLease` L99 (`is_released` L119); `class DetachedView` L126 (`acquire_lease`/`release_lease` L161/166, `has_live_leases`/`live_lease_count` L176/179); `broker.py` `outstanding_lease_count`/`register_unreleased_lease`/`retry_unreleased_leases` L389-435 | `test_b2c_correction4_durable_release_failure_cleanup.py`, `test_b2c_correction5_durable_release_failure_cleanup.py`, `test_b2c_correction6_durable_release_failure_cleanup.py` |
| View cache | `view_cache.py` | `class ViewCache` L14, keyed by generation+projection contract+coverage+consumer kind (never reused on SHA match alone); `get`/`admit`/`admit_batch` L31/39/92; `_evict_one` L166; `invalidate_generation` L275 | `test_b2c_b_freshness_and_cache.py` |
| Memory accounting | `memory_accounting.py` | `class AggregateLedger` L33 (one shared ledger, never per-tool quotas); `charge`/`release` L57/63; `would_exceed_retained_gate`/`would_exceed_transient_gate` L95/98 | `test_b2c_correction2_test2_memory_methodology.py`, `test_b2c_correction3_retained_plus_incoming_transient.py`, `test_b2c_correction5_preread_aggregate_transient.py` |
| Selection/projection logic | `normalizer_compat_adapter.py` `build_targeted_master_compatible_projection(wanted_folds)` L181 (reshapes a broker acquisition into the exact dict `parse_targeted_master()` returns); `projections.py` `build_normalizer_like_projection` L21 / `build_character_preset_like_projection` L59 (explicitly "qualification-fixture-only... NOT wired to any production consumer") | — | `test_b2c_c_plan_layer_equivalence.py` (55/55) |
| External rebuild utility/publication | `tools/sfm_master_sidecar/publisher.py` `publish()` L197, `PublisherLock` L141; `mutex_publisher.py` (`WindowsNamedMutex`-serialized variant) `publish()` L303, `recover_from_backup()` L249 | — | `tests/sidecar/test_publisher.py`, `test_publisher_concurrency.py`, `R3_B2E1_AbandonedMutex_Qualification_Report.md` (historical, closed) |
| Pointer/backup recovery | `pointer.py` `load_pointer()` L57 (read-only, bounded parsing — explicitly does not write/replace a pointer); `derive_artifact_path()` L149; `_reject_unsafe_relative_path` L124 | write-side recovery lives in `tools/sfm_master_sidecar/mutex_publisher.py` `recover_from_backup()` L249, not in the authority package | — |
| Normalizer authority compatibility adapter | `normalizer_compat_adapter.py` | `build_targeted_master_compatible_projection(wanted_folds)` L181; `AdapterCorrupt` exception L125 | `test_b2c_c_plan_layer_equivalence.py`, `test_b2c_c_execution_layer_equivalence.py` |
| Normalizer production/parser baseline | External file (real path, verified SHA-256-pinned every test run): `E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py`, extracted verbatim by exact line range into `tests/sidecar/qualification/candidate_b2c_c/production_plan_layer.py` (decision layer, `PLAN_LAYER_RANGES`) and `production_execution_layer.py` (execution layer, `EXECUTION_LAYER_RANGES`) | `classify_production`, `preflight_reconciliation_plan_pure`, `derive_generic_uniformity_plan`, `production_generic_composer` (frozen lines 6975-7924) | `candidate_b2c_c_normalizer/README_SCOPE_DECISION.md` explains why there is no "candidate Normalizer" source file for B2C-C (unlike B2C-B rounds 2-6, which each held a full swapped-seam copy under `candidate_b2c_correctionN_normalizer/`) |
| B2C-C decision comparison | `tests/sidecar/qualification/test_b2c_c_plan_layer_equivalence.py` | `compare_scenario`, `run_pipeline` | 55/55 PASS, `R3_B2C_C_plan_layer_ledger.json` |
| B2C-C execution comparison/fake-DME oracle | `tests/sidecar/qualification/test_b2c_c_execution_layer_equivalence.py`; fake object model in `candidate_b2c_c/fake_dme.py` (`FakeDmeControlGroup`, `FakeDmeControl`, `FakeDmeRig`, `MutationLog`) | `compare_scenario`, `run_execution` | 125/125 PASS, `R3_B2C_C_execution_layer_ledger.json`; `test_b2c_c_fake_dme_addchild_regression.py` (11/11, proves the fake model's `AddChild` exclusivity contract) |
| Broker → Normalizer execution composition evidence | `tests/sidecar/qualification/test_b2c_c_broker_mediated_authority_sanity.py` | `broker_payload_equals_direct_provider_projection`, `broker_payload_execution_stream_matches`, `broker_payload_execution_tree_matches` checks | 20/20 PASS |
| Any currently intended production integration seam | **None wired yet.** The authority package's own `__init__.py` states it is "NOT wired into either production consumer yet." No file under `tools/`, the real Normalizer, or a CPM source imports `sfm_master_authority_productionized`. | — | This is itself a fact for Astra's review, not a gap in this index |

---

## D. Evidence map by claim

| Claim / invariant | Best evidence to inspect | Historical background if challenged |
|---|---|---|
| Exact Master semantic parity (frozen parser == qualified adapter, full corpus) | `test_b2c_correction6_semantic_regression.py` (`fullcorpus.0`/`.1`/`.2` checks; canonical hash `3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2`) | `test_b2c_correction3/4/5_semantic_regression.py` (superseded, same claim at earlier authority states) |
| No silent TXT fallback | `test_b2c_correction6_semantic_regression.py` (`mutation.0`, scans the candidate Normalizer for native/DME mutation symbols); `test_b2c_c_broker_mediated_authority_sanity.py` (`no_txt_fallback`, `flex_no_txt_fallback`); `selection.py` `select_sidecar_candidate()` L80 itself (local pointer → shipped artifact → error, no TXT branch) | `test_b2c_b_mutation_absence_proof.py` (original static + dynamic code-object proof, B2C-B era) |
| Generation coherence (source == embedded == command-pinned) | `test_b2c_c_broker_mediated_authority_sanity.py` (`source_generation_matches`, `sidecar_embedded_generation_matches`, `command_generation_agrees`, and the `flex_*` D5 variants) | `R3_B1_Lifecycle_Broker_Rebuild_Architecture_ASTRA_CORRECTED.md` (design rationale for the 4-identity separation) |
| Stale-generation rejection | `errors.py` `SourceGenerationMismatch` L29, `AuthorityChangedDuringAcquisition` L49; `broker.py` `acquire_or_reuse_views` | `test_b2c_correction3_expected_generation_forwarding_no_prepublish_mismatch.py` |
| Pre-full-read resource bound | `resource_estimator.py` `parse_resource_shape()`/`evaluate_cumulative_admission()` | `test_b2c_correction6_offset_independent_preflight_memory.py`, `test_b2c_correction6_preread_floor.py` (final); correction2-5 equivalents superseded |
| Retained/transient memory accounting | `memory_accounting.py` `class AggregateLedger` | `test_b2c_correction5_preread_aggregate_transient.py` (final); correction2/3 equivalents superseded |
| Custom Master rebuild | `tests/sidecar/test_custom_master_gate1.py`; `tools/sfm_master_sidecar/publisher.py`/`mutex_publisher.py` | `docs/qualification/SFM_MASTER_SIDECAR_GATE_C0_PROMOTION_PREREQUISITES_AUDIT.md` (historical, pre-Correction6) |
| Archive reproducibility | `test_b2c_correction6_archive_reproducibility.py` (final); `R3_B2C_C_Independent_Reaudit_3b5aaa9_Report.md` Section 2 (independently reproduced synthetic Master/sidecar SHA-256 for B2C-C's own fixture) | correction3/4/5 equivalents superseded |
| Lease cleanup ownership | `views.py` `ViewLease`/`DetachedView`; `broker.py` `outstanding_lease_count`/`register_unreleased_lease`/`retry_unreleased_leases` L389-435 | `test_b2c_correction6_durable_release_failure_cleanup.py` (final); correction4/5 equivalents superseded |
| Provider closure before mutation | `test_b2c_c_broker_mediated_authority_sanity.py` (`provider_open_count_zero_at_boundary`, `flex_provider_open_count_zero_at_boundary`, `lease_release_clean`, `flex_lease_release_clean`) | — |
| Downstream Normalizer decision equivalence | `test_b2c_c_plan_layer_equivalence.py` (55/55); `R3_B2C_C_plan_layer_ledger.json` | `R3_B2C_C_Downstream_Mutation_Equivalence_Report.md` Part 1 |
| Native mutation-stream equivalence | `test_b2c_c_execution_layer_equivalence.py` (125/125); `R3_B2C_C_execution_layer_ledger.json` | Report Parts 2-4 |
| Final-tree equivalence | Same as above (`.final_tree` checks per fixture) | Report Parts 2-4 |
| Active-rig toe behavior | Fixture `D1_active_rig_toe_relocation` in `candidate_b2c_c/scenarios.py`; execution-layer ledger entry | Report Section 32/44 (mechanism: `model_leaf_specs` in the frozen `derive_generic_uniformity_plan`) |
| Flex-first ordering | Fixture `D5_flex_first_ordering`; `test_b2c_c_broker_mediated_authority_sanity.py`'s flex-first broker closure (Section 49 of the report) | Report Sections 33/49 (two disclosed design iterations before reaching a genuinely-observable ordering effect) |
| Tail generic relocation | Fixture `D6_tail_relocation`; `test_b2c_c_tail_real_canonical_authority.py` (15/15, proves the REAL canonical Master's actual root-level `Tail` group against the frozen parser and adapter) | Report Sections 43-44 (D2's original false Tail claim, retracted and renamed to `D2_rigbody_family_counterpart_refinement`) |
| Repeated-control preservation | Fixture `D3_repeated_control_preservation` | Report Section 35 (NC-D-a disclosed ineffective, superseded by NC-D-b) |
| Custom subtree preservation | Fixture `D4_untouched_custom_group_preservation` (`UserCustomGroup/{Alpha,Beta}`); `custom_subtree.zero_mutation_log_entries` check | Report Sections 45 (root-cause of the original design's failure and the fix) |
| Broker-to-execution composition | `test_b2c_c_broker_mediated_authority_sanity.py` Section 6 closure (`broker_payload_equals_direct_provider_projection`, `broker_payload_execution_stream_matches`, `broker_payload_execution_tree_matches`) | Report Section 49 |
| Known deferred live/runtime concerns | See Section F below | `SFM_SIDECAR_POSTC3_CLAIMS_LEDGER.md` Addendum 3/4 |

---

## E. Superseded / historical material — do not read on first pass

| Category | Paths | Read only if challenging |
|---|---|---|
| Superseded B2C-B correction rounds | `tests/sidecar/qualification/candidate_b2c/`, `candidate_b2c_correction/` through `candidate_b2c_correction5/` (and their `_normalizer` siblings); `R3_B2C_B_Astra_Correction_Gate_Report.md`, `_Astra_Second_Correction_Gate_Report.md`, `_Final_Targeted_Infrastructure_Correction_Report.md`, `_Independent_Audit_Targeted_Correction_Report.md`, `_Normalizer_ReadOnly_Migration_Report.md`, `_ParseDeferred_PreRead_Floor_Correction_Report.md`, `_PreRead_Aggregate_Transient_Correction_Report.md`; `test_b2c_correction_*.py` through `test_b2c_correction5_*.py` | `<the specific Correction6 mechanism it was superseded by, e.g. "was the resource-preflight memory accounting sound before the aggregate-transient fix?">` |
| Superseded B2C-C PARTIAL rounds | `R3_GitHub_Checkpoint_B2C_C_Report.md` (pre-audit checkpoint, superseded by the Independent Reaudit report); the original (retracted) D2 "Tail relocation" design and original `CustomUserGroup/Nested` D4 design — both are documented as corrections, not separate files, inside `R3_B2C_C_Downstream_Mutation_Equivalence_Report.md` Parts 3-4 | `<whether the correction record for D2/D4 is honest and complete>` |
| Old temporary fixture variants / candidate scaffolding | `candidate_offline_qualification.py`, `candidate_packed_provider.py` (pre-r3a2b), `candidate_packed_validator.py` (pre-r3a2b), `candidate_b2f1f_f5/` | `<whether an earlier resource-preflight or packed-format design had a flaw the final r3a2b version fixed>` |
| Raw workload captures / benchmark scripts | `tests/sidecar/qualification/b2f1_*.py`, `b2f1e_*.py`, `b2f1f_*.py`, `b2f_*.py`, `B2F1*_ExternalSampler_Launch*.py`, `CGN_R3_B2F1*.py`, and their `*_result.json`/`*_ground_truth.json`/`*_qualification_matrix.json` outputs; `R3_B2F1A` through `R3_B2F1F_*` reports; `R3_B2F_Implementation_Report.md`; `R3_B2F1_ExternalSamplerBoundary_Report.md` | `<whether the resource-preflight memory model was empirically derived soundly>` |
| Old stage/gate reports (pre-B2C-B sidecar design) | `docs/qualification/SFM_MASTER_SIDECAR_PHASE_A_*` through `PHASE_B2E_*`, `B1_1_ASTRA_COMPLIANCE_HANDOFF`, `B1_2_COMPLIANCE_CLOSURE`, `B1_ASTRA_REVIEW_HANDOFF`, `GATE1_*`, `GATE2*_*`, `GATE_A1/A2/B/C0/C1/C2_*`, `MINIMUM_C3_*`, `PY27_PATH_INPUT_FIX`, `ROUND3_FOUNDATION_SIMPLIFICATION_REPAIR` (all pinned to an earlier HEAD, `1028adcd...`, pre-dating B2C-B/C entirely) | `<whether the underlying compiler/writer/reader binary format itself — not the authority package built on top of it — was soundly designed>` |
| Old `session_owner.py`-era architecture | `tests/sidecar/qualification/session_owner.py`, `command_boundary.py`, `resource_budgets.py`, `bounded_provider.py` (S1, pre-r3a2b), `shared_txt_session.py`; `SFM_SIDECAR_POSTC3_ARCHITECTURE_AND_VERIFICATION.md`'s "Qualification-only code" table specifically | `<whether the abandoned owner/lease/view design contained an idea the current broker architecture should have kept>` |
| Old mutex-abandonment diagnostic | `R3_B2E1_AbandonedMutex_Qualification_Report.md`, `b2e1_*.py` | `<whether Windows named-mutex publication lock recovery is actually sound>` |
| Superseded/local-only git checkpoint reports | **Not present in the git HEAD tree.** Several prior-round checkpoint report files (e.g. `R3_GitHub_Checkpoint_B2C_C_Report.md`, `R3_GitHub_Checkpoint_Correction3_Report.md` through `_Correction6_Report.md`, `_SecondCorrection_Report.md`, `_PostAstraCorrection_Report.md`, `_PostB2CB_Report.md`) exist only in a local working directory and were never staged/committed — verified via `git cat-file -e HEAD:<path>` (all return "not in HEAD tree"). A reviewer pulling only the pushed repository will not see them. This is a pre-existing repo-hygiene gap noted for completeness, not a claim requiring action from this review. | `<needing the exact staging/push mechanics of a specific historical checkpoint, in which case ask for the local file directly>` |

Nothing above has been deleted or rewritten — this section only tells Astra where NOT to start.

---

## F. Known deferred / unresolved boundaries

Stated factually; none of these are assumed to require another synthetic test phase.

- Live SFM target/scope enumeration (`snapshot_work`'s real scene/shot/project walk) — never exercised offline; the dependency cut proves it is authority-independent except `_gate_is_alh`, which IS qualified offline.
- Real host timing (actual SFM process behavior under load) — not measured in this qualification arc.
- Native `ifm.dll` rebuild behavior — never emulated; the same captured post-rebuild snapshot is fed to both comparison sides by design, and the call site is proven temporally authority-independent by direct source reading.
- Final authorization → native-use race (the gap between a broker granting a lease and the Normalizer actually using it natively) — not yet exercised against real SFM timing.
- External generation changes during a long-lived consumer's lifetime — an open question for BOTH intended consumers; CPM's dossier (Section 6/12) states this explicitly as unresolved for CPM's process-global resident provider today.
- W3 (72-shot real-workload capture) remains `UNKNOWN` — its own real capture attempt failed (`ERROR=CaptureError('Wrong project: expected 72 shots, found 11.')`); never manufactured or force-substituted.
- Production promotion is not yet authorized — nothing in this arc constitutes or implies it.
- CPM final shared-authority integration is pending — CPM currently uses its own `SidecarSemanticProvider`/`get_semantic_provider` path (`SFM_CSP_G18AN_SaveNewCopy.py`), not the `sfm_master_authority_productionized` package this repo qualified for the Normalizer.

---

## G. Source-of-truth hierarchy

When prose and current source disagree, resolve in this order:

1. **Current implementation at review HEAD** (`fe22895ee80a73dab466293cedb741529902e66c`) — the actual `.py` files under `tools/` and `tests/sidecar/qualification/candidate_b2c_correction6/`, and the frozen production Normalizer/canonical Master (external, SHA-256-pinned).
2. **Current machine-readable evidence/tests** — `R3_B2C_C_execution_layer_ledger.json`, `R3_B2C_C_plan_layer_ledger.json`, and the exit-status-hardened test files themselves (real pass/fail, not narrative).
3. **Independent audit reports** — `R3_B2C_C_Independent_Reaudit_3b5aaa9_Report.md`.
4. **Claims/architecture summaries** — `SFM_SIDECAR_POSTC3_CLAIMS_LEDGER.md`, `R3_B2C_C_Downstream_Mutation_Equivalence_Report.md`, `R3_B1_Lifecycle_Broker_Rebuild_Architecture_ASTRA_CORRECTED.md`.
5. **Historical/superseded reports** — everything in Section E.

If current source contradicts any prose document (including this index), current source wins.

---

*Every path cited above was confirmed to exist at HEAD `fe22895ee80a73dab466293cedb741529902e66c` via `git ls-tree`/direct file reads; every symbol cited in Section C was confirmed via direct source grep/read (not copied from an earlier report) before this document was committed.*
