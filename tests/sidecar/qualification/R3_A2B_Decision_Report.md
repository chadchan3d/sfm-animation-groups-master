# R3-A2B Required Completion — Decision Report

Date: 2026-09-15. Scope: SFM_CGN_R3_A2B_Required_Completion prompt. Never
launched SFM. Never modified frozen R1D. No broker/rebuild implementation.
No Character Preset or Master modification. No formal R3 qualification
begun. No production deployment or commit performed.

## 1. R1D control identities (re-verified unchanged, start and end of task)

- `candidate_packed_validator.py`: `2dc3fe2268fdd12ef0a3002199635a8d24322bc422c50a637a21e1f664b65802`
- `candidate_packed_provider.py`: `74790fa285fad1b1369bf7bad9794f8125961dd553234c0294a55d7bc570f38c`

## 2. Python-2 `range()` audit (correcting the R3-A2 report's error)

R3-A2's report was wrong: Python 2.7's `range(N)` materializes a full list
of N Python int objects even without `list(...)` — only `xrange(N)` is
lazy. Full audit of every `range(` call site in the R1D/candidate
validator, provider, and the frozen `format.py` helper module actually
exercised by the hot path:

**Validator — 17 total `range()` sites, 6 classified high-cardinality /
direct-iteration-only** (loop variable used solely as an index/offset
multiplier, never stored/sliced/reused):

| Site | Phase | Real iteration count (official artifact) |
|---|---|---|
| STRING TABLE row loop | B | 221,565 |
| FOLD TABLE row loop | H | 124,728 |
| OCCURRENCE TABLE row loop | F | 128,555 |
| per-group occ_by_group slice loop (43 separate calls) | G | 128,555 (aggregate) |
| outer fold loop | I | 124,728 |
| per-fold occ_index slice loop (124,728 separate calls) | I | 128,555 (aggregate) |

11 remaining sites are low-cardinality (`group_count`=43 ×4,
`dir_row_count`≈10, `child_index_row_count`≈42 ×2, `metadata_row_count`≈54,
a 256-byte import-time translate table) — left as plain `range()`, per the
prompt's own classification guidance ("low-cardinality → likely
irrelevant").

**Provider** — all `range()` sites are low-cardinality (`group_count`=43,
`metadata_row_count`=54, `lookup_fold`'s per-query `occ_index_count`,
typically ≈1, not part of the cold-admission path). None converted.

**`format.py` (frozen production, never modified)** — one `range()` site
inside `ascii_fold_bytes` (byte-by-byte loop). Confirmed by direct source
read to be **dead code relative to this candidate's hot path**: the
candidate calls its own `_ascii_fold_bytes_fast` (translate-table, no
Python loop) instead. Correctly out of scope (frozen file) and irrelevant
regardless.

A Python-2/3 compatibility alias (`_irange = xrange` if available, else
`range`) was added and applied ONLY at the 6 high-cardinality sites,
producing composition **D**.

## 3. `xrange` experiment (composition D = C + xrange) — timing + memory

Real 32-bit Python 2.7.5 (`.../sdktools/python/2.7/win32/python.exe`),
real official artifact (9,506,244 bytes, SHA
`bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`).

**Peak working-set memory** (`GetProcessMemoryInfo`, fresh process per
sample, 2 independent samples each, byte-identical both times):

| Candidate | Peak WS delta | vs C |
|---|---|---|
| C (hardening + G/I) | 8,482,816 bytes | — |
| D (C + xrange) | 5,160,960 bytes | **−3,321,856 bytes (≈3.17 MiB, ≈39%)** |

Approximate Python-2.7 transient allocation avoided: ≈856,686 total int
values, materialized across 124,777 separate `range()`-produced list
objects (6 single big lists totaling 599,576 ints; 43 G-loop lists
totaling 128,555 ints; 124,728 I-inner-loop lists totaling 128,555 ints —
the last dominated by per-call list-object header overhead rather than raw
int count, since occurrence_count/fold_count ≈ 1.031, i.e. most of those
124,728 lists hold ~1 element).

