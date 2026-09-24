# F1-R7 — Lower-Level Fresh Traversal / Wrapper-Churn Feasibility Audit

Static, read-only audit. **No production modification. No real-SFM run performed for this
checkpoint.** All evidence below is cited directly from the real, installed SWIG-generated Python
binding stub actually shipped with this SFM install:

```
E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\sdktools\python\2.7\win32\Lib\site-packages\vs\datamodel.py
```

No C++ engine source or header files are present anywhere in this SFM installation (confirmed by a
recursive search for `*.h` under the install root — the only `.h` files found belong to an unrelated
bundled `lxml` library). Every claim below is therefore either (a) a direct citation of the Python
stub's own docstring/signature (which SWIG generates mechanically from the real C++ signature, so
argument/return **types** are reliable), or (b) an explicitly labeled inference where the stub alone
is insufficient to prove behavior, with the reasoning shown.

## 0. F1-R6 formal closure (performed first, as instructed)

Ran the accepted `F1_R6_Compare_Legacy_vs_Streaming_Results.py` (SHA-256
`5d155f68fa5598c6a255b7b07a2981b22376d0c506c04ace5efd549cd7cf2d8e`) against the two real artifacts
returned by the operator:

- `C:\Users\Public\Documents\sfm_checkpoint_f1_r6_legacy_result.json`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r6_streaming_candidate_result.json`

Result: **`OVERALL_COMPARISON_PASS=True`**. All 13 mechanical checks PASS, including
`parity.62_of_62_target_identity_and_order_match`, `parity.zero_semantic_mismatches -- (62, 0)`, and
`parity.branch_relevant_status_distribution_matches -- ({SUPPORTED_ACTIVE_RIG: 32, UNRIGGED: 30},
{SUPPORTED_ACTIVE_RIG: 32, UNRIGGED: 30})`. Independently re-derived `derived_metrics` from the
comparator's own arithmetic, cross-checked against the relayed numbers, bit-for-bit:

| Metric | Value |
|---|---|
| `candidate_private_reduction_bytes` | `3,735,552` |
| `candidate_private_reduction_ratio` | `0.05673758865248227` (5.6738%) |
| `candidate_free_vas_improvement_bytes` | `-5,242,880` (candidate worse by 5 MiB) |
| `candidate_largest_free_improvement_bytes` | `0` |
| `candidate_elapsed_reduction_seconds` | `-1.0870001316070557` (candidate ~4.36% slower) |

Additionally, independently computed (not part of the comparator's own derived-metrics set, verified
directly from each artifact's own `resource_deltas`) the working-set reduction the operator also
reported: legacy `working_set_delta=63,160,320`, streaming `working_set_delta=59,064,320`, reduction
`4,096,000` bytes = `6.485084...%` — matches the relayed `6.4851%` exactly. Also confirmed
`postgc_private_delta`/`postgc_free_vas_delta` equal the pre-GC deltas in both artifacts, confirming
"post-GC unchanged" for both arms.

**No discrepancy found between the official comparator and the relayed numbers.**

**F1-R6 PASS — REAL-SFM SEMANTIC PARITY 62/62.**

**F1-R6 STREAMING LIST-ELIMINATION CANDIDATE — DO NOT IMPLEMENT; NO MATERIAL COMMAND-SCALE RESOURCE
BENEFIT.** Removing `reachable()`'s large returned `out` list while preserving the full fresh object
traversal does not materially reduce the retained-memory/VAS problem (5.67% private / 6.49%
working-set reduction, VAS actually *worse*, elapsed time *worse*). The large `out` list itself is
cleared as the dominant cause. Wrapper construction is **not** called proven yet — that is precisely
this checkpoint's own open question.

**Overall `F`: `OPEN — LOWER-LEVEL FRESH TRAVERSAL / WRAPPER COST UNDER INVESTIGATION`.**

## 1. `CElementTreeTraversal` — exact binding evidence

Cited from `vs/datamodel.py` lines 3127-3175.

```python
class CElementTreeTraversal(_object):
    def __init__(self, *args):
        """__init__(CElementTreeTraversal self, CDmElement pRoot, char const * pAttrName) -> CElementTreeTraversal"""
    NOT_VISITED = _datamodel.CElementTreeTraversal_NOT_VISITED
    VISITING = _datamodel.CElementTreeTraversal_VISITING
    def Reset(self, *args):
        """Reset(CElementTreeTraversal self, CDmElement pRoot, char const * pAttrName)"""
    def IsValid(self):
        """IsValid(CElementTreeTraversal self) -> bool"""
    def Next(self, bSkipChildren=False):
        """Next(CElementTreeTraversal self, bool bSkipChildren=False) -> CDmElement"""
    def CurrentDepth(self):
        """CurrentDepth(CElementTreeTraversal self) -> int"""
    def GetElement(self):
        """GetElement(CElementTreeTraversal self) -> CDmElement"""
    def GetParent(self, *args):
        """GetParent(CElementTreeTraversal self, int i) -> CDmElement"""
    def GetChildIndex(self, *args):
        """GetChildIndex(CElementTreeTraversal self, int i) -> int"""
