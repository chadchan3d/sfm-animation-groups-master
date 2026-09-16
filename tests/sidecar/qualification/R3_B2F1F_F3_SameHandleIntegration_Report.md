# R3-B2F1F Stage F3: Test-Only Same-Handle Pre-Admission Integration — Report

**Authorization:** `SFM_CGN_R3_B2F1F_F3_SameHandleIntegration_ClaudeCode_Prompt_2026-09-16.md`
**Status:** `B2F1F F3 SAME-HANDLE INTEGRATION PASS — REAL-SFM F4 AUTHORIZED`

No frozen production/provider/broker/Normalizer file was modified. No SFM was run. Run 5 remains blocked. B2C/B2D remain unauthorized.

---

## 1. Frozen inputs, re-hashed fresh (not copied from prior prose)

Per the explicit warning in this task's own prompt about a possible stale/near-identical SHA appearing during a prior edit, every value below was re-computed directly against the files on disk in this turn:

| File | SHA-256 |
|---|---|
| Canonical Master | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |
| Official sidecar artifact | `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` |
| FINAL R3-A2B validator | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` |
| **FINAL R3-A2B provider** | **`d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677`** |
| Production Normalizer | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` |
| `sfm_master_authority/selection.py` | `946791edb172dcc295d1cd8c161db1be68a138e255a7ecb313afb2fee9d85abd` |
| `sfm_master_authority/cohort.py` | `50e686c34b498f4213103e9e2bc0c41734b9d78874141457bffbed0610f85387` |
| `sfm_master_authority/projections.py` | `7dd25ff7104730cef357a6710e3d56e098b7de216eb306527dad2b09c9f0b31a` |

**The provider's re-hashed digest matches the authoritative baseline used throughout this entire arc exactly.** The "two near-identical strings" the prior report briefly showed were my own transcription typo during an edit in that turn (`...b673` vs. the correct `...b677`), caught and corrected in that same turn — not a real file change. Confirmed again here from a completely fresh hash, independent of any prior prose. **No STOP condition triggered.**

Exact F1/F2 test-only files, re-hashed (unchanged since the prior turn):

| File | SHA-256 |
|---|---|
| `b2f1f_resource_shape_estimator.py` | `3c675b4e5651acc2194dd6315a2a85f00355d4d28ba49b2de0cf247c72709465` |
| `b2f1f_qualify_estimator.py` | `4710c141308c7a5dcb46938b8ed3c050bad6e3c9bc5b8ebca468b3acd1350a4d` |
| `b2f1f_monotonicity_boundary_tests.py` | `98ed36905f15e82692ae5e0d899a2bd98dbd0e4ce8ec6daab08a822b3b3e4dd0` |
| `b2f1f_collect_ground_truth.py` | `eba02784c6fc69a5d9544a4d7d42a9090abde1b3ce08d6e3a5e882c99db0e2a8` |

## 2. Same-handle architecture (implemented in the prototype)

```
candidate_open_path_with_preflight(path, expected_source_sha256, runtime_cap_bytes):
    f = open(path, "rb")                          # ONE open, recorded
    try:
        artifact_bytes = fstat(f).st_size          # Gate A -- on the OPEN handle, no path re-stat
        if artifact_bytes > runtime_cap_bytes: raise ResourceAdmissionRefusal(reason="artifact_bytes")

        header = f.read(HEADER_SIZE); f.seek(0)
        prefix = f.read(preflight_region_size)     # <=360 bytes, SAME handle
        shape  = parse_resource_shape(prefix, artifact_bytes)   # F1/F2, unmodified

        est_retained  = estimate_retained(shape)   # F1/F2, unmodified   -- Gate B
        est_transient = estimate_transient(shape, runtime_cap_bytes)  -- Gate C
        if est_retained  > 16_777_216: raise ResourceAdmissionRefusal(reason="estimated_retained")
        if est_transient > 33_554_432: raise ResourceAdmissionRefusal(reason="estimated_transient")

        f.seek(0)                                  # REPOSITION the SAME handle
        data = f.read(runtime_cap_bytes + 1)       # existing bounded-read discipline, mirrored
        if len(data) > runtime_cap_bytes: raise ResourceAdmissionRefusal(reason="post_read_length")
    finally:
        f.close()                                  # exactly once, always

    provider = BoundedProvider._open_from_buf(data, expected_source_sha256, bound=True)  # EXISTING,
                                                     # unmodified -- runs the EXACT SAME
                                                     # candidate_packed_validator.validate_packed
    return provider
```

