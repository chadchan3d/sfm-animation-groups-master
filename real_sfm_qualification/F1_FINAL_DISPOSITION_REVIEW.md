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

## Update (2026-09-24): scope-aware correction — the ">1 Selected shot = batch" proposal was rejected

The guard implementation above used Astra's original classification, under which any Selected Shot(s)
request over a single shot was treated as "batch" and gated identically to All Shots. **That classification
was reviewed and REJECTED as unsupported by the empirical evidence and harmful to the intended Selected
Shot(s) feature.** Nothing in this project's evidence (`F1-1`, `F2-R1-R3`, or any other checkpoint) shows
that selecting 2, 5, or 10 shots is unsafe — the only demonstrated failure mode involves large/cumulative
full-project workloads (All Shots, or repeated commands whose combined discovery cost approaches the same
scale). Selected Shot(s) is intended to support normal artist use across multiple selected shots, and the
guard must not cripple that.

The guard has been corrected accordingly. It now uses exactly two workload classes, never a numeric
threshold: **SELECTED_SCOPE** (Selected Shot(s) whose canonically resolved shot set is a proper subset of
the project, any size) and **FULL_SCOPE** (All Shots, or a Selected Shot(s) request whose resolved shot set
exactly equals the complete project shot set — exact workload equivalence, not a size threshold). Three
process states — `UNUSED`, `SELECTED_USED`, `FULL_SCOPE_STARTED` — replace the original single boolean:
Selected proper-subset use remains freely repeatable within one process (`UNUSED`/`SELECTED_USED` →
`SELECTED_USED`); only a full-scope request is gated, and only after either full-scope work has already
started in this process, or Selected-scope work has already been used and a *later* request is itself
full-scope. No numeric shot/target/model/control/memory threshold is used anywhere in this classification.
Full detail is recorded in `LEDGER.md`'s revised `F3-Guard` row and in
`checkpoint_process_attempt_guard/INSTRUCTIONS.md`.

**Historical-record correction (2026-09-24, independent review)**: an earlier version of this section
incorrectly stated the original broad-guard candidate (SHA-256
`6170d2a248845281b5f5d38dfea4b9f2decf908b8e3b79e80f4ada18d2f54625`) was never run against real SFM. That was
false. The operator DID begin its real-SFM guard qualification and intentionally stopped after snapshot #5
when the one-attempt-per-process product-policy problem was recognized — this has been independently
re-verified directly against the actual preserved artifacts on disk (`sfm_checkpoint_process_attempt_guard_
{state,result,summary}.{json,txt}` and `sfm_rebuild_control_groups.txt`), not merely recorded from a relayed
claim: fresh process (PID `15736`), marker absent; after opening/cancelling the scope dialog, marker still
absent and the production log unchanged; one real Selected-Shots command on `shot3` completed for real
(independently confirmed in the production log: `scope_mode=SELECTED_SHOTS scope_shots=1`,
`CONTEXTUALIZER_SCOPE_SHOT_NAMES = [u'shot3']`, `PRODUCTION_REBUILD_CONTROL_GROUPS = PASS`); the broad
process-attempt marker then present, run lock absent; a later Normalizer invocation was refused with the
production log byte-for-byte unchanged; the document/session was changed in the same SFM process; a later
invocation remained refused, again with the log unchanged. Full exact evidence is recorded in `LEDGER.md`'s
F3-Guard row. **Correct wording: the broad guard received PARTIAL real-SFM qualification through snapshot
#5. Its guard mechanics observed through that point behaved as designed. The qualification was intentionally
stopped before the restart/reset portion because the one-attempt-per-process product policy itself was
rejected as too restrictive** — not because of any guard-mechanics failure. This remains a design/policy
correction, not a reversal of a real result; no preserved evidence is rewritten or discarded.

A second, independent-review-driven correction (2026-09-24) found the scope-aware guard's own full-scope-
equivalence classifier used shot NAMES for identity (weaker than the contract, since duplicate shot names
could collapse distinct shots into a false match) instead of the canonical HANDLE/NATIVE-POINTER identity
`_resolve_selected_scope()` already uses for its own scope resolution. `_classify_scope_request()` has been
corrected to re-resolve every selected shot's canonical identity against a FRESH `sfmApp.GetShots()`
snapshot (never a stale pre-dialog one) via a new, self-contained helper —
`_resolve_selected_scope()` itself, part of the core mutation pipeline, was left completely untouched (`git
diff` confined to one contiguous 140-insertion/19-deletion region).

