# F1-R6 — Phase A/B: Exact Contract and Allocation/Materialization Audit

**Status: STATIC SOURCE AUDIT ONLY.** No production, integration, or lifecycle code has been modified.
Audited directly against the current accepted production Normalizer (SHA-256
`cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`). This is not authorization to modify
production. O3 remains closed; nothing here proposes cross-boundary discovery reuse, topology caching,
stale handles, semantic-generation shortcuts, or immutable-topology assumptions.

## Phase A — the exact existing contract

### `reachable(start, max_elements=50000)` (lines 1006-1039)

1. **Exact root argument**: `start` — in the one real call site (line 3329), this is `scene =
   scalar(shot, "scene")` (or `shot.scene` as a fallback, lines 3313-3319) — the shot's own `DmeElement`
   scene root, not the shot itself and not a specific animation set.
2. **Traversal algorithm**: explicit stack-based depth-first search (`stack = [start]`; `stack.pop()`/
   `stack.append(child)`).
3. **Traversal order**: LIFO (last-in-first-out) via `stack.pop()` from the end of a Python list — a
   depth-first order, but the exact visitation order among siblings is whatever order
   `element_ref_pairs()` yields them in (attribute-enumeration order via `FirstAttribute()`/
   `NextAttribute()`, itself dependent on the underlying DME element's own internal attribute storage
   order — not independently controlled by this Python code).
4. **Recursion/iteration structure**: iterative (explicit `stack`), confirmed **not** recursive — already
   independently established in `O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md` section 7 and
   `F1_R5_ALLOCATION_TRAVERSAL_AUDIT.md` item 4, re-confirmed here by direct re-reading.
5. **Cycle/duplicate detection**: a `seen` Python `set()`, checked/updated by `handle(obj)` (an `int`,
   line 1019-1022) before appending to `out`, and separately checked again before pushing a child onto
   `stack` (line 1036, `if ch not in seen: stack.append(child)`) — this second check is an optimization to
   avoid re-pushing already-visited handles, not a correctness requirement (the first check would still
   catch a duplicate later), but it does reduce `stack`'s own peak size.
6. **Identity key used for "seen"**: `handle(obj)` — `int(obj.GetHandle())` (line 860-861) — a plain
   integer DME handle, **not** Python object identity (`id()`) and **not** the SWIG wrapper object itself.
   This matters directly for Phase C/D: the de-duplication mechanism already keys on a cheap scalar, not
   on any wrapper-retention requirement.
7. **What the `seen` structure stores**: DME handles (plain ints), confirmed by item 6 — the cheapest of
   the four options this audit was asked to distinguish.
8. **Every collection/container materialized**: `stack` (a Python list, mutated throughout, transient);
   `seen` (a Python `set` of ints, transient); `out` (a Python list of **live SWIG wrapper objects**,
   returned to the caller — this is the one that survives the call and is the large materialization).
9. **Null/invalid elements**: if `handle(obj)` itself raises (line 1014-1017), that object is silently
   `continue`d past (neither added to `seen` nor `out`, and its own children are never enumerated) — not
   fatal, not retained. If a child reference within `element_ref_pairs()` cannot be resolved to a handle
   (line 1031-1034), that specific child edge is silently skipped, not fatal.
