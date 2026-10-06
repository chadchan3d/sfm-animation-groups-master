# CPM real-SFM Session 4 — evidence

**Verdict: PASS** — S4A (Body Apply) PASS and S4F (Clothing Fit) PASS, 2026-10-06.

- **Runbook:** `SESSION4_RUNBOOK.md` at `b65c085`. Harness `CPM_S4_Rollback_Harness.py` `45c44f3d…`
  (deployed byte-exact in both campaigns, `harness_deploy_record.json`).
- **Raw outputs:** `raw/` (redacted, byte-exact excerpts; SHA-256 in `raw/MANIFEST.md`).
- **Product:** unchanged since `00d0d83`; private app `9a78fc96…` verified by the harness at
  every ARM.
- **Authority:** exact production G1 throughout. `S2-Prepare` baselines and `S2-VerifyUntouched`
  comparisons (`untouched_compare.json` `exact_match: true`) in both campaigns.

## 1. S4A — Body Apply (§7.1)

Process pid 2540; CPM run `20261006-112749-pid2540`; broker `0x30fab290`; window `0x309ae698`.
Fixture `mia1`; A3 applied `Body` (`outcome='committed' changed_sides=3`, 11:28:05); the injected
and follow-up Applies used `BodyTest`.

| # | Criterion | Evidence | Result |
|---|---|---|---|
| 1 | G1 authorization | `PROD_CPM_OPERATION_AUTHORIZED operation=u'Apply Preset' sha256=ac45e5c1… membership=46` at 11:32:49.581 (CONTROL) and 11:35:11.730 (GATE); fire records `authority_master_sha256` G1 | PASS |
| 2 | Native writes, predicate after writes | both injections: caller `prod_apply`, `caller_opened: true`, preset `BodyTest`, kind body, `changed_sides: 1`, real precommit predicate `true` | PASS |
| 3 | CONTROL | `s1_fire`: `real_result: true`, `substituted: false`; log `PROD_APPLY_ABORT_REFRESH` then `PROD_APPLY_ABORT_VERIFY restored=True original_error=RuntimeError('Preset values failed precommit verification.')`; dialog "Can't apply preset"; `s1_state`: status "Preset could not be applied safely. This preset was not applied.", Undo `{count 30, "Apply Body Preset"}` = ARM, `mia1` diff `[]` | PASS |
| 4 | GATE | `s2_fire`: `real_result: true`, then `substituted: true`, `returned: false`; log `PROD_APPLY_ABORT_VERIFY restored=False`, `PROD_ACTION_ERROR … ProdRecoveryUnverifiedError('Preset Apply failed and recovery could not be verified. …')`; dialog "Recovery could not be verified"; Undo = ARM, `mia1` diff `[]` | PASS |
| 5 | No false success | operations 4 and 5: no `native-commit`, no `PROD_APPLY outcome='committed'`; both `PROD_OPERATION_END … phase=u'BEGIN' native_commit=None` | PASS |
| 6 | No reacquisition in rollback verification | `adapter_calls_during_verification: 0` in both fire records; broker 0/0/0 and `total_provider_opens` 1 → 1 across verification | PASS |
| 7 | Idle authority | P2–P5 (seq 62–65): 0 leases / 0 unreleased / 0 open providers, one window, one watcher; `s1_state`/`s2_state` RECORDED_OK (14/14 checks), `wrappers_absent: true` | PASS |
| 8 | Usable afterwards | A14 (operation 6): `native-commit`, `PROD_APPLY outcome='committed' … preset=u'BodyTest' changed_sides=1` | PASS |
| 9 | Restoration | `deploy_before_harness.txt` = `deploy_after_removal.txt` (`cefc2b88…`); `untouched_compare` exact; inventory Master `ac45e5c1…`, manifest `d810d648…`, sidecar `bcd97641…` | PASS |

## 2. S4F — Clothing Fit (§7.2)

Process pid 17544; CPM run `20261006-114606-pid17544`; broker `0x311d72b0`; window `0x30bea698`.
Injected Fits: generation 2 (operation 3, CONTROL) and generation 3 (operation 4, GATE), each
selecting exactly `assaultsuitbody1`, `loinclothbra_chadfix_071`. Follow-up: generation 4
(operation 5), `assaultsuitbody1` only.

