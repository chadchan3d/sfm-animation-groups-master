> **Repository context (added by this checkpoint, not part of the original dossier):** this document was supplied externally for Astra's holistic review of the SFM Master / shared-authority system (see `docs/qualification/ASTRA_HOLISTIC_REVIEW_BRIEF.md` for the controlling assignment and `docs/qualification/ASTRA_REPO_INDEX.md` for repository navigation). It documents Character Preset Manager (CPM) as a prospective second consumer. Everything below this line is the exact supplied dossier content, unmodified.

---

# Character Preset Manager — Astra Authority Consumer Dossier

**Purpose:** Technical dossier for Astra's holistic review of Character Preset Manager (CPM) as a prospective second consumer of the shared **Animation Groups Master → sidecar → authority** system.

**Scope:** Documentation only. This dossier does not modify CPM, redesign its feature model, integrate a new authority implementation, or propose a broker API.

---

## 1. Exact current CPM identity

### Current candidate

| Item | Identity |
|---|---|
| Current source | `SFM_CSP_G18AN_SaveNewCopy.py` |
| Source SHA-256 | `3326024ddecd544ad1e10659bbf7b98420b5f147fca775433878c19fd9e66b3e` |
| Source size | 846,628 bytes / 34,898 lines |
| Static checkpoint | `SFM_CSP_G18AN_SaveNewCopy_StaticCheckpoint_2026-09-16.md` |
| Static-checkpoint SHA-256 | `f62f8ef0aedd229496fd0610cd5eaa7d7b15efa5bc65c42ac61d9904d39cdaa4` |
| Cumulative ledger | `SFM_CSP_RefactorLedger_2026-09-16_v196.md` |
| Ledger SHA-256 | `043eeb5dd6b8872829286822cfc725bf5dd05c794bebb609b93654bd84e3a213` |
| Static refinement audit | `SFM_CSP_StaticRefinementAudit_G18AG_2026-09-15.md` |
| Audit SHA-256 | `155bc2c7e946eee589dafe19818d992d3e5bdf15737552ed3cb8e815833a3bf6` |
| Astra holistic-audit disposition | `SFM_CSP_Astra_HolisticAudit_Disposition_2026-09-15.md` |
| Disposition SHA-256 | `582e51b565006b0e5ee78093647877e70f84ce5d98b794513a495c0a6a874690` |

G18AN itself is a copy-only UI refinement over the qualified production lineage: it reverted an ineffective button-stretch change and renamed the Body/Expression save buttons to `Save New`. It did not change semantic, persistence, matching, scale, or mutation behavior.

### Runtime environment assumptions

- Source Filmmaker MAINMENU script.
- Embedded Python **2.7.5, 32-bit**.
- PySide **1.2**, Qt **4.8.x**.
- `__file__` is not assumed to exist in MAINMENU execution.
- Working directory may be the SFM `game` directory and is not used as semantic identity.
- Main CPM palette is a nonmodal `Qt.Dialog | Qt.WindowStaysOnTopHint`.
- G18AH adds a Qt-only foreign-modal watcher so native SFM dialogs take priority over CPM.
- Native DME objects are treated as operation-local/runtime objects. Long-lived semantic scopes are deliberately pure Python data.

### Current qualified stage

The following major mechanics are considered working/qualified in the current lineage:

- selected-model resolution using normalized model path + checksum as durable identity; Animation Set name is mutable display/runtime metadata;
- v3 preset/character storage with readable legacy v2 support;
- Body Preset Save, Update, Apply, no-op behavior, generic complete bone-scale capture/apply, native Undo/Redo, and saved-session persistence;
- Expression Save, Update, Apply, no-op behavior, and Undo;
- generic bone scaling under policy `complete-native-bone-map-physical-uniform-v1`;
- Clothing Fit source capture, structural mapping, per-target queued mutation, partial-result reporting, and normal success/no-op behavior;
- Review handling for genuine semantic misses, including Body / Expression / Exclude decisions and Reclassify;
- sidecar semantic parity and a production-style resident SIDECAR provider path;
- modal-yield behavior;
- Animation Set rename resilience;
- postcommit/readback failure semantics and rollback-hardening helpers in source.

Still pending before release:

- integration against the **final** shared authority/package/builder contract;
- controlled source-generation mismatch/fail-closed qualification against that final contract;
- controlled runtime qualification of rollback-verification failure branches for Body/Expression Apply and Clothing Fit;
- whole-program cleanup/refinement after authority behavior is frozen;
- final exact-artifact integrated regression and release packaging/documentation.

The current source still contains historical TXT/AUTO provider and qualification machinery. Current production selection is forced to SIDECAR at `SFM_CSP_G18AN_SaveNewCopy.py:1125-1128`.

---

## 2. Authority-consumption map

The table below distinguishes current production paths from historical/qualification paths that remain in the large development source.

