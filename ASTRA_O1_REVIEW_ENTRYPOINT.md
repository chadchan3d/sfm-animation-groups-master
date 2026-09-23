# Astra O1 Review — Entrypoint

This document orients an independent reviewer (Astra) to the O1 material-redundancy audit. **It is not
a substitute for source inspection.** The review artifact is the repository itself, at the immutable
commit below — not a separate package or extract.

## Immutable review baseline

Commit SHA: **`dc92623f17c6b151b7bf5f6ed4ab65cb3f1e29ea`** (short form `dc92623`)

Treat this commit as fixed. Every claim in O1 and in the qualification ledger should be checkable
against the exact files as they exist at this commit.

## Governing optimization rule

> Tangible savings, demonstrated redundancy, zero functional compromise.

Explicitly, for this review and for anything it may lead to later:

- **No micro-optimization campaign.** Millisecond-level loop tuning, tiny allocation reductions, and
  cosmetic refactors are out of scope.
- **No functionality reduction.**
- **No semantic weakening.**
- **No validation reduction.**
- **No model-support reduction.**
- **No stale caching, skipped freshness checks, or weakened isolation.**
- **No implementation is authorized yet.** This is a review of an audit, not a request to build or fix
  anything.

## Start here

Read first: **`real_sfm_qualification/o1_audit/O1_REBUILD_NORMALIZER_MATERIAL_REDUNDANCY_AUDIT.md`**

That document states its own method, cites exact file:line evidence for every claim, and lists its
three candidates plus what it explicitly rejected as immaterial and why.

## Starting manifest (not a restrictive file list)

These are the files most directly relevant to O1's claims — a starting point for navigation, not a
boundary:

- **Production Normalizer** (primary subject of the audit):
  `audit_external_runtime/Rebuild_Control_Groups_Normalizer.py`
  SHA-256 `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867` — confirmed identical to the
  live installed copy at commit time.
- **Authority/broker implementation** (accepted, deployed package):
  `tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/`
  — in particular `broker.py`, `runtime.py`, `resource_estimator.py`, `resource_preflight.py`,
  `views.py`, `view_cache.py`, `cohort.py`, `observation.py`, `selection.py`. This directory is
  confirmed file-for-file identical, by SHA-256, to the live deployed authority package.
- **Integration adapter** (production Normalizer ↔ authority package):
  `tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/normalizer_compat_adapter.py`
- **Qualification ledger** (the full, unabridged record of every real-SFM checkpoint run):
  `real_sfm_qualification/LEDGER.md`
- **Relevant F1 evidence and static audits**:
  - `real_sfm_qualification/checkpoint_f1/F1-1_STATIC_AUDIT.md` — the F1 harness's own object-lifetime
    audit, and `real_sfm_qualification/checkpoint_f1/f1_1_crash_evidence/` — the preserved production
    log from the F1-1 SFM crash.
  - `real_sfm_qualification/checkpoint_f1_r1/F1-R1_SEMANTIC_CAPTURE_STATIC_PROOF.md` — the harness-side
    attribution finding (Python/CRT allocator high-water retention) and its offline empirical test
    (`test_allocator_highwater_retention.py`).
  - `real_sfm_qualification/checkpoint_f1_2/F1-2_PRODUCTION_INTERNAL_STATIC_AUDIT.md` — the earlier,
    narrower static audit of `self.work` that O1 independently re-traced and partially corrected.
  - `real_sfm_qualification/o1_audit/F1_EVIDENCE_SUMMARY_FOR_ASTRA.md` — a condensed orientation across
    F1-1/F1-R1/F1-2/F1-R2; use the ledger for the authoritative, unabridged figures.
  - `real_sfm_qualification/checkpoint_f1_r2/` — the F1-R2 diagnostic (both phase scripts +
    `INSTRUCTIONS.md`). **Status: PARKED / UNRUN.** It has been built and offline-regressed but has not
    been executed against real SFM and is not an accepted next step — included as context for what
    runtime-proof mechanism already exists if O1's candidates need empirical confirmation later.

> **Astra may and should inspect any other repository file necessary to verify dependencies, ownership,
> lifetime, call flow, or correctness assumptions. The manifest above is only a starting point, not a
> restriction.**

## Current O1 candidates (hypotheses, not conclusions)

Stated here without argument — see the O1 document itself for the full evidence and reasoning behind
each:

1. **Retained/dead `self.work` `aset` reference** — a live native DME reference stored once per eligible
   target and, per O1's trace, apparently never read by any consumer thereafter.
2. **Repeated full recursive semantic-tree captures** — up to 3-5 full `capture_tree()` walks per
   target within one command, with at least two flagged as structurally or source-documented redundant.
3. **Unconditional warm-path classification/planning/composer** — the full pipeline runs identically
   whether or not a target is already normalized, per an explicit in-source design comment.

These are hypotheses awaiting independent review, not accepted findings.

## Known runtime evidence (concise facts only)

- Selected repeated-use (two consecutive Selected-Shots commands) remained comparatively stable:
  small, healthy private-memory growth and zero free-VAS loss, with confirmed idempotence.
- The lightweight F1-2 first All-Shots production pass increased private memory by about 227 MiB and
  consumed about 222 MiB of free VAS, within that one production command's own start/end measurement.
- Production's own periodic-global and end-of-run streaming verifiers showed zero private-memory delta
  across their own execution — the growth accumulates during target/shot processing itself.
- Checkpoint F1-R2 exists (both phase scripts, offline-regressed) but is **parked and unrun**.

Full figures, exact byte counts, and the underlying machine-derived evidence are in
`real_sfm_qualification/LEDGER.md` (rows F1-1, F1-R1, F1-2, F1-R2, O1) — this section is a summary only.

## Companion document

See `ASTRA_O1_AUDIT_PROMPT.md` for the exact audit instruction and the five questions Astra should
answer.