Malformed preflight parse (`PreflightCorruptOrIncompatible`) never invents a corruption verdict of its own — it silently defers (rewinds and falls through to the existing full read + `_open_from_buf`), leaving the frozen validator as the sole authority on corruption/incompatibility, exactly matching the design doc's "negative admission filter only" decision.

## 3/4. Proof of one-open/no-reopen

Instrumented every acquisition attempt (`Instrumentation` class): `file_open_count`, `file_close_count`, and a Windows file-identity tuple `(fileno, st_dev, st_ino, st_size, st_mtime)` captured via `os.fstat()` on the already-open handle both before preflight and after full-read positioning. Across **all 7 fixtures** in the required matrix: `file_open_count == 1` and `file_close_count == 1` in every case, and for every admitted fixture the `(st_dev, st_ino)` pair is identical before and after — proving the full read used the same underlying file identity, never a second `open()`.

## 5. Full fixture disposition matrix + instrumentation

| Fixture | Outcome | Reason | File open/close | Preflight bytes | Full-read count | Validator count | Est. retained | Est. transient (16 MiB cap) |
|---|---|---|---|---|---|---|---|---|
| official_control | accepted | — | 1/1 | 360 | 1 | 1 | 78,392 | 28,109,532 |
| fixtureA_1p5x | accepted | — | 1/1 | 360 | 1 | 1 | 736,724 | 25,183,813 |
| fixtureB_1p5x | accepted | — | 1/1 | 360 | 1 | 1 | 205,292 | 30,781,913 |
| fixtureC_1p0x | **refused** | `estimated_transient` | 1/1 | 360 | 0 | 0 | 13,231,328 | 42,145,509 |
| fixtureC_1p25x | **refused** | `estimated_retained` | 1/1 | 360 | 0 | 0 | 22,561,448 | 52,997,877 |
| fixtureC_1p5x | **refused** | `estimated_retained` | 1/1 | 360 | 0 | 0 | 32,720,784 | 64,679,461 |
| fixtureC_2p0x | **refused** | `artifact_bytes` | 1/1 | 0 | 0 | 0 | — | — |

Every disposition matches Section 8's expected table exactly, including the un-hardcoded `fixtureC_1p0x` transient refusal the qualified model naturally produces (consistent with B2F1F F1/F2's own finding — not tuned for this task). Full row data: `b2f1f_f3_fixture_matrix.json`.

## 6. Instrumentation table

Full per-fixture instrumentation (candidate path, handle identity tuples, preflight/full-read/validator counts, estimator model version `b2f1f-v1`, both gate values, outcome/reason) is recorded in `b2f1f_f3_fixture_matrix.json` for all 7 fixtures. For every refused fixture: `full_bounded_read_call_count == 0`, `validator_call_count == 0`, `projection_builder_call_count == 0`, `published_detached_view_count == 0`, `file_open_count/file_close_count == 1/1` — confirmed directly, not inferred.

## 7. Admitted-fixture semantic equivalence

For `fixtureA_1p5x` and `fixtureB_1p5x` (the two synthetic ADMIT cases), built both the Normalizer-like and Character-Preset-like projections through the prototype's provider **and** independently through the existing, completely unmodified `Broker.acquire_or_reuse_views()` path (fresh broker, real Cohort), then compared:

- Normalizer payload `groups` (full list) — **identical**
- Normalizer payload `metadata_by_path` (full dict) — **identical**
- Normalizer payload `lookup_results` — **identical**
- Normalizer payload `wrapper_path` — **identical**
- Normalizer `estimated_bytes` — **identical**
- CSP payload `lookup_results` — **identical**
- Artifact identity (embedded `source_sha256`, hex-compared) — **identical**
- `semantic_generation.master_sha256` (consistency across both existing views) — **identical**

Exact equality (`==` on the full Python structures), not "same counts" — satisfying the "do not accept 'same counts' as sufficient" requirement.

## 8. C_1p25x early-refusal proof