| Feature | File | Function | Approx. lines | Input | Output | Why semantic authority matters |
|---|---|---|---:|---|---|---|
| Provider adapter | `SFM_CSP_G18AN_SaveNewCopy.py` | `SidecarSemanticProvider` | 2298-2639 | live literal queries + verified Master/sidecar identity | detached semantic answers | Converts sidecar results into CPM states: resolved, absent, conflict, plus destination paths and diagnostics. |
| Provider lifetime | same | `get_semantic_provider` | 3339-3388 | forced provider mode | resident provider singleton | Reuses one verified semantic provider across model selections/operations. |
| Provider invalidation | same | `invalidate_semantic_provider` | 3391-3427 | current singleton | closes/clears provider, advances usable generation state | Defines how cached scopes become stale if authority is explicitly replaced. |
| Face classification | same | `p01_is_face_path` | 3455-3459 | resolved semantic path | Boolean | Current Expression membership is determined by a path whose first segment is `Face`. |
| Body classification | same | `semantic_is_body_morph_path` | 3763-3766 | resolved semantic path | Boolean | Current Body membership requires the semantic path to be `Body Morphs`. |
| Semantic classification | same | `semantic_snapshot_from_live_vocabulary` | 3769-3862 | live flex bindings + batched authority answers | semantic rows, Body set, Expression set, counts | Primary conversion from authority answers into CPM operational categories. |
| Model semantic snapshot | same | `semantic_snapshot_for_model_row` | 3885-3923 | selected live model row + provider | pure semantic snapshot | Enumerates supported live flexes, batches literal queries, and produces model-local semantic facts. |
| Long-lived semantic scope | same | `prod_scope` | 20136-20381 | selected identity + provider + local Review overrides | pure Body/Expression/unresolved/conflict scope | Central current production semantic view used by Body Presets, Expressions, Review, and Clothing Fit. |
| Cached-scope validation | same | `prod_scope_matches_identity` | 19527-19641 | cached scope + current identity/provider/profile | Boolean | Rejects stale scope when model/provider/policy/Review revision differs. |
| Fresh live binding resolution | same | `prod_live_bindings_for_cached_scope` | 19644-19778 | cached semantic scope + current scene | fresh live DME bindings | Reuses semantic membership without retaining DME objects; rejects vocabulary/representation drift. |
| Body Preset capture | same | `prod_capture_body_snapshot` | 26032-26122 | current Body scope/live bindings | Body flex values + complete bone-scale map | Authority determines which flex literals constitute the Body portion; bone-scale capture itself is authority-independent. |
| Body/Expression Save | same | `prod_save` | 26233-26549 | current scope + live bindings + kind | v3 preset record | Uses authority-derived Body or Expression membership to decide exactly which flex values are saved. |
| Body/Expression Update | same | `prod_update_preset` | 26554-26894 | current scope + existing preset + kind | rewritten preset record | Same semantic membership requirement as Save; exact current set becomes new saved set. |
| Body/Expression Apply | same | `prod_apply` | 27257-27730 | preset + cached scope + fresh live bindings | mutation plan/result | Requires the saved flex key set to exactly equal the currently accepted authority-derived set before mutation. |
| Review override write | same | `prod_set_override` | 20384-20508 | current model + literal + Body/Expression/Exclude decision | updated character profile | A local choice is allowed only for a genuine current Master miss. |
| Review override clear | same | `prod_clear_override` | 20512-20650 | model + literal | updated profile | Removes user classification so authority/current miss state governs again. |
| Review UI population | same | `ProdWindow.apply_scope_to_ui` | 30974-31157 | current pure scope | Needs Review / Reviewed choices / conflicts UI | Authority status determines whether a row is actionable, resolved, conflicted, or unavailable. |
| Review model change | same | `ProdWindow.review_changed` | 31707-31758 | tree selection/current scope | UI state | Reads semantic status and current local choice. |
| Reclassify Flex | same | `ProdWindow.review_reclassify` | 31761-31852 | selected reviewed literal | revised local override + rebuilt scope | Reclassification remains constrained to literals that are genuine Master misses. |
| Body / Expression / Exclude | same | `ProdWindow.review_decision` | 31855-31934 | selected miss + decision | persisted override + rebuilt scope | Authority decides whether the control is eligible for local classification at all. |
| Clothing Fit source Body set | same | `prod_body_source` | 27733-27805 | selected source model/scope | pure source-body baseline | Authority defines which source flexes are Body controls. |
| Clothing Fit fresh source | same | `prod_body_source_live_from_baseline` | 27809-27878 | source baseline + current scene | fresh source values | Verifies cached semantic membership still maps to the same current live representation. |
| Clothing Fit structural mapping | same | `g11a_safe_plan` | 16284-16471 | source/target live flex structures | safe mapping plan | Mapping itself is structural/native, not semantic-authority-based; semantic facts are used around it for relevance/warnings. |
| Clothing Fit mapping core | same | `p03_build_mapping` | 6906-7018 | source/target bindings | source-target mapping | Uses structural `global_key` and native controller compatibility, not Master canonical IDs. |
| Clothing Fit warning relevance | same | `p03_unmapped_relevant_controls` | 7225-7323 | unmapped target controls + semantic answers | warning/relevance set | Authority identifies semantically relevant target controls such as `Body Morphs` / `Clothing` that failed mapping. |
| Generic bone scaling | same | `prod_bs_index_snapshot`; `prod_bs_index_capture_map`; `prod_bs_index_build_plan` | 23869-24249; 25656-25950; 25024-25158 | native model bone topology/scale channels | complete physical scale map/plan | **No semantic-authority dependency.** Bone identity and scale topology are derived from SFM/native model data. |
| Head Scale adapter | same | `resolve_qualified_head_scale`; `prod_capture_scale`; `write_head_scale` | 9256-9442; 21471-21541; 9578-9600 | model-specific `bip_head` scale topology | historical `scale_multiplier` state | **No semantic-authority dependency.** Historical/special adapter; current complete generic bone map supersedes standalone production use. |
| Historical Body Match concept / current Clothing Fit | same | `g11a_safe_plan`, `p03_build_mapping`, current `prod_apply_match` | 16284-16471; 6906-7018; 27906-28051 | source/target bindings | operation-local mapping/mutation | Current source does **not** use Master identity as a cross-character mapping key. Authority selects relevant Body membership; actual correspondence remains CPM-owned structural mapping. |

### Important current distinction

