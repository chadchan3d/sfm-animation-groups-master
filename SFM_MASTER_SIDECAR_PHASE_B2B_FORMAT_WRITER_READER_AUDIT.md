# SFM Master Sidecar — Phase B2B: Experimental Format + Writer/Reader Audit

First production sidecar code. No CLI, manifest, publisher, Normalizer integration, official-Master
sidecar generation, Gate 1 declaration, or format v1 freeze in this phase. Qualified ONLY against the
small B2A fixture corpus (`tests/sidecar/fixtures/`) — NOT the official Master (reserved for Phase B2D).

## 1. VERDICT

**PASS for Phase B2B's own bounded scope.** No STOP condition was triggered. The experimental packed
format, deterministic writer, and Python-2.7-and-3-compatible reader were implemented exactly against
`SFM_MASTER_SIDECAR_PHASE_B1_2_FINAL_IMPLEMENTATION_SPEC.md`'s normative Sections 5–24/27–28, and every
one of the 28 sidecar-profile-eligible B2A `valid/` fixtures round-trips with **zero mismatches** against
both `tools/sfm_master_core.py` and the independent `tests/sidecar/oracle.py`. The 2 B2A `unsupported/`
fixtures are correctly refused by the writer's compatibility-profile gate. All 10 B2A `malformed/`
fixtures are rejected by `sfm_master_core` before the writer is ever invoked. This is an **experimental,
unfrozen format** (`format_contract_version = 0`) — passing this phase's own qualification does not
constitute Gate 1 PASS, a release candidate, or a stable v1, and none of those is declared here.

## 2. FILES CREATED / CHANGED

Created (all new; nothing pre-existing was modified):

- `tools/sfm_master_sidecar/__init__.py` — minimal, import-safe package root.
- `tools/sfm_master_sidecar/format.py` — constants/struct layouts/versions/section IDs/sentinels/checksum
  and fold helpers. Python 2.7 + 3 compatible.
- `tools/sfm_master_sidecar/writer.py` — deterministic compiler. Python 3 only.
- `tools/sfm_master_sidecar/reader.py` — full Section 20 (A–J) validation + lifetime + lookup. Python 2.7
  + 3 compatible.
- `tests/sidecar/test_format_layout.py` — pure constants/layout/ASCII-fold-byte/digest tests.
- `tests/sidecar/test_writer_reader_roundtrip.py` — the 28-fixture dual-oracle round trip, unsupported
  refusal, malformed non-reachability.
- `tests/sidecar/test_reader_lookup.py` — MasterUnknown, exact-spelling-inside-conflict, open-mode
  authority restrictions.
- `tests/sidecar/test_reader_lifetime.py` — the required invalidate→close→close lifecycle test plus
  supporting lifetime-state-machine tests.
- `tests/sidecar/test_writer_determinism.py` — same-process and cross-`PYTHONHASHSEED`-subprocess
  determinism.
- `tests/sidecar/test_basic_corruption.py` — the basic (not full B2C matrix) corruption cases.
- `tests/sidecar/test_runtime_import_boundary.py` — static/import-discipline Python-2.7-boundary checks.

**Unchanged, reconfirmed:** `sfm_defaultanimationgroups.txt` (SHA
`ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`), `tools/sfm_master_core.py`,
`tools/validate_master.py`, every B2A oracle/fixture/test file.

## 3. MODULE BOUNDARIES

- `__init__.py`: `__all__ = []`, zero imports beyond nothing — verified by
  `test_runtime_import_boundary.py::test_init_does_not_implicitly_import_writer_or_core_or_cli` (AST-based,
  not a prose/substring check) and by a subprocess import-in-isolation test.
- `format.py`: imports only `hashlib`, `struct`, `collections.namedtuple` — verified importable in a fresh
  subprocess with no `tools/` `sfm_master_core`/`writer` on `sys.path`
  (`test_format_module_is_importable_in_isolation`).
- `reader.py`: imports only `binascii` and `format` (sibling module) — verified the same way
  (`test_reader_module_is_importable_without_writer_or_core_present`). Contains **zero** references to
  `sfm_master_core`, `dataclasses`, `pathlib`, or `typing` (AST-checked, not grepped).
  `writer.py` is a Python-3-only file (uses `bytes.fromhex`, f-string-free but otherwise ordinary Python 3
  idioms) that imports `sfm_master_core` directly by inserting `tools/` onto `sys.path` — the same
  convention the existing B2A test files already use, since `tools/` has no `__init__.py` and is not
  itself a package.

