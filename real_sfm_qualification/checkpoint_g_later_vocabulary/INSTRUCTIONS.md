# Checkpoint G — Later/Different Vocabulary — Instructions

**Prepared 2026-09-25. Corrected 2026-09-25 (independent review, 5 blockers). NOT yet run against real
SFM. Second independent review required before execution.**

## Correction round 2 (2026-09-25) — five blockers fixed before any real-SFM run

1. **Real production PASS required.** `verify_run_log_content()` previously accepted `FINAL_REPORT_ENTRY`
   as equivalent to success. `final_report()` logs `FINAL_REPORT_ENTRY` unconditionally, BEFORE the
   PASS/FAIL decision is even computed (`Rebuild_Control_Groups_Normalizer.py` lines ~13292-13775) — it is
   a completion marker, not success evidence. Corrected to independently require an explicit
   `PRODUCTION_REBUILD_CONTROL_GROUPS = PASS` line and to fail outright on an explicit `= FAIL` line;
   `FINAL_REPORT_ENTRY` alone can never satisfy `all_checks_pass`.
2. **Baseline `HARD_GATES_PASSED` now mechanically gates everything.** Previously only vocabulary/cache-key
   conditions were gated. Now gates identities, guard/run-lock state, provider/lease counters, fixture
   identity (reusing `checkpoint_f2_r1`'s own already-qualified `GetDocumentRoot`/`GetFileId`/
   `g_pDataModel.GetFileName` technique), the established 15-shot project size, and every vocabulary/cache
   condition — one exhaustive `gate_checks` list; any single failure produces
   `INCONCLUSIVE_BEFORE_EXECUTION` with the exact failed-gate names, never a silent pass.
3. **Snapshot 02 is now a real stage gate.** Previously classified an unconditional `RECORDED`. Now
   mechanically evaluates 20+ conditions and classifies `V1_STAGE_PASSED` or `FAIL` with exact failed-gate
   names. **Do not run command 2 unless Snapshot 02 reports `V1_STAGE_PASSED`.**
4. **Snapshot 03 is now mechanically decisive.** Previously classified an unconditional `RECORDED`. Now
   evaluates the full G proposition and classifies `G_PASS` or `FAIL` with exact failed-gate names, exposed
   directly in the final rollup (`mechanical_final_verdict` / `mechanical_final_failed_checks`) rather than
   requiring a reviewer to reconstruct the verdict from three separate files.
5. **The V2-only Known witness is now proven against its actual payload row**, not merely the coverage
   index (a Known-coverage fold missing from `payload["folded"]` is detected, not silently accepted), and
   the entire V2 projection's `payload["folded"].keys()` is required to exactly equal the set of requested
   folds whose coverage status is `Known` — plus the run log's own `matched_folds` field is now
   cross-checked against both the view's `known_count` and its `payload_folded_key_count`.

Offline suite expanded accordingly: `test_checkpoint_g_later_vocabulary_dryrun.py` now **131/131 PASS**
(previously 66/66), including a corrected end-to-end walkthrough that drives a REAL `SELECTED_USED` marker
transition and REAL broker provider-open/close + `cohort_acquired` accounting between snapshots — the prior
suite's own simulated Snapshot 02/03 printed `guard_state = UNUSED (expected SELECTED_USED)` and still
passed 66/66 because nothing gated on it; the corrected evaluators and tests now make that impossible.

## Why this exists

