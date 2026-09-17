# R3 B2C-B — Astra SECOND Shared-Authority Correction Gate Report

Date: 2026-09-16
Candidate root: `tests/sidecar/qualification/candidate_b2c_correction2/` (authored source at
`sfm_master_authority_productionized/`, deterministically staged into the importable
`sfm_master_authority/` sibling via `stage_candidate_authority.py`)
Normalizer candidate: `tests/sidecar/qualification/candidate_b2c_correction2_normalizer/`
Derived from commit: `c16b9f80b79eab121a9de20932e4637fd3b427ca` ("R3 B2C-B: apply Astra
shared-authority corrections")
No git staging or commit has been performed as part of this phase (Section 14 requirement).

---

## 1. Finding → Correction Table

| Finding | Astra's re-audit verdict | Correction applied this round | Evidence |
|---|---|---|---|
| F1 (re-opened) | Bounded-directory-region fix still let the ACTUAL read span byte 0 → `section_directory_offset + directory_size`; an 8 MiB offset caused an ~8 MiB preflight read | `resource_preflight.py` now `seek()`s directly to the validated directory offset and reads ONLY the bounded directory bytes; header read and directory read are two separate, individually-bounded, individually-instrumented reads (`header_bytes_read`, `directory_bytes_read`) | Test 1 (13/13 both interpreters); `caseA_dir_offset_8mib`: max preflight requested read = 252 bytes with an 8 MiB directory offset |
| F2 (re-opened) | Average-family admission defeated by a real ~2.0–2.76 MB artifact with two 20,000-row families + 20,000 singletons | New `packed_family_counts.py` obtains REAL per-family occurrence counts (fold-table binary search only, never occurrence decode) BEFORE any provider construction; new `evaluate_cumulative_admission` sums real per-family costs, never an average | Test 2 (20/20 both interpreters): Astra's exact two-large-families artifact correctly refused (`total_retained=17,446,592` > 16 MiB gate) while a singleton fold from the SAME artifact admits cleanly |
| 20,000 cap demotion | Must not be primary admission proof | `MAX_SINGLE_FOLD_OCCURRENCE_ROWS` retained as an explicitly-documented SECONDARY ceiling (`secondary_cap_exceeded`), enforced from packed counts before expansion, never substituting for cumulative byte budgeting | Test 2 boundary cases: 19,999/20,000 admit on BYTES (not merely "under the cap"); 20,001 refused specifically via `secondary_single_family_cap_exceeded`, distinct from a byte-gate refusal |
| F3 (batch atomicity) | Two 9 MiB views: second admission evicted the first; ledger undercounted; a lease could be issued on an already-evicted view | New `ViewCache.admit_batch()` computes the WHOLE batch's cost up front, evicts only pre-existing unrelated entries, charges+inserts the entire batch atomically. NEW this session: `ViewCache.acquire_lease()` now refuses a lease on a view that is tracked in NEITHER `_entries` NOR `_leased_orphans` (`errors.EvictedViewLeaseRefused`) | Test 4 Part A (17/17): two 10 MiB views refused as a batch (sum exceeds gate); same-key replacement with two borrowers correctly preserves old+new overlap accounting; lease-on-evicted-view explicitly refused |
| F3 (real command teardown) | `final_report()` released the lease but left `self.master_index` referencing the payload | `self.master_index = None` now happens BEFORE lease release, inside the same `if self.finished` guard, with release wrapped in `try/finally` | Test 4 Part B (32/32 combined with Part A): normal completion, cancellation/failure, deferred re-invocation (idempotent no-op), acquisition-failure-before-lease, and non-fatal release failure (logged, reference still dropped) all verified against the REAL extracted `final_report` teardown block |
| F4 (generation binding) | Wrapper accepted no expected command generation at all | `expected_generation` threaded end-to-end: `acquire_master_index_via_qualified_authority` → `get_broker(expected_build_id=...)` / `broker.acquire_or_reuse_views(expected_generation=...)` → `acquire_cohort`; ONE unified retry budget (`acquire_or_reuse_views` owns it, always calls `acquire_cohort(retries_remaining=0)`) | Test 5 case4 (12/12 combined): command A + acquire A succeeds; command pinned to A while Master is B → explicit refuse (not silent B); A→B→A restore succeeds |
| F5 (snapshot re-admission) | Re-admission called the estimator without the requested-fold/ledger context used by preflight | Architecturally eliminated the separate reduced-signature re-check: ONE canonical `evaluate_cumulative_admission` call, always run against the ACTUAL full-read buffer | Test 3 (9/9 both interpreters): a real artifact swapped mid-open (A → B, genuinely different valid artifacts) is refused using B's real bytes; refusal happens before the frozen validator; exactly one `full_bounded_read` recorded |
| F6/F8 (bootstrap) | Corrected Normalizer candidate still bootstrapped `candidate_b2c` (old, pre-correction package) — the single most severe finding | `_B2C_QUALIFIED_AUTHORITY_ROOT` fixed to `candidate_b2c_correction2`; `_b2c_verify_bootstrap_identity()` added, checking origin dir, API version, `RUNTIME_BUILD_ID` presence/value, and `is_canonical()`, called unconditionally at import time | Test 5 (12/12, GENUINE non-bypassed bootstrap import — see Section 6 below): fresh bootstrap resolves to `candidate_b2c_correction2`; old `candidate_b2c` preloaded → explicit reject; frozen production package preloaded → explicit reject |
| F7 (diagnostics/missing-local) | Diagnostics silently discarded on the real cohort route; raw IOError escaped for missing local artifact; corrupt shipped candidate collapsed to SidecarMissing with no trace | `Cohort._open_provider_once` now passes the broker's REAL diagnostics list; `_try_local_candidate` catches `(IOError, OSError)`; `_find_and_open_matching_artifact` logs `shipped_candidate_skipped` for every skip reason | Test 6 Part A (9/9 under Python 2.7.5, 13/13 under Python 3.10 including the Python-3-only corrupt/unsupported fixture cases): all seven failure-matrix cases correctly classified, diagnostics survive where documented |
| NEW (found this session) | "Second-view failure" batch admission needlessly evicted an unrelated, still-useful cache entry even when the batch's OWN total already exceeded the gate (violating `admit_batch`'s own documented "pre-existing visible cache state is left completely untouched" promise) | Added an upfront hopeless-request check (`needed`/`total_needed > RETAINED_PROMOTION_GATE_BYTES`) to BOTH `admit()` and `admit_batch()`, refusing before touching any existing cache state | Test 4 Part A.2: an unrelated pre-existing 2 MiB entry survives a doomed 18 MiB batch untouched (entry_count and ledger charge both unchanged) |