## 4. EXPERIMENTAL FORMAT IDENTITY

`format_contract_version = 0`, `authority_semantics_version = 0` (both `format.FORMAT_CONTRACT_VERSION_EXPERIMENTAL`
/ `AUTHORITY_SEMANTICS_VERSION_EXPERIMENTAL`), matching the manifest example in the final spec's Section 33
and explicitly not `1` (final spec Sections 5/44 — no format freeze happens in this phase). No
`compiler_build_version` field exists anywhere in the binary (final spec Section 6's correction).

## 5. HEADER / DIRECTORY IMPLEMENTATION

`HEADER_STRUCT = "<8sII32sQQQI32s"`, size 108 bytes, fields exactly per final spec Section 6/17: `magic`,
`format_contract_version`, `authority_semantics_version`, `source_sha256` (32 raw digest bytes, not hex),
`source_byte_length`, `payload_length`, `section_directory_offset`, `section_count`,
`embedded_integrity_digest` (computed with its own 32 bytes zeroed during hashing, per Section 19).
`DIRECTORY_ROW_STRUCT = "<IQQII"` (`section_id, offset, length, row_count, row_size`), 28 bytes/row.
Layout is HEADER, then SECTION DIRECTORY, then the 9 sections contiguous in the fixed Section 5 order, with
no gaps and no padding. The reader treats the HEADER's own byte range and the SECTION DIRECTORY's own byte
range as protected regions exactly like any data section (final spec Section 7's correction) — all nine
sections plus these two protected regions are sorted by offset and checked pairwise for overlap.
`row_size` is cross-checked against the reader's own `NORMATIVE_ROW_SIZES` table (keyed by
`format_contract_version`) and is **never** used as decoding authority — verified directly by
`test_basic_corruption.py` exercising a wrong-version file, and by design: `reader.py`'s unpack functions
always call `format.py`'s fixed `struct.Struct` objects, never a width derived from the file.

## 6. STRING REPRESENTATION

One contiguous STRING POOL byte blob + a STRING TABLE of `(offset: u32, length: u32)` rows, deduplicated
by exact byte-for-byte string across one shared ID space (group names, metadata keys/values, control
literals, and fold keys all share the same pool). `STRING_POOL`'s own directory row uses `row_size = 1`
(byte granularity) so the generic `row_count * row_size == length` invariant (final spec Section 20.A)
applies uniformly to it too — a deliberate, documented choice since the final spec does not define row
semantics for a variable-length blob section. First-seen string ID assignment order is fully deterministic
(never dict/set iteration): groups' names (in `declare_order`), then every group's metadata (key, value) in
source order, then every occurrence's literal in global source order, then every fold key in
sorted-fold-key-UTF-8-byte order. Escape spelling is verified to survive unmodified end-to-end
(`test_escape_spelling_round_trips_with_backslashes_intact`, re-checking the exact Phase B1.2 bug: a
literal containing `\"` round-trips with every backslash intact). Non-ASCII BMP and non-BMP (astral-plane,
4-byte UTF-8) text both round-trip exactly (fixtures 19/20).

## 7. GROUP / WRAPPER ROUND TRIP

`path_id` is the GROUP TABLE row index, assigned by `declare_order` (verified as an invariant assertion in
`writer.compile_sidecar`: `g.declare_order == i` for every group, since `sfm_master_core.MasterParseResult.groups`
is already `declare_order`-sorted and contiguous from 0). `parent_path_id` uses `ROOT_SENTINEL = 0xFFFFFFFF`
for the sole parentless group. Full paths are never stored — reconstructed by walking `parent_path_id` to
`ROOT_SENTINEL` (`SidecarReader.group_full_path`, memoized, terminates by construction since the anti-cycle
check enforces `parent_path_id < path_id`). A custom (non-`"groupFile"`) wrapper name round-trips correctly
(`test_custom_wrapper_name_round_trips`), proving no hardcoded wrapper-name assumption anywhere in the
writer or reader. Deep nesting (fixture 27, 15 levels) and same-line sibling declarations (fixture 07,
exercising the `declare_order`-vs-`sibling_rank` tie-break) both round-trip exactly.

## 8. CHILD INDEX

Cardinality `child_index_row_count = group_count - parentless_group_count`, checked generically (from the
file's own declared counts, never hardcoded) both by the writer's construction and by the reader's
Section 20.C/D/J checks (bounds, ownership agreement, dense `0..child_count-1` sibling-rank run,
`declare_order` monotonic with `sibling_rank`, and the cardinality cross-check against the sum of every
group's own `child_count`). Every non-root group is confirmed to appear in exactly one slice; every
parentless group is confirmed to appear in none.

## 9. METADATA

`(path_id, key_string_id, value_string_id, source_order)` rows, one per entry, duplicates preserved in
exact source order. `metadata_count == 0` is never conflated with "key K absent" (final spec Section 11) —
the reader's `iter_metadata` always yields the group's actual slice, however many rows it has. Duplicate
metadata keys (fixture 15), an explicit `"0"` value distinct from absence (fixture 16), an unknown metadata
key preserved opaquely (fixture 17), and an empty-string metadata value (fixture 18) all round-trip
exactly, verified against `sfm_master_core`'s own `GroupMetadata.entries`.

## 10. OCCURRENCES

OCCURRENCE TABLE row index **is** `global_rank` (no separate stored field) — `result.occurrences` is
already in that exact order by construction, so the writer emits rows in list order directly. Duplicate
identical controls within one group (fixture 10) and across groups (fixture 11) both round-trip with
correct `local_rank`/`global_rank` distinctness, verified against both oracles.

## 11. FOLD TABLE / LOOKUP

FOLD TABLE sorted by raw folded-key UTF-8 bytes (writer: `sorted(fold_families.keys(), key=lambda k: k.encode("utf-8"))`;
reader: Section 20.H strict-ascending check plus a binary search in `lookup_fold` over the same ordering).
No `conflict_flag`/`destination_count` field exists — `lookup_fold` always recomputes the distinct
destination count fresh from the occurrence range (final spec Section 24). Verified: same-destination alias
families resolve `Hit` (fixture 12); cross-destination families resolve `FoldConflict` (fixture 13); an
exact spelling that matches one specific member of a still-conflicting 3-destination family still resolves
`FoldConflict`, not `Hit` (fixture 14, `test_exact_spelling_inside_conflict_tests`) — the literal rule from
final spec Section 24 stated explicitly: "even if the query's exact spelling matches one specific member."
A large (30-member) alias family (fixture 28) round-trips and resolves correctly. A query with no matching
fold resolves `MasterUnknown`; a malformed/oversized query raises (`TypeError`/`ValueError`), never
`MasterUnknown` (final spec Sections 4/24's explicit non-conflation).

## 12. EMBEDDED INTEGRITY DIGEST

One whole-file SHA-256, computed with the `embedded_integrity_digest` field's own 32 bytes zeroed during
hashing (`format.compute_embedded_integrity_digest`, operates on a temporary copy, never mutates its
input — verified by `test_digest_computation_zeroes_only_the_digest_field_and_restores_buffer`).
Recomputed and compared at every `open_generation`/`open_generation_unbound` call. Distinct from the
ordinary external whole-file SHA-256 (`sfm_master_core.sha256_of_bytes` on the full unmodified blob), which
this phase does not yet use anywhere (no manifest/filename-generation code exists yet).

## 13. SOURCE BINDING

`open_generation_unbound(path_or_bytes)`: performs the full Section 20 validation but never checks source
identity; `lookup_fold` (and only `lookup_fold` — inspection methods remain permitted diagnostically) raises
`AuthorityUnavailable` if called on such a handle (`test_unbound_open_refuses_lookup_fold`).
`open_generation(path_or_bytes, expected_source_sha256)`: performs the same full validation, THEN compares
the sidecar's embedded `source_sha256` header field (case-insensitive hex) against the caller-supplied
value, raising `SourceMismatchError` (a subclass of `AuthorityUnavailable`) **before returning a usable
handle** on any mismatch — verified directly, including the case-insensitivity.

## 14. BACKING MODEL

Candidate A only, exactly as specified (final spec Section 22): `_read_all` reads the entire file (or
accepts an in-memory `bytes`/`bytearray` directly) into one buffer; `_validate_and_decode` validates that
exact buffer and eagerly decodes every section into plain Python lists once, at open time; every subsequent
query is answered from those decoded lists — no further filesystem access for the handle's life. Candidates
B and C are not built, referenced only by name in this document, consistent with their still-unproven
stability status.

## 15. READER LIFETIME

VALID / INVALID / CLEANED implemented as `SidecarReader._state` string values. `_invalidate()` transitions
VALID→INVALID and **defers cleanup to `close()`** (the implementation's chosen one of the two permitted
Section 23 strategies — documented explicitly in the module docstring and in `_invalidate`'s docstring).
`close()` is idempotent, releases `_backing`/`_path_cache` whether called from VALID or INVALID, and is a
harmless no-op once CLEANED; it never restores authority. The exact 9-step invalidate→close→close lifecycle
test required by final spec Section 41/B1.2a passes (`test_reader_lifetime.py::RequiredInvalidateCloseCloseLifecycleTest`),
including the specific case that caught a real bug during this phase (see Section 25 below): a lazy,
provider-backed generator (`iter_groups`/`iter_occurrences`) obtained before invalidation fails on its next
access, checked on a still-untouched second generator to get a clean "first access after invalidation"
signal (an exhausted-by-a-prior-exception Python generator cannot be re-probed meaningfully). `Hit`/`FoldConflict`
are the other permitted kind — already-materialized, non-authoritative copies that remain readable even
after the provider that produced them is closed (`test_hit_result_remains_readable_after_close`).

## 16. PYTHON-2.7 COMPATIBILITY DISCIPLINE

**No Python 2.7 interpreter is available in this environment** (`py -2 --version` falls through to the
installed Python 3.10.6; `where python2` finds nothing) — confirmed again at the start of this phase, per
the task's own explicit allowance ("B2B does not yet need actual Python 2.7 execution if unavailable
locally; that remains mandatory Gate 1 evidence"). This phase substitutes:
- AST-based checks that `format.py`/`reader.py` contain zero f-strings (`ast.JoinedStr`) and zero walrus
  operators (`ast.NamedExpr`) — the two common accidental Python-3-only constructs.
- AST-based checks that neither module imports `sfm_master_core`, `dataclasses`, `pathlib`, `typing`, or
  `writer`.
- Subprocess import-in-isolation checks for both modules and the package `__init__.py`.
- Manual construction discipline: both modules use only `struct`, `hashlib`, `binascii`, `bytearray`/`bytes`
  indexing (which behaves identically for `str` in Python 2.7 and `bytes` in Python 3),
  `collections.namedtuple` (available in Python 2.7's standard library), plain classes with `__slots__`
  instead of `dataclasses`, `%`-style string formatting instead of f-strings, and generator functions with
  no Python-3-only syntax.

**This is explicitly NOT a substitute for actual Python 2.7 execution.** Real execution of
`format.py`/`reader.py` under a real Python 2.7 interpreter remains mandatory, deferred Gate 1A evidence
(final spec Section 38) and is not claimed as satisfied by anything in this phase.

## 17. FIXTURE ROUND-TRIP RESULTS

All 28 sidecar-profile-eligible `tests/sidecar/fixtures/valid/*.txt` fixtures: **0 mismatches** against
both `sfm_master_core` and `tests/sidecar/oracle.py`, covering — per fixture — full group parity
(name/parent/sibling_rank/declare_order/ancestry via reconstructed full path), full ordered occurrence
parity (literal/full_path/local_rank/global_rank), full metadata parity (key/value/source order,
duplicates), and full fold-lookup parity (Hit/FoldConflict classification plus the complete occurrence
evidence set per fold, not just a destination-count summary). Explicit required-semantics list (final spec
Part 30) coverage: custom wrapper ✓ (04), wrapper-owned control ✓ (02), wrapper-owned metadata ✓ (03),
nested parent/child order ✓ (05, 27), controls-before/after-nested-child order ✓ (08, 09), duplicate-control
distinctness within/across groups ✓ (10, 11), same-destination alias Hit ✓ (12), cross-destination alias
FoldConflict ✓ (13), exact-spelling-inside-conflict FoldConflict ✓ (14), duplicate/unknown/explicit-"0"
metadata ✓ (15, 16, 17), empty metadata value ✓ (18), BMP/non-BMP UTF-8 ✓ (19, 20), escape-spelling
preservation ✓ (21, 22), whitespace-distinction preservation ✓ (23), BOM/no-BOM pair ✓ (24, 25),
EOF-final-entry preservation ✓ (26), deep nesting ✓ (27), large alias family ✓ (28), same-line sibling
declarations ✓ (07).

## 18. FOLD CONFLICT RESULTS

Covered above (Section 11/17). Additionally: `test_reader_lookup.py::ExactSpellingInsideConflictTests`
independently re-verifies, for every one of fixture 14's three exact spellings, that each individually
resolves `FoldConflict` with all 3 destinations present, and `test_same_destination_family_is_a_hit_not_a_conflict`
confirms fixture 12's spellings all resolve `Hit`.

## 19. DETERMINISM RESULTS

Same-process double-compile is byte-identical across 6 representative fixtures (including a fresh
independent `parse_master_bytes` call each time, not object reuse). Cross-`PYTHONHASHSEED`-subprocess
compilation (`PYTHONHASHSEED=0` vs. an arbitrary large seed) of the 30-member alias-family fixture produces
an identical SHA-256. No dict/set/hash iteration ever determines output order anywhere in `writer.py` — every
ordering-sensitive step iterates an explicitly sorted or already-deterministically-ordered Python list
(`sfm_master_core`'s `declare_order`/global-source-order lists, or an explicit `sorted(..., key=...)` call
for fold keys).

## 20. BASIC CORRUPTION RESULTS

Wrong magic, unsupported `format_contract_version`, unsupported `authority_semantics_version`, bad embedded
checksum, truncated header, zero-byte file, truncated file (mid-section), `payload_length` mismatch, and
source-binding mismatch: all raise `AuthorityUnavailable` (or its `SourceMismatchError` subclass) with a
specific, identifying message — never a raw `struct.error`/`IndexError`/`UnicodeDecodeError`, never a
silent partial read. This is explicitly the **basic** list only (final spec Section 39's full Gate 1B
matrix — every Section 20.A–J check individually exercised with checksum-valid/checksum-invalid pairs — is
Phase B2C's job, not this phase's, per the task's own explicit scope limit).

## 21. PROFILE-UNSUPPORTED RESULTS

Both B2A `unsupported/` fixtures (`empty_document.txt`: 0 parentless groups; `multiple_parentless_groups.txt`:
2 parentless groups) parse cleanly under `sfm_master_core` (`result.ok is True`) but are refused by
`writer.check_compatibility_profile`/`compile_sidecar` with a `SidecarProfileError` naming the exact
parentless-group count — the compiler-level gate from final spec Section 3, entirely separate from
`sfm_master_core.py` (unmodified) and from `tools/validate_master.py`'s official policy (unmodified).

## 22. TEST RESULTS

**Corrected accounting (originally misstated — see the B2B Audit Reconciliation checkpoint).** "Ordinary
tests" below means top-level `unittest` test methods, as `pytest`'s own summary line counts them (each
counted once regardless of how many `subTest`/parameterized assertions it contains); "subtests" means the
separate `subTest(...)` context-manager assertions `pytest`'s `unittest`-subtest plugin counts and reports
on its own summary line. These are two different, non-interchangeable counters — a single ordinary test can
contain zero, one, or many subtests.

Measured by running the exact file sets in isolation with `python -m pytest <files> -q`:

| Scope | Files | Ordinary tests | Subtests |
|---|---|---|---|
| Pre-B2B baseline | everything under `tests/` EXCLUDING the 7 new B2B files below (includes the 3 pre-existing B2A files under `tests/sidecar/`: `test_oracle.py`, `test_fixture_contracts.py`, `test_official_master_oracle_parity.py`) | 81 | 121 |
| New B2B only | the 7 new files: `test_format_layout.py`, `test_writer_reader_roundtrip.py`, `test_reader_lookup.py`, `test_reader_lifetime.py`, `test_writer_determinism.py`, `test_basic_corruption.py`, `test_runtime_import_boundary.py` | **60** | **64** |
| Total (`python -m pytest tests/ -q`) | everything under `tests/` | **141** | **185** |

`81 + 60 = 141` and `121 + 64 = 185` — both reconcile exactly; the composition is simply "pre-B2B baseline"
plus "the 7 new B2B files," nothing more and nothing less.

**The previously reported "89" was not "new B2B tests."** It was the total ordinary-test count of running
`tests/sidecar/` as a whole directory (`python -m pytest tests/sidecar -q` → 89 passed) — which is the sum
of the 3 pre-existing B2A files already counted inside the 81-test pre-B2B baseline (`test_oracle.py`: 6,
`test_fixture_contracts.py`: 16, `test_official_master_oracle_parity.py`: 7 — 29 tests) plus the 60 new B2B
tests (`29 + 60 = 89`). Labeling that directory-scoped number "New B2B: 89 tests" alongside "prior 81 →
total 141" double-counted those 29 pre-existing B2A tests and was corrected here. No test file's contents,
no test outcome, and no test count on disk changed — this section's numbers were verified fresh
(`python -m pytest tests/sidecar -q` → 89 passed, 185 subtests, confirming the directory total independently
matches `29 + 60`) as part of this same checkpoint; only the prose accounting above was wrong.

- Pre-B2B baseline: **81 passed, 0 failed, 121 subtests passed**.
- New B2B tests (the 7 files listed above, run in isolation): **60 passed, 0 failed, 64 subtests passed**.
- Total: `python -m pytest tests/ -q` → **141 passed, 0 failed, 185 subtests passed**.
- `python tools/validate_master.py sfm_defaultanimationgroups.txt` → PASS (43 groups, 128,555 controls,
  124,728 fold keys, 0 exact duplicates, 0 cross-path fold-family invariant violations — all unchanged from
  the B2A baseline).
- `git diff --check`: clean (no whitespace errors).

## 23. KNOWN INCOMPLETE B2C WORK

Everything final spec Section 39/41 requires that this phase deliberately does not attempt:
- The full per-check (A–J) corruption matrix, each in checksum-valid AND checksum-invalid form.
- The remaining Gate 1B backing/lifetime fixtures this phase's scope did not call for: a view used after
  its parent handle is closed (no separate "view" object type exists yet — only the provider itself and its
  lazy generators/materialized results, which are covered); an old view proven to remain tied to its
  original generation after a second, separate generation is opened (partially covered by
  `test_two_independently_opened_generations_do_not_share_state`, but not against two *different* source
  generations since only one small fixture's compiled bytes were used); publishing-a-new-manifest
  non-retargeting (no manifest/publisher exists yet — genuinely inapplicable, not merely deferred).
- Real Python 2.7 execution (Section 16 above).
- Whole-family bounded *views* with `add_identity`/`query_complete_backing` (final spec Section 25) — not
  built this phase; `Hit`/`FoldConflict` already carry complete family evidence, which was judged
  sufficient for B2B's fixture-only scope without a separate view API.
- Long strings near the Section 18 single-string-length limit, and counts exceeding the former B1 u16
  ranges (>65,535) — no B2A fixture exercises these; the resource-limit *checks* exist and were smoke-tested
  directly (Section 22), but no fixture-driven test exercises them at real scale.
- Anything against the official Master (explicitly reserved for Phase B2D).

## 24. READINESS FOR B2C

The format/writer/reader triad is structurally complete and internally consistent against the full Section
20 A–J validation contract (not merely the "basic" subset tested this phase) — the validation code itself
implements every A–J check, so Phase B2C's job is authoring the *targeted corruption fixtures* that exercise
each check individually and in both checksum-valid/checksum-invalid forms, not writing new validation logic.
No design contradiction, writer/reader interpretation mismatch, or semantic-core defect was discovered.

## 25. GIT / SAFETY STATE

- `sfm_defaultanimationgroups.txt`: unchanged, SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`.
- `tools/sfm_master_core.py`, `tools/validate_master.py`: unchanged.
- B2A oracle/fixtures (`tests/sidecar/oracle.py`, `fixtures/`, `fixture_manifest.json`,
  `test_oracle.py`, `test_fixture_contracts.py`, `test_official_master_oracle_parity.py`): unchanged.
- No public CLI, manifest, publisher lock, or Normalizer-adjacent code exists anywhere in this phase.
- No official-Master sidecar was generated (confirmed: the official Master was parsed read-only, once, only
  to confirm it would pass the eligibility gate — it was never passed to `compile_sidecar`).
- No persistent generated `.bin` artifact exists in the repository (`find . -name "*.bin"` returns nothing
  outside `.git/`; all tests operate on in-memory `bytes`).
- HEAD unchanged: `d2d37b9c9bf2e354444f2fa0aea0e0253b5a93a9`.
- `git status`: only new, untracked files (`tools/sfm_master_sidecar/`, the 7 new `tests/sidecar/test_*.py`
  files, this audit document) — nothing staged, nothing committed, nothing modified in place.
- No agents or subagents were used.
