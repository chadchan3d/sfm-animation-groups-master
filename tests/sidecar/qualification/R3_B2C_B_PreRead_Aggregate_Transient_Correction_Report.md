# R3 B2C-B — Correction5: Pre-Full-Read Aggregate Transient Gate Ordering

**Date:** 2026-09-18
**Governing prompt:** `SFM_CGN_Correction5_PreReadAggregateTransient_ClaudeCode_Prompt_2026-09-18.md`
**Audit target (base commit):** `6e942f6d980ecc62921b58d4cea5c7c9d44442a8`
**Independent re-audit verdict being answered:**
`INDEPENDENT CORRECTION4 RE-AUDIT FAIL — B2C-C remains blocked solely by aggregate-transient gate ordering before the full bounded read.`

Scope discipline observed throughout: no SFM run, no B2C-C/B2C-D/Character-Preset work begun,
no taxonomy/presentation/mutation/generation-binding/lease-lifecycle/archive-rule changes, no
gate-threshold changes, **no staging/commit/push** (implementation-only phase).

---

## 1. Exact independent-audit counterexample

`resource_preflight.candidate_open_and_identify_with_preflight`'s PRE-FULL-READ preliminary
gate compared the incoming/preliminary transient estimate **alone** against `TRANSIENT_GATE_BYTES`
(32 MiB) — it never added `aggregate_existing_retained_bytes`, even though the AUTHORITATIVE,
post-full-read `resource_estimator.evaluate_cumulative_admission` (Correction3, "interpretation B")
already adds that same figure to its own transient sum. A request whose preliminary transient
estimate alone stayed under 32 MiB could therefore still trigger the one full bounded read
(`f.read(runtime_cap_bytes + 1)`) before the later, correctly-aggregated Stage 3 check finally
refused it.

Independently reproduced, fresh, against the exact `6e942f6...` archive/working tree
(`fixtures_ab/generation_a.sfmsidecar`, 610 bytes / 3 real occurrences; 2 requested folds
`left`/`right`; `runtime_cap_bytes` = 16 MiB; `aggregate_existing_retained_bytes` = 10 MiB):

```
preliminary incoming transient  = 23,075,300 B
existing retained               = 10,485,760 B  (10 MiB)
aggregate transient             = 33,561,060 B
TRANSIENT_GATE_BYTES            = 33,554,432 B  (32 MiB)
```

— exactly the independent audit's cited figures (verified by direct execution against
`candidate_b2c_correction4/`, see Section 6 below): the scenario is **admitted** at the
preliminary stage, the one full bounded read runs (`full_bounded_read_call_count == 1`), and
only then does Stage 3 refuse it (`cumulative_transient_exceeds_gate`, `total_transient_bytes`
= 33,561,060 — matching exactly).

## 2. Exact code change

File: `sfm_master_authority_productionized/resource_preflight.py` (staged unchanged into the
sibling `sfm_master_authority/`), inside
`candidate_open_and_identify_with_preflight`'s Stage 1 preliminary-rejection block.

Before:

```python
if prelim_transient > TRANSIENT_GATE_BYTES:
    ...
```

After:

```python
prelim_total_transient = aggregate_existing_retained_bytes + prelim_transient
if prelim_total_transient > TRANSIENT_GATE_BYTES:
    ...
```

The refusal message was updated to name both terms explicitly (`transient delta %d bytes plus
existing %d bytes...`), and `inst.reason` remains `"preliminary_estimated_transient"` (unchanged
identifier — a caller distinguishing this refusal from the post-read
`"cumulative_transient_exceeds_gate"` reason continues to work without modification).

No second, independent notion of retained authority was introduced: the fix reuses the exact
same `aggregate_existing_retained_bytes` parameter this function already receives and already
uses (unchanged) in the RETAINED preliminary check three lines above. The RETAINED gate
comparison, the post-full-read Stage 3 authoritative admission function
(`evaluate_cumulative_admission`), the 16 MiB / 32 MiB threshold constants, and every other
gate/semantic in this file are unchanged.

