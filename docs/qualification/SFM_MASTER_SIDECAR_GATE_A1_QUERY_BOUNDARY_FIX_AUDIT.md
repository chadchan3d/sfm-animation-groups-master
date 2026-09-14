# SFM Master Sidecar — Gate A1: Query-Boundary Correctness Closure

Bounded production correction + requalification only. No binary format change, no compiler semantics change,
no Master taxonomy change, no publication architecture change, no Candidate B/C, no Normalizer integration, no
Character Preset integration, no format v1 freeze, no bounded-materialization provider work. Nothing
committed until this document's own checkpoint gate authorizes it.

## 1. VERDICT

**PASS. Malformed UTF-8 query bytes must never resolve to `MasterUnknown` — corrected, narrowly, in exactly
one method (`SidecarReader.lookup_fold`), with zero change to valid-input semantics, artifact identity,
compiler behavior, or any other reader contract.** Independent Astra review reproduced a genuine query-input
correctness defect (Section 3); the fix is a single strict-UTF-8 validation line inserted before ASCII
folding/binary search/absence classification (Section 6); full Python 3 and real embedded Python 2.7.5
requalification both show all valid-input behavior unchanged and all malformed-input cases now correctly
rejected, never silently accepted as absence (Sections 10–11). Gate 1 is reclosed at 36/36, 0 OPEN, 0 FAIL
(Section 14).

## 2. DISCOVERY / INDEPENDENT REVIEW CONTEXT

An independent Astra review reproduced the defect by tracing the query path from `lookup_fold` through the
byte-level ASCII-fold helper and the fold-table binary search, and noted that existing tests
(`tests/sidecar/test_reader_lookup.py`) already covered oversized-length and wrong-Python-type malformed
input (`test_master_unknown_never_substituted_for_a_real_error`) but never malformed **UTF-8 encoding**
specifically — the exact gap this task closes. This narrowly reopens the Gate 1 query-boundary qualification
only; it does not invalidate valid-input semantic parity, compiler determinism, artifact identity, structural
corruption rejection, the Python-2 path/bytes correction, source binding, or publication qualification — all
of those remain exactly as previously closed.

## 3. ROOT CAUSE

`SidecarReader.lookup_fold(query)` (`tools/sfm_master_sidecar/reader.py`), prior to this correction:

```python
query = bytes(query)
if len(query) > fmt.LIMIT_READER_QUERY_BYTE_LENGTH:
    raise ValueError(...)
folded = fmt.ascii_fold_bytes(query)
```