CPM does **not** currently ask the Master for a canonical cross-character control ID and then use that ID to mutate another model. Its main semantic question is closer to:

> For this exact live flex literal, what semantic destination/path does the current authority assign, or is it absent/conflicted?

The current Body/Expression partition is then derived from that answer.

Left/right information is also not a Master query. `resolve_side` (`514-599`) and `flex_binding` (`602-668`) derive MONO/STEREO and left/right channels from live SFM DME structure.

---

## 3. Semantic queries CPM actually needs

This section describes the minimum information required by current behavior. It does not prescribe an authority API.

### Body Presets

Current operational need:

1. For every supported live flex literal on the selected model, determine whether semantic authority resolves it.
2. If resolved, identify its semantic path sufficiently to determine whether it belongs to `Body Morphs`.
3. Distinguish a genuine authority miss from a conflict or unavailable authority.
4. Preserve exact live literal identity so saved values can be keyed back to the same live control set.

Minimum semantic information:

- query literal;
- resolution state: resolved / absent / conflict;
- resolved destination path when uniquely resolved;
- enough conflict information to avoid treating conflict as a user-resolvable miss.

Not required for Body Preset mutation:

- canonical cross-model semantic ID;
- sibling order;
- presentation order;
- bone metadata;
- mutation order.

### Expressions

Same lookup shape as Body Presets, but operational classification is currently:

- resolved path whose first segment is `Face` → Expression;
- other resolved paths → not Expression;
- absent → Review candidate;
- conflict → not user-classifiable;
- authority unavailable → semantic operations disabled.

Minimum semantic information is therefore the same literal → status + path result.

### Generic bone scaling

No Master/sidecar semantic query is required.

CPM discovers complete native bone topology and physical scale state directly from the model/DME graph. Bone-scale persistence is keyed by native bone index and name.

### Head Scale

The historical Krystal2020 `bip_head` Head Scale adapter requires no semantic authority. It is model/topology-specific logic downstream of model resolution.

### Body Match / current Clothing Fit

Authority is required only for semantic **membership/relevance**, not correspondence:

- determine the source model's Body controls;
- identify unmapped target controls that are semantically relevant enough to warn about, including current `Body Morphs` / `Clothing` uses.

Current source-target correspondence uses structural live data (`global_key`, native flex controller name/type/range compatibility), not Master canonical IDs.

### Review / Needs Review

Review requires a strict distinction among:

- resolved positive authority result;
- genuine Master miss;
- Master conflict;
- authority unavailable.

Only a genuine miss may receive a local user decision.

Minimum semantic information:

- exact queried literal;
- status;
- resolved path if resolved;
- conflict destinations if conflicted.

Spellings, occurrence count, and exact-vs-folded match information are useful diagnostics but are not the core eligibility decision.

### Body / Expression / Exclude classifications

These are **CPM-owned local decisions**, not authored Master classifications.

They apply only when current authority reports a genuine miss for that literal. If a later authority generation positively resolves the same literal, the local override is ignored by current `prod_scope`.

Authority therefore needs to answer whether the literal is still a miss; it does not need to store the user's local decision.

### Reclassify Flex

Same authority dependency as Review. Reclassify changes CPM's model-local metadata and then rebuilds semantic scope. The authority remains authoritative over positive matches/conflicts.

### Corresponding left/right control

Current CPM does not need semantic authority for this. It derives stereo/side structure from native SFM bindings.

### “Does this semantic control exist on the current character?”

Current implementation does not ask authority this as a standalone global query. CPM first enumerates the **live character vocabulary**, then queries authority for those literals. Existence on the current character is therefore a live-model fact combined with semantic classification.

### Hierarchy depth actually consumed

Current production behavior consumes only limited hierarchy/category facts:

- `Face` as a root/category test for Expression membership;
- exact `Body Morphs` membership for Body classification;
- `Clothing` / Body relevance in Clothing Fit warning logic.

CPM does not presently consume the full Master hierarchy as a presentation tree.

---

## 4. Current internal data structures

### 4.1 Live flex binding descriptor

Long-lived semantic scope stores a **pure descriptor**, not the live DME object:

```python
{
    "literal": "voluptuous",
    "shape": "MONO",             # or "STEREO"
    "global_key": ("MONO", 42)   # representative shape
}
```

For stereo controls the structural key contains both native global indexes.

Live DME bindings are re-enumerated per operation and checked against these descriptors.

### 4.2 Pure semantic scope

Representative current shape produced by `prod_scope`:

```python
{
    "schema": "csp-semantic-scope-pure-v1",
    "identity": {...},
    "authority": {
        "provider_generation": 1,
        "provider_sha256": "<Master/source SHA>",
        "semantic_policy_revision": "master-category-operation-scope-v1",
        "override_revision": 0
    },
    "provider_descriptor": {...},
    "live_signature": {
        "vocabulary_sha256": "...",
        "representation_sha256": "..."
    },
    "semantic": {
        "rows": [...],
        "counts": {...}
    },
    "expression": {
        "SomeFaceFlex": {
            "literal": "SomeFaceFlex",
            "shape": "MONO",
            "global_key": ("MONO", 123)
        }
    },
    "body": {
        "SomeBodyFlex": {
            "literal": "SomeBodyFlex",
            "shape": "STEREO",
            "global_key": ("STEREO", 45, 46)
        }
    },
    "unresolved": [...],
    "conflicts": [...],
    "overrides": {
        "SomeLiteral": "body"
    },
    "excluded": [...]
}
```

`prod_scope_pure_assert` (`19167-19255`) explicitly protects the boundary: cached semantic state must not retain Qt, DME, or native runtime objects.

### 4.3 Character/library identity

