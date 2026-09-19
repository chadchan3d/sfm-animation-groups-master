# R3 B2C-B — Correction6: Shape-Independent Pre-Read Transient Floor

**Date:** 2026-09-18
**Governing prompt:** `SFM_CGN_Correction6_ParseDeferred_PreReadFloor_ClaudeCode_Prompt_2026-09-18.md`
**Audit target (base commit):** `3bb3468fc5ba1462519f3465170dd6398a69affc`
**Independent re-audit verdict being answered:**
`INDEPENDENT CORRECTION5 RE-AUDIT FAIL — B2C-C remains blocked solely by the parse-deferred path bypassing the shape-independent pre-full-read transient floor.`

Scope discipline observed throughout: no SFM run, no B2C-C/B2C-D/Character-Preset work begun,
no taxonomy/presentation/mutation/generation-binding/lease-lifecycle/archive-rule changes, no
gate-threshold changes, **no staging/commit/push** (implementation-only phase).

## 1. Exact independent counterexample

Correction5's pre-full-read aggregate transient check only ran inside
`if preliminary_shape is not None:`. Any header/directory parse failure (bad magic, unsupported
`format_contract_version`, a short/truncated header, an invalid `section_count`, an invalid
directory offset/extent, or a malformed directory row) set `preflight_parse_deferred = True` /
`preliminary_shape = None` and fell through to the one full bounded read
(`f.read(runtime_cap_bytes + 1)`) **unconditionally** — no aggregate-transient check of any kind
on that path.

Independently reproduced fresh, against a real malformed 1 KiB candidate (all-zero bytes — bad
magic), `runtime_cap_bytes` = 16 MiB, `aggregate_existing_retained_bytes` = 10 MiB:

```
minimum_full_read_transient = 23,068,673 B   (shape-independent: read_bound=16,777,217
                                               + FIXED_TRANSIENT_RUNTIME_OVERHEAD_BYTES=2,097,152
                                               + MEASUREMENT_MODEL_GUARD_BYTES=4,194,304)
existing retained                = 10,485,760 B  (10 MiB)
minimum aggregate transient      = 33,554,433 B
TRANSIENT_GATE_BYTES             = 33,554,432 B  (32 MiB)
```

— over gate by exactly one byte, from trusted/runtime-known inputs **alone**, before a single
header byte is read. Confirmed by direct execution against `candidate_b2c_correction5`: the
scenario performs the full bounded read once (`full_bounded_read_call_count == 1`) before
reaching the full validator's own `SidecarCorrupt("magic mismatch...")` classification.

This exact defect was also confirmed to reproduce identically for two OTHER, distinct preflight
parse-failure modes (not merely the one fixture the audit cited): an unsupported-format-version
header, and a header that parses but whose directory region cannot fit in the file (truncated
directory) — see Sections 4/6 below.

## 2. Source diff

`sfm_master_authority_productionized/resource_estimator.py`: one new function,
`estimate_minimum_full_read_transient(runtime_cap_bytes)`, single-sourced from the SAME
`FIXED_TRANSIENT_RUNTIME_OVERHEAD_BYTES`/`MEASUREMENT_MODEL_GUARD_BYTES` constants
`estimate_transient_preliminary` already uses — no constant duplicated into a second module.

```python
def estimate_minimum_full_read_transient(runtime_cap_bytes):
    read_bound = runtime_cap_bytes + 1
    return int(read_bound + FIXED_TRANSIENT_RUNTIME_OVERHEAD_BYTES + MEASUREMENT_MODEL_GUARD_BYTES)
```

`sfm_master_authority_productionized/resource_preflight.py`: one new check inserted right after
Gate A (the raw-artifact-size check) and **before** Stage 1's header read — so it runs
unconditionally, on every path, before any header/directory parsing is even attempted:

```python
minimum_full_read_transient = resource_estimator.estimate_minimum_full_read_transient(runtime_cap_bytes)
minimum_aggregate_transient = aggregate_existing_retained_bytes + minimum_full_read_transient
if minimum_aggregate_transient > TRANSIENT_GATE_BYTES:
    raise ResourceAdmissionRefusal(...)   # reason = "minimum_floor_estimated_transient"
```

Recommended ordering (governing prompt Section 3) followed exactly: (1) validate runtime cap →
(2) open file/fstat → (3) raw-artifact Gate A → **(4) shape-independent minimum transient floor
[NEW]** → (5) small header/directory preflight → (6) richer Correction5 shape-aware filters if a
shape parses → (7) the one full bounded read.

Companion mechanical change: `RUNTIME_BUILD_ID`/`_B2C_EXPECTED_BUILD_ID` bumped to
`"b2c-correction6-parsedeferred-floor-targeted-2026-09-18"`; Normalizer candidate's sibling-
authority-root path constant updated `candidate_b2c_correction5` → `candidate_b2c_correction6`
(candidate isolation bookkeeping only). Full diffs saved at
`candidate_b2c_correction6/diffs/{resource_estimator,resource_preflight,runtime}.py.diff` and
`.../diffs/Rebuild_Control_Groups_Normalizer_candidate.py.diff`.

