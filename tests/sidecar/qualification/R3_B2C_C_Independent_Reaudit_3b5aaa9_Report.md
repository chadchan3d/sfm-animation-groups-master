# R3 B2C-C Independent Re-Audit — Commit 3b5aaa9
**Date:** 2026-09-21

Governing prompt: `SFM_CGN_B2C_C_FinalDocumentationCheckpoint_ClaudeCode_Prompt_2026-09-21.md`.
This document records the independent re-audit result for the B2C-C targeted correction commit and
marks B2C-C **CLOSED**. It is a documentation record only — it changes no executable behavior and
does not itself authorize production promotion.

## Final independent verdict

**`INDEPENDENT B2C-C RE-AUDIT PASS — B2C-C CLOSED — AUTHORIZE B2C-D`**

Meaning:
- B2C-C downstream mutation equivalence is closed.
- B2C-D may begin after this documentation checkpoint.
- This is **not** production-promotion authorization.
- Live target/scope enumeration, native `ifm.dll` behavior, W3, and later live/runtime
  qualification remain separate, still-deferred gates.

## 1. Archive / correction integrity

- **Audit target (commit):** `3b5aaa955bafa822da27603514271944b280654e`
- **Audit ZIP:** `SFM_3b5aaa9_B2C_C_Correction_Independent_Audit.zip`
- **ZIP SHA-256:** `e5256e7a8f9ede2c709881111e1be1d59429de77c2c30e751af46db9b4eb1a16`
- **ZIP size:** `10,573,806` bytes
- **Tracked files:** `1,062`
- **No tracked `.pyc` / `__pycache__`** in the archive.
- The correction (`3b5aaa9`) is a narrow follow-up on the previously-audited commit
  `5cc98966d2425ca25ffcf310809fd01ae8514ff8` — pushed on top of it, no rebase/amend/force, 16 files
  changed (14 modified, 2 new), all within `tests/sidecar/qualification/` (execution/plan-layer
  harnesses, the `candidate_b2c_c` synthetic fixture/candidate directory, the two new dedicated
  test files, and the downstream-equivalence report/ledgers).
- **No Correction6 authority/runtime source was altered** — `candidate_b2c_correction6/` (the
  qualified authority package itself) does not appear in `3b5aaa9`'s diff at all.
- **No production Normalizer or canonical Master behavior was changed** — both are read-only
  inputs to every B2C-C test; their SHA-256 identities are re-verified unchanged below.

## 2. Corrected synthetic authority reproducibility

| Artifact | SHA-256 | Independently reproduced |
|---|---|---|
| Synthetic Master (`candidate_b2c_c/fixtures_authority/b2c_c_master.txt`) | `7c76648564d97b9e902174288ab1f2ceafd3a41eabdaddc05abf1c6a8cac7f0b` | yes, byte-for-byte, re-verified this checkpoint |
| Synthetic sidecar (`candidate_b2c_c/fixtures_authority/b2c_c.sfmsidecar`) | `1ed298b7f73d6b9fef97861ddd91e29823858ec93abbf4ec8cb5b5ff0ad04201` | yes, byte-for-byte, re-verified this checkpoint |

Independent rebuild reproduced the sidecar byte-for-byte.

## 3. Tail blocker — CLOSED

- The old D2 "Tail relocation" claim was retracted and the fixture renamed to
  `D2_rigbody_family_counterpart_refinement` — it is no longer claimed to demonstrate Tail
  anywhere in the report, the ledgers, or the fixture registry.