**Timing** (2 independent 25-run back-to-back trials):

| Trial | C median | D median | Δ |
|---|---|---|---|
| 1 | 1.237 s | 1.210 s | −0.027 s (−2.2%) |
| 2 | 1.243 s | 1.203 s | −0.040 s (−3.2%) |

Direction consistent both trials; effect correctly phase-localized to the
I-phase (the site with by far the most `range()` calls: 124,728) — I-phase
C≈0.217–0.223 s vs D≈0.206 s both trials. G-phase (only 43 calls) showed no
measurable difference. Full min/max bands overlapped (not the strict
non-overlapping bar used elsewhere in this project), but the medians were
consistently lower for D in 2/2 independent trials with correct phase
attribution.

**Verdict: KEEP.** Real, reproducible, non-regressive, and — independent of
the modest timing win — a real memory-safety-relevant reduction (32-bit
process, ~3.2 MiB avoided per validation pass). Adopted as a correction of
the prior report's factual Python-2 error, not a discretionary
micro-optimization.

## 4. Lazy success-path diagnostic-formatting experiment (Section 2, composition E = D + lazy diagnostics)

Audit found 4 hot eager-formatting call sites — string built via `%` on
EVERY row, success or failure:

- `_check_bounds(..., "STRING TABLE row %d" % i)` — B-phase, 221,565 calls.
- `string_bytes(f_key_id, "fold %d key" % i)` — H-phase, 124,728 calls.
- `string_bytes(o_literal_id, "occurrence %d literal" % i)` — F-phase, 128,555 calls.
- `string_bytes(..., "occurrence %d's fold key" % i)` — F-phase, 128,555 calls.

603,403 unconditional `%`-format operations per validation pass, all
discarded unless that exact row fails (never, in the success path
benchmarked).

**Design:** `_check_bounds`/`string_bytes`'s `what` parameter now accepts
either a plain pre-formatted string (unchanged, low-cardinality sites) or
a 2-tuple `(template, value)`, formatted via `%` only inside the failure
branch. Message-content equivalence proven via a real corruption test
(STRING TABLE row length corrupted past pool bounds): R1D, C, D, and E all
produced the byte-identical error message
`"STRING TABLE row 1 out of bounds (offset=9 length=4294967280 container_length=3148556)"`.

**Timing** (2 independent trials):

| Trial | D median | E median | Δ | Bands |
|---|---|---|---|---|
| 1 (25 runs) | 1.322 s (min 1.191, max 1.477) | 1.045 s (min 1.004, max 1.113) | −0.277 s (−21%) | **non-overlapping** |
| 2 (15 runs) | 1.268 s (min 1.242) | 1.083 s (max 1.123) | −0.185 s (−15%) | **non-overlapping** |

Effect phase-localized exactly to the 3 touched phases (B: −0.09 to
−0.107 s; H: −0.038 to −0.044 s; F: −0.097 to −0.108 s); G/I phases
(untouched code) unchanged both trials, confirming the attribution is real.

**Peak memory:** D=5,160,960 bytes, E=5,140,480 bytes (further small,
non-regressive reduction).

**Complexity:** low — 2 helper functions gain one `isinstance(what, tuple)`
branch each; 4 call sites changed from an eager `%` to a plain tuple
literal.

**Verdict: KEEP.** By far the largest single effect measured in this task,
fully repeatable (2/2 independent trials, non-overlapping bands both
times), simple, and zero message-content regression.

## 5. End-to-end provider-open benchmark (Section 3)

New `benchmark_provider_open.py`, same real artifact/Master pair, same
environment, real Python 2.7.5, 15 runs each. Isolates file-read,
`validate_packed`, and full `BoundedProvider.open_path` (construction
overhead = open_path − read − validate, consistently ≈0, since provider
construction is O(1) bookkeeping, never O(row-count) work):