Direct assertions against the prototype's own instrumentation for `fixtureC_1p25x`:
- Raises `errors.ResourceAdmissionRefusal` — ✅
- Reason is `estimated_retained` or `estimated_transient` — ✅ (`estimated_retained`)
- `preflight_bytes_read <= 360` — ✅ (exactly 360)
- `full_bounded_read_call_count == 0` — ✅
- `validator_call_count == 0` — ✅
- `projection_builder_call_count == 0` — ✅
- `published_detached_view_count == 0` — ✅
- `file_open_count == 1`, `file_close_count == 1` — ✅

**No 16,733,007-byte detached view was ever materialized.** The 16.7 MB payload construction this whole B2F1E→F chain exists to avoid paying for a doomed acquisition never runs.

## 9. Same-handle mutation/race probe — result and honest interpretation

The probe: open the candidate once, complete preflight, then (simulating an external actor) overwrite the **same path in place** with a different, legitimate artifact's bytes, then continue the full read on the **already-open handle** (never a second `open()`), then feed whatever bytes result to the existing, unmodified provider construction.

**This produced a genuinely interesting, interpreter-dependent result, reported exactly as observed rather than assumed:**

- **Python 3.10:** the post-mutation read returned a **hybrid** matching neither the original nor the replacement exactly (`matches_original=False`, `matches_replacement=False`) — `io.BufferedReader`'s internal buffering apparently retains some already-buffered pre-mutation bytes, mixed with fresh post-mutation reads.
- **Real Python 2.7.5** (SFM's actual interpreter): the post-mutation read returned a **clean, byte-exact copy of the replacement artifact** (`matches_replacement=True`) — Python 2.7's `file` object re-reads the live underlying file fully after `seek(0)`, with no stale buffering artifact.

**Neither result means "same handle" is a complete defense against a same-path overwrite race on its own** — under real Python 2.7.5, the full read can genuinely end up reading a different (but internally valid) file's bytes if something overwrites the path in place during the race window. **What actually prevents silent misuse in both cases is the existing, separately-mandatory `expected_source_sha256` check** inside `BoundedProvider._open_from_buf` (never touched, never weakened by this prototype): in the Python 3.10 hybrid case, the header's own `payload_length` self-consistency check catches the corruption (`AuthorityUnavailable: payload_length (...) does not match actual file size (...)`); in the real-Python-2.7.5 clean-swap case, the replacement artifact's own embedded `source_sha256` does not match the Master this acquisition was actually for, so `SourceMismatchError` is raised. **In both interpreters, tested directly, the resulting bytes were reliably rejected — never silently accepted as answering for the wrong Master.** This is reported as the honest, load-bearing finding: same-handle avoids the *original* concern this design exists for (a stale/mismatched pathname variable causing preflight-on-one-file, full-read-on-a-different-file due to a programming mistake), while the *cryptographic* protection against a genuine malicious same-path swap during the race window comes from the pre-existing, unmodified source-hash check — which this prototype correctly continues to rely on and does not weaken.

No second `open()` call of the candidate path occurred in either interpreter — confirmed directly (only the external mutation used a separate write-mode open, a different code path representing the "attacker," not the prototype re-opening for reading).

## 10. Error-classification tests

- **Malformed header (bad magic):** preflight defers (does not invent a verdict); the existing pipeline classifies it as `SidecarCorrupt` — never `ResourceAdmissionRefusal`, never a "missing" outcome. ✅
- **Unsupported `format_contract_version`:** preflight defers; existing validation rejects it via its own incompatibility path — never resource refusal, never missing. ✅
- **Valid, parseable, resource-expensive artifact:** `ResourceAdmissionRefusal` with an identifying reason (`artifact_bytes` / `estimated_retained` / `estimated_transient`) — never corruption, never missing. ✅ (the full fixture matrix, Section 5)
- **Resource refusal through a selection-like multi-candidate scan:** wrapped the prototype in a scan loop mirroring `selection.py`'s already-fixed `_find_matching_artifact` pattern (track the last-seen `ResourceAdmissionRefusal`; only report "missing" if nothing raised one) — the refusal survives distinctly, never collapsed into a "missing" outcome, without touching `selection.py` itself. ✅

## 11. Test totals — both interpreters

| Suite | Python 3.10 | Real Python 2.7.5 |
|---|---|---|
| F3 same-handle driver (this task) | 48/48 (first pass, before the race-probe assertion fix) → **47/47** (corrected assertion) | **47/47** |
| F1/F2 estimator qualification (no underestimate) | PASS (`False` underestimate) | PASS (`False` underestimate) |
| F1/F2 monotonicity/boundary | 20/20 | 20/20 |
| B2A offline regression | 38/38 | 38/38 |
| B2B offline regression | 64/64 | 64/64 |

(The F3 driver's total moved from 48 to 47 checks between the two interpreter runs only because one incorrect assertion — "post-mutation bytes must never match the replacement exactly" — was corrected mid-investigation once the real, interpreter-dependent behavior was understood; see Section 9. The corrected 47-check suite passes cleanly, unmodified, on both interpreters.)

No dedicated standalone "FINAL R3-A2B qualification suite" exists separately from B2A/B2B (which already exercise the FINAL R3-A2B provider/validator as their dependency) and this task's own extensive direct exercise of `BoundedProvider._open_from_buf`/`candidate_packed_validator.validate_packed` across 7 fixtures, 2 malformed-input cases, and the race probe — collectively a strong regression signal beyond B2A/B2B alone.

## 12. Was any estimator model revision required?

**No.** `b2f1f_resource_shape_estimator.py` is byte-identical to the version qualified in the prior F1/F2 turn (SHA re-confirmed above). Stage F3 integrates it as-is.

## 13. Test-only prototype files

| File | SHA-256 |
|---|---|
| `b2f1f_f3_same_handle_candidate.py` | `02653e032fb2e6ea18c6a51b3b9900e0cac7d1a5d402e3ca834121e84fd8c91f` |
| `b2f1f_f3_test_driver.py` | `a12177fe57f73e9b60ad45b14c4cc29adb78276e015743de7f9399d1d1a47c32` |

## 14. Stage F4 candidate design (prepared, not executed)

**Objective:** prove, in real SFM with the genuine external sampler, that `fixtureC_1p25x` (or `fixtureC_1p0x`, per Section 5's finding) is refused by the preflight **before** any expensive acquisition, that the authority-window transient stays ≤32 MiB, and that no detached view is published.

**Candidate files to prepare (not yet created):**
- A Main Menu launcher mirroring the corrected Run 2–4 pattern (module-scope execution, `sys.executable`-derived game root, `imp.load_source` for a shared core), but invoking `b2f1f_f3_same_handle_candidate.candidate_open_path_with_preflight()` against `fixtureC_1p25x` under the real 16 MiB cap, sampling S0–S3-equivalent stages exactly as Runs 2–4 did.
- The same genuine, separate-process `gate2a_external_sampler.py` wrapper pattern (PID auto-discovery, DONE-marker handshake) used for Runs 2–4.
- Success criteria for F4 (per the design doc's own Stage F4 definition): refusal occurs before expensive acquisition; authority-window transient ≤32 MiB; no retained view published; provider/handle counters balance; VAS remains healthy.

**This task stops here — no F4 files were created, no real-SFM run occurred, per the hard stop.**

## Deliverables checklist

1. ✅ Test-only prototype file list + SHA-256 — Section 13.
2. ✅ Exact frozen identity re-verification (fresh, not copied) — Section 1.
3. ✅ Same-handle architecture/sequence — Section 2.
4. ✅ Proof of one-open/no-reopen — Section 3/4.
5. ✅ Full fixture disposition matrix — Section 5.
6. ✅ Instrumentation table — Section 6.
7. ✅ Admitted-fixture semantic equivalence — Section 7.
8. ✅ C_1p25x early-refusal proof — Section 8.
9. ✅ Race/mutation probe result — Section 9 (nuanced, interpreter-dependent, honestly reported).
10. ✅ Error-classification tests — Section 10.
11. ✅ Python 2.7.5 + 3.10 test totals — Section 11.
12. ✅ B2A/B2B regression totals — Section 11 (38/38, 64/64, both interpreters).
13. ✅ Estimator model revision: **none required** — Section 12.
14. ✅ Stage F4 candidate design — Section 14 (design only).
15. ✅ Status: **`B2F1F F3 SAME-HANDLE INTEGRATION PASS — REAL-SFM F4 AUTHORIZED`**

## Hard stop

No frozen file was edited. No SFM was run. Run 5 remains not requested. B2C/B2D remain unauthorized. Stage F4 is authorized by this result but not begun — no operator instructions are given in this report.
