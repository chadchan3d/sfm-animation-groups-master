# R3-B2F1F Stage F5: Production-Candidate Pre-Admission Integration — Report

**Authorization:** `SFM_CGN_R3_B2F1F_F5_ProductionCandidateIntegration_ClaudeCode_Prompt_2026-09-16.md`
**Status:** `B2F1F F5 PRODUCTION-CANDIDATE INTEGRATION PASS — REAL-SFM F6 AUTHORIZED`

No frozen production/provider/broker/cohort/selection/projections file was modified. No SFM was run. `git status` confirms every F5 file is untracked (`??`), nothing staged, no `git add` of any kind performed.

---

## 1. Exact current call graph, and every full-read site for the winning candidate

Read `broker.py`, `cohort.py`, `selection.py`, `sidecar_contract.py`, `view_cache.py` directly (fresh, this task). The real flow for `Broker.acquire_or_reuse_views()`:

```
acquire_or_reuse_views(master_path, request_specs, ...)
  -> observation.observe_master(master_path)              # H0 (cheap, no candidate touched)
  -> view_cache pre-check (cache hit -> return, no provider opened)
  -> acquire_cohort(master_path, missing_specs, ...)
       -> Cohort(master_path, ..., broker=self)
       -> cohort.build_projections(builder_fns)
            -> _open_provider_once()
                 -> self.h0 = observation.observe_master(...)          # H0 AGAIN (cohort-scoped)
                 -> sidecar_contract.ensure_loaded()
                 -> selection.select_sidecar_candidate(h0=self.h0, ...)
                      -> _find_matching_artifact(shipped_root, h0.sha256, cap)
                           for each *.sfmsidecar in shipped_root:
                             -> sidecar_contract.validate_selected_artifact(candidate, ...)   # READ #1
                                  -> BoundedProvider.open_path(...)      # full bounded read + validate
                                  -> _sha256_of_file(artifact_path)      # READ #2 (separate, unbounded, chunked)
                                  -> provider.close()
                             (first match wins; non-matching candidates are read once each, then discarded)
                      -> identity = sidecar_contract.validate_selected_artifact(shipped_path, h0.sha256, cap)
                           -> BoundedProvider.open_path(...)             # READ #3 (SAME winning path, AGAIN)
                           -> _sha256_of_file(artifact_path)              # READ #4 (SAME winning path, AGAIN)
                           -> provider.close()
                      -> return SelectionResult(identity, source_kind, artifact_path)
                 -> provider = BoundedProvider.open_path(selection_result.artifact_path, h0.sha256, cap)  # READ #5
                 -> self._provider = provider; broker._on_provider_opened(...)
            -> for each builder_fn: payload, coverage, estimated_bytes = builder_fn(provider)
            -> H1 check, DetachedView construction
            -> finally: self._close_provider()                          # provider.close()
       -> for each detached view: ledger.charge(...); view_cache.admit(view)   # exact post-build retained gate, HERE
```

