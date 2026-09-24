# Process-Lifetime Scope-Aware Admission Guard Checkpoint — Instructions

## Why this exists, and why it was revised

F2-R1-R3 established, with real-SFM evidence, that legitimate same-process reinvocation of the Rebuild
Control Groups Normalizer is not reliably sustainable (`F2-R1 FAIL — LEGITIMATE SAME-PROCESS REINVOCATION
IS NOT RELIABLY SUSTAINABLE`; see `../LEDGER.md`'s F2-R1 row). Astra's independent F release-disposition
review authorized implementing an admission guard, and an original implementation contract classified any
Selected Shot(s) request over more than one shot as "batch" (gated the same as All Shots). **That
classification was reviewed and rejected as unsupported by the evidence and harmful to the intended
Selected Shot(s) feature** — nothing in this project's evidence shows selecting 2, 5, or 10 shots is
unsafe; the only demonstrated failure mode involves large/cumulative full-project workloads.

The guard has been revised and reimplemented accordingly. A subsequent independent review also found the
guard's original full-scope-equivalence check used shot NAMES for identity (weaker than the contract, since
duplicate shot names could collapse distinct shots) instead of the canonical handle/native-pointer identity
`_resolve_selected_scope()` already uses; this has been corrected too (see "Proof no execution semantics
changed" below). **This checkpoint has NOT been run against real SFM.** (The original, now-superseded broad
one-attempt-per-process guard DID receive partial real-SFM qualification through snapshot #5 before being
superseded — see `../LEDGER.md`'s F3-Guard row for the corrected historical record; that partial evidence
is for the superseded design, not this one.) It is prepared for the operator to run.

## What the revised guard does (for context — do not re-derive this while running the checkpoint)

Exactly two workload classes, never a numeric threshold:

- **SELECTED_SCOPE**: the user chose Selected Shot(s), and the canonically resolved selected shot set is a
  proper subset of the project — 1 shot, 2 shots, 5, 10, any number. Remains normal, repeatedly-usable
  functionality within one process.
- **FULL_SCOPE**: either `scope_mode == ALL_SHOTS`, or `scope_mode == SELECTED_SHOTS` whose resolved
  selected-shot set is *exactly* the complete project shot set (exact workload equivalence, not a size
  threshold). Gets the same restart-based admission control as All Shots.

Three logical process states, tracked by two independent marker `QtCore.QObject`s parented to
`main_window` (`_read_process_scope_state()`/`_find_named_process_marker()`/
`_install_named_process_marker()` in production):

| State | Selected proper subset | Full scope |
|---|---|---|
| `UNUSED` | ALLOW → `SELECTED_USED` | ALLOW → `FULL_SCOPE_STARTED` |
| `SELECTED_USED` | ALLOW, remains `SELECTED_USED` | **REFUSE** |
| `FULL_SCOPE_STARTED` | **REFUSE** | **REFUSE** |

This gives `Selected → Selected → Selected → continue working` while preventing
`prior Normalizer work → All Shots` and `All Shots → any later Normalizer work` until SFM restarts. State
never rolls backward once armed; only real process exit clears it (confirmed by exhaustive source-position/
identifier-count proofs in the offline regression test — no cleanup path anywhere references either marker
name).

