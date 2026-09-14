# SFM Animation Groups Master

A curated, structurally-validated `sfm_defaultanimationgroups.txt` for Source
Filmmaker, plus a compiled binary "sidecar" format that lets SFM's in-game
Normalizer tooling look up controls in that Master without re-parsing the
full TXT file on every query.

## What's here

- **`sfm_defaultanimationgroups.txt`** — the canonical Master: SFM's
  animation-group hierarchy (rig groups, controls, flexes, helper bones,
  metadata) reorganized and taxonomy-corrected from the stock/community
  baseline, while preserving every exact control literal.
- **`reference/`** — comparison data used while building the Master.
  (The third-party "Silkworm" reference file used during that work is kept
  locally only and is intentionally not part of this repository — see
  `.gitignore`.)
- **`tools/sfm_master_sidecar/`** — the compiled sidecar format: a compiler,
  binary reader/writer, manifest/publisher, and CLI, built to reproduce the
  Normalizer's exact lookup/fold/conflict semantics from a compact binary
  artifact instead of the raw TXT.
- **`tools/validate_master.py`** — a read-only structural validator for the
  Master (brace/indentation structure, exact-duplicate controls, and a
  native-Rebuild ASCII-casefold cross-path invariant).
- **`tools/verify_phase2_production_order.py`**, **`tools/extract_phase2_human_review.py`**
  — supporting tools from the taxonomy production pass.
- **`tests/`** — the pytest suite for the sidecar format, plus a
  `tests/sidecar/qualification/` harness suite that qualifies the sidecar
  against the real, unmodified Normalizer/T130 consumer source as a
  read-only oracle (desktop Python 3, cross-checked against real embedded
  Python 2.7 where noted).
- **`SFM_MASTER_SIDECAR_*.md`, `SFM_SIDECAR_*.md`** — the gate-by-gate
  design and qualification audit trail for the sidecar work: architecture
  decisions, resource/performance baselines, and the evidence behind each
  qualification verdict.
- **`HELPERS_*`, `MASTER_*`, `PHASE2_*`, `SEXUAL_BONES_*`** — the taxonomy
  classification ledgers and human-review records behind the Master's
  current organization.

## Editing the Master

The Master is maintained through deterministic, re-validated Python edits
rather than free-form text generation — see `CLAUDE.md` for the exact
editing contract (canonical-file discipline, structural parsing rules,
duplicate/casefold invariants, and the validate-before-promote workflow).

## Running the tests

```
python -m pytest tests/
python tools/validate_master.py sfm_defaultanimationgroups.txt
```

Some qualification harnesses under `tests/sidecar/qualification/` compare
the sidecar against the real, externally-owned SFM Normalizer/T130 source.
Those files aren't distributed with this repository; the harnesses that
need them report a clear skip with the exact environment variable
(`SFM_NORMALIZER_ORACLE_PATH`, `SFM_T130_ORACLE_PATH`) to set if you have
your own copies.

## License

Original material in this repository is released under CC0 1.0 (see
`LICENSE`) — public domain dedication, no rights reserved.
