# SFM Master Sidecar — B1 Astra Review Handoff

Full design: `SFM_MASTER_SIDECAR_PHASE_B1_DESIGN.md` (this document summarizes it for review; the full document is authoritative on detail).

## Problem being solved

`sfm_defaultanimationgroups.txt` (128,555 control occurrences, 43 groups, 124,728 ASCII-fold families, currently 0 duplicates/conflicts) is a hand-authored, text-parsed Master used by SFM's Python-2.7-era embedded runtime. We want a **generated, complete, disposable, deterministic, source-bound** packed binary sidecar so a production reader never re-parses the TXT and never treats a genuine miss as ambiguous. The TXT stays the sole authored authority; the sidecar is a pure compiled artifact of it, and the exact same compiler must serve both the official build and any advanced user's own compatible custom Master.

## Qualified B0 semantic foundation

Phase B0 (already implemented, committed only conceptually here — no new production code in B1) produced `tools/sfm_master_core.py`: a single, source-agnostic parser/fold/hierarchy authority, extended with presence-aware group metadata (`groupColor`/`selectable`/`visible` — no hardcoded key enum, so a custom Master's own keys work unmodified) and explicit 0-based global/local occurrence ranks. It has zero official-Master or repository assumptions. B1's compiler consumes this exact structure and never re-tokenizes/re-folds/re-infers hierarchy itself.

## Proposed binary layout

Small versioned binary, little-endian, fixed-width fields, one shared UTF-8 string pool (deduplicated, referenced everywhere by integer `string_id`), explicit `(offset, length, row_count)` section directory — no pickle/marshal/JSON/SQLite/compression-by-default. Sections: HEADER, SECTION DIRECTORY, STRING POOL, STRING TABLE, GROUP/PATH TABLE, CHILD INDEX, METADATA TABLE, OCCURRENCE TABLE (stored in source order — row index *is* the global rank), OCCURRENCE-BY-GROUP INDEX, FOLD TABLE (sorted by folded-key raw bytes), OCCURRENCES-BY-FOLD INDEX, INVENTORY FOOTER. Today's measured payload is roughly single-digit megabytes (string pool ~3.15 MB; occurrence/fold tables ~2 MB each).

## Lookup / fold / conflict semantics

Binary search over the FOLD TABLE by raw folded-key bytes (pure byte comparison, no locale/Unicode collation — Python 2.7's native `str` byte semantics make this a non-issue rather than something to work around). A fold with one destination is always `Hit`; a fold with more than one destination is always `FoldConflict`, **even when the query's exact spelling matches one specific member of the conflicting family** — an exact match never silently overrides a still-conflicting fold. A fold key absent from the table is `MasterUnknown`.

## Metadata handling

Metadata is stored generically (key/value string IDs, no closed enum), one row per entry, in a per-group variable-length slice. Absence is represented **exclusively** by a zero-row slice — never inferred from a stored `"0"` or empty value. Duplicate keys within one group are preserved as separate rows, never collapsed; an ambiguous duplicate is surfaced as ambiguous, not silently resolved.

## Completeness strategy

Redundant, independently-computed inventory counts in both the HEADER and a dedicated INVENTORY FOOTER (group/occurrence/fold/string counts, plus an explicit tail-occurrence fact). None of this is claimed as proof of *semantic* correctness by itself — that proof is Gate 1's job: an independent from-scratch inventory oracle (re-tokenizes the TXT, never imports the shared core) plus a full, whole-population semantic-parity pass (every occurrence/group/fold/metadata fact, TXT-derived vs. binary-derived), not a sample.

## Corruption behavior

Every structural invariant (section bounds/overlap, row-count agreement, string/path ID bounds, anti-cycle parent ordering, fold-table sort order, checksum) is checked once, eagerly, at open time. Any failure of any kind produces `AUTHORITY_UNAVAILABLE` — **never** `MASTER_UNKNOWN`. The two failure modes are never allowed to look the same to a caller.

## Python-2.7 reader model

`struct`-based fixed-width reads over plain file `seek`/`read`, byte strings throughout, no `pathlib`/`dataclasses`/modern typing at runtime. The same reader module is written in a Python-2.7/3.x dual-compatible subset so the compiler (Python 3) can run the identical reader against its own output for self-validation, and SFM's embedded Python 2.7 runs the same file unmodified in production — one reader, two interpreters, not two readers. Two backing-mode candidates (bounded ordinary file reads vs. `mmap`) are identified; bounded reads are the tentative default recommendation, with the decision deferred to Gate 2 measurement rather than made on elegance grounds.

## Memory strategy

Resident after open: header + section directory only. Everything else is decoded in small, bounded slices per lookup and released. Bounded caller views hold only the coverage they were explicitly given, never the whole occurrence graph. The reader never holds a decoded TXT graph (it never touches the TXT at all) and never holds two full generations' data simultaneously except a brief, bounded overlap during a hot-swap.

## Standalone/public compiler workflow

One compiler codebase (`tools/sfm_master_compiler/`), consuming `sfm_master_core` only. A single public CLI (`sfm-master-compiler <master.txt> ...`) serves maintainers and advanced modelers identically; the official build workflow is simply "this CLI, invoked against the official file, with output committed" — there is no separate/private compile path. A future standalone Windows executable would package this same codebase, not reimplement it.

## Publication model

Capture bytes → hash → compile (pure, in-memory) → write to temp → self-validate with the real reader → full parity check → re-verify source identity hasn't changed mid-build → atomic rename to an immutable, content-addressed filename (`sfm_master_<sha-prefix>_<format-version>.bin`) → update a small manifest pointer last. Any failure at any step leaves the previously-published generation and manifest completely untouched. Output is fully deterministic (recompiling identical bytes under identical version constants yields byte-identical output — a required Gate 1 check).

## Gate 1 proof plan

Four layers: (A) independent from-scratch source inventory; (B) full, whole-population semantic parity (TXT-derived vs. binary-reader-derived) across every occurrence/group/fold/metadata fact; (C) a concrete hand-audited fixture catalog (exact/alias/conflict/metadata/duplicate/tail/non-ASCII cases); (D) deliberate corruption/incompatibility/publication-failure testing, each asserting `AUTHORITY_UNAVAILABLE`, never a false `MASTER_UNKNOWN`. All four layers are additionally re-run against a small hand-authored custom Master to prove the single-compiler requirement isn't merely asserted.

## Known open Normalizer adapter questions

The real Normalizer/production-consumer contract (T138–T149 lineage) is not present anywhere in this repository (confirmed by search in Phase A, unchanged since). This design deliberately separates a **generic complete-authority reader contract** (fully specified in §13 of the full document — open/validate/lookup/hierarchy/bounded-view primitives, all finalizable now, independent of any external consumer) from a **Normalizer-specific provider adapter** (entirely unspecified — exact call signatures, when a bounded view gets expanded, whether any additional static fact is needed) that must wait for the real contract. Nothing in the generic design below depends on resolving the adapter first.

---

## Questions for Astra

1. Is the proposed byte layout sufficiently complete and auditable?
2. Is the fold/alias/conflict representation correct?
3. Is the metadata presence representation sound?
4. Are the proposed corruption/invalidation semantics fail-closed enough?
5. Is the Python-2.7/x86 reader design appropriate?
6. Is the memory model plausible for SFM?
7. Is the public standalone compiler architecture appropriate for advanced modelers maintaining custom Masters?
8. Does the publication/manifest model safely handle source changes and failed builds?
9. Are any parts overengineered?
10. Are any necessary static semantics missing?
11. What should be changed BEFORE implementation?
12. Is this design ready to implement and then qualify under Gate 1?

---

**Status:** Master unchanged, no production code changed, nothing staged, nothing committed, no binary/compiler/reader implementation begun. Waiting for Astra review before any Phase B1 implementation begins.