Companion mechanical changes (no logic change): `RUNTIME_BUILD_ID` /
`_B2C_EXPECTED_BUILD_ID` bumped to `"b2c-correction5-prerad-transient-targeted-2026-09-18"`
(`runtime.py`, both copies, and the Normalizer candidate), and the Normalizer candidate's
`__file__`-relative sibling-authority-root path constants updated from
`candidate_b2c_correction4` to `candidate_b2c_correction5` (candidate-isolation bookkeeping
only — Section 8).

## 3. Changed files + SHA-256

| File | SHA-256 |
|---|---|
| `candidate_b2c_correction5/sfm_master_authority_productionized/resource_preflight.py` | `f1b0da863f173e99431e4bae7ce703f3b1f0474555811c9bda3ed5a10f318874` |
| `candidate_b2c_correction5/sfm_master_authority/resource_preflight.py` (staged copy) | `f1b0da863f173e99431e4bae7ce703f3b1f0474555811c9bda3ed5a10f318874` (identical — confirms `stage_candidate_authority.py` ran cleanly) |
| `candidate_b2c_correction5/sfm_master_authority_productionized/runtime.py` | `19fe4a49701a8293b7c618378624d2a3510e3bd7e6c436f0af3eb813025c867b` |
| `candidate_b2c_correction5/sfm_master_authority/runtime.py` (staged copy) | `19fe4a49701a8293b7c618378624d2a3510e3bd7e6c436f0af3eb813025c867b` (identical) |
| `candidate_b2c_correction5_normalizer/Rebuild_Control_Groups_Normalizer_B2CB_correction5_candidate.py` | `bc38b646c44bc401e299ebc6373eb40bf1c0de51d7f348754ff74c9c3b7e593b` |
| `test_b2c_correction5_preread_aggregate_transient.py` (new permanent regression) | `1f8f6bb3bb36d1f5524c20fe7527ee3021eb089cc1852d223fbe99c4c344a50d` |

Every other file under `candidate_b2c_correction5/` and `candidate_b2c_correction5_normalizer/`
is byte-identical to its `candidate_b2c_correction4`/`candidate_b2c_correction4_normalizer`
counterpart (verified via `diff -rq --exclude=__pycache__ --exclude='*.pyc' --exclude=diffs`
across both directory trees — zero other differences reported), and via direct SHA-256
equality for `broker.py` and `view_cache.py` specifically (Section 10, items 4/5).

## 4. Diff against `6e942f6...`

Full unified diffs saved at:

- `candidate_b2c_correction5/diffs/resource_preflight.py.diff` (67 lines — the docstring note
  + the one comparison block change above)
- `candidate_b2c_correction5/diffs/runtime.py.diff` (11 lines — build-id bump only)
- `candidate_b2c_correction5/diffs/Rebuild_Control_Groups_Normalizer_candidate.py.diff`
  (26 lines — build-id + sibling-authority-root path constant only)

(Correction5's own `diffs/` directory replaces the stale correction3→correction4 diffs that
were incidentally carried over by the initial file-by-file copy from `candidate_b2c_correction4/`
— removed before any new diff was written, so this candidate's `diffs/` folder documents only
the change correction5 itself made.)

## 5. Pre-read aggregate formula

```python
prelim_total_transient = (
    aggregate_existing_retained_bytes
    + prelim_transient
)
if prelim_total_transient > TRANSIENT_GATE_BYTES:
    raise ResourceAdmissionRefusal(...)   # BEFORE the full bounded read
```

`prelim_transient` itself (`resource_estimator.estimate_transient_preliminary`) is unchanged:
`read_bound + provider_decode_upper + validator_scratch_upper + projection_upper +
FIXED_TRANSIENT_RUNTIME_OVERHEAD_BYTES + MEASUREMENT_MODEL_GUARD_BYTES`. Only the comparison
this function's caller performs against `TRANSIENT_GATE_BYTES` changed — exactly one new
local variable, one changed comparison operand, matching the "conceptually" block in the
governing prompt's Section 3 verbatim.

