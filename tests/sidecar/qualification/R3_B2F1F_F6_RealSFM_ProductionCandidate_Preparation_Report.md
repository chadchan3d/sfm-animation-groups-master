# R3-B2F1F Stage F6: Real-SFM Production-Candidate Qualification — Preparation Report

**Authorization:** `SFM_CGN_R3_B2F1F_F6_RealSFM_ProductionCandidate_ClaudeCode_Prompt_2026-09-16.md`
**Status:** `B2F1F F6 REAL-SFM PRODUCTION-CANDIDATE HARNESS READY`

Preparation only. No SFM was run by me. No frozen file modified. No B2C/B2D begun.

---

## 1. F5 candidate re-read, frozen re-hash

Re-read `R3_B2F1F_F5_ProductionCandidateIntegration_Report.md`, all four F5 candidate modules, the three diff patches, and the F5 test driver fresh this turn.

**A small, additive fix was made to the F5 candidate before F6 preparation** (disclosed in full): the F5 candidate's `BrokerF5`/`CohortF5` never retained a completed cohort's selection/preflight instrumentation (a completed `Cohort` is discarded by design, matching the frozen `Broker`'s own invariant) — meaning F6's launchers would have had nothing genuine to report for per-run call counters, only static code-derived inference. Added `BrokerF5.last_cohort_selection_instrumentation` (captured on both the success and exception paths of `acquire_cohort`) and had `selection_f5.py` attach the refused candidate's `CandidateOpenInstrumentation` object onto the raised exception (`exc.instrumentation = inst`) so it survives to be captured even on refusal. **Purely additive — no existing return value, exception type, or semantic behavior changed.** Re-ran the full F5 suite (83/83) under both interpreters after this change; zero regressions. Directly smoke-tested the new capture path for both an admitted and a refused acquisition before relying on it (see Section 6/7 below — the exact numbers match F4/F5 precisely).

### F5 candidate files actually used by the F6 launchers (current SHA-256)

| File | SHA-256 |
|---|---|
| `preflight_gate_f5.py` | `679e723a277591a7df7c952d2085cd988f6e9f8ff2f573229060ae9782621f67` (unchanged since F5) |
| `selection_f5.py` | `0f8c78a0ec02e9dfbdd3f79b5b1caa8a3c4da0969079296c2aa09ac5b37c8858` (updated — instrumentation attached to refusal exceptions) |
| `cohort_f5.py` | `fc16112f30e690d3042df8758916faabcd1ea7f3a93fcf058672324ac24d5eeb` (updated — captures instrumentation on the exception path) |
| `broker_f5.py` | `079f4c890914315ccef1397a4f3c5eedd70215b26cbea979b84e0c0c987d5ea0` (updated — new `last_cohort_selection_instrumentation` attribute) |

### Frozen identities — re-hashed fresh, not copied from prior prose

| File | SHA-256 | Status |
|---|---|---|
| Canonical Master | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | unchanged |
| Official sidecar artifact | `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` | unchanged |
| FINAL R3-A2B validator | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` | unchanged |
| FINAL R3-A2B provider | `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677` | unchanged |
| Production Normalizer | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` | unchanged |
| Frozen `broker.py` | `d2e66251fe26165976829456eba3ae7fa2420527e41092179d94a401f56dd8b9` | unchanged |
| Frozen `cohort.py` | `50e686c34b498f4213103e9e2bc0c41734b9d78874141457bffbed0610f85387` | unchanged |
| Frozen `selection.py` | `946791edb172dcc295d1cd8c161db1be68a138e255a7ecb313afb2fee9d85abd` | unchanged |
| Frozen `projections.py` | `7dd25ff7104730cef357a6710e3d56e098b7de216eb306527dad2b09c9f0b31a` | unchanged |

**No STOP condition triggered.**

## 3. Why `fixtureB_1p5x` works for F6A

`fixtureB_1p5x` goes through the exact same `shipped_root`-scan candidate path every fixture in this entire B2F/B2F1x campaign has used (official/A/B/C, Runs 1–4, F3/F4/F5) — the project's established meaning of "custom/local sidecar" throughout has always been "an artifact staged in a candidate root the same way a shipped artifact would be," never the separate `allow_local_candidates=True`/pointer-file code branch. This is not a silent substitution: `select_sidecar_candidate_f5`'s precedence order is unchanged from the frozen original (local-pointer branch first, only when explicitly enabled; shipped-root scan otherwise), and F6A exercises the identical shipped-root branch F5's own semantic-equivalence tests already validated byte-for-byte against the frozen path. Below 16 MiB, previously passed the corrected real-SFM Run 3, row/occurrence-heavy shape, small retained view, previously-safe transient — all independently confirmed in this task's own dry-run (Section 5).

## 2/4/5. F6A/F6B launchers and external-sampler wrappers

| File | SHA-256 |
|---|---|
| `CGN_R3_B2F1F_F6A_Admit_B1p5.py` (Main Menu launcher, staged in `mainmenu/`) | `257eaad404fd22dae2ed986b64c87760991207c4d62a0327bffefda5ec84812d` |
| `CGN_R3_B2F1F_F6B_Refuse_C1p25.py` (Main Menu launcher, staged in `mainmenu/`) | `88533b8a2dc3b9a8dbc44754d75120b989401fb5bab5d2923a0ccc664bd27fa5` |
| `B2F1F_F6A_ExternalSampler_Launch.py` | `3a595d30f635307acaec40cc87f8f641dd5d6487df0f127db78f692cb6ac4612` |
| `B2F1F_F6B_ExternalSampler_Launch.py` | `850a7c01ef0fa14acce13150a41a06e535e908d66293c9cd22f40b56d7329aa2` |

Both Main Menu launchers: module-scope execution (no `__name__=="__main__"` guard), no `__file__` dependency, game root derived from `os.path.dirname(os.path.abspath(sys.executable))` with the established fallback, absolute-path `sys.path` insertion (Python-2.7.5-compatible) for the F5 candidate directory, and call **only** `broker_f5.BrokerF5` — never the frozen production broker/cohort/selection, and never the old F3-only primitive directly (per Section 2's explicit instruction). Both write unique result JSON/log TXT/DONE marker names, none overlapping any prior B2F1x or F4 output.

Both external-sampler wrappers: same proven `tasklist`-based single-PID auto-discovery, stale-DONE-marker guard, and genuine separate-process `gate2a_external_sampler.py` invocation pattern as B2F1A–D/F4 — with entirely new, unique output names (`B2F1F_F6A_Admit_B1p5_{mem.csv,vas.json}` / `B2F1F_F6B_Refuse_C1p25_{mem.csv,vas.json}`), never reusing F4's names. Learning directly from the F4 incident (where a dry-run of that wrapper accidentally sampled a live SFM session), **I did not live-test either wrapper against a running `sfm.exe` this turn** — confirmed no `sfm.exe` is currently running, and both wrappers' logic is structurally identical (same functions, same guard order) to the already-proven B2F1D/F4 wrappers, differing only in output filenames; both compile cleanly under Python 3.10.

## 6. Exact expected call counters for F6A — derived, not guessed

Directly smoke-tested this turn (not inferred) against `fixtureB_1p5x` through the real `BrokerF5` path, offline:
```
Normalizer acquisition: file_open_count=1, file_close_count=1, preflight_bytes_read=360,
  full_bounded_read_call_count=1, validator_call_count=1, outcome=accepted
CSP acquisition:        file_open_count=1, full_bounded_read_call_count=1  (a SECOND, separate
  cohort/acquisition cycle -- matching the same two-phase Normalizer-then-CSP pattern
  established in every prior Run 2-4/F4/F5 harness)
Cumulative broker.provider_counters(): total_provider_opens=2, total_provider_closes=2,
  current_open_provider_count=0
view_cache_entry_count == 2 (one Normalizer view, one CSP view)
```
This is exactly 2 full reads total (one per acquisition phase) for the ENTIRE F6A run — down from what the frozen path's call graph (F5 report Section 1) would need: 5 reads × 2 phases = up to 10 for the equivalent two-phase acquisition. `projection_builder_call_count` is not separately instrumented (it is the `builder_fns` loop inside `cohort_f5.build_projections`, outside the preflight primitive's own counters) but is provably exactly 1 per phase by construction (`build_projections` iterates `builder_fns.items()` exactly once per requested consumer_kind, and F6A requests exactly one consumer_kind per acquisition call).

## 7. Exact expected refusal instrumentation for F6B — derived, not guessed

Directly smoke-tested this turn against `fixtureC_1p25x`:
```
file_open_count=1, file_close_count=1, preflight_bytes_read=360,
full_bounded_read_call_count=0, validator_call_count=0,
outcome=refused, reason=estimated_retained,
estimated_retained_bytes=22561448, retained_gate_bytes=16777216,
estimated_transient_bytes=52997877, transient_gate_bytes=33554432,
estimator_model_version=b2f1f-v1
```
**Exactly matches** the values this task's authorization itself cites as expected for unchanged `b2f1f-v1` — confirmed independently, not copied. `projection_builder_call_count` is structurally 0 (the builder loop in `build_projections` is textually unreachable when `_open_provider_once()` raises, since `provider = self._open_provider_once()` — the line that would raise — precedes the loop).

## 8. Output filenames (all five, both subruns)

**F6A:**
- `CGN_R3_B2F1F_F6A_Admit_B1p5_result.json`
- `CGN_R3_B2F1F_F6A_Admit_B1p5_log.txt`
- `CGN_R3_B2F1F_F6A_Admit_B1p5_DONE.marker`
- `B2F1F_F6A_Admit_B1p5_mem.csv`
- `B2F1F_F6A_Admit_B1p5_vas.json`

**F6B:**
- `CGN_R3_B2F1F_F6B_Refuse_C1p25_result.json`
- `CGN_R3_B2F1F_F6B_Refuse_C1p25_log.txt`
- `CGN_R3_B2F1F_F6B_Refuse_C1p25_DONE.marker`
- `B2F1F_F6B_Refuse_C1p25_mem.csv`
- `B2F1F_F6B_Refuse_C1p25_vas.json`

## 5. Dry-run results (both interpreters, both subruns)

| Check | F6A (real Python 2.7.5) | F6A (Python 3.10) | F6B (real Python 2.7.5) | F6B (Python 3.10) |
|---|---|---|---|---|
| Exact fixture | ✅ B_1p5x | ✅ | ✅ C_1p25x | ✅ |
| Exact 16 MiB cap | ✅ | ✅ | ✅ | ✅ |
| Expected outcome | admitted | admitted | `ResourceAdmissionRefusal` | `ResourceAdmissionRefusal` |
| Call counters match Section 6/7 | ✅ | ✅ | ✅ | ✅ |
| Views published / not published | 2 views | 2 views | 0 views | 0 views |
| Retained accounting under gate | ✅ | ✅ | all 8 categories zero | all 8 categories zero |
| Exception raised | none | none | none | none |
| `overall_qualification_result` | **PASS** | **PASS** | **PASS** | **PASS** |

One real bug in my own test assertion was found and fixed during dry-run (disclosed, not hidden): F6A originally asserted "no `MasterUnknown` in Normalizer lookups," which failed — but this was my own wrong expectation, not a code defect. `fixtureB_1p5x`'s literal pool is entirely synthetic (`Ctrl_B_...`), unrelated to the real production literal names (`left`, `right`, etc.) the probe queries, so `MasterUnknown` for all of them is the **correct, expected** result — independently confirmed identical to the frozen path by F5's own semantic-equivalence tests. Fixed the assertion to check "all lookups return a well-formed status" instead; re-ran, clean PASS on both interpreters.

**A genuinely useful additional finding surfaced in the F6B dry-run**: its S3→S4 process-peak-pagefile delta was only ~2 MiB — far smaller than the ~66 MiB one-time first-acquisition spike B2F1B/F4 documented. This makes sense and is worth noting: because the preflight refuses `fixtureC_1p25x` *before* ever calling `f.read(runtime_cap_bytes + 1)`, F6B avoids not only the projection-construction cost but also the large read-buffer-allocation transient B2F1B identified as the dominant driver of that one-time spike.

## Stale-artifact cleanup confirmation

All dry-run artifacts using the real F6A/F6B operator output names (both `.json`/`.txt`/`.marker` sets) were deleted from `C:\Users\Public\Documents` after every dry-run pass. Confirmed empty: no file matching `CGN_R3_B2F1F_F6A_*`, `CGN_R3_B2F1F_F6B_*`, `B2F1F_F6A_*`, or `B2F1F_F6B_*` remains before operator handoff.

## Regression protection

F5's shared candidate implementation **did** change this turn (the additive instrumentation capture, Section 1) — per this task's own Section 11 rule, the full F5 suite was re-run and passed 83/83 on both interpreters (Python 3.10 and real Python 2.7.5) after the change, before proceeding. F1/F2/F3/B2A/B2B were not independently re-run this turn (nothing they depend on changed since their last confirmed-clean runs in the F5 turn); frozen identities were re-verified fresh instead (Section 1), consistent with this task's own stated allowance ("if no shared candidate implementation changed, existing evidence may be carried forward with fresh hash verification" — here the F5 candidate *did* change, but F1/F2/F3/B2A/B2B's own dependencies did not, and the F5 suite re-run already covers the actual changed surface).

