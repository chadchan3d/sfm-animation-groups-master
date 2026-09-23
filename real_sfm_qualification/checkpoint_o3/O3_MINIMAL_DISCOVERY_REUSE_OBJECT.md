# O3 — Minimal Discovery Reuse Object

**Status: DESIGN/PROOF ONLY.** No production, integration, or lifecycle code has been modified. Nothing
here authorizes an optimization.

## Preferred vs. forbidden design (restated, governs every field decision below)

**Preferred**: reuse expensive discovery *knowledge* while still freshly reading semantic group/control
state on every capture. **Forbidden**: retain rich live DME graphs or semantic snapshots across unsafe
boundaries. This document evaluates `discover_rig_context()`'s own return fields (see
`O3_DISCOVERY_CALL_MAP.md` for the exact shape, `Rebuild_Control_Groups_Normalizer.py` line 3299-3436)
against that standard — it does **not** propose caching a full semantic snapshot.

## Per-field evaluation

| Field | Plain data or live object? | Native Rebuild could invalidate? | Contextual writes could invalidate? | Qt boundary could invalidate? | Shot activation could invalidate? | Target re-resolution could invalidate? | Identity re-validated at next use? | Can stale reuse fail closed? |
|---|---|---|---|---|---|---|---|---|
| `status` (str) | Plain | Yes, in general — but not within either proven-mutation-free reuse interval (see below) | Yes, in general — same caveat | N/A within one transaction (no Qt yield in either reuse interval, proven) | Out of scope — reuse is proposed strictly within one target's own transaction, never across the Qt-deferred inter-target gap | Out of scope — same reasoning | Not automatically; a design must add this | Yes — a stale `status` (e.g. no longer `SUPPORTED_ACTIVE_RIG`) is trivially detectable and must abort/fall back to fresh discovery |
| `rig` (**LIVE DmeRig native object reference**) | **Live native object** | Yes | Yes | Possible in general (native object lifetime is not guaranteed across any deferred boundary) | Yes, if carried across a target/shot boundary | Yes | Not by the object reference itself — a stale reference could silently point to a destroyed/reparented element | **This is the forbidden category.** Reuse of the object reference itself is explicitly out of scope |
| `registry` (**LIVE DmeRigAnimSetElements native object reference**) | **Live native object** | Yes | Yes | Same as `rig` | Same as `rig` | Same as `rig` | Same as `rig` | **Forbidden category**, same as `rig` |
| `rig_handle` (int) | Plain (detached identity token) | The *value* it identifies could change, but the int itself is inert data | Same | N/A within a proven-mutation-free interval | Out of scope (see above) | Out of scope | Not automatically — but cheap to re-check (`handle(rig) == cached_rig_handle`) | **Yes** — this is exactly the class of "detached reference/ID needed to locate the same rig again" the governing rule prefers |
| `registry_handle` (int) | Plain | Same as `rig_handle` | Same | Same | Out of scope | Out of scope | Same | Same as `rig_handle` |
| `matching_rig_count` / `reachable_rig_count` (int) | Plain | Could change if rig topology changes | Same | N/A within proven interval | Out of scope | Out of scope | Cheap to re-derive if ever needed | Yes — pure counts, trivially safe to carry as a snapshot-at-time-of-computation value |
| `owned_handles` (set of int) | Plain (detached identity set) | Could change if ownership changes (native Rebuild or composer writes) | Same | N/A within proven interval | Out of scope | Out of scope | Not automatically | Yes — a set of ints, cheap to compare against a fresh cheap re-check if a design wants one |
| `owned_names_in_order` (list of str) | Plain | Same as `owned_handles` | Same | Same | Out of scope | Out of scope | Same | Yes |
| `hidden_groups` (list of str) | Plain | Could change if registry's own hidden-groups list changes | Same | Same | Out of scope | Out of scope | Same | Yes |

## The minimal reusable object

**Everything in `discover_rig_context()`'s own return dict *except* the two live native references
(`rig`, `registry`) is already plain, detached Python data**, safe by construction to hold beyond the
call that produced it — the only question is whether the *values* remain *correct* to reuse, which is a
freshness question (answered per-interval in `O3_DISCOVERY_CALL_MAP.md`), not a live-object-safety
question.

The proposed minimal reusable object, if a reuse design is pursued, is therefore:

```python
DiscoveryIdentityToken = {
    "status": rig_context["status"],
    "rig_handle": rig_context["rig_handle"],
    "registry_handle": rig_context["registry_handle"],
    "matching_rig_count": rig_context["matching_rig_count"],
    "reachable_rig_count": rig_context["reachable_rig_count"],
    "owned_handles": rig_context["owned_handles"],
    "owned_names_in_order": rig_context["owned_names_in_order"],
    "hidden_groups": rig_context["hidden_groups"],
    # Deliberately excluded: "rig", "registry" (live native references)
}
```

**This is not a cache.** It is not persisted beyond a single target's own transaction, not stored on
`self`, not retained across the Qt-deferred inter-target boundary, and not shared between targets. Its
scope is strictly bounded to the SAME proven-mutation-free interval established in
`O3_DISCOVERY_CALL_MAP.md` (e.g., held from NATIVE_POST's own discovery through composer-before's own
capture, then discarded — never carried further).

**Why exclude `rig`/`registry` even though reuse would be "faster"?** Any downstream code that needs the
*live* rig/registry object (as opposed to its identity/handle) would still need to re-resolve it via a
fresh, cheap handle-based lookup rather than trusting a carried-forward live reference — this preserves
the "no runtime DME cache across callbacks" constraint and matches how the rest of this codebase already
treats native references (e.g., `contextualizer_resolve_resume_target()`'s own re-resolution pattern,
established in the O1 audit, which re-resolves `aset` fresh via `(ptr, name)` matching rather than
trusting a stored reference for exactly this reason).

## Required stale-state guard

Even within a proven-mutation-free interval, a defensible design should not rely *solely* on the static
proof holding forever as the code evolves. A minimal, cheap fail-closed guard: before consuming a reused
`DiscoveryIdentityToken`, re-verify `handle(aset) == expected_aset_handle` (the target identity itself)
and that `token["status"] == "SUPPORTED_ACTIVE_RIG"` (or whatever status was captured) still represents a
usable state. This is a single handle comparison plus a string equality check — negligible cost compared
to the ~0.15-0.19s `reachable(scene)` traversal being avoided — and it converts "the interval happens to
be mutation-free today" into "the design fails safely if that ever stops being true," rather than
silently returning stale data. See `O3_IMPLEMENTATION_RECOMMENDATION.md` for how this guard is proposed
to be wired into the one recommended candidate.
