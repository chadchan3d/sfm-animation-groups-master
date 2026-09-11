# SFM Master Sidecar — Final Gate 1 Qualification Consolidation

Qualification only. No new architecture, no binary-format change, no source-semantic change, no Normalizer
integration, no Gate 2 work, no format v1 freeze, no runtime installed/downloaded. No production code was
modified during this pass.

## 1. VERDICT

**GATE 1 QUALIFIED EXCEPT FOR EXTERNAL ENVIRONMENT EVIDENCE.**

**Revised in the reconciliation pass (see Section 23):** the current, explicitly-adopted public-compiler
support contract is **Windows only, CPython 3.10.x only** (no broader OS or Python-3-minor-version range has
ever been documented, tested, or promised anywhere in this project's history). Under that honestly-scoped
contract, cross-OS determinism and cross-Python-3-minor-version determinism are both **NOT REQUIRED FOR
GATE 1** — they are not mandatory items for a contract that does not itself claim that breadth. This leaves
exactly **one** remaining mandatory Gate 1 blocker: **H1, real Python 2.7 execution of the reader**, still
genuinely OPEN (no interpreter available; none installed, per explicit instruction).

Every implementation/correctness requirement this project controls has actual, current, re-verified
evidence: 395 tests / 255 subtests passing, the validator PASS, the official artifact reproducing its exact
qualified SHA through the public compiler, and every phase-critical suite (B2A oracle parity, B2C corruption
matrix, B2D full official parity, B2E publication/concurrency/custom-compiler) re-run fresh and passing at
full, non-sampled strength. No test failed. No defect was found. Per this task's own Part 11 rule, "all
implementation work PASS, one or more required environmental executions currently unavailable" is exactly
"GATE 1 QUALIFIED EXCEPT FOR EXTERNAL ENVIRONMENT EVIDENCE," not GATE 1 PASS and not GATE 1 FAIL — and that
single remaining required execution is now precisely identified as H1 alone.

## 2. QUALIFIED BASELINE / COMMIT

- HEAD: `1c05db9f8ef06e52c27a7f6205be21a358447c76` (the B2E checkpoint commit), unchanged throughout this pass.
- Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`, unchanged.
- `git status` before and after this pass: identical (only the single pre-existing, unrelated
  `tools/extract_phase2_human_review.py` untracked file, present since before Phase B2A and not touched by
  this or any sidecar-compiler phase).

## 3. GATE 1 REQUIREMENT MATRIX

| # | Category | Requirement | Status | Evidence |
|---|---|---|---|---|
| A1 | Source authority | Shared semantic core (`sfm_master_core.py`) | **PASS** | Unchanged since B0.1; 395/395 tests pass against it |
| A2 | Source authority | Source completeness (every token classified or reported) | **PASS** | B0.1 hardening; re-verified via full suite |
| A3 | Source authority | Wrapper/path identity (wrapper is an ordinary Group, paths wrapper-inclusive) | **PASS** | B2D Section 9: `groupFile/Face/Eyes` exact in all three of core/oracle/reader |
| A4 | Source authority | Exact UTF-8 / escape behavior (never unescaped, never re-escaped) | **PASS** | B1.2 escape-wording fix; B2D Section 19 full 128,555-literal round-trip |
| B1 | Independent oracle | Full official population parity | **PASS** | B2A: 43 groups / 128,555 occurrences / 54 metadata, exhaustive, zero mismatches |
| B2 | Independent oracle | Custom/adversarial fixtures (28 valid, 2 unsupported, 10 malformed) | **PASS** | B2A corpus, unchanged, still passing |
| B3 | Independent oracle | Completeness projections (first/middle/tail/coverage) | **PASS** | B2A `test_oracle.py` self-discipline tests; B2D Section 20 |
| C1 | Format/writer/reader | Deterministic layout | **PASS** | B2B; re-confirmed same-process + cross-`PYTHONHASHSEED` in this pass (B2D/B2E suites) |
| C2 | Format/writer/reader | Exact round-trip (28/28 fixtures + official Master) | **PASS** | B2B, B2D |
| C3 | Format/writer/reader | Source binding (exact digest, no prefix match) | **PASS** | B2C/B2D/B2E `SourceMismatchError` tests, all re-run passing |
| C4 | Format/writer/reader | Fold semantics (Hit/FoldConflict/MasterUnknown, never conflated) | **PASS** | B2B/B2C/B2D/B2E, exhaustive |
| C5 | Format/writer/reader | Metadata/occurrence preservation (order, duplicates, legal semantics) | **PASS** | B2B/B2C/B2D |
| D1 | Integrity | Embedded checksum (computed/verified correctly, checked before structural checks) | **PASS** | B2C's digest-ordering fix, re-verified in this pass |
| D2 | Integrity | Checksum-valid structural corruption rejected (71/71 cases) | **PASS** | B2C, re-run in this pass: 123 tests / 6 subtests, 0 failures |
| D3 | Integrity | Complete slices/permutations (never sampled) | **PASS** | B2B/B2C Section 20 A-J, re-verified |
| D4 | Integrity | Lifecycle invalidation/cleanup (VALID/INVALID/CLEANED, exactly-once) | **PASS** | B2C/B2D lifecycle tests, re-run passing |
| D5 | Integrity | Resource limits (rejected before dangerous allocation) | **PASS** | B2C, re-run passing |
| E1 | Official full-scale parity | 43/43 groups | **PASS** | B2D, re-run in this pass |
| E2 | Official full-scale parity | 42/42 child-index references | **PASS** | B2D, re-run in this pass |
| E3 | Official full-scale parity | 54/54 metadata entries | **PASS** | B2D, re-run in this pass |
| E4 | Official full-scale parity | 128,555/128,555 occurrences | **PASS** | B2D, re-run in this pass |
| E5 | Official full-scale parity | 124,728/124,728 fold families | **PASS** | B2D, re-run in this pass |
| E6 | Official full-scale parity | All known-fold lookups HIT | **PASS** | B2D: 124,728/124,728, re-run |
| E7 | Official full-scale parity | Exact-literal lookup coverage | **PASS** | B2D: 128,555/128,555, re-run |
| E8 | Official full-scale parity | Independent oracle parity at full scale | **PASS** | B2D, re-run in this pass |
| F1 | Public custom compiler | Same compiler path for official and custom | **PASS** | B2E Section 3; verified no branch exists anywhere in code |
| F2 | Public custom compiler | Custom wrapper / duplicate controls / conflicts / UTF-8 / metadata | **PASS** | B2E `test_custom_master_gate1.py`, 13 representative fixtures, re-run |
| F3 | Public custom compiler | Combined custom Gate-1A source, exhaustive parity | **PASS** | B2E Part 22 fixture; re-confirmed in this pass (Section 10 below) |
| G1 | Publication | Immutable generation naming/reuse/collision-refusal | **PASS** | B2E; re-confirmed live in this pass (Section 9 below) |
| G2 | Publication | Manifest build/hardened-parse | **PASS** | B2E; re-run passing |
| G3 | Publication | Source recheck / stale-source refusal | **PASS** | B2E; re-confirmed live in this pass |
| G4 | Publication | Atomic manifest activation | **PASS** | B2E; re-run passing |
| G5 | Publication | Publisher locking (real OS-backed, crash-safe) | **PASS** | B2E; re-run passing (real subprocess kill test) |
| G6 | Publication | Concurrent publishers never corrupt the namespace | **PASS** | B2E; re-run passing (real subprocess race test) |
| G7 | Publication | Crash/failure preservation (prior manifest survives) | **PASS** | B2E; re-confirmed live in this pass |
| G8 | Publication | Generation reuse (no duplicate churn) | **PASS** | B2E; re-confirmed live in this pass |
| H1 | Runtime compatibility | Real Python 2.7 execution of the reader | **OPEN — ENVIRONMENT UNAVAILABLE** | No interpreter found (Section 14) |
| I1 | Determinism environments | Cross-Python-3-minor-version identical output | **NOT REQUIRED (revised, Section 23)** | Current contract: CPython 3.10.x only — no range claimed |
| I2 | Determinism environments | Cross-OS identical output | **NOT REQUIRED (revised, Section 23)** | Current contract: Windows only — SFM/EXE target is Windows-only |

**Mandatory Gate 1 items (revised): 35 of 36 mandatory rows PASS. 1 row (H1) OPEN — ENVIRONMENT
UNAVAILABLE. Zero FAIL rows. I1/I2 are explicitly NOT mandatory under the current, honestly-scoped
support contract (Section 23) and are excluded from the mandatory PASS/OPEN/FAIL count — they remain
listed for traceability, not because they block this verdict.**

## 4. SOURCE SEMANTICS

Unchanged since B0.1, re-verified in this pass by the full suite (395/395 pass, including every
`sfm_master_core`-dependent test). No source-semantic code was touched by this consolidation pass — `git
diff` against `tools/sfm_master_core.py` is empty.

## 5. INDEPENDENT ORACLE

`tests/sidecar/oracle.py` unchanged; re-run fresh in this pass both alone
(`test_official_master_oracle_parity.py`: 7 tests, 81 subtests, 0 failures) and as part of the full suite. No
oracle expectation was adjusted at any point in this pass.

## 6. FORMAT / WRITER / READER

`tools/sfm_master_sidecar/{format,writer,reader}.py` unchanged (confirmed via empty `git diff` on each).
Deterministic layout, exact round-trip, source binding, and fold semantics all re-verified passing via the
full suite and the explicit phase-critical reruns (Section 3 rows C1-C5).

## 7. STRUCTURAL INTEGRITY

The full B2C checksum-valid structural-corruption matrix was re-run in isolation in this pass:
`test_structural_corruption_{header,strings,groups,occurrences,folds}.py` +
`test_reader_invalidation.py` + `test_resource_limits.py` + `test_writer_representability.py` →
**123 passed, 6 subtests passed, 0 failed** — the same 71 checksum-valid-rejection / 2 checksum-invalid /
2 documented-non-violation composition established in B2C, unweakened and unsampled.

## 8. LIFECYCLE / RESOURCE SAFETY

Re-confirmed via the same B2C suite rerun (Section 7): VALID/INVALID/CLEANED lifecycle, the
invalidate-close-close required test, lazy-object invalidation across every exposed accessor, and all 7
resource-limit checks (group/occurrence/fold/string counts, metadata-per-group, single-string length,
string-pool total bytes) all pass.

## 9. OFFICIAL FULL-SCALE PARITY

Re-run fresh in this pass: `test_official_master_full_compile.py` + `test_official_master_determinism.py` +
`test_official_master_semantic_parity.py` + `test_official_master_fold_parity.py` → **54 passed, 5 subtests
passed, 0 failed** in 72.31s. All full-scale counts (43 groups / 42 children / 54 metadata / 128,555
occurrences / 124,728 folds / 124,728 known-fold HITs / 128,555 exact-literal-lookup coverage) reconfirmed
exactly as in the original B2D pass, with zero drift.

**Publication evidence, reconfirmed live in this pass (temporary namespace, fully cleaned up afterward, no
persistent output):**
- Published the official Master twice to one temp namespace: first call `reused=False`, second call
  `reused=True`, identical generation basename
  `sfm_master_0_bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b.bin` both times.
- Manifest readback: parsed via the production hardened parser, generation basename safely resolved,
  ordinary SHA-256 of the on-disk generation file independently re-verified against the manifest's own
  `sidecar_sha256`, and the generation reopened via the production reader with `is_valid()` confirmed True.
- Failure injection at `before_manifest_replace` while attempting to publish a different (fixture) source:
  raised as expected; the ORIGINAL (official-Master) active manifest was confirmed byte-identical
  before/after the failed attempt.
- Source-mutation race (a separate temp source path, mutated from one B2A fixture to another immediately
  before the live-source recheck via the `before_source_recheck` fault hook): `SourceMutatedDuringPublicationError`
  raised as expected; activation aborted.
- The temp namespace directory itself no longer exists after this reconfirmation script completed
  (`Path(tmp).exists()` confirmed `False`).

## 10. CUSTOM MASTER PARITY

Re-run fresh in this pass as part of the B2E suite rerun (`test_custom_master_gate1.py`, included in the
77-passed/59-subtest B2E rerun in Section 3's evidence): the combined custom Gate-1A fixture
(`tests/sidecar/fixtures/custom_gate1/combined_custom_master.txt`) — custom wrapper `CustomRoot`, 3-level
nesting plus sibling groups, ordered metadata across 3 groups including one unknown key, a duplicate control
occurrence, a same-destination 3-spelling ASCII alias family, a genuine cross-destination `FoldConflict`,
non-ASCII UTF-8, and a preserved backslash-escape spelling — compared exhaustively across
`sfm_master_core`, the independent B2A oracle, the writer, the reader, and the public compiler
orchestration. Zero mismatches, exactly as first established in B2E.

## 11. PUBLIC COMPILER

`tools/sfm_master_sidecar/{compiler,manifest,publisher,cli}.py` unchanged (confirmed via empty `git diff` on
each). The 13-fixture representative custom-Master sweep (`CustomMasterPublicCompilerTests`, part of the
B2E rerun) and the CLI exit-status/outside-repo/source-immutability suites (`test_cli.py`, same rerun) all
pass unchanged.

## 12. PUBLICATION / MANIFEST / LOCKING

Re-run fresh in this pass as part of the B2E suite rerun: `test_publisher.py`, `test_publication_failures.py`,
`test_publisher_concurrency.py` — all passing, including the real-subprocess lock-crash-safety test
(a killed holder process, immediate reacquisition by a fresh lock object) and the real-two-subprocess
concurrent-publish race test (both generations survive on disk, the final manifest is complete valid JSON
referencing an existing, reopenable generation). Additionally directly reconfirmed live in this pass
(Section 9) using the official Master itself, not only B2A fixtures.

## 13. OFFICIAL ARTIFACT IDENTITY

Reconfirmed through the public compiler's `check_only` path in this pass (no output namespace touched at
all):

- **Source SHA-256:** `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` — **matches**.
- **Artifact (sidecar) SHA-256:** `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` — **matches**.

No drift of any kind was observed. Both digests were also independently reconfirmed via a live `publish()`
call to a temporary namespace (Section 9), producing the identical generation basename.

## 14. PYTHON 2.7 REAL-EXECUTION STATUS

**Available: NO.** Conservative search performed, no installation/download attempted, per explicit
instruction:

- `py -0` (the Python Launcher for Windows' own registry of installed versions): lists only `-V:3.10`.
- `py -2 --version`: falls through to Python 3.10.6 (the launcher has no `-2` mapping registered; it silently
  ran the only version it knows about instead of failing outright).
- `where python2` / `where python2.7` / `where python27`: all report "Could not find files for the given
  pattern(s)."
- No `C:\Python27`, `C:\Program Files\Python27`, `C:\Program Files (x86)\Python27`, or
  `%LOCALAPPDATA%\Programs\Python\Python27` directory exists.
- `%LOCALAPPDATA%\Programs\Python\` contains only a `Python310` subdirectory (confirmed by direct listing).
- No `conda` or `pyenv` executable found on `PATH`.
- The `PATH` environment variable does contain a `Python311` entry, but the directory it points to does not
  exist on disk (a stale/orphaned PATH entry, not a real interpreter) — checked directly and explicitly
  rejected as evidence rather than assumed usable.

**Status: OPEN — ENVIRONMENT UNAVAILABLE.** No interpreter was installed, downloaded, or bundled, per
explicit instruction. Static/import-discipline evidence (`test_runtime_import_boundary.py`, unchanged since
B2B, still passing under Python 3) remains supporting evidence only and is NOT substituted for real
execution anywhere in this document.

## 15. PYTHON 3 DETERMINISM STATUS

**Revised in the reconciliation pass — see Section 23 for the full support-contract analysis.**

No project document anywhere (the final implementation spec, any phase audit, or any module docstring) ever
declared a specific minimum Python 3 minor version or a range of supported minor versions — every reference
was the generic phrase "Python 3" or the final spec's Gate 1A aspiration ("at least two distinct Python 3
minor-version/OS environments," Section 38 — a robustness-proof goal, not a support-contract declaration).
This pass formally adopts, for the current experimental pre-v1 compiler, the contract **CPython 3.10.x
only** (the exact line actually built and tested throughout B0-B2E), reasoned in full in Section 23.

**Locally available environments:** `py -0` and direct filesystem inspection confirm exactly ONE genuine
Python 3 installation exists on this machine: Python 3.10.6, 64-bit, AMD64, at
`C:\Users\REDACTED\AppData\Local\Programs\Python\Python310\python.exe`. The `Python311` entry present in `PATH`
does not correspond to an installed interpreter (Section 14) and was not used as evidence.

**Status: NOT REQUIRED FOR GATE 1** (revised from OPEN). Under the now-explicit single-minor-version
contract, there is no second "supported minor" to cross-test against, so cross-minor-version determinism is
not a mandatory Gate 1 item — a product that claims to support exactly one interpreter line cannot
meaningfully fail a "does it agree across supported versions" test. Same-process and
cross-`PYTHONHASHSEED`-subprocess determinism (a genuinely different, already-fully-PASSing axis — hash-seed
independence, not interpreter-version independence) remain re-verified in this pass (identical official-Master
artifact SHA across `PYTHONHASHSEED=0` and `PYTHONHASHSEED=999983`). **This classification is reversible:**
if the project ever declares or needs a broader range (e.g., "CPython 3.9-3.12"), that broader claim
immediately reopens the requirement for actual multi-version testing evidence before it can be honestly
made — nothing in this document forecloses that.

## 16. PLATFORM SUPPORT / CROSS-OS STATUS

**Revised in the reconciliation pass — see Section 23 for the full support-contract analysis.**

`tools/sfm_master_sidecar/publisher.py` contains two lock implementations selected by `sys.platform`: a
`msvcrt`-based Windows branch (the one actually exercised, on this `win32` environment) and an
`fcntl`-based POSIX branch (present in the source, never executed by any test in this project's history, and
never promised as supported by any project document). This pass formally adopts, for the current
experimental pre-v1 compiler, the contract **Windows only** — reasoned in full in Section 23 from the
project's own stated context: SFM (the sole real consumer) is a Windows-target application, and the
compiler's own intended eventual packaging is a standalone Windows executable.

**Status: NOT REQUIRED FOR GATE 1** (revised from OPEN). Given the Windows-only contract, the POSIX branch
is correctly understood as incidental, unqualified, out-of-contract code — its mere presence does not create
a cross-platform support obligation this project never made. Per this task's own Part 3 instruction ("if
current public support is legitimately Windows-only: cross-OS determinism = NOT REQUIRED FOR GATE 1"), this
is the correct classification once the contract is honestly stated rather than inferred from dormant code.
**This classification is reversible:** if the project later decides to support Linux/macOS (e.g., for a
cross-platform CLI release independent of the Windows EXE), that decision immediately reopens the
requirement for real POSIX execution evidence before such support can be honestly claimed.

## 17. COMPLETE TEST RESULTS

Fresh, full re-run in this pass: `python -m pytest tests/ -q` → **395 passed, 0 failed, 255 subtests passed**
in 122.78s. Explicit phase-critical subset reruns (all included in the total above, also run standalone for
clarity):

| Suite | Result |
|---|---|
| B2A official oracle parity (`test_official_master_oracle_parity.py`) | 7 passed, 81 subtests passed |
| B2C corruption matrix (8 files) | 123 passed, 6 subtests passed |
| B2D full official parity (4 files) | 54 passed, 5 subtests passed |
| B2E publication/concurrency/custom compiler (7 files) | 77 passed, 59 subtests passed |

No test was skipped, weakened, or sampled to obtain these results.

## 18. VALIDATOR

`python tools/validate_master.py sfm_defaultanimationgroups.txt` → **PASS**. Groups=43, controls=128,555,
unique ASCII-fold keys=124,728, exact duplicate literals=0, cross-path (invariant violation)=0 — all
unchanged from every prior phase's baseline.

## 19. OPEN EXTERNAL EVIDENCE

**Revised in the reconciliation pass (Section 23):** with cross-OS and cross-Python-3-minor-version both
reclassified NOT REQUIRED under the now-explicit Windows-only/CPython-3.10.x-only current support contract,
exactly **one** item remains open:

1. **Real Python 2.7 execution** of `format.py`/`reader.py` (Section 14) — the single remaining Gate 1A gap,
   and now the sole remaining mandatory Gate 1 blocker of any kind.

This is environmental (requires a resource — a Python 2.7 interpreter, or access to SFM's own embedded one —
not currently exercised) rather than a correctness defect. No implementation code is implicated. Section 23
assesses whether SFM's own embedded Python 2.7 could serve as a stronger, narrower evidence path than an
unrelated standalone install, without beginning any Gate 2 work.

## 20. EXPLICITLY POST-GATE-1 WORK

The following are explicitly NOT Gate 1 blockers and are not evaluated by this audit:

- Embedded SFM x86 memory/VAS behavior, open-time latency, and input-string conversion cost (final spec
  Section 42, Gate 2 deferred measurements).
- Generation-overlap cost during a hot-swap inside a running SFM process (Gate 2).
- The Candidate A vs. B vs. C backing comparison (Gate 2 — only Candidate A is built or required for Gate 1,
  per the final spec's own explicit scoping, unchanged since B1.2).
- The Normalizer adapter/provider seam and any real consumer-contract check against the actual Normalizer
  (final spec Section 43/44 — explicitly deferred past Gate 1 by the spec itself).
- Format v1 freeze (final spec Section 44's milestone sequence places this strictly after Final Gate 1 PASS
  AND a Gate 2 measurement AND the Normalizer check — none of which have occurred).

## 21. GATE 2 READINESS

**Revised:** once the single remaining environmental gap (Section 14 — real Python 2.7 execution) is
closed — by locating an already-available interpreter (standalone, or via SFM's own embedded Python 2.7, see
Section 23), or by separate future authorization to provision one — Final Gate 1 PASS can be declared
without any further implementation work, since every correctness requirement this project controls already
has current, passing, non-sampled evidence, and both determinism-environment items (I1/I2) are no longer
mandatory blockers under the now-explicit support contract. Gate 2's own scope (Section 20) has not been
started and is not claimed as started anywhere in this document.

## 22. GIT / SAFETY STATE

- `sfm_defaultanimationgroups.txt`: unchanged, SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`.
- `tools/sfm_master_core.py`, `tools/validate_master.py`: unchanged.
- `tools/sfm_master_sidecar/{format,writer,reader,compiler,manifest,publisher,cli,__init__}.py`: all
  unchanged (empty `git diff` on every file).
- `tests/sidecar/oracle.py`, `fixtures/`, `fixture_manifest.json`: unchanged.
- No Normalizer integration, no SFM installation change, anywhere in this pass.
- No persistent generated sidecar/manifest/publication artifact exists anywhere in the repository or in any
  temp location this pass created (every temp directory used for reconfirmation was removed at the end of
  its own script; confirmed via `find . -iname "*.bin"` / `*.json` / `*.lock` returning nothing outside
  `.git/`).
- `git diff --check`: clean.
- HEAD unchanged: `1c05db9f8ef06e52c27a7f6205be21a358447c76`.
- `git status`: identical to the pre-pass baseline (only the single pre-existing unrelated untracked file,
  `tools/extract_phase2_human_review.py`, PLUS this audit document itself and every other historical
  untracked file already present in the repository root before Phase B2A began — see Section 23.1 for the
  full explanation of why an earlier report of this fact was imprecise).
- No agents or subagents were used.

## 23. RECONCILIATION ADDENDUM (support-contract + audit-file git-state + Python 2.7 path assessment)

### 23.1 Audit-file Git-state reconciliation

**No real contradiction exists.** `SFM_MASTER_SIDECAR_FINAL_GATE1_AUDIT.md` is, and always was after its
creation, **untracked** (correct — no commit was authorized for that pass), present on disk, and unmodified
since creation:

```
git status --short --untracked-files=all   -> "?? SFM_MASTER_SIDECAR_FINAL_GATE1_AUDIT.md" (present, listed)
git ls-files --error-unmatch <file>          -> error: pathspec did not match any file (confirms: untracked)
git check-ignore -v <file>                   -> exit 1, no output (confirms: NOT ignored)
git diff -- <file>                           -> empty (confirms: no tracked baseline to diff against; file
                                                  itself unchanged since it was written)
```

The apparent contradiction traces to an imprecise verification command in the prior pass's final report: its
"production files unchanged" and "git status" checks were run as `git status --porcelain=v1 -- tools tests
sfm_defaultanimationgroups.txt` — a **path-scoped** query restricted to exactly those three arguments. That
scope never included the repository root, so it could never have shown the newly-written root-level audit
file (or, for that matter, any of the dozens of other pre-existing untracked root-level historical report
files from earlier project phases). Reporting that scoped output as if it were the complete git status was
this session's own imprecision, not a real inconsistency in repository state. No ignore rule was found or
changed; the file was never at risk of being silently dropped.

### 23.2 Actual public compiler support contract

**What is explicitly promised today:** nothing, in writing, beyond the generic phrase "Python 3" in module
docstrings (`compiler.py`, `manifest.py`, `publisher.py`, `cli.py`) and the final spec's Gate 1A aspiration
of testing "at least two distinct Python 3 minor-version/OS environments" (a robustness-proof goal for
Gate 1, never phrased as a support-contract declaration for end users).

**What is merely technically implemented:** `publisher.py`'s `_ExclusiveFileLock` has a complete,
parallel POSIX (`fcntl`) branch alongside its Windows (`msvcrt`) branch. `manifest.py`/`compiler.py`/
`writer.py` use only `pathlib`/`os`/`hashlib`/`json`/`struct` — nothing Windows-specific beyond the lock
module. This makes the CODE portable in principle, but portability-in-principle is not the same as a
declared, tested support commitment.

**What is qualified by tests:** exclusively Windows (`win32`), exclusively CPython 3.10.6. Every real
subprocess test (lock crash-safety, concurrent publishers, cross-`PYTHONHASHSEED`) in B2E/B2D/this pass ran
on this one OS and this one interpreter. The POSIX branch has never been executed by any test in this
project's history.

**What is intended for the eventual public deliverable (per this task's own supplied context):** a Python 3
source/CLI now, later packaged as a **standalone Windows executable**, for use alongside **Source
Filmmaker**, which is itself a **Windows-target application**. Nothing in this stated intent describes a
cross-platform CLI release, a PyPI package supporting a version matrix, or any Linux/macOS deliverable.

**Recommended current support contract for this experimental pre-v1 compiler:**

| Dimension | Recommended contract | Basis |
|---|---|---|
| OS/platform | **Windows only** | Sole real consumer (SFM) is Windows-target; stated eventual packaging is a standalone Windows EXE; POSIX code path is incidental, never promised, never tested |
| Python implementation | **CPython only** | The only implementation ever run against this code; no PyPy/Jython/IronPython claim exists anywhere |
| Python 3 version | **3.10.x** (the exact tested minor line; specifically verified against 3.10.6) | Zero repository evidence (no `python_requires`, no CI matrix, no changelog, no docstring) of any broader intended range; a single-maintainer project with no multi-version testing infrastructure has no basis to claim one |

This is neither an artificial narrowing invented to pass Gate 1, nor an invented broadening to sound
general-purpose — it is the actual current scope, made explicit rather than left undocumented. It is fully
reversible: broadening it later (to another OS, another Python 3 minor, or a range) immediately and
correctly reopens the corresponding cross-environment determinism requirement before that broader claim
could be honestly made.

### 23.3 Reclassifications applied (Sections 1, 3, 15, 16, 19, 21)

- **Cross-OS determinism → NOT REQUIRED FOR GATE 1**, under the Windows-only contract (23.2).
- **Cross-Python-3-minor-version determinism → NOT REQUIRED FOR GATE 1**, under the CPython-3.10.x-only
  contract (23.2). Hash-seed determinism (a different, already-PASSing axis) is unaffected and remains PASS.
- **Python 2.7 real execution (H1): UNCHANGED, remains OPEN.** Nothing in this addendum touches its status;
  Part 5's own instruction is explicit that only actual execution evidence can close it.

### 23.4 Feasibility assessment: SFM's own embedded Python 2.7 as a narrower Gate 1 test path

**Not attempted in this pass (SFM was not run, per explicit instruction) — assessment only, for a possible
future task.**

Source Filmmaker ships with an embedded CPython 2.7 interpreter as part of its own scripting/console
environment (this is the runtime the eventual Normalizer/consumer integration would actually use — the same
runtime `format.py`/`reader.py` were deliberately hardened to be compatible with since Phase B0). In
principle, the exact bounded qualification probe already specified for standalone Python 2.7 (Phase B2C/B2E
task text: import `format`/`reader` only, never `writer`/`compiler`/`cli`/`sfm_master_core`; open a small
valid fixture artifact; checksum validation; source-bound open; a known `Hit`; a `FoldConflict` fixture; a
`MasterUnknown` query; metadata/group/occurrence iteration; `close()`; `close()` again; a post-close failure
check) requires nothing beyond: (a) a way to place `format.py`, `reader.py`, one small pre-compiled sidecar
fixture, and a short self-contained probe script (no `unittest`/`pytest` dependency assumed, to avoid
relying on packages that may not exist in SFM's embedded environment) somewhere SFM's embedded interpreter
can import from, (b) a way to actually execute that probe script inside SFM's own Python console/scripting
surface, and (c) a way to read back the probe's PASS/FAIL result (e.g., writing a small plain-text result
file, since capturing console stdout back into this automation session may not be straightforward).

**This machine shows evidence of SFM being used** (multiple `SourceFilmMaker Sessions` project directories
exist on two drives), but **no evidence was found of the actual SFM game installation directory itself**
(no `steamapps\common\SourceFilmmaker`-style path was located in the locations checked) — this would need
to be confirmed as the concrete first step of any future attempt, before anything else.

**Assessed as plausible and potentially stronger evidence** than an unrelated standalone Python 2.7 install,
specifically because it would exercise the actual runtime this project ultimately cares about, PROVIDED all
of the following hold, each unverified as of this pass: SFM is actually installed on this machine; SFM
exposes some mechanism to execute an arbitrary local `.py` file inside its embedded interpreter without
requiring Steam Workshop upload or network access; and the probe is kept deliberately tiny (one small
fixture only, no timing/memory measurement, no official-Master-scale operation) so that running it cannot be
mistaken for, or accidentally slide into, Gate 2 performance/memory qualification work. **Recommended next
concrete step, for a separately-authorized future task:** first confirm SFM's actual installation path and
its script-execution surface on this machine, before attempting to build or run any probe.