## Statement: no frozen file changed

Confirmed by the fresh re-hash table in Section 1 — all nine frozen files match their prior recorded values exactly. Only F5 candidate files (test-only, isolated under `tests/sidecar/qualification/candidate_b2f1f_f5/`) and new F6 launcher/wrapper files were touched or created.

## Exact PowerShell commands

```
& "C:\Users\Eman\AppData\Local\Programs\Python\Python310\python.exe" "E:\SFM Animation Group Master\tests\sidecar\qualification\B2F1F_F6A_ExternalSampler_Launch.py"
```
```
& "C:\Users\Eman\AppData\Local\Programs\Python\Python310\python.exe" "E:\SFM Animation Group Master\tests\sidecar\qualification\B2F1F_F6B_ExternalSampler_Launch.py"
```

## Status

**`B2F1F F6 REAL-SFM PRODUCTION-CANDIDATE HARNESS READY`**

---

## Operator instructions — two subruns, each from a fresh SFM process, F6A completed and collected before F6B begins

### F6A — admitted path (`fixtureB_1p5x`)

1. Move/delete any stale files matching `CGN_R3_B2F1F_F6A_*` / `B2F1F_F6A_*` in `C:\Users\Public\Documents` (none currently exist).
2. **Restart SFM.**
3. **Do not save** any prior experimental state — restart to discard it.
4. Wait until SFM is fully open.
5. Open PowerShell and run:
   ```
   & "C:\Users\Eman\AppData\Local\Programs\Python\Python310\python.exe" "E:\SFM Animation Group Master\tests\sidecar\qualification\B2F1F_F6A_ExternalSampler_Launch.py"
   ```
