# B2C-D Handoff — Architecture & Evidence Entry Point for Astra
**Date:** 2026-09-21

Purpose: give Astra a concise entry point for designing B2C-D, on top of a fully qualified,
independently re-audited B2C-B + B2C-C baseline. This document is a summary and pointer set, not a
replacement for the underlying reports/ledgers it cites.

**This document does not authorize production promotion.**

## Qualified baseline — B2C-B

- Correction6 final independent PASS.
- Immutable authority checkpoint: `514a100a380e33b6b6281afdc489921fd68728e1`.
- No silent TXT fallback (verified — the qualified path never falls back to the frozen text
  parser's output on the migrated success path).
- Broker/generation/resource/lease architecture (`sfm_master_authority_productionized`: `broker`,
  `sidecar_contract`, `selection`, `resource_preflight`, `view_cache`, `cohort`, `resolver`,
  `descriptors`, `projections`, `normalizer_compat_adapter`, etc.) qualified through Corrections
  2–6, independently re-audited.

## Qualified baseline — B2C-C

- Final correction commit: `3b5aaa955bafa822da27603514271944b280654e`.
- Independent PASS: `INDEPENDENT B2C-C RE-AUDIT PASS — B2C-C CLOSED — AUTHORIZE B2C-D` (see
  `tests/sidecar/qualification/R3_B2C_C_Independent_Reaudit_3b5aaa9_Report.md`).
- Downstream equivalence proven for:
  - decision plans;
  - native mutation streams;
  - final logical trees.
- Coverage includes:
  - left/right side normalization;
  - active-rig toe relocation;
  - flex-first ordering;
  - Tail generic relocation (via the real generic reconciliation machinery — no Tail-specific
    runtime branch exists; proven against BOTH a corrected synthetic fixture (D6) and the REAL
    canonical Master's actual root-level `Tail` group);
  - repeated-control preservation;
  - untouched custom-subtree preservation (exact zero-mutation-log-entries proof, not just a hash
    comparison).
- Broker-to-execution composition explicitly qualified: the real broker-acquired payload for a
  qualified fixture is canonically identical to the direct-provider projection used everywhere
  else in the B2C-C harness, and produces identical native-mutation-stream/final-tree output when
  run through the real `production_generic_composer`.

Full evidence trail: `tests/sidecar/qualification/R3_B2C_C_Downstream_Mutation_Equivalence_Report.md`
(Parts 1–4), `R3_B2C_C_execution_layer_ledger.json`, `R3_B2C_C_plan_layer_ledger.json`,
`docs/qualification/SFM_SIDECAR_POSTC3_CLAIMS_LEDGER.md` (Addenda 1–4).

## Remaining known B2C-D attack surface

Astra should focus on lifecycle/fault-injection hazards such as:
- generation changes during command lifetime;
- stale authority/view use;
- A → B generation transitions;
- cache invalidation;
- provider/lease cleanup;
- failed lease release and durable reconciliation;
- missing/corrupt/incompatible sidecar;
- resource-admission refusal;
- source-generation mismatch;
- recovery to permitted matching sidecar;
- zero mutation on authority failure;
- command interruption at selected lifecycle stages;
- repeated-command state hygiene;
- retained/transient memory accounting across command sequences;
- final authorization → native-use race;
- no silent TXT fallback under any failure path.

## Explicitly deferred later/live gates

- live SFM target/scope enumeration;
- real host timing;
- native `ifm.dll` rebuild behavior;
- W3 remains `UNKNOWN`;
- production promotion.

## Astra task

Given the fully qualified B2C-B and B2C-C baseline, what lifecycle/fault-injection failures remain
capable of producing stale authority, mixed generations, unsafe mutation, resource/lease leakage,
or silent fallback? Design the minimum decisive B2C-D test program required before live-SFM
qualification.