**Diff scope confirmed narrow:** `diff -rq --exclude=__pycache__ --exclude='*.pyc' --exclude=diffs`
between `candidate_b2c_correction5/` and `candidate_b2c_correction6/` reports exactly three
differing files (`resource_estimator.py`, `resource_preflight.py`, `runtime.py`) — every other
file (`broker.py`, `view_cache.py`, `cohort.py`, `selection.py`, `sidecar_contract.py`, all
fixtures, etc.) is byte-identical. `broker.py`/`view_cache.py` SHA-256-confirmed identical to
`candidate_b2c_correction5`'s copies (`d8935a0217...`/`206b51a52b7...`, both).

## 3. Minimum-floor formula

```
minimum_full_read_transient   = (runtime_cap_bytes + 1)
                                 + FIXED_TRANSIENT_RUNTIME_OVERHEAD_BYTES   (2 MiB)
                                 + MEASUREMENT_MODEL_GUARD_BYTES            (4 MiB)

minimum_aggregate_transient   = aggregate_existing_retained_bytes
                                 + minimum_full_read_transient

refuse iff minimum_aggregate_transient > TRANSIENT_GATE_BYTES   (strict '>', established semantics)
```

Every shape-dependent term omitted from this floor (`provider_decode_upper`,
`validator_scratch_upper`, `projection_upper`) is strictly `>= 0` in
`estimate_transient_preliminary`, so this floor is a genuine, provable lower bound on the richer
estimate for **any** possible shape — it can never itself introduce a false refusal that the
shape-aware check would not eventually have produced too, and it never weakens final validation.

## 4. Malformed decisive case (Section 5.A)

New permanent regression: `test_b2c_correction6_preread_floor.py`. Fixture:
`candidate_b2c_correction6/fixtures_malformed/malformed_1kib.sfmsidecar` (1024 all-zero bytes,
built deterministically by `build_malformed_fixtures_correction6.py`).

Against `candidate_b2c_correction5` (unfixed — documented for contrast, not claimed as a
Correction6 pass):

```
outcome=corrupt  exc_type=SidecarCorrupt  full_bounded_read_call_count=1  validator_call_count=0
```

Against `candidate_b2c_correction6` (fixed):

```
outcome=refused  exc_type=ResourceAdmissionRefusal  reason=minimum_floor_estimated_transient
full_bounded_read_call_count=0  validator_call_count=0
file_open_count=1  file_close_count=1  preliminary_shape_present=False
```

