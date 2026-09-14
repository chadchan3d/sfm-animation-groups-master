# SFM Master Sidecar — Phase B0 Semantic Core Extraction + Strictness Hardening Audit

Implementation performed within the bounded B0 scope only. No binary sidecar, reader, or provider
implemented. `sfm_defaultanimationgroups.txt` not modified. Nothing staged, nothing committed.

## 1. Files created/changed

| File | Change |
|---|---|
| `tools/sfm_master_core.py` | **New.** Source-agnostic semantic core: `ascii_fold`, `tokenize`, `parse_structure`/`ParseResult` (legacy-shape, byte-for-byte compatible), `parse_master_bytes`/`parse_master_file`/`MasterParseResult` (new rich shape), `Group`, `Occurrence`, `GroupMetadata`/`MetadataEntry`, `FoldFamily`, `build_fold_families`, `GrammarError`, `sha256_of_bytes`. |
| `tools/validate_master.py` | **Modified.** `ascii_fold`/`TOKEN_RE`/`tokenize`/`parse_structure`/`ParseResult` removed and re-imported from `sfm_master_core`; `validate()` extended (additively) to surface the new `grammar_error_count`/`grammar_error` failure kind; `format_report()` extended to render it. No other behavior changed. Net diff: -95/+39 lines. |
| `tests/test_sfm_master_core.py` | **New.** 25 tests covering Part 11.A–H. |
| `tests/test_validate_master.py` | **Unchanged.** All 11 pre-existing tests pass verbatim against the refactored code. |
| `SFM_MASTER_SIDECAR_PHASE_B0_SEMANTIC_CORE_AUDIT.md` | **New.** This report. |

No other file was touched. `tools/verify_phase2_production_order.py` (the pre-existing independent Phase 2 order-verification oracle) was **not modified** — see §13.

## 2. Exact production semantic ownership after refactor

`tools/sfm_master_core.py` is the sole production authority for: ASCII folding, tokenization, grammar-error detection, group/hierarchy construction, control-occurrence collection, metadata presence/value capture, occurrence ranking, and fold-family construction. `tools/validate_master.py` contains zero copies of any of this logic; it imports all of it and adds only validator-specific policy (report formatting, exit codes, warnings about BOM/newline style).

## 3. Validator dependency path

```
tools/validate_master.py
  -> sys.path.insert(tools/)
  -> from sfm_master_core import ascii_fold, tokenize, parse_structure, ParseResult, TOKEN_RE
```

`validate()` calls `parse_structure(lines)` exactly as it did before B0; the function now lives in, and is re-exported from, `sfm_master_core`.

## 4. Authoritative ASCII-fold location

`tools/sfm_master_core.ascii_fold()`. Logic is byte-for-byte identical to the pre-B0 `validate_master.ascii_fold()` (moved, not rewritten). `validate_master.py` no longer defines its own copy.

## 5. Parser/tokenizer location

`tools/sfm_master_core.py`: `TOKEN_RE`, `tokenize()`, `_tokenize_line()`, `_parse_tokens()` (the single hierarchy-construction algorithm), `parse_structure()` (legacy-shape adapter), `parse_master_bytes()`/`parse_master_file()` (rich-shape adapter). Both adapters call the same `_parse_tokens()` — there is one parser, not two.

## 6. Metadata presence result

**Fully preserved, presence-aware.** Confirmed by direct inspection of the live canonical Master (not assumption): exactly three metadata keys are used anywhere in it — `groupColor` (26 occurrences), `selectable` (26), `visible` (2) — verified by a fresh scan of every `"key" "value"` pair in the file before writing any code. The core makes **no closed-world assumption**: any key other than `"control"` is captured generically as metadata, so a custom Master using different keys parses correctly without a code change.

