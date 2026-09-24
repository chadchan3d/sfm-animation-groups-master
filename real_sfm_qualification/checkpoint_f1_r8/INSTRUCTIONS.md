# Checkpoint F1-R8 — CElementTreeTraversal Native Semantic Characterization

## Purpose

F1-R7's static audit classified the real, installed native `CElementTreeTraversal` class as a
`MEASUREMENT_CANDIDATE`, blocked from `EXACT_CANDIDATE` status by two questions that could not be
resolved from any binding stub, header, or source evidence present in this SFM install:

- **A. pAttrName semantics** — does `CElementTreeTraversal(root, pAttrName)` follow only the one named
  attribute, or can it be made to follow every element-reference attribute (matching legacy
  `reachable()`'s own whole-attribute-list walk)?
- **B. visitation semantics** — does it deduplicate shared/DAG-reachable elements across the whole
  traversal (matching legacy's permanent handle-keyed `seen` set), or only detect cycles along the
  current traversal path?

This checkpoint resolves ONLY those two questions, empirically, against a small, detached, native DME
graph. **It is a characterization checkpoint, not an optimization benchmark** — it does not measure
command-scale resource savings, does not redirect production discovery, and does not authorize the
F1-R7 optimization prototype. That remains gated behind this checkpoint's own result.

**This checkpoint does not modify production.** It never attaches created elements to the session, a
shot, an animation set, or the production scene hierarchy, and never calls `SaveToFile`.

## Detached graph technique

`vs.g_pDataModel.FindOrCreateFileId(name)` registers a new, purely in-memory file-ID namespace tag — no
disk I/O occurs unless `SaveToFile` is later called against that ID, which this script never does.
`vs.CreateElement(elemType, elemName, fileid)` (confirmed real via a first-party SFM script,
`platform/scripts/sfm/dag/exact/count1/create_lights.py`) creates elements tagged with that scratch
file ID. Nothing in this script ever assigns a scratch element as the value of any attribute belonging
to an element outside the scratch graph, so nothing created here ever becomes reachable from the open
document's own root. Every created element is destroyed (`IDataModel.DestroyElement`) and the scratch
file ID removed (`IDataModel.RemoveFileId`) in a `finally` block before the script finishes, regardless
of outcome.

If the required creation APIs cannot be resolved, or a minimal creation probe fails, the script reports
`detached_graph_available: False` with an explicit reason and stops the native-characterization work
there — it does not invent an alternative method, per instruction.

## Sequence

1. **RESTART SFM FIRST.**
2. **Do not save any prior experimental state.**
3. Open **only** `E:\SourceFilmmaker Sessions\F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx` — never the original
   `testscripts.dmx`. The script structurally refuses to proceed otherwise.
4. Run `Checkpoint_F1_R8_CElementTreeTraversal_Native_Characterization`.
5. Choose any scope in production's own real scope-choice dialog (this checkpoint neutralizes the
   instance immediately and never advances the real pipeline; the scope choice has no effect on this
   checkpoint's own work). No other user interaction is required — the detached native graph
   characterization runs automatically.
6. Wait for completion.
7. Return the output files (see below).
8. **DO NOT SAVE.**
9. **Fully restart SFM afterward.**

## Output files to return

- `C:\Users\Public\Documents\sfm_checkpoint_f1_r8_result.json`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r8_result_summary.txt`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r8_native_traversal_log.txt`

## What this run does NOT do

- Does not call native Rebuild, activate a shot, or write anything to the scene — confirmed by static
  source check.
- Does not attach any created element to the session, a shot, an animation set, or the scene hierarchy.
- Does not save the scene.
- Does not run 62 targets, native Rebuild, or the production contextual pipeline — the optional
  real-scene check (only attempted if the detached graph already establishes
  `EXACT_CANDIDATE_SUPPORTED`) touches exactly one shot's own scene, read-only, once.
- Does not measure resource/memory deltas — this is a semantics-only characterization.
- Does not invent wildcard attribute-name strings — every tested `pAttrName` value is explicitly
  justified in the script's own `TESTED_ATTR_NAMES_GRAPH1`/`TESTED_ATTR_NAMES_DAG_AND_CYCLE` constants.

## Three synthetic graphs

1. **Multi-attribute forward references**: `ROOT --attr_A--> A --attr_A--> C`;
   `ROOT --attr_B--> B --attr_B--> D`; `A --attr_list(array)--> [E, F]`. Tested `pAttrName` values:
   `"attr_A"`, `"attr_B"`, `"attr_list"` (the three real, present attribute names) and `""` (the natural
   "absence of a name" probe, a genuine safe non-NULL C-string) — four legitimate, justified probes, no
   invented sentinels.

   **A Python-`None` (NULL `const char*`) probe is deliberately excluded.** SWIG commonly maps Python
   `None` to a NULL pointer for `char const *` parameters, but nothing in the installed binding stub, any
   header, or any other evidence in this SFM install establishes that `CElementTreeTraversal`'s own C++
   implementation safely handles a NULL `pAttrName` (as opposed to, say, unconditionally dereferencing it
   and crashing the process). `""` is a genuine, safe, non-NULL C-string value — a different safety
   question from NULL, and the two are **not** assumed equivalent anywhere in this checkpoint. NULL
   `pAttrName` semantics are recorded as `NOT_TESTED_UNKNOWN` (`report["null_pattrname_probe_status"]`)
   rather than tested. If the remaining named/empty-string probes fail to establish complete-forward-
   traversal and global-dedup semantics, NULL may be revisited only after its own explicit safety review,
   and only if actually necessary to qualify the API — never silently reintroduced.
2. **Shared-reference DAG**: `ROOT --ref--> [A, B]`; `A --ref--> [C]`; `B --ref--> [C]` (C shared).
   Tested `pAttrName`: `"ref"` (the one real attribute name present).
3. **Cycle**: `ROOT --ref--> [A]`; `A --ref--> [B]`; `B --ref--> [ROOT]`. Tested `pAttrName`: `"ref"`.

A strict bounded watchdog (`MAX_TRAVERSAL_STEPS = 2000`) guards every native traversal call so a
pathological result cannot hang SFM; if triggered, that probe is marked `watchdog_triggered: True` and
the cycle graph's own dedup classification becomes `NO_SAFE_DEDUP`.

## Legacy control

Legacy's own `reachable()` (extracted verbatim from the exec()'d, SHA-256-pinned production namespace,
never reimplemented) is run over the same three detached graph roots, recording ordered/unique handle
sequences, duplicate counts, and exception behavior — the reference this checkpoint compares native
traversal against.

## Mechanical disposition

- **`EXACT_CANDIDATE_SUPPORTED`** only if BOTH: (1) at least one single tested `pAttrName` probe's own
  traversal alone reaches legacy's full unique-handle set on the multi-attribute graph (the decisive
  single-call coverage question), AND (2) the DAG/cycle graphs classify as `GLOBAL_DEDUP_EQUIVALENT`.
