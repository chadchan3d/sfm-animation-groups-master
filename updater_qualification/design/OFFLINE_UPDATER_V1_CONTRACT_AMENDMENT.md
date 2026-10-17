# SFM Character Tools Updater — Offline Updater v1 Contract Amendment

**Status: APPROVED by the owner on 2026-10-16. This is a superseding owner decision for the offline v1 release.** It supersedes specific provisions of the
Updater Blueprint R2 and of the owner decision of 2026-10-12, but only for the first release (v1). Every
superseded obligation is **removed from the v1 critical path**. None of them is recorded as passed.

**Date:** 2026-10-16. **Repository checkpoint:** `27aa6727902e674641ce8ea637a81058b2d5640b`.

**Prepared by:** Claude Code, as a documentation and planning assignment. The decision belongs to the owner,
ChadChan3D.

## 0. Basis and precedence

| Document | SHA-256 | Effect of this amendment |
|---|---|---|
| `cpm/qualification/R15_IMPLEMENTATION_BLUEPRINT.md` | `f6b3580cab9290564682b4a87b6c060de081566b462cd818bc1162c71c64d358` | **Unchanged.** Still frozen. |
| `updater_qualification/design/SFM_Character_Tools_Updater_Blueprint_R2.md` | `61cf8ed56668142132cef37806f56165d4f7371273215e5301b2f2b8200341bb` | Byte-preserved. Superseded only where §3 says so. |
| `updater_qualification/design/OWNER_DECISION_2026-10-12.md` (GitHub copy) | `bc5d87c9bdfc00e1d1a7de9fc107ca0b8a0b004128d37de4447b94fdfd6f81f1` | Byte-preserved. A1, A2 and A4, and the "not waived" lines, are superseded for v1 (§3.2). |
| `updater_qualification/design/SFM_Updater_Final_Architectural_Ruling_2026-10-12.md` (sanitized) | `d63b886b07224230f9271d8c63f9a2beb556aaee00981cc073e8d2ebd28c2e3c` | Recommendation record. Its §6 P2/P3 gates are removed from the v1 path (§3.3). |
| `cpm/qualification/CPM_CONVERGENCE_LEDGER.md` | `9a564b6e89d0c1cecd76010056086ef769348d8405d6ea5cf27c9023aa272317` | Updated in this checkpoint, as §8 specifies. |
| `updater_qualification/u0a/U0A_WINDOWS_ACTIVATION_FEASIBILITY_REPORT.md` | `3336e7aa84ac5bb5418deb6b072f450b17543d0ef0851f832c1b2470bbd6f779` | Evidence. Unchanged. |
| U0B-P0 report (private evidence) | `7f3b26e2672af6101ffc7d7d1b8a33fd31daeb906adcd2b120f61044c6fe8a14` | Evidence. Unchanged. |
| U0B-P1 report (private evidence) | `bb91b373e89a097187140587583adc115924bfca23006f3b97e25cdf63e62c6f` | Evidence. Unchanged. |
| Astra P2 necessity and design adjudication, 2026-10-16 (owner-supplied) | `0807bea8c1db78e62375823e252ed16ffaf31958d47cec69c437d2c6a0648995` | Input. Its §7 residual risks are carried into §5 below. |
| U0B-P2 final focused correction A–C report (private evidence) | `5274d85e1f70f3ee3f9c12987ff263bbe073092b74eeb762a3fba985083d4a70` | Verdict BLOCKED. Its findings remain unresolved. They are no longer required by the v1 contract (§3.4). |

**Not reproduced here:** the owner's authorization cites Astra's October 16 proportionality review as the
basis for the offline direction. This amendment implements that direction and does not restate that review.

**Precedence after approval:**
1. R15 Blueprint.
2. This amendment, for v1.
3. R2, for everything not superseded here.
4. The 2026-10-12 owner decision, as narrowed by this amendment.
5. The ruling and the audits, as evidence and recommendations.

## 1. Decision in one paragraph

