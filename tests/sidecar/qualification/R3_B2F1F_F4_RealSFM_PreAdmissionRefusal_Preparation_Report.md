# R3-B2F1F Stage F4: Real-SFM Preflight-Refusal Qualification — Preparation Report

**Authorization:** `SFM_CGN_R3_B2F1F_F4_RealSFM_PreAdmissionRefusal_ClaudeCode_Prompt_2026-09-16.md`
**Status:** `B2F1F F4 REAL-SFM PREFLIGHT-REFUSAL HARNESS READY`

This is a preparation-only task. No SFM was run by me. No frozen file was modified. No operator F4 run has occurred yet.

---

## Important disclosure before anything else

While dry-running the external-sampler wrapper (to confirm it fails gracefully when no `sfm.exe` is running), I discovered **your real SFM is currently running** (PID 23332, `E:\SteamLibrary\...\game\sfm.exe`, ~2.7 GB, launched 2026-09-16 03:05:58). The wrapper correctly found it and, because that is its designed behavior once a target is found, ran the genuine external sampler against it for the full 120-second window I had configured for dry-run testing. **I did not intend this and did not run the in-SFM F4 launcher during that window**, so no real acquisition/refusal ever happened inside SFM — the resulting CSV/VAS files contained only idle-SFM telemetry with no correlated stage markers, so they are not a real F4 result. I deleted both files immediately. The sampler itself is strictly read-only (`PROCESS_QUERY_INFORMATION | PROCESS_VM_READ`, `GetProcessMemoryInfo`/`VirtualQueryEx` only) and cannot have modified or destabilized your SFM session. I did not run the in-SFM launcher, and I am not treating this as satisfying any part of the real F4 qualification.

---

## 1. Frozen inputs, re-hashed fresh

| File | SHA-256 |
|---|---|
| Canonical Master | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |
| Official sidecar artifact | `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` |
| FINAL R3-A2B validator | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` |
| FINAL R3-A2B provider | `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677` |
| Production Normalizer | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` |
| `sfm_master_authority/selection.py` | `946791edb172dcc295d1cd8c161db1be68a138e255a7ecb313afb2fee9d85abd` |
| `sfm_master_authority/cohort.py` | `50e686c34b498f4213103e9e2bc0c41734b9d78874141457bffbed0610f85387` |
| `sfm_master_authority/projections.py` | `7dd25ff7104730cef357a6710e3d56e098b7de216eb306527dad2b09c9f0b31a` |

All match the authoritative baseline exactly. **No STOP condition triggered.**

## A real bug found and fixed in the F3 candidate (test-only file, disclosed transparently)

While preparing F4, I found that `b2f1f_f3_same_handle_candidate.py`'s `TRANSIENT_GATE_BYTES` was `32*1024*1024 + 1024*1024 = 34,603,008` — the comment beside it mislabeled `33,554,432` as "33 MiB" when **33,554,432 is exactly 32 MiB** (`32*1024*1024`); the extra `+ 1024*1024` was a genuine arithmetic error, making the live gate 1 MiB looser than intended throughout Stage F3. Fixed to `32 * 1024 * 1024` exactly. I re-ran the full F3 test driver (47/47) under both interpreters after the fix and confirmed **no fixture's `estimated_transient` fell within that 1 MiB band**, so none of F3's previously-reported classifications change. New SHA: `5487bade831903b8f447634193d1ba41283472fc6d1b256c215beaffcb994849`. (`b2f1f_qualify_estimator.py`'s own qualification matrix, used to report F1/F2/F3 results, already used the correct literal `33554432` directly and was never affected by this bug.)

## 2. F4 target and purpose

`fixtureC_1p25x` — 12,179,112 bytes (below the 16 MiB raw cap), current full-build retained charge 16,733,007 bytes, current non-preflight real-SFM transient peak ~37.06 MiB (Run 4, B2F1D). The preflight estimator's own numbers for this exact fixture (unchanged, re-confirmed this turn): `estimated_retained_bytes = 22,561,448` (exceeds the 16 MiB / 16,777,216-byte retained gate) and `estimated_transient_bytes = 52,997,877` (exceeds the 32 MiB / 33,554,432-byte transient gate, now using the corrected constant) — refusal reason reported is `estimated_retained` (checked first in gate order).

