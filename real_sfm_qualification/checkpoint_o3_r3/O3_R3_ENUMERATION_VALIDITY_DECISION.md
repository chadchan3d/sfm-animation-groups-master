# O3-R3 — Enumeration Validity Decision (Summary)

**Status: O3-R3 — ENUMERATION VALIDITY DECISION — COMPLETE.** No production, integration, or lifecycle
code has been modified. No SFM was run. No timing campaign was run. No optimization is implemented or
authorized by this checkpoint. F1-R2 remains parked/unrun. Checkpoint G was not prepared.

## Why this checkpoint exists

Astra's second independent review of O3 (after O3-R2's real-SFM measurement) returned
`REVISE_BEFORE_IMPLEMENTATION` again. O3-R2 materially validated the optimization's theoretical opportunity
— that dispute is closed, and no further timing measurement is authorized or needed. What remains open is a
single, narrower architectural question, stated exactly as Astra posed it:

> Is there an existing, cheap, authoritative mechanism or provable interval property that establishes that
> the native-POST rig candidate enumeration remains complete and applicable at composer entry?

## Astra findings preserved (unchanged, restated)

O3-R2 materially validated the optimization opportunity; no additional cost-split benchmark is needed;
approximate measured opportunity is ~0.202 s per applicable target in the bounded fixture; fresh
registry/ownership/hiddenGroups validation is not sufficient to prove candidate completeness; the remaining
defect is enumeration validity, precisely: "establish that the reused enumeration is still complete and
applicable to this shot and target at composer entry."

## What this checkpoint did

1. **`O3_R3_REUSE_OBJECT_DECISION.md`** — resolved the reuse-object ambiguity Astra identified between
   O3-R1's prose (a single already-identified candidate rig) and O3-R2's own measurement (the complete
   `reachable(scene)` object list, up to ~4,250 live wrappers in this fixture). The two are materially
   different designs; O3-R2's measured quantity — the larger, higher-risk one — is the one actually
   validated by real numbers and is therefore the one evaluated going forward. Both archetypes share the
   same structural defect: each is a stale, point-in-time snapshot of "what `reachable(scene)` returned at
   native POST," and no amount of fresh re-validation of members *already in* that snapshot can detect
   objects that were never enumerated into it.
2. **`O3_R3_ENUMERATION_VALIDITY_MECHANISM_SEARCH.md`** — searched the production source, this codebase's
   entire historical `g_pDataModel`/`DataModel` API surface (four methods, all undo-related), and this
   project's complete accumulated evidence base for any existing generation/revision/serial/dirty-flag
   mechanism. **None found.** Every candidate actually present in this codebase (`PRODUCTION_REVISION`, the
   authority broker's Master-hash-based generation, the undo-related `dm` methods) is classified
   `INSUFFICIENT` for this question; no candidate reaches `AUTHORITATIVE`. Per explicit instruction, none
   is invented to fill the gap.
3. **`O3_R3_INTERVAL_IMMUTABILITY_PROOF.md`** — re-traced the correct, full native-POST → composer-before
   interval directly against source (larger than O2-R1's own original proof examined: 15 `self.log()`
   calls, each calling `sys.stdout.write()`, plus 4 additional native getter calls not previously
   itemized). Confirmed, source-proven and unchanged: no explicit DME write, native Rebuild, Qt-yield, or
   Undo transition anywhere in this interval. **Not** established, at either the source or runtime-contract
   level: whether `sys.stdout.write()` or any native getter call in this interval can internally pump Qt
   events or reenter Python — this remains `UNRESOLVED`, and per explicit instruction, prior stability
   across every real-SFM run this project has performed does not count as proof.
4. **`O3_R3_COUNTEREXAMPLE_ANALYSIS.md`** — mechanically applied Astra's six hypothetical cases to the
   chosen reuse object. **All six fail.** Cases A, C, and E require re-walking the current reachable set to
   detect — a retained snapshot is structurally blind to them regardless of how thoroughly its own members
   are re-validated. Case D shows the reused design would **silently proceed to write** in a scenario where
   today's actual production code would raise and abort first — a genuine safety regression, not merely a
   missed optimization. Case F shows the retained native wrapper's own failure mode (`handle()` has no
   internal exception protection, unlike `typ()`/`name()`) carries unbounded severity — potentially a
   memory-safety hazard, not just a wrong answer.
