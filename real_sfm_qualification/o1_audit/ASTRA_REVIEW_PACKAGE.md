# Astra Review Package — O1 Rebuild + Normalizer Material Redundancy Audit

## Purpose

Independent review of `O1_REBUILD_NORMALIZER_MATERIAL_REDUNDANCY_AUDIT.md` before any production
change is considered. **This is a review request, not an implementation request.** Do not write fixes.

## Governing optimization rule (applies to this review too)

> Tangible savings, demonstrated redundancy, zero functional compromise.

Do not endorse or suggest millisecond-level loop tuning, tiny allocation reductions, cosmetic
refactors, reduced validation, narrower model support, stale caching, skipped freshness checks,
weakened isolation, reduced failure safety, or reduced Normalizer/Rebuild functionality. Functionality
and semantic correctness are frozen requirements.

## Review questions

1. Did O1 miss any material redundancies or lifetime problems?
2. Are any O1 candidates falsely labeled redundant despite being required for correctness?
3. Are there important Rebuild/Normalizer overlaps we failed to recognize?
4. Are any proposed measurement directions unsafe or misleading?
5. Which candidates, if any, deserve runtime measurement before considering changes?

## Package contents

All files below are the **exact accepted, currently-deployed versions** — every SHA-256 has been
independently verified in this session to match the live SFM installation. No new copies were made;
this package references existing repo paths plus the newly-written O1 audit and condensed evidence
summary.

### 1. Current production Normalizer

`audit_external_runtime/Rebuild_Control_Groups_Normalizer.py`
SHA-256: `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
(confirmed identical to the live installed copy at
`game/usermod/scripts/sfm/mainmenu/ChadChan3D/Rebuild_Control_Groups_Normalizer.py`)

### 2. Authority/broker implementation (accepted package, deployed)

Directory: `tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/`
(confirmed file-for-file identical, by SHA-256, to the live deployed
`game/usermod/scripts/sfm/mainmenu/ChadChan3D/sfm_master_authority_productionized/` directory)

Most relevant files for this review:
- `broker.py` — SHA-256 `b2113da7da5954e88f40f780cc36f012f5451ebcf6db4e5b8baf2d413cd9c514`
  (view/provider/lease lifecycle, `acquire_or_reuse_views()`, `provider_counters()`)
- `runtime.py` — SHA-256 `961a31d1e54171110f1f0e2abcb0bc615fe7c4a77689abae3510cd5469c9915c`
  (`get_broker()` entry point, API/build identity)
- `resource_estimator.py` — SHA-256 `1cc3649a44e1b3777afdd9f86c70386b2bc8d700508037e6a41d748a399771dd`
- `resource_preflight.py` — SHA-256 `8ac3795453cddcd13ceb59a1d9989561e3c0919fc7a163bc569e0ca2e05afec5`
  (existing historical-authority memory envelopes — relevant context for what's already resource-governed
  vs. what O1 is newly examining)
- `views.py`, `view_cache.py`, `cohort.py`, `selection.py`, `observation.py` — supporting
  view-acquisition infrastructure, present in the same directory if deeper reading is needed.

### 3. Integration code (production Normalizer ↔ authority package)

`tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/normalizer_compat_adapter.py`
SHA-256: `acfdb4e925f0c46e128b4a6b7c2a84e8d073930afb3527b660abb082add7661b`
(confirmed identical to the live deployed copy — the adapter layer between the Normalizer's own
`exec()`-time imports and the authority package's `runtime`/`broker` objects)

The production Normalizer's own per-target pipeline (`run_target_transaction()`,
`snapshot_work()`, `capture_snapshot_explicit()`, `capture_tree()`, `production_generic_composer()`)
lives entirely inside file #1 above — this is the primary subject of the O1 audit and should receive
the closest reading.

### 4. O1 audit itself

`real_sfm_qualification/o1_audit/O1_REBUILD_NORMALIZER_MATERIAL_REDUNDANCY_AUDIT.md`
Status: STATIC MATERIAL-REDUNDANCY AUDIT — COMPLETE / AWAITING INDEPENDENT REVIEW. Not approved.

### 5. Condensed F1 series evidence

`real_sfm_qualification/o1_audit/F1_EVIDENCE_SUMMARY_FOR_ASTRA.md` — condensed orientation covering
F1-1 (crash), F1-R1 (harness-side attribution), F1-2 (production-internal ~227 MiB/command-3 finding),
F1-R2 (parked, design-only). Full detail is in `real_sfm_qualification/LEDGER.md` and each checkpoint's
own directory if deeper verification of any specific figure is needed.

### 6. F1-R2 — context only, not an accepted next step

`real_sfm_qualification/checkpoint_f1_r2/` (both phase scripts + INSTRUCTIONS.md) is included for
context on the runtime-proof mechanism already available if O1's candidates still need empirical
confirmation after this review. **F1-R2 has not been run and is not proposed as the next action by this
package** — it is parked pending this review's outcome.

## What is explicitly NOT being asked of Astra

- Do not write or propose code changes.
- Do not approve any candidate for implementation.
- Do not assume any O1 candidate's expected-impact classification is correct without checking the
  cited line evidence yourself.

## How to use this package

Read file #1 (the Normalizer) with the O1 audit (#4) open alongside it — every candidate cites exact
line numbers in file #1. Files #2/#3 are needed only if a candidate's correctness dependency involves
authority/broker interaction (none of the three final O1 candidates do, but review question 3 asks
specifically about Rebuild/Normalizer overlaps, and the authority package is the other major
integration surface this Normalizer touches). File #5 provides the resource-evidence motivation; file
#6 is background only.
