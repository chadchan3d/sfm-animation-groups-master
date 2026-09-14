# SFM Master Sidecar — Phase B1.2 Final Pre-Implementation Specification

Specification correction only. No binary/compiler/reader code written. `sfm_defaultanimationgroups.txt`
unchanged. Nothing staged, nothing committed.

This document **supersedes** `SFM_MASTER_SIDECAR_PHASE_B1_DESIGN.md` and
`SFM_MASTER_SIDECAR_PHASE_B1_1_REVISED_DESIGN.md` for implementation purposes. It does not reopen the
architecture Astra already confirmed (packed binary direction, TXT-as-sole-authority, public/custom
compiler model, Python 3 compiler / Python 2.7 reader split, immutable generation + manifest model,
fold-family conflict semantics, whole-family view semantics, Gate 2 strategy, format-freeze timing) — it
corrects five localized defects (A–E below) plus the escape-wording and consistency points Astra flagged.

Baseline (reconfirmed fresh before writing this document): HEAD `8b4f0cb54750a5360a9897bb981af5463ab28681`,
Master SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`, groups 43, occurrences
128,555, folds 124,728, duplicates 0, ASCII conflicts 0, validator PASS, tests 52 passed.

---

## 1. Executive Status

**READY FOR IMPLEMENTATION.** This revision (B1.2a) resolves the single remaining defect Astra's final
compliance closure identified — the conflation of *provider invalidation* with *owned-resource cleanup*
in §23's lifetime contract (see the corrected §23 below) — leaving no known pre-implementation blocking
design defect. This is still an **experimental format** (§44) — Gate 1 passing identifies a release
candidate, not a stable v1. The five original corrections (A–E), all confirmed resolved:

- **A. M4 — exhaustive validation contract**: all sampling language removed; every check is total over its
  domain (§20).
- **B. M5 — validated-backing stability**: the invariant is stated as "the bytes used after validation
  are the exact bytes that were validated," with the mmap-snapshot overclaim removed, Candidate A
  specified as the only backing built for Gate 1 (§22), and (as of B1.2a) the lifetime contract itself
  corrected so that invalidity and resource release are tracked as two independent facts, never conflated
  (§23).
- **C. M9 — independent-oracle comparison scope**: corrected to compare the semantic projections the
  binary actually stores (per-group order, per-occurrence order, per-metadata order), not a single
  interleaved raw event stream the format never claimed to preserve (§37).
- **D. Initial root-profile compatibility rule**: the compiler now has an explicit structural-eligibility
  gate (`len(wrapper_paths) == 1`) separate from `sfm_master_core`'s broader generic acceptance (§3).
- **E. Gate 1 sequencing**: split into Gate 1A/1B/1C plus a Final Gate 1, with publication/locking built
  and proven **before** Final Gate 1 is ever declared passed (§38–41).

---

## 2. Qualified Source Semantics

Unchanged from B1.1 §3 — these are B0.1-committed facts, not re-derived here:

1. The wrapper is a real, ordinary `Group`. 2. Canonical paths include the wrapper
(`groupFile/Face/Eyes`). 3. `MasterParseResult.wrapper_paths` is distinct from `root_paths`. 4. Every
non-comment token is consumed or produces a `GrammarError`. 5. Duplicate full group paths are rejected.
6. Group names containing `/` are rejected (current compatibility profile). 7. Parent relationships derive
structurally from parser stack state. 8. Group ordering is `declare_order` (token-encounter based), not
line-based. 9. Duplicate CONTROL occurrences remain representable. 10. Cross-destination fold families
remain representable. 11. Unknown-but-well-formed metadata remains opaque and preserved, in order,
duplicates intact. 12. Source decoding is strict UTF-8, current BOM handling, no normalization, no
repair.

The compiler's sole input remains `sfm_master_core.parse_master_bytes(...)`; compilation is refused if
`result.ok` is `False`.

---

## 3. Compatibility Profile (Correction D)

**The contradiction between `sfm_master_core`'s generic acceptance and the sidecar's initial
compatibility profile is resolved by adding a compiler-level structural-eligibility gate, distinct from
both `sfm_master_core`'s own `.ok` check and from `tools/validate_master.py`'s official-release policy.**

```
if not result.ok:
    refuse: "source is not grammatically valid" (unchanged, sfm_master_core's own gate)

parentless = [g for g in result.groups if g.parent_path is None]
if len(parentless) != 1:
    refuse: "source has {N} parentless group(s); the initial sidecar compatibility profile
             requires exactly one document/wrapper group" -- COMPILER-LEVEL REFUSAL,
             not a sfm_master_core change, not an official-policy change.
```

This is explicitly **generic sidecar compatibility policy**, layered *above* `sfm_master_core` (which
correctly continues to represent broader document shapes structurally — a zero- or multi-wrapper document
is still validly *parsed*, just not yet *compilable* by this profile) and *below* `tools/validate_master.py`'s
official-release policy (which is a separate, additional, official-Master-only gate; §30). No change is made
to `sfm_master_core.py` for this reason — the restriction lives entirely in the (not-yet-implemented)
compiler's own eligibility check.

**Explicit behavior for edge cases (§15 of the task, Gate 1 fixtures required — see §37.C):**

| Case | `sfm_master_core` result | Compiler behavior |
|---|---|---|
| Exactly one parentless group (the normal/official shape) | `ok=True`, `wrapper_paths` has 1 entry | Compiles |
| Zero parentless groups (a pathological/empty or malformed-but-brace-balanced document) | `ok=True` is possible (e.g. a genuinely empty document — no groups at all — parses with zero errors) | Refused: "0 parentless groups; unsupported document shape" |
| Two or more parentless groups (e.g. two independent top-level `{...}` blocks with no common wrapper) | `ok=True` is possible | Refused: "2 parentless groups; unsupported document shape" |

---

## 4. String / Escape / UTF-8 Contract (Escape-Wording Correction)

**Corrected claim, verified directly against the tokenizer's actual behavior before writing this
section** (not assumed): the tokenizer performs **no escape resolution whatsoever**. Its
`(?:[^"\\]|\\.)*` regex construct exists solely so a backslash-quote sequence does not prematurely
terminate a quoted-string match — the token's captured value retains **every backslash character exactly
as written** in the source. Verified: source `"He said \"hi\""` parses to the literal Python string `He
said \"hi\"` (backslashes intact), not `He said "hi"`. The compiler adds no escaping or unescaping of its
own on top of this.

The contract, stated precisely:

```
source bytes --(strict UTF-8 decode, utf-8-sig BOM strip if present, no repair, no normalization)-->
    exact parsed token values (escape spelling preserved verbatim, never interpreted)
        --(UTF-8 re-encode, no transformation)--> stored string-pool bytes
```

| Concern | Contract |
|---|---|
| Compiler input type | Python 3 `str` — the exact token values `sfm_master_core` produces, escape spelling intact |
| Stored string encoding | Strict UTF-8 encoding of that exact `str` value, unmodified |
| Reader query type | UTF-8-encoded byte string only (`str` in Python 2.7, `bytes` in Python 3) |
| Reader output type | UTF-8-encoded byte string, matching storage exactly |
| Malformed query encoding | Input/authority error, raised, never `MasterUnknown` (§24) |
| Oversized query (> the §18 query-length limit) | Same — input error, never `MasterUnknown` |
| Python 2 behavior | `str` (bytes) throughout; `ascii_fold` iterates raw bytes via `ord()`/`chr()`; no `unicode()` anywhere in `runtime_safe/` |
| Python 3 behavior | `bytes` at the reader's public surface; the compiler works in `str` internally via `sfm_master_core`, encoding to `bytes` only at the writer boundary |

Source SHA-256 remains the identity of the original exact TXT bytes (formatting/BOM/newlines included) —
orthogonal to the string pool, which represents *parsed token values*, not source bytes.

**ASCII-fold/UTF-8 compatibility proof** (unchanged from B1.1 §3, restated): because ASCII bytes
`0x41`–`0x5A` never occur as part of a multi-byte UTF-8 sequence (UTF-8's self-synchronizing design
reserves those byte values exclusively for standalone ASCII characters), folding at the byte level after
UTF-8 encoding is provably identical to folding at the Unicode-character level before encoding:
`UTF8(ascii_fold(s)) == ascii_fold_bytes(UTF8(s))` for every valid parsed token, non-ASCII and non-BMP
characters included. This is a required Gate 1A check (§38), exercised over every one of today's ~221,565
pool strings plus the non-ASCII/mojibake/non-BMP fixtures of §37.C.

---

## 5. Experimental Binary Format

Unchanged section family from B1.1 §5 (INVENTORY FOOTER and per-fold `conflict_flag` remain removed —
Astra confirmed this direction, not reopened here):

```
[ HEADER ]
[ SECTION DIRECTORY ]
[ STRING POOL ]
[ STRING TABLE ]
[ GROUP TABLE ]
[ CHILD-ID INDEX ]
[ METADATA TABLE ]
[ OCCURRENCE TABLE ]
[ OCCURRENCE-BY-GROUP INDEX ]
[ FOLD TABLE ]
[ OCCURRENCE-BY-FOLD INDEX ]
```

`format_contract_version` for this document's design is the **experimental** identifier (§44) — not `1`.

---

## 6. Header

**Corrected (Part 19): `compiler_build_version` is removed from the embedded header entirely.**
Rationale: embedding it would make deterministic-output identity (§28) depend on which compiler build
produced the file, even when source bytes and both normative versions are identical — directly
contradicting the determinism guarantee. Compiler provenance is recorded externally only (manifest §33,
CLI output, build report), never inside the canonical binary bytes.

| Field | Type | Notes |
|---|---|---|
| `magic` | 8 bytes | fixed literal, e.g. `b"SFMMSTR\0"` |
| `format_contract_version` | u32 | byte-layout schema; **normative decoding authority lives in the reader's own code for this version, never in file-declared widths** (§9's row_size correction) |
| `authority_semantics_version` | u32 | grammar/encoding/hierarchy/fold-rule semantics |
| `source_sha256` | 32 bytes | identity of the original exact TXT bytes |
| `source_byte_length` | u64 | source file size |
| `payload_length` | u64 | total sidecar file length |
| `section_directory_offset` | u64 | absolute byte offset of the SECTION DIRECTORY |
| `section_count` | u32 | number of directory entries |
| `embedded_integrity_digest` | 32 bytes | SHA-256 over the entire file with this field's own bytes zeroed during computation (§19) |

Byte order: **little-endian** throughout, every multi-byte field, no exceptions.

---

## 7. Section Directory

One row per section, in fixed normative order (§5): `(section_id: u32, offset: u64, length: u64,
row_count: u32, row_size: u32)`.

**Corrected (Part 5): `row_size` is retained in the directory as a declared, cross-checkable value, but
it is NEVER used as decoding authority.** The reader owns its own normative `row_size` constant for each
section, hardcoded per `format_contract_version` (§16's field-width tables are that normative source).
At open time: `file_declared_row_size == reader_normative_row_size` for every section, or
`AuthorityUnavailable`. The reader then decodes using **its own** normative width, never the file's
value, even after the equality check passes — the check exists purely to catch a version/layout mismatch
early and explicitly, not to make the file self-describing for decoding purposes. This closes a real
attack/corruption surface: a corrupted or adversarial file cannot cause the reader to reinterpret bytes
at an attacker-chosen width.

**Header and directory are protected regions too (Part 6):** the same overlap-freedom check applied
between sections (§20.A) also treats the HEADER's own byte range (`[0, header_size)`) and the SECTION
DIRECTORY's own byte range (`[section_directory_offset, section_directory_offset + section_count *
directory_row_size)`) as two additional protected regions — no section may overlap either, and neither
may overlap any section. All range-end arithmetic (`offset + length`, `start + count`) is computed in a
width wide enough that the addition itself cannot silently wrap before the bounds comparison runs (e.g.
promote u32+u32 sums to a 64-bit accumulator before comparing against a u64 file length).

---

## 8. String Table

Unchanged from B1.1 §7: one contiguous UTF-8 STRING POOL blob + a `(offset: u32, length: u32)` STRING
TABLE indexed by `string_id`. Pooled: control literals, group names, metadata keys, metadata values,
folded keys — one shared pool, one ID space, deduplicated by exact byte-for-byte string (§4's escape
contract applies: two literals differing only in escape spelling, if such a case existed, would be
different exact strings, stored separately — but see §4, escape spelling is never altered, so this is
purely about legitimate exact-string differences, not an escaping edge case).

---

## 9. Group Table

Unchanged core fields from B1.1 §8, all widths now uniformly u32 (§17):

| Field | Type | Notes |
|---|---|---|
| `path_id` | u32 (= row index) | assigned by `declare_order` |
| `name_string_id` | u32 | |
| `parent_path_id` | u32 | `ROOT_SENTINEL = 0xFFFFFFFF` for a parentless group; otherwise `< path_id` |
| `declare_order` | u32 | |
| `sibling_rank` | u32 | 0-based among children of the same parent |
| `child_count` | u32 | |
| `child_index_start` | u32 | into CHILD-ID INDEX |
| `metadata_start` / `metadata_count` | u32 / u32 | into METADATA TABLE |
| `occ_by_group_start` / `occ_by_group_count` | u32 / u32 | into OCCURRENCE-BY-GROUP INDEX |

Full-path strings are not stored (reconstructed by walking `parent_path_id` to `ROOT_SENTINEL`).

---

## 10. Child-ID Index

**Corrected cardinality (Part 3):**

```
child_index_row_count = group_count - parentless_group_count
```

For the current official Master: `43 - 1 = 42` (verified directly against a fresh parse before writing
this document: 43 groups, exactly 1 parentless group, and the sum of every group's own `child_count`
independently totals exactly 42 — confirming the formula against real structure, not merely asserting
it). The reader validates this formula **generically** at open time (computed from the file's own
declared `group_count` and its own count of parentless rows), never hardcoded to `42` or to any other
Master's specific numbers.

Layout unchanged from B1.1 §9: one flat `u32[]` array, length `child_index_row_count`, holding child
`path_id` values laid out contiguously per parent in `(parent, sibling_rank)` order.

---

## 11. Metadata Table

Unchanged fields from B1.1 §10: `(path_id: u32, key_string_id: u32, value_string_id: u32, source_order:
u32)`, one row per entry, duplicates preserved, in exact source order.

**Absence wording corrected (Part 20):** `metadata_count == 0` for a group means that group has **no
metadata rows at all**. This is a distinct fact from "key K is absent" — a group with `metadata_count ==
3` can still have zero of those three rows carry key K; presence of a *specific* key is always determined
by scanning the group's slice (however many rows it has, including zero) for a matching `key_string_id`,
never inferred from the slice's row count alone. Both facts are real and must never be conflated in
documentation or in reader code comments.

---

## 12. Occurrence Table

Unchanged from B1.1 §11: stored in global source order, row index **is** `global_rank`. Each row:
`(literal_string_id: u32, path_id: u32, local_rank: u32, fold_id: u32)`. Represents, without
restriction: duplicate identical controls, repeated aliases, same-destination duplicates,
cross-destination occurrences — official validator policy is never encoded into the generic binary
(§30).

---

## 13. Occurrence-by-Group Index

Unchanged from B1.1 §12: `u32[]`, length = occurrence count, `global_rank` values permuted into
`(path_id, local_rank)` order. **Must be a complete, exact, gapless, non-overlapping partition of
`0..occurrence_count-1`** (§20.F) — not merely "every value is in bounds."

---

## 14. Fold Table

Unchanged core shape from B1.1 §13: one row per distinct fold key, sorted by folded-key raw UTF-8 bytes,
`(fold_key_string_id: u32, occ_index_start: u32, occ_index_count: u32)` — no `conflict_flag`, no
`destination_count` field. Conflict is always: distinct `path_id` values among the fold's occurrence
range, recomputed, count `> 1`.

**Additional required invariant (Part 7):** every fold row has `occ_index_count >= 1` — a fold with zero
occurrences is meaningless and is treated as corruption (`AuthorityUnavailable`), never silently accepted
as an empty/degenerate family.

---

## 15. Occurrence-by-Fold Index

Unchanged from B1.1 §14: `u32[]`, length = occurrence count, `global_rank` values permuted into
fold-grouped order. Same complete-partition requirement as §13.

---

## 16. Cardinality Formulas

Explicit, generically validated (never hardcoded to today's Master), each independently reconciled
against a fresh parse before this document was written:

| Section | Formula | Verified value (official Master) |
|---|---|---|
| GROUP TABLE rows | `group_count` | 43 |
| CHILD-ID INDEX rows | `group_count - parentless_group_count` | 42 |
| METADATA TABLE rows | `sum(group.metadata_count for group in groups)` | 54 |
| OCCURRENCE TABLE rows | `occurrence_count` | 128,555 |
| OCCURRENCE-BY-GROUP INDEX rows | `occurrence_count` | 128,555 |
| FOLD TABLE rows | `fold_count` | 124,728 |
| OCCURRENCE-BY-FOLD INDEX rows | `occurrence_count` | 128,555 |
| STRING TABLE rows | `string_count` | 221,565 (today's distinct pool strings) |

The reader validates every one of these relationships against the file's own SECTION DIRECTORY
`row_count` values at open time (§20.A), computed from the file's own GROUP TABLE/OCCURRENCE
TABLE/FOLD TABLE contents, never from an external constant.

---

## 17. Field Width Tables

**Default u32 for every count/ID/rank** (§10 of the task); u64 reserved for file-level byte
offsets/lengths only. Full normative table, one row per field, across every section:

| Section | Field | Width | Byte order | Sentinel | Meaning |
|---|---|---|---|---|---|
| HEADER | `magic` | 8 bytes | — | — | format identifier |
| HEADER | `format_contract_version` | u32 | LE | — | byte-layout schema |
| HEADER | `authority_semantics_version` | u32 | LE | — | grammar/fold/hierarchy semantics |
| HEADER | `source_sha256` | 32 bytes | — | — | source identity |
| HEADER | `source_byte_length` | u64 | LE | — | source size |
| HEADER | `payload_length` | u64 | LE | — | sidecar size |
| HEADER | `section_directory_offset` | u64 | LE | — | directory location |
| HEADER | `section_count` | u32 | LE | — | directory row count |
| HEADER | `embedded_integrity_digest` | 32 bytes | — | — | self-referential whole-file digest |
| DIRECTORY row | `section_id` | u32 | LE | — | which section |
| DIRECTORY row | `offset` | u64 | LE | — | section start |
| DIRECTORY row | `length` | u64 | LE | — | section byte length |
| DIRECTORY row | `row_count` | u32 | LE | — | declared row count (cross-checked, not decoding authority) |
| DIRECTORY row | `row_size` | u32 | LE | — | declared row size (cross-checked against reader's own normative constant, §7) |
| STRING TABLE row | `offset` | u32 | LE | — | into STRING POOL |
| STRING TABLE row | `length` | u32 | LE | — | byte length |
| GROUP TABLE row | `name_string_id` | u32 | LE | — | |
| GROUP TABLE row | `parent_path_id` | u32 | LE | `0xFFFFFFFF` = parentless | |
| GROUP TABLE row | `declare_order` | u32 | LE | — | |
| GROUP TABLE row | `sibling_rank` | u32 | LE | — | |
| GROUP TABLE row | `child_count` | u32 | LE | — | |
| GROUP TABLE row | `child_index_start` | u32 | LE | — | |
| GROUP TABLE row | `metadata_start` | u32 | LE | — | |
| GROUP TABLE row | `metadata_count` | u32 | LE | — | |
| GROUP TABLE row | `occ_by_group_start` | u32 | LE | — | |
| GROUP TABLE row | `occ_by_group_count` | u32 | LE | — | |
| CHILD-ID INDEX row | `child_path_id` | u32 | LE | — | |
| METADATA TABLE row | `path_id` | u32 | LE | — | |
| METADATA TABLE row | `key_string_id` | u32 | LE | — | |
| METADATA TABLE row | `value_string_id` | u32 | LE | — | |
| METADATA TABLE row | `source_order` | u32 | LE | — | |
| OCCURRENCE TABLE row | `literal_string_id` | u32 | LE | — | |
| OCCURRENCE TABLE row | `path_id` | u32 | LE | — | |
| OCCURRENCE TABLE row | `local_rank` | u32 | LE | — | |
| OCCURRENCE TABLE row | `fold_id` | u32 | LE | — | |
| OCCURRENCE-BY-GROUP INDEX row | `global_rank` | u32 | LE | — | |
| FOLD TABLE row | `fold_key_string_id` | u32 | LE | — | |
| FOLD TABLE row | `occ_index_start` | u32 | LE | — | |
| FOLD TABLE row | `occ_index_count` | u32 | LE | — | |
| OCCURRENCE-BY-FOLD INDEX row | `global_rank` | u32 | LE | — | |

No section uses a narrower field for anything countable — the former u16 overflow class (B1) does not
exist in this table.

---

## 18. Resource Limits

Unchanged in spirit from B1.1 §15, restated with clarified purpose (Part 22): these limits **prevent
knowingly unsafe work from being attempted at all**; they do **not** guarantee that an in-limit
allocation will succeed (a `MemoryError`, OS allocation failure, I/O failure, or `struct` packing failure
remains possible even for a fully in-limit value, and must still surface as an explicit compilation or
open-time failure, never a silent partial result).

| Resource | Limit |
|---|---|
| Source byte size | 512 MiB |
| Sidecar byte size | 512 MiB |
| Group count | 2^24 |
| Occurrence count | 2^28 |
| Fold count | 2^28 |
| Distinct pool strings | 2^28 |
| Total string-pool byte size | 512 MiB |
| Single string byte length | 1 MiB |
| Metadata rows per group | 2^16 |
| Reader query byte length | 4,096 bytes |

**Ordering requirement, stated explicitly per Part 22:** the reader validates a declared count/length
against both its field-width ceiling *and* this resource limit **before** allocating any buffer sized
from that value — a corrupted file claiming an enormous (but field-representable) count must be rejected
at the bounds-check step, never allowed to reach an allocation call first.

---

## 19. Embedded Integrity Digest

Unchanged from B1.1 §16: one SHA-256 over the entire published file, computed with
`embedded_integrity_digest`'s own 32 bytes locally zeroed during calculation, covering header, versions,
directory, and every section including padding. Recomputed and compared at every `open_generation` call.

The **ordinary full-file SHA-256** (nothing zeroed) remains a *separate*, externally-used-only value
(filename §32, manifest §33) — never stored inside the file, never conflated with the embedded digest.

Neither digest proves semantic completeness — that is Gate 1's job (§37–41), stated as an explicit
non-claim.

---

## 20. Complete Structural Validation (Correction A — No Sampling)

**Every check below is total over its stated domain. No check in this section may be implemented as a
sample, a bounded subset, or "where affordable." A successful `open_generation()` means every one of the
following was checked for every row/reference in scope — not a representative subset.** Checks remain
chunked/sequential (bounded-size reads per pass, not necessarily one giant in-memory decode), per §23's
memory posture — "not sampled" and "not one giant resident object graph" are independent properties, and
this section requires the former, not the latter.

**A. Header / Directory / Protected Regions.**
`magic` exact match. `format_contract_version`/`authority_semantics_version` recognized (else
`AuthorityUnavailable`). `payload_length` == actual file size. Section IDs form the exact expected set
for this format version, each appearing exactly once (no duplicate section IDs). Every section's
`(offset, length)` within `[0, payload_length)`. **No section overlaps another section, the HEADER's own
byte range, or the SECTION DIRECTORY's own byte range** (§7's protected-region correction) — computed
with overflow-safe end-of-range arithmetic. For every section: `row_count * row_size == length`
(checked, promoted to a wide-enough accumulator). For every section: file-declared `row_size` ==
reader's own normative constant for that section under this `format_contract_version` (§7's
decoding-authority correction) — the reader never decodes using a file-supplied width. `embedded_integrity_digest`
recomputed over the *entire* file and compared.

**B. String Table.** *Every* `(offset, length)` row (not a sample) lies within the STRING POOL section's
byte range. *Every* referenced string's bytes, when read, are verified as strictly valid UTF-8 (no
overlong encodings, no unpaired-surrogate CESU-8, no truncated multi-byte sequences).

**C. Group Table.** Path-identity uniqueness: reconstructing every group's full path (by walking each
row's `parent_path_id` chain) and confirming *no two groups reconstruct to the same full path* — a full
O(n) check with a seen-set of reconstructed paths, not a sample, and not something assumed true merely
because the compiler is trusted (a corrupted file could otherwise present two groups with identical
name+parent). Every `parent_path_id` is `ROOT_SENTINEL` or `< path_id` (anti-cycle). **Exactly one row
has `parent_path_id == ROOT_SENTINEL`** (the single-wrapper compatibility profile, §3, is itself a
structural invariant of any binary this compiler ever produces, and the reader enforces it as such — 0 or
2+ parentless rows in an opened binary is corruption, not merely "an unusual document"). Every non-root
group appears in the CHILD-ID INDEX **exactly once**, under its actual `parent_path_id`'s slice (full
partition check, not bounds-only — see D). `child_index_start + child_count` in bounds; every referenced
child's own `parent_path_id` equals this group's `path_id` (membership agreement); children within one
parent's slice appear in strictly increasing `sibling_rank`, forming a dense `0..child_count-1` run.
`declare_order` values are globally unique across the whole table and, restricted to any one parent's
children, increase monotonically with `sibling_rank` (declaration order and sibling order must agree).

**D. Index Slice Partitioning (Part 2 — strengthened beyond bounds-checking).** For every index that is
supposed to be a complete partition of a domain — CHILD-ID INDEX over "all non-root groups," OCCURRENCE-BY-GROUP
INDEX over "all occurrences," OCCURRENCE-BY-FOLD INDEX over "all occurrences," and METADATA TABLE over
"all metadata entries, grouped by owning group" — the validator confirms, for *every* declared slice: (1)
in bounds; (2) start+count arithmetic does not overflow; (3) **no gaps** — reading every group's/fold's
declared slice in directory order and concatenating them reconstructs the *entire* target array/table
with no index/row left uncovered; (4) **no overlap** — no two slices claim the same array index or table
row; (5) **no duplicate references** within a single slice; (6) **exact ownership agreement** — every
value found inside a slice, when dereferenced, actually belongs (by its own stored `path_id`/`fold_id`)
to the group/fold that claims to own that slice. "The array is *a* permutation of `0..N-1`" is checked
(§20.F/H below) but is explicitly **not treated as sufficient by itself** — the *slices themselves*, taken
together, must expose that same complete permutation exactly once, matching every group's/fold's own
`start/count` claims, which is a strictly stronger, separately-checked property (a permutation could
exist in the raw array while a corrupted slice still claimed the wrong sub-range of it; this check catches
that).

**E. Metadata.** Every group's `metadata_start/count` slice is in-bounds and — per D — forms a complete,
non-overlapping partition of the whole METADATA TABLE by `path_id`. Every `key_string_id`/`value_string_id`
in bounds. `source_order` values within one group's slice form a dense `0..count-1` run.

**F. Occurrences.** Every row's `literal_string_id`/`path_id`/`fold_id` in bounds. **For every single
occurrence row — not a sample — `ascii_fold(literal bytes) == the folded-key bytes of the fold row its
own `fold_id` points to`** (Part 1's explicit exhaustive requirement; O(occurrence_count), one fold
per row, each comparison is a cheap byte-level operation). `local_rank` values, grouped by `path_id` in a
single pass, form a dense `0..count-1` run per group, and each group's count matches its GROUP TABLE
row's `occ_by_group_count`.

**G. Occurrence-by-Group Index.** Per D: complete, gapless, non-overlapping partition of
`0..occurrence_count-1`, verified via a compact bit-array seen-marker (not a Python `set` of boxed
integers, §23). Every slice's members, when dereferenced, have `path_id` equal to the owning group's
`path_id`; within a slice, `local_rank` strictly increases.

**H. Fold Table.** Keys in strict ascending order by raw folded-key bytes (rules out duplicate fold keys
as a side effect). **Every fold row has `occ_index_count >= 1`** (Part 7). `occ_index_start/count` in
bounds within OCCURRENCE-BY-FOLD INDEX. Distinct-destination count is *always* recomputed fresh from the
occurrence range (never cached, §14) — this recomputation *is* how `FoldConflict` vs `Hit` is determined,
for every fold examined, not merely at validation time.

**I. Occurrence-by-Fold Index.** Per D: complete, gapless, non-overlapping partition of
`0..occurrence_count-1`. Every slice's members, when dereferenced, have `fold_id` equal to the owning
fold's row index.

**J. Cardinality cross-check (§16).** Every formula in §16 verified against the file's own directory row
counts.

---

## 21. Source Binding

Unchanged from B1.1 §20: `open_generation_unbound(path_or_bytes)` (diagnostic, not authority-usable) vs.
`open_generation(path_or_bytes, expected_source_sha256)` (raises `SourceMismatchError`, a subclass of
`AuthorityUnavailable`, on any mismatch, before returning a usable handle at all).

---

## 22. Backing Stability (Correction B)

**Normative invariant, stated without weakening:** *every byte used to answer an authority query after
`open_generation()`'s validation must be the exact same byte content that was validated.* Same pathname,
same file size, same mtime, or "the publisher promises not to touch it" are each explicitly **insufficient**
on their own to satisfy this — none of them prevent another process from replacing the underlying bytes
after validation while the path/size/mtime coincidentally look unchanged, or before an OS has flushed a
rename to a state the reader can observe consistently.

**Removed claim (Part 9):** any statement that memory-mapping a file inherently preserves a snapshot of
its contents from mapping time is retracted — this is not a general guarantee on the platforms in scope,
and no such claim survives into this document.

**Candidate labels, used consistently throughout this document (Part 21):**
- **Candidate A — immutable packed byte buffer.**
- **Candidate B — stable bounded file reads.**
- **Candidate C — memory mapping.**

**Candidate A is specified as the only backing built for the first implementation and for Gate 1**
(Part 10): `open_generation()` reads the *entire* sidecar file into one in-memory `bytes`/`bytearray`
buffer, validates that buffer (§20), and every subsequent query is answered by reading from that same
buffer — never touching the filesystem again for the life of the handle. This trivially satisfies the
normative invariant: the buffer *is* the validated bytes, and nothing external can mutate it out from
under a query.

Candidates B and C remain named for Gate 2 comparison (§42) but are explicitly **not built or chosen in
this phase**, and per instruction, **neither may become a production candidate until it independently
establishes the same stability invariant** stated above — for B, this means the publication contract
(§34) itself must be the thing guaranteeing immutability-after-publish (never the read mechanism alone);
for C, this means demonstrating the mapped region cannot silently reflect a post-validation external
modification for the mapping's practical lifetime on the deployment platform, which is a claim requiring
its own evidence, not an assumption (this is exactly the retracted claim above, now correctly framed as
"C would need to prove this, not assume it").

---

## 23. Reader Lifetime / Invalidation (Correction B, continued; corrected in B1.2a)

Unchanged base contract from B1.1 §19 (`AuthorityUnavailable`-family conditions are raised exceptions,
not lookup-result values; use-after-close raises; a view is invalidated when its parent handle closes;
generation ownership is caller-driven, no implicit cross-generation invalidation).

**Corrected (B1.2a): invalidation is not the same fact as resource cleanup.** The prior wording ("`close()`
on an already-invalidated handle remains a no-op") was defective — it conflated *authority being
forbidden* with *owned resources already having been released*, which are two independent facts. An
invalid provider may still be holding its complete packed backing buffer (§22), caches, or other owned
resources; "no-op" incorrectly implied those had already been freed, or that freeing them was no longer
`close()`'s job.

**Explicit state model** (implementation may use simpler internal flags that preserve the same three-way
distinction — these names are not prescribed):

| State | Authority queries | Owned resources |
|---|---|---|
| **VALID** | permitted | held |
| **INVALID** | forbidden | **may or may not yet be released** — invalidation alone does not imply cleanup has happened |
| **CLEANED** (reachable from either VALID, via `close()`, or from INVALID, via `close()` or via the invalidation event itself performing cleanup immediately) | forbidden | released |

**Critical invariant: `INVALID != CLEANED`.** A provider can be `INVALID` for an arbitrary period before
`close()` is ever called on it, and during that period it is expected to still be holding its resources —
`close()` must remain able to do real cleanup work at that point, not discover there is nothing left to do.

**Invalidation behavior** (unchanged triggers from B1.1: a backing integrity failure, internal corruption
inconsistent with what §20 should already have caught, an invalid lazy-evidence access that cannot be
serviced, an impossible structural state reached during a lookup, or a future non-Candidate-A backend's
fatal I/O/backing failure):

- The provider transitions to `INVALID` **immediately**.
- Every subsequent authority call on that handle, and on any view derived from it, raises
  `AuthorityUnavailable` (or the most specific subclass) — including calls that would otherwise have
  succeeded against unrelated, still-intact data. Partial continued service from a known-compromised
  provider is never permitted. `MasterUnknown` is never substituted for this.
- Any outstanding lazy result/evidence object obtained before the failure also fails on next access.
- **Resource cleanup may happen either immediately, as part of the invalidation event itself, or it may
  be deferred until `close()` is subsequently called — both are permitted implementation strategies, and
  the specification's only requirement is that cleanup remains possible, and happens, exactly once,
  whichever path performs it.**

**`close()` contract, stated completely:**

1. `close()` is idempotent — calling it any number of times is always safe.
2. `close()` called while `VALID`: releases owned resources and transitions the provider to `CLEANED`
   (which, from the caller's perspective, also forbids authority access — `CLEANED` is a stricter substate
   reachable through what was previously described as simply "closed").
3. `close()` called while `INVALID` **and resources have not yet been released** (i.e. invalidation did
   not perform immediate cleanup): **still releases every owned resource/cache**, exactly as it would from
   `VALID` — invalidation must never be treated as an excuse to skip this work.
4. `close()` called on a provider already `CLEANED` (whether reached via step 2, via step 3, or because
   invalidation itself performed cleanup immediately): a harmless no-op.
5. `close()` **never** restores validity, never restores a view, never rebinds authority, and never makes
   a previously-invalidated lazy result usable again — cleanup is a one-way transition, not a reset.
6. If a cleanup action itself fails partway (an implementation detail not fully specified here), that
   failure must never be interpreted as, or allowed to produce, a restoration of authority state — a
   partially-failed cleanup leaves the provider exactly as unusable as a fully-cleaned or merely-invalid
   one, never more usable.

**Dependent view/lazy-result contract, restated for clarity:** after parent-provider invalidation *or*
`close()` (in either order — a view does not need to know or care which one happened first), every
dependent bounded view, iterator, lazy-evidence object, or range reader remains permanently unusable. None
of them may retain authority access through a cached reference to the parent, silently reopen backing on
their own, or continue serving data from retained-but-now-stale backing bytes. (Whether a *specific*
result object is later implemented as an already-fully-materialized, non-authoritative copy — which could
legitimately keep returning its own already-known values after invalidation, since it no longer needs the
provider for anything — versus a lazy, provider-backed object that must fail, is an implementation
distinction deferred to actual implementation; §26's materialization posture already anticipates both
kinds existing, and this document does not need to resolve which specific accessor is which kind in
order to state the lifetime contract correctly.)

---

## 24. Lookup Semantics

Unchanged from B1.1 §13/§24: `handle.lookup_fold(query: bytes) -> Hit | FoldConflict | MasterUnknown`.
Steps: fold the query (§4's byte-level algorithm); binary search FOLD TABLE by folded-key bytes (using
the reader's own decode of STRING TABLE/POOL, never a file-supplied width, §7); on a match, recompute the
distinct-destination count from the occurrence range (§14/§20.H — never a cached flag); `destination_count
== 1` → `Hit`; `> 1` → `FoldConflict` (even if the query's exact spelling matches one specific member);
no match → `MasterUnknown`.

---

## 25. Whole-Family Views

Unchanged from B1.1 §22: coverage is by folded identity; `view.add_identity(literal)` covers the
*entire* fold family (every alias, occurrence, destination, and the true conflict state) — never a
partial slice; `add_path_prefix()` remains dropped from the initial API. `view.lookup(query) -> Hit |
FoldConflict | ViewUncovered | MasterUnknown`; `view.query_complete_backing(query)` remains the explicit,
same-binary escape hatch for deciding whether to expand coverage.

---

## 26. Result Materialization

Unchanged posture from B1.1 §23: `Hit`/`FoldConflict` carry range descriptors, not a mandatory
fully-materialized list; lazy iteration accessors exist for callers who want full evidence; a bounded
per-view cache budget is committed in shape, with exact numbers deferred to Gate 2 (§42).

---

## 27. Python-2.7 Runtime Boundary (M10)

Unchanged from B1.1 §25/§38: a `runtime_safe/` package (`format_constants.py`, `integrity.py`,
`reader.py`) imports nothing from `sfm_master_core`, the compiler, or any Python-3-only module — enforced
by package structure and a mechanical import-scan (a Gate 1B check, §39). `runtime_safe/__init__.py`
itself imports only its own submodules.

---

## 28. Determinism

Unchanged canonical-ordering table from B1.1 §26, with one correction flowing from §6: `compiler_build_version`
is no longer an embedded field, so it is trivially excluded from what determines output bytes (it was
never supposed to influence them; removing it from the header removes the *possibility* of accidentally
letting it, rather than merely promising not to). Normative deterministic identity depends on exactly:
**source bytes, `format_contract_version`, `authority_semantics_version`** — nothing else. Recompiling
identical source bytes under identical version constants, on any two supported Python 3 environments,
must produce byte-identical output (a required Gate 1A check, §38).

---

## 29. Generic Compiler Contract

Unchanged from B1.1 §27, with §3's new structural-eligibility gate added as an explicit early step:
validate source with `sfm_master_core` → refuse on `not result.ok` → refuse on `len(wrapper_paths) != 1`
(§3) → compile deterministically → self-validate with the `runtime_safe` reader → full semantic parity
against the `MasterParseResult` the writer was given → publish (§34).

---

## 30. Official Validator vs. Generic Compilability

Unchanged from B1.1 §28: the generic compiler compiles anything `sfm_master_core` reports as
representable *and* structurally eligible per §3 (including duplicate occurrences and fold conflicts);
`tools/validate_master.py`'s stricter policy remains a separate, additional, official-release-only gate.

---

## 31. Public CLI

Unchanged from B1.1 §17/§27 in shape (illustrative, not frozen): `sfm-master-compiler <master.txt>
[--output DIR]`. Same exit-code philosophy (0 success, 1 source/eligibility rejected, 2 I/O/internal, 3
self-check failure). CLI output is now also where `compiler_build_version`/provenance is surfaced,
per §6's header correction.

---

## 32. Generation Identity

Unchanged from B1.1 §29: `sfm_master_<format_contract_version>_<full-64-hex-sidecar-sha256>.bin`.
Filename is never validation authority. Identical-content-under-existing-name is a safe no-op;
different-content-under-the-same-computed-name is a hard publication failure, never an overwrite.

---

## 33. Manifest

Unchanged contract from B1.1 §30 (size cap, required keys, no duplicate JSON keys, bare-filename-only
`generation_basename`, invalid-JSON-is-treated-as-no-manifest, unsupported-version handled identically
to any other version mismatch), with `compiler_build_version` added as an explicit, optional,
diagnostic-only manifest field (since it no longer lives in the binary itself, §6):

```json
{
  "generation_basename": "sfm_master_<fmt>_<64-hex>.bin",
  "sidecar_sha256": "<64-hex>",
  "source_sha256": "<64-hex>",
  "source_byte_length": 3975311,
  "format_contract_version": 0,
  "authority_semantics_version": 0,
  "compiler_build_version": "0.1.0-experimental",
  "counts": { "groups": 43, "occurrences": 128555, "folds": 124728 }
}
```

`counts` and `compiler_build_version` remain diagnostic only, never re-derived as validation authority.

---

## 34. Publication Transaction

Unchanged 18-step sequence from B1.1 §31, with the same explicit non-claim about external-editor
atomicity retained verbatim: the manifest asserts *"this sidecar is the last successfully published
compilation of source SHA X, as of this publish transaction"* — current eligibility is always re-verified
by the consumer at use time (§21), never assumed permanently valid from the moment of publication.

---

## 35. Publisher Locking (Part 23)

**Corrected: distinguish an OS-held exclusive lock from a mere lockfile-existence convention.** A bare
"does a file named `*.lock` exist" check is explicitly **insufficient** as the actual mechanism, because
a leftover file from a crashed publisher is indistinguishable from an active lock under that check alone.
The final implementation must use a real OS-level exclusive-lock primitive (e.g., an exclusive-create/lock
call that the OS itself releases if the holding process dies, rather than a plain file whose mere
existence is the entire signal) — the *existence* of a lock file may still be part of the visible
mechanism, but *ownership* must be established through OS-enforced exclusivity, not file presence.

Scope unchanged from B1.1 §32: acquired only around the narrow live-manifest-replacement window (§34
steps 16–18), not the whole transaction.

**Stale-lock/recovery** remains conceptual (no timeout constants frozen here, per instruction), but the
*requirement* is now explicit and testable: **Gate 1B/1C must prove that crash recovery cannot result in
two concurrent publishers successfully replacing the live manifest** (§39/§40's fixture list, §27) — a
real OS-exclusive-lock design satisfies this by construction (the lock is released by the OS when the
crashed process dies, so a second publisher can proceed cleanly, but never *concurrently* with a still-live
first publisher), whereas a bare lockfile-existence convention could not be proven safe under a crash
scenario, which is exactly why it is rejected as the sole mechanism.

---

## 36. Cleanup / Orphan Generations

Unchanged from B1.1 §33: never automatic; optional, separate, conservative maintenance; publication
correctness never depends on it; an orphaned generation after a crash is harmless.

---

## 37. Independent Inventory Oracle (Correction C)

**Corrected scope.** The oracle does **not** require parity of one giant interleaved raw
source-token-position event stream — the binary intentionally does not preserve a single unified
interleaving of "group declarations and control occurrences in exact original token order across the
whole document" (groups are ordered among themselves by `declare_order`; occurrences are ordered among
themselves by global source rank; these are two *separate* monotonic sequences in the compiled format,
not one merged sequence, and `sfm_master_core` itself does not expose a single shared counter across
both either — recording that as a discovered fact, not merely designing around a maybe-existing one).

**Required independent projections instead** — each one is a fact the binary genuinely, normatively
stores, so comparing against it is a real parity claim, not an aspirational one:

**A. Groups.** Declaration order (`declare_order`); exact names; full ancestry (parent chain, in order,
reconstructed the same way the reader itself reconstructs a path); parent/child relationship; sibling
order.

**B. Controls.** Global occurrence order; exact token text (literal); owning destination/group; local
rank; multiplicity (how many times an exact literal occurs, and at which ranks/paths).

**C. Metadata.** Owning group; the *ordered* key/value sequence for that group (source order, duplicates
included); multiplicity per key.

**D. Coverage.** First entry, a sample of middle entries, and the final/tail entry, for both groups and
occurrences, plus a total-count coverage check (every group and every occurrence the oracle's own
tokenization found has a corresponding entry somewhere in the reconstructed projection — an explicit
"nothing the source had is missing from what the binary claims to have" check, at the granularity these
projections actually support).

The oracle independently tokenizes the reference TXT to build these four projections from scratch, and
**separately** reconstructs the same four projections from the *published binary* via `runtime_safe.reader`'s
own structural traversal (never importing `sfm_master_core`). The two sets of projections must match
**exactly**, per-element, not merely in aggregate count — this still catches exactly the case Astra
raised ("one omitted control replaced by a duplicate elsewhere") within projection B, because the omitted
control's exact literal at its specific global rank/owning-group would differ from the oracle's
independently-tokenized expectation, even though a naive total *count* would remain unchanged.

**Source positions are diagnostic only (Part 13):** the oracle may retain line/column/token-offset
information for its own error messages ("mismatch at TXT line 4021, expected literal X, binary claims Y
at global_rank 128"), but this positional data is **not** a required compiled-sidecar fact, and no
section of the binary is enlarged merely to make such positions independently recoverable from the binary
itself unless a genuine future consumer need is proven (none is claimed here).

The oracle remains bound by the same exclusion as before: never a source of truth for taxonomy
classification, fold-conflict policy, reader lookup policy, or metadata interpretation — comparison of
independently-produced structural projections only.

---

## 38. Gate 1A — Semantic Parity

- Full population parity (§20's own exhaustiveness, exercised end-to-end): every occurrence/group/fold/metadata
  fact, `sfm_master_core`'s parse of the reference TXT vs. the `runtime_safe` reader's view of the
  published binary.
- The independent content-parity oracle of §37, run against the same binary.
- The ASCII-fold/UTF-8 byte-equivalence proof of §4, over every pool string plus the non-ASCII/mojibake/non-BMP
  fixtures of §40.
- Deterministic binary equality: compile the same source on at least two distinct Python 3
  minor-version/OS environments available to Gate 1; byte-for-byte diff must be empty.
- Actual Python 2.7 execution of the production reader (not merely "written to be compatible") —
  Gate 1A's parity suite re-run under a real Python 2.7 interpreter.
- A small, hand-authored custom Master (not the official one) run through the identical Gate 1A parity
  suite, proving "same compiler for official and custom" is verified, not merely asserted.

## 39. Gate 1B — Corruption / Integrity

- Every §20.A–J check individually exercised by a targeted corruption fixture (§40's expanded list),
  each asserting `AuthorityUnavailable` at the *specific* check it violates, not merely "some rejection
  happened."
- Checksum-aware doctrine (unchanged from B1.1 §36, restated): every structural-corruption fixture is
  tested in **two** forms — checksum-invalid (old digest left in place, must fail at digest comparison)
  and checksum-valid-but-structurally-invalid (digest correctly recomputed over the mutated bytes, must
  still fail, at the specific structural check the mutation actually violates) — proving the structural
  checks pull real weight independent of the checksum.
- The `runtime_safe/` import-boundary mechanical scan (§27).
- Backing/lifetime fixtures (§41).

## 40. Gate 1C — Publication / CLI

- Full publication transaction (§34) exercised end-to-end, including the source-mutated-during-build
  abort path (step 16) and an interrupted-publication scenario (kill the process between manifest-temp-write
  and the final atomic rename; assert the live manifest still points at the prior generation, untouched).
- Publisher locking (§35) exercised under a simulated crash-while-holding-lock scenario, proving two
  publish attempts cannot both succeed in replacing the live manifest.
- Generation-identity collision handling (§32): identical-content republish is a no-op; a
  fabricated-different-content-under-the-same-computed-name case is a hard failure, never an overwrite.
- CLI exit codes and the generic-vs-official distinction (§30) — a custom Master with duplicates/conflicts
  compiles successfully via the public CLI and is reported factually, without implying rejection.

## 41. Final Gate 1

**All of Gate 1A, 1B, and 1C must pass before Final Gate 1 is declared PASS.** This is a **sequencing
correction** from B1.1, which described publication/locking as an implementation step *after* Gate 1 —
that was inconsistent with Gate 1's own D-layer already requiring publication-failure testing. Corrected
implementation sequence (§45) now builds publication and locking early enough that Gate 1C can actually
run before Final Gate 1 is ever reported.

Final Gate 1 PASS identifies an **experimental format as a release candidate** — not a stable v1 (§44).

Additional Gate 1 fixture list, exhaustively per Parts 26/27/33 (each built as a small custom Master or a
deliberately corrupted binary, never against the official Master, since it cannot exercise most of these
paths):

**Positive fixtures:** duplicate controls within one group; duplicate controls across groups;
same-destination alias families; cross-destination alias families; an exact query landing inside a
still-conflicting family; wrapper-owned controls; wrapper-level metadata; a custom (non-`"groupFile"`)
wrapper name; unknown metadata keys; duplicate metadata entries; an empty-string metadata value;
non-ASCII text; the project's historical mojibake pair (`注視TipsParent` / its corrupted sibling); non-BMP
text (an astral-plane character, exercising 4-byte UTF-8 sequences); escaped-looking backslash sequences
inside a literal (verifying they round-trip with escape spelling intact, per §4); unusual whitespace;
valid EOF final entry; same-line nested/sibling groups; deep nesting (20+ levels); long strings (near the
§18 single-string-length limit); large alias families (hundreds of aliases); counts exceeding the former
B1 u16 ranges (>65,535 children or occurrences for one group/fold).

**Negative source-level fixtures:** duplicate group paths; slash-containing group names; malformed UTF-8
in the raw source bytes; malformed/unterminated quotes; unmatched braces; zero parentless groups (§3);
two-or-more parentless groups (§3); any remaining unconsumed-token case.

**Negative binary-corruption fixtures (checksum-valid AND checksum-invalid forms of each, §39):** wrong
`row_size` for a section; a gap between group child-index slices; an overlap between group child-index
slices; a duplicate occurrence reference in OCCURRENCE-BY-GROUP or OCCURRENCE-BY-FOLD INDEX; a missing
occurrence reference in either index; an occurrence whose index slice claims it but whose own `path_id`
disagrees (wrong owning group); a fold with `occ_index_count == 0`; an occurrence assigned to the wrong
`fold_id`; a fold row whose key is inconsistent with its member occurrences' actual folded literals; a
duplicate fold key; unsorted fold keys; a group with a `child_count` that disagrees with its actual
CHILD-ID INDEX slice; a parentless group incorrectly appearing as someone's child in the CHILD-ID INDEX;
a non-parentless group missing entirely from the CHILD-ID INDEX; a duplicate reconstructed canonical
path across two different `path_id`s; a malformed-UTF-8 string-pool record; a section overlapping the
header or the directory (§7/§20.A).

**Backing/lifetime fixtures (§41 of the task, Part 27):** source-binding mismatch at open; diagnostic
unbound open used where authority is required (must be refused, §21); `close()` called twice; a lookup
attempted after `close()`; a view used after its parent handle is closed; lazy evidence accessed after
provider invalidation (§23); provider invalidation triggered by a simulated fatal backing error, followed
by a confirmation that *every* subsequent call (not just the one that triggered it) now raises; an old
view proven to remain tied to its original generation's data even after a new generation is opened
separately; confirmation that publishing a new manifest does **not** silently retarget an already-open
provider's view of its own (older) generation.

**Required invalidate-close-close lifecycle test (B1.2a, §23):**

```
1. open a valid provider
2. force a fatal invalidation (simulate the corruption/failure condition directly, not via a real
   corrupted file if a direct fault-injection hook is simpler)
3. verify every authority access now raises AuthorityUnavailable
4. call close()
5. verify owned backing/resources were released -- exactly once (whichever lifecycle strategy the
   implementation adopted: if invalidation itself already performed cleanup at step 2, this step
   confirms close() recognizes that and performs no redundant/double release; if cleanup was deferred,
   this step confirms close() is the one that actually performs it)
6. call close() again
7. verify step 6 is a harmless no-op (no error, no double-free, no exception)
8. verify the provider remains unusable (authority access still raises AuthorityUnavailable)
9. verify every dependent lazy result / view obtained before step 2 remains unusable
```

The required conceptual assertion this test proves: **invalidate -> close -> close releases owned
resources exactly once and never restores authority**, regardless of which of the two permitted
strategies (cleanup-at-invalidation vs. cleanup-deferred-to-close) the implementation adopts — the test
is written to verify whichever one is actually true of the code under test, not to presuppose one.

---

## 42. Gate 2 Deferred Measurements

Unchanged list from B1.1 §37: backing-mode choice among Candidates A/B/C (§22); real SFM
input-string-conversion cost/path; actual resident/VAS cost of an open handle and active views;
validation/open latency, measured; generation-overlap cost during hot-swap; view retention/cache cost
against §26's eventual concrete budget numbers; `close()` behavior under real SFM process-lifetime
patterns; largest-free-region/VAS-fragmentation effects specifically. Only Candidate A is built for Gate
1/first measurement; B and C are revisited only if Gate 2 measurement of A shows a concrete problem, and
only after each independently proves the §22 stability invariant for its own mechanism.

---

## 43. Normalizer Adapter Boundary

Unchanged separation from B1.1 §38: everything in §24–26 (lookup, views, materialization posture), the
full integrity/lifetime contract (§20, §23), and the binary format itself (§5–§19) are finalizable now,
independent of the Normalizer contract. Kept provisional: exact result-object shapes; eager/lazy
materialization defaults for real usage patterns; view-API ergonomics; the SFM-boundary string-conversion
mechanism (§4); any relative/wrapper-stripped path presentation (§9); cache-tuning beyond §26's bounded-budget
posture. Gate 1 (§38–41) does not block on any provisional item.

---

## 44. Format Freeze Policy

Unchanged milestone sequence from B1.1 §39, with Gate 1's internal structure now reflecting §38–41:

```
EXPERIMENTAL format_contract_version (e.g. 0)
    -> Gate 1A + Gate 1B + Gate 1C all PASS -> FINAL GATE 1 PASS (sec 41)
        -> identified as a RELEASE CANDIDATE format
            -> Gate 2 measurement in embedded x86 SFM (sec 42)
                + a narrow, real consumer-contract check against the actual Normalizer
                    -> THEN, and only then: format_contract_version 1 declared STABLE
```

No public v1 compatibility promise before that final step. A release-candidate format may still change
if Gate 2 or the real Normalizer check surfaces a genuine problem.

---

## 45. Exact Implementation Sequence (Correction E)

**Resequenced so publication and locking are built and proven before Final Gate 1 is ever declared,**
correcting B1.1's inconsistency (which described official-workflow-adjacent publication work as
happening "after Gate 1 passes" while Gate 1's own scope already required publication-failure testing):

1. `runtime_safe/format_constants.py` — the byte format as code (§17's tables), isolated, no
   writer/reader logic yet.
2. `sfm_master_compiler/writer.py` — against small, hand-built in-memory `MasterParseResult` fixtures,
   including §3's structural-eligibility gate, covering §41's positive fixture categories one at a time.
3. `runtime_safe/reader.py` + `runtime_safe/integrity.py` — full §20 A–J validation, round-tripped
   against the same fixtures, under **both** Python 3 and a real Python 2.7 interpreter, before touching
   the real Master.
4. §41's negative/corruption fixtures, including the checksum-aware doctrine (§39) — **Gate 1B**.
5. The independent content-parity oracle (§37), built and proven against the small fixtures first.
6. **Publication transaction (§34) and publisher locking (§35)**, implemented and proven against the
   small fixtures — moved earlier than B1.1's sequence specifically so Gate 1C (§40) can actually run.
7. The compiler CLI (§31) and the full official-Master compile-and-self-validate path.
8. **Gate 1A** (§38) — full semantic parity, determinism, real Python 2.7 execution — against the real
   canonical Master.
9. **Gate 1C** (§40) — the full publication/locking/CLI suite — now exercised against the real official
   Master's compiled output, not only the small fixtures from step 6.
10. **Final Gate 1** (§41) declared only once 4/5/8/9 (Gate 1A+1B+1C) all pass together.
11. Official build workflow wiring — last, only after Final Gate 1 passes.

---

## Safety Confirmation

- `sfm_defaultanimationgroups.txt`: unchanged, SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- HEAD: unchanged, `8b4f0cb54750a5360a9897bb981af5463ab28681`
- `tools/validate_master.py`: PASS; tests: 52 passed, 0 failed (both reconfirmed fresh before writing
  this document, and again after all edits in this pass — no production code was touched)
- Nothing staged, nothing committed
- No binary format, compiler, reader, manifest, lock, or inventory-oracle implementation begun
- No agents or subagents used