---

## 2. Exact Changed Candidate Files + SHA-256 (this round, current working tree)

| File | SHA-256 |
|---|---|
| `sfm_master_authority_productionized/broker.py` | `bd1d3fb3d9f437e2f10a6ca85034918e15a8f8d3ebdab30a0e5c0ce5696c9cdf` |
| `sfm_master_authority_productionized/cohort.py` | `bca015e7101107a0275fd7bea0f2407d02d6ab2dbc10322dfcdee752ef906bc2` |
| `sfm_master_authority_productionized/errors.py` | `873698907b84529bceb6136751711d986c25274122c8bc23f99ae07c38bc935b` |
| `sfm_master_authority_productionized/normalizer_compat_adapter.py` | `ccbff06f185737754183c44a752dfc95866169873718df5e74c7cd33f2fed6f0` |
| `sfm_master_authority_productionized/packed_family_counts.py` (NEW file) | `667fb319fda61714c008672ef365c5e24f7a39e9075b6750ffb9f77ddae592db` |
| `sfm_master_authority_productionized/projections.py` | `483988ce67e1e7f529e751e87782781bd3395ef5253ea61d628e6225960b53dd` |
| `sfm_master_authority_productionized/resource_estimator.py` | `c4ede2d39efee7c24c795219094258b5045a27bfff935a02403a31080f263451` |
| `sfm_master_authority_productionized/resource_preflight.py` | `c1d6f4fe9364e1fe32a46530dfa2a13690aca79c62714cdb0fbb1f11553490ca` |
| `sfm_master_authority_productionized/runtime.py` | `ab8f7be4a75e0c0f87af7e2022c0258ece6075127c240254fe5ebd783e286f5c` |
| `sfm_master_authority_productionized/selection.py` | `ad9ffe286af5909a4e6af9c31ecb14a01fabc53991e140b913702092a69fb337` |
| `sfm_master_authority_productionized/view_cache.py` | `2e0f91938d708503a740dc399bbae59fe4db270d794ad0612f3bd513b52508be` |
| `candidate_b2c_correction2/stage_candidate_authority.py` (NEW file, staging script) | `d2829c133ea4f2d99e78ab848215c1b8e3d503765160a521ed439b594f5c56ae` |
| `candidate_b2c_correction2_normalizer/Rebuild_Control_Groups_Normalizer_B2CB_correction2_candidate.py` | `b01fc7376d66267bc3d16eccc6eeefd3f09e2ca9bf91c411c4ba3c5d70b47444` |