**The winning candidate is fully opened and fully read FIVE times before this task's changes** — not the "double read" this whole B2F1x arc had assumed up to F3. `sidecar_contract.validate_selected_artifact()` alone does **two** full reads internally (`BoundedProvider.open_path`'s bounded read, **plus** a completely separate `_sha256_of_file(artifact_path)` chunked disk re-read purely to compute `sidecar_artifact_sha256` for the identity object) — and that function is called **twice** for the winning candidate (once inside `_find_matching_artifact`'s own match-check, once again immediately after by `select_sidecar_candidate` itself, just to obtain the identity), for 4 reads, plus `_open_provider_once`'s own separate `BoundedProvider.open_path` call for a 5th.

**F3 alone would not have fixed this.** Wiring F3's `candidate_open_path_with_preflight` in naively at only the `_open_provider_once` call site (read #5) would still let reads #1–#4 fully open and validate the artifact *before* the preflight ever runs — exactly the risk this task's own authorization called out ("must not accidentally retain an earlier full validation/read in `selection.py`"). The fix has to collapse **all five** sites into one.

## 2/3. Integration architecture and seam chosen

**Chosen seam: `selection.py` + `cohort.py` together, not `provider.py` alone.** A single new primitive, `candidate_open_and_identify_with_preflight()` (`preflight_gate_f5.py`), does exactly what the design requires per candidate scanned: one `open()`, `fstat` for raw-cap admission, a ≤360-byte preflight read, the `b2f1f-v1` estimator, and — only if admitted — one `seek(0)` + one bounded full read + one call into the **existing, unmodified** `BoundedProvider._open_from_buf` (hence the exact same `candidate_packed_validator.validate_packed`). It returns `(provider, identity)` with the provider **left open**, ownership transferred to the caller. `sidecar_artifact_sha256` is computed via `hashlib.sha256(data)` on the **already-read in-memory buffer** — mathematically identical to the original's `_sha256_of_file(path)` disk re-read, eliminating that redundant read entirely with zero behavioral change.

`selection_f5.py`'s scan loop (`_find_and_open_matching_artifact_f5`) calls this ONE primitive per candidate file — a non-matching/refused candidate is closed immediately (never leaked); the winning candidate's open provider is returned directly, never reopened. `cohort_f5.py`'s `_open_provider_once` calls this selection function directly and uses its returned provider as-is — no second `BoundedProvider.open_path` call anywhere in the candidate path. Every other line of `Cohort.build_projections` (builder loop, H1 check, `DetachedView` construction, `finally: self._close_provider()`) is **byte-for-byte unchanged** from the frozen original. `broker_f5.py` mirrors `acquire_cohort`/`acquire_or_reuse_views`/counters/ledger methods exactly, importing the **real, unmodified** `memory_accounting`/`view_cache` modules — the exact post-build `AggregateLedger` retained gate (`view_cache.admit()`) is untouched and still runs after every successful build, exactly where it always has.

No second authored authority, no new exception types, no silent TXT fallback: confirmed by construction (every error class raised — `SidecarMissing`, `ResourceAdmissionRefusal`, `SidecarCorrupt`, `SourceGenerationMismatch`, `AuthorityChangedDuringAcquisition`, `AuthorityBusy` — is imported from the real `sfm_master_authority.errors` module, passed in as a parameter, never redefined).

## Handle ownership / close-path table

| Stage | Owner | Close path |
|---|---|---|
| Non-matching/refused candidate during scan | `_find_and_open_matching_artifact_f5`'s own local scope | Closed inside `candidate_open_and_identify_with_preflight`'s own `finally: f.close()` before the function even returns to the scan loop — never escapes |
| Winning candidate's file handle (`open(path,"rb")`) | `candidate_open_and_identify_with_preflight`'s local `f` | Closed in its own `finally: f.close()` immediately after the bounded read — **before** `_open_from_buf` is even called; only the in-memory `data` buffer crosses that boundary |
| Winning candidate's `BoundedProvider` object | `Cohort._provider` (from `_open_provider_once()` onward) | `Cohort._close_provider()`, called unconditionally in `build_projections`'s `finally:` — identical to the frozen original |

No long-lived handle leaks into `Broker`/`BrokerF5` state at any point — `BrokerF5` only ever holds `_ledger`/`_view_cache`/counters, never a provider or file handle, matching the frozen `Broker`'s own documented invariant.

## 4. Error semantics — preserved exactly

All six required classifications verified directly (Section 5 tests, 83/83 PASS): `SidecarMissing` (missing/stale/single-unusable-candidate), `ResourceAdmissionRefusal` (`artifact_bytes` / `estimated_retained` / `estimated_transient` reasons, never collapsed into `SidecarMissing` — the earlier B2F correction, re-verified), `SidecarCorrupt` (malformed/corrupt), incompatibility (unsupported format version), `SourceGenerationMismatch` (embedded-hash mismatch). No TXT fallback anywhere (none of the candidate files reference a TXT path at all).

## 5. Race and generation-check probes

Three probes, all PASS:
1. **Pathname replacement after preflight**: the admitted candidate's reported `artifact_identity.sidecar_artifact_sha256` matches the originally-staged file's real hash — impossible for it to silently switch, since this integration never opens a second path for one acquisition.
2. **Same-path in-place overwrite after preflight**: reproduces F3's own nuanced finding — post-mutation bytes are still reliably rejected by the existing, unmodified `expected_source_sha256` check inside `_open_from_buf`. F5 does not weaken or bypass this in any way (same exception classes, same comparison, unchanged).
3. **H0/H1 Master mutation**: `CohortF5.build_projections` contains the identical `H1 != H0` / `H1 != embedded_source_sha256` → `AuthorityChangedDuringAcquisition` checks as the frozen `Cohort`, verified by direct source comparison (not reproduced as a live probe, since that would require a builder-side-effect Master mutation mid-acquisition — out of scope for an offline harness; stated explicitly rather than silently skipped).

## 6. Candidate-only implementation

All four candidate files live under `tests/sidecar/qualification/candidate_b2f1f_f5/`:

| File | SHA-256 |
|---|---|
| `preflight_gate_f5.py` | `679e723a277591a7df7c952d2085cd988f6e9f8ff2f573229060ae9782621f67` |
| `selection_f5.py` | `4bded523f63438845bdb6dc9616a36de876c35d10a83ef72095708ec58207de6` |
| `cohort_f5.py` | `48a401bd5072a8026b86dde30c93fa105f956f53b68e33f1ded9931e88e89931` |
| `broker_f5.py` | `fff4f23b0a63fe6ca483a9a7b246a507fece3afb06fddae5fb978a48650397ca` |
| `b2f1f_f5_test_driver.py` (test-only, `tests/sidecar/qualification/`) | `510175857cb91587b491a0f61075e575424fd88a479c931d56ce6566d1a12df2` |

Exact patch/diff against the current frozen package: `diff_selection.patch`, `diff_cohort.patch`, `diff_broker.patch` (all under `candidate_b2f1f_f5/`) — full unified diffs, generated directly with `diff -u` against the actual frozen files. No `git add .`/`git add -A` used anywhere; `git status` confirms every new file is untracked.

## 7. Full fixture/error disposition matrix

| Fixture | Outcome | Matches expected |
|---|---|---|
| official_control | accepted | ✅ |
| fixtureA_1p5x | accepted | ✅ |
| fixtureB_1p5x | accepted | ✅ |
| fixtureC_1p0x | refused | ✅ (preflight) |
| fixtureC_1p25x | refused | ✅ (preflight) |
| fixtureC_1p5x | refused | ✅ (preflight) |
| fixtureC_2p0x | refused | ✅ (raw-cap) |

All three admitted fixtures: provider opens==closes==1 (balanced). All three preflight-refused Family C fixtures: 0 provider opens reach the broker counters at all (refused entirely inside the preflight primitive, before any `Cohort`/`Broker` bookkeeping), all 8 ledger categories zero.

Adversarial matrix (17 checks, all PASS): bad magic, unsupported format version, malformed directory containment (each checked at **both** the low-level primitive — correct distinct classification — and the scan-integrated level — verified, not assumed, to produce the exact same `SidecarMissing` result the **frozen** path independently produces in the identical single-corrupt-candidate scenario), source-generation mismatch, exact retained/transient boundary comparisons (`>` operator, at-gate admits / gate+1 refuses, both gates), an integer/overflow probe, a corrupt-payload-beyond-preflight-region case (using an admitted-shape fixture specifically, so the low-level classification genuinely proves full validation — not resource refusal — caught it), candidate-absent, and candidate-stale.

Full row data: `b2f1f_f5_fixture_matrix.json`.

## 8. Admitted-path exact semantic equivalence

For official/A/B, compared the candidate's output against a **fresh, unmodified `Broker`** running the exact same request — not count equality, full structural equality:
- `semantic_generation.master_sha256` — identical
- `artifact_identity.embedded_source_sha256` — identical
- `artifact_identity.sidecar_artifact_sha256` — identical (proving the in-memory hash computation is mathematically equivalent to the original's disk re-read)
- Normalizer payload `groups`, `metadata_by_path`, `lookup_results`, `wrapper_path` — identical
- Normalizer `estimated_bytes` — identical
- CSP payload `lookup_results` — identical
- `cache_key()` — identical (cache-key semantics preserved)
- Provider counters, `retained_detached_views` ledger charge, `view_cache_entry_count` — identical between candidate and frozen

## 9. Refusal-path proof (C_1p25x)

Exact instrumentation match to F4's real-SFM result: `ResourceAdmissionRefusal` raised, message contains the exact `22561448`-byte retained estimate (no estimator revision — `b2f1f-v1` unchanged), broker provider counters all zero, `view_cache_entry_count == 0`, all 8 ledger categories zero.

## 10. Aggregate memory accounting

Untouched: `broker_f5.py` imports the real `memory_accounting`/`view_cache` modules directly and calls `view_cache.admit()` at the identical point in the flow the frozen `Broker.acquire_cohort` does. Preflight estimates are gates on whether construction is even attempted — they never substitute for or bypass the exact post-build ledger check, confirmed structurally (same call, same module) and behaviorally (Section 8's equivalence results).

## 11. Test suite totals — all under both interpreters, reported separately

| Suite | Python 3.10 | Real Python 2.7.5 |
|---|---|---|
| F1/F2 estimator qualification (no underestimate) | `False` (PASS) | `False` (PASS) |
| F1/F2 monotonicity/boundary | 20/20 | 20/20 |
| F3 same-handle integration | 47/47 | 47/47 |
| **F5 integrated-candidate suite (this task)** | **83/83** | **83/83** |
| B2A regression | 38/38 | 38/38 |
| B2B regression | 64/64 | 64/64 |

No separate standalone "FINAL R3-A2B qualification suite" exists (as previously noted in F3); B2A/B2B plus this task's own extensive direct exercise of `BoundedProvider._open_from_buf`/`candidate_packed_validator.validate_packed` across 7 fixtures and 17 adversarial cases remain the practical equivalent.

## 12. Performance sanity

| Fixture | Candidate elapsed | Frozen elapsed | Speedup |
|---|---|---|---|
| official_control (Python 3.10) | 0.569 s | 1.549 s | 2.7x faster |
| fixtureA_1p5x (Python 3.10) | 0.185 s | 0.505 s | 2.7x faster |
| fixtureB_1p5x (Python 3.10) | 0.819 s | 2.448 s | 3.0x faster |
| official_control (real Python 2.7.5) | 1.361 s | 3.804 s | 2.8x faster |
| fixtureA_1p5x (real Python 2.7.5) | 0.583 s | 1.467 s | 2.5x faster |
| fixtureB_1p5x (real Python 2.7.5) | 2.039 s | 5.713 s | 2.8x faster |

**The candidate is genuinely and consistently faster, not just no-worse** — directly confirming the Section 1 finding (five reads collapsed to one). The 360-byte preflight itself is negligible; no second full read or substantial overhead was introduced anywhere.

## 13. Frozen identity table — before and after F5

| File | SHA-256 | Status |
|---|---|---|
| Canonical Master | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | unchanged |
| Official sidecar artifact | `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` | unchanged |
| FINAL R3-A2B validator | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` | unchanged |
| FINAL R3-A2B provider | `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677` | unchanged |
| Production Normalizer | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` | unchanged |
| `sfm_master_authority/selection.py` | `946791edb172dcc295d1cd8c161db1be68a138e255a7ecb313afb2fee9d85abd` | unchanged |
| `sfm_master_authority/cohort.py` | `50e686c34b498f4213103e9e2bc0c41734b9d78874141457bffbed0610f85387` | unchanged |
| `sfm_master_authority/projections.py` | `7dd25ff7104730cef357a6710e3d56e098b7de216eb306527dad2b09c9f0b31a` | unchanged |
| `sfm_master_authority/broker.py` (newly recorded this task) | `d2e66251fe26165976829456eba3ae7fa2420527e41092179d94a401f56dd8b9` | unchanged (matches the original full-package hash dump from earlier in this session) |

Verified identically both before this task's work began and again after all candidate files/tests were built and run.

## 14. Estimator version decision

**No revision.** `b2f1f-v1` is used unchanged throughout; F5's own tests confirm the exact `22,561,448`-byte C_1p25x retained estimate and `52,997,877`-byte transient estimate are still produced identically through the new integration path.

## 15. Status

**`B2F1F F5 PRODUCTION-CANDIDATE INTEGRATION PASS — REAL-SFM F6 AUTHORIZED`**

---

## F6 design (prepared, NOT run)

Per this authorization's own terms: prepare but do not run, and do not create operator instructions yet unless explicitly asked after this report's review.

**Objective:** verify in real SFM, with the genuine external sampler, that the F5 candidate integration (`broker_f5.BrokerF5` + `cohort_f5`/`selection_f5`/`preflight_gate_f5`) behaves in real SFM exactly as it does offline, for:

1. **One admitted integrated-candidate path** — e.g. `fixtureA_1p5x` or `fixtureB_1p5x` through `BrokerF5.acquire_or_reuse_views`, confirming real-SFM transient/retained deltas are consistent with (and, per Section 12's measured speedup, likely smaller than) the already-qualified frozen-path numbers from Runs 2–4.
2. **One early-refused integrated-candidate path** — `fixtureC_1p25x`, mirroring F4's exact real-SFM proof (refusal before expensive acquisition, ≤32 MiB transient, no published view) but through `BrokerF5` instead of the raw F3 primitive directly — the meaningful new thing F6 adds is exercising the **full** `Broker`/`Cohort`/`selection` orchestration layer in real SFM, not just the innermost preflight primitive F4 already proved.
3. Genuine external sampler (`gate2a_external_sampler.py`, unmodified, same PID-discovery wrapper pattern as B2F1A–D/F4).
4. Memory gates: ≤32 MiB transient, ≤16 MiB retained, exactly as established throughout this arc.
5. Exact outcome/error semantics matching what this report's offline suite already proved.

**Candidate files to prepare (not created yet):** two Main Menu launchers (admitted case + refused case) following the exact module-scope/`sys.executable`-derived/`imp.load_source` pattern used throughout B2F1A–F, each calling `BrokerF5.acquire_or_reuse_views` (loaded via `imp.load_source` from `candidate_b2f1f_f5/`) instead of the frozen `Broker`; one external sampler wrapper reusing the established pattern with new unique output names.

**Not begun. No operator instructions given. Awaiting explicit go-ahead after this report is reviewed.**