## 3. F4 launcher

**`CGN_R3_B2F1F_F4_PreflightRefusal_C1p25.py`** — SHA-256 `bd1060e414d8752010c4e1fea7e2bbb35e6e98ebe8dbae79a714c1cb1ea2f14a`, staged in `mainmenu/`.

- Module-scope execution (called unconditionally, no `__name__=="__main__"` guard).
- No `__file__` dependency.
- Game root derived from `os.path.dirname(os.path.abspath(sys.executable))`, with the established fallback if that directory doesn't contain the expected `usermod\scripts\sfm\mainmenu` subtree.
- Loads the F3 candidate (`b2f1f_f3_same_handle_candidate.py`) via `imp.load_source` from its absolute path in `tests/sidecar/qualification/` — the proven Python-2.7-compatible mechanism.
- Targets exactly `fixtureC_1p25x`, exact 16 MiB (`16*1024*1024`) `runtime_cap_bytes`.
- Calls **only** `candidate.candidate_open_path_with_preflight(...)` — never touches `Broker.acquire_or_reuse_views` or any production mutation path. A **fresh, otherwise-untouched** `Broker` is constructed solely to read `ledger_snapshot()`/`provider_counters()` afterward, as the honest way to report the required AggregateLedger categories (the F3 candidate itself never constructs a Broker/Cohort at all).
- Writes the recommended output set (Section 11) to `C:\Users\Public\Documents`.

## 4. Same-handle instrumentation, expected/observed values (dry-run)

| Field | Expected | Dry-run observed (both interpreters) |
|---|---|---|
| candidate file opens | 1 | 1 |
| candidate file closes | 1 | 1 |
| preflight bytes read | ≤360 | 360 |
| full bounded-read call count | 0 | 0 |
| validator call count | 0 | 0 |
| projection-builder call count | 0 | 0 |
| provider left open at end | 0 | 0 |
| estimated retained bytes | — | 22,561,448 |
| estimated transient bytes | — | 52,997,877 |
| refusal reason | `estimated_retained` or `estimated_transient` | `estimated_retained` |
| error class | `ResourceAdmissionRefusal` | `ResourceAdmissionRefusal` |
| ledger categories after refusal | all zero | all zero (all 8 categories) |
| broker provider counters after refusal | all zero | all zero |
| `overall_qualification_result` | `PASS` | `PASS` |

Every Section 6 assertion is computed and stored explicitly in the result JSON (`assertions` dict, 14 boolean checks) — the launcher does **not** report PASS merely because it ran to completion; `overall_qualification_result` is `all(assertions.values())`.

## 5. External sampler wrapper

**`B2F1F_F4_ExternalSampler_Launch.py`** — SHA-256 `4bf91a05dc0bc91b098e6b07fae92635e88b6dd11e43bfcb99711311ee719360`.

- Auto-discovers the single running `sfm.exe` via `tasklist` (refuses to guess if zero or multiple matches; refuses to proceed if a stale DONE marker already exists).
- Launches the genuine, unmodified `gate2a_external_sampler.py` (separate OS process, `OpenProcess`/`VirtualQueryEx`/`GetProcessMemoryInfo`) targeting that PID.
- Prints `Found sfm.exe PID <n>.` and, on completion, `External sampler finished.`
- Writes uniquely-named output (Section 11) — nothing overwrites any B2F1A–D evidence.
- Fixed one latent bug found while writing it: a literal Windows path inside a plain (non-raw) docstring caused a `SyntaxError` (`\U` in `\Users` parsed as a unicode escape) — fixed by making that docstring a raw string. None of the earlier B2F1A–D wrapper files had this exact pattern, so none needed the same fix.
- **Confirmed working via the disclosed incident above**: it correctly found the real running `sfm.exe` PID and launched the genuine sampler against it — direct, if unintended, proof the PID-discovery and sampler-invocation path functions correctly end-to-end. The zero-match and stale-marker-guard paths were already proven in the B2F1A turn (identical logic, a synthetic `sfm.exe`-named test double) and were not re-tested live this turn, to avoid any further unintended interaction with your actual running SFM.

