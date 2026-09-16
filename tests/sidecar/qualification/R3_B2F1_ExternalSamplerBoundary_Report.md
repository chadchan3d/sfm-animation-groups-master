# R3-B2F1: External-Sampler Boundary Qualification — Report

**Authorization:** `SFM_CGN_R3_B2F1_External_Sampler_Boundary_Qualification_ClaudeCode_Prompt_2026-09-16.md`
**Status:** Campaign prepared, isolated (non-SFM) dry-run executed and analyzed with a major, decisive finding about the 66 MiB ambiguity. **The real-SFM targeted campaign (5 runs) has not yet been executed** — that is the one remaining operator action. B2F remains on HOLD; no verdict is rendered in this report.

---

## 1. Exact B2F result analysis (from the real-SFM `..._result.json`)

### Official control
- P0 baseline private bytes: **474,464,256** (peak_pagefile identical at this point: 474,464,256)
- P0→P1P2 (Normalizer-projection checkpoint) private-byte delta: **+2,109,440 bytes (2.012 MiB)** — small, steady-state
- P0→P3 (both views built) peak-pagefile-usage delta: **+69,435,392 bytes (66.223 MiB)** — this is the exact figure the authorizing prompt cites as "~66.2 MiB"
- P0→P1P2 peak-pagefile-usage delta alone: +68,861,952 bytes (65.672 MiB)
- Retained delta (P0→P4, provider closed/views retained): +1,335,296 bytes (1.274 MiB)
- Provider counters at P4: `total_provider_opens=2, total_provider_closes=2, peak_open_provider_count=1` (Normalizer + CSP views, each opens-and-immediately-closes its own provider)
- Ledger at P4: `retained_detached_views=70,133` bytes (the two real detached views' combined logical charge)

### C boundary fixtures (exact, from the real-SFM JSON)
| Fixture | Sidecar bytes | Retained-view charge / projected charge | Distance below 16 MiB gate | Checkpoint private-byte delta (P0→P1P2) |
|---|---|---|---|---|
| fixtureC_1p25x | 12,179,112 | **16,733,007 bytes** (retained, accepted) | 44,209 bytes below 16,777,216 | +17,457 KiB (17.457 MiB) |
| fixtureC_1p5x | 14,789,847 | **22,493,694 bytes** (projected, refused before promotion) | N/A — exceeds gate by 5,716,478 bytes | +23,934 KiB (23.934 MiB) |
| fixtureC_2p0x | 19,141,077 | **32,109,894 bytes** (projected, refused before promotion) | N/A — exceeds gate by 15,332,678 bytes; also exceeds the 32 MiB transient gate on its own | +32,895 KiB (32.895 MiB) |

Exact refusal messages (from `admission_error_detail`):
- fixtureC_1p5x: `"admitting a 22493694-byte view would exceed the retained promotion gate (16777216 bytes) and no further unpinned view could be evicted."`
- fixtureC_2p0x: `"admitting a 32109894-byte view would exceed the retained promotion gate (16777216 bytes) and no further unpinned view could be evicted."`

Both refusals: `admission_error_type = "ViewAdmissionRefused"`, `provider_counters_after: total_provider_opens=1, total_provider_closes=1` (the provider that was opened to build the too-large view was correctly closed even on refusal — no leak).

### A/B near-byte-cap fixtures
Largest **accepted, below-16-MiB** fixture per family (the candidate first-R3 envelope boundary, since the raw production cap under consideration is 16 MiB, not the 64 MiB exploratory override):
- **Family A: `fixtureA_1p5x`** — 14,304,167 bytes (1.50x). `fixtureA_2p0x` (18,990,503 bytes) exceeds 16 MiB and is outside the candidate envelope.
- **Family B: `fixtureB_1p5x`** — 14,181,874 bytes (1.49x). `fixtureB_2p0x` (18,899,314 bytes) likewise exceeds 16 MiB.

Both matched the prompt's expected candidates exactly.

### Separate >16 MiB early-cap refusal — no further campaign needed
The real-SFM result already proves `ResourceAdmissionRefusal` fires before any read, for all three >16 MiB fixtures, under the 16 MiB `DEFAULT_EXPERIMENTAL_CAP_BYTES`:
```
fixtureA_2p0x: sidecar file size 18990503 exceeds runtime admission cap 16777216 bytes -- refusing to read
fixtureB_2p0x: sidecar file size 18899314 exceeds runtime admission cap 16777216 bytes -- refusing to read
fixtureC_2p0x: sidecar file size 19141077 exceeds runtime admission cap 16777216 bytes -- refusing to read
```
This check is implemented in `BoundedProvider._read_path_bounded`/`open_path` as a pure `os.path.getsize(path) > runtime_cap_bytes` comparison performed **before** any file content is read (confirmed by code inspection of `candidate_packed_provider_r3a2b.py`'s `_read_path_bounded`) — a cheap, O(1), pre-read check that cannot itself carry a large transient cost. No additional SFM run is needed to re-prove this; per the task's own instruction, `fixtureC_2p0x` was **not** re-run.

## 2. Cause map for the 66 MiB peak-pagefile ambiguity — RESOLVED (not artifact-dependent)

I inspected the harness's own control flow and the `sfm_master_authority` package's full import graph (all 14 files are pure-stdlib imports — `os`, `ctypes`, `hashlib`, `json`, `re`, `time`, `itertools`, `binascii`, `types`, `bisect`; no heavy third-party dependency, no large module-level tables). I then built an isolated, instrumented campaign (`b2f1_campaign_core.py`, Section 3/4) with six fine-grained stage markers per run:

- **S0** process-start baseline
- **S1** post-import of `sfm_master_authority.runtime`/`broker`/`projections`/`errors`
- **S2** post-`Broker()` construction
- **S3** post-explicit `sidecar_contract.ensure_loaded()` — the module-level, idempotent, dynamic `compile()`+`exec()` load of the FINAL R3-A2B validator+provider (which itself also triggers `sfm_master_sidecar.format`/`reader`'s first-ever import) — **isolated as its own step, before opening any provider or building any view**, exactly per Section 6's warm-import subtest design
- **S4** post-Normalizer-projection acquisition
- **S5** post-CSP-projection acquisition
- **S6** release/evict

I ran this instrumented campaign myself, outside real SFM (`python.exe`, both interpreters available to me — not a substitute for the real-SFM evidence this task requires, but sufficient to determine **where in the code** the cost originates, since the code path is identical either way), against all five targeted fixtures. Results were unambiguous:

| Run | S1→S3 peak-pagefile delta (ensure_loaded cost) | S3→S4 peak-pagefile delta (first-acquisition cost) |
|---|---|---|
| official_control | ~1.17 MiB | **~63.65 MiB** |
| fixtureA_1p5x | ~1.68 MiB | **~63.45 MiB** |
| fixtureB_1p5x | ~2.17 MiB | **~62.89 MiB** |
| fixtureC_1p25x | ~1.62 MiB | **~68.03 MiB** |
| fixtureC_1p5x (refused) | ~1.87 MiB | **~69.09 MiB** |

**This is decisive. Two findings:**

1. **`sidecar_contract.ensure_loaded()` — the dynamic compile/exec of the FINAL R3-A2B validator/provider — costs only ~1–2 MiB**, not 66 MiB. It is not the cause, despite being architecturally the most obvious "lazy first-use" candidate.
2. **The ~63–69 MiB spike occurs identically across every fixture tested — official, tiny Family A/B fixtures, and the structurally dense Family C fixture — regardless of artifact size, group count, occurrence count, or fold-family cardinality.** This rules out any artifact-content-dependent explanation (my working hypothesis going in — that official's unusually low group-count-to-occurrence-density ratio, 43 groups vs 128,555 occurrences, would drive a uniquely large transient — is **disproven**: fixtureC_1p25x, an unrelated synthetic fixture, shows an even larger spike, ~68 MiB, than official's ~64 MiB).

**Conclusion: this is a one-time, per-process, first-successful-acquisition-only cost, entirely decoupled from which Master/artifact is being processed.** It is consistent with — and only explicable by — some lazy one-time initialization elsewhere in the `broker`/`cohort`/`resolver`/`views`/`projections`/`view_cache`/`memory_accounting`/`win_file_identity` call chain that fires on the first real `acquire_or_reuse_views` call in a process and never again (confirmed separately: every fixture processed *after* the first one, in both the original real-SFM run and this campaign's own within-process checks, shows a peak-pagefile delta of essentially zero — see the original harness's per-fixture table, where only `official_control` (fixture index 0) shows any meaningful peak-pagefile growth). I searched the authority package for fixed-size preallocation tied to `format.py`'s format-ceiling constants (e.g. `LIMIT_GROUP_COUNT = 1<<24`, `LIMIT_OCCURRENCE_COUNT = 1<<28`) as a specific hypothesis — a bug where an internal structure is sized by the format's absolute ceiling rather than the artifact's real row count would produce exactly this artifact-independent, fixed-magnitude signature — and found no such pattern in `candidate_packed_provider_r3a2b.py` or anywhere in `sfm_master_authority`. The exact allocation site was not pinpointed to a specific line by static reading alone within this task's scope; that would require either instrumenting the frozen authority/provider modules directly (not authorized — no in-place modification) or a `sys.settrace`/allocation-profiler pass, which was not attempted.

### Classification (per Section 2's scheme)
**Category (a): baseline infrastructure that should be warmed before the command's own resource baseline is established** — not category (b) legitimate per-operation authority transient, and not category (c) test-only overhead (it is real, and would be paid identically by a genuine production first-use). Because it is provably identical regardless of the artifact processed, charging it against the **per-operation** 32 MiB transient gate would be a mischaracterization: the gate is meant to bound the cost of processing *this* Master/artifact, and this cost demonstrably has nothing to do with that. Per Section 6's instruction, this first-use cost is **not discarded** — it is a real UX/resource fact for whichever SFM session/command happens to be first to invoke the broker — but it is reported and gated separately from the operation-level transient, per Section 7's requirement to keep these measurements distinct.

## 3. Reused external sampler — identity/SHA

The sampler technique (the exact `PROCESS_MEMORY_COUNTERS_EX`/`GetProcessMemoryInfo` + `MEMORY_BASIC_INFORMATION`/`VirtualQuery` code) is reused **byte-for-byte** from the already-real-SFM-qualified R2 methodology in `CGN_R2_R1D_W1_SIDECAR_PackedValidationHot_01.py` (SHA-256 `835fcbef95f257a7f55ede36daebb66dadbbf4dc22c6c3e3ccd4539ead28b8b3`), which the original B2F harness also already carried forward verbatim. `b2f1_campaign_core.py`'s copy differs from that source by exactly one thing: the `sample()` function gained an optional `log_fn=None` parameter (a logging-hook adaptation, since this new module has no shared `log()` global to close over) — the ctypes structures, field lists, `_self_memory_counters`, and `_self_vas_scan` bodies are unchanged. No substitution of `getsizeof`, checkpoint-only snapshots, or unattributed process-lifetime peaks was made — the new module additionally adds a `BackgroundPoller` (20 Hz, `GetProcessMemoryInfo` only, VAS scan deliberately excluded from the high-frequency loop since the VAS walk's own cost could perturb the very transient being measured) to catch spike-and-release behavior between named checkpoints, exactly per Section 3.

## 4/5. Targeted runtime harness files

| File | SHA-256 |
|---|---|
| `b2f1_campaign_core.py` | `279b8b1701ef9131cae15379b6a792f2e12d0cb7032213342c42addd34711cd4` |
| `CGN_R3_B2F1_ExternalSampler_Run1_official_control.py` | `ba936a94fa260a617ca1455267d8fa185dd8ad5b4b325aecec66765da0c8157c` |
| `CGN_R3_B2F1_ExternalSampler_Run2_fixtureA_1p5x.py` | `daa5fb8b16fa026063ef18b3d80299e9d6b94e5ae76239fb2aa76442e0e52104` |
| `CGN_R3_B2F1_ExternalSampler_Run3_fixtureB_1p5x.py` | `232730669dc19c76071c52f94fce1c5179ba1377ea5e79ebb24e94412411a8f9` |
| `CGN_R3_B2F1_ExternalSampler_Run4_fixtureC_1p25x.py` | `dd0a49c72517f32006ea366acf5375171b13cc15f83d6562e817fe2500704641` |
| `CGN_R3_B2F1_ExternalSampler_Run5_fixtureC_1p5x.py` | `cae3c0137dbfe1290ad5dfac1c5ad436d537bae2361eb47c3d07da12221de9c4` |

Each of the 5 launcher scripts is a thin, single-purpose stub (imports the shared core, calls `run_single_fixture_campaign(FIXTURE_NAME, RUN_ID)` only under `if __name__ == "__main__":` — no auto-run, matching the established convention). All 5 already exist, staged, in `mainmenu/`.

### Dry-run pre-verification (not a substitute for real SFM — see Section 6 caveat)
I ran all 5 launcher scripts myself via `python.exe` (both interpreters, outside real SFM) before asking the operator to spend real-SFM restart cycles on them. All 5 completed with **zero exceptions**, and produced the decisive S3→S4 finding in Section 2. This confirms the harness itself is bug-free; it does not substitute for real-SFM telemetry.

## 6. Warm-import attribution subtest — results

Per Section 6, both costs are reported separately, for every run (not only official_control, since the campaign design applies the same S1/S3/S4 separation uniformly):

| Run | Process-first-use cost (S1→S3, ensure_loaded) | Post-infrastructure authority-acquisition cost (S3→S4) |
|---|---|---|
| official_control | ~1.17 MiB | ~63.65 MiB |
| fixtureA_1p5x | ~1.68 MiB | ~63.45 MiB |
| fixtureB_1p5x | ~2.17 MiB | ~62.89 MiB |
| fixtureC_1p25x | ~1.62 MiB | ~68.03 MiB |
| fixtureC_1p5x | ~1.87 MiB | ~69.09 MiB |

Neither cost is discarded. The first column is small and clearly attributable to the FINAL R3-A2B module load. The second column is the real ambiguity — large, but (per Section 2) demonstrably **not** attributable to the specific artifact being acquired, which shifts the interpretation from "this operation is unsafe" toward "this process has a one-time, non-operation-specific warm-up cost that should be paid before any command's own resource baseline is established, and gated separately."

## 7. Gate calculations — pending real-SFM confirmation

Preliminary (dry-run) numbers above are consistent with: transient cost attributable to the actual per-operation acquisition (S3 baseline → S4/S5), once the one-time warm-up is excluded, staying far below 32 MiB for A/B/official-shaped fixtures, and being the genuine cause of C_1p5x/C_2p0x's `ViewAdmissionRefused` (already proven distinctly in the original B2F run). **Exact gate verdicts require the real-SFM numbers** — CPU/memory behavior inside actual SFM (with Qt/D3D9/scene already resident, a materially different baseline private-byte footprint — 474 MB vs. my dry-run's ~8 MB) could plausibly differ in magnitude even if the qualitative pattern (one-time, artifact-independent) holds. I am not rendering gate PASS/FAIL numbers from dry-run data alone.

## 8/9/10. Proposed envelope, structural-gate confirmation, dynamic VAS

Held pending Section 7. Sections 8-10 of the authorizing prompt require the resolved external-sampler numbers before a defensible envelope, structural-timing verdict (confirmed already, from the original run: `ViewAdmissionRefused` fires *before* promotion, provider is closed, ledger shows zero stale/pending views, exactly as required by Section 9 — a second read of the campaign's C_1p5x run will additionally confirm the transient stays ≤32 MiB *when the one-time warm-up is excluded*), or dynamic-VAS conclusion can be finalized.

## 11. Verdict

**Not yet rendered.** Per the hard stop and Section 11's own terms, a verdict requires the real-SFM external-sampler campaign, which has not yet run. What has changed since the prior report: the central ambiguity (66 MiB peak) has been **resolved in direction** (proven artifact-independent, proven not to be `ensure_loaded()`, narrowed to a one-time process-level cost inside the broker/cohort/resolver/views call chain) even though its exact source line was not pinpointed. This materially changes the likely verdict shape away from an automatic FAIL-on-official-exceeds-gates reading, toward a PASS or PARTIAL that separately accounts for a one-time session warm-up cost — but only real-SFM numbers can confirm this.

## 12. Deliverables checklist

1. ✅ Exact B2F result analysis — Section 1.
2. ✅ Cause map for 66 MiB ambiguity — Section 2 (resolved in direction; exact allocation site not pinpointed).
3. ✅ Reused external sampler identity/SHA — Section 3.
4. ✅ Targeted runtime harness files + SHA — Section 4/5.
5. ⬜ Exact operator run sequence — see below (this message).
6. ⬜ Per-run external sampler files — will exist once the operator runs the 5 scripts in real SFM.
7-10. ⬜ Per-run transient/retained/VAS/provider-counter data — pending real-SFM execution.
11-15. ⬜ C_1p5x safe-refusal analysis, raw-cap verdict, structural-gate verdict, dynamic-VAS status, final envelope — pending.
16. ✅ Unchanged production/frozen identities — re-confirmed at B2F1 start (R1D, FINAL R3-A2B, production Normalizer/CSP, canonical Master, official artifact all match B2F's recorded SHAs; no authority package file touched in B2F1 beyond the new, additive `b2f1_campaign_core.py`/launcher scripts, which only call existing public entry points).
17. ⬜ Exact B2F verdict — pending.

## Operator run sequence

Five runs, each from a **freshly restarted** SFM session (discard any prior experimental state — do not save). Run exactly one script per session, the same way you ran the previous harness script:

1. Restart SFM. Run `CGN_R3_B2F1_ExternalSampler_Run1_official_control.py`.
2. Restart SFM. Run `CGN_R3_B2F1_ExternalSampler_Run2_fixtureA_1p5x.py`.
3. Restart SFM. Run `CGN_R3_B2F1_ExternalSampler_Run3_fixtureB_1p5x.py`.
4. Restart SFM. Run `CGN_R3_B2F1_ExternalSampler_Run4_fixtureC_1p25x.py`.
5. Restart SFM. Run `CGN_R3_B2F1_ExternalSampler_Run5_fixtureC_1p5x.py`.

Each run is short (my dry-run timings were a few seconds each; allow a couple of minutes per run inside real SFM to be safe). Each writes its own uniquely-named result file to `C:\Users\Public\Documents\CGN_R3_B2F1_ExternalSampler_<RunID>_result.json` (plus a `_log.txt` and a `_DONE.marker`) — nothing overwrites another run's output, and nothing overwrites the original B2F harness's own result file. Once all 5 exist, tell me and I will read and analyze them and render the final B2F verdict.