- **Refusal boundary** (`StartRebuildControlGroups()`): checked BEFORE `_choose_scope()` (refuses
  immediately if `FULL_SCOPE_STARTED`; a `SELECTED_USED` process is still allowed to open the dialog, since
  the request's own scope class is not yet known) and AGAIN immediately after scope resolution (the dialog
  runs its own nested Qt event loop, so state is reread rather than trusted from before it opened — this is
  where a `SELECTED_USED` process's full-scope *request* is caught). Both refusal paths perform zero scope-
  control collection, work inventory, discovery, provider/broker acquisition, native Rebuild, production-run
  construction, or production-log truncation.
- **Arming boundary** (`RebuildControlGroupsProductionRun.start()`, immediately before
  `collect_scope_master_wanted_folds()`): final recheck, then install (only from `UNUSED`) or no-op (already
  `SELECTED_USED` and request is `SELECTED_SCOPE`), then verification — one uninterrupted sequence of plain
  function calls, no intervening Qt event-loop yield.
- **Legacy marker**: the original broad guard's marker (commit `f3efd132ad5456a583df5917ef85576db0690c60`)
  cannot distinguish Selected use from All-Shots use. If found without valid new-scheme state, the process
  is treated as unreadable/ambiguous — REQUIRE RESTART. Never assumed `UNUSED`, never reinterpreted as
  `SELECTED_USED`.
- User-facing messages are concise, actionable, and restart-instructing — never mention "unsafe," "may
  crash," or internal marker/state/VAS terminology.

## Offline qualification already performed (before this checkpoint was prepared)

- `test_process_attempt_guard_regression.py` (SHA-256
  `bfd1c197fe16e0f460957445af2e85a694e8aba73c2729f458eaa092c1492c84`) — **81/81 PASS** under the real
  embedded Python 2.7.5. Covers all 24 items from the revised contract plus the independent-review canonical-
  identity correction's own adversarial coverage: the full state-transition matrix (behavioral, real
  `QtCore.QObject` instances) including that a refused full-scope request after `SELECTED_USED` leaves state
  unchanged and a later Selected request is still allowed; full-scope-equivalence classification using
  canonical shot HANDLE/NATIVE-POINTER identity (never shot names), including a 40-of-50-shot large-but-
  proper-subset case proving there is no size threshold, duplicate-shot-name cases proving names cannot
  collapse or fabricate distinct identity, a reordered-selection case proving identity-set comparison is
  order-independent, and unresolved/ambiguous-identity cases failing closed; malformed/conflicting/
  unreadable state and the legacy marker all fail closed; no scene/authority payload retained; survives
  `gc.collect()`; and static source-position proofs against the actual deployed production script text
  (cancel/bounded-rejection leave state unused, the dialog's nested event loop is accounted for by a reread,
  no cleanup path ever references either marker, refused requests reference zero substantial-work
  identifiers, exactly one log-truncating `open()` call exists and it is unreachable from refusal, the core
  mutation pipeline's own defining names are unchanged, and the classifier's own extracted source no longer
  contains any shot-name-based equality check).
- `test_checkpoint_process_attempt_guard_dryrun.py` (SHA-256
  `70eda6991d2f2f8337db61a37de4af6b0cc6e46b170831d9f4d12d6cc3d16ca6`) — **33/33 PASS** — offline-verifies
  this checkpoint script itself never references `StartRebuildControlGroups()`/scope-dialog machinery/
  substantial-traversal identifiers; `load_production_definitions()` extracts exactly the pinned scope-aware
  definitions by exact line range without importing the real SFM-only modules; the revised
  **evidence-file discipline** (2026-09-24): `write_evidence_json_once()`/`write_evidence_text_once()`
  refuse to overwrite an existing path (raise, verified original content stays byte-identical after a
  refused overwrite); three sequential `main()` invocations each write a NEW, uniquely-numbered,
  immutable snapshot file pair using the fixed 13-entry operation-label schedule, never overwriting a
  prior one (independently re-read and confirmed byte-identical after later invocations); the first
  invocation correctly captures the current production log as a uniquely-labeled, immutable run-evidence
  file (`..._run_01_selected_shot3.txt`) from the fixed 8-entry label schedule; a second invocation with
  an unchanged log captures no new run; the freely-overwritten rollup files
  (`final_result.json`/`final_summary.txt`) correctly reflect the cumulative index after each call; and
  checkpoint numbering (via the small, explicitly non-evidentiary continuation-state pointer file)
  continues correctly across a simulated restart (a fresh namespace reusing the same evidence directory).

## Proof no execution semantics changed

`git diff --stat` against the prior committed (broad-guard) production script shows the guard rewrite is a
scope-only change confined to the admission-guard region: constants, the two exception/state-marker helper
functions, the refusal boundary in `StartRebuildControlGroups()`, and the arming boundary in
`RebuildControlGroupsProductionRun.start()`/`__init__`. The offline regression test's own item-24 static
checks confirm the core mutation pipeline's defining names (`class RebuildControlGroupsProductionRun`,
`collect_scope_master_wanted_folds`, `acquire_master_index_via_qualified_authority`,
`_resolve_selected_scope`) are unchanged and present. The subsequent canonical-identity correction (also
independent-review-driven) is confirmed by `git diff --stat` against the prior scope-aware commit as a
single contiguous, narrowly-scoped change (140 insertions, 19 deletions, both hunks confined entirely to
`_classify_scope_request` and its new `_resolve_shot_canonical_identity_for_classification` helper — nothing
elsewhere in the file touched). `_resolve_selected_scope()` itself, part of the core mutation pipeline, was
deliberately left completely untouched; the new classifier helper duplicates its handle/native-pointer
matching technique rather than sharing code with it. `git diff --check` passes with zero whitespace errors
for both changes.

## Real-SFM operator sequence

