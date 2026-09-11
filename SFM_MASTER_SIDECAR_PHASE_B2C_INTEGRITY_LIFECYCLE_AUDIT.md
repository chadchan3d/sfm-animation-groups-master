# SFM Master Sidecar — Phase B2C: Exhaustive Structural Integrity, Corruption, and Lifecycle Hardening

Hardens the existing experimental writer/reader (`tools/sfm_master_sidecar/{format,writer,reader}.py`)
established in Phase B2B. No public CLI, manifest, publisher locking, Normalizer integration, official-Master
sidecar generation, Final Gate 1 declaration, or format v1 freeze in this phase. This is Gate 1B foundation
work only.

## 1. VERDICT

**PASS.** No STOP condition (Part 33) was triggered. One genuine defect was found and fixed during this
phase (see Section 2/16 below) — an ordering issue in `reader.py`'s validation sequence, not a defect in
the Master, semantic core, validator, or B2A oracle, and squarely within B2C's authorized "hardens the
existing experimental writer/reader" scope. Every one of the 71 checksum-valid structural-corruption test
cases constructed across Parts 2–12 is correctly rejected; the 2 deliberately-checksum-invalid contrast
cases are correctly rejected at the digest-comparison step specifically; all 28 B2A valid fixtures continue
to round-trip with zero regressions; both profile-unsupported fixtures remain refused; all 10 malformed
fixtures remain rejected before the writer is ever invoked.

## 2. FILES CHANGED / CREATED

**Changed:**
- `tools/sfm_master_sidecar/reader.py` — (a) moved the embedded-integrity-digest comparison to run
  immediately after the header's own basic sanity checks (magic/versions/`payload_length`), BEFORE any
  SECTION DIRECTORY row is decoded or structurally checked — see Section 16 below for why this was a real
  defect, not a style preference; (b) added two previously-missing Section 18 resource-limit checks that
  existed in the writer but not the reader: `STRING POOL` total byte size vs. `LIMIT_STRING_POOL_TOTAL_BYTES`,
  and per-string length vs. `LIMIT_SINGLE_STRING_BYTE_LENGTH`, both checked before the string-decoding loop
  builds the `strings` list.

**Created:**
- `tests/sidecar/corruption_helpers.py` — TEST-ONLY (never imported by production code) checksum-valid /
  checksum-invalid mutation framework: `MutableSidecar` (header/directory/every row-type getter+setter,
  raw pool-byte patching, `recompute_checksum()` and the deliberate no-op `corrupt_checksum_only()`) and
  `compiled_fixture()`.
- `tests/sidecar/test_structural_corruption_header.py` — Part 2 (14 tests).
- `tests/sidecar/test_structural_corruption_strings.py` — Part 3 (7 tests).
- `tests/sidecar/test_structural_corruption_groups.py` — Parts 4/5/6 (25 tests).
- `tests/sidecar/test_structural_corruption_occurrences.py` — Parts 7/8 (15 tests).
- `tests/sidecar/test_structural_corruption_folds.py` — Parts 9/10/11/12 (19 tests).
- `tests/sidecar/test_reader_invalidation.py` — Parts 13–18 (17 tests).
- `tests/sidecar/test_resource_limits.py` — Part 19 (9 tests).
- `tests/sidecar/test_writer_representability.py` — Part 20 (17 tests).
- This audit document.

**Unchanged, reconfirmed:** `sfm_defaultanimationgroups.txt`, `tools/sfm_master_core.py`,
`tools/validate_master.py`, `tests/sidecar/oracle.py`, `tests/sidecar/fixtures/`,
`tests/sidecar/fixture_manifest.json`, `tests/sidecar/test_oracle.py`, `tests/sidecar/test_fixture_contracts.py`,
`tests/sidecar/test_official_master_oracle_parity.py`, `tools/sfm_master_sidecar/format.py`,
`tools/sfm_master_sidecar/writer.py`, every B2B test file.

## 3. STRUCTURAL VALIDATION MODEL

Unchanged in shape from B2B: `reader._validate_and_decode` implements final spec Section 20's full A–J
checklist, non-sampled, over the entire decoded structure at `open_generation`/`open_generation_unbound`
time. What changed in B2C is strictly the CHECK ORDER (digest now checked before directory-row structural
checks — Section 16) and two added resource-limit checks (Section 19). No check was weakened, removed, or
made partial to accommodate a test.

