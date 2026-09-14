# SFM Master Sidecar — Phase B2E: Public Compiler CLI + Immutable Generation Publication

Gate 1C foundation work: the public Python 3 compiler CLI, immutable generation publication, the JSON
manifest pointer, and OS-backed publisher locking, all built on the SAME single production compiler path
used by official and custom builds alike. No Normalizer integration, no SFM installation, no Final Gate 1
declaration, no format v1 freeze, and no change to the qualified normative binary layout or fold semantics.

## 1. VERDICT

**PASS.** No STOP condition (Part 40) was triggered. There is exactly one production compiler/orchestration
path (`tools/sfm_master_sidecar/compiler.py`), used identically by the CLI, the publisher, and every test in
this phase — official and custom builds are never branched. The official Master compiled through this
entire new path (compiler → publisher → CLI) reproduces the exact B2D artifact SHA
(`bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`) with zero discrepancy. The publisher
lock is real OS-backed exclusive locking (`msvcrt.locking` on this Windows environment), proven crash-safe
via an actual killed subprocess. Failure injection at every required stage leaves a prior valid publication
completely unchanged. Zero changes were made to the Master, `sfm_master_core.py`, `tools/validate_master.py`,
the B2A oracle, or any of `format.py`/`writer.py`/`reader.py`.

## 2. FILES CHANGED / CREATED

**Changed:** none. `tools/sfm_master_sidecar/{format,writer,reader}.py`, `tools/sfm_master_sidecar/__init__.py`,
`tools/sfm_master_core.py`, `tools/validate_master.py`, `sfm_defaultanimationgroups.txt`, and every B2A
oracle/fixture file are byte-for-byte identical to the Phase B2D checkpoint (confirmed via empty `git diff`
on each).

**Created — production (Python 3 only):**
- `tools/sfm_master_sidecar/compiler.py` — the single compiler orchestration path (237 lines).
- `tools/sfm_master_sidecar/manifest.py` — manifest build/serialize/hardened-parse (208 lines).
- `tools/sfm_master_sidecar/publisher.py` — the publication transaction + OS-backed lock (327 lines).
- `tools/sfm_master_sidecar/cli.py` — the public CLI entry point (116 lines).

**Created — tests:**
- `tests/sidecar/test_compiler.py`, `test_manifest.py`, `test_publisher.py`, `test_publication_failures.py`,
  `test_publisher_concurrency.py`, `test_cli.py`, `test_custom_master_gate1.py`.
- `tests/sidecar/fixtures/custom_gate1/combined_custom_master.txt` — the Part 22 hand-authored combined
  custom Master (new fixture, does not touch the B2A `fixtures/{valid,unsupported,malformed}` corpus or its
  manifest).
- This audit document.

## 3. PUBLIC COMPILER ARCHITECTURE

`compiler.py` is THE one path: `capture_source_snapshot(path)` (read-once, hash) →
`parse_and_compile(snapshot, official_policy=False)` (generic `sfm_master_core` + sidecar-profile
eligibility via `writer.compile_sidecar`, with `official_policy=True` layering `tools/validate_master.py`
as an ADDITIONAL, opt-in-only gate never inherited by default) → `self_validate_from_bytes`/
`self_validate_from_path` → `verify_semantic_parity` (exhaustive, generically-sized, reused by both
`--check-only` and real publication). `publisher.py` and `cli.py` both call into this exact module — no
separate official/custom/maintainer compiler exists anywhere (confirmed by direct code inspection: neither
`publisher.py` nor `cli.py` contains any parsing/compilation logic of its own).

## 4. SOURCE SNAPSHOT CONTRACT

`capture_source_snapshot` opens the path, reads exact bytes ONCE inside a `with open(...) as f` block (the
handle is closed before the function returns), then hashes those exact bytes — `SourceSnapshot.bytes` and
`SourceSnapshot.sha256_hex` are set together, from one read, and never re-derived from a second read. Every
subsequent step (`parse_and_compile`, `self_validate_from_bytes/path`) consumes `snapshot.bytes`/
`snapshot.sha256_hex` directly, never re-opening `snapshot.path`. The one exception — `_run_official_policy_gate`,
which must call `tools/validate_master.py`'s `validate(path)` (a path-taking function that does its own
read) — writes the captured `snapshot.bytes` to a private temporary file and validates THAT, specifically to
avoid ever re-reading the live (possibly-since-changed) source path.

## 5. GENERIC VS OFFICIAL POLICY