Offline qualification of the corrected, canonical-identity guard: **81/81 PASS**
(`test_process_attempt_guard_regression.py`, all 24 revised-contract items plus adversarial canonical-
identity coverage — duplicate-shot-name cases proving names cannot collapse or fabricate identity, a
reordered-selection case proving order-independence, and unresolved/ambiguous-identity cases failing closed)
plus **17/17 PASS** for the companion real-SFM checkpoint script's own dry run (unchanged functionally,
since it never calls the classifier itself). The canonical-identity candidate (SHA-256
`2c0edbb8a95f96147e6310fe1c039da7ee053f5e985f11bb3535dda8aa5ec23d`) and the checkpoint script have both been
deployed to the live SFM install and hash-verified matching the repo exactly.

**This candidate has NOT yet been qualified against real SFM.** `F` remains **OPEN**; the F1 optimization
search remains CLOSED/exhausted (not reopened); `G` has not begun.

## Update (2026-09-24): checkpoint evidence-file discipline corrected

Before the real-SFM run, the checkpoint script's own evidence-file handling was corrected: the operator must
never manually rename or copy files between steps, and no evidence file may ever be overwritten. Each of the
13 fixed-schedule snapshots now writes a new, uniquely-numbered, immutable file pair
(`sfm_scope_guard_snapshot_NN_<operation>.{json,txt}`); the checkpoint itself detects a changed production
log and copies it into a new, uniquely-labeled, immutable file from a fixed 8-entry schedule
(`sfm_scope_guard_run_NN_<label>.txt`), so the operator never manually preserves
`sfm_rebuild_control_groups.txt`; immutable per-step cumulative-history indexes are also written; and only a
small, explicitly non-evidentiary continuation-state pointer file plus the freely-overwritten final rollup
(`sfm_scope_guard_final_result.json`/`_final_summary.txt`) are ever replaced. The write primitives refuse
(raise) rather than silently overwrite an existing evidence filename. This is a checkpoint-tooling
correction only — the guard implementation and its qualification semantics are unchanged. Offline
qualification: `test_checkpoint_process_attempt_guard_dryrun.py` (SHA-256
`70eda6991d2f2f8337db61a37de4af6b0cc6e46b170831d9f4d12d6cc3d16ca6`) — **33/33 PASS**. Checkpoint script
SHA-256: `8c347db86a84d7f293cb4872d19fd8fe4e31350f5d26ee9337e71d954b4eb11e`, deployed and hash-verified. The
real-SFM checkpoint was not run. `F` remains **OPEN**; `G` has not begun.

## Update (2026-09-24): two evidence-integrity defects in the above correction fixed

Independent review of the evidence-file-discipline correction found two defects, fixed before the real-SFM
run: (a) snapshot 01 (baseline) could incorrectly capture a PRE-EXISTING production log (left over from
earlier qualification work) as run 01, corrupting the fixed 8-run schedule — fixed so snapshot 01 only
fingerprints and seeds the checkpoint's own "last known log" pointer, never advancing the run counter; the
first genuinely NEW log content at a later snapshot becomes the real run 01. (b) The prior 13-snapshot
schedule combined a refused invocation with the next successful command before the next observation, so it
could not actually prove the refusal alone left the log unchanged — the schedule is expanded to 15 snapshots
so a dedicated snapshot immediately follows every refusal, and the checkpoint now mechanically computes and
records three refusal fingerprint-equality proofs directly into the rollup. Manual operator resource-sample
recording was also removed (extracted after the fact from the 8 preserved run logs instead) and the
operator's shot/target/control selections were made fully deterministic. Offline: `test_process_attempt_
guard_regression.py` re-run unchanged at **81/81 PASS** (production untouched);
`test_checkpoint_process_attempt_guard_dryrun.py` (SHA-256
`ab45cce04235d951e72f21a7543d98a9f76df789c7828836c7299cb61e91cf1c`) — **47/47 PASS**. Checkpoint script
SHA-256: `1c004bdaefba48e61b21339a2c5bbea348034d1201f8b29940208173bc287a58`, deployed and hash-verified. The
real-SFM checkpoint was not run. `F` remains **OPEN**; `G` has not begun.

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
