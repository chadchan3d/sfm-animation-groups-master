# SFM Master Sidecar Compiler — Phase A Infrastructure Assessment

Assessment only. No Master edit, no staging, no commit, no implementation performed.

Baseline at time of assessment:
- HEAD: `3487afd5fac95308e1e5f8205593f69e42a34d70`
- Master: `sfm_defaultanimationgroups.txt`
- Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- groups: 43, controls: 128,555, exact duplicates: 0, ASCII cross-path conflicts: 0, validator: PASS (all re-confirmed fresh below)

---

## 1. Executive Verdict

**PROCEED WITH BOUNDED REFACTOR.**

There is no fundamental architectural incompatibility. The repository already contains exactly one authoritative implementation of the grammar/tokenizer/hierarchy parser and exactly one correct ASCII-fold definition, and both are simple enough to factor cleanly. But three real gaps exist that a compiler cannot inherit as-is:

1. **Metadata (groupColor/selectable/visible/etc.) is not parsed into any structure anywhere in this repository.** It is tokenized and deliberately discarded by the only existing parser (confirmed by a passing unit test asserting exactly this). A compiler needs metadata as first-class, presence-aware data — this must be built new, not "reused."
2. **The ASCII-fold function is duplicated, not shared.** It exists verbatim (and correctly) in `tools/validate_master.py` and again in `tools/verify_phase2_production_order.py`, and has been re-implemented ad hoc dozens of times more in this project's own one-off migration scripts. There is no importable single source today.
3. **The tokenizer silently drops malformed quoting** (an unterminated `"`) with no warning and no failure. This is invisible on the current, already-clean canonical Master, but a compiler oracle cannot inherit "silently skip and continue" as its contract.

None of these are architecturally deep. The smallest resolution is a single new shared module (Part 10 below) that both the validator and the future compiler import, built by extending the existing parser rather than replacing it.

There is a fourth, out-of-repository gap: **no production reader/provider/"Normalizer" code exists anywhere in this repository, in any commit, or in any local file.** Part 8's contract questions are unanswerable from local sources and are reported as unavailable, not invented.

---

## 2. Repository / Tooling Inventory

The entire repository contains exactly **4 Python files**, confirmed by a repo-wide search (`find . -name "*.py"`, excluding `.git`/`__pycache__`) and cross-checked against the full commit history (`git log --all --oneline`, 30+ commits inspected, all either Master-content commits or absent any `.py` changes beyond these four):

