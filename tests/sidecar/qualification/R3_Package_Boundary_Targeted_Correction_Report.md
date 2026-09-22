# R3 Package-Boundary Targeted Correction

## Base

Base HEAD for this correction: `1abe91498080dd2b7e64bbf21f8441cc2314c0ef`.
Documentation commit recording the independent audit's own findings (this correction's
prerequisite, per governing-prompt Section 11): `0e1ca55ff406dab109b31c2eac7d13cd8ab3d070`.

Governing prompt: `SFM_PackageBoundary_TargetedCorrection_ClaudeCode_Prompt_2026-09-22.md`.
Full audit findings: `R3_Package_Boundary_Independent_Audit_1abe914_Report.md`. This report
covers the correction that closes the two integration-base blockers that audit identified.

Hard constraints observed throughout: no Normalizer integration performed; CPM not modified;
SFM never launched; explicit path-by-path `git add`, never `git add .`/`-A`/`-a`; no destructive
git operations.

## 1. Stale `.bin` regression expectations — root cause and fix

Root cause: `compiler.generation_basename()`'s immutable-generation-file extension changed from
`.bin` to `.sfmsidecar` during the prior package-boundary correction (commit `d039c92`), but not
every place in the tracked test suite that hardcoded the old extension was updated at the same
time.

Fixed:

- `tests/sidecar/test_compiler.py` — `GenerationBasenameTests.test_generation_basename_format`
  now asserts `name.endswith(".sfmsidecar")` (was `.bin`).
- `tests/sidecar/test_publisher.py` — `GenerationReusePartTests.
  test_publishing_identical_source_twice_reuses_generation` now filters
  `p.suffix == ".sfmsidecar"` (was `.bin`).
- `tests/sidecar/test_publication_failures.py` — a broader search (not limited to the two tests
  named above) found two **masked-test-weakening** occurrences, not merely cosmetic mismatches:
  `FailurePreservationTestCase.setUp()` and `_assert_baseline_untouched()` both filtered
  `p.suffix == ".bin"` when listing the output directory. After the real extension change, that
  filter finds **zero** files on every run, so the "the prior generation must never be removed by
  a failed publication" assertion passed trivially without checking anything real. Both filters
  are now `p.suffix == ".sfmsidecar"`.
- `tools/sfm_master_sidecar/publisher.py` — module docstring's "output namespace" description and
  the transactional temp-generation filename (`.tmp-gen-%s.sfmsidecar`, was `.tmp-gen-%s.bin`)
  updated to match; the rename is cosmetic (the temp file is always renamed away by its extension
  before any read-back depends on it), zero functional risk.
