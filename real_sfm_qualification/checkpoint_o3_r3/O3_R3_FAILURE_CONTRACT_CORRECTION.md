# O3-R3 — Failure Contract Correction

**Status: DESIGN/PROOF CORRECTION ONLY.** No production, integration, or lifecycle code has been modified.
This document corrects `O3_R1_PREWRITE_FAILURE_CONTRACT.md` and the branch-map description in
`O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md` per Astra's second review: several discovery-related failures were
previously described as uniform fail-closed aborts when the actual behavior, re-verified directly against
the pinned production source, is more granular — some are caught internally and degrade gracefully, some
are caught and simply skip one element, some propagate raw, and one discovery result (`before`, at
composer-before) turns out not to be checked at all.

## Corrections, each re-verified directly against source this turn

### 1. `HasAnimationSet()` exceptions are caught, not propagated

`discover_rig_context()` lines 3340-3344:

```python
try:
    if bool(obj.HasAnimationSet(aset)):
        matches.append(obj)
except Exception:
    pass
```

A `HasAnimationSet()` failure on any candidate object is silently swallowed — that candidate is simply not
added to `matches`. This is **not** listed in `O3_R1_PREWRITE_FAILURE_CONTRACT.md`'s enumeration table at
all; it is now added below. It is a Category-1-like caught behavior, but with a subtlety the prior
enumeration's Category 1/Category 2 split did not capture: a failure here does not produce a distinct
`status` value either — it is indistinguishable, from the caller's perspective, from the object genuinely
not matching.

### 2. Binding-handle comparison exceptions are treated as false, not propagated

`discover_rig_context()` lines 3367-3373:

```python
try:
    same = bool(
        linked is not None
        and handle(linked) == handle(aset)
    )
except Exception:
    same = False
```

The prior enumeration table listed `handle(rig)` / `handle(registry)` / `handle(control)` as uniformly
**Category 2 — uncaught**. That is correct for the *standalone* `handle()` calls used to populate result
fields (lines 3381, 3409-3410, 3423-3424, and the per-control loop at 3387-3390) — those are genuinely
unwrapped. It is **incorrect** for the two `handle()` calls at line 3370 (`handle(linked)`,
`handle(aset)`), which are wrapped by the surrounding `try/except` above and degrade to `same = False` (the
candidate registry record is simply not matched) rather than raising. This is a real correction: not every
`handle()` call site shares the same failure behavior; it depends on which call site.

### 3. Some registry-element handle failures are skipped, not propagated

`discover_rig_context()` lines 3394-3398:

```python
for obj in arr(registry, "elementList"):
    try:
        registry_handles.add(handle(obj))
    except Exception:
        pass
```

The prior enumeration table's row for `arr(registry, "elementList")` correctly identifies the `arr()` call
itself as Category 2 (unwrapped, can raise from `arr()`'s own internal `ProbeError`). But it did not
separately note that **each individual `handle(obj)` call inside this loop, over `arr()`'s own returned
elements, is independently wrapped** — a `GetHandle()` failure on one element is silently skipped (that
element is simply absent from `registry_handles`), not a raw exception that aborts the whole discovery
call. This is a finer grain than the prior table represented.

### 4. Some handle/array failures genuinely propagate — re-confirmed, unchanged

Re-verified directly: `arr(rig, "animSetList")` (line 3361), `arr(aset, "controls")` (line 3386),
`arr(registry, "hiddenGroups")` (lines 3429-3432), and the standalone `handle(rig)` / `handle(registry)`
calls used to populate result fields (lines 3381, 3409-3410, 3423-3424) have **no** wrapping `try/except` at
their own call sites. This part of the prior enumeration is accurate and is not corrected.

### 5. `name()` catches its own failure and yields `<UNNAMED>` — not previously stated

`name(obj)` (module-level helper, line 863-867):

```python
def name(obj):
    try:
        return to_unicode(obj.GetName())
    except Exception:
        return u"<UNNAMED>"
```

Every call to `name()` anywhere in discovery or capture (including the one live-`rig` dereference inside
`capture_snapshot_explicit`, line 3661-3667 — the specific call `O3_R1_DISCOVERY_CAPTURE_CONTRACT.md`
already identified as the sole use of the live `rig` object) degrades gracefully to a placeholder string
rather than raising. This means a stale or otherwise-degraded `rig` reference passed into
`capture_snapshot_explicit` would **not** necessarily surface as a Python exception at that call site — it
could silently become `rig_name = u"<UNNAMED>"` and the code would continue. (`GetHandle()`, used by
`handle()`, has no equivalent protection — see `O3_R3_COUNTEREXAMPLE_ANALYSIS.md` case F for why this
matters for a *retained* native wrapper specifically, as opposed to a fresh one.)

### 6. Composer-before's own discovery status is never subsequently checked — a new finding, not previously documented anywhere

Directly re-tracing `production_generic_composer()` (line 7162 onward) for every later use of `before` /
`before_rig` (the composer-before discovery+capture, lines 7175-7185): **there is none.** `before` and
`before_rig` are referenced only at their own creation; they do not appear again anywhere else in the
function body, and the function's own return dict (lines 8066-8090) does not include them either. Composer
writes are driven entirely by `plan` / `uniformity_plan` / `rig_source`, all derived from `pre` and `post`
(the captures taken *before* and *immediately after* native Rebuild, at lines 11267 and 11487 respectively)
— **not** from `before`. This directly corrects the implicit assumption, present in prior O3-series
documents, that composer-before's own discovery result gates or informs composer's write decisions. It
does not. Its *value* is unconsumed by production. What remains load-bearing is only its **failure
behavior**: if `discover_rig_context()` raises an uncaught (Category 2) exception during this call, that
exception propagates out of `production_generic_composer()` before `production_ensure_group_path()`'s own
first write (see next item) — so an exception here still correctly prevents a write, even though a
*successful* result here proves nothing about what gets written. This is the precise sense in which
Astra's framing ("the decisive missing property... enumeration validity") matters for *safety* (case D in
`O3_R3_COUNTEREXAMPLE_ANALYSIS.md`) even though it does not matter for *data correctness* of the write
itself.

