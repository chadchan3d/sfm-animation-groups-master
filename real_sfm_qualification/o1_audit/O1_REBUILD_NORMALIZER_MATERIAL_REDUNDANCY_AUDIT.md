# O1 — Rebuild + Normalizer Material Redundancy & Resource Audit

**Status: STATIC MATERIAL-REDUNDANCY AUDIT — COMPLETE / AWAITING INDEPENDENT REVIEW.**
This is analysis only. No production code, integration code, or lifecycle behavior has been
changed. Nothing here is approved, accepted, or authorized for implementation.

## Governing rule

> Tangible savings, demonstrated redundancy, zero functional compromise.

This audit excludes millisecond-level loop tuning, tiny allocation reductions, cosmetic refactors,
reduced validation, narrower model support, stale caching, skipped freshness checks, weakened
isolation, reduced failure safety, and reduced Normalizer/Rebuild functionality. A candidate is
included only if it plausibly produces tangible runtime or memory/VAS savings at command scale.
Functionality and semantic correctness are frozen requirements throughout.

## Why this audit exists

Checkpoint F1-2 (real-SFM qualification) confirmed production's own **All-Shots command 3** grows
~227.32 MiB private / loses ~222.44 MiB free VAS / ~105.88 MiB largest-contiguous-block **within its
own single run** (its own `CP0_COMMAND_START` vs its own `FINAL_REPORT_ENTRY`), after the qualification
harness's own separately-identified retention (F1-R1, Python/CRT allocator high-water retention from
the harness's own whole-85-target capture) had already been eliminated. This is production-internal.
Checkpoint F1-R2 (a two-phase scene-resident-vs-per-run-native-retention diagnostic) was built and is
parked, pending this static audit, per explicit instruction.

## Method

Direct source reading of the accepted production Normalizer
(`Rebuild_Control_Groups_Normalizer.py`, SHA-256
`cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`), focused on the per-target
transaction pipeline (`run_target_transaction()`, the `self.work` snapshot built by `snapshot_work()`,
and every stage between command setup and the next target). Four independent trace passes were
performed and completed (native Rebuild↔Normalizer overlap and warm-path behavior; `self.work` consumer
tracing; repeated discovery/planning computation across 5 sub-categories; native/DME/Qt/transaction
lifetime beyond `self.work`), each citing exact file:line evidence, then synthesized and cross-checked
against each other and against the earlier `F1-2_PRODUCTION_INTERNAL_STATIC_AUDIT.md` finding (which
this audit **corrects** in one material respect — see Candidate 1).

## Per-target pipeline overview (source-grounded)

One call to `run_target_transaction()` per eligible target, driven from `self.work` (built once via
`snapshot_work()`, never shrunk during the command):

1. **PRE capture** (~11262-11272): `discover_rig_context()` + `capture_snapshot_explicit()` — a full
   recursive control-group-tree walk (`capture_tree()`, line 1200) of the target's entire rig.
2. **Native Rebuild** (~11464-11468): `self.rebuild(ctypes.c_void_p(aset_ptr))` — a fixed, command-scoped
   `ctypes.WINFUNCTYPE(None, ...)` callback resolved once per command (line 9328), fire-and-forget, no
   return value retained.
3. **POST capture** (~11482-11492): `discover_rig_context()` + `capture_snapshot_explicit()` again — a
   **second**, structurally identical full tree walk, immediately after Rebuild, diffed against PRE
   purely as a validation gate.
4. **Classification/planning** (~11608-11891): `preflight_reconciliation_plan()` then, **unconditionally**
   (see Candidate 3), `derive_generic_uniformity_plan()`.
5. **Composer/reconciliation** (~11897-11976): `production_generic_composer()` — the actual
   parenting/membership/ordering mutation. Its own log line reports `already_correct_count` — proving
   the composer *internally* computes a fresh-vs-warm distinction, but only after the full pipeline
   already ran.
6. **Target isolation, post-composer** (~12100-12167): `isolation_fingerprint()` (a lighter walk, not
   `capture_tree()`), then `semantic_target_fingerprint()` at line 12129 — which internally calls
   `discover_rig_context()` + `capture_snapshot_explicit()` **a third time**, with source comments
   (12123-12151) explicitly stating this capture's own rich payload has *"no downstream consumer"* and
   is `del`-eted immediately (`"the sole CONTEXTUALIZER resource ablation"`) — its only purpose is
   asserting the capture *succeeded*, not using its content.