`GroupMetadata.present(key)` returns a real boolean distinguishing "never appeared" from "appeared with a falsy value"; `GroupMetadata.value(key)` returns `None` both for absence and for an ambiguous duplicate (never silently picking a winner) — callers needing to distinguish those two `None` cases use `present()`/`values()`. Verified against the real Master: `RigHelpers` → `selectable` present/`"0"`, `visible` present/`"0"`, `groupColor` absent; `Helpers` → `groupColor` present/`"240 210 255 255"`, `selectable` present/`"0"`, `visible` absent; `RigArms` → `groupColor` absent. Duplicate-key handling verified by a dedicated fixture test (`test_duplicate_metadata_key_not_silently_collapsed`).

## 7. Occurrence-rank result

**Explicit, 0-based, source-order-derived, documented.** Every `Occurrence` carries `global_rank` (0-based index across the whole file, in encounter order) and `local_rank` (0-based index among occurrences sharing the same `full_path`, in encounter order). Verified against the canonical Master: occurrence 0 is `'left'` at `groupFile/Face/Eyes`; occurrence 128,554 (the last) is `'WrinkleTexture'` at `groupFile/Useless`. Duplicate-occurrence handling verified by a dedicated fixture (two occurrences of `"Dupe"` retain distinct ranks 0/1 — never collapsed).

## 8. Malformed-input hardening result

| Case | Pre-B0 behavior | Post-B0 behavior |
|---|---|---|
| Unterminated quoted string | Silently dropped (the stray `"` matched no token; the tokenizer advanced past it with no record) | `GrammarError(kind="unrecognized_content", ...)`; `result.ok is False` |
| Unmatched opening brace / structurally truncated group | Already reported (`unmatched_opens`, `stack_depth_at_eof`) | Unchanged (already correct; still reported the same way) |
| Unmatched closing brace | Already reported (`unmatched_closes`) | Unchanged (already correct) |
| `"{"` not preceded by any name token ("impossible token sequence") | Silently advanced past (`idx += 1`), which could silently corrupt hierarchy attribution for everything nested under the stray brace, because the eventual matching `"}"` would pop whatever frame actually happened to be on top of the stack | `GrammarError(kind="brace_without_name", ...)`; `result.ok is False` |

Investigated (not assumed) before hardening: the live canonical Master has **zero** instances of any of these four cases (verified: zero orphan `WORD` tokens, zero `OPEN` tokens without a preceding name, zero lines with an odd raw quote count). Hardening therefore changes nothing about valid-Master semantics — confirmed by `test_canonical_master_parity` and by the unmodified `validate_master.py` test suite passing unchanged. Six dedicated malformed-input fixtures (unterminated quote, unmatched open, unmatched close, truncated nested group, brace-without-name, and a "this must NOT trip" valid-fixture control) all pass with the expected result.

Documented, intentional grammar boundary (not invented from assumption, but named because the pre-existing tokenizer has always operated line-by-line): a quoted string must open and close on the same line. This was never actually supported before B0 either — a value spanning multiple lines would have hit exactly the same per-line `TOKEN_RE.finditer` call and produced the same silent character loss; B0 makes that boundary an explicit, reported error instead of silent data loss.

## 9. Current Master parity (fresh, independent re-run)