All required proofs satisfied: `ResourceAdmissionRefusal` raised; zero full bounded reads; no
validator call (`validator_call_count == 0`); no provider construction (exception raised before
any provider object exists); no cache/generation/ledger mutation possible by construction (this
call path never reaches `Cohort`/`Broker`/`ViewCache`/`AggregateLedger` — it calls the preflight
primitive directly, exactly as Correction5's own decisive test does).

## 5. Low-retained corruption-classification case (Section 5.B)

Same malformed fixture, `aggregate_existing_retained_bytes = 0` (floor comfortably under gate):

```
full_bounded_read_call_count=1   outcome=corrupt   exc_type=SidecarCorrupt
```

The full bounded read proceeds normally, and the authoritative corruption classification
(`SidecarCorrupt`, "magic mismatch...") remains fully observable — proving Correction6 does
**not** turn all malformed input into a resource refusal (governing prompt Section 4).

## 6. Unsupported-format case (Section 5.C)

Fixture: `unsupported_format.sfmsidecar` — valid magic, valid-size header, but
`format_contract_version=999` (not in `NORMATIVE_ROW_SIZES`).

- Over floor (10 MiB existing): `outcome=refused`, `reason=minimum_floor_estimated_transient`,
  `full_bounded_read_call_count=0` — zero full reads.
- Under floor (0 existing): `full_bounded_read_call_count=1`, `outcome=format_unsupported`
  (`errors.FormatUnsupported`) — authoritative classification remains observable, confirming
  this is a genuinely different preflight failure point than the bad-magic case (one step
  further into header validation) and the fix applies uniformly to it too.

## 7. Invalid-directory case (Section 5.D)

Fixture: `truncated_directory.sfmsidecar` — valid magic, valid `format_contract_version=0`,
valid `section_count=9`, but the file is only `HEADER_SIZE + 4` bytes, far short of the 252 bytes
the declared directory region would require.

- Over floor (10 MiB existing): `outcome=refused`, `reason=minimum_floor_estimated_transient`,
  `full_bounded_read_call_count=0`.
- Under floor (0 existing): `full_bounded_read_call_count=1`; **confirmed** the preflight's own
  directory-region parse genuinely failed (`preflight_parse_deferred=True`,
  `preliminary_shape_present=False`) — i.e. this exercises the directory-level failure
  specifically, not merely a header-level one (header parses fine; only the directory-region
  containment check fails). The full validator's own eventual classification differs in exact
  message (`payload_length` mismatch, caught by an earlier validator-internal check) but is
  still `SidecarCorrupt` — irrelevant to what this correction targets (preflight gate ordering,
  not the validator's own check order).

## 8. Exact boundary matrix (Section 5.E)

Using the malformed_1kib fixture, `minimum_full_read_transient` = 23,068,673 (fixed for
`runtime_cap_bytes` = 16 MiB, independent of the fixture):

| Case | existing_retained_bytes | minimum aggregate | Result |
|---|---|---|---|
| one byte below gate | 10,485,758 | 33,554,431 (gate − 1) | may proceed — full read occurs |
| exactly at gate | 10,485,759 | 33,554,432 (gate, exact) | **may proceed** — see semantics note |
| one byte above gate | 10,485,760 | 33,554,433 (gate + 1) | refused pre-read, zero full reads |

**`== gate` semantics:** unchanged from every prior round — strict `>` throughout this project's
gates, so `== gate` is admitted, never refused; this fix's new comparison
(`minimum_aggregate_transient > TRANSIENT_GATE_BYTES`) uses the identical operator.

Note: the "one byte above gate" boundary case (`existing = 10,485,760` = exactly 10 MiB) is
literally the same value as the Section 4 decisive case — confirmed identical and asserted as
such in the permanent test.

## 9. `full_bounded_read_call_count`

- Decisive malformed case (10 MiB existing): **0** (Correction6, fixed) vs. **1** (Correction5,
  unfixed).
- Low-retained malformed / unsupported-format / truncated-directory (all at 0 existing): **1**
  in every case (full read legitimately proceeds; authoritative classification observed).
- Unsupported-format / truncated-directory over floor (10 MiB existing): **0** in both cases.
- Boundary (below/exact): **1**. Boundary (above): **0**.

## 10. Correction5 regression (re-run unmodified)

`test_b2c_correction5_preread_aggregate_transient.py` — re-run **unmodified**, exactly as
pushed at `3bb3468...`: **19/19 PASS**, both Python 3.10 and real 32-bit Python 2.7.5. Its
parseable 10 MiB decisive case remains zero-full-read (this file is untouched, still points at
`candidate_b2c_correction4`/`candidate_b2c_correction5`, and neither of those directories was
modified this round).

## 11. Preserved Correction4 gates (no regression)

| Area | Test | Result |
|---|---|---|
| Offset-independent preflight allocation | `test_b2c_correction6_offset_independent_preflight_memory.py` (duplicated, pointed at `candidate_b2c_correction6`) | **20/20 PASS** — private-bytes delta = 0 at every offset |
| Durable lease cleanup ownership | `test_b2c_correction6_durable_release_failure_cleanup.py` | **25/25 PASS** (both interpreters) — `broker.py` SHA-256-identical to Correction5's copy |
| Archive-only A/B exact-byte validation | `test_b2c_correction6_archive_reproducibility.py` | **15/15 PASS** (both interpreters), pre-commit fallback mode |
| Expected-generation-before-publication | same suite, Part 5 (`expected_generation=GEN_A` vs. mutated-to-B Master) | `AuthorityChangedDuringAcquisition` raised before cache publication, exercised live |
| Atomic batch/cache accounting | `view_cache.py` SHA-256 identity check | byte-for-byte identical to `candidate_b2c_correction5` (`206b51a52b7...`, both); this correction's only code change never touches `ViewCache` at all |

## 12. Semantic regression

`test_b2c_correction6_semantic_regression.py` (duplicated, pointed at
`candidate_b2c_correction6`), real Python 2.7.5: **14/14 PASS**.

- Full-corpus combined hash: `3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2`
  — unchanged, exact match.
- W1 (208 folds) / W2 (1354 folds): ref == adapter exactly, `mapping_count=128555`,
  `destination_count=42` — unchanged.
- groupFile-wrapper regression unchanged; provider-closed-at-would-be-mutation-boundary
  confirmed.
- **W3 remains `UNKNOWN`.**

No SFM run.

## 13. Frozen production identities

| Identity | SHA-256 |
|---|---|
| Production `Rebuild_Control_Groups_Normalizer.py` | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` |
| Canonical `sfm_defaultanimationgroups.txt` | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |
| `broker.py` (correction5 == correction6) | `d8935a021db15cce7971c96eeeea06462da6f9a4e251752d4b6f46c830b5350b` |
| `view_cache.py` (correction5 == correction6) | `206b51a52b7bcfbd929c7ee91d6f198501508186bdc6cdf71e1a4acadb819a2d` |

Canonical full-corpus structure hash preserved: `3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2`.
W3 remains `UNKNOWN`.

## 14. Repo state / scope discipline

`git status --short` shows only new, untracked additions (new candidate directories, new
malformed-fixture builder/fixtures, and the new/duplicated test files) — zero modifications to
any previously-tracked file. No `git add`/`commit`/`push` performed this phase. No SFM run.
B2C-C, B2C-D, and Character Preset migration not started. Taxonomy, presentation, Normalizer
mutation semantics, generation-binding behavior, lease-lifecycle behavior, and archive-
reproducibility rules unmodified; 16 MiB/32 MiB gate constants unmodified.

## Final status

**`B2C-B PARSE-DEFERRED PRE-READ FLOOR CORRECTION IMPLEMENTATION PASS — INDEPENDENT RE-AUDIT REQUIRED`**

Do NOT self-authorize B2C-C.