Uses lightweight resource samples only (private bytes, free VAS, largest free region, and their deltas) —
**no pass/fail threshold is invented from memory or VAS**; report the numbers and whether accumulation
looks modest/stable or materially continuing, for the record, not as an automatic gate. Do **not** execute a
second All Shots in one process and do **not** deliberately try to recreate the known crash.

### Evidence-file discipline (2026-09-24 revision)

**The operator must never manually rename, copy, or move any evidence file.** Every one of the 13 numbered
**[SNAPSHOT]** points below means: run `Checkpoint_Process_Attempt_Guard_Qualification`. It is a pure
read-only observer — it never calls the real Normalizer itself, never opens a dialog, and performs zero
scene/provider/native work. Each invocation:

- Writes a **new, uniquely numbered, immutable** snapshot file pair —
  `sfm_scope_guard_snapshot_NN_<operation>.json` / `.txt` — using a fixed, predetermined operation label for
  step `NN` (`baseline`, `after_cancel`, `after_shot3`, `after_5shots`, `after_3shots`, `after_edit_repair`,
  `after_post_refusal_selected`, `after_reopen_selected`, `fresh_after_restart`, `after_all_shots`,
  `after_refusals`, `reset_after_restart`, `final_after_restart_selected`, in that order). It refuses (raises
  loudly) rather than silently overwriting if that exact filename already exists.
- If the real production log's own content has changed since the checkpoint's own last observation (i.e. a
  real Normalizer command completed since the previous invocation), automatically copies the log's exact
  byte content itself into a new, uniquely labeled, immutable file —
  `sfm_scope_guard_run_NN_<label>.txt` — from the fixed 8-entry label schedule below. **The operator never
  manually copies or renames `sfm_rebuild_control_groups.txt`.**
- Writes an immutable `sfm_scope_guard_history_through_NN.json` cumulative index, and refreshes (freely
  overwrites — these are index/bookkeeping, not evidence themselves) `sfm_scope_guard_final_result.json`,
  `sfm_scope_guard_final_summary.txt`, and a small continuation-state pointer file that carries the
  numbering across the Phase A → Phase B restarts.

The 8-entry run-log label schedule, in the fixed order the real commands below produce them:
`selected_shot3`, `selected_5shots`, `selected_3shots`, `selected_edit_repair`, `selected_after_all_refusal`,
`selected_after_reopen`, `all_shots`, `selected_after_restart`.

### Phase A — Selected Shot(s) normal workflow

1. **RESTART SFM FIRST.**
2. Open **only** `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx` (the accepted normalized qualification fixture) —
   never `testscripts.dmx`.
3. **[SNAPSHOT 01 — baseline.]** Expect `expected_state = observed_state = UNUSED`, `run_lock_present =
   False`, `production_sha256_matches_expected = True`, no run captured.
4. Invoke the real **Rebuild Control Groups** command. When the scope dialog appears, click **Cancel**.
5. **[SNAPSHOT 02 — after_cancel; proves cancel leaves state unused.]** Expect `UNUSED` still, no run
   captured (production log unchanged).
6. Invoke **Rebuild Control Groups** again. Choose **Selected Shot(s)**, selecting `shot3` alone. Let it run
   to completion. Record command-start/command-end resource samples (private bytes, free VAS, largest free
   region).
7. **[SNAPSHOT 03 — after_shot3; proves SELECTED_USED.]** Expect `SELECTED_USED`, `run_lock_present =
   False`, and a new run captured as `sfm_scope_guard_run_01_selected_shot3.txt`.
8. Invoke **Rebuild Control Groups** again. Choose **Selected Shot(s)**, this time selecting a representative
   multi-shot subset of approximately **five** shots, using a deterministic fixture subset that includes
   meaningfully denser shots such as `shot8` and/or `shot11` (this must remain a **proper subset** of the
   project — do not select every shot). Let it complete normally. Record resource samples before/after.
9. **[SNAPSHOT 04 — after_5shots.]** Expect `SELECTED_USED`, new run captured as
   `sfm_scope_guard_run_02_selected_5shots.txt`.
10. Run another, **different** Selected proper-subset selection of about three shots (any shots not yet
    exercised, still a proper subset). Let it complete. Record resource samples before/after.
11. **[SNAPSHOT 05 — after_3shots.]** Expect `SELECTED_USED`, new run captured as
    `sfm_scope_guard_run_03_selected_3shots.txt`.
12. Make one documented, legitimate presentation/group edit in one previously-processed shot (any real,
    predetermined control-group change that genuinely warrants renormalization — do not invent an
    arbitrary edit; reuse the same kind of qualified edit this project has used before, e.g. moving a
    control to/from the `Hidden` group per `checkpoint_f2_r1/F2_R1_CONTROLLED_EDIT_JUSTIFICATION.md`, if a
    fresh qualified edit target is not otherwise available — STOP and report if none can be identified
    safely rather than inventing one).
