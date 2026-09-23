# O2-R1 — Native Timing Correction + Narrow Capture-Overlap Proof

**Status: PREPARATION COMPLETE / ROOT CAUSE CONFIRMED / OFFLINE FIX VERIFIED / REAL-SFM RE-RUN PENDING
OPERATOR EXECUTION.** No SFM has been run for this checkpoint. No production, integration, or lifecycle
code has been modified. Nothing here authorizes an optimization.

## Governing rule

> Tangible savings, demonstrated redundancy, zero functional compromise.

This remains measurement/proof only.

## 1. O2's preserved findings

O2 is recorded as: **O2 — BOUNDED PHASE ATTRIBUTION — PASS WITH NATIVE-INSTRUMENTATION GAP.** See
`real_sfm_qualification/checkpoint_o2/O2_REBUILD_NORMALIZER_PHASE_ATTRIBUTION.md` (updated) and
`o2_phase_attribution_result.json` (updated) for the full preserved findings, unchanged by this
correction:

- Whole-shot/rig discovery: **MATERIAL** (10 calls/command, ~1.54s total, ~0.15s mean).
- Tree construction: **IMMATERIAL** (10 calls/command, ~0.02s total) — not pursued as standalone.
- Composer-before witness: `EXERCISED_PATH_EQUIVALENT_NO_INTERVENING_MUTATION` for Fox and Mia, both
  commands — **DESIGN REVIEW JUSTIFIED, validation/freshness proof still required.**
- Composer-after→terminal witness: same result, reconciled path only — **DESIGN REVIEW JUSTIFIED FOR
  RECONCILED PATH ONLY**, not generalized to native-only fallback.
- Warm second run: Fox desired 74/moved 72/already_correct 2; Mia desired 69/moved 67/already_correct 2
  — expected Rebuild→Normalizer behavior, not a bug or redundancy by itself.

## 2. Root cause of the native-instrumentation gap

Confirmed by direct source reading of the accepted production Normalizer
(`Rebuild_Control_Groups_Normalizer.py`, SHA-256
`cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`), not guessed:

- **Every `self.rebuild` touch in the whole file** (exactly 3): `self.rebuild = None` (`__init__`, line
  9040); the real assignment `self.rebuild = NativeRebuild(callback_address)` (line 9328-9332, inside
  `prepare_native_callback`); the one call site `self.rebuild(ctypes.c_void_p(aset_ptr))` (line 11464,
  inside `run_target_transaction`). No second/later assignment exists anywhere.
- **`prepare_native_callback`'s own single call site**: line 9426, inside `derive_paths(self)` (def line
  9345) — called exactly once, not repeatedly.
- **The decisive finding**: module top level, line 13939, `StartRebuildControlGroups()` is called
  **unconditionally**. Its body (13884-13936) constructs `run = RebuildControlGroupsProductionRun(...)`
  (line 13930) and calls `run.start()` (line 13936) — both plain, synchronous calls. `start()` (13341)
  runs straight through its own setup logging and `CP0_COMMAND_START` checkpoint, then at line
  13483-13486 calls `self.derive_paths()` **synchronously**, which at line 9426 calls
  `self.prepare_native_callback(module_base)` **synchronously**, which at line 9328 sets the real
  `self.rebuild`. **All of this — instantiation through native-callback setup — completes before
  `exec()` itself returns control to the diagnostic script.** Only the per-target processing loop is
  Qt-deferred (via `QTimer.singleShot`); the one-time command-level setup, including native-callback
  prep, is not.

O2's own class-level patch on `RebuildControlGroupsProductionRun.prepare_native_callback`, installed
*after* `exec()` returned, was therefore installed strictly too late — the one-and-only call to that
method had already happened. O2's other four wraps (`discover_rig_context`, `capture_tree`,
`capture_snapshot_explicit`, `run_target_transaction`) all worked correctly precisely because their real
calls happen later, during the Qt-deferred per-target loop, which runs *after* `exec()` returns.

## 3. The fix

Instead of patching the class's `prepare_native_callback` (too late), O2-R1 locates the
**already-constructed run instance** immediately after `exec()` returns — via the same
`main_window.findChildren(QtCore.QObject)` + `objectName() == RUN_LOCK_NAME` technique every earlier
checkpoint's own wait-loop already uses to detect the run-lock — and wraps that **instance's own**
`self.rebuild` attribute directly (a plain instance-attribute reassignment, which by normal Python
attribute-lookup rules takes precedence over any class-level definition). Since `self.rebuild` is
already the real ctypes callable by the time `exec()` returns, and the actual per-target
`self.rebuild(...)` call only happens later inside the Qt-deferred loop this wrap correctly precedes,
this closes the gap without touching production's own timing, callback order, or behavior in any way.

