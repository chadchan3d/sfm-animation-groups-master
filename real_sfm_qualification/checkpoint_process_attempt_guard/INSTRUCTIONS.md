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
  `ec729e253ef366a451c22dfd752f33e3a5cad2f0b0dc184393912be7e07e210a`) — **17/17 PASS** — offline-verifies
  this checkpoint script itself never references `StartRebuildControlGroups()`/scope-dialog machinery/
  substantial-traversal identifiers; `load_production_definitions()` extracts exactly the pinned scope-aware
  definitions by exact line range without importing the real SFM-only modules; `take_snapshot()` against a
  fresh real `QtCore.QObject` main window correctly reports `UNUSED` and the exact real marker names
  (`SELECTED_USED`, `FULL_SCOPE_STARTED`, and the legacy marker name); `main()` persists auto-numbered
  snapshots without ever overwriting prior history. (This checkpoint script never calls the classifier
  itself, so it needed no functional change for the canonical-identity correction — only the pinned
  production SHA-256 was updated.)

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

At each numbered **[SNAPSHOT]** step, run `Checkpoint_Process_Attempt_Guard_Qualification`. It is a pure
read-only observer — it never calls the real Normalizer itself, never opens a dialog, and performs zero
scene/provider/native work. Each run appends one auto-numbered record (`process_scope_state`,
`run_lock_present`, production-log fingerprint) and reprints the full history so far.

### Phase A — Selected Shot(s) normal workflow

1. **RESTART SFM FIRST.**
2. Open **only** `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx` (the accepted normalized qualification fixture) —
   never `testscripts.dmx`.