`g09a_normalize_model_path` (`15665-15669`) normalizes the model path.

`g09a_library_key` (`15672-15676`) creates a path-based library key:

```text
modelpath-sha256-v1:<sha256(normalized-model-path)>
```

Current durable runtime model identity uses:

- normalized model path;
- model checksum.

Animation Set name is mutable display/runtime metadata and is not treated as durable model identity.

### 4.4 Character profile / Review metadata

Representative v3 character record from `prod_character_record` (`20065-20102`):

```python
{
    "schema_version": 3,
    "record_kind": "character",
    "library_key": "...",
    "identity_policy": "normalized-model-path-sha256-v1",
    "display_name": "<current animation-set name>",
    "model_ref": {
        "path": "<normalized model path>",
        "last_validated_checksum": 123456789
    },
    "default_body_preset_id": None,
    "semantic_overrides": {},
    "semantic_override_revision": 0,
    "structural_capabilities": {},
    "created_at": "...",
    "updated_at": "...",
    "semantic_policy": "master-category-operation-scope-v1",
    "last_validated_provider": {...}
}
```

Representative local Review decision:

```python
"semantic_overrides": {
    "SomeLiteral": {
        "source": "user",
        "applies_when": "master-miss",
        "decision": "body",      # or "expression" / "exclude"
        "created_at": "..."
    }
}
```

These are model-library metadata. They are not Master data and are not part of SFM Undo.

### 4.5 Body / Expression flex value records

`p02_saved_value_record` (`4603-4661`) and `p03_capture_values` (`5715-5741`) produce literal-keyed records.

MONO example:

```python
"flex.voluptuous": {
    "representation": "MONO",
    "mono": 0.72
}
```

STEREO example:

```python
"flex.UpperLid": {
    "representation": "STEREO",
    "left": 0.20,
    "right": 0.35
}
```

The persisted key is the **model control literal**, prefixed with `flex.`. CPM does not currently persist a separate canonical semantic-control identifier for that value.

### 4.6 v3 preset record

Representative record created by `prod_save`:

```python
{
    "schema_version": 3,
    "record_kind": "preset",
    "preset_id": "preset-...",
    "character_key": "<model-path library key>",
    "kind": "body",              # or "expression"
    "name": "Example",
    "model_ref": {
        "path": "<normalized model path>",
        "capture_checksum": 123456789
    },
    "capture_semantic_policy": "master-category-operation-scope-v1",
    "capture_provider": {
        "provider_contract": "...",
        "source_sha256": "...",
        "fold_policy": "...",
        "provider_generation": 1
    },
    "created_at": "...",
    "values": {
        "flex.SomeLiteral": {
            "representation": "MONO",
            "mono": 0.5
        }
    }
}
```

Body presets additionally carry the complete bone-scale map and bone-scale policy.

### 4.7 Generic bone-scale record

Representative current entry:

```python
{
    "bone_index": 17,
    "bone_name": "bip_head",
    "representation": "uniform_local_scale_multiplier",
    "value": 1.25,
    "capture_state": "existing-static-control"
}
```

`capture_state` may also describe an implicit-neutral state where no authored scale graph existed at capture time.

Complete-map identity is native:

```text
(bone_index, lowercased bone_name)
```

This is model-specific structural data, not semantic Master data.

### 4.8 Historical Head Scale representation

Historical/special logic used the logical identifier:

```text
body.scale.head
```

and a representation conceptually equivalent to:

```python
{
    "representation": "scale_multiplier",
    "value": 1.25
}
```

Current production Body Presets use the complete generic bone map instead. `prod_capture_scale()` has no current production caller, and `prod_apply` explicitly rejects old standalone `body.scale.head` test data.

### 4.9 Body Match / Clothing Fit mappings

Current Clothing Fit mappings are operation-local plans, not persistent per-character semantic maps.

They are computed from live source/target structural bindings. The important matching identity is the native structural `global_key` plus compatibility checks. No current persistent per-character Body Match mapping record was found in G18AN.

---

## 5. Persistence and compatibility

### What identifies a control inside a saved preset?

Flex values are stored by:

```text
flex.<exact model control literal>
```

The saved value record separately states MONO/STEREO representation and scalar value(s).

Thus current persistence is model-literal-based. It does **not** save a canonical semantic ID and later ask authority to translate that ID back onto the model.

Bone scales are identified separately by native bone index + bone name.

### What is semantic versus model-specific?

Semantic:

- whether a live literal belongs to Body or Expression;
- whether authority resolves it, misses it, or conflicts;
- semantic destination path used for classification.

Model-specific:

- exact flex literal persisted in the preset;
- MONO/STEREO representation;
- native global indexes used to validate a current live binding;
- model path/checksum;
- bone index/name and scale topology;
- local Review decisions.

### Current preset compatibility

`prod_validate_preset` (`20676-20914`) validates record/schema/library/model/value structure.

At Apply, `prod_apply` (`27257-27730`) obtains the current accepted live Body or Expression set from the selected model's semantic scope and requires:

```text
saved flex mutation-key set == current accepted flex mutation-key set
```

If the set differs, Apply is refused rather than partially applying.

The current UI condition represented by:

> `preset no longer matches Body controls...`

is therefore produced when the old saved preset's flex set no longer exactly matches the currently accepted Body set. This can happen because:

- the model's live flex vocabulary changed;
- a flex representation changed;
- Review choices changed;
- semantic authority now classifies the vocabulary differently.

Body Presets additionally validate the complete current bone-layout key set. A changed bone layout causes a separate fail-closed incompatibility.

### Could shared authority invalidate old presets?

Yes, indirectly.

