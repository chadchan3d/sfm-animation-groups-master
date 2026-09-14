# SFM Master Sidecar — B1.2 Compliance Closure Summary

Full spec: `SFM_MASTER_SIDECAR_PHASE_B1_2_FINAL_IMPLEMENTATION_SPEC.md` (supersedes B1 and B1.1 for
implementation). This document is the compact closure record.

Baseline: HEAD `8b4f0cb54750a5360a9897bb981af5463ab28681`, Master SHA
`ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`, validator PASS, tests 52 passed.

---

## B1.2a — final sole blocker resolved

Astra's final compliance closure found exactly one remaining blocking defect: the specification's lifetime
contract stated that `close()` on an already-invalidated provider "remains a no-op," which incorrectly
conflated **provider invalidation** (authority use forbidden) with **owned-resource cleanup** (backing
buffer/caches actually released) — two independent facts. An invalid provider may still be holding its
complete packed backing bytes and other resources; invalidation alone does not imply they have been freed.

**Resolved** (full detail in the spec's corrected §23): an explicit three-state model
(VALID → authority permitted, resources held; INVALID → authority forbidden, resources may or may not yet
be released; CLEANED → authority forbidden, resources released) with the critical invariant **`INVALID !=
CLEANED`** stated directly. `close()`'s contract is now complete: idempotent; releases owned resources
whether called from VALID or from INVALID-but-not-yet-cleaned; a harmless no-op once CLEANED; never
restores validity, a view, authority binding, or a stale lazy result. Cleanup may happen either
immediately at the invalidation event or deferred to `close()` — either is permitted, but cleanup is
guaranteed to happen exactly once. A required Gate 1B invalidate→close→close lifecycle test was added,
written to verify whichever of the two permitted cleanup-timing strategies the implementation actually
adopts.

No other section was reopened or reinterpreted.

---

## M1–M10 final status

| Item | Status |
|---|---|
| M1 wrapper/path identity | RESOLVED BY B0.1 (unchanged in B1.2) |
| M2 source completeness / ambiguous group identity | RESOLVED BY B0.1 (unchanged in B1.2) |
| M3 exact encoding/query contract | RESOLVED (B1.1), **wording corrected in B1.2** (§4 — no escape resolution occurs; corrected everywhere it was misstated) |
| M4 complete integrity/index validation | RESOLVED — **all sampling language removed in B1.2**; every §20 check is total over its domain, not a subset. Execution proof remains GATE 1 EVIDENCE (Gate 1A/1B, §38–39). |
| M5 reader lifetime/failure semantics | RESOLVED (B1.1), strengthened in B1.2 (post-open invalidation propagates to the whole provider and all derived views/lazy results), **and fully closed in B1.2a** — invalidation and resource cleanup are now tracked as independent facts (`INVALID != CLEANED`), with `close()`'s complete contract specified and a required Gate 1B lifecycle test added (§23) |
| M6 whole-family bounded-view semantics | RESOLVED (B1.1), unchanged in B1.2 |
| M7 field widths/arithmetic/resource limits | RESOLVED (B1.1), unchanged in B1.2 |
| M8 generation naming/publication corrections | RESOLVED (B1.1), unchanged in B1.2 |
| M9 stronger independent inventory oracle | RESOLVED — **comparison scope corrected in B1.2** to the four semantic projections the binary actually stores (groups/controls/metadata/coverage), not a single interleaved raw event stream the format never claimed to preserve. Tool itself remains GATE 1 EVIDENCE (§37–38). |
| M10 runtime integrity dependency boundary | RESOLVED (B1.1), unchanged in B1.2 |

---

## Astra compliance A–E

| Item | Resolution |
|---|---|
| **A** — M4 exhaustive validation contract | **RESOLVED.** Every "bounded sample"/"where affordable"/"spot-check" phrase removed from the validation section. §20.F now requires `ascii_fold(literal) == owning fold key` checked for **every** occurrence, unconditionally. §20.D adds a strengthened index-slice-partitioning requirement (gapless, non-overlapping, exact ownership agreement) beyond mere bounds-checking. |
| **B** — M5 validated-backing stability | **RESOLVED.** Normative invariant restated without weakening ("the bytes used after validation are the exact bytes that were validated" — same pathname/size/mtime/publisher-convention explicitly declared insufficient). The incorrect mmap-snapshot-guarantee claim is retracted. Candidate A (immutable packed byte buffer) is specified as the only backing built for the first implementation and Gate 1; B/C remain named, unchosen, and must each independently prove the same invariant before ever becoming production candidates. **B1.2a additionally closed the invalidation-vs-cleanup gap** in the same lifetime contract (see the B1.2a section above). |
| **C** — M9 independent-oracle comparison scope | **RESOLVED.** The oracle no longer requires parity of a single interleaved raw event stream. It compares four independently-produced semantic projections (groups: order/names/ancestry/sibling order; controls: global order/exact text/owning group/local rank/multiplicity; metadata: owning group/ordered key-value sequence/multiplicity; coverage: first/middle/tail + total) — each a fact the binary genuinely stores. Source positions are explicitly diagnostic-only, never a required compiled fact. |
| **D** — Initial root-profile compatibility rule | **RESOLVED.** A new compiler-level structural-eligibility gate (`len(wrapper_paths) == 1`, else refusal) sits between `sfm_master_core`'s generic acceptance and any compilation attempt — explicitly generic sidecar compatibility policy, not forced back into `sfm_master_core`, not conflated with official release policy. Zero- and multi-parentless-group fixtures are now explicit required Gate 1 cases. |
| **E** — Gate 1 sequencing | **RESOLVED.** Gate 1 split into 1A (semantic parity)/1B (corruption/integrity)/1C (publication/CLI), with Final Gate 1 requiring all three. The implementation sequence (§45) now builds publication and publisher locking *before* Gate 1C can run, correcting B1.1's inconsistency of describing publication work as following Gate 1's own pass declaration. |

---

## Other corrections applied

- **Escape-preservation wording** corrected in all three affected documents: `SFM_MASTER_SIDECAR_PHASE_B1_1_REVISED_DESIGN.md` (§4's core claim), `SFM_MASTER_SIDECAR_B1_1_ASTRA_COMPLIANCE_HANDOFF.md` (M3 row), and `SFM_MASTER_SIDECAR_PHASE_B0_1_COMPLETENESS_AUDIT.md` (§12) — each now states plainly, with the direct verification behind it (`"He said \"hi\""` parses to `He said \"hi\"`, backslashes intact), that the tokenizer performs no unescaping and the compiler adds none either.
- **Child-index cardinality** corrected to `group_count - parentless_group_count` (verified `43 - 1 = 42` against a fresh parse, formula validated generically, never hardcoded).
- **Directory `row_size` authority** corrected: the file's declared `row_size` is cross-checked against the reader's own normative constant and never used as decoding authority — closes a corruption/adversarial-input surface where a file could otherwise tell the reader to use the wrong field width.
- **Header/directory protection** made explicit: the HEADER and SECTION DIRECTORY are now themselves protected regions in the section-overlap check, not merely checked against each other.
- **Compiler provenance vs. determinism** resolved by removing `compiler_build_version` from the embedded binary entirely (it now lives only in the manifest and CLI output) — determinism now depends on exactly source bytes + two normative versions, with no possibility of a compiler-build field ever influencing output bytes.
- **Metadata absence wording** clarified: `metadata_count == 0` (no metadata at all) is now explicitly distinguished from "a nonempty slice that happens to omit key K."
- **Backing candidate labels** unified to A/immutable packed buffer, B/stable bounded file reads, C/memory mapping, used consistently throughout.
- **Resource-limit wording** clarified: limits prevent *known*-unsafe work; they do not guarantee allocation success, and untrusted counts are validated against both field-width and resource ceilings *before* any allocation sized from them is attempted.
- **Locking contract** clarified: an OS-held exclusive lock is required as the actual ownership mechanism; a bare lockfile-existence convention is explicitly insufficient on its own.
- **Full field-width table** and **explicit cardinality formulas** added as normative references (§16–17 of the final spec) so implementation does not begin with any unspecified width.
- **Expanded Gate 1 fixture catalog** added per the task's explicit lists (structural-corruption cases with both checksum-invalid and checksum-valid-but-structurally-invalid forms; backing/lifetime cases; custom-Master positive/negative cases).

No new architecture was introduced (no database, compression, second production parser, second reader,
live-SFM compiler, source-event-stream section, or generalized caching framework) — this pass is a
consistency correction of the existing, already-confirmed architecture only.

---

## No remaining pre-implementation design defect known

Every item raised by the task (Parts 1–28) has a corresponding correction recorded above or in the full
spec. The following are the only remaining open items, and each is explicitly classified as evidence to
be produced during implementation/qualification, not as an unresolved design question:

| Remaining item | Classification |
|---|---|
| Full §20 A–J validation actually implemented and passing against real and corrupted fixtures | **GATE 1 EVIDENCE** |
| Independent content-parity oracle actually built and agreeing with the reader | **GATE 1 EVIDENCE** |
| Deterministic binary equality across real Python 3 environments | **GATE 1 EVIDENCE** |
| Actual Python 2.7 execution of the reader | **GATE 1 EVIDENCE** |
| Publisher-lock crash-recovery safety under a real simulated crash | **GATE 1 EVIDENCE** |
| Backing-mode choice among Candidates A/B/C | **GATE 2 EVIDENCE** |
| Real SFM string-conversion path and cost | **GATE 2 EVIDENCE** |
| Actual resident/VAS cost, validation latency, generation-overlap cost | **GATE 2 EVIDENCE** |
| View-cache exact budget numbers | **GATE 2 EVIDENCE** |
| Normalizer adapter's exact shape | **BLOCKED ON EXTERNAL CONTRACT**, not a Gate 1/2 evidence item — explicitly does not block Gate 1 |

---

## Final pre-implementation status

A RESOLVED, B RESOLVED, C RESOLVED, D RESOLVED, E RESOLVED. M1–M10 RESOLVED. The B1.2a lifecycle
correction closes Astra's final identified blocker. **No known pre-implementation blocking design defect
remains.** Every item still open is evidence to be produced during implementation/qualification (the
GATE 1 EVIDENCE / GATE 2 EVIDENCE table above), not an unresolved design question.

---

## Safety Confirmation

- Master unchanged, SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- HEAD unchanged, `8b4f0cb54750a5360a9897bb981af5463ab28681`
- validator PASS, tests 52 passed (reconfirmed fresh)
- Nothing staged, nothing committed
- No compiler/reader/sidecar implementation begun
- No agents or subagents used