## 4. CHECKSUM-VALID MUTATION FRAMEWORK

`tests/sidecar/corruption_helpers.MutableSidecar` wraps a compiled blob in a mutable `bytearray` and exposes
typed getters/setters for every row kind (header fields, directory rows by section-id or by raw index,
string-table/group-table/child-id-index/metadata/occurrence/fold-table/occurrence-by-fold-index rows, and
raw string-pool byte patching). `recompute_checksum()` recomputes the embedded digest over the CURRENT
(already-mutated) buffer using the exact same `format.compute_embedded_integrity_digest` production
function the writer/reader themselves use — so every "checksum-valid" test in this phase is validated with
the real digest algorithm, not a stand-in. `corrupt_checksum_only()` is an explicit no-op documenting the
contrasting path (mutate, never recompute). This module is test-only; production `writer.py`/`reader.py`
gained no corruption-construction machinery.

## 5. HEADER/DIRECTORY VALIDATION

14 tests (`test_structural_corruption_header.py`). Checksum-valid rejections confirmed for: duplicate
section ID, a section_id vanishing from the required set as a side effect of the same mutation ("missing
required section"), an unrecognized/out-of-range section_id, a wrong normative `row_size` (isolated from
the `row_count*row_size==length` check by adjusting `row_count` to compensate), a section overlapping the
HEADER's own protected region, a section overlapping the SECTION DIRECTORY's own protected region, two
sections overlapping each other, a section's declared end extending past EOF, an offset large enough to
make the range "impossible" (2⁶⁰, still `u64`-representable — Python's arbitrary-precision integers mean no
classic wraparound occurs, so this exercises the bounds-comparison path rather than true overflow, noted
explicitly), `row_count*row_size != length`, and a `section_count` that disagrees with the directory's
actual row layout. **No distinct "nonzero reserved field" case exists**: this format version defines no
field that is merely reserved-and-must-be-zero (verified directly against `Header._fields`/
`DirectoryRow._fields`), documented rather than silently skipped. A dedicated `PairedChecksumValidVsInvalidTests`
class demonstrates, for two representative mutations (wrong `row_size`; self-parenting group), that the
CHECKSUM-INVALID form fails specifically at the digest comparison while the CHECKSUM-VALID form of the
identical field mutation is instead caught by the specific structural check — proving both branches are
real (this is also what surfaced the ordering defect fixed in Section 16).

## 6. STRING VALIDATION

