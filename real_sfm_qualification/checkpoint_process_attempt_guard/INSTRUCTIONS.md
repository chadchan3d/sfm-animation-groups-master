# Process-Lifetime Scope-Aware Admission Guard Checkpoint — Instructions

## RESULT (2026-09-24): PASS. F IS NOW CLOSED (2026-09-25).

This checkpoint was run for real against real SFM on 2026-09-24 and **PASSED**: all 15 snapshots' observed
state exactly matched the expected state in order; the baseline-seeding fix correctly seeded a genuine
pre-existing log without misattributing it as a run; all 8 runs were captured contiguously despite 3
interleaved refusals; all three refusal fingerprint-equality proofs reported `equal: true`; 3 correct
process-restart transitions were observed; the controlled edit was independently confirmed repaired exactly
as specified; the standalone All-Shots command completed cleanly. Full evidence: `LEDGER.md`'s F3-Guard row.

An independent fresh-eyes review of the complete F campaign then concluded **CLOSE F AFTER NARROW
NON-ARCHITECTURAL CORRECTIONS**. The one narrow correction was copy-only: the three user-facing restart-
warning messages were reworded (see `Rebuild_Control_Groups_Normalizer.py`'s `PROCESS_GUARD_MESSAGE_*`
constants) with zero guard-behavior change, confirmed by `git diff` and by both offline test suites
re-passing unchanged. **This checkpoint is closed. Do not run it again** — the question it was built to
answer has been answered and F is closed. See `../F1_FINAL_DISPOSITION_REVIEW.md`'s FINAL CLOSEOUT section
for the complete disposition. **F CLOSED. G NOT YET BEGUN.**

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
  `ab45cce04235d951e72f21a7543d98a9f76df789c7828836c7299cb61e91cf1c`) — **47/47 PASS** — offline-verifies
  this checkpoint script itself never references `StartRebuildControlGroups()`/scope-dialog machinery/
  substantial-traversal identifiers; `load_production_definitions()` extracts exactly the pinned scope-aware
  definitions by exact line range without importing the real SFM-only modules; the revised
  **evidence-file discipline** (2026-09-24, independent-review-corrected same day): a fully controllable
  fake production-log fingerprint (redirecting only the internal read primitive, never touching the real
  `sfm_rebuild_control_groups.txt` on this machine) drives the WHOLE 15-snapshot/8-run schedule end to end
  offline: a nonempty pre-existing log observed at snapshot 01 is fingerprinted and seeds the "last known
  log" pointer, but is never captured as a run and never advances the run counter; the first genuinely new
  log content at snapshot 03 correctly becomes run 01; all 15 snapshot operation labels and expected states
  match the exact specified schedule in order; a snapshot taken immediately after a refused invocation
  (snapshots 07, 12, 13) captures no run and its own recorded log sha256 exactly matches the immediately
  preceding successful snapshot's; run indices stay exactly contiguous 1 through 8 despite the three
  interleaved refusals; numbering survives two simulated restarts (fresh namespaces reusing the same
  evidence directory and the same persisted fake-log state); `write_evidence_json_once()` still refuses to
  overwrite an existing path; and the final rollup indexes all 15 snapshots, all 8 runs, and all three
  mechanically-computed refusal fingerprint-equality proofs, each correctly `equal: true`.

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

The production log's own `CONTEXTUALIZER_RESOURCE_CHECKPOINT` telemetry already records private bytes, free
VAS, and largest free region throughout each command. **The operator does not manually record or transcribe
any resource numbers.** After the run, independent review extracts command-start/command-end private bytes,
free VAS, largest free region, per-command deltas, and the cumulative trend directly from the 8 preserved
run-evidence logs (see below) — **no pass/fail threshold is invented from memory or VAS**; this is reported
for the record, not applied as an automatic gate. If a command crashes before the next checkpoint
invocation, preserve and return whatever production log exists; do not attempt to reconstruct telemetry by
hand. Do **not** execute a second All Shots in one process and do **not** deliberately try to recreate the
known crash.

### Evidence-file discipline (2026-09-24 revision, independent-review-corrected same day)

**The operator must never manually rename, copy, or move any evidence file.** Every one of the 15 numbered
**[SNAPSHOT]** points below means: run `Checkpoint_Process_Attempt_Guard_Qualification`. It is a pure
read-only observer — it never calls the real Normalizer itself, never opens a dialog, and performs zero
scene/provider/native work. Each invocation:

- Writes a **new, uniquely numbered, immutable** snapshot file pair —
  `sfm_scope_guard_snapshot_NN_<operation>.json` / `.txt` — using a fixed, predetermined operation label for
  step `NN` (`baseline`, `after_cancel`, `after_shot3`, `after_5shots`, `after_3shots`, `after_edit_repair`,
  `after_all_refusal`, `after_post_refusal_selected`, `after_reopen_selected`, `fresh_after_restart`,
  `after_all_shots`, `after_refused_selected`, `after_refused_all`, `reset_after_restart`,
  `final_after_restart_selected`, in that order). It refuses (raises loudly) rather than silently
  overwriting if that exact filename already exists.
- **Snapshot 01 (baseline) only**: whatever production log already exists on disk (e.g. left over from
  earlier qualification work) is observed and fingerprinted, but is **never** copied into a run-evidence
  file and never advances the run counter — it only seeds the checkpoint's own "last known log" pointer.
  The first genuinely NEW log content, observed at a later snapshot, becomes run 01.
- On every later snapshot, if the real production log's own content has changed since the checkpoint's own
  last observation (i.e. a real Normalizer command completed since the previous invocation), automatically
  copies the log's exact byte content itself into a new, uniquely labeled, immutable file —
  `sfm_scope_guard_run_NN_<label>.txt` — from the fixed 8-entry label schedule below. **The operator never
  manually copies or renames `sfm_rebuild_control_groups.txt`.** A dedicated snapshot immediately follows
  every refused invocation, before any later successful command can replace the log, so each refusal's own
  "log unchanged" proof is never contaminated by a later command.
- Writes an immutable `sfm_scope_guard_history_through_NN.json` cumulative index — including three
  mechanically-computed refusal fingerprint-equality proofs once their referenced snapshots exist — and
  refreshes (freely overwrites — these are index/bookkeeping, not evidence themselves)
  `sfm_scope_guard_final_result.json`, `sfm_scope_guard_final_summary.txt`, and a small continuation-state
  pointer file that carries the numbering across the Phase A → Phase B restarts.

The 8-entry run-log label schedule, in the fixed order the real commands below produce them:
`selected_shot3`, `selected_5shots`, `selected_3shots`, `selected_edit_repair`, `selected_after_all_refusal`,
`selected_after_reopen`, `all_shots`, `selected_after_restart`.

### Deterministic operator selections

These exact shot/target/control names come from the established qualification fixture
(`F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx`). **If any named shot, animation set, or control is unexpectedly
missing, STOP and report it — do not substitute another fixture element.**

| Step | Selection |
|---|---|
| Initial Selected command | `shot3` alone |
| Five-shot Selected proper subset | `shot11`, `shot8`, `shot1`, `shot2`, `shot6` |
| Three-shot Selected proper subset | `shot12`, `shot10`, `shot7` |
| Controlled edit | shot `shot3`, animation set `foxmccouldwm1`, control `rig_hand_L` — use the qualified SFM DAG "move to hidden group" command; expected repair: restored to `RigArms/LeftArm`, direct order `rig_collar_L, rig_elbow_L, rig_hand_L` |
| Selected after refused All | `shot5` |
| Selected after document reopen | `shot9` |
| Selected after final restart | `shot4` |

### Phase A — Selected Shot(s) normal workflow

1. **RESTART SFM FIRST.**
2. Open **only** `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx` (the accepted normalized qualification fixture) —
   never `testscripts.dmx`.
3. **[SNAPSHOT 01 — baseline.]** Expect `expected_state = observed_state = UNUSED`, `run_lock_present =
   False`, `production_sha256_matches_expected = True`. Any pre-existing production log is fingerprinted and
   seeded but `run_captured` must be `none`/`baseline_seeded = true`.
4. Invoke the real **Rebuild Control Groups** command. When the scope dialog appears, click **Cancel**.
5. **[SNAPSHOT 02 — after_cancel; proves cancel leaves state unused.]** Expect `UNUSED` still, no run
   captured (production log unchanged from snapshot 01).
6. Invoke **Rebuild Control Groups** again. Choose **Selected Shot(s)**, selecting `shot3` alone. Let it run
   to completion.
7. **[SNAPSHOT 03 — after_shot3; proves SELECTED_USED.]** Expect `SELECTED_USED`, `run_lock_present =
   False`, and a new run captured as `sfm_scope_guard_run_01_selected_shot3.txt`.
8. Invoke **Rebuild Control Groups** again. Choose **Selected Shot(s)**, selecting exactly `shot11`, `shot8`,
   `shot1`, `shot2`, `shot6` (a proper subset). Let it complete normally.
9. **[SNAPSHOT 04 — after_5shots.]** Expect `SELECTED_USED`, new run captured as
   `sfm_scope_guard_run_02_selected_5shots.txt`.
