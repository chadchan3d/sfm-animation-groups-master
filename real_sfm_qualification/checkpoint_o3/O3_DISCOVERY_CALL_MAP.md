# O3 — Discovery Call Map

**Status: DESIGN/PROOF ONLY.** Read-only source analysis of the accepted production Normalizer
(`Rebuild_Control_Groups_Normalizer.py`, SHA-256
`cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`). No production, integration, or
lifecycle code has been modified. Nothing here authorizes an optimization.

## Governing question

> Within the Normalizer's required post-Rebuild pathway, can expensive whole-shot rig discovery be
> safely reused across semantic capture boundaries where rig identity cannot have changed, while still
> performing fresh semantic reads whenever freshness is required?

## `discover_rig_context(shot, aset)` — exact return shape (line 3299-3436)

```python
result = {
    "status": "UNRIGGED",              # str -- terminal classification (see below)
    "rig": None,                       # LIVE DmeRig native object reference, or None
    "registry": None,                  # LIVE DmeRigAnimSetElements native object reference, or None
    "rig_handle": None,                # int native handle (detached identity), or None
    "registry_handle": None,           # int native handle (detached identity), or None
    "matching_rig_count": 0,           # int -- cheap, already computed
    "reachable_rig_count": 0,          # int -- cheap, already computed
    "owned_handles": set(),            # set of int handles -- detached, plain Python
    "owned_names_in_order": [],        # list of unicode strings -- detached, plain Python
    "hidden_groups": [],               # list of unicode strings -- detached, plain Python
}
```

Possible terminal `status` values (each an early `return`): `RIG_CONTEXT_UNAVAILABLE` (no `scene`),
`RIG_TRAVERSAL_FAILED` (`reachable(scene)` raised), `UNRIGGED` (no matching rig), `AMBIGUOUS_MULTIPLE_RIGS`
(more than one matching rig), `AMBIGUOUS_RIG_REGISTRY` (registry match not unique — `rig`/`rig_handle`
set here, `registry` fields not), `STALE_ZERO_OWNERSHIP_RIG` (no owned controls — `rig`/`registry` set),
and the only fully-successful terminal state, `SUPPORTED_ACTIVE_RIG` (all fields populated).

**The expensive part**: `objs = reachable(scene)` (line 3329) — a broad, unbounded traversal of every
DME element reachable from the shot's own `scene` attribute (via `element_ref_pairs`/`iter_attributes`,
capped at 50,000 elements), filtered down to `DmeRig`-typed objects. This is O(scene size), not O(rig
size) — it re-walks the *entire* shot graph every single call, regardless of how small the actual rig
of interest is. This is the measured ~0.15-0.19s-per-call cost.

## Exact call sites — `capture_snapshot_explicit(shot, aset, label, rig_context=None)`

`capture_snapshot_explicit` (line 3544-3549) itself contains: `if rig_context is None: rig_context =
discover_rig_context(shot, aset)` (line 3550-3554) — meaning a caller *could* pass an already-computed
`rig_context` to skip an internal discovery call. **Directly confirmed by reading all 5 call sites: none
of them do.** Every one explicitly computes its own fresh `rig_context` immediately before its own call,
even in cases where an earlier discovery result is already available in scope:

| # | Label | Capture line | Discovery call (immediately preceding) | Caller / function |
|---|---|---|---|---|
| 1 | `PRE` | 11267 | fresh, inline (confirmed in O2-R1's own prior work: `pre_rig = discover_rig_context(shot, aset)` immediately before) | `run_target_transaction` (11198) |
| 2 | `NATIVE_POST` | 11487 | fresh, inline: `post_rig = discover_rig_context(shot, aset)` immediately before (line ~11482) | `run_target_transaction` |
| 3 | `PRODUCTION_GENERIC_COMPOSER_PRE` | 7180-7185 | fresh, inline: `before_rig = discover_rig_context(shot, aset)` (line 7175-7178) — **confirmed NOT reused from the `post`/`post_rig` computed by the caller**; `production_generic_composer`'s own signature (`root, pre, post, master, shot, aset, plan, uniformity_plan`, line 7162-7170) does not even accept a `rig_context` parameter | `production_generic_composer` (7162) |
| 4 | `PRODUCTION_GENERIC_COMPOSER_POST` | 7529-7534 | fresh, inline: `after_rig = discover_rig_context(shot, aset)` (line 7524-7527) | `production_generic_composer` |
| 5 | `PRODUCTION_SEMANTIC_FINGERPRINT` | 5254-5259 | fresh, inline: `rig_context = discover_rig_context(shot, aset)` (line 5249-5252) | `semantic_target_fingerprint` (5246) |

**Confirms and corrects O1's own earlier characterization**: this is not merely "3-5 captures per
target" — it is **exactly 5 independent, fresh, full-cost `discover_rig_context()` calls per target on
the reconciled path**, each re-walking the entire shot scene graph from scratch, with zero reuse of any
of the 4 prior discoveries' own results — even though, as shown below, several of these intervals are
already proven to contain no operation that could change the answer.

## Reconciled supported-active-rig path — full discovery sequence, execution order

| # | discover_rig_context() call | Before/after native Rebuild | Before/after composer's own DME writes | Before/after Undo restoration | Before/after Master reassertion | Qt/event-loop boundary since prior? | DME mutation possible since prior? | Native mutation possible since prior? | Fields actually consumed downstream | Preliminary classification |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Line ~11262 (PRE, `pre_rig`) | Before (this is the pre-Rebuild baseline) | Before | Before (Undo is disabled around this point, not yet restored) | N/A (first discovery this transaction) | N/A (first) | N/A (first) | N/A (first) | `status` (compared against `post`'s own status for drift detection), full `pre` snapshot content | `FRESH_DISCOVERY_REQUIRED` — this is the pre-Rebuild identity baseline; nothing to reuse from |
| 2 | Line ~11482 (`post_rig`) | **After** native Rebuild (line 11464) | Before composer's own writes (composer hasn't run yet) | Before Undo restoration | Before Master reassertion | No (same synchronous flow) | **N/A for the interval before this call** (native Rebuild itself is the intended mutation) — but this discovery is REQUIRED because native Rebuild is exactly the operation expected to have changed rig/group state | Native Rebuild already ran (line 11464) — this discovery exists specifically to observe its effect | `status` (fallback-branch check against `plan["status"]`), full `post` snapshot content, `pre`/`post` diff at 11494-11587 | `FRESH_DISCOVERY_REQUIRED` — native Rebuild is the one operation in this whole transaction explicitly expected to invalidate any prior discovery; this call's entire purpose is observing that change |
| 3 | Line 7175 (`before_rig`, composer-before) | After native Rebuild | Before composer's own DME writes (mutation primitives at 7205+ all come later) | Before Undo restoration | Before Master reassertion | No (per `O2_R1_OUTER_POST_TO_COMPOSER_BEFORE_PROOF.md`, exhaustively confirmed: no `processEvents`/`singleShot` anywhere in the 11492-11897 interval) | **No** — the SAME proof exhaustively confirmed no DME write anywhere between outer POST and composer-before | **No** — no native mutation call exists in that interval either (confirmed by whole-file grep for every write-capable primitive) | `rig`/`status` implicitly via the `before` snapshot's own `rig_status` field, consumed in composer's own later comparison logic | **`REUSE_CANDIDATE`** — the interval since discovery #2 (`post_rig`) is PROVEN (not merely presumed) mutation-free at both the DME and native level; discovery #2's own result is data-equivalent to what #3 would independently compute |
| 4 | Line 7524 (`after_rig`, composer-after) | After native Rebuild | **After** composer's own DME writes (the mutation primitives at lines 7205, 7222, 7239, 7293, 7391, 7513, 7519 all execute before this point, per `production_reorder_contextual_tree()` at 7519-7522 being the last of them) | Before Undo restoration | Before Master reassertion | No (still inside the same synchronous `production_generic_composer` call) | **Yes, by design** — this discovery exists specifically to observe composer's own just-applied mutations | No native mutation (composer's writes are DME-level, not native Rebuild) | `after` snapshot content, compared against `desired` in `failures` check (7536-8010) | `FRESH_DISCOVERY_REQUIRED` — composer's own writes are exactly the mutation this discovery must observe; cannot reuse #3 (pre-mutation) here |
| 5 | Line 5249 (terminal, `semantic_target_fingerprint`) | After native Rebuild | After composer's own DME writes (composer already returned) | **After** Undo restoration (`TARGET_UNDO_RESTORE_GATE`, ~12005-12017) | **After** Master reassertion (`self.assert_master_stable()`, ~12098) | No (per `O2_R1_COMPOSER_AFTER_TO_TERMINAL_PROOF.md`, exhaustively confirmed: no Qt yield in this interval) | **No** — the SAME proof exhaustively confirmed no DME write anywhere between composer-after and terminal (undo-restore and protect-release are non-content state changes only) | No native mutation (protect-handle *release* is not a mutation) | `status`/full snapshot, checked only for `is not None` (12134) then immediately `del`-eted (12151) — content is provably unused, per the production source's own comment | **`REUSE_CANDIDATE`** for the discovery portion specifically — the interval since discovery #4 (`after_rig`) is proven mutation-free at the DME level (per the existing proof); the *capture* retains a distinct procedural purpose (attesting post-cleanup capturability, per the existing proof) but that purpose does not depend on re-walking the scene graph, only on the capture succeeding |

## Native-only fallback path — TWO distinct sub-cases, both reaching TERMINAL

Confirmed (correcting an earlier draft of this document): `terminal` (`semantic_target_fingerprint()`,
line 5246, called at line ~12129) is reached **unconditionally on every branch**, including both
fallback sub-cases below — it is not exclusive to the reconciled path. `NativePostFallback` is one
exception class raised from three distinct trigger points, all caught by the same downstream handler
that falls through into the same terminal-capture code:

**Sub-case A — policy/wrapper fallback** (`plan["status"] != "AUTHORIZED"`, line 11673-11691, or
reconciliation-wrapper groups surviving post-Rebuild, `NATIVE_POST_WRAPPER_SURVIVED`, line 11718-11734):
fires **after** NATIVE_POST's own discovery/capture succeed, but **before** composer-before (line 7180)
is ever reached. Discovery sequence: PRE (`FRESH_DISCOVERY_REQUIRED`) → NATIVE_POST
(`FRESH_DISCOVERY_REQUIRED`) → TERMINAL. Since composer never runs in this sub-case, **nothing mutates
DME state between NATIVE_POST's own discovery and TERMINAL's own discovery** — an even stronger
mutation-free interval than the reconciled path's own TERMINAL case (no composer-writes phase exists to
have happened at all in this sub-case). Classification: **`REUSE_CANDIDATE`** for TERMINAL's discovery
portion, same caveat as the reconciled path (terminal's capture itself retains its distinct
post-cleanup-capturability purpose, per `O2_R1_COMPOSER_AFTER_TO_TERMINAL_PROOF.md`, which did not
depend on which branch was taken).

