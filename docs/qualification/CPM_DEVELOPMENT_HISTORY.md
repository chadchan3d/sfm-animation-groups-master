> **Repository context (added by this checkpoint, not part of the original CPM document):** source repository `chadchan3d/sfm-character-preset-manager`, commit `390e01e` (`390e01eb7ac1ceb220e480126f40077703acb0f4`), original path `docs/DEVELOPMENT_HISTORY.md`, source SHA-256 `f1027660e074882c0e441bcbed97f87f19f635acaccdf7b007db8c40c84601d1`.
>
> This repository (`chadchan3d/sfm-animation-groups-master`) is now the continuing home of SFM Character Tools and CPM convergence. The CPM repository is closed at commit `390e01e` as a source archive; this supersedes any statement below that the CPM repository "remains canonical."
>
> "Shared authority remains unchanged" means the `sfm_master_authority_productionized` package in this repository stays byte-stable at its already-qualified build; CPM code is not added to that package.
>
> References below to CPM-repo paths map to their imported locations here: `README.md` is not imported and remains only in the closed CPM source archive; `docs/ENGINEERING_NOTES.md` -> `docs/qualification/CPM_ENGINEERING_NOTES.md`; `docs/DEVELOPMENT_HISTORY.md` -> `docs/qualification/CPM_DEVELOPMENT_HISTORY.md`; `docs/reviews/CPM_CONVERGENCE_ADVERSARIAL_REVIEW.md` -> `docs/qualification/CPM_CONVERGENCE_ADVERSARIAL_REVIEW.md`; `docs/SFM_CHARACTER_TOOLS_INTEGRATION_HANDOFF.md` -> `docs/qualification/CPM_CONVERGENCE_INTEGRATION_HANDOFF.md`; `src/SFM_CSP_G18AN_SaveNewCopy.py` -> `cpm/baseline/SFM_CSP_G18AN_SaveNewCopy.py`.
>
> Everything below this line is exact imported content.

---

# Development history

SFM Character Preset Manager was developed substantially before this Git repository existed.

This document preserves a public-safe chronology supported by surviving source, runtime evidence, qualification records, performance assessments, and audits.

The historical G-series, RC, P, Q, and other development identifiers:

- predate this Git repository;
- are development or qualification identifiers;
- are not historical Git commits; and
- must not be interpreted as reconstructed Git history.

Git history begins with the surviving G18AN development baseline. No retrospective commits are manufactured for earlier work.

## Product model

The project converged on four primary workflows:

1. **Body Presets** — save and reuse body flexes plus generic bone scaling.
2. **Expressions** — save and reuse facial-expression flexes separately.
3. **Clothing Fit** — match compatible selected clothing/accessories to the selected model's body state.
4. **Review** — classify genuine semantic-authority misses without overriding positive or conflicted authority results.

The product deliberately keeps Body and Expression state separate. Skins and bodygroups are not part of the current Body Preset definition.

## Native mutation foundation

Early qualification established the mutation discipline retained by the current production lineage:

- preflight before mutation;
- no-op detection before opening Undo;
- one explicit native SFM Undo operation for a bounded mutation;
- write and verification before commit where applicable;
- Finish Undo;
- same-time refresh;
- Qt event processing; and
- independent postcommit/readback verification.

Qualified low-level flex and bone-scale mutation mechanics were subsequently treated as frozen unless new runtime evidence contradicted them.

## Generic bone scaling

The project initially used narrow model-specific scaling work to establish safe mechanics, including a Head Scale path.

That path was superseded by a generic complete-map architecture. Body Presets now treat supported bone scaling as a generic production feature rather than a hardcoded per-character exception.

Qualification later covered:

- capture of the complete supported bone-scale map;
- writing existing scale controls;
- creation of a missing supported scale graph;
- non-default physical multipliers, including a 2.0× case; and
- persistence across a saved-session reopen.

The current saved representation identifies a bone by index and name and stores a uniform physical scale multiplier.

## Semantic authority and Review

The Animation Groups Master became the semantic authority for ordinary flex classification.

The durable rules are:

- preserve exact control literals;
- do not silently normalize punctuation or whitespace;
- distinguish a genuine healthy-authority miss from authority unavailable;
- fail closed on missing, stale, incompatible, or generation-mismatched authority;
- do not let local Review choices override positive authority results; and
- do not let local Review choices override authority conflicts.

Review was qualified specifically as a miss-only recovery layer rather than an alternate semantic authority.

## Storage and identity

The current primary preset schema is v3, with readable legacy-v2 support retained for existing libraries.

The durable runtime model identity was refined to normalized model path plus model checksum.

Animation Set name was proven mutable during ordinary SFM use and was therefore demoted to display/runtime metadata. A simple rename can be accepted when path and checksum still resolve one unique live instance; ambiguous duplicate instances fail closed and require reselection.

## Exact-set compatibility

Body and Expression Apply intentionally reject incompatible old semantic sets rather than partially applying a subset.

For flex state, the saved mutation-key set must equal the currently accepted semantic flex key set. Body Presets additionally require compatible saved bone-layout identity.

This rule protects users from a quiet partial application after model or semantic-authority changes.

## Clothing Fit

Clothing Fit evolved into a persistent workflow with a strict transaction rule:

- Body membership comes from the selected model's current semantic scope;
- actual source-target correspondence is structural/native;
- compatibility is planned before mutation;
- one changed target receives one native transaction; and
- each target is staged on its own zero-delay Qt event turn.

This preserves per-target Undo behavior and keeps long scene-facing work bounded.

## Long-lived palette and foreign modals

The Manager is a persistent nonmodal Qt palette.

Runtime testing established that an always-on-top project window must yield to foreign SFM modal dialogs. The current policy watches Qt modal state, publishes scene suspension before hiding, performs no scene-facing work while suspended, restores without stealing focus, and resumes a parked Clothing Fit stage at most once.

## Indexed Body capture performance

An earlier Body Save/Update implementation repeatedly traversed the complete native bone map and took roughly 3.7 seconds in the measured fixture, with substantial repeated private-memory growth.

A later operation-scoped indexed capture path was tested against the historical capture oracle and produced exact capture parity in the qualification workload.

Representative measured results after that change were approximately:

- Body Save: ~0.09–0.10 seconds;
- Body Update median: ~0.07 seconds; and
- indexed complete-map capture median: ~0.03 seconds.

The earlier per-operation memory-growth slope was not present in the indexed qualification run.

These are historical measurements under the tested fixtures, not universal performance guarantees.

## Shared-authority transition

The semantic-authority work later moved toward a compiled sidecar generated from the editable Animation Groups Master.

The intended runtime direction is:

- the editable Master is source of truth;
- a matching compiled sidecar is required runtime material;
- the sidecar must identify the active Master generation from which it was built; and
- ordinary runtime does not silently fall back to reparsing the TXT authority when the sidecar is missing or stale.

The current G18AN source consumes a development-era sidecar deployment and therefore remains a development baseline rather than a final public release package.

## G18AN baseline

G18AN is the surviving source imported at Git adoption.

Its product-facing change from the immediately preceding lineage was intentionally small: both tab-local create buttons use the concise label **Save New**, while an ineffective equal-stretch layout experiment was reverted.

G18AN otherwise inherits the qualified semantic scope, persistence, generic bone scaling, Clothing Fit, Review, model-identity, modal-yield, and native mutation behavior of the preceding production lineage.

## Remaining pre-1.0 gates at Git adoption

The remaining release work includes:

1. integrate the final shared-authority/package contract;
2. qualify controlled source-generation mismatch behavior without damaging a user's real authority package;
3. qualify deliberately forced rollback-verification failure branches for preset Apply and Clothing Fit;
4. remove historical/development-only dead code and diagnostic machinery without reopening frozen mutation mechanics;
5. reduce qualification logging to release-appropriate output while preserving nonthrowing logging safety;
6. run an exact release-artifact regression across startup, model identity, Body, Expressions, generic scale, Clothing Fit, Review, modal yield, storage, authority mismatch, and shutdown behavior; and
7. package and document the actual release artifact.

No v1.0 tag or release should be inferred until those gates are closed against the final artifact.