`fmt.ascii_fold_bytes` is a **purely byte-level** operation (folds ASCII `0x41`–`0x5A` to `+0x20`, every other
byte — valid or not — passes through completely unchanged). It never validates that `query` is well-formed
UTF-8. The subsequent binary search compares this un-validated `folded` value against the fold table's own
keys, which ARE guaranteed valid UTF-8 (each is `backing.strings[...].encode("utf-8")`, itself already
decoded-then-re-encoded at open time). A malformed byte string essentially never coincides with any real
folded key, so the search simply finds no match (`found < 0`) and returns `MasterUnknown(folded)` — **the
exact defect**: malformed caller input silently resolves to "valid query, absent from the Master," when the
authority contract requires it to be a distinct input/query error. The method's own docstring already
*claimed* the correct contract ("Raises `AuthorityUnavailable` for... a malformed/oversized query -- never
returns `MasterUnknown` for those cases") — the implementation simply never enforced the malformed-encoding
half of that claim (the oversized-length half WAS enforced, correctly, by the length check immediately
above).

**Existing exception taxonomy available for input errors**, inventoried before writing any fix:
`TypeError` (used, unchanged, for wrong Python type), `ValueError` (used, unchanged, for oversized length),
and `AuthorityUnavailable`/`SourceMismatchError` (reserved for backing/source corruption and closed/invalidated
providers — explicitly **not** appropriate for caller input errors, since malformed caller input is not
source/backing corruption). `UnicodeDecodeError` was already used elsewhere in the reader (structural STRING
TABLE decode, `reader.py` line ~330) for stored-string corruption, always wrapped into `AuthorityUnavailable`
there — but that is a **different** boundary (already-validated backing bytes at open time) from this one
(caller-supplied query bytes at lookup time); the two must not be conflated, and this fix does not reuse that
wrapping.

## 4. OLD BEHAVIOR

```
malformed query bytes
    -> fmt.ascii_fold_bytes(query)   [byte-level, no UTF-8 validation]
    -> binary search finds no match
    -> MasterUnknown(folded)         [WRONG: silently treated as valid-but-absent]
```

## 5. REQUIRED CONTRACT

```
VALID query, present in the Master           -> Hit or FoldConflict (unchanged)
VALID query, absent from the Master          -> MasterUnknown (unchanged)
MALFORMED query encoding                     -> input/query error (NEW: UnicodeDecodeError, a ValueError
                                                 subclass -- never MasterUnknown, Hit, or FoldConflict,
                                                 and never AuthorityUnavailable/source-corruption)
```

No replacement decoding, no `errors="ignore"`, no permissive fallback, no "try query, then treat failure as
absent," and no normalization beyond the already-qualified ASCII A–Z folding rule. Per this task's own Part 2
instruction, the existing strict built-in `TypeError`/`ValueError`-style philosophy is preserved exactly —
**no new named exception class was introduced or required.**

## 6. IMPLEMENTATION CHANGE

**Exactly one call-site, one new line, in exactly one method.** Method inventory performed before editing
(Part 4's own requirement) confirmed `lookup_fold` is the **only** public method that accepts caller-supplied
name/literal query bytes — `group_full_path`, `iter_groups`, `iter_occurrences`, and `iter_metadata` all take
internal integer `path_id` references, never caller-supplied text, so none of them are affected and none were
touched.

```python
query = bytes(query)
if len(query) > fmt.LIMIT_READER_QUERY_BYTE_LENGTH:
    raise ValueError(...)
# Gate A1 correction: strict UTF-8 validation BEFORE ASCII folding / binary
# search / absence classification. The decoded value is discarded --
# folding still operates on the original bytes, exactly as before.
query.decode("utf-8")
folded = fmt.ascii_fold_bytes(query)
```

`bytes.decode("utf-8")` (strict, the default) raises `UnicodeDecodeError` — a `ValueError` subclass in both
CPython 3.10.x and embedded CPython 2.7.5 — on any malformed input, confirmed identical in both interpreters
(Section 3's byte/Unicode boundary discipline: query bytes are validated the same way regardless of the
`str`/`bytes`/`unicode` relationship differences between the two interpreters, since `bytes.decode("utf-8")`
means the same thing on both). No scattering: this is the single centralized validation point every caller of
`lookup_fold` inherits automatically.

- New `reader.py` SHA-256: `c0ed4250cfe13b892e54baf0538ee3bab946f000f20466d5c4da5b15c60bf2a9` (was
  `d79f7ae87c1999b7fe728f7dd6ddafb29b7cc62c246cd332f061875095288b00`).
- No other production file was touched (`format.py`, `writer.py`, `manifest.py`, `publisher.py`, `cli.py`,
  `compiler.py`, `__init__.py`: all unchanged, confirmed in Section 15).

## 7. VALID QUERY REGRESSION

New `MalformedQueryEncodingTests` class in `tests/sidecar/test_reader_lookup.py` (10 test methods, matching
Part 5's A–I matrix plus Part 6's explicit distinction test):

| Case | Assertion | Result |
|---|---|---|
| A. Valid ASCII bytes | `Hit`, unchanged | PASS |
| B. Valid non-ASCII UTF-8 (`注視TipsParent`) | `Hit`, unchanged, no Unicode-casefold substitution (only ASCII letters folded) | PASS |
| C. Valid absent query | `MasterUnknown` | PASS |
| E. Wrong type (`str` instead of `bytes`) | `TypeError`, unchanged | PASS |
| F. Oversized (5000 bytes) | `ValueError`, unchanged | PASS |
| G. Conflict family (`Bar`/`bar`) | `FoldConflict`, unchanged | PASS |
| H. Exact spelling inside a still-conflicting family | `FoldConflict` (never `Hit`), unchanged | PASS |
| I. ASCII case variants (same-destination alias family) | `Hit`, unchanged | PASS |

All PASS — every previously-qualified valid-input behavior is bit-for-bit unchanged.

## 8. MALFORMED UTF-8 MATRIX

| Case | Bytes | Python 3 result | Real embedded Python 2.7.5 result |
|---|---|---|---|
| Isolated continuation byte | `b"\x80"` | `UnicodeDecodeError` (invalid start byte) | `UnicodeDecodeError` (invalid start byte) |
| Truncated multibyte sequence | `b"\xc2"` | `UnicodeDecodeError` (unexpected end of data) | `UnicodeDecodeError` (unexpected end of data) |
| Invalid leading byte | `b"\xff"` | `UnicodeDecodeError` (invalid start byte) | `UnicodeDecodeError` (invalid start byte) |
| Invalid continuation sequence | `b"\xc2\x20"` | `UnicodeDecodeError` (invalid continuation byte) | `UnicodeDecodeError` (invalid continuation byte) |

**All four cases: PASS on both interpreters — never `MasterUnknown`, never `Hit`, never `FoldConflict`, never
`AuthorityUnavailable` (would have wrongly classified caller input as source corruption).**

## 9. MASTERUNKNOWN DISTINCTION

Explicit, impossible-to-silently-regress side-by-side assertion added
(`test_malformed_query_never_collapses_into_valid_absent_result`), against the **same open provider**:

```python
valid_absent = r.lookup_fold(b"ValidAsciiButAbsentFromThisFixture")
assert isinstance(valid_absent, reader.MasterUnknown)          # PASS

with pytest.raises(UnicodeDecodeError):                         # not merely "some exception"
    r.lookup_fold(b"\x80")                                       # PASS
```

Both assertions target the **specific class/contract**, not merely "an exception happened" or "not
MasterUnknown" — matching Part 6's explicit instruction.

## 10. PYTHON 3 RESULT

`tests/sidecar/test_reader_lookup.py`: **19 passed, 16 subtests passed** (10 new `MalformedQueryEncodingTests`
methods + 9 pre-existing methods, all passing). Full repository suite: **421 passed, 0 failed, 265 subtests
passed** (Section 13).

## 11. EMBEDDED PYTHON 2.7 RESULT

Real `sfm.exe`, embedded CPython 2.7.5 (32-bit), Qt/main-event thread (never `threading.Timer`), deployed
corrected `reader.py` (SHA-256 confirmed matching, Section 6) against the exact same small hand-composed
fixture used in the original Gate 1 H1 run (source SHA-256
`8d9802a86780ae43ef4b4cc623070d6d5d4c42ffe2f4217367a5b893800a8ea4`, artifact SHA-256
`21d66e75885032e8bff3a8d3751838dd958b5637d29e19c484c81ca6738a2094`, re-confirmed byte-identical on
regeneration):

```
open_generation_bytes: PASS is_valid=True
open_generation_path:  PASS is_valid=True   (path/bytes smoke check, re-verified though the fix
                                              did not touch the shared _coerce_bytes/_read_path/
                                              _open_from_buf helpers)
1. valid ASCII HIT ('Alpha'):                          PASS (Hit)
2. valid ASCII absent -> MasterUnknown:                PASS (MasterUnknown)
3. valid non-ASCII UTF-8 query ('注視Tips') HIT:        PASS (Hit)
4. malformed isolated continuation byte (\x80):        PASS (UnicodeDecodeError)
5. malformed truncated multibyte sequence (\xc2):      PASS (UnicodeDecodeError)
6. malformed invalid leading byte (\xff):               PASS (UnicodeDecodeError)
6b. malformed invalid continuation sequence (\xc2\x20): PASS (UnicodeDecodeError)
7. malformed input never -> MasterUnknown/Hit/FoldConflict: PASS
8. conflict (Bar/bar) unchanged:                        PASS (FoldConflict / FoldConflict)
9. close/double-close/post-close unchanged:             PASS
```

**All 10 checks PASS, zero uncaught exceptions.** (Python 2.7's exception repr shows `UnicodeDecodeError('utf8', '\x80', 0, 1, 'invalid start byte')` — the codec name/string form differs cosmetically from
Python 3's `UnicodeDecodeError('utf-8', b'\x80', 0, 1, 'invalid start byte')`, but the exception **class**
(`UnicodeDecodeError`, a `ValueError` subclass on both interpreters) and the outcome are identical.)

## 12. OFFICIAL ARTIFACT IDENTITY

Recompiled fresh, outside SFM, via the unchanged public compiler, immediately before and after the fix:

- Bytes: **9,506,244** — unchanged.
- SHA-256: **`bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`** — unchanged, matches exactly.
- Source SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` — unchanged.

Proves the fix touched only reader query-input handling, never the binary format or writer/compiler
semantics.

## 13. FULL REGRESSION

- `python -m pytest tests/ -q` → **421 passed, 0 failed, 265 subtests passed** in 118.61s (prior baseline
  411/255; the +10/+10 delta is exactly the new `MalformedQueryEncodingTests` class).
- Validator: PASS — 43 groups, 128,555 controls, 124,728 fold keys, 0 duplicate literals, 0 cross-path
  invariant violations, structural parse PASS, 0 grammar errors.
- `git diff --check`: clean (only pre-existing LF/CRLF line-ending advisories, no actual errors).
- B2C corruption matrix (8 files): 116 passed, 6 subtests passed — unchanged.
- B2D full official parity (4 files): 54 passed, 5 subtests passed — unchanged.
- B2E publication/compiler (7 files): 77 passed, 59 subtests passed — unchanged.

No regression anywhere.

## 14. GATE 1 REOPEN / RECLOSE HISTORY

Recorded in full, without erasing prior history, in `SFM_MASTER_SIDECAR_FINAL_GATE1_AUDIT.md` Section 25
(new) and Section 1 (updated to point to it). Sequence, stated explicitly per this task's own Part 10
instruction:

1. Original Gate 1 PASS (36/36, historical).
2. H1 (real Python 2.7 execution) later reopened/reclosed by the path/bytes correction (already recorded,
   `SFM_MASTER_SIDECAR_FINAL_GATE1_AUDIT.md` Section 24 — unaffected by this task).
3. **Independent Astra review found the malformed-query gap** (this task).
4. **Query boundary reopened narrowly** — H1, path/bytes correctness, artifact identity, structural
   corruption rejection, compiler determinism, source binding, and publication qualification were **not**
   invalidated by this reopening.
5. **Defect corrected** (Section 6, one method, one line).
6. **Python 3 + real embedded Python 2.7 requalified** (Sections 10–11).
7. **Gate 1 reclosed**: `SFM_MASTER_SIDECAR_FINAL_GATE1_AUDIT.md` restored to **GATE 1 PASS, 36/36 mandatory
   items PASS, 0 OPEN, 0 FAIL.**

History was not rewritten — the original Gate 1 audit's prior text remains exactly as it was; only a new,
clearly-labeled Section 25 and pointer updates in Section 1/3/17 were added.

## 15. SAFETY / CLEANUP

- All SFM sessions in this task were fresh, disposable instances (`tasklist` confirmed no running `sfm.exe`
  before launch); the one launch used for Section 11 was terminated after its qualification completed.
- Deployed runtime package (`usermod\scripts\sfm_master_sidecar_gate_a1_runtime\`), fixture directory
  (`usermod\scripts\gate_a1_fixture\`), and the autoinit probe
  (`usermod\scripts\sfm\autoinit\zz_gate_a1_probe_temp.py`) were all removed after use; a directory-wide
  search for `*gate_a1*` (and, from the immediately-prior Gate 2C task, `*gate2c*`) under `usermod\scripts\`
  found nothing remaining.
- `usermod\scripts\sfm\sfm_init.py` confirmed byte-for-byte unchanged
  (`08be8719e2f9d321c72ae434fb1fd8f260e684543567ee1b4832fa107b7cbf15`).
- No launch-option or SFM configuration change was made or left behind.
- No manifest, active generation, or publisher-lock file was created anywhere by this task.
- No new crash dump (`*.mdmp`) attributable to this task's activity was found.

## 16. GIT STATE

Files changed by this task:

- `tools/sfm_master_sidecar/reader.py` — production correction (Section 6).
- `tests/sidecar/test_reader_lookup.py` — new `MalformedQueryEncodingTests` class (Section 7).
- `SFM_MASTER_SIDECAR_FINAL_GATE1_AUDIT.md` — Section 25 appended, Sections 1/3/17 updated to point to it
  (Section 14).
- `SFM_MASTER_SIDECAR_GATE_A1_QUERY_BOUNDARY_FIX_AUDIT.md` — this new document.

No other file was modified. No Candidate B/C code, no Normalizer code, no Character Preset code, no
bounded-materialization provider code was written.

## 17. EXPLICITLY DEFERRED WORK

Per this task's own Part 13/15 constraints, none of the following were begun:

- Normalizer `master_view` parity work (Gate A2 — the explicitly-named next step).
- Bounded-materialization provider implementation.
- Consumer benchmark work.
- Character Preset integration.
- Candidate B/C implementation (Gate 2C's own investigation remains exactly as it was left — leaning
  recommendation only, no production backing change).
- Format v1 freeze.
- Any general reader redesign beyond the single-method, single-line correction in Section 6.
