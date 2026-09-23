# O3-R1 — Corrected Substitution Design

**Status: DESIGN/PROOF CORRECTION ONLY.** No production, integration, or lifecycle code has been
modified. Nothing here authorizes an optimization. Terminal reuse remains deferred/unresolved and is not
addressed here, per explicit instruction.

## Sole candidate (unchanged scope)

Outer native POST → composer-before discovery substitution, **on the supported-active-rig composer-entry
path only**. Not broadened.

## 4. Substitution options

### Option A — No reuse

Keep fresh composer-before discovery exactly as today: `before_rig = discover_rig_context(shot, aset)`
(line 7175-7178) unconditionally re-runs the full `reachable(scene)` traversal plus every downstream
validation read. Zero risk, zero saving. Always available as the fallback.

### Option B — Reuse a historical token, cheap guard only (O3's own original design)

**Rejected.** Per `O3_R1_PREWRITE_FAILURE_CONTRACT.md`, this design provides no protection against any of
the Category 2 (raw-exception) failure modes — `arr(rig,"animSetList")`, `arr(registry,"elementList")`,
`arr(registry,"hiddenGroups")`, and the repeated `handle()` calls can all currently raise before composer
writes, and a historical `status` field says nothing about whether they would raise if freshly
re-attempted now. A handle-equality guard alone (O3's own proposal) also cannot distinguish a genuine
still-valid rig from a "replacement incarnation" occupying a recycled native handle (Astra's objection
#2) — handle equality is *necessary* evidence but not *sufficient* proof of identity continuity.

### Option C — Reuse only the expensive traversal's own output; freshly re-validate every discovery-derived obligation

Reuse **only** the candidate rig identity that `reachable(scene)` + the `DmeRig`-type filter already
produced at outer NATIVE_POST time (i.e., skip re-walking the whole scene graph to re-find "which rig(s)
exist and which one matches this `aset`") — but then **freshly re-execute, in the exact same order, every
downstream validation step discovery currently performs**, immediately before composer's own writes:

1. Freshly re-confirm the candidate rig still matches this `aset` (a single, bounded
   `rig.HasAnimationSet(aset)`-style check — NOT a full scene re-walk).
2. Freshly re-run `arr(rig, "animSetList")`, freshly re-derive the unique registry match (same
   uniqueness check, same `AMBIGUOUS_RIG_REGISTRY` failure mode).
3. Freshly re-run `arr(registry, "elementList")`, freshly re-derive `owned_handles` via the same
   intersection logic (same `STALE_ZERO_OWNERSHIP_RIG` failure mode).
4. Freshly re-run `arr(registry, "hiddenGroups")`.
5. Freshly compute `rig_name` via `name(rig)` (cheap — or reuse the value computed at outer NATIVE_POST
   time if identity is confirmed continuous through step 1, since it is a single string read with no
   correctness-affecting cost either way).

**What this actually reuses**: only the *candidate-identification* work — "which native rig object is
the one to re-validate" — skipping the O(scene-size) `reachable(scene)` traversal and the `DmeRig`-typed
filter loop over its results. **What this does NOT reuse**: any of the Category 1 or Category 2
validation outcomes themselves — every one of those re-runs fresh, with its exact original failure
semantics, at the exact original point in the sequence (before composer writes).

This is the corrected candidate. It is a genuinely narrower, more conservative substitution than O3's own
original proposal.

## 5. No unsupported identity token

The only carried-forward evidence in Option C is a **candidate rig object reference for immediate
re-validation use within the same transaction** — not a trusted historical record. Its explicit purpose:
avoid re-walking the whole scene graph to re-*find* the rig; its explicit non-purpose: substitute for any
of the fresh validation reads listed above. It is:

- **Transaction-local**: never stored on `self`, never persisted past the single target's own
  `run_target_transaction` call, never shared between targets.
- **Not relied upon for topology-change detection via handle equality alone** — Option C does not ask
  "is this handle still equal to what I saw before, therefore nothing changed"; it asks "here is a
  candidate rig, freshly re-validate everything about it right now," which is robust even if the
  underlying native object were somehow replaced (a replacement would simply fail one of the fresh
  re-validation steps, or succeed with genuinely current data — either way, correctness is not contingent
  on handle-value uniqueness assumptions).
- **Fails closed**: any fresh re-validation failure (Category 1 or Category 2) aborts exactly as it does
  today, before any composer write.
- **Immutable-copy discipline for any detached data actually carried forward**: if `rig_name` is carried
  forward from the outer NATIVE_POST discovery rather than recomputed (a discretionary micro-optimization,
  not load-bearing for correctness), it is a single immutable string — not a list/set that could be
  mutated by other code holding an aliased reference (Astra's objection #2). No list/set field is carried
  forward at all in Option C, since `owned_handles`/`owned_names_in_order`/`hidden_groups` are all
  **freshly re-derived**, not reused.

If evidence cannot support even this narrower record, Option A (no reuse) remains available and is never
architecturally excluded.

## 6. Live `rig` capture contract — resolved

Per `O3_R1_DISCOVERY_CAPTURE_CONTRACT.md`: `capture_snapshot_explicit()`'s only use of `rig_context["rig"]`
is one `name()` call to produce `rig_name`; `rig_context["registry"]` is never dereferenced by it at all.

Under Option C, the fresh re-validation sequence (step 1 above) produces a **live, freshly-confirmed**
`rig` object — the same live object `discover_rig_context()` would have produced on a fully fresh call,
just reached via a cheaper path (candidate lookup + confirmation, not full scene re-walk). This live
object is passed into `capture_snapshot_explicit` **exactly as today** — the capture contract is
satisfied without modification, without supplying `None`, and without needing any new capture-side code
change at all. `registry` (never used) requires no special handling.

Candidates evaluated for this step, per instruction not to choose based on elegance alone:

| Candidate | Semantic parity | Failure parity | Live-object lifetime | Complexity | Risk | Net expected saving |
|---|---|---|---|---|---|---|
| Freshly resolve current rig from current target evidence (Option C, as described) | Full — produces the same live objects the fresh path would | Full — same exceptions, same order | Live object exists only within the re-validation call and the capture call immediately following, same as today | Moderate — requires factoring `discover_rig_context` into a "locate candidate" step and a "validate candidate" step (conceptually, not necessarily a literal refactor of the shared function) | Low — closest to today's behavior | Materially reduced (traversal only, not full discovery) but **not yet quantified** — see `O3_R1_MATERIALITY_REEVALUATION.md` |
| Separate `rig_name` acquisition from the rest of discovery (carry forward just the string) | Full for the one field it covers; does not address the other discovery-derived obligations | N/A — does not touch failure semantics at all | No live-object lifetime concern (a string) | Low | Low, but insufficient alone — solves only the capture-contract question, not the pre-write-failure-preservation question | Negligible on its own (skips nothing expensive) |
| Change capture's own input contract to accept explicitly validated detached fields (modify `capture_snapshot_explicit` itself) | Requires touching `capture_snapshot_explicit`'s own signature/body — a wider blast radius than any candidate needs to accept | Depends entirely on the new contract's own design — open-ended risk | N/A | High — modifies a function used by every capture, not just composer-before's own call | **Rejected on risk-to-benefit grounds** — no candidate in this document proposes modifying `capture_snapshot_explicit` itself | N/A |

Recommended: the first candidate (fresh resolution via Option C's own re-validation sequence), combined
optionally with the second (reusing the cheap `rig_name` string specifically, once identity continuity
is confirmed) as a minor refinement, not a substitute for re-validation.

## 7. Unproven interval boundaries — native getters and `sys.stdout.write()`

Astra correctly identified that O2-R1's own static proofs established "no explicit DME write / native
Rebuild / Qt-yield" in the relevant intervals, but did **not** establish "no possible reentrancy via a
native getter call or a logging call."

**What can be established statically**: every native getter call in the traced intervals (`IsVisible()`,
`GetAttribute()`, `GetName()`, `GetTypeString()`, `HasAnimationSet()`, `Count()`, array indexing, etc.)
is a SWIG-bound call into compiled C++ — the Python source contains no evidence of any of these
triggering a Python-level callback, and no `QCoreApplication.processEvents()`/`QTimer.singleShot()`
call exists anywhere in the traced intervals (already confirmed in `O2_R1_OUTER_POST_TO_COMPOSER_BEFORE_
PROOF.md` and `O2_R1_COMPOSER_AFTER_TO_TERMINAL_PROOF.md` by exhaustive grep).

**What cannot be established statically**: whether the underlying C++ implementations of these native
methods could, internally, pump the Qt event loop, invoke a registered Python callback, or otherwise
reenter Python — this is compiled-binary behavior with no Python-source evidence either way.
`sys.stdout.write()` similarly: whether this embedded SFM Python environment's own `sys.stdout` is a
plain, non-reentrant stream object, or a custom object that could (for example) drive a console-widget
repaint synchronously, cannot be determined from this file's own source.

**Classification: `UNRESOLVED`**, honestly, per explicit instruction not to claim impossibility without
evidence.

**Why the candidate remains viable despite this**: Option C's own safety does **not** depend on proving
these calls cannot reenter or cannot trigger a mutation. Because Option C freshly re-executes every
Category 1 and Category 2 validation read (registry resolution, ownership derivation, hiddenGroups,
handle reads) immediately before composer's own writes, **any** mutation or reentrancy-induced change to
the rig/registry/ownership state — from *any* source, proven or not — would be caught by that fresh
re-validation exactly as it is caught today, because that re-validation *is* today's own code, unchanged,
just no longer preceded by a redundant full scene re-walk. This is the concrete sense in which Option C's
"safety does not depend on proving undocumented native non-reentrancy," per the explicit preference this
correction was asked to satisfy.

## 8. Corrected branch map

O3's own document loosely referred to "the reconciled path" and "successful reconciled path" before
reconciliation had actually occurred, imprecisely conflating pre-composer state with post-composer
success. Corrected terminology, used consistently in this document and its companions:

| Phase-truthful name | Description | Reaches composer-before? |
|---|---|---|
| **Supported-active-rig composer-entry path** | `discover_rig_context()` returns `SUPPORTED_ACTIVE_RIG` at both PRE and NATIVE_POST, `plan["status"] == "AUTHORIZED"`, no reconciliation-wrapper survives — the target is *entering* composer, not yet proven to have been correctly composed | **Yes** — this is the path the sole candidate applies to |
| Unrigged PRE | PRE discovery returns `UNRIGGED` | No |
| Ambiguous/stale PRE | PRE discovery returns `AMBIGUOUS_MULTIPLE_RIGS` / `AMBIGUOUS_RIG_REGISTRY` / `STALE_ZERO_OWNERSHIP_RIG` | No |
| Duplicate-semantic fallback | PRE or NATIVE_POST capture raises `ProbeError` on a duplicate group path (`capture_tree()`'s own check) | No |
| Policy fallback | `plan["status"] != "AUTHORIZED"` (line 11673-11691) | No — fires before composer-before |
| Surviving-wrapper fallback | Reconciliation-wrapper groups still present post-Rebuild (`NATIVE_POST_WRAPPER_SURVIVED`, line 11718-11734) | No — fires before composer-before |
| PRE discovery failure | A Category 2 raw exception from `discover_rig_context()`'s own body during the PRE call | No — this is a harness/target-level failure prior to any capture succeeding |
| PRE capture failure | `capture_snapshot_explicit`/`capture_tree` itself raises during PRE (e.g. missing root, duplicate path) → `NATIVE_POST_ONLY_PRE_CAPTURE_UNSUPPORTED` | No |
| Exceptional exits | Any unhandled exception propagating out of `run_target_transaction` itself | No |
| Successful native-only terminal | Native-only fallback (any sub-case) reaching the terminal capture, per `O3_DISCOVERY_CALL_MAP.md` | No — composer never runs on this path |

The sole candidate applies **only** to the first row. It does not describe, and this document does not
claim, that reaching composer-before implies the target *will* be successfully composed — only that it
has entered the composer-entry code path where the candidate's own discovery call lives.

## Summary of this correction

Option C is the corrected design: reuse only the expensive whole-scene-traversal candidate-identification
work; freshly re-execute every discovery-derived validation read (Category 1 status checks and Category 2
raw-exception-capable reads alike) in the same order, before composer writes; satisfy the capture contract
by producing a freshly-confirmed live `rig` object through that re-validation, not by omitting or
replacing it; do not depend on proving native non-reentrancy, since fresh re-validation provides the same
safety net regardless. No implementation is authorized by this document.
