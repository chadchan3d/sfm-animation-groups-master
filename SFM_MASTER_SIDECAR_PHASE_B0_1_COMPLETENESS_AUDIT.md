# SFM Master Sidecar — Phase B0.1 Source-Completeness Hardening + Wrapper/Path-Identity Audit

Implementation performed within the bounded B0.1 scope only. No binary sidecar, compiler, or reader
implemented. `sfm_defaultanimationgroups.txt` not modified. Nothing staged, nothing committed.

## 1. Verdict

**PASS.** All five Astra findings addressed; no stop condition was triggered; the canonical Master
regresses to zero-change parity on every measured fact.

## 2. Files changed

| File | Change |
|---|---|
| `tools/sfm_master_core.py` | Modified. `_parse_tokens` hardened for token-consumption completeness, slash-name rejection, duplicate-group-path rejection, structural (not string-split) parent tracking, and an explicit `declare_order` encounter-rank. `Group` gained `declare_order`; `MasterParseResult` gained `wrapper_paths`. No change to `ascii_fold`, `tokenize`'s line-level scanning, or any B0-era test's expected behavior. |
| `tests/test_sfm_master_core_b01.py` | **New.** 16 tests covering Part 12.A–J plus a dedicated parent-validity test and a full canonical-Master regression test. |
| `tests/test_sfm_master_core.py`, `tests/test_validate_master.py` | **Unchanged.** All 52 tests (36 pre-existing + 16 new) pass. |
| `SFM_MASTER_SIDECAR_PHASE_B0_1_COMPLETENESS_AUDIT.md` | **New.** This report. |

`tools/validate_master.py` was **not** touched in this pass (its B0-era import of `parse_structure`/`ParseResult`/`ascii_fold`/`tokenize` from `sfm_master_core` continues to work unmodified against the hardened core).

## 3. Wrapper Semantics

The wrapper was already modeled as an ordinary `Group` in B0 (confirmed by direct inspection before making any change: `groupFile` already appeared in `result.groups`/`groups_by_path` with `parent_path=None`, its own metadata object, and any wrapper-owned controls correctly attributed). B0.1's contribution is making this **explicit and named**, and closing the one place a custom wrapper name could have been mishandled:

- Added `MasterParseResult.wrapper_paths` — the parentless "document" group(s), distinct from `root_paths` (the taxonomy-root children of the single wrapper, when exactly one exists).
- Verified, by fixture (`WrapperPreservationTests`), that a **custom, non-`"groupFile"`** wrapper name is retained exactly, with its own metadata and wrapper-owned control occurrences correctly attributed, and that nested full paths correctly incorporate the custom wrapper's exact name.
- Confirmed no code path hardcodes the string `"groupFile"` as a semantic constant — `root_paths`/`wrapper_paths` construction in `parse_master_bytes` dynamically discovers whatever the actual parentless group's name is.

## 4. Root / Taxonomy-Root Model

Now explicit and documented via two distinct fields:
- `MasterParseResult.wrapper_paths` — the document/wrapper group(s) themselves (`["groupFile"]` for the official Master).
- `MasterParseResult.root_paths` — the taxonomy-root groups (`Face`, `Correctives`, `Helpers`, ... — 21 for the official Master), i.e. the wrapper's children when exactly one wrapper exists.

If zero or more than one parentless group exists (an unsupported/unusual document shape for the initial compatibility profile), `root_paths` falls back to being identical to `wrapper_paths` rather than guessing at an implicit single wrapper that doesn't exist — this fallback is unchanged from B0 and remains explicitly documented in the source comment, not silently reinterpreted.

Parent relationships are never inferred by splitting `full_path` strings (see §8).

## 5. Token-Consumption Invariant

`_parse_tokens`'s STR/WORD dispatch now recognizes exactly three shapes — name+`{`, `"key" "value"` (both quoted), and `"control" "LITERAL"` (a specialization of the quoted-pair shape) — and every token that does not fit one of these produces a specific `GrammarError`:

| Grammar error kind | Trigger |
|---|---|
| `dangling_token` | A STR/WORD token with no recognizable partner at all (next token is `CLOSE`, or it is the last token) |
| `unquoted_metadata_key` | An unquoted (WORD) key immediately followed by a quoted (STR) value |
| `unquoted_metadata_value` | A quoted (STR) key immediately followed by an unquoted (WORD) value |
| `bare_property_value_pair` | Both key and value unquoted (WORD, WORD) |
| `slash_in_group_name` | A group name containing `/` |
| `duplicate_group_path` | Two groups resolving to the same canonical full path |
| `brace_without_name` | (pre-existing from B0, unchanged) a `{` not attributable to any name |

No case was found, by construction or by fixture, where a non-comment token is silently skipped without one of the above being recorded. `successful parse == all meaningful tokens consumed` is satisfied by design: the STR/WORD branch's final `else` (the `dangling_token` case) is the sole fallthrough, and it always appends an error before advancing.

## 6. Duplicate Group-Path Handling

