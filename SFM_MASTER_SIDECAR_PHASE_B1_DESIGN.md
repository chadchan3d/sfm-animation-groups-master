# SFM Master Sidecar — Phase B1 Design (Design Only, Not Implemented)

Design only. No production code changed. `sfm_defaultanimationgroups.txt` unchanged. Nothing staged, nothing committed.

Grounding data (measured against the current canonical Master via `tools/sfm_master_core.py`, not assumed):

| Quantity | Value |
|---|---|
| Groups | 43 |
| Occurrences | 128,555 |
| Distinct exact literals | 128,555 (0 duplicates today) |
| Fold families | 124,728 |
| Metadata rows (groupColor+selectable+visible) | 54 |
| Distinct pool strings (literals + group names + metadata keys/values + fold keys) | 221,565 |
| String-pool payload (UTF-8, no separators) | ~3.15 MB |
| Average string length | ~14.2 bytes |

These numbers ground field-width and size decisions below; **none of them are baked into the format as constants** — every count is a runtime header/footer value, not a compile-time limit.

---

## 1. Executive Architecture

```
sfm_defaultanimationgroups.txt (or any compatible custom Master)
        |  read-only
        v
tools/sfm_master_core.parse_master_bytes()   <-- SOLE semantic authority (Phase B0)
        |  MasterParseResult (groups, occurrences, fold families, metadata)
        v
tools/sfm_master_compiler/                    <-- NEW, Phase B implementation (not yet built)
        |  deterministic serialization, no re-tokenizing, no re-folding, no re-hierarchy-inference
        v
packed binary sidecar (one immutable file per (source SHA, format version))
        |
        +--> generic reader/provider (Python 2.7-compatible subset, also runnable under
        |    the modern-Python compiler process for self-validation -- ONE reader
        |    implementation, two interpreters)
        |
        +--> Normalizer-specific provider adapter (NOT designed here -- seam only, Part 25)
```

The TXT remains the sole authored authority. The compiler is a pure function of (source bytes, fixed version constants) → binary bytes. The reader never reparses the TXT and never falls back to it. A complete-backing miss is a `MASTER_UNKNOWN` fact about this exact Master generation, never an artifact of partial compilation.

---

## 2. Input Semantic Contract

The compiler's **only** input is the return value of `sfm_master_core.parse_master_bytes(data, source_name)` plus `sfm_master_core.build_fold_families(result.occurrences)`. It never re-reads or re-tokenizes the TXT itself.

| B0 structure | Field(s) | Becomes |
|---|---|---|
| `MasterParseResult.source_sha256` | str (hex) | HEADER.source_sha256 (raw 32 bytes) |
| `MasterParseResult.groups` / `.groups_by_path` | `Group` list | GROUP/PATH TABLE rows |
| `Group.full_path`, `.parent_path` | str | resolved to integer `path_id`/`parent_path_id` at compile time (never stored as duplicated full-path strings — see §5) |
| `Group.name` | str | STRING POOL entry, referenced by `name_string_id` |
| `Group.sibling_rank`, `.child_paths` | int / list[str] | GROUP TABLE `sibling_rank`; child enumeration via the CHILD INDEX section (§5) |
| `Group.metadata` (`GroupMetadata.entries`) | list[`MetadataEntry`] | METADATA TABLE rows, presence = non-empty slice (§9) |
| `Group.local_occurrence_global_ranks` | list[int] | OCCURRENCE-BY-GROUP INDEX (§7) |
| `MasterParseResult.occurrences` | `Occurrence` list | OCCURRENCE TABLE, stored **in global-rank order so row index == global_rank** (§7) |
| `Occurrence.literal`, `.full_path`, `.local_rank` | str / str / int | `literal_string_id`, `path_id`, `local_rank` fields per row |
| `build_fold_families(...)` result | `dict[fold_key -> FoldFamily]` | FOLD LOOKUP INDEX, sorted by folded-key bytes (§8) |
| `FoldFamily.exact_spellings`, `.destinations`, `.is_conflict` | set / set / bool | derivable from the fold's occurrence-range in the OCCURRENCE TABLE; `is_conflict` is also cached directly in the FOLD TABLE row for O(1) reader access, cross-checked at compile time |
| `MasterParseResult.ok` | bool | compiler refuses to compile if `False` (see §6 — never ship a partial graph) |

No B0 field is discarded silently. Anything not explicitly placed into a section below (e.g. `name_line`/`open_line`/`close_line` diagnostic line numbers) is intentionally omitted from the binary as non-essential to runtime lookup — flagged in §26 as an open question (should diagnostic line numbers be preserved for a future "explain this answer" reader feature?).

---

## 3. Binary Format Overview

Format family: **small versioned binary, explicit fixed-width fields, little-endian, shared string pool, sorted integer-keyed index, no compression by default, no pickle/marshal/JSON/SQLite.**

Sections, in file order:

```
[ HEADER ]                          fixed size, magic + versions + section directory pointer
[ SECTION DIRECTORY ]                fixed-width array: (section_id, offset, length, row_count)
[ STRING POOL ]                      raw UTF-8 bytes blob
[ STRING TABLE ]                     (offset:u32, length:u32) per string, indexed by string_id
[ GROUP/PATH TABLE ]                 one row per group (§5)
[ CHILD INDEX ]                      (parent_path_id, child_path_id) sorted, for O(log n) child-range lookup (§5)
[ METADATA TABLE ]                   one row per metadata entry, preserving duplicates (§9)
[ OCCURRENCE TABLE ]                 one row per occurrence, in source/global order (§7)
[ OCCURRENCE-BY-GROUP INDEX ]        permutation of occurrence row indices, grouped by path_id (§7)
[ FOLD TABLE ]                       one row per fold family, sorted by folded-key bytes (§8)
[ OCCURRENCES-BY-FOLD INDEX ]        permutation of occurrence row indices, grouped by fold_id (§8)
[ INVENTORY FOOTER ]                 redundant, independently-computed summary counts + checksum (§10)
```

Every section is described by an explicit `(offset, length, row_count)` entry in the SECTION DIRECTORY, itself at a fixed, header-declared offset. Nothing is located by scanning or by "read until you hit the next known marker" — every boundary is an explicit integer, checked at open time (§11).

