# Checkpoint J — Mechanical Gates & Instrumentation Design

## Confirmed production shape (direct source reading, `audit_external_runtime/Rebuild_Control_Groups_Normalizer.py`)

- `native_master_protect_acquire(path)` (lines 356-404): opens `path` with `GENERIC_READ`,
  `FILE_SHARE_READ` only, `OPEN_EXISTING`; returns the real handle or `None` on any failure — never
  raises.
- `native_master_protect_release(handle)` (lines 407-413): `CloseHandle(handle)`, swallowing exceptions;
  no-op on `None`.
- `run_target_transaction` (lines 11661-12479): acquires the handle at line 11837 immediately before a
  `try`, calls `self.assert_master_stable()` (line 11857, itself calling `sha256_stream(self.master_path)`
  at line 9901) as the FIRST protected operation, calls `self.rebuild(...)` (line 11927 — a `ctypes`
  `WINFUNCTYPE` bound to the real native callback address, assigned inside `prepare_native_callback` at
  line 9791), calls `production_generic_composer(...)` (line 12360), and releases the handle in the
  `finally` at line 12461.
- `self.scope_mode`/`self.scope_shots` (lines 9475-9481): real instance attributes set at construction;
  `SCOPE_SELECTED = u"SELECTED_SHOTS"` (line 8492). `self.work` (line 14238, via `snapshot_work()`): a list
  of `{"name": shot_name, "targets": [{"name": aset_name, ...}, ...]}` records, built synchronously inside
  `start()` (called at module level, line 14592) — before `exec()` returns, same as everything else in this
  section.