## 6. Decisive 10 MiB retained case

New permanent regression: `test_b2c_correction5_preread_aggregate_transient.py`. It imports
and exercises **both** `candidate_b2c_correction4` (documenting the bug, unfixed) and
`candidate_b2c_correction5` (proving the fix) against the identical scenario, so it fails
against the unfixed `6e942f6...` code path and passes only with the Correction5 change.

Against `candidate_b2c_correction4` (unfixed — for contrast/documentation only, not claimed
as a passing correction5 result):

```
outcome=refused  reason=cumulative_transient_exceeds_gate  full_bounded_read_call_count=1
cumulative_admission.total_transient_bytes = 33,561,060   (exact audit figure)
```

Against `candidate_b2c_correction5` (fixed):

```
outcome=refused  reason=preliminary_estimated_transient  full_bounded_read_call_count=0
validator_call_count=0   cumulative_admission=None (Stage 3 never reached)
file_open_count=1  file_close_count=1  (opened/closed once; only header+directory read)
```

Required proofs, all satisfied by construction (the exception is raised from inside the
preliminary block, strictly before Stage 2's full read, Stage 3's cumulative-admission call,
or `BoundedProvider._open_from_buf` — the sole entry point into the frozen structural
validator and any view/cache publication or generation mutation — are ever reached):

