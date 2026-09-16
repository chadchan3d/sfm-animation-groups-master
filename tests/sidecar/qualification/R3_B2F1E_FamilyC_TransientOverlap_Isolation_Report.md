# R3-B2F1E: Family C Transient-Overlap Isolation — Report

**Authorization:** `SFM_CGN_R3_B2F1E_FamilyC_TransientOverlap_Isolation_ClaudeCode_Prompt_2026-09-16.md`
**Status:** `B2F1E CURRENT SEMANTICS REQUIRE >32 MiB FOR FAMILY C — NARROWER ADMISSION REQUIRED`

---

## Method

No production/frozen file was modified. I built a test-only phase-isolation harness (`b2f1e_phase_isolation_harness.py`) that mirrors `Cohort._open_provider_once()`/`build_projections()` **exactly** — calling the same underlying frozen functions (`observation.observe_master`, `sidecar_contract.ensure_loaded`, `selection_mod.select_sidecar_candidate`, `BoundedProvider.open_path`, `provider.close()`, `views.DetachedView`, `views.LiveAuthorizationToken`, `descriptors.SemanticGeneration`) in the same order cohort.py's own code does, but inlined so I can sample between steps the bundled `build_projections()` call cannot expose without editing the frozen file.

**Honest limitation, stated up front:** `BoundedProvider.open_path()` bundles the bounded read and complete Section 20 A-J structural validation atomically (`_read_path_bounded` → `_validate_complete` → object construction) — there is no public seam between "read acquired" and "fully validated" without editing the frozen provider. P2 (this task's numbering) and P3 are therefore reported as **one** measured boundary (labeled `P2_3` below), not fabricated as separate.

## 1. Offline reproduction of Run 4 (control)

Real Python 2.7.5, fresh process, exact `fixtureC_1p25x`, exact 16 MiB cap, current code:
- Admission: **accepted**
- `retained_detached_views` (Normalizer view only, this isolated harness): **16,732,158 bytes** — matches the two-view Run 4 ledger total (16,733,007, which additionally includes the tiny CSP view) to within 849 bytes, i.e. essentially all of Run 4's retained charge is the Normalizer view alone.
- Provider opens/closes: balanced (open → close, once per read pass observed).
- Fresh-process peak delta from clean baseline: **35.16 MiB** (36,868,096 bytes) — same general range as real-SFM Run 4's **37.06 MiB**. Control confirmed.

## 2/3. Phase-by-phase table (Family C, `fixtureC_1p25x`)

| Phase | private_bytes | peak_pagefile_usage | What just happened |
|---|---|---|---|
| P0 | 3,813,376 | 3,813,376 | clean baseline, before any authority import |
| P1 | 3,936,256 | 3,936,256 | authority package imported |
| P1b | 4,923,392 | 6,119,424 | `sidecar_contract.ensure_loaded()` (dynamic FINAL R3-A2B module load) |
| P2 | 7,020,544 | **24,408,064** | `selection.select_sidecar_candidate()` returns — this call performs its **own internal** bounded-read + full-validate + close (via `validate_selected_artifact` inside `_find_matching_artifact`), purely to resolve the artifact path/identity; **that buffer is already closed** by the time this returns (private_bytes settled back to 7.0 MB) but the OS peak counter (24.4 MB) proves a real transient spike happened during it |
| P2_3 | 19,599,360 | 24,408,064 | cohort-level `BoundedProvider.open_path()` returns — **second** bounded read + full validation, this time kept open (`provider._buf` live); `_groups`/`_metadata_rows`/`_child_index` still `None` (confirmed by direct attribute inspection, not inferred) |
| P4 | 19,599,360 | 24,408,064 | about to call `builder_fn(provider)` |
| **P5** | **40,636,416** | **40,681,472** | `builder_fn(provider)` returns — projection payload allocated (`estimated_bytes=16,732,158`); `provider._groups`/`_metadata_rows` confirmed populated (`True`/`True`); `provider._buf` still live **simultaneously** with the new payload — **this is the peak phase** |
| P6 | 26,841,088 | 40,681,472 | `provider.close()` — `_buf`/`_groups`/`_metadata_rows`/`_child_index` released; ~13.8 MB freed |
| P7_8 | 26,841,088 | 40,681,472 | `DetachedView` constructed and held (mirrors cache publication + consumer retention) |
| P9 | 9,478,144 | 40,681,472 | references dropped + `gc.collect()`; ~17.4 MB freed (the payload itself) |

**Peak delta from P0: 36,868,096 bytes = 35.16 MiB, reached at phase P5.**

## 3. Exact answers (A–F), by direct inspection, not subtraction alone

- **A. Bounded-read/buffer contribution:** the first (selection-internal) read+validate pass alone drives peak from 6.1 MB → 24.4 MB, an **~18.3 MB** transient contribution — freed immediately, never retained.
- **B. Retained detached view:** **16,732,158 bytes** (`estimated_bytes`, confirmed identical to the ledger figure).
- **C. Validator/provider caches/scratch:** at P4 (buf live, caches not yet decoded), private = 19,599,360. At P5 (caches decoded + payload built), private = 40,636,416. Delta = 21,037,056. Subtracting the known payload size (16,732,158) leaves **≈4,304,898 bytes (~4.1 MB)** attributable to the provider's own lazily-decoded `_groups`/`_metadata_rows` caches — confirmed as a real, separate structure by directly checking `provider._groups is not None` / `provider._metadata_rows is not None` (both `True` at P5), not inferred from subtraction alone.
- **D. Overlap between packed backing and completed view:** at P5, **all three** are simultaneously resident: `provider._buf` (raw ~12.18 MB sidecar bytes, still referenced), the provider's own decoded caches (~4.1 MB), and the fully-built payload (~16.7 MB) — none released until P6's `provider.close()`. This triple-overlap, required by the current architecture (provider must stay open and decoded while the builder consumes it; the payload must be fully built before the provider can close), is the direct cause of the peak.
- **E. Exact phase of peak:** **P5** — immediately after `builder_fn(provider)` returns, before `provider.close()`.
- **F. Objects alive at that phase:** `provider._buf`, `provider._groups`, `provider._metadata_rows`, and the local `payload` dict (`groups`, `metadata_by_path`, `lookup_results`, `wrapper_path`) — all four simultaneously strongly referenced.

## 4. Family A/B/C comparison (same phase harness, same 16 MiB cap)

| Fixture | Sidecar bytes | Payload (`estimated_bytes`) | Peak phase | Peak delta from P0 | Dominant extra structure |
|---|---|---|---|---|---|
| A (`fixtureA_1p5x`) | 14,304,167 | **271,224** | **P2** (first read/validate) | 17.09 MiB | none — payload negligible; peak is entirely the read/validate step |
| B (`fixtureB_1p5x`) | 14,181,874 | **194,238** | **P2** (first read/validate) | 22.11 MiB | none — payload negligible; B's higher peak-at-P2 than A reflects validating far more occurrences (181,632 vs 21,024), a validation-time cost, not a payload cost |
| C (`fixtureC_1p25x`) | 12,179,112 | **16,732,158** | **P5** (after payload build) | 35.16 MiB | the Normalizer-like payload itself (`groups` + `metadata_by_path`), 60–86x larger than A/B's |

**This exactly explains why A/B pass and C fails.** `build_normalizer_like_projection` materializes `list(provider.iter_groups())` and, per group, `list(provider.iter_metadata(path_id))` — a complete copy of the group hierarchy and all metadata, by design ("complete hierarchy/metadata fidelity", per the function's own docstring). Payload size therefore scales with **group_count × metadata-per-group density**, not with raw occurrence count: A and B both have only 127 groups with 252/126 total metadata entries (payload stays under 300 KB); C has 2,729 groups and 19,096 metadata entries (payload reaches 16.7 MB) despite A/B/C all having comparable-or-larger occurrence counts. For A/B, the payload is so small that the pre-existing read/validate step (peaking around 17–22 MiB, itself well inside the 32 MiB gate) remains the process peak throughout the whole acquisition. For C, the payload-construction step adds enough on top of that same read/validate baseline to push the total past 32 MiB.

## 5. Design-alternative prototypes

### Alternative A — chunked cumulative bounded read: tested, insufficient alone
Built and ran a test-only prototype (`b2f1e_singleread_prototype.py`) that skips the redundant selection-internal validate-and-discard pass entirely and goes straight to one `BoundedProvider.open_path()` call (source_sha256 still fully verified; no safety weakened). Result for Family C:
- Single-read peak at the open step: 23,523,328 (vs. 24,408,064 with the current double-read) — only **884,736 bytes (~0.84 MiB)** lower.
- Final peak after `builder_fn`: 40,009,728 (vs. 40,681,472) — only **671,744 bytes (~0.64 MiB)** lower.

**Eliminating the duplicate read does not materially help.** The validation pass's own cost (proportional to structural complexity, not merely buffer size) dominates that stage regardless of whether it runs once or twice — CPython's allocator reaches nearly the same high-water mark either way. A genuinely chunked read would save at most this same sub-1-MiB margin. **Rejected as insufficient on its own.**

### Alternative B — exact-known-size-plus-one bounded read: not separately tested, same conclusion applies
Since Alternative A already demonstrates that buffer-*sizing* is not the dominant cost at the read/validate stage (the validation *computation* is), a same-in-kind change to right-size the read buffer would be expected to save a similarly small margin. Not worth a separate prototype run given Alternative A's direct evidence.

### Alternative C — earlier backing release / staged projection: reasoned infeasible within current semantics, not merely assumed
Read `projections.py`'s actual `_builder(provider)` body directly:
```python
groups = list(provider.iter_groups())
metadata_by_path = {}
for g in groups:
    metadata_by_path[g["path_id"]] = list(provider.iter_metadata(g["path_id"]))
```
This **is** the complete-fidelity payload — there is no way to avoid fully materializing it without dropping "complete hierarchy/metadata fidelity" (an explicit, named consumer-semantic requirement, which Section 5.C's own constraint forbids changing). The provider must remain open (backing live) for the full duration of this construction, since `iter_groups()`/`iter_metadata()` decode from `provider._buf` on demand. The provider's own `_groups`/`_metadata_rows` caches (the ~4.1 MB in Section 3.C) are populated as a side effect of that iteration and are only released at `provider.close()` — there is no exposed API to flush just those caches earlier while keeping the provider technically open for a still-in-progress builder. **Staged release before the payload is complete is not possible without either (a) changing the frozen provider to expose an early-cache-flush primitive, or (b) redesigning the builder to stream/serialize incrementally instead of building one in-memory payload — both are real implementation changes, not offline-provable within this task's no-frozen-code-change constraint. Per Section 5.C's own escape hatch: this is reported as infeasible under current semantics, not glossed over.**

### Alternative D — structural transient admission estimator: recommended
The existing `ViewAdmissionRefused` gate already computes `_estimate_payload_bytes(payload)` — but only **after** `_builder(provider)` has already fully run, i.e., after the entire ~35–37 MiB transient cost has already been paid. This confirms and quantifies, for the first time with real numbers, a limitation this project's own earlier B2F Section 9 raised but couldn't yet measure: **the current admission check is too late to protect the transient gate — it only protects the retained gate.**

A cheap, *pre-read* estimator is directly feasible: `format.py`'s directory rows (`SECTION_GROUP_TABLE`, `SECTION_METADATA_TABLE`) already carry each section's exact `row_count` in the artifact's header/directory (a fixed ~108+9×28-byte region per `HEADER_SIZE`/`DIRECTORY_ROW_SIZE`), readable with a tiny, cheap partial read — **before** any full bounded-read or structural validation. `group_count` and `metadata_count` are therefore knowable up front, and a conservative formula calibrated against this task's own real measurements (e.g., ≈876 bytes/metadata-entry, derived from 16,732,158 bytes ÷ 19,096 entries) could refuse a Family-C-shaped artifact **before** paying any of the expensive read/validate/build cost — correctly classified as a resource-admission refusal (`ResourceAdmissionRefusal`-style), never as corruption.

## 6. Qualification criterion check

No candidate from Sections 5.A–5.C brought Family C's measured peak at or under 32 MiB. Alternative A's best empirical result (single-read) was still 40,009,728 bytes (~38.16 MiB) — 6.16 MiB over gate. Alternative C could not be safety-provably implemented without a frozen-code or builder-architecture change beyond this task's scope. **No offline-provable, semantics-preserving, gate-qualifying candidate exists** — the qualification criterion in Section 6 is not met by anything tested.

## 7. Decision

**`B2F1E CURRENT SEMANTICS REQUIRE >32 MiB FOR FAMILY C — NARROWER ADMISSION REQUIRED`**

The overlap is intrinsic to the current architecture's contract (provider stays open and decoded for the full duration of a complete-fidelity payload build; the payload itself must fully materialize the entire hierarchy+metadata by design) for structurally dense shapes like Family C. The recommended next architecture step is Alternative D: a cheap, header/directory-only, pre-read structural estimator (using `group_count`/`metadata_count` directly from the format's own table row-counts) that refuses such shapes **before** the expensive bounded-read/validate/build sequence, closing the gap this task found — that today's admission check runs only after the transient cost has already been paid.

## 8. Frozen identities — unchanged, confirmed

All read-only throughout this task (no edits made to any of them):

| File | SHA-256 |
|---|---|
| Canonical Master | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |
| Official sidecar artifact | `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` |
| FINAL R3-A2B validator | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` |
| FINAL R3-A2B provider | `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677` |
| Production Normalizer | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` |
| `sfm_master_authority/selection.py` | `946791edb172dcc295d1cd8c161db1be68a138e255a7ecb313afb2fee9d85abd` |
| `sfm_master_authority/projections.py` (read for analysis only) | `7dd25ff7104730cef357a6710e3d56e098b7de216eb306527dad2b09c9f0b31a` |
| `sfm_master_authority/cohort.py` (read for analysis only) | `50e686c34b498f4213103e9e2bc0c41734b9d78874141457bffbed0610f85387` |
| `b2f1_campaign_core.py` (shared test harness core, unchanged since B2F1B) | `f40200fee5dfe266bc4e3d11ca04fa5359b0ef279c0bb696c56a04bf5934f00f` |

No shared authority implementation was changed experimentally in this task, so no B2A/B2B regression rerun was required.

New test-only files (diagnostic only, never wired into production):

| File | SHA-256 |
|---|---|
| `b2f1e_phase_isolation_harness.py` | `39533452ac2db18b37376f79c709b47fad2ca0d7b2530ef8b578bb13f8711b03` |
| `b2f1e_singleread_prototype.py` | `b2987a55fa9a9234e29daa3b1122ceaf794e47869c33d8e4ed8af23d8e6f4047` |

## Deliverables checklist

1. ✅ Phase-by-phase table — Section 2.
2. ✅ A/B/C comparison — Section 4.
3. ✅ Peak object/lifetime attribution — Section 3.
4. ✅ Prototype results A–D — Section 5.
5. ✅ Semantic/safety analysis — Section 5.C, 5.D.
6. ✅ Recommended next architecture step — Section 7 (Alternative D estimator).
7. Whether another real-SFM Run 4 is justified: **no** — this task's finding is that current semantics intrinsically exceed the gate for this shape; a repeat real-SFM run would not change that conclusion. The next real-SFM-relevant step would come only after a narrower-admission estimator is designed and implemented (out of scope here).
8. ✅ Frozen identities — Section 8, all unchanged.
9. ✅ Status: **`B2F1E CURRENT SEMANTICS REQUIRE >32 MiB FOR FAMILY C — NARROWER ADMISSION REQUIRED`**

## Hard stop

Run 5 is not requested. B2C/B2D are not begun. No production/frozen code was altered.
