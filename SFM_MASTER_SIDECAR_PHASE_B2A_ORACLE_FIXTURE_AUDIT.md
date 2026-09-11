# SFM Master Sidecar — Phase B2A Independent Inventory Oracle + Adversarial Fixture Foundation Audit

Test/qualification infrastructure only. No production binary writer, reader, compiler CLI, manifest,
publisher lock, or Normalizer adapter implemented. `sfm_defaultanimationgroups.txt`,
`tools/sfm_master_core.py`, and `tools/validate_master.py` all unchanged.

## 1. Verdict

**PASS.** The independent oracle agrees exactly with the qualified `sfm_master_core` on the entire
official Master (43 groups, 128,555 controls, 54 metadata entries — every field, not a sample), the
fixture corpus exercises every required category, and the self-discipline tests prove the oracle is not
a mere counter. No Stop Condition (Phase B2A Part 19) was triggered.

## 2. Files created/changed

All new; nothing existing was modified.

| File | Purpose |
|---|---|
| `tests/sidecar/oracle.py` | The independent inventory oracle (hand-written character tokenizer + recursive-descent structural parser) |
| `tests/sidecar/fixture_manifest.json` | Machine-readable manifest, 40 entries (28 valid + 2 unsupported + 10 malformed) |
| `tests/sidecar/fixtures/valid/*.txt` | 28 valid fixtures |
| `tests/sidecar/fixtures/unsupported/*.txt` | 2 core-parseable-but-profile-ineligible fixtures |
| `tests/sidecar/fixtures/malformed/*.txt` | 10 rejection fixtures |
| `tests/sidecar/test_oracle.py` | Oracle self-discipline tests (Part 12) + an independence-boundary smoke test |
| `tests/sidecar/test_fixture_contracts.py` | Manifest-driven contract tests + targeted UTF-8/escape/duplicate/fold-expectation assertions |
| `tests/sidecar/test_official_master_oracle_parity.py` | The single required complete (non-sampled) official-Master parity test |
| `SFM_MASTER_SIDECAR_PHASE_B2A_ORACLE_FIXTURE_AUDIT.md` | This report |

No `sidecar_format.py`, `sidecar_writer.py`, `sidecar_reader.py`, `compiler.py`, `manifest.py`, or
`publisher.py` was created, per explicit instruction. No binary offsets or row layouts appear anywhere in
fixture data.

## 3. Oracle Independence Boundary

`tests/sidecar/oracle.py` contains no `import` or `from ... import` of `sfm_master_core`,
`validate_master`, or any other production module — verified both by direct code review and by a
dedicated AST-based test (`test_oracle_module_does_not_import_production_core`) that parses the module's
own source and inspects its actual import statements (not a naive substring search, which would have
false-flagged the module's own docstring prose discussing `sfm_master_core.py` by name while explaining
the boundary). The oracle uses only the Python 3 standard library (`dataclasses`, `typing`, plus plain
string/byte operations) and is not imported by, and does not import, anything under `tools/`.

## 4. Oracle Lexical/Structural Method

Deliberately different implementation strategy from `sfm_master_core.py`, so a shared blind spot in one
cannot silently hide from the other:

- **Tokenizer**: a hand-written character-by-character scanner (`_tokenize`), not a single compiled
  regular expression matched line-by-line. It independently recognizes quoted strings (same-line-closure
  contract, backslash-escaped-pair-for-termination-purposes-only, no unescaping — matching the documented
  grammar contract, not inventing a different one), `//` comments, braces, and bare words.
- **Structure**: a recursive-descent parser (`_parse_tokens`/`parse_group`) — one Python function
  invocation per nested group — rather than an explicit brace-depth stack consumed by a flat loop over a
  pre-built token list. Groups are appended to the result list in **OPEN order** (naturally pre-order, a
  direct consequence of recursing immediately upon seeing a name+`{` pair), independently reproducing the
  same `declare_order` fact `sfm_master_core` computes via its own, structurally different, iterative
  stack-based approach.
- Malformed input is handled by raising `OracleError` and refusing to produce a projection at all — the
  oracle does not attempt to replicate `sfm_master_core`'s specific `GrammarError` kind taxonomy (per
  Part 2, it must not become a competing malformed-input classifier); malformed fixtures are asserted
  primarily against `sfm_master_core`'s own (already-qualified) error categories.

## 5. Group Projection

