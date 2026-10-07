# CPM item 7 — diagnostic/development logging reduction (evidence)

**Result: COMPLETE — offline qualification PASS (2026-10-07).** This is an **offline-qualified
candidate** only; no real-SFM claim is made for the new app bytes (§7).

Design: `cpm/qualification/ITEM7_DIAGNOSTIC_LOGGING_REDUCTION_DESIGN.md` (owner-approved, recorded at
`4d414c5`). Implemented exactly within its §3–§10 dispositions, §8 allowlist and §16 assignment; no
§14 stop condition was met.

## 1. Starting gate (verified before editing)

| Check | Result |
|---|---|
| Branch / HEAD / `origin/master` | `master` at `4d414c59fd915731cb2b0f64500135d8ed730588`, equal to `origin/master` |
| Starting app | `1e8668717f9a4a1def0900c6b51e20cb9a7676cc365244eab5c31233f133eeeb` (item-6 candidate, committed at `7b69b52`) |
| Ledger | item 7 APPROVED DESIGN — IMPLEMENTATION NOT STARTED; changed to the §13 IN PROGRESS wording at start |
| Design counts (independently recomputed from the starting app) | 77 timing calls in 19 owners; 72 timer assignments over the 24 pinned names (timing-only use); 46 direct log removals (incl. the four logging-only `try` constructs holding 8 records and 11 `PROD_MODEL_SWITCH_STAGE` stages); 88 wrappers across 53 owners; 6 constant exclusions; route sets 20 / 8 / 24; `kind_label` consumed only by removed records; `time.` used only by the 72 timers and `prod_perf_seconds` — all exact |

## 2. Identities

| Artifact | Before | After |
|---|---|---|
| `cpm/app/SFM_Character_Preset_Manager.py` | `1e8668717f9a4a1def0900c6b51e20cb9a7676cc365244eab5c31233f133eeeb` (33,304 lines) | **`bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5`** (32,593 lines) |
| `cpm/convergence/tests/test_cpm_app_canonical_route.py` | `29ae0e8433c9c50ee469944dbd00df340f0b517f30a4f55ce74fb0fd3bf80686` | `e21ba3ae625d02ec36759792d6541413e0e3d6c142140fc9d7945e3ad2029691` |
| `cpm/convergence/tests/test_cpm_app_logging_cleanup.py` | — (new) | `2aa6b567301f6491aa4f00df1c58d81df26be6077de20fce9e0ec8cb2eef7dbb` |
| `cpm/convergence/tests/item7_precleanup_source_manifest.json` | — (new) | `cbb3010b10219588b202c9ec011319962b2aef17742a5f7fa5e6dbb508503d5d` |

Hashes are of LF content. Unchanged and asserted by the item-7 test's `protected.*` checks: launcher
`996ca483…`, frozen G18AN baseline, adapter, `cpm_compat_v1` projection, Normalizer audit copy,
Master, the shared authority package (24 `.py` files, one digest), the seven other convergence
suites, the item-6 test/manifest/design/evidence and the Session 1 probe. `real_sfm_qualification/`
(Sessions 1–4) is untouched. No deployment occurred.

## 3. Historical item-6 confirmation (design §9)

- Detached worktree at `7b69b520a2472d3700ce347a1d2a59bc98e926f2` (long paths enabled, no line-ending
  conversion). Pinned hashes asserted inside it: app `1e866871…`, item-6 test `a3024d34…`, item-6
  manifest `a92647949…`, canonical-route test `29ae0e84…` — all exact.
- The untouched item-6 test was run from the worktree with `CPM_TEST_APP_PATH` unset; imports
  resolved to the worktree's own test dependencies. Result: **2.7.5 46/46 · 3.10 46/46**.
- Recorded as historical item-6 confirmation, not candidate qualification
  (`item7_offline_outputs/historical_item6/`). The same verified worktree app was the reference
  input for manifest generation and every reconstruction/comparison. The worktree was removed after
  all comparisons finished.
- The item-6 test at the current checkpoint still pins app `1e866871…` by design and is not a gate
  for the new candidate.

## 4. Pre-edit transformation manifest (design §10)

- Generated **before any production edit** by `test_cpm_app_logging_cleanup.py`'s manifest writer,
  which refuses unless both the explicit reference and the working app are exactly `1e866871…`, and
  refuses to overwrite an existing manifest. Its SHA-256 is pinned in the test; it was never
  regenerated from the candidate. It is byte-identical when generated under 2.7.5 and 3.10.
- 295 records identified by qualified owner, domain/key and ordinal with a token-text digest of the
  original statement (line numbers are navigation only): 77 timing calls, 72 timer assignments,
  38 direct log deletions, 4 logging-only `try` constructs, 2 accepted-path diagnostic statements,
  1 `kind_label` assignment, 87 wraps + 1 wrap-pair (Q3 REJECT), 2 payload replacements, 1
  `raise` → `raise exc`, 8 top-level removals + `import time`, and 1 preserve record for the excluded
  `G18AN_POST_FIT_ACTION_STATE` statement. Untouched top-level blocks, `ProdWindow` member order and
  the `p02_safe_write_json` hash are recorded.
