# F Final Disposition Review (prepared for independent review — not acted on)

**Status: prepared only.** This document answers the six requested questions from the evidence already
established in `LEDGER.md` and `F1_OPTIMIZATION_INVESTIGATION_SUMMARY.md`. It does not close `F`, does
not begin `G`, and does not propose or run any new experiment. The disposition itself — whether the
answers below are sufficient to close `F` — is for independent review, not decided here.

## Update (2026-09-24): F2-R1-R3 real-SFM result resolves the open question raised in Q6

`F2-R1` (see `checkpoint_f2_r1/INSTRUCTIONS.md`, `LEDGER.md` F2-R1 row) was the one narrow real-SFM
confirmation `F1_REPEAT_HISTORY_AUDIT.md` identified as still missing: does a legitimate workflow — All
Shots completes, ordinary editing, one real predetermined control-group edit that genuinely warrants
renormalization, All Shots again — succeed in one unrestarted SFM process. The F2-R1-R3 hardened script
validly reached Stage 2 for real (mode classification correct: same-process marker present, current PID
matched Stage 1's own recorded PID exactly) and **Stage 2's own real production All-Shots command crashed**
at target 54 of 62, immediately after `PRE_NATIVE` telemetry, with no subsequent `NATIVE_REBUILD_RETURNED`
line and no further log content — an unambiguous terminal trace. Formal classification:

**F2-R1 FAIL — LEGITIMATE SAME-PROCESS REINVOCATION IS NOT RELIABLY SUSTAINABLE.** A legitimate,
product-intended workflow (one completed All-Shots command, an intervening real edit that genuinely
warrants renormalization, one further All-Shots command, all within a single unrestarted SFM process) was
qualified for real and did not complete. Stage 2 was validly reached — this is not a harness artifact —
and Stage 2 itself crashed mid-command, carrying forward retained memory/VAS pressure from Stage 1's own
already-completed command in the same process. Full evidence, exact byte-level deltas across three
checkpoints (Stage-2-start / `AFTER_SHOT_13` / final `PRE_NATIVE`), and independent verification against
the primary artifacts are recorded in the `LEDGER.md` F2-R1 row.

This result:

- Resolves the open question this document's own Q6 named ("whether a single standalone command's
  resource behavior holds..." was already answered; the genuinely open question was whether **repeated**
  legitimate use in one process is safe) — it is now **RESOLVED UNSAFE** on the qualified workload.
- Does **not** reopen the F1 optimization search. That search's own conclusion —
  **OPTIMIZATION SEARCH SUFFICIENTLY EXHAUSTED** — is unchanged; F2-R1 is not an F1 optimization
  experiment and its failure says nothing about whether a fix exists, only that repeated use without a
  restart is not currently safe.
- Means no further F runtime experiments are warranted to establish repeated-command safety. The
  question F2-R1 was designed to answer has been answered.
- Leaves `F` **OPEN** only for a final product-policy/admission disposition (see the recommended policy
  below); `G` has **not** begun.
- Does not retroactively reclassify F2-R1's own three prior real attempts, which remain
  `HARNESS MODE-CLASSIFICATION FAILURE / INCONCLUSIVE` — those were harness defects with no production
  command ever run; F2-R1-R3 is a new, distinct, decisive result from a hardened script that reached
  Stage 2 for real.

### Recommended admission/recovery policy (recorded for independent review — not implemented in this task)

After one successful Normalizer command completes in an SFM process, the product should **block any
further Normalizer invocation in that same process** before allowing production work to continue, with an
explicit operator-facing instruction to save, restart SFM, reopen the file, and re-run the Normalizer if
another normalization is genuinely needed. This guard should apply to **any** subsequent Normalizer
invocation in that process — not only a second All-Shots command — because:

- The safe repeat count is workload-dependent, not a fixed number: `F1-1` already showed cumulative
  pressure building across a **Selected → Selected → All** sequence (crashing on the 3rd command, not the
  2nd), while `F2-R1` now shows a **legitimate All → [edit] → All** sequence failing on its 2nd command.
  Two different workloads failed at two different command counts.
- No evidence in this project supports a universal safe threshold (e.g., "exactly one repeat is always
  safe" or "exactly two commands is always safe") — the observed failures depend on scope (Selected vs.
  All), target count, and how much retained pressure the specific commands already run happened to
  accumulate.
- A simple one-command-per-process rule avoids guessing at a threshold this evidence base cannot support,
  while not removing any capability — normalization remains fully available immediately after a restart.

This was recorded above as a recommendation for independent review, exactly as the evidence supports it.
**Update (2026-09-24): Astra's independent F release-disposition review authorized implementing it** — see
the section immediately below. The recommendation as originally written, and the evidence supporting it, is
preserved unchanged above; only its implementation status has changed.

## Update (2026-09-24): Astra-authorized guard implementation

