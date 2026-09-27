> **Repository context (added by this checkpoint, not part of the original CPM document):** source repository `chadchan3d/sfm-character-preset-manager`, commit `390e01e` (`390e01eb7ac1ceb220e480126f40077703acb0f4`), original path `docs/SFM_CHARACTER_TOOLS_INTEGRATION_HANDOFF.md`, source SHA-256 `0b9a9d4266b20475a80939381c6825ae7362f00096a46088c917483f8a32d9e1`.
>
> This repository (`chadchan3d/sfm-animation-groups-master`) is now the continuing home of SFM Character Tools and CPM convergence. The CPM repository is closed at commit `390e01e` as a source archive; this supersedes any statement below that the CPM repository "remains canonical."
>
> "Shared authority remains unchanged" means the `sfm_master_authority_productionized` package in this repository stays byte-stable at its already-qualified build; CPM code is not added to that package.
>
> References below to CPM-repo paths map to their imported locations here: `README.md` is not imported and remains only in the closed CPM source archive; `docs/ENGINEERING_NOTES.md` -> `docs/qualification/CPM_ENGINEERING_NOTES.md`; `docs/DEVELOPMENT_HISTORY.md` -> `docs/qualification/CPM_DEVELOPMENT_HISTORY.md`; `docs/reviews/CPM_CONVERGENCE_ADVERSARIAL_REVIEW.md` -> `docs/qualification/CPM_CONVERGENCE_ADVERSARIAL_REVIEW.md`; `docs/SFM_CHARACTER_TOOLS_INTEGRATION_HANDOFF.md` -> `docs/qualification/CPM_CONVERGENCE_INTEGRATION_HANDOFF.md`; `src/SFM_CSP_G18AN_SaveNewCopy.py` is not imported and remains only in the closed CPM source archive.
>
> Everything below this line is exact imported content.

---

# Character Preset Manager → SFM Character Tools Integration Handoff

**Status:** Controlling CPM convergence implementation specification
**Checkpoint purpose:** Documentation-only checkpoint incorporating the external adversarial review (verdict: ACCEPT WITH CORRECTIONS)
**Implementation status:** No CPM integration code has been written at this checkpoint

This document supersedes earlier CPM → SFM Character Tools handoff drafts and review addenda. It is intended to stand alone.

## Adversarial review outcome

The external adversarial review of the previous checkpoint returned **ACCEPT WITH CORRECTIONS**.

The core seam remains approved:

> unchanged canonical broker → CPM-owned `cpm_compat_v1` projection → exact-literal interpretation → existing CPM semantics

The review found no correctness reason to move the CPM projection into the shared authority package or to change the qualified shared build.

The full review is archived verbatim at `docs/reviews/CPM_CONVERGENCE_ADVERSARIAL_REVIEW.md`. That archive is the detailed source for the corrections below; where this handoff and that review differ, the review governs.

This revision incorporates the corrections:

- operation-bound authority contexts replace the single release-after-planning model (§14);
- Clothing Fit retains its stage lease through post-stage verification (§15);
- G18AN is not the sole oracle for provider-native conflicts (§4, §7, §20);
- CPM compatibility identity excludes broker-local counters (§11);
- CPM builder callback qualification obligations are explicit (§6);
- `estimated_bytes` covers all retained view data, not only family rows (§9);
- the broad parity plan is replaced by four focused qualification suites (§20);
- the implementation sequence is corrected (§22).

Maintained without change:

- the CPM repository remains canonical for CPM;
- the shared authority repository remains unchanged;
- no Normalizer package modification;
- no K work yet.

## 1. Product architecture and migration objective

The target product is **SFM Character Tools**:

- Control Group Normalizer
- Character Preset Manager (CPM)
- one shared Animation Groups Master / compiled sidecar authority
- one canonical shared broker/runtime
- separate consumer projections and lifetimes
- SFM Model Scanner as an optional contribution utility

The shared-authority/Normalizer foundation is treated as settled through:

- **F — CLOSED**
- **G — PASS / CLOSED**
- **I — PASS / CLOSED**
- **J — PASS / CLOSED**

The migration objective is deliberately narrow:

> **unchanged canonical shared broker + CPM-owned `cpm_compat_v1` fold-family projection + CPM-owned exact-literal interpretation + existing CPM product semantics**

CPM should join the settled shared foundation without redesigning qualified CPM mechanics or unnecessarily changing the shared package already used by the Normalizer.

## 2. Governing identities

### CPM

- Repository: `chadchan3d/sfm-character-preset-manager`
- Branch: `main`
- Migration baseline: `src/SFM_CSP_G18AN_SaveNewCopy.py`
- G18AN SHA-256: `3326024ddecd544ad1e10659bbf7b98420b5f147fca775433878c19fd9e66b3e`
- G18AN Git blob: `e8c1bceecdd2d3569168a35b27b8e49d7a38b911`
- Internal version: `0.2.0-rc7-g18an-save-new-copy`

No later runnable CPM candidate is authoritative. This checkpoint must not create one.

### Shared authority / Normalizer

The currently accepted shared runtime identity is:

- API: `1.0.0-b2a`
- build: `package-boundary-corrected-2026-09-22`

The shared runtime is imported canonically as:

`sfm_master_authority_productionized.runtime`

