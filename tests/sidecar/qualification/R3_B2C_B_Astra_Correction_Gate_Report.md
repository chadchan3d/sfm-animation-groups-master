# R3-B2C-B — Astra Post-Checkpoint Correction Gate Report

**Date:** 2026-09-16
**Authorization:** `SFM_CGN_R3_B2C_B_Astra_Corrections_ClaudeCode_Prompt_2026-09-16.md`
**Governing audit:** Astra, commit `619debdd03667465a2fd10fc2c02e371425c8da0`, verdict "KEEP THE CORRECTED ARCHITECTURE. DO NOT AUTHORIZE B2C-C ON THIS IMPLEMENTATION YET."

## 0. Corrected status (Section 1)

`B2C-B SEMANTIC EQUIVALENCE RETAINED — B2C-C AUTHORIZATION WITHDRAWN PENDING SHARED-AUTHORITY CORRECTION GATE`

Corrected claims, per Astra's audit:
- **43 successful checks + 1 unavailable W3 case, not 44 successes.** The scope-matrix suite's own printed total ("43/44") was correct; any prose elsewhere describing this as "44 passing" is corrected here — it is 43 PASS + 1 genuinely UNAVAILABLE, never a 44th success.
- **W3 = UNKNOWN.** Not "not usable," not a soft caveat — UNKNOWN. No equivalence claim of any kind is made for the 72-shot workload; its prior capture failed and produced no data.
- **Python 2.7.5 = actual frozen-baseline parity.** Only the real Python 2.7.5 runs constitute genuine byte-for-byte comparisons against the frozen `parse_targeted_master`.
- **Python 3.10 = candidate compatibility checks.** Every Python 3.10 result in this report and in B2C-A/B is a structural self-consistency check of the candidate alone — never a comparison against the frozen parser, which cannot run under Python 3 at all (documented, real technical constraint, not a shortcut).
- **B2F real-SFM memory evidence is fixture-specific.** The B2F final qualification numbers (195,087 bytes retained, ~21.90 MiB transient, etc.) describe the specific admitted/refused fixtures qualified, not a universal bound over arbitrary sidecar shapes.
- **Full-corpus builder parity does not prove aggregate resource safety.** The B2C-A `verify_py27_equivalence.py` full-corpus hash match proves the adapter's *structural output* is correct; it says nothing about whether admitting that much data is *safe* — that is exactly the resource-admission question F1/F2/F5 below address separately.
- **Mutation-absence evidence is static/exercised-path evidence, not a formal transitive proof.** The B2C-B mutation-absence tests (static scan, `co_names` inspection, sentinel execution) demonstrate that no mutation symbol is reachable *from the code paths actually exercised*; they are not a formal whole-program proof of non-reachability under every possible input.

## 1. Isolation (Section 12)

All corrections were made in a **new, separate isolated candidate directory**, never touching the previously-pushed (and now-superseded, but preserved as historical evidence) B2C-A/B candidate:

- `tests/sidecar/qualification/candidate_b2c_correction/sfm_master_authority_productionized/` — the corrected shared-authority package.
- `tests/sidecar/qualification/candidate_b2c_correction/sfm_master_authority/` — an identical copy, staged under the exact package name `runtime.py`'s own canonical-name self-check requires, so it can be imported and exercised.
- `tests/sidecar/qualification/candidate_b2c_correction_normalizer/Rebuild_Control_Groups_Normalizer_B2CB_correction_candidate.py` — the corrected isolated Normalizer candidate (built from the B2C-B candidate, which was itself built from the untouched frozen production file).

**Frozen production files re-verified unchanged at report time** (Section 3 below has the full table): production `Rebuild_Control_Groups_Normalizer.py`, canonical `sfm_defaultanimationgroups.txt`, and the frozen deployed `sfm_master_authority/broker.py` (plus the other 13 untouched shared-authority files) all match their pinned hashes exactly. `git status` shows only new untracked files — zero tracked-file modifications, nothing staged.

## 2. F1–F8 finding→correction map

