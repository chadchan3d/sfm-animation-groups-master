# F Final Disposition Review (prepared for independent review — not acted on)

**Status: prepared only.** This document answers the six requested questions from the evidence already
established in `LEDGER.md` and `F1_OPTIMIZATION_INVESTIGATION_SUMMARY.md`. It does not close `F`, does
not begin `G`, and does not propose or run any new experiment. The disposition itself — whether the
answers below are sufficient to close `F` — is for independent review, not decided here.

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
discovery sites) and does **not** get released by garbage collection (consistent across `F1-R3` through
`F1-R6`). This retained cost **accumulates** across multiple such commands run back-to-back in one
unbroken process, which is what a 32-bit address space eventually cannot absorb.

**The failed behavior is specifically: multiple Rebuild Control Groups commands, each triggering its own
full discovery pass, executed consecutively within a single SFM process that is never restarted between
them.**

## 2. What single-command behavior has already passed?

Every single-command execution in this project's entire history has passed:

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
  semantically-verified result. **No single command has ever failed or crashed anywhere in this project's
  history.** Every observed failure (`F1-1`/`F1-2`) was specific to multiple consecutive commands in one
  unbroken process.

## 3. What practical user workflow does the product require?

The Rebuild Control Groups Normalizer is a maintenance/setup utility invoked from SFM's MAINMENU to
(re)build control-group structure for a project — run occasionally (e.g., after adding models/rigs or
restructuring animation sets), not as a continuously or repeatedly invoked per-frame or per-edit
operation. Ordinary SFM work (posing, animating, rendering) never invokes it at all. A realistic session
looks like: open SFM, work on a project, run the Normalizer once (Selected or All Shots) when control-
group maintenance is actually needed, continue other work, and eventually close or restart SFM through
ordinary session boundaries — not "run this specific tool repeatedly back-to-back in one unbroken process"
(the exact pattern `F1-1`/`F1-2` deliberately engineered to stress-test).

## 4. Release blocker, documented limitation, or stress behavior outside normal usage?

This is presented as the evidence-supported reading, not a unilateral verdict — the classification itself
is for independent review:

- Every actual unit of user-facing work — one command — has passed cleanly, with memory staying bounded
  (up to ~3.42GB on the tested fixture, never exceeding the 32-bit ceiling) and zero crashes, across every
  single-command run in this project's history (`C1`/`C2`/`D1`/`D2`/every `F1-R` checkpoint).
- The only real failure occurred under a specific, deliberately-engineered repeated-command stress
  pattern (4 consecutive commands, no restart) — not literally how the tool is normally invoked per
  Q3.
- An exhaustive, real-SFM-verified search (`F1-R2` through `F1-R8`) found no material, semantics-
  preserving fix available anywhere in this SFM install's own Python/datamodel surface.

Given those three facts together, the evidence points toward this being either a **documented practical
limitation** (e.g., "restart SFM between Rebuild Control Groups runs, especially in a 32-bit process") or
a **stress behavior outside normal product usage**, rather than a release blocker for the tool's actual,
ordinary single-command-per-session use. Whether that classification is acceptable for release is the
reviewer's call, not asserted here as final.

## 5. Is one successful Selected/All command per ordinary editing workflow sufficient?

Based on the pattern established across every single-command run in this project (`C1`/`C2`/`D1`/`D2`,
and every native-only/discovery-isolated/streaming-candidate/legacy run in `F1-R1` through `F1-R8`):
**yes** — one successful Selected or All Shots command per ordinary editing session accomplishes the
tool's actual purpose (rebuilding control groups) and has been repeatedly, independently verified as
semantically correct and resource-bounded.

## 6. What minimum practical real-SFM confirmation, if any, is still needed before F can be closed and G can begin?

Already covered by existing, real-SFM-verified evidence: single-command correctness for both scopes
(Selected/All Shots), both pre- and post-integration, on the real qualification project; single-command
resource behavior staying within the 32-bit ceiling on the tested fixture; the exact mechanism and
magnitude of repeated-command retained growth; and an exhaustive, concluded search for a fix.

Open questions worth the reviewer's own judgment (named here, not proposed as new experiments to run):

1. Every single-command resource measurement in this project was taken against the same qualification
   fixture (a bounded, ~62-eligible-target project). Whether "one command per session is sufficient" holds
   on substantially larger real production scenes has not been separately measured.
2. Whether the practical guidance should be an unconditional "restart SFM between Rebuild Control Groups
   runs" or a more specific safe-repeat-count — this is a documentation/product decision, not a further
   diagnostic.
3. Whether the tool's own UI should warn the user after a command completes that repeating it without
   restarting SFM is not recommended — a UX decision, explicitly outside this investigation's own scope.

None of the above requires reopening the optimization search (F1) — that search is concluded. Whether any
of them constitutes a "minimum practical confirmation still needed" before closing `F`, or whether the
evidence already on record is sufficient, is the disposition this review exists to obtain.