| Candidate | file-read | validate | open_path (E2E) |
|---|---|---|---|
| R1D (control, unbounded read) | 0.003 s | 1.291 s | **1.279 s** |
| B (hardening only) | 0.004 s | 1.234 s | 1.237 s |
| C (+ G/I) | 0.004 s | 1.202 s | 1.204 s |
| D (+ xrange) | 0.004 s | 1.196 s | 1.201 s |
| E (+ lazy diagnostics) | 0.004 s | 1.035 s | 1.059 s |
| **FINAL** (+ cap validation) | 0.004 s | 0.989 s | **0.990 s** |

File-read time is negligible and near-identical bounded vs. unbounded
(~3 ms vs ~4 ms) — the bounded-read hardening introduces no meaningful
regression relative to its safety benefit.

**Existing-harness check:** `r2_formal_benchmark.py`'s `run_cold_sidecar`
(lines 520–523) already isolates `BoundedProvider.open_path`'s total
duration as one segment (`t0`→`t_validation_done`) within its larger
cold-acquisition timeline, but does not further decompose that interval
into file-read / validate / construction-overhead sub-costs.
`benchmark_provider_open.py` (this task) is the first script providing
that finer attribution.

## 6. Runtime admission cap (Section 4) — remains UNFROZEN

`DEFAULT_RUNTIME_ADMISSION_CAP_BYTES = 16 MiB` is NOT promoted to a
production-final contract; its docstring and this report both state this
explicitly. Added `_validate_runtime_cap_bytes()`, called first inside
`_read_path_bounded`, rejecting with an explicit `AuthorityUnavailable`
(never a silent pass-through, never an incidental crash):

- non-integer values (`None`, `float`, `str`) — rejected
- `bool` — rejected (excluded even though `bool` is an `int` subclass)
- `<= 0` — rejected
- `> fmt.LIMIT_SIDECAR_BYTE_SIZE` (512 MiB, the format's own absolute
  ceiling) — rejected: a runtime cap can never be looser than the format's
  own malformed-input ceiling

All 7 malformed-value cases (`None`, `-5`, `0`, `3.5`, `"16777216"`,
`True`, `629145600`) confirmed rejected; the valid default case still
opens correctly.

**Future runtime-cap qualification design** (not performed this task, per
explicit prohibition): 2–3 synthetically enlarged valid artifacts at
different row-density shapes; real 32-bit SFM external memory sampler;
validation-only vs. representative query/view phases distinguished;
existing transient/retained gates retained unless governance changes them.

## 7. G/I direct-unpack wrapper-equivalence proof (Section 5)

Direct source inspection of frozen `format.py`:

```python
def unpack_occ_by_group_index_row(buf, offset=0):
    return OCC_BY_GROUP_INDEX_ROW_STRUCT.unpack_from(buf, offset)[0]
def unpack_occ_by_fold_index_row(buf, offset=0):
    return OCC_BY_FOLD_INDEX_ROW_STRUCT.unpack_from(buf, offset)[0]
```

Both wrappers are one-line pass-throughs with no validation, normalization,
endian handling, type conversion, or diagnostics beyond the Struct's own
fixed `"<I"` format — mathematically identical to the candidate's direct
`STRUCT.unpack_from(buf, offset)[0]` call (same Struct instance).

New focused test `test_gi_wrapper_equivalence.py` (28 checks: representative
values incl. 0/1/uint32-max/high-bit-only, offset-handling, short-buffer
exception-type identity, negative-offset behavior identity, 5,000-case
randomized cross-check) — **ALL PASS**, both Python 2.7.5 and Python 3.10.

**Verdict: the ~25 ms G/I win from R3-A2 remains valid; KEEP (no longer
provisional).**

## 8. Candidate composition matrix (Section 6)