v1 is an **offline updater**: it installs data only while SFM is closed. It does not try to be safe against a
concurrently running SFM. Instead it:
- refuses to install when SFM is running or its process state cannot be determined;
- tells the user to keep SFM closed until the updater finishes;
- states the unsupported overlap as an explicit limitation.

Because of this, the P2/P3 native-concurrency program and the WPR/ETW observation work no longer gate v1. Two
further substitutions follow:
- **Durability:** ordinary process-interruption and recovery qualification replaces mandatory physical
  hard-reset testing.
- **Accounts:** v1 is qualified for a single Windows account. The physical installation lock and the
  access-denied refusal are retained.

These changes alter **what must be qualified** before v1 ships. They do **not** alter how installation is
performed. The following are unchanged:
- the protected activation and recovery mechanism (R2 C4–C9 and C12, substantively unchanged);
- package authenticity (D) and compatibility (E);
- the R15 and K results and the installed consumer architecture.

The changed qualification standard gives no permission to implement a weaker installation mechanism (§4).

**Owner decision recorded here:** v1 has **three equally prominent primary buttons**: **Get Official Data**,
**Rebuild My Data** and **Use Another TXT**. All three are first-class v1 workflows, and their labels have no
ellipses. All three converge on the same validated, protected installed-publication backend. This supersedes
R2's two-primary-button limitation.

## 2. Offline v1 operating contract

### 2.1 Supported workflow and primary actions

| Step | User-visible action | Contract |
|---|---|---|
| 1 | Save work and close SFM. | The updater's first screen says this. It is a precondition the updater enforces at step 6, not one it assumes. |
| 2 | Open the updater. | It is a standalone application. It has no launch interceptor, service, startup task, runtime handshake or background polling. |
| 3 | Choose one of the three actions. | **Get Official Data**, **Rebuild My Data** or **Use Another TXT**: three equally prominent primary buttons with no ellipses. An unfinished transaction replaces them with one recovery action (R2 §F Recovery, C12). |
| 4 | Prepare and validate the candidate. | All expensive preparation happens here (R2 C3, C7.1–C7.4). It **may run while SFM runs**, because it writes only to updater-private staging and cannot modify the effective Master path or `sfm_shared_authority`. |
| 5 | Obtain consent where required. | The updater shows the intended destination and what will be kept. Replacing a modified or unrecognized TXT, or any Use Another TXT installation, requires explicit consent (R2 C3, C7.5, §F). Consent binds to the observed destination generation. A declined replacement changes nothing. |
| 6 | Perform the protected installation while SFM is closed. | Process gate (A3) → installation lock (C4) → process gate again → protection (C7.6–C7.9) → journaled moves (C8) → final verification through held handles → release. **RUNNING or UNKNOWN at either gate refuses before any protection or move:** "Close SFM and try again. Nothing was changed." |
| 7 | Verify the installed result and tell the user to reopen SFM. | After releasing the handles, re-open the files by path and verify the TXT/SIDECAR correspondence: the effective Master bytes equal the installed source; exactly one active sidecar exists; its embedded source hash and the manifest bind that Master; the sidecar passes reader self-validation and FINAL R3-A2B admission; and the consumer read paths are within the budget of §2.3. A failure is reported truthfully, never as success. The success report names the installed data, its provenance and where the previous files were kept. Provenance is "official [version]", "locally rebuilt" or "installed from another TXT". If the process status is no longer CLEAR at this point, the report says so and requires a restart of SFM before use; it does not retract the verified installation. |

**The three primary actions.** All three use the same canonical compiler and validator, the same consent rules
and the same protected backend. None has its own publication path.

- **Get Official Data.**
  - Obtains authenticated official data (R2 D) and validates its compatibility (R2 E).
  - Installs the matching official TXT/SIDECAR pair through the backend. The official sidecar is never combined
    with unrelated TXT bytes (R2 C3).
  - Preserves customizations: replacing a modified or unrecognized TXT requires informed consent, and the
    previous TXT and authority are kept in the transaction's recovery storage.