`F` is closed (see `../F1_FINAL_DISPOSITION_REVIEW.md`'s FINAL CLOSEOUT). `G` begins a different question,
unrelated to F's own process-lifetime memory/admission concern:

> Within one SFM process and one unchanged canonical Master generation, after a successful Normalizer
> command has acquired a projection for command vocabulary V1, a later legitimate Normalizer command whose
> vocabulary V2 differs from V1 and contains at least one fold absent from V1 must acquire/materialize
> authority covering V2 under that same generation. The earlier V1 projection must never be silently
> treated as authoritative for V2.

This is explicitly **not** generation replacement (roadmap item `I`). This checkpoint never edits the
Master, never republishes the sidecar, and never tests mid-command generation drift.

## Architecture this design relies on (independently verified by direct source inspection)

- Production's `acquire_master_index_via_qualified_authority()` requests consumer kind `normalizer_compat`
  with `expected_generation=self.master_hash` (`Rebuild_Control_Groups_Normalizer.py` lines ~10059-10134).
- The broker's `acquire_or_reuse_views()` cache-key formula (`broker.py` line ~498):
  `(h0.sha256, None, frozenset(folded_keys), consumer_kind)` — reproduced verbatim in this checkpoint's own
  `cache_key_for()`, never imported from production.
- `runtime.get_broker()` returns the SAME broker object on every call once READY in a process; calling it
  merely constructs/returns the resident object and never opens a sidecar or touches the Master.
- The authority package (`sfm_master_authority_productionized/*`, plus its `sfm_master_sidecar` sibling
  dependency) has zero SFM-only import dependencies — confirmed importable directly, offline and in real
  SFM, with no line-range-extraction workaround needed (unlike production itself, which is extracted by
  exact line range for its process-lifetime guard state only).
- `DetachedView.cache_key()` / `is_stale()` / `coverage.covered_keys()` / `coverage.lookup(folded_key)` →
  `CoverageResult(status, destination, occurrences)` with status in `{"Known", "MasterUnknown", "Uncovered"}`.
- `broker.provider_counters()` / `view_cache_entry_count()` / `outstanding_lease_count()` /
  `unreleased_lease_count()` / `recent_diagnostics()` / `cached_view(cache_key)` are all read-only.

Full citation trail and exact source line numbers are in `Checkpoint_G_Later_Vocabulary.py`'s own module
docstring.

## What this checkpoint is

A pure **read-only observer**. It never invokes the Normalizer, never invokes native Rebuild, never mutates
the scene, never changes shot selection, never acquires an authority projection itself, never opens a
provider, and never saves the project. The operator invokes the real, ordinary "Rebuild Control Groups"
command manually, between this script's own three invocations.

V1/V2 vocabulary is derived **independently** — this script never calls production's own
`collect_scope_master_wanted_folds()`. It uses fresh, self-contained reimplementations of the same neutral,
stated rule (ASCII-fold every control name in every animation set of the named shot).

## The V1/V2 pair and why

- **V1 = `shot3`** — established Checkpoint-B fixture identity and vocabulary evidence.
- **V2 = `shot9`** — a different, previously-proven legitimate Selected proper-subset workload.

The baseline snapshot does **not assume** these differ enough. It independently derives V1 and V2 from the
live scene and hard-gates before any production command:

1. exact `shot3` exists uniquely;
2. exact `shot9` exists uniquely;
3. V1 nonempty;
4. V2 nonempty;
5. `V1 != V2`;
6. `V2_ONLY = V2 - V1` is nonempty;
7. neither V1's nor V2's exact `normalizer_compat` cache key is already present in the broker's cache
   (clean-start gate, using the same cheap H0 observation the broker itself uses internally — no provider
   open).

**If any gate fails, the checkpoint classifies `INCONCLUSIVE_BEFORE_EXECUTION`, reports the exact evidence,
and the operator does not run the Normalizer.** Do not substitute another fixture shot if this happens —
report the failure.

### Exact list of corrected hard gates (correction round 2 — `_snapshot_01_baseline`'s own `gate_checks`)

`identity.production_sha256_matches_expected`, `identity.canonical_master_sha256_matches_expected`,
`identity.runtime_api_version_matches_expected`, `identity.runtime_build_id_matches_expected`,
`identity.runtime_is_canonical`, `state.main_window_available`, `state.guard_state_is_unused`,
`state.run_lock_absent`, `provider.current_open_provider_count_is_zero`,
`provider.total_opens_equals_total_closes`, `lease.outstanding_lease_count_is_zero`,
`lease.unreleased_lease_count_is_zero`, `fixture.matches_expected_normalized_copy`,
`fixture.is_not_forbidden_original`, `fixture.shots_enumerable`,
`fixture.project_shot_count_matches_established_size` (== 15, this fixture's own real-SFM-confirmed
project size), `vocabulary.v1_shot_resolves_uniquely`, `vocabulary.v2_shot_resolves_uniquely`,
`vocabulary.v1_nonempty`, `vocabulary.v2_nonempty`, `vocabulary.v1_not_equal_v2`,
`vocabulary.v2_only_nonempty`, `authority.broker_and_observation_available`,
`authority.observed_master_hash_matches_governing_master_sha256`, `cache.v1_cache_key_absent_at_baseline`,
`cache.v2_cache_key_absent_at_baseline`. `HARD_GATES_PASSED` requires every one of these to pass; the
snapshot JSON's own `failed_gates` list names exactly which ones did not.

## Real-SFM operator sequence

Evidence-file discipline matches this project's established convention
(`checkpoint_process_attempt_guard/`): every snapshot/run is written to a new, uniquely-numbered, immutable
file; `write_evidence_*_once()` refuses (raises) rather than silently overwriting an existing path; only a
small, non-evidentiary continuation-state pointer file and the freely-overwritten final rollup are ever
replaced.

1. **RESTART SFM FIRST.**
2. Open **only** `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx` — never `testscripts.dmx`.
3. Run `Checkpoint_G_Later_Vocabulary`. **[SNAPSHOT 01 — baseline.]** Confirm the printed summary reports
   `classification = HARD_GATES_PASSED`. If it instead reports `INCONCLUSIVE_BEFORE_EXECUTION`, **STOP** —
   do not proceed to step 4 — and report the exact `gate_failure` text, the full `failed_gates` list, and
   the recorded V1/V2/V2_ONLY sets verbatim.
4. Invoke the real **Rebuild Control Groups** command. Choose **Selected Shot(s)**, selecting `shot3` alone.
   Let it complete normally.
5. Run `Checkpoint_G_Later_Vocabulary` again, in the same SFM process. **[SNAPSHOT 02 — after_v1.]** Confirm
   the printed summary reports `classification = V1_STAGE_PASSED`. **If it instead reports `FAIL`, STOP —
   do NOT run command 2.** A bad command-1 state must not be followed by command 2 merely to finish the
   schedule. Report the exact `gate_failure` text and the full `failed_gates` list verbatim.
6. Without restarting SFM, select only `shot9`. Invoke **Rebuild Control Groups** again. Choose **Selected
   Shot(s)**. Let it complete normally.
7. Run `Checkpoint_G_Later_Vocabulary` one more time. **[SNAPSHOT 03 — after_v2.]** This is the decisive G
   snapshot; confirm the printed summary reports `classification = G_PASS`. If it instead reports `FAIL`,
   report the exact `gate_failure` text and the full `failed_gates` list verbatim — this indicates a genuine
   authority-behavior defect, not an inconclusive setup problem.
8. Return all output artifacts (see below), including `sfm_checkpoint_g_final_result.json`, whose own
   `mechanical_final_verdict` / `mechanical_final_failed_checks` fields directly expose the decisive result.

**Do not** run All Shots, test large Selected batches, edit the Master, republish the sidecar, or attempt a
second All-Shots/heavy campaign — this checkpoint's own two commands are both small, single-shot Selected
requests, deliberately lighter than any prior F-series campaign.

## Output files to return

- `sfm_checkpoint_g_snapshot_01_baseline.{json,txt}`
- `sfm_checkpoint_g_snapshot_02_after_v1.{json,txt}`
- `sfm_checkpoint_g_snapshot_03_after_v2.{json,txt}`
- `sfm_checkpoint_g_run_01_v1_shot3.txt` (the real production log preserved automatically after command 1)
- `sfm_checkpoint_g_run_02_v2_shot9.txt` (the real production log preserved automatically after command 2)
- `sfm_checkpoint_g_final_result.json` / `sfm_checkpoint_g_final_summary.txt` (freely-overwritten rollup —
  complete after snapshot 03)
- `sfm_checkpoint_g_continuation_state.json` (non-evidentiary bookkeeping)

The operator never manually renames, copies, or preserves the production log themselves — the checkpoint
does this automatically.

## Mechanical G PASS contract (now self-classified by the checkpoint script itself, not merely a post-hoc
## review checklist — Snapshot 03's own `classification` field IS the decisive result)

Snapshot 01 classifies `HARD_GATES_PASSED` only if ALL of the following mechanically pass (any single
failure produces `INCONCLUSIVE_BEFORE_EXECUTION` with the exact failed-gate names — see "Exact list of
corrected hard gates" below for every gate name).

Snapshot 02 classifies `V1_STAGE_PASSED` only if ALL of the following mechanically pass (any single failure
produces `FAIL` with exact failed-gate names):

- continuity: same PID as baseline;
- identities still correct (production/Master SHA, runtime API/build, runtime canonical);
- guard state is exactly `SELECTED_USED`; run lock absent;
- the Master generation observed now is identical to the one observed at baseline;
- exactly one new run-01 log was captured, and its verifier reports `all_checks_pass = true` (which itself
  now requires an explicit `PRODUCTION_REBUILD_CONTROL_GROUPS = PASS` line, not merely
  `FINAL_REPORT_ENTRY`) with the logged `unique_scope_folds` matching `len(V1)`;
- provider counters increased from baseline by exactly +1 open / +1 close, and `current_open_provider_count
  == 0` now;
- the exact V1 cache key is present, fresh, `normalizer_compat`, under the governing Master generation, with
  `covered_keys_equals_requested = true` and zero Uncovered, and its `payload["folded"].keys()` exactly
  equals its own coverage-Known fold set;
- the exact V2 cache key is still absent;
- outstanding and unreleased lease counts are `0`;
- the diagnostics delta since baseline contains a `cohort_acquired` entry and does NOT contain a
  `fully_reused_no_provider_open` entry;
- the log's own `matched_folds` field equals both the V1 view's `known_count` and its
  `payload_folded_key_count`.

Snapshot 03 classifies `G_PASS` only if ALL of the following mechanically pass (any single failure produces
`FAIL` with exact failed-gate names):

- continuity: same PID as baseline/Snapshot 02; identities still correct; guard state remains
  `SELECTED_USED`; the Master generation observed now still matches baseline;
- exactly one new run-02 log was captured, its verifier reports `all_checks_pass = true` for the exact
  single selected `shot9`, with the logged `unique_scope_folds` matching `len(V2)`;
- provider counters increased since Snapshot 02 by exactly +1 open / +1 close, and
  `current_open_provider_count == 0` now;
- the exact V2 cache key is present, fresh, `normalizer_compat`, under the governing Master generation, with
  `covered_keys_equals_requested = true`, zero Uncovered, and `payload["folded"].keys()` exactly equal to
  its own coverage-Known fold set;
- outstanding and unreleased lease counts are `0`;
- the diagnostics delta since Snapshot 02 contains a `cohort_acquired` entry and does NOT contain a
  `fully_reused_no_provider_open` entry;
- the log's own `matched_folds` field equals both the V2 view's `known_count` and its
  `payload_folded_key_count`;
- a V2-only Known witness fold was found AND is proven present in the view's actual
  `payload["folded"][folded_key]` row, with a row count matching its coverage occurrence count and a
  destination consistent with its coverage destination (never merely "coverage says Known").

**INCONCLUSIVE BEFORE EXECUTION** if snapshot 01 itself reports anything other than `HARD_GATES_PASSED` —
no production command is ever run in that case.

## Offline qualification already performed (before this checkpoint was prepared)

`test_checkpoint_g_later_vocabulary_dryrun.py` (SHA-256
`824761ed71223afb19ee566c2f4a29e9ffe2c23d311d9aa7ddb3e2b7a5d0e77c`) — **131/131 PASS** under the real
embedded Python 2.7.5, using the REAL accepted authority package
(`tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/`, confirmed
byte-identical to the live-deployed copy) against a fake `sfmApp`/DME object model. Covers, in addition to
everything the first-round suite covered: FINAL_REPORT_ENTRY alone never satisfying `all_checks_pass`, and
an explicit production FAIL line forcing it false even alongside a correct fold count; full mechanical
coverage of the 26 baseline gates with targeted negative scenarios — wrong production SHA, wrong Master
SHA, wrong runtime API/build, non-canonical runtime, unavailable main window, non-`UNUSED` guard state, a
present run lock, an open provider, a provider opens/closes mismatch, an outstanding lease, an unreleased
lease, a wrong fixture filename, the forbidden original fixture filename, a wrong project shot count — each
independently isolated via its own non-colliding fold-vocabulary tag to avoid broker-singleton cross-test
contamination);
the V1-stage evaluator's full mechanical matrix (happy path plus 14 adversarial single-gate-failure cases:
explicit production FAIL, wrong guard state, PID changed, generation changed, provider delta 0/>1, V1 view
absent/stale/wrong-coverage, V2 already present, diagnostics missing `cohort_acquired`/containing
`fully_reused_no_provider_open`, outstanding/unreleased lease, `matched_folds` inconsistency); the
final-G evaluator's full mechanical matrix (happy path plus 8 adversarial cases covering the same plus the
V2-only-witness-specific ones: full-cache-reuse, V2 Uncovered, no Known V2-only witness, a Known-coverage
witness missing from the payload, a payload key-set inconsistency, outstanding/unreleased lease,
`matched_folds` inconsistency); a corrected end-to-end `main()` walkthrough that installs a REAL
`SELECTED_USED` marker and drives REAL broker provider-open/close + `cohort_acquired` accounting between
snapshots, reaching `HARD_GATES_PASSED` → `V1_STAGE_PASSED` → `G_PASS` and confirming the final rollup's own
`mechanical_final_verdict`/`mechanical_final_failed_checks` fields; plus everything the first-round suite
already covered (independent ASCII-fold/vocabulary derivation and provenance recording; baseline log
seeding without becoming a run; broker diagnostic inspection against controlled cache states; real lease
acquire/release/register/reconcile accounting; zero-provider-opened confirmation; immutable-evidence
refuse-to-overwrite discipline; a smoke check confirming the scope-aware guard's own pinned line ranges are
still valid against the current production script). `test_process_attempt_guard_regression.py` (the
existing, unrelated F3-Guard offline suite) was not touched and was not re-run as part of this preparation,
since this checkpoint makes no production edits.