10. **Exception behavior**:
    - Attribute enumeration (`iter_attributes`, lines 941-964): `FirstAttribute()`/`NextAttribute()`
      failures are caught and terminate that element's own attribute walk cleanly (`except Exception: a =
      None` / `except Exception: break`) — not propagated.
    - Array traversal inside `element_ref_pairs` (`element_array` branch, lines 983-1004): `Count()`/`len()`
      failures `continue` past that specific attribute (skip it entirely); per-index access failures
      (`a[i]`/`a.GetValue(i)`) are individually caught, yielding nothing for that index — not fatal.
    - Scalar DME references (`element` branch, lines 971-981): `GetValue()`/`GetValueUntyped()` failures
      are individually caught, yielding nothing for that attribute — not fatal.
    - Wrapper/handle access inside `reachable()` itself (lines 1014-1017, 1031-1034): caught, `continue`s
      past that one object/edge — not fatal.
    - **The only exception `reachable()` itself can propagate is the explicit safety-cap `ProbeError`**
      (line 1025-1028, `if len(out) > max_elements: raise ProbeError(...)`) — everything else is
      swallowed at the point closest to its own source, by design.
11. **Is the root itself returned?** Yes — `start` is pushed onto `stack` first (line 1007) and, assuming
    `handle(start)` succeeds, is the first object appended to `out`.
12. **Duplicate-reference behavior**: an object reachable via multiple parent-child edges is visited (and
    appended to `out`) **exactly once** — the `seen`-handle check guarantees this — but a fresh SWIG
    wrapper is still constructed for it via `element_ref_pairs()`'s own `a[i]`/`GetValue()`/`GetValue(i)`
    access **for every edge that references it**, before the `seen` check discards the redundant ones (see
    Phase B).
13. **Deterministic-order assumptions**: none of `discover_rig_context()`'s own logic depends on
    `reachable()`'s own traversal order — every downstream use (`typ(obj)` filtering, `HasAnimationSet`
    checking) is order-independent; only membership/count matters, confirmed by direct reading (no
    `objs[0]`-style positional access anywhere in `discover_rig_context()`).
14. **Approximate live object count on the qualification fixture**: ~4,250, established by O3-R2 and
    re-cited in every subsequent F1-R series checkpoint; not independently re-measured by this static
    audit.
15. **Every caller of `reachable()`**: exactly one, confirmed by exhaustive grep across the entire pinned
    production source — `discover_rig_context()` (line 3329). No other function in this file calls
    `reachable()`. This means any change to `reachable()`'s own behavior, or introduction of an alternative
    function, needs to satisfy only this single call site's own contract — not an unknown set of other
    consumers.

### `discover_rig_context(shot, aset)` (lines 3299-3436) — observable contract

- **Inputs**: `shot` (a `DmeElement`-like shot object), `aset` (a specific, already-known animation-set
  object).
- **Returned keys and value types**: `status` (`unicode` enum string), `rig` (live wrapper or `None`),
  `registry` (live wrapper or `None`), `rig_handle`/`registry_handle` (`int` or `None`),
  `matching_rig_count`/`reachable_rig_count` (`int`), `owned_handles` (`set` of `int`),
  `owned_names_in_order` (`list` of `unicode`), `hidden_groups` (`list` of `unicode`).
- **Success state**: `status == "SUPPORTED_ACTIVE_RIG"` — the only status where every key is populated with
  its full, non-default value.
- **Failure/non-success states** (each returns immediately, at the point named): `RIG_CONTEXT_UNAVAILABLE`
  (no scene); `RIG_TRAVERSAL_FAILED` (`reachable()` itself raised); `UNRIGGED` (zero `aset`-matching
  `DmeRig` objects); `AMBIGUOUS_MULTIPLE_RIGS` (>1 matching `DmeRig` objects — **`rig`/`rig_handle` remain
  `None`, not set**, a specific asymmetry re-confirmed by direct reading this turn); `AMBIGUOUS_RIG_REGISTRY`
  (`rig` uniquely found, but 0 or >1 registry-binding records match — **`rig`/`rig_handle` ARE set here,
  `registry`/`registry_handle` are not**); `STALE_ZERO_OWNERSHIP_RIG` (rig and registry both uniquely
  found, but zero owned controls — `rig`/`registry`/both handles ARE set).
- **Ambiguity/uniqueness semantics**: both the rig-selection and registry-selection steps require **exactly
  one** match; zero or more-than-one both fail (differently labeled), never picking an arbitrary one.
- **Rig selection semantics**: the object must be `typ(obj) == u"DmeRig"` (line 3335) **and**
  `obj.HasAnimationSet(aset)` return `True` (line 3341) — both conditions, on the same object, required.
- **Registry selection semantics**: among `rig`'s own `animSetList` array, a record must be
  `typ(rec) == u"DmeRigAnimSetElements"` **and** its own `scalar(rec, "animationSet")` must handle-equal
  `aset` (lines 3361-3376).
- **Ownership/control lookup semantics**: `owned_handles = control_handles ∩ registry_handles` (lines
  3386-3403) — a control is "owned" only if it is simultaneously present in both `aset`'s own `controls`
  array and `registry`'s own `elementList` array, compared by handle.
- **Does reachable-object ORDER affect any result?** No (item 13 above) — confirmed no positional/order
  dependency anywhere in this function.
- **More than one pass over the reachable list?** No — confirmed exactly one `for obj in objs:` loop
  (line 3334) over `reachable()`'s own return value; every other loop in this function iterates a
  **different**, much smaller collection (`arr(rig,"animSetList")`, `arr(aset,"controls")`,
  `arr(registry,"elementList")`, `arr(registry,"hiddenGroups")`).
- **Does any caller depend on wrapper identity rather than semantic identity?** The two live objects placed
  into the returned dict (`rig`, `registry`) are consumed downstream (per `O3_R1_DISCOVERY_CAPTURE_
  CONTRACT.md`, re-confirmed unchanged) by exactly one caller, `capture_snapshot_explicit()`, which uses
  `rig` for exactly one `name()` call and never dereferences `registry` at all — a **semantic** identity use
  (the object's own current name), not a Python-identity (`is`) comparison anywhere. No code anywhere in
  this file compares discovery's own returned `rig`/`registry` objects by Python `is`-identity against
  anything else.

## Phase B — allocation/materialization map, one `discover_rig_context()` call

| Structure | Cardinality (fixture) | Element type | Contains DME/SWIG wrappers? | Max simultaneous lifetime | Survives return? | Required for semantics? | Replaceable by scalar/constant state? | Command-scale? | Classification |
|---|---|---|---|---|---|---|---|---|---|
| `reachable()`'s own `stack` | up to ~4,250 transient pushes, not all simultaneous | live wrappers | Yes | Duration of `reachable()`'s own execution only | No | Yes (traversal frontier) | No | No (bounded by algorithm, not itself a redundant copy) | `SEMANTICALLY_REQUIRED` |
| `reachable()`'s own `seen` | up to ~4,250 | `int` (handles) | No | Duration of `reachable()`'s own execution only | No | Yes (cycle/duplicate detection) | Already scalar | No | `SEMANTICALLY_REQUIRED` |
| `reachable()`'s own `out` (the return value, `objs` at the call site) | ~4,250 | live wrappers | Yes | From construction until `discover_rig_context()`'s own single filtering pass completes | **No** (never stored in `result`; local-only past the one filtering loop) | The *traversal itself* is required (item 12/Phase A #12); holding all ~4,250 references *simultaneously in one Python list* is not, since only a per-object `typ()` check is ever performed | **Yes** — see Phase D | **Yes — the single largest materialization in this function, ~2 orders of magnitude above every other structure below** | `STREAMING_CANDIDATE` |
| `rigs` | up to `reachable_rig_count` (single digits in this fixture, per prior gate-skip evidence) | live wrappers | Yes | From loop start until function return (never cleared early) | No | Only `len(rigs)` is ever read after the loop (line 3346) — the object references themselves are **never used again** | **Yes — trivially, a plain counter suffices** | No (single-digit cardinality) but the *pattern* is worth fixing since it is free to fix once `objs` itself is streamed | `PROVEN_REDUNDANT_MATERIALIZATION` |
| `matches` | 0, 1 (expected), or more (ambiguous/error case) | live wrappers | Yes | From loop start until function return | No | Only `len(matches)` and `matches[0]` (once uniqueness is confirmed) are ever read | **Yes — count + first-candidate reference is exactly sufficient**, per Phase D | No (single-digit) | `STREAMING_CANDIDATE` (same fusion opportunity as `objs`, smaller scale) |
| `registry_matches` | 0, 1 (expected), or more | live wrappers | Yes | From loop start until function return | No | Only `len(registry_matches)` and `registry_matches[0]` are ever read | Yes, same pattern | No | `STREAMING_CANDIDATE` (design-consistency fix, not command-scale on its own) |
| `arr(rig, "animSetList")`'s own returned list | bounded by rig's own binding-record count (small) | live wrappers | Yes | One loop's duration | No | Yes, each record must be inspected | Not fully — must still visit each record; the fusion is in what's *retained*, not whether the array is read | No | `SEMANTICALLY_REQUIRED` |
| `control_objs` (`arr(aset,"controls")`) | 136/174 in this fixture's own targets | live wrappers | Yes | Held across two separate loops (`control_handles` construction, then `owned_names` construction, lines 3386-3417) | No | Yes — reused for a second pass (`for control in control_objs:` at line 3415), a genuine multi-pass use, unlike `objs` | No — both passes are needed; `control_objs` itself must be retained between them, or `arr()` re-called (a second, redundant scene-adjacent read) | No (136-174, two orders of magnitude below `objs`) | `SEMANTICALLY_REQUIRED` |
| `control_handles` / `registry_handles` / `owned_handles` | bounded by control/registry scale | `int` (handles) | No | Function duration | `owned_handles` yes (placed in `result`) | Yes | Already scalar | No | `SEMANTICALLY_REQUIRED` |
| `owned_names` (`owned_names_in_order`) | bounded by owned-control count | `unicode` strings | No | Function duration | Yes (placed in `result`) | Yes | Already scalar/string | No | `SEMANTICALLY_REQUIRED` |
| `arr(registry, "hiddenGroups")`'s own returned list | small, bounded by hidden-group count | live wrappers (converted to `unicode` immediately via `to_unicode(x)`) | Transiently | One list-comprehension's duration | No (converted to strings before storage) | Yes | Already reduced to strings at the point of storage | No | `SEMANTICALLY_REQUIRED` |
| `rig` (the single retained wrapper) | 1 (on success/registry-ambiguous/stale-ownership paths) | live wrapper | Yes | Survives into `result`, therefore into the caller | Yes | Downstream needs exactly one `name()` call from it (per `O3_R1_DISCOVERY_CAPTURE_CONTRACT.md`) | Could in principle be reduced to a pre-computed `name(rig)` string, per that same prior finding — **not pursued here**, per explicit instruction not to exploit this without the complete consumer contract confirming it is safe in every caller/branch, which this audit does not re-litigate | No (a single reference) | `SEMANTICALLY_REQUIRED` (as currently consumed); noted, not changed |
| `registry` (the single retained wrapper) | 1 (on success path only) | live wrapper | Yes | Survives into `result` | Yes | **Never dereferenced by any known consumer** (re-confirmed, not reopened) | Yes, in principle omittable entirely, per the same prior finding | No (a single reference) | `SEMANTICALLY_REQUIRED`-adjacent, not pursued here (same reasoning as `rig`) |

**Conclusion**: exactly one structure is genuinely command-scale and a `STREAMING_CANDIDATE`:
`reachable()`'s own returned `out`/`objs` list, together with the `rigs`/`matches` lists that consume it in
a single pass. Every other structure in this function is either already scalar, already required for a
genuine multi-pass use (`control_objs`), or small enough (single digits to low hundreds) to be explicitly
out of scope per "do not waste time on tiny containers."