`OracleGroup(declare_order, name, ancestry, full_path, parent_path, sibling_index, is_parentless)` — one
record per group, in declaration order. `ancestry` is the tuple of ancestor names root-to-parent (not
including self), independently threaded through the recursion rather than reconstructed after the fact.
Verified exactly against `sfm_master_core.Group` for every one of the official Master's 43 groups (§9).

## 6. Control Projection

`OracleControl(global_order, token, owning_path, local_rank)` — one record per occurrence, in true
encounter order (the list append order during the single recursive traversal). `local_rank` is assigned
in a deliberate second pass, grouping by `owning_path` in encounter order — mirroring
`sfm_master_core.Occurrence`'s own two-concern (global vs. local) rank design without sharing its code.
`literal_multiplicity()` is provided for duplicate-detection assertions. Verified exactly for every one
of the official Master's 128,555 occurrences (§9).

## 7. Metadata Projection

`OracleMetadataEntry(owning_path, local_order, key, value)` — one record per entry, duplicates and order
preserved exactly (never collapsed), via the same encounter-order-then-second-pass-local-numbering
strategy as controls. Verified exactly for every one of the official Master's 54 metadata entries,
across all 42 groups that carry any (§9).

## 8. Coverage Projection

`OracleResult` exposes `group_count()`, `control_count()`, `metadata_count()`, `first_group()`/`last_group()`,
`first_control()`/`last_control()`, and `parentless_groups()` as direct, cheap derivations over the three
projections above — no separate stored "coverage" record is needed, since first/middle/tail/total facts
are all simple slices/counts of data already captured. Source line/column is retained on internal tokens
(`_Tok.line/.col`) purely for `OracleError` diagnostics; it is not part of any projection compared for
parity, per Part 13 of the B1.2 spec ("source positions are diagnostic only").

## 9. Official Master Parity

Run via `tests/sidecar/test_official_master_oracle_parity.py`, complete (not sampled):

| Check | Result |
|---|---|
| `core_result.ok` | `True` |
| Group count | oracle 43 == core 43 |
| Control count | oracle 128,555 == core 128,555 |
| Metadata count | oracle 54 == core 54 |
| Wrapper identity | both report exactly one parentless group, named `groupFile` |
| Group path-set equality | exact match, all 43 |
| Group declaration-order sequence | exact match |
| Per-group name/parent_path/sibling_rank/declare_order | exact match, all 43 (individually sub-tested) |
| Per-group ancestry (oracle's threaded ancestry vs. core's reconstructed parent-chain) | exact match, all 43 |
| Per-occurrence literal/destination/local_rank/global_rank | exact match, all 128,555 |
| Per-group metadata key/value/order | exact match, all 42 non-empty groups |
| Oracle scan runtime | 1.85s |
| Core parse runtime | 1.00s |

**Zero disagreements found.** No Stop Condition triggered.

## 10. Valid Fixture Inventory

