# SFM Master Sidecar — B1.1 Astra Compliance Handoff

Full revision: `SFM_MASTER_SIDECAR_PHASE_B1_1_REVISED_DESIGN.md` (this document summarizes compliance for a
short check, not a fresh full architecture review).

Baseline: HEAD `8b4f0cb54750a5360a9897bb981af5463ab28681`, Master SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`, validator PASS, tests 52 passed.

---

## MUST items — resolution summary

| # | Item | Resolution |
|---|---|---|
| **M1** | Wrapper/path identity | Already resolved by the committed B0.1 core (`82fba35`): the wrapper is an ordinary `Group`, `wrapper_paths` is distinct from `root_paths`. B1.1 stores the wrapper as one ordinary GROUP TABLE row with no special-casing (design §8). |
| **M2** | Source completeness / ambiguous group identity | Already resolved by B0.1: every token is consumed or rejected; duplicate group paths and slash-containing names are grammar errors. B1.1's compiler simply refuses to compile unless `MasterParseResult.ok` (design §3). |
| **M3** | Exact encoding/query contract | Corrected: the stored string pool holds UTF-8 encodings of the *exact parsed token value* returned by `sfm_master_core`, not a copy of raw source bytes. **Further corrected in Phase B1.2:** the tokenizer performs no unescaping at all -- escape spelling (e.g. a literal backslash) is preserved verbatim in the token value, and the compiler adds no escaping/unescaping of its own; the earlier "post-escape-resolution" phrasing was inaccurate and has been retracted (see B1.2). Reader queries/results are UTF-8 byte strings only; a malformed or oversized query is an explicit input error, never `MasterUnknown` (design §4). |
| **M4** | Complete integrity/index validation | Replaced "spot-check" language with an exhaustive, enumerated A–H checklist (header/directory, string table, group table, metadata, occurrences, occurrence-by-group index, fold table, occurrence-by-fold index), each check total over its section, not sampled, designed as chunked/sequential passes (design §17). |
| **M5** | Reader lifetime/failure semantics | `AuthorityUnavailable` (and named subclasses) are now **raised exceptions**, never an ordinary lookup-result value, applying both at open and after successful open. Explicit `close()` idempotency, use-after-close, view-invalidation-on-parent-close, and caller-driven generation-ownership rules (design §19). |
| **M6** | Whole-family bounded-view semantics | Corrected: view coverage is by folded identity, and adding one identity covers its entire fold family (all aliases/destinations/conflict state) — a view can never turn a complete-backing `FoldConflict` into a local `Hit`. `add_path_prefix()` dropped from the initial API pending an actual Normalizer need (design §22). |
| **M7** | Field widths/arithmetic/resource limits | All counts/IDs/ranks widened to u32 by default (removing every former u16 overflow risk); u64 reserved for file-level offsets/lengths. Explicit, generously-set resource limits (source/sidecar byte size, group/occurrence/fold/string counts, per-string length, metadata rows per group, query length) defined separately from raw field capacity; the compiler fails explicitly, before any unsafe allocation, if a value exceeds either (design §15). |
| **M8** | Generation naming/publication corrections | Filename now keyed on the full ordinary sidecar SHA-256 (not a source-SHA prefix); identical-content republication is a safe no-op, and a name collision with *different* content is a hard publication failure — the existing file is never overwritten (design §29, §31). |
| **M9** | Stronger independent inventory oracle | Redesigned from count parity to **ordered content parity**: the oracle independently reconstructs a full ordered event log (group enter/exit, exact control text, metadata tokens, source position) from the raw TXT and separately from the published binary via the runtime reader, and requires exact element-by-element equality — closing the "one control swapped for a duplicate elsewhere, same total count" blind spot explicitly (design §34). |
| **M10** | Runtime integrity dependency boundary | A `runtime_safe/` package (format constants, integrity checks, the reader itself) is defined to import nothing from `sfm_master_core`, the compiler, or any CLI/Python-3-only module — enforced by package structure and checkable by a mechanical import-scan, not left as a convention (design §25, §38). |

All ten items have a concrete design resolution; none remain vague. M4's and M9's *design* is resolved here; their *execution proof* is explicitly deferred to Gate 1 (not re-opened as a design question — the design specifies exactly what Gate 1 must exercise).

---

## SHOULD items — adopted/deferred

| Item | Decision |
|---|---|
| Remove INVENTORY FOOTER | **Adopted.** Completeness is proven externally by Gate 1, never claimed via an embedded summary section. |
| Remove per-fold cached `conflict_flag` | **Adopted.** Conflict is always the validated distinct-destination count, recomputed from the (small, bounded) occurrence range. |
| Remove separate header CRC32 | **Adopted.** One whole-file self-referential SHA-256 (digest field zeroed during its own computation) supersedes it. |
| Flatten child-parent pair table into a single CHILD-ID array | **Adopted.** |
| Reduce four version domains to two (format contract + authority semantics) plus a non-normative compiler-build provenance field | **Adopted**, with explicit rationale recorded for merging parser/fold/hierarchy semantics into one domain rather than keeping them independently versioned (design §18). |
| Generation filename from full sidecar SHA instead of source-SHA prefix | **Adopted** (this is M8, listed here too since it was framed as both a MUST correction and a naming simplification). |

No SHOULD item was rejected outright; where a SHOULD implied a specific mechanism (e.g. lock implementation, backing-mode choice) without enough grounding to decide now, it was scoped as a Gate 2 deferral instead (below), not silently dropped.

---

## Deliberate deviations from a literal reading of the brief

- **`AuthorityUnavailable` as an exception rather than a result-enum member** (M5): the brief asked to "consider" this explicitly; B1.1 makes a definite choice (exception) with stated rationale (categorical difference between "fact about a sound query" and "the provider itself is unusable"), rather than leaving it open. If Astra intended a specific answer here, this is the one place worth confirming rather than assuming agreement.
- **Backing-mode candidates (A/B/C) are described but not narrowed further than B1's original tentative lean** (§21/§37): the brief explicitly says not to choose in B1.1, so B1.1 does not narrow beyond restating "one candidate for Gate 2's first pass" and naming Mode A as the suggested starting point — this is intentionally non-committal, not an oversight.

---

## Remaining unresolved design issues

1. **Normalizer adapter shape** — unavoidably open until the actual contract is reviewed (§38); does not block Gate 1.
2. **Exact stale-lock recovery heuristic** (§32) — described conceptually only, no concrete timeout/PID-check values chosen; deliberately deferred as an implementation-time detail once the lock mechanism itself is built, not a design gap requiring resolution now.
3. **Exact view-cache budget numbers** (§23) — the *shape* of the bound (an explicit, finite budget, LRU or similar) is committed; the *numbers* are explicitly a Gate 2 concern.

None of these three block Gate 1 qualification as scoped in this revision.

---

**Question for Astra:** Does B1.1 faithfully resolve the pre-implementation MUST changes (M1–M10), or is any correction still required before implementation begins?
