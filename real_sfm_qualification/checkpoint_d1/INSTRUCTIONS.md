# Checkpoint D1-2 — Historical (Pre-Integration) All-Shots Baseline Run (corrected)

## CORRECTION NOTICE (2026-09-22)

D1-1's real historical All-Shots run itself completed cleanly and every runtime/mutation check passed
— all the runtime findings below were established and are preserved permanently in the ledger — but the
required JSON evidence artifact was written as **zero bytes** (`write_ok=False`). Root cause, found by
direct code review of the D1-1 writer (not guessed):

D1-1's writer opened `JSON_OUTPUT_PATH` directly in `"wb"` mode — which **truncates any existing file
immediately on open** — and only *then* called `json.dumps(report, indent=2, sort_keys=True)`. A bare
`except Exception: json_write_ok = False` around that whole block discarded the actual exception, so the
specific failure (whether a serialization `TypeError`, a `MemoryError` from the expensive pretty-printed
serialization of a ~9MB payload, or something else) is **not recoverable from the existing D1-1
artifacts** — the prior instrumentation destroyed the one piece of evidence that would have said why.
That information loss is itself a confirmed, code-reviewed defect, not a hypothesis, and is the first
thing this correction fixes.

A representative-scale, code-level review of every field the D1-1 report dict added beyond the
already-proven-working Checkpoint C1/C2 writer (same code, same pattern, both of which wrote comparable
or larger payloads without incident) found no structural JSON-type-safety defect — every new D1-only
field (`excluded_target_witness`, `target_set_diff`, `selection_state_evidence`, `fixture_totals`, the
in-scope note) is a plain `str`/`unicode`/`int`/`bool`/`None`, correctly JSON-serializable on its own.
The most plausible remaining explanation, consistent with the exact observed signature (silently
swallowed exception, zero-byte truncated file, zero reported runtime anomalies elsewhere) is memory
pressure during the expensive `indent=2, sort_keys=True` serialization: D1 is the first of these
checkpoints to hold a **second full independent-witness rebuild** (163 targets) in memory simultaneously
with both full 85-target PRE and POST fingerprint payloads, immediately after an All-Shots-scale native
operation touched the entire project. This cannot be confirmed without a live rerun under the corrected
instrumentation below — which is exactly why preserving the exact exception on any future failure was
Section 1's own explicit requirement.

**What changed (writer only — see "Source review" below for the exact, minimal diff):**

1. A new `write_json_atomic()` helper never truncates the final authoritative path. It serializes to a
   **temporary** path first, flushes/closes it, verifies the temp file is nonzero and independently
   reopens/reparses it, and **only then** promotes it to the real path. On any failure at any step, it
   returns the real exception's `repr()` instead of silently discarding it, and the final path is left
   completely untouched — proven, using the failed attempt against a pre-existing valid file, in the new
   offline regression below.
2. Artifact writing is now part of `OVERALL_PASS` (Section 3): the report is written once to verify
   round-trip integrity (including that the stored PRE/POST hashes **recompute correctly from the
   reparsed, round-tripped semantic data**, not merely that the file is valid JSON), then `overall_pass`
   and a new `artifact_write_verified` field are corrected based on that outcome, and a final corrective
   write publishes the accurate values. A required-evidence-write failure now makes the checkpoint FAIL
   even when the SFM mutation itself succeeded.
3. A last-resort **degraded fallback artifact** (the same report with the large fingerprint payload
   dropped, but every check/hash/count/anomaly preserved) is written if the final corrective write
   somehow still fails after an initial successful verification pass — so the authoritative output is
   never again left as a misleading zero-byte file, even in that pathological edge case.

**Nothing else changed.** Historical Normalizer invocation, fingerprint semantics, fixture/starting-state
gates, and the All-Shots operation itself are byte-identical to D1-1 — see "Source review" below for the
exact diff scope.

## Preserved D1-1 runtime findings (not overwritten — see LEDGER.md)

