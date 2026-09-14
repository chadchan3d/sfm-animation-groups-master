# Qualification audit trail

Design, decision, and gate-by-gate audit documents for the compiled
"sidecar" format under `tools/sfm_master_sidecar/` — architecture proposals,
compatibility/parity/timing gate reports, resource baselines, and the
evidence behind each qualification verdict, plus post-close-out chronology
and claims-ledger documents.

This is documentary/narrative evidence, not runnable code. The actual
qualification harnesses and their fixtures live under
`tests/sidecar/qualification/`; this directory records what those harnesses
found and why the design evolved the way it did, gate by gate.

`SFM_SIDECAR_NORMALIZER_R1_PARITY_MATRIX.json` is the one non-Markdown file
here: the machine-readable parity matrix referenced by the R1 consumer-
projection audit.
