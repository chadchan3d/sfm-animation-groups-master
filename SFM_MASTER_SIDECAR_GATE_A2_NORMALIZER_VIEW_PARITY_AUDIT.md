# SFM Master Sidecar — Gate A2: Exact Normalizer Consumer-View Parity

Read-only consumer-semantic qualification only. No production Normalizer code modified, no production sidecar
reader/writer/compiler code modified, no Normalizer integration, no bounded production provider, no
Candidate B/C, no native Rebuild, no model mutation, no Master change, no binary format change, no format v1
freeze, no performance conclusion. Nothing committed until this document's own checkpoint gate authorizes it.

## 1. VERDICT

**FORMAT SEMANTICALLY SUFFICIENT FOR NORMALIZER.** The current sidecar binary contains every static Master
fact the real, currently-deployed `parse_targeted_master()` consumer contract needs, and a test-only
sidecar-derived compatibility-view producer reproduces that exact contract — same top-level keys, same
`mapping_count`/`destination_count` (global, unscoped), same per-fold occurrence order/literal/destination/
rank facts, same group hierarchy and sibling order, same narrow 4-key metadata projection, same
`master_lookup`/`validate_master_subset_conflicts` behavior including exception parity — across four official-
Master workloads (single/medium/large/disjoint-late scopes), eleven adversarial custom-Master fixtures, and an
explicit coverage-vs-`MasterUnknown` proof. 145 of 149 individual assertions passed; the remaining 4 were a
test-harness comparison artifact (Section 15), not a product discrepancy — traced to source and corrected in
analysis, with the real underlying behavior (both sides complete without raising) independently confirmed.
Two required conversions were identified and are **not format changes**: wrapper-path stripping and a narrow
4-key metadata projection (Section 17). One pre-existing, dormant discrepancy between the Normalizer's own
independent TXT tokenizer and `sfm_master_core`'s tokenizer (backslash-escape resolution) was discovered and
is reported honestly (Section 19) — it does not affect the real official Master, which contains zero
backslash characters, and was therefore deliberately excluded from this gate's comparison scope rather than
silently glossed over.

## 2. PURPOSE / CONSUMER ORACLE

The proposition under test: the CURRENT sidecar binary contains all static Master information needed to
reproduce the Normalizer's CURRENT scoped authority contract exactly, without changing the Normalizer's
downstream semantics. The Normalizer's own `parse_targeted_master(master_path, wanted_folds,
validate_conflicts=False)` is the consumer oracle — the sidecar is explicitly NOT the oracle here; it is the
thing being checked against that oracle's real, current, unmodified behavior.

## 3. BASELINE IDENTITIES

- HEAD before and after this task: `24a337a66673c2a9c496225f171378ce427d9520` — verified, matches expected,
  subject "Reject malformed sidecar query encoding".
- Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` — verified.
- Official sidecar: 9,506,244 bytes, SHA-256
  `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` — verified via fresh recompile.
- Reader SHA-256: `c0ed4250cfe13b892e54baf0538ee3bab946f000f20466d5c4da5b15c60bf2a9` — verified.
- `git status`: no tracked modifications before this task began. Nothing staged.

## 4. CURRENT NORMALIZER SOURCE