| Check | Result |
|---|---|
| Master SHA-256 | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` (unchanged) |
| Groups | 43 |
| Control occurrences | 128,555 |
| Exact duplicates | 0 |
| ASCII cross-path conflicts | 0 |
| Grammar errors (new) | 0 |
| Validator | PASS |
| Exact literal sequence, rich API vs. legacy adapter | identical (asserted in test) |
| Destination sequence, rich API vs. legacy adapter | identical (asserted in test) |
| Root order (21 root-level taxonomy groups) | `Face, Body Morphs, Sexual Bones, Hair, Clothing, Correctives, Helpers, Body, Arms, Fingers, Legs, Toes, Wings, RigBody, RigArms, RigLegs, RigHelpers, Tail, Attachments, Other, Useless` — matches this project's own independently-verified root order from the Helpers Pass 1H promotion |
| Fold-family count | 124,728 (matches validator's `unique_ascii_fold_keys`) |
| Multi-spelling families | 3,267 (matches validator) |
| Conflicting fold families | 0 (matches validator) |

## 10. Test results

`python -m pytest tests/ -v`: **36 passed, 0 failed** (11 pre-existing `test_validate_master.py`, unmodified and unchanged in behavior; 25 new `test_sfm_master_core.py` covering Part 11.A through H).

## 11. Advanced-user compiler readiness

- **Official-Master assumptions in the core: none.** `parse_master_bytes`/`parse_master_file` take arbitrary bytes/paths; nothing references the official filename, the official SHA, the repository root, Git, or today's counts.
- **Repository assumptions remaining:** none inside `sfm_master_core.py` itself. `tools/validate_master.py`'s `default_master_path()` still hardcodes the official filename, but that is validator/CLI convenience, not core semantics, and a caller can always pass an explicit path (as the existing CLI already supports via its optional positional argument).
- **Custom source path support: yes.** `parse_master_bytes(data, source_name=...)` accepts any bytes; `parse_master_file(path)` accepts any path. Demonstrated by every fixture test in `tests/test_sfm_master_core.py`, none of which touch the canonical Master path except the one parity test that explicitly names it.

## 12. Independent-oracle boundary confirmation

No new production parser was introduced; `_parse_tokens()` is the single hierarchy-construction algorithm behind both the legacy and rich APIs. No new independent Gate-1 inventory oracle was built in B0 (none was required by this phase's scope). The pre-existing `tools/verify_phase2_production_order.py` was **not modified** in this phase; it remains what Phase A identified it as — an independent oracle for an unrelated domain (the Phase 2 semantic-classification processing-batch ORDER, not the Master's physical structure), with its own small, deliberately separate `strict_fold()` implementation. That duplication is intentional independence, not a production-authority conflict, and per the brief's explicit instruction it was left untouched rather than mechanically merged.

## 13. `tools/verify_phase2_production_order.py` disposition

Assessed, not changed. It is not imported by, and does not import, `sfm_master_core` or `validate_master`. Its `strict_fold()` exists to independently re-derive a Phase-2-specific fold-key ordering from first principles and compare it against a stored, SHA-fingerprinted artifact — exactly the checker-independence pattern Phase A's Gate-1 recommendation (its Part 8) is built on. Leaving it untouched preserves that independence; no textual-duplication cleanup was performed against it, per explicit instruction.

## 14. Remaining bounded issues before Phase B1

1. The Normalizer/production-consumer contract remains completely unavailable in this repository (Phase A finding, unchanged by B0; no B0 work depended on it, per instruction).
2. `sfm_master_core.py`'s metadata model has no declared "known key" registry (by design — see §6); a future compiler will need an explicit, documented policy for how it treats an *unexpected* metadata key in a custom Master (accept-and-preserve opaquely vs. reject) — this was flagged as an open question in Phase A and remains open; B0 intentionally did not invent one.
3. `_parse_tokens()`'s "impossible token sequence" hardening currently covers exactly the one case found to matter on inspection (`"{"` without a preceding name). A lone trailing `STR`/`WORD` token that doesn't form a key/value pair or a name/`{` pair is still silently advanced past (this exists in the pre-B0 code too, and zero such cases were found in the canonical Master); this is disclosed as a narrower hardening scope than "every conceivable impossible sequence," not silently left unaddressed.
4. No independent Gate-1 inventory oracle exists yet (Phase A Part 7/8's recommendation); building one remains future work, not started here.

## Safety confirmation

- `sfm_defaultanimationgroups.txt`: unchanged, SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- HEAD: unchanged, `aa77a9199a363f5a783f6e6043b8831f071f39bf`
- `git diff --check`: clean (exit 0)
- `git diff --stat`: `tools/validate_master.py | 134 +++++++------------------ (39 insertions, 95 deletions)` — the only modified tracked file
- Nothing staged (`git diff --cached --name-only` empty), nothing committed
- No binary/compiler/reader/provider implementation begun
- No Normalizer work begun
- No agents or subagents used
