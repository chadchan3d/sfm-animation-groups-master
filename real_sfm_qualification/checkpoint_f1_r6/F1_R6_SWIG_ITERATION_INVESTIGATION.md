# F1-R6 — Phase C: DME/SWIG Iteration Options Investigation

**Status: STATIC INVESTIGATION ONLY.** No production code has been modified. Investigated against the real
Python 2.7.5 SFM/datamodel bindings actually bundled with this SFM install
(`sdktools/python/2.7/win32/Lib/site-packages/vs/datamodel.py`) and this project's own accumulated
evidence of what the production Normalizer actually uses. Examples given by the requesting instruction are
treated as examples only — nothing below is invented; every mechanism cited is confirmed present in the
real bundled bindings.

## What the production Normalizer actually uses today

Confirmed by exhaustive grep across the entire pinned production source: the **only** iterator-style
mechanism ever used is `FirstAttribute()`/`NextAttribute()` (lines 941-964, `iter_attributes()`), consumed
by `element_ref_pairs()` (966-1004) to enumerate one element's own attributes one at a time — already a
streaming primitive, not a materializing one. Indexed array access (`Count()` + `a[i]`/`GetValue(i)`) is
used by `arr()` (895-927) for named array-typed attributes. No other iteration mechanism (visitor,
enumerator, native tree-walker) is used anywhere in this codebase's own history.

## Mechanisms confirmed present in the real bundled bindings, not previously used by this codebase

### 1. `CElementTreeTraversal` (a dedicated native tree-iterator class)

Confirmed present (`vs/datamodel.py`, ~line 3140-3170):

```
Reset(pRoot, pAttrName)   -- initialize/reset the traversal at a root, along a named attribute
IsValid()                 -- whether the traversal currently points at a valid element
Next(bSkipChildren=False) -- advance and return the next CDmElement directly
CurrentDepth()            -- current depth in the walk
GetElement()              -- the current element
GetParent(i)              -- an ancestor at a given depth
GetChildIndex(i)          -- child index at a given depth
```

`Next()` is a **true streaming iterator protocol**: one call returns one element; the caller can inspect
and discard it before calling `Next()` again, without ever building a Python list of every visited element.
This satisfies Phase C's own "iterator-like access" / "visitor-style traversal" categories directly, and is
a genuinely lower-level mechanism than anything this codebase has used before.