- **Rebuild My Data.**
  - Reads the currently installed Master TXT, including user customizations, as a captured snapshot.
  - Compiles its sidecar with the canonical compiler (generic acceptance, not the official policy), then
    validates and installs it.
  - The TXT is **not moved or rewritten** (R2 C3, C8 `M0 == M1`). An already-matching installation is a
    verified no-op.
  - This is the normal workflow for users who edit their animation groups.
- **Use Another TXT.**
  - The user selects a Master TXT anywhere on the computer. The updater captures an immutable copy of it, then
    compiles and validates the pair.
  - It shows the intended destination and obtains explicit replacement consent (R2 §F Import and C3).
  - It installs through the backend's replacement route. The previously installed Master TXT and its
    associated data are preserved in the transaction's recovery storage (C8 and C12).
  - The external source file is **never modified**. After confirmation, the captured copy, not a re-read file,
    is what gets installed. A change before confirmation requires a new preview.

### 2.2 Explicitly not provided in v1

- Hot updating, live updating, seamless runtime reload, a launch interceptor, a background service, a runtime
  handshake or automatic runtime refresh.
- Any guarantee of coherent native SFM operation for an SFM process started during step 6 or before step 7
  completes. That launch is **unsupported**, and the user is told not to start SFM until the updater reports
  completion.
- Coordination with a second Windows account.
- Power-loss or cache-loss persistence guarantees.

### 2.3 Support boundary (replaces R2 C1)

v1 supports the following:
- **Platform:** the Windows versions listed at release.
- **Storage:** local NTFS, with the installation and transaction storage on the same volume.
- **Master resolution:** the standard qualified `usermod` Master resolution.
- **Account:** one Windows account performs all updater operations for an installation.
- **SFM state:** SFM and both Character Tools are closed from step 6 through step 7.
- **Other writers:** no software installation or update is running in parallel, and there is no simultaneous
  third-party or legacy-publisher writer to the managed paths.
- **Links:** no reparse points or hard links in the managed slots. Installation aliases resolve to one verified
  physical target.

The following refuse:
- an unknown configuration;
- an unknown transaction schema;
- unfamiliar authority content;
- an access-denied lock, or any ambiguous installation-lock ownership state (there is no per-user substitute
  lock);
- RUNNING or UNKNOWN process status;
- any consumer read path (effective Master or active sidecar) of 260 characters or more. This is the P1-F1
  finding. The Master threshold was not separately measured, so the same conservative bound applies to both.

No elevation is used to force access.

## 3. Superseded provisions

### 3.1 Updater Blueprint R2