`parse_and_compile`'s generic acceptance is exactly: `sfm_master_core.parse_master_bytes(...).ok` AND the
sidecar compatibility-profile gate inside `writer.compile_sidecar` (exactly one parentless wrapper) — never
more. Verified directly: fixtures with duplicate control occurrences (`10_repeated_identical_control_one_group.txt`)
and cross-destination fold conflicts (`13_same_fold_different_destinations.txt`) both compile successfully
with `official_policy=False`. `official_policy=True` is a strictly additive gate — verified it does not
change what the GENERIC checks themselves accept (`test_official_policy_flag_does_not_change_generic_acceptance_of_valid_fixtures`);
it only adds a further, separate, official-release-only rejection path via `OfficialPolicyRejectedError`.

## 6. CLI CONTRACT

`python -m tools.sfm_master_sidecar.cli SOURCE_TXT --output OUTPUT_DIR [--check-only] [--official-policy] [--lock-timeout SECONDS]`.
Requires nothing beyond the standard library plus this package's own modules — no Git, no Claude Code, no
SFM installation, no repository cwd for the OPERATION itself (module discovery via `python -m` does need
`tools` importable, documented separately — Section 27). Depends on no hardcoded official source SHA
anywhere in `cli.py`/`compiler.py`/`publisher.py` (confirmed by code inspection — the only SHA constants
anywhere in this phase's new production code are the format-version constants already qualified since B2B).

## 7. CHECK-ONLY

`publisher.check_only(source_path, official_policy=False)` runs snapshot capture → parse/compile → in-memory
self-validation via `reader.SidecarReader.open_generation(outcome.blob, ...)` — no `output_dir` parameter
exists on this function at all, so it is structurally incapable of touching any output namespace, publishing
a generation, or modifying a manifest. Verified directly
(`test_check_only_never_touches_an_output_directory`, `test_check_only_leaves_no_generation_or_manifest_anywhere`):
an otherwise-empty temp directory remains empty after `--check-only` runs. Source immutability re-confirmed
via SHA-256 comparison before/after, including against the official Master itself.

## 8. SELF-VALIDATION

Every compiled artifact is reopened through the real production `reader.SidecarReader` before publication —
`self_validate_from_path` specifically opens the artifact from the ACTUAL BYTES WRITTEN TO DISK (the temp
generation file's path, not the in-memory `blob`), proving what will be published is what was validated, not
merely what was intended. No second compiler-side binary reader exists anywhere in this phase (confirmed:
`compiler.py`'s only reader-related import is `from . import reader as reader_module`, the same production
module qualified since B2B/B2C).

## 9. SEMANTIC PARITY

`compiler.verify_semantic_parity(result, r)` is exhaustive and generically sized to the actual input (never
hardcoded to official counts): full group-fact agreement (name/declare_order/sibling_rank/parent_path), full
per-group metadata agreement (key/value/order), full ordered occurrence agreement (literal/full_path/local_rank),
and full fold-family agreement (Hit/FoldConflict classification, destination sets, AND the complete
occurrence-evidence global-rank set per fold — not a destination-count summary). This is the SAME method
B2D used ad hoc in test code, now promoted into production code so both `--check-only` and real publication
share it. A deliberately tampered `MasterParseResult` (an extra fake group not actually present in the
reader) is confirmed to be caught (`test_verify_semantic_parity_detects_group_count_mismatch`). The B2A
independent oracle is correctly NOT invoked by ordinary public compilation (confirmed by code inspection:
neither `compiler.py`, `publisher.py`, nor `cli.py` imports `oracle.py`) — it remains qualification/test
infrastructure only, per Part 8's explicit instruction; it IS still used directly (independently, never fed
core's output) in `test_custom_master_gate1.py`'s Gate-1A comparison, exactly as intended.

## 10. GENERATION IDENTITY

`compiler.generation_basename(sha256_hex, format_contract_version=None)` produces
`sfm_master_<fmt>_<64-hex-sidecar-sha256>.bin` using the FULL ordinary SHA-256 of the final sidecar bytes —
no source-SHA prefix, no timestamp. For the official Master, this reproduces
`sfm_master_0_bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b.bin` exactly (Section 21).
Reuse-on-identical-content and refuse-on-different-content-under-the-same-name are both implemented in
`publisher._publish_or_reuse_generation` and directly tested (`GenerationReusePartTests`,
`test_generation_collision_with_different_bytes_is_refused`).

## 11. MANIFEST CONTRACT

`manifest.build_manifest_dict`/`serialize_manifest` produce exactly the final spec Section 33 shape:
`generation_basename`, `sidecar_sha256`, `source_sha256`, `source_byte_length`, `format_contract_version`,
`authority_semantics_version`, `compiler_build_version` (diagnostic-only, `"0.1.0-experimental"`), and
`counts` (`groups`/`occurrences`/`folds`, diagnostic-only, never re-derived as validation authority — the
reader never consults the manifest at all). Serialization is deterministic (`sort_keys=True`) purely as a
diagnostic convenience, not a normative requirement.

## 12. MANIFEST HARDENING

`manifest.parse_manifest_bytes` rejects, each independently verified: oversized payload (> 64 KiB), invalid
JSON, non-object top level, duplicate JSON keys (via a custom `object_pairs_hook`), every required key
missing (7 cases), every required key's wrong type (7 cases, `bool` explicitly excluded from `int`/`str`
matches since Python's `bool` is an `int` subclass), invalid SHA-256 values for both hash fields (wrong
length, uppercase, non-hex — 5 variants × 2 fields), unsupported `format_contract_version`/
`authority_semantics_version`, missing `counts` sub-keys, negative `source_byte_length`, and non-UTF-8
bytes. `generation_basename` path-traversal hardening covers 10 distinct unsafe forms (`../evil.bin`,
`../../etc/passwd`, absolute path, nested subdirectory, both slash directions, a bare Windows drive prefix,
a drive-relative form, `..` itself, empty string, whitespace-only) plus a naming-scheme mismatch check.
`resolve_generation_path` never joins a basename that wasn't already validated, with a defense-in-depth
re-check that the resolved path's parent is exactly `output_dir`.

## 13. PUBLICATION TRANSACTION

Implemented exactly per final spec Section 34 / Part 13's 19 steps in `publisher.publish`: capture snapshot
→ hash → parse/compile → write a UUID-named temp generation file to the destination filesystem, flush +
`os.fsync` → reader self-validation FROM THAT DISK PATH → semantic parity → close validation handles →
compute the final immutable identity → publish-or-reuse → prepare a UUID-named temp manifest, flush +
`os.fsync` → acquire the publisher lock ONLY for the critical section → re-read/hash the LIVE source path →
compare to the captured hash → abort activation on mismatch → atomically `os.replace` the manifest → release
the lock. Verified end-to-end (`PublicationTransactionTests`) and via the official Master
(`OfficialMasterThroughPublisherTests`).

## 14. SOURCE RECHECK

No claim of TXT+manifest global atomicity against arbitrary external editors is made anywhere in this
phase's code or docstrings — `publisher.py`'s module docstring states this explicitly, quoting the same
non-claim from the final spec. The manifest means only "generation G was compiled from source hash X."
`SourceMutationRaceTests.test_source_mutated_before_recheck_aborts_activation` proves the concrete scenario:
capture source A, mutate the live path to B immediately before the critical section's live-source read
(via the `before_source_recheck` fault hook), and confirm `SourceMutatedDuringPublicationError` is raised,
the prior manifest is untouched, and no stale generation is ever activated. An orphan immutable generation
for the captured (now-stale) snapshot may remain — confirmed harmless, never cleaned up automatically
(Section 17).

## 15. PUBLISHER LOCK

Real OS-backed exclusive locking — `msvcrt.locking(fd, LK_NBLCK, 1)` on this Windows environment (an
`fcntl.flock`-based equivalent exists in the same module for POSIX, unexercised here since this environment
is `win32`), never a bare lockfile-existence check. **Proven crash-safe with an actual subprocess kill**
(`LockCrashSafetyTests.test_killed_lock_holder_does_not_permanently_block_future_publisher`): a subprocess
acquires the lock, signals readiness, is `kill()`ed (not asked to exit cleanly), and a second, independent
`PublisherLock` in the test process acquires it again in ~0.00s — the OS released the lock the instant the
holding process's file handle was force-closed. `TwoConcurrentPublishersTests` runs two REAL subprocesses
(never a mocked lock) racing to publish two different sources into the same namespace concurrently: both
generations end up on disk, never clobbering each other, and the final manifest is complete, valid JSON
referencing one of the two, verified openable.

## 16. ATOMIC REPLACEMENT

Both the immutable generation promotion and the manifest activation use `os.replace` (atomic rename on the
same filesystem/directory — Windows `MoveFileEx` with `MOVEFILE_REPLACE_EXISTING` under the hood via
CPython's implementation), never in-place mutation of an existing file. `TwoConcurrentPublishersTests.test_manifest_is_never_observed_as_partial_json_during_concurrent_publishes`
polls the live manifest file hundreds of times per second while two real publishers race and confirms every
successful read is complete, parseable JSON — never truncated/partial content. **Durability distinction,
stated explicitly and not overclaimed:** `os.fsync` is called on both the temp generation file and the temp
manifest file before they are promoted/activated, giving durability for THOSE writes against an ordinary
process crash: but this project makes no claim about power-loss durability of the directory-entry rename
itself (a stronger guarantee requiring platform-specific directory-fsync semantics this phase does not
implement or test).

## 17. FAILURE PRESERVATION

`test_publication_failures.py`'s `InjectedStageFailurePreservationTests.test_injected_failure_at_every_stage_preserves_baseline`
establishes one valid baseline publication, then injects a failure at each of 7 named stages
(`before_self_validation`, `before_generation_publication`, `after_generation_publication`,
`before_manifest_temp_write`, `after_manifest_temp_write`, `before_source_recheck`, `before_manifest_replace`)
while attempting to publish a DIFFERENT source — and confirms, for every single stage, that the baseline
manifest bytes are byte-identical to before, the baseline generation file still exists, and no leftover
`.tmp-*` file remains. A failure strictly after the new generation's immutable promotion (but before
manifest activation) is confirmed to leave that new generation as a harmless orphan while the active
manifest still points at the original baseline (`test_after_generation_publication_failure_leaves_new_generation_as_harmless_orphan`).
Source-level rejections (malformed grammar, profile-unsupported) are confirmed to leave the baseline
untouched too.

## 18. GENERATION REUSE

Publishing the identical source twice (`28_large_alias_family.txt`) produces the same sidecar bytes, the
same full SHA, the same immutable basename, and the second call is confirmed `reused=True` with exactly one
`.bin` file present in the namespace afterward — no duplicate generation churn.

## 19. CUSTOM MASTER QUALIFICATION

`CustomMasterPublicCompilerTests` runs the real `check_only`/`publish` path (the exact same functions the
official Master uses) against 13 representative B2A `valid/` fixtures spanning custom wrapper, wrapper-owned
control/metadata, duplicate controls (within and across groups), same-destination aliases, cross-destination
FoldConflict, non-ASCII/astral-plane UTF-8, escape-spelling preservation, and duplicate/unknown metadata —
every one compiles and publishes successfully, and the cross-destination-conflict fixture is confirmed to
still resolve `FoldConflict` correctly when looked up through the fully-published, reopened artifact.

## 20. COMBINED CUSTOM GATE-1A

One new, hand-authored, hand-auditable fixture (`tests/sidecar/fixtures/custom_gate1/combined_custom_master.txt`,
23 lines) combines every remaining element in a single source: a custom wrapper (`CustomRoot`, not
`groupFile`), 3-level nesting plus sibling groups, ordered metadata across 3 different groups including one
unknown key, a duplicate control occurrence (`"Bar"` × 2 in one group), a same-destination 3-spelling ASCII
alias family (`Foo`/`foo`/`FOO`, all in `NestedA`), a genuine cross-destination `FoldConflict`
(`Bar`/`NestedB` vs `bar`/`NestedC`), non-ASCII UTF-8 (`注視Tips`), and a preserved backslash-escape spelling
(`He said \"hi\"`). `CombinedCustomGateOneATests` runs the full exhaustive comparison: core vs. independent
B2A oracle (group-by-group, occurrence-by-occurrence, full metadata count), writer+reader round-trip
matching both core and oracle (including the exact `FoldConflict` destination set and escape-spelling
preservation), the public compiler orchestration reproducing byte-identical output to a direct
`writer.compile_sidecar` call, and both `check_only`/`publish` succeeding end-to-end with the published,
reopened artifact still correctly resolving the conflict. Zero mismatches anywhere.

## 21. OFFICIAL MASTER PUBLIC-COMPILER QUALIFICATION

The official Master, compiled through `compiler.parse_and_compile` (both with and without
`official_policy=True`), through `publisher.publish` directly, and through the real `python -m
tools.sfm_master_sidecar.cli` subprocess invocation, produces the artifact SHA
**`bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`** in every single case — **identical to
the B2D artifact SHA**, confirming no normative binary contract changed anywhere in this phase's new
orchestration layer. Temporary publication namespaces only were used (a system temp directory via the CLI
smoke test and `tempfile.TemporaryDirectory()`/`tempfile.mkdtemp()` in every test) — never the repository,
never a persistent location.

## 22. DETERMINISM

`DeterminismThroughPublicOrchestrationTests`: same-process double-compile via `compiler.parse_and_compile`
is byte-identical for both a small fixture and the official Master; cross-`PYTHONHASHSEED`-subprocess
compilation of the official Master through the exact same public orchestration entry point (`PYTHONHASHSEED=0`
vs. `999983`) produces an identical SHA-256 AND an identical generation basename. Compiler provenance
(`compiler_build_version` in the manifest) is confirmed to never perturb binary output, since it is never
written into the binary at all (unchanged since B1.2's header correction) — only into the manifest, which is
never hashed into the sidecar's own identity.

## 23. CONCURRENT PUBLISHERS

Covered fully in Section 15 — real subprocess concurrency, never mocks. Additionally: the lock's normal-exit
release path is independently confirmed (`test_lock_release_on_normal_exit`) distinct from the crash-release
path, so both release mechanisms (clean `__exit__` and OS-forced release on process death) are exercised as
genuinely different code paths, not just asserted to be equivalent.

## 24. SOURCE-MUTATION RACE

Covered fully in Section 14.

## 25. FAILURE INJECTION

The narrow, test-only `_fault_hook(stage)` parameter on `publisher.publish` is the ONLY failure-injection
mechanism added — never a broad public debug API (it is not exposed via the CLI, is undocumented in
`cli.py`'s help text, and its docstring in `publisher.py` explicitly labels it test-only). It supports the 5
stages Part 27 names verbatim (`before_generation_publication`, `after_generation_publication`,
`before_manifest_temp_write`, `after_manifest_temp_write`, `before_manifest_replace`) plus 2 more this phase
found necessary for complete coverage (`before_self_validation`, `before_source_recheck` — the latter being
the only point at which a source-mutation-race test could actually inject the mutation at the intended
moment; without it, the fault would fire too late, after the live-source comparison had already succeeded,
as directly discovered while first constructing that test).

## 26. MANIFEST READBACK

`ManifestReadbackTests.test_readback_proves_self_consistent_namespace`: after publication, the manifest is
parsed via the production hardened parser, the generation basename is safely resolved via
`manifest.resolve_generation_path`, the generation file's existence and ordinary SHA-256 are independently
re-verified against the manifest's own `sidecar_sha256` field, and the generation is reopened via the
production reader with its embedded `source_sha256` checked against the manifest's `source_sha256` — the
full namespace is proven self-consistent, not merely "a manifest file exists."

## 27. CLI OUTSIDE-REPO USABILITY

`OutsideRepositoryCliTests` invokes the CLI as a real subprocess with `cwd` set to a temp directory entirely
outside the repository, using absolute source and output paths, for both `--check-only` and full publish —
both succeed. **Documented separately, as instructed (Part 30):** `python -m tools.sfm_master_sidecar.cli`
module discovery itself requires `tools` to be importable as a namespace package, which this test achieves
via `PYTHONPATH=<repository root>` in the subprocess environment — a development-environment packaging
concern, orthogonal to (and does not compromise) the source/output PATH independence itself, which never
depends on `cwd`. Future standalone Windows EXE packaging remains explicitly later work, untouched here.

## 28. EXIT STATUS

`cli.py` defines exactly the 5 codes Part 31 suggests: `0` success, `2` usage/input-path error, `3` source
grammar/sidecar-profile/official-policy rejection, `4` compilation self-validation/field-overflow failure,
`5` publication/locking failure (also used as the fallback for any genuinely unexpected exception during a
publish attempt, while an unexpected exception during `--check-only` falls back to `4`). Verified for every
category: missing source file (2), missing `--output` for a non-check-only run (2), malformed source (3),
profile-unsupported source (3), successful check-only (0), successful publish (0).

## 29. SOURCE IMMUTABILITY

`SourceImmutabilityTests` records the source's SHA-256 before and after `--check-only`, a successful
publish, and a FAILED publish (malformed source, exit code 3) — all four cases confirm byte-identical
source content, including for the official Master itself. The compiler never opens its source path for
writing anywhere in `compiler.py`/`publisher.py`/`cli.py` (confirmed by code inspection: every `open(...)`
call against a caller-supplied source path uses mode `"rb"`).

## 30. TEST RESULTS

| Scope | Ordinary tests | Subtests |
|---|---|---|
| Pre-B2E baseline (everything under `tests/` EXCLUDING the 7 new B2E files) | 318 | 196 |
| New B2E only (`test_compiler.py`, `test_manifest.py`, `test_publisher.py`, `test_publication_failures.py`, `test_publisher_concurrency.py`, `test_cli.py`, `test_custom_master_gate1.py`) | **77** | **59** |
| Total (`python -m pytest tests/ -q`) | **395** | **255** |

`318 + 77 = 395` and `196 + 59 = 255` — both reconcile exactly. **B2E-specific runtime:** ~38s (the 7 new
files run together). **Complete suite runtime:** ~118s.

## 31. PYTHON-2.7 STATUS

**OPEN, unchanged from B2D.** No Python 2.7 interpreter is available in this environment (`py -2 --version`
falls through to the installed Python 3.10.6; `where python2` finds nothing) — reconfirmed fresh at the
start of this phase. Nothing in B2E's new code touches `format.py`/`reader.py` at all (both are byte-for-byte
unchanged, Section 2), so the Python-2.7 runtime boundary itself has zero new surface area to re-qualify;
`compiler.py`/`manifest.py`/`publisher.py`/`cli.py` are all explicitly Python-3-only and were never claimed
otherwise. No interpreter was installed, downloaded, or bundled without authorization.

## 32. CROSS-PYTHON/OS STATUS

**OPEN, unchanged from B2D.** Only one Python 3 interpreter (3.10.6) and one OS (Windows/win32) were
available in this environment; no new runtime or VM was installed for this phase, per explicit instruction.
The POSIX (`fcntl`-based) branch of the publisher lock exists in the source but was never exercised on this
platform — noted explicitly as untested code, not claimed as verified.

## 33. READINESS FOR FINAL GATE 1

The full Gate 1C surface (public CLI, generic-vs-official policy, immutable generation naming/publication/
reuse, hardened manifest, real OS-backed publisher locking proven crash-safe with actual process kills,
atomic manifest replacement, failure preservation across every named injection point, the source-mutation
race, and both official and custom Masters running through the identical stack) is now built and passing.
Combined with B2D's exhaustive official-Master semantic parity and this phase's own combined custom
Gate-1A fixture, the remaining blockers to Final Gate 1 are narrow and enumerated exactly in Section 34 —
no open architectural or correctness question remains.

## 34. REMAINING FINAL-GATE-1 EVIDENCE

1. **Real Python 2.7 execution** of the `runtime_safe` reader's parity suite under an actual Python 2.7
   interpreter (Section 31) — unchanged blocker since B2B.
2. **Cross-Python-3-minor-version / cross-OS deterministic binary equality** — only one environment was ever
   available across B2D and B2E (Section 32).
3. **Gate 2 embedded x86 SFM measurement** (final spec Section 42) — explicitly out of scope for every phase
   through B2E.
4. A **real consumer-contract check against the actual Normalizer** (final spec Section 44's format-freeze
   policy) — explicitly out of scope; B2E does not integrate with the Normalizer at all.

None of these four gates B2E's own PASS verdict for its own bounded scope; all four remain the named
prerequisites before format v1 can ever be declared stable.

## 35. GIT / SAFETY STATE

- `sfm_defaultanimationgroups.txt`: unchanged, SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`.
- `tools/sfm_master_core.py`, `tools/validate_master.py`: unchanged.
- `tools/sfm_master_sidecar/{format,writer,reader,__init__}.py`: unchanged (empty `git diff` on each).
- `tests/sidecar/oracle.py`, `fixtures/{valid,unsupported,malformed}/`, `fixture_manifest.json`: unchanged.
- Validator re-run fresh after the full qualification: PASS, all canonical facts unchanged (groups=43,
  controls=128,555, folds=124,728, duplicates=0, cross-path conflicts=0).
- `git diff --check`: clean.
- No Normalizer integration, no SFM installation, anywhere in this phase.
- **No persistent test publication artifact exists anywhere** — every test used
  `tempfile.TemporaryDirectory()`/`tempfile.mkdtemp()` with cleanup, and `find . -iname "*.bin"` returns
  nothing outside `.git/` after the complete suite ran.
- HEAD unchanged: `2a132490d27c7e196171990a7b7502f8329ad306`.
- `git status`: only new, untracked files — 4 new production modules, 7 new test files, 1 new fixture
  directory (`tests/sidecar/fixtures/custom_gate1/`), and this audit document. **Nothing staged, nothing
  committed.**
- No agents or subagents were used.
