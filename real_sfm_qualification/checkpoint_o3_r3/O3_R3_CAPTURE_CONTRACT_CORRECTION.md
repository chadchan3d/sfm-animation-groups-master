# O3-R3 — Capture Contract Correction

**Status: DESIGN/PROOF CORRECTION ONLY.** No production, integration, or lifecycle code has been modified.
This document removes the superseded detached/cached rig-name proposal from `O3_R1_CORRECTED_SUBSTITUTION_
DESIGN.md` section 6 and restates the capture contract in terms consistent with this checkpoint's own
final decision.

## What is removed

`O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md` section 6 ("Live `rig` capture contract — resolved") listed, as
one of three evaluated candidates, "Separate `rig_name` acquisition from the rest of discovery (carry
forward just the string)" — i.e., detaching and caching a plain string produced by `name(rig)` at native
POST, to be reused at composer-before instead of recomputing it. That document did not select this
candidate as primary, but retained it as a "minor refinement." **This candidate is superseded and should no
longer be read as live.** Reason: `O3_R3_FAILURE_CONTRACT_CORRECTION.md` correction 6 establishes that
composer-before's own captured snapshot (`before`, including its `rig_name` field) is never subsequently
consumed by production at all — caching or freshly computing this specific string makes no observable
difference to anything production does with it. Proposing to optimize its acquisition path is therefore
moot, not merely deprioritized, and the prior document's framing of it as a "minor refinement" worth
retaining should be dropped rather than carried forward.

## Corrected statement of the capture contract

`capture_snapshot_explicit(shot, aset, label, rig_context)`'s only use of `rig_context["rig"]` remains
exactly as `O3_R1_DISCOVERY_CAPTURE_CONTRACT.md` established: one `name()` call (line 3661-3667) to produce
the `rig_name` field. `rig_context["registry"]` remains never dereferenced. **This part of the prior
analysis is unchanged and correct.**

Since this checkpoint's own final decision is `DO_NOT_IMPLEMENT` (see
`O3_R3_ENUMERATION_VALIDITY_DECISION.md`), no live current rig is retained by anything this checkpoint
authorizes. For completeness, and to leave a clean record for any future reconsideration: **had** a design
survived, the correct framing (not the superseded one above) would have been:

- Retain a live current rig only for the bounded, immediate capture use described above — never as a
  general-purpose cached identity.
- Execute `name(rig)` fresh at the point of use, not detached/cached ahead of time — since
  `O3_R3_FAILURE_CONTRACT_CORRECTION.md` correction 5 establishes `name()` degrades silently
  (`u"<UNNAMED>"`) on failure rather than raising, a *cached* string computed earlier would not even carry
  the same failure-detection value a fresh call provides at the point of actual use; caching it forfeits
  information rather than merely re-deriving something equivalent.
- Leave `capture_snapshot_explicit()`'s own semantic behavior completely unchanged — no signature change,
  no new parameter, no `None`-substitution path. This remains unmodified from every prior O3-series
  document's own position.
- Capture compatibility remains conditional on independently establishing the current correct rig through
  whatever validation sequence precedes the capture call — which is exactly the property
  `O3_R3_COUNTEREXAMPLE_ANALYSIS.md` shows cannot be established for any evaluated reuse-object archetype.

## Consequence

This document leaves no competing capture-contract proposal in force. The only capture-contract fact that
survives this checkpoint is the original, already-verified one (`O3_R1_DISCOVERY_CAPTURE_CONTRACT.md`'s own
finding about the single `name()` use and the never-dereferenced `registry`) — it requires no further
action because no reuse design is being pursued.
