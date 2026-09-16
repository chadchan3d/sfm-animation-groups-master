# R3-B2F1A: Runtime Harness Correction — Report

**Authorization:** `SFM_CGN_R3_B2F1A_RuntimeHarness_Correction_ClaudeCode_Prompt_2026-09-16.md`
**Status:** `B2F1A HARNESS CORRECTION PASS — RUN2 READY`

---

## 1. Root cause of the summary crash

`_compute_summary()` in `b2f1_campaign_core.py` called `max(list, default=s3_priv)` and `max(list, default=s3_peak_pf)`. The `default=` keyword argument to `max()`/`min()` was added in **Python 3.4** and does not exist in Python 2.7.5 (SFM's shipped interpreter), which raised `TypeError: max() got an unexpected keyword argument` — exactly the traceback captured in Run 1's own `result.json`'s `exception` field, confirmed by direct inspection:
```
File "...\b2f1_campaign_core.py", line 259, in _compute_summary
    default=s3_priv,
TypeError: max() got an unexpected keyword argument
```
This fired only in post-processing, **after** all six stage samples (S0–S6) had already been captured and written into the in-memory `result` dict — the crash was in summarization, not measurement.

## 2. Run 1 evidence — preserved, not rerun

Run 1's three files are untouched and remain the authoritative record of that run:
- `CGN_R3_B2F1_ExternalSampler_Run1_official_control_result.json`
- `CGN_R3_B2F1_ExternalSampler_Run1_official_control_log.txt`
- `CGN_R3_B2F1_ExternalSampler_Run1_official_control_DONE.marker`

Confirmed directly from the JSON: all 7 stage keys present (`S0_process_baseline` through `S6_release_evict`), `admission_outcome: "accepted"`, `final_provider_counters: {total_provider_opens: 2, total_provider_closes: 2, peak_open_provider_count: 1}`, `ledger_snapshot_at_S5.retained_detached_views: 70133`. Run 1 was **not** rerun and will not be.

## 3. Corrected core file

Fixed by replacing both `max(..., default=...)` calls with an explicit build-list-then-conditionally-max pattern (no behavior change, just 2.7-compatible syntax):
```python
priv_candidates = [...]
max_priv_in_window = max(priv_candidates) if priv_candidates else s3_priv
```
No other Python-3-only constructs were found in the file (checked for f-strings, `:=`, `nonlocal`, dict-unpacking-in-call — none present). No measurement semantics changed.

**Regression, applying the corrected `_compute_summary()` directly to Run 1's own real-SFM JSON, under real Python 2.7.5:**
```
transient_max_peak_pagefile_delta = 66,170,880 bytes
transient_max_private_bytes_delta = 13,955,072 bytes
retained_private_bytes_delta_at_last_full_stage = -8,192 bytes
```
Clean summary generation confirmed under both real Python 2.7.5 and Python 3.10, and confirmed again by dry-running all 4 corrected Run 2–5 launchers end-to-end under both interpreters (all produced clean `summary` blocks, zero exceptions).

`b2f1_campaign_core.py` SHA-256 (corrected): `9a41dd559b969fe269ab0489ba21ee42b1e1d6827dcd9e50c6ee465338374200`

## 4. Corrected Runs 2–5 launchers

Section 3's three claims about SFM Main Menu execution — no `__name__=="__main__"`, no `__file__`, sibling directory not on `sys.path` — could not be independently verified by me (SFM's own Main Menu loader is not part of this repo's source), but I am not overriding the owner's stated, ground-truth characterization of their own SFM environment. I designed the correction so it is unconditionally correct **regardless of** exactly how SFM's loader behaves internally, provided the owner's core claim (manual selection executes the file; startup does not) holds:

- All real work is at plain module scope — no `if __name__ == "__main__":` guard.
- The shared core is loaded by an explicit absolute path via `imp.load_source(...)`, never a bare `import b2f1_campaign_core`.
- The absolute path is derived from `sys.executable` — inside real SFM, `sys.executable` **is** `...\game\sfm.exe` itself (confirmed in this project's own prior H1 runtime audits), so `os.path.dirname(sys.executable)` **is** the game root directly, with a hardcoded fallback only if that directory doesn't actually contain the expected `usermod\scripts\sfm\mainmenu` subtree (defensive, never silently wrong).
- No `__file__` reference anywhere in the launcher.

All 4 were dry-run end-to-end (both interpreters, outside real SFM) with zero exceptions, correctly exercising the `_derive_game_root()` fallback path (since a bare `python.exe` isn't `sfm.exe`).

| File | SHA-256 |
|---|---|
| `CGN_R3_B2F1A_ExternalSampler_Run2_fixtureA_1p5x.py` | `4f43068e0f2bfada7bbc319e3d48b294db4086da5d42bc3e78393edf5c136fb1` |
| `CGN_R3_B2F1A_ExternalSampler_Run3_fixtureB_1p5x.py` | `ef4d34f6bbb10ab79ef9d453a12b3b429e1ba65f2eec1573843735f054b18a43` |
| `CGN_R3_B2F1A_ExternalSampler_Run4_fixtureC_1p25x.py` | `cead1ee2fd46d33d30f59186bc44d15770a4e90b5b626eeefd9e65e99cce8ff4` |
| `CGN_R3_B2F1A_ExternalSampler_Run5_fixtureC_1p5x.py` | `134b3f923bc1b2456f2d85f53215de23d90a886d7b625de5716da2fa54cabe09` |

Per the hard stop, only **Run 2's** operator instructions are given below; Runs 3–5 wait for a later turn.

## 4. Was R2's sampler truly external, or in-process? — determined

**R2 had BOTH, and I had conflated them.** I searched this session's own scratchpad and the user's archived R2 evidence and found:

- **The in-process technique** (`GetCurrentProcess()`-based `PROCESS_MEMORY_COUNTERS_EX`/`VirtualQuery`) that I reused verbatim into `b2f1_campaign_core.py`'s `BackgroundPoller` and into `sample()` — this self-samples the SAME process being measured. It originates from `CGN_R2_R1D_W1_SIDECAR_PackedValidationHot_01.py`'s `_self_memory_counters`/`_self_vas_scan` (note the `_self_` naming — always self-sampling, never a separate observer).
- **A genuinely separate-process sampler**, `gate2a_external_sampler.py` (Python 3, found at `.../scratchpad/gate2a_external_sampler.py`, confirmed against its own historical output logs: `gate2a_mt_sampler_stdout.log` reads `"opened PID 120, sampling for up to 180.0s..."`, where PID 120 matches that same run's in-SFM `os.getpid()=120` — i.e. it genuinely attached to SFM's own PID via `OpenProcess`/`VirtualQueryEx`/`GetProcessMemoryInfo` from a **separate OS process**, polling at 0.15 s intervals with a 2.0 s VAS-scan cadence, coordinated via a DONE-marker handshake).

**Conclusion: my B2F/B2F1 "external sampler" terminology was wrong.** `BackgroundPoller` is an in-process poller — real, useful, but not external. `gate2a_external_sampler.py` is the genuine article, and it already exists, already qualified, and needed no reimplementation. I am reusing it verbatim (SHA-256 `0ecc3e9539ee38336216718e5788a3254733d818c771549d10cb8eade0d4418f`), not fabricating a new one, per Section 5.

**Why this matters, concretely (not just terminology):** applying the corrected `_compute_summary()` to Run 1's own in-process 20 Hz poll data shows its highest observed instantaneous value was only **13.96 MB above the S3 baseline**, while the OS's own process-lifetime `PeakPagefileUsage` counter (unaffected by thread scheduling) recorded a **66.17 MB** increase over the same window. The in-process poller thread was demonstrably too coarse — almost certainly GIL/scheduling-starved during the acquisition's CPU-bound work inside real SFM's heavier process (a bare dry-run `python.exe` process, with far less thread contention, does not reproduce this gap — its own poller caught deltas of 66–68 MB, close to the OS peak). **This is exactly why a genuinely separate, external-process sampler is necessary for Runs 2–5**, not a nice-to-have: the in-process poller cannot be trusted to observe the true transient inside real SFM specifically.

## 5. External sampler wrapper for Run 2

`B2F1A_ExternalSampler_Launch_Run2.py` (SHA-256 `7c5463cb104cf542f87c51ed871775f840059805ba819e55b588333bef05157c`) — run from an ordinary terminal, Python 3, never inside SFM:
- Finds the one running `sfm.exe` PID via `tasklist` (refuses to guess if zero or more than one match).
- Launches `gate2a_external_sampler.py` (unmodified) targeting that PID, with Run 2's own unique DONE-marker and output paths.
- Blocks until the in-SFM script's DONE marker appears (plus a short trailing grace period — the sampler's own already-fixed post-DONE VAS-scan correction is preserved unmodified).
- Writes `B2F1A_ExternalSampler_Run2_fixtureA_1p5x_mem.csv` and `..._vas.json` to `C:\Users\Public\Documents`.

Dry-run tested (no `sfm.exe` running): correctly detects zero matches and exits with a clear message rather than guessing; correctly detects and refuses to proceed if a stale DONE marker from a prior run is already present (the exact historical bug class documented in `CGN_R2_R1D`'s own header comment). I cleared out my own dry-run leftovers for Runs 2–5's output paths so the real runs start clean; **Run 1's files were never touched.**

## 6. New separate-process sampler required for B2F1? — No

Not needed. Section 6 only applies if R2's method turns out to have been purely in-process; it was not. `gate2a_external_sampler.py` already meets every requirement in Section 6's checklist (external Python 3, attaches read-only via `OpenProcess`/`VirtualQueryEx`, samples at ~6.7 Hz for memory + 2 s cadence for VAS, timestamps every sample, stops on DONE marker or process exit, writes CSV/JSON, no code injection).

## 7. Run 1 exact telemetry analysis

| Quantity | Value |
|---|---|
| S0 baseline private bytes | 476,585,984 |
| S3 post-infrastructure private bytes | 477,696,000 |
| S3 post-infrastructure peak-pagefile (OS field, already-established) | 478,810,112 |
| Process-lifetime peak-pagefile reached during first acquisition (OS field, at S4) | 544,980,992 |
| **S3 → process-peak delta** | **66,170,880 bytes (63.11 MiB)** |
| Highest sampled *instantaneous* `pagefile_usage` (20 Hz in-process poller, anywhere in S0..S6) | 491,651,072 |
| **S3 → highest sampled instantaneous delta** | **13,955,072 bytes (13.31 MiB)** |
| S4 current private bytes | 476,848,128 |
| S5 current private bytes | 477,687,808 |
| S6 current private bytes | 477,687,808 |
| Retained logical view charge (ledger, at S5) | 70,133 bytes |
| S0 free VAS / largest free region | 3,135,492,096 / 2,088,398,848 |
| S6 free VAS / largest free region | 3,135,119,360 / 2,088,398,848 |

**The two peak measurements in bold are not the same thing, and the gap between them (66.17 MiB vs. 13.31 MiB) is itself the headline finding of this correction pass**: the OS's own process-lifetime `PeakPagefileUsage` field is authoritative and gap-free (tracked continuously by the kernel, immune to sampling-thread scheduling); the 20 Hz in-process poller is a best-effort sample series that, in this real-SFM run, missed the true peak by roughly 5x.

## 8. Classification of Run 1 evidence

Run 1 is:
- ✅ **Valid real-SFM stage telemetry** — all 6 stages captured cleanly, real provider open/close counters, real ledger state.
- ✅ **Valid process-peak evidence** — the OS `PeakPagefileUsage` field is a legitimate, kernel-tracked ground truth, unaffected by the crash or by sampling cadence.
- ⚠️ **A valid, but demonstrably insufficient, in-process 20 Hz sample series** — real data, but proven (via the gap above) not to reflect the true transient peak inside real SFM.
- ❌ **NOT true external-sampler qualification** — per Section 4's finding, `BackgroundPoller` is in-process; the genuine external sampler (`gate2a_external_sampler.py`) has not yet observed any B2F1 run.

No B2F verdict is rendered. None was requested at this stage.

## 9. Unchanged production/frozen identities

Re-verified at the end of this correction pass — all match their previously recorded SHA-256 exactly: R1D validator/provider, FINAL R3-A2B validator/provider, production Normalizer, production Character Preset, canonical Master, and `sfm_master_authority/selection.py` (the one intentional B2F change, unchanged since). `test_b2a_offline.py` (38/38) and `test_b2b_offline.py` (64/64) both re-ran clean under both interpreters — zero regressions from this correction pass, which touched only `b2f1_campaign_core.py` (bugfix) and added new files (launchers, sampler wrapper); nothing in `sfm_master_authority`, R1D, or the FINAL R3-A2B contract was touched.

## 10. Exact status

**`B2F1A HARNESS CORRECTION PASS — RUN2 READY`**

## Operator instructions — Run 2 only

1. Restart SFM. Do not save any prior experimental scene state.
2. From an ordinary terminal on the host machine (not inside SFM), run:
   ```
   python "E:\SFM Animation Group Master\tests\sidecar\qualification\B2F1A_ExternalSampler_Launch_Run2.py"
   ```
   (or the equivalent copy staged wherever you keep host-side tooling — it needs `gate2a_external_sampler.py` in the same folder, which is already there). Leave this window open; it will find SFM's PID automatically and wait.
3. From SFM's Main Menu, manually select and run `CGN_R3_B2F1A_ExternalSampler_Run2_fixtureA_1p5x.py`.
4. Wait for the terminal window to print "External sampler finished." (a couple of minutes is plenty of margin).
5. Tell me when it's done — I'll read the in-SFM result JSON plus the two external CSV/JSON files and report Run 2's numbers before we move to Run 3.