3. **[SNAPSHOT #1 — baseline.]** Expect `process_scope_state = UNUSED`, `run_lock_present = False`,
   `production_sha256_matches_expected = True`.
4. Invoke the real **Rebuild Control Groups** command. When the scope dialog appears, click **Cancel**.
5. **[SNAPSHOT #2 — proves cancel leaves state unused.]** Expect `process_scope_state = UNUSED` still, and
   the production-log fingerprint unchanged from snapshot #1.
6. Invoke **Rebuild Control Groups** again. Choose **Selected Shot(s)**, selecting `shot3` alone. Let it run
   to completion. Record command-start/command-end resource samples (private bytes, free VAS, largest free
   region).
7. **[SNAPSHOT #3 — proves SELECTED_USED.]** Expect `process_scope_state = SELECTED_USED`,
   `run_lock_present = False`.
8. Invoke **Rebuild Control Groups** again. Choose **Selected Shot(s)**, this time selecting a representative
   multi-shot subset of approximately **five** shots, using a deterministic fixture subset that includes
   meaningfully denser shots such as `shot8` and/or `shot11` (this must remain a **proper subset** of the
   project — do not select every shot). Let it complete normally. Record resource samples before/after.
9. Run another, **different** Selected proper-subset selection (any shots not yet exercised, still a proper
   subset). Let it complete. Record resource samples before/after.
10. Make one documented, legitimate presentation/group edit in one previously-processed shot (any real,
    predetermined control-group change that genuinely warrants renormalization — do not invent an
    arbitrary edit; reuse the same kind of qualified edit this project has used before, e.g. moving a
    control to/from the `Hidden` group per `checkpoint_f2_r1/F2_R1_CONTROLLED_EDIT_JUSTIFICATION.md`, if a
    fresh qualified edit target is not otherwise available — STOP and report if none can be identified
    safely rather than inventing one).
11. Re-run a Selected proper-subset scope containing the edited shot and verify the expected correction is
    applied. Record resource samples before/after.
12. Request **All Shots**. **REQUIRE refusal before any expensive work begins** (no scope-collection delay,
    immediate message).
13. Immediately afterward, invoke **Rebuild Control Groups** again and run another Selected proper-subset
    request. **REQUIRE it is still permitted** and completes normally.
14. **[SNAPSHOT #4 — proves the refused All left state unchanged and Selected use continued normally.]**
    Expect `process_scope_state = SELECTED_USED` still (never became `FULL_SCOPE_STARTED`), and the
    production-log fingerprint reflects only the permitted commands (steps 6/8/9/11/13), never a truncated/
    partial write from the refused All-Shots attempt in step 12.
15. Reopen or switch to a **different** document in the same SFM process (no restart).
16. **[SNAPSHOT #5 — proves the guard is process-scoped, not session-scoped.]** Expect
    `process_scope_state = SELECTED_USED` still.
17. Attempt another Selected proper-subset request after the session change. **REQUIRE it is still
    permitted** and completes normally.

**Resource reporting for Phase A (steps 6/8/9/11/13/17):** for each command, report exact private bytes,
free VAS, largest free region, and the deltas from the immediately preceding command — in bytes and MiB.
**If realistic multi-shot Selected use itself shows substantial cumulative depletion comparable to the
known large-run failure pattern (F1-1/F2-R1-R3), STOP and report the evidence rather than silently treating
Phase A as passed** — this checkpoint's purpose is to observe and report, not to assume Selected use is
unconditionally safe at any command count.

### Phase B — full-scope behavior

18. **Fully restart SFM.**
19. Reopen `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx`.
20. **[SNAPSHOT #6 — proves a fresh process starts UNUSED.]** Expect `process_scope_state = UNUSED`, and
    `current_pid` different from every Phase A snapshot's own PID.
21. Run **one** standalone **All Shots** operation. Let it complete. Record resource samples before/after.
22. **[SNAPSHOT #7 — proves FULL_SCOPE_STARTED.]** Expect `process_scope_state = FULL_SCOPE_STARTED`.
23. Attempt **Selected Shot(s)** (any proper subset). **REQUIRE immediate refusal before any expensive work
    begins.**
24. Attempt **All Shots** again. **REQUIRE immediate refusal before any expensive work begins.**
25. **[SNAPSHOT #8 — proves both later attempts left state unchanged and the log was not touched.]** Expect
    `process_scope_state = FULL_SCOPE_STARTED` still, and the production-log fingerprint unchanged from
    snapshot #7.
26. **Fully restart SFM.**
27. Reopen the fixture. **[SNAPSHOT #9 — proves the state resets.]** Expect `process_scope_state = UNUSED`,
    new `current_pid`.
28. Run a Selected Shot(s) request (any proper subset). **REQUIRE it is permitted** and completes normally.

**Do NOT execute a second All Shots command in one process. Do NOT deliberately recreate the known crash.**

### Selected-equals-all-shots equivalence

Also confirm exact Selected-set-equals-complete-project-set classification behaves as `FULL_SCOPE`, either:

- in this real-SFM checkpoint if practical without triggering another heavy run (e.g., from a fresh `UNUSED`
  process, select **every** project shot individually through Selected Shot(s) rather than the All-Shots
  button, and confirm the admission guard treats it exactly like All Shots — same refusal behavior for any
  later request in that process); or
- offline, through the exact same classifier code — already covered by
  `test_process_attempt_guard_regression.py` items 10/10b/11a/11b (**64/64 PASS**, including the exact-set-
  equality case and a large-but-proper-subset case proving there is no size threshold).

## Output files to return

- `C:\Users\Public\Documents\sfm_checkpoint_process_attempt_guard_result.json` (the full snapshot history)
- `C:\Users\Public\Documents\sfm_checkpoint_process_attempt_guard_summary.txt`
- `C:\Users\Public\Documents\sfm_checkpoint_process_attempt_guard_state.json`
- The real Normalizer's own output artifacts from every permitted command in steps 6/8/9/11/13/17/21/28
  (`sfm_rebuild_control_groups.txt` and whatever result/summary files that command itself produces), for
  independent cross-reference against the checkpoint's own `production_log` fingerprints.
- The resource samples recorded at each step in Phase A and Phase B.

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
post-restart process being refused; any snapshot's own `production_sha256_matches_expected` being `False`.

## Identities this checkpoint is pinned against

- Production Normalizer SHA-256 (canonical-identity candidate, current): `2c0edbb8a95f96147e6310fe1c039da7ee053f5e985f11bb3535dda8aa5ec23d`
- Production Normalizer SHA-256 (scope-aware, name-based identity, superseded): `1f2b87f2954d1944c06497a8adcda4de1e1663a148d655bf7cd6f3ace4f757dc`
- Production Normalizer SHA-256 (broad-guard, superseded; received PARTIAL real-SFM qualification through snapshot #5, see `../LEDGER.md`'s F3-Guard row): `6170d2a248845281b5f5d38dfea4b9f2decf908b8e3b79e80f4ada18d2f54625`
- Production Normalizer SHA-256 (pre-guard baseline): `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256 (unchanged, not touched by this work): `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Checkpoint script SHA-256: `7be08aa277cea7b8b8deb7892637ab75c0462d318e3d411033039ff145266f38`
- Guard offline regression test SHA-256: `bfd1c197fe16e0f460957445af2e85a694e8aba73c2729f458eaa092c1492c84`
- Checkpoint dry-run test SHA-256: `ec729e253ef366a451c22dfd752f33e3a5cad2f0b0dc184393912be7e07e210a`

## Explicit non-authorization

This checkpoint does not modify production beyond the already-implemented guard, does not reopen the F1
optimization search, and does not begin G. `F` remains `OPEN` pending this checkpoint's own real-SFM result
and independent review of the recommended admission policy recorded in `../F1_FINAL_DISPOSITION_REVIEW.md`.
