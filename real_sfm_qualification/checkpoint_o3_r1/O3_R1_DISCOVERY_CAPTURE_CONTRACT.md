# O3-R1 — Discovery-to-Capture Contract

**Status: DESIGN/PROOF CORRECTION ONLY.** Read-only source analysis of the accepted production
Normalizer (`Rebuild_Control_Groups_Normalizer.py`, SHA-256
`cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`). No production, integration, or
lifecycle code has been modified. Nothing here authorizes an optimization.

This document is produced per Astra's `REVISE_BEFORE_IMPLEMENTATION` disposition on O3. It replaces
O3's own looser token design with an exact, field-by-field contract, derived by reading
`capture_snapshot_explicit()`'s complete body (line 3544-3726) directly — O3's own analysis had only
partially read this function.

## `discover_rig_context()`'s complete return shape (line 3299-3436, unchanged from O3)

```python
result = {
    "status": str,               "rig": <live>,          "registry": <live>,
    "rig_handle": int|None,      "registry_handle": int|None,
    "matching_rig_count": int,   "reachable_rig_count": int,
    "owned_handles": set(int),   "owned_names_in_order": [str],
    "hidden_groups": [str],
}
```

## Exact field-by-field contract

| Field | Type | Detached or live? | Consumer(s) | Consumed by `capture_snapshot_explicit`? | Consumed by classification/planning? | Consumed by composer? | Diagnostics only? | Production-read failure semantics |
|---|---|---|---|---|---|---|---|---|
| `status` | str | Detached | `capture_snapshot_explicit` line 3658-3660 (→ `rig_status` in the returned snapshot); `capture_snapshot_explicit` line 3637-3639 (gates whether `owned_names` is computed at all) | **Yes**, directly | No — only indirectly, via `rig_status` in the already-captured `pre`/`post` snapshot dicts (see below) | No — same, indirectly via snapshot fields | No | N/A — it is the terminal classification `discover_rig_context()`'s own body produces; cannot itself fail further |
| `rig` | **live `DmeRig` object** | **Live** | `capture_snapshot_explicit` line 3661-3667, **exactly one use**: `name(rig_context["rig"])` → `rig_name` string. **No other line in the entire function dereferences this object.** | **Yes, but only for one cheap `GetName()` call** — see "The rig_name fix" below | No | No (composer never receives `rig_context` at all — see below) | No | The `name()` wrapper (line 863-867) itself catches `Exception` and returns `u"<UNNAMED>"` on failure — never raises out of `capture_snapshot_explicit` |
| `registry` | **live `DmeRigAnimSetElements` object** | **Live** | **Never dereferenced anywhere in `capture_snapshot_explicit`'s body.** Confirmed by exhaustive read of lines 3544-3726 — only `registry_handle` (the detached int) is read (line 3671-3673). | **No — confirmed unused** | No | No | **Effectively diagnostic-only from `capture_snapshot_explicit`'s own perspective** — its live form serves no purpose downstream of discovery once `registry_handle` has been extracted | N/A |
| `rig_handle` | int | Detached | `capture_snapshot_explicit` line 3668-3670 → `rig_handle` in the snapshot | Yes, directly (as a plain int) | No — indirectly via snapshot | No | No | N/A — plain data |
| `registry_handle` | int | Detached | `capture_snapshot_explicit` line 3671-3673 → `registry_handle` in the snapshot | Yes, directly | No — indirectly | No | No | N/A |
| `matching_rig_count` | int | Detached | `capture_snapshot_explicit` line 3674-3676 → snapshot field of the same name | Yes | No — indirectly | No | Effectively diagnostic (used for anomaly detection, not control flow, in the reading done so far) | N/A |
| `reachable_rig_count` | int | Detached | `capture_snapshot_explicit` line 3677-3679 → snapshot field | Yes | No — indirectly | No | Effectively diagnostic | N/A |
| `owned_handles` | set(int) | Detached (but see mutability note below) | `capture_snapshot_explicit` line 3637-3649: gates and populates `owned_names`/`owned_control_name_set` in the returned snapshot **only when `status == "SUPPORTED_ACTIVE_RIG"`** | Yes, conditionally | No — indirectly, via `owned_control_names_in_animation_set_order`/`owned_control_name_set` in the snapshot | No | No — directly drives snapshot content | N/A — a fresh `set()` literal in `discover_rig_context`'s own body (line 3308, repopulated at 3400-3403), not shared with any other retained structure at the time of writing, but see the mutability caveat in `O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md` |
| `owned_names_in_order` | list(str) | Detached | Also embedded via the recomputation at line 3645-3649 (note: `capture_snapshot_explicit` recomputes its own `owned_names` from `control_objs` + `owned_handles`, rather than reading `rig_context["owned_names_in_order"]` directly) | **No — not read directly; only `owned_handles` is read, and `owned_names` is independently re-derived** | No | No | Diagnostic-adjacent — present in `discover_rig_context`'s own return for callers that want it without recomputation, but `capture_snapshot_explicit` itself does not use it | N/A |
| `hidden_groups` | list(str) | Detached | `capture_snapshot_explicit` line 3691-3695 → `hidden_groups` in the snapshot (a fresh `list()` copy is made here, not the same list object) | Yes, directly | No — indirectly | No | No | N/A |