- **`SEMANTICALLY_INSUFFICIENT`** if either condition fails.
- **`INCONCLUSIVE`** if the detached graph cannot be safely built, or either classification cannot be
  computed.

This checkpoint does not automatically authorize production or prototype integration even if
`EXACT_CANDIDATE_SUPPORTED` is reached — the evidence returns to independent review before the F1-R7
prototype is authorized.

## Offline verification performed before deployment

`test_f1_r8_diagnostic_regression.py` (SHA-256
`f3f80f5a5171c906b1acd788a7f43188ef99089fa1d6f7713f0d2697b9c271da`) extracts the script's own pure-Python
harness functions verbatim (by source line range) and exercises them against synthetic
`FakeElement`/`FakeAttribute` objects and deliberately-scripted fake traversal classes — **77/77 PASS**,
covering: graph-accounting (`build_graph_*` wiring correctness), the legacy control wrapper
(`run_legacy_reachable`, including its own exception path), the bounded watchdog (an intentionally
infinite fake traversal is caught at `max_steps` without hanging), the dual `GetElement()`/`Next()`
step-recording logic (including the terminal-`None`-filtering edge case), the four result-classification
functions (`classify_dag_cycle_dedup`, `graph1_single_call_coverage_ok`,
`compute_final_classification`) across every branch including every failure/inconclusive path, that
exactly the four justified `pAttrName` values are present with no NULL probe, and static safety checks
(no `SaveToFile`, no native Rebuild, no shot activation, neutralization ordering, scratch cleanup in a
`finally` block, no 62-target/full-shot-loop in the optional real-scene check, the NULL-`pAttrName`
unknown-status record present and explicitly not inferred equivalent to `""`). **No
fake traversal class result is treated as native qualification evidence** — these tests validate the
harness only, exactly as required; real `CElementTreeTraversal` semantics can only be observed by
actually running this checkpoint inside real SFM. All under the real embedded Python 2.7.5. Not yet run
against real SFM.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256: `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Expected normalized-copy fixture filename: `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx`
- F1-R8 real-SFM script SHA-256: `863213058e66103f4a03d8f95d4e07d702c0274f6f2adb9d0be94cbbac962551`
- F1-R8 offline regression test SHA-256: `f3f80f5a5171c906b1acd788a7f43188ef99089fa1d6f7713f0d2697b9c271da`

## Explicit non-authorization

This checkpoint does not patch production, does not touch authority/broker code, does not build the
F1-R7 optimization prototype, and does not close F. Even an `EXACT_CANDIDATE_SUPPORTED` result returns
to independent review before the next step is authorized.
