# O3-R1 — Pre-Write Failure Contract

**Status: DESIGN/PROOF CORRECTION ONLY.** No production, integration, or lifecycle code has been
modified. Nothing here authorizes an optimization.

## Decisive finding: two distinct failure categories, not one

Re-reading `discover_rig_context()`'s complete body (line 3299-3436) with a specific failure-semantics
lens (rather than only a status-classification lens, as O3's own analysis did) reveals **discover_rig_
context does not uniformly convert failure into a status value**. Two categories exist:

- **Category 1 — status-value failures** (caught internally, function returns normally with a non-success
  `status` field): `scene is None` → `RIG_CONTEXT_UNAVAILABLE`; `reachable(scene)` raising, caught by an
  explicit `try/except` at line 3328-3332 → `RIG_TRAVERSAL_FAILED`; no matching rig → `UNRIGGED`; more
  than one matching rig → `AMBIGUOUS_MULTIPLE_RIGS`; registry match not unique → `AMBIGUOUS_RIG_REGISTRY`;
  empty ownership intersection → `STALE_ZERO_OWNERSHIP_RIG`.
- **Category 2 — raw, uncaught exceptions** (propagate straight out of `discover_rig_context`, not
  converted to any status value): `arr(rig, "animSetList")` (line 3361) is **not** wrapped in its own
  `try/except` at this call site — if `arr()`'s own internal `ProbeError` fires (its documented failure
  mode: `"Cannot read %s[%d] on %r."`, raised when both `a[i]` and `a.GetValue(i)` fail after `Count()`
  succeeded), it propagates out of `discover_rig_context` entirely. The **same** is true of
  `arr(registry, "elementList")` (line 3394) and `arr(registry, "hiddenGroups")` (line 3429-3432).
  `handle(rig)`/`handle(registry)`/`handle(control)` calls (lines 3381, 3409-3410, 3423-3424, 3387-3390)
  are similarly unwrapped — `handle()` itself (line 860-861, `return int(obj.GetHandle())`) has no
  internal `try/except` at all, so a `GetHandle()` failure on any of these objects propagates raw.

**This is the single most important correction to O3's own analysis**: O3 treated `discover_rig_context`
as producing one clean, always-caught `status` classification. It does not. Several of its own internal
reads can raise **uncaught** exceptions that are not represented by any `status` value at all.

## Enumeration

| Operation | Current failure/result | When, relative to composer writes (7205+) | Must the replacement reproduce it? | Cheaper to reproduce than full discovery? |
|---|---|---|---|---|
| Scene traversal (`scalar(shot,"scene")` / `shot.scene` fallback) | `None` → status `RIG_CONTEXT_UNAVAILABLE` (Category 1) | Before | Only if target identity itself could have become invalid — see `O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md` | N/A — this step is exactly the expensive traversal's own entry point |
| `reachable(scene)` | Caught `try/except` → status `RIG_TRAVERSAL_FAILED` (Category 1) | Before | **This is the operation being proposed for reuse** — its own broad-traversal cost is the target | N/A |
| Rig uniqueness (0 or >1 matches) | Status `UNRIGGED` / `AMBIGUOUS_MULTIPLE_RIGS` (Category 1) | Before | **Yes, in general** — but *if* the candidate rig identity itself is reused rather than re-derived, this specific re-count is exactly what a reuse design would skip; see Option C's own narrower claim below | Depends on what "reuse" means — see design document |
| `arr(rig, "animSetList")` | **Uncaught `ProbeError`** (Category 2) | Before | **Yes — this is a genuine data-integrity check with no status-value equivalent; skipping it silently removes a real pre-write failure mode** | Yes — bounded by the rig's own animSetList size, not the whole scene |
| Registry uniqueness (`len(registry_matches) != 1`) | Status `AMBIGUOUS_RIG_REGISTRY` (Category 1) | Before | Yes | Yes — same bounded cost as above |
| `arr(registry, "elementList")` | **Uncaught `ProbeError`** (Category 2) | Before | **Yes** — same reasoning as `animSetList` | Yes — bounded by the registry's own element count |
| Ownership intersection (empty) | Status `STALE_ZERO_OWNERSHIP_RIG` (Category 1) | Before | Yes | Yes — bounded, local set intersection |
| `arr(registry, "hiddenGroups")` | **Uncaught `ProbeError`** (Category 2) | Before | Yes | Yes — bounded |
| `handle(rig)` / `handle(registry)` / `handle(control)` (repeated) | **Uncaught, unspecified exception** (Category 2 — no `try/except` at all in `handle()` itself) | Before | Yes | Yes — cheap per-call, but called once per relevant object, bounded by rig/registry/control-set size, not scene size |
| `root = aset.GetRootControlGroup()` (in `capture_snapshot_explicit`, not `discover_rig_context`) | Caught, falls back to `scalar(aset,"rootControlGroup")`; if both fail, `raise ProbeError("Animation set has no root control group.")` | Before (this runs before `capture_tree(root)`, itself before any composer write) | Unaffected by any discovery-reuse design — this is inside the capture step, which stays fully fresh in every option considered | N/A — already fresh in every candidate |

## Consequence for design

Every Category 2 (raw-exception) operation above is **currently a genuine pre-write failure mode with no
status-value representation** — a reuse design that merely trusts a historical `status` field (O3's own
original token design) provides **no equivalent protection** against any of these, because `status`
never encoded them in the first place; it only encodes the Category 1 outcomes. A token holding a
historical `"status": "SUPPORTED_ACTIVE_RIG"` says nothing about whether `arr(registry, "elementList")`
would raise `ProbeError` if it were freshly re-attempted right now.

**This is the concrete, mechanical reason O3's original design (Option B / "trust a cheap-guard token")
is insufficient**, independent of the reentrancy question Astra separately raised (`O3_R1_CORRECTED_
SUBSTITUTION_DESIGN.md`, section 7): even in a world with zero reentrancy, zero native mutation, and
perfect identity continuity, the Category 2 operations above are real, bounded-cost validation reads that
a historical token cannot substitute for without re-running them. Any corrected design must re-execute
every Category 2 operation fresh, in the same order, before composer's own writes — see Option C in
`O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md`.

A corrected design is invalid if any Category 1 or Category 2 failure that currently occurs before
composer writes could instead occur after them, or not occur at all.