historical SHA correct; production Normalizer untouched; canonical Master unchanged; initial PRE hash
matched `eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0`; historical All-Shots
completed cleanly; 85 eligible targets captured PRE/POST; 78 excluded targets witnessed PRE/POST; no
target vanished/appeared/was reclassified; historical POST hash
`299cbba30634da1a4949ed7b14187b813260c533dced3d1e71149ede98c124e7`; 57 changed eligible targets, 28
unchanged; 0 excluded targets changed; zero reported runtime anomalies. D1-2 is expected to reproduce
these same values if the starting fixture is identical — but D1-2 measures them again independently; the
57/28 counts and the POST hash are **not** hardcoded as a substitute for that measurement.

## THIS CHECKPOINT MUTATES THE SCENE

Like C1, D1 **does** mutate the disposable qualification project. It invokes the exact historical,
pre-integration frozen Normalizer's own real **All Shots** behavior, unmodified.

**Do not save afterward.**

## Purpose

Establish the historical (pre-integration) All-Shots outcome as the authoritative baseline Checkpoint
D2 will later be compared against — the same role Checkpoint C1 played for Selected Shots vs C2. D1
does **not** assume every eligible target changes; it measures and reports historical truth, which
becomes D2's own expected values.

## 1. What D1 actually does (non-interactive parts)

1. Verifies the historical baseline's SHA-256: `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e`.
2. Verifies the installed production Normalizer has **not** been replaced
   (`cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`) — read-only identity check; it
   is never imported or executed by this checkpoint.
3. Verifies the canonical Master's SHA-256 (`ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`).
4. Independently re-derives the Checkpoint-B-style fixture witness fresh from the live document and
   cross-checks it against fixed structural totals: 15 shots, 163 targets, 85 eligible, 78 excluded, 22
   distinct models, 21 distinct eligible vocabulary hashes. **Unlike C1/C2, no selected-shot-specific
   check gates this run** — All-Shots scope does not depend on which shot(s) are selected. The live
   selection state is captured and recorded in the report for evidence only, never gated on.
5. Captures a structural PRE fingerprint of all 85 eligible targets (same technique C1/C2 used) and
   computes its hash. **Hard gate**: this hash must equal C1/C2's own accepted PRE hash exactly
   (`eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0`) — this proves Checkpoint C2's
   own mutation was discarded and this run starts from the same original disposable fixture state.
6. Captures a lightweight, non-mutating **structural witness** (never the full fingerprint schema) of
   all 78 independently-classified excluded targets — `shot_name`, `aset_name`, `model_backed`,
   `model_name`, `root_group_valid`, `is_duplicate_aset_ptr`, `control_count`, `fold_vocabulary_hash`,
   `category`. This is deliberately never routed through `capture_snapshot_explicit()`, which raises
   `ProbeError` for any target lacking a valid root control group — not guaranteed for non-model-backed
   excluded targets such as cameras/lights, so routing them through the same schema as the 85 eligible
   targets would risk inventing semantics or generating spurious harness anomalies.
7. **If any check above fails, the script raises and writes its report here — it never executes a byte
   of the historical baseline or mutates the scene.**

## 2. What D1 needs from you (the interactive part)

After the PRE fingerprint and excluded witness are captured and the gate passes, the script executes
the historical baseline source. This triggers the historical code's own real, completely unmodified
"choose scope" dialog.

**When that dialog appears: select "All Shots" and confirm.** Do not modify or work around this dialog
in any way — it is the real, original product behavior, and exactly what this checkpoint is measuring.

The script then waits (pumping SFM's own Qt event loop, watching for the historical run's own
completion signal — the same technique C1 used) for the real, asynchronous operation to finish, before
rebuilding the independent witness fresh, capturing the POST fingerprint/excluded witness, and writing
its report. **Do not interact with SFM while it's running** — this run covers the full project and may
take longer than the Selected-Shots runs.

## Exact project to open, and required selection state

Open the **exact same disposable qualification project used for B-2/C1/C2**. Selection state may
remain whatever it currently is — All-Shots scope must not depend on it, and the script does not gate
on it. What **is** required is that the project's *content* matches the original fixture exactly (i.e.
Checkpoint C2's mutation has been discarded by restarting SFM without saving) — the script mechanically
verifies this via the PRE-hash gate in step 5 above and will abort before touching anything if it does
not match.

## What gets reported (Section 5/6 of the governing brief)

