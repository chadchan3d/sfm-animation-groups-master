# F1-R3 — Static Native-Path Audit

**Status: STATIC SOURCE AUDIT ONLY.** No production, integration, or lifecycle code has been modified.
This document traces exactly how the accepted production Normalizer (SHA-256
`cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`) obtains and invokes native Rebuild,
and exactly what genuinely-required guards versus contextualizer-only setup surround that call, before
any F1-R3 diagnostic code was written. Every claim below is a direct source citation.

## How production obtains the native callback

`self.rebuild` is assigned exactly once, inside `prepare_native_callback()` (line 9275), called from
`derive_paths()` (line 9345), itself called from `start()`'s own early synchronous flow -- this whole
chain executes unconditionally the moment the production file is `exec()`'d (already established by
O2-R1's own root-cause finding). By the time any diagnostic locates the already-constructed run instance
via the `RUN_LOCK_NAME` technique (every earlier checkpoint's own established method), `self.rebuild` is
already the real, live `ctypes`-bound native callable.

## Exact target/shot inventory: `self.work`

`self.work = self.snapshot_work()` (line 13665-13667) runs synchronously inside `start()`, **before** any
shot is activated and **before** the whole-session semantic fingerprint baseline is captured. It returns
an ordered list of shot-records (sorted by shot start time, line 10198-10202), each holding an ordered
`targets` list built by iterating `shot.animationSets` in native order and applying the eligibility gate
(`snapshot_work()`, lines 9828-10245) -- **the exact same helper production itself uses**, not
reimplemented. `self.work` is exactly the object F1-R3 must read, not re-derive.

## The eligibility gate, exactly (verified against source and a real preserved production log)

`snapshot_work()`'s per-target loop (lines 10009-10185) applies, in this exact order:

1. `if not row["root_valid"]: continue` -- root-group validity (not itself one of the 3 named gate-skip
   reasons; zero occurrences in this fixture, confirmed below).
2. `STATIC_PROP` (line 10023-10034): `header["is_static_prop"] is True` -> skip.
3. `DIRECT_SKELETAL_FOLLOWER` (line 10126-10132): a bounded-overlap/child-coverage heuristic
   (`GATE_MIN_SHARED_TRANSFORMS=4`, `GATE_MIN_CHILD_COVERAGE=0.20`) -> skip.
4. `LOW_BONE_NO_ALH` (line 10159-10165): `numbones <= GATE_LOW_BONE_CEILING=30` and the accessory-look
   heuristic (`_gate_is_alh`) explicitly returns `False` -> skip.
5. `fail-closed process` (lines 10143-10171): low-bone but the Master-index gate itself could not be
   validated, or `_gate_is_alh` itself raised, or `numbones` could not be determined at all -- counted,
   but **does NOT skip** (falls through to `targets.append(...)`) -- this is a fail-**open** count in the
   sense that the target remains eligible; "fail-closed" describes the *policy default* (when the
   low-bone check itself cannot be resolved, the system does not risk silently miscategorizing a target as
   a follower/static-equivalent, and instead includes it for native processing, deferring to native
   Rebuild's own behavior).

**Verified against a real preserved production log** (`checkpoint_f1/f1_1_crash_evidence/
sfm_rebuild_control_groups_F1-1_command3_crash.txt`, an All-Shots run against this same fixture, lines
57-66): `scope_mode=ALL_SHOTS scoped_shots=15`, `gate skips static=12 follower=4 lowbone_no_alh=7
failclosed_process=0`, with the exact per-model breakdown (`DIRECT_SKELETAL_FOLLOWER`:
`assaultsuitbody.mdl`x2 + `loinclothbra_chadfix_07.mdl`x2 = 4; `LOW_BONE_NO_ALH`:
`deserteagle_round.mdl`x1 + `utah_teapot.mdl`x6 = 7; `STATIC_PROP`:
`palmtree_bendy_c.mdl`x4 + `stoneblocks48.mdl`x4 + `boulder6.mdl`x4 = 12). `12+4+7+0 = 23`;
`85 - 23 = 62`, confirming `total_duplicate_aset_skips` and `total_root_skips` are both zero in this
fixture (not independently logged in this particular excerpt, but arithmetically required for the
85-model-backed/62-eligible totals to reconcile exactly, and consistent with a clean, already-qualified
fixture). This is real evidence, not hard-coded assumption, per explicit instruction.

## Native invocation: exact guarded sequence (`run_target_transaction`, lines 11198-12029)

In call order, everything between "shot activated" and "native Rebuild call":

1. `aset_ptr = native_ptr(aset)`; `if aset_ptr != target["ptr"]: raise ProbeError(...)` (line 11221-11233)
   -- pointer-stability check against inventory.
2. `if self.get_game_model(aset) is None: raise ProbeError(...)` (line 11235-11239) -- model backing still
   present. `get_game_model()` itself (line 9213-9236) is a cheap, already-safe, exception-wrapped read.
3. `root = self.get_root_group(aset)`; `if root is None or not native_ptr(root): raise ProbeError(...)`
   (line 11241-11255) -- root-group validity, same helper `snapshot_work()` itself used.
4. PRE discovery+capture (lines 11262-11316) -- **contextualizer-only; skipped by F1-R3**.
5. `dm.SetUndoEnabled(False)`; verify `dm.IsUndoEnabled() is False` (line 11396-11404) -- **Undo state
   genuinely affects the native call**: it must be OFF, matching production's own explicit
   `"UNDO POLICY: entire per-target transaction is non-undoable"` log line (13439).
6. `native_master_protect_handle = native_master_protect_acquire(self.master_path)`; `if ... is None:
   raise ProbeError(...)` (line 11374-11386) -- **Master-file protection is genuinely part of the
   invocation**: a `FILE_SHARE_READ`-only handle, acquired before the protected region and released in
   the matching `finally:`.
7. `self.assert_master_stable()` (line 11394, inside the same protected `try:`) -- cheap SHA-256
   re-verification of the canonical Master file (line 9436-9449, pure hash comparison, no side effects).
8. `self.rebuild(ctypes.c_void_p(aset_ptr))` (line 11464-11468) -- **the native call itself**.
9. `self.log("NATIVE_REBUILD_RETURNED = PASS")` (line 11472-11474).
10. Everything after this point (PRE-fallback branch, POST discovery+capture, classification/planning,
    composer, terminal fallback/success branches) is **contextualizer-only; skipped by F1-R3**.
11. `finally:` (line 11996-12029) -- `native_master_protect_release(handle)`; restore
    `dm.SetUndoEnabled(undo_prior)` + verify restoration succeeded. **Genuinely required cleanup**,
    reused as-is.

## Shot activation: genuinely required, not contextualizer-only

`activate_next_shot()` (line 12574-12649) moves the SFM playhead into the target shot's own timeframe
(`sfmApp.SetHeadTimeInSeconds(record["midpoint"])`) and immediately verifies
`sfmApp.GetShotAtCurrentTime()` matches the expected shot pointer (`SHOT_ACTIVATION_IMMEDIATE_GATE`,
line 12628-12641) **before** any target in that shot is processed. This is not UI convenience -- SFM's own
native Rebuild implicitly operates against the currently-active shot (a host-application concept, not
purely a function of the `aset` pointer passed to `self.rebuild()`), so this step is a genuine
prerequisite, confirmed by direct reading, and is reproduced by F1-R3 exactly (a single synchronous
`SetHeadTimeInSeconds` + immediate verify, mirroring the immediate gate; the *deferred* re-verification
`process_current_shot()` performs after its own Qt-level defer exists to detect drift introduced by that
defer -- a defer F1-R3 does not introduce between activation and its own first native call, so the
deferred re-check is not required for F1-R3's own narrower design).

## Target re-resolution: genuinely required, narrowly reused

`contextualizer_resolve_resume_target(record, target)` (line 12259-12393) re-resolves the live `aset`
object fresh before every target (matching by `aset_ptr` + name, uniquely, within the *current* shot's own
`animationSets`) rather than trusting the object reference `snapshot_work()` recorded at inventory time --
directly addressing the same stale-reference concern this whole project's O3 series investigated at
length. This part of the method is reused. **One check inside it is NOT reusable as-is**: for
`self.current_target_index > 0`, it additionally requires `previous_pair in
self.production_terminal_results` -- a set populated only by the real terminal semantic-fingerprint
capture (`semantic_target_fingerprint()` / `capture_snapshot_explicit(..., "PRODUCTION_SEMANTIC_
FINGERPRINT", ...)`), which F1-R3 deliberately never performs. Calling this method unmodified for the
second-or-later target in any multi-target shot would therefore always raise, not because of any risk
inherent to F1-R3's own design, but because it verifies a fact (prior terminal capture completion) that
only exists in production's own fuller pipeline. **Resolution**: F1-R3 reuses this method's own re-
resolution matching logic (the `aset_ptr` + name uniqueness search within `at_head.animationSets`) via a
narrow, separately-written helper that omits only the terminal-results membership check -- documented here
as the one deliberate, justified deviation from calling an existing method completely unmodified, not a
reimplementation of the eligibility gate, the native invocation, or any contextual/composer logic. This
does not materially alter native Rebuild's own semantics; it only affects how the live `aset` object is
located immediately beforehand, using the same matching approach already established as safe.

## Neutralizing the real instance's own further progression (the safe way, verified)

Every state-machine method examined (`activate_next_shot`, `process_current_shot`, `process_current_target`,
`abort`, `request_restore_and_finish`, `finish_after_restore`) begins with `if self.finished: return`
(confirmed by direct reading of each). Setting `instance.finished = True` immediately after locating the
already-constructed run instance -- **before ever pumping the Qt event loop** -- permanently and safely
neutralizes every further step of production's own real pipeline (including the already-scheduled
`QTimer.singleShot(DEFER_MS, self.process_current_shot)` from the first shot's own synchronous activation,
which already occurred during `exec()`, unavoidably, before any diagnostic code runs -- see below). This
requires no monkey-patch and no interception of a Qt-scheduled callback: the callback may still fire later
(if F1-R3's own harness ever pumps events for other reasons), but it will see `self.finished == True` and
return immediately, doing nothing.

## The one unavoidable, one-time cost: the whole-session fingerprint baseline

`start()`'s own synchronous flow (line 13736-13739, `self.session_expected, baseline_shape =
capture_session_fingerprint_digests()`) runs **once**, unconditionally, between `snapshot_work()` and the
first `activate_next_shot()` call -- entirely before `exec()` can return control to any diagnostic script.
This cannot be intercepted by patching names in the executed namespace (the `def
capture_session_fingerprint_digests():` statement inside the same exec()'d source rebinds any pre-seeded
stub the instant it runs), and building a parallel harness that avoids `exec()`-ing
`StartRebuildControlGroups()` entirely would require reimplementing `snapshot_work()`'s own eligibility
gate from scratch -- exactly what "do not copy large sections of production logic" forbids. **This one-time
cost is accepted as unavoidable overhead of the exec()-and-reuse technique**, not skipped -- but it does not
contaminate F1-R3's own measured interval, because F1-R3's own "before" resource checkpoint is taken *after*
`exec()` returns, i.e. strictly after this one-time baseline has already been paid. It is a single,
one-time cost, not a per-shot or per-target one, and is architecturally distinct from the *repeated*
per-shot/per-target verification layers (Layer 2/3) and the final exhaustive verifier, all of which occur
later, driven by the Qt-deferred loop this design never advances -- those are the ones Section 3's
instruction means by "whole-session semantic fingerprint verification" and "final exhaustive semantic
verifier," and neither ever executes under F1-R3.

## Conclusion

No case in this audit required inventing a surrogate that alters native Rebuild's own semantics. Every
genuinely-required guard (pointer-stability check, model/root validity, Undo-disable, Master-protection
acquire/release, `assert_master_stable`, the native call itself, shot activation, target re-resolution) is
reused directly from the already-initialized, real production instance's own methods -- not reimplemented.
The one narrow exception (target re-resolution for index > 0) omits a single membership check that
verifies a fact meaningless under F1-R3's own design, and is documented above rather than silently patched
around.