The production Normalizer already uses the canonical runtime and broker, including origin/build checks, `runtime.get_broker(...)`, `broker.acquire_or_reuse_views(...)`, `expected_generation`, explicit view leases, and deterministic lease release.

Historical material that says the shared authority is not yet wired into a production consumer is superseded by the current production Normalizer and current F/G/I/J evidence.

## 3. What remains qualified and should not be redesigned

The authority migration sits above already-qualified CPM mechanics. Absent contradictory new evidence, do not reopen:

- Normalizer F/G/I/J closure;
- RC7 native mutation sequencing;
- preflight before Undo creation;
- no-op-before-Undo behavior;
- Abort/Finish/rollback discipline;
- same-time refresh and independent readback boundaries;
- the prohibition on unsafe native access patterns already excluded by qualification;
- generic complete bone scaling;
- operation-scoped indexed Body capture;
- normalized model path + checksum as durable model identity;
- Animation Set name as mutable metadata;
- fresh live DME/native binding resolution per operation;
- exact-set preset compatibility;
- miss-only Review;
- authority positive/conflict precedence over Review;
- structural/native Clothing Fit source-target mapping;
- one changed Fit target = one native transaction;
- one Fit target per zero-delay Qt event turn;
- foreign-modal yielding;
- scalar Qt row identifiers with complex records kept Python-owned;
- no silent TXT fallback;
- the conclusion that the old multi-second Body Save/Update cost was caused by repeated native bone-map traversal and was already addressed by indexed capture.

The authority migration must preserve these mechanics rather than treating them as open architecture questions.

## 4. Current G18AN authority behavior to preserve

G18AN's current development-era provider path is not the final production seam, but its consumer semantics are the migration oracle for ordinary resolution, fold matching, healthy absence, wrapper paths, and snapshot/signature behavior.

G18AN is **not** the sole oracle for provider-native conflicts; see §7 (Conflict) and Suite 1 in §20.

For each exact queried flex literal, the existing answer contract carries:

- `query_literal`;
- `status`;
- `match_kind`;
- `resolved_path`;
- `destinations`;
- `spellings`;
- `occurrence_count`.

Current semantic status values include:

- `resolved`;
- `conflict`;
- `absent`;
- authority-unavailable as a separate failure state.

Current match values are:

- `exact`;
- `ascii-fold`;
- `none`.

G18AN uses `match_kind` to maintain folded-resolution counts. It also stores `match_kind`, destinations, and Master spellings in its semantic snapshot, and they participate in `semantic_snapshot_signature()`.

Therefore these semantics must not disappear incidentally during the shared-authority migration.

### Path representation

G18AN strips the sidecar's synthetic outer wrapper before CPM sees semantic paths.

CPM therefore expects paths such as:

- `Face/...`
- exact `Body Morphs`
- `Clothing/...`

and not lower-level forms such as:

- `groupFile/Face/...`
- `groupFile/Body Morphs`

The migration must preserve this wrapper-stripped representation exactly.

## 5. Shared authority remains unchanged

CPM will **not** add a production CPM adapter module to `sfm_master_authority_productionized` for this migration.

The accepted shared package remains the authority owner for:

- effective Master observation;
- sidecar selection and source-generation validation;
- provider lifetime;
- generation identity;
- cache ownership;
- cache admission and eviction;
- aggregate resource accounting;
- requested-vocabulary admission;
- authorization tokens;
- leases;
- generation invalidation and retire/drain behavior.

CPM uses the broker's already-supported consumer-supplied projection-builder seam.

This preserves the currently qualified shared package and the Normalizer's currently pinned shared-build identity rather than creating a new shared-package build solely to add CPM.

If a later design materially changes the shared package or adds API surface consumers depend upon, the package's build-identity policy still applies: the build ID must change and all production consumers must converge on that same newly identified build. Do not silently retain the old build string after materially changing what it identifies.

## 6. CPM owns the projection adapter

CPM owns the production consumer projection code.

Use:

`consumer_kind = "cpm_compat_v1"`

The version suffix is part of cache identity. Until the shared authority has an independent consumer-projection contract-version dimension, a future incompatible projection must use a new consumer identity such as:

`cpm_compat_v2`

A v2 consumer must not reuse a v1 cache entry.

### Builder contract

The CPM-owned adapter is passed to the canonical broker through `request_specs`.

It:

- receives a temporary provider only through the broker-owned builder callback;
- never opens a sidecar itself;
- never selects a generation;
- never owns or retains a provider;
- never creates another broker;
- never bypasses broker admission;
- declares the exact requested folded vocabulary;
- declares the accurate request scale required by the accepted broker contract;
- returns detached payload + shared `CoverageDescriptor` + conservative `estimated_bytes`;
- returns before cohort/provider teardown;
- retains no provider or provider-backed state.

The adapter may use the pinned shared package's core coverage/view types and broker-supplied provider callback protocol. That is an intentional dependency on the exact API/build CPM verifies at startup, not a second authority implementation.

### Callback qualification obligations

The broker's builder extension seam is approved, but the broker does not deeply validate consumer callbacks. Callback correctness is therefore a CPM qualification obligation.

The CPM builder must prove:

- requested vocabulary equals declared vocabulary;
- coverage keys match the requested folds;
- the returned payload is fully detached;
- the payload contains no provider references;
- no iterators, closures, or generators retain provider or authority state;
- `estimated_bytes` is conservative (§9);
- unsupported provider results fail closed;
- partial healthy results are never published as a complete view.

