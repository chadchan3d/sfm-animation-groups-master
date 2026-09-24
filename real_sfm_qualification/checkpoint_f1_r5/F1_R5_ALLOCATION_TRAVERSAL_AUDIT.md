# F1-R5 — Fresh Discovery Allocation / Traversal Decomposition (Static Audit)

**Status: STATIC SOURCE AUDIT ONLY.** No production, integration, or lifecycle code has been modified.
This document performs the Phase A/B static audit required before any F1-R5 runtime code is written,
against the current accepted production Normalizer (SHA-256
`cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`). It does not propose or authorize any
production change. The governing constraint is unchanged: freshness semantics remain mandatory; this audit
does not reopen O3's rejected stale-discovery reuse/cache design.

## Phase A — complete object/allocation path of `discover_rig_context()` and every helper it calls

Full body re-read directly from source (lines 3299-3436), together with every helper it calls: `scalar`/
`attr` (881-893, 875-879), `reachable` (1006-1039), `typ` (869-873), `arr` (895-927), `handle` (860-861),
`name` (863-867), and `element_ref_pairs`/`iter_attributes` (966-1004, 941-964, called only from inside
`reachable()`, not directly from `discover_rig_context()`).

### 1. What SFM/DME collections are traversed

- The entire reachable object graph from `scene` (via `reachable(scene)`) — confirmed ~4,250 objects in
  this fixture (O3-R2's own established figure).
- `rig`'s own `animSetList` (`arr(rig, "animSetList")`) — bounded by the rig's own binding-record count
  (small, single digits typically).
- `aset`'s own `controls` (`arr(aset, "controls")`) — bounded by target scale (136/174 in this fixture's
  Fox/Mia targets — moderate, not scene-scale).
- `registry`'s own `elementList` (`arr(registry, "elementList")`) — bounded by registry/control scale
  (comparable to the above, not scene-scale).
- `registry`'s own `hiddenGroups` (`arr(registry, "hiddenGroups")`) — small, bounded by hidden-group count.

### 2. Materialized as Python lists/tuples/dicts?

Yes, in every case above. `arr()` (895-927) always builds and returns a full `out = []` list via
`for i in xrange(count): out.append(a[i])` — never a generator, never streamed. `reachable()` (1006-1039)
also builds and returns a full `out = []` list. **The single largest materialization by far is
`reachable(scene)`'s own `out` list — ~4,250 elements, versus dozens at most for every other `arr()` call
inside this function.**

### 3. Are SWIG/DME wrappers created for every traversed object?

Yes. `a[i]` (SWIG `__getitem__`) and `a.GetValue(i)` each construct a new Python-side wrapper object for
the underlying C++ element on every access — confirmed by the code's own pattern (a fresh wrapper is the
only way Python code can hold or inspect the object at all). This applies to every element appended into
`reachable()`'s own `out` list (~4,250 wrapper constructions per call) and every element appended by each
`arr()` call.

### 4. Recursive traversal?

No, for the code this audit covers. `reachable()` uses an explicit iterative `stack` (`stack.pop()`/
`stack.append(child)`), not recursion — already independently confirmed in `O3_R1_CORRECTED_SUBSTITUTION_
DESIGN.md` section 7, re-confirmed here by direct re-reading. (`capture_tree()`'s own `walk()` closure IS
recursive and self-referential, with an already-documented GC-cycle finding — but `capture_tree()` is never
called by `discover_rig_context()` and is out of scope for this specific audit.)

### 5. Is the same scene/shot/aset structure walked more than once inside ONE discovery call?

No. `reachable(scene)` is called exactly once per `discover_rig_context()` invocation (line 3329). Each
`arr()` call targets a different object/attribute (`rig`'s `animSetList`, `aset`'s `controls`, `registry`'s
`elementList`/`hiddenGroups`) — none re-walks the same collection twice within one call. (Across MULTIPLE
discovery calls per target — PRE, NATIVE_POST, composer-before, composer-after, terminal — the *same*
`reachable(scene)` full-scene scan repeats once per site, which is exactly what F1-R4 already measured at
the whole-discovery-call level; this is a cross-call repetition, not a within-call one.)

### 6. Which objects survive only as local temporaries?