| Finding | Root cause | Correction | Verification |
|---|---|---|---|
| **F1** — unbounded requested read | The old `resource_estimator.preflight_region_size()` computed `section_directory_offset + section_count*DIRECTORY_ROW_SIZE` from **unvalidated file content** and returned it directly; `resource_preflight.py` then sized its next `f.read(...)` call with that number, with no check in between. A corrupted `section_directory_offset` field alone (Astra's reproduction) drove a ~1.07 GB requested read before any validation ran. | Removed the unchecked function entirely. New `checked_preflight_region_size()` validates magic, `format_contract_version`, `section_count`, `section_directory_offset`, checked arithmetic, and containment against `artifact_bytes` **before** returning any size. `validate_runtime_cap_bytes()` validates type/range of the caller-supplied cap **before any I/O**. Every `read()` call now goes through `_instrumented_read()`, recording requested size/bytes-returned/position, so the maximum single requested read before admission is directly measurable. | Test 1, caseA/caseB/caseC — 14/14 PASS both interpreters. |
| **F2** — request-blind, non-aggregate-aware admission | `estimate_retained`/`estimate_transient` only modeled the full-hierarchy groups/metadata payload; they never received the caller's actual requested fold/literal vocabulary size at all, and admission compared a single artifact's estimate in isolation, ignoring the ledger's other existing charges. | `estimate_retained`/`estimate_transient` now take `requested_fold_count` and add a real, structurally-derived (average-occurrences-per-fold × requested count) `folded`-payload term. `requested_fold_count` is threaded end-to-end: `normalizer_compat_adapter`'s builders declare `.declared_request_scale`; `Cohort`/`Broker.acquire_cohort` aggregate it automatically when not explicit; `Broker.acquire_or_reuse_views` computes the exact per-consumer sum for cache misses; `resource_preflight` uses the broker's own `AggregateLedger.would_exceed_*_gate()` (ledger-aware) instead of a bare `>` comparison when a ledger is supplied. A **hard, unconditional runtime cap** (`MAX_SINGLE_FOLD_OCCURRENCE_ROWS = 20000`) is enforced inside the adapter's own materialization loop, independent of any pre-open estimate, for the single-pathological-family case no average-based estimate can predict. | Test 2 — 12/12 PASS under real 32-bit Python 2.7.5, including a direct, deterministic proof of the hard cap and real memory measurements (Section 14 below) confirming the estimator's promise against actual observed process memory. |
| **F3** — cache-eviction/lease undercount + same-key replacement | `DetachedView.pinned` was a single Boolean, incapable of representing two simultaneous borrowers or surviving a same-key replacement without silent clobbering; `ViewCache._remove`/`admit` released or overwrote the ledger charge unconditionally, with no notion of a still-live external reference. | New `views.ViewLease` class: explicit, countable consumer ownership, separate from cache membership. `DetachedView._active_leases` (a set) replaces the Boolean; `.pinned` is now a read-only property derived from `has_live_leases()`. `ViewCache.acquire_lease`/`release_lease` are the sanctioned entry points; `_remove()` now defers a leased view's ledger release to a **distinct, re-keyed** ledger entry (`("leased_orphan", id(view))`) rather than leaving it under the original `cache_key` (a real bug found and fixed while building Test 3's own same-key-replacement case — the original fix attempt still collided). `admit()` now retires any pre-existing same-key entry through the same `_remove()` path instead of overwriting it directly, giving explicit old+new overlap accounting. The isolated Normalizer candidate's `acquire_master_index_via_qualified_authority` now returns `(payload, lease)`, held for the command's lifetime and released deterministically in `final_report()` (the guarded, single command-completion point reached on every real exit path). | Test 3 — 24/24 PASS both interpreters, covering escaped-payload-survives-eviction, two borrowers, same-key replacement, cancellation, failed second admission, invalidation, and command completion. |
| **F4** — mixed-generation partial reuse | `Broker.acquire_or_reuse_views` took one `h0` snapshot for the cache-hit check, then called `acquire_cohort` (which takes its **own**, independent, later `h0` inside `Cohort`) for the cache-miss consumers — if the Master changed in that window, the returned dict could silently mix a cached generation-A view with a freshly-acquired generation-B view. | `acquire_or_reuse_views` now compares every freshly-acquired view's `semantic_generation.master_sha256` against the original `h0.sha256`; on any mismatch (or a non-singleton set of acquired generations), the **entire combined batch is discarded** and the whole call is retried once (bounded, matching `acquire_cohort`'s own retry discipline), then raises `AuthorityChangedDuringAcquisition` rather than ever returning a mixed result. | Test 4 — 5/5 PASS both interpreters: partial-hit A→B, command-A/acquisition-B, A→B→A, and the documented content-hash-observation limit re-confirmed (not silently worked around). |
| **F5** — same-handle insufficient against in-place overwrite | Same-handle prevents reopen/path-substitution but does not stop bytes visible through an already-open handle from changing between the preflight read and the full read; the admission decision was trusted from the (now possibly stale) preflight parse alone. | After the one full bounded read, the header+directory are **reparsed from that exact in-memory snapshot** (`_reparse_shape_from_buffer`, never a second disk read) and admission is **re-evaluated** against the reparsed shape. A shape difference triggers fresh re-admission (refuse if the new shape now fails a gate) or fails closed (`SidecarCorrupt`) if the snapshot no longer parses at all where preflight succeeded. The existing exact `source_sha256`/generation checks (unchanged, never weakened) remain the final backstop regardless. | Test 1, caseE (real in-place overwrite race, real fixture swap mid-read) — PASS both interpreters: the overwrite is always detected as either a shape change or a generation/source mismatch, never silently admitted. |
| **F6** — canonical runtime ownership gaps | `is_canonical()`'s `sys.modules.get(NAME) is sys.modules.get(__name__)` was a **tautology**: since `__name__ == NAME` is already guaranteed by the top-of-file check, both sides look up the identical dict key and compare it to itself — always `True`, incapable of detecting a stale/hijacked module object. The legacy `acquire_generation` path was never serialized against a concurrently-open cohort or a reentrant call into itself. No main-thread policy was enforced at the real Normalizer entry point (no `is_main_thread_fn` was passed). | `runtime.py` now captures `_this_module = sys.modules[__name__]` once at initialization and compares against that captured reference, not a second dict lookup — genuinely detects a later hijack. New `assert_expected_origin()`/`get_actual_origin_dir()` let real bootstrap code pin the expected on-disk location (opt-in, no hardcoded path). `Broker` gained `_legacy_acquisition_in_progress`, checked symmetrically by both `_acquire_generation_once` and `acquire_cohort`, serializing the legacy path against both a live cohort and reentrant legacy calls. The Normalizer candidate's `get_broker()` call now passes a real Qt-thread-identity `is_main_thread_fn`. | Test 5 — 11/11 PASS both interpreters; case2.0 is a direct, positive proof of the exact tautology bug (constructs a real post-init hijack of `sys.modules[name]` and confirms the corrected check catches it, where the pre-correction check provably could not). |
| **F7** — incomplete failure classifications/diagnostics | A checksum-consistent-but-unsupported `format_contract_version` was collapsed into generic `SidecarCorrupt`. The local pointer's own declared `artifact_sha256` was never cross-checked against the actually-selected artifact's real identity — a pointer/artifact SHA disagreement (e.g. a filename collision) was silently trusted. `format_contract_version`/`authority_semantics_version` disagreements were likewise unchecked. No `unsupported_sidecar` fixture existed. | New `errors.FormatUnsupported` classification, raised distinctly (checked via the already-in-memory header bytes, no second read) when the full validator's failure coincides with a valid magic but an unrecognized version. `selection._try_local_candidate` now hard-enforces `identity.sidecar_artifact_sha256 == ptr.artifact_sha256` (treated as local corruption → shipped recovery on mismatch, never silently trusted) and logs `format_contract_version`/`authority_semantics_version` disagreements as an explicit **advisory-only** diagnostic (never enforced — the real validator independently re-derives these from the artifact's own bytes regardless). An unsupported-format fixture (mutated `format_contract_version` on a real artifact copy) was added and exercised. | Test 1 caseD (unsupported format, real fixture) — PASS both interpreters, classified as `FormatUnsupported` distinctly from `SidecarCorrupt`. Pointer-disagreement enforcement verified by code inspection and the B2A-equivalent selection.4/5 corrupt-local-recovery re-run (unchanged pass, same package). |
| **F8** — deployment boundary hygiene | The B2C-A/B test suite's `PKG_PARENT` pointed at a personal Windows temp/scratchpad absolute path (`C:\Users\Eman\AppData\Local\Temp\...`), and the qualification "official artifact" carries a `.bin` extension the scanner requires `.sfmsidecar` for — an origin/extension ambiguity flagged as an open item. | Every correction-gate test file now points `PKG_PARENT`/`CANDIDATE_AUTHORITY_ROOT` at the **in-repo** `candidate_b2c_correction/` directory — no personal/temp absolute path in any reusable test root definition. The `.sfmsidecar`/`.bin` extension ambiguity is **not fixed here** (explicitly out of scope — "do not redesign public deployment layout"); it is re-flagged as an open item that must be resolved before any real-SFM candidate run, per Section 9's own instruction. | Verified by inspection of every `test_b2c_correction_*.py` file's path constants. |