## 7. Broker-cached CPM projection is fold-family based

The accepted broker cache identifies a detached view using the effective combination of:

- Master generation;
- projection contract version;
- covered folded-key set;
- consumer kind.

Exact request spelling is not part of that identity.

Therefore the cached CPM projection must contain only facts invariant for a folded family.

It must **not** cache:

- exact `query_literal`;
- exact-query-dependent `match_kind`.

### `cpm_compat_v1` payload

Conceptually:

```text
{
    "contract": "cpm-compat-v1",

    "families_by_fold": {
        <folded key>: {
            "status": "resolved" | "conflict" | "absent",
            "resolved_path": <wrapper-stripped unique path> | None,
            "destinations": [<wrapper-stripped path>, ...],
            "spellings": [<actual Master literal spelling>, ...],
            "occurrence_count": <integer>
        }
    }
}
```

Every family row must be a property of the Master fold family itself.

### Unique resolution

For a family with one destination:

- `status = "resolved"`
- `resolved_path` is the unique wrapper-stripped destination;
- `destinations` contains that destination;
- `spellings` contains the actual Master spellings in the family;
- `occurrence_count` records the family occurrences.

### Conflict

Whatever provider-native representation denotes a fold family with multiple destinations must normalize to:

- `status = "conflict"`
- `resolved_path = None`
- complete normalized `destinations`;
- complete actual Master `spellings`;
- family `occurrence_count`.

CPM must not depend on whether the provider internally represented this as a conflict object or as occurrence rows spanning multiple destinations.

G18AN cannot serve as the sole oracle for this normalization: its current adapter rejects a provider result type that its pinned provider returns. Therefore:

- ordinary Hit / MasterUnknown parity is compared against G18AN;
- conflict parity is compared against independent expected fixtures;
- provider-native conflict translation is an adapter qualification requirement.

The CPM conflict taxonomy itself does not change.

### Healthy absence

For a genuinely searched fold with no Master match:

- `status = "absent"`
- `resolved_path = None`
- `destinations = []`
- `spellings = []`
- `occurrence_count = 0`

Healthy absence is distinct from authority failure and from Uncovered.

## 8. Exact-literal interpretation remains CPM-owned

When materializing the pure CPM semantic scope, CPM starts from the **current exact live literal**.

For each literal:

1. apply the canonical ASCII-fold rule;
2. find its fold-family row in `families_by_fold`;
3. reconstruct the existing G18AN answer contract.

The exact answer is:

```text
{
    "query_literal": <current exact live literal>,
    "status": <family status>,
    "match_kind": <reconstructed below>,
    "resolved_path": <family resolved path>,
    "destinations": <family destinations>,
    "spellings": <family Master spellings>,
    "occurrence_count": <family occurrence count>
}
```

`match_kind` is:

- `none` if the healthy family result is absent;
- `exact` if the current exact live literal occurs in the family's actual Master spellings;
- otherwise `ascii-fold`.

The reconstructed exact answer then feeds the existing G18AN-style semantic snapshot and product classification.

This split is deliberate:

```text
broker cached view
    = fold-family authority facts

CPM scope materialization
    = current exact live literal
    + fold-family facts
    -> G18AN-compatible exact answer

CPM product policy
    = Body / Expression / Other / Review / Conflict
```

## 9. Coverage and resource-accounting contract

The CPM projection participates normally in the existing broker contract.

The request uses:

`consumer_kind = "cpm_compat_v1"`

and declares the exact folded request set.

The builder must expose the accepted-build equivalents of:

- `declared_request_folds`;
- `declared_request_scale`.

The broker remains responsible for:

- packed per-family admission;
- cumulative requested-vocabulary accounting;
- aggregate retained/transient accounting;
- provider open/close;
- H0/H1 generation validation;
- atomic view publication;
- eviction;
- authorization;
- leases.

The CPM adapter's `estimated_bytes` must conservatively cover everything the broker retains for the view:

- the detached semantic payload;
- coverage storage;
- any other retained view data.

Counting only family rows under-reports retained cost and is not acceptable.

Later exact-literal answers, live-binding data, semantic classes, Review overlays, and semantic snapshot/signature state belong to CPM's pure scope and are not part of broker retained-view accounting.

### Coverage distinctions

Maintain the shared distinction between:

- Known;
- MasterUnknown;
- Uncovered;
- AuthorityUnavailable at acquisition level.

For CPM:

- a uniquely resolved family can be broker coverage Known;
- a conflict family can also be broker coverage Known because the requested family was successfully materialized;
- a healthy missing family maps to broker MasterUnknown and CPM `absent`;
- a requested fold that is Uncovered is a projection/coverage contract failure;
- AuthorityUnavailable means no trustworthy CPM view exists.

Only a genuine healthy Master absence may enter Review.

Uncovered and AuthorityUnavailable must never be converted into `absent`.

## 10. Shared authority versus CPM policy

### Shared broker/runtime owns

- canonical package identity;
- one process broker;
- Master observation;
- sidecar/source admission;
- provider lifetime;
- generation;
- requested-fold resource accounting;
- cache;
- authorization;
- leases;
- retire/invalidate/drain.

### CPM projection adapter owns

Neutral fold-family materialization:

- unique resolution;
- provider-native conflict normalization;
- genuine Master absence;
- wrapper stripping;
- normalized destinations;
- actual Master spellings;
- occurrence counts;
- complete requested coverage;
- conservative detached payload estimate.

### CPM scope materialization owns

- current exact `query_literal`;
- exact versus ASCII-fold `match_kind`;
- reconstruction of the full G18AN answer.

### CPM product layer owns

- Body classification;
- Expression classification;
- Other;
- Review;
- Exclude/Reclassify;
- semantic snapshot/signature;
- preset compatibility;
- generic bone scaling;
- Clothing Fit structural/native mapping;
- native scene mutation and Undo.

The shared broker never needs to understand “Body Preset.”

## 11. Long-lived pure scope, short broker lease

CPM retains its pure selected-character semantic scope during UI idle time.

It does **not** retain a broker lease merely because the character remains selected.

### Long-lived CPM state may include

- model identity;
- exact semantic literals;
- Body/Expression/Other classifications;
- genuine misses;
- conflicts;
- reconstructed `match_kind`;
- Master spellings;
- normalized destinations;
- Review metadata;
- vocabulary signature;
- representation signature;
- semantic snapshot/signature;
- semantic policy revision;
- authority generation SHA.

This is detached Python state.

### Compatibility identity

CPM compatibility identity uses only:

- Master SHA;
- CPM projection identity (`cpm_compat_v1`);
- CPM policy identity (semantic policy revision).

Do not map any of the following into CPM compatibility identity:

- broker cohort IDs;
- provider-open counters;
- artifact IDs.

Reopening the same semantic authority must not invalidate a valid CPM scope. Broker-local counters may remain in diagnostics only.

### Short broker leases

A lease exists only while CPM is consuming a shared view for a bounded authority operation, such as:

- initial scope construction;
- action-boundary freshness/reauthorization;
- a Clothing Fit target stage.

Leases are deterministically released at the operation-specific boundary defined in §14.

No CPM lease should survive ordinary UI idle time.

### Additional lifetime notes

- If G2 has no usable sidecar, CPM remains explicitly unavailable; do not restore G1 as mutation authority or synthesize Review misses.
- Clear released lease/view references: a released `ViewLease` still contains its `.view` reference.
- The CPM builder callback remains synchronous and avoids Qt event pumping.
- Do not copy Normalizer's J protected-file-handle mechanism into CPM merely for symmetry: CPM's writes never invoke native Rebuild to reread the Master, so require fresh authorization at operation entry, no yield between authorization/planning and mutation entry, and no new interpretation after a yield -- readback and recovery remain tied to the completed operation.

## 12. Initial scope construction

The intended sequence is:

```text
live model vocabulary
        ↓
folded requested vocabulary
        ↓
canonical broker
        ↓
acquire_or_reuse_views(...)
        ↓
cpm_compat_v1 DetachedView
        ↓
short ViewLease
        ↓
materialize exact G18AN-compatible answers
        ↓
build pure CPM semantic scope
        ↓
release lease
        ↓
publish scope into CPM UI
```

The broker owns the provider throughout the cohort. The resulting CPM scope retains no provider/native backing.

## 13. Action-boundary freshness proof

Before a later semantic-dependent operation, CPM performs a fresh:

`broker.acquire_or_reuse_views(... expected_generation=<scope generation>)`

using the same requested folded vocabulary and `cpm_compat_v1` consumer identity.

This is the generation proof.

The accepted broker performs a fresh Master observation even on a fully reusable cached path, so this boundary can reject an old scope generation without requiring an independent CPM filesystem watcher.

### Successful reauthorization

If acquisition succeeds under the same expected generation:

- take a short lease;
- verify authorization and requested coverage;
- perform the bounded semantic planning required by the action;
- capture the CPM Operation Authority Context (§14);
- release the lease at that operation's release boundary (§14);
- continue from detached CPM state, with late helpers consuming the captured context.

A complete scope rebuild is not required merely to prove the same generation is still current.

### Generation mismatch

If the old generation no longer matches:

- no mutation begins;
- do not reinterpret the mismatch as Review;
- do not silently replay the old action under the new generation;
- invalidate/discard the selected semantic scope;
- acquire current authority;
- rebuild the pure scope under the new generation;
- release its build lease;
- republish Body / Expression / Review state;
- require a new user action.

### Save/Update prompt-boundary timing

Save and Update currently check scope before opening a modal prompt, then revalidate scene context afterward. That ordering does not prove authority freshness at the point that matters. Place authorization after user prompts: the migration's `expected_generation` acquisition belongs after prompt return and before semantic work, not before the prompt opens.

## 14. Operation-bound authority contexts and release boundaries

The previous checkpoint proposed a single rule: release the short broker lease after planning and finish the mutation from detached state. Review showed this overstates how detached CPM state currently is.

Do not state or implement "all operations release authority after planning."

### Remaining authority dependencies

Four paths still reach provider or authority metadata after planning:

- Clothing Fit queries target vocabulary outside the selected-character scope;
- Fit performs semantic verification after staging;
- Apply postcommit and rollback verification revisit provider helpers;
- Save and Review reach provider metadata through persistence helpers.

### CPM Operation Authority Context