D1 does not define PASS as "all 85 targets changed." It reports, separately:

1. `semantically_changed_target_set` / `changed_target_count` — eligible targets whose fingerprint
   actually differs PRE→POST.
2. `semantically_unchanged_target_set` / `unchanged_eligible_target_count` — eligible targets whose
   fingerprint is identical PRE→POST (legitimate no-ops, already matching the Master).
3. `excluded_target_witness` (`pre`/`post`/`changed_targets`/`changed_count`) — the 78 excluded
   targets' structural witness before and after. A change here is reported, never automatically
   labeled a regression (Section 7) — the historical product may legitimately touch some structural
   property of an excluded target as a side effect.
4. `target_set_diff` (`missing_targets_entirely`/`new_targets_entirely`/
   `reclassified_eligible_to_excluded`/`reclassified_excluded_to_eligible`) — computed by rebuilding
   the independent witness fresh after the run and comparing target-key sets against the PRE witness.
   A target moving between eligible and excluded is reported as a reclassification, not conflated with
   a target vanishing entirely.
5. `targets_considered_in_scope_note` — an honest documented limitation: the exact set of targets the
   historical All-Shots target planner iterated internally is not independently observable from outside
   the running command without new instrumentation (same class of limitation as Checkpoint C2's own
   in-process authority-lease state). PRE/POST semantic comparison is used instead, which is sufficient
   to establish D2's expected values.

## Operator instructions

1. **RESTART SFM FIRST.**
2. **DO NOT SAVE the previous experimental state; restart SFM to discard it.**
3. Open the exact same disposable qualification project.
4. Run **`Checkpoint_D1_Historical_All_Shots_Baseline`**, the same way as the earlier checkpoints.
5. **A real dialog will appear.** Select **"All Shots"** and confirm.
6. Give it generous time — this run covers the full project (163 targets total, 85 fingerprinted twice
   plus 78 structurally witnessed twice), larger than any prior checkpoint.
7. Do not touch SFM again until the console output shows the final summary and the
   "DO NOT SAVE. Restart SFM..." message.
8. Return the exact contents of **both** output files:
   - `C:\Users\Public\Documents\sfm_checkpoint_d1_historical_all_shots_result_summary.txt`
   - `C:\Users\Public\Documents\sfm_checkpoint_d1_historical_all_shots_result.json`

   Also tell me about any error dialog or console traceback beyond what's in those files.
9. **DO NOT SAVE. Restart SFM to discard the historical mutation before D2.**

## Output artifact paths

- `C:\Users\Public\Documents\sfm_checkpoint_d1_historical_all_shots_result.json` (full detail — every
  check, both eligible fingerprints, excluded witness before/after, target-set diff, anomalies)
- `C:\Users\Public\Documents\sfm_checkpoint_d1_historical_all_shots_result_summary.txt` (concise, read
  this first)

## Mechanical D1 PASS criteria (decided before execution)

`OVERALL_PASS` in the report requires **all** of:

- exact historical SHA verified;
- production Normalizer SHA still installed (unreplaced);
- canonical Master SHA unchanged;
- fixture totals match exactly (15/163/85/78/22/21) — **a mismatch here means the script already
  stopped; no mutation occurred, and none of the checks below apply**;
- the initial 85-target PRE fingerprint hash equals C1/C2's own accepted PRE hash exactly (proves C2's
  mutation was discarded and this run starts from the original fixture);
- the historical run was actually started (dialog was confirmed with All Shots, not cancelled) and
  completed within the wait timeout;
- PRE and POST capture both complete for all 85 eligible targets;
- the excluded-target structural witness is complete for all 78 pre-excluded targets (POST rows
  resolvable for every PRE key);
- no target vanishes entirely (present in the PRE witness under some category, absent from the POST
  witness under every category) — `target_set_diff.missing_targets_entirely` is empty;
- the script completes without an unhandled exception;
- **(D1-2) the JSON evidence artifact itself was written, is nonzero, reopens and reparses, contains
  every required evidence key, and its own stored PRE/POST fingerprint hashes recompute correctly from
  the reparsed semantic data** — `artifact_write_verified` must be `true`. A required-evidence-write
  failure makes `OVERALL_PASS=False` even if every runtime/mutation check above passed (this is exactly
  what happened in D1-1, preserved in the ledger as "runtime PASS / evidence artifact FAIL").

