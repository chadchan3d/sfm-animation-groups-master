# Ledger

## Current milestone

CPM Convergence Step 1 (handoff §22 step 1): CPM-owned `cpm_compat_v1` family projection builder,
exact-answer interpreter, compatibility identity (§11), strict coverage validation, complete
retained-size estimation, Suite 1 foundation tests. Nothing beyond Step 1. Status: implemented and
tested; Suite 1 recorded **PARTIAL** (not PASS).

## Current state

Base `e080daa` on `master`. Step 1 adds `cpm/convergence/cpm_compat_v1_projection.py` (module) and
`cpm/convergence/tests/test_cpm_compat_v1_projection.py` (Suite 1 foundation). Canonical package
(operator APPROVED): `tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/`,
imported read-only (`views`, `errors`, `resource_estimator`; `broker`/`sidecar_contract` in tests).
Frozen G18AN, the shared package, `tools/` and the canonical Master are unchanged. No bootstrap
wiring, UI, Stage M, Stage F or K work started.

## Verified

- Suite 1 foundation: 196/196 PASS under Python 3.10 (`--phase=publish`) and 196/196 PASS under
  embedded Python 2.7.5 (`--phase=suite`, separate process, same published directory). The two
  result digests are byte-identical (`--phase=compare` 3/3 on both interpreters).
- Mutation controls: uncovered-as-absent, occurrence-carrying coverage, and accepting unknown result
  types are each detected by the suite.
- G18AN oracle extracted verbatim from pinned ranges (SHA-256 `3326024d…66b3e` checked at runtime).
  Hit/MasterUnknown answers match `_answer_from_result` exactly. That function is confirmed to raise
  on FoldConflict, so conflict families are checked against hand-audited fixtures.
- Fold parity with G18AN `p01_ascii_fold`, the adapter's `_ascii_fold_to_bytes` and
  `format.ascii_fold_bytes` (ASCII, non-ASCII, whitespace, boundary characters).
- Real broker: cache key uses text folds; the payload holds only fold-family facts (no
  query literal, match kind or Master SHA); coverage is compact; builder errors publish nothing and
  close the provider; same-fold/different-literal reuse (§20) reuses the same view with no provider
  open; `cpm_compat_v2` does not reuse v1; the compatibility identity and the stable descriptor
  fields are equal across brokers.
- G18AN blob `e8c1bce…` unchanged; no diff under `tools/`, `tests/` or `cpm/baseline/`.

## Unresolved

- Suite 1 deferred items: live-snapshot parity, final-signature parity and mutation parity against
  G18AN on real presets. These need Stage M / Stage F wiring, so they are out of Step 1 scope.
- `tests/sidecar/qualification/verify_py27_equivalence.py` is not runnable as-is: its hardcoded
  scratch fixture directories no longer exist, and it pins a pre-integration Normalizer SHA. It was
  left unmodified. Py2.7.5 equivalence was instead shown with the established two-interpreter
  publish/acquire technique plus a digest comparison.
- `CPM_DESCRIPTOR_PROVIDER_GENERATION` is a fixed constant (1). Whether G18AN's
  `prod_scope_matches_identity()` inputs need any further mapping is a bootstrap-wiring decision.

## Next

Stop at this checkpoint and await operator review of Step 1. Rerun the suite (Python 3:
`--phase=publish`; Python 2.7.5: `--phase=suite`, then `--phase=compare`) before building on it.

Maintenance: Update at checkpoints. Replace stale entries; keep about one screen. Preserve unresolved issues. Verify relevant claims when resuming. Keep history in Git or an archive.
