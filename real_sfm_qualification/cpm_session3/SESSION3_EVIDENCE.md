# CPM real-SFM Session 3 — evidence

**Verdict: PASS** — `S3` CORE PASS (2026-10-06) + `S3_ADD` PASS (2026-10-06).

- **Runbook:** `SESSION3_RUNBOOK.md` (§1–§9 at `eb71dad`; §10 S3_ADD at `bcfa9b6`;
  criterion-9, criterion-12 and C13 wording corrected at closeout).
- **Raw outputs:** `raw/` (redacted, byte-exact excerpts, SHA-256 in `raw/MANIFEST.md`).
- **Product:** unchanged since `00d0d83`. The launcher (`996ca483…`), private app (`9a78fc96…`)
  and probe v3 (`ce4ace98…`) are as deployed for R15.

## 1. Campaign S3 — Clothing Fit G1 → G2 interruption (CORE PASS)

Process pid 26156; CPM run `20261006-000600-pid26156`; broker `0x314d92b0`; window `0x30ee7698`
(the same window at P2, P3 and P4). Fit generation 2, operation 3: `assaultsuitbody1`, then
`loinclothbra_chadfix_071`.

| # | Criterion | Evidence | Result |
|---|---|---|---|
| 1 | Gfit = G1 | `PROD_CPM_OPERATION_AUTHORIZED operation=u'Clothing Fit' sha256=ac45e5c1…` | PASS |
| 2 | Target 1 committed under G1 | stage open index 0 `gfit=ac45e5c1…`; native-commit; `CLOTHING_FIT_STAGE=PASS … committed=True` | PASS |
| 3 | Lease released before target 2 | `RELEASED index=0 ok=True` precedes every index-1 event. Pause record (00:10:02.868) PAUSED_VALID: `fit_stage_running false`; broker 0/0/0; changed literals `Breastsize`, `Muscles`, `slim` | PASS |
| 4 | Exact G2 between targets | yield enter, then `G18AN_MODAL_DEFER_FIT generation=2 index=1`; activation 00:11:04 → `54413b6c…`; post-switch inventory exact G2; resume record (00:13:37.588) shows a live G2 Master; then yield exit | PASS |
| 5 | Gfit re-proved at resume | `G18AN_MODAL_RESUME_FIT generation=2 index=1`, then the index-1 stage proof | PASS |
| 6 | Refused | `PROD_CPM_FIT_STAGE_REFUSED index=1 gfit=ac45e5c1… kind=u'generation-mismatch'` | PASS |
| 7 | Target 2 never mutated | no index-1 stage open or commit; `CLOTHING_FIT_FAIL … index=1 … committed_current=False` | PASS |
| 8 | No continuation under G2 | no further generation-2 stage events | PASS |
| 9 | Truthful accounting (wording corrected at closeout) | `CLOTHING_FIT_FAIL … changed=[] failed=[] unattempted=[loinclothbra_chadfix_071]`. Target 1 committed with plan warnings, so it is held in `fit_partial`, not `fit_changed`. `G18AN_FIT_FAILURE_DIALOG verified_changed=[u'assaultsuitbody1'] committed_uncertain=[] recovery_unverified=[] unattempted=[u'loinclothbra_chadfix_071'] undo_count=1`. The dialog said 1 target committed and to use Undo once | PASS |
| 10 | Target-1 Undo valid | `harness_undo_snapshot.json` (00:18:38) `undo_restored_pre_fit: true`; operator visual check at C10 | PASS |
| 11 | Scope rebuilt under G2 | operation end; stale rebuild scheduled, then rebuild; automatic Select Model with `PROD_PROVIDER_HEALTH … sha256=54413b6c…`; P3 (seq 55): same window, scope `54413b6ca618`, 0/0/0 | PASS |
| 12 | Later new Fit under G2 (wording corrected at closeout) | generation 3: authorized `54413b6c…`; stage open index 0 `gfit=54413b6c…`; released ok; `CLOTHING_FIT_STAGE=SKIP … "has no established compatible Body mappings."`; `CLOTHING_FIT_RESULT=PASS … changed=0 … skipped=1 failed=0 unattempted=0`. This proves G2 authorization and stage, but not a G2 **commit**; that is carried by S3_ADD | PASS (begin); commit → S3_ADD |
| 13 | No lease across queued stages | every stage open is followed by `RELEASED ok=True`; P2–P4 (seq 54–56) and the pause record are 0/0/0. P5 was not taken; idle-after-G2-Fit → S3_ADD | PASS (P2–P4); P5 → S3_ADD |
| 14 | Exact restoration, no residue | `finalization_record` and `restore_compare` `exact_match: true`; `deploy_after_removal.txt` == `deploy_before_harness.txt` | PASS |