```

| Question | Answer | Basis |
|---|---|---|
| Exact binding signature | `__init__(CDmElement pRoot, char const * pAttrName)`; `Next(bool bSkipChildren=False) -> CDmElement` | Direct stub docstrings, lines 3135, 3149-3154 |
| Accepted argument types | `pRoot`: an already-constructed `CDmElement` wrapper (**not** a handle/int — the root itself must already be wrapped); `pAttrName`: a C string, **required, no default** | Line 3135 |
| Returned type | `Next()` returns `CDmElement` directly (not a handle, not `None`-checkable via a separate "IsValid" pattern for the return itself — validity is checked via the **iterator's own** `IsValid()`, a separate call) | Lines 3145-3154 |
| Callbacks involved | No — pull-based iterator (`Reset`/`IsValid`/`Next`), not a visitor/callback API | Lines 3141-3154 |
| Crosses Python/SWIG boundary per visited element | **Yes** | `Next()`'s own declared return type is `CDmElement`, which SWIG's standard out-typemap wraps as a new Python proxy object on every call, unconditionally of whether the caller inspects it |
| Python wrapper constructed per visited element | **Yes, one `CDmElement` wrapper per call to `Next()`** | Same as above |
| Executes predominantly native-side | Partially — the *walk itself* (parent/child bookkeeping, depth tracking, `NOT_VISITED`/`VISITING` state) is native (no Python-visible callback drives it), but **surfacing each visited node still requires one Python/SWIG wrapper construction per node**, so it is not "native-side with zero Python crossing" | Inferred from the API shape: `CurrentDepth()`/`GetParent(i)`/`GetChildIndex(i)` all operate on internal native state without extra arguments, consistent with an internal native stack, but `Next()` still marshals the visited node back into Python every step |
| Traversal order defined | **UNKNOWN** — not stated in the available stub; no accompanying C++ header/source is present in this install to confirm pre-order/post-order/BFS | Absence of documentation; not resolvable from the stub alone |
| Cycles/shared references handled | **UNKNOWN, with a specific inference risk flagged.** Only two states are exported: `NOT_VISITED` and `VISITING` — no `VISITED`/`DONE` state. A two-state (not three-state) marking scheme is the classic pattern for detecting a cycle *along the current traversal path* (an ancestor revisited), not for deduplicating a node reached via two *different, non-overlapping* paths (a DAG diamond). If that inference is correct, a shared/DAG-reachable element could be visited (and re-wrapped) **more than once** for the whole traversal — a real difference from legacy's own permanent `seen`-by-handle set in `reachable()`, which visits each element **at most once, total**. This is not provable from the stub alone and would need either the C++ source (not present in this install) or a live empirical probe | `NOT_VISITED`/`VISITING` constants, line 3139-3140; no third state exported |
| Complete traversal possible | Contingent on `pAttrName` (see next row) | -- |
| Constrainable by element type | No type filter parameter anywhere in the constructor/`Reset` signature | Lines 3135, 3142 |
| Can observe all matching elements | **UNKNOWN — the single largest open question.** `pAttrName` is a **required, single** C-string argument, naturally read as "the one attribute name to follow." Legacy's own `reachable()` must follow **every** element/element_array-typed attribute regardless of name (via `element_ref_pairs()` → `iter_attributes()`, which walks the element's **entire** attribute list). Whether passing an empty string, `None`, or some sentinel to `pAttrName` broadens `CElementTreeTraversal` to "follow every element-typed attribute" (matching legacy) or narrows it to "follow nothing"/errors is **not determinable from this stub** and is not documented anywhere in this SFM install | No default value is given for `pAttrName` in either `__init__` or `Reset`, and no overload omitting it appears in the docstring (contrast with e.g. `FirstAttribute`, whose docstring explicitly lists a zero-arg overload) |
| Ambiguity/uniqueness provable | Only if the previous two rows resolve favorably (complete coverage, correct dedup) — otherwise a rig count derived from this traversal cannot be trusted for the ambiguity/uniqueness decision | Depends on unresolved rows above |
| Fresh/live state observed every call | Yes in principle — `Reset(pRoot, pAttrName)` explicitly re-initializes against a `CDmElement` passed in by the caller each time; nothing here implies caching across `Reset()` calls | Line 3142 |
| Exception behavior | **UNKNOWN** from the stub; no documented exception contract for `Next()`/`Reset()` | Not stated |
| Ownership/lifetime of returned wrappers | Same general SWIG proxy-object lifetime as every other `CDmElement`-returning call in this binding (e.g. `IDataModel.GetElement()`, `CDmAttribute.GetOwner()`) — no distinguishing behavior found | Comparison with other `CDmElement`-returning signatures in the same stub |
| Hidden persistent cache/state | The traversal instance itself holds internal state (`NOT_VISITED`/`VISITING` bookkeeping, current position) across `Next()` calls by design (that's what makes it an iterator) — this is **expected, per-instance, non-persistent-across-instances** state, not a cross-call/cross-command cache in the O3 sense. `Reset()` explicitly starts fresh from a caller-supplied root each time | Lines 3141-3143 |

**Wrapper/allocation-behavior assessment:** `CElementTreeTraversal.Next()` still constructs one
`CDmElement` Python wrapper per visited node (same *order of magnitude* of wrapper construction as
legacy's own per-node cost), but it plausibly **eliminates the separate `CDmAttribute` wrapper
construction legacy pays for** — legacy's `element_ref_pairs()` calls `FirstAttribute()`/
`NextAttribute()` and constructs one `CDmAttribute` wrapper for **every** attribute on every visited
element (not just element-typed ones — `attribute_type(a)` must be read from the wrapper before the
type is even known), whereas `CElementTreeTraversal.Next()`'s own signature suggests the per-attribute
walk happens natively and only the resulting **child elements** are surfaced to Python. If confirmed,
this is a materially different allocation profile from a straight rewrite of the same wrapper walk —
it removes a whole class of intermediate wrapper (attribute wrappers), not merely reorganizing element
wrapper construction. This is the basis for **not** dismissing this mechanism outright.

## 2. `FirstAttributeReferencingElement` / `NextAttributeReferencingElement` / `GetAttributeFromIterator` — exact binding evidence

Cited from `vs/datamodel.py` lines 1361-1371, plus the sentinel constant at line 394 and the related
convenience class `CAttributeReferenceIterator` at lines 3086-3118.

```python
def FirstAttributeReferencingElement(self, *args):
    """FirstAttributeReferencingElement(IDataModel self, DmElementHandle_t hElement) -> DmAttributeReferenceIterator_t"""
