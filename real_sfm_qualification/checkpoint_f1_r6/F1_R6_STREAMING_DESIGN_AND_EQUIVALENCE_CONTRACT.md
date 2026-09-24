# F1-R6 — Phase D/E: Streaming Design and Formal Equivalence Contract

**Status: DESIGN/PROOF ONLY.** No production code has been modified. This is not authorization to modify
production. The candidate below is FRESH STREAMING OBSERVATION, not cached discovery: it performs the
exact same live traversal, every time, from scratch — nothing is reused across calls, no topology is
cached, no handle is trusted as still valid without being freshly re-observed.

## Phase D — minimum safe streaming design

### What is fused, and why it is safe to fuse

Per `F1_R6_CONTRACT_AND_ALLOCATION_AUDIT.md`'s own Phase A #13, `discover_rig_context()` makes **exactly
one pass** over `reachable()`'s own returned list, and every downstream consumer needs only `len()` and
(once uniqueness is confirmed) the single `[0]` element from `rigs`/`matches`/`registry_matches`. This
satisfies Phase D's own explicit precondition ("mechanically convert... unless all downstream multi-pass
semantics have been accounted for" — confirmed: there is no second pass over the reachable-object list to
account for).

The candidate fuses `reachable(scene)`'s own traversal with the immediately-following `for obj in objs: if
typ(obj) != "DmeRig": continue; ...` filter loop into **one** traversal: each object is classified
(`typ()`, and for `DmeRig` matches, `HasAnimationSet(aset)`) the instant it is popped from the stack and
confirmed newly-seen, instead of first being appended to a persistent list for a later, separate pass.

`rigs`/`matches`/`registry_matches` (each only ever read via `len()` and `[0]`) become **count + first-
match reference** pairs: a plain integer counter, plus a single retained object reference for the *first*
match only. Any *subsequent* match's own wrapper is inspected (to confirm ambiguity) and then immediately
discarded — never appended anywhere. This is exactly the "count / first candidate / second candidate /
ambiguity bit" reduction Phase D itself suggests, and it produces **exactly** the same decision
(`count == 1` vs. `count != 1`) and, when unique, the identical object reference legacy would have selected
(`matches[0]`), with a strictly smaller simultaneous retention footprint in the ambiguous case, and an
identical footprint in the (overwhelmingly common) unique case.

### What is explicitly NOT fused

- `arr(rig, "animSetList")`'s own registry-record loop uses the same count+first pattern (small-scale, not
  command-scale on its own — included only for design consistency, per `F1_R6_CONTRACT_AND_ALLOCATION_
  AUDIT.md`'s own Phase B classification).
- `control_objs`, `control_handles`, `registry_handles`, `owned_handles`, `owned_names`,
  `arr(registry,"hiddenGroups")` are copied **unchanged, verbatim** from legacy — each is either genuinely
  multi-pass (`control_objs`, read twice) or already small-scale/scalar, per Phase B's own classification.
  Nothing here is touched.
- The returned `rig`/`registry` live-wrapper fields are retained exactly as legacy does. Per explicit
  instruction ("do not exploit [the O3-R1 finding that only a derived string is needed] unless current
  source confirms the complete consumer contract"), this candidate does **not** attempt to replace them
  with pre-derived strings — that would require re-verifying every caller's own complete contract, which
  this checkpoint does not do.

### Exact candidate pseudocode (implemented verbatim in `F1_R6_Discovery_Streaming_Prototype.py`)

```
def reachable_classify_rigs_streaming(start, aset, max_elements=50000):
    stack = [start]; seen = set()
    visited_count = 0
    reachable_rig_count = 0
    matching_rig_count = 0
    first_match = None
    while stack:
        obj = stack.pop()
        try: h = handle(obj)
        except Exception: continue
        if h in seen: continue
        seen.add(h)
        visited_count += 1
        if visited_count > max_elements:
            raise ProbeError("DME traversal exceeded safety cap.")
        if typ(obj) == u"DmeRig":
            reachable_rig_count += 1
            try:
                if bool(obj.HasAnimationSet(aset)):
                    matching_rig_count += 1
                    if matching_rig_count == 1:
                        first_match = obj
            except Exception:
                pass
        for unused_attr, child in element_ref_pairs(obj):
            try: ch = handle(child)
            except Exception: continue
            if ch not in seen:
                stack.append(child)
    return reachable_rig_count, matching_rig_count, first_match