Exact source path inspected:
`E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py`
(13,594 lines; header docstring confirms "RUN TYPE: MAIN MENU SCRIPT", "MUTATION STATUS: MUTATING PRODUCTION
CANDIDATE"). Exact function line ranges confirmed by direct inspection (not assumed from any prior report):
`ascii_fold` (659–671), `stream_tokens` (1204–1339), `parse_targeted_master` (1416–1724),
`validate_master_subset_conflicts` (1726–1764), `master_lookup` (1767–1824), plus their pure dependencies
`to_unicode` (647–657), `ProbeError` (604–605), `BufferedChars` (1169–1202), `parse_master_bool_text`
(1340–1370), `parse_master_rgba_text` (1373–1413). **The methodology report's line numbers were not assumed
to still be exact and were independently re-located in this pass; the current source's logical contract
matches what the report described.** The module unconditionally imports `sfmApp`, `sfmClipEditor`, `vs`, and
`PySide` at top level, and its final line (`StartRebuildControlGroups()`) begins a real, mutating rebuild
scope-selection flow — this file was therefore never `exec`'d wholesale; only the exact byte ranges of the
pure, read-only functions above were extracted (Section 7) and executed inside real embedded Python 2.7,
their natural, qualified runtime.

## 5. EXACT MASTER_VIEW CONTRACT

Established from the actual current source, not inferred from the sidecar's design:

| Field | Type | Semantics |
|---|---|---|
| `mapping_count` | `int` | **GLOBAL** total control-occurrence count across the WHOLE file — incremented for every control regardless of `wanted_folds` |
| `destination_count` | `int` | **GLOBAL** count of distinct destination paths owning ≥1 control — also unscoped |
| `folded` | `dict[unicode, list[dict]]` | per requested folded key, a list of `{"literal": unicode, "destination": unicode, "global_index": int, "local_index": int}`, in **original file/stream order** — ONLY for folds in `wanted_folds` |
| `exact_literals` | `set[unicode]` | literal strings actually seen, **scoped** to `wanted_folds` only |
| `group_sibling_order` | `dict[unicode or u"<ROOT>", list[unicode]]` | children of each group (or of the wrapper, under the literal key `u"<ROOT>"`), in first-declaration order |
| `group_metadata` | `dict[unicode, dict]` | keyed by group path; **narrow projection of exactly 4 known keys** (`groupColor`, `selectable`, `visible`, `snappable`) — any other metadata key is silently discarded; duplicate declarations of any of the 4 known keys within one group **raise `ProbeError`** |

`global_index`: a running counter across ALL controls in the whole file (0-based) — identical in meaning to
the sidecar's OCCURRENCE TABLE row index (`global_rank`, "row index IS global_rank" per the final format
spec). `local_index`: a running counter per destination (0-based) — identical to the sidecar's `local_rank`.
**Path convention difference, identified explicitly (not silently normalized away):** the oracle's own
`stack`-based paths are **wrapper-EXCLUSIVE** (e.g. `u"Face/Eyes"`), built by never pushing `"groupFile"`
itself onto `stack`; the sidecar's own paths are **wrapper-INCLUSIVE** (`u"groupFile/Face/Eyes"`). The
required conversion is an exact prefix strip of `wrapper_name + u"/"` (Section 6/17). Wrapper-owned controls
(if any existed) map to the empty string `u""` in the oracle's model — reproduced exactly, not approximated.
The oracle also **hard-requires** the literal wrapper name `"groupFile"` (`if take() != "groupFile": raise
ProbeError(...)`) — a real, current scope limitation of the Normalizer's own contract (satisfied trivially by
the real official Master, which does use `"groupFile"`).

## 6. SIDECAR FACT MAPPING

| Normalizer field | Sidecar source | Conversion required | Lossless |
|---|---|---|---|
| `literal` | `iter_occurrences()["literal"]` (already-decoded unicode) | none | Yes |
| ASCII fold | recomputed via the identical character-level algorithm (`ascii_fold_unicode`) applied to the decoded literal | none (proven equivalent to the sidecar's own byte-level `ascii_fold_bytes` per the final spec's ASCII/UTF-8 proof) | Yes |
| `destination` | `iter_occurrences()["full_path"]` | strip wrapper prefix | Yes |
| `global_index` | `iter_occurrences()["global_rank"]` | none (identical meaning) | Yes |
| `local_index` | `iter_occurrences()["local_rank"]` | none (identical meaning) | Yes |
| complete fold family | `lookup_fold()`/full enumeration — every occurrence sharing a fold key | none | Yes |
| `exact_literals` | scoped subset of `iter_occurrences()["literal"]` | filter by `wanted_folds` | Yes |
| group hierarchy | `iter_groups()["parent_path"]`/`["full_path"]` | strip wrapper prefix; skip the wrapper's own row | Yes |
| sibling ordering | `iter_groups()` row order (== `declare_order`, monotonic with `sibling_rank` per §20.C) | none | Yes |
| metadata presence/value | `iter_metadata(path_id)` | filter to the 4 known keys; duplicate-of-known-key → raise (matching oracle) | Yes (generic store is a superset; narrowing is the correct, documented projection, not data loss) |
| `mapping_count` | `occurrence_count()` | none (both already global/unscoped) | Yes |
| `destination_count` | distinct `full_path` values across ALL occurrences | strip wrapper prefix before counting distinctness | Yes |

