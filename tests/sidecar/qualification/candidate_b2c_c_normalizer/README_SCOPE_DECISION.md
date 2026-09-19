# Why this directory has no candidate Normalizer file

Every prior correction round (`candidate_b2c_correction2_normalizer/` through
`candidate_b2c_correction6_normalizer/`) held a full copy of the production
Normalizer with its authority-acquisition seam swapped to the qualified
broker/adapter, because those rounds needed a real, importable module whose
bootstrap logic (path resolution, build-ID checks, lease lifecycle) could be
exercised end-to-end.

B2C-C's actual comparison subject is narrower and more surgical: it extracts
the frozen production Normalizer's **decision-layer functions**
(`classify_production`, `preflight_reconciliation_plan`,
`derive_generic_uniformity_plan`, and their pure helper closure) directly, by
exact line range, from the real frozen file — see
`tests/sidecar/qualification/candidate_b2c_c/production_plan_layer.py`. Both
the baseline and migrated comparison runs call these SAME extracted functions;
the only input that differs between them is the `master` authority dict
(computed once via the frozen `parse_targeted_master`, once via the qualified
Correction6 `normalizer_compat_adapter`). There is no separate "candidate
Normalizer" source file to maintain for this comparison — the frozen
production file itself, read fresh at test time and SHA-256-pinned, is the
only Normalizer-shaped source involved.

See `tests/sidecar/qualification/R3_B2C_C_Downstream_Mutation_Equivalence_Report.md`
Section 2 for the full scope decision, including what this narrower
comparison does and does not prove.
