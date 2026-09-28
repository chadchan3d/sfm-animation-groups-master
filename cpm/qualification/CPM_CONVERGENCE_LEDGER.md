# Ledger

## Current milestone

CPM Convergence Step 2 investigation (handoff §22 step 2, discovery only): map the current CPM
semantic acquisition path and identify the minimum safe bootstrap seam for `cpm_compat_v1`. Done
means: `cpm/qualification/CPM_BOOTSTRAP_INTEGRATION_INVESTIGATION.md` committed, with no code
changes. Status: document written; awaiting review before any bootstrap code.

## Current state

Base `a52098e` on `master` (Step 1: `cpm/convergence/cpm_compat_v1_projection.py` plus Suite 1
foundation tests, 196/196 on Python 3.10 and 2.7.5, identical digests; Suite 1 PARTIAL). This
checkpoint adds only the investigation document and this ledger update. Frozen G18AN, the shared
package, `tools/` and the canonical Master are unchanged.

## Verified

- Earliest safe seam: `prod_scope(identity, provider=...)` (G18AN @20136) uses the provider only
  through `generation_descriptor()` and `query_many()`. It keeps only a descriptor dict, so the
  published scope stays pure.
- The seam is not sufficient alone. `prod_scope_matches_identity` (@19527) compares against the
  global `get_semantic_provider()` descriptor. Six production-route helpers reach the global
  directly, and Fit threads a provider object into `p03_unmapped_relevant_controls` (target
  vocabulary).
- `provider_generation` is always 1 per script execution: the singleton is never invalidated
  (`invalidate_semantic_provider` has no callers). G18AN has no in-process Master-change detection.
  Persisted `capture_provider` / `last_validated_provider` values are never read back. The Step 1
  constant (1) is value-compatible.
- Save/Update identity checks run before their modal prompts (@31999/@32018, @32221/@32294).
- The parity shortcut in `ProdWindow` (@28601 → @28841) constructs TXT and development-sidecar
  providers directly.

## Unresolved

- Suite 1 deferred items: live-snapshot, final-signature and mutation parity. The snapshot/signature
  part can be done offline in Step 2a.
- `verify_py27_equivalence.py` is not runnable as-is (stale scratch fixtures, pinned
  pre-integration Normalizer SHA). It was left unmodified; the two-interpreter digest technique is
  used instead.
- R3: the G18AN health gate needs whole-Master `occurrence_count` / `fold_family_count` and a
  qualified `provider_kind`. How the adapter supplies these is undecided.
- R6: behavior of late helpers that still reach the global provider before Step 3 (fail closed vs
  adapter-backed global) is undecided.
- R13: location and form of a G18AN-derived runnable CPM candidate needs a reviewer decision.
- UI reaction to a stale scope once freshness is real (R1) is unspecified.

## Next

Await review of the investigation. If approved, Step 2a: an offline CPM authority adapter under
`cpm/convergence/` (bootstrap checks, provider-shaped facade, descriptor/health mapping, freshness
check) plus offline snapshot/signature parity against extracted G18AN functions. No CPM runtime
edits until 2a and R13 are reviewed.

Maintenance: Update at checkpoints. Replace stale entries; keep about one screen. Preserve unresolved issues. Verify relevant claims when resuming. Keep history in Git or an archive.
