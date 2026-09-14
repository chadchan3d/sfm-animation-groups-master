# SFM Master Sidecar — Gate 1 H1: Embedded SFM Python 2.7 Reader Compatibility Probe

Qualification only, closing the sole remaining mandatory Gate 1 blocker: real Python 2.7 execution of
`tools/sfm_master_sidecar/format.py` and `tools/sfm_master_sidecar/reader.py`. Not Gate 2 — no memory, VAS,
timing, backing-strategy, or Normalizer work was performed or measured.

> **STATUS UPDATE (superseding note — see Section 22 for full detail):** the run documented below is the
> **original** H1 run. It exercised ONLY the legacy `open_generation(bytes, ...)` call shape — it never
> passed a path string to the reader. A later Gate 2A resource-baseline task discovered that the reader's
> then-current path/bytes type-dispatch (`isinstance(x, (bytes, bytearray))`) is inherently ambiguous under
> Python 2.7 (where `bytes is str`), and reproduced a genuine defect when a path string was passed. That
> discovery formally **REOPENED Gate 1 H1** — this document's original PASS verdict (Sections 1, 19–20) is
> preserved below **exactly as it was recorded**, as an accurate historical record of what was actually
> tested at the time, and must **not** be read as having covered the path-input boundary. A separate,
> complete requalification was performed after the reader was corrected (explicit
> `open_generation_bytes`/`open_generation_path`/`open_generation_unbound_bytes`/`open_generation_unbound_path`
> entry points, no type dispatch) — see
> `SFM_MASTER_SIDECAR_PY27_PATH_INPUT_FIX_AUDIT.md` Sections 8–11 for that full requalification's evidence,
> and Section 22 below for the reconciliation. Gate 1 H1 is, as of that requalification, **RE-CLOSED / PASS**
> against the corrected `reader.py`.

## 1. VERDICT

**PASS.** The actual embedded Python 2.7.5 interpreter shipped inside this machine's real Source Filmmaker
installation (`sfm.exe` itself, confirmed via `sys.executable`) successfully imported the exact, byte-verified
committed `format.py`/`reader.py` and executed all 18 required behaviors (Part 7) plus the byte/Unicode
(Part 8) and error-classification (Part 9) checks with zero uncaught exceptions and zero incorrect results.
One documentation-only discrepancy was observed (Section 17) — it caused no functional defect and does not
change the PASS verdict.

## 2. TARGET SFM INSTALL

Discovered conservatively via Steam's own library configuration (`Steam\steamapps\libraryfolders.vdf`,
never modified), cross-referenced against the corresponding `appmanifest_1840.acf`:

- **Source Filmmaker root:** `E:\SteamLibrary\steamapps\common\SourceFilmmaker`
- **Game directory:** `E:\SteamLibrary\steamapps\common\SourceFilmmaker\game`
- **Executable:** `E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\sfm.exe`
- **Embedded Python evidence located before running anything:** `game\bin\python27.dll` and
  `game\bin\shiboken-python2.7.dll`.