| R2 provision | Current text (summary) | v1 replacement | Status of the replaced obligation |
|---|---|---|---|
| **B**, "The two primary actions remain" | Get Official Data and Rebuild My Data. | **Three equally prominent primary actions**, adding Use Another TXT (owner decision, §1 and §2.1). The architecture diagram is unchanged: all three feed one compiler and validator, then one backend. | Superseded by owner decision. |
| **C1** support boundary | Includes "SFM closed before activation". Has no account clause and no preparation/installation split. | §2.3 above. Adds the single-account clause, the closed window from step 6 through step 7, the A3 refusal, the ambiguous-ownership refusal and the consumer path budget. | Narrowed scope. Not a qualification result. |
| **C10**, final paragraph | "Hard-reset testing is required…" | Qualify **ordinary process interruption**: kill the worker or GUI at every journaled boundary and during recovery, then recover twice. Constructed inconsistent states are tested as **recovery-logic** cases only. Checked writes, `FlushFileBuffers`, retained originals and post-restart revalidation stay mandatory. **Power/cache-loss persistence: unqualified, and no claim is made.** | Hard-reset campaign **removed from the v1 critical path. NOT PASSED. Not performed.** The rest of C10 is retained. |
| **C11**, rows 2–4 (SFM starts after the check, between the check and protection, or during moves) | Bounded fail-closed behavior; exact behavior "requires qualification". | **Unsupported condition.** The two process gates refuse RUNNING/UNKNOWN, but they do not prevent a later launch. The held share-0 handles and the existing consumer guards are incidental mitigations. The library-level behavior was observed in P1 I1–I2; the native behavior is not claimed. The user is instructed not to start SFM, and step 7 reports a status change it detects. | Live-overlap qualification **removed from the v1 critical path. NOT PASSED.** |
| **C11**, row 1 | Refuse if SFM is already running. | Retained. It is strengthened by A3: UNKNOWN also refuses, and it is checked at both gates and before recovery. | Retained. |
| **C11**, row 5 | No forcible revocation of detached authority. | Retained as a statement of non-promise. Under the v1 boundary, no consumer is running. | Retained. |
| **C11**, Limits bullets 3–4 | "Unexpected launch must be qualified…"; "If that test exposes unsafe native behavior, shipping is blocked." | Replaced by the explicit limitation L-A (§5). The rule that "a runtime handshake or stronger exclusion requires separate scope approval" is retained. | **Removed from the v1 critical path. NOT PASSED.** |
| **§F Official update**, steps 5–6 | "Prepares everything before requesting SFM closure; activates and verifies." | The §2.1 seven-step workflow. Step 7 adds the correspondence check and the reopen instruction. | Clarified. |
| **§F Import** | An import action with consent and backup wording. | **Retained and made a primary v1 action, Use Another TXT** (§2.1). The label has no ellipsis. The R2 C3 capture and consent rules are unchanged. | Retained and strengthened by owner decision. |
| **§F Minimal interface retained**, "Two primary buttons" | Two primary buttons, an installation selector, occasional confirmation, progress and Details. | **Three equally prominent primary buttons**, with the rest unchanged. There is still no background polling, persistent warning panel, automatic merging or maintenance dashboard. | Superseded by owner decision. |
| **G**, "one publication owner" | Includes cross-user races. | The **alias and same-account races are retained as a blocker** (P1 F1–F5 mechanism). The cross-user part is replaced by the single-account boundary: the physical lock is retained, access-denied refuses, there is no per-user substitute lock, and cross-user behavior is UNKNOWN. | Cross-user part **removed from the v1 critical path. NOT PASSED.** |
| **G**, "safe suite concurrency" | Pause at every rename, launch SFM, exercise both consumers. | Replaced by the **offline activation and refusal** blocker: both gates refuse RUNNING and every UNKNOWN form before protection, using real detection of an actually running SFM. | **Removed from the v1 critical path. NOT PASSED.** |
| **G**, "power interruption" | VM hard resets. | Replaced by the process-crash recovery blocker (already in G) plus constructed-state recovery cases. | **Removed from the v1 critical path. NOT PASSED.** |
| **I**, Stage 0 | Primitive experiment plus a real-SFM concurrency test. | The primitive part is satisfied for the qualified scope by U0A (bounded PASS, 256/1/0) and P1 (bounded PASS, 130/130 on E:). The concurrency tests (unexpected launch, Normalizer and CPM overlap, cross-user contention) are removed. | Primitive part: evidence, bounded. Concurrency part: **removed, NOT PASSED.** |
| **I**, Stages 1–3 | Packaging/trust, backend and GUI, installed suite. | Replaced by the L-1 … L-6 plan in the L Implementation Authorization Card. | Restructured. Content retained. |
| **J1** | Authorize the prerequisite experiment. | Superseded as described for Stage 0 above. | Superseded. |
| **J2–J5** | Support boundary, signatures and key custody, failure policy, L roadmap. | Approved in §7, as amended here. | Approved 2026-10-16. |

**Unchanged in R2:**
- B: architecture, worker process and in-place authority directory, except the number of primary actions.
- C2–C9, substantively unchanged: layout, source selection, lock, supported publication paths, primitives,
  preparation and protection, transitions, expected failures.
- C10, except its final paragraph.
- C12, substantively unchanged: the recovery matrix and truthful messages.
- D: the five-file package, Ed25519, key custody, freshness and ordering, and deleted releases.
- E: profile, signed software inventory, and the limits of what can be established.
- F Rebuild and F Recovery, and the minimal interface apart from the button count.
- All other G rows, including authenticity, compatibility, confinement, portability and resource/UI containment.
- The one-active-sidecar disposition.
- H.

