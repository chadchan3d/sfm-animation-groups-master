# R3-B2F1C: Run 3 16 MiB Qualification — Preparation Report

**Authorization:** `SFM_CGN_R3_B2F1C_Run3_16MiB_Qualification_ClaudeCode_Prompt_2026-09-16.md`
**Status:** `B2F1C RUN3 16-MiB HARNESS READY`

---

## 1/2. Corrected Run 3 launcher + external wrapper

| File | SHA-256 |
|---|---|
| `CGN_R3_B2F1C_ExternalSampler_Run3_16MiBCap_fixtureB_1p5x.py` (Main Menu launcher) | `a420fc0ceb3614e9b7c0e0c014ccdd2b93bb7806ab720766c406dcf344a16253` |
| `B2F1C_ExternalSampler_Launch_Run3.py` (terminal wrapper, genuine separate-process sampler) | `192d47730a0a4e7fd981ff63f45310307cdee98b76e076d070be3d65d6489f2c` |

Both follow the exact corrected pattern established in B2F1A/B2F1B: module-scope execution (no `__name__=="__main__"` dependency), no `__file__` dependency, game root derived from `sys.executable`, shared core (`b2f1_campaign_core.py`) loaded by absolute path via `imp.load_source`. The wrapper auto-discovers the single running `sfm.exe` PID via `tasklist`, launches the unmodified `gate2a_external_sampler.py`, targets Run 3's own DONE marker, and writes uniquely-named `B2F1C_ExternalSampler_Run3_16MiBCap_fixtureB_1p5x_mem.csv`/`_vas.json` — never touching SFM itself.

## 3. Exact fixture size

`fixtureB_1p5x.sfmsidecar`: **14,181,874 bytes** — under the 16 MiB (16,777,216-byte) cap by 2,595,342 bytes. Section 4's stop condition ("if fixtureB_1p5x is >=16 MiB") does not apply.

## 4. Proof the 16 MiB cap is used for both acquisitions

Launcher sets `RUNTIME_CAP_BYTES = 16 * 1024 * 1024` and calls:
```python
_core.run_single_fixture_campaign(FIXTURE_NAME, RUN_ID, runtime_cap_bytes=RUNTIME_CAP_BYTES)
```
Inside `b2f1_campaign_core.py`'s `run_single_fixture_campaign`, that single parameter flows into **both** acquisition call sites unchanged:
```python
# line 362 (Normalizer acquisition)
shipped_root=fx["shipped_root"], runtime_cap_bytes=runtime_cap_bytes,
# line 391 (CSP acquisition)
shipped_root=fx["shipped_root"], runtime_cap_bytes=runtime_cap_bytes,
```
Same variable, same value, both call sites — confirmed by direct source inspection (not inferred from any prior report).

## 5. Dry-run results (both interpreters, outside real SFM)

| Interpreter | Exception | Admission | Provider opens/closes | Summary transient peak-pagefile delta |
|---|---|---|---|---|
| Real Python 2.7.5 | none | accepted | 2/2 (balanced) | 21,327,872 bytes (20.34 MiB) — dry-run only, bare-process baseline; not the real-SFM number |
| Python 3.10 | none | accepted | (not separately re-checked; identical code path) | — |

`retained_private_bytes_delta_at_last_full_stage`: 720,896 bytes (~0.69 MiB) in the dry-run. These dry-run numbers are expected to differ from the real-SFM figures (as they did for Run 2 vs. corrected Run 2) since this is a much lighter bare-`python.exe` process — they only confirm the harness itself is bug-free, not the production-relevant magnitude.

## 6. Stale-output cleanup confirmation

All dry-run artifacts for `Run3_16MiBCap_fixtureB_1p5x` (`_result.json`, `_log.txt`, `_DONE.marker`) were deleted from `C:\Users\Public\Documents` after verification. Confirmed empty: no files matching that run ID remain.

## Identities / regression

Re-verified unchanged: canonical Master, official sidecar artifact, FINAL R3-A2B validator/provider, production Normalizer, `sfm_master_authority/selection.py`, and `b2f1_campaign_core.py` itself (SHA identical to the version already regression-tested in B2F1B — this task made **no** changes to the shared core or to any test-harness code; only new, additive per-run files were created). Because no test-harness code changed, the B2A/B2B regression evidence already recorded in B2F1B (38/38 and 64/64, both interpreters) remains sufficient and was not re-run.

## 7. Operator instructions — Run 3 only

1. Remove/move any stale files matching `Run3_16MiBCap_fixtureB_1p5x` in `C:\Users\Public\Documents` (none currently exist, per Section 6, but check before starting).
2. **Restart SFM.**
3. **Do not save** any prior experimental scene state — restart to discard it.
4. Wait until SFM is fully open.
5. From PowerShell:
   ```
   & "C:\Users\Eman\AppData\Local\Programs\Python\Python310\python.exe" "E:\SFM Animation Group Master\tests\sidecar\qualification\B2F1C_ExternalSampler_Launch_Run3.py"
   ```
6. Wait for: `Found sfm.exe PID <n>.`
7. From SFM's Main Menu, manually invoke `CGN_R3_B2F1C_ExternalSampler_Run3_16MiBCap_fixtureB_1p5x.py`.
8. Wait for: `External sampler finished.`
9. Collect all five outputs: the in-SFM `CGN_R3_B2F1_ExternalSampler_Run3_16MiBCap_fixtureB_1p5x_{result.json,log.txt,DONE.marker}` plus the external `B2F1C_ExternalSampler_Run3_16MiBCap_fixtureB_1p5x_{mem.csv,vas.json}`.

## Status

**`B2F1C RUN3 16-MiB HARNESS READY`**

Per the hard stop: Run 4 and B2C/B2D remain unauthorized. This report stops before the real operator Run 3.
