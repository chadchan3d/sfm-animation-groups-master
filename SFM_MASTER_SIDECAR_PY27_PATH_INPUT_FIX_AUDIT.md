# SFM Master Sidecar — Python 2.7 Path/Bytes Reader Input Boundary Fix

Bounded defect fix only. No binary format change, no Master change, no Candidate B/C, no Normalizer
integration, no Gate 2 work resumed. Nothing committed in this pass (pending separate authorization).

## 1. VERDICT

**PASS.** The genuine, reproducible Python-2.7 path/bytes ambiguity defect discovered during Gate 2A
(`SFM_MASTER_SIDECAR_GATE2A_CANDIDATE_A_EMBEDDED_BASELINE_AUDIT.md`) has been fixed by removing all
type-based input dispatch from `tools/sfm_master_sidecar/reader.py` and replacing it with explicit,
unambiguous entry points. The fix was verified in three independent ways: the full repository test suite
(411 passed, 0 failed, 255 subtests, up from the pre-fix 395/255 baseline), the official artifact identity
reproduced exactly unchanged, and — the evidence that actually matters — a complete requalification run
inside the real embedded Python 2.7.5 interpreter in `sfm.exe`, proving both the new explicit path-open entry
point and the new explicit bytes-open entry point succeed and agree, and that all 18 original Gate 1 H1
behavioral checks still pass against the corrected file.

## 2. ROOT CAUSE

`reader.py`'s `_read_all(path_or_bytes)` used `isinstance(path_or_bytes, (bytes, bytearray))` to decide
whether its argument was raw artifact content or a filesystem path to open. Under Python 2.7, `bytes` **is**
`str` — there is no distinct native byte-string type separate from `str` — so an ordinary path string always
satisfies that `isinstance` check and was always treated as if its characters WERE the artifact's own bytes,
never reaching the `open(path, "rb")` branch. This is not an edge case or a rare input shape: it is
categorical and 100% reproducible for every path-string argument, on every call, under Python 2.7. It was
invisible throughout B2B–B2E and the original Gate 1 H1 run because:
- Every B2B–B2E test ran under Python 3, where `str` and `bytes` are genuinely distinct types, so the same
  `isinstance` check correctly distinguishes them there — masking the defect completely on that runtime.
- The original Gate 1 H1 probe always passed already-decoded `bytes` (from a base64 literal) to
  `open_generation`, never a path string, so it never exercised the ambiguous branch at all.
- Production `compiler.py` itself had one path-string call site
  (`self_validate_from_path`, passing `str(artifact_path)`) that "worked" only because `compiler.py` is
  Python-3-only and has never run under Python 2.7.

**Why the ambiguity is inherent to Python 2, not merely an unlucky implementation choice:** any type-based
check attempting to distinguish "this `str`/`bytes` value is a path" from "this `str`/`bytes` value is raw
content" is fundamentally unable to do so on Python 2.7, because both are represented by the exact same
builtin type. No refinement of the `isinstance` check (checking length, checking for a magic-looking prefix,
checking for path separators, retry-on-failure) can close this gap without becoming an ambiguous heuristic —
which this fix's own governing instructions explicitly ruled out.

## 3. OLD AMBIGUOUS API BEHAVIOR

```python
def _read_all(path_or_bytes):
    if isinstance(path_or_bytes, (bytes, bytearray)):
        return bytes(path_or_bytes)
    f = open(path_or_bytes, "rb")
    ...
```
called from a single `open_generation`/`open_generation_unbound` pair that accepted either a path or bytes
under one shared argument name and dispatched by type alone.

## 4. CHOSEN EXPLICIT PATH/BYTES CONTRACT

No type-based dispatch remains anywhere in `reader.py`. Two small, explicit helper functions replace
`_read_all`:

- `_coerce_bytes(data)` — always treats `data` as already-loaded bytes; raises `TypeError` if `data` is not
  actually `bytes`/`bytearray` (a real, useful check on Python 3, where `str` and `bytes` are distinct; on
  Python 2.7 this check cannot catch a mistaken path string, since it IS `bytes` there too — which is exactly
  why the explicit-entry-point split, not a smarter type check, is the actual fix).
- `_read_path(path)` — always calls `open(path, "rb")` unconditionally; the only function in the module that
  ever touches the filesystem.

Four new explicit public classmethods on `SidecarReader`:

| Method | Input | Authority |
|---|---|---|
| `open_generation_bytes(data, expected_source_sha256)` | bytes/bytearray | bound |
| `open_generation_path(path, expected_source_sha256)` | filesystem path | bound |
| `open_generation_unbound_bytes(data)` | bytes/bytearray | diagnostic only |
| `open_generation_unbound_path(path)` | filesystem path | diagnostic only |

The legacy names are **retained as explicitly-documented bytes-only aliases** — never a path, on any Python
version, regardless of the argument's runtime type:

```python
@classmethod
def open_generation(cls, data, expected_source_sha256):
    """Legacy alias for open_generation_bytes -- explicitly BYTES-ONLY..."""
    return cls.open_generation_bytes(data, expected_source_sha256)

@classmethod
def open_generation_unbound(cls, data):
    """Legacy alias for open_generation_unbound_bytes -- explicitly BYTES-ONLY..."""
    return cls.open_generation_unbound_bytes(data)
```

This choice (smallest coherent API, per the governing instruction) required **zero changes** to the ~85
existing test call sites that already only ever passed bytes — their behavior is unchanged and now
unambiguous by construction, not merely by convention. Passing a path string to the legacy alias is still
safely rejected on both runtimes (never silently opens the file) — see Section 8's regression test, which
proves this explicitly rather than assuming it.

## 5. PRODUCTION CALL-SITE MIGRATION

Both actual production call sites (the only two found by inventorying every caller of `open_generation`/
`open_generation_unbound`/`_read_all` across `tools/` and `tests/` — Part 2's required inventory) now state
their intent explicitly:

| Site | Before | After |
|---|---|---|
| `compiler.self_validate_from_bytes` | `open_generation(outcome.blob, ...)` | `open_generation_bytes(outcome.blob, ...)` |
| `compiler.self_validate_from_path` | `open_generation(str(artifact_path), ...)` | `open_generation_path(str(artifact_path), ...)` |

Four test call sites that were passing a path (`test_custom_master_gate1.py` ×2, `test_publisher.py`,
`test_publisher_concurrency.py`) were migrated to `open_generation_path` for the same reason — every
remaining call site in the repository that passes bytes was deliberately left on the legacy alias, since it
is now unambiguous.

No Python-3-only compiler/publisher/manifest/CLI code was merged into the Python-2.7-safe runtime surface;
`format.py`/`reader.py` remain the only two modules exercised under Python 2.7, unchanged in that boundary.

## 6. CANDIDATE A / BINARY IDENTITY PRESERVED

No change to `format.py`, `writer.py`, section layout, versions, or serialization order. Candidate A's own
semantics (one complete immutable byte buffer retained; validation and queries operate on those same
retained bytes) are untouched — this fix only changes HOW the buffer is obtained (bytes handed in directly,
vs. read once from a path), never what happens to it afterward. Recompiled the official Master through the
unchanged public compiler after the fix:

- Source SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` — matches.
- **Artifact SHA-256: `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` — matches exactly,
  unchanged.**
- Artifact size: 9,506,244 bytes — unchanged.

## 7. PYTHON 3 REGRESSION EVIDENCE

New file `tests/sidecar/test_reader_path_bytes_input.py` (16 tests, confirmed by
`pytest --collect-only`; this is also the exact net increase in the full-repository suite total below —
395 + 16 = 411, since the three other modified test files only changed existing call sites and added or
removed no test methods, confirmed by an unchanged `def test_` count in each): explicit bytes-open success and
type-rejection; explicit path-open success, rejection of a nonexistent path, and proof that path TEXT is
never misread as content; full path-vs-bytes semantic equivalence (group/occurrence enumeration, Hit/
FoldConflict lookup agreement) on a real compiled fixture; checksum-failure, source-mismatch, and
close-lifetime parity between the two entry points; and explicit proof that the legacy `open_generation`/
`open_generation_unbound` aliases remain bytes-only (including a direct proof, via `inspect.getsource`, that
they delegate to the `_bytes` methods rather than duplicating logic that could drift back into ambiguity).

## 8. REAL SFM PYTHON 2 PATH-OPEN EVIDENCE

Executed inside the real embedded Python 2.7.5 (32-bit) interpreter in `sfm.exe`
(`E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\sfm.exe`) via the same already-proven
`usermod\scripts\sfm\autoinit\` mechanism used for the original H1 run:

```
--- EXPLICIT PATH-OPEN (open_generation_path) ---
open_generation_path: PASS, is_valid=True
```

This is the EXACT call shape (`open_generation_path(<path string>, expected_source_sha256)`) that Gate 2A
found broken under the pre-fix code. It now succeeds.

## 9. REAL SFM PYTHON 2 BYTES-OPEN EVIDENCE

```
--- EXPLICIT BYTES-OPEN (open_generation_bytes) ---
open_generation_bytes: PASS, is_valid=True
```

## 10. PATH/BYTES EQUIVALENCE (REAL SFM PYTHON 2)

```
group_count equal: True (4 == 4)
occurrence_count equal: True (8 == 8)
iter_groups() lists equal: True
iter_occurrences() lists equal: True
lookup_fold(u'Alpha'): bytes=Hit(...) path=Hit(...) same_type=True
lookup_fold(u'foo'): bytes=Hit(...) path=Hit(...) same_type=True
lookup_fold(u'Bar'): bytes=FoldConflict(...) path=FoldConflict(...) same_type=True
lookup_fold(u'bar'): bytes=FoldConflict(...) path=FoldConflict(...) same_type=True
```

Full group/occurrence enumeration and every tested lookup (including both the same-destination alias family
and the cross-destination conflict) agree exactly between the two entry points, in the real target runtime.

**Legacy alias behavior, also directly confirmed in real Python 2.7** (not merely inferred from Python 3):
passing the SAME path string to the legacy `open_generation` raised `AuthorityUnavailable` ("magic mismatch")
— a DIFFERENT exception type than Python 3 produces for the identical call (`TypeError`, since `_coerce_bytes`
can distinguish `str` from `bytes` there), but the same essential guarantee holds on both runtimes: **the
file is never opened, and no path is ever silently misread.** This is the expected, correct consequence of
the fundamental Python 2/3 type-system difference, not a residual bug — documented explicitly, not silently
smoothed over.

## 11. COMPLETE H1 REQUALIFICATION

All 18 original Gate 1 H1 checks were re-run against the newly-corrected, byte-verified `reader.py`, inside
real embedded Python 2.7.5, in one combined probe alongside the new path/bytes checks:

**18 / 18 original checks: PASS** — import, ordinary HIT, same-destination alias family (complete evidence),
cross-destination FoldConflict, exact-spelling-inside-conflict (still FoldConflict, never Hit), MasterUnknown
(never substituted for an error), full group/metadata/occurrence iteration, ASCII-only byte-fold with
non-ASCII bytes and backslash-escape spelling both preserved exactly, checksum-invalid rejection (now proven
for BOTH the bytes and path entry points), source-mismatch rejection (both entry points), and the full
close/close/post-close/lazy-after-close lifecycle sequence.

**3 new checks: PASS** — explicit path-open, explicit bytes-open, path/bytes semantic equivalence (Sections
8–10).

**Total: 21 / 21 required behaviors PASS**, zero uncaught exceptions, in the real target runtime.

## 12. UNCHANGED ARTIFACT IDENTITY

Reconfirmed in Section 6: `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`, exactly as
before the fix. This is direct proof the fix touched only input-handling code, never serialization.

## 13. FULL REPOSITORY REGRESSION

- `python -m pytest tests/ -q` → **411 passed, 0 failed, 255 subtests passed** (prior baseline: 395 passed,
  255 subtests; the 16-test delta is exactly `test_reader_path_bytes_input.py`, the new regression file —
  no other test count changed).
- Validator: PASS, all canonical facts unchanged (43 groups, 128,555 controls, 124,728 fold keys, 0
  duplicates, 0 cross-path conflicts).
- `git diff --check`: clean.
- B2A oracle parity (`test_official_master_oracle_parity.py`): 7 passed, 81 subtests passed.
- B2C corruption matrix (8 files): 123 passed, 6 subtests passed.
- B2D full official parity (4 files): 54 passed, 5 subtests passed.
- B2E publication/compiler suite (7 files): 77 passed, 59 subtests passed.

No regression anywhere.

## 14. PRODUCTION FILES CHANGED

- `tools/sfm_master_sidecar/reader.py` — the fix itself (Sections 2–4). New SHA-256:
  `d79f7ae87c1999b7fe728f7dd6ddafb29b7cc62c246cd332f061875095288b00` (was
  `dd1e5da29058394c99e37f5eeaffd262c0b07421d052661ca51b06f1e11e7b02`).
- `tools/sfm_master_sidecar/compiler.py` — the two call-site updates (Section 5). No format/writer/manifest/
  publisher/CLI code was touched.

## 15. TEST FILES CHANGED / CREATED

- Created: `tests/sidecar/test_reader_path_bytes_input.py` (Section 7).
- Updated (path-caller migration only, Section 5): `tests/sidecar/test_custom_master_gate1.py`,
  `tests/sidecar/test_publisher.py`, `tests/sidecar/test_publisher_concurrency.py`.

## 16. CLEANUP

- `usermod\scripts\sfm\autoinit\zz_h1rerun_probe_temp.py` — removed.
- `usermod\scripts\sfm_master_sidecar_h1rerun_runtime\` (temporary corrected-reader.py copy) — removed
  entirely.
- `usermod\scripts\h1rerun_temp_artifact\` (valid + checksum-invalid fixture artifacts) — removed entirely.
- `usermod\scripts\sfm\sfm_init.py` — confirmed byte-for-byte unchanged.
- No new crash dump appeared.
- SFM closed after the run (a fresh instance launched solely for this requalification, per the same pattern
  as the original H1/Gate 2A runs).
- No launch-option or SFM configuration changes were made or left behind.
- No manifest/publisher-lock file was ever created (the artifact was opened directly, never through
  `publisher.publish`).

## 17. GIT / SAFETY STATE

- `sfm_defaultanimationgroups.txt`: unchanged, SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`.
- `tools/sfm_master_core.py`, `tools/validate_master.py`: unchanged.
- `tools/sfm_master_sidecar/{format,writer,manifest,publisher,cli,__init__}.py`: unchanged (empty `git diff`
  on each) — only `reader.py` and `compiler.py` were modified, exactly as this fix required and nothing
  more.
- No Normalizer code touched. No Gate 2 resource measurement resumed or attempted.
- Nothing staged, nothing committed (pending separate authorization).
- No agents or subagents were used.