## Proof no production/authority/Master files were touched

`git status --porcelain` after writing this checkpoint shows only the new
`real_sfm_qualification/checkpoint_g_later_vocabulary/` directory as untracked; `git diff --stat` against
`audit_external_runtime/Rebuild_Control_Groups_Normalizer.py`, `sfm_defaultanimationgroups.txt`, and the
entire `tests/` tree (including the accepted authority package candidate) shows zero changes. This
checkpoint only reads those files.

## Identities this checkpoint is pinned against

- Production Normalizer SHA-256: `1f4ec5a26605aa90380eb0532fec3915d2cc24a3a20473ed70d57198bd995db7`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Authority runtime API version: `1.0.0-b2a`
- Authority runtime build ID: `package-boundary-corrected-2026-09-22`
- Checkpoint script SHA-256 (correction round 2): `c0b1ab2268137b17080b5a70edbb0d32091c8841aefc1cccefeb29da1d9c778d`
- Offline dry-run test SHA-256 (correction round 2): `824761ed71223afb19ee566c2f4a29e9ffe2c23d311d9aa7ddb3e2b7a5d0e77c`

## Explicit non-authorization

This checkpoint does not modify production, the authority runtime/broker/cache implementation, or the
canonical Master. It does not reopen `F`. It does not perform generation replacement (roadmap item `I`).
**The real-SFM G campaign has not been run.** Whether the shot3→shot9 pair is mechanically qualified to
produce a decisive result is established here only by static/offline design (the pair's real vocabulary in
the live fixture has not yet been observed) — the live V1/V2 hard-gate result is not claimed until real SFM
actually produces it.