- The production edit was applied by a deterministic, manifest-driven editor (not committed) that
  located every record by digest, refused any overlap, and wrote the result once.

## 5. Dispositions applied

- **Timing machinery (D1):** `prod_perf_seconds`, `prod_perf_log`, `astra_perf_timing`,
  `prod_action_timing`, `PROD_PERF_LOGGING` and `import time` removed; all 77 timing calls and 72
  timer assignments removed.
- **Reporting constants (D3):** `SEMANTIC_PROVIDER_MODE_SIDECAR`, `SEMANTIC_PROVIDER_FORCE_MODE`,
  `G18AN_PARITY_SHORTCUT` and the `G18AN_PROVIDER_FORCE_MODE` startup line removed;
  `self.g18an_parity_shortcut = None` retained. The four-line comment above those constants
  (describing them) was removed with them; no other comment changed.
- **Direct removals:** the 46 approved log records, the accepted-path diagnostic assignment/reset in
  `prod_bs_index_capture_map` and `kind_label` in `refresh_preset_view`.
- **Payload substitutions:** `PROD_MODELS count=%d initial_index=%d` (candidate list dropped);
  `CLOTHING_FIT_RESULT=PASS generation=` → `CLOTHING_FIT_RESULT generation=`.
- **Bounded containment:** exactly 88 `try: <log> except Exception: pass` wrappers across the 53
  owners (the Q3 REJECT wrapper holds the diagnostic assignment plus its log). The six constant
  records, `p02_safe_write_json` and the complete `G18AN_POST_FIT_ACTION_STATE` statement are not
  wrapped and are byte-identical.
- **Startup:** the compound `StartProdTool` lines were split one statement per line with their
  approved removals/wrappers; the bare `raise` in the `not isinstance(exc, Exception)` branch is now
  `raise exc`.
- **Retained (D2 and §4):** Q1 parity oracle disabled (`PROD_Q1_INDEXED_CAPTURE_PARITY = False`) and
  all retained events, authority/broker/adapter/projection, operation contexts, mutation/persistence/
  rollback, Fit stage/release, resource checkpoints and R14, R15 ownership/lifecycle.
- Deleted statements leave the neighbouring blank lines in place; every untouched block is
  byte-identical (proven by the reconstruction gate).

## 6. Qualification

Commands (from `cpm/convergence/tests`, `PYTHONDONTWRITEBYTECODE=1`): each phased suite
`<py3.10> --phase=publish`, `<py2.7.5> --phase=suite`, `<py3.10> --phase=compare`; R14/R15
`--phase=run` under each interpreter; the item-7 test with `--reference=<pinned item-6 app>` under
each interpreter, after the route publish phase. Interpreters: embedded Python 2.7.5 (production,
real PySide 1.2 / Qt 4.8) and Python 3.10.6. Outputs: `item7_offline_outputs/candidate/` (they
contain no workstation paths; only carriage returns were removed so line endings are uniform).

| Suite | Item-6 candidate (`1e866871…`) | Item-7 candidate (`bfba4d3a…`) |
|---|---|---|
| `test_cpm_compat_v1_projection.py` | 196/196 · 196/196 · 3/3 | 196/196 · 196/196 · 3/3 |
| `test_cpm_authority_adapter.py` | 205/205 · 205/205 · 3/3 | 205/205 · 205/205 · 3/3 |
| `test_cpm_app_canonical_route.py` | 85/85 · 85/85 · 3/3 | 85/85 · 85/85 · 3/3 |
| `test_cpm_app_operation_context.py` | 108/108 · 108/108 · 3/3 | 108/108 · 108/108 · 3/3 |
| `test_cpm_app_clothing_fit.py` | 95/95 · 95/95 · 3/3 | 95/95 · 95/95 · 3/3 |
| `test_cpm_convergence_gates.py` | 152/152 · 152/152 · 3/3 | 152/152 · 152/152 · 3/3 |
| `test_cpm_app_r14_ctypes_isolation.py` | 2.7.5 18/18 · 3.10 15/15 | 2.7.5 18/18 · 3.10 15/15 |
| `test_cpm_app_r15_namespace_isolation.py` | 2.7.5 345/345 (Qt real + model) · 3.10 188/188 (model) | 2.7.5 345/345 (Qt real + model) · 3.10 188/188 (model) |
| `test_cpm_app_logging_cleanup.py` (new) | — | **2.7.5 144/144 (window gates Qt real + model) · 3.10 117/117 (model)** |