7 tests (`test_structural_corruption_strings.py`). Confirmed rejected: a string range extending beyond the
pool, malformed UTF-8 (a lone continuation byte patched into the pool), a truncated multi-byte UTF-8
sequence (a lead byte with its continuation byte cut off via a shortened declared length), an
out-of-bounds `name_string_id` referenced from a GROUP TABLE row, and a `STRING_TABLE` `row_count`
inconsistent with its declared length. **Two intentional non-findings, documented rather than silently
omitted:** there is no distinct "before the pool" case (offsets are zero-based unsigned values — 0 already
IS the pool's start, so the single generic bounds check already covers both directions), and overlapping
string ranges between two different `string_id`s are NOT a violation the final spec defines (Section 20.B
requires only in-bounds + valid-UTF-8 per string; verified directly by constructing exactly this scenario
and confirming the reader accepts it).

## 7. GROUP VALIDATION

11 tests within `test_structural_corruption_groups.py`'s `GroupTableCorruptionTests`, plus 2 more in the
paired header tests. Confirmed rejected: an out-of-range `parent_path_id`, self-parenting, a forward-reference
parent (`parent_path_id > path_id`, distinct from exact self-reference), duplicate canonical path (two
siblings sharing one name under the same parent), an out-of-range `name_string_id`, duplicate `declare_order`,
inconsistent `sibling_rank` (swapped between two siblings without touching the CHILD-ID INDEX's own
physical order), an out-of-bounds metadata slice, an out-of-bounds occurrence-by-group slice, zero parentless
groups, and two parentless groups.

## 8. CHILD-INDEX VALIDATION

8 tests (`ChildIdIndexCorruptionTests`). Confirmed rejected: wrong `child_index_count` (disagreeing with
`group_count - parentless_group_count`), the parentless wrapper appearing as someone's child, a duplicate
child reference (which, in a fixed-size complete-partition array, necessarily also leaves another
non-root group missing — both invariants violated by one minimal mutation, documented as such rather than
padded into two artificially-separate cases), an out-of-range child ID, a child assigned under the wrong
parent (ownership disagreement), a group child slice gap, a group child slice overlap (two groups' slices
sharing a position), and a child slice declared out of bounds.

## 9. METADATA VALIDATION

6 tests (`MetadataTableCorruptionTests`). Confirmed rejected: an out-of-range `key_string_id`, an
out-of-range `value_string_id`, a metadata slice gap (declared count smaller than actual), a metadata
slice overlap (two groups both claiming the same row), and non-dense `source_order` values within one
slice. **Legal semantics explicitly confirmed NOT rejected**, re-verified in this hardening context: duplicate
metadata keys, an unknown metadata key, an explicit `"0"` value, and an empty-string value all open
successfully (`test_legal_metadata_semantics_are_never_rejected_as_corruption`).

## 10. OCCURRENCE VALIDATION

7 tests (`OccurrenceTableCorruptionTests`). Confirmed rejected: an out-of-range `literal_string_id`, an
out-of-range destination `path_id`, an out-of-range `fold_id`, an impossible `local_rank` (not a dense
0..count-1 member), and an `OCCURRENCE_TABLE` `row_count` inconsistent with its length. **No distinct
"wrong global-rank representation" case exists**: `global_rank` is never a stored field at all — the row's
own physical table index IS `global_rank` (final spec Section 12) — verified directly against
`OccurrenceTableRow._fields`. Repeated exact literals (both within one group and across groups) are
re-confirmed legal, not corruption.

## 11. BY-GROUP PARTITION VALIDATION

8 tests (`OccurrenceByGroupIndexCorruptionTests`). Confirmed rejected: a duplicate occurrence reference
(necessarily leaving another missing, same pigeonhole reasoning as Section 8), the wrong occurrence owner
(occurrence repointed to a different group at the table level while the index still lists it under the
old owner), swapped ownership between two entries, a gap between slices, an overlap between slices, a
deliberately unreachable trailing index row, an out-of-range occurrence ID referenced from the index, and
an order reversal within one group's slice (`local_rank` no longer strictly increasing).

## 12. FOLD VALIDATION

8 tests (`FoldTableCorruptionTests`). Confirmed rejected: `FOLD_TABLE` `row_count` inconsistency, a
zero-occurrence fold, a duplicate fold key, unsorted fold keys, a "wrong fold key" (isolated from the
sort-order check using a single-fold fixture, so a 1-row table's trivial "sortedness" cannot mask the
defect — the fold's declared key is repointed at a real, different, in-bounds string that its member
occurrences do not actually fold to), an out-of-range `fold_key_string_id`, a fold slice declared out of
bounds, and an overlap between two folds' occurrence-index slices.

## 13. BY-FOLD PARTITION VALIDATION

5 tests (`OccurrenceByFoldIndexCorruptionTests`). Confirmed rejected: a duplicate occurrence reference
(pigeonhole-missing counterpart, as above), an occurrence reassigned to the wrong `fold_id` while the index
still lists it under the old fold, an out-of-range occurrence ID in the index, an unreachable tail row, and
overlapping fold slices. **One intentional non-finding, documented:** final spec Section 20.I states only
"complete, gapless, non-overlapping partition" plus "ownership agreement" for this index — unlike its
by-group counterpart (Section 20.G), it defines NO within-slice ordering requirement. Verified directly:
reversing the two-member order of a conflicting fold's slice (still an ownership-correct permutation of the
same two members) is accepted, not rejected — this is intentional per the final spec text, not a gap.

## 14. ASCII-FOLD EVIDENCE VALIDATION

