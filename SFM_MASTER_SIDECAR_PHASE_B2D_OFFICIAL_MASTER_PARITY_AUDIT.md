# SFM Master Sidecar — Phase B2D: Full Official-Master Compile + Exhaustive Semantic Parity

The first full official-Master sidecar compile. The generated artifact is a **TEST ARTIFACT ONLY** — it was
never written to disk, never persisted, never published as an active generation. No public CLI, manifest,
publisher locking, Normalizer integration, Final Gate 1 declaration, or format v1 freeze in this phase.

## 1. VERDICT

**PASS.** No STOP condition (Part 32) was triggered. The complete official Master compiles through the
unmodified production writer, opens through the unmodified production reader, and achieves **exact, 100%,
non-sampled parity** across every stored fact this project has ever defined as authoritative — all 43
groups, all 42 child-index references, all 54 metadata entries, all 128,555 occurrences, all 124,728 fold
families, and every one of 124,728 known-fold lookups plus 128,555 exact-literal lookups. Zero production
code changes were required (`format.py`, `writer.py`, and `reader.py` are byte-for-byte unchanged from the
Phase B2C checkpoint). Final Gate 1 remains formally OPEN pending real Python 2.7 execution and cross-Python/
cross-OS determinism evidence (Sections 27/31), consistent with this phase's own explicit non-goal.

## 2. FILES CHANGED / CREATED

**Changed:** none. `tools/sfm_master_sidecar/{format,writer,reader}.py`, `tools/sfm_master_core.py`,
`tools/validate_master.py`, `tests/sidecar/oracle.py`, `tests/sidecar/fixtures/`, and
`sfm_defaultanimationgroups.txt` are all byte-for-byte identical to the Phase B2C checkpoint.

**Created:**
- `tests/sidecar/official_master_fixture.py` — a shared, `lru_cache`-backed, NOT-a-test-file module: reads
  the official Master exactly once (SHA-verified against the expected baseline immediately), then exposes
  cached accessors for the core parse, the independent oracle scan, the fold-family map, and the compiled
  artifact bytes, so the (~6s) full pipeline runs once per test session rather than once per test file.
- `tests/sidecar/test_official_master_full_compile.py` — Parts 1/3/4/20/21/22 (11 tests).
- `tests/sidecar/test_official_master_determinism.py` — Part 5 (4 tests).
- `tests/sidecar/test_official_master_semantic_parity.py` — Parts 6–10/16–18/23 (29 tests).
- `tests/sidecar/test_official_master_fold_parity.py` — Parts 11–15 (10 tests, 5 subtests).
- This audit document.

## 3. SOURCE SNAPSHOT IDENTITY

Read exactly once via `official_master_fixture.load_source_bytes()` (an `lru_cache`d function — every other
cached accessor in that module derives from this same captured `bytes` object, never re-reading the file):

- **Byte length:** 3,972,355
- **SHA-256:** `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` — verified to match the
  required baseline immediately inside `load_source_bytes()`, which raises before anything else in the
  qualification pipeline can run if it ever disagreed.

## 4. FULL COMPILE RESULT

`sfm_master_core.parse_master_bytes` → `result.ok == True`, exactly one parentless group (`groupFile`),
compiled via `writer.compile_sidecar` — the exact same function every B2B/B2C fixture used, imported
directly with no full-Master-specific writer, shortcut serializer, or separate qualification binary path
(confirmed via `inspect.getfile` pointing at `tools/sfm_master_sidecar/writer.py`). Compilation succeeded
with **zero exceptions, zero refusals**. The compiled artifact opens successfully via
`reader.SidecarReader.open_generation` (full Section 20 A–J structural validation, non-sampled, over the
entire 9.06 MiB artifact) with **zero rejections**.

## 5. ARTIFACT IDENTITY

- **Bytes:** 9,506,244
- **Ordinary full-file SHA-256:** `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`
- **Embedded integrity digest:** `49a8a7f86c2ee39e3b60190092d49b1695e6d35f03c248cff3d2c471d465915c`