- **Script auto-execution mechanism identified (already in use in this install, not invented):**
  `game\usermod\scripts\sfm\autoinit\` — an existing, empty, reserved directory sitting alongside
  `game\usermod\scripts\sfm\sfm_init.py`, whose own first-line comment ("Initial Script after SFM started
  up, and the main window got focus") confirms this is SFM's real, already-functioning startup-script
  entry point in this exact installation.
- SFM was found already running (PID 11892, live user session) at the start of this task; per explicit user
  instruction, it was left untouched until the user confirmed they had saved and closed it themselves.

## 3. EMBEDDED PYTHON IDENTITY

Recorded directly from `sys` inside the running interpreter, not inferred:

- `sys.version`: `'2.7.5 (default, Jul  3 2013, 16:44:46) [MSC v.1600 32 bit (Intel)]'`
- `sys.version_info`: `sys.version_info(major=2, minor=7, micro=5, releaselevel='final', serial=0)`
- `sys.platform`: `'win32'`
- `sys.executable`: `'E:\\SteamLibrary\\steamapps\\common\\SourceFilmmaker\\game\\sfm.exe'`
- Pointer size: `struct.calcsize('P') * 8 = 32` — **the embedded interpreter is 32-bit**, distinct from this
  development machine's 64-bit standalone Python 3.10.6.

**Confirmed: real Python 2.7** (2.7.5 specifically), not inferred from documentation or filename convention.

## 4. RUNTIME MODULE SHA-256 IDENTITY

Computed from the committed repository files before deployment:

| File | SHA-256 |
|---|---|
| `tools/sfm_master_sidecar/format.py` | `b401967db8d07943e9f171058a006c30f0e23eb70a7b43bb5ab950203a3c3259` |
| `tools/sfm_master_sidecar/reader.py` | `dd1e5da29058394c99e37f5eeaffd262c0b07421d052661ca51b06f1e11e7b02` |
| `tools/sfm_master_sidecar/__init__.py` | `8cad865fd9954035aebb3e02d5c454228e80a095595bd9cd3746df0b357f904c` |

Re-verified identical at the deployed location (`usermod\scripts\sfm_master_sidecar_probe_runtime\`)
immediately before launching SFM, and again from INSIDE the running probe itself (the probe script computes
its own SHA-256 of the on-disk files it is about to import and logs the comparison — see Section 7's log
excerpt: both report `True`). No hand-edited compatibility copy was used at any point — the deployed files
were plain, unmodified byte copies of the committed repository files.

## 5. SCRIPT INVOCATION METHOD

The existing, already-proven `usermod\scripts\sfm\autoinit\` mechanism (Section 2) — a single temporary file
(`zz_gate1_h1_probe_temp.py`) was placed there, executed automatically once when SFM started, and was
removed immediately after the run completed. No new autoload architecture was built; no existing file
(including `sfm_init.py`) was modified. No permanent plugin, tool, or startup option was added or left
behind.

## 6. TEST ARTIFACTS

One small, hand-composed custom Master (never the 9.5 MiB official artifact) was compiled OUTSIDE SFM using
the already-qualified Python 3 writer (`tools/sfm_master_sidecar/writer.py`, unmodified), covering every
element Part 6 requires in a single 1,041-byte compiled artifact:

```
groupFile
{
	"GrpA"
	{
		"selectable"	"1"
		"control"		"Alpha"
		"control"		"Foo"
		"control"		"foo"
		"control"		"FOO"
	}
	"GrpB"
	{
		"control"		"Bar"
	}
	"GrpC"
	{
		"control"		"bar"
		"control"		"注視Tips"
		"control"		"He said \"hi\""
	}
}
```

- Source SHA-256: `8d9802a86780ae43ef4b4cc623070d6d5d4c42ffe2f4217367a5b893800a8ea4`
- Compiled artifact: 1,041 bytes
- **A.** Ordinary valid HIT: `"Alpha"` (unique, single destination).
- **B.** Same-destination ASCII alias family: `Foo`/`foo`/`FOO`, all in `GrpA`.
- **C.** Cross-destination FoldConflict: `Bar` (`GrpB`) vs. `bar` (`GrpC`).
- **D.** `MasterUnknown`: a query for a literal guaranteed absent from this tiny source.
- **E.** Metadata/group/occurrence iteration: `GrpA` carries `"selectable" "1"`; 4 groups, 8 occurrences total.
- **F.** Checksum-invalid variant: the same 1,041-byte artifact with one STRING_POOL content byte flipped,
  digest deliberately NOT recomputed.
- **Part 8 UTF-8/escape coverage, in the same artifact:** `注視Tips` (non-ASCII UTF-8) and
  `He said \"hi\"` (preserved backslash-escape spelling), both alongside pure-ASCII literals in the same
  small source.