CPM uses bounded authority contexts. Semantic planning may detach facts, but any late helper that currently depends on authority metadata must consume the captured operation context rather than reopening a global provider path.

A CPM Operation Authority Context contains:

- Master SHA;
- broker generation/provenance identity;
- projection contract identity;
- resolved semantic membership;
- persistence descriptor facts;
- operation baselines.

Late Save, Update, Apply, and Review helpers consume this context. None may implicitly reacquire global authority.

### Operation-specific release rules

**Body Save / Expression Save**

Release after:

- current-generation authorization;
- membership resolution;
- persistence descriptor capture.

Release happens before the durable write. Late persistence helpers must not reacquire global authority.

**Body Update / Expression Update**

Same rule as Save: detached semantic/capture planning, operation context retained, durable replacement afterward.

**Body Apply / Expression Apply**

Release only after:

- the detached mutation plan exists;
- the operation context is captured;
- postcommit and rollback verification dependencies are resolved into that context.

Rollback verification must not silently reopen authority.

**Review / Reclassify**

Release after:

- healthy-miss eligibility is established;
- persistence facts are captured.

If a later scope rebuild is needed, it uses a separate fresh acquisition rather than extending the original lease.

**Clothing Fit**

See §15. Fit is the case where a source-only scope is insufficient, so the first migration retains the stage lease through post-stage verification.

### Rule for later findings

If a migrated operation is found to need authority after its release point, move that operation's release boundary later or capture the missing facts into its context. Do not expand lease lifetime globally.

## 15. Clothing Fit generation rule

One user-initiated Clothing Fit owns one semantic generation, `Gfit`.

Before every queued target begins, CPM re-proves that same generation through:

`acquire_or_reuse_views(... expected_generation=Gfit)`

The existing Fit mechanics remain:

- one target per zero-delay Qt event turn;
- one changed target per native transaction/Undo;
- structural/native target correspondence.

### Stage lease rules

The first migration retains each target's stage lease through post-stage verification:

- target vocabulary must be included in the request, because it lies outside the selected-character scope;
- planning and verification remain pinned to Gfit;
- the lease is released before the next target is scheduled;
- a lease is never held across queued UI stages.

### If generation remains Gfit

For the target:

- acquire/reuse `cpm_compat_v1` with the target's vocabulary included in the request;
- take a stage lease;
- verify coverage/authorization;
- perform target semantic planning under Gfit;
- run the existing target mutation;
- perform post-stage semantic verification under the same lease, still pinned to Gfit;
- release the lease;
- only then queue the next target.

### If generation changes between targets

If target 1 committed under G1 and G2 becomes current before target 2:

- target 1 remains committed;
- target 2 does not begin;
- remaining targets do not switch to G2 inside the same Fit;
- terminate that Fit;
- rebuild selected CPM semantic scope under current authority;
- a later user-initiated Fit may begin under G2.

One Fit must never silently span multiple semantic generations.

### Additional corrections

- Keep `Gfit` separate from the existing integer `fit_generation`, which is a callback-cancellation identity, not a semantic generation.
- Perform the `Gfit` check after any foreign-modal suspension ends.
- On mismatch before the next target, stop the remaining targets and retain truthful committed/unattempted accounting.
- Uncovered post-stage vocabulary fails rather than triggering an implicit G2 acquisition.

## 16. Canonical bootstrap/import

CPM uses the same canonical package-bootstrap contract as the qualified Normalizer.

Before package import, use the same `sys.executable`-derived MAINMENU location formula already established by the Normalizer.

Then import only the canonical package identity:

- `sfm_master_authority_productionized.runtime`
- shared errors/bootstrap modules as required.

CPM must verify:

- expected package origin;
- runtime API `1.0.0-b2a`;
- runtime build `package-boundary-corrected-2026-09-22`;
- canonical module identity;
- broker acquisition through `runtime.get_broker(...)`.

Do not:

- create a second authority owner;
- vendor another runtime copy into CPM;
- `execfile()` the shared runtime;
- use G18AN's development sidecar discovery path in the final production seam;
- introduce a second provider-discovery system.

The tiny pre-import locator formula may be duplicated intentionally because the package path must be established before its bootstrap module can itself be imported. Add an offline equivalence check against the Normalizer formula rather than redesigning bootstrap merely to remove those few lines.

## 17. Saved presets across authority generations

Authority generation is capture provenance, not a permanent preset compatibility lock.

If a preset was saved under G1 and current authority is G2:

### Compatible semantic set

If the current accepted semantic mutation-key set and the existing model/representation/bone compatibility requirements remain equal, Apply may continue.

Generation difference alone does not reject the preset.

### Membership change

If current authority changes the accepted Body or Expression mutation-key set, existing exact-set compatibility rejects the old preset.

Do not partially apply it.

### Authority unavailable

If current authority cannot establish the accepted semantic set, semantic-dependent Apply fails closed before mutation.

## 18. Shared-authority migration hazards

### Real hazards that migration must close