```

`discover_rig_context_streaming(shot, aset)` calls this helper in place of `reachable(scene)` + the filter
loop, then proceeds with **legacy's own unmodified code, verbatim**, for every step from `rig =
matches[0]`-equivalent onward (registry search using the same count+first fusion; everything after that
copied unchanged).

## Phase E — formal equivalence contract

Candidate streaming discovery is required to be equivalent to legacy discovery for:

1. **Status/result classification** — identical status string for every input, by construction (same
   branch conditions, evaluated against the same counts).
2. **Rig existence/nonexistence** — `matching_rig_count == 0` triggers `UNRIGGED` identically.
3. **Selected rig identity** — when `matching_rig_count == 1`, `first_match` is the *same* object reference
   `matches[0]` would have been (both are "the first, and only, `DmeRig`-typed object found via this
   traversal that has `HasAnimationSet(aset) == True`" — traversal order is unchanged, so "first" means the
   same object in both designs).
4. **Registry result** — identical, same count+first fusion, same underlying `arr(rig,"animSetList")` read.
5. **Duplicate/ambiguity failure** — `AMBIGUOUS_MULTIPLE_RIGS`/`AMBIGUOUS_RIG_REGISTRY` trigger under
   exactly the same count conditions; the specific **asymmetry** already documented in Phase A (rig/handle
   fields left `None` for `AMBIGUOUS_MULTIPLE_RIGS` but set for `AMBIGUOUS_RIG_REGISTRY`) is preserved
   exactly, since the candidate's own branch structure mirrors legacy's line-for-line at these points.
6. **Ownership determination** — unchanged code, verbatim.
7. **Target association** — unchanged (`aset` is the same parameter, used identically).
8. **Exception/fail-closed behavior** — every per-object/per-edge `try/except` granularity is preserved
   exactly (same catch scopes as legacy's own `reachable()`/`element_ref_pairs()`/`iter_attributes()`); the
   top-level `RIG_TRAVERSAL_FAILED` catch around the fused traversal call mirrors legacy's own catch around
   `reachable(scene)`.
9. **Traversal completeness** — every object legacy's own `reachable()` would visit, the candidate also
   visits (identical stack/seen/child-enumeration structure) — confirmed by Phase G's own adversarial
   parity suite, not merely asserted here.
10. **Live-state freshness** — the candidate performs a full, live traversal on every single call, with zero
    caching, zero reuse of any object or handle across calls, and zero assumption that any previously-
    observed topology remains valid. This is the central, non-negotiable property this whole checkpoint
    exists to preserve.
11. **All supported model categories** — the candidate makes no model-specific assumption anywhere;
    identical to legacy in this respect by construction (no code path is model-aware).
12. **Branch decisions used by production** — `run_target_transaction()`'s own branch logic reads only
    `status`, `rig_handle`, `owned_names_in_order`, `hidden_groups` from the returned dict (already
    established across F1-R3/F1-R4/F1-R5's own audits) — all populated identically by the candidate.

### Distinguishing exact-error-text/order parity from behavioral parity

Exact **error text** for the two Category-2 raw exceptions (`arr()`'s own `"Cannot read %s[%d] on %r."`,
`handle()`'s own bare propagation) is unaffected by this candidate — those call sites are in the
**unchanged** portion of the function (registry/ownership derivation), not touched by the fusion. Exact
**visitation order** among sibling attributes is preserved (same `element_ref_pairs()` call, same
argument, same iteration). No error text or ordering is silently changed anywhere; this is confirmed, not
merely assumed, by Phase G's own parity suite comparing full result dicts, not just status strings.

## Known unresolved risks — disclosed, not hidden

1. **Interleaved native calls during an ongoing traversal.** The fused design calls `typ(obj)` and, for
   `DmeRig` candidates, `obj.HasAnimationSet(aset)` *while the stack-based traversal is still in progress*
   (between processing one object and pushing/popping the next), whereas legacy calls `typ(obj)` only
   *after* `reachable()`'s own traversal has fully completed and returned. **This is not, however, a new
   category of risk**: legacy's own `reachable()` already interleaves multiple native calls with ongoing
   traversal (`handle(obj)`, and via `element_ref_pairs()`/`iter_attributes()`, `FirstAttribute()`/
   `NextAttribute()`/`a[i]`/`GetValue()`/`GetValue(i)` — all native, all already happening between stack
   pushes/pops in the unmodified, currently-shipping code). The fused design adds two more native calls
   (`typ()`, `HasAnimationSet()`) to that already-interleaved set — a quantitative increase in how many
   native calls occur during the walk, not a qualitatively new exposure. Whether **any** of these native
   calls (old or new) can trigger reentrant scene mutation remains `UNRESOLVED`, exactly as classified
   throughout the O3 series (`O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md` section 7) — this checkpoint does not
   resolve it, and does not depend on resolving it, since the candidate performs a genuinely fresh
   traversal every call regardless (see freshness property #10 above) — an argument structurally identical
   to O3-R1's own reasoning for Option C, applied here to a design that (unlike Option C) is never
   authorized for production use by this checkpoint in the first place.
2. **`CElementTreeTraversal`'s own unverified scope semantics** (see
   `F1_R6_SWIG_ITERATION_INVESTIGATION.md`) — not used by this candidate, recorded only as a future lead.
3. **`FirstAttributeReferencingElement`'s own unverified reverse-lookup completeness/scope** (see the same
   document) — not used by this candidate, recorded only as a future lead, explicitly not pursued because
   it would be a different algorithm, not a streaming rewrite of the same one.
4. **CPython-level object lifetime**: even with fusion, Python's own reference-counting means a discarded
   wrapper is not necessarily *instantly* reclaimed at the OS/process level (the same `pymalloc`-arena
   caveat `F1_R5_ALLOCATION_TRAVERSAL_AUDIT.md` already discloses) — this checkpoint's own Phase H resource
   measurement, if justified, is what determines whether the reduced *peak simultaneous* retention actually
   translates into a measurable process-level improvement; this document does not assume it does.
