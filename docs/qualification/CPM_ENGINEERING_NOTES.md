> **Repository context (added by this checkpoint, not part of the original CPM document):** source repository `chadchan3d/sfm-character-preset-manager`, commit `390e01e` (`390e01eb7ac1ceb220e480126f40077703acb0f4`), original path `docs/ENGINEERING_NOTES.md`, source SHA-256 `10bb08dbf658c0cac25f2a5bae52c8c73b6ba84e8cea9b1b8b25b6b74c60d7c4`.
>
> This repository (`chadchan3d/sfm-animation-groups-master`) is now the continuing home of SFM Character Tools and CPM convergence. The CPM repository is closed at commit `390e01e` as a source archive; this supersedes any statement below that the CPM repository "remains canonical."
>
> "Shared authority remains unchanged" means the `sfm_master_authority_productionized` package in this repository stays byte-stable at its already-qualified build; CPM code is not added to that package.
>
> References below to CPM-repo paths map to their imported locations here: `README.md` is not imported and remains only in the closed CPM source archive; `docs/ENGINEERING_NOTES.md` -> `docs/qualification/CPM_ENGINEERING_NOTES.md`; `docs/DEVELOPMENT_HISTORY.md` -> `docs/qualification/CPM_DEVELOPMENT_HISTORY.md`; `docs/reviews/CPM_CONVERGENCE_ADVERSARIAL_REVIEW.md` -> `docs/qualification/CPM_CONVERGENCE_ADVERSARIAL_REVIEW.md`; `docs/SFM_CHARACTER_TOOLS_INTEGRATION_HANDOFF.md` -> `docs/qualification/CPM_CONVERGENCE_INTEGRATION_HANDOFF.md`; `src/SFM_CSP_G18AN_SaveNewCopy.py` is not imported and remains only in the closed CPM source archive.
>
> Everything below this line is exact imported content.

---

# Engineering notes

These notes describe the architecture preserved by the G18AN development baseline and distinguish current production rules from limitations that remain before a public 1.0 release.

They are not a substitute for final release qualification.

## Evidence language

This document uses three practical categories:

- **Observed** — established by preserved live SFM runtime evidence or a controlled measured qualification.
- **Production rule** — behavior implemented in the current lineage because of that evidence and the product's safety model.
- **Limitation** — not established generally, still pending controlled qualification, or intentionally outside current scope.

## Runtime environment

**Production rule:** The Manager targets SFM's embedded Python 2.7.5 32-bit environment with PySide 1.2 and Qt 4.8.x.

**Production rule:** MAINMENU execution must not assume `__file__` exists or that the process working directory identifies the script location.

## Long-lived state versus native objects

The persistent Manager window outlives individual scene operations.

**Production rule:** Long-lived selected-character semantic state is pure Python data.

The semantic scope stores durable identity, authority generation/provenance, policy revision, vocabulary/representation signatures, semantic descriptors, unresolved/conflict information, and local Review state.

**Production rule:** Live DME/SFM/native objects are operation-local. Before Save, Update, Apply, or Clothing Fit touches the scene, the Manager resolves fresh live bindings and verifies that model identity, authority generation, semantic policy, live vocabulary, and live representation still match the cached scope.

**Production rule:** Stale or ambiguous state fails before mutation rather than mutating through an old native handle.

## Model identity

**Observed:** Animation Set names can change during ordinary SFM use while the underlying model instance remains the intended model.

**Production rule:** Durable model identity uses normalized model path plus model checksum.

**Production rule:** Animation Set name is mutable display/runtime metadata.

**Production rule:** If path and checksum resolve exactly one live Animation Set, an ordinary rename is accepted and the display metadata is refreshed.

**Production rule:** If duplicate identical model instances remain ambiguous, the Manager does not guess. It requires model-list refresh/reselection.

## Semantic authority

The Animation Groups Master is semantic authority for ordinary FLEX classification.

**Production rule:** Exact literal spelling is authoritative. The consumer does not silently strip whitespace, normalize punctuation, or perform general Unicode casefolding.

The operational semantic states are intentionally distinct:

- positive resolved path;
- genuine healthy-authority miss;
- authority conflict; and
- authority unavailable/incompatible.

**Production rule:** A healthy miss may become Review material.

**Production rule:** Missing, corrupt, stale, incompatible, or source-generation-mismatched authority fails closed and is not reinterpreted as an ordinary unknown flex.

**Production rule:** Local Review choices cannot override positive authority or conflicts.

**Limitation:** G18AN still contains development-era sidecar deployment assumptions. The final public shared-authority package and consumer seam are not yet integrated in this baseline.

## Semantic scope categories

The Manager derives operational membership from resolved authority paths:

- Face paths are treated as Expression;
- exact `Body Morphs` is treated as Body;
- other resolved paths are treated as Other;
- healthy misses are Review candidates; and
- conflicts remain non-overridable conflicts.

Preset flex records remain keyed by the exact live model control literal rather than a cross-character canonical semantic ID.

## Review

**Production rule:** Review is available only for genuine current healthy-authority misses.

User decisions are:

- Body;
- Expression; or
- Exclude from Presets.

A previously reviewed choice may be reclassified.

**Production rule:** If a later healthy authority generation positively resolves a previously missing literal, that authority result supersedes the local miss-only choice.

## Storage and migration

Current storage root:

```text
Documents\SFM Character Preset Manager\
```

Historical root:

```text
Documents\SFM Character Preset Tool\
```

**Production rule:** If the new root is absent and the historical root exists, migration may rename/move and verify the library.

**Production rule:** If both roots already exist, the Manager does not silently merge them.