| # | Criterion | Evidence | Result |
|---|---|---|---|
| 1 | Gfit = G1 | `PROD_CPM_OPERATION_AUTHORIZED operation=u'Clothing Fit' sha256=ac45e5c1… membership=26` (11:47:52.468, 11:49:49.373); `PROD_CPM_FIT_STAGE_OPEN index=0 gfit=ac45e5c1… literals=34` (11:47:53.615, 11:49:49.421); harness `stage_opened.generation` G1 | PASS |
| 2 | Writes, predicate inside the open Undo | both injections: caller `prod_apply_match`, `caller_opened: true`, target `assaultsuitbody1`, `changed_sides: 3`, gfit G1, real predicate `true` | PASS |
| 3 | CONTROL | `s1_fire`: `real_result: true`, `substituted: false`; log `PROD_CLOTHING_FIT_ABORT_REFRESH`, `PROD_CLOTHING_FIT_ABORT_VERIFY … restored=True original_error=RuntimeError("Clothing Fit write failed for u'assaultsuitbody1'.")`; `CLOTHING_FIT_FAIL generation=2 index=0 … committed_current=False`; `fit_failed` = [assaultsuitbody1, `committed: false`, `verification: not-committed`]; status "Clothing Fit could not finish. Nothing changed."; no failure dialog | PASS |
| 4 | GATE | `s2_fire`: `real_result: true`, then `substituted: true`; `PROD_CLOTHING_FIT_ABORT_VERIFY … restored=False`; `CLOTHING_FIT_FAIL generation=3 … ProdRecoveryUnverifiedError(…)`; `fit_failed` verification `abort-unverified`; `G18AN_FIT_FAILURE_DIALOG verified_changed=[] committed_uncertain=[] recovery_unverified=[u'assaultsuitbody1'] unattempted=[u'loinclothbra_chadfix_071'] undo_count=0`; status "Clothing Fit stopped. Recovery of the failed target could not be verified." | PASS |
| 5 | Lease held through recovery | both fire records: `entry_counters.outstanding_leases 1`, `entry_releases 0`, `adapter_calls_during_verification 0`, `total_provider_opens` 2 → 2 across verification | PASS |
| 6 | Released exactly once | each state record: one `release()` on the armed stage (`0x2af9a6f0`, `0x2b484bb0`), result `None`, leases 1 → 0; state counters 0/0/0 | PASS |
| 7 | Target 2 never staged or mutated | no `PROD_CPM_FIT_STAGE_OPEN index=1` and no target-2 skip in the run; `fit_unattempted` = [loinclothbra_chadfix_071] only; target-2 values diff `[]` | PASS |
| 8 | Nothing committed | `fit_committed_order` `[]` in both states; only `native-commit` in the run is the follow-up; Undo `{count 0, ""}` = ARM | PASS |
| 9 | Idle authority | P2–P6 (seq 67–71): 0/0/0, one window, one watcher; `s1_state`/`s2_state` RECORDED_OK (21/21 checks), `wrappers_absent: true` | PASS |
| 10 | Usable afterwards | generation 4: stage open `gfit=ac45e5c1…`, `native-commit`, `CLOTHING_FIT_STAGE=PASS … committed-verified mappings=26 warnings=7 committed=True`, `PROD_CPM_FIT_STAGE_RELEASED index=0 ok=True`, `CLOTHING_FIT_RESULT=PASS … partial_changed=1 … failed=0 unattempted=0`; F14 one Undo, visually restored (operator) | PASS |
| 11 | Restoration | deployment `cefc2b88…` before = after; `untouched_compare` exact; inventory G1 Master/manifest/single sidecar | PASS |

Probes: S4A P1–P5 = seq 61–65; S4F P1–P6 = seq 66–71. P1 records precede CPM in each process.

## 3. Observations (not failures)

- **Native Undo count:** `GetUndoItemCount` counts native undo items, not entries (one Body Apply
  at A3: 0 → 30). The count and description were unchanged across every injected operation.
- **Fit exception-path release (carried to cleanup/K):** the exception path releases with a bare
  `stage_authority.release()` (no `PROD_CPM_FIT_STAGE_RELEASED` line; result discarded). Live
  evidence shows exactly one successful release per injected stage, so there is no defect; the
  missing log line and the theoretical second `release()` after a raising success-path release
  remain a cleanup/K note.
- **Coverage limit:** `BodyTest` changes no bone scales (`changed_existing_scales=0`), so the Body
  bone-scale branch of rollback verification is covered offline only. Expression Apply shares
  `prod_apply` and is covered offline (§9 of the runbook). Postcommit/post-stage
  committed-unverified branches were out of scope.
- **Provider opens:** `total_provider_opens` rose 1 → 2 at S4F's first stage open (before any
  injection) and never changed during rollback verification.

## 4. Session 4 result

Handoff §22 blockers 4 and 5 are qualified: for both Body Apply and Clothing Fit, an authentic
Abort followed by authentic rollback verification reports "not applied / not committed" when
restoration is verified, and production's own recovery-unverified path is truthful and fail-closed
when verification fails — without reacquiring authority, without a false success, and (Fit) with
the stage lease held through recovery and released exactly once.