| Composition | Validator SHA-256 | Provider SHA-256 |
|---|---|---|
| A — R1D control | `2dc3fe2268fdd12ef0a3002199635a8d24322bc422c50a637a21e1f664b65802` | `74790fa285fad1b1369bf7bad9794f8125961dd553234c0294a55d7bc570f38c` |
| B — hardening only | `a12180a88a4d617365da4e3937bef862c6aaca5031731afd4a140b5ba73a8550` | `c0cbc010b4da5f0d92a1c2e41dca72afbe7371bffeeefc5a5ac9b613f03f416f` |
| C — hardening + G/I | `62a59c7817d5b714637b67b53f5d78cf2bdd310155f26129e782785073ef9516` | `8831886bcd0bc22ea54a6888867f119e232ec8d90ea7350733de9d2190976335` |
| D — C + xrange | `4e2f20c02bf0ad61f38fbcc0831099467bff0391361a1253eb75ff4f0ac62998` | `4812976f7da9d6492ccef7010cbdd2611d3a2e226848b014ec8fc8bbee8a0d5a` |
| E — D + lazy diagnostics | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` | `9e9fdf93dbe75e13903c30b08f778c7df6bce64b1aa67b4b4f9a5f48a64736b8` |
| **FINAL — E + cap-parameter validation** | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` (unchanged from E) | `9f5574036e1501135aee43e010d9c12de7807794065baa1d4d38aba72fb349d2` |

open_path (E2E) medians: see Section 5 table above (R1D 1.279 s → FINAL
0.990 s).

## 9. Valid/invalid parity

- FINAL passes the full offline qualification suite
  (`candidate_offline_qualification.py`, isolated-import technique): **34/34
  PASS**, both at the scratch working copy and at the exported location.
- Preallocation-hardening corruption suite (near-uint32-max, many-legal-
  sum-exceeds, final-group-boundary, deflation) re-run directly against
  FINAL: **6/6 PASS**.
- Bounded-read suite (real artifact, oversized, TOCTOU-closing stat-lie
  proof) re-run directly against FINAL's provider: **5/5 PASS**.
- Zero regression vs. R1D on any accept/reject case.

## 10–11. Final retained candidate + stable exported paths

Scratch working copies:
`...\scratch_r3a2\candidate_packed_validator_r3a2b_FINAL.py`
`...\scratch_r3a2\candidate_packed_provider_r3a2b_FINAL.py`

**Exported to stable handoff location** (untracked; no commit performed):
- `E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_packed_validator_r3a2b.py`
  SHA-256: `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f`
- `E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_packed_provider_r3a2b.py`
  SHA-256: `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677`
  (differs from FINAL's scratch-copy provider SHA only because the
  imported validator module name changed to match its new filename;
  re-verified via the full 34-check qualification suite at this exact
  exported location.)
- This report: exported alongside as
  `E:\SFM Animation Group Master\tests\sidecar\qualification\R3_A2B_Decision_Report.md`

R1D itself remains completely untouched at its original deploy-dir
location throughout.

## 12. Remaining plausible optimization opportunity

None identified within authorized scope exceeding the >0.1 s bar. Whole-
pool UTF-8 redesign (explicitly deferred/rejected per the prompt) and
Master-SHA consolidation (explicitly lifecycle work, not validator
optimization, per the prompt) are correctly NOT reopened.

## 13. Section 8 stop-condition answers

- **Does `xrange` materially reduce Python-2 transient allocation?** Yes —
  ≈3.32 MiB (≈39% of the validation-induced peak working-set delta),
  deterministic and reproducible across independent process launches.
- **Does it materially improve timing?** Modestly — ≈0.03–0.04 s (≈2.5–3.2%),
  real and reproducible (2/2 trials, correct phase attribution) but an
  order of magnitude smaller than the lazy-diagnostics effect.
- **Does lazy formatting help?** Yes, dramatically — ≈0.19–0.28 s
  (≈14–21%), fully non-overlapping bands in 2/2 independent trials, zero
  message-content regression.
- **Final cold provider-open time vs. R1D?** R1D 1.279 s → FINAL 0.990 s:
  **−0.289 s (≈22.6%)** total reduction, real 32-bit Python 2.7.5, same
  real official artifact/Master pair, same environment.
- **Any remaining authorized optimization plausibly >0.1 s per cold
  acquisition?** No.

## Verdict

**`R3-A2 COMPLETE — FREEZE OPTIMIZATION`.**

Per the hard stop: no SFM launch, no R1D modification, no broker/rebuild-
utility implementation, no Character Preset modification, no Master
modification, no formal R3 qualification begun, no production deployment
or commit performed. Stopping here.