`objs` (the ~4,250-element `reachable()` result), `rigs`, `matches`, `registry_matches`, and `control_objs`
are all plain local variables, never stored in any module-level, instance, or closure state, and never
placed into the returned `result` dict. By ordinary CPython refcounting semantics, once
`discover_rig_context()` returns, these local variables' own references are released and, absent any
external reference or SWIG-side retention (see item 8), the underlying Python wrapper objects become
eligible for immediate collection — **not requiring a `gc.collect()`**, since none of this traversal
constructs a reference cycle (unlike `capture_tree()`'s own recursive closure, already separately
documented as cycle-forming).

### 7. Which objects are placed in the returned context?

Only two live wrapper references survive into the returned `result` dict on the success path: `rig` and
`registry` (line 3421-3422). Every other returned field is a plain Python scalar/string/int/set/list of
strings (`status`, `rig_handle`, `registry_handle`, `matching_rig_count`, `reachable_rig_count`,
`owned_handles` — a set of ints, `owned_names_in_order` — a list of unicode strings, `hidden_groups` — a
list of unicode strings).

**Cross-reference to `O3_R1_DISCOVERY_CAPTURE_CONTRACT.md`** (already established, not reopened here):
`capture_snapshot_explicit()`'s only use of the live `rig` reference is a single `name(rig_context["rig"])`
call producing a string; `registry` is never dereferenced by it at all. This means `discover_rig_context()`
retains two live wrapper references in its return value when its own only real consumer needs, at most, one
string derived from one of them. This is a genuine, source-confirmed observation about the *shape* of the
return value — **not** a proposal to reuse or cache a discovery result across calls (every call remains
fully fresh); it concerns only what a single fresh call's own return value needs to hold. Given the
overwhelming scale difference between two extra object references and the ~4,250-element traversal list,
this specific observation is **not command-scale** on its own (see Required Conclusions below) and is
recorded for completeness, not proposed as an optimization target here.

### 8. Module/global/cache/closure/SWIG ownership structures that may retain wrappers

No Python-level module/global/cache/closure retains any reference from this function — confirmed by
exhaustive reading of `discover_rig_context()`'s own body and every helper it calls; none references any
name outside its own parameters/locals except other pure functions (`scalar`, `reachable`, `typ`, `arr`,
`handle`, `name`) and the `ProbeError` exception class. **Whether the SWIG binding layer itself pools,
caches, or otherwise retains wrapper objects internally (independent of Python-level reference counting)
cannot be determined from this project's available evidence** — this is compiled, closed-source binary
behavior, exactly analogous to the already-established `UNRESOLVED` native-reentrancy question from the O3
series. This is classified `UNKNOWN` below, honestly, not assumed either way.

### 9. Are Python references actually released at return?

Reasoned, not directly observable from static source alone: yes, at the Python level, by ordinary
refcounting (see item 6). Whether the *process* actually returns the underlying memory to the OS afterward
is a **separate, well-documented CPython behavior**, independent of anything in this file: CPython's own
small-object allocator (`pymalloc`) manages memory in arenas that are only returned to the OS once
completely empty of live objects — under the kind of large, transient, non-uniform allocation burst
`reachable()` produces (many thousands of same-session wrapper objects allocated together, then freed
together), arena fragmentation commonly prevents full arena release even after every individual object
within it is freed. This is a general, well-known property of CPython's own memory manager, not something
specific to this file, and is the most plausible explanation for process-level growth surviving individual
object collection without implying any logical reference leak in this code.

### 10. Can traversal be streamed instead of materialized while preserving exact semantics?

The union-based *reachability* itself intrinsically requires visiting the whole connected object graph at
least once to prove no other matching rig exists (see item 11) — that traversal cost cannot be eliminated
without an alternative uniqueness proof this project has no evidence for (see item 12). But the
*materialization* — building and returning a full `out` list of ~4,250 live objects, only to have the
immediate caller (`discover_rig_context()`) throw almost all of them away after a single `typ(obj)`
check — is a distinct question from the traversal itself. In principle a streaming/generator form of
`reachable()` could yield each object as it is discovered, letting the caller filter for `DmeRig`-typed
objects without ever holding all ~4,250 wrappers in one Python list simultaneously. **This project has no
evidence this would reduce peak SWIG wrapper churn** (each object would still need its own wrapper
constructed to be inspected via `typ()`), but it could plausibly reduce the *peak simultaneous list size*
Python itself must hold, which is a separate lever from wrapper-construction count. Not implemented or
proposed as a production change by this checkpoint — noted as the shape of the "eventual safe optimization
direction" the request itself names (fresh streaming traversal, not reuse).