## Candidate shortlist (≤5, material only)

### Candidate 1 — `self.work`'s stored `aset` reference is provably dead data; `game_model` is never stored at all

**Observed redundancy/lifetime.** The earlier `F1-2_PRODUCTION_INTERNAL_STATIC_AUDIT.md` stated
`self.work` holds live `aset`/`game_model` DME references for every eligible target for the whole
command, "architecturally necessary." A deeper consumer trace **corrects** this:
- `game_model` is **never stored in `self.work` at all** — `snapshot_work()`'s per-shot `rows`/`gm_index`
  locals (holding `game_model`, lines 9902-9976) go out of scope every shot iteration; only a trimmed
  dict `{"anim_set": row["aset"], "name": ..., "ptr": ...}` is appended into what becomes `self.work`
  (lines 10173-10196).
- The stored `"anim_set"` (`aset`) field is **written once (line 10174) and never read from `self.work`**.
  Its only two touches elsewhere are: (a) `contextualizer_resolve_resume_target()` (called for *every*
  target, not just genuine resumes, lines 12488-12494) **overwrites** it with a freshly re-resolved
  `aset` found by matching `(ptr, name)` against the live scene (lines 12364-12366) — never reading the
  stored value; (b) `run_target_transaction()` (line 11212-11214) reads `target["anim_set"]`, but is
  always invoked with the already-overwritten fresh value (line 12514-12517). Exhaustive grep found only
  these 3 occurrences of `"anim_set"` in the ~14,000-line file.
- `game_model` downstream is likewise always re-fetched fresh via `self.get_game_model(aset)` on the
  fresh `aset` (line 11235) — never read from any stored `self.work` field.

**Why material.** At peak (85 eligible targets in an All-Shots command), this means up to 85 live native
`aset` references are held in `self.work` for the whole command's duration, apparently without any code
path ever consuming the stored reference — every consumer re-resolves fresh via cheap `(ptr, name)`
matching instead, specifically because the per-target pipeline is Qt-deferred
(`QTimer.singleShot`, line ~12556) and defensively re-verifies the world hasn't changed since the last
target completed. A live native DME element reference is not free to hold — whatever underlying native
memory it keeps reachable stays committed for the whole command, for no discovered functional benefit.

**Expected impact.** Medium. This is a genuine, well-evidenced structural redundancy, but its
*measured* memory contribution is unknown — 85 native pointer-sized Python wrapper objects themselves
are trivial; the open question is whether holding the underlying **native DME element** reachable (vs.
letting it become unreachable, if nothing else holds it) has any measurable effect on native/CRT memory
retention. This audit cannot resolve that without runtime measurement.

**Correctness dependency.** The fresh-reresolution pattern (`contextualizer_resolve_resume_target()`)
exists specifically to defend against exactly this kind of staleness across the Qt-deferred gap between
targets — removing the stored `aset` field would not, on this trace, remove any functionality, since
nothing observed consumes it. One residual uncertainty flagged by the trace: whether any
exception/error-path logging elsewhere reads `target["anim_set"]` outside the two call sites traced;
grep found no further occurrences, but this was not exhaustively proven across every exception branch.

**What proof would be required before changing it.** (1) A full, unambiguous confirmation that no code
path — including error/exception/logging paths — ever reads the stored `anim_set` value before it is
overwritten. (2) A runtime measurement (e.g. an instrumented dry run comparing peak/retained native
handle counts or process memory with `self.work` storing only `(ptr, name)` tuples vs. the current live
`aset` reference) to confirm this candidate actually contributes measurably to the ~227 MiB figure,
since the static trace cannot quantify native-side memory effects.

**Recommended next action.** **Measure.** This is the single highest-confidence structural finding in
this audit and the most promising candidate for the scene-resident-vs-per-run-retention question, but
its magnitude is unproven — do not change production before a targeted runtime measurement (not
necessarily full F1-R2; a smaller instrumented probe may suffice) confirms both the "unused" claim
holistically and the actual memory effect of holding vs. not holding the reference.

### Candidate 2 — 3-5 full semantic tree-walk captures per target; at least two are source/structurally redundant

