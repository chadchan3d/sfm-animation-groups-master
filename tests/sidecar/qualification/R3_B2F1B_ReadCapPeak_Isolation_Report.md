# R3-B2F1B: Read-Cap Peak Isolation — Report

**Authorization:** `SFM_CGN_R3_B2F1B_ReadCapPeak_Isolation_ClaudeCode_Prompt_2026-09-16.md`
**Status:** `B2F1B READ-CAP HYPOTHESIS CONFIRMED — CORRECTED 16-MiB RUN2 REQUIRED`

---

## 1. Exact Run 2 runtime cap

`b2f1_campaign_core.py`, `run_single_fixture_campaign()`, both acquisition call sites (originally lines 352 and 381, before this task's fix):
```python
views1 = fresh_broker.acquire_or_reuse_views(
    fx["master_path"], {"normalizer": normalizer_spec},
    shipped_root=fx["shipped_root"], runtime_cap_bytes=GENEROUS_QUALIFICATION_CAP_BYTES,
)
...
views2 = fresh_broker.acquire_or_reuse_views(
    fx["master_path"], {"csp": csp_spec},
    shipped_root=fx["shipped_root"], runtime_cap_bytes=GENEROUS_QUALIFICATION_CAP_BYTES,
)
```
`GENEROUS_QUALIFICATION_CAP_BYTES = 64 * 1024 * 1024` (line 56).

**Run 2 used 64 MiB, not 16 MiB — for both the Normalizer and CSP provider opens (same constant, both call sites).** The corrected Run 2 launcher (`CGN_R3_B2F1A_ExternalSampler_Run2_fixtureA_1p5x.py`) calls `core.run_single_fixture_campaign(FIXTURE_NAME, RUN_ID)` with no override, so it inherited this default. Section 1's stop condition ("if Run 2 already used 16 MiB") does not apply — the hypothesis branch proceeds.

## 2. `_read_path_bounded` — exact bounded-read sequence

From `candidate_packed_provider_r3a2b.py` (the FINAL R3-A2B candidate, unmodified, SHA `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677`):

```python
def _read_path_bounded(path, runtime_cap_bytes):
    _validate_runtime_cap_bytes(runtime_cap_bytes)
    try:
        early_size = os.path.getsize(path)
    except OSError:
        early_size = None
    if early_size is not None and early_size > runtime_cap_bytes:
        _fail(...)

    f = open(path, "rb")
    try:
        try:
            fstat_size = os.fstat(f.fileno()).st_size
            if fstat_size > runtime_cap_bytes:
                _fail(...)
        except (AttributeError, OSError):
            pass
        data = f.read(runtime_cap_bytes + 1)
        if len(data) > runtime_cap_bytes:
            _fail(...)
        return data
    finally:
        f.close()
```

**Confirmed: `f.read(runtime_cap_bytes + 1)` is called unconditionally, regardless of `early_size`/`fstat_size`.** The two size checks are early-exit fast-fail signals only (explicitly documented as such — "TOCTOU-safe: the early stat/fstat checks are signals only, never trusted alone"); the actual buffer request handed to `read()` is always sized off the *cap*, never off the file's real size. This is the exact, single line responsible for the effect under investigation.

## 3. Raw `read(size)` isolation (no broker, no validation)

Fresh Python 2.7.5 process per case, against the real `fixtureA_1p5x.sfmsidecar` (14,304,167 bytes on disk):

| Case | `read(size)` requested | Bytes actually returned | Peak-pagefile delta | Peak-pagefile ≈ requested size? |
|---|---|---|---|---|
| A: 16 MiB + 1 | 16,777,217 | 14,304,167 | 16,863,232 (16.08 MiB) | **yes** |
| B: 64 MiB + 1 | 67,108,865 | 14,304,167 | 67,284,992 (64.16 MiB) | **yes** |
| C: actual size + 1 | 14,304,168 | 14,304,167 | 14,344,192 (13.68 MiB) | yes (trivially, since requested ≈ actual here) |

**The process peak scales with the requested `read(size)` argument, not the bytes actually returned.** Case A and Case B return the *identical* 14,304,167 bytes, yet their peak deltas differ by almost exactly the difference between their requested sizes (16 MiB vs 64 MiB). Python 2.7's `file.read(size)` evidently commits a buffer sized at (or very close to) the requested argument before trimming to the actual data length.

## 4. Provider-level isolation (real validation path, no broker/views)

Same fixture, through `sfm_master_authority.sidecar_contract.validate_selected_artifact()` — the exact function `selection.py`/`broker.py` call during a real acquisition — fresh process per cap:

| Cap | Peak-pagefile delta (module-load → validate+close) | Retained private bytes after close |
|---|---|---|
| 16 MiB | 16,039,936 (15.30 MiB) | 937,984 |
| 64 MiB | 66,445,312 (63.37 MiB) | 929,792 |

The 64 MiB case's peak delta (**63.37 MiB**) lands almost exactly on Run 2's own observed real-SFM transient peak (**63.5859375 MiB**, per the authorizing prompt's Section "Exact Run 2 evidence") — well within run-to-run noise. The retained cost after close is small (~0.9 MB) and **does not depend on the cap at all**, confirming the cap only affects the transient read buffer, not anything retained.

## 5. Measured peak-scaling table (combined)

| Measurement | 16 MiB cap | 64 MiB cap | Real Run 2 (real SFM, 64 MiB cap) |
|---|---|---|---|
| Raw `read()` peak-pagefile delta | 16.08 MiB | 64.16 MiB | — |
| Provider-level peak-pagefile delta | 15.30 MiB | 63.37 MiB | — |
| Real-SFM process-peak delta from S3 | *(not yet run)* | — | **63.59 MiB** |

The provider-level 64 MiB number (63.37 MiB) and the real-SFM 64 MiB number (63.59 MiB) agree to within 0.22 MiB — the read-cap mechanism alone accounts for essentially the entire observed transient.

## 6. Is the ~64 MiB B2F1 peak cap-induced?

**Yes — confirmed, not just plausible.** The read-cap hypothesis is not merely "not rejected"; it is positively demonstrated at two independent levels (raw `read()`, and the real provider/validation call path) with numbers that reproduce the real-SFM observation to within noise. This also **retroactively explains the B2F1 report's own "process-independent, first-acquisition-only" finding**: `PeakPagefileUsage`/`PeakWorkingSetSize` are monotonic, process-lifetime, kernel-tracked high-water marks. The *first* `_read_path_bounded` call in a process raises the peak to ~cap-sized; every subsequent call — regardless of which artifact, regardless of size — allocates the same cap-sized buffer again but does not raise the peak further, because it was already there. What I had attributed in the B2F1 report to "some one-time lazy initialization elsewhere in broker/cohort/resolver/views" is now identified precisely: it is `f.read(runtime_cap_bytes + 1)`, and it fires on every call, but the *peak counter* only visibly moves the first time.

## 7. TOCTOU-safe design implication (proposal only — no implementation change made)

The bounded-read requirement is **not weakened or removed** by this finding, and no such change is authorized or made here. What the finding actually shows is narrower: the *qualification harness* has been measuring its own 64 MiB exploratory override, not the candidate production cap. Under the intended 16 MiB production cap, this exact same code already only requests `16 MiB + 1`, costing ~15.3 MiB peak — comfortably inside the 32 MiB transient gate on its own.

If a future task wants the read-side cost to scale with the *actual* file size rather than the configured cap (relevant mainly if a much larger production cap were ever proposed), a TOCTOU-safe redesign direction — **not implemented here** — would be a chunked, cumulative bounded read: read in bounded increments (e.g. `min(remaining_cap, chunk_size)` at a time), accumulate total bytes read, and fail as soon as the cumulative total would exceed `runtime_cap_bytes`. This preserves the exact same guarantee (never trust `stat`/`fstat` alone; the read itself is the enforcement point, and a file that grows after the size check is still caught) while never requesting a single buffer larger than the actual content plus one bounded increment. This is a design note for a future task, not a change proposed for adoption now.

## 8. Production-envelope relevance

Because Run 2 used 64 MiB, **its ~63.6 MiB transient peak cannot be used to adjudicate the proposed 16 MiB production cap**, and per the hard stop this is **not** being reported as a >32 MiB transient-gate violation of the production envelope. The <=32 MiB transient gate itself is unchanged and not waived. A corrected Run 2 rerun at the intended 16 MiB cap is required before any conclusion about the production envelope can be drawn from real-SFM telemetry.

## Regression / identities

No production or frozen files were modified. `b2f1_campaign_core.py` (test-only harness code) gained one new, additive, default-preserving parameter (`runtime_cap_bytes`, defaulting to the original 64 MiB constant — Runs 1–5's recorded behavior is unaffected). Re-verified unchanged: R1D validator/provider, FINAL R3-A2B validator/provider, production Normalizer, production Character Preset, canonical Master, `sfm_master_authority/selection.py`. `test_b2a_offline.py` (38/38) and `test_b2b_offline.py` (64/64) both re-ran clean under both interpreters.

## Deliverables

1. Exact Run 2 cap and source line — Section 1.
2. Exact `_read_path_bounded` logic — Section 2.
3. Raw-read 16/64/actual comparison — Section 3.
4. Provider-level 16 vs 64 comparison — Section 4.
5. Peak-scaling table — Section 5.
6. Cap-induced determination — Section 6: **yes, confirmed**.
7. TOCTOU-safe design implication — Section 7 (proposal only, not implemented).
8. Next real-SFM action — one corrected Run 2 rerun at 16 MiB cap (below).
9. Identity verification — above, all unchanged.
10. **`B2F1B READ-CAP HYPOTHESIS CONFIRMED — CORRECTED 16-MiB RUN2 REQUIRED`**

## Corrected Run 2 — new files

| File | SHA-256 |
|---|---|
| `b2f1_campaign_core.py` (additive `runtime_cap_bytes` param) | `f40200fee5dfe266bc4e3d11ca04fa5359b0ef279c0bb696c56a04bf5934f00f` |
| `CGN_R3_B2F1B_ExternalSampler_Run2Corrected_16MiBCap_fixtureA_1p5x.py` | `b62cc8786c732d917b75db074227d568dade27ad635083ca2c372be69c8eb089` |
| `B2F1B_ExternalSampler_Launch_Run2Corrected.py` | `a2b302f998a41ed68a3d07a27b5d8ac966ad39e7576b20d8070a98ae74d98db4` |

Dry-run confirmed (both interpreters, outside real SFM): fixture still admits successfully under the 16 MiB cap (14.3 MB file, well under 16 MiB), zero exceptions, predicted transient peak ≈ 15.4 MiB (matching Section 4's provider-level number).

## Operator instructions — corrected Run 2 rerun only (per hard stop, Run 3 remains blocked)

1. Restart SFM. Do not save any prior experimental scene state.
2. From an ordinary terminal (not inside SFM):
   ```
   "C:\Users\Eman\AppData\Local\Programs\Python\Python310\python.exe" "E:\SFM Animation Group Master\tests\sidecar\qualification\B2F1B_ExternalSampler_Launch_Run2Corrected.py"
   ```
   Leave it open until it prints `Found sfm.exe PID <n>.`
3. From SFM's Main Menu, manually run `CGN_R3_B2F1B_ExternalSampler_Run2Corrected_16MiBCap_fixtureA_1p5x.py`.
4. Wait for the terminal to print `External sampler finished.`
5. Tell me when done. If the corrected run's transient stays ≤32 MiB (expected, based on Sections 3–5), we proceed to Run 3 using the same corrected 16 MiB cap. If it doesn't, we stop and investigate before Run 3 — per the hard stop, Run 3 itself is not requested yet either way.