Probes: P1 = seq 53 (no window), P2 = 54 (scope `ac45e5c1cd45`), P3 = 55 (`54413b6ca618`),
P4 = 56 (`54413b6ca618`). Every P2–P4 record has broker leases 0, unreleased 0, open providers 0,
one window and one watcher.

**Adjudication:** CORE PASS. The interruption, deferral, Gfit refusal, truthful stop, G2 rebuild
and target-1 Undo are proven. The fresh G2 commit and the idle check after it were left to the
addendum.

## 2. Addendum S3_ADD — fresh Clothing Fit committing under G2

Process pid 2324 (a fresh SFM process); CPM run `20261006-010820-pid2324`; broker `0x31419270`;
window `0xb92d1c60`. Fit generation 2, operation 3: `assaultsuitbody1` only.

| # | Criterion (§10.4) | Evidence | Result |
|---|---|---|---|
| 1 | Exact G2 before SFM | `g2_activation_record` `success: true`, wall time 01:03:42, `ac45e5c1…` → `54413b6c…`; `post_switch_inventory` (01:03:43) Master `54413b6c…`, manifest `9da5057f…`, sidecars `bcd97641…` + `cd370f67…`. The process's first CPM log line is at 01:08:20 | PASS |
| 2 | G2 scope at P2 | 01:08:43 `PROD_PROVIDER_HEALTH status=u'healthy' … sha256=u'54413b6c…'` for `krystal20201`; P2 (seq 58, 01:09:57) scope `54413b6ca618`, 0/0/0 | PASS |
| 3 | G2 authorization | 01:10:14.526 `PROD_CPM_OPERATION_AUTHORIZED operation=u'Clothing Fit' sha256=54413b6c… kind=u'body' membership=26`; `CLOTHING_FIT_START generation=2` selected = [`assaultsuitbody1`] | PASS |
| 4 | G2 stage | 01:10:16.735 `PROD_CPM_FIT_STAGE_OPEN index=0 gfit=54413b6c… literals=34` | PASS |
| 5 | Native commit | 01:10:16.750 `PROD_OPERATION_PHASE id=3 phase=u'native-commit'` for `assaultsuitbody1` | PASS |
| 6 | Committed-verified | 01:10:16.789 `CLOTHING_FIT_STAGE=PASS generation=2 index=0 … phase=u'committed-verified' mappings=26 warnings=7 committed=True` | PASS |
| 7 | Released | 01:10:16.789 `PROD_CPM_FIT_STAGE_RELEASED index=0 ok=True` | PASS |
| 8 | Result | 01:10:16.848 `CLOTHING_FIT_RESULT=PASS generation=2 selected=1 changed=1 already_matched=0 partial=1 partial_changed=1 partial_already_matched=0 skipped=0 failed=0 unattempted=0`; operator status "1 item updated."; no stop dialog, warning or error | PASS |
| 9 | Idle authority | P2 (seq 58), P3 (59, 01:11:14) and P4 (60, 01:11:27): broker before and after 0 leases / 0 unreleased / 0 open providers; window `0xb92d1c60`, one top-level CPM window, one watcher; scope `54413b6ca618` | PASS |
| 10 | Undo | D6: one Edit → Undo, visually restored (operator) | PASS |
| 11 | Exact G1 restoration | `finalization_record` (01:11:39) `exact_match: true`, G2 sidecar removed, Master restored; `restore_compare` `exact_match: true`, no sidecar added, changed or removed; `restored_inventory` (01:11:50) Master `ac45e5c1…`, manifest `d810d648…`, one sidecar `bcd97641…` | PASS |

Probes: P1 = seq 57 (01:08:09, no CPM window). `r15_harness.enabled` is false in every S3_ADD probe.

**Procedural observation (not a criterion):** CPM was first opened at 01:08:20 while the start-up
scene was still loaded (Refresh Models listed 2 unrelated models). It was closed at 01:08:35
(`PROD_CLOSE_REQUEST operation=None fit_active=False`; provider `open_count 0`) with no Select Model,
authorization or stage. It was then reopened at 01:08:38 on the Krystal scene. No authority was
used before the reopen, so this does not affect any criterion.

**Adjudication:** S3_ADD PASS. CPM was closed at 01:11:34 with `fit_active=False` and
`fit_stage_running=False`.

## 3. Session 3 result

Session 3 (handoff §21, Clothing Fit generation transition) is **PASS**:
- a queued Fit stops truthfully at a generation change, and target 2 never mutates (S3);
- target 1's Undo stays valid (S3);
- a later, user-initiated Fit commits under G2, and authority is idle afterwards (S3_ADD);
- the live authority is restored to exact G1 after each campaign.

Not covered (out of scope): forced Apply and Fit rollback-verification failure.