**Observed redundancy/lifetime.** Every eligible target triggers `capture_snapshot_explicit()` /
`capture_tree()` (the full recursive rig/control-group walk) **three to five separate times**,
unconditionally:
1. **PRE** (line ~11263-11272, labeled `"PRE"`) — before native Rebuild.
2. **POST-native** (line ~11482-11492, labeled `"NATIVE_POST"`) — immediately after
   `self.rebuild()` (line 11464).
3. **Composer's own internal "before" capture** (inside `production_generic_composer()`, line
   7175-7185, labeled `"PRODUCTION_GENERIC_COMPOSER_PRE"`) — **despite the composer already receiving
   `post` as a parameter** (its own signature, line 7162-7170, includes `post`). Everything between the
   outer POST capture (line 11487) and the composer call (line 11897) — `contextualizer_validate_master_index_subset()`,
   `preflight_reconciliation_plan()`, `derive_generic_uniformity_plan()`, extensive logging — is
   **read-only**; no DME mutation occurs in between. This capture appears to recapture state
   functionally equivalent to the `post` value already in hand.
4. **Composer's own "after" capture** (line 7524-7534, labeled `"PRODUCTION_GENERIC_COMPOSER_POST"`) —
   self-verification of the composer's own destination application; this one has an actual purpose
   (confirming composer's own writes landed correctly) and is not flagged as redundant.
5. **The "terminal" capture** inside `semantic_target_fingerprint()` (called once per target at line
   12129). Production's own source comment (lines 12123-12128) is decisive: *"execute the exact same
   fresh terminal semantic capture, but do not retain its rich nested payload after successful
   construction. The prior rich dictionary values had no downstream consumer; final accounting consumed
   only one successful capture per terminal target."* The result (`semantic_now`) is checked only for
   `is not None` (line 12134) then `del`-eted at line 12151 — a full heavyweight rig-tree walk performed
   solely as a success/failure signal.

**Why material.** 3-5 full recursive tree walks per target, ×85 targets in an All-Shots command, is the
single largest repeated-computation candidate found in this audit. Two of the five (capture 3 and
capture 5) are structurally/source-documented as redundant: capture 3 appears to recapture data already
available via the `post` parameter with no intervening mutation; capture 5 is explicitly acknowledged in
production's own source comment as producing a payload with no downstream consumer. Each walk both
spends CPU time and transiently materializes a full nested-dict object graph per target — exactly the
shape this campaign's own offline test (`checkpoint_f1_r1/test_allocator_highwater_retention.py`) proved
leaves a persistent allocator floor even after `del()`/scope-exit, under the real embedded Python 2.7.5
this production code also runs under.

**Expected impact.** High. This is the most structurally certain, partly source-documented redundant
computation found, executed at full target-count scale (up to 85× per command, ×3-5 per target) with a
materialized object graph shape already proven (in a different context, same interpreter/allocator) to
leave retained allocator footprint behind.

**Correctness dependency.** Capture 5's *log-evidenced success* (not its content) is treated as a
required terminal isolation proof — removing it outright would remove that specific assurance unless an
equivalent, cheaper success signal replaces it (the source comment already says its content is unused,
suggesting the POST or composer-after capture already covers the substance). Capture 3's relationship to
the already-available `post` parameter needs confirmation that the composer does not rely on some subtle
difference between "outer POST, before classification/planning ran" and "composer's own POST, right
before it mutates" — even though no DME mutation was found between them in this trace.

**What proof would be required before changing it.** (1) Confirmation that composer's own "before"
capture (3) is byte-for-byte/structurally equivalent to the outer `post` value it already receives, for
a representative range of targets — if so, it could be passed through rather than recomputed. (2)
Confirmation that eliminating capture 5 (or replacing it with a cheap existence/identity check against
already-captured data) does not remove any semantic guarantee downstream stages rely on. (3) A runtime
measurement of one `capture_tree()` walk's actual peak/retained memory and time cost at representative
target sizes (Fox: 136 controls, Mia: 174 controls, and the full 85-target distribution), to size the
potential saving.

**Recommended next action.** **Candidate for redesign, pending measurement.** This is the strongest,
best-evidenced candidate in this audit — production's own source structure and comments support it — but
no change should be made before confirming capture 3's data-equivalence to the already-available `post`
parameter and measuring one capture's actual cost.

### Candidate 3 — Full classification/composer pipeline runs unconditionally on already-normalized targets

**Observed redundancy/lifetime.** Explicit, commented proof at lines 11700-11711: *"A supported active
rig still enters the generic presentation planner even when classifier repair rows are empty... presentation
policy independent of whether rig-owned drift was detected."* Even when classification (~11615-11670)
finds **zero** rows needing repair, `derive_generic_uniformity_plan()` and `production_generic_composer()`
still run in full — identical cost to a fresh target. No pipeline-level short-circuit exists anywhere in
the per-target flow; grep for `already`/`no_change`/`unchanged`/`skip`/`identical`/`matches_desired`
conditionals gating stage *execution* (not just an outcome label) found none. The composer's own
`already_correct_count` is computed only *after* the full classify→plan→compose pipeline already ran.

**Why material.** This directly answers the "already-normalized warm path" question the campaign has
been building toward since F1-2: an idempotent re-run (e.g. Selected #2, or a hypothetical All Shots
re-run on an already-normalized target) pays the full classification/planning/composer cost even though
the eventual semantic result is unchanged. Combined with Candidate 2 (three captures every time,
regardless of outcome), this means the warm path is **not materially cheaper** than the fresh path
anywhere in the traced pipeline except at the native Rebuild call itself (whose own internal warm-path
cost is outside this audit's visibility).

**Expected impact.** Medium-High. This doesn't by itself explain command 3's ~227 MiB (command 3 was a
*fresh*-target run for 83 of 85 targets, so the "already-normalized" cost wasn't the dominant factor
there) — its material value is for **repeated-use** scenarios (Selected #2's healthy small footprint in
F1-2 is consistent with this: even though the full pipeline ran, the actual captured/composed data per
target is small for only 2 targets). For a hypothetical repeated All-Shots run (F1-1/F1-2 command 4,
which never completed) or future workflows that re-run All Shots on an already-normalized project, this
candidate predicts the SAME full-cost pipeline runs again with the same per-target capture/allocator
cost as Candidate 2, regardless of the target already being correct.

**Correctness dependency.** The in-source comment explains *why* this is currently unconditional:
"presentation policy" (Finger/Carpal/Toe translation, helper accessibility, metadata, Master ordering)
is treated as independent of drift detection — i.e., the current design's philosophy is that
"already normalized" is not a safe signal to skip planning, because the *desired* state itself could
have been redefined (e.g., a Master update) even if the target's own prior state was already compliant
with an older desired state. Any change here must preserve that guarantee: a warm-path skip must only
apply when the target is ALREADY correct relative to the CURRENT desired state, not merely "was already
processed once."

**What proof would be required before changing it.** (1) Confirmation that the classification stage
(~11615-11670) itself already fully and correctly determines drift relative to the current Master state
(not stale/cached) before the composer runs — if so, a genuinely safe short-circuit is theoretically
possible when classification finds zero rows needing repair AND the composer's own historical
`already_correct_count` signal could be hoisted earlier. (2) Runtime measurement of classification's own
cost in isolation (its cost is unavoidable regardless, since it's what DETECTS "already correct") vs. the
composer/uniformity-plan stages' cost, to quantify what a skip would actually save.

**Recommended next action.** **Measure**, specifically the relative cost of classification alone vs.
composer/uniformity-plan given a zero-repair-rows outcome, before considering any redesign — the
correctness dependency here (presentation-policy independence from drift detection) is real and must be
preserved, not merely a validation weakening to bypass.

Three material candidates were identified from this audit — fewer than the maximum of 5, by design:
every other traced area (model/header discovery, composer/destination planning as a single call site,
low-level traversal primitives, Qt callbacks, transaction/undo, the small per-target accounting dicts,
and whole-session isolation digests) was either confirmed not redundant or found to compose entirely
within Candidate 2 rather than being a distinct root cause. See REJECTED AS IMMATERIAL below.

## REJECTED AS IMMATERIAL

- **Native Rebuild call itself** (`self.rebuild(ctypes.c_void_p(aset_ptr))`, line 11464): a fixed-size,
  command-scoped `ctypes.WINFUNCTYPE` callback resolved once per command (line 9328), fire-and-forget,
  no return value retained. Nothing here scales with target count beyond the one pointer-sized call
  itself. Rejected.
- **Qt deferred-callback pattern** (`QTimer.singleShot`, 3 call sites total: lines 12556, 12646, 12758):
  implements a bounded, self-cleaning sequential state-machine advance (one target/shot hands off to the
  next via a single-shot call, fired and discarded by Qt immediately). No evidence of accumulation
  scaling with target count. Rejected.
- **Per-target transaction/undo open-close** (lines ~11396-12097): cleanly scoped open/close pair per
  target, not held open across the command. Rejected.
- **`self.production_terminal_results` / `self.production_mixed_direct_by_target`**: confirmed small
  per-target payloads (a status string/enum; a short list of path strings, only when non-empty) — dicts
  that scale with target count but at negligible per-entry size, several orders of magnitude below the
  ~227 MiB figure. Rejected as immaterial on their own; would only be worth revisiting if they somehow
  composed with a much larger candidate, which no evidence here supports.
- **`self.session_expected` / whole-session isolation accounting**: confirmed to store only compact
  digests (`isolation_fingerprint_digest()` output), never live objects or raw payloads — explicitly
  by design, per the in-source comment at line 12149-12150 ("the sole CONTEXTUALIZER resource
  ablation"). Rejected — this is already the lean pattern Candidate 2 should ideally follow more broadly.
- **`self.gate_mdl_cache`**: bounded by distinct model count (22 in the qualification fixture), each
  entry a small parsed `.mdl` header (via `_gate_read_mdl_header()`, which reads only a header, not full
  mesh/vertex data). Rejected.
- **Model translation / header discovery** (`_gate_consensus_header`/`_gate_loose_candidates`/
  `_gate_read_mdl_header`): confirmed computed exactly once per target, inside `snapshot_work()`'s gate
  pass (line 9929-9934), cached via `gate_mdl_cache`. No other call sites found anywhere in the file.
  Not redundant. Rejected.
- **`production_generic_composer` / destination-planning invocation count**: exactly one call site
  (line 11897) — not independently duplicated across targets or within one target's own turn, beyond
  the internal capture redundancy already captured under Candidate 2. Rejected as a separate candidate.
- **Low-level tree-traversal primitives** (`children()`, `direct_controls()`, `_gate_nonroot_transform_names`):
  each has few call sites and is not independently redundant; their repeated cost is entirely a
  consequence of `capture_tree()` itself being invoked 3-5×/target (Candidate 2), not a distinct root
  cause. Rejected as a separate candidate — already covered by Candidate 2.
- **Master index subset/conflict validation** (`contextualizer_validate_master_index_subset()`, called
  at line 9993 during the gate pass and again at line 11601 during the per-target turn): two call sites
  exist, but with **different inputs** — the gate-pass call validates `wanted_folds` derived from
  snapshot-time transform names, while the per-target call validates folds derived from
  `post["control_names_in_animation_set_order"]` (post-Rebuild names, which can legitimately differ from
  pre-Rebuild names). This is plausibly NOT redundant — it may be validating genuinely different fold
  sets at two different points in the pipeline for a good reason (pre-Rebuild eligibility vs.
  post-Rebuild actual state). Ambiguous from static reading alone; rejected as a material candidate for
  now given the plausible legitimate difference in inputs, but flagged here (not silently dropped) in
  case a future runtime trace of the actual fold sets at both call sites shows them to be identical in
  practice for most/all targets.

## Fresh vs. warm execution comparison

| Stage | Fresh target: executes? | Fresh: materially allocates? | Fresh: changes semantic state? | Warm target: executes? | Warm: materially allocates? | Warm: changes semantic state? | Warm: appears redundant? | Proof level |
|---|---|---|---|---|---|---|---|---|
| PRE capture (`capture_tree`) | Yes | Yes (full rig tree) | No (read-only) | Yes | Yes (same cost) | No | Yes — same cost regardless of outcome | Source-proven |
| Native Rebuild | Yes | Native-side only (opaque to this audit) | Yes (on fresh) | Yes | Native-side only | Presumably no-op on already-correct state (not verifiable from this audit's visibility) | Unknown | Runtime measurement needed |
| POST capture (`capture_tree`) | Yes | Yes (full rig tree) | No (read-only) | Yes | Yes (same cost) | No | Yes — same cost regardless of outcome | Source-proven |
| Classification | Yes | Moderate (diff computation) | No (read-only) | Yes | Moderate (same cost) | No | Partially — this stage is what DETECTS "already correct," so its cost is not itself removable | Source-proven |
| Uniformity plan + composer (incl. its own internal before/after `capture_tree` pair) | Yes | Yes (plan/composer structures + 2 more full tree walks) | Yes (on fresh) | Yes (unconditionally, per lines 11700-11711) | Yes (same cost) | No (composer's own `already_correct_count` can be 0) | Yes — explicitly documented as unconditional; composer's own "before" capture also appears to recapture the already-available `post` value | Source-proven |
| Target isolation / terminal capture (5th `capture_tree`, via `semantic_target_fingerprint`) | Yes | Yes (full rig tree, `del`-eted immediately) | No (content unused per source comment) | Yes | Yes (same cost) | No | Yes — source-documented as content-redundant on every run, fresh or warm | Source-proven |
| `self.work` live `aset` retention | N/A (command-scoped, not per-target-outcome) | Native reference held, not re-materialized | N/A | N/A | Native reference held | N/A | Possibly — appears unused by any consumer (Candidate 1) | Source-proven (usage); runtime measurement needed (memory effect) |

## Scene-resident vs. process-retained framing for the confirmed ~227 MiB / ~222 MiB figure

Per instruction, this section frames candidate explanations only — it does not claim attribution static
evidence cannot prove. F1-R2 (parked) remains the intended runtime-proof mechanism if this distinction
still needs empirical resolution after review.

| Candidate mechanism | Scene-resident (baked into saved scene) | Process-only retention | Assessment |
|---|---|---|---|
| Native Rebuild's own structural changes to the DME scene (new/restructured control groups, attributes) | Plausible — this is exactly what "the scene got more complex" would look like | N/A | **Likely scene-resident** — this is Rebuild's actual job; some growth here is expected and legitimate |
| `self.work`'s retained live `aset` references (Candidate 1) | No — these are Python-side wrapper/reference objects, not scene content | Plausible — holding a native element reachable for the whole command, if otherwise unreferenced, could affect what the native layer considers "in use" | **Likely process-only retention**, pending measurement |
| The 3-5 per-target `capture_tree()` walks' own Python object graphs (Candidate 2) | No — these are ephemeral analysis structures (dicts/lists of strings), explicitly `del`-eted or scope-exited, never written back to the DME scene | Plausible — matches the allocator-high-water-retention mechanism F1-R1's own offline test proved for this exact interpreter | **Likely process-only retention** |
| Composer/reconciliation's own actual mutations (parenting, group membership, ordering) applied to the live DME scene | Yes — by definition, this changes the scene itself | N/A | **Likely scene-resident** |
| Native/CRT allocator behavior of the Rebuild call itself (opaque native code) | Ambiguous — could be either, native internals not visible to this audit | Ambiguous | **Ambiguous — cannot assess from static source reading** |

## Summary

Three material candidates identified, none approved for change:

1. `self.work`'s apparently-unused live `aset` reference retention, up to 85 simultaneously in an
   All-Shots command — corrects the earlier `F1-2_PRODUCTION_INTERNAL_STATIC_AUDIT.md`'s assumption of
   architectural necessity. Highest structural confidence; memory impact unmeasured.
2. 3-5 full `capture_tree()` semantic walks per target, at least two (composer's own internal "before"
   capture, and the terminal fingerprint capture) structurally/source-documented as redundant. Highest
   overall expected impact; the strongest, best-evidenced candidate in this audit.
3. The full classification/planning/composer pipeline runs unconditionally regardless of whether a
   target is already normalized — explicitly documented in-source as intentional (presentation policy
   independent of drift detection), so any change here carries a real, explained correctness dependency,
   not merely unexploited opportunity.

One ambiguous, lower-confidence observation (possible duplicate Master-index-subset validation with
different inputs at two call sites) is recorded under REJECTED AS IMMATERIAL rather than promoted to a
candidate, given the plausible legitimate reason for the two calls to differ.

All three candidates require runtime measurement before any change is considered, per the
correctness-dependency and proof-required sections above — this audit establishes *where* to look and
*why* each candidate might matter, not that any of them should be changed. No production, integration,
or lifecycle code has been modified. This document is submitted for independent review (Astra) before
any further action.