Rejected alternatives and why: `pickle`/`marshal` (interpreter-version-coupled, unsafe to load untrusted/mismatched-version data, not naturally cross-Python-version); JSON (no fixed-width random access, large parse cost, no native binary string handling); SQLite (real dependency weight and a much larger surface area than a 128k-row flat lookup table needs — revisit only if a concrete future need for ad hoc queries emerges, none identified here); compression by default (defeats direct seek/struct access without adding decompression state; the format is already compact — §3's grounding numbers put the whole payload in the single-digit megabytes).

---

## 4. Header

| Field | Type | Width | Reason | Validation rule |
|---|---|---|---|---|
| `magic` | bytes | 8 | Fast reject of non-sidecar files | must equal a fixed literal, e.g. `b"SFMMSTR\0"` |
| `format_version` | u16 | 2 | Byte-layout schema version (§12) | reader must recognize exactly; mismatch → `AUTHORITY_UNAVAILABLE` |
| `parser_semantic_version` | u16 | 2 | Which `sfm_master_core` grammar semantics produced this data (§12) | reader must recognize |
| `ascii_fold_version` | u16 | 2 | Which fold algorithm was used to build the FOLD TABLE (§12) | reader must recognize |
| `compiler_semantic_version` | u16 | 2 | Which table-construction rules were used (ordering, ID-assignment) (§12) | reader must recognize |
| `source_sha256` | bytes | 32 | Exact source-byte identity | reader compares against caller-supplied expected SHA when one is available |
| `source_byte_length` | u64 | 8 | Sanity cross-check against source_sha256 | must be > 0 |
| `payload_length` | u64 | 8 | Total file length this header describes | must equal actual file size |
| `section_directory_offset` | u64 | 8 | Where the SECTION DIRECTORY begins | must be within file bounds |
| `section_count` | u16 | 2 | Number of directory entries | must match the fixed known section list for `format_version` |
| `total_group_count` | u32 | 4 | Redundant with GROUP TABLE row_count (self-consistency check) | must equal directory's GROUP TABLE row_count |
| `total_occurrence_count` | u32 | 4 | Redundant with OCCURRENCE TABLE row_count | must equal directory's row_count |
| `total_fold_count` | u32 | 4 | Redundant with FOLD TABLE row_count | must equal directory's row_count |
| `total_string_count` | u32 | 4 | Redundant with STRING TABLE row_count | must equal directory's row_count |
| `header_checksum` | u32 | 4 | CRC32 of all preceding header bytes | must match on open |
| `payload_checksum` | bytes | 32 | SHA-256 of the entire file **excluding this field's own bytes** (or of everything after the header — see note) | must match on open; catches any post-compile corruption/truncation the section-bounds checks alone might not (e.g. bit flips inside a section) |

No field encodes today's specific counts (128,555 / 43 / 124,728) as a compile-time constant — they are always read from the header/directory at runtime, for the current file, whatever it is.

Note on `payload_checksum`: it is computed over the file with the checksum field itself zeroed out during hashing, then written in afterward — a standard self-referential-checksum pattern. The reader re-zeros the same field on its local copy of the header bytes before recomputing, matching the compiler exactly.

---

## 5. String Pool

Two-part design:
- **STRING POOL**: one contiguous UTF-8 byte blob, no separators, no null-termination (lengths are explicit).
- **STRING TABLE**: `(offset: u32, length: u32)` per `string_id`, in ascending `string_id` order, so `string_id` is simply an index into this fixed-width array — O(1) dereference.

What is pooled, each exactly once (deduplicated by exact byte-for-byte string, never by fold): control literals, group names, metadata keys, metadata values, and folded keys. All five categories share **one pool and one ID space** — a `string_id` is just a `string_id`; callers only assign it meaning via which table references it (`literal_string_id`, `name_string_id`, `key_string_id`, `value_string_id`, `fold_key_string_id`). This is the simplest design that still fully deduplicates (e.g., a metadata value that happens to equal an existing literal string is stored once).

Encoding: UTF-8, explicitly. No normalization of any kind — capitalization, punctuation, whitespace (including the deliberately-preserved double-space and non-ASCII/mojibake cases already exercised by this project's own history) all pass through as the exact original bytes. The compiler takes B0's already-exact Python `str` values, encodes them once, and stores the resulting bytes verbatim.

**Python 2.7 comparison safety.** The FOLD TABLE is sorted by, and searched using, the **raw UTF-8 bytes of the folded key**, compared with plain byte-string `<`/`==`/`>` — never `unicode()`, never `str.lower()`, never any locale-aware collation. In Python 2.7, `str` already *is* a byte string, so this is not a special case to work around — it is the natural, zero-conversion representation. The reader's own fold function (needed to fold an incoming query literal before searching) is the exact same "shift A–Z by 32, leave everything else alone" byte-level operation as `sfm_master_core.ascii_fold`, trivially portable to Python 2.7 as a loop over `ord()`/`chr()` on a byte string — no dependency on Python 2's `unicode` type, no `sys.setdefaultencoding` workarounds, no codec guessing. This directly satisfies Part 4's requirement and is the reason the format deliberately does not store or compare `unicode` objects anywhere.

`total_string_count` = 221,565 today (measured); pool payload ≈ 3.15 MB today. `u32` offsets support pools up to 4 GiB, vastly beyond any plausible Master size.

---

## 6. Group/Path Table

One row per group **excluding** the implicit outermost wrapper (conventionally `groupFile`) — the wrapper carries no taxonomy meaning (Phase B0 §9 established `root_paths` already means "children of the wrapper," not the wrapper itself), so the compiled format omits it entirely and root groups' `parent_path_id` uses a reserved sentinel (`0xFFFFFFFF`, "no parent").

Row fields:

| Field | Type | Notes |
|---|---|---|
| `path_id` | u32 (implicit = row index) | Assigned by a fixed deterministic pre-order traversal (§21) — **not** by the pre-B0 close-order bug B0 already fixed at the `sfm_master_core` level; the compiler simply serializes the order B0 already produces |
| `name_string_id` | u32 | into STRING TABLE |
| `parent_path_id` | u32 | `0xFFFFFFFF` for a root group; otherwise **must be `< path_id`** (anti-cycle invariant, checked at open, §11) |
| `sibling_rank` | u16 | 0-based, among children of the same parent, matching `Group.sibling_rank` |
| `child_count` | u16 | number of direct children; their IDs are looked up via the CHILD INDEX (below), not stored inline (avoids a variable-length row) |
| `metadata_row_start` | u32 | first row index into METADATA TABLE for this group |
| `metadata_row_count` | u16 | 0 means **no metadata of any kind was ever present** — the only representation of absence (§9) |
| `local_occ_index_start` | u32 | first index into OCCURRENCE-BY-GROUP INDEX for this group's direct-member occurrences |
| `local_occ_index_count` | u32 | count of direct-member occurrences (this group's `Occurrence.local_rank` values run `0..count-1` in the same order as this slice) |

Full path strings are **not stored**. A full path is reconstructed on demand by walking `parent_path_id` back to the sentinel and joining `name_string_id` strings with `/` — bounded by the Master's actual nesting depth (currently at most a handful of levels), so this is a cheap, allocation-light operation, and it avoids storing ~43 largely-redundant path strings that are trivially derivable. (This is a deliberate space/complexity tradeoff, not a hard requirement — see §26 if a future reader profile shows path reconstruction is a hot path worth caching.)

**CHILD INDEX** section: rows of `(parent_path_id: u32, child_path_id: u32)`, sorted by `(parent_path_id, sibling_rank)`. A group's children are found by binary-searching for the first row with this group's `path_id` as `parent_path_id`, then reading `child_count` consecutive rows — giving exact declaration-order child enumeration without embedding a variable-length list in the fixed-width GROUP TABLE row.

---

## 7. Occurrence Table

One row per occurrence, **stored in global source order, so the row index IS the `global_rank`** — this single design choice removes the need to store `global_rank` as its own field, saving 4 bytes/row (~500 KB today) at zero semantic cost, since the table's own physical order carries that fact.

| Field | Type | Notes |
|---|---|---|
| `literal_string_id` | u32 | into STRING TABLE — the exact literal, unmodified |
| `path_id` | u32 | into GROUP/PATH TABLE — the occurrence's canonical destination |
| `local_rank` | u32 | 0-based rank among occurrences sharing this `path_id`, matching `Occurrence.local_rank` (not derivable from row index alone, since a group's occurrences are not necessarily contiguous in global order — a nested child group's controls can be interleaved between a parent's direct-member controls in file order) |
| `fold_id` | u32 | into FOLD TABLE — precomputed at compile time so a reader never needs to re-fold a stored literal to find its family |

Duplicate exact literals (0 today, but the format must not assume this holds forever, per instruction) are represented as **two full rows** with the same `literal_string_id` but distinct `global_rank` (row index) and, if in the same group, distinct `local_rank` — nothing is collapsed or merged. Aliases (different exact spellings, same fold) are likewise always distinct rows; the FOLD TABLE's occurrence range simply contains more than one distinct `literal_string_id`.

**OCCURRENCE-BY-GROUP INDEX**: a `u32` array, length = total occurrence count, holding `global_rank` values **permuted into (path_id, local_rank) order**. This is the section a GROUP TABLE row's `local_occ_index_start/count` slices into — giving O(1) "all direct-member occurrences of group X, in local order" without disturbing the main OCCURRENCE TABLE's global-order invariant.

---

## 8. Fold Lookup Index

**FOLD TABLE**: one row per distinct fold key, **sorted by the folded key's raw UTF-8 bytes** (ordinary byte comparison — no locale, no Unicode collation, deterministic and reproducible on any platform/Python version).

| Field | Type | Notes |
|---|---|---|
| `fold_key_string_id` | u32 | into STRING TABLE |
| `destination_count` | u16 | distinct `path_id` values among this fold's occurrences; precomputed, cross-checked at compile time against a fresh scan of the occurrence range |
| `conflict_flag` | u8 | `1` iff `destination_count > 1` — precomputed, but **the reader must still treat `destination_count > 1` as authoritative even if this flag were somehow wrong**, i.e. the flag is a fast-path, not the sole source of truth (defense in depth; Gate 1 also independently re-derives it, §22) |
| `occ_index_start` | u32 | first index into OCCURRENCES-BY-FOLD INDEX for this fold |
| `occ_index_count` | u32 | count of occurrences sharing this fold |

Exact aliases and destinations are **not stored redundantly** in the FOLD TABLE row itself — they are derived on demand by walking the fold's occurrence range (via OCCURRENCES-BY-FOLD INDEX → OCCURRENCE TABLE rows → `literal_string_id`/`path_id`), which is bounded (today's largest observed family has 3 members; even a pathological future family of hundreds is a trivial scan). This keeps the FOLD TABLE row fixed-width and avoids a second copy of alias/destination data that could drift out of sync with the OCCURRENCE TABLE.

**Lookup steps** (binary search over FOLD TABLE by folded-key bytes; each candidate's key bytes are dereferenced via STRING TABLE → STRING POOL during the search):

| Scenario | Result |
|---|---|
| Query's folded key found, `destination_count == 1` | `HIT` — resolve destination path, return whether the query's *exact* spelling appears among the family's occurrences (informational; does not change the `HIT` classification) |
| Query's folded key found, exact spelling differs from all stored spellings but fold matches, `destination_count == 1` | `HIT` (a genuine case-variant alias resolves the same as any other family member) |
| Query's folded key found, `destination_count == 1`, multiple exact spellings (same-destination alias family) | `HIT` |
| Query's folded key found, `destination_count > 1` | `FOLD_CONFLICT` — **even if the query's own exact spelling matches one specific member of the conflicting family**; the reader never lets an exact-string match short-circuit a still-conflicting fold, matching the confirmed existing project doctrine (Phase A §4.8, re-verified against this session's own `animroot`/`AnimRoot` resolution history) |
| Query's folded key not found in FOLD TABLE at all | `MASTER_UNKNOWN` |

---

## 9. Metadata Representation

**METADATA TABLE**: one row per metadata entry, in the exact source order `GroupMetadata.entries` already preserves (including duplicates of the same key within one group — never collapsed).

| Field | Type | Notes |
|---|---|---|
| `path_id` | u32 | which group this entry belongs to |
| `key_string_id` | u32 | e.g. `groupColor` / `selectable` / `visible`, or any other key a custom Master happens to use — **no hardcoded key enum**, the format is key-agnostic |
| `value_string_id` | u32 | the exact value string, unmodified |
| `source_line` | u32 | diagnostic only (from `MetadataEntry.line`); not required for lookup correctness, included because it is nearly free and materially helps debugging a "why does this group have this value" question later |

Table is sorted by `(path_id, source order within that group)`, matching each GROUP TABLE row's `metadata_row_start/count` slice.

Representation choice: **presence via row-count, value via typed string reference, hybrid — not a bitmask.** A bitmask of "known" keys was considered and rejected: it would require a closed, versioned enum of metadata keys, directly contradicting §2's "no hardcoded key enum" requirement for custom-Master compatibility. The chosen design — a variable-length slice per group, keyed generically by string ID — handles an arbitrary future metadata key with zero format change, at the cost of one extra indirection per lookup (`key_string_id` → STRING TABLE) which is cheap relative to a file-backed format.

Absence is **exclusively** represented by `metadata_row_count == 0` for that key — never inferred from a value being `"0"`, `""`, or any other content. Reading "does group G have key K" means: scan the (typically 0–3 row) slice for a matching `key_string_id`; zero matches = absent; one match = present with that value; more than one match = present-but-ambiguous (surfaced to the caller exactly as `GroupMetadata.value()` already does in B0 — returning "ambiguous," never silently picking one).

---

## 10. Completeness / Inventory Data

**INVENTORY FOOTER** (a dedicated section, not merely header fields, so it can be independently re-verified against the section directory without re-trusting the header's own redundant counts):

| Field | Purpose |
|---|---|
| `group_count`, `occurrence_count`, `fold_count`, `string_count` | must equal the corresponding SECTION DIRECTORY row counts (self-consistency; a mismatch here means the compiler itself produced an inconsistent file, or the file was tampered with post-compile) |
| `metadata_row_count`, `child_index_row_count`, `occ_by_group_index_count`, `occ_by_fold_index_count` | same self-consistency purpose for the smaller auxiliary sections |
| `source_byte_length`, `source_sha256` (duplicated from the header) | belt-and-suspenders: computed by an independent code path within the compiler (footer-writer vs. header-writer) so an internal compiler bug that diverges the two is itself detectable at open time |
| `tail_occurrence` (`global_rank`, `literal_string_id`, `path_id` of the very last occurrence) | a concrete, cheap, human-auditable "did the compiler actually reach the end of the source" fact, directly answering Phase A/B0's recurring concern about late/tail entries being silently dropped |

**Explicit non-claim:** none of the above, nor the header's `payload_checksum`, constitutes proof that the binary is a *semantically correct* compilation of the reference TXT. A checksum proves the bytes are internally self-consistent and unmodified since compilation; it says nothing about whether the compiler correctly transcribed every occurrence, path, fold, and metadata fact from the source. That proof is Gate 1's job (§22–24), specifically Layer A (independent inventory, computed straight from the TXT, compared against these footer counts) and Layer B (full semantic parity, comparing every fact, not just counts).

---

## 11. Integrity / Corruption Model

All of the following are checked once, eagerly, at `open_generation()` time, before any lookup is trusted. Any failure → `AUTHORITY_UNAVAILABLE` / `INVALID_BACKING`, **never** `MASTER_UNKNOWN`.

| Check | Rule |
|---|---|
| File length | actual file size == `header.payload_length` |
| Magic / versions | exact match against the reader's supported set (§12) |
| Header checksum | recomputed CRC32 of header bytes matches `header_checksum` |
| Payload checksum | recomputed SHA-256 (with the checksum field zeroed) matches `payload_checksum` |
| Section directory bounds | every `(offset, length)` lies within `[0, payload_length)` |
| Section non-overlap | sections sorted by offset must not overlap; gaps are allowed (e.g. alignment padding) but overlaps are not |
| Row-count consistency | each section's `length` must equal `row_count * fixed_row_size` for fixed-width sections |
| Header/footer/directory count agreement | `header.total_*_count` == footer's counts == directory `row_count`s for the corresponding sections |
| String ID bounds | every `*_string_id` field in every table, scanned once, must be `< total_string_count` |
| String offset/length bounds | every STRING TABLE `(offset, length)` must lie within the STRING POOL section |
| Path ID bounds | every `path_id`/`parent_path_id` reference must be `< total_group_count` or the reserved root sentinel |
| Anti-cycle invariant | `parent_path_id < path_id` for every non-root row (a stricter, cheaper substitute for general cycle detection, sufficient because the compiler always assigns IDs in a parent-before-child traversal — see §21) |
| Rank bounds/uniqueness | `sibling_rank` values within one parent's children must form a dense `0..child_count-1` run with no gaps or repeats; the same rule applies to `local_rank` within one group's occurrences |
| Fold-table sort order | scanned once at open: each row's folded-key bytes must be `>` the previous row's (strict ascending, which also rules out duplicate fold keys as a side effect) |
| Occurrence/fold index bounds | every value in OCCURRENCE-BY-GROUP INDEX / OCCURRENCES-BY-FOLD INDEX must be `< total_occurrence_count`, and each index's rows falling in one group's/fold's slice must, when dereferenced, actually have that `path_id`/`fold_id` (cheap spot-check at open, full check available as an optional deeper-validate mode for Gate 1) |
| Truncation | any attempted read past `payload_length` during any of the above is itself a failure, not a Python exception the caller has to separately guard against — the reader's low-level read wrapper enforces this |

This is an O(n) pass over the file (dominated by the string-ID and rank checks), performed once per `open_generation()` call, not per lookup — cheap relative to the lifetime of an open provider.

---

## 12. Version Contract

Four **distinct-purpose** version domains, each incrementable independently, each causing outright rejection on mismatch (no partial-compatibility logic in B1):

| Version | What it tracks | Changes when | Mismatch behavior |
|---|---|---|---|
| `format_version` | byte layout (section list, row shapes, field widths) | the on-disk structure itself changes | reject — reader literally cannot interpret the bytes |
| `parser_semantic_version` | `sfm_master_core`'s grammar/hierarchy/tokenization semantics | the meaning of "a group," "an occurrence," "a fold" changes (e.g. a future grammar extension) | reject — the compiled facts might mean something different than the reader assumes |
| `ascii_fold_version` | the fold algorithm itself | (not expected to change — ASCII A-Z→a-z is about as stable as an algorithm gets — but versioned anyway because a "policy" this load-bearing deserves an explicit escape hatch rather than an unversioned assumption) | reject |
| `compiler_semantic_version` | table-construction rules not already covered above (ID-assignment traversal order, index-construction algorithm) | the *compiler's* internal construction strategy changes in a way that would produce different bytes for identical semantic input | reject |

**Explicitly rejected as a version domain: a "policy version."** Part 11 asks not to create versions without distinct purpose; a runtime lookup/conflict-resolution *policy* is a Normalizer-adapter concern (§25), not a fact about the generic Master authority itself. The generic binary format and generic reader described in this document carry **no** policy version field, because they implement no policy beyond the fold-conflict/miss semantics already fixed by §8 — those are load-bearing *data* facts (a fold either has one destination or several), not a tunable policy.

**The official Master's current SHA-256 is explicitly not a version.** It is data identity (§4's `source_sha256`), checked per-generation, completely orthogonal to whether a reader can interpret the byte layout at all.

A future compatible custom Master compiles under the *same* four version numbers as the official build, because compiling is a pure function of (bytes, fixed constants) — a custom Master never needs its own version domain.

---

## 13. Generic Reader API

Two layers, deliberately separated (§25 develops this further):

### 13.1 Generation handle (the complete, unbounded authority)

```
handle = open_generation(path_or_bytes)
    -> GenerationHandle                          on success (all §11 checks passed)
    -> raises/returns AUTHORITY_UNAVAILABLE       on any §11 failure, with structured evidence

handle.source_sha256                             -> bytes (32)
handle.matches_source(expected_sha256: bytes)    -> bool   # caller-driven identity check
                                                             # against an independently-known TXT SHA

handle.lookup_fold(query_literal: str)           -> LookupResult
    # LookupResult is one of:
    #   Hit(destination_path, exact_spellings, occurrence_refs)
    #   FoldConflict(candidate_destination_paths, all_occurrence_refs)
    #   MasterUnknown()
    # folding of query_literal happens inside this call, using the SAME
    # byte-level ascii_fold as the compiler (see sec 5).

handle.get_occurrence(global_rank: int)          -> OccurrenceRecord
handle.get_group(full_path: str)                 -> GroupRecord | None
handle.iter_root_paths()                         -> ordered list[str]
handle.iter_children(full_path: str)             -> ordered list[str]

handle.close()
```

### 13.2 Bounded caller view (generic, source-agnostic; NOT the Normalizer adapter itself)

```
view = handle.new_view()

view.add_path_prefix(full_path: str)             # expand coverage: every occurrence whose
                                                    destination is at/under this path
view.add_literal(exact_or_folded: str)           # expand coverage: one specific identity

view.lookup_fold(query_literal: str)             -> ViewLookupResult
    # one of: Hit(...) | FoldConflict(...) | ViewUncovered() | MasterUnknown()
    #   ViewUncovered: the fold exists in the complete backing (or might --
    #     the view doesn't know) but was never added to THIS view's coverage.
    #   MasterUnknown: query_complete_backing() was consulted (or the
    #     implementation can prove absence some other way) and the identity
    #     genuinely does not exist in this generation at all.

view.query_complete_backing(query_literal: str)  -> Hit | FoldConflict | MasterUnknown
    # Explicit escape hatch: ask the complete authority directly, bypassing
    # this view's coverage. This is how a caller decides whether to EXPAND
    # the view. It is emphatically NOT a TXT-parsing fallback -- it is a
    # query against the exact same compiled binary the view itself reads
    # from GenerationHandle.
```

**Invariants preserved throughout (Phase A §12, re-affirmed):**
- A bounded-view miss (`ViewUncovered`) is never reported the same way as a true Master miss (`MasterUnknown`).
- A binary/integrity failure (`AUTHORITY_UNAVAILABLE`, raised at `open_generation`) is never reported the same way as `MasterUnknown`.
- `query_complete_backing()` is a same-binary query, never a request to reparse or fall back to the TXT.

This API is a **design candidate**. Anything about *when* a real caller would call `add_path_prefix`/`add_literal`, or what triggers a `query_complete_backing` call, is a Normalizer-consumption decision this document does not make (§25).

---

## 14. Python-2.7 Implementation Model

Primitives used, deliberately conservative:

- `open(path, "rb")`, `.seek()`, `.read(n)` — no `pathlib`.
- `struct.unpack`/`struct.calcsize` for every fixed-width field, with an explicit `<` (little-endian) format prefix everywhere, so byte order is never platform-dependent.
- Plain byte strings (`str` in Python 2.7) throughout; no `unicode`, no implicit codec-driven comparisons.
- Manual binary search (a small `bisect`-style loop) over the FOLD TABLE, dereferencing candidate keys via STRING TABLE/STRING POOL reads during the search — no reliance on `bisect.bisect` needing a fully-materialized in-memory sequence, though a thin sequence-like wrapper object exposing `__len__`/`__getitem__` over file reads would let `bisect` itself be reused if desired (a Gate-2-level implementation choice, not decided here).
- No `dataclasses` (`namedtuple` or plain tuples/classes with `__slots__` instead — both work identically on 2.7 and 3.x, so the reader module can be a single dual-compatible source file, see next paragraph).
- No modern `typing` runtime usage (comments/docstrings only).

**Resolving the "compiler validates using the production reader" requirement (Part 15/16):** the compiler runs under modern Python 3, but "the production reader" is the artifact that must run under SFM's embedded Python 2.7. Rather than building two readers (which would violate "must not reimplement the reader"), the reader module is written in a **deliberately dual-compatible subset** of Python (struct/bytes/plain-class primitives only, verified to run unmodified under both 2.7 and 3.x). The compiler's own self-validation step imports and runs this **exact same reader module** under whichever Python the compiler itself is running (3.x), and Gate 1 additionally exercises it under a real 2.7 interpreter as part of qualification. One reader source file, two interpreters, zero duplicated logic.

Two candidate backing modes are identified for later Gate 2 measurement, not chosen now:

- **Mode A — bounded ordinary file reads.** One open file handle held for the life of the `GenerationHandle`; every table access is an explicit `seek`+`read` of just the bytes needed. Minimal upfront memory; more syscalls per lookup (bounded — a single fold lookup is one `O(log 124728)` ≈ 17-step binary search, each step a small seek+read, almost certainly satisfied from the OS page/file cache after the first touch).
- **Mode B — memory-mapped file (`mmap`, present in Python 2.7's standard library).** Removes per-step syscall overhead and avoids the reader's own buffering copy, at the cost of holding the whole file mapped into the 32-bit process's virtual address space for the mapping's lifetime — exactly the VAS-fragmentation risk §15 exists to avoid. `mmap` is not rejected outright, but it is **not the default recommendation** here; Gate 2 should measure Mode A first, since it more directly respects the "avoid mapped duplicate held resident" guidance, and only adopt Mode B if Gate 2 measurement shows Mode A's syscall overhead is actually a problem in practice.

---

## 15. Memory / VAS Model

Kept resident for the life of an open `GenerationHandle` (Mode A): the HEADER (fixed, small) and the SECTION DIRECTORY (fixed, small — one entry per section, currently ~9 sections). Nothing else is pre-decoded.

Decoded per operation, then released: a `lookup_fold` call materializes only the handful of FOLD TABLE rows its binary search actually touches (≈17 candidate reads for 124,728 entries) plus, on a hit, the small occurrence-range slice for that one fold (today's largest family has 3 members; even a much larger hypothetical family is still a bounded, small read). A `get_group`/`iter_children` call materializes one GROUP TABLE row and one small CHILD INDEX slice.

A bounded caller view holds only what it was explicitly told to cover: the set of `path_id`s/literal-or-fold keys added via `add_path_prefix`/`add_literal`, plus a small cache of already-answered lookups within that view — never the whole 128,555-occurrence graph, regardless of how large the complete backing is.

Explicitly avoided, matching Phase A/B0's stated hazards: no full raw-TXT parse graph is ever held by the reader (the reader never touches the TXT at all — that is exclusively the offline, Python-3, compiler-side concern); no full decoded-binary object graph is materialized; no duplicate byte-buffer of the whole file is kept alongside a memory-mapped copy (Mode A and Mode B are mutually exclusive per handle, never combined); generation hot-swap (a new sidecar replacing an old one while the process is still running) opens and validates the new `GenerationHandle` fully before closing the old one — a brief, bounded overlap of two small (header+directory-sized) resident footprints, not two full decoded graphs.

Today's measured sizes (§ grounding table) put the *whole file* at roughly single-digit megabytes (string pool ~3.15 MB + occurrence table ~128,555 × 16 bytes ≈ 2 MB + fold table ~124,728 × ~14 bytes ≈ 1.7 MB + indices/metadata/groups, all small) — comfortably under the Gate 2 review ceilings (~16 MiB incremental resident, ~32 MiB incremental peak) **for Mode A's resident footprint specifically** (header+directory only); this is not a Gate 2 proof, only a plausibility estimate from the design's own numbers, exactly as instructed.

---

## 16. Compiler Codebase

```
tools/
    sfm_master_core.py                  # existing, B0 — untouched by B1

    sfm_master_compiler/
        __init__.py
        format.py         # struct layouts, magic, section IDs, all four version
                           #   constants, fixed row sizes -- the single source of
                           #   truth for the byte format, imported by BOTH the
                           #   writer and the reader (so they can never drift apart)
        writer.py          # takes a MasterParseResult + fold families -> bytes;
                           #   pure, deterministic, no file I/O of its own beyond
                           #   accepting an output stream to write into
        reader.py          # the dual-Python-2.7/3.x reader module (sec 14);
                           #   imports ONLY format.py and the standard library
        validation.py      # the section-11 integrity checks + a full self-parity
                           #   pass (compiled reader output vs. the MasterParseResult
                           #   the writer was given) -- used by the CLI's publish step
        cli.py             # sec 17 entry point
```

Boundaries: `sfm_master_core` owns all semantics (what a group/occurrence/fold/metadata *is*). `format.py` owns the byte-level contract (how a semantic fact is laid out on disk) and is the only module allowed to hardcode struct format strings. `writer.py` owns turning B0's semantic objects into bytes per `format.py`'s layout — it never invents a fact `sfm_master_core` didn't already provide. `reader.py` owns turning bytes back into queryable facts per the same `format.py` layout — it never re-derives a fact from raw TXT-like reasoning (it has no TXT-parsing code at all). `validation.py` owns proving the two agree. `cli.py` owns process-level concerns (argument parsing, exit codes, file I/O orchestration, printing) and contains no format or semantic logic of its own.

The compiler **imports** `sfm_master_core`; it never re-tokenizes, re-folds, or re-infers hierarchy — every semantic fact `writer.py` serializes comes directly from a `MasterParseResult`/`FoldFamily` object it was handed.

---

## 17. Public / Advanced-User CLI

```
sfm-master-compiler <master.txt> [--output DIR] [--check-only]
```

(Illustrative shape, not frozen — a subcommand style, e.g. `sfm-master-compiler compile ...` / `sfm-master-compiler check ...`, is an equally reasonable alternative to finalize during implementation.)

Behavior, matching `validate_master.py`'s established exit-code philosophy and extending it rather than inventing an unrelated scheme:

1. Read `<master.txt>` read-only (never opened for writing).
2. `sfm_master_core.parse_master_file(...)`; if `not result.ok`, print the same kind of evidence-rich failure report `validate_master.py` already produces (structural/grammar errors with line/column context) and exit **1** — nothing is compiled.
3. Compute and print `source_sha256`.
4. Compile deterministically (§21) into an in-memory byte buffer (or a temp file for very large sources — implementation detail).
5. Self-validate: run the dual-compatible `reader.py` (§14) against the just-produced bytes, plus `validation.py`'s full-parity pass against the original `MasterParseResult`. Any discrepancy → exit **3** ("compiled but failed self-check"), and nothing is published.
6. Only on full success: atomically publish (§20) into `--output DIR` (default: alongside the source, in a `sidecar/` subdirectory), update the manifest, and print `sidecar_sha256`, all four version numbers, and the summary counts (groups/occurrences/folds/strings).
7. On any I/O error (can't read source, can't write output) → exit **2**, matching `validate_master.py`'s existing "could not be performed reliably" code.
8. Success → exit **0**.

Requirements satisfied: never edits the TXT (opened read-only); validates before compiling; reports useful source errors (reuses the existing evidence style); produces a complete sidecar; validates the sidecar with the actual reader; preserves the previous valid output on any failure (temp-file-then-atomic-publish, §20 — a failure never touches the last-published generation or manifest); deterministic output (§21); prints both SHAs and all version/count information.

**Standalone Windows executable (future, not built now):** package this exact `sfm_master_compiler` codebase (e.g. via PyInstaller) so an advanced modeler with no Python installed can run a `.exe` — the executable wraps the same `cli.py` entry point, it does not reimplement compilation logic. No SFM installation and no embedded-Python dependency are required for this offline step, consistent with §16's boundary (the compiler never needs Python 2.7 compatibility itself — only `reader.py`, imported unchanged, does).

---

## 18. Official Build Workflow

```
edit sfm_defaultanimationgroups.txt (existing CLAUDE.md Preflight/Atomic-Write workflow, unchanged)
    -> python tools/validate_master.py sfm_defaultanimationgroups.txt   (existing Section-25 gate, unchanged)
    -> sfm-master-compiler sfm_defaultanimationgroups.txt --output sidecar/   (THE SAME public CLI -- no private path)
    -> (compiler's own internal reader-validation + parity, sec 17 step 5, already ran)
    -> independent Gate 1 inventory oracle (sec 22) run against the freshly-published generation
    -> git add sfm_defaultanimationgroups.txt sidecar/<generation file> sidecar/manifest.json
    -> git commit
```

There is exactly one compiler codebase; "official" means nothing more than "this CLI, invoked against `sfm_defaultanimationgroups.txt`, with its output committed to this repository." An advanced user runs the identical CLI against their own file and gets a sidecar bound to *their* file's SHA — the reader's source-identity check (§13.1 `matches_source`) is what keeps the two universes from ever being confused, not a difference in compiler behavior.

---

## 19. Generation + Manifest Model

Immutable, content-addressed generation filename, e.g.:

```
sidecar/sfm_master_<source-sha256-first-12-hex>_<format_version>.bin
```

Two different source byte-sets, or two different format versions of the same source, never collide; recompiling the *same* source under the *same* format version is idempotent by construction (§21) — republishing produces byte-identical output, so an atomic-publish step can always safely no-op if the target filename already exists with matching content (worth an explicit existence+hash check before writing, to avoid gratuitous rewrites).

```json
// sidecar/sfm_master_sidecar.manifest.json
{
  "source_sha256": "...",
  "generation_file": "sfm_master_<...>_<...>.bin",
  "sidecar_sha256": "...",
  "format_version": 1,
  "parser_semantic_version": 1,
  "ascii_fold_version": 1,
  "compiler_semantic_version": 1,
  "counts": { "groups": 43, "occurrences": 128555, "folds": 124728, "strings": 221565 },
  "compiled_at": "2026-09-11T00:00:00Z"
}
```

**Is a manifest necessary, or would a simpler model suffice?** Given the filename is already content-addressed, a manifest's only *load-bearing* job is answering "which generation file is currently the published/active one" in one small, fast-to-read place, without hashing the (multi-megabyte) binary just to discover its own identity. That is a real, small need — a bare "just always recompute and glob for the newest file" approach is fragile (ordering by filesystem mtime is not a safe substitute for an explicit pointer) and a full database is overkill. The small manifest is the right-sized answer. `compiled_at` is recorded for human/ops visibility only — §21 explicitly excludes it from anything that determines the *binary's* bytes.

---

## 20. Atomic Publication

```
1.  capture exact source bytes (single read)
2.  source_sha256 = sha256(source bytes)
3.  result = sfm_master_core.parse_master_bytes(source bytes); require result.ok
4.  fold_families = build_fold_families(result.occurrences)
5.  compiled_bytes = writer.compile(result, fold_families, versions)      # pure, in-memory
6.  write compiled_bytes to a TEMP file in the target directory (e.g. ".sfm_master_sidecar.tmp-<pid>-<random>")
7.  flush + fsync the temp file (best-effort on platforms where this is meaningful; Windows equivalent flush)
8.  open the temp file with reader.py; run the full sec-11 integrity checks
9.  run validation.py's full semantic-parity pass (compiled bytes vs. `result`/`fold_families` from step 3-4)
10. if the source was read from a live path (not passed as in-memory bytes), re-read and re-hash it now;
    if it no longer matches source_sha256 from step 2, ABORT without publishing (source mutated during build)
11. os.replace(temp_file, final_generation_filename)          # atomic rename, same filesystem, both platforms
12. write/update the manifest LAST, only after step 11 succeeds, via the same temp-write-then-os.replace pattern
13. on ANY failure at steps 3-11: delete the temp file; the manifest and all previously-published
    generation files are untouched -- the last known-good state remains exactly as it was
```

A changed TXT makes an old generation semantically ineligible (its `source_sha256` will not match) even though the old `.bin` file may still be physically present on disk — eligibility is a property the *reader* checks (`matches_source`) at use time, not something the publication step needs to enforce by deleting old files (indeed, keeping old generations around is harmless and potentially useful for rollback, though a retention/cleanup policy is out of scope for this design).

---

## 21. Determinism

Output bytes are a pure function of exactly: (source bytes, `format_version`, `parser_semantic_version`, `ascii_fold_version`, `compiler_semantic_version`). Nothing else.

Explicitly excluded from influencing output bytes: wall-clock time, filesystem paths, usernames, process IDs, random IDs, hostnames, environment variables, or the order Python happens to iterate a `set`/`dict` (Python 3.7+ dicts are insertion-ordered, but the design does not rely on this incidentally — every ordered structure below is built by iterating an already-explicitly-ordered source, never a `set`).

- **String IDs**: assigned in a single deterministic pass — literals and group names in the order `sfm_master_core` already yields them (occurrence global order for literals; pre-order traversal for group names, see next point), metadata keys/values in METADATA TABLE row order, fold keys in FOLD TABLE's own sorted order. First-seen wins; a string already assigned an ID is never re-added.
- **Path IDs**: assigned by a fixed pre-order traversal starting from each `root_paths` entry in `MasterParseResult.root_paths` order (itself already deterministic — B0 sorts by `open_line`), recursing into `child_paths` in their already-deterministic declaration order.
- **Row ordering**: OCCURRENCE TABLE = global source order (already deterministic in B0). FOLD TABLE = sorted by folded-key raw bytes (a pure, total, deterministic order — Python's default byte-string comparison, not locale-aware). METADATA TABLE = `(path_id, source order within group)`. CHILD INDEX = `(parent_path_id, sibling_rank)`. Both permutation indices (OCCURRENCE-BY-GROUP, OCCURRENCES-BY-FOLD) = stable sorts keyed by `(path_id or fold_id, local_rank or global_rank)` — stable sort preserves the deterministic tie-break already present in the input order.
- **Section ordering**: fixed by `format_version`, never data-dependent.

Recompiling identical source bytes under identical version constants therefore produces byte-identical output — verified as a required Gate 1 check (§22, "compile twice, diff the bytes").

---

## 22. Gate 1 Qualification

Four mandatory proof layers, now made concrete against the actual binary/reader pair:

**A. Independent source inventory.** A structurally separate script (not importing `sfm_master_core` or anything from `sfm_master_compiler`) re-tokenizes the reference TXT from scratch and independently computes: occurrence count, group count, distinct fold-key count, source SHA-256. Compared against both (a) the compiled binary's INVENTORY FOOTER and (b) `sfm_master_core`'s own numbers for the same TXT — a three-way agreement, not a two-way one, so a bug shared between the "shared core" and the "compiler" cannot hide from this layer alone (Layer B below is the deeper check for that).

**B. Full semantic parity.** For **every** occurrence (128,555 today; must scale to whatever a given Master contains, not a fixed number), compare, between (i) `sfm_master_core.parse_master_bytes` on the reference TXT and (ii) `reader.py` reading the published binary: exact literal, destination path, global rank, local rank, fold family membership, and (per fold) exact-alias set, destination set, conflict status. For every group: full path (reconstructed), parent, sibling rank, child order, and every metadata key's presence/value(s). Full population, every single time — not sampled, matching Phase A's original requirement.

**C. Hand-audited adversarial fixtures.** See §24's catalog — each fixture compiled and read back, asserting the exact expected `LookupResult`/`GroupRecord` shape.

**D. Corrupt/incompatible/publication-failure testing.** Every §11 integrity rule exercised by deliberately corrupting a valid compiled binary (flip a byte in an offset field, truncate the file, zero out a section-length field, swap two fold-table rows to break sort order, etc.) and asserting `AUTHORITY_UNAVAILABLE` — never `MASTER_UNKNOWN` — for each. Additionally: wrong `format_version`/`parser_semantic_version`/`ascii_fold_version`/`compiler_semantic_version`; wrong `source_sha256` presented to `matches_source`; a source-mutated-during-build scenario exercised against the §20 publication sequence directly (steps 10's abort path); an interrupted-publication scenario (kill the process between steps 11 and 12, assert the manifest still points at the prior generation).

**Also required, per the public/advanced-user requirement:** compile a small, hand-authored **custom** Master (not the official one, but syntactically compatible) through the identical pipeline, and re-run Layers A and B against it — proving "same compiler for official and custom" is verified, not merely asserted.

**Determinism check:** compile the same source twice (fresh process each time); the two output files must be byte-identical.

---

## 23. Independent Oracle

A new, dedicated script — e.g. `tools/sfm_master_gate1_inventory.py` (not built in this design phase) — structurally isolated from `sfm_master_core` and from `sfm_master_compiler`:

- Its own from-scratch tokenizer/counter, written independently (deliberately not sharing code with `sfm_master_core`, mirroring the pattern `tools/verify_phase2_production_order.py` already establishes for an unrelated domain — reconstruct from first principles, compare against a stored/claimed result).
- Reads the compiled binary's HEADER/SECTION DIRECTORY/INVENTORY FOOTER via **raw `struct.unpack`** only — it does not import or invoke `reader.py`'s higher-level lookup logic, so a bug in `reader.py`'s interpretation of the format cannot hide from this oracle.
- Computes and compares: occurrence count, group count, fold count, string count, source SHA-256 (from the raw TXT bytes, independently) against `source_sha256` in the header.

**It never becomes a second production authority.** It has no opinion on destinations, fold conflict policy, metadata interpretation, or runtime lookup semantics — it only counts, hashes, and compares counts/hashes. This boundary is enforced by construction (the script has no function that resembles a "lookup" or "classify" operation) and stated explicitly in its own module docstring when built, exactly as `tools/verify_phase2_production_order.py` already documents its own scope today.

---

## 24. Adversarial Fixture Catalog

| Fixture | Setup | Expected result |
|---|---|---|
| Exact hit | single-spelling fold, one destination | `Hit`, exact spelling in evidence |
| Case-variant alias hit | query differs in case from the only stored spelling, same fold | `Hit` |
| Same-destination aliases | 3 exact spellings, one fold, one destination | `Hit`, all 3 in `exact_spellings` |
| Cross-destination folded conflict | 2 exact spellings, one fold, two destinations | `FoldConflict`, both destinations listed |
| Exact spelling inside conflicting fold | query's exact spelling matches one member of a still-conflicting fold | `FoldConflict` (not `Hit` — §8) |
| True missing fold | query folds to a key absent from FOLD TABLE | `MasterUnknown` |
| Metadata absent | group with zero metadata rows | `metadata_row_count == 0`; `present(key)` False for any key |
| `selectable "0"` explicit | one metadata row | present, value `"0"` |
| `selectable "1"` explicit | one metadata row | present, value `"1"` |
| `visible "0"` explicit | one metadata row | present, value `"0"` |
| `visible "1"` explicit | one metadata row | present, value `"1"` |
| `groupColor` present | one metadata row, RGBA value | present, exact value string |
| Duplicate metadata (same key twice) | two rows, same `key_string_id` | both preserved in the slice; `value()`-equivalent reports ambiguous, never picks one |
| Duplicate exact occurrences | same literal, same destination, twice | two distinct OCCURRENCE TABLE rows, distinct global/local rank |
| Repeated aliases | same fold, same literal, appearing at two different destinations | `FoldConflict`; occurrence range shows both |
| Unusual punctuation / spaces-in-literal | literal with embedded spaces, slashes, hyphens | byte-exact round-trip through STRING POOL |
| Non-ASCII / mojibake | a literal with non-ASCII bytes (if a real project fixture is available, e.g. the historical kanji/mojibake carry-along pair) | byte-exact round-trip; folding leaves non-ASCII bytes untouched |
| Final entry at EOF | last occurrence in the source, no trailing content after it | present with correct `global_rank == occurrence_count - 1`; INVENTORY FOOTER's `tail_occurrence` matches |
| Malformed quote (source-level, pre-compile) | unterminated quoted string in the TXT | compiler refuses to compile (`parse_master_bytes(...).ok is False`); no binary produced |
| Unmatched brace (source-level) | missing `}` | compiler refuses to compile |
| Structurally truncated group (source-level) | file ends mid-group | compiler refuses to compile |
| Unsupported grammar (source-level) | a `"{"` with no preceding name | compiler refuses to compile |
| Corrupt header | flip a byte in `magic` or a version field | `AUTHORITY_UNAVAILABLE` |
| Truncation | binary file cut short mid-section | `AUTHORITY_UNAVAILABLE` |
| Bad offsets | a section's declared offset points past EOF | `AUTHORITY_UNAVAILABLE` |
| Bad counts | header's `total_occurrence_count` doesn't match the OCCURRENCE TABLE's actual row count | `AUTHORITY_UNAVAILABLE` |
| Bad string ID | an occurrence row's `literal_string_id` >= `total_string_count` | `AUTHORITY_UNAVAILABLE` |
| Wrong versions (each of the four independently) | any one version field altered post-compile | `AUTHORITY_UNAVAILABLE` |
| Wrong source SHA | `matches_source(unexpected_sha)` called against a validly-opened binary | `False` returned (this one is a normal, non-corrupt outcome — the binary is fine, it just isn't a match for the caller's expected source) |
| Payload corruption | flip a data byte deep inside e.g. the FOLD TABLE | `payload_checksum` mismatch → `AUTHORITY_UNAVAILABLE` |

---

## 25. Normalizer Adapter Boundary

**Can be fully finalized now, independent of the Normalizer contract** (everything in §13 — `GenerationHandle` and the generic `View` — depends only on the Master's own static shape):

- `open_generation` / integrity validation / `matches_source`
- `lookup_fold` and its `Hit`/`FoldConflict`/`MasterUnknown` result shape
- `get_occurrence` / `get_group` / hierarchy enumeration
- The generic bounded-`View` primitives (`add_path_prefix`, `add_literal`, `lookup_fold`, `query_complete_backing`) and their `ViewUncovered` state

**Must remain open until the real Normalizer contract is obtained** (Phase A/B0 confirmed it is not present anywhere in this repository, and this document does not invent it):

- The **NORMALIZER-SPECIFIC PROVIDER ADAPTER** — a thin translation layer mapping the Normalizer's actual call signatures, expected result types, and specific rig/model-scoped view-construction triggers onto the generic API above.
- *When* and *why* a caller expands a view (what real-world event corresponds to `add_path_prefix`/`add_literal`) — this is entirely a Normalizer-consumption decision.
- Whether the Normalizer needs any additional static fact this design hasn't captured (unknown until its actual lookup inputs/outputs are reviewed).
- Any "policy" layer above raw fold-conflict/miss semantics (§12 already excludes this from the generic format on purpose, precisely so it can live entirely in this未-designed adapter without requiring a binary-format change later).

This separation means Astra's review of §1–24 does not need to wait on the Normalizer contract at all — only a future, distinctly-scoped adapter design would.

---

## 26. Open Questions

1. Should the reader expose the (currently discarded) `name_line`/`open_line`/`close_line` diagnostic line numbers for a future "explain this answer" feature, at the cost of a wider GROUP TABLE row? (Not needed for §13's lookup API as designed.)
2. Should full-path strings be cached (stored redundantly) for groups, trading STRING POOL space for avoiding repeated parent-chain walks, if a future reader profile shows path reconstruction is a measurable hot path? (§6 currently reconstructs on demand.)
3. Mode A vs. Mode B (§14) is explicitly left to Gate 2 measurement, not decided here.
4. Exact CLI command shape (single command vs. subcommands) is illustrative, not frozen (§17).
5. Retention/cleanup policy for old, no-longer-current generation files (§20) is out of scope for this design — publication safety does not require deleting them, but an unbounded number of orphaned `.bin` files is an eventual disk-hygiene question.
6. Whether `compiler_semantic_version` and `parser_semantic_version` will, in practice, ever need to change independently of each other, or whether experience shows they always move together (in which case a future revision could reasonably merge them) — left as observed-not-decided, since inventing a merge now would be speculative.

## 27. Astra Review Questions

See the companion handoff document, `SFM_MASTER_SIDECAR_B1_ASTRA_REVIEW_HANDOFF.md`, for the 12 questions posed to Astra directly.

## 28. Exact Implementation Phase Proposed After Review

Pending Astra's review and explicit authorization: implement `tools/sfm_master_compiler/format.py` and `writer.py` first (the byte-format itself, in isolation, unit-tested against small in-memory `MasterParseResult` fixtures — no CLI yet); then `reader.py` against those same fixtures (round-trip parity before ever touching the real 128,555-occurrence Master); then `validation.py`'s integrity checks (§11) exercised against deliberately corrupted fixtures (§24's D-category); then `cli.py` and the full official-Master compile-and-self-validate path; then the independent Gate 1 inventory oracle (§23); then the full Gate 1 run (§22) against the real canonical Master before any official generation is ever published or committed.

---

## Safety Confirmation

- `sfm_defaultanimationgroups.txt`: unchanged, SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- HEAD: unchanged, `3487afd5fac95308e1e5f8205593f69e42a34d70`
- No production code changed in this phase (design-only; the grounding numbers in this document's opening table were gathered via read-only calls into the existing, already-committed `tools/sfm_master_core.py`)
- Nothing staged, nothing committed
- No binary format, compiler, reader, or provider implementation begun
- No agents or subagents used