### 3.2 Owner decision 2026-10-12

| Provision | v1 replacement |
|---|---|
| **A1** "Direction approved, qualification waiver NOT approved… C11/G remains outstanding" | The live-concurrency **qualification obligation** is superseded within the narrower offline-v1 contract: it is replaced by the offline boundary (§3.1). This is a scope amendment, not a waiver presented as a PASS. Live concurrency remains **unqualified** (L-A). |
| **A2** "hard-reset waiver NOT approved" | The hard-reset/power-loss **qualification obligation** is superseded within the offline-v1 contract by the C10 substitution (§3.1), which Astra's ruling A2 recommended. No hard reset is performed. Power-loss behavior remains **unqualified** (L-B). |
| **A3** | **Retained unchanged.** |
| **A4** "DEFERRED… no single-account restriction or cross-user waiver is approved" | The single-account qualification boundary is approved for v1, as the ruling's A4 fallback describes. The physical lock, alias resolution and access-denied refusal are retained. Cross-user behavior is UNKNOWN. |
| `publisher.lock` direction; N1-first rejection; U0A tally | **Retained unchanged.** N1-first and all hazardous native experiments remain unauthorized. |
| "On HOLD": U0B real-SFM qualification, hazardous faults, power loss, cross-user, release | Hazardous faults, power loss and cross-user are removed from v1 and become limitations (§5). U0B real-SFM qualification of live overlap is removed. Real-SFM use **with SFM closed during installation** is qualified in L-6, group 5. Release still requires L-6. |
| "P2 ordinary SFM launch and P3 hazard cases each require a separate authorization" | P2 and P3 are removed from the v1 critical path. Any future P2/P3 work requires a new decision naming the release decision it affects (§6). |
| "R2's original C10/G hard-reset and C11/G concurrency blockers are **not waived**" | They are superseded **for v1** by §3.1. They are not passed. They are restated as limitations L-A and L-B. A product promise of live-overlap safety or power-loss preservation would revive them. |
| "L … NOT STARTED. No updater or packaging implementation is approved here." | L becomes authorizable by increment (see the L card). L-1 is ready for authorization. It is **not authorized and not started** by this document. |

**Scope of the A1/A2 supersession.** Only the two **qualification obligations** change. Neither A1 nor A2 is
permission to implement a weaker installation mechanism. Every filesystem protection listed in §4 is mandatory
in v1, exactly as it would have been under the original A1/A2 wording.

### 3.3 Ruling 2026-10-12 §6 qualification plan

The P0 and P1 rows are retained as completed bounded evidence. The **P2** (passive ordinary-SFM
characterization) and **P3** (unresolved native/concurrency boundaries) rows are removed from the v1 path. The
**L final candidate** row is retained, and its "owner-approved qualification/support boundary" is this
amendment.

### 3.4 Qualification dispositions (effective on approval, 2026-10-16)

| Item | Disposition |
|---|---|
| U0B-P2 (passive ordinary-SFM characterization: the R1/R2 observation cards, preparation P-1 to P-5 including the C1 correction, the BST DMX oracle) | Removed from the offline-v1 critical path. **NOT PASSED.** |
| Broad U0B-P3 native-concurrency testing | Removed from the offline-v1 critical path. **NOT PASSED. Not started.** |
| WPR/ETW recorder and storage-accounting development | **Discontinued, not completed.** |
| P2 recorder/comparator final correction A–C findings (BLOCKED) | **Unresolved**, and no longer required by the v1 qualification contract. |
| Hard-power-loss behavior | **Unqualified** (L-B). |
| Unexpected native SFM overlap | **Unqualified** (L-A). |
| Cross-user contention | **Unqualified** (L-C). |

All of this evidence is preserved unchanged as private evidence. It is not used to support any v1 claim.

