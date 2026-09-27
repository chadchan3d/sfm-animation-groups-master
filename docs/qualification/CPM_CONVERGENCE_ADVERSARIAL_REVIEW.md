> **Repository context (added by this checkpoint, not part of the original CPM document):** source repository `chadchan3d/sfm-character-preset-manager`, commit `390e01e` (`390e01eb7ac1ceb220e480126f40077703acb0f4`), original path `docs/reviews/CPM_CONVERGENCE_ADVERSARIAL_REVIEW.md`, source SHA-256 `06cf8b601e6079a6e58a1631704b5f4b9040247f78d2723be5eafd810d52318b`.
>
> This repository (`chadchan3d/sfm-animation-groups-master`) is now the continuing home of SFM Character Tools and CPM convergence. The CPM repository is closed at commit `390e01e` as a source archive; this supersedes any statement below that the CPM repository "remains canonical."
>
> "Shared authority remains unchanged" means the `sfm_master_authority_productionized` package in this repository stays byte-stable at its already-qualified build; CPM code is not added to that package.
>
> References below to CPM-repo paths map to their imported locations here: `README.md` is not imported and remains only in the closed CPM source archive; `docs/ENGINEERING_NOTES.md` -> `docs/qualification/CPM_ENGINEERING_NOTES.md`; `docs/DEVELOPMENT_HISTORY.md` -> `docs/qualification/CPM_DEVELOPMENT_HISTORY.md`; `docs/reviews/CPM_CONVERGENCE_ADVERSARIAL_REVIEW.md` -> `docs/qualification/CPM_CONVERGENCE_ADVERSARIAL_REVIEW.md`; `docs/SFM_CHARACTER_TOOLS_INTEGRATION_HANDOFF.md` -> `docs/qualification/CPM_CONVERGENCE_INTEGRATION_HANDOFF.md`; `src/SFM_CSP_G18AN_SaveNewCopy.py` is not imported and remains only in the closed CPM source archive.
>
> Everything below this line is exact imported content.

---

**Reviewer:** Astra
**Date:** 2026-09-26
**Reviewed pins:** CPM `2c905fb` / Master `9d200e3`
**Verdict:** ACCEPT WITH CORRECTIONS
**Status:** Incorporated into handoff at `d9563b4`

---

## 1. Overall verdict

**ACCEPT WITH CORRECTIONS.**

The proposed seam is sound:

> Unchanged canonical broker → CPM-owned `cpm_compat_v1` projection → exact-literal interpretation → existing CPM semantics.

I found **no correctness reason to move the CPM projection into the shared package** or change its qualified build.

However, the proposed lease-release boundary is not yet sufficiently precise. The source exposes four dependencies that implementation must address:

1. Clothing Fit queries **target vocabulary outside the selected character’s scope**.
2. Fit performs another semantic query during **post-stage verification**.
3. Apply’s postcommit and rollback verification revisit the current-provider helper.
4. Save and Review reach provider metadata through library-persistence helpers.

There is also a concrete correction to the parity plan: **G18AN cannot serve as the sole oracle for provider-native conflicts**, because its adapter rejects a result type its pinned provider actually returns.

I inspected the specified source checkpoints. This was a source review; I did not run SFM, modify either repository, implement migration, or begin K.

## 2. Consumer-owned builder verdict

**Safe as a trusted, qualified consumer extension—not as an automatically validated arbitrary plugin.**

The extension point is real:

- `Broker.acquire_or_reuse_views()` accepts a consumer key, requested folds and callback.
- `Broker.acquire_cohort()` forwards those folds into resource admission.
- `Cohort.build_projections()` invokes the callback with the temporary provider, takes H1, constructs detached views and closes the provider in `finally`.
- Nothing requires the callback’s implementation to reside inside the authority package. [Broker](https://github.com/chadchan3d/sfm-animation-groups-master/blob/9d200e324ed34f45d5001bad516840be8cb19e6f/tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/broker.py#L249), [cohort](https://github.com/chadchan3d/sfm-animation-groups-master/blob/9d200e324ed34f45d5001bad516840be8cb19e6f/tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/cohort.py#L108).

The important qualification is that the broker **does not deeply inspect the callback’s payload for detachment, completeness or truthful size estimation**. Those are consumer obligations.

The CPM builder must therefore:

- Query only its declared vocabulary.
- Return the canonical shared coverage types.
- Verify that requested folds, family rows and coverage keys agree.
- Distinguish `Hit`, `FoldConflict` and `MasterUnknown` explicitly; reject unexpected result types.
- Return ordinary detached data, without provider references, deferred iterators or lookup closures.
- Remain synchronous and avoid Qt event pumping.
- Propagate failure without publishing an apparently healthy partial result.

**Resource correction:** `estimated_bytes` should conservatively cover everything retained by the CPM view, including coverage storage—not merely `families_by_fold`. Avoid copying full occurrence dictionaries into coverage when a compact coverage result suffices. The broker trusts the supplied estimate when charging the cache. [Views](https://github.com/chadchan3d/sfm-animation-groups-master/blob/9d200e324ed34f45d5001bad516840be8cb19e6f/tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/views.py#L126), [cache admission](https://github.com/chadchan3d/sfm-animation-groups-master/blob/9d200e324ed34f45d5001bad516840be8cb19e6f/tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/view_cache.py#L92).

There is an intentional package dependency: CPM uses the pinned callback protocol, provider result shape, coverage classes and lease APIs. That justifies exact API/build verification; it does not justify moving CPM policy into the package.

## 3. Lease-release verdict by operation

**A lease controls ownership/accounting. It does not lock the Master or freeze authorization.** Extending a lease alone cannot solve a generation-change problem.

| Operation | Recommended release boundary | Required correction |
|---|---|---|
| **Body Save** | After current-generation authorization, membership resolution and capture of the descriptor needed for persistence; before durable writes. | Pass the pinned descriptor into character-library helpers. They must not reacquire the global provider later. |
| **Body Update** | After authorization and detached semantic/capture planning; before durable replacement. | Preserve the operation’s descriptor and accepted membership through write/readback. |
| **Body Apply** | Before native mutation **once a detached operation context also supports postcommit and rollback verification**. | Separate fresh DME verification from a new global-provider/freshness decision. |
| **Expression Save** | Same as Body Save, without bone capture. | Same persistence-descriptor correction. |
| **Expression Update** | Same as Body Update. | Same pinned-context requirement. |
| **Expression Apply** | Same as Body Apply. | Its postcommit and abort paths use the same problematic helper. |
| **Review/Reclassify** | Release the decision lease after proving current healthy-miss eligibility and capturing persistence facts. Acquire a separate short lease for the post-write scope rebuild. | Preserve “write committed” if later scope refresh fails or discovers changed authority. |
| **Clothing Fit** | **For the first migration, retain the target-stage lease through post-stage verification**, then release before scheduling the next target. | Cover target vocabulary and bind both planning passes to `Gfit`. No lease across queued stages or UI idle. |

### Why these boundaries differ

**Save has a late metadata dependency.** `prod_save()` reaches `prod_ensure_character()`, which calls `get_semantic_provider()` either through `prod_character_record()` or its update branch. Review uses the same helper. Those calls must consume the already-authorized operation descriptor rather than opening another authority path. [Library helpers](https://github.com/chadchan3d/sfm-character-preset-manager/blob/2c905fb35a927ab150dac41387ec11f3cce4d73a/src/SFM_CSP_G18AN_SaveNewCopy.py#L20065).

**Apply has late scope checks.** After `same_time_refresh()` processes events, Apply calls `prod_live_bindings_for_cached_scope()` again. Abort verification also calls it. That helper currently checks the global provider descriptor and returns the provider. An unconditional “refresh scope on mismatch” inserted there could interrupt verification of an already-committed or aborted transaction. [Apply readback](https://github.com/chadchan3d/sfm-character-preset-manager/blob/2c905fb35a927ab150dac41387ec11f3cce4d73a/src/SFM_CSP_G18AN_SaveNewCopy.py#L27579), [abort verification](https://github.com/chadchan3d/sfm-character-preset-manager/blob/2c905fb35a927ab150dac41387ec11f3cce4d73a/src/SFM_CSP_G18AN_SaveNewCopy.py#L27045).

The correction is narrow: verify fresh scene state against the **operation’s authorized membership and baselines**. Do not reinterpret that membership under G2 during recovery or readback. Preserve all existing native checks.

**Fit really performs another semantic lookup.** `fit_stage()` runs `g11a_safe_plan()` before mutation and again afterward. Both can call `p03_unmapped_relevant_controls()`, which queries unmatched target literals. Keeping one bounded stage lease through this second pass is simpler than prematurely introducing another detached verification representation. [Fit stage](https://github.com/chadchan3d/sfm-character-preset-manager/blob/2c905fb35a927ab150dac41387ec11f3cce4d73a/src/SFM_CSP_G18AN_SaveNewCopy.py#L33256), [target semantic query](https://github.com/chadchan3d/sfm-character-preset-manager/blob/2c905fb35a927ab150dac41387ec11f3cce4d73a/src/SFM_CSP_G18AN_SaveNewCopy.py#L7225).

## 4. Cache-identity verdict

**The fold-family design is correct.**

The actual key is:

```text
Master SHA
+ projection_contract_version
+ exact covered-fold set
+ consumer_kind
```

In this build, the generic projection-contract field is `None`; therefore **`cpm_compat_v1` is the effective CPM contract-version discriminator**. A v2 consumer key cannot hit a v1 entry. The builder’s code identity itself is not part of the cache key. [Cache key](https://github.com/chadchan3d/sfm-animation-groups-master/blob/9d200e324ed34f45d5001bad516840be8cb19e6f/tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/views.py#L191).

For same-fold/different-exact-query reuse:

- Family status, destinations, spellings and occurrence count are invariant.
- `query_literal` must come from the current live literal.
- `match_kind` must be recomputed against actual Master spellings.
- An exact spelling inside a conflicting family **remains a conflict**.

Additional constraints:

- Use one consistent folded-key representation across request specs, coverage and payload. For compatibility with the existing Python-2-facing admission helpers, **Unicode folded strings internally, explicitly encoded to UTF-8 for provider lookup**, is the least surprising choice.
- Preserve sorted, deduplicated spellings/destinations as G18AN does.
- Count all occurrences, not distinct spellings.
- Do not place Review choices, model identity or live representation in the shared family cache.
- Bump the consumer kind when cached family interpretation changes incompatibly.

## 5. Freshness/generation verdict

### Initial scope

Acquire the current authority, lease, verify authorization/coverage, materialize the pure scope, release, then publish.

The provider has already closed before acquisition returns. No window-owned provider is necessary.

### Later actions

The claimed cache-hit freshness proof is real: `acquire_or_reuse_views()` calls `observe_master()` before checking the cache and checks `expected_generation` on the entirely reused path. [Fresh observation and cache-hit check](https://github.com/chadchan3d/sfm-animation-groups-master/blob/9d200e324ed34f45d5001bad516840be8cb19e6f/tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/broker.py#L493).

But it proves the Master observed at that boundary. It is not a continuous watcher, artifact revalidation on every hit, or file lock.

**Place authorization after user prompts.** Save and Update currently check scope before opening a modal prompt, then revalidate scene context afterward. The latter does not prove authority freshness. The migration’s expected-generation acquisition belongs after prompt return and before semantic work. [Save prompt boundary](https://github.com/chadchan3d/sfm-character-preset-manager/blob/2c905fb35a927ab150dac41387ec11f3cce4d73a/src/SFM_CSP_G18AN_SaveNewCopy.py#L31992), [Update confirmation](https://github.com/chadchan3d/sfm-character-preset-manager/blob/2c905fb35a927ab150dac41387ec11f3cce4d73a/src/SFM_CSP_G18AN_SaveNewCopy.py#L32214).

### Open window, G1 → G2

Accept the proposed behavior:

1. Reject the old action before mutation.
2. Discard or disable the stale scope.
3. Attempt a current-generation scope rebuild.
4. Require a new user action.

If G2 has no usable sidecar, remain explicitly unavailable. Do not restore G1 as mutation authority or synthesize Review misses.

### Clothing Fit

The `Gfit` rule is sound, with these corrections:

- Keep `Gfit` separate from the existing integer `fit_generation`, which is a callback-cancellation identity.
- Discover the current target’s relevant vocabulary before its bounded acquisition.
- Cover source requirements **plus target requirements** under `expected_generation=Gfit`.
- Perform the check after any foreign-modal suspension ends.
- Verify the running target against its pinned plan.
- On mismatch before the next target, stop the remaining targets and retain truthful committed/unattempted accounting.

A source-only request is insufficient.

### Final hash-to-use interval

CPM’s writes do not invoke native Rebuild to reread the Master. Once a bounded operation is authorized, it can finish from pinned semantic facts.

Consequently, **do not copy Normalizer’s J protected-file-handle mechanism into CPM merely for symmetry**. Require fresh authorization at operation entry, no yield between authorization/planning and mutation entry, and no new interpretation after a yield. Readback and recovery remain tied to the completed operation.

## 6. Semantic-parity omissions and corrections

### A. The conflict oracle is incomplete

G18AN `_answer_from_result()` accepts `MasterUnknown` and `Hit`; it rejects other class names before its multiple-destination branch. Its pinned R1D provider—whose source hash matches the G18AN constant—returns `FoldConflict` for multiple destinations. [G18AN adapter](https://github.com/chadchan3d/sfm-character-preset-manager/blob/2c905fb35a927ab150dac41387ec11f3cce4d73a/src/SFM_CSP_G18AN_SaveNewCopy.py#L2496), [pinned R1D provider](https://github.com/chadchan3d/sfm-animation-groups-master/blob/9d200e324ed34f45d5001bad516840be8cb19e6f/tests/sidecar/qualification/candidate_packed_provider.py#L391).

Therefore:

- Ordinary valid answers should match G18AN.
- Provider-native conflict handling needs a hand-audited expected answer.
- Record this as an adapter-translation correction, not a taxonomy change.
- Do not claim the existing G18AN path already demonstrates successful native-conflict handling.

### B. Fit needs target-side semantic parity

Preserve the exact existing warning classification: unmatched target controls resolved to exact `Body Morphs` or `Clothing`. Do not broaden this to arbitrary descendants or omit it because correspondence itself is structural.

### C. Descriptor compatibility needs an explicit mapping

G18AN compares both `provider_generation` and source SHA in `prod_scope_matches_identity()`. Its numeric generation currently counts provider creation.

**Do not map that integer to broker cohort IDs, provider-open counts or artifact IDs.** Reopening the same semantic generation must not invalidate a scope. Use Master SHA plus CPM projection/policy identity for compatibility; keep any local counter diagnostic. Preserve provenance fields used by `prod_provider_capture()`. [Scope identity checks](https://github.com/chadchan3d/sfm-character-preset-manager/blob/2c905fb35a927ab150dac41387ec11f3cce4d73a/src/SFM_CSP_G18AN_SaveNewCopy.py#L19527).

### D. Signature parity includes more than classifications

Preserve literal, live-binding count, live shapes, ambiguity, status, match kind, path, destinations, spellings, class and operation—including deterministic ordering. `occurrence_count` belongs to answer parity but is **not currently part of `semantic_snapshot_signature()`**. Do not conflate those gates. [Snapshot and signature](https://github.com/chadchan3d/sfm-character-preset-manager/blob/2c905fb35a927ab150dac41387ec11f3cce4d73a/src/SFM_CSP_G18AN_SaveNewCopy.py#L3769).

### E. Reclassify can legitimately rebuild differently

After persistence, a newer authority may positively resolve the literal. The current assertion that it must return to `unresolved` cannot be treated as unconditional across generation changes. Report the successful durable edit separately from the resulting current-authority classification.

## 7. Classified findings

| Category | Finding | Why it belongs here |
|---|---|---|
| **CPM MIGRATION BLOCKER** | Target-aware Fit coverage and post-stage semantic lookup are unspecified. | A source-only view changes behavior or produces uncovered lookups. |
| **CPM MIGRATION BLOCKER** | Late provider access in Apply verification and persistence helpers. | A superficial provider replacement could mix generations or misreport committed work. |
| **CPM MIGRATION BLOCKER** | Post-modal authorization and stable descriptor-generation mapping. | Otherwise stale actions can proceed, or valid same-generation scopes can fail spuriously. |
| **CPM MIGRATION BLOCKER** | Callback completeness, detachment and accounting must be qualified explicitly. | The broker does not enforce these deeply on behalf of arbitrary callbacks. |
| **CPM MIGRATION BLOCKER** | Conflict qualification cannot rely solely on the existing adapter. | Its native-conflict path fails before producing the intended answer. |
| **IMPORTANT BUT DEFERRABLE** | Historical provider code and extensive diagnostics. | Keep isolated during migration; remove release ambiguity after the new seam passes. |
| **IMPORTANT BUT DEFERRABLE** | Aggregate CPM-scope plus Normalizer-cache resource qualification. | Required for K, not a reason to redesign the broker before CPM exists. |
| **NICE-TO-HAVE** | Tighten mismatch retry latency using existing bounded retry controls. | Improves responsiveness; does not alter the architectural verdict. |

“Detached” must not become an unbounded second cache. Retain the selected scope and bounded active-operation data; discard obsolete scopes and completed Fit-stage data. Clear released lease/view references as well: a released `ViewLease` still contains its `.view` reference.

## 8. Corrected minimum implementation sequence

1. **Implement the CPM-owned family projection and exact-answer interpreter.** Include descriptor mapping, strict coverage checks and complete retained-size estimation. Keep the shared package unchanged.
2. **Wire canonical bootstrap and initial scope construction.** Preserve a pure idle scope with no lease/provider. Make the old development provider unreachable from the migrated production route without deleting it yet.
3. **Introduce one CPM operation-authority context.** It carries generation, contract/policy identity, detached membership and provenance. Wire Save, Update, Apply and Review at their actual post-prompt boundaries; route late verification/persistence helpers through that context.
4. **Integrate Fit per target.** Include target vocabulary, pin `Gfit`, retain only the stage lease through verification, and release before the next timer turn.
5. **Run the focused qualification below, then clean historical authority paths and perform a narrow post-cleanup regression.**

This is a consumer migration, not a shared-runtime redesign.

## 9. Corrected minimum offline qualification

Consolidate the handoff’s twelve gates into four focused suites.

| Suite | Decisive proof |
|---|---|
| **Projection and semantic parity** | Unique, aliases, exact/folded queries, duplicate occurrences, non-ASCII/whitespace literals, absence, conflict and wrapper paths; same-fold/different-query reuse; v1/v2 separation; Python-2.7 snapshot/signature parity. Use an independent expected conflict fixture. |
| **Callback and ownership contract** | Actual broker invocation; declared/requested/covered vocabulary agreement; unsupported result, omitted coverage and builder exceptions fail closed; provider closed; no retained provider/result/iterator; conservative coverage-plus-payload accounting; deterministic lease release and durable release-failure handling. |
| **Action boundary routing** | For every requested operation, instrument authority calls and writes. After authorization, late persistence/readback/recovery must use the operation context. Prompt-time G1→G2 rejects before writes. No production fallback or old provider open. |
| **Fit continuation and failure** | Target-only folds are requested; post-stage verification uses Gfit; a changed generation before target two causes zero target-two writes; uncovered post-stage vocabulary fails rather than triggering an implicit G2 acquisition. Preserve commit accounting and cancel stale callbacks. |

Also verify canonical origin/API/build checks and identical bootstrap path calculation. These are targeted CPM entry-point tests, not another broker requalification campaign.

## 10. Corrected minimum real-SFM qualification

Use three controlled sessions or scenarios:

1. **Normal CPM operation through the new seam.** Build scope, exercise Body and Expression Save/Update, changed/no-op Apply, and Review/Reclassify. Confirm the expected semantic results, existing native outcomes, provider closure and no idle lease. Include a Fit target with relevant vocabulary absent from the source.
2. **Generation changes at real UI boundaries.** Change G1→G2 while CPM remains open and during a Save/Update prompt. Confirm refusal before writes, current-scope refresh and no replay. Include unchanged-membership versus changed-membership preset compatibility.
3. **Queued Fit transition.** Commit target one under G1; change authority before target two. Confirm target one’s truthful outcome/Undo, no target-two mutation, clean lease release and a later new Fit under G2.

In the failure qualification, include the already-outstanding forced rollback-verification failures for Apply and Fit. Exercise the new authority plumbing without redesigning or repeating the entire native transaction campaign.

Measure CPM’s actual new scope/projection retention and replacement peak during these runs. Broker accounting excludes CPM-owned scope copies; it cannot establish their cost by itself.

A single coexistence smoke check should confirm that CPM and Normalizer obtain the same runtime and broker. Broader alternation belongs to K.

## 11. What must wait for K

- Normalizer-first and CPM-first workflows.
- Repeated alternation with CPM remaining open.
- Cross-consumer generation replacement and failure recovery.
- Aggregate broker views **plus CPM scopes/plans**.
- Close ordering and cross-consumer eviction pressure.
- Representative combined animator workflows.

K should test the composed product, not repeat standalone projection parity.

## 12. What must wait for L

- Exact shipping layout and bytes.
- Clean install and update install.
- Duplicate/stale package detection from installed artifacts.
- Final package provenance and release hashes.
- Restart/reopen and shipping-byte coexistence.
- Focused regression after final cleanup/packaging.

Canonical import correctness is needed now; exhaustive installation qualification is appropriately deferred to L.

## 13. Existing evidence that must not be repeated

Do not reopen:

- Normalizer F optimization/resource disposition.
- G later-vocabulary service.
- I generation replacement.
- J native Master protection.
- CPM generic scaling and indexed Body capture.
- Structural/native Fit correspondence.
- Exact-set compatibility, rename identity or fresh DME resolution.
- RC7 transaction ordering and no-op-before-Undo.
- Modal scheduling and scalar Qt row ownership.

Current production source already imports and acquires the canonical broker; historical “not integrated” descriptions are superseded. [Production acquisition](https://github.com/chadchan3d/sfm-animation-groups-master/blob/9d200e324ed34f45d5001bad516840be8cb19e6f/audit_external_runtime/Rebuild_Control_Groups_Normalizer.py#L10059).

The new proof obligation is that **CPM’s adapter and lifetime choices preserve those established mechanics**.

## 14. Go/no-go criterion for beginning CPM implementation

**GO for CPM implementation incorporating these corrections.**

No additional broad architecture investigation or shared-package modification is required first.

The implementation must explicitly include:

- target-aware Fit coverage;
- operation-bound authority/provenance for late helpers;
- post-prompt generation checks;
- no same-generation invalidation from provider/cohort counters;
- independent native-conflict expectations;
- bounded detached ownership and complete view accounting.

**Do not begin K or promote the migrated CPM until those points pass the focused qualification.** The standalone CPM repository remains canonical until a qualified successor exists.

**Confidence: high** in the migration seam and identified source dependencies; runtime latency, retained memory and Qt-boundary behavior remain qualification results to obtain, not conclusions of this static review.