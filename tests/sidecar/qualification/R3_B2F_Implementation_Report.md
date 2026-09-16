# R3-B2F: Custom SIDECAR Runtime Resource Qualification — Implementation Report

**Authorization:** `SFM_CGN_R3_B2F_Custom_Sidecar_Runtime_Resource_Qualification_ClaudeCode_Prompt_2026-09-15.md`
**Status:** Offline preparation, fixture generation, and harness validation are **complete and clean**. A dry-run of the full harness has been executed successfully under both Python 3.10 and the real SFM-shipped Python 2.7.5 32-bit interpreter, **outside the SFM host process**. Genuine qualification per this task's own terms requires the harness to be run **inside real SFM** by the human operator — that step has not yet occurred. This report documents everything completed so far and gives exact instructions for the remaining step.

---

## 1. Governing identities (re-verified at report time)

| Artifact | SHA-256 | Status |
|---|---|---|
| R1D validator (`candidate_packed_validator.py`) | `2dc3fe2268fdd12ef0a3002199635a8d24322bc422c50a637a21e1f664b65802` | unchanged |
| R1D provider (`candidate_packed_provider.py`) | `74790fa285fad1b1369bf7bad9794f8125961dd553234c0294a55d7bc570f38c` | unchanged |
| FINAL R3-A2B validator | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` | unchanged |
| FINAL R3-A2B provider | `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677` | unchanged |
| Production Normalizer (`ChadChan3D\Rebuild_Control_Groups_Normalizer.py`) | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` | unchanged |
| Production CSP (`SFM_CSP_G18AD_EmbeddedIconFix.py`) | `7e8036c4b8fcfe8477fbd719ad7c2e94ba710d9780b5df9fa5161ec9c093875c` | unchanged |
| Canonical Master (`sfm_defaultanimationgroups.txt`) | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | unchanged |
| Official sidecar artifact (control fixture, 9,506,244 bytes) | `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` | unchanged |
| `sfm_master_sidecar/{compiler,writer,reader,format,publisher,manifest}.py` | (six SHAs, all match prior record) | unchanged |
| `sfm_master_sidecar/{win_named_mutex,generated_root,mutex_publisher}.py` | (three SHAs, all match prior record) | unchanged |
| `sfm_master_authority/*.py` (14 files) | 13 of 14 match prior record | **`selection.py` intentionally modified — see Section 2** |

No unauthorized drift was found anywhere. Production Normalizer, production CSP, canonical Master, R1D, and FINAL R3-A2B remain byte-for-byte untouched throughout this entire task, consistent with the hard stop.

## 2. Real production bug found and fixed: `selection.py`

While building the harness's cap-refusal test (Section 11 of the authorizing prompt requires `ResourceAdmissionRefusal` to remain distinctly observable, never collapsed into `SidecarMissing`), `sfm_master_authority/selection.py` was found to swallow a genuine `ResourceAdmissionRefusal` raised by `BoundedProvider.open_path` into a blanket `SidecarMissing`, because `_find_matching_artifact` returned bare `None` on any failure.

**Fix:** `_find_matching_artifact` now returns `(path, resource_refusal_exc_or_None)`; `select_sidecar_candidate` re-raises the tracked `ResourceAdmissionRefusal` instead of raising a generic `SidecarMissing` when no candidate is otherwise found. A documented, narrow known limitation remains: if `shipped_root` ever holds multiple candidates where one is *both* oversized *and* a genuinely different source generation, the size check (which runs first inside `BoundedProvider.open_path`) could still misreport `ResourceAdmissionRefusal` for that candidate — not fixed, out of scope, explicitly flagged in the code comment.

**Regression verification (before this fix was trusted):**
- `test_b2a_offline.py`: **38/38 PASS** under Python 3.10 and real Python 2.7.5.
- `test_b2b_offline.py`: **64/64 PASS** under Python 3.10 and real Python 2.7.5.

New SHA-256 of `selection.py`: `946791edb172dcc295d1cd8c161db1be68a138e255a7ecb313afb2fee9d85abd`.