Offline-verified before deployment: `test_o2r1_native_instance_wrap_mechanism.py` (SHA-256
`5ec33023f9187bb5abdfd991090e53f6c4e22e2c7e4ffaef052289e8d87473db`), **7/7 PASS** under the real embedded
Python 2.7.5, using a synthetic source shaped like the real synchronous-construction pattern — first
reproducing O2's own bug (a class-level patch installed after exec() never fires again), then proving
the instance-level fix correctly intercepts the later call with the exact same argument and return
value, and that the wrapped callable lives on the instance's own `__dict__`, not the class.

Deployed script: `Checkpoint_O2_R1_Native_Timing_Correction.py`, SHA-256
`fe062549bbf3f0b0611ed57824b537e7edf9efa1219b5ca7f4499a8b2dc8f8f7`. All four of O2's other wraps are
unchanged. Measures at minimum, per native call: elapsed time, working-set/private memory immediately
before and after, target identity (via the surrounding event sequence), success/failure (whether the
call raised).

## 4. Narrow static proofs

Both produced this turn, motivated by (not proven by) O2's own real-run equivalence witnesses:

- **`O2_R1_OUTER_POST_TO_COMPOSER_BEFORE_PROOF.md`** — traces every operation between the outer native
  POST capture and the composer-before capture, reconciled path. Mechanical conclusion:
  **`SOURCE_EQUIVALENCE_SUPPORTED`** — exhaustive whole-file grep confirms no DME write, no native
  mutation, and no Qt-yield exists anywhere in the interval; the only write-capable primitives in the
  entire file are downstream, inside the composer's own post-before-capture mutation phase.
- **`O2_R1_COMPOSER_AFTER_TO_TERMINAL_PROOF.md`** — traces every operation between the composer-after
  capture and the terminal capture, reconciled path. Mechanical conclusion:
  **`RECONCILED_PATH_REUSE_PLAUSIBLE`** — no DME mutation occurs in this interval either, but terminal
  retains a **distinct procedural purpose**: attesting the DME remains cleanly capturable *after* the
  undo-restore/protect-release/Master-stability-reassert steps that run between the two captures —
  something composer-after's own (earlier) capture cannot attest to by itself. This conclusion is
  explicitly scoped to the reconciled path; terminal is the sole validation point on the native-only
  fallback branch, confirmed by its unconditional, branch-independent placement in the source.

Neither proof authorizes reuse. Both are proof-gathering only, feeding a decision made elsewhere.

## 5. Scope discipline

This is the smallest real-SFM rerun needed to correct native timing: the same bounded fixture (`shot3`,
Selected Shots, Fox + Mia), the same two-command fresh-then-already-normalized sequence O2 already used
(kept, rather than reduced to one command, because a fresh-vs-warm native-timing comparison is one of
the required O2-R1 conclusions). No All-Shots command. No F1-R2 execution. No broad new runtime campaign.

## 6. Interpretation constraint (restated)

Rebuild→Normalizer overlap is not a newly discovered optimization target — the Normalizer's job is to
normalize the state native Rebuild produces, every time, warm or not. The optimization question this
whole O1→Astra→O2→O2-R1 chain is narrowing toward is specifically: **within the Normalizer's required
post-Rebuild pathway, are we materially repeating discovery/capture/validation work that can be safely
reused without weakening freshness or correctness?** Nothing in this document answers that question
definitively — it supplies the native-timing data and the two narrow static proofs needed to keep
narrowing it.

## Deliverables

- `Checkpoint_O2_R1_Native_Timing_Correction.py` (SHA-256
  `fe062549bbf3f0b0611ed57824b537e7edf9efa1219b5ca7f4499a8b2dc8f8f7`)
- `test_o2r1_native_instance_wrap_mechanism.py` (SHA-256
  `5ec33023f9187bb5abdfd991090e53f6c4e22e2c7e4ffaef052289e8d87473db`) — 7/7 PASS
- `O2_R1_OUTER_POST_TO_COMPOSER_BEFORE_PROOF.md` — `SOURCE_EQUIVALENCE_SUPPORTED`
- `O2_R1_COMPOSER_AFTER_TO_TERMINAL_PROOF.md` — `RECONCILED_PATH_REUSE_PLAUSIBLE`
- `INSTRUCTIONS.md` — operator sequence for the one required real-SFM re-run

O2's own updated deliverables (findings preserved, gap documented):
`real_sfm_qualification/checkpoint_o2/O2_REBUILD_NORMALIZER_PHASE_ATTRIBUTION.md`,
`o2_phase_attribution_result.json`.