2 tests (`CompleteAsciiFoldValidationTests`) plus 2 more folded into Section 11's conflict-evidence tests.
Confirmed: flipping one ASCII letter byte inside a fold key that ALSO contains adjacent non-ASCII (kanji)
bytes is rejected — proving the byte-level check operates correctly with non-ASCII bytes present, not only
on pure-ASCII literals; corrupting the LAST occurrence's shared fold key in a 30-member alias family is
rejected — proving the per-occurrence check is exhaustive across the whole family, not merely checking the
first member or a sample.

## 15. SOURCE BINDING

5 tests (`SourceBindingHardeningTests`). Confirmed: the correct SHA opens successfully; a candidate SHA
differing from the correct one ONLY in its final hex character is rejected (proves exact full-digest
comparison, not a near-match/prefix-tolerant one); a 32-character truncated prefix of the correct SHA is
rejected; a binding failure is confirmed to raise `SourceMismatchError` and NOT be (or be substitutable
for) `MasterUnknown`; an unbound handle is confirmed to never grant `lookup_fold` authority.

## 16. INVALIDATION MODEL

**A genuine ordering defect was discovered and fixed here (Part 33 does not require a STOP for reader.py
hardening — only for the Master/semantic-core/validator/oracle, which this is not).** Before this phase,
`reader._validate_and_decode` checked the SECTION DIRECTORY's row-level structural properties (bounds,
`row_size` normative match) BEFORE recomputing and comparing the embedded integrity digest. This meant a
CHECKSUM-INVALID mutation targeting a directory-row field (e.g. a wrong `row_size`, left with a stale
digest) would be caught by the STRUCTURAL check first, never actually reaching the digest comparison —
making the "checksum-invalid → must fail at digest comparison" half of final spec Section 39's
checksum-aware doctrine unreachable for that entire class of mutation, discovered directly by
`test_structural_corruption_header.py`'s `PairedChecksumValidVsInvalidTests` (its first assertion,
expecting the digest-mismatch message, instead observed the row_size-mismatch message). **Fix:** the digest
comparison now runs immediately after the header's own basic sanity checks (magic, versions,
`payload_length`) and strictly BEFORE any SECTION DIRECTORY row is decoded — digest computation only ever
needs the whole buffer, never the directory's own content, so there was no reason to defer it. Re-verified:
the paired test now passes in both directions, and the full pre-existing B2B corruption suite
(`test_basic_corruption.py`) still passes unchanged. 3 additional tests (`InvalidationModelTests`) confirm
invalidation never falls back to `MasterUnknown`, affects every subsequent call (not just the first), and
refuses even a query that would have cleanly resolved on valid backing.

## 17. INVALIDATE-CLOSE-CLOSE

The required 9-step lifecycle test remains exactly as established in Phase B2B
(`test_reader_lifetime.py::RequiredInvalidateCloseCloseLifecycleTest`, unmodified, re-verified passing). Phase
B2C adds explicit, direct proof of WHICH of the two permitted cleanup-timing strategies this implementation
uses (`CleanupStrategyTests.test_this_implementation_defers_cleanup_to_close_not_to_invalidation`):
`_backing` is confirmed still non-`None` immediately after `force_invalidate_for_testing()` (cleanup has NOT
happened yet), and only becomes `None` after `close()` — i.e., this implementation is deferred-cleanup, not
cleanup-at-invalidation, stated as an explicit, testable fact rather than only a docstring claim. A further
test confirms `_path_cache` is also released, and that calling `close()` twice never attempts to
double-release anything.

## 18. LAZY OBJECT INVALIDATION

Every currently-exposed lazy, provider-backed accessor is covered: `iter_groups`/`iter_occurrences` (Phase
B2B's lifecycle test), and `iter_metadata` (new in B2C — confirmed to fail on next access after both
invalidation and ordinary `close()`, and confirmed to fail immediately even when never yet advanced past
its first `next()` call). `Hit`/`FoldConflict` are re-confirmed as the OTHER permitted, deliberately
different category: already-materialized, non-authoritative copies that legitimately remain readable after
their parent provider is invalidated — tested explicitly and labeled as the documented exception, never
blurred with the lazy category. No whole-family vocabulary view exists yet (Section 24/Part 25 below), so
there is nothing further of that specific kind to test this phase.

## 19. RESOURCE LIMITS

