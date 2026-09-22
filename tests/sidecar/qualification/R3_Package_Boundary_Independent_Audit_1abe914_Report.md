# R3 Package-Boundary Independent Audit — commit `1abe91498080dd2b7e64bbf21f8441cc2314c0ef`

## Scope

This report records the disposition of an independent audit of the Shared-Authority
Package-Boundary Correction (commits `d039c92685948b59c8202e315df29a7b4bf8197a` and
`1abe91498080dd2b7e64bbf21f8441cc2314c0ef`), performed under the governing prompt
`SFM_PackageBoundary_TargetedCorrection_ClaudeCode_Prompt_2026-09-22.md`. It is a
disposition record, not a re-derivation of the original package-boundary correction's
own evidence — that evidence (leased-orphan invalidation, clean-directory publish/
acquire, installed-package isolation, `acquire_generation()` legacy fix) is preserved
by exact identity in `R3_Package_Boundary_Correction_Report.md` and re-confirmed by
identical-result re-run as part of this session's own regression pass (see
`R3_Package_Boundary_Targeted_Correction_Report.md`).

**Verdict of the independent audit: PARTIAL, not FAIL.** The shared-authority
architecture itself — leased-orphan revocation, the generic compiler/publisher
`.sfmsidecar` contract, manifest/pointer field reconciliation, bundled validator/
provider identity, the runtime canonical module-name repair, and the
`acquire_generation()` legacy-call repair — is accepted as real and correct. Those
designs are NOT reopened by this audit or by the correction that follows it.

## Verified Closed

The following defects, closed by `d039c92`/`1abe914`, were independently re-confirmed
against current source at audit time and are **not** revisited by this correction:

1. **Leased-orphan generation invalidation** — `ViewCache.invalidate_generation()` now
   iterates `self._leased_orphans.values()` in addition to `self._entries`, so a
   displaced-but-still-leased view's authorization token is correctly revoked.
2. **Generic compiler/publisher `.sfmsidecar` contract** — `compiler.
   generation_basename()` emits `.sfmsidecar` (was `.bin`); the runtime's shipped-root
   candidate scan and `manifest.py`'s naming-scheme validation both agree with this
   extension.
3. **Bundled validator/provider identity** — `sidecar_contract.py` resolves its
   validator/provider dependency from bundled, byte-identical copies inside
   `sfm_master_authority_productionized/` itself, not a repository-relative
   qualification path two directory levels outside the package.
4. **Canonical runtime package-name repair** — `runtime.py`'s `_CANONICAL_MODULE_NAME`
   constant correctly names `"sfm_master_authority_productionized.runtime"` (was the
   old, pre-productionized `"sfm_master_authority.runtime"`, which made the entire
   canonical broker-factory entry point unimportable under its real name).
5. **`Broker.acquire_generation()` legacy-call repair** — the call into
   `select_sidecar_candidate` uses the real, current keyword
   (`aggregate_existing_retained_bytes`), not the invalid `ledger=` keyword that
   previously raised `TypeError` unconditionally.

## Integration-Base Blockers Found

Two narrow integration-base defects were found in the tracked/committed state at
`1abe914`, both now closed by this correction (see `R3_Package_Boundary_Targeted_
Correction_Report.md` for the fixes and regression evidence):

1. **Stale `.bin` regression expectations.** `tests/sidecar/test_compiler.py`'s
   `GenerationBasenameTests.test_generation_basename_format` and `tests/sidecar/
   test_publisher.py`'s `GenerationReusePartTests.test_publishing_identical_source_
   twice_reuses_generation` still asserted the old `.bin` suffix. A broader search
   (not limited to these two named tests) additionally found two masked-test-
   weakening occurrences in `tests/sidecar/test_publication_failures.py`
   (`FailurePreservationTestCase.setUp`/`_assert_baseline_untouched`): both filtered
   `p.suffix == ".bin"`, which after the real extension change would find **zero**
   files on every run, making the "prior generation must never be removed" assertion
   trivially pass without testing anything real. This is a genuine, previously-
   undiscovered regression-detection gap, not merely a cosmetic mismatch.
2. **`RUNTIME_BUILD_ID` not bumped.** `runtime.py`'s own docstring requires bumping
   `RUNTIME_BUILD_ID` "whenever a build adds or changes an API surface that callers
   depend on, even if `RUNTIME_API_VERSION` does not change." The package-boundary
   correction added exactly such caller-relevant behavior (orphan revocation,
   `acquire_generation()` repair, bundled-dependency resolution, canonical-name
   repair) without bumping the build id, silently defeating the stale/wrong-build
   protection the id exists to provide.

## Clarifications (not defects; recorded, not silently assumed)

- **`tools/sfm_master_sidecar/mutex_publisher.py` remains machine/repository-path-
  bound.** Three constants (`_FINAL_R3A2B_VALIDATOR_PATH`, `_FINAL_R3A2B_PROVIDER_
  PATH`, `_GATE_R2_DEPLOY_DIR`) are hardcoded absolute paths specific to this exact
  development checkout. Hardened custom/local-Master rebuild support through this
  module is **not** an installed-release feature until it is itself productionized
  with a real, supported dependency location. This is documented in-source (see
  `R3_Package_Boundary_Targeted_Correction_Report.md` Section 7) rather than silently
  fixed by repointing at a still-repository-relative location, which would not be a
  genuine portability fix.
- **Installed isolation proves package operation once on `sys.path`, not the real
  MAINMENU bootstrap seam.** `test_package_boundary_installed_isolation.py` proves
  the package imports and acquires correctly from only its own real files, with no
  repository/CWD dependency, once its installed directory is already on `sys.path`.
  It does not exercise the actual MAINMENU-side `sys.path.insert(...)` + import call
  against a real embedded SFM process — that exact entry seam remains a real-SFM
  production Normalizer integration concern, not something offline isolation testing
  can qualify. `bootstrap.py` supplies the deterministic `sys.executable`-relative
  path calculations such an entry point would use; it does not itself perform the
  entry.
- **Failed-batch eviction remains `IMPORTANT BUT DEFERRABLE`.** No code in this
  correction touches `admit_batch()`'s eviction sequencing. This is a real,
  acknowledged risk/debt item, correctly left out of scope rather than expanded into
  an unrequested redesign.

## Disposition

`PACKAGE-BOUNDARY INDEPENDENT AUDIT: PARTIAL — CORE ARCHITECTURE ACCEPTED; TWO
INTEGRATION-BASE BLOCKERS IDENTIFIED, CLOSED BY THE FOLLOWING TARGETED CORRECTION.`

This report is a documentation-only record of the audit's own findings, committed
separately from — and before — the implementation changes that close the two
integration-base blockers, per the governing prompt's git-discipline requirement
(Section 11). No source file is modified by this report or by its companion ledger
addendum.
