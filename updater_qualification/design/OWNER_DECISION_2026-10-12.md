# SFM Character Tools Updater — Owner Design Decision, 2026-10-12

**Status:** APPROVED design adjudication and U0B-P0 authorization. **U0B-P0: NOT STARTED.**
**Evidence base:** GitHub `chadchan3d/sfm-animation-groups-master` at
`1a2bbd18066a670f56ad2d407c81d028eb1695a5` prior to this documentation checkpoint.

## Authoritative documents and precedence

1. Frozen `cpm/qualification/R15_IMPLEMENTATION_BLUEPRINT.md` governs existing product work; unchanged.
2. `updater_qualification/design/SFM_Character_Tools_Updater_Blueprint_R2.md` governs the updater protocol except where explicitly approved in this record. Original owner-supplied file SHA-256: `61cf8ed56668142132cef37806f56165d4f7371273215e5301b2f2b8200341bb`. The GitHub copy is byte-identical to that original.
3. `updater_qualification/design/SFM_Updater_Final_Architectural_Ruling_2026-10-12.md` is the final Astra architectural assimilation; original uploaded file SHA-256: `b985e8680690f492b8c4d1c51df9b36eb89710dbc90ef7fd6113c1d3afef2fb8`. The GitHub copy is a **sanitized derivative, not byte-identical** (see "Sanitization record" below).
4. This owner record distinguishes decisions from recommendations. Audits are evidence, not automatic approvals. The current committed Ledger is the progress checkpoint.

## Approved decisions

- **Retain R2 C6–C8 and C12 unchanged:** protected source identity, identity-bound no-clobber renames, original activation move order, held handles through final verification, and conservative evidence-based recovery. Reject Checkpoint I hash-then-overwrite and M-R2 tight as product replacements.
- **A1: Direction approved, qualification waiver NOT approved.** Use existing evidence and offline/static cases to reduce redundant live-concurrency experiments where defensible. The R2 C11/G safety requirement remains outstanding until an explicit review of evidence and any narrower release scope.
- **A2: Investigation approved, hard-reset waiver NOT approved.** Constructed inconsistent disk states qualify recovery logic, not actual power-loss persistence. Any revised first-release hard-reset requirement requires separate owner approval; no hard reset of this sole machine is authorized.
- **A3: APPROVED.** A process-status query must classify RUNNING/CLEAR/UNKNOWN; exceptions, nonzero exit, incomplete enumeration, or unparseable results are UNKNOWN and must refuse before activation. Test harness barriers must also be exact-token, fail-closed on EOF/bad token/timeout/controller failure.
- **A4: DEFERRED.** Cross-user contention remains unqualified; no single-account support restriction or cross-user waiver is approved. A temporary account/test requires separate authorization; do not create one as part of P0.
- **`publisher.lock`: approved design direction is preserve and recognize a verified legacy file in place**, with provenance and exact inventory checks. Neither name alone nor presence authorizes trusting an active writer. No migration/deletion or concurrent legacy publishing is approved; implementation details remain to qualify.
- **N1-first: REJECTED.** No deliberate native Master lock/absence, native fault injection or other hazardous experiment on the sole installation is authorized by this record.
- **U0B-P0: OWNER-AUTHORIZED, NOT STARTED.** The bounded read-only preflight in Astra's final ruling §7 may begin only as a separate next-window execution assignment after reconciliation with the then-current Ledger. It may read relevant installed files and metadata and prior evidence, but may not launch SFM, lock/move/write installed authority, compile, run tests, install tracing, change settings, or implement any code. Only P0 report/inventory files under the specified new Codex evidence folder are allowed to be written during P0.
- **U0A tally correction:** 256 PASS, 1 NOT RUN, 0 FAIL (257 recorded). Correct the Ledger and U0A report through an explicit documentation-only correction note; do not alter raw evidence, imply a retest, or change the bounded PASS verdict.

## Explicitly unresolved and still on HOLD

- U0B real-SFM qualification, hazardous native/concurrency faults, power-loss durability, cross-user contention and release remain unqualified.
- Future P1 scratch mutation, P2 ordinary SFM launch and P3 hazard cases each require a separate authorization; none is bundled with P0.
- L (installation/coexistence/release) NOT STARTED. No updater or packaging implementation is approved here.
- R2's original C10/G hard-reset and C11/G concurrency blockers are **not waived**.

## Required checkpoint and handoff

Commit the byte-preserved R2 original, the sanitized derivative of the ruling, this decision record, and any audit preserved as evidence (sanitized as recorded below). Reconcile the current GitHub HEAD before editing; update `cpm/qualification/CPM_CONVERGENCE_LEDGER.md` to point to this approved decision and state **U0B-P0 authorized / NOT STARTED**. Correct the U0A tally in the Ledger and report with a correction-history note, not a fictional new run. Push and verify the remote commit, then pass the **actual commit SHA and file paths** to the new designer. Do not begin P0 while completing this documentation checkpoint.

## Sanitization record (owner-approved Option 2, 2026-10-12)

The repository's sanitation rule forbids workstation paths and personal names other than ChadChan3D. The owner approved targeted redaction of exactly two strings. Each copy differs from its original only on the line shown; all other bytes and formatting are preserved. The removed strings are deliberately not reproduced here.

| GitHub copy | Line | Redaction | Original SHA-256 (provenance) | GitHub copy SHA-256 |
|---|---|---|---|---|
| `updater_qualification/design/SFM_Character_Tools_Updater_Blueprint_R2.md` | — | none; byte-identical, CRLF kept (`.gitattributes` `-text`) | `61cf8ed56668142132cef37806f56165d4f7371273215e5301b2f2b8200341bb` | `61cf8ed56668142132cef37806f56165d4f7371273215e5301b2f2b8200341bb` |
| `updater_qualification/design/SFM_Updater_Final_Architectural_Ruling_2026-10-12.md` | 213 | a backtick-quoted absolute workstation path (32 bytes) → `the operator's approved local Codex evidence directory, outside the repository` | `b985e8680690f492b8c4d1c51df9b36eb89710dbc90ef7fd6113c1d3afef2fb8` | `d63b886b07224230f9271d8c63f9a2beb556aaee00981cc073e8d2ebd28c2e3c` |
| `updater_qualification/reviews/U0B_Independent_Adversarial_Audit_R2_Reconciled.md` | 3 | an `@`-mention of a personal name (14 bytes) → `@OWNER` | `7c552f745b5d36d6f587a2ce31f7b8becab2693b43c32a053f3d4dd76a1b2112` | `c5ab370cda9aacecd2acba265f8bfd58881724d47b594f47d66239aa26fb2f30` |

The P0 requirement is unchanged: P0 writes only the report and inventory, into one new evidence folder under the operator's approved local Codex evidence directory, outside the repository. No new absolute path is defined here.

This record was supplied with SHA-256 `0a83ab0375ed9e5ae0308075a06c3f5573e50ac0bb9c40a4ae16f4e6f41cc67a`. Its GitHub copy additionally contains the byte-identity notes in items 2–3, the adjusted checkpoint sentence, and this section. `updater_qualification/SHA256SUMS.txt` lists the SHA-256 of every committed copy (paths relative to the repository root).