| File | Role | Relevant to sidecar? |
|---|---|---|
| `tools/validate_master.py` | Read-only structural + native-Rebuild-casefold validator (Section 25 tool) | **Yes — the single authoritative parser/fold implementation** |
| `tests/test_validate_master.py` | Unit tests for the above (11 tests, all passing) | Yes — documents intended parser behavior, including the metadata-exclusion decision |
| `tools/verify_phase2_production_order.py` | Independent SHA-seeded verifier for an unrelated **Phase 2 semantic-classification production ORDER** (a cryptographic processing-batch sequence over 14,282 fold-key families, nothing to do with the Master's physical control ordering) | Only as a second, independent `ascii_fold` implementation (see Part 4) |
| `tools/extract_phase2_human_review.py` | One-off `.xlsx` → `.tsv` extractor for a completed human-review workbook from the earlier Phase 2 project | Not relevant — no parsing/fold/hierarchy logic |

No other directories contain code. `reference/` holds two static data files (the Silkworm reference Master, read-only per CLAUDE.md §1a, and a large external Scanner corpus TSV). `.claude/` contains no files at the time of this assessment. There is no `src/`, `lib/`, `sfm_runtime/`, `provider/`, `normalizer/`, or similar directory. A repo-wide case-insensitive search for `normalizer`, `sidecar`, `T138`–`T149`, `provider.*api`, and `compiler` across `*.py`/`*.md`/`*.txt` returned **zero matches** outside of this very assessment's own future filename.

Mapping the 25 requested inventory items to actual ownership:

| # | Semantic responsibility | Owner today |
|---|---|---|
| 1 | TXT parsing/tokenization | `validate_master.tokenize()` (regex `TOKEN_RE`) |
| 2 | Grammar handling | Same tokenizer; comments (`//...`) and bare words handled inline |
| 3 | Hierarchy construction | `validate_master.parse_structure()` (explicit brace-depth stack) |
| 4 | Canonical group paths | Same function — `full_path` built as `/`-joined stack names |
| 5 | Parent/child group order | Implicit in `result.groups` append order (post-order, on close) + `depth`; not separately modeled |
| 6 | Exact control literal preservation | Same function — literal captured verbatim from the quoted-string token, no transformation |
| 7 | Control occurrence collection | `result.controls`: list of `(literal, full_path, line_no)`, one entry per `"control"` key encountered |
| 8 | Global control ordering/rank | Not an explicit field, but implicit: `result.controls` is appended in token-scan order = file order |
| 9 | Local/group ordering/rank | Not modeled at all; would need to be derived by filtering `result.controls` by `full_path` and re-using file order |
| 10 | ASCII-fold behavior | `validate_master.ascii_fold()` — correct, ASCII-only, single canonical definition |
| 11 | Casefold-family construction | `validate` function's `families` dict, keyed by `ascii_fold(literal)` |
| 12 | Cross-destination conflict detection | Same function's `cross_path` list — flags a fold family with >1 exact spelling AND >1 distinct path |
| 13 | Alias handling | Not modeled as a first-class concept; same-path multi-spelling families are counted but not otherwise structured |
| 14 | Group metadata parsing | **Nowhere.** Tokenized as generic `STR key / STR value` pairs and discarded unless `key == "control"` |
| 15 | Control metadata parsing | **Does not exist as a grammar concept anywhere in this Master format** (controls are bare `"control" "NAME"` pairs; no per-control metadata is ever written) |
| 16 | Metadata presence/absence representation | **Not represented anywhere** — see Part 6 |
| 17 | Malformed-source behavior | Braces: explicit, reported, not repaired. Quoting: silently dropped, unreported (see Part 3) |
| 18 | Unsupported grammar handling | No directive types beyond string-pairs/braces/comments exist to be "unsupported"; unrecognized bare words are tokenized as `WORD` but never consumed into any structure |
| 19 | Master validation | `tools/validate_master.py`, invoked throughout this project's history as the Section 25 tool |
| 20 | Duplicate detection | Same tool — exact-literal duplicates (`by_exact`) |
| 21 | Master SHA/inventory checks | Ad hoc — every migration this session computed `hashlib.sha256` manually in throwaway scripts; no shared helper exists |
| 22 | Release/update tooling | None exists — commits are the only "release" mechanism |
| 23 | Reconciliation/editing tooling used by Claude Code | Entirely one-off scratch Python scripts per task, written fresh each time against CLAUDE.md's contract; no shared editing library exists beyond `validate_master`'s read-only functions being imported for reuse |
| 24 | Generated-artifact workflow | **None exists** — no build step, no compiled output, no manifest, ever, for anything in this repository |
| 25 | Tests | `tests/test_validate_master.py` only; nothing else is tested |

---

## 3. Authoritative Semantic Map

| Semantic fact | Current authority | Location | Representation | Sidecar role | Reason |
|---|---|---|---|---|---|
| Exact literal spelling | `parse_structure` | `validate_master.py:70-124` | Python `str`, verbatim from quoted token | **SHARE** | Already exact, already the single source; re-deriving would risk drift |
| Raw occurrence identity | `parse_structure` | same | tuple `(literal, path, line_no)` in a list | **FACTOR** | Present but untyped/implicit; needs an explicit occurrence record with a stable index for the compiler |
| Canonical destination/path | `parse_structure` | same | `/`-joined group-name string | **SHARE** | Correct and exercised by 3+ years of migrations; no reason to reinterpret |
| Group hierarchy | `parse_structure` | same | stack-based, `result.groups` records `name_line/open_line/close_line/depth` | **SHARE** | Structurally sound, brace-depth based per CLAUDE.md §7's own requirement |
| Parent relationship | `parse_structure` | same | derivable from `full_path.rsplit('/', 1)` | **FACTOR** | Correct but not materialized as an explicit parent pointer; trivial to add |
| Child ordering | `parse_structure` | same | `result.groups` order is close-order (post-order traversal), not declaration order | **FACTOR** | A compiler needs declaration/child order for deterministic tables; must capture `open_line`-based order, not `close_line`-based append order |
| Root ordering | `parse_structure` | same | derivable by filtering `full_path.count('/') == 1` and sorting by `open_line` (used successfully in Pass 1H's own root-order verification this session) | **FACTOR** | Works today via manual post-processing every time; should be a named helper |
| Global control rank | `parse_structure` | same | implicit list-index of `result.controls` | **FACTOR** | Order is preserved, but not exposed as a field; a rename/typed field is all that's needed |
| Local/group control rank | none | — | not modeled | **FACTOR** | Must be computed by filtering global order per path; straightforward, currently done ad hoc per-script |
| Exact ASCII A-Z→a-z folding | `ascii_fold` | `validate_master.py:35-41` | pure function, one line, no Unicode dependency | **SHARE** | Correct, minimal, and independently re-verified this session dozens of times against it — but presently **duplicated**, not centrally imported (see Part 4) |
| Alias/fold-family membership | `validate()`'s `families` dict | `validate_master.py:210-234` | `dict[fold_key -> list[(literal, path, line)]]`, built fresh per validation run, not persisted | **FACTOR** | Logic is correct; needs to be a reusable function returning a typed structure, not inline validator-report code |
| Destination evidence per fold | none | — | not modeled | **INDEPENDENTLY CHECK** | This is Master-external provenance (Silkworm/Scanner), lives only in this session's throwaway TSVs, never in shared code; a compiler has no business inheriting it — it operates on the Master as already-authored |
| Cross-destination conflict state | `validate()` | `validate_master.py:220-244` | boolean-ish: family is in `cross_path` list or not | **SHARE the algorithm, FACTOR the function** | Exactly the invariant Part 4's contract needs; must return a queryable per-fold verdict, not just an all-file report |
| Explicit metadata values | none | — | tokenized and discarded | **must be newly built (not reuse)** | See Part 6 — this is the largest real gap |
| Metadata presence vs absence | none | — | not distinguished from "value is falsy" because it is never retained at all | **must be newly built** | Same |
| Malformed grammar behavior | `tokenize`/`parse_structure` | same | braces: explicit failure with evidence; quoting: silent character skip | **INDEPENDENTLY CHECK required; brace behavior SHARE, quote behavior must change** | See Part 3.E/F |
| Unsupported grammar behavior | `tokenize` | same | unknown bare `WORD` tokens are produced but never consumed into any structure (effectively ignored, not rejected) | **FACTOR (decide + implement an explicit policy)** | No current failure path for "this looks like a directive but isn't `control`" |
| Group count | `parse_structure` | same | `len(result.groups)` | **SHARE** | Trivial, correct, exercised every session |
| Occurrence count | `parse_structure` | same | `len(result.controls)` | **SHARE** | Same |
| Source SHA identity | none in shared code | ad hoc `hashlib.sha256(...)` calls, freshly written every task | plain hex string, never stored anywhere persistent | **FACTOR** | Trivial one-liner; belongs in the shared module so compiler/validator/manifest agree on exactly one hashing convention (whole-file bytes, not normalized text) |

---

## 4. Parser + Grammar Assessment

**A. Is there already one parser that fully represents the supported grammar?**
Yes, for the subset of the grammar that matters to control/hierarchy semantics: `TOKEN_RE` + `tokenize()` + `parse_structure()` in `tools/validate_master.py`. It is the only parser in the repository, has run cleanly against the real 128,555-control Master in every one of this session's ~15 mutation passes, and is unit-tested. It does **not** fully represent the grammar's metadata surface (see D).

**B. Does it preserve exact control spellings without stripping/case-normalizing/Unicode-casefolding/punctuation-normalizing?**
Yes. The quoted-string regex group (`"((?:[^"\\]|\\.)*)"`) captures the literal byte-for-byte (module Python's own UTF-8 decoding of the file, which is lossless for this Master — confirmed BOM-less, UTF-8, no decode failures across the whole project). No `.lower()`, `.strip()`, or Unicode normalization is ever applied to a captured literal. This was independently re-verified this session in the mojibake/kanji carry-along case (`注視TipsParent` vs its corrupted `æ³¨è¦TipsParent` sibling), both of which round-trip through this exact tokenizer untouched.

**C. Does it preserve ordering authority?**
Partially. Token order = file order, and `result.controls`/`result.groups` are built by appending in scan order, so the *information* to reconstruct any ordering is present. But no field explicitly names "this is your rank" — every consumer (including every script in this session) has had to re-derive order from `line_no` or list position by convention. This is a **factoring gap**, not a data-loss gap.

**D. Does it distinguish metadata ABSENT from metadata PRESENT with a false/default-like value?**
**No.** `parse_structure()` tokenizes every `"key" "value"` pair generically; the `if key == "control":` branch is the *only* place a key/value pair is retained. `"groupColor"`, `"selectable"`, `"visible"`, and any other metadata key are read, matched, and discarded (`idx += 2; continue`) without being recorded anywhere. This is deliberate and tested (`test_non_control_metadata_keys_excluded`), correct for the validator's narrow purpose, and a **hard gap for a compiler**, which must know the difference between "this group never had a `selectable` key" and "this group has `selectable "0"`."

**E. Malformed-input behavior:**

| Condition | Current behavior |
|---|---|
| Malformed/unterminated quoting | **Silently dropped.** A lone `"` matches no alternative in `TOKEN_RE` (the bare-word alternative `[^\s"{}]+` explicitly excludes `"`), so `re.finditer` simply never returns a match for that character; there is no warning, no failure, no evidence recorded. |
| Malformed braces | **Explicit and correct.** Unmatched closes are appended to `unmatched_closes`; unmatched opens remain on the stack and are reported via `unmatched_opens`; `stack_depth_at_eof != 0` fails validation with full evidence (line numbers, group names). This satisfies CLAUDE.md §7's "do not repair a missing or misplaced brace merely by making counts balance" — the validator never repairs, only reports. |
| Unsupported directives | There is no directive concept beyond `"key" "value"` pairs, group blocks, and `//` comments. An unrecognized key is not rejected — it is read as a generic pair and discarded, indistinguishable from a known-but-ignored key. |
| Duplicate metadata (e.g., two `groupColor` lines in one group) | **Undetectable today** — because metadata is never retained, "duplicate" is not even representable. Section 6 of CLAUDE.md states the editing *rule* ("exactly one `groupColor`"), but no code anywhere checks it; every enforcement this session has been manual (a human-authored preflight check re-derived per task). |
| Unknown metadata | Same as duplicate — not distinguished from known metadata, because none is distinguished at all. |
| Unexpected tokens | A `WORD` token not immediately followed by `OPEN` or `STR` is simply advanced past (`idx += 1`) with no record. |
| Truncated input | No explicit end-of-file handling beyond the final `stack_depth_at_eof` check; a truncated file mid-quote would trigger the same silent-skip as E's first row for the dangling partial token, and would likely surface only as a **stack_depth_at_eof mismatch** if the truncation also swallowed closing braces (which it would validly report). A truncation that lands cleanly on a brace boundary but mid-way through the *logical* content would currently be indistinguishable from an intentionally short file. |

**F. Does it ever silently skip syntax and continue with a partial parse?**
**Yes — the unterminated-quote case above is a real silent-skip.** Everything else (braces, unmatched pairs) is explicit and fails loudly. This is the one concrete grammar-robustness gap.

**G. Is the parser suitable as the compiler's source oracle as-is?**
For control-literal/hierarchy/fold semantics: yes, as-is, with the caveat in F documented and accepted or closed. For metadata: no — nothing to reuse, must be built new (see Part 6, Part 10).

**H. If not, what is the exact gap, and can it be factored without changing behavior?**
Two gaps, both additive:
1. Metadata capture — a new, separate data structure recorded alongside (not replacing) today's group/control records. Adding it does not change `validate_master.py`'s existing report fields, exit codes, or the 11 passing tests, provided the new capture is optional/additional output from a shared `parse_structure`-equivalent.
2. Malformed-quote detection — one additional check (e.g., scanning for a `"` that opens but is never closed before end-of-line/EOF) that can be added as a new failure class without touching any currently-passing check.

Both are additive, not breaking. No second parser is required if `parse_structure` is extended and shared.

---

## 5. ASCII-Fold + Conflict Authority

**1. Where does the fold function live?** `validate_master.ascii_fold()` (`tools/validate_master.py:35-41`) — a plain function, ASCII A-Z→a-z only, verified against the docstring's own claim: "not Unicode casefold/lower."

**2. Do multiple implementations exist?** **Yes.** A byte-identical reimplementation, `strict_fold()`, exists in `tools/verify_phase2_production_order.py:25-26`. Additionally — disclosed for completeness even though these are not tracked shared code — every one of this session's ~20+ throwaway migration scripts reimplemented the same one-liner locally (`ascii_fold = lambda s: ''.join(chr(ord(c)+32) if 'A'<=c<='Z' else c for c in s)` or equivalent), because no importable module existed to pull it from. All observed copies are logically identical; no drift was found. This is a maintainability/single-source-of-truth risk, not a current correctness bug.

**3. Which implementation is authoritative?** `validate_master.ascii_fold()`, by virtue of being the one attached to the Section 25 tool and covered by tests (`test_ascii_only_fold_pass`, `test_punctuation_distinction_pass`).

**4. How are fold families built?** `validate()`'s local `families = defaultdict(list)` dict, keyed by `ascii_fold(literal)`, populated once per validation run and discarded afterward (never persisted, never exposed as a callable API — it's inline procedural code inside the `validate` function body, not a reusable `build_fold_families()` helper).

**5. How are exact aliases retained?** Every occurrence keeps its own tuple in the family's list; nothing is deduplicated or collapsed at this stage.

**6. How are multiple destinations within one fold represented?** `distinct_paths = set(m[1] for m in members)`; if `len(distinct_paths) > 1` the family is flagged.

**7. How are conflicts reported?** As a `"cross_path_casefold"` failure entry in the validator's report, with every member's literal/path/line enumerated — human-readable text, not a queryable structured verdict a compiler could call per-lookup.

**8. Does an exact spelling currently override a conflicting folded family?** **No — and this matches the required future binary contract.** The validator's cross-path check is unconditional: any fold family touching more than one distinct path is a FAIL regardless of whether one of its exact spellings happens to match a hypothetical query string. There is no "exact match wins" shortcut anywhere in the current logic. Confirmed directly: this session's own Pass 1G/1H work repeatedly treated an exact-spelling match inside a still-conflicted fold family as **still requiring resolution**, never as an automatic pass-through (e.g., the `animroot`/`AnimRoot` case was escalated to human review specifically because one exact spelling's own hard evidence did not settle the conflicting family). **Current infrastructure already obeys the required contract; no behavior change needed here**, only exposing it as a callable per-fold query rather than a whole-file report.

---

## 6. Occurrence + Order Authority

At minimum, per occurrence, current infrastructure **can** supply (with a thin factoring pass, not new logic):

| Need | Available today? | How |
|---|---|---|
| Exact literal | Yes | `result.controls[i][0]` |
| Full destination/path | Yes | `result.controls[i][1]` |
| Global source/order rank | Yes, implicitly | list index `i` of `result.controls` (already file-order because tokens are scanned linearly) |
| Local/group source/order rank | Derivable, not stored | filter by path, keep relative order |
| Duplicate/occurrence identity | Yes | `by_exact` groups every occurrence of one literal; today's canonical Master has exactly 0 with count > 1, but the *mechanism* handles N ≥ 1 correctly (verified this session: the validator's duplicate-count logic was exercised against a live 402→8 RigHelpers repair with zero incidents, and its unit test `test_exact_duplicate_fail` exercises a synthetic duplicate) |
| Fold family | Yes | `ascii_fold(literal)`, then group-by |
| Relevant static metadata/evidence | **No** | not retained (Part 6 gap) |

**Does any current maintenance step collapse repeated exact occurrences or aliases before downstream consumers see them?**
**No.** There is no deduplication step anywhere in this repository's tooling. Every migration this session (Sexual Bones, RigBody reorder, Helpers taxonomy) operated by *moving* lines (remove-old + insert-new, per CLAUDE.md §10), never by collapsing. The validator's duplicate check is purely diagnostic (report-only), never corrective. The canonical Master's current 0-duplicate, 3,267-same-path-family state is a property of careful editing, not of a collapsing pipeline silently hiding pre-collapse data. If a future edit ever *did* introduce a duplicate or a cross-path fold conflict, the validator would surface it and, per CLAUDE.md §25, promotion would be blocked — there is no silent-collapse path for the compiler to worry about inheriting.

**Conclusion:** occurrence/order information is not currently lost or collapsed anywhere; it simply is not yet exposed as an explicit, typed API. This is a **FACTOR**, not a design blocker.

---

## 7. Metadata Semantics

This is the most consequential finding of Phase A.

**Metadata keys actually observed in the live Master** (confirmed by direct inspection during the Helpers migration this session, not assumption):

| Key | Observed scope | Observed values | Separator convention observed |
|---|---|---|---|
| `groupColor` | group-level, first content line after `{` per CLAUDE.md §6 | RGBA quoted string, e.g. `"240 210 255 255"` | exactly two tabs between key and value (verified byte-exact against multiple groups this session) |
| `selectable` | group-level (root groups and nested subgroups both observed, e.g. `RigBody`, `RigHelpers`, `RigArms/LeftArm`) | `"0"` or `"1"` | **exactly one space**, not tabs — verified via `cat -A`-equivalent byte inspection on 10+ instances this session; this differs from `groupColor`'s two-tab convention and is easy to get wrong if inferred rather than checked |
| `visible` | group-level (observed on `RigHelpers` specifically) | `"0"` | same single-space convention as `selectable` |

**Current representation:** none. All three keys are read by the tokenizer as generic `STR`/`STR` pairs and thrown away unless the key literal is exactly `"control"`. There is no code anywhere — validator, tests, or any migration script committed to history — that retains "this group has `selectable "0"`" as data. Every single migration this session that needed to preserve or place metadata correctly (the new `Helpers` group's `groupColor`/`selectable`, confirming `RigHelpers`' pre-existing `selectable "0"` + `visible "0"` survived untouched) did so via **fresh manual byte-level inspection performed inline in that task's own throwaway script**, not by querying any shared authority.

**Presence vs. absence:** Because metadata is not retained at all today, "absent" and "present-with-a-falsy-value" are **currently indistinguishable to any piece of code in this repository** — both simply produce no record. This is exactly the failure mode Part 6 warns against for the future binary ("must NOT silently compile absent → explicit false/default"). Building this distinction correctly requires new capture logic; there is nothing to reuse. The good news: the underlying grammar is simple enough (`"key"` immediately followed by a `STR` value, as a direct group member) that capturing (key, value-or-absent, separator-width, source-line) per group is a small, well-bounded addition to `parse_structure`.

---

## 8. Validator / Independent Oracle Map

| Tool | Classification | What it can independently verify today |
|---|---|---|
| `tools/validate_master.py` | **Shared semantic code** (uses the one authoritative parser/fold) | source occurrence count, group/path count, fold count (`unique_ascii_fold_keys`), alias count (`same_path_multi_spelling_families`), exact destinations (via `full_path`), conflicts (`cross_path_family_count`), malformed-brace behavior |
| `tests/test_validate_master.py` | Shared-code regression suite, not independent of the code it tests | Confirms `validate_master`'s *intended* behavior stays stable across changes; it is not a second implementation, so it cannot catch a bug that exists identically in both the tool and its own test's expectations |
| `tools/verify_phase2_production_order.py` | **Independent parity oracle**, but for an unrelated domain (Phase 2 processing-batch ORDER, a SHA-seeded pseudo-random sequence over semantic-classification fold-key families — not the Master's physical control order) | Demonstrates the *pattern* this project already uses for independent verification (reconstruct from first principles, compare against a stored artifact, verify a stored SHA fingerprint) — directly reusable as a template, not reusable as code |
| This session's ad hoc scripts (not committed as tools) | Neither — throwaway, single-use, never re-run | N/A |

**Is there a sufficiently independent inventory today for Gate 1?** **No.** `validate_master.py` is presently the *only* code that knows how to compute occurrence/group/fold counts; using it as both "the compiler's semantic source" and "the independent oracle" would violate Part 7's own requirement ("Gate 1 must not self-certify merely because compiler and reader agree with each other" — the same principle applies to compiler-vs-oracle).

**Smallest independent inventory needed later:** a second, deliberately separate script that re-derives occurrence count / group count / fold count / cross-path conflicts **from the raw TXT bytes using its own from-scratch tokenizer**, structurally isolated from whatever module the compiler imports — mirroring exactly the pattern `verify_phase2_production_order.py` already demonstrates for a different domain. This is Gate 1's Layer A oracle. No such tool exists yet; none was built in this assessment (only a trivial, already-necessary read-only inspection was performed to answer these questions — no new files, no probes left behind beyond this report).

---

## 9. Normalizer Static-Authority Consumer Seam

**Not available in this repository.** A targeted search (case-insensitive, across `*.py`, `*.md`, `*.txt`, filenames and content) for `normalizer`, `sidecar`, `T138` through `T149`, `provider.*api`, and `compiler` returned zero hits outside artifacts this assessment itself is creating. `git log --all` shows no commit ever touched a file matching those concepts. There is no `.claude/` content, no design doc, no README, no code comment anywhere referencing this consumer.

**Exactly what is unavailable, stated plainly rather than invented:**
- The current provider/API seam the production SFM consumer actually calls
- Its lookup input/output contract
- Its actual alias/fold behavior at the call site (vs. what this Master's own data supports)
- Its actual conflict-result handling
- What ordering data it consumes, if any
- What metadata it consumes, if any
- Its bounded-view (per-model/per-rig) behavior
- Its Master-unknown behavior
- Where it draws the line between static Master facts and contextual/live rig state

None of this can be answered from this workspace. If this contract information exists, it is in a different repository or system not present here, and Phase B planning must either import that repository into this workspace for inspection or obtain the contract from its owner directly — it must not be guessed at from the Master's own shape.

---

## 10. Recommended Shared / Factored Code

A single new module, e.g. `tools/sfm_master_core.py`, extending (not replacing) `validate_master.py`'s existing functions:

1. `ascii_fold(literal)` — **moved** here verbatim; `validate_master.py` and any future compiler both `import` it. Deletes the duplication identified in Part 4.
2. `tokenize(lines)` / `parse_structure(lines)` — **moved** here, extended to additionally record, per group, an ordered list of `(key, value_or_None, line_no, separator_width)` for every non-`"control"` direct-member key/value pair encountered (this is purely additive to `ParseResult`; existing `.groups`/`.controls`/`.unmatched_*` fields and all their current semantics are untouched, so `validate_master.py`'s 11 existing tests keep passing unmodified).
3. `build_fold_families(controls)` — **factored out** of `validate()`'s inline loop, returning a typed mapping fold→family so both the validator and a compiler can call one function instead of two copies of the same 15 lines.
4. `sha256_of_file(path)` — **new**, trivial, but centralizes the hashing convention (whole raw bytes, matching how this session's manual `hashlib.sha256(open(path,'rb').read())` calls have consistently done it) so compiler, validator, and any future manifest agree by construction rather than by convention.
5. `validate_master.py` becomes a thin wrapper: import from `sfm_master_core`, keep its own report-formatting/exit-code logic exactly as-is (Section 25's read-only diagnostic tool does not change externally).

This is the "smallest architectural resolution" called for in the prompt: one new shared module, zero behavior change to the existing validator, zero Master changes, and a real single source of truth for the two facts (`ascii_fold`, `parse_structure`) a compiler must never reinterpret independently.

---

## 11. Proposed Binary Format Family (design candidate, not frozen)

Small versioned binary, shared string pool, explicit tables — matching the repository's actual data shape (one flat 128,555-control, 43-group, ASCII-fold-invariant-respecting Master):

| Section | Purpose | Record fields | Source semantic owner | Ordering | Integrity |
|---|---|---|---|---|---|
| HEADER | format/version identity, source binding | magic, format_version, parser_semantic_version, fold_policy_version, source_sha256, source_byte_length, generation timestamp, table offsets/counts | new (compiler-authored) | n/a | must be checked first, before any other section is trusted |
| STRING POOL | dedup storage for every exact literal, group name, and metadata value string | offset-length pairs into a single UTF-8 blob | `sfm_master_core.parse_structure` literals | insertion order = first-seen | every string reference elsewhere validated in-bounds at load |
| GROUP/PATH TABLE | full hierarchy | group_id, parent_group_id (or root sentinel), name_string_ref, full_path_string_ref (or reconstructable from parent chain), depth, declaration-order rank among siblings, metadata_block_ref | `parse_structure` (extended, Part 10 item 2) | declaration (open-brace) order, not close-brace order — a real correction versus today's `result.groups` append order | parent_group_id must be `< group_id` (acyclic-by-construction) or explicitly root |
| METADATA TABLE | per-group key/value/presence facts | group_id, key_enum, presence_flag, value_string_ref-or-None, separator_width | new capture (Part 10 item 2) | grouped by group_id | presence_flag must never be inferred from value being falsy |
| OCCURRENCE TABLE | every control occurrence, order-preserving | occurrence_id (= global rank), literal_string_ref, group_id, local_rank_within_group, fold_key_ref | `parse_structure` controls (extended with explicit rank fields) | file/global order, exactly as parsed | occurrence_id must be strictly increasing; group_id must resolve in GROUP TABLE |
| FOLD LOOKUP INDEX | sorted folded-key → occurrence-id-list, for O(log n) query | fold_key_string_ref, sorted occurrence_id run, conflict_flag (destination count > 1) | `build_fold_families` | sorted by folded key bytes | binary-searchable; conflict_flag must agree with the number of distinct group_ids among the run |
| VALIDATION/INVENTORY FOOTER | Gate-1-checkable summary counts, redundant with the tables on purpose | group_count, occurrence_count, fold_key_count, cross_path_conflict_count, exact_duplicate_count | derived, redundant by design | n/a | independent oracle (Part 8) recomputes these from raw TXT and compares — this footer existing does not substitute for that recomputation |

This is a candidate shape only; no byte layout or version number is frozen in this phase, per the prompt's explicit instruction.

---

## 12. Proposed Reader API Contract (design candidate)

Minimum distinguished outcomes — never collapsed to `None`:

- `HIT(occurrence_id, group_path, metadata)`
- `FOLD_CONFLICT(fold_key, candidate_group_paths)` — returned even if the query's exact spelling matches one of the conflicting family's members (per Part 4.8's confirmed existing doctrine)
- `MASTER_UNKNOWN(query)` — the folded identity does not exist in this exact generation at all
- `VIEW_UNCOVERED` / `VIEW_NOT_LOADED` — the bounded caller view (a model/rig-scoped subset) was never expanded to include this identity, distinct from the identity being absent from the Master
- `AUTHORITY_UNAVAILABLE` / `INVALID_BACKING` — the binary itself is missing, truncated, wrong version, or fails its source-SHA/policy-version check

Lifecycle to describe explicitly in Phase B design (not implemented here): open+validate generation (header/version/SHA check) → source identity check against the expected Master SHA → exact-then-fold lookup → bounded view construction/expansion for a caller-scoped subset → complete-backing miss handling → conflict handling → corrupt/incompatible backing handling → close/release. The critical invariants to preserve: a bounded-view miss is never reported the same way as a true Master-unknown; a binary-integrity failure is never reported the same way as a Master-unknown; and neither ever silently triggers a TXT-parsing fallback (that would reintroduce the second-parser problem this whole assessment exists to prevent).

---

## 13. Compiler / Runtime Language Split

- **Offline compiler:** modern standalone Python (3.x) is appropriate and requires no new constraint discovery — this repository already exclusively uses modern Python 3 (`pathlib`, f-strings, `argparse`, type-annotation-free but 3-only syntax throughout `validate_master.py` and every migration script this session), and nothing about compiling a static binary sidecar needs SFM's embedded runtime.
- **SFM runtime reader:** must target Python 2.7-era compatibility per the stated constraint; this is a **new, separate codebase** relative to everything in this repository today (no reader code of any kind exists here — see Part 9). It should consume the packed binary with minimal allocation (fixed-width struct reads, not a decoded object graph), independent of the compiler's implementation language.
- **Shared semantic module strategy:** `sfm_master_core.py` (Part 10) is the compiler-side semantic source; it does not need to run under Python 2.7, because the reader never re-parses the TXT — it only reads the already-compiled binary. This cleanly avoids forcing 2.7 compatibility onto the parsing/fold logic.
- **Advanced-user/modeler compiler packaging:** since nothing in this repository currently packages Python tooling for redistribution (no `setup.py`, no `pyproject.toml`, no wheel, no installer of any kind), a standalone compiler for custom-Master rebuilders would need new packaging (e.g., a single-file script with stdlib-only dependencies, matching `validate_master.py`'s own zero-dependency style, or a PyInstaller-style bundle if a GUI/CLI convenience is wanted later). No SFM-embedded-Python requirement should be introduced for this offline step.

---

## 14. File / Manifest / Publication Model

**Current repository convention, confirmed by inspection:** there is no generated-artifact or manifest convention of any kind today. `.gitignore` only excludes `*.tmp`, `*.bak*`, and `__pycache__/`. Every "artifact" produced in this project's history (all the `HELPERS_PASS1*`/`SEXUAL_BONES_*`/`PHASE2_*` TSVs and audits) is a hand-named, one-off, human-readable evidence file, committed selectively and manually — never a build output with a manifest or pointer.

**Proposed for the sidecar** (design candidate, matching the prompt's preferred model, since nothing in-repo already provides an equally-safe simpler mechanism): capture exact TXT bytes → hash → compile → write to a **new, immutable, generation-named file** (e.g. embedding the source SHA or a monotonic generation id in the filename) → validate with the production reader → run Gate 1 parity/inventory → re-confirm source identity unchanged → atomically publish, with a small separate manifest/pointer file (e.g. `sfm_master_sidecar.manifest.json` naming the current generation file and its source SHA) rather than overwriting one mutable binary filename in place. This avoids ever leaving a partially-written binary at a name a reader might already have open, and gives Gate 1 something concrete to point at if a generation fails validation (the bad generation file simply never gets referenced by the manifest).

---

## 15. Joint Master + Sidecar Maintenance Integration Point

**Attach to:** the existing Section 25 validator invocation point — every Master-mutating pass in this project's history already ends with `python tools/validate_master.py sfm_defaultanimationgroups.txt` as a mandatory gate before promotion/commit (demonstrated in every Phase-2-execute step this session, e.g. the Helpers Pass 1H promotion). The natural integration point is: **immediately after a Master edit passes `validate_master.py` and before `git commit`**, a new compile-and-parity step would run, using the *same* just-validated canonical file and its *just-computed* SHA as input — not a separately re-read copy.

**This should not become a second hand-maintained workflow.** Concretely: one new deterministic script (the offline compiler, Part 13) invoked exactly once per approved Master edit, with its own Gate 1 checks, sitting alongside — never replacing — the existing Preflight Approval Gate. Editing the TXT remains entirely the existing CLAUDE.md workflow; compiling the sidecar is a new, separate, fully automatic step that a human never hand-edits.

**Custom Master users** (per Part 13's requirement) would invoke the identical standalone compiler script against their own edited TXT — no SFM installation, no embedded Python, matching how `tools/validate_master.py` already works as a standalone, dependency-free script today.

---

## 16. Advanced-User Rebuild Workflow

Same standalone compiler binary/script as project maintenance uses (Part 13/15) — a modeler who hand-edits their own copy of `sfm_defaultanimationgroups.txt`-shaped content runs the compiler locally against their file, gets a sidecar bound to *their* file's SHA, and the reader's source-identity check (Part 12) naturally refuses to silently treat their custom binary as authoritative for a different Master — it will report a source-SHA mismatch (an `AUTHORITY_UNAVAILABLE`/`INVALID_BACKING`-class outcome), not a silent misattribution.

---

## 17. Gate 1 Qualification Matrix (design plan, not implemented)

**A. Source inventory parity** — a from-scratch, deliberately independent re-tokenizer (not importing `sfm_master_core`) computing occurrence count, group count, path count, fold count, alias coverage, and tail/late-entry coverage directly from the raw TXT bytes, compared against the compiler's own claimed counts and the binary's VALIDATION/INVENTORY FOOTER (Part 11). This is the layer `verify_phase2_production_order.py` already demonstrates the *pattern* for (independent reconstruction + stored-fingerprint comparison), applied to the Master rather than to the Phase 2 batch order.

**B. Full semantic parity** — for every one of the 128,555+ occurrences, compare (exact literal, destination, global rank, local rank, fold family, aliases, conflict state, hierarchy, child order, every supported metadata key, and metadata presence) between the TXT-derived reference (via `sfm_master_core`) and the production binary reader's answers. Full-population, not sampled.

**C. Hand-audited adversarial fixtures** — one fixture per: exact hit; case-variant alias hit; multi-destination fold conflict; an exact spelling that matches inside a still-conflicting fold (must still report conflict, per Part 4.8); a true Master-unknown; a late/tail control (last occurrence in file order); metadata absent; metadata explicit `"0"`; metadata explicit `"1"`; malformed quotes; malformed braces; unsupported/unknown grammar; and any duplicate/odd occurrence pattern the grammar technically permits (even though the current canonical Master has zero of these, the compiler must not assume that always holds for every custom Master it will ever compile).

**D. Invalid-artifact/publication behavior** — truncation, corrupt header, invalid offsets, impossible counts, corrupted string references, wrong format/parser/fold/policy version, wrong source SHA, payload corruption, source mutation mid-build, and interrupted publication must each produce **compilation refusal, sidecar rejection, or "authority unavailable"** — never a silent, successful `MASTER_UNKNOWN`, which would be indistinguishable from a genuinely absent identity and is explicitly the failure mode this whole architecture exists to prevent.

None of this matrix is implemented in this phase; it is a plan to execute once a compiler exists.

---

## 18. Memory / Python-2.7 / 32-bit Risks

No benchmarking performed (per instruction). Principled risks recorded for later Gate 2 review:

- A packed, fixed-width-record binary read via direct offset/struct access (not a decoded Python object graph) is compatible in principle with Python 2.7/32-bit/LAA constraints; this repository's Master is a flat, non-recursive-metadata, ~129k-line text file, so the compiled form's scale is bounded and known (128,555 occurrences, 43 groups, ~124,728 unique fold keys) — there is nothing about its actual size that forces an unbounded design.
- **Avoid:** materializing all 128,555 occurrences as live Python objects (tuples/dicts) simultaneously in the reader process; a giant `dict` keyed by every control name; retaining both a fully-decoded TXT-equivalent graph *and* the binary's own structures concurrently; and any reader-side re-parse of the TXT as a "double check" at runtime (that would defeat the sidecar's purpose and double the resident memory for no benefit).
- **Favor:** the reader treating the binary largely as an mmapped/blob-backed read surface, materializing only the bounded caller-view subset (Part 12) actually requested, not the whole Master, per query.
- The provisional Gate 2 ceilings (~16 MiB incremental resident, ~32 MiB incremental peak) are not proven or disproven here; they are recorded as the target the packed-binary-plus-bounded-view design above is aimed at satisfying, pending actual measurement once a compiler/reader exist.

---

## 19. Open Questions

- What is the actual Normalizer/production-consumer contract (Part 9)? Entirely unknown from this repository; must be obtained externally before Phase B can finalize the reader API (Part 12) with confidence rather than as a plausible-looking guess.
- Should child-group ordering in the binary be declaration-order (open-brace) or the validator's current close-brace append order? This assessment recommends declaration order (Part 11) as the more intuitive/likely-correct choice, but this is a design recommendation, not a confirmed requirement, absent the Normalizer contract.
- What metadata keys, beyond the three observed (`groupColor`, `selectable`, `visible`), might appear in a *different* user's custom Master? The compiler needs an explicit, extensible metadata-key policy (known keys strictly typed, unknown keys preserved-but-opaque, or unknown keys rejected) — this assessment did not find any existing precedent for that decision anywhere in the repository.
- How should the malformed-quote silent-skip gap (Part 3) be resolved — treated as a compiler-refusal condition, or upgraded to an explicit warning that still allows compilation? No existing project precedent settles this either way.

---

## 20. Blockers, If Any

**No hard blocker to *starting* Phase B design/prototyping.** The one item that would block *finalizing* the reader API contract and the metadata-key policy is the unavailable Normalizer contract (Part 9) — proceeding to build a compiler and binary format without it risks designing a reader API that doesn't match what the real production consumer needs, which would have to be redone. This is a **sequencing** blocker for finishing Phase B, not an architectural blocker for beginning it.

---

## 21. Exact Next Implementation Phase

Recommended Phase B scope, bounded to exactly what this assessment justifies:

1. Create `tools/sfm_master_core.py` per Part 10, moving `ascii_fold`/`tokenize`/`parse_structure` out of `validate_master.py` with zero behavior change, extended additively with metadata capture (Part 7) and explicit occurrence-rank fields (Part 6). Re-run `tests/test_validate_master.py` unmodified to confirm zero regression.
2. Add the malformed-quote detection as a new, explicit, reported condition (Part 3.F) inside the same module.
3. Build the independent Gate-1 Layer-A inventory oracle (Part 8) as a second, structurally separate script.
4. Obtain or explicitly escalate for the missing Normalizer contract (Part 9) before finalizing the reader API (Part 12) or the metadata-key policy (Part 19).
5. Only after 1-4: prototype the offline compiler against the binary format candidate in Part 11, and begin the Gate 1 fixture set (Part 17.C).

This assessment does not authorize starting any of the above; it identifies them as the smallest next-justified steps pending explicit authorization.

---

## Safety Confirmation

- Master file: unchanged (not opened for writing at any point in this assessment)
- HEAD: unchanged, `3487afd5fac95308e1e5f8205593f69e42a34d70`
- Nothing staged, nothing committed
- No sidecar/compiler/reader implementation begun; only read-only repository inspection was performed
- No agents or subagents used