def NextAttributeReferencingElement(self, *args):
    """NextAttributeReferencingElement(IDataModel self, DmAttributeReferenceIterator_t hAttrIter) -> DmAttributeReferenceIterator_t"""
def GetAttributeFromIterator(self, *args):
    """GetAttributeFromIterator(IDataModel self, DmAttributeReferenceIterator_t hAttrIter) -> CDmAttribute"""

DMATTRIBUTE_REFERENCE_ITERATOR_INVALID = _datamodel.DMATTRIBUTE_REFERENCE_ITERATOR_INVALID  # line 394
```

| Question | Answer | Basis |
|---|---|---|
| Exact binding signature | `First...(hElement) -> iterator`; `Next...(hAttrIter) -> iterator`; `GetAttributeFromIterator(hAttrIter) -> CDmAttribute` | Lines 1362, 1366, 1370 |
| Accepted argument types | `hElement`: `DmElementHandle_t` (a plain handle, **not** a wrapper — can be obtained from `handle(obj)`-style code without needing the target wrapped first, or from any other handle source); `hAttrIter`: the opaque `DmAttributeReferenceIterator_t` returned by the previous call | Lines 1362, 1366 |
| Returned type | Iterator steps (`First`/`Next`) return a **plain opaque iterator handle** (`DmAttributeReferenceIterator_t`), not a Python object wrapper; only `GetAttributeFromIterator` returns an actual `CDmAttribute` wrapper, and only when explicitly called | Lines 1362-1371 |
| Callbacks involved | No — classic First/Next pull iterator, same shape as the already-used `FirstAttribute`/`NextAttribute` pair (production's own `iter_attributes()` already relies on that exact naming convention terminating cleanly) | Structural analogy to `CDmElement.FirstAttribute()`/`CDmAttribute.NextAttribute()`, lines 2688, 2177, and to production's own `iter_attributes()` at `Rebuild_Control_Groups_Normalizer.py:941-964` |
| Crosses Python/SWIG boundary per visited **reference** | The iteration step itself (`First.../Next...`) does **not** construct a Python object — it returns a plain handle value. A wrapper is constructed **only** when `GetAttributeFromIterator()` is explicitly called on a given iterator position | Lines 1362-1371 |
| Python wrapper constructed per visited element | **No, not during enumeration.** Genuinely cheaper per-step than every other mechanism examined here (including `CElementTreeTraversal`) | Same as above |
| Executes predominantly native-side | Yes for the enumeration step itself | Return type is a raw handle, not an object |
| Traversal order defined | Not stated (order of references found is native-internal); irrelevant to this algorithm's use (see semantic mismatch below) | -- |
| Cycles/shared references handled | Not applicable — this is a **reverse**-reference lookup (who points at X), not a forward graph walk, so forward-cycle handling does not apply the same way | -- |
| Complete traversal possible | **Yes, appears to be a genuine complete enumeration**, not "first match only." Confirmed by: (a) the explicit `Next...` continuation function (mirroring the already-used, already-verified-complete `FirstAttribute`/`NextAttribute` pattern); (b) a named invalid-sentinel constant, `DMATTRIBUTE_REFERENCE_ITERATOR_INVALID` (line 394), which is exactly the shape of a "loop until you hit the terminal value" contract. **This corrects the F1-R6-era characterization of this mechanism as "only first, no enumeration" — it is a real iterator, not a single-lookup call** | Lines 1361-1371, 394 |
| Constrainable by element type | No — enumerates every attribute that references the given element, regardless of the referencing element's own type; a post-filter (`typ(a.GetOwner()) == "DmeRig"`) would be needed | -- |
| Can observe all matching **references** | Yes, per the row above | -- |
| Ambiguity/uniqueness provable for THIS specific question ("who references element X") | Yes, in isolation | -- |
| Fresh/live state observed every call | Yes — nothing here implies caching; each `First...` call presumably starts a fresh native scan | -- |
| Exception behavior | Not documented in the stub | -- |
| Ownership/lifetime of returned wrappers | `GetAttributeFromIterator()`'s returned `CDmAttribute` follows the same SWIG proxy lifetime as any other `CDmAttribute`-returning call; the iterator handle itself is a plain value with no Python-side lifetime concerns | -- |
| Hidden persistent cache/state | None apparent; the iterator handle is a plain opaque value passed explicitly on every call, not an object holding hidden state | -- |

**A separate, higher-level convenience class exists — `CAttributeReferenceIterator`** (lines
3086-3118): `__init__(self, pElement) -> CAttributeReferenceIterator`, `__nonzero__`/`__bool__`
(validity), `GetAttribute() -> CDmAttribute`, `GetOwner() -> CDmElement`. **No `Next`/advance method of
any kind is exposed on this class.** This strongly suggests `CAttributeReferenceIterator` is a
convenience "does anything reference this element, and if so what/who" **single-shot** checker, not a
full enumerator — i.e., exactly the "only first, no way to enumerate every reference" shape the
instruction warned about, but that limitation applies to **this convenience class only**, not to the
lower-level `IDataModel.FirstAttributeReferencingElement`/`NextAttributeReferencingElement`/
`GetAttributeFromIterator` triple, which does support full enumeration.

### Why this mechanism cannot replace `discover_rig_context()`'s own forward search regardless

This is a **reverse**-reference lookup: given one specific element, find every attribute anywhere in
the datamodel that references it. Production's own algorithm is the opposite shape — a **forward**
search starting from `scene`, discovering *which* elements are reachable rigs in the first place. To
use `FirstAttributeReferencingElement` for rig discovery you would already need to know which specific
elements are candidate rigs, which is precisely the unknown the forward search exists to resolve. There
is no type-scoped or scene-scoped reverse-lookup entry point anywhere in this binding surface (no
"give me every reference to any `DmeRig`" call — only "give me every reference to *this one already-
identified* element"). **Classification: `SEMANTICALLY_INSUFFICIENT` for this algorithm, regardless of
its otherwise-excellent (handle-only, zero-wrapper, complete) enumeration profile.** This is a genuine,
useful negative result: the mechanism is real, well-behaved, and cheap, but it solves a different
problem.

## 3. Broader binding surface — other mechanisms inspected

Found while auditing the two mechanisms above, in the same `IDataModel` class (lines 915-2109 of
`vs/datamodel.py`):

| Mechanism | Signature | Assessment |
|---|---|---|
| `FirstAllocatedElement()` / `NextAllocatedElement(it)` | Both return `DmElementHandle_t` (lines 1128-1134) — a **plain handle, zero wrapper construction per step**, exactly like the reverse-reference iterator above | Genuinely the cheapest raw enumeration mechanism found in this binding surface. **Disqualified on scope, not cost**: this enumerates **every element currently allocated anywhere in the datamodel/process**, not elements reachable from a specific `scene` object. Production's own contract requires scene-scoped reachability (a rig must be *reachable from this shot's scene* to count); this API has no such scoping. Using it would risk false-positive rig matches from elements that exist in the loaded document but are not actually part of this scene's own reachable graph (other shots, orphaned/pending-GC elements, etc.) — an unproven and unsafe assumption to make silently. **Classification: `SEMANTICALLY_INSUFFICIENT`** (wrong scope), despite an excellent allocation profile |
| `GetElementType(hElement) -> CUtlSymbolLarge` / `GetElementName(hElement) -> char const *` / `GetElementId(hElement) -> UniqueId_t` | Lines 970-980 | Genuine handle-only accessors (no `CDmElement` wrapper needed to check an element's type/name/id if you already hold its handle). **Not independently useful here**: this binding surface has no handle-only way to enumerate an element's own *outgoing references* (finding a node's children still requires `element_ref_pairs()`'s own attribute-value access, which always returns actual `CDmElement`/`CDmAttribute` wrappers, never bare handles) — so by the time a child handle is known, its wrapper has already been constructed anyway. These accessors would only help if paired with a handle-only forward-reference enumerator, which does not exist in this binding surface |
| `FindElement(id) -> DmElementHandle_t` | Line 1353-1355 | Looks up one already-known element by its `UniqueId_t`. Not useful for "find all rigs" — requires already knowing the ID |
| `GetExistingElements(CElementIdHash & hash)` | Line 1357-1359 | Takes a C++ reference to an otherwise-unexposed `CElementIdHash` output type (no such class is defined anywhere in this stub) — very likely **not practically callable from Python** in this binding as-is. Even if it were, it would share the same whole-datamodel scope problem as `FirstAllocatedElement`. Not pursued further |
| `EstimateMemoryUsage(hElement, depth) -> int` | Line 1136-1138 | A native memory-estimation call, not an enumeration mechanism; noted only for completeness, not relevant to the traversal question |

No visitor/callback-based traversal API, no type-indexed global registry, and no scene-scoped
handle-only reference enumerator were found anywhere in this binding surface.

## 4. Semantic-capability matrix

| Requirement | `CElementTreeTraversal` | `FirstAttributeReferencingElement` triple | `FirstAllocatedElement`/`NextAllocatedElement` |
|---|---|---|---|
| Fresh current scene each call | Yes (`Reset()`/`__init__` take a live root each time) | Yes | Yes |
| Same status / same ambiguity result | **Unresolved** (depends on `pAttrName` scope + dedup semantics) | No — wrong algorithm shape | **No — wrong scope** (whole-datamodel, not scene-reachable) |
| Same reachable-rig count | **Unresolved** | No | No |
| Same matching-rig result | **Unresolved** | No | No |
| Same selected rig identity | **Unresolved** | No | No |
| Same registry identity | **Unresolved** | No | No |
| Same ownership result/order | **Unresolved** (ownership derivation is unchanged downstream code regardless of traversal mechanism) | No | No |
| Same hidden groups | **Unresolved**, same reasoning | No | No |
| Same fail-closed behavior | **Unknown**, exception contract undocumented | Unknown | Unknown |
| Same supported models | **Unresolved** | No | No |
| No stale reuse / O3 remains closed | Yes if used as designed (fresh `Reset()`/root every call) | Yes | Yes |

## 5. Classification

| Mechanism | Classification | Reasoning |
|---|---|---|
| `CElementTreeTraversal` | **`MEASUREMENT_CANDIDATE`** | Plausibly eliminates per-attribute `CDmAttribute` wrapper construction (a real, structurally different allocation profile from legacy, not just a rearrangement of the same wrapper walk), but **two specific, binding-evidence-blocking semantic gaps remain unresolved and are not answerable from any source-level evidence present in this SFM install**: (1) whether `pAttrName` can be made to follow every element-typed attribute (matching legacy's whole-attribute-list walk) or only one named attribute; (2) whether shared/DAG-reachable elements are deduplicated across the whole traversal (matching legacy's permanent `seen`-by-handle set) or only cycle-guarded along the current path. Neither gap can be resolved by more static reading — no C++ source is present in this install |
| `FirstAttributeReferencingElement` / `NextAttributeReferencingElement` / `GetAttributeFromIterator` | **`SEMANTICALLY_INSUFFICIENT`** | Genuinely complete, cheap (handle-only per-step), well-behaved enumeration — but solves the reverse problem (who references a known element) rather than the forward problem this algorithm needs (which elements are reachable rigs from an unknown-in-advance set). No amount of enumeration completeness fixes a mismatched algorithm shape |
| `CAttributeReferenceIterator` (convenience wrapper) | **`SEMANTICALLY_INSUFFICIENT`** | No enumeration method exposed at all (single-shot "first reference" checker only), and inherits the same reverse-lookup algorithm-shape mismatch as above |
| `FirstAllocatedElement` / `NextAllocatedElement` | **`SEMANTICALLY_INSUFFICIENT`** | Wrong scope (whole-datamodel/process, not scene-reachable) despite the best raw per-step allocation profile of anything examined here |
| `GetElementType`/`GetElementName`/`GetElementId` (handle-based accessors) | **`PARTIAL_ONLY`** | Real and cheap, but not independently actionable — no handle-only way exists in this binding surface to enumerate a node's own outgoing references, so these accessors cannot by themselves avoid the wrapper construction that already happens when references are found |
| `FindElement` / `GetExistingElements` | **`SEMANTICALLY_INSUFFICIENT`** / **`UNKNOWN`** | `FindElement` requires an already-known ID; `GetExistingElements` is likely impractical to call from this Python binding and would share the whole-datamodel scope problem even if usable |

## 6. Prototype gate decision

**No prototype is built or proposed in this checkpoint.**

Per instruction: *"Do not create a prototype merely because an API exists... Prepare an F1-R7
prototype only if at least one mechanism is an EXACT_CANDIDATE or a strong MEASUREMENT_CANDIDATE with
materially different allocation behavior... first prove exact semantics offline where possible."*

`CElementTreeTraversal` is a genuine `MEASUREMENT_CANDIDATE` with a plausibly different allocation
profile (attribute-wrapper elimination) — but its two disqualifying-if-unresolved semantic gaps
(`pAttrName` scope; shared-reference dedup) **cannot be proven offline** in this environment: there is
no C++ source, no header, and no documentation anywhere in this SFM install that settles either
question, and — unlike F1-R6's candidate, which was pure Python testable against synthetic fake DME
objects — `CElementTreeTraversal` is a real native SWIG-bound class with its own internal C++
implementation that cannot be adversarially tested with Python-side fakes. Resolving these two
questions would require either external documentation (not available) or a narrow, live, read-only
empirical probe inside real SFM against a small, deliberately-constructed test graph (e.g., a root with
two children reachable via differently-named attributes, and a diamond/shared-reference sub-element) —
**not** a resource-comparison run, and **not** the qualification fixture. That probe, if the user wants
it, would itself need its own Phase-1-style design/approval before any real-SFM execution, per standing
discipline, and is explicitly **not** authorized by this audit.

**Everything else audited is disqualified on semantic grounds** (`FirstAttributeReferencingElement`:
wrong algorithm shape; `FirstAllocatedElement`/`NextAllocatedElement`: wrong scope), independent of
their allocation profile — no amount of resource benefit would make a semantically-insufficient
mechanism acceptable, per the equivalence contract this project has held throughout F1-R6.

**This is a useful negative-leaning result, per instruction that a negative result is acceptable.** No
mechanism currently qualifies as an `EXACT_CANDIDATE`. One (`CElementTreeTraversal`) remains open as a
`MEASUREMENT_CANDIDATE` pending semantics that this audit cannot resolve from available evidence.

## 7. Explicit non-authorization

This audit does not modify production, does not build or run a prototype, and does not authorize any
real-SFM execution. `Overall F` remains `OPEN — LOWER-LEVEL FRESH TRAVERSAL / WRAPPER COST UNDER
INVESTIGATION`.