Astra's independent review of this document (and the full F2-R1-R3 evidence chain) returned:
**AUTHORIZE GUARD IMPLEMENTATION**, with a detailed implementation contract (arm before scope-control
collection; refuse used processes before scope selection; recheck atomically at arming; fail closed on
marker lookup/installation errors; retain the marker after every post-arming outcome until process exit;
complete the narrow qualification before closing F).

The one-resource-consuming-Normalizer-attempt-per-SFM-process guard recommended above has been implemented
directly in production (`audit_external_runtime/Rebuild_Control_Groups_Normalizer.py`) as a gate-only
change — a pure 204-line addition with zero deletions against the prior committed script (`git diff
--stat`), touching no existing Normalizer semantics, Selected/All semantics, authority rules, discovery
freshness, provider/broker semantics, native Rebuild behavior, validation coverage, failure safety, model
support, or target-transaction mechanics. Full implementation detail, the exact refusal/arming boundaries,
and the fail-closed semantics are recorded in `LEDGER.md`'s new `F3-Guard` row and in
`checkpoint_process_attempt_guard/INSTRUCTIONS.md`.

Offline qualification: **52/52 PASS** (`test_process_attempt_guard_regression.py`, all 16 contract items)
plus **15/15 PASS** for the companion real-SFM checkpoint script's own dry run
(`test_checkpoint_process_attempt_guard_dryrun.py`). The guarded candidate and the new checkpoint script
have both been deployed to the live SFM install and hash-verified matching the repo exactly.

**This candidate has NOT yet been qualified against real SFM.** A real-SFM checkpoint
(`checkpoint_process_attempt_guard/`) has been prepared, per instruction, but not run. `F` remains **OPEN**
— per Astra's own review, the narrow real-SFM qualification of this guard must complete before `F` can
close. The governing "Production Normalizer SHA-256" identity in `LEDGER.md` is deliberately left pointing
at the pre-guard, already-accepted baseline until that qualification passes, consistent with how every
other unqualified production candidate has been treated in this project. This implementation does not
reopen the F1 optimization search (still concluded/exhausted) and does not begin `G`.

## 1. What repeated-use behavior has actually failed?

The one real, observed failure in this entire investigation is **`F1-1`**: an actual SFM process crash
during the 3rd of 4 consecutive real commands (Selected×2, All×2) run back-to-back in **one continuous,
never-restarted SFM process**. `F1-2`'s corrected harness still did not reach a clean, fully-verified 4th
command.

The mechanism, precisely quantified across `F1-R1` through `F1-R8`, is **not** "any second command
always grows retained memory" — `F1-R1` showed a second Selected command, measured in isolation from the
harness's own verification overhead, itself produced **zero** retained private/VAS growth. The real
driver is fresh `discover_rig_context()` calls performed during native Rebuild's own discovery schedule
(up to 250 discovery calls across 62 eligible targets per command, per the real, source-derived branch
schedule established in `F1-R4`), whose retained cost is dominated by scene traversal/materialization
(`F1-R5`: ~92% of private growth / ~96% of free-VAS loss survives even after removing 126 of 250 full
discovery sites). The failure is associated with **cumulative process-retained memory/VAS pressure
dominated by fresh discovery's scene traversal** — this attribution is established, and is not weakened
here. Across `F1-R3` through `F1-R6`, **ordinary garbage collection was repeatedly observed not to
materially return that pressure**. **The exact lower-level allocator/SWIG/native retention mechanism
responsible remains unproven** — `F1-R5`'s own audit classified candidate mechanisms such as CPython
`pymalloc` arena non-release and SWIG wrapper pooling as `UNKNOWN`/`MEASUREMENT_CANDIDATE`, never
confirmed as the sole or proven cause from source evidence alone. This retained pressure **accumulates**
across multiple such commands run back-to-back in one unbroken process, which is what a 32-bit address
space eventually cannot absorb.

**The failed behavior is specifically: multiple Rebuild Control Groups commands, each triggering its own
full discovery pass, executed consecutively within a single SFM process that is never restarted between
them.**

## 2. What single-command behavior has already passed?

Every standalone, fresh-process qualification of a single command in this project's history has passed:

- `C1-2` — PASS: baseline (pre-integration) Selected-Shots command against a real project; exactly the
  expected 2 targets touched, 83 untouched peers verified unchanged.
- `C2-1` — PASS: the same command with integrated (accepted) production code; 85/85 target parity, 83/83
  peer parity against `C1-2`'s own baseline; authority/native-protection evidence clean.
- `D1-3` — PASS: baseline (pre-integration) **All-Shots** command; 57 changed / 28 unchanged / 78 excluded
  targets, all correct; memory rose from ~2.99GB to ~3.42GB working set **within one command** —
  approaching but never exceeding the 32-bit ceiling, zero `MemoryError`.
- `D2-2` — PASS: the same All-Shots command with integrated production code; exact equivalence to
  `D1-3`'s own baseline; authority lifecycle clean.
- `F1-R1` through `F1-R8` — every individual real command run in this whole optimization search (native-
  only, discovery-isolated, streaming-candidate, or legacy) completed correctly and produced the expected,
  semantically-verified result.