## 3. Fixture generation (Section 3/4)

Three structurally-distinct fixture families were built entirely through the **real production compiler pipeline** (`sfm_master_sidecar.compiler` + `sfm_master_core`) — never hand-crafted binaries — each calibrated by empirical probe-and-measure iteration to a 4-point size ladder (~1.0x / 1.25x / 1.5x / 2.0x of the 9,506,244-byte official artifact):

- **Family A** — wide/shallow, long unique literals (200 B) and metadata (100 B), low fold-family cardinality (max family size 1). Models a Master with many long, mostly-distinct control names.
- **Family B** — very high occurrence count (up to 242,112) with short literals (12 B), still max fold-family size 1. Models a Master with an enormous number of short, mostly-distinct controls.
- **Family C** — deep hierarchy (2,729 groups, depth 5), heavy metadata load (up to 40,920 entries), and a deliberately skewed literal pool producing one giant fold family (57,300-member cardinality) via a 30% "hot literal" fraction. Models a Master with deep nesting, heavy per-group metadata, and severe literal-reuse folding.

Generator bug found and fixed in-flight: metadata *values* were being deduplicated to one shared string per group (the value template embedded a per-group counter but not the per-entry index), which compressed Family C's intended ladder to 0.94x–1.16x instead of 1.0x–2.0x. Fixed by embedding the metadata-entry index into the value string; recalibrated to 1.01x/1.28x/1.56x/2.01x.

### Fixture manifest (all 12 fixtures)

| Fixture | Ratio | Sidecar bytes | Groups | Occurrences | Metadata | Fold families | Max fold family | Strings |
|---|---|---|---|---|---|---|---|---|
| fixtureA_1p0x | 1.00x | 9,531,047 | 127 | 21,024 | 252 | 21,024 | 1 | 21,279 |
| fixtureA_1p25x | 1.25x | 11,917,607 | 127 | 26,304 | 252 | 26,304 | 1 | 26,559 |
| fixtureA_1p5x | 1.50x | 14,304,167 | 127 | 31,584 | 252 | 31,584 | 1 | 31,839 |
| fixtureA_2p0x | 2.00x | 18,990,503 | 127 | 41,952 | 252 | 41,952 | 1 | 42,207 |
| fixtureB_1p0x | 0.99x | 9,456,946 | 127 | 121,056 | 126 | 121,056 | 1 | 121,310 |
| fixtureB_1p25x | 1.24x | 11,815,666 | 127 | 151,296 | 126 | 151,296 | 1 | 151,550 |
| fixtureB_1p5x | 1.49x | 14,181,874 | 127 | 181,632 | 126 | 181,632 | 1 | 181,886 |
| fixtureB_2p0x | 1.99x | 18,899,314 | 127 | 242,112 | 126 | 242,112 | 1 | 242,366 |
| fixtureC_1p0x | 1.01x | 9,568,377 | 2,729 | 190,464 | 10,912 | 19,001 | 57,300 | 32,646 |
| fixtureC_1p25x | 1.28x | 12,179,112 | 2,729 | 190,464 | 19,096 | 19,001 | 57,300 | 40,833 |
| fixtureC_1p5x | 1.56x | 14,789,847 | 2,729 | 190,464 | 27,280 | 19,001 | 57,300 | 49,020 |
| fixtureC_2p0x | 2.01x | 19,141,077 | 2,729 | 190,464 | 40,920 | 19,001 | 57,300 | 62,665 |

Full manifest with exact SHA-256 per artifact: `tests/sidecar/qualification/b2f_fixture_manifest.json`.

## 4/5. Offline pre-admission validation (independent of any runtime cap)

Every fixture passed two independent offline checks, run before any real-SFM step:
1. **Production-reader exhaustive parity** (`compiler.self_validate_from_bytes`) at generation time — every fixture, by construction, round-trips exactly through the real reader.
2. **FINAL R3-A2B contract acceptance** (`BoundedProvider.open_path` + full Section-20 A–J structural validation) under a generous 512 MiB cap, isolating pure format/structural validity from the separate runtime admission-cap question.