### 11. Is target identity already known at call sites, yet discovery rebuilds a whole-session search structure?

Yes, precisely. Every call site already holds a specific, known `aset` object (`shot`, `aset` are both
passed in by the caller). `discover_rig_context()` nonetheless performs a full scene-wide `reachable(scene)`
walk and filters for `DmeRig`-typed objects, checking `obj.HasAnimationSet(aset)` against **every**
candidate found — it never attempts any direct, targeted lookup path from `aset` to its own owning rig.
**Whether such a direct lookup path exists in the underlying DME schema** (e.g. a back-reference attribute
from an animation set to its owning rig) **cannot be determined from this project's available evidence** —
this project has no SFM/Source SDK schema documentation beyond what is empirically observable through the
generic `arr`/`scalar`/`attr` accessors already used throughout this codebase, and no prior checkpoint in
this project's history has ever discovered or used such a reverse lookup. Classified `UNKNOWN`, not
`PROVEN_REDUNDANT_MATERIALIZATION` — the cost is real and measurable, but this audit cannot prove a cheaper
correct alternative exists without schema knowledge this project does not have.

### 12. What duplicate/ambiguity/freshness checks require traversal beyond the desired target?

The `AMBIGUOUS_MULTIPLE_RIGS` status (`len(matches) != 1`, line 3353-3355) is only detectable by finding
**every** `DmeRig`-typed object in the scene that claims this `aset` — proving uniqueness structurally
requires seeing every candidate, not just the first match. This is the same reasoning already applied in
`O3_R3_COUNTEREXAMPLE_ANALYSIS.md` (case A: "additional matching rig appears... requires re-walking the
current reachable set to detect... structurally blind" for any partial/retained enumeration). The same
logic applies here in the opposite direction: any correct implementation of this uniqueness check must
observe the whole reachable graph at least once, **unless** an alternative, already-authoritative
uniqueness mechanism exists — which section 2's own mechanism search (`O3_R3_ENUMERATION_VALIDITY_
MECHANISM_SEARCH.md`) already established does not exist anywhere in this project's evidence base.

### 13. Correspondence with O3-R2's own measured expensive whole-scene traversal

O3-R2 measured, per composer-before discovery call: total ≈0.857s, whole-scene traversal (Phase 1,
`reachable()`+`scalar(shot,"scene")`) ≈0.809s (~94.4%), retained/context work (Phases 2/4/6/7/8 + residual)
≈0.048s. This audit's own static findings are fully consistent with, and explain structurally, that
timing split: the ~4,250-element `reachable()` traversal (item 1-3 above) is the single large
materialization; every other step (`arr(rig,"animSetList")`, `arr(aset,"controls")`,
`arr(registry,"elementList")`, `arr(registry,"hiddenGroups")`, the pure-Python uniqueness/ownership checks)
operates on collections one to two orders of magnitude smaller. **This timing result is used here only to
identify the known structural seam** (`reachable()` itself) — it is not used to infer memory ownership,
which this audit derives independently from the object/allocation-path tracing above.

## Phase B — measurable internal seam

`reachable(start, max_elements=50000)` is already an independently-defined, directly-callable module-level
function — not an inline block requiring extraction or reimplementation. Calling `scalar(shot, "scene")`
then `reachable(scene)` directly, at the same call sites F1-R4 already established, reproduces **exactly**
the traversal/materialization component in isolation, using the identical, unmodified production code path
— zero semantic difference from what production itself executes internally.

The remaining component — candidate/registry/ownership derivation (the `for obj in objs: ...` DmeRig
filter loop, the `animSetList`/`controls`/`elementList`/`hiddenGroups` reads, and the pure-Python
uniqueness/ownership checks) — is **inline code inside `discover_rig_context()`'s own body**, not a
separately-defined function. It cannot be invoked in isolation without either reimplementing it (forbidden:
"do not copy large sections of production logic") or calling the whole function (which includes the
traversal too).

**Decomposition actually supported by source**: A (fresh topology traversal, `reachable()` alone) is a
clean, real, already-existing seam. B (candidate/context derivation) is not independently callable. C
(returned-context construction) is trivial pure-Python, not separately measurable in any meaningful way.

**A clean seam exists for component A only.** Per Phase B's own instruction, this authorizes preparing a
matched retention measurement that isolates the traversal component specifically — not a three-way clean
split of A/B/C.

## Design consequence: how F1-R5 measures "traversal alone" without abandoning branch determination

F1-R4's own branch determination (`PRE_CAPTURE_UNSUPPORTED` / `NATIVE_POST_ONLY_STATUS_MISMATCH` /
`NATIVE_POST_WRAPPER_SURVIVED` / `COMPOSER_ENTRY_PATH`) requires the *full* `discover_rig_context()` result
(`status`, `rig_handle`, `owned_names_in_order`, `hidden_groups`) at the PRE and NATIVE_POST sites for
every target — this is a genuine logical necessity of knowing which branch applies at all, not a
measurement artifact, and F1-R5 cannot avoid it without also abandoning the exact 62-target/branch schedule
F1-R4 already established. Per the real F1-R4 result, PRE+NATIVE_POST account for 124 of the 250 sites
(62 targets × 2). The **remaining 126 sites** (32 composer-entry targets × 3 extra sites each
[composer-before, composer-after, terminal] = 96, plus 30 status-mismatch targets × 1 extra site each
[terminal] = 30) occur strictly **after** the branch is already known. For these 126 sites specifically,
F1-R5 substitutes the isolated traversal-only seam (`reachable()` alone) in place of the full
`discover_rig_context()` call F1-R4 performed there — since the branch-determination purpose these later
sites would otherwise re-serve is already satisfied. This is a measurement design, disclosed exactly as
such, not a production change: the 124 branch-determining sites remain full, correctness-complete fresh
discovery calls, identical to F1-R4's own; the 126 "extra" sites are narrowed to the traversal-only
component specifically to isolate its own contribution.

## Required conclusions — classification of every suspected source

| Finding | Classification |
|---|---|
| `reachable(scene)`'s own ~4,250-element list materialization, one fresh SWIG wrapper per traversed object, repeated once per discovery call | `MEASUREMENT_CANDIDATE` — real, quantifiable, command-scale (F1-R4's own real numbers already show discovery dominates); this checkpoint exists specifically to further decompose it |
| Full scene-wide scan performed even though the caller already knows the specific target `aset` | `UNKNOWN` — real, but whether a cheaper correct alternative exists in the DME schema cannot be determined from available evidence |
| Ambiguity-uniqueness check (`AMBIGUOUS_MULTIPLE_RIGS`) requiring whole-graph visibility | `SEMANTICALLY_REQUIRED` — proving no other rig exists structurally requires seeing every candidate, absent an alternative authoritative mechanism (none found, per `O3_R3_ENUMERATION_VALIDITY_MECHANISM_SEARCH.md`) |
| `arr()`'s own list-materialization pattern for `animSetList`/`controls`/`elementList`/`hiddenGroups` | `SEMANTICALLY_REQUIRED` at the current scale (dozens of elements, one to two orders of magnitude below `reachable()`'s own ~4,250 — not command-scale on its own) |
| `discover_rig_context()` returning live `rig`/`registry` references when the sole real consumer needs at most one derived string | `SEMANTICALLY_REQUIRED`-adjacent but explicitly **not command-scale** (two extra object references per call, versus thousands from traversal) — recorded for completeness, not pursued here |
| Repeated wrapper construction per graph *edge* (not just per node) inside `element_ref_pairs`'s own child enumeration before the `seen`-handle check discards duplicates | `MEASUREMENT_CANDIDATE` — real, confirmed directly from source, scales with edge count; whether it materially exceeds the per-node cost already captured by `reachable()`'s own `out` list is not separately measured by this checkpoint |
| SWIG-side wrapper pooling/retention independent of Python refcounting | `UNKNOWN` — compiled, closed-source binary behavior, no evidence either way, not invented |
| CPython `pymalloc` arena non-release after a large transient allocation burst | `MEASUREMENT_CANDIDATE` as the most plausible *mechanism* connecting confirmed source-level allocation patterns to F1-R4's own observed process-level retention — not provable as the sole cause from source reading alone, but consistent with every fact this audit did establish |
| Recursive traversal / repeated same-collection re-walk within one discovery call | Confirmed **absent** — not applicable |

No optimization candidate is proposed by this document. Only a measurement design is authorized, per Phase
C below, to further decompose the `MEASUREMENT_CANDIDATE` findings above.
