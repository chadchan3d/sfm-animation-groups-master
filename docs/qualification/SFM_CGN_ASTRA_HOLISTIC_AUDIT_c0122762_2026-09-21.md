# Astra Holistic Audit Disposition — Commit c0122762
**Date:** 2026-09-21

Governing prompt: `SFM_SharedAuthority_PackageBoundaryCorrection_ClaudeCode_Prompt_2026-09-21.md`.
This document records Astra's holistic review of the shared-authority architecture at commit
`c0122762acf11b8ccc4bb7b9d0d891434bf4eb7c` in-repo, before any implementation correction. Every
defect below was independently re-inspected directly against the current source in this session
(not inferred from Astra's summary alone) before this document was written — see each subsection's
"Independently confirmed" note.

## Holistic verdict

- The shared-authority architecture is **fundamentally sound**.
- The compiled sidecar, packed provider, canonical broker, finite acquisition cohorts, and
  detached leased views should **remain** — no architectural redesign is warranted.
- Previous architecture concerns (B2A through B2C-C, Corrections 2–6) were **substantially
  resolved** — this review found package-boundary/deployment-contract gaps, not a flaw in the core
  acquisition/lease/coverage model itself.
- **Begin production Normalizer integration** after the bounded package corrections below are
  closed.
- **Do not promote this checkpoint (`c0122762`) unchanged** — the two RELEASE/INTEGRATION BLOCKERS
  below must close first.
- **Do not create another broad B2C-D prerequisite campaign** — Astra explicitly advises against
  this; the remaining gaps are narrow, package-boundary defects, not evidence that more synthetic
  lifecycle qualification is needed.

Astra independently reran, under real 32-bit Python 2.7.5, against `c0122762`:

| Suite | Result |
|---|---|
| Decision equivalence | `55/55` |
| Execution equivalence | `125/125` |
| Broker composition | `20/20` |
| Semantic regression | `14/14` |
| Pre-read floor | `18/18` |
| Offset-independent preflight | `20/20` |
| Durable cleanup | `25/25` |

Recommended shipping sequence: **canonical installed package → connected Normalizer → decisive
real-SFM qualification → release → separate CPM migration**.

## Reproduced defect A — leased orphan views escape generation invalidation
**Priority: RELEASE / INTEGRATION BLOCKER**

Astra reproduced:
- `ViewCache._remove()` preserves displaced leased views in `_leased_orphans`;
- `invalidate_generation()` visits only cached entries;
- after acquire A → replace A while borrowed → acquire B, the original orphan A token remained
  valid;
- accounting survived replacement, but revocation did not.

**Independently confirmed** by direct reading of `candidate_b2c_correction6/sfm_master_authority_
productionized/view_cache.py`: `invalidate_generation()` iterated `self._entries.values()` only,
never `self._leased_orphans`. A view displaced into `_leased_orphans` by `_remove()` (the
`admit()`/`admit_batch()` same-cache-key retirement path) keeps its own `authorization` token
unless that exact token object is separately visited. Confirmed empirically with a constructed
repro (separate per-cohort tokens, matching the real one-token-per-cohort model in `cohort.py:144`)
before any fix: the orphan's token remained valid after `invalidate_generation()`.

Important nuance (Astra's own, preserved):
- this did not independently prove a stale Normalizer mutation;
- additional Normalizer source checks still exist;
- nevertheless generation invalidation semantics are incomplete and must be corrected.

## Reproduced defect B — compiler output and broker input do not form one deployable contract
**Priority: RELEASE / INTEGRATION BLOCKER**

Astra reproduced:
- public compiler publishes `source_sha256`/`sidecar_sha256` manifests and `.bin` generations;
- runtime expects different pointer fields and a different artifact layout;
- a real successful CLI compilation produced a manifest rejected by runtime;
- the resulting output directory was reported as `SidecarMissing`.

**Independently confirmed** by direct reading of `tools/sfm_master_sidecar/compiler.py`
(`generation_basename()` emitted a `.bin`-suffixed name), `tools/sfm_master_sidecar/manifest.py`
(built/expected fields `source_sha256`/`source_byte_length`/`sidecar_sha256`/`generation_
basename`), `candidate_b2c_correction6/sfm_master_authority_productionized/selection.py`
(`_find_and_open_matching_artifact` scans only for `*.sfmsidecar`, so a real `.bin` publish is
invisible to it — confirmed `SidecarMissing` reproduces exactly), and `pointer.py` (required fields
`master_sha256`/`master_byte_length`/`artifact_sha256`/`artifact_relative_path` — none of which any
real publisher ever wrote; a real `manifest.json` raised `LocalPointerCorrupt: missing required
field 'master_sha256'`). Also confirmed: every existing qualification fixture builder bypasses the
public compiler/publisher entirely, hand-inventing its own `.sfmsidecar`-suffixed filename and a
fifth, ad-hoc manifest schema — which is exactly why this contract mismatch was never caught by
any existing test.

The supported publisher and runtime must share one canonical installed publication contract.

## Reproduced defect C — legacy `acquire_generation()` is broken
**Priority: IMPORTANT BUT DEFERRABLE unless currently exported/supported**

A real call raised `TypeError` because it passes `ledger=` to `select_sidecar_candidate()`, which
does not accept that argument.

The qualified Normalizer acquisition path does not use this API.

**Independently confirmed**: `broker.py`'s `_acquire_generation_once` passed the broker's ledger
object under a keyword named `ledger`; `selection.select_sidecar_candidate`'s real signature has
never accepted that keyword (its real resource-accounting parameter is `aggregate_existing_
retained_bytes`, an int). Confirmed the qualified path (`acquire_or_reuse_views` →
`acquire_cohort` → `cohort.py`'s `_open_provider_once`) has always used the correct parameter, so
this legacy method's breakage carries zero risk to already-qualified B2C-C evidence. Confirmed
`acquire_generation()` is a real, non-underscore, independently-documented public `Broker` method
— by that criterion it is part of the supported surface.

**Disposition:** fixed (smallest possible change — the same real parameter the qualified path
already uses), not deprecated/removed, per the "if supported/reachable, fix it" instruction. See
`R3_Package_Boundary_Correction_Report.md` for the regression proof.

## Reproduced defect D — failed batch admission can evict unrelated cache entries
**Priority: IMPORTANT BUT DEFERRABLE**

Astra reproduced an incoming batch evicting an unrelated unleased cache entry before refusing
admission. This contradicts an unchanged-cache-on-failure claim but does not publish incorrect
authority.

**Disposition:** deferred, per the governing prompt's explicit instruction not to expand this task
into a batch-admission redesign. Not touched by the package-boundary correction — no code path this
correction modifies interacts with `admit_batch()`'s eviction-before-refusal sequencing.

## Remaining release boundaries

Astra also identified:
- candidate bootstrap still depends on repository qualification paths, `__file__`, and provisional
  deployment directories;
- final Master hash does not protect native Rebuild from an intervening external TXT edit.

**Independently confirmed and additionally found**, while investigating defect B's contract: the
authority package's own `sidecar_contract.py` loaded its validator/provider dependencies from
`tests/sidecar/qualification/candidate_packed_validator_r3a2b.py`/`candidate_packed_provider_
r3a2b.py` — two levels outside the package itself, in the qualification directory, exactly the gap
Astra named. **Additionally found** (not named by Astra, discovered while tracing the package's own
import boundary): `sfm_master_authority_productionized/runtime.py` — "the one canonical
broker-factory entry point ... every caller must call" — has been **completely unimportable** the
entire time: its own canonical-module-name self-check hardcoded the OLD, pre-productionized package
name (`sfm_master_authority.runtime`), so importing it under its real name
(`sfm_master_authority_productionized.runtime`) always raised `ImportError`. Undiscovered until now
because no B2C-B/B2C-C test ever imported it (every existing test constructs `Broker()` directly or
uses `sidecar_contract`/`normalizer_compat_adapter` instead).

The native-use hash/write race is **NOT** part of this package-boundary task. It belongs in the
subsequent real Normalizer integration, with one decisive SFM compatibility test of the chosen
protection mechanism (a short Windows Master read handle permitting readers, denying writes/
deletion, held from final protected hash through native Rebuild and contextual reconciliation).

## What this document does NOT claim

This document records the review and independently-confirmed findings only. It does not itself
claim any defect is fixed — see `R3_Package_Boundary_Correction_Report.md` (a separate,
subsequent commit) for the implementation correction and its evidence. This checkpoint
(`c0122762`) remains un-promoted; do not begin Normalizer production integration on the strength of
this document alone.