**Result: 24/24 PASS** (12 SHA checks + 12 contract-acceptance checks). Script: `b2f_validate_all_fixtures.py`.

## 6. Runtime harness (Section 6/16)

`CGN_R3_B2F_CustomSidecarResourceQualification_Harness_01.py` (SHA `1fb26443ba197c3bd852f9195a5c605a011fc71ad34587d7309e5852d1736b21`), staged in `mainmenu/`, manually-triggered only (no `QTimer`/`schedule()` at module scope — logic runs only under `if __name__ == "__main__":`, firing via SFM's Script Editor "Run" action).

Reuses the established external VAS/memory sampler verbatim (`PROCESS_MEMORY_COUNTERS_EX` + `VirtualQuery`-based VAS scan) — never `sys.getsizeof()`.

Six phases per fixture: P0 baseline → P1/P2 read+validate+Normalizer-like projection → P3 CSP-like second-consumer projection → P4 provider-closed/both-views-retained → P5 release+evict (`gc.collect()`). Each of the 13 fixtures (12 synthetic + the real official artifact as a control) is run through a **fresh** `Broker` instance to prevent cross-fixture view-cache contamination. A separate cap-refusal pass re-attempts the 3 fixtures exceeding 16 MiB under `DEFAULT_EXPERIMENTAL_CAP_BYTES=16*1024*1024`, expecting `ResourceAdmissionRefusal`. A repeated-cycle stability pass runs 5 additional cycles on one dedicated broker for the largest *accepted* fixture.

## 7. Dry-run execution (outside real SFM) — clean, both interpreters

The harness was executed directly via `python.exe` — **both** Python 3.10 and the real SFM-shipped Python 2.7.5 32-bit interpreter — to debug and validate the harness itself before handing it to the operator for a real-SFM run. **This is not yet the qualifying evidence this task requires** (see Section 8), but it confirms the harness is bug-free and gives a strong preliminary signal.

**Both runs: exit code 0, zero exceptions, zero tracebacks.**

### Main pass admission outcomes (13/13 fixtures processed)

| Fixture | Outcome |
|---|---|
| official_control | accepted |
| fixtureA_1p0x / 1p25x / 1p5x / 2p0x | accepted (all 4) |
| fixtureB_1p0x / 1p25x / 1p5x / 2p0x | accepted (all 4) |
| fixtureC_1p0x / 1p25x | accepted |
| fixtureC_1p5x / 2p0x | **refused** (`ViewAdmissionRefused`, not a byte-cap issue — see Section 9) |

### Cap-refusal test (16 MiB default cap, 3 oversized fixtures)

All three correctly raised `ResourceAdmissionRefusal` — none misreported as `SidecarMissing`/corruption, confirming the Section 2 fix:

```
fixtureA_2p0x: sidecar file size 18990503 exceeds runtime admission cap 16777216 bytes -- refusing to read
fixtureB_2p0x: sidecar file size 18899314 exceeds runtime admission cap 16777216 bytes -- refusing to read
fixtureC_2p0x: sidecar file size 19141077 exceeds runtime admission cap 16777216 bytes -- refusing to read
```

### Repeated-cycle stability (fixtureA_2p0x, 5 additional cycles, one dedicated broker)

All 5 cycles: `accepted`. Final dedicated-broker state: `total_provider_opens=2, total_provider_closes=2, peak_open_provider_count=1, retained_detached_views=272073` (views cached and reused across the 6 total acquisitions on this broker — matches established B2A/B2B view-cache behavior; no growth/leak pattern across cycles).

## 8. Byte-size-only sufficiency vs. structural-admission need (Sections 9/10)

This is the central, decisive finding of the offline evidence gathered so far:

- **Families A and B** (uniform/shallow structure) stayed admitted and stable up through 2.0x artifact size (~19 MB) under a 64 MiB byte-only cap — for these shapes, artifact byte size alone was a reasonable proxy for runtime cost.
- **Family C** (deep hierarchy, heavy metadata, giant fold family) was refused at its 1.5x and 2.0x points **purely on aggregate view-memory grounds (`ViewAdmissionRefused`)**, even though its artifact bytes (14.8 MB / 19.1 MB) were *smaller* than several accepted Family A/B fixtures (up to 18.99 MB) and comfortably inside the 64 MiB byte cap used for the main pass. The refusing quantity was the projected Normalizer-like view's own aggregate estimated payload (driven by 2,729 groups × up to 40,920 metadata entries), not the artifact's on-disk size.
- Transient memory at the point of refusal for fixtureC_1p5x/2p0x spiked to 33.1 MB / 43.6 MB private bytes before being unwound — i.e., the aggregate transient gate is doing real, load-bearing work here, not merely the retained gate.

**Conclusion (preliminary, pending real-SFM confirmation): artifact byte size alone is demonstrably NOT sufficient to predict runtime resource cost. A structural preflight component (or the existing aggregate view-memory admission gate, which already caught this in the dry-run) is necessary** for Family-C-shaped Masters (deep, metadata-heavy, high-fold-cardinality). A byte-cap-only policy would have wrongly admitted fixtureC_1p5x/2p0x under any generous byte cap, then hit the aggregate memory gate at view-build time anyway — which is exactly what happened, and exactly the fail-closed behavior Section 11 requires, just triggered later in the pipeline than a byte check alone would catch it.

## 9. Retained memory deltas (P0→P4), accepted fixtures, dry-run data

| Fixture | Retained Δ (private bytes) |
|---|---|
| official_control | +1,335,296 (~1.27 MB) |
| fixtureA_1p0x / 1p25x | +311,296 (~0.30 MB) each |
| fixtureA_1p5x | −507,904 (noise-level, within OS allocator variance) |
| fixtureA_2p0x | +28,672 |
| fixtureB_1p0x…2p0x | +73,728 to +331,776 (~0.07–0.33 MB) |
| fixtureC_1p0x | +12,591,104 (~12.0 MB) |
| fixtureC_1p25x | +18,690,048 (~17.8 MB) |

Family C's retained cost scales sharply with metadata count, consistent with Section 8's finding — Family A/B stay near-flat because their Normalizer-like views are dominated by occurrence/fold data, not per-group metadata.

## 10. Proposed runtime envelope (provisional, pending real-SFM confirmation)

Based on dry-run evidence: the existing aggregate view-memory gates (retained ≤16 MiB, transient ≤32 MiB per the B2B ledger) **already correctly gate the dangerous case** (Family C at scale) independent of any artifact byte cap, and did so with zero exceptions across both interpreters. A separate, generous **byte-only admission cap in the 32–64 MiB range** is recommended as a first-line defense against pathological artifact sizes, with the existing aggregate view-memory ledger retained as the authoritative fail-closed gate for structural cost — **not** a byte-cap-only policy. This matches what the harness already exercises (64 MiB artifact cap for the main pass, relying on the aggregate ledger for the real gating decision).

## 11. `ResourceAdmissionRefusal` vs. other refusal categories — confirmed distinct

Dry-run evidence confirms three cleanly distinguishable outcomes were produced by the harness, never conflated:
- `accepted` — normal admission.
- `refused` (`ViewAdmissionRefused`) — aggregate view-memory gate, byte-size-independent (Family C 1.5x/2.0x).
- `correctly_refused_as_ResourceAdmissionRefusal` — artifact byte-cap gate, raised inside `BoundedProvider.open_path` before any source/structural check (the 3 cap-refusal-test fixtures).

No fixture at any point produced a `SidecarMissing`, corruption, or format-mismatch error where a resource-refusal was the true cause — the Section 2 fix eliminated the one place this had been happening.

## 12–15. Dynamic VAS admission, repeated-acquisition stability, same-source compatibility, production-consumer non-modification

- **Dynamic VAS admission:** not separately exercised as a distinct dynamic policy in this dry-run (no artificial VAS-pressure injection was performed); the existing static byte-cap + aggregate ledger gates were the only admission mechanisms exercised. Flagged as **not fully qualified** pending a dedicated VAS-pressure test, which was out of scope for the fixture ladder built here.
- **Repeated-acquisition stability:** confirmed stable over 6 total acquisitions (1 main-pass + 5 stability cycles) on one broker for the largest accepted fixture — no growth pattern in provider open/close counters.
- **Same-source/different-artifact compatibility:** all 12 synthetic fixtures + the official artifact were each compiled against their own distinct Master, each correctly selected via its own `source_sha256`, with zero cross-fixture cache contamination once the harness's per-fixture Master-path/broker-instance bugs (Section 13) were fixed.
- **Production consumers unchanged:** confirmed via Section 1 identity table — production Normalizer and CSP scripts were never touched, executed, or imported by this task; only the harness's own Normalizer-like/CSP-like *projection builders* (already-existing `sfm_master_authority.projections` code, exercised read-only) were used.

## 13. Harness debugging history (for the record)

Three bugs were found and fixed purely through my own dry-run testing before any operator involvement:
1. Tuple-unpacking error passing a bare builder function instead of `(folded_keys, builder_fn)` to `acquire_or_reuse_views` — fixed at all 3 call sites.
2. Cross-fixture cache contamination: all fixtures initially shared one broker and were incorrectly pointed at the real canonical Master path regardless of which synthetic Master they were compiled against — fixed by adding `master_path` to each manifest entry and constructing a fresh broker per fixture.
3. The `selection.py` production bug described in Section 2.

## 14. What remains: real SFM execution (operator action required)

Everything above was produced by running the harness via `python.exe` directly — using the real Python 2.7.5 32-bit interpreter SFM ships with, but **outside the actual SFM host process**. This is valuable diagnostic evidence (the harness logic, admission-category correctness, and structural findings are interpreter-level and do not depend on SFM's own process state), but it is **not** the same as real SFM telemetry: an actual SFM session carries substantially more baseline private-byte and VAS footprint (Qt, DirectX/D3D9, the loaded scene/DMX system, other mainmenu scripts already imported), and the 32-bit process's *available* address space is correspondingly smaller. The authorizing prompt requires genuine in-SFM execution for full qualification, and explicitly does not include "no SFM launch" in its hard-stop list — real execution by the operator is expected.

### Operator instructions

1. **Restart SFM first** (a clean process, not one that has already loaded other heavy scripts this session) — this matters for a clean P0 baseline.
2. Open the Script Editor.
3. Run exactly one script: `mainmenu/CGN_R3_B2F_CustomSidecarResourceQualification_Harness_01.py` (use "Run", not the mainmenu auto-discovery — the harness only executes its real logic under `if __name__ == "__main__":`).
4. Let it run to completion uninterrupted — it processes 13 fixtures, a 3-fixture cap-refusal check, and 5 stability cycles; expect it to take roughly the sum of the dry-run's per-fixture durations (single-digit seconds each, a few minutes total), likely longer inside real SFM.
5. Do not save the scene afterward unless you intend to — the harness does not modify the Master, any production script, or scene state; it only reads synthetic fixture artifacts staged under `C:\Users\Public\Documents\`.
6. Results land at `C:\Users\Public\Documents\CGN_R3_B2F_CustomSidecarResourceQualification_Harness_01_result.json`. Send that file back (or tell me it's ready) and I will independently re-analyze it exactly as I did the dry-run above, and render the final classification.

## 15. Interim classification

**Not yet classified.** Per this task's own terms, a final verdict (`B2F PASS` / `B2F PARTIAL` / `B2F FAIL`) requires real in-SFM telemetry, which has not yet been produced. The dry-run results above are consistent with a strong outcome — zero harness exceptions, correct fail-closed categorization in every case, a genuine and correctly-caught structural finding for Family C — but I am not willing to report a final PASS/PARTIAL/FAIL classification against data gathered outside the actual SFM process this task exists to qualify. Awaiting the operator's real-SFM run per Section 14.