- The frozen production Normalizer has **no Tail-specific runtime branch**: a full
  case-insensitive grep of the entire 13,594-line frozen source for the literal "tail" returns
  zero matches (re-confirmed both in the prior correction round and by
  `test_b2c_c_tail_real_canonical_authority.py`'s own `grep.no_tail_runtime_branch` check).
- The canonical Master has a **root-level `Tail` group** (`sfm_defaultanimationgroups.txt`, line
  116343, indent depth 1 — a direct child of the top-level `groupFile` wrapper, a sibling of
  `Body`/`RigBody`/`RigArms`/etc, never nested under `Body`).
- An **independent full canonical-Master rebuild reproduced the official sidecar SHA**:
  `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` — re-verified this checkpoint
  against `official.sfmsidecar` on disk, byte-for-byte match.
- The Correction6 projection was **independently confirmed**: real Tail literals (`BaseTail`,
  `Back_tail_01_L`, `Back_tail_01_R`) resolve to destination `Tail` identically via the frozen
  `parse_targeted_master` and the Correction6 adapter, against the REAL canonical Master (not a
  synthetic stand-in) — `test_b2c_c_tail_real_canonical_authority.py`, 15/15 PASS.
- The new **D6** fixture exercises a genuine, observable generic downstream relocation into `Tail`:
  - `created_paths = ["Tail"]`
  - `moved_count = 2`
  - exact Master destination ordering: `destination_direct_order_authorities` records
    `{"Tail": {"order": ("tail_control_a", "tail_control_b"), "authority":
    "EXACT_MASTER_DESTINATION_TOTAL_ORDER"}}`
  - equal baseline/migrated decision-plan hashes (`D6_tail_relocation.decision_plan_regression`,
    PASS)
  - equal baseline/migrated native-mutation hashes (`D6_tail_relocation.native_mutation_stream`,
    PASS)
  - equal baseline/migrated final-tree hashes (`D6_tail_relocation.final_tree`, PASS)
  - stable repeat hashes (`D6_tail_relocation.determinism`, PASS; full repeat-1/repeat-2 SHAs
    preserved in `R3_B2C_C_execution_layer_ledger.json`)
- **Effective Tail negative control present**: NC-C (suppressing `AddControl` for
  `tail_control_a`, retaining it in `WrongGroup` instead of relocating it into `Tail`) is detected
  via mutation-stream and final-tree hash divergence.

## 4. Custom-subtree blocker — CLOSED

- The corrected D4 uses `UserCustomGroup/{Alpha,Beta}` (renamed from the original
  `CustomUserGroup/Nested` design, which never reached the real reorder function's early exit).
- Production's root reorder (`production_reorder_children_by_master`) now genuinely **early-exits**
  (`if desired == current_names: return desired`, evaluated before any `RemoveChild`/`AddChild`
  call) rather than performing an unconditional detach/re-add — because `UserCustomGroup` sorts
  alphabetically after `RigArms`, matching where a contextual (non-Master-known) group always lands
  in the function's own `desired` ordering anyway.
- D4 records (re-verified this checkpoint, direct execution):
  - `mutation_count = 0`
  - `created_paths = []`
  - `moved_count = 0`
- The fixture includes, as required:
  - two custom child groups (`UserCustomGroup/Alpha`, `UserCustomGroup/Beta`), in a known
    (alphabetical, deterministic) order;
  - two custom controls (`custom_control_alpha`, `custom_control_beta`);
  - non-default selectable/snappable/color/visibility state (`UserCustomGroup`:
    selectable=False, snappable=False, group_color=[11,22,33,255]; `Alpha`:
    group_color=[44,55,66,255]; `Beta`: visible=False, selectable=False).
- An **exact zero-touch mutation-log assertion exists**: `custom_subtree.zero_mutation_log_entries`
  builds one throwaway world to read out the real handles of `UserCustomGroup`/`Alpha`/`Beta` and
  the exact control names, then scans the ACTUAL baseline run's mutation log directly against
  them — zero matching entries, confirmed by direct execution (stronger than a hash-equality check
  alone, which could in principle mask a set-then-reset toggle).
- Baseline/migrated plan, mutation, and final-tree hashes match
  (`D4_untouched_custom_group_preservation.decision_plan_regression`/`.native_mutation_stream`/
  `.final_tree`, all PASS).
- Repeat hashes stable (`D4_untouched_custom_group_preservation.determinism`, PASS; full
  repeat-1/repeat-2 SHAs preserved in the ledger).
- **Effective accidental-custom-mutation negative control present**: NC-E-b (injecting one
  accidental `SetVisible(False)` call directly into the live world's `UserCustomGroup` at
  construction time) is detected via mutation-stream/final-tree divergence. NC-E-a's ineffective
  first attempt (wrapping `SetVisible` — never invoked, since real production never calls
  `SetVisible` on this group at all) remains honestly disclosed, not hidden.

## 5. Harness hardening — CLOSED

- All four RESULTS-accumulating B2C-C qualification scripts
  (`test_b2c_c_plan_layer_equivalence.py`, `test_b2c_c_execution_layer_equivalence.py`,
  `test_b2c_c_broker_mediated_authority_sanity.py`, `test_b2c_c_fake_dme_addchild_regression.py`)
  now return **non-zero process exit status on any failed check**
  (`if not all(condition for _, condition in RESULTS): sys.exit(1)`).
- A dedicated subprocess self-test (`test_b2c_c_exit_status_self_test.py`, 4/4 PASS) proves this in
  both directions: a synthetic script with every check passing exits 0; the same script with one
  check deliberately forced to fail exits non-zero; and a real, already-hardened file (run as a
  subprocess in its current genuinely-passing state) exits 0.
- Per-fixture deterministic repeat hashes and fixture-spec SHAs are preserved for all 16 named
  fixtures in both ledgers — 12 repeat-1/repeat-2 SHA fields per fixture (decision-plan,
  native-mutation-stream, final-tree, baseline and migrated), never replaced with only a
  `determinism_confirmed: true` boolean.
- Broker-to-execution D5 composition is explicit:
  - broker payload hash == direct-provider payload hash
    (`broker_payload_equals_direct_provider_projection`, PASS);
  - D5 execution through both payload sources yields identical mutation-stream and final-tree
    hashes (`broker_payload_execution_stream_matches`, `broker_payload_execution_tree_matches`,
    both PASS).

## 6. Fresh reported qualification totals (re-verified this checkpoint)

Real Python 2.7.5 / Windows, all processes exit code 0:

| Suite | Result |
|---|---|
| Decision layer | `55/55 PASS` |
| Execution layer | `125/125 PASS` |
| Broker sanity | `20/20 PASS` |
| Semantic regression | `14/14 PASS` |
| AddChild regression | `11/11 PASS` |
| Real canonical Tail closure | `15/15 PASS` |
| Exit-status self-test | `4/4 PASS` |

Canonical semantic structure hash remains: `3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2`

W3 remains: `UNKNOWN`

## Final disposition

**`INDEPENDENT B2C-C RE-AUDIT PASS — B2C-C CLOSED — AUTHORIZE B2C-D`**

**This does not authorize production promotion.**