**Every standalone/fresh-process qualification of a single Selected or All command has completed
successfully. The only observed production crash occurred during the third consecutive command in one
unrestarted SFM process** (`F1-1`); `F1-2`'s corrected harness still did not reach a clean, fully-verified
4th command. This is not a claim that every invocation under every process-lifetime condition has passed
— only that no standalone, freshly-started qualification of a single command has ever failed; the one
observed failure occurred specifically as the third of several consecutive commands within one unbroken
process.

## 3. What practical user workflow does the product require?

The Rebuild Control Groups Normalizer is an **occasional maintenance operation used when control-group
structure needs normalization** — e.g., after adding models/rigs or restructuring animation sets — not a
continuously or repeatedly invoked per-frame or per-edit operation. Ordinary SFM work (posing, animating,
rendering) never invokes it at all. **Immediate repeated whole-session normalization of an
already-normalized session is not an intended workflow.** This does not rule out a later, legitimate
invocation after meaningful scene/control-group changes, within the same or a later session — only that
reflexively re-running the Normalizer against a session it has already just normalized, with no
intervening change, is not how the product is meant to be used. This is a description of intended use, not
a claim that the product formally prohibits more than one invocation per SFM process — the one observed
failure (`F1-1`/`F1-2`) occurred under a specific, deliberately-engineered repeated-command stress pattern
(4 consecutive commands, no restart, no intervening change), not the workflow described here.

## 4. Release blocker, documented limitation, or stress behavior outside normal usage?

This is presented as the evidence-supported reading, not a unilateral verdict — the classification itself
is for independent review:

- Every standalone/fresh-process qualification of a single command — Selected or All Shots, baseline or
  integrated — has completed successfully, with memory staying bounded (up to ~3.42GB on the tested
  fixture, never exceeding the 32-bit ceiling) (`C1`/`C2`/`D1`/`D2`/every `F1-R` checkpoint). The only
  observed production crash occurred during the third consecutive command in one unrestarted SFM process
  (`F1-1`); this is not a claim that every invocation under every process-lifetime condition has passed.
- The only real failure occurred under a specific, deliberately-engineered repeated-command stress
  pattern (4 consecutive commands, no restart) — not the intended occasional-maintenance workflow
  described in Q3.
- An exhaustive, real-SFM-verified search (`F1-R2` through `F1-R8`) found no material, semantics-
  preserving fix available anywhere in this SFM install's own Python/datamodel surface.

Given those three facts together, the evidence points toward this being either a **documented practical
limitation** (e.g., "restart SFM between Rebuild Control Groups runs, especially in a 32-bit process") or
a **stress behavior outside normal product usage**, rather than a release blocker for the tool's intended,
occasional-maintenance use. Whether that classification is acceptable for release is the reviewer's call,
not asserted here as final.

## 5. Is one successful Selected/All command per ordinary editing workflow sufficient?

Based on the pattern established across every standalone, fresh-process single-command run in this
project (`C1`/`C2`/`D1`/`D2`, and every native-only/discovery-isolated/streaming-candidate/legacy run in
`F1-R1` through `F1-R8`): **yes** — one successful Selected or All Shots command accomplishes the tool's
actual purpose (rebuilding control groups) and has been repeatedly, independently verified as
semantically correct and resource-bounded. This describes what a single, standalone invocation achieves;
it does not itself establish that repeated invocations within one unrestarted process are safe, and it
does not assert that the product formally requires exactly one invocation per session — the Normalizer
remains available for legitimate re-invocation after real control-group-affecting changes (see Q3).

## 6. What minimum practical real-SFM confirmation, if any, is still needed before F can be closed and G can begin?

Already covered by existing, real-SFM-verified evidence: single-command correctness for both scopes
(Selected/All Shots), both pre- and post-integration, on the real qualification project; single-command
resource behavior staying within the 32-bit ceiling on the tested fixture; the established attribution and
magnitude of repeated-command retained growth (dominant cause identified; exact lower-level retention
mechanism not proven); and an exhaustive, concluded search for a fix.

Open questions worth the reviewer's own judgment (named here, not proposed as new experiments to run):

1. Every single-command resource measurement in this project was taken against the same qualification
   fixture (a bounded, ~62-eligible-target project). Whether a single standalone command's resource
   behavior holds on substantially larger real production scenes has not been separately measured.
2. Whether the practical guidance should be an unconditional "restart SFM between Rebuild Control Groups
   runs" or a more specific safe-repeat-count — this is a documentation/product decision, not a further
   diagnostic.
3. Whether the tool's own UI should warn the user after a command completes that repeating it without
   restarting SFM is not recommended — a UX decision, explicitly outside this investigation's own scope.

None of the above requires reopening the optimization search (F1) — that search is concluded. Whether any
of them constitutes a "minimum practical confirmation still needed" before closing `F`, or whether the
evidence already on record is sufficient, is the disposition this review exists to obtain.