## The `rig_name` fix — resolving Astra's capture-contract objection directly

Astra's objection #3 is now precisely answered: `capture_snapshot_explicit()` does access
`rig_context["rig"]`, but **only** to compute `name(rig_context["rig"])` — a single, cheap
`obj.GetName()` call. It never uses the live object for anything else (no method call beyond `GetName()`,
no attribute traversal, no structural read). This means the live `rig` reference is **not architecturally
required** by `capture_snapshot_explicit` — only the **string it produces** (`rig_name`) is required.

**Correction to O3's own token**: the reusable identity record must include a pre-computed `rig_name`
field (the result of calling `name(rig)` once, at the time of the *original* discovery, before the live
reference is ever allowed to go out of scope) — not attempt to carry the live `rig` reference forward, and
not attempt a "fresh handle-based re-resolution" (O3's own vague fallback, now understood as unnecessary
complexity: a single string, computed once, is sufficient). `registry` requires no equivalent handling at
all, since it is never dereferenced.

**This does not yet authorize omitting `rig` from any call.** The corrected design in
`O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md` addresses exactly how `capture_snapshot_explicit`'s own input
contract is satisfied without supplying a live object nor supplying `None` (both of which Astra correctly
identified as changing the semantic result — `None` specifically triggers `capture_snapshot_explicit`'s
own internal `discover_rig_context()` call, line 3550-3554, which is not what a reuse design intends).

## Section 2 — three separated obligations

**A. Target identity** — which animation set/shot/transaction is being processed. Established by
`(shot, aset)` themselves (the Python object references passed into `run_target_transaction`, confirmed
in O1's own audit to be freshly re-resolved per target via `contextualizer_resolve_resume_target()`
before each target's own transaction begins — unchanged by anything in this document). Detached identity
evidence: `handle(aset)` (an int), already used elsewhere in this codebase for exactly this purpose.

**B. Rig/topology discovery** — which current rig and registry correspond to that target, with current
reachability/ownership/hidden-groups evidence. Established **exclusively** by `discover_rig_context()`
itself (line 3299-3436) — the function under discussion for reuse.

**C. Semantic tree capture** — current groups, controls, memberships, metadata, ordering. Established by
`capture_tree()` (line 1200-1334), called from inside `capture_snapshot_explicit()` — **entirely
untouched by any reuse design considered here**; O3's own governing constraint (preserve fresh semantic
reads) already excluded this from any candidate, and this remains true in O3-R1.

## Which obligations must remain freshly established immediately before composer writes

Per Astra's objection #4 (fresh discovery has real failure semantics that must occur *before* mutation,
not be silently deferred past it): **obligation B (rig/topology discovery) is where discover_rig_context's
own fail-closed validation lives** — rig uniqueness (`AMBIGUOUS_MULTIPLE_RIGS`), registry uniqueness
(`AMBIGUOUS_RIG_REGISTRY`), and ownership non-emptiness (`STALE_ZERO_OWNERSHIP_RIG`) are all determined
inside `discover_rig_context()`'s own body, all before composer's own writes (lines 7205+) in the current
code. Any reuse design must preserve this exact validation, at this exact point in the sequence, not
merely trust a historical `status` value computed earlier. See `O3_R1_PREWRITE_FAILURE_CONTRACT.md` for
the full enumeration this requirement is based on, and
`O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md` (Option C) for how the corrected design satisfies it.