Two sibling groups (or, more generally, any two groups anywhere that resolve to the same canonical full path) now produce a `duplicate_group_path` `GrammarError` naming both the first and the repeated declaration's line numbers. Neither declaration is dropped, merged, or silently overwritten in the raw evidence (`raw_groups` retains both; `result.ok` is `False`, which is the documented signal that `groups`/`groups_by_path` must not be trusted downstream — consistent with the existing `ok` contract rather than adding a second enforcement mechanism). Verified by `DuplicateSiblingGroupTests`.

This is explicitly **not** the same rule as duplicate CONTROL occurrences, which remain fully representable and unrestricted — verified side-by-side by `DuplicateControlOccurrenceStillAllowedTests` and `CrossDestinationFoldFamilyStillAllowedTests`, both passing with `result.ok is True`.

## 7. Path-Separator Rule

A group name containing `/` now produces a `slash_in_group_name` `GrammarError` at the moment the group is declared (frame-push time), applied uniformly to any group including a hypothetical slash-containing wrapper name. Verified by `SlashInGroupNameTests`. Confirmed, before making this change, that the current official Master contains **zero** group names with `/` (a fresh scan of all 43 group names), so this is a pure compatibility-tightening with no effect on the official Master.

## 8. Parent Validity

Parent relationships are now recorded **structurally**, from the parser's own stack state at the moment a group closes (`parent_path = "/".join(f["name"] for f in stack) if stack else None`, computed *before* popping affects anything downstream) — never by re-splitting the child's own `full_path` string. This was a real, if currently latent, gap: the B0 implementation computed `parent_of` by `full_path.rsplit("/", 1)`, which happened to agree with the structural truth only because no slash-containing names existed; it is now impossible for the two to diverge, because there is only one source of truth. Self-parenting and orphaning are ruled out by construction of the stack itself (a frame's parent is always whatever remains on the stack immediately after that frame is popped). Verified by `ParentValidityTests`.

## 9. Source Encounter Order

Added `Group.declare_order` (0-based, incremented once per group-name token recognized, in true left-to-right token order) as the explicit ordering authority for sibling rank, child order, and the final `groups` list order — replacing `open_line`, which is not a unique ordering key (the grammar permits multiple sibling groups declared on one source line; a same-line tie would previously have silently fallen back to Python's stable-sort preserving *close order*, not true declaration order). `open_line`/`close_line`/`name_line` remain on `Group` as diagnostic fields, no longer as ordering authorities. Verified by `SameLineEncounterOrderTests` (two and three sibling groups declared on a single source line, in both cases resolving to correct left-to-right `sibling_rank`).

Occurrence global/local rank were **already** correct under B0 (built by pure token-scan order, never line-based) and are unchanged — reconfirmed by `CanonicalMasterRegressionTest` and the untouched B0 occurrence-order tests.

## 10. Metadata Consumption

Well-formed metadata (`"key" "value"`, both quoted) continues to be preserved exactly as B0 established — presence-aware, order-preserving, duplicates retained. An **unknown but well-formed** key (anything other than `groupColor`/`selectable`/`visible`) continues to be accepted opaquely and preserved, with no semantic interpretation added — verified by `UnknownWellFormedMetadataTests` (a fictitious `someFutureKey` with two duplicate values, order and duplication both preserved). This is explicitly distinguished from **malformed token structure** (§5/§9's bare-key/bare-value/bare-pair cases), which now fails instead of being silently discarded.

## 11. Official Policy vs. Generic Representability

Kept explicit and tested as two separate axes:

- **Grammar/structural acceptance** (this pass strengthens): a dangling token, a bare property/value pair, a slash-containing name, and a duplicate group path are all now grammar-level rejections — these are facts about whether the *document* is well-formed, independent of any specific Master's content policy.
- **Official taxonomy/content policy** (unchanged, still lives only in `tools/validate_master.py`): duplicate CONTROL occurrences and cross-destination ASCII-fold conflicts remain fully parseable and representable by `sfm_master_core` — `result.ok` is `True` for both — and are rejected, if at all, only by the validator's own separate `exact_duplicate`/`cross_path_casefold` checks, which this pass did not touch. `DuplicateControlOccurrenceStillAllowedTests` and `CrossDestinationFoldFamilyStillAllowedTests` assert this distinction directly.

## 12. UTF-8 / String Semantics

Unchanged and reconfirmed, not redesigned: `parse_master_bytes` strictly decodes as UTF-8, with a UTF-8 BOM stripped via `utf-8-sig` if present; a decode failure raises `UnicodeDecodeError` (unchanged "fatal" behavior). No normalization of any kind is applied to a decoded token's text at any stage. **Correction (identified in Phase B1.2, recorded here for the historical record):** the tokenizer's `(?:[^"\\]|\\.)*` regex construct performs **no unescaping at all** -- `\\.` exists solely so a backslash-quote sequence does not prematurely end the quoted-string match; the captured token value retains every backslash character literally (verified directly: source `"He said \"hi\""` parses to the exact Python string `He said \"hi\"`, backslashes intact, not `He said "hi"`). No correctness problem was found that would justify moving to byte-oriented parsing, so none was made. This is the authoritative behavior `SFM_MASTER_SIDECAR_PHASE_B1_2_FINAL_IMPLEMENTATION_SPEC.md`'s binary string-pool contract builds on.

## 13. Adversarial Fixture Results

All 16 new fixtures in `tests/test_sfm_master_core_b01.py` pass:

| Category | Result |
|---|---|
| A. Wrapper preservation | PASS |
| B. Dangling token | PASS (fails as required) |
| C. Bare property/value form (3 malformed variants + 1 well-formed control) | PASS |
| D. Duplicate sibling groups | PASS (fails as required, no overwrite/merge) |
| E. Slash-containing group name | PASS (fails as required) |
| F. Valid duplicate control occurrences | PASS (still accepted, independently ranked) |
| G. Cross-destination fold family | PASS (still accepted, conflict evidence retained) |
| H. Same-line group structures (2-way and 3-way) | PASS (declaration order correct) |
| I. Unknown well-formed metadata | PASS (preserved, order and duplicates intact) |
| J. EOF / final entry | PASS |
| (additional) Parent validity | PASS |
| (additional) Full canonical-Master regression | PASS |

## 14. Current Master Parity

| Check | Result |
|---|---|
| Master SHA-256 | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` (unchanged) |
| Groups | 43 |
| Controls | 128,555 |
| Fold families | 124,728 |
| Exact duplicates | 0 |
| ASCII cross-path conflicts | 0 |
| Grammar errors (new checks) | 0 |
| Validator | PASS |
| `wrapper_paths` | `["groupFile"]` |
| `root_paths` count | 21 (unchanged order, verified against the same list confirmed in B0/B1) |
| Exact literal sequence, control destination sequence | unchanged (asserted directly in `CanonicalMasterRegressionTest` and indirectly via every B0 parity test still passing) |
| `declare_order` values | strictly increasing, unique, across all 43 groups (verified) |

No stop condition was triggered: the current official Master contains zero slash-containing group names, zero duplicate sibling groups, and the hardening changes zero semantic output for it.

## 15. Test Results

`python -m pytest tests/ -v`: **52 passed, 0 failed** (36 pre-existing across `test_validate_master.py` + `test_sfm_master_core.py`, unmodified; 16 new in `test_sfm_master_core_b01.py`).

## 16. Remaining Semantic-Core Limitations

1. Metadata keys remain fully generic/unvalidated by design (no closed enum) — an intentional B0 decision, reaffirmed here, not a gap.
2. `_parse_tokens`'s dangling-token classification covers the shapes Astra identified plus their generalization (any STR/WORD with no valid partner); it does not attempt to classify every conceivable multi-token malformed run beyond that — a run of N unpaired tokens produces N individual `dangling_token`/paired-malformed errors rather than one consolidated "N tokens of garbage" error, which is more verbose but strictly more informative, not less complete.
3. `wrapper_paths`/`root_paths`'s "exactly one wrapper" assumption remains the only supported compatibility profile for the initial phase, exactly as instructed (Part 3: "If only one document/wrapper shape is supported for the initial compatibility profile, enforce and document that explicitly") — a zero- or multi-wrapper document degrades to treating all parentless groups as both `wrapper_paths` and `root_paths`, not silently reinterpreted as something else.

## 17. Readiness for B1.1 Design Revision

The semantic core's group-identity, parent-validity, and ordering facts are now free of the three concrete gaps Astra identified (string-inferred parents, open_line-based ordering, silent duplicate-path overwrite), plus the general token-consumption-completeness gap. `sfm_master_core.py` remains source-agnostic, repository-agnostic, and official-Master-agnostic — no B0.1-only API was introduced that a future compiler would need to work around; `wrapper_paths`, `declare_order`, and the new `GrammarError` kinds are permanent, documented parts of the same `MasterParseResult`/`Group` shape B1's design already assumed. B1's binary-format design (`SFM_MASTER_SIDECAR_PHASE_B1_DESIGN.md`) referenced `Group.parent_path` and declaration-order-based IDs as inputs; both are now backed by structurally-derived data rather than string-inference, which strengthens rather than invalidates that design — no revision to the binary format itself is required by this pass.

## 18. Git / Safety State

- `sfm_defaultanimationgroups.txt`: unchanged, SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- HEAD: unchanged, `aa77a9199a363f5a783f6e6043b8831f071f39bf`
- `git diff --check`: clean (exit 0)
- Tracked-file diff: none changed in this pass beyond what B0 already modified (`tools/validate_master.py`, untouched again here); `tools/sfm_master_core.py` remains untracked (never committed), so its B0.1 edits do not appear in `git diff` against HEAD
- New untracked file: `tests/test_sfm_master_core_b01.py`
- Nothing staged (`git diff --cached --name-only` empty), nothing committed
- No binary/compiler/reader/manifest/publication-transaction/bounded-view/independent-inventory-oracle implementation begun
- No Normalizer work performed
- No agents or subagents used