**Why this is not adopted as F1-R6's own prototype, despite being promising**: `Reset()` takes a specific
`pAttrName` — a single **named** attribute to traverse along. `reachable()`'s own actual semantics (via
`element_ref_pairs()`) generically follow **any** attribute whose *type* is `element` or `element_array`,
regardless of its name — a materially different, broader traversal scope. This project has no SDK
documentation establishing whether `CElementTreeTraversal` can be configured (via some other call not
captured by this stub's own docstring, or via a wildcard/empty `pAttrName`) to reproduce that same
"follow every element-typed attribute, whatever its name" semantics, or whether it is intentionally scoped
to a single named containment hierarchy (e.g., a control-group child tree) for a narrower, different
purpose than `reachable()`'s own general graph walk. **Using it without first proving this equivalence
would risk silently narrowing or widening what `reachable()` actually visits — an exact-parity violation
Phase E/G explicitly forbid.** This is recorded as a genuine, promising lead for a **future, separately-
scoped investigation** (verifying `pAttrName`'s own exact semantics against further evidence this project
does not currently have), not adopted here. Classified `MEASUREMENT_CANDIDATE` / `UNKNOWN` (promising
mechanism exists; its exact equivalence to `reachable()`'s own scope is unverified) — not
`PROVEN_REDUNDANT_MATERIALIZATION` and not adopted as this checkpoint's own streaming design.

### 2. `FirstAttributeReferencingElement` / `NextAttributeReferencingElement` / `GetAttributeFromIterator`

Confirmed present (`vs/datamodel.py`, ~line 1361-1371) on `IDataModel` itself (`vs.g_pDataModel`):

```
FirstAttributeReferencingElement(hElement) -> DmAttributeReferenceIterator_t
NextAttributeReferencingElement(hAttrIter) -> DmAttributeReferenceIterator_t
GetAttributeFromIterator(hAttrIter)        -> CDmAttribute
```

This is a **reverse-reference lookup**: given a specific element's handle, enumerate every attribute
*anywhere in the datamodel* that references it — the opposite direction of `reachable()`'s own forward
walk. In principle, this could answer "what points to this `aset`?" directly, without any whole-scene
forward traversal at all — directly relevant to `F1_R5_ALLOCATION_TRAVERSAL_AUDIT.md`'s own item 11
("target identity is already known at call sites but discovery nevertheless rebuilds a whole-session
search structure"), previously classified `UNKNOWN` for lack of evidence such a mechanism existed.

**This finding upgrades that prior `UNKNOWN` from "no evidence of any such mechanism" to "a candidate
reverse-lookup mechanism is confirmed to exist in the bindings" — but this checkpoint does not pursue it.**
Reasons, stated plainly:

1. This would be a **fundamentally different algorithm** (reverse-reference lookup replacing forward
   whole-scene search), not a streaming rewrite of the *same* algorithm — outside F1-R6's own explicit
   governing mandate ("fresh streaming observation," not an algorithm change).
2. It would require separately re-proving every correctness property the current forward search provides
   by construction: does it reliably enumerate **every** referencing attribute datamodel-wide, or only
   within some scope? Does it distinguish a genuine `DmeRigAnimSetElements` binding reference from any
   other, unrelated attribute that happens to reference the same `aset` (there is no evidence either way)?
   Would `reachable_rig_count` — currently "how many `DmeRig` objects exist anywhere in the reachable scene
   graph," a property of the *scene*, independent of this specific `aset` — even remain a meaningful
   quantity under a reverse-lookup design, since reverse lookup could only ever report rigs that reference
   *this* `aset`, not the total scene-wide `DmeRig` population?
3. None of this can be resolved from this project's currently available evidence (no SDK schema
   documentation, no prior exercise of this API anywhere in this project's history).

**Classification: `UNKNOWN`, explicitly not pursued.** Recorded here as a legitimate, evidence-grounded
lead for a possible future, separately-authorized investigation — not something F1-R6 implements, prototypes,
or recommends adopting now.

### No other mechanism found

Exhaustive search of the bundled stub for `First*`/`Next*`/`Visit*`/`Enumerate*`/`GetIterator*`-named
methods surfaces exactly the four already discussed (`FirstAttribute`/`NextAttribute`,
`FirstAttributeReferencingElement`/`NextAttributeReferencingElement`, and the `CElementTreeTraversal`
class's own `Next()`) plus `FirstAllocatedElement`/`NextAllocatedElement` (module-level, datamodel-wide
allocation iteration — used elsewhere in this project's own diagnostics, e.g. `cleanEmptyControls.py`'s own
reference usage cited in F1-R2's own audit — but this walks **every allocated element in the entire
process**, not scoped to a scene/root at all, and is not a candidate for a scene-scoped traversal). No
other iteration mechanism is invented or assumed here.

## Evaluation against Phase C's own required properties, for the mechanism actually adopted (Phase D)

The design adopted in `F1_R6_STREAMING_DESIGN_AND_EQUIVALENCE_CONTRACT.md` does **not** introduce any new
low-level API — it restructures the *existing* `reachable()` traversal (same `stack`, same `seen`-handle
set, same `element_ref_pairs()`/`iter_attributes()` chain, same `FirstAttribute()`/`NextAttribute()`
primitive already in use) to classify each object immediately upon visiting it, rather than first
collecting all of them into a persistent list. Since this reuses the exact mechanism already fully
understood and exercised by this project (no new API surface), every property Phase C asks about is
answered by the existing analysis in `F1_R6_CONTRACT_AND_ALLOCATION_AUDIT.md`'s own Phase A section:

- **Still creates a SWIG wrapper per visited element?** Yes — unavoidable; every visited element must be
  inspected (`typ()`, and for `DmeRig`-typed candidates, `HasAnimationSet()`), which requires a wrapper.
  This design does not reduce wrapper *construction* count, only wrapper *retention* (simultaneous
  materialization in a persistent list).
- **Permits the wrapper to fall out of scope immediately?** Yes, for every non-matching object (the large
  majority) — this is the entire point of the redesign.
- **Requires a persistent Python collection?** No, for the traversal frontier's own membership testing
  (`seen`, already a cheap `int`-keyed set); the `stack` itself remains a small, bounded-depth transient
  list (traversal frontier, not accumulated results).
- **Preserves traversal order?** Yes, identical (same stack/pop/push structure, same child-enumeration
  order).
- **Preserves exception behavior?** Yes, identical (same per-object/per-edge `try/except` granularity).
- **Permits exact duplicate/cycle detection?** Yes, identical (`seen`-handle set, unchanged).
- **Permits complete ambiguity checking?** Yes — count-based tracking (see Phase D) still visits and
  classifies every reachable object exactly once, preserving the "must see every candidate" requirement
  the ambiguity check structurally needs.