- **Canonical-route edits (design §7):** `ITEM7_CHANGED_TOP` (20) merged into the cumulative
  `EXPECTED_CHANGED_TOP` (consumed by R14, unedited); removals must equal
  `ITEM6_REMOVED_TOP | ITEM7_REMOVED_TOP` (8); `ITEM7_CHANGED_METHODS` (24) unioned into the
  expected changed methods; the unnamed top-level comparison removes exactly one `import time` and
  asserts it is absent from the candidate (imports are not ignored generally). Added/removed method
  expectations are unchanged. No assertion was weakened.
- **Item-7 test coverage (2.7.5 groups):** identity and manifest pins (4); protected hashes (19);
  counts (7); reconstruction + byte identity of every untouched block/member, `p02` hash and the
  preserved G18AN statement digest (1); structure — 88 new wrappers in the 53 owners, R14's two
  pre-existing wrapper shapes unchanged, no unwrapped non-constant log (3); closure — no removed
  symbol, `import time` or timer survives, module compiles, retained symbols present, new payloads
  (7); post-baseline helper coverage (5); item-6 continuity (2); sensitivity (10); real sink
  open/write/flush/close containment for `log_line`/`reset_log` (8); route-harness injection with a
  throwing emitter per event plus a failing-`__repr__` argument, broker idle after each (24); window
  gates for Python-2 handler continuity, real `fit_finish` and R15 startup, in real Qt and the Qt
  model (27 + 27).
- **§11.5 real `fit_finish`:** the real `fit_finish`, `semantic_provider_ready` and
  `prod_cpm_request_stale_rebuild_if_needed` run with a stale scope. Readiness calls are attributed
  to their caller: exactly one comes from `fit_finish` (the post-Fit statement) and the remainder from
  the unchanged `operation_end` refresh, matching the reference total. The stale rebuild is queued
  first; with an injected `CLOTHING_FIT_RESULT` failure the behaviour equals the uninjected run; a
  closing window makes no `fit_finish` readiness call and equals the reference; a scheduling failure
  propagates exactly as in item 6.
- **§11.6 R15 startup:** injected `G18AN_RUN`, `PROD_R15_MODULE` and `PROD_WINDOW_SHOWN` failures
  still return `created` with an idle state and a live window; `PROD_OPEN_FAIL` during a genuine
  construction failure leaves no stuck `STARTING`; a non-`Exception` `BaseException` escapes as the
  original object both with and without an injected logging failure. The reference was observed to
  let the injected logging failure replace the original in that last case, which `raise exc` fixes.
- **§11.7 sensitivity:** ten mutated candidates were rejected under both interpreters — changed
  product predicate, omitted release, widened handler, changed retained event, deleted post-Fit
  readiness, wrapped post-Fit readiness, altered `p02_safe_write_json`, missing `raise exc`, edited
  post-baseline helper and an unexpected removal.
- **Test-authoring corrections made before the qualifying run** (all in the new, uncommitted item-7
  test; none in product code or existing suites): (a) the wrapper census subtracts the two wrapper
  shapes already present in R14's `prod_resource_snapshot`, now asserted separately; (b) the real
  sink's close-failure case returns `True` because write and flush already succeeded — every mode is
  required to return its exact value without raising; (c) route-injection reference runs moved after
  all candidate idle checks, because the reference's uncontained emitter strands a process-wide
  broker lease (the defect item 7 removes); (d) handler scenarios record a raised exception per case
  instead of aborting the child, and require a non-raising baseline; (e) `fit_finish` expectations
  were corrected from hard-coded values to caller attribution plus equality with the reference, since
  `operation_end` legitimately re-reads readiness and queues its own callbacks; (f) Python 2 parses
  the app from bytes. The first edit attempt dropped `diagnostics = traceback.format_exc()` in
  `StartProdTool`; the reconstruction gate caught it. The app was restored from the pinned reference
  and the corrected editor re-applied.
- The Session 4 harness was not rerun or repinned (it pins the pre-cleanup app by design).

## 7. Qualification status and limitations

- **Offline-qualified candidate:** app `bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5`.
- Sessions 1–4 qualify only app `9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900`.
  Neither `1e866871…` nor `bfba4d3a…` inherits their exact-build real-SFM PASS; post-cleanup
  real-SFM qualification is item 8.
- The candidate is not deployed. Any later deployment follows the R15 restart rule.
- Python 3.10 window and R15 results use the Qt model only (PySide is unavailable there).
- Item-8 inputs (design §12): candidate hash above, preserved-component hashes (§2), manifest
  identity (§4) and the offline results (§6). Fit results are now matched as
  `CLOTHING_FIT_RESULT generation=`; `PROD_MODELS` no longer lists candidates; timing records
  (`PROD_PERF`, `ASTRA_PERF`, `PROD_ACTION_TIMING`) no longer exist.
- Not done (out of scope): item 8; the Session 4 Fit release-path observation; stale-scope UI and
  `SidecarMissing` messaging; legacy cleanup; K and L.