Changing the classification mechanism does not make the v3 JSON unreadable, but if the new authority produces a different accepted Body/Expression membership set for the same model vocabulary, current exact-set Apply compatibility will reject an older preset.

Therefore the stability requirement is not “same provider implementation.” The practical compatibility-sensitive behavior is:

- same model/library identity rules;
- same persisted flex literal/value representation;
- semantically equivalent Body/Expression membership for those live literals, unless intentional incompatibility is accepted;
- same complete bone-layout policy for Body Presets.

### Does a preset currently depend on Master/sidecar generation?

A preset records:

- `capture_semantic_policy`;
- `capture_provider.source_sha256`;
- `capture_provider.fold_policy`;
- `capture_provider.provider_generation`.

In current G18AN, those fields are provenance/diagnostic capture data. Current Apply logic does **not** require the capture provider generation or source SHA to equal the active generation.

There is therefore no current implementation requirement that an old preset be tied permanently to the authority generation under which it was saved.

### Model/model-version changes

- Library identity is based on normalized model path.
- Current runtime resolution also uses checksum to validate the selected live model.
- Animation Set name may change and is refreshed as mutable metadata.
- Model disappearance or unresolved duplicate ambiguity fails closed.
- Model vocabulary or representation drift invalidates the cached semantic scope and/or causes preset exact-set incompatibility.
- Bone layout drift invalidates a Body Preset's complete bone-scale map.

---

## 6. Lifetime model

CPM is a long-lived interactive consumer. Its authority usage differs from a one-shot normalization pass.

### Window open

`StartProdTool` (`34871-34895`) constructs/opens the production window.

The window can remain open while the user:

- changes selected characters;
- saves multiple presets;
- updates presets;
- applies presets repeatedly;
- uses Review;
- performs multi-target Clothing Fit operations.

### Provider lifetime

`get_semantic_provider` holds a process-global `_SEMANTIC_PROVIDER`.

Current behavior:

- first semantic need opens/verifies the provider;
- subsequent calls reuse the same provider;
- provider has a generation identity;
- closing the CPM window does **not** automatically invalidate that provider;
- explicit `invalidate_semantic_provider` closes it.

The sidecar adapter returns detached Python results so packed/internal provider IDs do not escape into CPM state.

### Selected-character lifetime

`ProdWindow.render` (`30503-30838`) assembles a new character context before publishing it.

For a healthy selection it builds one `prod_scope`, loads preset-library metadata, then publishes:

- `self.identity`;
- `self.scope`;
- Body/Expression preset items;
- Review state;
- library metadata;
- Clothing Fit candidate state.

If publication fails, prior window state is restored rather than leaving a half-switched character context.

### Semantic scope lifetime

A selected character's semantic classification is retained as one pure scope and reused across multiple operations.

Ordinary:

- Save;
- Update;
- Apply;
- Preset Info/library refresh;
- Clothing Fit source use

do not rebuild the entire semantic scope each time.

Instead, scene-facing operations call `prod_live_bindings_for_cached_scope`, which:

1. re-enumerates current live supported flex bindings;
2. recomputes vocabulary/representation signatures;
3. verifies the cached semantic membership still describes the same live controls;
4. returns fresh DME bindings for the operation.

This is intentional separation between long-lived semantic facts and short-lived native objects.

### Character change

Selecting another model creates a new model-local semantic scope. Warm provider reuse means the authority source itself need not be reopened for each selection.

G18AI additionally treats Animation Set name as mutable. A uniquely resolvable rename refreshes display/runtime metadata rather than changing durable model identity.

### Review lifecycle

A Review classification change is one of the cases that deliberately invalidates semantic scope:

1. clear current `self.scope`;
2. persist the user override/reclassification;
3. rebuild one fresh scope;
4. republish UI state.

This is required because Body/Expression membership may change.

### Body Match / Clothing Fit pair lifetime

Current production Clothing Fit does not keep a persistent per-character pair mapping database.

At operation start it captures a pure source baseline. Each queued target stage re-resolves the source against current scene state and computes/uses operation-local target mapping.

If source context becomes stale during the queued operation, the fit operation stops rather than continuing against an unverified source.

### Save → Update → Apply

Within one selected-character session:

- Save and Update reuse the selected character's semantic scope but resolve current live bindings fresh.
- Apply similarly reuses semantic membership and resolves the current live DME controls fresh before preflight/mutation.
- No long-lived DME controls are required merely because the window stays open.

### Library refresh

`ProdWindow.reload_library_cache` (`31626-31686`) refreshes preset/library UI state without rebuilding semantic scope or traversing the scene.

### Model disappearance/change

When current live vocabulary/representation no longer matches the cached scope, CPM fails the operation and requires model reselection/resynchronization rather than silently reclassifying mid-operation.

### Authority files changing while the window remains open

Current CPM has no external Master/sidecar file watcher.

The resident provider and selected model scope therefore remain tied to the generation currently opened in the process until explicit invalidation/reopen/restart behavior occurs.

How a future shared authority should handle an external generation change during a long-lived CPM session is an open architectural question for Astra.

---

## 7. Performance evidence

### Historical baseline: before indexed Body capture

The often-cited ~3.7 second Body Save/Update numbers describe the **older pre-indexed capture path**, not current G18AN performance.

Historical PERF-01 approximately measured:

| Operation | Historical time |
|---|---:|
| Body Save | ~3.72 s |
| Body Update | ~3.77 s |
| Body Apply | ~0.132 s |
| Expression Save/Update | ~0.021-0.034 s |

A detailed historical Body Save around ~3.510 s decomposed approximately as:

| Work | Time |
|---|---:|
| complete bone-scale capture | ~1.130 s |
| prewrite bone-layout validation | ~1.170 s |
| readback bone-layout validation | ~1.164 s |
| disk inventory | ~0.011 s |
| live flex binding work | ~0.007 s |
| flex value capture | ~0.001 s |
| library ensure | ~0.012 s |
| JSON write | ~0.009 s |

Thus approximately **99% of the historical ~3.7 s path was repeated complete native bone-layout/scale work**, not semantic Master classification or serialization.

Historical repeated Body Save/Update also correlated with roughly **+27-29 MiB** settled private-commit growth.

### Current indexed Body path

Q1/Q2 replaced those repeated full traversals with operation-scoped indexed bone capture/validation.

Measured evidence:

- indexed capture ~**0.029 s** versus historical oracle ~**1.189 s**, with exact parity;
- Body Save ~**0.090 s** production / ~**0.103 s** post-confirm;
- Body Update median ~**0.068 s** across representative samples;
- indexed capture median ~**0.033 s**;
- settled private commit roughly +**1.75 MiB** on Save, with five Updates totaling roughly +**0.344 MiB**;
- historical ~27-29 MiB growth slope was not present.

Therefore the historical ~3.7 s Body bottleneck should not be attributed to authority lookup and should not be used as justification for an authority redesign.

### Semantic authority timing

Older full-Master TXT work established approximately:

- full cold semantic work: ~**1.524 s**;
- warm: ~**0.040 s**.

Production-style sidecar qualification later measured approximately:

- cold Krystal selection: ~**1.453 s** total;
- warm Nika selection: ~**0.053 s**;
- warm Krystal revisit: ~**0.063 s**.

Representative cold decomposition included:

- active Master identity work ~0.047 s;
- verified path work ~0.099 s;
- provider import ~0.001 s;
- bounded sidecar open ~1.276 s;
- semantic-scope work ~1.396 s total;
- remaining Manager work only tens of milliseconds.

Runtime evidence showed:

- one resident provider open;
- zero production TXT parses;
- warm model changes do not repeat the cold provider-open cost.

Diagnostic memory evidence placed cold sidecar private-commit delta around +13 MiB versus roughly +62 MiB in an older full-TXT run. This was not a formal matched benchmark and should remain diagnostic evidence only.

### What could theoretically be shared/indexed?

Already current:

- semantic provider is retained and reused;
- selected-model semantic classification is cached as a pure scope;
- live DME bindings are re-resolved instead of retaining native objects;
- generic bone capture is indexed per operation.

No current evidence shows a second multi-second CPM-side classification bottleneck after the resident sidecar provider is warm.

---

## 8. Failure semantics

### Authority cannot be obtained

Current production behavior is fail-closed.

`prod_probe_semantic_provider` (`18612-18650`) and `ProdWindow.apply_provider_unavailable_to_ui` (`29576-29636`) treat missing/stale/invalid sidecar authority as a provider-health failure.

Result:

- `self.scope` is unavailable;
- Review is cleared/not offered as if everything were unknown;
- semantic scene actions are disabled, including Body Presets, Expressions, and Clothing Fit;
- ordinary library/nonsemantic actions remain available where safe;
- user receives a sidecar missing/out-of-date/rebuild message.

Critically:

> Missing authority is **not** converted into `MasterUnknown`.

### Unknown live controls

If authority is healthy and a literal genuinely has no Master result:

```text
MasterUnknown → CPM ABSENT → master-miss
```

That literal becomes a candidate for Needs Review.

Other known controls continue to function.

### Semantic conflict

A conflict becomes `master-conflict`.

It is visible diagnostically but is not treated as a user-classifiable missing flex. Local Body/Expression/Exclude decisions cannot override a positive/conflicted Master result.

### Saved preset contains absent current controls

Body/Expression Apply requires exact equality between saved flex keys and the current accepted semantic set.

Missing/added/reclassified controls therefore cause the preset to be refused. CPM does not partially apply whichever flexes happen to remain.

### Bone disappears/changes

Complete generic bone-scale validation requires the current bone key set to match the saved Body Preset's expected key set. A mismatch refuses Body Apply rather than guessing.

### Body Match / Clothing Fit mapping invalid

Current Clothing Fit distinguishes expected mapping limitations from uncertain mutation state.

Examples of nonfatal planning skips can include:

- unsupported target FLEX shape;
- no compatible mapping;
- target ambiguity;
- semantically relevant unmapped controls.

Actual native mutation uncertainty is handled more conservatively: the queued process stops, reports a partial/uncertain result as appropriate, and rollback verification helpers exist for precommit failures.

### User changes characters while window remains open

A model change rebuilds the model-local context. Cached scope is not blindly reused for a different identity.

Animation Set rename is handled as mutable metadata when path+checksum uniquely resolve the same model. True identity ambiguity or disappearance fails closed.

### Cached classification becomes stale

`prod_scope_matches_identity` requires current:

- model identity;
- provider generation;
- provider/source SHA;
- semantic policy revision;
- Review override revision/digest.

`prod_live_bindings_for_cached_scope` independently verifies live vocabulary and representation signatures.

A mismatch does not become empty data or “Unknown”; the operation fails and instructs the user to reselect/resynchronize.

### Classification/parsing exception

Provider/open/classification failure becomes authority unavailable/degraded rather than a false semantic miss.

`ProdWindow.guard` (`29710-29872`) separately distinguishes operation failure phases such as precommit, native committed, and durable persisted state so scene/persistence errors are not mislabeled.

### Current fail-open / fail-closed summary