## 4. Retained safeguards (the installation mechanism is not weakened)

These protections are mandatory for all three primary actions and for recovery. R2 C6–C9 and C12 remain
substantively unchanged.

- **Protected source identity and exact-source binding:** the captured source bytes are revalidated through held
  handles. The installed sidecar and manifest bind exactly those bytes (C3, C7).
- **No-clobber file moves:** a handle-based rename with `ReplaceIfExists=FALSE`; nothing is overwritten (C6).
- **The approved activation move order** (C8).
- **Protection handles held through final verification**, and released before success is reported (C7, C8).
- **Preservation of original and customized data:** old files are moved to recovery storage, never deleted or
  overwritten. External sources are never modified (C3, C8).
- **Checked writes and flushing** (`CREATE_NEW`, complete-write checks, `FlushFileBuffers`) (C6, C10).
- **Transaction journaling** before each move (C8, C12).
- **Conservative evidence-based recovery** (C12).
- **Refusal on unexpected occupants or incompatible state** (C9, C12, E).
- **Verification of the actual installed TXT/SIDECAR relationship** (§2.1 step 7).
- **Truthful failure and success reporting** (C9, C12, §F).

In detail:

- **C4:** one physical installation lock (share 0, `OPEN_ALWAYS`, non-inheritable). Ownership is the live
  handle. Access-denied or ambiguous ownership refuses. There is no per-user substitute lock.
- **C5:** all installed writes go through the one backend. `publisher.py`, `mutex_publisher.py` and the compiler
  CLI remain export and development tools only. A recognized legacy `publisher.lock` is preserved and held
  during protection. A held or unrecognized one refuses. This is the P1 G1–G9 mechanism.
- **C6:** `CREATE_NEW`; protection with share 0; `FileRenameInfo` with `ReplaceIfExists=FALSE`;
  `FlushFileBuffers`. Not used: `REPLACE_EXISTING`, a cross-volume fallback, delete-on-close or delayed moves.
- **C7–C8:** prepare, then protect, then revalidate through the held handles. Use the original move order.
  Journal before each move, never delete or overwrite, and hold the handles through final verification.
- **C9:** expected-failure handling. Unknown errors are never translated into "nothing changed".
- **C12:** evidence-based recovery from verified disk state:
  - newer user edits are preserved as CONFLICT;
  - recovery is idempotent;
  - an interrupted rollback is reconciled;
  - stale restoration is reported as stale;
  - an unknown schema is not mutated.
- **Package authenticity (D):**
  - the five-file package;
  - Ed25519 over the exact `release.json` bytes;
  - only embedded trusted keys;
  - key custody outside the repository;
  - the sequence high-water mark;
  - no false "latest" claim.
- **Compatibility (E):** a signed software inventory plus an authority profile. Runtime API `1.0.0-b2a` and
  build `package-boundary-corrected-2026-09-22` are checked exactly. The updater's success is never presented
  as proof of embedded-SFM headroom.
- **Release qualification:** L-6 (§6) is mandatory before release.
- **Unchanged:**
  - R15 Blueprint and K;
  - the installed CPM `4e35f292…`;
  - the production Normalizer `1f4ec5a2…`;
  - the production authority package;
  - the selector's source-hash rule;
  - the Normalizer's `native_master_protect_acquire` interlock;
  - CPM operation-time generation authorization.

## 5. Explicit v1 limitations (residual risks)