- `tools/sfm_master_sidecar/mutex_publisher.py` — the same trivial, safe temp-filename fix applied
  (see Section 7 below for the module's other, deliberately-NOT-fixed, disposition).
- `tests/sidecar/test_manifest.py` — inspected, **not modified**. Its `.bin`-suffixed literals are
  all in NEGATIVE/rejection test cases (unsafe-path-traversal data, wrong-naming-scheme rejection)
  that remain correctly rejected regardless of which specific suffix is the "right" one; its
  baseline valid-manifest fixture (`_sample_manifest_dict()`) already calls `compiler.
  generation_basename()` dynamically, so it automatically tracks the real extension.

## 2. Core regression re-run

```
python -m pytest -q tests/sidecar/test_compiler.py tests/sidecar/test_publisher.py \
    tests/sidecar/test_manifest.py tests/sidecar/test_publication_failures.py
```

Result: **50 passed, 33 subtests passed, 0 failed.**

Broader `tests/sidecar` suite (excluding the `qualification/` standalone harness scripts, which
are run individually below), for additional confidence beyond the minimum required set:

```
python -m pytest -q tests/sidecar --ignore=tests/sidecar/qualification
```

Result: **369 passed, 265 subtests passed, 0 failed.**

## 3. `RUNTIME_BUILD_ID` bump

`runtime.py`'s own docstring requires bumping `RUNTIME_BUILD_ID` "whenever a build adds or
changes an API surface that callers depend on, even if `RUNTIME_API_VERSION` does not change."
The package-boundary correction (`d039c92`, `1abe914`) added exactly such caller-relevant
behavior — leased-orphan revocation, the `acquire_generation()` call-contract repair, the
bundled-dependency resolution change, the canonical-module-name repair — without bumping the id.

- Old: `"b2c-correction6-parsedeferred-floor-targeted-2026-09-18"`
- New: `"package-boundary-corrected-2026-09-22"`
- `RUNTIME_API_VERSION` intentionally **unchanged** (`"1.0.0-b2a"`) — no reason was found for the
  broad calling-contract generation itself to change, and the independent audit did not require
  an API-version bump.

A whole-repository grep confirmed no other tracked file outside historical/superseded candidate
snapshots (`candidate_b2c_correction2` through `candidate_b2c_correction5`, each a frozen prior
candidate correctly retaining its own period-accurate build id) or the frozen candidate Normalizer
scripts pins a specific `RUNTIME_BUILD_ID` string value that this bump would break.

## 4. Decisive build-identity regression

New file: `tests/sidecar/qualification/test_package_boundary_runtime_build_id_regression.py`.
Independent of sidecar I/O — exercises only `runtime.py`'s own module-level state machine
(`get_broker`/`_reset_for_test_only`), never a compiled sidecar or provider.

Proves, in order: the new build id is reported by both the constant and
`get_runtime_build_id()`; `get_broker(expected_build_id=<new>)` is accepted; `get_broker
(expected_build_id=<old, pre-package-boundary>)` is rejected with `BrokerIdentityConflict`,
whose message names both the caller's expected (old) and the actually-loaded (new) build id;
`RUNTIME_API_VERSION` remains unchanged and its own matching-accept/mismatch-reject behavior is
unaffected by this correction.

Result: **9/9 PASS**, both Python 3.10 and real embedded Python 2.7.5.

## 5. Stale package-name documentation

Both files still described the package under its old, pre-productionized name
(`sfm_master_authority.runtime` / `from sfm_master_authority import runtime`) in prose separate
from the `_CANONICAL_MODULE_NAME` constant itself (which the prior package-boundary correction
already fixed):

- `sfm_master_authority_productionized/__init__.py` — module docstring's self-description and both
  import-example lines corrected to the real, current package name.
- `sfm_master_authority_productionized/runtime.py` — module docstring's opening line and import-
  example lines, plus three live error-message strings (`assert_expected_origin`'s origin-mismatch
  message, `get_broker()`'s API-version-mismatch message, `get_broker()`'s `is_canonical()`-failure
  message) corrected the same way. One historical comment (documenting exactly what the *old*,
  since-fixed `_CANONICAL_MODULE_NAME` string used to say, as part of the prior correction's own
  changelog) was deliberately left unchanged — it accurately describes past state, not a live
  instruction to callers.

No package rename performed. No working runtime semantics changed — confirmed by re-running the
build-identity regression (Section 4) after these edits: still 9/9 PASS on both interpreters,
proving the docstring/error-string-only edits introduced zero behavioral regression.

Scope note: a repository-wide grep found the same old name in historical/superseded candidate
snapshots (`candidate_b2c_correction` through `candidate_b2c_correction5`) and in frozen prior
audit reports. These are out of scope — they are historical record, not current production package
source, and rewriting them would violate the "preserve everything not explicitly changed"
discipline this project runs under for anything outside the one canonical Master-editing contract.

## 6. Bootstrap scope clarification

`bootstrap.py`'s docstring gained an "Exact scope" paragraph stating precisely what IS and is NOT
proven: the installed-isolation regression proves import/acquire with no repository/CWD dependency
**once** the installed package directory is already on `sys.path`; that regression does not call
`bootstrap_import_path()` itself, and builds `sys.path` directly. `bootstrap.py` supplies the
deterministic `sys.executable`-relative path calculations a real MAINMENU entry point would use;
the actual `sys.path.insert(...)` + import entry seam against a real embedded SFM process remains
a real-SFM production Normalizer integration concern, not something offline isolation testing can
qualify.

New file: `tests/sidecar/qualification/test_package_boundary_bootstrap_paths.py` — a small, pure
unit test of `bootstrap.py`'s path arithmetic only (`installed_authority_root(root=...)`'s
deterministic join under the one documented relative path; `bootstrap_import_path()`'s real,
`sys.executable`-derived signature and output; `game_root()`/`installed_authority_root()`/
`bootstrap_import_path()` mutual consistency and no-exception behavior against the real
interpreter; `ownership_report()`'s documented key set and no-exception behavior). Never exercises
a real MAINMENU entry seam or a real SFM process.

Result: **8/8 PASS**, both Python 3.10 and real embedded Python 2.7.5.

## 7. Hardened external rebuild (`mutex_publisher.py`) disposition

Inspected in full. Three constants remain hardcoded, absolute, and specific to this exact
development machine/checkout: `_FINAL_R3A2B_VALIDATOR_PATH`, `_FINAL_R3A2B_PROVIDER_PATH`,
`_GATE_R2_DEPLOY_DIR`. All three currently resolve correctly on this machine (the tool is not
currently broken), which is exactly the non-portability the independent audit's Astra-review
predecessor already identified.

Disposition chosen: **document, do not silently relocate.** Repointing these paths at the
already-bundled copies inside `sfm_master_authority_productionized/` was considered and rejected
— it would still be a repository-qualification-tree dependency in substance, not a genuine
portability fix, and could be mistaken for "fixed" when the module fundamentally still is not
portable. A large explanatory comment block was added directly above the three constants stating
plainly: hardened custom/local-Master rebuild support through this module is **not** an
installed-release feature; production Normalizer integration may proceed using the shipped
prebuilt sidecar; custom/local Master rebuild support through this module must remain
unadvertised/disabled in any release until it is itself productionized with a real supported
dependency location. The trivial, safe `.bin`→`.sfmsidecar` temp-filename fix (Section 1) was
applied since it carries zero portability risk either way.

## 8. Failed-batch eviction

Left untouched and deferred, as directed. No code in this correction touches `admit_batch()`'s
eviction sequencing.

## 9. Full regression evidence (this correction)

| Regression | Result |
|---|---|
| `pytest tests/sidecar/test_compiler.py test_publisher.py test_manifest.py test_publication_failures.py` | 50 passed, 33 subtests passed |
| `pytest tests/sidecar` (excl. `qualification/`) | 369 passed, 265 subtests passed |
| `test_package_boundary_leased_orphan_invalidation.py` | 20/20 PASS, both interpreters |
| `test_package_boundary_runtime_build_id_regression.py` (new) | 9/9 PASS, both interpreters |
| `test_package_boundary_bootstrap_paths.py` (new) | 8/8 PASS, both interpreters |
| `test_package_boundary_clean_directory_publish_and_acquire.py --phase=publish` | 15/15 PASS (Python 3.10) |
| `test_package_boundary_clean_directory_publish_and_acquire.py --phase=acquire` | 11/11 PASS (real Python 2.7.5, separate process, same published directory) |
| `test_package_boundary_installed_isolation.py` | 14/14 PASS (Python 3.10 orchestrator; embedded real Python 2.7.5 subprocess 11/11 within) |
| `test_package_boundary_acquire_generation_legacy_fix.py` | 6/6 PASS, both interpreters |

B2C-C plan-layer/execution-layer/broker-sanity/Tail-authority/AddChild/exit-status-self-test
evidence is carried forward **by exact identity**, not re-run: a grep of every `test_b2c_c_*.py`
file confirmed none references `runtime.py` or calls `get_broker()` at all (they open the
provider/adapter directly, one layer below the broker), so this correction's changes — confined to
`.bin`→`.sfmsidecar` test fixes, `runtime.py`/`__init__.py` docstrings, `RUNTIME_BUILD_ID`,
`bootstrap.py` documentation/tests, and `mutex_publisher.py`'s comment/temp-filename — have zero
exposure to that evidence.

Frozen identities re-verified unchanged:

- Frozen production Normalizer SHA-256:
  `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e`
- Canonical Master SHA-256:
  `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`

## 10. Explicit statements

- **Production Normalizer integration has NOT begun.**
- CPM has not been modified.
- SFM has not been launched at any point in this correction.

## Disposition

`PACKAGE-BOUNDARY TARGETED CORRECTION READY FOR NARROW RE-AUDIT`