The two digests are computed differently (the embedded one zeroes its own 32-byte field before hashing) and
are confirmed distinct, as required. The artifact exists only as an in-memory Python `bytes` object for the
duration of the test process — never written to any file, confirmed both by direct inspection of
`official_master_fixture.py`'s source (its only I/O is the one source-file read) and by `find . -iname
"*.bin"` returning nothing after the full suite ran (Section 32).

## 6. ARTIFACT SIZE

9,506,244 bytes total — 2.39× the 3,972,355-byte source, dominated by the STRING POOL/TABLE (a full copy of
every distinct group name, metadata key/value, control literal, and fold key, UTF-8 encoded plus an 8-byte
offset/length row per string) and the OCCURRENCE TABLE (16 bytes × 128,555 rows). See Section 7 for the
complete breakdown.

## 7. SECTION SIZE BREAKDOWN

| Section | Row count | Bytes | % of artifact |
|---|---|---|---|
| HEADER | — | 108 | 0.001% |
| SECTION DIRECTORY | 9 | 252 | 0.003% |
| STRING_POOL | 3,148,556 (bytes) | 3,148,556 | 33.12% |
| STRING_TABLE | 221,565 | 1,772,520 | 18.65% |
| GROUP_TABLE | 43 | 1,720 | 0.02% |
| CHILD_ID_INDEX | 42 | 168 | 0.00% |
| METADATA_TABLE | 54 | 864 | 0.01% |
| OCCURRENCE_TABLE | 128,555 | 2,056,880 | 21.64% |
| OCCURRENCE_BY_GROUP_INDEX | 128,555 | 514,220 | 5.41% |
| FOLD_TABLE | 124,728 | 1,496,736 | 15.74% |
| OCCURRENCE_BY_FOLD_INDEX | 128,555 | 514,220 | 5.41% |

Sum of all section lengths + HEADER + SECTION DIRECTORY = 9,506,244 — **reconciles exactly** to the total
artifact size (`test_section_sizes_reconcile_to_total_artifact_size`), with no padding/alignment bytes
anywhere (sections are laid out fully contiguous, as designed since B2B). Every row count matches its
expected canonical-baseline value (43/42/54/128,555/128,555/124,728/128,555).

## 8. DETERMINISM

- **Same-process double-compile:** byte-identical (`blob_a == blob_b`), including with two entirely
  independent fresh `parse_master_bytes` calls (not object reuse).
- **Cross-`PYTHONHASHSEED`-subprocess:** compiled the full official Master in two fresh subprocesses
  (`PYTHONHASHSEED=0` and `PYTHONHASHSEED=999983`) — identical SHA-256
  (`bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`) and identical byte length
  (9,506,244) in both.
- **Cross-Python-version/cross-OS determinism is explicitly NOT claimed** — only one Python 3 interpreter
  (this environment's 3.10.6) was available to test against; this remains open Gate 1A evidence (Section
  27).

## 9. GROUP PARITY

**Passed: 43 / 43.** All 43 groups present and identical (name, `declare_order`, `sibling_rank`,
`parent_path`, parentless status) across `sfm_master_core`, the independent oracle, and the reader
simultaneously — checked group-by-group, not merely by count. Wrapper confirmed as `groupFile`; canonical
paths confirmed wrapper-inclusive and exact (e.g. `groupFile/Face/Eyes` present verbatim in all three, no
stripping). Every group's child sequence (declare-order-derived from `sfm_master_core`) matches the reader's
own sibling-rank-ordered reconstruction exactly.

## 10. CHILD PARITY

**Cardinality confirmed:** `group_count=43`, `parentless_group_count=1`, `child_index_row_count=42`
(43 − 1). Every one of the 42 non-wrapper groups confirmed to appear in coverage exactly once; the wrapper
confirmed to appear zero times — checked via the reader's own already-validated child/parent relationships
(B2C's Section 20.C/D checks are what actually enforce exact ownership/sibling-order/no-duplicate/no-missing
at open time; this phase's test re-confirms the resulting coverage fact at official scale).

## 11. METADATA PARITY

**Passed: 54 / 54.** Every metadata entry's owning group, local order (source order, duplicates included),
exact key, and exact value agree across core, oracle, and reader — checked entry-by-entry. Per-group slices
confirmed: groups with zero metadata rows return an empty list (never conflated with "specific key absent
from a non-empty slice"); every key present in a non-empty slice is independently confirmed present via
`GroupMetadata.present()`.

## 12. OCCURRENCE PARITY

**Passed: 128,555 / 128,555.** For every occurrence, in exact global order: literal, destination group path,
and local rank agree across `sfm_master_core`, the oracle, and the reader. The reader's OCCURRENCE TABLE row
index confirmed equal to `global_rank` for every single row (`test_row_index_is_global_rank_for_every_row`,
checked with a plain index-equality loop over all 128,555 rows, not a sample).

## 13. BY-GROUP PARITY

Every group's direct occurrence membership (from `sfm_master_core`'s `local_occurrence_global_ranks`, already
local-rank-ordered) confirmed to form a complete, non-overlapping partition of `0..128554` — a per-occurrence
coverage boolean array of length 128,555 ends up entirely `True` with zero double-claims. This specifically
exercises the case final spec Part 10 calls out: groups containing nested children still correctly separate
their OWN direct-member occurrences from occurrences declared inside child groups (`sfm_master_core`'s
`local_occurrence_global_ranks` is scoped to the exact `full_path`, not any descendant path, by construction —
re-confirmed here at full scale rather than only on B2A's small fixtures).

## 14. FOLD-FAMILY PARITY

**Passed: 124,728 / 124,728, individually — not by count alone.** For every fold family: folded-key value,
Hit-vs-FoldConflict classification, destination set, and the COMPLETE occurrence-evidence global-rank set
(not merely a destination-count summary) were each compared against `sfm_master_core.build_fold_families()`'s
own record. **0 cross-destination conflicts confirmed** in the official Master, matching the canonical
baseline exactly (and independently re-confirmed via the validator's own "cross-path (invariant violation):
0" line in Section 28).

## 15. KNOWN-FOLD LOOKUP PARITY

**Passed: 124,728 / 124,728.** Every known official folded identity resolved `Hit` via
`reader.lookup_fold` — zero `FoldConflict`, zero `MasterUnknown`, exactly as expected for a Master with 0
cross-destination conflicts.

## 16. EXACT-LITERAL LOOKUP COVERAGE

**Passed: 128,555 / 128,555.** Every occurrence's exact literal spelling (Option A — meaningfully identical
to Option B here since the official Master has 0 exact duplicate literals, independently re-confirmed:
`len(literals) == len(set(literals)) == 128,555`) resolved to its correct stored fold family and destination.

## 17. ABSENT LOOKUPS

A deterministic 5-member set of fold keys guaranteed absent from the Master (`thisliteraldoesnotexistanywhereinthemaster`,
etc. — independently confirmed absent from the 124,728 known fold keys before testing lookup behavior)
resolved `MasterUnknown` for all 5 against the valid, source-bound reader. No malformed UTF-8 or invalid
query type was used for this category (those are separately covered as input-error behavior in B2B/B2C).

## 18. ASCII-FOLD VALIDATION

**Passed: 128,555 / 128,555.** The reader's own open-time exhaustive per-occurrence check (B2C, Section
20.F) already ran over the entire OCCURRENCE TABLE non-sampled when `open_generation` succeeded; this phase
additionally re-confirms every occurrence independently via `sfm_master_core.ascii_fold` (ASCII-byte-only
fold, never Unicode casefold/lower) against its recorded fold family membership.

## 19. STRING ROUND-TRIP

Every group name, every metadata key/value, and every one of the 128,555 exact control literals confirmed
byte-for-byte identical between `sfm_master_core`'s parsed value and the reader's decoded value — strict
UTF-8, no normalization, no compiler-added escaping, no compiler-side unescaping. Every fold key
independently re-verified as the exact `ascii_fold()` of every one of its family's exact spellings (not
merely one representative spelling per family). The source-file SHA (Section 3) remains a wholly separate
identity from these semantic string values, as designed.

## 20. INDEPENDENT ORACLE PARITY

Group projection (all 43), control projection (all 128,555, including explicit first/middle/tail spot
checks alongside the full-population comparisons already covered in Sections 9/12), and metadata projection
(all 54) all agree exactly between the independent B2A oracle and the reader. **Zero mismatches; no oracle
expectation was adjusted to accommodate reader output** — `tests/sidecar/oracle.py` is confirmed unchanged
(Section 32).

## 21. SOURCE BINDING

Correct SHA opens successfully. A candidate SHA differing in only its final hex character, a full 64-`f`
mismatch, a full 64-`0` mismatch, and a 32-character truncated prefix are all rejected with
`SourceMismatchError` (a subclass of `AuthorityUnavailable`) — never `MasterUnknown`. The diagnostic
`open_generation_unbound` handle permits inspection (`group_count()`) but refuses `lookup_fold` with
`AuthorityUnavailable`, confirming it never silently grants current-source authority.

## 22. FULL OPEN VALIDATION

`open_generation` on the full 9.06 MiB official artifact completed successfully, running every Section 20
A–J check (header/directory/protected-regions, string-table UTF-8 validity, group-table path-uniqueness/
parent-validity, complete index-slice-partitioning for both by-group and by-fold indices, exhaustive
per-occurrence ASCII-fold agreement, fold-table sort-order, and every cardinality cross-check) over the
complete structure — measured at ~0.90s on this development host (Section 24).

## 23. RESOURCE-LIMIT HEADROOM

| Resource | Official usage | Limit | % of limit |
|---|---|---|---|
| source_byte_size | 3,972,355 | 536,870,912 | 0.74% |
| sidecar_byte_size | 9,506,244 | 536,870,912 | 1.77% |
| group_count | 43 | 16,777,216 | 0.0003% |
| occurrence_count | 128,555 | 268,435,456 | 0.048% |
| fold_count | 124,728 | 268,435,456 | 0.046% |
| string_count | 221,565 | 268,435,456 | 0.083% |
| string_pool_total_bytes | 3,148,556 | 536,870,912 | 0.59% |
| max_single_string_length | 96 | 1,048,576 | 0.009% |
| max_metadata_rows_per_group | 3 | 65,536 | 0.005% |

**No usage is unexpectedly close to any limit** — every measured quantity is well under 2% of its configured
ceiling, most under 0.1%. No limit was silently changed in this phase.

## 24. DEVELOPMENT-HOST TIMINGS

**DEVELOPMENT-HOST ONLY — not Gate 2 embedded x86 SFM evidence.**

| Stage | Time (s) |
|---|---|
| source read + SHA-256 | 0.004 |
| `sfm_master_core` parse | 0.936 |
| independent oracle scan | 1.762 |
| writer compile | 2.340 |
| reader open + full structural validation | 0.898 |
| **total pipeline** | **5.940** |

## 25. DEVELOPMENT-HOST MEMORY OBSERVATION

**DEVELOPMENT-HOST ONLY — stdlib `tracemalloc`, no new dependency, never used to infer embedded x86 SFM
memory safety.** Opening a reader against the full official artifact showed a `tracemalloc`-measured delta
of ~61 MiB (current traced ~61 MiB, peak traced ~74 MiB for that isolated measurement); a separate
full-pipeline trace (parse + compile + open) showed cumulative deltas of ~51 MiB / +9 MiB / +61 MiB
respectively, with an overall peak traced of ~265 MiB across the whole in-process pipeline. These numbers
describe this desktop Python 3.10 process only.

## 26. FULL LIFETIME REGRESSION

Source-bound open of the full official artifact → valid `Hit` lookup → a lazy `iter_groups()` generator
obtained and partially consumed → `close()` → lookup after close raises `AuthorityUnavailable` → second
`close()` is harmless → the previously-obtained lazy generator's next access also raises
`AuthorityUnavailable`. All steps passed exactly as at B2C's small-fixture scale — no scale-dependent
lifetime defect found. The full 71-case B2C corruption matrix was NOT replayed at official scale, per this
phase's own explicit instruction ("No need to").

## 27. PYTHON-2.7 STATUS

**OPEN.** No Python 2.7 interpreter is available in this environment (`py -2 --version` falls through to
the installed Python 3.10.6; `where python2` finds nothing) — reconfirmed fresh at the start of this phase.
No interpreter was installed, downloaded, or bundled without authorization, per explicit instruction.
Static/import-discipline evidence (Phase B2B's `test_runtime_import_boundary.py`, unchanged and still
passing against the unmodified `format.py`/`reader.py`) remains supporting evidence only — **Final Gate 1 is
NOT declared complete**, and real Python 2.7 execution of the reader against this exact official artifact
remains the single largest piece of outstanding Gate 1A evidence.

## 28. VOCABULARY-VIEW STATUS

**DEFERRED**, unchanged from Phase B2C's judgment. The authoritative specification (final spec Section 43,
"Normalizer Adapter Boundary") explicitly states that view-API ergonomics are provisional and "Gate 1 does
not block on any provisional item" — nothing in B2D's own official-scale qualification exposed a concrete
need for `add_identity`/`query_complete_backing`/`ViewUncovered` that `Hit`/`FoldConflict`'s already-complete
per-lookup evidence does not already satisfy. No whole-family view, path-prefix view, or Normalizer-specific
vocabulary model was implemented in this phase.

## 29. TEST RESULTS

| Scope | Ordinary tests | Subtests |
|---|---|---|
| Pre-B2D baseline (everything under `tests/` EXCLUDING the 4 new B2D test files) | 264 | 191 |
| New B2D only (`test_official_master_full_compile.py`, `test_official_master_semantic_parity.py`, `test_official_master_fold_parity.py`, `test_official_master_determinism.py`) | **54** | **5** |
| Total (`python -m pytest tests/ -q`) | **318** | **196** |

`264 + 54 = 318` and `191 + 5 = 196` — both reconcile exactly. `official_master_fixture.py` is not itself a
test file (no `test_`-prefixed names) and contributes 0 to these counts, confirmed by direct collection.

**B2D qualification runtime** (the 4 new files only): ~62s. **Complete suite runtime** (`tests/` in full):
~80s.

## 30. READINESS FOR B2E

The writer/reader pair is now qualified against the actual, complete, official 128,555-occurrence Master
with zero discrepancies of any kind — the single largest remaining question B2A/B2B/B2C could not answer
("does this generalize past small fixtures?") is answered yes. B2E's publication-layer work (CLI, manifest,
immutable generation naming, publisher locking, crash recovery) can proceed against a writer/reader pair
that has now demonstrated correct behavior at the real scale it will actually be asked to serve.

## 31. REMAINING FINAL-GATE-1 EVIDENCE

Per final spec Section 38 (Gate 1A), still outstanding: (a) real Python 2.7 execution of the reader's
parity suite (Section 27); (b) deterministic binary equality across at least two distinct Python 3
minor-version/OS environments (Section 8 — only one environment was available here); (c) a small,
hand-authored CUSTOM Master run through the identical Gate 1A parity suite (proving "same compiler for
official and custom" is verified, not merely asserted by architecture) — not attempted in B2D, which was
scoped to the OFFICIAL Master only. None of these gate B2D's own PASS verdict; all three remain explicitly
open for whenever Final Gate 1 is formally pursued.

## 32. GIT / SAFETY STATE

- `sfm_defaultanimationgroups.txt`: unchanged, SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`.
- `tools/sfm_master_core.py`, `tools/validate_master.py`: unchanged.
- `tests/sidecar/oracle.py`, `fixtures/`, `fixture_manifest.json`: unchanged.
- `tools/sfm_master_sidecar/{format,writer,reader}.py`: unchanged (byte-for-byte identical to the B2C
  checkpoint commit `1a1dd8246cb2c24d3c258ef233ee4bd653aff956`).
- Validator re-run fresh after the full qualification: PASS, all canonical facts unchanged (groups=43,
  controls=128,555, folds=124,728, duplicates=0, cross-path conflicts=0).
- `git diff --check`: clean.
- No public CLI, manifest, publisher lock, or Normalizer-adjacent code exists anywhere in this phase.
- **No official-Master sidecar was persisted anywhere** — confirmed via `find . -iname "*.bin"` returning
  nothing outside `.git/` after the complete test suite ran.
- HEAD unchanged: `1a1dd8246cb2c24d3c258ef233ee4bd653aff956`.
- `git status`: only 5 new, untracked files (`tests/sidecar/official_master_fixture.py` and the 4 new
  `test_official_master_*.py` files) plus this audit document. **Nothing staged, nothing committed.**
- No agents or subagents were used.
