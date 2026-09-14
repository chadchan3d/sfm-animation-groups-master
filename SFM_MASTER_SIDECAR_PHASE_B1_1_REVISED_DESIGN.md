# SFM Master Sidecar — Phase B1.1 Revised Design (Astra Compliance Pass)

Design revision only. No binary/compiler/reader code written. `sfm_defaultanimationgroups.txt` unchanged.
Nothing staged, nothing committed.

Baseline: HEAD `8b4f0cb54750a5360a9897bb981af5463ab28681`, Master SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`, groups 43, occurrences 128,555, folds 124,728, duplicates 0, ASCII conflicts 0, validator PASS, tests 52 passed (all reconfirmed fresh before writing this document).

This document **supersedes** `SFM_MASTER_SIDECAR_PHASE_B1_DESIGN.md` wherever the two disagree. It does not repeat unchanged rationale at B1's length; where a B1 decision stands unmodified, it is stated concisely with a pointer back to the corresponding B1 section rather than re-derived.

---

## 1. Executive Verdict

**READY FOR ASTRA COMPLIANCE CHECK.** Every MUST item (M1–M10) has a concrete, non-vague resolution below. M1/M2 were already resolved by the B0.1 implementation (committed at `82fba35`) and are treated here as settled facts, not re-opened. M3–M10 are resolved as *design* decisions in this document; their *proof* is Gate 1 (functional correctness) or Gate 2 (performance/memory), never re-opened as unresolved design questions. This is an experimental/release-candidate format design, explicitly not a stable v1 (§39).

---

## 2. Astra Compliance Matrix

| Item | Prior B1 design | B0.1 impact | Revised B1.1 decision | Section | Status |
|---|---|---|---|---|---|
| **M1** wrapper/path identity | Wrapper treated as disposable; `root_paths` conflated with wrapper's own identity | `sfm_master_core` now models the wrapper as an ordinary `Group`, with `wrapper_paths` distinct from `root_paths` | Binary format stores the wrapper as an ordinary GROUP TABLE row (§8); no special-casing | §8 | **RESOLVED BY B0.1** |
| **M2** source completeness / ambiguous group identity | Silent token loss possible; duplicate group paths could silently overwrite | `sfm_master_core` now rejects every unconsumed token, every duplicate group path, and every slash-containing name as an explicit `GrammarError` | Compiler refuses to compile unless `MasterParseResult.ok` | §3 | **RESOLVED BY B0.1** |
| **M3** exact encoding/query contract | Claimed "preserve raw source bytes" (imprecise) | None (B0.1 didn't touch this) | Corrected contract: strict-UTF-8-decoded token *values* are what's stored (UTF-8 re-encoded), not a copy of source bytes; malformed query encoding is an input error, never `MasterUnknown` | §4 | **RESOLVED** |
| **M4** complete integrity/index validation | "Spot-check" language, partial bounds checks | None | Full enumerated A–H validation checklist, every check exhaustive not sampled, chunked/sequential design | §17 | **RESOLVED** (design); execution proof **DEFERRED TO GATE 1** |
| **M5** reader lifetime/failure semantics | `AUTHORITY_UNAVAILABLE` as an ordinary lookup-result variant, ambiguous on exception-vs-value | None | `AuthorityUnavailable`-family conditions are **raised exceptions**, not lookup-result values; explicit close()/use-after-close/view-invalidation contract | §19 | **RESOLVED** |
| **M6** whole-family bounded-view semantics | Coverage by path-prefix; could turn a `FoldConflict` into a local `Hit` | None | Coverage is by folded identity only; adding one literal covers its **entire** fold family (all aliases/destinations/conflict state); `add_path_prefix` dropped from the initial generic API | §22 | **RESOLVED** |
| **M7** field widths/arithmetic/resource limits | Mixed u16/u32, no explicit resource-limit domain separate from field capacity | None | All counts/IDs/ranks default to u32; u64 for file-level offsets/lengths; explicit, generous, compiler-enforced resource limits distinct from raw field capacity; compilation fails explicitly (never truncates) if a value doesn't fit | §15 | **RESOLVED** |
| **M8** generation naming/publication corrections | Filename keyed on source-SHA prefix; publication steps didn't fully address collision/overwrite | None | Filename keyed on the **full ordinary sidecar SHA-256**; identical-content reuse, different-content-under-same-name is a hard failure, never an overwrite | §29, §31 | **RESOLVED** |
| **M9** stronger independent inventory oracle | Count-only comparison (could miss "one control swapped for a duplicate elsewhere") | None | Oracle performs **ordered content parity** (event-by-event: group enter/exit, exact control text, metadata tokens, position, multiplicity, tail), not count parity | §34 | **RESOLVED** (design); tool **DEFERRED TO GATE 1** |
| **M10** runtime integrity dependency boundary | Reader described as "dual-compatible" but package boundary not enforced | None | Explicit `runtime-safe` package that imports *nothing* from `sfm_master_core`/compiler/CLI; enforced by structure, not convention | §25, §38 | **RESOLVED** |

**Adopted SHOULD simplifications** (from the explicit "remove unless a concrete need is proven" instructions):

| Simplification | Adopted? | Section |
|---|---|---|
| Remove INVENTORY FOOTER section | Yes — completeness is proven externally by Gate 1, not claimed internally | §5 |
| Remove per-fold cached `conflict_flag` | Yes — conflict is always the validated distinct-destination count | §13 |
| Remove separate header CRC32 | Yes — replaced by one whole-file self-referential SHA-256 (§16) | §16 |
| Flatten per-group child_start/count into a single CHILD-ID array | Yes | §9 |
| Two version domains instead of four | Yes — FORMAT_CONTRACT_VERSION + AUTHORITY_SEMANTICS_VERSION; compiler build version is provenance-only | §18 |
| Generation filename from full sidecar SHA instead of source-SHA prefix | Yes | §29 |

---

## 3. Qualified Source Semantics (from B0.1, treated as settled)

Per the task's explicit instruction, these are **not re-derived** — they are inputs to this design:

1. The wrapper is a real, ordinary `Group` (not disposable syntax).
2. Canonical paths include the wrapper (`groupFile/Face/Eyes`).
3. `MasterParseResult.wrapper_paths` is distinct from `root_paths`.
4. Every non-comment token is either consumed by supported grammar or produces a `GrammarError`.
5. Duplicate full group paths are rejected (`duplicate_group_path`).
6. Group names containing `/` are rejected (`slash_in_group_name`) — current compatibility profile.
7. Parent relationships derive structurally from parser stack state, never from string-splitting.
8. Group declaration/sibling ordering is `declare_order` (token-encounter based), not line-based.
9. Duplicate CONTROL occurrences remain representable (`result.ok` stays `True`).
10. Cross-destination fold families remain representable (`result.ok` stays `True`).
11. Unknown-but-well-formed metadata remains opaque and preserved, in source order, duplicates intact.
12. Source decoding is strict UTF-8 (`utf-8-sig` if a BOM is present), no normalization, no repair.

The compiler's sole input remains `sfm_master_core.parse_master_bytes(...)` (never a second parse) — compilation is refused outright if `result.ok` is `False`.

---

## 4. String / Encoding Contract

**Corrected claim.** The prior B1 document's "preserve raw source bytes" language was imprecise and is retracted. The actual, qualified pipeline (per B0.1, unchanged by B1.1) is:

```
source bytes --(strict UTF-8 decode, utf-8-sig BOM strip if present)--> Python str token values
    --(no normalization, no repair, no locale conversion)--> exact parsed Unicode token values