## 6. Dry-run results (both interpreters)

| Check | Real Python 2.7.5 | Python 3.10 |
|---|---|---|
| Exact fixture (`fixtureC_1p25x`) | ✅ | ✅ |
| Exact 16 MiB cap | ✅ | ✅ |
| Expected `ResourceAdmissionRefusal` | ✅ | ✅ |
| One open / one close | ✅ | ✅ |
| 0 full read / validator / builder | ✅ | ✅ |
| 0 published views | ✅ | ✅ |
| Summary/result JSON generation | ✅ | ✅ |
| Exception raised | none | none |
| `overall_qualification_result` | `PASS` | `PASS` |

## 7. Stale-output cleanup confirmation

All dry-run artifacts using the real F4 operator filenames were deleted from `C:\Users\Public\Documents` after each dry-run pass, including the unintended external-sampler CSV/JSON described above. Confirmed empty: no file matching `CGN_R3_B2F1F_F4_PreflightRefusal_C1p25_*` or `B2F1F_F4_PreflightRefusal_C1p25_*` remains before operator handoff.

## 8. Output names (as used throughout preparation)

- `CGN_R3_B2F1F_F4_PreflightRefusal_C1p25_result.json`
- `CGN_R3_B2F1F_F4_PreflightRefusal_C1p25_log.txt`
- `CGN_R3_B2F1F_F4_PreflightRefusal_C1p25_DONE.marker`
- `B2F1F_F4_PreflightRefusal_C1p25_mem.csv`
- `B2F1F_F4_PreflightRefusal_C1p25_vas.json`

## 9. Regression protection

No frozen implementation changed. The only change this turn was the `TRANSIENT_GATE_BYTES` arithmetic fix in the test-only F3 candidate (Section "A real bug found..." above), which B2A/B2B's own test suites do not import or depend on at all (they exercise `sfm_master_authority` directly, never `b2f1f_*` files). Re-hashed all frozen identities (Section 1, all match). Given B2A (38/38) and B2B (64/64) were already re-confirmed clean on both interpreters multiple times this session with zero changes to anything they depend on, and this turn's only code change has no dependency relationship to them, the existing evidence remains sufficient without a further re-run. The F3 suite itself **was** re-run after the fix (47/47, both interpreters) since it directly exercises the changed file.

## 10. Race-protection sanity

Confirmed by direct source inspection (`grep`) that `b2f1f_f3_same_handle_candidate.py` still calls `provider_mod.BoundedProvider._open_from_buf(data, expected_source_sha256, bound=True)` and still has an `except provider_mod.SourceMismatchError` clause mapping to `errors.SourceGenerationMismatch` — the exact source-hash/generation check that caught the F3 overwrite race is present, unchanged, and not bypassed by anything added this turn.

## Status

**`B2F1F F4 REAL-SFM PREFLIGHT-REFUSAL HARNESS READY`**

## 13. Operator instructions — exactly one run

1. Move/delete any stale files matching `CGN_R3_B2F1F_F4_PreflightRefusal_C1p25_*` or `B2F1F_F4_PreflightRefusal_C1p25_*` in `C:\Users\Public\Documents` (none currently exist, per Section 7, but check before starting).
2. **Restart SFM.**
3. **Do not save** any prior experimental scene state — restart to discard it.
4. Wait until SFM is fully open.
5. Open PowerShell.
6. Run:
   ```
   & "C:\Users\Eman\AppData\Local\Programs\Python\Python310\python.exe" "E:\SFM Animation Group Master\tests\sidecar\qualification\B2F1F_F4_ExternalSampler_Launch.py"
   ```
7. Wait for: `Found sfm.exe PID <n>.`
8. From SFM's Main Menu, manually run `CGN_R3_B2F1F_F4_PreflightRefusal_C1p25.py`.
9. Wait for: `External sampler finished.`
10. Collect all five outputs (Section 8) and let me know — I'll analyze them against the exact gates in this report before any B2F verdict is considered.