### 7. The actual first potential composer mutation boundary is `production_ensure_group_path()`, not composer entry itself

Re-traced directly: `production_generic_composer()`'s own first statements (lines 7171-7185) are a pure
dict read (`plan["rig_source"]`) followed by composer-before's own discovery+capture — no write. The first
write-capable call is `production_ensure_group_path()` (line 7293, inside the `for target_path in
required_paths:` loop), whose own body (line 6658 onward) calls `create_independent_group()`,
`apply_source_metadata()`, `set_visible()`, and `rename_group()` — the actual scene-mutating operations —
but **only** inside the `if existing is not None: ... else: ...` branch that fires when a required
technical group does not already exist (lines 6691-6743). This is the corrected first-mutation boundary,
replacing any prior looser description of "composer entry" as the boundary.

### 8. PRE / native-POST fallback behavior — corrected, not a uniform fail-closed abort

Re-traced `run_target_transaction`, lines 11262-11278: a Category 2 raw exception (or any other failure)
during the **PRE** discovery+capture is caught by a local `try/except` and recorded as
`pre_capture_ok = False` — this does **not** abort the target transaction. Execution continues: undo is
disabled, the native-Master-protection handle is acquired, `assert_master_stable()` runs, and
**`self.rebuild(...)` (native Rebuild) still executes** regardless of whether PRE capture succeeded. Only
after native Rebuild returns does the code check `if not pre_capture_ok: raise NativePostFallback(...)`
(line 11476-11480) — and `NativePostFallback` is not an unhandled error; it is caught by a single
`except NativePostFallback as fallback:` clause (line 11987) that logs
`TARGET_CONTEXTUAL_RESULT = NATIVE_POST_ONLY_...` and proceeds through the same cleanup (`finally:` block,
protection release, undo restore) as the success path. **This corrects any prior description implying a PRE
discovery failure is a hard, exceptional abort** — it is a graceful, fully-anticipated fallback to
native-only mode, with native Rebuild still running normally. The five `raise NativePostFallback(...)`
sites this project has already enumerated (`O3_DISCOVERY_CALL_MAP.md`) all funnel into this same single
catch point.

## Consequence for this checkpoint

None of these corrections change the final decision in `O3_R3_ENUMERATION_VALIDITY_DECISION.md` — if
anything, correction 6 (composer-before's result is unconsumed) narrows *what* enumeration validity
protects (safety via exception propagation, not data correctness of the write), and correction 5 (`name()`
degrades silently) combined with the counterexample analysis's case F (native wrapper/handle recycling,
where `handle()` has no equivalent protection) sharpens *why* a retained enumeration remains unsafe: the
one live object dereference the reused design would still need (`rig`, for `capture_snapshot_explicit`'s
own `name()` call) could silently degrade instead of raising, masking exactly the kind of staleness this
whole investigation is trying to detect.