13. Re-run a Selected proper-subset scope containing the edited shot and verify the expected correction is
    applied. Record resource samples before/after.
14. **[SNAPSHOT 06 — after_edit_repair.]** Expect `SELECTED_USED`, new run captured as
    `sfm_scope_guard_run_04_selected_edit_repair.txt`.
15. Request **All Shots**. **REQUIRE refusal before any expensive work begins** (no scope-collection delay,
    immediate message).
16. Immediately afterward, invoke **Rebuild Control Groups** again and run another Selected proper-subset
    request. **REQUIRE it is still permitted** and completes normally.
17. **[SNAPSHOT 07 — after_post_refusal_selected; proves the refused All left state unchanged.]** Expect
    `SELECTED_USED` still (never became `FULL_SCOPE_STARTED`), new run captured as
    `sfm_scope_guard_run_05_selected_after_all_refusal.txt` — this run's own byte content, compared against
    the immediately-preceding snapshot 06's own log fingerprint, must show the refused All-Shots attempt in
    step 15 never touched the log at all (only step 16's own real command is reflected in the delta).
18. Reopen or switch to a **different** document in the same SFM process (no restart).
19. Run another Selected proper-subset request after the session change. **REQUIRE it is still permitted**
    and completes normally.
20. **[SNAPSHOT 08 — after_reopen_selected; proves the guard is process-scoped, not session-scoped.]** Expect
    `SELECTED_USED` still, new run captured as `sfm_scope_guard_run_06_selected_after_reopen.txt`.

**Resource reporting for Phase A (every real command in steps 6/8/10/13/16/19):** for each command, report
exact private bytes, free VAS, largest free region, and the deltas from the immediately preceding command —
in bytes and MiB. **If realistic multi-shot Selected use itself shows substantial cumulative depletion
comparable to the known large-run failure pattern (F1-1/F2-R1-R3), STOP and report the evidence rather than
silently treating Phase A as passed** — this checkpoint's purpose is to observe and report, not to assume
Selected use is unconditionally safe at any command count.

### Phase B — full-scope behavior

21. **Fully restart SFM.**
22. Reopen `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx`.
23. **[SNAPSHOT 09 — fresh_after_restart; proves a fresh process starts UNUSED.]** Expect `UNUSED`, and
    `current_pid` different from every Phase A snapshot's own PID; no new run captured (the log's own content
    from Phase A's last command is still on disk, unchanged, until a new command actually runs).
24. Run **one** standalone **All Shots** operation. Let it complete. Record resource samples before/after.
25. **[SNAPSHOT 10 — after_all_shots; proves FULL_SCOPE_STARTED.]** Expect `FULL_SCOPE_STARTED`, new run
    captured as `sfm_scope_guard_run_07_all_shots.txt`.
26. Attempt **Selected Shot(s)** (any proper subset). **REQUIRE immediate refusal before any expensive work
    begins.**
27. Attempt **All Shots** again. **REQUIRE immediate refusal before any expensive work begins.**
28. **[SNAPSHOT 11 — after_refusals; proves both later attempts left state unchanged and the log was not
    touched.]** Expect `FULL_SCOPE_STARTED` still, no new run captured (log unchanged from snapshot 10).
29. **Fully restart SFM.**
30. Reopen the fixture. **[SNAPSHOT 12 — reset_after_restart; proves the state resets.]** Expect `UNUSED`,
    new `current_pid`; no new run captured yet.
31. Run a Selected Shot(s) request (any proper subset). **REQUIRE it is permitted** and completes normally.
32. **[SNAPSHOT 13 — final_after_restart_selected.]** Expect `SELECTED_USED`, new run captured as
    `sfm_scope_guard_run_08_selected_after_restart.txt`. This is the last invocation; the rollup files
    (`sfm_scope_guard_final_result.json` / `_final_summary.txt`) now hold the complete, final index.

**Do NOT execute a second All Shots command in one process. Do NOT deliberately recreate the known crash.**

### Selected-equals-all-shots equivalence

Also confirm exact Selected-set-equals-complete-project-set classification behaves as `FULL_SCOPE`, either:

- in this real-SFM checkpoint if practical without triggering another heavy run (e.g., from a fresh `UNUSED`
  process, select **every** project shot individually through Selected Shot(s) rather than the All-Shots
  button, and confirm the admission guard treats it exactly like All Shots — same refusal behavior for any
  later request in that process); or
- offline, through the exact same classifier code — already covered by
  `test_process_attempt_guard_regression.py` items 10/10b/11a/11b/adv1–adv5 (**81/81 PASS**, including the
  exact-set-equality case, a large-but-proper-subset case proving there is no size threshold, and duplicate-
  shot-name adversarial cases proving names cannot fabricate a false equivalence).

## Output files to return

Every file below is a uniquely-named, immutable evidence file except the three explicitly marked as
freely-overwritten rollup/bookkeeping — the operator returns the whole `C:\Users\Public\Documents\` set
matching the `sfm_scope_guard_*` prefix and never renames or copies any of them by hand:

- 13 snapshot file pairs: `sfm_scope_guard_snapshot_01_baseline.{json,txt}` through
  `sfm_scope_guard_snapshot_13_final_after_restart_selected.{json,txt}`.
- 8 preserved production-log runs: `sfm_scope_guard_run_01_selected_shot3.txt` through
  `sfm_scope_guard_run_08_selected_after_restart.txt` — the checkpoint's own copy of
  `sfm_rebuild_control_groups.txt`'s exact byte content at the moment each was captured; the operator never
  manually copies that file themselves.
- 13 cumulative-index files: `sfm_scope_guard_history_through_01.json` through `..._through_13.json`.
- `sfm_scope_guard_final_result.json` and `sfm_scope_guard_final_summary.txt` (freely overwritten rollup —
  by the final invocation, the complete and correct final index).
- `sfm_scope_guard_continuation_state.json` (freely overwritten, non-evidentiary bookkeeping only).
- The resource samples recorded at each step in Phase A and Phase B (reported alongside, not written by the
  checkpoint script itself).

## PASS / FAIL contract

**PASS** requires all of: Phase A's cancel/Selected/refused-All/session-change sequence behaves exactly per
the state matrix at every snapshot; no realistic multi-shot Selected sequence shows substantial cumulative
depletion comparable to the known failure pattern (reported, not silently assumed); Phase B's All Shots →
refused Selected → refused All → restart → reset sequence behaves exactly per the state matrix; the
Selected-equals-all-shots equivalence is confirmed; every refused request's production-log fingerprint is
byte-for-byte unchanged from immediately before the refusal.

**FAIL** includes: a dialog appearing on any refused invocation; `SELECTED_USED` not reached after a
completed Selected command; `FULL_SCOPE_STARTED` not reached after a completed All-Shots command; any
refused request's log fingerprint changing; state resetting on a document/session change without a restart
(guard would be session-scoped, contradicting the design); state surviving a real restart; a fresh
post-restart process being refused; any snapshot's own `production_sha256_matches_expected` being `False`;
the checkpoint script itself raising a "refusing to overwrite" error at any point (would indicate a
numbering/schedule mismatch, not evidence of a guard defect, but requires investigation before continuing);
fewer than 13 snapshot file pairs or fewer than 8 preserved run-log files present at completion.

## Identities this checkpoint is pinned against

- Production Normalizer SHA-256 (canonical-identity candidate, current): `2c0edbb8a95f96147e6310fe1c039da7ee053f5e985f11bb3535dda8aa5ec23d`
- Production Normalizer SHA-256 (scope-aware, name-based identity, superseded): `1f2b87f2954d1944c06497a8adcda4de1e1663a148d655bf7cd6f3ace4f757dc`
- Production Normalizer SHA-256 (broad-guard, superseded; received PARTIAL real-SFM qualification through snapshot #5, see `../LEDGER.md`'s F3-Guard row): `6170d2a248845281b5f5d38dfea4b9f2decf908b8e3b79e80f4ada18d2f54625`
- Production Normalizer SHA-256 (pre-guard baseline): `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256 (unchanged, not touched by this work): `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Checkpoint script SHA-256: `8c347db86a84d7f293cb4872d19fd8fe4e31350f5d26ee9337e71d954b4eb11e`
- Guard offline regression test SHA-256: `bfd1c197fe16e0f460957445af2e85a694e8aba73c2729f458eaa092c1492c84`
- Checkpoint dry-run test SHA-256: `70eda6991d2f2f8337db61a37de4af6b0cc6e46b170831d9f4d12d6cc3d16ca6`

## Explicit non-authorization

This checkpoint does not modify production beyond the already-implemented guard, does not reopen the F1
optimization search, and does not begin G. `F` remains `OPEN` pending this checkpoint's own real-SFM result
and independent review of the recommended admission policy recorded in `../F1_FINAL_DISPOSITION_REVIEW.md`.