The primary current schema is v3. Readable legacy-v2 support remains intentionally because it protects existing user libraries.

## Flex persistence

Flex mutation keys are literal-based:

```text
flex.<exact literal>
```

MONO and STEREO representations are stored explicitly rather than inferred at Apply time.

**Production rule:** Apply requires the saved accepted flex mutation-key set to equal the current accepted semantic flex mutation-key set.

**Production rule:** The Manager does not silently partially apply an old preset whose accepted semantic set changed.

## Generic bone scaling

Generic bone scaling is required Body Preset functionality.

Current policy identifier:

```text
complete-native-bone-map-physical-uniform-v1
```

Saved bone identity includes:

- bone index;
- bone name;
- uniform local physical scale multiplier; and
- capture-state information.

**Observed:** Qualification established writing existing supported scale controls, creation of a missing supported scale graph, a non-default 2.0× case, and persistence after saved-session reopen in the tested fixtures.

**Production rule:** Body capture represents the complete supported bone-scale layout, not only values visibly different from 1.0×.

**Production rule:** Body Apply requires compatible saved bone-layout identity.

**Limitation:** This does not mean every possible model-specific custom scaling system in SFM is supported. The production contract is the qualified generic native scale topology.

## Native mutation contract

Qualified low-level mutation mechanics are treated as frozen unless new runtime evidence contradicts them.

**Production rule:** A mutation follows this order:

1. complete preflight;
2. detect no-op before starting Undo;
3. explicitly start native SFM Undo;
4. perform the planned write or writes;
5. verify required precommit state where applicable;
6. Finish Undo;
7. perform same-time refresh;
8. call/process Qt events as required; and
9. perform independent postcommit/readback verification.

**Production rule:** Failure before a safe commit uses the supported abort path and verifies recovery where the operation contract requires it.

**Limitation:** The current source contains hardened rollback-verification helpers, but deliberately forced rollback-verification failure branches remain a release qualification gate.

## Indexed bone capture

**Observed:** The historical complete-map path spent most Body Save/Update time repeatedly traversing and validating the native scale map.

**Observed:** The later operation-scoped indexed snapshot/projection path matched the historical capture oracle exactly in qualification.

**Observed:** Representative measured indexed capture was roughly 0.03 seconds, with Body Save around 0.09–0.10 seconds and Body Update median around 0.07 seconds in the qualification fixture.

**Production rule:** Do not restore repeated full native-map traversal merely for architectural tidiness.

## Clothing Fit

**Production rule:** Clothing Fit source Body membership comes from the selected model's current semantic scope.

**Production rule:** Actual source-target correspondence is structural/native; the Animation Groups Master is not treated as a cross-character Body Match map.

**Production rule:** Compatibility planning occurs before mutation.

**Production rule:** One changed target receives one native transaction.

**Production rule:** Each target is staged on a separate Qt event turn using zero-delay `QTimer.singleShot(0, ...)` scheduling.

**Production rule:** A no-op target does not create an Undo entry.

**Production rule:** A warning-bearing target that successfully changes is counted as changed rather than falsely reported as already matching.

## Foreign-modal priority

The Manager is a persistent nonmodal palette using `Qt.Dialog | WindowStaysOnTopHint` during normal operation.

**Observed:** SFM-owned modal dialogs can appear while the Manager remains open.

**Production rule:** A Qt-only modal watcher checks `QApplication.activeModalWidget()` and excludes Manager-owned dialog descendants.

When a foreign modal appears, the current policy is:

1. publish scene suspension;
2. hide the Manager;
3. perform no scene-facing work while suspended; and
4. restore with `show()` after the foreign modal closes, without `raise_()` or `activateWindow()`.

**Production rule:** If Clothing Fit was between queued target stages, at most one continuation is parked and resumed after the modal closes.

## Window icon and chrome

**Production rule:** The current icon is embedded in the script, avoiding a separate asset and `__file__` dependency.

**Observed:** `Qt.Tool` did not reliably show the intended title-bar icon in the tested Windows/SFM environment.

**Production rule:** The main palette uses normal `Qt.Dialog` chrome plus `WindowStaysOnTopHint`.

**Production rule:** Final window flags are set before `setWindowIcon()` because changing flags may recreate the native window.

## Logging

**Production rule:** Diagnostic logging must never change product control flow or turn a successful user operation into a failure.

**Limitation:** G18AN still includes substantial development/qualification logging and historical code. Release cleanup should reduce that material without weakening nonthrowing logging safety or reopening frozen mechanics.

## Source bloat and cleanup sequencing

A whole-script static audit found substantial disconnected historical/qualification code in the production lineage.

This is primarily a maintenance/source-size issue, not the historical Body Save performance bottleneck.

The safe cleanup sequence is:

1. settle the final shared-authority contract;
2. remove disconnected historical UI/qualification families;
3. remove or isolate development-only TXT/AUTO/parity/oracle surfaces;
4. reduce diagnostic logging;
5. static-equivalence-check frozen mechanics; and
6. run controlled failure gates followed by exact release regression.

Bulk deletion before the authority seam is settled risks conflating architecture integration with unrelated cleanup.

## Current release gates

At the G18AN baseline, the remaining gates are:

- final shared-authority/package integration;
- controlled source-generation mismatch qualification;
- controlled rollback-verification failure qualification for preset Apply and Clothing Fit;
- whole-program historical/development cleanup;
- exact release-artifact regression; and
- final packaging/documentation.

Until those gates are closed against the exact shipping bytes, G18AN should be described as a development baseline rather than a public 1.0 release.
