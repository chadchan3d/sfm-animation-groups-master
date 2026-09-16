# R3-B2C-B — Isolated Production Normalizer Read-Only Authority Migration Report

**Date:** 2026-09-16
**Authorization:** `SFM_CGN_R3_B2C_B_Normalizer_ReadOnly_Migration_ClaudeCode_Prompt_2026-09-16.md`

---

## 1. Frozen identities (Section 2)

Re-hashed immediately before any candidate file was created, independently confirmed on both interpreters where re-checked:

| Item | SHA-256 | Status |
|---|---|---|
| Production Normalizer (`Rebuild_Control_Groups_Normalizer.py`) | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` | matches pinned value; **unchanged throughout B2C-B** |
| Canonical Master (`sfm_defaultanimationgroups.txt`) | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | matches pinned value |
| Official sidecar (`official_sidecar_artifact.bin`) | `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` | matches pinned value |

## 2. Isolated candidate Normalizer path + SHA (Section 15.2)

`tests/sidecar/qualification/candidate_b2c_normalizer/Rebuild_Control_Groups_Normalizer_B2CB_candidate.py`
SHA-256: `aab65ebd3dbf33e79e9d6549eef82adf5cefa0bba85f15b2847c28ca65f3de4c`

Compiles cleanly under both Python 3.10 and real Python 2.7.5 (`py_compile`, syntax-only check — the file cannot be fully imported offline under either interpreter; see Section 4 below).

## 3. Exact diff against production Normalizer (Section 15.3)

Exactly **3 hunks**, 82 lines added, 3 lines removed. Full diff at `tests/sidecar/qualification/candidate_b2c_normalizer/b2cb_candidate.diff`.

1. **Lines 124→147** (after the file's own `try: long / except NameError: long = int` block): adds `sys.path` plumbing for the candidate authority package + `tools/`, and imports `runtime`/`normalizer_compat_adapter` from `sfm_master_authority`.
2. **Lines 1413→1436** (immediately before `parse_targeted_master`'s own definition, which is otherwise byte-identical and untouched): adds the new function `acquire_master_index_via_qualified_authority(master_path, wanted_folds, shipped_root, allow_local_candidates=False, local_pointer_path=None, generated_root=None, runtime_cap_bytes=None)`.
3. **Lines 13191→13210** (the single call site): replaces `parse_targeted_master(self.master_path, self.master_index_scope_folds, validate_conflicts=False)` with `acquire_master_index_via_qualified_authority(self.master_path, self.master_index_scope_folds, shipped_root=os.path.join(usermod_dir, "scripts", "sfm", "gate_r2_formal_deploy"))`.

No downstream logic, skip logic, target eligibility, group ordering, metadata handling, colors/selectability, mutation code, or Qt yield behavior touched. `parse_targeted_master` itself remains fully intact and callable (used throughout this report as the reference implementation for A/B comparison) — it is simply no longer reached by the production call site.

**Open item (not a B2C-B blocker, flagged for before any real-SFM authorization):** `shipped_root` at the call site is a **provisional** path (`usermod_dir/scripts/sfm/gate_r2_formal_deploy`) — no prior B2 stage has finalized where a real production shipped sidecar would be deployed, and this qualification directory's `official_sidecar_artifact.bin` doesn't even carry the `.sfmsidecar` extension the scanner requires. B2C-B is read-only/no-SFM, so this never needed to resolve correctly for a real run; it must be settled before B2C-R (real-SFM qualification).

## 4. Proof no mutation function executes (Section 15.5)

`test_b2c_b_mutation_absence_proof.py` — **6/6 PASS on both interpreters**. Three independent proofs:

1. **Static text scan** of the new function's exact source (lines 1439–1485) and every file in the candidate authority package for mutation-related symbols/call patterns (`SetUndoEnabled`, `WINFUNCTYPE`, `native_ptr`, `prepare_native_callback`, `dm.`, `.rebuild(`, `set_group_color`, `set_selectable`, `DmeTransformControl`, `CreateUndo`/`StartUndo`, etc.) — zero hits. (One initial false positive — a bare-word "rebuild" match in `pointer.py`'s prose about sidecar-artifact republication, an unrelated B2E concept — corrected to call-syntax matching.)
2. **Dynamic code-object inspection**: recursively walks `co_names`/`co_varnames` of the compiled function (and every nested code object) — the complete name set is `['_b2c_authority_runtime', '_b2c_normalizer_adapter', 'acquire_master_index_via_qualified_authority', 'acquire_or_reuse_views', 'allow_local_candidates', 'broker', 'build_targeted_master_compatible_projection', 'builder', 'detached', 'folded_key', 'frozenset', 'generated_root', 'get_broker', 'local_pointer_path', 'master_path', 'payload', 'request_specs', 'runtime_cap_bytes', 'shipped_root', 'wanted_folds']` — no mutation-related name is even nameable from this call path.
3. **Sentinel execution**: ran the function for real; the returned dict contains **zero** live `BoundedProvider` references anywhere in its structure (recursive walk), and `current_open_provider_count == 0` before the (simulated) mutation boundary.

The whole file cannot be `import`-ed/fully executed offline under either interpreter regardless (module scope does `import sfmApp`/`sfmClipEditor`/`vs`/`PySide`, real-SFM-only, and the file's last line unconditionally calls `StartRebuildControlGroups()`) — this is a pre-existing, structural property of the file, unrelated to and unaffected by the B2C-B patch. Consistent with this whole project's established methodology (verify_py27_equivalence.py, B2C-A), the new function is exercised via **verbatim extraction by exact line range** from the hash-identified candidate file, never retyped, never a full-file import.

## 5/6/7. Full parser-vs-migrated structure comparison, scope matrix, canonical hashes (Sections 5, 6, 15.6/15.7)

`test_b2c_b_readonly_migration.py`. Reference (`parse_targeted_master`) extracted verbatim from the **unchanged production file**; candidate (`acquire_master_index_via_qualified_authority`) extracted verbatim from the **B2C-B candidate file**. Both sides canonically serialized (JSON, sorted keys, list/occurrence order preserved) and SHA-256 hashed, per-component and combined.

**Important, real finding this turn**: `parse_targeted_master`'s tokenizer (`BufferedChars`/`stream_tokens`) treats `open(path, "rb")` output as Python-2 str-as-bytes throughout — indexing a bytes buffer under Python 3 yields an `int`, not a character, breaking `ch.isspace()`/comparisons. **The reference side genuinely cannot run under Python 3** without an unverified translation (the same risk B2C-A deliberately avoided for the same reason). So:
- Under **real Python 2.7.5**: full reference-vs-candidate cross-comparison, real hash equality.
- Under **Python 3.10**: candidate-only structural self-consistency (the reference is skipped, not force-translated).

### Results (real Python 2.7.5 — the authoritative cross-comparison)

| Scope-matrix case | Folds requested | Combined hash match | current_open_provider_count==0 |
|---|---:|:---:|:---:|
| 6A: full canonical Master (all folds) | 124,728 | N/A — correctly **refused** (see below) | ✅ |
| 6B: known exact literals | 5 | ✅ | ✅ |
| 6B: unknown literal | 1 | ✅ | ✅ |
| 6B: punctuation/whitespace (`"     =Body="`) | 1 | ✅ | ✅ |
| 6B: left/right | 2 | ✅ | ✅ |
| 6B: case variants (LEFT/Left/lEfT/left → 1 fold) | 1 | ✅ | ✅ |
| 6B: mixed known+unknown | 6 | ✅ | ✅ |
| 6C: W1 real single-shot/single-target (Fox) | 208 | ✅ | ✅ |
| 6C: W2 real six-target union | 1,354 | ✅ | ✅ |
| 6C: W2 per-target × 6 (real, distinct target/model shapes) | 178–436 each | ✅ (all 6) | ✅ |
| 6C: synthetic MasterUnknown-only scope | 5 | ✅ | ✅ |
| 6D: W3 (72-shot) | — | **not usable** (see below) | — |

**43/44 PASS.** The one non-pass is documented, not a defect: W3's own stored capture recorded `status: FAIL`, `error: "CaptureError('Wrong project: expected 72 shots, found 11.')"` — its capture run itself failed in an earlier session, so it contains no real workload data to compare against. Not force-substituted with synthetic data (the prompt explicitly says not to force anything to reach a historical hash).

**6A (full corpus)**: requesting all 124,728 folds at once (~95 MB estimated payload) legitimately exceeds the already-qualified 16 MiB retained-promotion gate. This is correct, intended B2B behavior — `acquire_master_index_via_qualified_authority` correctly propagates `errors.ViewAdmissionRefused` rather than silently truncating or corrupting data, and the provider is still closed (`current_open_provider_count == 0`) even on refusal. The **exact full-corpus structural-hash equality** itself was already established in B2C-A (`verify_py27_equivalence.py`, 15/15 PASS) against this same, hash-unchanged adapter code (bypassing the admission gate to isolate the builder's own correctness) — re-confirmed again this turn (Section 13) with the identical combined hash `3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2` on both sides.

**"Skipped/non-eligible targets" scope-matrix item**: not applicable at this authority-acquisition boundary. Per the B2C-A fork's finding, `collect_scope_master_wanted_folds()` and the master_index build both run *before* any GATE-phase eligibility classification — the wanted_folds set doesn't vary by eventual per-target eligibility, and the same already-built index is reused for eligible and skipped targets alike.

### Results (Python 3.10 — candidate-only structural self-consistency)

Same 12 scope-matrix cases run; **43/44 PASS** (same single documented W3 gap). Every case: structurally well-formed output (`mapping_count`/`destination_count` positive ints, `folded`/`group_sibling_order`/`group_metadata` correctly typed, `<ROOT>` sentinel present), `current_open_provider_count == 0`.

## 8. W1/W3 read-only comparison (Sections 6.D, 15.9)

- **W1** (real single-shot, single-target "Fox", 208 real facial-control folds): full cross-comparison, exact hash match (Python 2.7.5); structural self-consistency (Python 3.10).
- **W2** (real six-target scope, 1,354-fold union, plus all 6 per-target sub-scopes individually — genuinely distinct target/model shapes): full cross-comparison, exact hash match on all 7 sub-cases (Python 2.7.5).
- **W3** (72-shot, all-shots workload): **unusable** — its own stored capture is an error record (wrong project, 11 shots found instead of 72), not real workload data. No B2C-B defect; a pre-existing data-availability gap from an earlier session's capture run.

## 9. Provider lifecycle table (Section 7)

Hard gate — `current_open_provider_count == 0` after every single acquisition (success or refusal) — held in **every one of the ~24 distinct test cases** across all four new B2C-B test files, on both interpreters, without exception. Representative counters (W1 scope, real Python 2.7.5, from `test_b2c_b_performance_sanity.py`):

| Metric | First acquisition | Repeated (same generation) |
|---|---:|---:|
| `total_provider_opens` | 1 | 1 (delta 0 — cache hit) |
| `peak_open_provider_count` | 1 | 1 |
| `current_open_provider_count` (after) | 0 | 0 |
| Returned dict contains a live `BoundedProvider` anywhere | No (recursive-walk-verified) | No |

## 10. Repeated-acquisition/cache table (Section 8)

`test_b2c_b_freshness_and_cache.py` (Section 8 portion) — **16/16 PASS on both interpreters** (freshness + cache combined). Same broker instance, same generation, same wanted_folds requested twice:

| | Python 2.7.5 | Python 3.10 |
|---|---:|---:|
| First acquisition elapsed | 1.227 s | 0.539 s |
| Second (cache-hit) elapsed | 0.016 s | 0.004 s |
| `total_provider_opens` after 1st / 2nd | 1 / 1 (unchanged) | 1 / 1 (unchanged) |
| Returned structures semantically identical | ✅ | ✅ |
| Widened vocabulary → fresh cohort, provider opens again | ✅ (opens → 2) | ✅ (opens → 2) |

## 11. Generation/error classification matrix (Section 9)

| Scenario | Fixture | Expected classification | Result (both interpreters) |
|---|---|---|---|
| Unchanged Master / matching sidecar | real Master + `shipped_root_valid` | success | ✅ |
| Missing sidecar | `shipped_root_empty` | `SidecarMissing` | ✅ |
| Stale/mismatched Master | `install_a` fixture Master vs. `shipped_root_valid` | `SidecarMissing` | ✅ |
| Corrupt local candidate | `local_corrupt_test` pointer + generated root | passive recovery to shipped (unchanged, established B2A policy) | ✅ |
| Resource-refused sidecar | `runtime_cap_bytes=1024` | `ResourceAdmissionRefusal` | ✅ |
| Master changed before/between H0/H1 | — | not independently re-derived here | see note below |
| Unsupported sidecar | — | **no fixture available** | **open item**, not claimed as covered |
| No TXT fallback | compiled code-object `co_names` inspection | zero `parse_targeted_master`/`stream_tokens`/`BufferedChars` references | ✅ |

**Design note, stated explicitly rather than silently assumed**: `acquire_master_index_via_qualified_authority` is a completely transparent pass-through — its entire body is one call to `broker.acquire_or_reuse_views(...)` followed by returning `.payload`, with no exception handling or branching of its own around H0/H1 stability or generation matching. Those classifications are owned entirely by `broker.py`/`cohort.py`/`selection.py`, already exhaustively proven correct by the B2A-equivalent suite's `h0h1.1`–`h0h1.4` and the B2B-equivalent suite's `invariant.1`–`invariant.7` (re-run this turn, Section 13, unchanged 38/38 and 64/64). This file proves the narrower, B2C-B-specific claim: the wrapper does not swallow, alter, or reclassify any outcome — not a second, independent derivation of the underlying H0/H1 mechanism.

**"Unsupported sidecar"** has no distinct fixture in the current B2A/B2B fixture set (a `format_contract_version` mismatch was never separately fixture-built in any prior stage) — flagged here rather than silently assumed covered by the corrupt-sidecar fixture.

## 12. `groupFile` wrapper regression (Section 10)

`test_b2c_b_groupfile_regression.py` — **22/22 PASS (real Python 2.7.5, includes full ref-vs-candidate hash comparison) / 15/15 PASS (Python 3.10, candidate-only)**.

Tested on **two structurally distinct fixtures**:
1. **Real canonical Master** (42 real groups, 21 top-level siblings under the wrapper) — re-confirms B2C-A's finding.
2. **Synthetic fixture** (`fixtureA_1p0x`, 126 real groups including the wrapper → 125 real groups after stripping, 6 top-level siblings, 3+ levels of nesting, generic non-whitelisted `meta0`/`meta1` metadata keys, 21,024 occurrences, 96 destinations) — a genuinely different shape, proving the strip logic generalizes rather than being overfit to the real Master's specific topology. Full exact-hash match against `parse_targeted_master` on all 6 components + combined, under real Python 2.7.5.

Explicit checks in both cases: no phantom `groupFile` entry in `group_metadata`; `group_sibling_order["<ROOT>"]` never contains `"groupFile"`; `group_metadata` count equals real provider group count minus exactly one (the wrapper); no `full_path`/destination anywhere retains a `"groupFile/"` prefix.

## 13. Provider-handle leak regression (Section 11)

The candidate-only `broker.py` fix (in `_acquire_generation_once`, the **legacy identity-only** `acquire_generation` path — not on the call graph `acquire_master_index_via_qualified_authority` actually uses, which goes through `acquire_or_reuse_views`/`acquire_cohort`/`Cohort._open_provider_once` instead) is retained unchanged and re-verified via the B2A-equivalent suite's `h0h1.2`/`h0h1.2b`/`h0h1.3`/`h0h1.3b` tests (Section 13 re-run below): provider opens/closes balanced, `current_open_provider_count` zero, and the H0/H1-instability test doubles (`_FakeSelectionResult`, which deliberately omits a real `.provider` attribute) still work correctly via the `getattr(selection_result, "provider", None)` duck-typing guard — **38/38 PASS on both interpreters**, no behavior change in the frozen baseline (re-confirmed by direct diff, Section 17 below).

## 14. Python 2.7.5 and 3.10 suite totals (Section 15.15)

| Suite | Python 2.7.5 | Python 3.10 |
|---|---:|---:|
| `test_b2c_b_readonly_migration.py` (scope matrix) | 43/44 (1 documented W3 gap) | 43/44 (same, candidate-only) |
| `test_b2c_b_groupfile_regression.py` | 22/22 | 15/15 (candidate-only, fewer applicable checks) |
| `test_b2c_b_mutation_absence_proof.py` | 6/6 | 6/6 |
| `test_b2c_b_freshness_and_cache.py` | 16/16 | 16/16 |
| `test_b2c_a_b2a_equiv_offline.py` (re-run) | 38/38 | 38/38 |
| `test_b2c_a_b2b_equiv_offline.py` (re-run) | 64/64 | 64/64 |
| `test_b2c_a_normalizer_adapter_offline.py` (re-run) | 18/18 | 18/18 |
| `verify_py27_equivalence.py` (re-run) | 15/15 | N/A (documented Python-2-only) |
| **Total (excluding documented N/A and the one documented W3 gap)** | **222/224** | **200/201** |

No claim of interpreter parity is made beyond what each interpreter can actually run — the scope-matrix reference comparison and `verify_py27_equivalence.py` are real-Python-2.7.5-only by a genuine, documented technical constraint (the production tokenizer's bytes-as-str assumption), not a shortcut.

## 15. Performance/read-count measurements (Section 14)

W1's real 208-fold single-target scope, real Master + real official artifact:

| | Python 2.7.5 | Python 3.10 |
|---|---:|---:|
| Frozen `parse_targeted_master` | 2.785 s | not runnable (documented) |
| Candidate FIRST acquisition | 1.293 s (**0.46×** the frozen parser — faster, not slower) | 0.508 s |
| Candidate REPEATED (cache hit) | 0.019 s (**0.0068×** the frozen parser) | 0.004 s |
| `full_bounded_read_count` per generation | 1 (0 on cache hit) | 1 (0 on cache hit) |
| `peak_open_provider_count` | 1 | 1 |

The migrated candidate is faster than the frozen character-by-character tokenizer even on a cold first acquisition (reading pre-compiled binary directory/occurrence tables vs. re-tokenizing the whole text file), and a cache-hit on a repeated same-generation acquisition costs roughly 150× less than the first acquisition. No optimization was attempted beyond the already-qualified B2A/B2B/B2C-A architecture, per the prompt's instruction.

## 16. Frozen shared-authority identity table (Section 15.17)

Re-hashed at the start of B2C-B, before any candidate file existed:

| File | Frozen deploy SHA-256 | B2C-A/B2C-B candidate SHA-256 | Status |
|---|---|---|---|
| `__init__.py` | `3d313d04...5e5a533e` | *(identical)* | unchanged |
| `broker.py` | `d2e66251...56dd8b9` | `dd0d2f44...5104b5` | **modified** (provider-leak fix, isolated) |
| `cohort.py` | `50e686c3...f85387` | `40213b61...4480fa` | **modified** (F5-integrated single-open primitive, isolated) |
| `descriptors.py` | `79c0bcd6...b60b5a` | *(identical)* | unchanged |
| `errors.py` | `0ebb3aad...668051` | *(identical)* | unchanged |
| `memory_accounting.py` | `13f15d29...9d4b4ab` | *(identical)* | unchanged |
| `native_discovery.py` | `463b2a89...698c98` | *(identical)* | unchanged |
| `observation.py` | `6ce3763d...09baaf8a3` | *(identical)* | unchanged |
| `pointer.py` | `5ddfb66d...10211e6f1` | *(identical)* | unchanged |
| `projections.py` | `7dd25ff7...09a31a` | *(identical)* | unchanged |
| `resolver.py` | `26739148...bced38be9e392` | *(identical)* | unchanged |
| `runtime.py` | `dadb5db1...c99fd0` | *(identical)* | unchanged |
| `selection.py` | `946791ed...ee9d85abd` | `c2d28884...4b04df` | **modified** (unified preflight+open primitive, isolated) |
| `sidecar_contract.py` | `24732dbf...67461` | *(identical)* | unchanged |
| `view_cache.py` | `3d89e0b9...942ebad04d` | *(identical)* | unchanged |
| `views.py` | `60a0c1af...268d1270d8b0d` | *(identical)* | unchanged |
| `win_file_identity.py` | `31bf82ff...538ecc5a5c6e74` | *(identical)* | unchanged |
| `normalizer_compat_adapter.py` | — (no frozen counterpart) | `949498764...033a4ffb2` | **new, candidate-only** |
| `resource_estimator.py` | — (no frozen counterpart) | `9412f7295...15af13d112aea9f34` | **new, candidate-only** |
| `resource_preflight.py` | — (no frozen counterpart) | `7f894854...4aff1613` | **new, candidate-only** |

**14 files byte-identical, 3 files modified (all isolated, all already-qualified in B2C-A, unchanged again this turn), 3 new candidate-only files. No file in this table changed during B2C-B itself** — B2C-B added zero lines to any shared-authority file; its only new code lives in the isolated Normalizer candidate (`acquire_master_index_via_qualified_authority`) and its only new plumbing is `stage_candidate_authority.py` (a deterministic copy script, in-repo, not shared-authority logic) plus the in-repo staged `candidate_b2c/sfm_master_authority/` directory it produces.

## 17. Open items (not B2C-B blockers, carried forward)

1. **`shipped_root` provisional path** at the real call site — real production shipped-sidecar deployment location is not yet finalized by any prior B2 stage (Section 3 above).
2. **"Unsupported sidecar" classification** — no distinct fixture exists to independently prove this path through the migrated call site (Section 11 above).
3. **`declare_order`/`sibling_rank` ordering equivalence** — now empirically proven (B2C-A + this turn, real Python 2.7.5, exact hash match including list order) for both the real Master and a structurally distinct synthetic fixture; no longer an open item, listed here only for continuity with B2C-A's own open-items note.

## 18. Status

Every hard gate specified in this authorization passed: identity freeze intact, minimal 3-hunk diff, zero mutation-API reachability (static + dynamic + sentinel proof), provider lifecycle closed in 100% of ~24 test cases across two interpreters, cache/reuse behavior correct, generation/error classification correctly propagated (one fixture gap honestly flagged, not silently assumed), `groupFile` regression proven on two independent structural shapes, provider-handle leak regression intact, shared-authority package hash-confirmed unchanged, and the migrated path measured faster than the frozen parser on both cold and cache-hit acquisition.

**B2C-B READ-ONLY NORMALIZER MIGRATION PASS — B2C-C MUTATION EQUIVALENCE AUTHORIZED**