10. Invoke **Rebuild Control Groups** again. Choose **Selected Shot(s)**, selecting exactly `shot12`,
    `shot10`, `shot7`. Let it complete normally.
11. **[SNAPSHOT 05 — after_3shots.]** Expect `SELECTED_USED`, new run captured as
    `sfm_scope_guard_run_03_selected_3shots.txt`.
12. Make the controlled edit: on `shot3`, animation set `foxmccouldwm1`, select control `rig_hand_L` in the
    DAG view and run the qualified SFM "move to hidden group" command.
13. Invoke **Rebuild Control Groups** again. Choose **Selected Shot(s)**, selecting `shot3` (the edited
    shot), and verify `rig_hand_L` is restored to `RigArms/LeftArm` with direct order `rig_collar_L,
    rig_elbow_L, rig_hand_L`.
14. **[SNAPSHOT 06 — after_edit_repair.]** Expect `SELECTED_USED`, new run captured as
    `sfm_scope_guard_run_04_selected_edit_repair.txt`.
15. Request **All Shots**. **REQUIRE refusal before any expensive work begins** (no scope-collection delay,
    immediate message).
16. **[SNAPSHOT 07 — after_all_refusal; proves the refused All left the log untouched.]** Expect
    `SELECTED_USED` still (never became `FULL_SCOPE_STARTED`), `run_captured = none`, and this snapshot's own
    `production_log_fingerprint.sha256` exactly equal to snapshot 06's own recorded sha256 — this is the
    direct, uncontaminated proof that step 15's refusal alone never touched the log (no later successful
    command has run yet at this point).
17. Invoke **Rebuild Control Groups** again. Choose **Selected Shot(s)**, selecting `shot5`. Let it complete
    normally.
18. **[SNAPSHOT 08 — after_post_refusal_selected.]** Expect `SELECTED_USED`, new run captured as
    `sfm_scope_guard_run_05_selected_after_all_refusal.txt`.
19. Reopen `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx` **from disk** in the same SFM process (do **not** restart).
    If prompted to save the currently modified fixture, choose **Don't Save**.
20. Invoke **Rebuild Control Groups** again. Choose **Selected Shot(s)**, selecting `shot9`. Let it complete
    normally.
21. **[SNAPSHOT 09 — after_reopen_selected; proves the guard is process-scoped, not session-scoped.]** Expect
    `SELECTED_USED` still, the **same PID** as every earlier Phase A snapshot, new run captured as
    `sfm_scope_guard_run_06_selected_after_reopen.txt`.

### Phase B — full-scope behavior

22. **Fully restart SFM.**
23. Reopen `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx`.
24. **[SNAPSHOT 10 — fresh_after_restart; proves a fresh process starts UNUSED.]** Expect `UNUSED`, and
    `current_pid` different from every Phase A snapshot's own PID; no new run captured (the log's own content
    from Phase A's last command is still on disk, unchanged, until a new command actually runs).
25. Run **one** standalone **All Shots** operation. Let it complete.
26. **[SNAPSHOT 11 — after_all_shots; proves FULL_SCOPE_STARTED.]** Expect `FULL_SCOPE_STARTED`, new run
    captured as `sfm_scope_guard_run_07_all_shots.txt`.
27. Attempt **Selected Shot(s)** (any proper subset). **REQUIRE immediate refusal before any expensive work
    begins.**
28. **[SNAPSHOT 12 — after_refused_selected; proves this refusal left the log untouched.]** Expect
    `FULL_SCOPE_STARTED` still, `run_captured = none`, and this snapshot's own log sha256 exactly equal to
    snapshot 11's own recorded sha256.
29. Attempt **All Shots** again. **REQUIRE immediate refusal before any expensive work begins.**
30. **[SNAPSHOT 13 — after_refused_all; proves this second refusal also left the log untouched.]** Expect
    `FULL_SCOPE_STARTED` still, `run_captured = none`, and this snapshot's own log sha256 exactly equal to
    **both** snapshot 11's and snapshot 12's own recorded sha256.
31. **Fully restart SFM.**
32. Reopen the fixture. **[SNAPSHOT 14 — reset_after_restart; proves the state resets.]** Expect `UNUSED`,
    new `current_pid`; no new run captured yet.
33. Invoke **Rebuild Control Groups** again. Choose **Selected Shot(s)**, selecting `shot4`. **REQUIRE it is
    permitted** and completes normally.
34. **[SNAPSHOT 15 — final_after_restart_selected.]** Expect `SELECTED_USED`, new run captured as
    `sfm_scope_guard_run_08_selected_after_restart.txt`. This is the last invocation; the rollup files
    (`sfm_scope_guard_final_result.json` / `_final_summary.txt`) now hold the complete, final index,
    including all three refusal fingerprint-equality proofs, each `equal: true`.

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