Unchanged since the first correction (`c16b9f80...`): `descriptors.py`, `memory_accounting.py`,
`observation.py`, `pointer.py`, `views.py`, `native_discovery.py`, `resolver.py`,
`win_file_identity.py`, `sidecar_contract.py`, `__init__.py`. The 21-file staged
`sfm_master_authority/` sibling directory is a byte-identical copy of
`sfm_master_authority_productionized/`, produced by `stage_candidate_authority.py` (never hand-edited).

## 3. Exact Diffs Against `c16b9f80...`

Full unified diffs (against the corresponding file in the untouched, still-`c16b9f80`-identical
`candidate_b2c_correction/` directory) are at
`tests/sidecar/qualification/candidate_b2c_correction2/diffs/`:
`broker.py.diff`, `cohort.py.diff`, `errors.py.diff`, `normalizer_compat_adapter.py.diff`,
`projections.py.diff`, `resource_estimator.py.diff`, `resource_preflight.py.diff`, `runtime.py.diff`,
`selection.py.diff`, `view_cache.py.diff`, `Rebuild_Control_Groups_Normalizer_candidate.py.diff`, plus
`packed_family_counts.py.NEW_FILE` (no prior counterpart — copied verbatim, entirely new this round).
`git status --porcelain` on `candidate_b2c_correction/` and `candidate_b2c_correction_normalizer/`
confirms both remain byte-identical to `c16b9f80...` (clean, zero diff), so every diff above is
attributable solely to this round's own changes.

## 4. Actual Preflight Read-Size Traces (F1)

From Test 1 (`test_b2c_correction2_test1_preflight_sizes.py`), against a REAL official artifact
relocated to an 8 MiB directory offset (`struct.pack_into` patching the header field directly, real
directory bytes copied to the new location):

```
[caseA_dir_offset_8mib] header=108 directory=252 max_preflight_requested=252
[caseB_huge_offset_1gib] header=108 directory=0   max_preflight_requested=108
[caseC_truncated_directory] header=108 directory=0 max_preflight_requested=108
```

All three stay at or below the small-preflight ceiling (`HEADER_SIZE + _MAX_PREFLIGHT_REGION_BYTES`
= 65,644 bytes) regardless of where the directory offset points, including a directory offset at
8 MiB and at ~1 GiB. Invalid explicit `runtime_cap_bytes` (negative/zero/string/bool/huge) is
rejected with **zero candidate-artifact file opens** in every case.

## 5. Packed-Family Pre-Expansion Counts (F2)

`packed_family_counts.get_packed_family_counts_batch()` obtains real per-fold occurrence counts via
FOLD_TABLE binary search alone (`_resolve_string` reimplements only the string-lookup half of
`BoundedProvider.lookup_fold`, never entering its occurrence-decode loop). Verified exact against
the REAL compiled fixtures' own manifest `occurrence_count`:

```
boundary_below_19999  -> 19999  (manifest: 19999)  — 0 provider constructions triggered
boundary_at_20000     -> 20000  (manifest: 20000)  — 0 provider constructions triggered
boundary_above_20001  -> 20001  (manifest: 20001)  — 0 provider constructions triggered
```

## 6. Aggregate Reservation Model (F2)