| Condition | Current treatment |
|---|---|
| Provider missing/corrupt/mismatched | **Fail closed**; semantic actions disabled |
| Healthy authority says literal absent | `MasterUnknown` / Needs Review candidate |
| Healthy authority says conflict | conflict; no local override |
| One unknown literal among otherwise valid literals | known literals remain usable; miss enters Review |
| Cached scope generation/policy/profile stale | **Fail closed** for operation |
| Live vocabulary/representation drift | **Fail closed**; reselect model |
| Saved Body/Expression control-set mismatch | **Fail closed**; no partial preset Apply |
| Saved Body bone-layout mismatch | **Fail closed** |
| Expected Clothing Fit unmappable target | skip/report according to Fit plan semantics |
| Native mutation uncertainty | stop/report; rollback verification where applicable |

---

## 9. Separate authority from mutation

Current CPM can be described in three conceptual layers without changing its architecture.

### Layer 1 — semantic discovery/classification

Primary current entry points:

- `SidecarSemanticProvider` — `2298-2639`
- `get_semantic_provider` — `3339-3388`
- `semantic_snapshot_from_live_vocabulary` — `3769-3862`
- `semantic_snapshot_for_model_row` — `3885-3923`
- `prod_scope` — `20136-20381`
- `prod_set_override` / `prod_clear_override` — `20384-20650`

Responsibilities:

- resolve live control literals through authority;
- classify Body vs Expression vs Other;
- preserve miss/conflict/unavailable distinctions;
- layer model-local Review decisions over genuine misses;
- publish one pure semantic scope.

No scene mutation belongs here.

### Layer 2 — preset computation / matching

Representative entry points:

- `prod_live_bindings_for_cached_scope` — `19644-19778`
- `p03_capture_values` — `5715-5741`
- `prod_capture_body_snapshot` — `26032-26122`
- `prod_validate_preset` — `20676-20914`
- `prod_bs_index_capture_map` — `25656-25950`
- `prod_bs_index_build_plan` — `25024-25158`
- `prod_body_source` / `prod_body_source_live_from_baseline` — `27733-27878`
- `g11a_safe_plan` / `p03_build_mapping` — `16284-16471`, `6906-7018`

Responsibilities:

- convert semantic membership into a current model-specific set of live controls;
- capture values;
- validate exact preset membership;
- compute complete bone-scale plans;
- compute Clothing Fit source/target structural mappings;
- produce mutation-ready pure/preflight data.

Authority informs classification here indirectly through the semantic scope; it does not perform mutation.

### Layer 3 — actual SFM mutation

Representative entry points:

- `write_side` — frozen low-level flex write mechanic;
- `prod_bs_create_graph` — generic bone-scale graph creation;
- `prod_bs_write_existing_scale` — existing scale-channel mutation;
- `prod_apply` — `27257-27730`;
- `prod_apply_match` — `27906-28051`;
- Clothing Fit staged driver `ProdWindow.fit_stage` — `33182-33571`.

Qualified native transaction contract:

1. preflight;
2. explicit native Undo;
3. write;
4. precommit verification;
5. Finish Undo;
6. same-time refresh;
7. `ProcessEvents`;
8. independent postcommit/readback verification.

On a precommit exception, current hardened paths use Abort plus rollback verification. No-op operations occur before starting Undo.

From current-source behavior, semantic authority belongs conceptually in **Layer 1**. This statement identifies the existing separation; it is not an integration/API recommendation.

---

## 10. Model-specific adapters

The following behavior is CPM-owned and should not be mistaken for generic Master/sidecar responsibility merely because it coexists with semantic classification.

### Krystal2020 `bip_head` Head Scale adapter

Relevant historical/qualified functions:

- `resolve_qualified_head_scale` — `9256-9442`
- `scale_snapshot` — `9451-9486`
- `write_head_scale` — `9578-9600`
- `prod_capture_scale` — `21471-21541`

This adapter understands a specific native bone/scale representation and previously exposed a `scale_multiplier` concept.

It does not rely on semantic Master classification. Current production complete generic bone-scale capture supersedes standalone Head Scale persistence.

### Generic bone-scale rules

Current complete bone-scale capture/planning is entirely CPM-owned native model logic.

It determines:

- native bone inventory;
- existing scale control topology;
- implicit neutral scale;
- physical multiplier;
- missing-scale graph creation;
- complete-map compatibility.

No semantic sidecar information is required.

### Clothing Fit structural correspondence

Current Fit mapping is CPM-owned:

- source Body membership is authority-informed;
- actual source-target pairing is structural/native;
- compatibility checks use controller identity/type/range;
- one target is mutated per Qt event turn.

The sidecar is not currently the mapping database.

### Local Review classifications

Body / Expression / Exclude decisions are CPM-owned per-character user metadata.

Authority controls when a local choice is eligible (`master-miss` only), but the local choice itself should not be confused with Master content.

### Model identity / Animation Set rename handling

Normalized model path, checksum, Animation Set enumeration, ambiguity handling, and rename metadata refresh are CPM runtime/model-management responsibilities, not semantic authority.

### Persistent per-character Body Match mappings

No current persistent pair-mapping record was found in G18AN. Older project language referring to per-character Body Match mappings should not be assumed to describe current production behavior. Current Clothing Fit recomputes mapping operation-locally.

---

## 11. What CPM does NOT need

Based on current production behavior, CPM does not appear to require the complete Normalizer-facing semantic/presentation surface.

It does **not** currently require semantic authority to provide:

- full presentation hierarchy retained as a decoded graph;
- sibling ordering;
- presentation/display ordering;
- UI descriptions;
- mutation ordering;
- DME/native object references;
- model-instance or Animation Set identity;
- bone topology or scale metadata;
- Head Scale rules;
- generic scale graph construction rules;
- preset-library schema knowledge;
- Undo/transaction policy;
- cross-character left/right DME channel mapping;
- a canonical semantic ID used as the persistence key for flex values;
- a persistent cross-character Body Match mapping;
- whole-Master decoded state retained inside CPM after queries are answered.