- `ResourceAdmissionRefusal` raised — **yes** (`errors.ResourceAdmissionRefusal`).
- Refusal reason clearly indicates the pre-read aggregate/preliminary transient gate — **yes**
  (`"preliminary_estimated_transient"`, distinct from the alternate post-read
  `"cumulative_transient_exceeds_gate"` reason, which the test explicitly asserts is NOT the
  reason returned — satisfying the prompt's "do not allow an alternate PASS" requirement).
- `full_bounded_read_call_count == 0` — **yes**.
- Validator/build/views not entered — **yes** (`validator_call_count == 0`; `evaluate_
  cumulative_admission`/`packed_family_counts` never called — `cumulative_admission is None`).
- Provider construction does not occur — **yes** (no `BoundedProvider` instance created; the
  function raises before that line).
- No cache publication / no generation mutation / no ledger corruption — **yes by construction**:
  this call path never reaches `Cohort`/`Broker`/`ViewCache`/`AggregateLedger` at all (the test
  calls the preflight primitive directly, with the caller-supplied
  `aggregate_existing_retained_bytes` — the same parameter shape the broker's own ledger already
  supplies at both real call sites in `selection.py`); with `validator_call_count == 0` and the
  exception raised before any provider exists, there is no code path remaining that could have
  touched a cache, ledger, or generation identifier.

## 7. Boundary matrix

All against the fixed `candidate_b2c_correction5` code, same fixture/request
(runtime_cap_bytes=16 MiB, 2 folds), `prelim_transient` = 23,075,300 B (fixed for this
fixture/request, independent of `aggregate_existing_retained_bytes`):

| Case | existing_retained_bytes | aggregate transient | Result |
|---|---|---|---|
| A. zero retained | 0 | 23,075,300 | **admitted**, full read proceeds (`full_bounded_read_call_count=1`, `validator_call_count=1`) — normal later behavior unchanged |
| B. small, still under | 5,242,880 (5 MiB) | 28,318,180 | **admitted**, full read proceeds |
| C. one byte below gate | 10,479,131 | 33,554,431 (gate − 1) | **admitted**, full read proceeds |
| C. exactly at gate | 10,479,132 | 33,554,432 (gate, exact) | **ADMITTED** — see semantics note below |
| C. one byte above gate | 10,479,133 | 33,554,433 (gate + 1) | **refused** pre-read, `full_bounded_read_call_count=0` |
| D. 10 MiB retained | 10,485,760 | 33,561,060 | **refused** pre-read, zero full reads (the decisive case) |
| D. 11 MiB retained | 11,534,336 | 34,609,636 | **refused** pre-read, zero full reads |
| D. 12 MiB retained | 12,582,912 | 35,658,212 | **refused** pre-read, zero full reads |
| D. 15 MiB retained | 15,728,640 | 38,803,940 | **refused** pre-read, zero full reads |

**`== gate` semantics:** this project's existing gate comparisons are strict `>` throughout
(`resource_estimator.evaluate_cumulative_admission`: `combined_retained_bytes > retained_gate_
bytes`, `total_transient_bytes > transient_gate_bytes`) — i.e. a value exactly equal to a gate
is **admitted**, never refused. The Correction5 fix's new preliminary comparison
(`prelim_total_transient > TRANSIENT_GATE_BYTES`) uses the identical strict operator, so
`== gate` is admitted here too, consistent with the pre-existing contract (not a new decision
introduced by this correction).

All boundary cases confirm the retained gate (16 MiB) never fires in any of these scenarios
(`existing + prelim_retained` stays well under 16,777,216 B even at 15 MiB existing — max
observed 15,734,864 B) — every refusal above is cleanly attributable to the transient gate
alone, isolating exactly the ordering defect this correction targets.

Verified 19/19 under both Python 3.10 and real 32-bit Python 2.7.5 (Section 9).

## 8. `full_bounded_read_call_count`

- Decisive case (10 MiB existing): **0** (fixed) vs. **1** (unfixed `candidate_b2c_correction4`).
- Boundary A/B/C(≤gate): **1** in every admitted case (full read legitimately proceeds).
- Boundary C(above)/D (all 4 sub-cases): **0** in every refused case.

## 9. Test results

`test_b2c_correction5_preread_aggregate_transient.py` (new, permanent): **19/19 PASS**, both
Python 3.10 and real 32-bit Python 2.7.5 — identical results on both interpreters.

## 10. Correction4 regression results (no regression)

Per Section 6 of the governing prompt ("do not rerun unrelated historical campaigns"), items
were verified at the narrowest sufficient scope:

1. **Offset-independent preflight allocation** — `resource_preflight.py`'s Stage 1 read/seek
   mechanics are byte-unchanged by this correction (the fix is confined to the comparison
   inside the *later* preliminary-rejection block, after Stage 1's bounded reads already
   completed). Re-ran the full offset sweep against `candidate_b2c_correction5` directly
   (`test_b2c_correction5_offset_independent_preflight_memory.py`, duplicated from the
   Correction4 suite with its own fixtures copy): **20/20 PASS**, private-bytes delta = 0 at
   every offset (64 KiB … 15.9 MiB), max single preflight read bounded at every offset.
2. **Durable lease cleanup ownership** — `broker.py` is byte-for-byte SHA-256-identical between
   `candidate_b2c_correction4` and `candidate_b2c_correction5`
   (`d8935a021db15cce7971c96eeeea06462da6f9a4e251752d4b6f46c830b5350b`, both). Re-ran the full
   lifecycle suite against `candidate_b2c_correction5`/`candidate_b2c_correction5_normalizer`
   anyway (`test_b2c_correction5_durable_release_failure_cleanup.py`), exercising the REAL
   extracted lease-retry/finalize methods against the real broker: **25/25 PASS**, both
   interpreters.
3. **Archive-only A/B exact-byte validation** — re-ran the full A/B-fixture / validator-pin /
   provider-pin / fresh-root simulation suite against `candidate_b2c_correction5`
   (`test_b2c_correction5_archive_reproducibility.py`): **15/15 PASS**, both interpreters.
   `candidate_b2c_correction5/` is not yet committed (this phase forbids staging/commit), so
   this ran in the same honest, self-reporting "fresh working-tree copy" fallback mode the
   original Correction4 test used pre-commit; Part 1's real `git archive --worktree-attributes
   HEAD` check against the already-tracked validator/provider still passed exactly
   (`74fe8d96.../d6ef9650...`, matching the pins).
4. **Expected-generation-before-publication behavior** — exercised live (not merely by hash
   equality) as Part 5 of the same archive-reproducibility re-run above: a real
   `acquire_or_reuse_views(..., expected_generation=GEN_A)` call against a mutated-to-Generation-B
   Master correctly raises `AuthorityChangedDuringAcquisition` before any cache publication
   (`view_cache_entry_count()` unchanged before/after) — unaffected by this correction (`broker.py`
   confirmed byte-identical above), re-proven live rather than only by hash.
5. **Atomic batch/cache accounting** — `view_cache.py` is byte-for-byte SHA-256-identical between
   `candidate_b2c_correction4` and `candidate_b2c_correction5`
   (`206b51a52b7bcfbd929c7ee91d6f198501508186bdc6cdf71e1a4acadb819a2d`, both); this correction's
   only code change (Section 2) never touches `ViewCache.admit`/`admit_batch`/`acquire_lease` at
   all, so this behavior cannot have regressed by construction.

## 11. Semantic regression

`test_b2c_correction5_semantic_regression.py` (duplicated from the Correction4 suite, pointed
at `candidate_b2c_correction5`), under real Python 2.7.5: **14/14 PASS**.

- Frozen production `parse_targeted_master` vs. `normalizer_compat_adapter.
  build_targeted_master_compatible_projection`, full real corpus: combined canonical hash
  **`3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2`** — unchanged, exact match
  on both the reference parser and the correction5 adapter.
- W1 (208 folds) / W2 (1354 folds) real command-scope equivalence: ref == adapter exactly for
  both; `mapping_count=128555`, `destination_count=42` for both (unchanged).
- groupFile-wrapper regression: exactly one root-level group named `groupFile`; adapter output
  contains no phantom `groupFile` group.
- Provider-closed-at-would-be-mutation-boundary: the candidate Normalizer file references no
  native/DME mutation symbol (`CDmeAnimationSet`, `AddChannel`, `dm.CreateElement`, `vs.mutate` —
  none present).
- **W3 (72-shot) remains explicitly UNKNOWN** — not re-derived, not force-substituted.

No SFM run.

## 12. Frozen production identities

Re-verified fresh in this round (not assumed from memory):

| Identity | SHA-256 |
|---|---|
| Production `Rebuild_Control_Groups_Normalizer.py` | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` |
| Canonical `sfm_defaultanimationgroups.txt` | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |
| Frozen `candidate_packed_validator_r3a2b.py` (archive-reproduced) | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` |
| Frozen `candidate_packed_provider_r3a2b.py` (archive-reproduced) | `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677` |
| `broker.py` (candidate4 == candidate5) | `d8935a021db15cce7971c96eeeea06462da6f9a4e251752d4b6f46c830b5350b` |
| `view_cache.py` (candidate4 == candidate5) | `206b51a52b7bcfbd929c7ee91d6f198501508186bdc6cdf71e1a4acadb819a2d` |

Canonical full-corpus structure hash preserved: `3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2`.
W3 remains `UNKNOWN`.

## 13. Repo state / scope discipline

- No `git add`/`commit`/`push` performed this phase. `git status --short` shows only new,
  untracked additions (the new candidate directories and the new/duplicated test files) —
  zero modifications to any previously-tracked file.
- No SFM run.
- B2C-C not started; B2C-D not started; Character Preset migration not started; taxonomy,
  presentation, Normalizer mutation semantics, generation-binding behavior, lease-lifecycle
  behavior, and archive-reproducibility rules all unmodified; 16 MiB/32 MiB gate constants
  unmodified.

## 14. Final status

**`B2C-B PRE-READ AGGREGATE TRANSIENT CORRECTION IMPLEMENTATION PASS — INDEPENDENT RE-AUDIT REQUIRED`**

Do NOT self-authorize B2C-C.