`resource_estimator.evaluate_cumulative_admission(shape, per_consumer_packed_family_counts,
runtime_cap_bytes, retained_gate_bytes, transient_gate_bytes, aggregate_existing_retained_bytes,
enforce_secondary_single_family_cap=True)` — the ONE canonical, unconditional admission function.
Per-consumer retained cost = real per-family byte sum (`estimate_retained_from_packed_counts`,
never averaged) + exact hierarchy/metadata cost; summed conservatively across consumers (never
assuming cross-consumer sharing). Combined against `aggregate_existing_retained_bytes` (the
broker's own ledger total BEFORE this acquisition). Astra's exact two-large-families reproduction
(real compiled artifact, 60,000 total occurrences: two 20,000-row families + 20,000 singletons,
2,760,596 bytes):

```
requesting {astrafamilyone, astrafamilytwo} only:
  total_retained=17,446,592  total_transient=29,273,001  reason=cumulative_retained_exceeds_gate
  -> REFUSED, zero provider constructions (Test 2 "t2.astra_repro" cases)
requesting {astrasingleton00000} only (same artifact):
  -> ADMITTED cleanly (request-aware, not a blanket artifact-level refusal)
```

## 7. Lease/Publication Ownership Model (F3)

`ViewCache.admit_batch(views)`: computes `total_needed = sum(v.estimated_bytes)` up front; evicts
only pre-existing, unrelated entries (never a batch member, since none are in `_entries` yet) until
the WHOLE batch fits or nothing more can be evicted; if the batch's own total already exceeds the
gate, refuses immediately WITHOUT touching any existing state (new this session — see Section 1's
last row); retires any same-key predecessor via `_remove()` (deferring its charge as a "leased
orphan" if it still has live leases) before charging+inserting the entire batch atomically.
`ViewCache.acquire_lease(view)` (corrected this session): refuses (`errors.EvictedViewLeaseRefused`)
a lease attempt on a view tracked in neither `_entries` nor `_leased_orphans` — closing the exact
gap Astra named ("a lease can be issued on an already-evicted returned view without restoring
charge"). Proven via Test 4 Part A (17/17): two 10 MiB views refused as a batch; an unrelated 2 MiB
pre-existing entry survives a doomed batch untouched; a same-key replacement with two live borrowers
preserves both charges until both release; a genuinely evicted (zero-lease-at-eviction) view's
lease attempt is explicitly refused.

## 8. Actual Command Teardown Evidence (F3)

Test 4 Part B extracts and execs `final_report()`'s REAL teardown block (lines 12675–12720 of the
correction2 Normalizer candidate) verbatim, against a REAL broker/lease (genuine acquisitions
against the real canonical Master), across five cases — all PASS on both interpreters:

- **Normal completion**: `self.finished` → True, `self.master_index` → None, `self._master_index_lease`
  → None, real `outstanding_lease_count()` drops by exactly 1.
- **Cancellation/command failure** (`success=False`): identical teardown (the block has no branch on
  `success`), same lease-count proof.
- **Deferred re-invocation** (simulating a deferred QObject-deletion callback or a caller race): a
  second `final_report()` call on an already-finished command is a genuine no-op (guarded by
  `if self.finished: return`) — no double release.
- **Acquisition failure before a lease ever existed** (`_master_index_lease` attribute absent
  entirely): does not crash (`getattr` default handles it); `finished` still becomes True.
- **Non-fatal release failure** (a synthetic `release_view_lease` raising `RuntimeError`): the
  failure is logged exactly once, never silently swallowed, and `_master_index_lease` is STILL
  dropped via the `finally` clause (never left as a stale, un-recheckable live reference).

## 9. Explicit Command/View Generation Model (F4)

`acquire_master_index_via_qualified_authority(..., expected_generation=None)` →
`get_broker(expected_api_version=_B2C_EXPECTED_API_VERSION, expected_build_id=_B2C_EXPECTED_BUILD_ID)`
→ `broker.acquire_or_reuse_views(..., expected_generation=expected_generation)`. Production call site
passes `expected_generation=self.master_hash` (the command's own pinned hash at start). Test 5 case4
(genuine, non-bypassed bootstrap — see Section 6 below), against two REAL Master fixture generations
A and B:

```
case4.0 command A + acquire A (matching pin)                 -> succeeds
case4.1 command STILL pinned to A, Master now B               -> explicit refuse (AuthorityChangedDuringAcquisition/SidecarMissing), NEVER silently accepts B
case4.2 A -> B -> A (restore)                                  -> re-acquisition under restored generation A succeeds
```

One unified retry budget: `acquire_or_reuse_views` owns the sole `retries_remaining` counter and
always calls `acquire_cohort(..., retries_remaining=0)`, so the inner call never retries
independently.

## 10. Snapshot A→B Re-Admission Evidence (F5)

Test 3 (9/9, both interpreters) engineers a genuine mid-open replacement: a real, valid artifact A
is open (header+directory already read) when the SAME on-disk file is rewritten in place (via a
fresh, unbuffered handle — `io.BufferedReader` can otherwise serve stale cached bytes across a
`seek()`, a real hazard discovered and worked around while building this test) to become a
different, genuinely valid artifact B (Astra's two-large-families artifact), before the module's own
single `full_bounded_read` call. Result:

```
t3.0  swap occurred before the full read                                    -> True
t3.1  acquisition against the REPLACED content is REFUSED                    -> True
t3.3  preliminary shape (from A) WAS present                                 -> True
t3.4  final shape (from B) DIFFERED from the preliminary (A) shape           -> True
t3.5  exactly ONE full_bounded_read occurred                                 -> True (count=1)
t3.6  zero provider constructions before the refusal                        -> True (count=0)
t3.8  cumulative_admission.total_retained_bytes reflects B's real ~17.4MB    -> True (17,446,592 > 16 MiB)
```

Refusal happens from resource admission BEFORE validator/projection expansion, exactly one full disk
read, no reliance on any malformed/corruption signal.

## 11. Actual Bootstrap Package/Origin/API/Build Evidence (F6/F8)

**Critical methodology correction** (Section 1 note, re-affirmed here): every test in BOTH prior
correction rounds extracted `acquire_master_index_via_qualified_authority`'s source via line-range
`exec()` and injected a FAKE `_b2c_authority_runtime` module directly into the exec namespace —
bypassing the real module-level bootstrap import entirely, which is exactly why no test ever caught
the wrong-package bootstrap. Test 5 fixes this: it extracts and execs the REAL bootstrap block
(lines 152–210: genuine `sys.path` insertion, real `from sfm_master_authority import ...`
statements, real `_b2c_verify_bootstrap_identity()` call) FIRST, via a `fresh_bootstrap_namespace()`
helper that pops all `sfm_master_authority*` entries from `sys.modules` to simulate fresh-process
import behavior, and only THEN execs the function body into that SAME namespace — no injected fake
at any point.

```
case1.0 fresh-process bootstrap with correction2 on sys.path succeeds        -> True
case1.1 REAL bootstrap resolved to candidate_b2c_correction2 (not candidate_b2c/) -> True
case1.2 loaded package has RUNTIME_BUILD_ID (the corrected build)            -> True
case1.4 a REAL acquisition through the ACTUAL bootstrap succeeds             -> True
case2.0 old candidate_b2c/ preloaded first under the canonical name          -> explicitly REJECTED
case3.0 frozen production package preloaded first                           -> explicitly REJECTED
```

`RUNTIME_BUILD_ID = "b2c-correction2-lease-generation-binding-2026-09-16"` (distinct from the
broader, unchanged `RUNTIME_API_VERSION = "1.0.0-b2a"`, which the pre-correction candidate also
shared — build ID is the field that actually distinguishes them). `_b2c_verify_bootstrap_identity()`
checks `assert_expected_origin`, `get_runtime_api_version()`, `hasattr(runtime, "RUNTIME_BUILD_ID")`
(rejects any pre-correction package lacking it entirely), `get_runtime_build_id()`, and
`is_canonical()` — called unconditionally at module import time.

## 12. Reproducible Fixture Manifest + Hashes (F8)

New, explicit, repo-relative fixture root:
`tests/sidecar/qualification/candidate_b2c_correction2/fixtures/`, generated deterministically by
`tests/sidecar/qualification/build_test2_fixtures_correction2.py` (Python 3 only — uses the real
production compiler/writer/reader pipeline; every fixture is genuinely compiled and
self-validated via `compiler.self_validate_from_bytes`, never hand-assembled). Manifest at
`fixtures/manifest.json` records, per fixture: `master_sha256`, `artifact_sha256`, `artifact_bytes`,
`group_count`, `occurrence_count`, and both file paths. Eight fixtures: `boundary_below_19999`,
`boundary_at_20000`, `boundary_above_20001`, `astra_two_large_families`, `concentrated_small_vocab`,
`long_literals`, `deep_hierarchy`, `dense_metadata`. This removes THIS gate's own new-fixture
dependence on Claude-temp directories or `C:\Users\Public\Documents` historical staging (the
pre-existing B2A/B2F fixture roots referenced by Tests 1/2/6 for OFFICIAL-artifact/W1/W2 comparison
purposes remain as-is — reproducing those historical roots is explicitly out of this gate's scope
per Section 10's "final public deployment layout may still wait"). `stage_candidate_authority.py`
(new this round, direct counterpart of the first correction's script) makes the
`sfm_master_authority_productionized/` → `sfm_master_authority/` staging step itself a checked-in,
re-runnable script rather than an ad hoc copy.

## 13. Failure/Diagnostic Matrix (F7)

Test 6 Part A calls `selection.select_sidecar_candidate` (the exact function F7 corrected) directly:

| Case | Classification | Structured diagnostic survives? |
|---|---|---|
| A.1 unsupported format_contract_version (checksum-valid) | `SidecarMissing` (only candidate skipped) | Yes — `reason=FormatUnsupported` |
| A.2 structurally corrupt (checksum-valid) | `SidecarMissing` | Yes — `reason=SidecarCorrupt` |
| A.3 missing local (valid pointer, file absent) | Recovers to valid SHIPPED | Yes — `local_sidecar_missing_passive_notice` |
| A.4 missing shipped (empty root, no local) | `SidecarMissing` | n/a (nothing to report) |
| A.5 resource refusal (valid, too expensive) | `ResourceAdmissionRefusal` (distinct from Missing/Corrupt) | n/a (not a diagnostic-bearing path) |
| A.6 pointer/artifact SHA disagreement | Recovers to valid SHIPPED | Yes — `local_pointer_artifact_disagreement` |
| A.7 valid local pointer+artifact | Succeeds directly, `SOURCE_LOCAL` | None needed (no recovery) |

A.1/A.2 require Python 3 (`corruption_helpers.py` uses `pathlib`, matching the established
Python-3-only convention for compiled-fixture-mutation tooling) — independently verified there
(13/13); A.3–A.7 verified under BOTH interpreters.

## 14. Fresh-Process Memory Measurement Method + Raw Evidence (Section 12)

**Methodology correction**: each case now runs in its OWN FRESH real-Python-2.7.5 subprocess
(`_test2_memory_worker.py`, spawned via `subprocess.Popen` from
`test_b2c_correction2_test2_memory_methodology.py`), so `PeakPagefileUsage` is a genuine
fresh-process peak (never inherited from a prior case), `PrivateUsage` is sampled immediately
before/after the ONE acquisition attempt (phase-resolved, not an end-of-run delta), and `PagefileUsage`
(committed VAS) is recorded alongside. Raw samples (33/33 checks PASS):

```
boundary_below_19999 [admit]:  before.private=4,472,832  after.private=13,762,560  after.peak_pagefile=16,166,912
boundary_at_20000    [admit]:  before.private=4,456,448  after.private=13,565,952  after.peak_pagefile=15,945,728
boundary_above_20001 [refuse]: before.private=4,468,736  after.private=5,398,528   after.peak_pagefile=12,562,432
astra_two_large      [refuse]: before.private=4,481,024  after.private=5,410,816   after.peak_pagefile=12,357,632
astra_singleton      [admit]:  before.private=4,440,064  after.private=5,423,104   after.peak_pagefile=10,334,208
```

Refused cases show markedly smaller private-bytes deltas and peak pagefile than admitted cases of
comparable requested scale — direct evidence the fix refuses BEFORE the expensive materialization,
not merely reports a post-hoc number.

## 15. Tests 1–6 Totals, Both Interpreters

| Test | Python 3.10 | Real Python 2.7.5 |
|---|---|---|
| Test 1 (preflight sizes, F1) | 13/13 PASS | 13/13 PASS |
| Test 2 (packed admission, F2) | 20/20 PASS | 20/20 PASS |
| Test 2 memory methodology (Section 12) | n/a (32-bit-only) | 33/33 PASS |
| Test 3 (snapshot replacement, F5) | 9/9 PASS | 9/9 PASS |
| Test 4 (atomic ownership + teardown, F3/F4) | 32/32 PASS | 32/32 PASS |
| Test 5 (generation + bootstrap, F4/F6/F8) | 12/12 PASS | 12/12 PASS |
| Test 6 Part A (failure matrix, F7) | 13/13 PASS | 9/9 PASS (A.1/A.2 require Python 3, see Section 13) |
| Test 6 Part B (semantic regression) | 39/39 PASS (candidate-only) | 39/39 PASS (full ref-vs-candidate hash equality) |

**Grand total**: 138/138 PASS (Python 3.10); 167/167 PASS (real Python 2.7.5, including the 32-bit
memory-methodology suite). Zero failures across both interpreters.

## 16. Repaired Semantic-Equivalence Results

Under real Python 2.7.5 (Test 6 Part B), the corrected `acquire_master_index_via_qualified_authority`
matches the frozen production `parse_targeted_master()` EXACTLY (combined structure hash, covering
`mapping_count`, `destination_count`, `folded`, `exact_literals`, `group_sibling_order`,
`group_metadata`) across every scope-matrix case: `6B_known_exact_literals`, `6B_unknown_literal`,
`6B_left_right`, `6B_mixed_known_and_unknown`, `6C_W1_single_shot_single_target_Fox`,
`6C_W2_six_target_union` — all `mapping_count=128555/128555 destination_count=42/42`. The
6A_full_corpus case correctly refuses (already-qualified resource gate, unchanged intended
behavior) with `current_open_provider_count == 0` even on refusal. The groupFile synthetic-wrapper
regression (a structurally different 61-group nested fixture) confirms no phantom `groupFile` group
ever leaks into adapter output. **W3 (72-shot) remains explicitly UNKNOWN** — its own historical
capture recorded a failed run against the wrong project (expected 72 shots, found 11); not
force-substituted with synthetic data, consistent with every prior gate in this project.

## 17. Frozen Identity Table

| Artifact | SHA-256 | Status |
|---|---|---|
| Production `Rebuild_Control_Groups_Normalizer.py` | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` | Re-verified unchanged this session |
| Canonical `sfm_defaultanimationgroups.txt` | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | Re-verified unchanged this session |
| Frozen deployed `sfm_master_authority/broker.py` (production package) | `d2e66251fe26165976829456eba3ae7fa2420527e41092179d94a401f56dd8b9` | Re-verified unchanged this session |
| Frozen `candidate_packed_provider_r3a2b.py` (validator/provider) | Unchanged — never modified in any correction round | Reused as-is |
| First-correction candidate directories (`candidate_b2c_correction/`, `candidate_b2c_correction_normalizer/`) | — | `git status --porcelain` clean — byte-identical to commit `c16b9f80...` |
| Correction2 Normalizer candidate | `b01fc7376d66267bc3d16eccc6eeefd3f09e2ca9bf91c411c4ba3c5d70b47444` | New this round (see Section 2) |

## 18. Current Support-Domain Declaration

Unchanged from the prior correction round's declared support domain: read-only Normalizer authority
acquisition (B2C-B scope) only. No mutation policy, taxonomy, or presentation logic has been touched.
`MAX_SINGLE_FOLD_OCCURRENCE_ROWS = 20000` remains an explicitly-flagged, non-authoritative secondary
ceiling with no corpus-derived justification (the real canonical Master's own maximum observed
single-family occurrence count remains 7). The 16 MiB retained / 32 MiB transient promotion gates
remain gates pending real 32-bit-process qualification, not proven facts established by the Python-side
ledger alone (per `AggregateLedger.RUNTIME_QUALIFICATION_NOTE`, unchanged). B2C-C, B2C-D, and
Character Preset migration remain entirely out of scope and have not been started.

## 19. Status Line

**B2C-B SECOND CORRECTION IMPLEMENTATION PASS — INDEPENDENT ASTRA RE-AUDIT REQUIRED**

This report does NOT self-authorize B2C-C. No SFM has been run. No git staging or commit has been
performed. All six required tests (Section 13 of the second-correction-gate prompt) pass on both
Python 3.10 and real 32-bit Python 2.7.5, including genuine ref-vs-candidate hash equality against
the frozen production parser and a non-bypassed, genuinely-imported bootstrap proof. Two additional
real defects were found and fixed during this session's own test construction (not present in
Astra's original F1–F8 list): the "hopeless batch eviction" gap in `admit`/`admit_batch`, and the
"evicted view lease" gap in `acquire_lease` — both are documented in Section 1's final row and
proven in Section 7/Test 4 Part A. Independent Astra re-audit of this second correction round is
required before any B2C-C authorization.