**No required Normalizer fact was found unavailable from the existing binary.** No fact was invented from
model/DME state — every field above is drawn directly from the sidecar's own generic, already-qualified
structural facts.

## 7. TEST-ONLY COMPATIBILITY PRODUCER

`gate_a2_compat_producer.py` (this session's scratchpad; never placed in `tools/sfm_master_sidecar/` or any
production Normalizer path). Uses the current, unmodified, eager `reader.SidecarReader` (bytes/path open,
`iter_groups`/`iter_occurrences`/`iter_metadata`) exactly as already qualified — no optimization, no bounded
materialization, per this task's own explicit instruction. `build_compatibility_view(provider, wanted_folds,
ProbeError)` returns the exact dict shape of Section 5, reusing the caller-supplied `ProbeError` class (itself
extracted byte-for-byte from the real Normalizer source, Section 4) so that error-type parity is meaningful,
not merely "some exception". `compat_master_lookup`/`compat_validate_master_subset_conflicts` mirror the real
`master_lookup`/`validate_master_subset_conflicts` functions' logic exactly, for Part 11's existing-consumer-
function parity requirement.

## 8. TYPE / ENCODING BOUNDARY

| Field | Normalizer oracle type | Sidecar raw type | Compatibility-view type |
|---|---|---|---|
| `literal` | `unicode` (Py2)/`str` (Py3), via `to_unicode()` (strict UTF-8, `latin-1` fallback only on failure) | already `unicode`/`str` (reader's own eager `raw.decode("utf-8")`, strict) | same, no conversion needed |
| `destination` | `unicode`, `/`-joined stack | `unicode`, wrapper-inclusive | wrapper-prefix strip only |
| query bytes at the reader boundary | n/a (oracle never queries the sidecar) | UTF-8 bytes only (Gate A1's own strict-decode boundary) | n/a — the compatibility producer never calls `lookup_fold` with anything but already-decoded unicode re-encoded consistently via `ascii_fold_unicode` on the unicode value directly |

**No replacement decoding, `errors="ignore"`, Unicode casefolding, or implicit locale decoding was used
anywhere.** The generic reader contract (strict UTF-8 query bytes, Gate A1) was not rewritten; all consumer-
specific adaptation (wrapper stripping, narrow metadata projection, dict/view construction) lives entirely in
the test-only compatibility producer, exactly where Part 10 requires it to live.

## 9. SINGLE-TARGET PARITY

**No historical "Fox" `wanted_folds` capture artifact was found** in the repository or the SFM install
(searched: `usermod/scripts` tree for exported fold/vocabulary files, Character Preset probe scripts for
inline `wanted_folds` literals — none found; Character Preset scripts reference "Kaitlyn" etc. only as live
animation-set names in mutation-based tests, never as a static exported vocabulary). Per this task's own
fallback instruction, a **real, exact, current substitute** was used instead: the official Master's own
`Fingers` group — **216 real occurrences/folds**, close in scale to the historical ~208 figure, drawn directly
from the actual, current, canonical Master (never invented).

- Parity result: **PASS** — full structural comparison (Section 14) passed on every field; consumer-function
  parity (Section 15) passed (behavioral, corrected).

## 10. MULTI-TARGET PARITY

**No historical six-target (Kaitlyn/Ayane/Tifa/Lola/Ruby/Vortex) vocabulary capture was found** either (same
search, same result). Substitute: six real, distinct top-level Master groups —
`Correctives ∪ Attachments ∪ RigBody ∪ RigArms ∪ RigLegs ∪ RigHelpers` — **union of 417 real folds**
(298+45+36+17+13+8, before de-duplication of shared folds across groups; distinct-fold-count as actually
computed by both sides matched exactly, Section 14).

- Parity result: **PASS.**

## 11. LARGE-SCOPE PARITY

**No historical ~800-fold ("T66") capture was found or reused.** Per this task's own instruction not to force
a historical number, a real, current, substantial scope was built instead: `Body Morphs ∪ Sexual Bones ∪
Arms` — three real top-level groups totaling **21,989 real occurrences** in the actual current Master (8,521 +
7,196 + 6,272). This is reported as the actual current number, not adjusted to match any historical figure.

- Parity result: **PASS** — full structural comparison passed at this scale, including exact per-fold
  occurrence-list ordering across thousands of rows.

## 12. DISJOINT / LATE-VOCABULARY PARITY

Scope: `Legs ∪ Tail` (real groups, disjoint from every other workload above) plus one deliberately-constructed
genuinely-absent literal (`"Gate_A2_Genuinely_Absent_Literal_Sentinel_999"`, folded and added to
`wanted_folds`). Newly-uncovered-relative-to-Section-9 fold count: the `Legs`/`Tail` groups' own real fold
vocabulary (not separately re-tallied here beyond the deep-comparison pass, Section 14, which covers it in
full). Composition: known real folds (from two groups never used in any other workload) + one genuinely
absent fold. Real non-ASCII literals ARE present in the actual current Master (587 non-ASCII literals found
by direct scan) — none happened to fall within `Legs`/`Tail` specifically, so non-ASCII coverage for this gate
came from the adversarial fixture matrix instead (Section 13), which is where Part 7D's own conditional
wording ("if supported by fixture evidence") anticipates it may need to come from.

- Parity result: **PASS**, including the absent-literal case (Section 16).

## 13. ADVERSARIAL CUSTOM-MASTER PARITY

Eleven cases (Part 8's ten plus one directly-useful bonus already implied by Gate 1's own fixture corpus),
all against the real, unmodified oracle and the real, unmodified corrected reader — no new fixture framework
built; ten of eleven reuse existing, already-qualified sidecar fixtures verbatim, one small custom fixture
(`gate_a2_metadata_present_fixture.txt`, this session's scratchpad only) was added for the one case (clean,
single, present metadata value) no existing fixture happened to cover cleanly:

| Case | Fixture | Result |
|---|---|---|
| 1. Same-destination ASCII aliases | `12_same_fold_same_destination.txt` | **PASS** |
| 2. Cross-destination fold conflict | `13_same_fold_different_destinations.txt` | **PASS** |
| 3. Exact spelling inside conflicting family | `14_exact_spelling_inside_conflicting_fold.txt` | **PASS** |
| 4. Duplicate occurrences (one group) | `10_repeated_identical_control_one_group.txt` | **PASS** |
| 5. Metadata explicitly present | `gate_a2_metadata_present_fixture.txt` (new, scratch-only) | **PASS** |
| 6. Metadata omitted | `06_sibling_groups.txt` | **PASS** |
| 7. Non-ASCII valid UTF-8 literal | `19_non_ascii_bmp_text.txt` | **PASS** |
| 8. Valid absent query | (any fixture + absent literal — covered directly in every workload, Section 16) | **PASS** |
| 9. Wrapper/hierarchy ordering | `05_nested_groups.txt` | **PASS** |
| 10. Multiple sibling groups/order | `06_sibling_groups.txt` | **PASS** |
| Bonus: duplicate KNOWN metadata key (both sides must raise) | `15_duplicate_metadata_keys.txt` | **PASS** (both raised `ProbeError`, exception-type parity confirmed) |
| Bonus: unknown metadata key (both sides silently ignore) | `17_unknown_metadata_key.txt` | **PASS** |

**All 11 cases: PASS.** The official Master's own 0-cross-path-conflict property (correctly noted as
insufficient on its own) is directly compensated for by cases 2/3/Bonus-1 above.

## 14. COMPLETE STRUCTURAL VIEW COMPARISON

For every one of the 4 official-Master workloads and 10 successfully-completing adversarial cases (the 11th,
`duplicate_known_metadata_raises`, correctly raised on both sides instead of returning a view — Section 13),
the full comparison covered: top-level key set equality; `mapping_count` exact equality; `destination_count`
exact equality; `exact_literals` exact set equality; `folded` key-set exact equality; **per-fold, row-by-row
exact equality of literal/destination/global_index/local_index, in original order** (no sorting was used to
conceal any ordering difference); `group_sibling_order` exact dict/list equality (order-sensitive); and
`group_metadata` exact path-set and per-field value equality. **Every one of these checks passed on every
workload and every successfully-completing adversarial case.**

## 15. EXISTING CONSUMER FUNCTION PARITY

`master_lookup` parity: **PASS** on every workload, for representative present literals and the deliberately
absent one — identical `known`/`destination`/`mode`/`global_index`/`local_index` results on both sides in
every case.

`validate_master_subset_conflicts` parity: **initially reported FAIL on all 4 official workloads — traced to
a test-harness comparison defect, not a product discrepancy.** The real oracle function (Section 4 line range
1726–1764) has **no `return` statement** — it either raises `ProbeError` (conflicts found) or implicitly
returns `None`. This session's own compatibility mirror (`compat_validate_master_subset_conflicts`) was
written with an explicit `return conflicts`, so the two were compared as `None == []`, which is `False` for
every no-conflict case — a defect in this session's own test code, confirmed by direct re-reading of the
extracted oracle source (reproduced verbatim in Section 4/15 of this document). The **actual, meaningful
behavioral parity** — does the real function raise or not, for the same inputs — is independently confirmed
by the stage-marker log itself: every one of the 4 official workloads' stages ran cleanly through to
completion with no uncaught exception, proving neither side raised, for the official Master's real,
0-cross-path-conflict content. This is corrected here rather than silently patched into the raw pass/fail
count; the true result is **PASS** (behavioral parity), with the counting defect fully disclosed.

## 16. COVERAGE VS MASTERUNKNOWN

Explicit sequence proven (Part 12), using the real sidecar as complete authority throughout:

1. View A built from the single-target (`Fingers`) scope.
2. A real literal known to exist under the medium-scope `Correctives` group (vocabulary B, not in A's
   `wanted_folds`) was looked up against view A: **`known: False`** — correctly representing "not requested
   in this view," even though the literal genuinely exists in the complete Master.
3. An expanded view (A ∪ B folds) was built directly from the same complete sidecar generation — no TXT
   re-scan of any kind was needed conceptually (the sidecar already held complete authority in one open
   handle); the same literal now resolved **`known: True`**, with the correct destination.
4. Genuinely absent folds (Section 12's disjoint-scope sentinel) resolved `known: False` in every workload
   that included them, distinguished cleanly from the "not requested" case above — the two are never
   conflated by the compatibility producer, matching the oracle's own contract exactly (both share the same
   underlying limitation: a `wanted_folds`-scoped view cannot distinguish "not requested" from "requested and
   the requester made an over-broad absence claim" without separately re-querying a properly-expanded
   `wanted_folds` set — this is a property of the CURRENT Normalizer contract itself, not something the
   sidecar changes or improves in this gate).

## 17. FORMAT SUFFICIENCY

**FORMAT SEMANTICALLY SUFFICIENT FOR NORMALIZER.** Necessary consumer-adapter conversions that do **not**
require any format change:

- Wrapper-path conversion (strip the leading `wrapper_name + "/"` segment; wrapper-owned facts map to `u""`).
- UTF-8 bytes → Unicode consumer values (already performed by the reader's own eager decode; no additional
  conversion needed at this boundary).
- Narrow 4-key (`groupColor`/`selectable`/`visible`/`snappable`) metadata projection, discarding any other
  metadata key, with duplicate-of-a-known-key detection matching the oracle's own raise behavior.
- Dict/view construction (`group_sibling_order`/`group_metadata`/`folded` as Python dicts, `exact_literals` as
  a Python set) — ordinary consumer-side data-structure assembly, not a format concern.

No format v1 freeze decision is made or implied by this result.

## 18. CHARACTER PRESET OBSERVATION

**No static Master fact relevant to Character Preset was found missing from the binary.** Every field
inventoried in Sections 5–6 (literal, fold, destination, rank, family evidence, hierarchy, sibling order,
metadata) is a generic structural fact already fully present in the qualified binary format. This is
explicitly **not** a Character Preset compatibility PASS claim — Character Preset's own exact contract (which
this task did not inspect) remains a separate, later qualification.

## 19. EXPLICITLY UNTESTED

- **Backslash-escape spelling divergence between the Normalizer's own tokenizer and `sfm_master_core`'s
  tokenizer.** Direct inspection (Section 4) found `stream_tokens` (the Normalizer's real, current tokenizer)
  performs actual escape resolution (`\n`→newline, `\r`→CR, `\t`→tab, any other `\X`→`X`, i.e. it *unescapes*),
  while `sfm_master_core`'s tokenizer (and therefore the sidecar) performs **no** escape resolution
  whatsoever (backslashes preserved verbatim, per the final format spec's own escape-wording correction). This
  is a genuine, pre-existing divergence between two independently-written TXT parsers of the same grammar —
  **not introduced by this gate or by the sidecar** — and it is currently **dormant**: the real official
  Master contains **zero backslash characters** anywhere (confirmed by direct scan), so it never manifests on
  real production content. This gate deliberately did not exercise the sidecar's own escape-preserving custom
  fixtures (`21_escaped_quote_spelling.txt`/`22_escaped_backslash_spelling.txt`) against the oracle, since
  doing so would measure this pre-existing tokenizer divergence, not sidecar/reader correctness — reported
  here explicitly rather than silently avoided.
- Six-target/large-scope figures used real substitute vocabularies (Sections 9–11) rather than the specific
  historical Fox/Kaitlyn-Ayane-Tifa-Lola-Ruby-Vortex/~800-fold ("T66") captures, since no such capture artifact
  was recoverable in-repo or in the SFM install.
- Performance/timing was not used to draw any conclusion (Part 13) — incidental elapsed times were not even
  specifically recorded in this pass, consistent with this gate's explicit non-goal.
- Session-level caching for late-loaded models was not implemented or evaluated (Part 12's own explicit
  scope boundary).

## 20. REGRESSION / SAFETY

- `python -m pytest tests/ -q` → **421 passed, 0 failed, 265 subtests passed** (unchanged from the Gate A1
  baseline — no test regression, since no production code was touched).
- Validator: PASS (43 groups, 128,555 controls, 124,728 fold keys, 0 duplicates, 0 cross-path invariant
  violations).
- `git diff --check`: clean.
- `git status`: no tracked file modified by this task.
- Official artifact SHA reconfirmed unchanged: `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`.
- Master SHA reconfirmed unchanged: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`.
- Gate 1 remains **PASS, 36/36, 0 OPEN, 0 FAIL** (untouched by this task).
- All SFM sessions were fresh, disposable instances; the one used for this task's real embedded Python 2.7
  qualification was terminated after completion. All deployed files (runtime package, oracle extraction,
  compatibility producer, official artifact copy, adversarial fixture copies, autoinit probe) were removed;
  a directory-wide search for `*gate_a2*`/`*gate_a1*` under `usermod\scripts\` found nothing remaining.
  `usermod\scripts\sfm\sfm_init.py` confirmed byte-for-byte unchanged
  (`08be8719e2f9d321c72ae434fb1fd8f260e684543567ee1b4832fa107b7cbf15`). No launch-option change. No
  manifest/generation/publisher-lock file created. No new crash dump attributable to this task.

## 21. DESIGN CONSEQUENCE

The current packed binary format need not change to support the Normalizer's real consumer contract. All
required adaptation belongs at a thin, test-proven consumer/compatibility boundary (wrapper-path conversion,
narrow metadata projection, dict/view assembly) — exactly the separation the final implementation spec's own
Normalizer Adapter Boundary section already anticipated. This clears the semantic precondition for Gate B
(bounded-materialization consumer value) to proceed on solid ground: Gate B's job is to determine whether a
bounded/streaming backing can deliver this SAME already-proven-correct view at acceptable resource cost and
latency, not to re-litigate whether the format itself is expressive enough (this gate answers that: yes).

## 22. NEXT GATE

**Gate B — Bounded-Materialization Consumer Value**, per this task's own closing instruction. Not begun here.