- 15 snapshot file pairs: `sfm_scope_guard_snapshot_01_baseline.{json,txt}` through
  `sfm_scope_guard_snapshot_15_final_after_restart_selected.{json,txt}`.
- 8 preserved production-log runs: `sfm_scope_guard_run_01_selected_shot3.txt` through
  `sfm_scope_guard_run_08_selected_after_restart.txt` — the checkpoint's own copy of
  `sfm_rebuild_control_groups.txt`'s exact byte content at the moment each was captured; the operator never
  manually copies that file themselves. Independent review extracts all resource telemetry from these 8
  files directly.
- 15 cumulative-index files: `sfm_scope_guard_history_through_01.json` through `..._through_15.json`.
- `sfm_scope_guard_final_result.json` and `sfm_scope_guard_final_summary.txt` (freely overwritten rollup —
  by the final invocation, the complete and correct final index, including the three refusal
  fingerprint-equality proofs).
- `sfm_scope_guard_continuation_state.json` (freely overwritten, non-evidentiary bookkeeping only).

## PASS / FAIL contract

**PASS** requires all of: Phase A's cancel/Selected/refused-All/session-change sequence behaves exactly per
the state matrix at every snapshot; both Phase A's refusal (snapshot 07) and Phase B's two refusals
(snapshots 12/13) show `run_captured = none` with log sha256 exactly matching the immediately-preceding
successful snapshot; Phase B's All Shots → refused Selected → refused All → restart → reset sequence behaves
exactly per the state matrix; the Selected-equals-all-shots equivalence is confirmed; the final rollup's
three refusal fingerprint-equality proofs are all `equal: true`; run indices remain exactly contiguous 1
through 8 despite three interleaved refusals.

**FAIL** includes: a dialog appearing on any refused invocation; `SELECTED_USED` not reached after a
completed Selected command; `FULL_SCOPE_STARTED` not reached after a completed All-Shots command; any
refused-invocation snapshot's log sha256 differing from the immediately-preceding snapshot's; any of the
three refusal fingerprint-equality proofs reporting `equal: false`; a pre-existing log being captured as run
01 instead of seeding the baseline; state resetting on a document/session change without a restart (guard
would be session-scoped, contradicting the design); state surviving a real restart; a fresh post-restart
process being refused; any snapshot's own `production_sha256_matches_expected` being `False`; the checkpoint
script itself raising a "refusing to overwrite" error at any point (would indicate a numbering/schedule
mismatch, not evidence of a guard defect, but requires investigation before continuing); fewer than 15
snapshot file pairs or fewer than 8 preserved run-log files present at completion.

## Identities this checkpoint is pinned against

- Production Normalizer SHA-256 (F-closeout accepted state, final, now the governing pin): `1f4ec5a26605aa90380eb0532fec3915d2cc24a3a20473ed70d57198bd995db7`
- Production Normalizer SHA-256 (pre-copy-closeout, real-SFM-qualified 2026-09-24): `2c0edbb8a95f96147e6310fe1c039da7ee053f5e985f11bb3535dda8aa5ec23d`
- Production Normalizer SHA-256 (scope-aware, name-based identity, superseded): `1f2b87f2954d1944c06497a8adcda4de1e1663a148d655bf7cd6f3ace4f757dc`
- Production Normalizer SHA-256 (broad-guard, superseded; received PARTIAL real-SFM qualification through snapshot #5, see `../LEDGER.md`'s F3-Guard row): `6170d2a248845281b5f5d38dfea4b9f2decf908b8e3b79e80f4ada18d2f54625`
- Production Normalizer SHA-256 (pre-guard baseline): `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256 (unchanged, not touched by this work): `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Checkpoint script SHA-256 (final, deployed): `403c235aec5408c29f99e3c1c649ea225bb4f7023af12146713f620f40d30c50`
- Guard offline regression test SHA-256 (final): `c2b185ff464719304c6410f07c8023d279b7a70dbe126dbef3edc3bcd04cad38` — 81/81 PASS
- Checkpoint dry-run test SHA-256 (final): `76ff4a931446d29d51d1f78dff2a2fe4441a1363014befe52bc9467357bef9d3` — 47/47 PASS

## Explicit non-authorization

This checkpoint's own real-SFM result and the subsequent copy-only closeout correction did not reopen the
F1 optimization search and did not begin G. `F` is now **CLOSED** — see
`../F1_FINAL_DISPOSITION_REVIEW.md`'s FINAL CLOSEOUT section for the complete disposition. `G` has **NOT YET
BEGUN**.