Current CPM does need sufficient semantic information to preserve these distinctions:

- unique resolved semantic path;
- genuine absence;
- conflict;
- authority unavailable at the provider/health level;
- enough path/category information for `Face`, `Body Morphs`, and current Clothing Fit relevance tests.

Diagnostics currently also retain data such as match kind, destination list, spelling list, and occurrence count. Some of those are useful for evidence/debugging rather than core Body/Expression mutation semantics.

---

## 12. Open architectural questions

These are intentionally left unresolved for Astra.

1. Can Normalizer and CPM safely consume exactly the same authority projection when CPM's central workload is batched live-literal → status/path classification rather than hierarchy presentation?

2. Does CPM need full resolved hierarchy paths long-term, or only category facts equivalent to the current `Face`, `Body Morphs`, and `Clothing` tests?

3. Which current diagnostic fields — spellings, destination arrays, occurrence counts, exact/folded match kind — belong in the normal production consumer view versus an optional diagnostic view?

4. Is the current process-global resident provider lifetime appropriate under shared authority, or should CPM use an operation-scoped or window-scoped authority view?

5. If the authority generation changes while CPM remains open, when should the currently selected character's cached semantic scope become invalid?

6. Should an already-selected character continue using the generation under which its scope was built until explicit reselection, or should a generation change force immediate semantic-context invalidation?

7. Should v3 presets continue recording `capture_provider` source SHA/generation as provenance? Current Apply logic records but does not enforce those values.

8. How should model-local Review misses be surfaced when a later authority generation positively resolves them? Current CPM automatically ceases to apply the override because overrides are valid only for current Master misses.

9. Can the current CPM pure semantic scope be populated from the same shared consumer projection used by Normalizer without importing Normalizer-only presentation requirements?

10. Is CPM's selected-model pure semantic scope still the right caching boundary if shared authority makes repeated batch lookup extremely cheap?

11. Where should authority admission/health validation live so CPM can preserve its current distinction between `MasterUnknown` and `AuthorityUnavailable` without duplicating validation policy?

12. Does any future shared projection need special support for Clothing Fit's target relevance checks, or are those adequately expressed by the same path/category lookup CPM already consumes?

13. When an authority revision intentionally changes Body/Expression classification, should existing exact-set preset incompatibility remain the sole migration behavior, or should a later integration plan provide an explicit compatibility transition? Current implementation itself does not answer this.

---

## 13. Final deliverable notes

### Source entry points for Astra

The smallest useful inspection set is:

#### Primary source

`SFM_CSP_G18AN_SaveNewCopy.py`

Focus on these current production regions:

- **1125-1128** — current provider-mode constants / forced SIDECAR selection.
- **2298-2639** — `SidecarSemanticProvider`.
- **3339-3459** — provider singleton/invalidation/runtime stats and basic path classification.
- **3763-3923** — semantic literal classification and model semantic snapshot.
- **18612-18650** — provider health probe.
- **19167-19255** — pure-scope assertion boundary.
- **19527-19778** — cached-scope authority/live-model validity and fresh live binding resolution.
- **20041-20650** — provider provenance capture, character record, semantic scope, Review override persistence.
- **20676-20914** — persisted preset validation.
- **23869-25950** — current generic bone-scale indexed capture/plan/validation; useful specifically to see what semantic authority does **not** own.
- **26032-26894** — Body snapshot, Save, and Update.
- **27257-28051** — Body/Expression Apply and Clothing Fit source/apply flow.
- **28097-34867** — `ProdWindow`; especially provider-unavailable UI, render/model selection, Review, Clothing Fit staging, and close lifetime.
- **34871-34895** — production entry point.

Historical/qualification regions worth reading only where relevant:

- **514-668** — live MONO/STEREO/left-right binding structure.
- **6803-7323** — structural Clothing Fit mapping and semantic relevance warnings.
- **9256-9600** — historical Krystal2020 Head Scale adapter.
- **16284-16471** — safe structural Fit mapping plan.

#### Supporting evidence

- `SFM_CSP_RefactorLedger_2026-09-16_v196.md` — chronological qualification/evidence ledger.
- `SFM_CSP_StaticRefinementAudit_G18AG_2026-09-15.md` — current-code bloat/reachability/release-hygiene assessment.
- `SFM_CSP_Astra_HolisticAudit_Disposition_2026-09-15.md` — prior audit findings and dispositions.
- `SFM_CSP_G18AN_SaveNewCopy_StaticCheckpoint_2026-09-16.md` — current candidate checkpoint identity.

### Unresolved questions

- Whether CPM should receive full paths or a narrower semantic projection.
- Whether diagnostics and operational classification should use the same authority view.
- Correct lifetime/pinning behavior for a long-lived CPM window when authority generation changes.
- Whether provider/source-generation provenance should remain in saved presets.
- Whether the current selected-model pure semantic scope remains the appropriate cache boundary after shared authority integration.
- Whether Normalizer and CPM can use one identical consumer projection without either consumer inheriting unnecessary semantics.
- How intentional future semantic reclassification should interact with existing exact-set preset compatibility.
- Whether shared authority health/admission should fully replace CPM-local provider-health checks or merely feed them.

### Scope statement

> This dossier documents Character Preset Manager as a prospective consumer of the shared Animation Groups Master authority. It does not recommend an integration architecture, broker API, sidecar modification, or migration sequence. Those decisions are intentionally left to Astra's holistic review.