28 fixtures (`tests/sidecar/fixtures/valid/`), one per required category (Part 6, items 1–28): minimal
wrapper; wrapper-owned control; wrapper-owned metadata; custom (non-`groupFile`) wrapper name; nested
groups; sibling groups; same-line group declarations; controls before/after a nested child (two separate
fixtures); repeated identical control within one group / across groups; same-fold-same-destination /
same-fold-different-destinations / exact-spelling-inside-conflict (three fold fixtures); duplicate
metadata keys; explicit `"0"` metadata value; unknown-but-well-formed metadata key; empty metadata value;
non-ASCII BMP text; non-BMP (astral-plane, emoji) text; escaped-quote and escaped-backslash spelling
(two fixtures, written via raw bytes so this test file's own Python source cannot silently "fix" them);
meaningful whitespace inside quoted values; BOM and no-BOM sources (byte-identical content otherwise);
final entry immediately before EOF with no trailing newline; 15-level deep nesting; a 30-member alias
family. Every fixture: `sfm_master_core.parse_master_bytes(...).ok is True`, exactly one parentless
group, and oracle/core count agreement — all asserted via `test_valid_fixtures_match_manifest`.

## 11. Profile-Unsupported Fixtures

2 fixtures (`tests/sidecar/fixtures/unsupported/`): `empty_document.txt` (comment-only source, zero
groups, zero parentless) and `multiple_parentless_groups.txt` (two independent top-level groups, two
parentless). Both verified `CORE_PARSEABLE` (`sfm_master_core... .ok is True`) while
`SIDECAR_PROFILE_UNSUPPORTED` (parentless-group count != 1) — the exact distinction Part 7 requires,
asserted by `test_unsupported_fixtures_are_core_parseable_but_profile_ineligible`. `sfm_master_core`
itself was not changed to reject these; the (not-yet-built) compiler's own eligibility gate is what
would refuse them, per the B1.2 spec's §3.

## 12. Malformed Fixture Inventory

10 fixtures (`tests/sidecar/fixtures/malformed/`), each asserted against `sfm_master_core`'s own already-
qualified error categories (`test_malformed_fixtures_are_rejected_by_core`):

| Fixture | Result |
|---|---|
| `duplicate_sibling_group_path.txt` | `grammar_errors` kind `duplicate_group_path` |
| `slash_in_group_name.txt` | `slash_in_group_name` |
| `dangling_quoted_token.txt` | `dangling_token` |
| `malformed_bare_property_value.txt` | `bare_property_value_pair` |
| `unterminated_quote.txt` | `unrecognized_content` + `unquoted_metadata_value` (see note below) |
| `malformed_utf8.txt` | `UnicodeDecodeError` raised at the decode stage, before grammar parsing |
| `unmatched_opening_brace.txt` | `stack_depth_at_eof > 0`, `unmatched_opens` non-empty (no `grammar_errors` entry — a structural, not lexical, failure) |
| `unmatched_closing_brace.txt` | `unmatched_closing_brace` |
| `incomplete_key_value_pair.txt` | `dangling_token` |
| `trailing_unconsumed_token.txt` | `dangling_token` |

**Note on `unterminated_quote.txt`**: the observed classification is `unrecognized_content` (the stray
opening `"` itself) followed by `unquoted_metadata_value` (the remaining bare word being read as an
unquoted value for the preceding `"control"` key) rather than a single dedicated "unterminated string"
kind. This is a genuine, correct rejection (`core.ok` is `False`, exactly as required) via a legitimate
cascading classification of the qualified B0.1 tokenizer's existing error vocabulary — not a defect, and
not something this phase changed or needs to change (Part 8 explicitly forbids expanding the production
error taxonomy in B2A). Recorded here for transparency rather than silently asserting a specific error
string that happened to match without explaining why it's two kinds, not one.

## 13. UTF-8 / Escape Fixtures

Six targeted tests in `UtfEscapeFixtureTests`, each comparing source bytes → oracle token → core token
for exact equality, with expectations computed directly from the raw fixture bytes (not typed as escaped
Python string literals in the test file itself, to rule out this test file's own source-escaping
accidentally "fixing" what's under test):

- Escaped quote spelling (`He said \"hi\"`) round-trips with backslashes intact in both oracle and core.
- Escaped backslash spelling (`C:\\Path\\To\\Thing`) round-trips with backslashes intact.
- Non-ASCII BMP text (kanji) round-trips exactly in both a group name and a control literal.
- Non-BMP text (an emoji, exercising 4-byte UTF-8) round-trips exactly.
- BOM and no-BOM sources (byte-identical content otherwise) produce identical projections in both
  oracle and core.
- Embedded double-space and embedded-tab whitespace inside quoted literals is preserved exactly.

All six pass; oracle and core agree with each other and with the raw-byte-derived expectation in every
case.

## 14. Fold-Semantic Expectation Fixtures

Four tests in `FoldExpectationFixtureTests`, using `sfm_master_core.build_fold_families` directly (the
oracle itself makes no fold claims, per Part 4 — `oracle.ascii_fold_for_test_fixtures` exists solely to
let test code state its own expectations without hand-computing folded keys):

- Same-destination alias family (`Foo`/`foo`/`FOO`): `is_conflict` is `False`.
- Cross-destination alias family (`Bar`/`bar`, two destinations): `is_conflict` is `True`.
- Exact spelling inside a conflicting family (`Baz`/`baz`/`BAZ`, three destinations): the family remains
  `is_conflict == True` even though one member's exact spelling is present — the fixture exists precisely
  so a future writer/reader test can exercise "query the exact spelling that's inside a still-conflicting
  fold" and assert `FoldConflict`, never a silent `Hit`.
- The 30-member large alias family: `len(exact_spellings) == 30`, `is_conflict` is `False`.

## 15. Oracle Self-Discipline Tests

Five required cases (Part 12), all passing, each proving the oracle detects a real semantic change that
a count-only comparison would miss:

- **A** (remove a middle control): control count changes from 4 to 3, and the literal sequence changes.
- **B** (replace a middle control with a duplicate of another, total count unchanged): count stays 4 in
  both baseline and mutated versions, but the literal sequence differs, the omitted literal ("Second") is
  no longer present, and the duplicated literal's multiplicity becomes 2 — proving the oracle would catch
  exactly the "one control swapped for a duplicate elsewhere" case the B1.2 spec's independent-oracle
  design (§37) was built to close.
- **C** (reorder two metadata entries within one group): the ordered `(key, local_order)` sequence
  changes while the unordered set of `(key, value)` pairs stays identical — proving order, not just
  content, is independently captured.
- **D** (swap the declaration order of two sibling groups): the declaration-order name sequence changes
  while the set of names stays identical.
- **E** (remove the final/tail group+control): `last_control().token` changes from `"Fourth"` to
  `"Third"`, and the group count decreases — proving tail coverage is genuinely tracked, not just a total
  count.

## 16. Test Results

`python -m pytest tests/ -q`: **81 passed, 0 failed** (52 pre-existing, unmodified in behavior, plus 29
new B2A tests: `test_oracle.py` 6, `test_fixture_contracts.py` 16, `test_official_master_oracle_parity.py`
7). 121 subtests passed within those 29 (per-group/per-fixture `subTest` breakdowns). No regression from
the 52 pre-B2A tests.

## 17. Performance

Official-Master full-parity test: oracle scan **1.85s**, core parse **1.00s**, total test-file runtime
**~3.0s** including all per-group/per-occurrence/per-metadata subtests. Comfortably practical on a normal
development machine, well under the generous 30-second guard assertion included in the test itself
(`test_runtime_is_practical`) to catch a future accidental O(n²) regression rather than to prove any
specific performance target.

## 18. Remaining Limitations

1. The oracle's malformed-input handling is intentionally coarse (raise `OracleError`, refuse to produce
   a projection) rather than replicating `sfm_master_core`'s specific error-kind taxonomy — this is by
   design (Part 2: the oracle must not become a competing malformed-input classifier), not an oversight.
2. The oracle does not independently re-derive ASCII-fold family/conflict evidence (Part 4 explicitly
   scopes this out); fold-expectation fixtures (§14) are verified directly against
   `sfm_master_core.build_fold_families`, which is the correct qualified authority for that fact, not a
   gap in the oracle.
3. Fixture coverage is deliberately modest in scale (a 30-member alias family, 15-level nesting) rather
   than stress-scale (thousands of aliases, hundreds of nesting levels) — sufficient to prove the
   *mechanism* works and to seed later writer/reader tests, not intended as a performance/scale stress
   suite (that remains Gate 1/Gate 2 territory per the B1.2 spec).
4. `tests/sidecar/fixtures/malformed/malformed_utf8.txt` is rejected at the Python `bytes.decode` stage,
   before `sfm_master_core`'s own grammar-error machinery ever runs — correct and expected, but it means
   this specific fixture never produces a `GrammarError` object to inspect, only a raised
   `UnicodeDecodeError`, which the test suite accounts for explicitly rather than papering over.

## 19. Readiness for B2B

The oracle, fixture corpus, and manifest together give the future binary writer/reader implementation
(B2B and beyond) a pre-proven, independently-verified ground truth for: exact literal/order/ancestry
preservation on the real Master; the full valid/unsupported/malformed fixture matrix required by the
B1.2 spec's Gate 1 fixture catalog (§41); and concrete fold-conflict expectation fixtures ready to be
exercised against an actual `FoldConflict`/`Hit` reader response once one exists. No additional oracle or
fixture-corpus work is identified as a prerequisite for beginning B2B's writer/format implementation.

## 20. Git / Safety State

- `sfm_defaultanimationgroups.txt`: unchanged, SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- `tools/sfm_master_core.py`: unchanged (byte-for-byte, confirmed via `git diff --stat`, empty)
- `tools/validate_master.py`: unchanged (same confirmation)
- No production sidecar module (`sidecar_format.py`/`sidecar_writer.py`/`sidecar_reader.py`/`compiler.py`/
  `manifest.py`/`publisher.py`) created
- `git diff --check`: clean
- Nothing staged, nothing committed
- No agents or subagents used
