# F1 Repeat-Command History Audit — All Shots → All Shots

Evidence-reconstruction only. No SFM run performed. No new qualification test created. No production
modified. No optimization work reopened. No documentation altered except where noted at the end.

## Search performed

Searched: the full working tree (`real_sfm_qualification/checkpoint_f1*`, `checkpoint_f1_r1`,
`checkpoint_f1_2`), every real-SFM runtime artifact preserved under `C:\Users\Public\Documents\`, `git log
--all` for every commit touching F1/F1-1/F1-2/F1-R1, and `git log --all --diff-filter=D` for any deleted
F1-related file (none found — no abandoned/superseded repeat checkpoint exists beyond F1-1 → F1-R1 → F1-2,
confirmed by the unbroken commit sequence `b57371e` → `1565f5a` → `12077ca` → `0dee82c`). No file was
found or lost through history that isn't already referenced below.

## Chronological run table

| Run | Command | Scope | SFM process freshness | Command began | Production processing began | Last preserved state | Command completed | Final marker present | Verifier ran | Crash/hang directly observed | Process termination observed | Memory/VAS at boundary | Primary artifact | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F1-1 | 1 | Selected | Fresh restart | Yes | Yes | — | Yes (implied; command 2 exists) | — | — | No | No | not separately preserved | (superseded by F1-2's own re-run of this exact scope) | COMPLETED |
| F1-1 | 2 | Selected | Same process as cmd 1 | Yes | Yes | — | Yes (implied; command 3 log exists and represents production's continuous run) | — | — | No | No | not separately preserved | — | COMPLETED |
| F1-1 | 3 | **All** | Same process as cmd 1-2 | Yes | Yes | Target 4/8 in shot8 (`lola bunny1`), `PRE_NATIVE` telemetry logged, `target_seq=52` | **No** | No | No | **Yes** — production log itself ends abruptly mid-target, immediately after `PRE_NATIVE`, with no subsequent `NATIVE_REBUILD_RETURNED` line, no further target output, no `FINAL_REPORT_ENTRY`, no exception trace, no controlled shutdown message | Yes (the SFM process crash is the reason no further log lines exist; corroborated by the checkpoint's own already-recorded "FAIL" disposition and by `git log` commit `1565f5a`'s own text: *"crashed the real SFM process during command 3 (All Shots), target_seq 52, immediately after PRE_NATIVE telemetry"*) | `working_set=3452686336`, `pagefile=3499929600`, `largest_free` not re-sampled at this exact point (last VAS sample was at `CP0_COMMAND_START`) | `real_sfm_qualification/checkpoint_f1/f1_1_crash_evidence/sfm_rebuild_control_groups_F1-1_command3_crash.txt` (1,906 lines, `scope_mode=ALL_SHOTS scope_shots=15` confirmed at line 22) | **CRASHED** |
| F1-1 | 4 | All (intended) | — | **No** | No | — | No | No | No | No | N/A | N/A | none — command 4 was never reached because command 3 crashed the process | **NOT_STARTED** |
| F1-R1 | 1-2 | Selected ×2 | Fresh restart | Yes | Yes | — | Yes | — | — | No | No | not the focus of this audit | `LEDGER.md` F1-R1 row | COMPLETED (not relevant to All→All) |
| F1-R1 | 3 | All | Same process | Yes | Yes | — | Yes | — | — | No | No | not the focus of this audit | `LEDGER.md` F1-R1 row | COMPLETED (not relevant to All→All) |
| F1-R1 | 4th command | — | — | **Never attempted by design** ("Selected Shots x2, All Shots x1, **no 4th command**" — deliberate, per F1-R1's own design intent, not a failure) | — | — | — | — | — | — | — | — | `checkpoint_f1_r1/INSTRUCTIONS.md`, commit `1565f5a` | **NOT_STARTED** (by design) |
| F1-2 | 1 | Selected | Fresh restart | Yes | Yes | — | Yes | Yes | Yes | No | No | private `3138953216`→`3153453056` (~13.83 MiB growth), zero free-VAS loss | `sfm_checkpoint_f1_2_result.json` `command_records[0]` | COMPLETED |
| F1-2 | 2 | Selected | Same process as cmd 1 | Yes | Yes | — | Yes | Yes | Yes (idempotence: Fox/Mia hashes exactly match cmd 1) | No | No | private `3156811776`→`3160018944` (~3.06 MiB growth), zero free-VAS loss | `sfm_checkpoint_f1_2_result.json` `command_records[1]` | COMPLETED |
| F1-2 | 3 | **All** | Same process as cmd 1-2 | Yes | Yes | All 15 shots / 62 targets processed; `FINAL_REPORT_ENTRY` reached | **Yes** | Yes | Yes (production's own periodic-global and end-of-run verifiers, zero private delta) | No | No | CP0 private `3166584832`/free VAS `416239616`/largest free `186384384` → FINAL private `3404951552`/free VAS `182996992`/largest free `75366400` — **within this one command**: private +`238366720` B (~227.32 MiB), free-VAS −`233242624` B (~222.44 MiB), largest-free −`111017984` B (~105.88 MiB) | `sfm_checkpoint_f1_2_result.json` `command_records[2]`; `sfm_checkpoint_f1_2_production_log_command3.txt` (401,629 bytes, full log, ends cleanly) | **COMPLETED** |
| F1-2 | 4 | **All (intended)** | **Same process as cmd 1-3, immediately following cmd 3's own completion** | **Not evidenced** — see below | Not evidenced | None whatsoever — no `before_command_4` memory snapshot, no `command_records[3]` entry, no `command_4.*` check, no `sfm_checkpoint_f1_2_production_log_command4.txt` of any kind (not even truncated) | No | No | No | **No** — no crash log, no exception trace, no truncated production log exists for this command at all | Not directly observed; inferred only from total silence after command 3's own complete, clean post-processing | Rolling JSON left `in_progress: True`, `overall_pass: None`; last written state is command 3's own `after_command_3_gc_collect` snapshot | `sfm_checkpoint_f1_2_result.json` (top-level `in_progress`/`memory_snapshots`/`command_records` fields); absence of `sfm_checkpoint_f1_2_production_log_command4.txt` | **STARTED_BUT_OUTCOME_UNKNOWN** (see precise reconstruction below — closer to "never demonstrably began" than "began and failed") |

## Command-by-command reconstruction of the one genuine All→All attempt (F1-2, commands 3→4)

F1-2's own harness loop (`Checkpoint_F1_2_Corrected_Repeated_Warm_Use_Stability.py`, lines 1024-1295) is
structured as `for ordinal, scope_label in COMMAND_SPECS:` with, at the very top of each iteration (line
1025), a cheap, pure-Python `memory_snapshot()` call written into
`report["memory_snapshots"]["before_command_%d" % ordinal]` — **before** the operator-facing prompt is even
printed (line 1027-1031) and **before** production is `exec()`'d (line 1038, the step that triggers the
real scope-choice dialog and any native call). At the end of each iteration (lines 1289-1295), the harness
runs `gc.collect()`, takes an `after_command_N_gc_collect` snapshot, appends the full `command_record`, and
calls `write_rolling_evidence()` — an atomic, verified JSON write (`write_json_atomic`, the same primitive
used throughout this project).

The real, returned `sfm_checkpoint_f1_2_result.json` contains exactly three `command_records` (ordinals 1,
2, 3 — all `run_completed_cleanly: True`), exactly six `memory_snapshots` keys
(`before_command_1`/`after_command_1_gc_collect`/`before_command_2`/`after_command_2_gc_collect`/
`before_command_3`/`after_command_3_gc_collect`), 82 `checks` entries (the last ten all `command_3.*`, all
`pass: True`), and top-level `in_progress: True`, `overall_pass: None`. **`before_command_4` was never
written.**

Because `before_command_4` is the very first statement of the loop's 4th iteration — a pure-Python
operation with no native call, executed *before* the operator would even be prompted to choose a scope for
command 4 — its total absence means the harness's own control flow never demonstrably reached the start of
command 4's own iteration at all. This is a narrower, more precise finding than "command 4 began and then
failed": **there is no preserved evidence that command 4 ever began**, only that command 3 finished all of
its own post-processing cleanly and then, at some point between that and the next (trivial) Python
statement, all further evidence stopped. No production log for command 4 exists in any form — not even a
truncated one, unlike F1-1's own command-3 crash, which preserved 1,906 lines of production log ending
mid-target.

This does **not** license inferring a crash, a hang, or any other specific mechanism — those all remain
unproven. It also does not support the specific, narrower claim (in the currently-recorded ledger prose)
that command 4 "began... against the already-reduced headroom" — the evidence is agnostic between "command
4 began and something then stopped it before even a cheap Python statement could run" and "the whole
process/harness became unable to proceed at all immediately after command 3's own completion, before
command 4 was ever reached." Both readings are consistent with the same preserved facts.

## Decisive classification

**C. ALL → ALL WAS ATTEMPTED BUT THE SECOND-ALL OUTCOME IS NOT PRESERVED/DETERMINATE.**

The one genuine same-process All-Shots → All-Shots sequence this project ever set up for real is **F1-2's
commands 3 and 4** (F1-1 never reached an All→All pair at all — it crashed during its own *first* All-Shots
command, command 3, with command 4 never started; F1-R1 deliberately never included a second All-Shots
command by design). F1-2's command 3 (first All-Shots) **completed cleanly** — full production log, all
checks pass, `FINAL_REPORT_ENTRY` reached, ~227 MiB private growth / ~222 MiB free-VAS loss within that one
command. Command 4 (second All-Shots), the very next scheduled command in the same unrestarted process,
**has zero preserved evidence of outcome** — no completed record, no partial/crash log, no
`before_command_4` snapshot, no check entries, nothing. The rolling JSON was left permanently
`in_progress: True`.

This is precisely how far the second All progressed, stated exactly: **as far as can be shown from
preserved evidence, it did not demonstrably progress at all** — not even to its own first, trivial,
native-call-free bookkeeping statement. What disappears is everything: no production log, no memory
snapshot, no check, no exception trace, no termination marker. The only preserved fact is that this silence
begins immediately after command 3's own fully-clean completion.

## Implications for Astra's proposed final same-process All→edit→All test

**Update (2026-09-24): this test has since been run for real (`F2-R1`/`F2-R1-R3`) and the question below is
now resolved.** Result: **FAIL — LEGITIMATE SAME-PROCESS REINVOCATION IS NOT RELIABLY SUSTAINABLE.** Stage 1
(All Shots) completed cleanly; the controlled edit was correctly applied and confirmed; Stage 2 (All Shots
again, same unrestarted process) was validly reached — mode classification was correct, not a harness
artifact — and Stage 2's own real production run crashed at target 54 of 62, immediately after `PRE_NATIVE`
telemetry, with no subsequent `NATIVE_REBUILD_RETURNED` line and no further log content of any kind. Full
evidence is recorded in `LEDGER.md`'s F2-R1 row and in `F1_FINAL_DISPOSITION_REVIEW.md`'s 2026-09-24 update.
This does not reopen the F1 optimization search (still concluded/exhausted); it establishes that the
question below — whether this specific missing test was needed — is now answered, and it resolves in favor
of a product-level admission/recovery policy rather than a further diagnostic. The paragraphs immediately
below are preserved as the original, still-accurate reasoning for why the test was needed at the time it
was proposed:

Astra's proposed test (a final same-process All Shots → [edit] → All Shots confirmation) was, at the time
this audit was written, **genuinely missing, not redundant and not contradicted**:

- It is **not redundant**: no preserved run in this project's history reached a determinate outcome for a
  second consecutive All-Shots command in one unrestarted process. F1-2 attempted the closest analogue and
  left the question open with total evidentiary silence, not a resolved answer.
- It is **not contradicted**: nothing here proves a second All-Shots command necessarily fails, hangs, or
  crashes — F1-2's silence is equally consistent with a hang, a crash, an external interruption, or (least
  likely, given the harness's own next step is trivial) something else entirely. The evidence base is too
  thin to draw ANY firm conclusion about the second command's own true behavior.
- What IS established, and should inform how that test is designed: command 3's own single-All-Shots
  resource cost is large and real (~227 MiB private / ~222 MiB free-VAS / ~106 MiB largest-free-block, all
  within one command), and whatever happens next happens at or immediately after that point — so a test
  designed to observe the second All-Shots command's own outcome should capture evidence as early and as
  cheaply as possible (before the operator is even prompted, matching F1-2's own `before_command_N` design)
  and should not assume that reaching production's own native call for command 2 of the pair is guaranteed
  — the harness itself becoming unable to continue is a real, evidenced possibility worth designing around
  (e.g., writing the "test is about to attempt command 2" marker to disk *before* attempting it, so even
  total process death after that marker still narrows down where the failure occurred).

## Documentation correction made

The current `LEDGER.md` F1-2 row states: *"Command 4 (All Shots again) produced no completed record and
the final external verification was never reached -- consistent with **command 4 beginning against** the
already-reduced ~183 MB free VAS / ~75 MB largest-contiguous-block headroom command 3's own completion left
behind."*

The phrase "command 4 beginning against" asserts, as an accepted fact, that command 4 began. The primary
artifact (`sfm_checkpoint_f1_2_result.json`) does not support that specific claim — the complete absence of
even a `before_command_4` snapshot (a cheap, pre-dialog, pure-Python step that precedes any actual "start"
of command 4's own work) is equally consistent with command 4 never being reached at all. This is a
demonstrable imprecision in the existing wording, not a reversal of the FAIL/INCOMPLETE disposition itself
(which remains correct and unchanged) or of any measurement. A minimal, evidence-precision correction was
applied to `LEDGER.md` — see the diff in the commit referenced below. No measurement, classification, or
disposition status was altered; only the unsupported "began" assumption was corrected to reflect what the
primary artifact actually shows.