**Sub-case B — PRE-unsupported** (`NATIVE_POST_ONLY_PRE_CAPTURE_UNSUPPORTED`, line 11476-11480): fires
when the PRE capture itself raises (e.g. `ProbeError` on a duplicate group path, or a missing root
control group) — caught at lines 11262-11278. **Native Rebuild still runs unconditionally regardless**
(line 11464 has no gate on `pre_capture_ok`). Immediately after, if the PRE capture had failed, the
fallback fires **before NATIVE_POST's own discovery (line 11482) is ever reached at all**. Discovery
sequence: PRE (`FRESH_DISCOVERY_REQUIRED` — its own capture already failed, nothing usable to reuse from)
→ TERMINAL. Classification: **`UNRESOLVED`** — no prior *successful* discovery of this target's
post-Rebuild state exists in this sub-case (NATIVE_POST's own discovery/capture never ran at all), so
there is no proven-mutation-free interval to reuse across; reuse would require, at minimum, confirming
this sub-case's TERMINAL discovery is genuinely a *fresh* requirement here, not merely defaulting to
`FRESH_DISCOVERY_REQUIRED` without proof either way. `discover_rig_context()` itself never raises (every
branch in its own body returns a status dict, confirmed no unguarded `raise` exists in it) — the failure
is always inside the *capture* (`capture_snapshot_explicit`/`capture_tree`), not discovery.

`discover_rig_context()` returning a non-`SUPPORTED_ACTIVE_RIG` status (`UNRIGGED`,
`AMBIGUOUS_MULTIPLE_RIGS`, `AMBIGUOUS_RIG_REGISTRY`, `STALE_ZERO_OWNERSHIP_RIG`,
`RIG_CONTEXT_UNAVAILABLE`, `RIG_TRAVERSAL_FAILED`) is a *status value* discovery #1 (PRE) itself already
reports — not a structurally distinct code path with its own discovery-call sequence.

## Discovery-call fields consumed (confirms discovery output is not discardable)

`capture_snapshot_explicit`'s own return dict directly embeds every field of its `rig_context` argument:
`rig_status`, `rig_name`, `rig_handle`, `registry_handle`, `matching_rig_count`, `reachable_rig_count`,
`hidden_groups`, and (when `status == "SUPPORTED_ACTIVE_RIG"`)
`owned_control_names_in_animation_set_order`/`owned_control_name_set` — all folded directly into the
capture's own snapshot content (lines ~3637-3650). Discovery's own output is not merely a gate-check
that could be discarded after validation; it is part of the semantic content every downstream comparison
reads. This matters for reuse design: reusing a discovery result changes *where in time* those specific
snapshot fields were computed, not their meaning — for the proven-mutation-free intervals (calls #3 and
#5 above), the reused values would be provably identical to a fresh recomputation, since nothing capable
of changing rig identity/ownership/hidden-groups occurred in between.

## Summary

| Branch | Discovery sequence | Reuse candidates |
|---|---|---|
| Reconciled (full success) | PRE → NATIVE_POST → COMPOSER_PRE → COMPOSER_POST → TERMINAL (5 calls) | COMPOSER_PRE (#3), TERMINAL (#5, discovery portion only) |
| Native-only fallback, policy/wrapper (sub-case A) | PRE → NATIVE_POST → TERMINAL (3 calls) | TERMINAL (discovery portion only) — even stronger mutation-free interval than the reconciled path, since no composer-writes phase occurs |
| Native-only fallback, PRE-unsupported (sub-case B) | PRE → TERMINAL (2 calls) | None — `UNRESOLVED`, no prior successful discovery exists to reuse from |

Every reuse candidate identified is on the **discovery portion only** — no candidate proposes reusing a
full semantic *capture* (`capture_snapshot_explicit`'s own tree-construction work), consistent with the
governing rule's requirement to preserve fresh semantic reads. This directly grounds sections 2-4.