- AuthorityUnavailable being mistaken for healthy absence.
- Uncovered being mistaken for healthy absence.
- conflict being flattened into resolved/Known at the CPM product layer.
- stale pure scope after authority generation change.
- exact-query-dependent data being placed in the fold-keyed shared cache.
- a future projection contract reusing the same consumer-kind cache identity.
- duplicate runtime/broker module ownership.
- a long-lived CPM lease delaying retire/drain.
- Clothing Fit switching generations between targets.
- old development-provider paths remaining accidentally reachable as silent production fallback.
- late Save/Update/Apply/Review helpers reopening a global provider path instead of consuming operation context.
- rollback verification silently reacquiring authority.
- a source-only Fit scope missing target vocabulary.
- a Fit lease held across queued UI stages.
- broker cohort IDs, provider-open counters, or artifact IDs leaking into CPM compatibility identity.
- `estimated_bytes` counting only family rows.
- partial healthy builder results being published.

### Not migration hazards

Do not reopen:

- scale graph mechanics;
- indexed Body capture;
- exact-set compatibility;
- native Undo design;
- Animation Set rename identity;
- Fit structural mapping;
- old Body Save performance work.

## 19. Historical dead ends / do-not-repeat work

Do not re-propose these superseded approaches without new evidence:

- mandatory per-character semantic profiles instead of shared Master authority;
- hardcoded Head Scale as the production scaling architecture;
- repeated full bone-map traversal for every Body validation step;
- provider failure converted into Unknown/Review;
- local Review overriding positive authority;
- local Review overriding conflicts;
- silent TXT fallback;
- long-lived DME/native objects in semantic scope;
- persistent cross-character Body Match tables as the current Fit architecture;
- Animation Set name as durable identity;
- generic same-name sidecar imports vulnerable to SFM module-path collisions;
- complex nested preset dictionaries retained in Qt `UserRole`;
- reopening the already-resolved multi-second Body Save investigation.

## 20. CPM convergence qualification

The following qualification belongs to CPM convergence before K.

The earlier broad parity plan (former gates C1–C6, C11, and C12) is replaced by four focused suites. Boundary gates C7–C10 are carried forward.

### Suite 1 — Projection and semantic parity

Cover:

- unique families;
- aliases;
- exact and folded queries;
- duplicate occurrences;
- healthy absence;
- conflict;
- wrapper paths (Face, `Body Morphs`, Clothing, nested Other, conflict paths);
- same-fold/different-exact-query cache reuse;
- `cpm_compat_v1` / `cpm_compat_v2` cache separation;
- final semantic snapshot/signature parity.

Oracles:

- ordinary resolved and MasterUnknown/absent cases compare against G18AN;
- conflict cases compare against independent expected fixtures, because G18AN's adapter rejects a provider result type its pinned provider returns.

Answer parity requires:

- family status;
- wrapper-stripped resolved path;
- destinations;
- actual Master spellings;
- occurrence count;
- query literal;
- reconstructed match kind;
- semantic class;
- operation;
- folded-resolved count;
- accepted Body literals;
- accepted Expression literals.

Signature parity requires (matches `semantic_snapshot_signature()`; `occurrence_count` belongs to answer parity above and is not currently part of this signature -- do not conflate the two gates):

- literal;
- live-binding count;
- live shapes;
- ambiguity;
- status;
- match kind;
- path;
- destinations;
- spellings;
- class;
- operation;
- deterministic ordering.

An exact spelling inside a conflicting family remains a conflict.

No synthetic outer wrapper may leak to CPM.

**Fit target-side warning parity:** preserve the exact existing warning classification for Fit -- unmatched target controls resolve to exact `Body Morphs` or `Clothing`, never broadened to arbitrary descendants and never omitted because the correspondence is structural.

**Same-fold/different-exact-query reuse (decisive):**

1. Choose exact literal A and fold F.
2. Acquire `cpm_compat_v1` for F.
3. Lease the view.
4. Materialize A's exact G18AN-compatible answer.
5. Release the lease.
6. Request a different exact literal B where `fold(A) == fold(B) == F`.
7. Require the broker to be able to reuse the same cached fold-family view.
8. Lease that reused view.
9. Materialize B independently from B + the cached family facts.
10. Release.

Require for B:

- `query_literal == B`;
- `match_kind` is recomputed correctly for B;
- status is correct;
- paths/destinations are correct;
- Master spellings are correct;
- occurrence count is correct;
- resulting G18AN semantic snapshot/signature matches the old provider.

The suite fails if exact-query-dependent information has leaked into the cached projection.

**Projection-version separation:**

Using the same generation and folded coverage, `cpm_compat_v1` must not satisfy a `cpm_compat_v2` request. A fixture consumer identity is sufficient; no real v2 implementation is required.

### Suite 2 — Callback ownership

Prove:

- the broker invokes the CPM builder through the approved seam;
- declared, requested, and covered vocabulary agree exactly;
- request scale is accurate and broker admission receives the real requested vocabulary;
- unsupported provider results fail closed;
- partial healthy results are not published;
- missing requested coverage fails closed, and Uncovered never becomes absent;
- the broker closes the provider after the callback;
- no provider, iterator, closure, or generator is retained by the payload;
- `estimated_bytes` includes detached semantic payload, coverage storage, and retained view data;
- no production path opens authority outside the broker.

### Suite 3 — Action boundary routing

Instrument Save, Update, Apply, and Review/Reclassify.

Prove:

- each operation captures a CPM Operation Authority Context before its release point;
- late helpers consume that context;
- no late helper reopens a global provider path after release;
- Apply postcommit and rollback verification complete without reacquiring authority;
- a Review scope rebuild uses a separate fresh acquisition;
- Reclassify reports the successful durable edit separately from the resulting rebuilt classification.