9 tests (`test_resource_limits.py`). Because none of the small B2A/B2C fixtures can naturally exceed the
real Section 18 ceilings (2²⁴ groups, 2²⁸ occurrences, 512 MiB pool, etc.) without constructing multi-gigabyte
files — explicitly against this phase's own "do not deliberately allocate huge memory" instruction — every
test instead temporarily lowers the relevant `format.py` `LIMIT_*` constant (via `unittest.mock.patch.object`)
to a value the fixture already exceeds, exercising the exact same check code path a real oversized file
would hit. Confirmed rejected once lowered: group count, occurrence count, fold count, distinct string
count, metadata-rows-per-group, single-string byte length (this test also DROVE the discovery that the
reader was missing this specific check — see Section 2 — since without the fix this test failed), and
STRING POOL total byte size (also previously missing — same fix). The reader query-length ceiling
(`LIMIT_READER_QUERY_BYTE_LENGTH`) is confirmed both over-limit (raises) and exactly-at-limit (accepted,
resolves `MasterUnknown` for gibberish input) — a boundary check, not an off-by-one. A final structural test
inspects `reader._validate_and_decode`'s own source text to confirm the resource-limit checks appear
BEFORE the per-row decode loops they guard, so a future accidental reordering is caught mechanically, not
only by code review.

## 20. WRITER REPRESENTABILITY

17 tests (`test_writer_representability.py`). Direct unit tests of `writer._check_u32`/`_check_u64`/
`_check_limit` confirm exact boundary behavior (accept at the limit, reject one past it, reject negative
values) and confirm no masking/modulo ever occurs (`2**32` and `2**32 + 5`, which would wrap to `0` and `5`
respectively under masking, both correctly raise instead of silently "succeeding" at a wrapped value).
End-to-end `compile_sidecar` tests (via the same `LIMIT_*`-lowering technique as Section 19, plus lowering
`format.U32_MAX` itself) confirm the writer refuses group-ID overflow, and every one of the group/occurrence/
fold/metadata/single-string/source-byte-size resource limits, all the way through the real compile path —
not merely in the isolated helper functions — and that a refused compile never returns a partial/truncated
byte buffer (the exception is raised before any `blob` value is ever produced).

## 21. VALID FIXTURE REGRESSION

All 28 sidecar-profile-eligible B2A `valid/` fixtures re-run via the UNCHANGED `test_writer_reader_roundtrip.py`
(not touched in this phase) after both the digest-ordering fix and the two new resource-limit checks:
**28/28 pass**, zero mismatches against both `sfm_master_core` and the independent oracle, exactly as in
B2B. No corruption-detection hardening in this phase narrowed acceptance of any legitimate document shape.

## 22. CORRUPTION MATRIX RESULTS

Across Parts 2–12 (`test_structural_corruption_{header,strings,groups,occurrences,folds}.py`, 80 test
methods total): **71 distinct checksum-valid structural-corruption mutations, 71/71 correctly rejected**
(13 header/directory, 5 string, 24 group/child-index/metadata, 13 occurrence/by-group, 16 fold/by-fold);
**2 deliberately-checksum-invalid contrast mutations, 2/2 correctly rejected at the digest-comparison step
specifically** (the paired header tests); **2 deliberately-non-corrupting checksum-valid mutations, 2/2
correctly ACCEPTED** as the final spec explicitly does not define them as violations (overlapping string
ranges; reordered by-fold evidence within one slice); the remaining test methods are pure structural
documentation (confirming certain fields/flags simply do not exist in this format, so no case can target
them) or positive legality/regression re-confirmations (legal metadata semantics, repeated literals,
cross-destination conflict resolution) folded into the same files for locality with the corruption tests
they sit beside.

## 23. PYTHON-2.7 STATUS

**Unchanged from Phase B2B: no Python 2.7 interpreter is available in this environment** (`py -2` falls
through to the installed Python 3; `where python2` finds nothing) — not re-verified with a fresh probe this
phase since nothing about the local toolchain changed, but the fact remains current. `reader.py`'s changes
this phase (the digest-check reordering, the two new resource-limit checks) use only constructs already
present elsewhere in the file (plain conditionals, `fmt.` constant references, string formatting via `%`) —
no new import, no f-string, no walrus operator, no dependency on `sfm_master_core`/`dataclasses`/`pathlib`/
`typing` was introduced. `tests/sidecar/test_runtime_import_boundary.py` (Phase B2B, unmodified) continues
to pass against the modified file, re-confirming the import/syntax discipline holds. **Real Python 2.7
execution of the reader remains mandatory, deferred Gate 1A evidence, not claimed as satisfied here.**