| ID | Limitation | Mitigation retained | Evidence status |
|---|---|---|---|
| **L-A** | **Unexpected native overlap.** SFM, or a Character Tools operation, is started by the user or another program after the final process gate and before step 7 completes. | Two A3 gates; share-0 protection of the Master and sidecars, under which consumers see MasterUnreadable/SidecarMissing at library level (P1 I1–I2); the Normalizer interlock (a held Master handle blocks protection and the updater abandons; P1 I2); CPM generation authorization; a post-install status recheck; user instruction. | Native SFM behavior in this window: **UNKNOWN, unsupported**. No claim that native SFM, or either tool's UI, refuses safely. P1-F2 (busy reported as "missing") still applies. |
| **L-B** | **Power or cache loss** during installation or recovery. | Flushes, retained originals and snapshots, post-restart revalidation, refusal on ambiguous states. | **Unqualified.** No hard reset was performed. The constructed-state tests qualify recovery logic only. There is no guarantee that originals or backups survive storage loss. |
| **L-C** | **Cross-user contention.** A second Windows account runs a writer against the same installation. | The physical lock is the same file for all accounts; access-denied refuses; there is no per-user lock. | **UNKNOWN.** Excluded from v1 support. Single-account use is not enforced by the software. |
| **L-D** | **Non-participating writers.** Legacy CLI publishing, editors or third-party tools change managed files outside the protocol. | Exact inventory checks, identity checks, refusal and preservation. | Detection only. No exclusion of nonparticipants (R2 C5). |
| **L-E** | **Release freshness.** A first-contact client, or an old/offline one, cannot detect suppression or replay of releases (R2 D4). | High-water mark; no "globally newest" claim. | Accepted limitation from R2. |
| **L-F** | **Detection timing.** The process checks do not positively prevent SFM from launching after a check (ruling A3). | Two gates plus the post-install recheck. | Inherent. Stated in the UI and the documentation. |

**Accepted residual risks.** Approving this amendment accepts L-A to L-F as the residual risks of v1. It also
accepts the narrower supported product contract: an offline updater, used by one Windows account, with SFM
closed during installation. Nothing outside that contract is claimed as supported or qualified.

## 6. v1 qualification standard

The release requires **all five groups** of the L card's §6 to PASS on the exact shipping candidate. Each group
covers all three primary actions.
1. candidate and package acceptance;
2. offline activation and refusal;
3. preservation and interrupted-operation recovery;
4. failure containment and truthful reporting;
5. final installed-product qualification with both SFM tools.

Prior U0A/P1 evidence is reused only for mechanisms shown to be equivalent. The equivalence is established by
re-running the ported P1 case suite against the product backend.

**Rule for additional qualification:** an additional qualification step may be added only by an owner-approved
card that names:
- (a) a concrete unresolved risk;
- (b) the specific release decision it changes;
- (c) the smallest test that decides it.

A general native-tracing campaign, a WPR/ETW development effort or a new DMX-oracle campaign does not meet this
rule for v1.

## 7. Owner decisions (approved 2026-10-16)

The owner approved each item:

1. The offline v1 operating contract and support boundary (§2). The three primary buttons are already an owner
   decision and are recorded in §1 and §2.1.
2. The supersession of R2 C1, C10 (final paragraph), C11 (rows 2–4 and limits 3–4), the G rows named in §3.1,
   Stage 0 and J1, as specified in §3.1.
3. The supersession of owner decision A1, A2 and A4 and of the "not waived" lines, as specified in §3.2, and the
   removal of P2/P3 from the v1 path (§3.3–3.4).
4. The limitations L-A to L-F (§5), which become the published v1 limitations.
5. The R2 J2–J5 items as amended:
   - J2 is §2.3.
   - J3 is approved unchanged: Ed25519 signatures and key custody with the stated revocation limits.
   - J4 is approved unchanged: a preserved conflict or a stale restoration is an acceptable truthful outcome.
   - J5 is the L-1 … L-6 roadmap in the L card.
6. The v1 qualification standard and the additional-qualification rule (§6).
7. The Ledger transition (§8). L-1 (L card §8) is ready for authorization. Its actual authorization is a
   separate owner act after the documentation checkpoint.

**On approval (done in this checkpoint):** commit this amendment and the L card as a documentation-only checkpoint under
`updater_qualification/design/`, add both to `updater_qualification/SHA256SUMS.txt`, and apply the §8 Ledger
transition. R2, the 2026-10-12 owner decision and the ruling stay byte-preserved.

## 8. Ledger transition (deliverable C)

