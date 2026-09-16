# R3-B2F1D: Run 4 16 MiB Retained-Boundary Qualification — Preparation Report

**Authorization:** `SFM_CGN_R3_B2F1D_Run4_16MiB_RetainedBoundary_ClaudeCode_Prompt_2026-09-16.md`
**Status:** `B2F1D RUN4 16-MiB RETAINED-BOUNDARY HARNESS READY`

---

## 1. Exact Run 4 fixture verification

| Quantity | Value |
|---|---|
| Sidecar byte size | 12,179,112 bytes |
| Master byte size | 13,728,598 bytes |
| Structural shape | Family C: 2,729 groups, 19,096 metadata entries, 190,464 occurrences |
| 16 MiB raw admission cap | 16,777,216 bytes |
| Raw sidecar below cap? | **Yes** — 4,598,104 bytes of headroom on the raw-admission check alone |

**Recomputed (not hardcoded) current projected/logical retained-view charge**, via a fresh offline `Broker` running the exact real `acquire_or_reuse_views` path (Normalizer then CSP acquisition) against this fixture's own staged artifact, under the real 16 MiB cap, with no SFM required (the aggregate ledger's `retained_detached_views` figure is a deterministic Python-level estimate, not an OS measurement):

- **Real Python 2.7.5**: `retained_detached_views = 16,733,007 bytes` — **exactly** matching the historical exploratory figure cited in this task's authorization (used here only as a cross-check, never assumed).
- Python 3.10 (cross-check only, not authoritative — SFM runs 2.7.5): `16,732,959 bytes` (48 bytes lower; immaterial, does not change the PASS/FAIL comparison at either interpreter).

**Distance below the 16 MiB (16,777,216-byte) retained gate: 44,209 bytes** (0.26% margin). This is a genuinely tight boundary case, not a comfortable pass. Neither of Section 1's stop conditions applies: the raw sidecar is well under 16 MiB, and the current projected retained charge (16,733,007) is **not** already above 16,777,216 — so Run 4 is not deterministically refused before real SFM. Preparation proceeds.

## 2/3. Run 4 launcher + external wrapper

| File | SHA-256 |
|---|---|
| `CGN_R3_B2F1D_ExternalSampler_Run4_16MiBCap_fixtureC_1p25x.py` (Main Menu launcher) | `f78b31eccf0cafafba876a3fab3d6941300a3ded6a322e04b4b3ddf90f31beae` |
| `B2F1D_ExternalSampler_Launch_Run4.py` (terminal wrapper, genuine separate-process sampler) | `3de29d8e9c0e1cb91fe9c4ea30d6c05f01e325a711015c79493c67f699f1d60b` |
| `b2f1d_projected_retained_probe.py` (offline Section 1 recomputation script) | `b2ac374126ae255eba0b08f9818f5678913adabe6748fac25e90c62dc02c6956` |

Both follow the exact corrected pattern from Runs 2/3: module-scope execution, no `__name__=="__main__"`/`__file__` dependency, game root derived from `sys.executable`, shared core loaded by absolute path via `imp.load_source`. The wrapper auto-discovers the single running `sfm.exe` PID, launches the unmodified `gate2a_external_sampler.py`, targets Run 4's own unique DONE marker, writes `B2F1D_ExternalSampler_Run4_16MiBCap_fixtureC_1p25x_{mem.csv,vas.json}` — never launches SFM, never substitutes an in-process poller.

## Proof the 16 MiB cap reaches both acquisitions

Launcher sets `RUNTIME_CAP_BYTES = 16 * 1024 * 1024` and calls `_core.run_single_fixture_campaign(FIXTURE_NAME, RUN_ID, runtime_cap_bytes=RUNTIME_CAP_BYTES)`. Inside the unchanged shared core, this single value flows to both the Normalizer acquisition and the CSP acquisition call sites (same code already verified in B2F1C — unchanged here).

## 4. Boundary accounting — all ledger categories (dry-run, S5-equivalent)

From the offline recomputation (Section 1) and confirmed identically in the dry-run harness result, every category is reported, none omitted for being zero:

| Category | Value (bytes) |
|---|---|
| `one_incoming_packed_snapshot` | 0 |
| `pending_projection_payload` | 0 |
| `provider_caches` | 0 |
| `resident_broker_metadata` | 0 |
| **`retained_detached_views`** | **16,733,007** |
| `stale_invalidated_views_still_referenced` | 0 |
| `temporary_replacement_overlap` | 0 |
| `validator_scratch_estimate` | 0 |
| **Total logical retained charge** | **16,733,007** |
| View-cache entry count | 2 (Normalizer + CSP) |
| Provider counters | opens=2, closes=2, peak simultaneous=1, current open=0 |

All eight ledger categories are present and will be reported this way from the real-SFM result too — this fixture's entire retained cost is concentrated in `retained_detached_views`, with every other category at zero.

## 5. Dry-run verification (both interpreters, outside real SFM)

Real Python 2.7.5, exact target fixture, exact 16 MiB cap:
- Admission outcome: **accepted**
- Exception: **none**
- Provider opens/closes: **2/2** (balanced)
- Summary generation: clean (`_compute_summary` produced a full result with no error)
- `retained_detached_views` at S5: **16,733,007** (matches Section 1 exactly)

One honest caveat, reported rather than hidden: the dry-run's own OS-level transient peak-pagefile delta (`38,117,376` bytes, ≈36.4 MiB) **exceeds** the 32 MiB transient gate in this bare-`python.exe` environment. Per the established finding from B2F1A/B2F1B, dry-run peaks measured outside real SFM are **not** predictive of real-SFM peaks (different baseline process, different GIL/thread-scheduling behavior affecting any concurrent sampling, and — per B2F1B — the read-cap-sized buffer allocation itself dominates the transient regardless of host). I am not claiming this dry-run number predicts a Run 4 failure, and I am equally not hiding it or smoothing it over: unlike Family A/B (Runs 2/3, which showed comfortable transient margins), Family C's deeper/denser structure means Run 4's transient side may also be closer to its gate than Runs 2/3 were, in addition to the already-tight 44,209-byte retained margin. This is exactly why the real, genuine external-sampler measurement in actual SFM is required and is not being second-guessed here.

Python 3.10 dry-run: same admission outcome, same balanced counters, no exception (cross-check only).

## 6. Stale-output cleanup confirmation

All dry-run artifacts for `Run4_16MiBCap_fixtureC_1p25x` (`_result.json`, `_log.txt`, `_DONE.marker`) were deleted from `C:\Users\Public\Documents`. Confirmed: no files matching that run ID remain before operator handoff.

## Identity / regression protection

Re-verified unchanged: canonical Master, official sidecar artifact, FINAL R3-A2B validator/provider, production Normalizer, and `b2f1_campaign_core.py` itself (SHA identical to the version already regression-tested in B2F1B). This task created only new, additive Run 4 files (launcher, wrapper, offline probe) — the shared core was not modified, so the B2A/B2B regression evidence already on record (38/38, 64/64, both interpreters, from B2F1B) remains sufficient and was not re-run.

## 7. Operator instructions — Run 4 only

1. Move/delete any stale files matching `Run4_16MiBCap_fixtureC_1p25x` in `C:\Users\Public\Documents` (none currently exist, per Section 6, but check before starting).
2. **Restart SFM.**
3. **Do not save** any prior experimental scene state — restart to discard it.
4. Wait until SFM is fully open.
5. From PowerShell:
   ```
   & "C:\Users\Eman\AppData\Local\Programs\Python\Python310\python.exe" "E:\SFM Animation Group Master\tests\sidecar\qualification\B2F1D_ExternalSampler_Launch_Run4.py"
   ```
6. Wait for: `Found sfm.exe PID <n>.`
7. From SFM's Main Menu, manually invoke `CGN_R3_B2F1D_ExternalSampler_Run4_16MiBCap_fixtureC_1p25x.py`.
8. Wait for: `External sampler finished.`
9. Collect all five outputs: `CGN_R3_B2F1_ExternalSampler_Run4_16MiBCap_fixtureC_1p25x_{result.json,log.txt,DONE.marker}` plus `B2F1D_ExternalSampler_Run4_16MiBCap_fixtureC_1p25x_{mem.csv,vas.json}`.

## Status

**`B2F1D RUN4 16-MiB RETAINED-BOUNDARY HARNESS READY`**

Per the hard stop: Run 5 and B2C/B2D remain unauthorized. This report stops before the real operator Run 4. Given the tight 44,209-byte retained margin and the dry-run's transient caveat above, this is the run where the actual external-sampler numbers matter most so far — I am not predicting PASS or FAIL.