## 24. KNOWN B2D WORK

- The official Master production compile and its own Gate-1-relevant qualification (explicitly Phase B2D's
  job, never attempted here).
- **Whole-family vocabulary view (Part 25): deferred to B2D, per the final spec's own Section 43
  ("Normalizer Adapter Boundary") statement that view-API ergonomics are explicitly provisional and "Gate 1
  does not block on any provisional item").** `Hit`/`FoldConflict` already carry complete, non-truncated
  family evidence for every lookup this phase's fixtures require; a separate `add_identity`/
  `query_complete_backing`/`ViewUncovered` API was judged unnecessary to build before B2D can state a
  concrete consumer need for it, consistent with B2B's identical judgment call, now re-confirmed rather
  than silently re-deferred.
- The full Gate 1C publication/CLI/manifest/locking suite (explicitly out of scope for B2C, per Part 30).
- Real Python 2.7 execution (Section 23 above).
- A handful of corruption categories this phase's small fixtures cannot exercise without constructing an
  actual large file (e.g. counts genuinely exceeding the former B1 u16 ranges, at real scale rather than via
  a lowered-limit proxy) — not required by B2C's own instructions, and not attempted.

## 25. TEST RESULTS

Measured by running the exact file sets in isolation with `python -m pytest <files> -q`, following the same
non-conflating methodology the prior checkpoint's reconciliation established:

| Scope | Ordinary tests | Subtests |
|---|---|---|
| Pre-B2C baseline (everything under `tests/` EXCLUDING the 8 new B2C files) | 141 | 185 |
| New B2C only (the 8 new files: `test_structural_corruption_{header,strings,groups,occurrences,folds}.py`, `test_reader_invalidation.py`, `test_resource_limits.py`, `test_writer_representability.py`) | **123** | **6** |
| Total (`python -m pytest tests/ -q`) | **264** | **191** |

`141 + 123 = 264` and `185 + 6 = 191` — both reconcile exactly.

## 26. READINESS FOR B2D

The reader's structural validation is now exercised (not merely implemented) against 71 distinct targeted
corruption cases spanning every A–J subsection of final spec Section 20, plus the full source-binding,
invalidation, lifecycle, resource-limit, and writer-representability contracts. One real ordering defect
was found and fixed by this exercise itself — direct evidence the hardening work was substantive, not
pro forma. Phase B2D can proceed to compile the official Master through this exact writer/reader pair with
justified confidence that a structurally corrupt (even checksum-valid) artifact cannot silently pass as
authority-usable.

## 27. GIT / SAFETY STATE

- `sfm_defaultanimationgroups.txt`: unchanged, SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`.
- `tools/sfm_master_core.py`, `tools/validate_master.py`: unchanged.
- B2A oracle/fixtures (`tests/sidecar/oracle.py`, `fixtures/`, `fixture_manifest.json`, `test_oracle.py`,
  `test_fixture_contracts.py`, `test_official_master_oracle_parity.py`): unchanged.
- `tools/sfm_master_sidecar/format.py`, `tools/sfm_master_sidecar/writer.py`: unchanged.
- `tools/sfm_master_sidecar/reader.py`: modified (the digest-check-ordering fix and two new resource-limit
  checks — see Section 2/16/19).
- No public CLI, manifest, publisher lock, or Normalizer-adjacent code exists anywhere in this phase.
- No official-Master sidecar was generated.
- No persistent generated `.bin` artifact exists anywhere in the repository.
- HEAD unchanged: `5ea55a2352e5d4609f8f267e94d22bb9219040b9`.
- `git status`: `tools/sfm_master_sidecar/reader.py` shows modified; `tests/sidecar/corruption_helpers.py`
  and the 8 new test files, plus this audit document, are new/untracked. **Nothing staged, nothing
  committed.**
- No agents or subagents were used.