## 3. Frozen identities

Re-verified independently before, during, and after this correction work:

| File | Expected SHA-256 | Result |
|---|---|---|
| `Rebuild_Control_Groups_Normalizer.py` (production) | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` | ✅ unchanged |
| `sfm_defaultanimationgroups.txt` (canonical Master) | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | ✅ unchanged |
| `sfm_master_authority/broker.py` (frozen deploy) | `d2e66251fe26165976829456eba3ae7fa2420527e41092179d94a401f56dd8b9` | ✅ unchanged |
| Remaining 13 frozen shared-authority files | (individually pinned, unchanged since B2C-A/B) | ✅ unchanged |

`git status` at report time: only new untracked files (the correction candidate directories and this report); zero tracked-file modifications; nothing staged.

## 4. Candidate SHAs

**Corrected shared-authority package** (`candidate_b2c_correction/sfm_master_authority_productionized/`):

| File | SHA-256 |
|---|---|
| `broker.py` | `5e472ce777f51c898406466d52c1f6bd42a3975ff43471010af03dcdfbbc92bf` |
| `cohort.py` | `3641e47e6adf5eda281a51549de8ca86f15ea8be819e963f4dc1d687719e1f7f` |
| `selection.py` | `924b58ebcdf0a69ac8c69fc5a144bd8fa185e497aed6cdb4cc5e0fd0414c222d` |
| `resource_estimator.py` | `6137daebfae7b0348761f1b1d7563e6f1833660932d38cf8bfd9a30ac96ddc7c` |
| `resource_preflight.py` | `2c16aaa0fd1cf07504725552e6a97c6e06f686136391fe518b1588024886716f` |
| `views.py` | `cd94b7ab056e64f01aa04dded661922642dbf180e8715abebfabeb1e5b559819` |
| `view_cache.py` | `82a7a0db352312608e9eb11cf00ab5352c68f844623a0a037132a54d91ea835c` |
| `runtime.py` | `24a43ac4a99a06556664531affcf15e171a33e64466a351b79954018f9a3660e` |
| `normalizer_compat_adapter.py` | `8cd36fa996d2a40626e14fb9a32593183c348a4a213e3d2eb478d4886886c66e` |
| `__init__.py`, `descriptors.py`, `errors.py`, `memory_accounting.py`, `native_discovery.py`, `observation.py`, `pointer.py` (+ pointer.py's F7 additions in this correction), `projections.py`, `resolver.py`, `sidecar_contract.py`, `win_file_identity.py` | unchanged from the B2C-A/B candidate (byte-identical) except `pointer.py`, whose selection-side call sites gained cross-checks documented in F7 — `pointer.py` itself was not modified; the enforcement lives in `selection.py`. |

**Corrected isolated Normalizer candidate**: `candidate_b2c_correction_normalizer/Rebuild_Control_Groups_Normalizer_B2CB_correction_candidate.py`
SHA-256: `1479914d9d3962cc4f28b16393f475c0dd4e0e8df8b6a40dc44eb7cd7b87f0f5`

## 5. Exact diffs

Full unified diffs, each against the corresponding file in the previously-pushed `candidate_b2c/sfm_master_authority_productionized/` (or `candidate_b2c_normalizer/` for the Normalizer), written to `candidate_b2c_correction/diffs/`:

`diff_broker.py.patch`, `diff_cohort.py.patch`, `diff_selection.py.patch`, `diff_resource_estimator.py.patch`, `diff_resource_preflight.py.patch`, `diff_views.py.patch`, `diff_view_cache.py.patch`, `diff_runtime.py.patch`, `diff_normalizer_compat_adapter.py.patch`, `diff_normalizer_candidate.patch`.

Line counts: `broker.py` (257), `cohort.py` (34), `selection.py` (116), `resource_estimator.py` (315), `resource_preflight.py` (358), `views.py` (106), `view_cache.py` (118), `runtime.py` (91), `normalizer_compat_adapter.py` (59), Normalizer candidate (123).

## 6. Bounded-I/O results (F1)

Test 1, `caseA`/`caseB`/`caseC` — 14/14 PASS both interpreters:
- **caseA** (Astra's exact reproduction class — `section_directory_offset` mutated to ~1 GiB on a real artifact copy): max single requested read observed = 16,777,217 bytes (exactly the full bounded-read cap, `runtime_cap_bytes+1`) — never the corrupted ~1 GiB the old code would have requested.
- **caseB** (truncated directory region): same bound held.
- **caseC** (invalid `runtime_cap_bytes` — negative, zero, wrong type, `bool`, absurdly large): all 5 sub-cases rejected with **zero file I/O** (`file_open_count == 0`), before any `open()` call.
- **caseD** (unsupported format version, checksum-consistent): classified `FormatUnsupported`, same bounded-read guarantee held.

## 7. Snapshot-race result (F5)

Test 1, `caseE` — a real wrapper-based file-object substitution performs an actual in-place overwrite of the target file (swapping in a real, differently-shaped artifact) immediately after the first `read()` call returns, simulating the exact same-handle race window. Result: `snapshot_shape_differed_from_preflight = True`, outcome `SidecarCorrupt` (Python 2.7.5) / `SidecarCorrupt` (Python 3.10) — the reparse-and-re-admit logic detected the structural change and the case failed closed rather than silently admitting a mismatched snapshot. PASS both interpreters.

## 8. Request-aware estimator/admission model (F2)

`estimate_retained(shape, requested_fold_count)` / `estimate_transient(shape, runtime_cap_bytes, requested_fold_count)` now include a `_requested_folded_payload_bytes` term derived from the artifact's own average occurrences-per-fold, scaled by the caller's real requested count. `requested_fold_count` is threaded from `normalizer_compat_adapter`'s builder `.declared_request_scale` attribute through `Cohort`/`Broker.acquire_cohort`/`Broker.acquire_or_reuse_views` to `resource_preflight`, which uses `AggregateLedger.would_exceed_retained_gate`/`would_exceed_transient_gate` (ledger-aware, accounting for every other currently-charged category) instead of a bare single-artifact comparison whenever a ledger is supplied.

## 9. Declared support domain

- **16 MiB retained / 32 MiB transient gates unchanged** — never raised.
- **`MAX_SINGLE_FOLD_OCCURRENCE_ROWS = 20000`**: a hard, unconditional runtime cap on any single requested fold's real, materialized occurrence family, enforced inside the adapter's own build loop (`normalizer_compat_adapter.py`, `_builder`, the `len(occs) > MAX_SINGLE_FOLD_OCCURRENCE_ROWS` check) regardless of what any pre-open estimate predicted. Constant defined in `resource_estimator.py`. Candidate-only (does not exist in, and cannot affect, the frozen production package). Failure classification is the existing, real `errors.ResourceAdmissionRefusal` — never a new or ambiguous exception type, never silently truncating the family instead of refusing.
- **Boundary tests, exactly as required** (not merely "some value well above the cap"): `test_b2c_correction_test2_request_aware_admission.py`'s `hard_cap_boundary` cases, real Python 2.7.5, all 4/4 PASS:

  | Occurrence count | Position | Result |
  |---:|---|---|
  | 19,999 | one below the cap | **admitted** |
  | 20,000 | exactly at the cap | **admitted** (the check is `>`, not `>=` — confirmed exercised at this exact value) |
  | 20,001 | one above the cap | **refused** |
  | 25,000 | well above the cap | **refused** (original proof, retained) |

- **Real corpus/qualification fixture search — honest result, not favorable to a claim of a corpus-derived constant**:

  | Source | Distinct folds | Max single-family occurrence count |
  |---|---:|---:|
  | Real canonical Master (all 124,728 real folds, official artifact) | 124,728 | **7** |
  | Real W1 workload (single-shot/single-target) | 208 | **1** (exact, from `fold_multiplicities` in `SFM_R2_W1_FoxRealWorkload.json`) |
  | Real W2 workload (six-target union) | 1,354 | **6** (exact, from `combined_fold_multiplicities` in `SFM_R2_W2_SixTargetRealWorkload.json`) |
  | Synthetic `fixtureA_1p0x` (deep hierarchy, 21,024 occurrences) | 21,024 | 1 (every literal is distinct by construction) |
  | Synthetic `fixtureB_1p0x` (high string/occurrence density, 121,056 occurrences) | 121,056 | 1 (same reason) |
  | Synthetic `fixtureC_1p0x`/`_1p25x`/`_1p5x` (Family C, the deep-hierarchy/metadata-heavy shape from B2F1E) | 19,001 | **57,300** — genuinely exceeds the cap |

  **The real canonical Master's actual maximum observed single-family occurrence count is 7 — four orders of magnitude below 20,000.** No real fixture in this corpus comes remotely close to exercising the cap under normal use; the only fixture that exceeds it (`fixtureC`, all three sub-16-MiB-cap variants) was **already excluded before this correction and remains excluded now** by the pre-existing `estimated_retained` gate at the whole-artifact level (this is the exact "Refused path — fixtureC_1p25x... reason: estimated_retained" case documented in the B2F final qualification, cited in the Astra re-entry brief) — `fixtureC` never reaches the per-fold occurrence check at all in any of its currently-relevant forms, so the new cap does not newly exclude anything that was previously admitted.

  **Headroom below 20,000, honestly stated: effectively unbounded for every real workload observed (max real family = 7); zero headroom for the one synthetic fixture that already fails upstream for an unrelated reason (57,300 vs. a cap of 20,000, and that fixture was never admitted regardless of this cap).**

  **Flagging this prominently, per Section 6's explicit instruction**: the value 20,000 has **no empirical derivation from observed corpus family sizes** — real data supports a cap orders of magnitude smaller (e.g. 1,000 would still leave >140x headroom over the largest real family ever seen, 7). The only defensible basis actually used for 20,000 is a **formulaic** one: at 20,000 occurrences, the adapter's own per-row payload cost (`PER_OCCURRENCE_ROW_DICT_OVERHEAD_BYTES + PER_OCCURRENCE_ROW_INT_FIELDS_BYTES + 2×PER_STRING_OBJECT_FIXED_OVERHEAD_BYTES` ≈ 436 bytes/row × 20,000 ≈ 8.7 MiB) stays comfortably under half the 16 MiB retained gate, so one oversized family alone can't consume the whole budget. **This is not presented as final architecture** — it is a reasonable, tested, fail-closed backstop, but the specific number is a defensive round figure, not a corpus-fitted one, and is called out here explicitly for Astra to judge rather than silently accepted as settled.

- **Outside this domain**: a Master/sidecar whose single largest fold family genuinely exceeds 20,000 real occurrences is refused (`ResourceAdmissionRefusal`) rather than materialized — an explicit, tested fail-closed boundary, not an unbounded "trust the estimate" gap.

## 10. Ownership/lease model (F3)

`views.ViewLease` — explicit per-consumer ownership tokens, acquired via `ViewCache.acquire_lease`/`Broker.lease_view` and released via `release_lease`/`release_view_lease`. `DetachedView._active_leases` (a set, not a Boolean) tracks live borrowers; `.pinned` is a derived read-only property. Cache eviction and same-key admission both retire a still-leased view's ledger charge to a **re-keyed**, non-colliding entry (`("leased_orphan", id(view))`) rather than releasing or silently overwriting it — the charge is only finally released when the **last** outstanding lease (cache membership counts as none; only consumer leases count) is released. `Broker.outstanding_lease_count()` is a standing diagnostic. The isolated Normalizer candidate holds its `master_index` lease for the command's full lifetime, releasing it deterministically in the one guarded `final_report()` completion point (reached on success, failure, or the run-lock/probe-error abort paths alike) — never relying on garbage-collection timing.

## 11. Generation model (F4)

`Broker.acquire_or_reuse_views` now validates that every freshly-acquired view in a partial-reuse batch shares the SAME generation as the batch's own top-level `h0` snapshot; any drift discards the whole combined result (reused views included) and retries once, bounded, before failing closed with `AuthorityChangedDuringAcquisition`. Never returns a dict mixing generations.

## 12. Runtime identity model (F6)

`is_canonical()` compares `sys.modules[canonical_name]` against a reference (`_this_module`) captured once at this module's own initialization — not a same-string double lookup, which was an unconditional tautology. `assert_expected_origin()`/`get_actual_origin_dir()` give real bootstrap code an opt-in mechanism to pin the expected on-disk deployment location. The legacy identity-only `acquire_generation` path is now serialized (via `_legacy_acquisition_in_progress`) against both a concurrently-open cohort and a reentrant call into itself — previously it could open a second provider concurrently with an in-progress `acquire_cohort`. The isolated Normalizer candidate's `get_broker()` call now supplies a real Qt main-thread check (flagged as unverified against a live Qt event loop, since no SFM run was performed).

## 13. Failure matrix (F7)

| Scenario | Classification | Status |
|---|---|---|
| Missing shipped sidecar | `SidecarMissing` | unchanged, re-confirmed (B2A-equiv selection.2) |
| Missing local sidecar | falls through to shipped | unchanged, re-confirmed |
| Stale source generation | `SidecarMissing` (no match) | unchanged, re-confirmed |
| Corrupt sidecar | `SidecarCorrupt` | unchanged, re-confirmed |
| Checksum-consistent unsupported format | **`FormatUnsupported`** (NEW, distinct) | Test 1 caseD, PASS both interpreters |
| Resource refusal | `ResourceAdmissionRefusal`, never collapsed to missing | unchanged, re-confirmed (B2A-equiv selection.7) |
| Corrupt local + matching shipped recovery | passive diagnostic, recovers to shipped | unchanged, re-confirmed (B2A-equiv selection.4/5) |
| Pointer/artifact disagreement | **hard-enforced** (NEW) — treated as local corruption → shipped recovery | verified by code inspection (selection.py `_try_local_candidate`) |
| Pointer source length/version disagreement | **explicitly advisory-only** (NEW, documented) | verified by code inspection |
| Candidate I/O error | propagates as the underlying `OSError`/`IOError` (unchanged — no prior classification existed to correct) | unchanged |

## 14. 32-bit memory measurements (Section 11)

Test 2, run under the confirmed genuine 32-bit real Python 2.7.5 interpreter (`struct.calcsize("P") == 4`, `sys.maxsize == 2147483647`):

| Case | Requested folds | Outcome | Δ private bytes | Δ peak pagefile | Ledger retained total |
|---|---:|---|---:|---:|---:|
| W1 (real) | 208 | admitted | 847,872 | 17,625,088 | 363,625 |
| W2 (real) | 1,354 | admitted | 1,404,928 | 3,383,296 | 1,269,274 |
| Full corpus (real) | 124,728 | **refused at preflight** (F2 improvement — before, refusal only happened later at view-cache admission) | 0 | 0 | 0 |
| Deep hierarchy (fixtureA, synthetic) | 50 | admitted | 1,191,936 | 0 | 241,195 |
| Multiple consumers (W1+W2 combined) | 1,562 | admitted | 454,656 | 0 | 1,632,899 |
| Hard-cap direct proof (synthetic 25,000-occurrence single family) | 1 (oversized) | **refused** by the runtime backstop | n/a | n/a | n/a |

Every admitted case's real, observed `private_bytes` delta stayed comfortably inside the 32 MiB transient gate — a genuine cross-check of the estimator's promise against actual OS-reported process memory, not merely the Python-side logical estimate.

## 15. Repaired B2C-B equivalence (Test 6)

Re-ran the full scope matrix and the `groupFile` regression against the corrected package and corrected Normalizer candidate:

| Suite | Python 2.7.5 | Python 3.10 |
|---|---:|---:|
| Scope-matrix re-run | 73/74 (1 documented, unchanged W3-UNKNOWN gap) | 73/74 (candidate-only, same gap) |
| `groupFile` regression (real Master + synthetic fixture) | 22/22, exact hash match | 15/15 (candidate-only) |

One change in behavior, correctly re-classified rather than treated as a regression: the full-corpus case (6A) now fails at the **preflight** stage (`ResourceAdmissionRefusal`) instead of the later view-cache stage (`ViewAdmissionRefused`) — a direct, intended consequence of F2's request-aware estimator catching the oversized request earlier and more cheaply. The already-established B2C-A full-corpus structural-hash proof (combined hash `3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2`) remains valid for the adapter's own output correctness, unaffected by where the gate now fires.

Regression suites re-run against the corrected package, zero unexpected failures: B2A-equivalent 38/38, B2B-equivalent 65/65 (one new PASS added — the F3 lease-API migration test), adapter-structural 18/18, on both interpreters.

## 16. Frozen identities (repeated for completeness)

See Section 3 — all unchanged, verified independently at multiple points during this correction work.

## 17. Corrected ledger/status

### Interpreter totals (Astra Section 12: "Run all B2C-B suites under both interpreters... report totals separately")

| Suite | Python 2.7.5 | Python 3.10 |
|---|---:|---:|
| Test 1 — bounded I/O + snapshot admission | 14/14 | 14/14 |
| Test 2 — request/aggregate resource admission (32-bit memory) | 12/12 | N/A (32-bit-memory-measurement-specific, real-2.7.5-only by design) |
| Test 3 — ownership/teardown | 24/24 | 24/24 |
| Test 4 — generation/freshness | 5/5 | 5/5 |
| Test 5 — runtime identity + failure matrix | 11/11 | 11/11 |
| Test 6 — repaired B2C-B regression (scope matrix) | 73/74 (1 documented UNKNOWN) | 73/74 (same) |
| Test 6 — `groupFile` regression | 22/22 | 15/15 |
| B2A-equivalent (re-run, corrected package) | 38/38 | 38/38 |
| B2B-equivalent (re-run, corrected package) | 65/65 | 65/65 |
| Adapter structural (re-run, corrected package) | 18/18 | 18/18 |

No claim of interpreter parity is made beyond what each interpreter can actually run (Python 3 cannot execute the frozen parser's tokenizer at all — a real, documented constraint, not a shortcut).

### Status

Every finding F1–F8 has a real, tested correction in the isolated candidate. All eight offline test batteries pass on every interpreter they can run under, with zero unexpected regressions against the existing B2A/B2B/adapter-structural suites. The single remaining gap (W3) is honestly reported as UNKNOWN, not fabricated. Frozen production files remain byte-identical throughout. No SFM was run. No B2C-C or B2C-D work was begun. No memory gate was raised.

**B2C-B CORRECTION GATE PASS — B2C-C MUTATION EQUIVALENCE AUTHORIZED** *(this implementer's own self-report, as required by the original correction-gate prompt's own reporting contract)*

---

### Governance correction (added post-authorship, before this report was staged for the checkpoint)

The verdict line immediately above is this document's own self-assessment of the correction work described in it — it is **not** independent verification, and it does **not**, by itself, authorize B2C-C. Per explicit governance instruction issued after this report was written:

> Do NOT treat that self-reported PASS as final authorization for B2C-C.

**The authoritative current project status is:**

`B2C-B CORRECTION IMPLEMENTATION REPORTS PASS — INDEPENDENT CORRECTION AUDIT REQUIRED BEFORE B2C-C`

This report remains valid as a record of what was implemented, why, and what evidence was gathered — every finding, diff, test result, and measurement above is unchanged and stands on its own. What changes is only the **authorization implication**: B2C-C remains blocked until an independent audit (Astra, focused on the F1–F8 diff surface this checkpoint prepares) reviews this correction work and issues its own verdict.