Both compiled artifacts were sanity-checked against the real reader under Python 3 (matching this project's
existing qualified behavior) before ever being shipped into SFM, and were embedded directly in the temporary
probe script as base64 text (no separate binary file needed inside SFM's directory tree at all).

## 7. IMPORT RESULT

```
import format.py: PASS
import reader.py: PASS
```

Both imported successfully as `sfm_master_sidecar_probe_runtime.format` /
`sfm_master_sidecar_probe_runtime.reader` (package name differs from the repository package name by
necessity of deployment; file contents are byte-identical, confirmed in Section 4). No import of `writer`,
`compiler`, `manifest`, `publisher`, `cli`, `sfm_master_core`, `pytest`, or the B2A oracle occurred anywhere
in the probe.

## 8. HIT RESULT

```
lookup 'Alpha' -> Hit(fold_key='alpha', destination=u'groupFile/GrpA', n=1)
is Hit: True
Hit.destination: u'groupFile/GrpA'
```

**PASS.**

## 9. SAME-DESTINATION ALIAS RESULT

```
lookup 'foo' -> Hit(fold_key='foo', destination=u'groupFile/GrpA', n=3)
is Hit: True
family evidence count: 3
family evidence literals: [u'FOO', u'Foo', u'foo']
```

**PASS** — complete family evidence (all 3 exact spellings) returned, not merely the queried spelling.

## 10. FOLD-CONFLICT RESULT

```
lookup 'bar' -> FoldConflict(fold_key='bar', destinations=[u'groupFile/GrpB', u'groupFile/GrpC'], n=2)
is FoldConflict: True
FoldConflict.destinations: [u'groupFile/GrpB', u'groupFile/GrpC']

--- exact spelling inside conflicting family ---
lookup exact 'Bar' -> FoldConflict(fold_key='bar', destinations=[u'groupFile/GrpB', u'groupFile/GrpC'], n=2)
still FoldConflict (never Hit): True
```

**PASS** — including the critical rule that an exact spelling matching one specific conflicting member
(`"Bar"`) still resolves `FoldConflict`, never `Hit`.

## 11. MASTER-UNKNOWN RESULT

```
lookup absent -> MasterUnknown(fold_key='thisdoesnotexistinprobemaster')
is MasterUnknown: True
```

**PASS.**

## 12. ITERATION RESULT

```
group_count(): 4, len(iter_groups()): 4
occurrence_count(): 8, len(iter_occurrences()): 8
GrpA metadata: [{'source_order': 0, 'value': u'1', 'key': u'selectable'}]
```

All 4 groups, all 8 occurrences, and the one metadata entry enumerated correctly, with exact
name/parent/declare_order/sibling_rank/full_path and literal/full_path/local_rank fields matching the
source exactly (full log retained — see Section 18/scratchpad reference). **PASS.**

## 13. UTF-8 / BYTE-FOLD RESULT

```
literal=u'注視Tips' utf8_bytes='\xe6\xb3\xa8\xe8\xa6\x96Tips' ascii_only=False
literal=u'He said \"hi\"' utf8_bytes='He said \"hi\"' ascii_only=True
escape-spelling occurrences (backslash preserved): [...'He said \"hi\"'...]
non-ASCII occurrences: [...'注視Tips'...]
ascii_fold_bytes('MiXeD_Case_Only_ASCII') -> 'mixed_case_only_ascii'
ascii_fold_bytes(kanji+'ABC' utf8) -> '\xe6\xb3\xa8\xe8\xa6\x96abc'
```

**PASS** — only ASCII A-Z folded; the kanji bytes (`\xe6\xb3\xa8\xe8\xa6\x96`) pass through completely
unchanged in both the stored literal and the direct `ascii_fold_bytes` call; the backslash-escaped quote
spelling round-trips with every backslash intact, not unescaped; strict UTF-8 decoding succeeded with no
replacement characters and no Unicode casefold/lower substitution anywhere.

## 14. CHECKSUM FAILURE RESULT

```
checksum-invalid open: PASS (raised AuthorityUnavailable: AuthorityUnavailable('embedded_integrity_digest
mismatch -- file content does not match its own recorded digest',))
```

**PASS.**

## 15. SOURCE-BINDING FAILURE RESULT

```
source-mismatch open: PASS (raised SourceMismatchError: SourceMismatchError(u'expected source_sha256
000...000, sidecar header declares 8d9802a8...',))
```

**PASS** (`SourceMismatchError` is a subclass of `AuthorityUnavailable`, confirmed by the exception actually
being caught by the `except reader.AuthorityUnavailable` clause in the probe).

## 16. CLOSE / LIFETIME RESULT

```
close() #1: PASS (no exception)
close() #2 (idempotent): PASS (no exception)
lookup after close: PASS (raised AuthorityUnavailable: AuthorityUnavailable('provider is not VALID
(state=CLEANED)',))
closed-provider != MasterUnknown: True
lazy iterator after close: PASS (raised AuthorityUnavailable: AuthorityUnavailable('provider is not VALID
(state=CLEANED)',))
```

**PASS** — a lazy `iter_groups()` generator obtained and primed (one item consumed) BEFORE `close()` correctly
raises `AuthorityUnavailable` on its next advance AFTER `close()`, exactly matching the qualified B2B/B2C
lifetime contract.

## 17. ERROR-CLASSIFICATION RESULT

```
corrupt-backing != MasterUnknown: True
source-mismatch != MasterUnknown: True
closed-provider != MasterUnknown: True
```

**PASS** — every failure mode raised a distinct `AuthorityUnavailable`-family exception; `MasterUnknown` was
returned ONLY for the genuine valid-backing/absent-fold case (Section 11). The mandatory distinction
(Part 9) holds exactly under real Python 2.7.

**One notable, non-blocking observation, corrected wording:** the Python 2 reader's string-table decode step
calls `.decode("utf-8")` on the raw pool bytes, which under Python 2.7 always produces `unicode` values
(visible as `u'...'` throughout the captured log) for every stored string (group names, full paths,
occurrence literals, metadata keys/values, fold keys). **Python 2 reader decoding currently produces
`unicode` values through strict UTF-8 decoding.** H1 proved exact UTF-8 round-trip, ASCII-only folding,
escape-spelling preservation, and correct failure semantics (Sections 13–17) in the real embedded
interpreter, on top of that `unicode`-valued representation — every comparison that matters (fold-key
lookup, byte-fold computation, equality checks) explicitly re-encodes back to `str`/bytes via
`.encode("utf-8")` before comparing, so no incorrect result was ever produced. **No H1 semantic defect
resulted.** The final SFM/DME-facing byte/Unicode representation choice (whether the eventual Normalizer
consumer wants `unicode`, `str`, or a specific DME-compatible string type at its own boundary) remains
explicitly **post-Gate-1 consumer/Gate-2 work**, not something this qualification-only probe resolves or
needed to resolve. `reader.py` itself was not modified in response to this observation.

## 18. CLEANUP RESULT

- SFM process terminated after the probe log was captured (`taskkill /PID 17840 /F` — the process had
  already finished writing its result log; no user-visible session data existed to lose, since SFM was
  launched fresh for this single probe run, not the user's own earlier session).
- `usermod\scripts\sfm\autoinit\zz_gate1_h1_probe_temp.py` — removed; directory confirmed empty afterward
  (back to its original reserved-but-unused state).
- `usermod\scripts\sfm_master_sidecar_probe_runtime\` (the temporary runtime-module copy) — removed entirely.
- `usermod\scripts\sfm\sfm_init.py` — confirmed byte-for-byte unchanged (`"Initial Script after SFM started
  up..." / print "USERMOD: Python initial startup complete"`, verified by direct re-read after cleanup).
- No new crash dump (`*.mdmp`) appeared in `game\` from this session.
- No `.pyc` bytecode cache or any other file was left behind under `usermod\scripts\` from this probe
  (confirmed by directory search for any remaining `*probe*`/`*gate1*` name matching only pre-existing,
  unrelated user content with different naming, e.g. `ChadChan3D`-authored animation-rigging probe scripts
  from the user's own prior, unrelated work).
- The complete probe result log was preserved OUTSIDE the SFM install and outside the repository, in this
  session's own scratchpad directory (`gate1_h1_probe_result.log`), for audit traceability; its full content
  is reproduced across Sections 8–17 above.
- No persistent generated sidecar, manifest, or publisher-lock file was created anywhere by this task.

## 19. GATE 1 H1 VERDICT

**PASS.** Every one of the 18 required behaviors (Part 7), the byte/Unicode compatibility checks (Part 8),
and the error-classification distinction (Part 9) were verified against the real, committed, byte-identical
`format.py`/`reader.py` running under the actual embedded Python 2.7.5 interpreter inside this machine's real
Source Filmmaker installation — not a standalone, unrelated Python 2.7 install, and not a static/AST
substitute. No compatibility defect was found (Section 17's observation is a documentation/design-principle
discrepancy, not a functional defect).

## 20. GATE 1 FINAL STATUS

Per this task's own Part 15 closure rule: **H1 PASS, and all previously qualified evidence
(SFM_MASTER_SIDECAR_FINAL_GATE1_AUDIT.md, commit `8efb70b2e3d5d8ff2d686626795ee89b254fc52a`) remains valid
and unchanged** — nothing in this task altered the Master, the semantic core, the validator, or any
production sidecar code. Therefore, per that rule:

**FINAL GATE 1: PASS.**

**Matrix: 36 / 36 mandatory items PASS. 0 OPEN. 0 FAIL.**

(H1 moves from OPEN to PASS; I1/I2, already reclassified NOT REQUIRED under the current Windows-only/
CPython-3.10.x-only support contract per the prior consolidation pass, remain excluded from the mandatory
count for the same reasons stated in that document's Section 23.)

This document records that conclusion; the standalone `SFM_MASTER_SIDECAR_FINAL_GATE1_AUDIT.md` file itself
was NOT edited in this task (only this new H1-specific document was created, per Part 13's instruction) —
formally updating that file's own verdict/matrix text to match is a small, separate step available for a
future checkpoint task, not performed here.

**Gate 2 is NOT begun by this result.** Gate 2 (embedded SFM memory/VAS/performance measurement, backing-
strategy comparison, generation-overlap cost) still requires separate, explicit authorization, per Part 15's
own instruction ("Do not begin Gate 2 automatically").

## 21. GIT / SAFETY STATE

- `sfm_defaultanimationgroups.txt`: unchanged.
- `tools/sfm_master_core.py`, `tools/validate_master.py`: unchanged.
- All production sidecar code (`tools/sfm_master_sidecar/*.py`): unchanged — this task deployed only
  read-only, byte-verified COPIES to a temporary SFM location; the repository's own files were never opened
  for writing.
- No Normalizer code touched.
- No persistent generated sidecar, manifest, or publisher-lock artifact anywhere (repository or SFM
  install).
- No SFM launch option, configuration file, or startup script left modified or added.
- Nothing staged, nothing committed (`git status --porcelain` unchanged from the pre-task baseline aside
  from this new audit file itself, which remains untracked pending a separate commit authorization).
- No agents or subagents were used.

## 22. ADDENDUM — Path-Input Defect Discovery, H1 Reopening, and Requalification

This section is an ADDITION appended after the fact. **Sections 1–21 above are preserved unedited as the
exact historical record of the original H1 run** — they are not retroactively reinterpreted as having tested
anything they did not actually test.

**What the original run above actually covered:** every check in Sections 7–17 called the reader exclusively
through `open_generation(<already-decoded bytes>, expected_source_sha256)` (Section 6's artifacts were
embedded as base64 text and decoded to bytes BEFORE being handed to the reader). **The original run never
once passed a path string to the reader.** Its PASS verdict is accurate for exactly what it tested — bytes
input — and remains true. It is not accurate to describe it, after the fact, as having qualified path-string
input, and this document does not do so.

**Why that mattered:** a later task (Gate 2A, embedded SFM x86 Candidate A resource baseline) called
`reader.SidecarReader.open_generation(ARTIFACT_PATH, SOURCE_SHA256)` with a PATH STRING, inside the same real
embedded Python 2.7.5 interpreter, and found the path text itself was misread as the artifact's own bytes.
Root cause: the reader's `_read_all(path_or_bytes)` used `isinstance(path_or_bytes, (bytes, bytearray))` to
decide whether to treat its argument as raw content or as a path to open — and under Python 2.7, `bytes IS
str`, so an ordinary path string always satisfies that check. This is documented in full in
`SFM_MASTER_SIDECAR_GATE2A_CANDIDATE_A_EMBEDDED_BASELINE_AUDIT.md` (left unchanged, a factual record of that
blocked attempt) and formally reopened Gate 1 H1, since the original qualification above never exercised the
call shape that actually failed.

**Correction and requalification:** `reader.py` was corrected to remove all type-based path/bytes dispatch,
replacing it with four explicit entry points (`open_generation_bytes`, `open_generation_path`,
`open_generation_unbound_bytes`, `open_generation_unbound_path`); the legacy `open_generation`/
`open_generation_unbound` names remain as explicitly-documented bytes-only aliases. Full root-cause analysis,
the chosen API, and complete regression evidence are in `SFM_MASTER_SIDECAR_PY27_PATH_INPUT_FIX_AUDIT.md`.
That document's Section 11 records a **complete H1 requalification**, run inside the real embedded Python
2.7.5 interpreter against the newly-corrected `reader.py` (SHA-256
`d79f7ae87c1999b7fe728f7dd6ddafb29b7cc62c246cd332f061875095288b00`, superseding the original run's
`dd1e5da29058394c99e37f5eeaffd262c0b07421d052661ca51b06f1e11e7b02`): all 18 original checks from Sections
7–17 above re-passed against the corrected file, PLUS three new checks specifically closing the Gate
2A-discovered gap — explicit path-open PASS, explicit bytes-open PASS, and path/bytes semantic equivalence
PASS (21/21 total).

**Current status:** Gate 1 H1 is **RE-CLOSED / PASS**, qualified against the corrected `reader.py`
identified above, per the requalification evidence in `SFM_MASTER_SIDECAR_PY27_PATH_INPUT_FIX_AUDIT.md`. The
verdict text in Sections 1, 19, and 20 above is retained as-is because it was — and remains — a true
statement about the original run's own (bytes-only) scope; it is this Section 22, not an edit to that
original text, that carries the reopening/re-closure history forward.