D1 does **not** require a predetermined POST hash, changed-target count, or that every eligible target
change — those are D1's own *outputs*, and become D2's expected values. New targets appearing, or a
target being reclassified between eligible and excluded as a side effect of the All-Shots run, are
reported but do not by themselves fail D1 (Section 7) — they are historical truth, not a regression
verdict, which D1 exists to measure, not to judge.

If the report shows `"gate_failure": true`, that means a pre-flight or starting-state check failed and
the script correctly stopped before touching anything — re-verify the project/installed files and
rerun, rather than treating it as a script bug.

## Source review: only the writer changed; production Normalizer / canonical Master are never overwritten

A direct line-by-line diff between the D1-1 and D1-2 script bytes shows every removed/changed line is
confined to the final "Finalize / write output" section (the naive `open(..., "wb")` blocks and the
`overall_pass` assignment, now renamed `runtime_checks_passed` and gated further by artifact
verification) — historical baseline invocation, the Clip-Editor dialog wait loop, fingerprint capture,
the excluded-witness capture, the fixture/starting-state gates, and the target-set-diff logic are
byte-identical to D1-1. `Rebuild_Control_Groups_Normalizer.py` is still never imported (only opened once,
`"rb"`, for its SHA-256 identity check); the canonical Master is still opened only `"rb"`, once;
`sfm_master_authority_productionized` is still never imported or referenced anywhere in this script.

## Offline verification already performed

Before D1-1's deployment: (1) syntax-checked under the real embedded Python 2.7.5, PASS; (2)
`real_sfm_qualification/checkpoint_d1/test_d1_witness_and_gate_regression.py` (SHA-pin updated for D1-2,
line ranges unchanged since the correction was appended after them) extracts `dumps_sorted`,
`target_key`, and `excluded_witness_row` verbatim and proves the excluded-target structural witness,
PRE/POST excluded-witness comparison, and target-set-diff logic all behave correctly — **16/16 PASS**,
reconfirmed against the corrected D1-2 script.

Before this correction's (D1-2) deployment, additionally: (3) syntax-checked under the real embedded
Python 2.7.5, PASS; (4) a new offline regression,
`real_sfm_qualification/checkpoint_d1/test_d1_artifact_writer_regression.py`, extracts the deployed
script's own `stable_hash`, `dumps_sorted`, `write_json_atomic`, `write_text_atomic`,
`REQUIRED_EVIDENCE_KEYS`, and `verify_artifact_evidence` verbatim (SHA-256 pinned) and proves, using
**the real 85 PRE + 85 POST target fingerprints from the already-accepted Checkpoint C1-2 artifact** (not
synthetic toy data) plus a representative 78-row excluded-target witness: a complete, D1-shaped result
(full fingerprints + excluded witness) serializes; it reopens/reparses correctly; the stored PRE/POST
hashes recompute correctly from the round-tripped data; a deliberately unserializable payload (a raw
Python `set`) is correctly rejected with a real, non-swallowed error message; critically, an **existing
valid file at the same final path is left completely byte-identical** by the failed write attempt (the
exact defect class D1-1 hit, now proven fixed) with no leftover `.tmp` file; `write_text_atomic` exhibits
the same non-truncating behavior on a write failure; and the exact boolean composition the real script
uses for `OVERALL_PASS` correctly evaluates to `False` whenever the artifact write fails, even when every
runtime check passed — **25/25 PASS under the real embedded Python 2.7.5**. Not yet run against real SFM.

## Identities this checkpoint is pinned against

- Historical baseline SHA-256: `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e`
- Installed production Normalizer SHA-256 (must remain unreplaced):
  `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Required initial PRE fingerprint hash (C1/C2's own accepted value):
  `eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0`
- D1-2 (corrected) script SHA-256: `d8af1437c0090c62c29e2fcc3797c78c5e30f4d464703df83c2d7d769a1cf9a2`
  (D1-1's superseded script SHA-256, preserved for the record: `d3137e38c637898649fab3b26d3cdf0c1a742cface2ece991841affce15856ba`)