### Suite 4 — Fit continuation and failure

Prove:

- target-only vocabulary is requested and covered;
- planning and post-stage verification are pinned to Gfit;
- the stage lease is released before the next target is scheduled;
- no lease is held across queued UI stages;
- a generation change before target two prevents any target-two mutation.

### Gate C7 — AuthorityUnavailable boundary

Exercise controlled:

- no valid authority;
- source-generation mismatch;
- expected-generation rejection;
- canonical-runtime/build rejection;
- adapter contract failure.

Require:

- no synthetic absent rows;
- no false Review population;
- no semantic-dependent mutation.

### Gate C8 — lease lifecycle / no-idle-lease

Prove:

- scope build uses a short lease;
- pure scope survives lease release;
- ordinary UI idle holds no CPM lease;
- action reauthorization uses another short lease;
- each operation releases at its defined boundary (§14);
- normal paths return outstanding CPM lease count to baseline;
- release failure uses the broker's durable unreleased-lease mechanism rather than GC dependence.

### Gate C9 — expected-generation reauthorization

Build G1 scope.

Require:

- unchanged G1 passes;
- current G2 rejects the stale G1 expected generation;
- old user action performs no mutation;
- G2 scope rebuilds;
- old Review/classification data cannot silently override current positive/conflict authority.

### Gate C10 — canonical package/broker identity

Prove:

- CPM bootstrap resolves the current qualified package;
- expected origin matches;
- API/build identities match;
- runtime is canonical;
- CPM and Normalizer obtain the same process broker.

## 21. Minimum real-SFM CPM convergence tests

Do not repeat the whole historical CPM qualification campaign.

Run the smallest real-SFM set that exercises the new seam.

### Startup / scope

- open CPM;
- select representative model;
- build scope through canonical broker;
- confirm expected semantic results;
- confirm development provider path is unused;
- confirm no CPM lease remains after scope publication.

### Representative downstream path

Exercise enough existing functionality to prove the seam reaches qualified mechanics:

- Body Save or Update;
- changed/no-op Body Apply;
- representative Expression Apply;
- native Undo;
- a Fit target with relevant vocabulary absent from the source.

### Review

Exercise:

- healthy Master absence;
- local classification;
- Reclassify;
- positive authority;
- conflict;
- AuthorityUnavailable.

Only healthy absence may be reviewable.

### Open-window generation replacement

- build G1 scope;
- keep CPM open;
- activate controlled G2;
- invoke semantic-dependent action;
- G1 expected-generation proof rejects before mutation;
- CPM rebuilds G2 scope;
- original action does not replay automatically.

### Generation change during a Save/Update prompt

- open the Save or Update modal prompt under G1;
- change authority to G2 while that prompt is open;
- confirm the prompt;
- the post-prompt `expected_generation` acquisition rejects the stale G1 expectation before any write;
- no write occurs under the stale generation;
- current-scope refresh follows, with no replay of the original action.

### Clothing Fit generation transition

- start Fit under G1;
- commit target 1;
- change to G2 before target 2;
- no CPM lease remains held between targets;
- target-2 G1 proof fails;
- target 2 does not mutate;
- Fit stops;
- target 1 Undo remains valid;
- later new Fit may use G2.

### Minimal Normalizer coexistence sanity

During CPM convergence prove only:

- both consumers use the same canonical runtime;
- both obtain the same broker;
- CPM leaves no inappropriate lease;
- CPM does not destroy Normalizer state;
- one already-qualified representative Normalizer operation remains usable.

Broader cross-consumer workflow qualification belongs to K.

### Resource measurement

Measure CPM's actual new scope/projection retention and replacement peak during these runs. Broker accounting excludes CPM-owned scope copies; it cannot establish their cost by itself.

## 22. Implementation sequence and remaining CPM blockers before K

### Implementation sequence

1. Implement the CPM-owned family projection and exact-answer interpreter.
2. Wire canonical bootstrap and the pure idle scope.
3. Introduce the CPM Operation Authority Context.
4. Integrate Clothing Fit per target.
5. Run the focused qualification suites and carried-forward gates (§20).
6. Only then begin K.

### Remaining blockers before K

After the seam is implemented:

1. pass Suites 1–4;
2. pass gates C7–C10;
3. pass the Fit generation-interruption test;
4. deliberately qualify rollback-verification failure for Body/Expression Apply;
5. deliberately qualify rollback-verification failure for Clothing Fit;
6. remove or isolate historical development authority machinery only after the new seam passes;
7. remove unnecessary diagnostic/development logging;
8. run focused post-cleanup regression.

Do not clean the old authority machinery in the same change that first proves the new seam.

## 23. K — SFM Character Tools product/workflow qualification

CPM is ready to enter K when:

- the production CPM authority path uses only the canonical broker;
- `cpm_compat_v1` parity is established;
- generation reauthorization is established;
- late operation helpers consume operation authority contexts;
- open-window replacement behavior is established;
- no idle CPM lease exists;
- Fit generation behavior is established;
- rollback failure gates are closed;
- historical development authority paths no longer present release ambiguity;
- no known CPM-specific convergence blocker remains.

K then qualifies the multi-consumer product, including:

- Normalizer first → CPM;
- CPM first → Normalizer;
- repeated alternation;
- CPM remaining open while Normalizer operates;
- close-order behavior;
- separate consumer view lifetimes;
- joint generation transitions;
- shared failure/recovery behavior;
- aggregate resource behavior;
- representative workflows from each tool.

## 24. L — installation/coexistence/release qualification

Leave for L:

- final installation layout;
- clean install;
- update install;
- exact installed shared package;
- exact installed CPM and Normalizer bytes;
- no duplicate authority package;
- no development deployment paths;
- no unintended TXT fallback;
- restart/reopen behavior;
- exact release hashes;
- final release-artifact CPM regression;
- required exact release-artifact Normalizer regression;
- coexistence from shipping bytes;
- packaging/documentation/provenance.

K proves the product workflow.

L proves the actual installed release.

## 25. Evidence and reading order for reviewers

Reviewers should establish current governing state before reading historical architecture prose.

### CPM repository

Read:

1. `README.md`
2. `docs/ENGINEERING_NOTES.md`
3. this handoff
4. `src/SFM_CSP_G18AN_SaveNewCopy.py`

For G18AN, focus on:

- semantic status/match constants;
- current provider result shape;
- wrapper normalization;
- semantic snapshot construction/signature;
- pure-scope validity;
- Review;
- Body Save/Update;
- Apply/Fit;
- long-lived window behavior.

### SFM Animation Groups Master repository

Read current governing:

1. real-SFM qualification ledger;
2. production Normalizer;
3. canonical runtime;
4. broker;
5. cohort;
6. views/view cache;
7. bootstrap;
8. production Normalizer compatibility adapter;
9. F/G/I/J closeout evidence relevant to ownership, later vocabulary, generation replacement, and native protection.

Treat older prose saying the package is not yet used by production as historical when current production source/ledger contradicts it.

### Private evidence

Use private CPM evidence only for disputed historical qualification claims. Raw logs, handoff archives, workstation paths, and unrelated development evidence should not be added to the public repository merely for completeness.

## 26. Historical evidence boundary

The project predates Git.

Do not invent retrospective Git commits for earlier G/RC/Q checkpoints.

Git history begins with the surviving audited G18AN baseline. Earlier checkpoint identifiers remain development-history identifiers, not Git commits.

Raw development evidence is intentionally excluded from the public repository.

## 27. Resolved adversarial challenge points

The previous checkpoint left two deliberate challenge points open. Both are resolved.

### A. Consumer-owned projection boundary — approved

No hidden broker, cohort, or package invariant was found that makes a CPM-owned projection builder unsafe. The unchanged J-qualified shared package is preserved. The approval is conditioned on the callback qualification obligations in §6 and Suite 2.

### B. Lease-release-before-mutation boundary — corrected

The single release-after-planning model is replaced by operation-bound authority contexts with operation-specific release rules (§14). Clothing Fit retains its stage lease through post-stage verification (§15).

## 28. Controlling implementation statement

The controlling migration seam is:

> **unchanged canonical shared broker + CPM-owned `cpm_compat_v1` fold-family projection + CPM-owned exact-literal interpretation + existing CPM product semantics**

More explicitly:

```text
shared broker cache
    = generation
    + folded vocabulary
    + cpm_compat_v1
    + fold-family authority facts

CPM pure semantic scope
    = current exact live literals
    + reconstructed exact/ascii-fold match semantics
    + G18AN-compatible semantic snapshot

CPM operation authority context
    = Master SHA
    + generation/provenance identity
    + projection contract identity
    + captured membership, persistence facts, baselines
    -> consumed by late operation helpers

CPM product behavior
    = Body / Expression / Other / Review / Conflict
```

The migration should preserve valid broker cache reuse rather than preventing it, preserve G18AN's existing semantic/signature contract, bind late authority dependencies to captured operation context, keep the shared package byte-stable, and avoid reopening already-qualified CPM mechanics.

## Final checkpoint verdict

**A. CPM current-state verdict**

G18AN remains the correct behavioral migration baseline. CPM's qualified mutation, storage, identity, scale, Review, modal, and Clothing Fit mechanics should remain intact.

**B. Minimum migration plan**

Implement one CPM-owned, broker-mediated, fold-family `cpm_compat_v1` projection; reconstruct exact G18AN answers in CPM; retain pure scopes without idle leases; reauthorize generation before semantic-dependent actions; capture a CPM Operation Authority Context per operation and release leases at operation-specific boundaries; pin one Fit to one generation, with a per-target stage lease held through post-stage verification.

**C. Release blockers after migration**

Pass the four focused suites and gates C7–C10, close the rollback-verification failure gates, clean historical authority and diagnostic machinery after the seam is proven, then enter K. Exact installation/release qualification remains L.

**D. Evidence reviewers should inspect**

Current CPM G18AN + Engineering Notes + this handoff, and current Animation Groups Master production Normalizer + runtime/broker/cohort/views/bootstrap + F/G/I/J evidence.

**E. Things that must not be reopened**

Do not reopen Normalizer F/G/I/J, RC7 transaction ordering, generic scaling, indexed Body capture, exact-set compatibility, rename identity, DME resolution, miss-only Review, structural Fit mapping, per-target transaction staging, modal scheduling, Qt row ownership, or the old Body Save performance investigation without contradictory evidence.

Both deliberate architecture challenges are resolved. This handoff is the controlling implementation specification.