**Approved 2026-10-16 and applied to the Ledger in this checkpoint.** It replaces the Ledger's "Current milestone" header, the
"Unresolved" U0B and U0A items, and the "Next" section with the following. It records
only the state that is true when the Ledger is edited.

**Current milestone:**
- **Offline Updater v1 Contract Amendment: APPROVED 2026-10-16**
  (`updater_qualification/design/OFFLINE_UPDATER_V1_CONTRACT_AMENDMENT.md`; SHA-256 in
  `updater_qualification/SHA256SUMS.txt`).
- **L Implementation Authorization Card: APPROVED 2026-10-16.**
- **L-1 (activation backend and Rebuild My Data, headless): READY FOR AUTHORIZATION / NOT STARTED.** Change
  this to "AUTHORIZED / NOT STARTED" only when the owner actually authorizes L-1.

**Status lines:**
- **U0A:** PASS (bounded), 256 PASS / 1 NOT RUN / 0 FAIL. Unchanged.
- **U0B-P0:** technical PASS (bounded). Unchanged.
- **U0B-P1:** COMPLETE / PASS (bounded). Unchanged.
- The Amendment is approved, so the following apply:
  - **U0B-P2:** REMOVED FROM THE OFFLINE-v1 CRITICAL PATH (owner amendment 2026-10-16). **NOT PASSED.**
    - The preparation evidence is retained privately, unchanged.
    - The final recorder/comparator correction A–C (BLOCKED): findings unresolved, and no longer required by the
      v1 qualification contract.
    - WPR/ETW development: discontinued, not completed.
    - No native observation was performed.
  - **U0B-P3 (broad native concurrency):** REMOVED FROM THE OFFLINE-v1 CRITICAL PATH. **NOT PASSED. Not
    started.**
  - **U0B, for v1:** closed at the P1 evidence boundary. Unexpected native SFM overlap, hard-power-loss
    behavior and cross-user contention remain **unqualified**. They are published as v1 limitations L-A, L-B
    and L-C, not recorded as PASS or as waivers.
- **v1 interface:** three primary actions: Get Official Data, Rebuild My Data and Use Another TXT (owner
  decision).
- **L:** L-1 READY FOR AUTHORIZATION / NOT STARTED. L-2 … L-6 NOT STARTED; each requires its own authorization.
- **K:** COMPLETE / PASS. R15: frozen. Installed CPM `4e35f292…`, production Normalizer `1f4ec5a2…` and exact
  G1 authority: unchanged.

**Unresolved (replacing the U0A residuals and U0B boundaries for v1):**
- **v1 limitations, published and not qualified:**
  - L-A: unexpected native overlap;
  - L-B: power/cache-loss persistence;
  - L-C: cross-user contention;
  - L-D: non-participating writers;
  - L-E: release freshness;
  - L-F: detection timing.
- **L design inputs carried forward:**
  - P1-F1: consumer path budget below 260 characters;
  - P1-F2: busy-versus-missing messaging. Only the updater's own messages are in L scope; consumer messaging is
    unchanged K/L product work.
  - P1-F3: authority-slot conflict messaging;
  - P1-F4: legacy-lock fail-closed behavior;
  - F4: `publisher.lock` preserve-and-recognize;
  - real running-SFM detection, to be qualified in L-6 group 2;
  - `intent_schema()` hardening.
- The remaining K/L residuals from R15 and the deferred UI findings are unchanged.

**Next:**
- Owner authorization of L-1. Execution begins only after that authorization.
- No native SFM run, WPR/ETW work, live installation write or release is authorized by this checkpoint.

## 9. Repository copy record

This repository copy was derived from the approved draft (SHA-256 `e07c3e10409e59f94b4204445a72c7df7737c72fee65e4b3f7226d3cb352fadf`). It differs only in two respects:
- the approval-status wording;
- the resolved `[PROPOSED | APPROVED]`, `[date]` and `[hash]` placeholders.

The owner approved it on 2026-10-16, through the designer's acceptance of the reconciled drafts. Its own SHA-256 is
listed in `updater_qualification/SHA256SUMS.txt`.