5. **`O3_R3_FAILURE_CONTRACT_CORRECTION.md`** — corrected `O3_R1_PREWRITE_FAILURE_CONTRACT.md` and the
   branch-map description per Astra's specific list: `HasAnimationSet()` exceptions are caught, not
   propagated; the binding-handle comparison at line 3367-3373 treats a failure as `False`, not a
   propagated exception; some registry-element `handle()` failures are individually skipped, not
   propagated; some `arr()`/`handle()` calls do still genuinely propagate raw (unchanged from before);
   `name()` catches and yields `u"<UNNAMED>"`; composer-before's own discovery result (`before`/`before_rig`)
   is **never subsequently checked or consumed anywhere** in `production_generic_composer()` — a new
   finding, established this turn by direct exhaustive tracing, not previously documented; a PRE discovery
   failure is a graceful, fully-anticipated fallback (native Rebuild still runs, `NativePostFallback` is
   caught by a single well-defined handler) — not a hard abort as any prior looser description might imply;
   the actual first potential composer mutation boundary is `production_ensure_group_path()`'s own
   group-creation branch (line 6691-6743), confirmed by direct tracing of `production_generic_composer()`'s
   full body.
6. **`O3_R3_CAPTURE_CONTRACT_CORRECTION.md`** — removed the superseded detached/cached-`rig_name` proposal
   (moot, not merely deprioritized, since composer-before's own captured value is never consumed by
   production at all) and restated the capture contract in terms consistent with this checkpoint's final
   decision.

## Section 7 — lifetime constraint

Addressed within `O3_R3_REUSE_OBJECT_DECISION.md`'s own final section: no retention lifetime is authorized,
since the final decision below is `DO_NOT_IMPLEMENT`. The specification of what a surviving design *would*
have required (acquisition point, release point, both cleanup paths, no cross-target survival) is recorded
there for completeness only.

## Section 8 — complexity gate, applied

**Do not build a new generalized scene-topology observer, invalidation bus, persistent cache, mutation
tracker, or framework to save approximately 0.2 s per applicable target.** This checkpoint's own findings
make clear that closing the enumeration-validity gap without such new architecture is not possible with
what currently exists: no authoritative mechanism exists (item 2 above), and no immutable-interval proof
exists (item 3 above). Both required routes are closed. Building a new mechanism to manufacture either would
itself violate this gate.

## Section 9 — final decision

### `DO_NOT_IMPLEMENT`

No cheap authoritative enumeration-validity mechanism exists in this codebase or this project's evidence
base, and no provable immutable interval exists between native POST and composer-before. The counterexample
analysis independently confirms the gap is not closeable by any degree of fresh re-validation of a retained
object, for any of the reuse-object archetypes considered — the defect is structural, not an implementation
detail. Per explicit instruction, this is an acceptable and expected outcome, not a failure of this
investigation. **Production retains fresh composer-before discovery, unmodified, exactly as it exists
today.**

This decision applies specifically and only to the sole candidate this entire O3 series has ever
considered: outer native POST → composer-before discovery substitution, on the supported-active-rig
composer-entry path. Terminal reuse remains separately deferred and unaddressed, as it has been throughout
this entire series — this decision does not reopen or resolve that question, which was never in scope for
any O3-series checkpoint after O3-R1's own explicit deferral.

## Frozen invariants (unchanged, restated)

Everything every prior checkpoint's own frozen list already covered remains frozen and is now, additionally,
confirmed as the **permanent** state for this specific candidate rather than a temporary one pending further
measurement: native Rebuild, PRE eligibility, native guards, Master protection/validation, authority lease,
classification/planning, destination ordering, isolation, target callback guards/re-resolution, failure
behavior (now corrected in finer detail, not changed in substance), native-only fallback correctness,
terminal validation, no runtime DME cache. No warm-path shortcut. No stale semantic cache. No F1-R2. No
Checkpoint G.

## What happens next

Nothing, without separate explicit authorization. This specific optimization candidate (outer native POST →
composer-before discovery reuse) is closed as `DO_NOT_IMPLEMENT`. Should a future authoritative mechanism
become known (e.g., through genuine SFM SDK documentation this project does not currently have access to),
this decision could be revisited from `O3_R3_ENUMERATION_VALIDITY_MECHANISM_SEARCH.md`'s own starting point
— but nothing in this checkpoint proposes seeking that out as a project activity.