```

**Correction (Phase B1.2):** the tokenizer does **not** resolve/unescape backslash sequences. `(?:[^"\\]|\\.)*` exists solely to let the tokenizer find a quoted string's true closing quote without stopping early at an escaped `\"`; the token's captured value retains every backslash character exactly as written in the source (verified directly: source `"He said \"hi\""` parses to the literal Python string `He said \"hi\"`, backslashes and all -- not `He said "hi"`). The compiler performs no additional escaping or unescaping of its own either. So: what the compiler stores is the exact parsed token value returned by `sfm_master_core` -- for every literal observed in the official Master (which uses no backslash sequences), and for a custom Master's literal containing a literal backslash character, the stored bytes are that exact spelling, untouched by any resolution step.

| Concern | Contract |
|---|---|
| Compiler input type | Python 3 `str` (Unicode) — the `Occurrence.literal` / `Group.name` / `MetadataEntry.key`/`.value` / fold-key values already produced by `sfm_master_core` |
| Stored string encoding | Strict UTF-8 encoding (`str.encode("utf-8")`, no `errors=` fallback — a str that came from a successful strict-UTF-8 decode always re-encodes cleanly) of the exact parsed token value |
| Reader query type | UTF-8-encoded byte string (`str` in Python 2.7, `bytes` in Python 3) — **the generic reader never accepts or produces `unicode`/`str`-as-text objects**; converting a caller's native text to UTF-8 bytes is the caller's (eventually, the Normalizer adapter's) responsibility |
| Reader output type | UTF-8-encoded byte string, matching storage exactly — never auto-decoded by the generic reader |
| Malformed query encoding | An **input/authority error** (raised, per §19), e.g. the caller passed bytes that are not valid UTF-8 at all — this is a caller-side programming error, not a fact about the Master, and must never be reported as `MasterUnknown` |
| Python 2 behavior | `str` (byte string) throughout; `ascii_fold` operates by iterating raw bytes with `ord()`/`chr()` — no `unicode()` call anywhere in the reader |
| Python 3 behavior | `bytes` throughout the reader's public surface (the compiler, which runs under Python 3, works with `str` internally via `sfm_master_core` and only encodes to `bytes` at the format/writer boundary) |

The **source SHA-256** remains, unchanged from B1, the identity of the original exact TXT bytes including formatting/BOM/newlines — a fact about the *file*, orthogonal to the string pool, which is a fact about *parsed token values*. The string pool is never described as "a textual copy of the source" anywhere in this design.

---

## 5. Format Overview

Sections, in fixed file order (INVENTORY FOOTER removed per §2's adopted simplification):

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

Same section family as B1 (§3 of the prior document), same rejected alternatives (pickle/marshal/JSON/SQLite/compression-by-default — unchanged reasoning, not repeated here). Completeness is proven externally, by Gate 1 parity/inventory (§34), never claimed via an embedded summary section.

---

## 6. Header + Section Directory

| Field | Type | Notes |
|---|---|---|
| `magic` | 8 bytes | fixed literal, e.g. `b"SFMMSTR\0"` |
| `format_contract_version` | u32 | byte-layout schema (§18) |
| `authority_semantics_version` | u32 | grammar/encoding/hierarchy/fold-rule semantics (§18) |
| `compiler_build_version` | u32 | **provenance only** — never causes reader rejection (§18) |
| `source_sha256` | 32 bytes | identity of the original exact TXT bytes |
| `source_byte_length` | u64 | source file size, for cross-reference with `source_sha256` |
| `payload_length` | u64 | total sidecar file length this header describes |
| `section_directory_offset` | u64 | absolute byte offset of the SECTION DIRECTORY |
| `section_count` | u32 | number of directory entries |
| `embedded_integrity_digest` | 32 bytes | SHA-256 over the **entire file**, with this field's own 32 bytes treated as zero during computation (§16) — the sole embedded checksum; no separate header CRC |

No header field duplicates a SECTION DIRECTORY row's `row_count` (the B1 header's `total_group_count`/`total_occurrence_count`/`total_fold_count`/`total_string_count` are removed — they added no independent verification value: both were populated by the same compiler run from the same data, so agreement proved nothing about correctness, only that the compiler didn't contradict itself, which the section-arithmetic check in §17.A already establishes just as well from the directory alone).

**SECTION DIRECTORY**: one row per section, in the fixed normative section order (§5), each `(section_id: u32, offset: u64, length: u64, row_count: u32, row_size: u32)`. `row_size` is included explicitly (rather than assumed from a hardcoded per-`format_contract_version` table) so §17.A's arithmetic check (`row_count * row_size == length`) is self-contained and does not require the validator to also hardcode row layouts out-of-band.

---

## 7. String Table

Unchanged in shape from B1 §4 (one contiguous UTF-8 STRING POOL blob + a `(offset: u32, length: u32)` STRING TABLE indexed by `string_id`), corrected only in what it claims to represent: per §4, pooled strings are UTF-8 encodings of **parsed token values**, not raw source substrings. All five categories (control literals, group names, metadata keys, metadata values, folded keys) continue to share one pool and one ID space. `string_id` and pool offsets are u32 (§15's resource limit on total pool size, generously beyond today's ~3.15 MB, keeps this safely within u32 range — see §15's explicit limit and required compile-time check).

---

## 8. Group / Wrapper / Root Representation

The wrapper is stored as **one ordinary row** in the GROUP TABLE, indistinguishable in row shape from any other group — no special-cased "is this the wrapper" bit anywhere in the format itself.

| Field | Type | Notes |
|---|---|---|
| `path_id` | u32 (= row index) | assigned by declaration order (`declare_order`, §26) over **every** group including the wrapper |
| `name_string_id` | u32 | into STRING TABLE |
| `parent_path_id` | u32 | `ROOT_SENTINEL` (`0xFFFFFFFF`) for a parentless group (the wrapper, in the single-wrapper compatibility profile); otherwise **must be `< path_id`** |
| `declare_order` | u32 | token-encounter order (duplicated from row index for clarity; see §17.C) |
| `sibling_rank` | u32 | 0-based among children of the same parent, by `declare_order` |
| `child_count` | u32 | number of direct children |
| `child_index_start` | u32 | first index into the CHILD-ID INDEX (§9) for this group's children |
| `metadata_start` / `metadata_count` | u32 / u32 | slice into METADATA TABLE (§10) |
| `occ_by_group_start` / `occ_by_group_count` | u32 / u32 | slice into OCCURRENCE-BY-GROUP INDEX (§11) |

Full-path strings are **not stored** — reconstructed on demand by walking `parent_path_id` to `ROOT_SENTINEL` and joining `name_string_id` strings with `/` (unchanged reasoning from B1 §6; bounded by actual nesting depth).

**Reader-exposed distinctions** (generic, no Normalizer-specific presentation logic):

- `all_parentless_group_ids()` — every row with `parent_path_id == ROOT_SENTINEL` (in the single-wrapper compatibility profile, this is exactly one; the API does not assume that, it returns whatever the compiled data actually contains, matching B0.1's own documented zero/multi-wrapper fallback, §3 item 3).
- `wrapper_group_ids()` — an alias for the above, named for clarity at call sites that specifically mean "the document root(s)."
- `root_group_ids()` — the direct children of the single wrapper when `len(wrapper_group_ids()) == 1`; otherwise identical to `wrapper_group_ids()` (mirrors `sfm_master_core.root_paths`'s documented fallback exactly).

No code path anywhere assumes the wrapper's name is `"groupFile"`. A Normalizer adapter wanting a "path relative to the wrapper" presentation (stripping the leading `groupFile/` for display) is explicitly a **later, adapter-layer** concern (§37) — the generic reader always returns full, wrapper-inclusive paths.

---

## 9. Child-ID Index

Astra's flattening adopted: a single `u32[]` array, length = total group count, holding **child `path_id` values**, laid out contiguously per parent in `(parent, sibling_rank)` order. A GROUP TABLE row's `child_index_start`/`child_count` slices directly into this one array — no redundant `(parent_id, child_id)` pair table (the parent is already known from whichever GROUP TABLE row is asking).

---

## 10. Metadata Table

Unchanged in shape and semantics from B1 §9 / B0.1's `GroupMetadata`: one row per metadata entry, `(path_id: u32, key_string_id: u32, value_string_id: u32, source_order: u32)`, in the exact order `GroupMetadata.entries` already preserves, duplicates included, never collapsed. `source_order` (renamed from B1's diagnostic `source_line`) is the 0-based encounter index *within that group's metadata list* — sufficient to reproduce exact order without depending on a source line number, consistent with §3 item 8's line-number-is-not-an-ordering-key principle applied uniformly. Absence remains exclusively `metadata_count == 0`; no bitmask; no closed key enum (unchanged rationale, B1 §9).

---

## 11. Occurrence Table

Unchanged core design from B1 §7: stored in **global source order**, row index **is** `global_rank` (no separate field needed). Each row: `(literal_string_id: u32, path_id: u32, local_rank: u32, fold_id: u32)`. `fold_id` is retained (Astra's "if it materially simplifies reverse integrity validation" test is met: §17.E/H's reverse-membership checks need an occurrence's fold_id to confirm OCCURRENCE-BY-FOLD INDEX correctness without re-folding every literal at validation time).

The table represents, without restriction: repeated identical controls, repeated aliases, same-destination duplicates, and cross-destination occurrences — this is unconditional at the format level; the official validator's policy (rejecting duplicates/conflicts for the *official* Master specifically) is never encoded into the generic binary (§28).

---

## 12. Occurrence-by-Group Index

Unchanged from B1 §7: a `u32[]` array, length = total occurrence count, holding `global_rank` values permuted into `(path_id, local_rank)` order. Sliced by each GROUP TABLE row's `occ_by_group_start/count`.

---

## 13. Fold Table

One row per distinct fold key, sorted by folded-key raw UTF-8 bytes (unchanged ordering rule, B1 §8). Row: `(fold_key_string_id: u32, occ_index_start: u32, occ_index_count: u32)` — **no `destination_count` field, no `conflict_flag` field** (both removed per the adopted simplification). Conflict status is **always** computed by the reader as "distinct `path_id` values among this fold's occurrence range, count `> 1`" — a cheap scan bounded by `occ_index_count` (today's largest family has 3 members; even a large custom-Master family is a small, bounded range per §15's alias-family expectations).

If a future profiling need ever shows this recomputation is a hot path, a cached count could be reintroduced — but per Astra's instruction, it is not added preemptively, and if it ever were reintroduced, **disagreement between the cached value and the freshly-scanned range must be treated as artifact corruption (`AuthorityUnavailable`), never silently trusted**. This rule is recorded now so it is not forgotten if that decision is revisited later.

Required lookup rule, unchanged and re-affirmed: a fold with more than one distinct destination is `FoldConflict` **even when the query's exact spelling matches one specific member** — exact-spelling convenience never overrides a genuine cross-destination conflict.

---

## 14. Occurrence-by-Fold Index

Unchanged from B1 §8: a `u32[]` array, length = total occurrence count, holding `global_rank` values permuted into fold-grouped order. Sliced by each FOLD TABLE row's `occ_index_start/count`.

---

## 15. Field Widths + Resource Limits

**Field widths** (default u32 for everything countable, per instruction; u64 only for file-level byte offsets/lengths that must outlive a single section's practical row-count scale):

| Category | Width | Fields |
|---|---|---|
| File-level byte offsets/lengths | u64 | `source_byte_length`, `payload_length`, `section_directory_offset`, SECTION DIRECTORY `offset`/`length` |
| All counts, IDs, ranks, slice starts | u32 | `path_id`, `parent_path_id`, `string_id`, `declare_order`, `sibling_rank`, `child_count`, `child_index_start`, `metadata_start/count`, `occ_by_group_start/count`, `global_rank` (implicit), `local_rank`, `fold_id`, `occ_index_start/count`, STRING TABLE `offset/length`, SECTION DIRECTORY `row_count`/`row_size` |
| Small fixed enums/flags | u8 | none required in the current design (the removed `conflict_flag` was the only candidate) |
| Version fields | u32 | `format_contract_version`, `authority_semantics_version`, `compiler_build_version` |
| Digests | 32 bytes (fixed) | `source_sha256`, `embedded_integrity_digest` |

No field silently truncates. **Every value is checked against its declared width's maximum, and separately against the resource limit below, before serialization; any violation is a compilation failure with a specific "value N for field F exceeds Y" error message, never a wraparound.**

**Resource limits** (compiler-enforced ceilings, deliberately generous relative to today's Master, explicitly distinct from what a u32/u64 field could theoretically encode — chosen so the *practical* limits are the ones checked, not the field's raw numeric capacity):

| Resource | Limit | Rationale |
|---|---|---|
| Source byte size | 512 MiB | A hand-authored text Master; today's is ~3.9 MB. 512 MiB gives ~130x headroom while still bounding worst-case memory during compilation. |
| Sidecar byte size | 512 MiB | Same order as source; today's estimate is single-digit MB. |
| Group count | 2^24 (16,777,216) | Vastly beyond 43; keeps `path_id` comfortably inside u32 with headroom for `ROOT_SENTINEL` (`0xFFFFFFFF`) to remain unambiguous. |
| Occurrence count | 2^28 (268,435,456) | ~2,088x today's 128,555. |
| Fold count | 2^28 | Bounded by occurrence count in practice (folds ≤ occurrences); same ceiling for consistency. |
| Distinct pool strings | 2^28 | Bounded by occurrence+group+metadata counts in practice. |
| Total string-pool byte size | 512 MiB | Matches the sidecar-size ceiling; today's is ~3.15 MB. |
| Single string byte length | 1 MiB | No plausible control literal, group name, or metadata value needs to exceed this; bounds a pathological single-row allocation. |
| Metadata rows per group | 2^16 (65,536) | Today's maximum for any one group is a handful; generous headroom without being unbounded. |
| Reader query byte length | 4,096 bytes | An identity string; anything longer is rejected as an input error before any lookup work begins (§4's "malformed/oversized query is an input error, not `MasterUnknown`" rule extended to length as well as encoding validity). |

These limits exist specifically so **the compiler fails explicitly, before any unsafe allocation or seek is attempted**, for any input that would exceed them — never a silent truncation, never an out-of-memory crash mid-write.

---

## 16. Integrity / Checksum Model

Two **distinct-purpose** digests, per Astra's required separation:

1. **`embedded_integrity_digest`** (in the HEADER, §6): SHA-256 over the entire published file, computed with the digest field's own 32 bytes locally zeroed during the calculation (a standard self-referential-checksum pattern). Covers header, versions, directory, and every section including any padding/reserved bytes. This is what `open_generation()` recomputes and compares at open time (§17) — it proves *this file's bytes are exactly what the compiler wrote*, nothing more.
2. **Ordinary full-file SHA-256** (`sidecar_sha256`, computed the normal way, nothing zeroed): used **externally only** — for the immutable generation filename (§29) and the manifest (§30). It is not stored inside the file at all (storing it would require the same self-reference problem `embedded_integrity_digest` already solves; there is no benefit to solving it twice with two different fields).

Neither digest proves *semantic* source-completeness (i.e., that the compiler correctly transcribed every fact from the reference TXT) — that is Gate 1's job (§34), stated as an explicit non-claim, matching B1 §10's original disclosure, now sharpened to name exactly which two digests exist and why neither is a substitute for parity testing.

No separate header CRC32 is retained — the single embedded SHA-256 supersedes it (a CRC32 was never a meaningfully faster check for a file already being SHA-256'd in the same open-time pass).

---

## 17. Complete Open-Time Validation

Performed once, in full, at `open_generation()` — not sampled, not "spot-checked." Chunked/sequential design: each pass below reads its target section(s) in bounded-size blocks (rather than requiring the whole file, or a whole fully-decoded Python object graph, resident at once), consistent with §21's memory posture. No pass depends on a prior pass having produced decoded Python objects beyond the small scalars (counts, offsets) needed for bounds arithmetic.

**A. Header / Directory.** `magic` exact match. `format_contract_version`/`authority_semantics_version` recognized by this reader (mismatch → `AuthorityUnavailable`, §19); `compiler_build_version` recorded, never checked for rejection. `payload_length` == actual file size. Section IDs form the exact expected set for this `format_contract_version`, each appearing **exactly once** (duplicate section IDs rejected). Every `(offset, length)` within `[0, payload_length)`. Sections sorted by offset with **no overlap** (gaps for alignment are permitted, overlaps are not). For every section, `row_count * row_size == length` (checked, unsigned, overflow-safe arithmetic — computed in a width wide enough that the multiplication itself cannot silently wrap before comparison). `embedded_integrity_digest` recomputed and compared.

**B. String Table.** Every `(offset, length)` row lies within the STRING POOL section's byte range. No two STRING TABLE entries are *required* to be non-overlapping (two IDs could legitimately reference the exact same bytes if the compiler ever chose to, though the compiler as designed never does this — dedup means it won't happen in practice, but the validator does not depend on non-overlap for correctness, only on in-bounds). Every referenced string's bytes, when read, are verified as **strictly valid UTF-8** (reject overlong encodings, unpaired surrogates encoded as CESU-8, and truncated multi-byte sequences) — a corrupt string reference must not be silently accepted as "whatever garbage bytes happen to be there."

**C. Group Table.** Every `parent_path_id` is either `ROOT_SENTINEL` or `< path_id` (the anti-cycle invariant — sufficient because the compiler always assigns `path_id` in `declare_order`, a parent-before-child traversal, §26). Every `name_string_id` in bounds (per A's/B's checks). `child_index_start + child_count` in bounds within the CHILD-ID INDEX section; every referenced child's own `parent_path_id` actually equals this group's `path_id` (membership agreement, not just bounds); children appear in strictly increasing `sibling_rank`, forming a dense `0..child_count-1` run with no gaps or repeats. `declare_order` values across the whole table are unique and, restricted to any one parent's children, monotonically increasing in `sibling_rank` order (declaration order and sibling order must agree — a coherence check, not merely two independently-plausible facts).

**D. Metadata.** Every GROUP TABLE row's `metadata_start/count` slice is in-bounds and **non-overlapping with every other group's slice** (each metadata row is owned by exactly one group — verified by confirming the table, read start-to-end once, partitions cleanly into contiguous, non-overlapping, `path_id`-homogeneous runs matching the GROUP TABLE's own slice claims). Every `key_string_id`/`value_string_id` in bounds. `source_order` values within one group's slice form a dense `0..count-1` run.

**E. Occurrences.** Every row's `literal_string_id`/`path_id`/`fold_id` in bounds. Global-rank invariant: trivially true by construction (row index is the rank) but the validator still confirms the table's declared `row_count` matches its section length under B's row-size arithmetic. `local_rank` values, when occurrences are grouped by `path_id` (via a single pass, not via re-invoking F below), form a dense `0..count-1` run per group, and that per-group count matches the owning GROUP TABLE row's `occ_by_group_count`.

**F. Occurrence-by-Group Index.** Read once, start to end: every value is a valid `global_rank` (< occurrence count); the **complete array constitutes an exact permutation** of `0..occurrence_count-1` — every occurrence referenced **exactly once**, no omissions, no duplicates (checked with a single bounded bitset/seen-count pass, not by materializing a Python set of a potentially large size — see §21). Each slice `[occ_by_group_start, occ_by_group_start+occ_by_group_count)` for a given group, when dereferenced, points only to OCCURRENCE TABLE rows whose `path_id` equals that group's `path_id`, and within the slice, `local_rank` is strictly increasing (local ordering agreement, not just membership).

**G. Fold Table.** Keys in **strict** ascending order by raw folded-key bytes (a single linear scan; also rules out duplicate fold keys as a side effect of strictness). For a bounded sample **and**, where affordable within the chunked-read budget, the full table: each fold row's `fold_key_string_id`'s bytes, when independently ASCII-folded-and-compared (or, more strongly, when every occurrence in its range is independently re-folded and compared), actually equal that row's own key — i.e. the row's claimed key is not merely well-sorted relative to its neighbors but **true** relative to the occurrence evidence it claims to summarize. `occ_index_start/count` slices in-bounds within OCCURRENCE-BY-FOLD INDEX.

**H. Occurrence-by-Fold Index.** Same permutation-completeness check as F, applied to this array: every occurrence referenced exactly once across the whole table (no omissions, no duplicates). Each fold's slice, when dereferenced, points only to OCCURRENCE TABLE rows whose `fold_id` equals that fold's row index, confirming full alias/destination evidence for that fold is actually reachable through the index (not silently short-sliced).

**Design note on scale:** F and H's "exact permutation of `0..N-1`" checks are the most work-intensive (O(N) with a bounded auxiliary structure). They are implemented as a single forward pass maintaining a compact seen-marker (e.g., a bit-array sized to `occurrence_count`, not a Python `set` of boxed integers) — bounded, predictable memory, no per-lookup cost once amortized at open time.

---

## 18. Version Contract

Two runtime-compatibility domains, replacing B1's four:

| Version | Covers | Mismatch behavior |
|---|---|---|
| `format_contract_version` | Byte layout: section list, row shapes, field widths | Reject (`AuthorityUnavailable`) — the reader literally cannot interpret the bytes |
| `authority_semantics_version` | Everything about what a group/occurrence/fold/metadata *means*: supported grammar, encoding contract, canonical hierarchy semantics, and the ASCII-fold algorithm itself | Reject — the compiled facts might mean something different than the reader assumes |
| `compiler_build_version` | Which compiler *implementation* build produced this file | **Provenance only. Never causes rejection.** Two compiler builds that implement the identical format+semantics contracts, one merely optimized relative to the other, must produce interchangeable, mutually-acceptable output. |

**Why merge parser/fold/compiler-construction semantics into one `authority_semantics_version` instead of keeping them separate:** B1 kept four domains partly to allow independent evolution, but no concrete scenario was identified where the ASCII-fold algorithm, the grammar, and the canonical-hierarchy-construction rules would need to version *independently of each other* — a change to any one of them changes what a compiled fact means, which is exactly what "authority semantics" is meant to capture as a single unit. Keeping them merged avoids the "two independent rejection domains with no demonstrated independent need" problem the task specifically asked to justify or avoid. If a genuine need to split them ever arises (e.g., a fold-only change that is provably compatible with all existing grammar/hierarchy consumers), that would be a deliberate future revision with its own justification, not a default posture.

The official Master's `source_sha256` remains explicitly **not** a version domain (unchanged from B1 §12) — data identity and format/semantics compatibility are orthogonal facts.

---

## 19. Reader Lifetime + Failure Contract

**`AuthorityUnavailable` (and its more specific subclasses) are raised exceptions, not ordinary lookup-result values.** Rationale: a lookup against valid, open, source-bound backing has exactly four meaningful outcomes (`Hit`, `FoldConflict`, `MasterUnknown`, `ViewUncovered`, for a view) — these are *facts about the query relative to sound data* and belong in an ordinary return-value enum. "The backing itself is unusable" is a categorically different situation: it says nothing about the query and everything about the provider's own health, and every call site that might encounter it needs to react the same defensive way (stop trusting this handle) regardless of which method it occurred in — an exception naturally propagates that without requiring every method's return type to carry a fifth, unrelated variant.

Conditions producing `AuthorityUnavailable` (a base exception type, with more specific subclasses where useful for callers who want to distinguish causes):

| Condition | When | Subclass (illustrative) |
|---|---|---|
| Any §17.A–H validation failure | At `open_generation()` | `InvalidBackingError` |
| Source-binding mismatch (§20) | At bind time, or at any authority-required call if binding was deferred | `SourceMismatchError` |
| Method called after `close()` | Any subsequent call on that handle or a view derived from it | `ClosedProviderError` |
| Short read / I/O error while servicing a lookup | Any lookup, if the backing mode involves live reads (§21) | `BackingIOError` |
| Backing mutation/invalidation detected (e.g. a live file's mtime/size changed since open, if the backing mode can detect this) | Any subsequent call | `BackingInvalidatedError` |
| Corrupt data discovered on a *later* read not covered by the eager open-time pass (should not happen given §17's exhaustiveness, but a defensive re-check on each section touch is cheap and required as a second line of defense) | Any lookup | `InvalidBackingError` |
| A view's parent handle has been closed | Any call on that view | `ViewInvalidatedError` |

**Lifetime rules:**
- `close()` is **idempotent** — calling it more than once is a no-op, never an error.
- Any call on a handle after `close()` raises `ClosedProviderError`.
- A `View` created from a handle is only valid while that handle remains open; closing the handle invalidates every view derived from it (`ViewInvalidatedError` on next use) — a view does **not** keep its parent handle alive implicitly.
- **Generation ownership is explicit and caller-driven.** Opening a new generation does **not** implicitly close an old one. During a hot-swap, both handles may be simultaneously open and valid; the caller decides when the old handle (and its views) are no longer needed and closes it explicitly. This is a deliberate, bounded overlap (§21), not an accident.
- On any error during `open_generation()` itself (including every §17 validation failure), no partial handle is returned — the call raises before producing an object the caller could mistakenly treat as usable.

`MasterUnknown` is reserved **exclusively** for a successful lookup, against valid, source-bound, fully-opened backing, whose folded identity genuinely does not exist in this exact Master generation. It is never returned, and never conflated with, any of the above.

---

## 20. Source Binding

Separated explicitly, per Astra's requirement, into two distinct open modes:

- **Diagnostic open** (`open_generation_unbound(path_or_bytes)`): validates the backing (§17) and returns a handle usable for inspection (dumping structure, running Gate 1 tooling, manual debugging) — but this handle is explicitly marked "not authority-bound" and any attempt to use it as production authority (see next bullet) raises.
- **Source-bound authority open** (`open_generation(path_or_bytes, expected_source_sha256)`): performs the same §17 validation, **plus** requires `header.source_sha256 == expected_source_sha256`; on mismatch, raises `SourceMismatchError` (a subclass of `AuthorityUnavailable`) rather than returning a handle at all. Only a handle obtained this way is permitted to serve as production lookup authority.

A structurally valid generation that simply doesn't match the caller's expected source **never silently becomes authority** — it either isn't opened as authority at all (this path), or, if opened diagnostically, is unusable for lookups (prior bullet). This directly satisfies the requirement that a mismatched-but-valid file cannot masquerade as authoritative.

---

## 21. Backing Immutability

**The invariant that must hold, regardless of which candidate is eventually chosen (Gate 2 decides, not this document):** *the bytes used by any lookup after `open_generation()` validation are exactly the bytes that were validated.* A read-only file handle alone does **not** guarantee this (the underlying file can still be replaced or truncated by another process between validation and a later read, on most filesystems/OSes).

Three candidates, each described in terms of what it would need to satisfy the invariant — none chosen here:

| Candidate | What it needs to satisfy the invariant |
|---|---|
| **A. One immutable packed byte buffer** (the whole validated file read once into a single in-memory buffer at open time) | Trivially satisfies the invariant (the buffer *is* the validated bytes, nothing external can change it) at the cost of holding the whole file resident — the memory-model question §21 of B1 already raised, deferred to Gate 2 measurement (§35). |
| **B. Bounded file reads from an immutable generation** | Needs the *publication* contract (§31) to guarantee the file at a given path is never modified in place after publish (only replaced-by-rename under a **different** immutable filename, §29) — i.e., immutability is enforced by the publication/naming scheme, not by the read mechanism itself. Still vulnerable to an external actor bypassing the publication contract (e.g. manually overwriting a "immutable" file) — a risk this design does not claim to defend against, only to make correct-usage safe. |
| **C. Memory mapping** | Same reliance on the publication contract as B for correctness against external modification, plus the platform-level guarantee that a mapped region reflects the file *at the time it was mapped* for the mapping's lifetime (true on the platforms in scope, but ties the mapping's lifetime directly to VAS occupancy — the §14/§15-of-B1 fragmentation concern, unresolved here, deferred to Gate 2). |

No candidate is chosen in B1.1. Gate 2 measures actual resident/latency cost under the real embedded environment before a default is picked (§35).

---

## 22. Bounded View Semantics

**Corrected from B1.** Coverage is by **folded identity**, never by a truncated path/destination slice.

```
view = handle.new_view()
view.add_identity(literal_or_folded_key: bytes) -> None
    # Resolves the COMPLETE fold family for this identity against the
    # complete backing and marks the ENTIRE family as covered: every
    # alias, every occurrence, every destination, and the conflict state
    # itself. There is no partial-family coverage.

view.lookup(query: bytes) -> Hit | FoldConflict | ViewUncovered | MasterUnknown
    # ViewUncovered: this fold exists (or might exist) in the complete
    #   backing but was never added to THIS view via add_identity().
    # MasterUnknown: the identity does not exist in the complete backing
    #   at all (established by consulting the complete backing directly,
    #   not merely by absence from this view's coverage).
    # A view can NEVER report Hit for a fold whose complete-backing truth
    # is FoldConflict -- if the family is covered at all, its true
    # conflict state is exposed exactly as the complete backing has it.

view.query_complete_backing(query: bytes) -> Hit | FoldConflict | MasterUnknown
    # Unchanged concept from B1 -- an explicit escape hatch to consult the
    # complete authority directly, used to decide whether to expand
    # coverage. Never a TXT-parsing fallback; always a same-binary query.
```

`add_path_prefix()` is **dropped from the initial generic API**, per instruction, pending an actual Normalizer requirement that would justify it. If such a requirement emerges, it would be implemented as a convenience that internally resolves every occurrence under that path to its fold and calls `add_identity()` for each — i.e., a derived convenience over the whole-family primitive, never a way to add partial coverage.

---

## 23. Result Materialization

No API promises a `Hit`/`FoldConflict` result is always a tiny, fully-materialized list. A compatible custom Master could have a fold with thousands of aliases or duplicate occurrences. Design posture (not implemented yet):

- `Hit`/`FoldConflict` carry a **range descriptor** (start/count into the relevant index, or an opaque cursor), not a required fully-materialized Python list.
- A separate accessor (e.g. `result.iter_occurrences()`) yields evidence lazily, one bounded read at a time, so a caller who only needs "is this a hit, and what's the primary destination" never pays for materializing a large alias set they don't want.
- A caller who does want the full evidence can explicitly materialize it (e.g. `list(result.iter_occurrences())`), at a cost proportional to that family's actual size — an informed choice, not an implicit default.
- View-level caching (§22) has an explicit, bounded budget (a maximum number of cached fold lookups, evicted LRU or similar) rather than an unbounded cache that could grow with a long-lived view's query history — exact budget numbers are a Gate 2 concern, not fixed here.

Nothing here is implemented in B1.1; this is the API-shape commitment that later implementation must honor so it doesn't quietly regress into "always materialize everything."

---

## 24. Generic Reader API

Class/method names are illustrative, not frozen (per instruction, pending Normalizer seam review, §37).

```
open_generation(path_or_bytes, expected_source_sha256) -> GenerationHandle   # raises AuthorityUnavailable-family on any failure
open_generation_unbound(path_or_bytes) -> GenerationHandle                   # diagnostic only, not authority-usable for lookups

handle.source_sha256 -> bytes
handle.lookup_fold(query: bytes) -> Hit | FoldConflict | MasterUnknown
handle.get_family_evidence(query: bytes) -> FamilyEvidence                   # aliases/destinations/occurrences, materialized per sec 23's posture
handle.get_group(full_path: bytes) -> GroupRecord | None                     # sec 25 addresses lookup efficiency
handle.iter_metadata(full_path: bytes) -> iterator[(key, value)]
handle.iter_occurrences(full_path: bytes) -> iterator[OccurrenceRecord]
handle.wrapper_group_ids() / root_group_ids() / all_parentless_group_ids() -> list
handle.new_view() -> View
handle.close() -> None                                                       # idempotent

view.add_identity(literal_or_folded_key: bytes) -> None
view.lookup(query: bytes) -> Hit | FoldConflict | ViewUncovered | MasterUnknown
view.query_complete_backing(query: bytes) -> Hit | FoldConflict | MasterUnknown
```

`AuthorityUnavailable` and its subclasses (§19) are raised, not returned, from any of the above.

---

## 25. Python-2.7 Import Boundary

Enforced by **package structure**, not convention (§38 gives the full module map):

```
runtime_safe/            <- importable under Python 2.7; the ONLY package SFM ever imports
    format_constants.py    # magic, section IDs, field layouts, version constants
    integrity.py            # sec 17's validation checks, sec 16's digest verification
    reader.py               # GenerationHandle / View / lookup logic (sec 24)
```

`runtime_safe/` imports nothing from `sfm_master_core`, the compiler, the CLI, or any Python-3-only validation module — enforced by the package simply never containing such an import statement, and checkable mechanically (a Gate 1 check: `grep`/AST-scan `runtime_safe/` for any `import` outside its own package and the Python 2.7/3.x-common standard library). `runtime_safe/__init__.py` itself must not import anything beyond its own submodules, so that `import runtime_safe` alone (as SFM would do) can never accidentally pull in a Python-3-only module transitively.

Everything else (`sfm_master_core.py`, the compiler package, the CLI, the offline validation/Gate-1 package) may freely import `runtime_safe/` (to self-validate/self-test using the exact same reader code, §38) but the dependency direction is strictly one-way.

---

## 26. Deterministic Serialization

Unchanged in principle from B1 §21, restated exactly per the requested canonical-ordering list:

| Element | Canonical order |
|---|---|
| String IDs | First-seen, in a single deterministic traversal: group names in `declare_order`; control literals in global occurrence order; metadata keys/values in METADATA TABLE row order; fold keys in FOLD TABLE's own sorted order. A string already assigned an ID is never re-added (pool dedup). |
| Group IDs | `declare_order` (token-encounter order) |
| Metadata | Source order within each group (`source_order`, §10) |
| Occurrences | Global source order |
| Folds | Sorted folded UTF-8 byte key (strict, total, locale-free) |
| Occurrence-by-Group Index | Owning-group, then local rank |
| Occurrence-by-Fold Index | Owning-fold, then... (a documented tie-break: global occurrence rank, so two occurrences of the same fold order by when they appeared in the source, not by any other incidental factor) |
| Child IDs | Sibling encounter order (`sibling_rank`, itself derived from `declare_order`) |
| Sections | Fixed normative order (§5), never data-dependent |
| Padding | Zero bytes |
| Reserved | Zero bytes |

No output byte depends on: `dict`/`set` iteration order, Python's hash randomization, locale, filesystem enumeration order, source file path, machine path, username, or wall-clock time. Recompiling identical source bytes under identical version constants must produce byte-identical output — a required Gate 1 check (§34), verified across every Python 3 environment Gate 1 runs in (a stated, checkable determinism claim, not an assumption).

---

## 27. Public Compiler Contract

Unchanged in shape from B1 §17, restated with the corrected encoding language (§4) and the explicit generic/policy separation (§28) folded in. The public CLI (illustrative shape, not frozen): validate source with `sfm_master_core` → refuse on `not result.ok` → compile deterministically → self-validate with the `runtime_safe` reader (§25) → full semantic parity against the `MasterParseResult` the writer was given → only then publish (§31). Same exit-code philosophy as `validate_master.py` (0 success, 1 source rejected, 2 I/O/internal, 3 self-check failure), unchanged from B1 §17.

---

## 28. Official Validator vs. Generic Compilability

Explicit two-tier separation, sharpened per instruction:

- **A. Generic compilability**: a source is compilable if `sfm_master_core.parse_master_bytes(...).ok` is `True` — i.e. structurally valid and every fact fully representable in the binary format, **including** duplicate control occurrences and cross-destination fold conflicts (§3 items 9–10; §11, §13). The public compiler compiles such a source unconditionally — it applies no additional taxonomy/content policy of its own.
- **B. Official Master release policy**: `tools/validate_master.py`'s own checks (`exact_duplicate`, `cross_path_casefold`) remain a **separate, additional** gate that only the official release workflow (§30 of B1, unchanged) applies before *this project* accepts a generation as its official published artifact. An advanced user compiling their own custom Master — one that happens to contain duplicate controls or fold conflicts — gets a fully valid, complete, loadable sidecar; whether *this project* would ever publish such a Master as "official" is an entirely separate question the compiler itself never decides or blocks on.

The CLI's language (help text, success messages) must reflect this: a successful compile of a Master with duplicates/conflicts says so factually ("compiled: 3 duplicate control occurrences present, 1 cross-destination fold conflict present") without implying rejection, and without silently applying the official validator's stricter policy to a file that never asked to be the official Master.

---

## 29. Generation Identity

**Corrected from B1.** Immutable generation filename is keyed on the **full ordinary sidecar SHA-256** (§16), not a source-SHA prefix:

```
sfm_master_<format_contract_version>_<full-64-hex-char-sidecar-sha256>.bin
```

Including `format_contract_version` in the filename is a human-readability aid (so a directory listing groups generations by format era at a glance) — it carries no validation authority; **the filename is never treated as validation authority under any circumstance** (§16/§17 are the only authority). If a file already exists at the computed name: read it, compute its digest, and compare — identical digest means this exact generation was already published (a safe no-op, publication succeeds trivially); a **different** digest under the same computed name is an internal contradiction (SHA-256 collision territory, or a filesystem-level tampering/bug) and is treated as a **hard publication failure** — the existing file is never overwritten under any circumstance.

---

## 30. Manifest Contract

Small JSON pointer, contents unchanged in spirit from B1 §19, tightened per instruction:

```json
{
  "generation_basename": "sfm_master_1_<64-hex>.bin",
  "sidecar_sha256": "<64-hex>",
  "source_sha256": "<64-hex>",
  "source_byte_length": 3975311,
  "format_contract_version": 1,
  "authority_semantics_version": 1,
  "counts": { "groups": 43, "occurrences": 128555, "folds": 124728 }
}
```

`counts` are **diagnostic only** — a human/ops convenience, never re-derived as validation authority; the binary's own §17 validation and the source-binding check (§20) remain the sole authority.

Manifest parser contract (must be defined precisely, not left implicit, per instruction):
- Maximum manifest file size (e.g. 64 KiB) — reject larger files outright as invalid, never attempt to parse an unbounded blob as JSON.
- Required keys: `generation_basename`, `sidecar_sha256`, `source_sha256`, `format_contract_version`. Missing any required key → invalid manifest.
- Duplicate JSON keys: reject the manifest as invalid (do not rely on "last key wins" JSON-library behavior, which is not something this design should depend on implicitly).
- `generation_basename` **must be a bare filename with no path separators of any kind** (reject any value containing `/`, `\`, or a `..` component) — resolved only by joining it to the manifest's own known, trusted containing directory. This directly prevents an arbitrary relative/absolute path from a manifest ever causing the loader to open a file outside the intended output namespace.
- Invalid JSON (parse failure) → manifest invalid, treated identically to "no manifest present" for loading purposes (i.e., no eligible published generation is currently known), never a crash.
- Unsupported `format_contract_version` recorded in the manifest → the manifest is *readable* (its own JSON is well-formed) but the generation it points to is not opened as authority by a reader that doesn't support that version — this is reported the same way any other `format_contract_version` mismatch is (§17.A, §19), not as a manifest-specific error class.

---

## 31. Publication Transaction

Revised ordering, per the task's explicit 18-step sequence, condensed here with the corrections it calls for:

```
1.  capture exact source-byte snapshot
2.  hash that snapshot -> source_sha256
3.  parse with sfm_master_core; require result.ok
4.  compile complete generation (writer.py, pure, in-memory or spooled to a temp buffer)
5.  write to a UNIQUE temporary file in the destination filesystem (not the final immutable name yet)
6.  flush/fsync as appropriate for the platform
7.  validate with the runtime_safe reader (open_generation_unbound -- diagnostic, since this
    temp file isn't published yet)
8.  exhaustive semantic parity (sfm_master_core's own parse of the source vs. the reader's view
    of the temp file)
9.  independent inventory parity (the Gate-1 oracle, sec 34)
10. close all validation handles on the temp file
11. compute the temp file's full ordinary SHA-256 -> the generation's permanent identity (sec 29)
12. publish/reuse the immutable generation (sec 29's identical-content-reuse /
    different-content-hard-failure rule)
13. write a NEW temporary manifest (not overwriting the live one yet)
14. flush the temporary manifest
15. acquire the output-namespace publisher lock (sec 32) -- serializes step 16-18 against any
    concurrent publisher for this SAME output directory
16. re-read and re-hash the LIVE source path (if the source was given as a path, not as
    in-memory bytes) -- if it no longer matches source_sha256 from step 2, ABORT without
    touching the live manifest (source mutated during build)
17. atomically replace the live manifest with the new temporary one (rename)
18. release the publisher lock
```

On any failure at steps 3–16, the temp file/temp manifest are discarded and the **previously published generation and manifest are left completely untouched** (unchanged guarantee from B1).

**Explicit non-claim, stated plainly per instruction:** the source recheck at step 16 does **not** make "the TXT plus the pointer" atomic against an arbitrary external editor that might modify the TXT again a moment after step 16's re-read. What the manifest actually asserts, precisely, is: *"this sidecar is the last successfully published compilation of source SHA X, as of the publish transaction that wrote it."* Whether that sidecar remains *eligible* for use as production authority right now is a separate, always-current check: `current source SHA == manifest's recorded source SHA`, re-verified by the *consumer* (via §20's source-bound open) every time it matters, not asserted once and trusted forever by the publication transaction. This is a deliberately weaker, honestly-stated guarantee, not a claim of full external-editor-proof atomicity.

---

## 32. Concurrent Publishers

An explicit output-namespace lock, acquired only around steps 16–18 of §31 (the narrow window that actually mutates the shared, live manifest pointer) — not around the whole transaction, so two publishers compiling independently (steps 1–15) never block each other; they only serialize at the moment of actually deciding which one's manifest becomes live.

Simplest sufficient mechanism (not over-engineered, per instruction): an OS-level exclusive lock file in the output directory (e.g. `sfm_master_sidecar.manifest.lock`), acquired with a non-blocking or short-timeout exclusive-open/lock primitive available on both the compiler's Python 3 environment and any tooling that might also publish (this lock is never touched by the Python-2.7 reader, which never publishes anything).

**Stale-lock/recovery, described conceptually:** if a publisher crashes while holding the lock, the lock file may be left behind. Recovery is a simple staleness heuristic (e.g., the lock file records the holder's PID and a timestamp; a subsequent publisher finding a lock older than a generous threshold, and whose recorded PID is no longer running, may reclaim it) — not implemented in B1.1, but the design explicitly rejects any scheme that would require a distributed-consensus mechanism for what is, in practice, a single-repository, small-number-of-publishers scenario.

---

## 33. Generation Cleanup

**Not automatic.** An immutable generation file is never deleted by the publication transaction itself, regardless of whether it is still the "current" one per the manifest — a reader (e.g. a long-running SFM session) may still have it open. Cleanup of no-longer-referenced generations is explicitly:

- **Optional maintenance**, run separately (e.g. a manual or scheduled sweep that deletes generation files not referenced by the current manifest and older than some retention window).
- **Never** a dependency of publication correctness — publication succeeds or fails based solely on §31's steps, never on whether cleanup has run recently or at all.
- **Conservative by design**: an orphaned generation left behind after a crash (or simply superseded by a newer one) is harmless disk usage, not a correctness hazard, and is treated that way rather than being aggressively reclaimed.

---

## 34. Independent Inventory Oracle

**Strengthened per Astra's specific "content parity, not counts only" requirement.** The oracle (still not built in this design phase; still `tools/`-adjacent, structurally isolated from `sfm_master_core` and the compiler, per B0's established `verify_phase2_production_order.py` pattern) produces an **ordered event log** from its own from-scratch tokenization of the reference TXT:

```
[ (event_kind, payload, source_position), ... ]
```

where `event_kind` is one of `group_enter` (payload: name, parent-ancestry-as-a-list-of-names), `group_exit`, `control` (payload: exact literal text), `metadata` (payload: exact key text, exact value text) — each carrying its token-stream position for tie-breaking and diagnostics.

The oracle independently reconstructs this same event log from the **published sidecar** via `runtime_safe.reader` (raw structural traversal — group enter/exit by walking the GROUP TABLE/CHILD-ID INDEX, controls via OCCURRENCE TABLE in global order, metadata via METADATA TABLE per group in `source_order`) and requires the two ordered event logs to be **exactly equal**, element for element — not merely equal in aggregate counts. This closes precisely the gap Astra identified: "one omitted control replaced by a duplicate elsewhere" would leave total occurrence *count* unchanged but would produce a different literal at some specific position in the ordered event log, which this comparison catches where a count-only comparison would not.

The oracle remains bound by the same production-authority exclusion as B1 §22: it never becomes a source of truth for taxonomy classification, fold-conflict policy, reader lookup policy, or metadata *interpretation* — it only compares two independently-produced ordered token streams for exact equality.

---

## 35. Custom / Adversarial Fixtures

The full B1 §23 catalog is retained and **extended** exactly per the task's list. New/expanded categories, each to be built as a small, hand-authored, syntactically-compatible custom Master (since the official Master has zero duplicates/conflicts and cannot exercise these paths):

**Positive (must compile and behave correctly):** duplicate controls within one group; duplicate controls across groups; same-destination alias families; cross-destination alias families; an exact query landing inside a still-conflicting family (must report `FoldConflict`, §13); wrapper-owned controls; wrapper-level metadata; a custom (non-`"groupFile"`) wrapper name; unknown metadata keys; duplicate metadata entries; an empty-string metadata value (`""`) if the grammar's quoted-string rule permits it (it does — an empty quoted string is a valid, zero-length STR token); non-ASCII text; the project's own historical mojibake pair (`注視TipsParent` / its corrupted sibling) as a literal-preservation regression case; non-BMP text (e.g. an emoji or other astral-plane character, to exercise UTF-8's 4-byte sequences specifically, since §3's fold/UTF-8 proof must hold for these too); escaped quotes/backslashes inside a literal; unusual whitespace (embedded tabs, multiple consecutive spaces — already partially covered by B0's tests, extended here); a valid final entry at EOF; same-line nested/sibling groups (already covered by B0.1, re-exercised at the binary-format level here); deliberately deep nesting (e.g. 20+ levels, to stress path reconstruction, §8); long strings (near the §15 single-string-length limit, to prove the limit is enforced rather than merely documented); large alias families (hundreds of aliases for one fold, to exercise §23's lazy-materialization posture); and counts specifically chosen to exceed what the *former* B1 u16 fields would have overflowed (e.g. a group with >65,535 children, or a fold with >65,535 occurrences) — proving the u32 widening (§15) actually matters, not just that it was declared.

**Negative (must be refused, each with the specific expected failure):** duplicate group paths (already a B0.1 parser-level rejection, re-exercised end-to-end through the compiler here); slash-containing group names (same); malformed UTF-8 in the raw source bytes (a decode failure, per §4 — refused before `sfm_master_core` even reaches token-level parsing); malformed/unterminated quotes; unmatched braces; an unsupported document/root shape (e.g. zero or more than one parentless group, exercising §3 item 3's documented fallback rather than a crash); and any unconsumed-token case beyond what B0.1's own test suite already covers (a belt-and-suspenders re-check at the compiler-integration level, not a claim of new parser behavior).

---

## 36. Gate 1 Qualification

Four proof layers, unchanged in structure from B1 §22, **strengthened** per this document's revisions:

**A. Independent ordered source inventory** — now the content-parity oracle of §34, not a count-only comparator.
**B. Full semantic parity** — every occurrence/group/fold/metadata fact, `sfm_master_core` vs. the `runtime_safe` reader reading the published binary, full population.
**C. Hand-audited adversarial fixtures** — the expanded catalog of §35.
**D. Corruption/version/publication-failure testing** — every §17 check exercised by deliberate corruption, **plus the checksum-awareness doctrine below**.

**Checksum-aware corruption testing (new, per instruction):** for every structural-corruption test case, the test **first mutates the target structure, then correctly recomputes `embedded_integrity_digest` over the mutated bytes, then opens the artifact.** Two explicit sub-categories are required for every corruption class where both are meaningful:
- **Checksum-invalid corruption**: mutate a byte and leave the old digest in place → must fail at the digest-comparison step (§17.A) specifically.
- **Checksum-valid, structurally-invalid corruption**: mutate a byte *and* correctly recompute the digest over the mutated file → must still fail, but at whichever specific §17.B–H check the mutation actually violates (e.g. an out-of-bounds string ID, or a broken fold-sort-order) — proving the structural checks are pulling real weight and are not merely redundant with the checksum.

**Additionally required, per instruction:**
- **Deterministic binary equality across supported Python 3 environments** — compile the same source on at least two distinct Python 3 minor versions / OS environments available to Gate 1 and diff the output bytes; must be identical.
- **Actual Python 2.7 execution of the production reader** — not merely "written to be 2.7-compatible" but run under a real Python 2.7 interpreter as part of Gate 1, exercising at minimum Layer B's parity suite and a representative slice of Layer C's fixtures.

Gate 1's outcome, if fully passed, identifies an **experimental / release-candidate format** — explicitly not a declaration of a stable public v1 (§39).

---

## 37. Gate 2 Deferred Measurements

Explicitly not decided in B1.1, deferred to Gate 2 measurement in the actual embedded x86/Python-2.7 SFM environment:

- Backing mode choice among §21's candidates A/B/C.
- Real SFM input-string conversion cost/path (how a caller's native string reaches the reader's UTF-8-bytes contract, §4).
- Actual resident/VAS cost of an open `GenerationHandle` and of active `View`s.
- Validation/open latency (§17's full pass, measured wall-clock, not just "O(n) and cheap" asserted).
- Generation-overlap cost during a hot-swap (§19's caller-driven dual-handle window).
- View retention/cache cost under §23's eventual concrete budget numbers.
- `close()` behavior and any observable cost under real SFM process-lifetime patterns.
- Largest-free-region / VAS-fragmentation effects specifically, given 32-bit/LAA constraints.

Only **one** backing-mode candidate should be implemented for Gate 2's first measurement pass (per instruction, not multiple production strategies built preemptively) — Mode A (bounded ordinary file reads, per B1 §14's original tentative lean) remains the suggested starting candidate, revisited only if Gate 2 measurement shows a concrete problem.

---

## 38. Normalizer Adapter Boundary

Unchanged separation from B1 §25, restated with this document's revised generic surface:

**Finalizable now, independent of the Normalizer contract:** everything in §24 (`open_generation`/`open_generation_unbound`, source binding §20, `lookup_fold`/`get_family_evidence`, group/metadata/occurrence iteration, the `View` primitives of §22 including the corrected whole-family coverage rule), the full integrity/lifetime contract (§17/§19), and the binary format itself (§5–§16).

**Kept provisional, pending actual Normalizer contract review:** exact result-object class names/shapes; whether evidence materialization (§23) defaults to eager or lazy for the Normalizer's actual usage patterns; the vocabulary/view API's exact ergonomics (e.g. whether `add_identity` should accept a batch, or whether a convenience wrapping `add_path_prefix`'s semantics — resolving to per-identity calls internally — is ever justified, §22); how a caller's native string reaches this reader's UTF-8-bytes contract at the actual SFM boundary (§4); any relative/wrapper-stripped path presentation (§8); and any cache-behavior tuning beyond §23's bounded-budget posture.

Gate 1 qualification (§36) does not block on any of the provisional items above — it exercises only the finalized generic contract.

---

## 39. Format Freeze Policy

Revised milestone sequence, per instruction:

```
implementation uses an EXPERIMENTAL format_contract_version (e.g. 0, or an explicitly
    labeled "-exp" identifier, never "1")
    -> Gate 1 PASS (sec 36, including Python 2.7 execution + cross-environment determinism)
        -> identified as a RELEASE CANDIDATE format
            -> Gate 2 measurement in embedded x86 SFM (sec 37)
                + a narrow, real consumer-contract check against the actual Normalizer
                  (not the provisional adapter guesses of sec 38)
                    -> THEN, and only then: format_contract_version 1 declared STABLE
```

No public "v1 compatibility" promise is made immediately after Gate 1 passes. A release-candidate format may still change before the stable freeze if Gate 2 or the real Normalizer check surfaces a genuine problem — Gate 1 proves *correctness of what was designed*, not that *nothing about the design needs to change*.

---

## 40. Exact Implementation Sequence

Unchanged in spirit from B1 §28, resequenced to front-load the `runtime_safe` boundary (§25) given its new prominence:

1. `runtime_safe/format_constants.py` — the byte-format-as-code, in isolation, no writer/reader logic yet.
2. `sfm_master_compiler/writer.py` — against small, hand-built in-memory `MasterParseResult` fixtures (not the real Master), covering §35's positive fixture categories one at a time.
3. `runtime_safe/reader.py` + `runtime_safe/integrity.py` — round-trip against the same fixtures, under **both** Python 3 (compiler-side self-validation) and a real Python 2.7 interpreter, before ever touching the real 128,555-occurrence Master.
4. §35's negative/corruption fixtures, including the checksum-aware doctrine of §36.D.
5. The independent content-parity oracle (§34), built and proven against the small fixtures first.
6. The compiler CLI (§27) and the full official-Master compile-and-self-validate path.
7. The full Gate 1 run (§36) against the real canonical Master, including cross-Python-3-environment determinism and real Python 2.7 execution.
8. Only after Gate 1 passes: publication transaction (§31) and concurrent-publisher locking (§32) implemented and exercised, still without touching the official build workflow.
9. Official build workflow wiring (unchanged from B1 §18) — last, and only after everything above is independently proven.

---

## Safety Confirmation

- `sfm_defaultanimationgroups.txt`: unchanged, SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- HEAD: unchanged, `8b4f0cb54750a5360a9897bb981af5463ab28681`
- `tools/validate_master.py`: PASS (reconfirmed fresh before writing this document)
- Tests: 52 passed, 0 failed (reconfirmed fresh before writing this document)
- No production code changed in this phase (design-only)
- Nothing staged, nothing committed
- No binary format, compiler, reader, manifest, lock, or inventory-oracle implementation begun
- No agents or subagents used