- Production's own log literals (lines 13879-13894, 11769 area): `"scope_mode=%s scope_shots=%d" %
  (self.scope_mode, len(self.scope_shots))`; `"CONTEXTUALIZER_SCOPE_SHOT_NAMES = %r" % [shot.GetName() for
  shot in self.scope_shots]`; `"PRODUCTION_PRE_CAPTURE_GATE = PASS target=%r signature=%r" % (exact_pair,
  ...)` where `exact_pair = (shot_name, aset_name)`; `"NATIVE_REBUILD_RETURNED = PASS"`.
- `sfm_master_authority_productionized/runtime.py`: `RUNTIME_API_VERSION`/`RUNTIME_BUILD_ID` module-level
  constants; `get_state()`/`is_canonical()` module-level functions; `STATE_READY = "READY"`.
- `self.master_path`/`self.master_hash` (lines 9505-9506 initialized `None`; lines 9865-9886 assigned):
  real instance attributes, `self.master_path = os.path.join(usermod_dir, "cfg",
  "sfm_defaultanimationgroups.txt")` and `self.master_hash = sha256_stream(self.master_path)` — set
  synchronously inside `derive_paths()`, before `exec()` returns, same as everything else in this section.

## Five wrap points

Four are module functions patched by reassignment in the `exec()`'d namespace dict. The fifth —
`self.rebuild` — is patched via an **instance-attribute** reassignment on the already-constructed run
instance, **never** a class-level patch. A sixth wrap — `run_target_transaction` itself — is the
fail-closed guard (see below), distinct from the five observational wraps described in the checkpoint's
own spec.

1. `native_master_protect_acquire` — records `protect_acquire` (path, success, start/end); sets
   `state["protection_active"]`/`state["protected_path"]` only after a REAL non-`None` handle returns.
2. `native_master_protect_release` — records `protect_release`; clears `state["protection_active"]`;
   immediately runs the J3 post-release probe matrix and records it as `post_release_probe_matrix`.
3. `sha256_stream` — records `sha256_stream_call` with whether protection was active and whether the path
   matches the protected Master path. **This evidence is now a real verdict gate** (see "Protected Master
   SHA gate" below), not merely event-ordering decoration.
4. `production_generic_composer` — records `composer_enter` (with a protected-matrix probe taken here,
   before calling the original) and `composer_return` (after).
5. `<run_instance>.rebuild` (instance-attribute patch, via `wrap_run_instance_native_rebuild()`) —
   records `native_rebuild_enter` (with a protected-matrix probe taken here, before calling the original
   native callable) and `native_rebuild_return` (after, also recording whether protection was still active
   at that moment).

The harness never substitutes its own handle for production's; `state["protection_active"]` reflects only
the real acquire/release lifecycle.

## Round 1 correction: instance-level native-rebuild wrap (not class-level)

Executing the production file's bytes does not merely define classes/functions. Its own top-level code
(`StartRebuildControlGroups()`) SYNCHRONOUSLY shows the real scope dialog, constructs the run instance once
the operator responds, and performs one-time command-level setup — including the real `self.rebuild`
assignment via `prepare_native_callback()`, called from `derive_paths()` — and **all of this completes
before `exec()` itself returns**; only the per-target processing loop that follows is Qt-deferred. A
class-level patch installed after `exec()` returns is therefore always too late: `self.rebuild` is already
a plain INSTANCE attribute by then, which takes precedence over any class-level definition by ordinary
Python attribute-lookup rules. This is exactly why Checkpoint O2's own original native-Rebuild wrap recorded
**zero** interceptions despite production logs proving native Rebuild ran (see
`checkpoint_o2_r1/O2_R1_NATIVE_TIMING_CORRECTION.md`).

The fix: `locate_run_instance(main_window, run_lock_name)` locates the ALREADY-CONSTRUCTED run instance
immediately after `exec()` returns, via the same `main_window.findChildren(QtCore.QObject)` +
`objectName() == RUN_LOCK_NAME` technique every earlier checkpoint's own wait-loop already uses — requiring
**exactly one** match, never guessing between zero or several. `wrap_run_instance_native_rebuild()` then
patches that instance's own `self.rebuild` attribute directly.

## Round 2 correction: the fail-closed guard is the real prevention mechanism, not an outer raise

A raised exception in the checkpoint script's own outer control flow, after `exec()` has already returned,
does **not** itself prevent anything: by that point production has already constructed the run and
scheduled its Qt-deferred target callback via the ambient SFM Qt event loop, which this script neither owns
nor can stop merely by raising in its own frame.

The real prevention mechanism is `install_run_target_transaction_guard()`: a **class-level** wrap of
`RebuildControlGroupsProductionRun.run_target_transaction` itself (unaffected by the round-1 timing issue,
since this method is only ever called later, from inside the Qt-deferred per-target loop). Installed as the
**first** post-exec instrumentation action, before any operation that can itself fail, the guard checks
`state["instrumentation_ready"]` on every call: while it is not `True`, the guard raises
`CheckpointJInstrumentationNotReadyError` **inside production's own real call chain** and never calls the
original method at all. `instrumentation_ready` only becomes `True` after: the guard itself installed; the
run instance located and its `self.rebuild` wrapped; the exact workload-identity gates (below) all passed;
and the four module-level wraps installed. Because PySide's Qt event-loop dispatch does not generally
propagate a Python exception raised from inside a Qt-deferred callback back into the checkpoint script's own
frame, the checkpoint does not rely on *catching* this exception for safety — only on the fact that raising
it, inside the guard, prevents the original method (and therefore native protection acquisition and native
Rebuild) from ever running uninstrumented. `state["blocked_call_count"]` and the
`"target_transaction_blocked_not_ready"` event record this independently either way; a nonzero blocked-call
count is itself disqualifying (`fail_closed_guard_never_blocked_a_call` gate).

Offline-regressed both paths: setup-fails (`instrumentation_ready` stays `False`) → original method called
zero times, every attempt raises; setup-succeeds → original method called exactly once, with identical
arguments and its exact, unmodified return value.

## Round 2 correction: mechanically pinned workload identity (three layers)

1. **Pre-production** (before `exec()`, hard-gates via `CheckpointJError`): fixture basename independently
   resolved via `sfmApp.GetDocumentRoot().GetFileId()` -> `vs.g_pDataModel.GetFileName()` (never assumed
   from shot names; rejects `testscripts.dmx` explicitly); exactly 15 project shots; `shot9` resolves
   uniquely (`resolve_unique_shot()`); its sole animation set is exactly `krystalv21`;
   `sfmClipEditor.GetSelectedShots()` shows exactly one selected shot, canonically (native-pointer-identity,
   `b_native_ptr()`/`canonical_single_shot_match()`) matching the resolved `shot9` — never a name-only
   comparison.
2. **Post-exec, on the already-constructed instance** (gates `instrumentation_ready`, never raises directly
   — see the guard above): `run_instance.master_path`/`run_instance.master_hash` match the canonical Master
   path/SHA-256 exactly (`path_matches_baseline()`, see "Round 3 correction" below); `run_instance.scope_mode
   == u"SELECTED_SHOTS"`; exactly one `run_instance.scope_shots` entry, canonically matching the preflight
   `shot9`; and `run_instance.work` is exactly one shot record (`shot9`) with exactly one target
   (`krystalv21`) — a HARD requirement as of round 3 (see "Round 3 cleanup" below), never a soft pass on
   empty/absent work.
3. **Post-run, from production's own completed log** (`production_log_scope_confirmed()`,
   `production_log_single_target_transaction()`, `production_log_single_native_rebuild()`): exact
   `scope_mode=SELECTED_SHOTS scope_shots=1` and exact `CONTEXTUALIZER_SCOPE_SHOT_NAMES = [u'shot9']`;
   exactly one `PRODUCTION_PRE_CAPTURE_GATE = PASS target=...` line in the WHOLE log, and it is exactly
   `(u'shot9', u'krystalv21')`; exactly one `NATIVE_REBUILD_RETURNED = PASS` line.

A correct protection matrix observed on any *other* workload cannot reach `J_PASS`: layer 1 failure aborts
before `exec()`; layer 2 failure leaves `instrumentation_ready` `False`, so the guard blocks the real
transaction; layer 3 failure is its own hard verdict gate (`workload_identity_confirmed`,
`production_log_scope_confirmed`, `production_log_single_target_confirmed`,
`production_log_single_native_rebuild_confirmed`).

## Round 2 correction: protected Master SHA gate

`find_protected_master_sha256_ok(events, protected_path)` requires **at least one** `sha256_stream_call`
event whose recorded path equals the protected live Master path, whose `protection_active` was `True`, and
which occurs — by **event-list ORDINAL POSITION**, never wall-clock timestamp — strictly after the first
successful `protect_acquire` event and strictly before the first `native_rebuild_enter` event. This is kept
separate from `validate_event_order()` (which assumes exactly one event per required kind) because
`sha256_stream` may legitimately be called more than once (`assert_master_stable()` is called from multiple
sites in production, not only inside the protected window), so a "first-match" assumption would be
incorrect; "at least one qualifying occurrence in the right position" is the correct and sufficient proof.

## Round 2 correction: derived (never hard-coded) handle-hygiene gate

`probe_access()` now records the ACTUAL `CloseHandle()` result for every successfully-opened probe handle:
`close_attempted`/`close_succeeded`/`close_error`. A failed open never attempts `CloseHandle` at all (proven
statically, as before). `matrix_all_probe_handles_closed(matrix)` requires every successfully-opened probe
in that matrix to have `close_succeeded is True`; `open_handle_leak_detected` in the final verdict context
is `not all(matrix_all_probe_handles_closed(m) for m in <every matrix actually used this run>)` — a real,
derived boolean, never a literal `False`. Offline-regressed with a real, synthetic forced `CloseHandle`
failure (monkeypatching the pinned namespace's own `_probe_close_handle` to fail exactly once) proving
`probe_access()` faithfully records the failure and that it correctly fails the hygiene gate end-to-end.

## Round 2 correction: actual (not merely expected) authority runtime identity

Previously, only `prod_ns["_AUTHORITY_EXPECTED_API_VERSION"]`/`prod_ns["_AUTHORITY_EXPECTED_BUILD_ID"]` were
checked — proving only what production *expects*, not what actually loaded. Now the checkpoint reads the
ACTUAL loaded module directly: `authority_runtime.RUNTIME_API_VERSION`, `authority_runtime.RUNTIME_BUILD_ID`,
`authority_runtime.is_canonical()`, `authority_runtime.get_state()` (module-level attributes/functions on the
real `sfm_master_authority_productionized.runtime` module, confirmed by direct source reading). Production's
own expectation constants are still recorded (`j4.production_expected_api_version_corroborates` /
`..._build_id_corroborates`) but only as additional corroboration, never as a substitute for the actual
identity checks (`actual_runtime_api_version_matches`, `actual_runtime_build_id_matches`,
`authority_canonical`, `authority_state_ready`).

## Round 3 correction: J1 baseline handle hygiene gates before `exec()`

The J1 baseline probe matrix (`probe_matrix(CANONICAL_MASTER_PATH)`, taken before production ever runs) must
ALSO satisfy `matrix_all_probe_handles_closed(baseline_matrix)` — a HARD pre-production gate
(`j1.baseline_handles_all_closed`), participating directly in `baseline_gate_passed` alongside the three
existing read/write/delete-succeeds checks. A leaked baseline WRITE or DELETE probe handle (opened
successfully but never actually closed) could itself conflict with production's own subsequent
GENERIC_READ/FILE_SHARE_READ protection handle, contaminating the experiment before it even begins. On
failure: classified `PRE_PRODUCTION_GATE`; `exec()` is never called; the raised `CheckpointJError` message
explicitly tells the operator to restart SFM before another attempt. A static structural check (source-order
inspection) confirms `"j1.baseline_handles_all_closed"` textually precedes the production `exec()` call.

## Round 3 correction: protected path/generation mechanically bound to the canonical Master

Previously, the file this harness independently SHA-256'd (`CANONICAL_MASTER_PATH`) and the file production
actually protected were only ASSUMED to be the same. `normalize_path_for_comparison()`/
`path_matches_baseline()` (reused verbatim from `checkpoint_i_generation_replacement/I_Generation_Helper.py`'s
own already-qualified implementation — normalized absolute, case-insensitive, NTFS-safe path comparison) now
bind them explicitly, checked at TWO independent points:

1. **Immediately after locating `run_instance`, before `instrumentation_ready` can become `True`**:
   `run_instance.master_path` matches the canonical Master path, and `run_instance.master_hash` equals the
   pinned canonical Master SHA-256 exactly. Both values are recorded in `report["provenance"]`.
2. **At final verdict assembly**: the one successful `protect_acquire` event's own recorded `path`, AND
   `state["protected_path"]` (the harness's own derived record of what got protected), BOTH independently
   match the canonical Master path too.

All four conditions are ANDed into the single named verdict gate `protected_path_is_canonical_master`. The
first two also feed `workload_identity_confirmed` (so a mismatch there prevents `instrumentation_ready`,
engaging the fail-closed guard); the full four-condition gate is the final, independent mechanical proof.
Offline-regressed with wrong-path and wrong-hash cases via direct `path_matches_baseline()` unit tests
(identical/case-different/`..`-normalized paths match; wrong path, `None`, and empty-string inputs never
match) and the `protected_path_is_canonical_master` adversarial case.

## Round 3 correction: purely ordinal, exact-count event ordering

`validate_event_order()` no longer reads any timestamp field at all. For each of the seven required kinds,
it now requires the kind to appear in the append-ordered `events` list **exactly once** (zero or more than
one is `False` — no more "first match wins"), takes that occurrence's own LIST INDEX, and requires the
resulting seven indexes to be strictly increasing. `find_protected_master_sha256_ok()` already used the same
ordinal-index technique since round 2 and is unchanged. Offline-regressed with: a genuine list-position swap
(an out-of-order append, not merely an out-of-order timestamp field) correctly failing; deliberately
misleading timestamps that CONTRADICT the correct list/append order being correctly IGNORED (ordinal
position alone determines the result); and a duplicate required event (e.g. two `native_rebuild_enter`
entries) correctly failing.

## Round 3 cleanup: `run_instance.work` is now a hard requirement

`work_inventory_matches_single_target()` no longer treats an empty/absent `work` as an "available soft pass"
-- for this exact one-target J workload, production's own `start()` always constructs `self.work =
self.snapshot_work()` synchronously, before `exec()` returns, so it is always genuinely available by the
time this check runs; an empty/missing inventory is now itself a failure, folded into
`workload_identity_confirmed` exactly like the other Layer-2 gates.

## Win32 access probe (`probe_access` / `probe_matrix`)

`CreateFileW(path, desired_access, FILE_SHARE_READ|WRITE|DELETE, NULL, OPEN_EXISTING,
FILE_ATTRIBUTE_NORMAL, NULL)` for exactly one of `GENERIC_READ` / `GENERIC_WRITE` / `DELETE` (0x00010000)
at a time. Maximally permissive sharing on the probe's OWN side means the result is governed entirely by
compatibility with whatever handle production currently holds, never a conflict the probe introduces.
Success closes the handle immediately with no file operation, recording the ACTUAL close result; failure is
never passed to `CloseHandle` (proven both by static source-order inspection and, offline, by a
2000-iteration `GetProcessHandleCount` regression showing zero net handle growth across both successful and
failed probe bursts).

`matrix_is_exactly_protected()` requires READ success AND WRITE/DELETE failure with **exactly**
`ERROR_SHARING_VIOLATION` (32) — a matrix showing a different denial code (e.g. `ERROR_ACCESS_DENIED`, 5)
is explicitly NOT classified as protected.

## Mechanical verdict (`classify_j_verdict`)

A single, pure function taking a `context` dict assembled from the real run's baseline matrix, wrapper
events, production log evidence, workload-identity results, authority-runtime identity, path-binding
evidence, and before/after Master SHA/size. Returns `("J_PASS", [])` only if none of the **29** named gates
fail; otherwise `("J_FAIL", [<failed gate names>])`. The offline suite exercises the happy path plus each of
the 29 gates individually forced to fail, plus an explicit count assertion (`len(set(gate names)) == 29`),
proving none is silently skipped or miscounted.

## Event-order requirement (`validate_event_order`)

`protect_acquire < native_rebuild_enter < native_rebuild_return < composer_enter < composer_return
< protect_release < post_release_probe_matrix`, checked via each event's own PURELY ORDINAL (append-list
INDEX) position — never a timestamp field (round 3 correction: see above). Each of the seven required kinds
must occur EXACTLY once; zero or more-than-one occurrences, or indexes that are not strictly increasing,
is `False`. Baseline probes (J1) are, by construction (they run before the production bytes are ever
`exec()`'d), always ordered first. The protected-Master-SHA ordering requirement (`protect_acquire <
protected_master_sha256 < native_rebuild_enter`) is proven separately, by `find_protected_master_sha256_ok()`
(see above), using the SAME ordinal-index technique, since `sha256_stream` does not satisfy the
exactly-once-per-kind assumption this function relies on for its own seven kinds.

## Offline qualification summary

`test_checkpoint_j_native_protected_handle_dryrun.py` — **192/192 PASS**, embedded Python 2.7.5. Extracts
all six reusable blocks (Win32 probe helper, module-level wrapper installer, run-instance locator +
native-rebuild instance wrap, `run_target_transaction` fail-closed guard, workload-identity gates,
event-order validator + mechanical verdict) verbatim by exact pinned line range and exercises the ACTUAL
deployed logic — never a reimplementation. Coverage: real disposable-temp-file share-matrix regression with
real `CloseHandle`-result tracking, a synthetic forced-close-failure regression, a J1-baseline-specific
leaked-probe-handle case plus a static proof the hygiene check precedes `exec()`, and a 2000-iteration
handle-leak regression across both successful and failed probes; a historical-bug reproduction (rejected
class-level patch → zero interceptions; corrected instance-level mechanism on the SAME instance → exactly
one, identity preserved); a guard regression (setup-fails → zero original calls, always raises;
setup-succeeds → exactly one original call, identical arguments, exact return value); a full wrapper/guard
regression against a synthetic fake-production module (never the real Normalizer) that opens/closes a REAL
Windows handle, including a premature-call-is-blocked-then-succeeds-once-ready sequence; direct unit tests of
every workload-identity helper (now including `normalize_path_for_comparison()`/`path_matches_baseline()`,
and `work_inventory_matches_single_target()`'s hard, no-soft-pass requirement) including
`resolve_fixture_basename()` against a fake `sfmApp`/`vs` object model; direct ordinal-position tests of
`find_protected_master_sha256_ok()`; purely-ordinal `validate_event_order()` regressions (a genuine
list-position swap fails; deliberately misleading timestamps that contradict the correct list order are
correctly ignored; a duplicate required event is correctly rejected); and the full 29-gate adversarial
matrix. The full script's own syntax compatibility with the embedded interpreter is proven by direct
`py_compile.compile()`, since its own top-level flow depends on `sfmApp`/`PySide` and cannot run offline.