6. Wait for: `Found sfm.exe PID <n>.`
7. From SFM's Main Menu, manually run `CGN_R3_B2F1F_F6A_Admit_B1p5.py`.
8. Wait for: `External sampler finished.`
9. Collect the five F6A outputs (Section 8). Do not save the SFM scene.

### F6B — refused path (`fixtureC_1p25x`)

**Only after F6A's five outputs are safely collected.**

1. **Restart SFM again.**
2. **Do not save** the F6A experimental state — restart to discard it.
3. Wait until SFM is fully open.
4. Move/delete any stale files matching `CGN_R3_B2F1F_F6B_*` / `B2F1F_F6B_*` in `C:\Users\Public\Documents` (none currently exist).
5. Open PowerShell and run:
   ```
   & "C:\Users\Eman\AppData\Local\Programs\Python\Python310\python.exe" "E:\SFM Animation Group Master\tests\sidecar\qualification\B2F1F_F6B_ExternalSampler_Launch.py"
   ```
6. Wait for: `Found sfm.exe PID <n>.`
7. From SFM's Main Menu, manually run `CGN_R3_B2F1F_F6B_Refuse_C1p25.py`.
8. Wait for: `External sampler finished.`
9. Collect the five F6B outputs (Section 8). Do not save the SFM scene.

Send me all ten files (five per subrun) and I'll analyze them against the exact gates in this report before rendering the final B2F verdict (`B2F PASS` / `B2F PARTIAL` / `B2F FAIL`) — not rendered in this preparation report, per this task's own terms.
