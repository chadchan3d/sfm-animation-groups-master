# U0B Independent Adversarial Audit — Revision 2 (reconciled with Updater Blueprint R2)

Oct 12, 2026 · @OWNER

## Bottom line and final recommendation

**Recommendation: retain R2's activation mechanism and move order (C6–C8) unchanged. Withdraw both of this reviewer's earlier alternatives. Amend R2's qualification methods, not its file protocol, so the remaining blockers can be met on one installation.**

R2 forbids `REPLACE_EXISTING` and POSIX replacement flags, and forbids weakening to hash-then-overwrite (C6). Under that rule, a missing-Master state after termination cannot be designed out: an occupied path can only be vacated and refilled, never swapped. The earlier Checkpoint I proposal broke R2's protected-source-identity blocker. The later "M-R2 tight" proposal turned out to add nothing for native safety, because R2 already moves the old and new Master back to back. It only made guarded tools available in more crash states, at the cost of new unqualified states.

The decisive open question is therefore not ordering. It is what native SFM does when it finds the Master **locked** or **absent**. Native Rebuild reads only the TXT, so those two static conditions are the only native-relevant states the protocol can produce. Both can be reproduced without timing races. R2 C11 makes unsafe native behavior a shipping blocker, and this audit keeps that blocker.

The next milestone is a static, two-condition native characterization on the owner's installation, with complete backups and a disposable session (N1). Its result decides between three paths:

- **Native fails safely:** R2's protocol stands; the residual is disclosed.
- **Native fails silently:** C6's prohibition on replace semantics must be reopened by Astra and the owner, trading a rare clobber risk against a rare silent-scene-damage risk.
- **Inconclusive:** HOLD.

Two R2 qualification requirements cannot be met as written without a VM or second machine: live launch races (C11, G "safe suite concurrency") and VM hard resets (C10, G "power interruption"). This audit proposes substitute methods with the same pass criteria. They are **amendments requiring Astra and owner approval**, not approvals in themselves.

No code was written, no test run, and no repository, Blueprint or Ledger file changed.

## Evidence basis and withdrawals

R2 was read in full. Its SHA-256, `61cf8ed5…341bb`, matches the hash recorded in the U0A report, so this is the exact design U0A tested. The repository was read at `1a2bbd18` through a read-only clone. Markers: **(R2)** stated in the Blueprint; **(repo)** checked in source or evidence; **(inference)** reviewer reasoning; **(proposal)** recommendation needing approval.

Repository facts this revision relies on:

- U0A's `make_plan()` implements R2 C8's order exactly: old sidecars, old manifest, old Master out; new Master, sidecar, manifest in. (repo)
- Each move is journaled `BEGIN`, renamed, then journaled `DONE`, with `FlushFileBuffers` on journal writes. Two flushed journal records therefore separate the old-Master retirement from the new-Master placement. (repo)
- Checkpoint I hashed the Master by path, closed it, then called `MoveFileExW(REPLACE_EXISTING)` with no handle held. (repo)
- The live authority folder contains `publisher.lock`. U0A case 6h shows R2's rules refuse it as unfamiliar. (repo)
- The legacy named mutex embeds the user's SID, as R2 C4 states. (repo)
- The writer has no time or random inputs, and the publisher reuses byte-identical generations; Checkpoint I's G1 republish reused the same artifact. (repo)
- The selector scans sorted `.sfmsidecar` names, returns the first whose embedded source hash matches, and never reads the manifest. The broker rereads the Master on every call, including warm-cache hits. (repo)

**Withdrawn from Revision 1 and the interim response:**

1. **Checkpoint I's `MoveFileExW` replacement** for user-facing use. It violates R2 C6 and fails R2 G's protected-source-identity blocker: an edit saved between hash and replace is silently overwritten.
2. **M-R2 tight**, including early release of the new Master's handle. Matters 1 and 2 below explain why.
3. **"R2 brought the hazard back."** R2 traded a missing-Master window for identity protection on purpose. That trade is defensible.
4. **"The residual race lasts one rename."** The live unreadable interval runs from protection to release. It includes every rename, every flushed journal record and two full hash passes. It is unmeasured, not milliseconds by assumption.
5. **Release-test list T1–T9 as sufficient.** It omitted R2 G blockers (editor race, path confinement, lock ownership, complete recovery evidence) and treated R2's shipping blockers as optional. It is replaced by the qualification section below.

## Architecture comparison

Only R2's own mechanism satisfies both R2's no-clobber blocker and its protected-source-identity blocker. Every never-absent alternative gives up one of them.

| Mechanism | Missing Master after termination? | Concurrent edit protection | Native view during live activation | R2 compatibility | Verdict |
| --- | --- | --- | --- | --- | --- |
| **R2 C6–C8** (identity-bound no-clobber renames, all handles held to final verification) | Yes: one state, between old-Master retirement and new-Master placement | Full while handles are held: writers, renamers and deleters refused; collisions preserved | Master locked (sharing violation) or absent, from protection to release | Native | **Recommended** |
| **Checkpoint I** (path hash, then `MoveFileExW` replace, no handle) | No | **None** between hash and replace: in-place and save-by-replace edits overwritten | Readable until the swap | Prohibited by C6 | **Rejected**: fails G identity blocker |
| **M-P** (hold old Master read with read and delete sharing, POSIX replace from candidate) | No | In-place writers refused. An editor that deletes or renames the Master and creates a new file in the window is overwritten (inference) | Readable until the swap (inference) | Prohibited by C6 | **Rejected for first release**; reconsider only if N1 shows harmful native behavior |
| **M-R2 tight** (prepublish new sidecar, R2 Master pair, early handle release) | Yes: the same single state as R2 | Weaker after early release (Matter 1) | Same as R2 until early release | Allowed primitives, new order | **Withdrawn** |
| **Prepublish order only** (M-R2 tight without early release) | Yes: the same single state | Same as R2 | Same as R2 | Allowed primitives, new order | **Optional hardening**, not first release |

Prepublishing the new sidecar changes only the guarded tools' post-crash view. Old-Master/no-sidecar and new-Master/no-sidecar states become selectable states. That is an availability gain, not a safety gain: guarded tools already refuse safely in those states (repo), and native Rebuild reads only the TXT, which is present and correct in both. The cost is new journal states needing fresh qualification, two sidecars in the scan root during the transaction, and for rebuilds a post-crash state where two artifacts match the same source. R2's order leaves that rebuild state honestly unavailable instead, which R2's one-active-artifact disposition prefers.

No primitive in the documented Windows API renames a file only if the destination still has a given file identity (reviewer's understanding of the documented API; to be confirmed in the scratch experiment). Without such a primitive, a path cannot be both continuously occupied and protected against substitution by another writer.

## Matter 1: early release of Master protection

**Rejected. Hold every protected handle, including the new Master's, until final verification and the completion record, as R2 C8 specifies.**

The interim proposal released the new Master's handle after placement, before the manifest pair and old-sidecar retirement. Its only benefit was that native SFM could read the new Master slightly earlier. The remaining steps are a few renames and flushed journal records, so the gain is a fraction of an unmeasured but short interval.

The costs are concrete:

- **A new mid-transaction state.** Once released, the Master can be edited, replaced or deleted while the updater still holds the manifest and old sidecar. No R2 C12 row describes "Master changed during live activation, after partial release." The nearest row, "TXT changed after crash," assumes the updater is no longer running.
- **Final verification can no longer prove the completed set.** R2's completion condition requires the effective Master, the sole sidecar and the manifest to agree. Once the Master is unprotected, any verification of it is a path read that can be stale the instant it returns. The updater could record COMPLETE for a set that no longer exists.
- **Journal consistency weakens.** The journal would contain a released-Master record followed by further moves. Recovery would have to treat the Master as user-owned partway through a transaction. That is a new direction rule needing new qualification.
- **No-lost-customization still holds, but only by refusal.** The updater never writes the Master path after placement, so an edit made in that window is not overwritten. But it strands the transaction: the user's edited TXT now sits beside a new sidecar and manifest it does not match. The honest outcome is a conflict the user must resolve. No bytes are lost, but a successful update has become a failed one for a benefit measured in milliseconds.

Holding all handles keeps R2's existing guarantee simple: during live activation, no ordinary process can change any managed file, and completion is recorded only for a set verified through the handles that protect it.

## Matter 2: crash and power-loss exposure

**Shortening the interval gains nothing here: R2 already places the old-Master retirement and new-Master placement back to back. The missing-Master state is irreducible under C6, rare, recoverable, and native consequences in it are unknown.**

**What "shortening" could and could not change.** Between the two Master renames, R2 writes two flushed journal records: the retirement's `DONE` and the placement's `BEGIN`. That is the whole exposure window for a process kill. It could be narrowed by journaling the pair as one record, but that changes recovery semantics and only lowers probability. Lower probability is not elimination: any termination in that window still leaves the same state, with the same consequences.

**After process termination.** The kernel closes every handle. The disk holds no Master; the old Master sits in `retired` with its data untouched (it was only renamed); the new Master sits verified in `candidate`; a snapshot copy of the old Master also exists. Guarded tools refuse, because a fresh observation of the Master fails (repo). Native SFM's behavior is unknown. If the user opens SFM, runs bare native Rebuild on a real project and saves before recovering, the damage can become persistent.

**After power loss.** Three further uncertainties apply (R2 C10):

- **Journal and disk can disagree.** A rename may persist while its `DONE` record does not, or the reverse. R2 A5 already requires recovery to read state from files, not the journal.
- **Rename order.** NTFS logs metadata changes in order, so the surviving disk state should be one of the same step states, each rename either done or not done (inference from documented NTFS behavior; not qualified). A storage device that ignores flush requests can break even that; R2 C10 already excludes such devices from guarantees.
- **New-file contents.** The new Master and sidecar were flushed before being renamed into place. If the device ignored that flush, the file at the live path may hold wrong bytes. Recovery's hash check would detect that.

**Is recovery reliably safe?** For the original data, yes in principle, and this is the strongest property of R2's design: originals are never rewritten, only renamed, so the old Master's bytes survive any interruption that leaves the filesystem consistent. A verified snapshot provides a second copy. Recovery may go forward (place the verified new Master into the vacant path, no-clobber) or back (return the old Master by identity, no-clobber). A file that appeared at the Master path meanwhile is preserved as a conflict (C12). U0A demonstrated this for process kills on synthetic data (repo). Real artifacts, the `E:` volume and journal/disk disagreement have not been tested.

**What remains untrue:** recovery cannot undo a scene that native SFM altered and the user saved while the Master was missing. That residual is why N1 is the next milestone.

## State and recovery matrices

During live activation every managed file is either held exclusively or absent, so new reads by native SFM fail and new guarded authorizations refuse (R2 C8). The tables show what remains **after the updater terminates and the kernel releases its handles**. M0 and S0 are the old Master and sidecar, M1 and S1 the new ones, P0 and P1 the manifests.

### Replacement or import (Master changes)

| After step | Master path | Authority folder | Native SFM reads | Guarded tools | Recovery (R2 C12 row) |
| --- | --- | --- | --- | --- | --- |
| Protected, no moves | M0 | S0, P0 | M0, correct | G1 | Abandon: "Nothing was installed" |
| S0 retired | M0 | P0 | M0, correct | Cold acquisition refuses; covered warm view of M0 may be reused (repo) | Known partial: resume or restore |
| P0 retired | M0 | empty | M0, correct | As above | Known partial |
| **M0 retired** | **absent** | empty | **Unknown (N1)** | Refuse | Known partial: place verified M1 or return M0 by identity, both no-clobber |
| M1 placed | M1 | empty | M1, correct | Refuse (no matching sidecar) | Known partial: resume |
| S1 placed | M1 | S1 | M1, correct | G2 usable; transaction incomplete | Install validated P1 into vacant path |
| P1 placed | M1 | S1, P1 | M1, correct | G2 | Verify, then finish receipt |
| Verified, recorded, released | M1 | S1, P1 | M1, correct | G2 | Complete |

### Rebuild with a different artifact (Master unchanged, S1 differs from S0)

The Master is protected with read access and no sharing, and never moves (R2 C6, C8).

| After step | Master path | Authority folder | Native SFM reads | Guarded tools | Recovery |
| --- | --- | --- | --- | --- | --- |
| S0 retired | M0 | P0 | M0, correct | Cold refuses; covered warm reuse possible | Known partial |
| P0 retired | M0 | empty | M0, correct | As above | Known partial |
| S1 placed | M0 | S1 | M0, correct | Rebuilt artifact usable; incomplete | Install validated P1 |
| P1 placed and verified | M0 | S1, P1 | M0, correct | Rebuilt artifact | Complete |

Rebuild never produces a missing Master. The deterministic compiler means a rebuild with the same compiler build reproduces S0 byte for byte, which R2 C8 treats as a verified no-op (repo).

### Conditions applied across both tables

- **Master edited or replaced after termination, before recovery:** recovery compares bytes and identity with the journal. A Master matching neither M0 nor M1 is preserved, nothing is overwritten, and the user chooses (C12, "TXT changed after crash").
- **File appears at a vacant destination:** preserved as a conflict; authority may stay unavailable (C12, "Unfamiliar active files").
- **Power loss:** the disk should hold one of the step states above, possibly disagreeing with the journal; recovery reads the disk (R2 A5). Wrong bytes in a placed file fail the hash check and are handled as a conflict.
- **Recovery interrupted:** the reverse direction is journaled in the same transaction; a second recovery must change nothing (C12, "Rollback interrupted").

## Rebuilds, multiple sidecars, publisher.lock, admission and the U0A tally

**Unchanged-source rebuilds.** With the same compiler build, a rebuild reproduces the existing artifact byte for byte (repo), so R2's verified no-op applies. Determinism across build environments has not been shown: the updater's packaged Python 3 compiler versus the development environment that produced existing artifacts. That belongs to R2 Stage 1's "deterministic compilation/parity" test. If the bytes differ, the rebuild matrix applies: the old artifact is retired before the new one is placed, so two matching artifacts never coexist inside an R2 transaction.

**Multiple matching sidecars.** They cannot arise from R2's order, but they can already exist on an installation. The existing publisher never retires generations, and a format change produces a new name prefix that sorts after the old one (repo). The selector would then serve whichever valid match sorts first. R2 G rightly rejects "intended artifact sorts first" as fragile. The first activation on any installation therefore needs a recognition rule: owned historical artifacts are identified by name pattern and validated bytes and moved outside the scan root only with explicit authorization. Anything else refuses.

**publisher.lock: an unresolved gap in R2.** R2's layout (C2) does not list it, and C12 refuses unfamiliar active content. The owner's live authority folder contains it (repo), so R2 as written refuses every activation on the only installation it must serve. The file is not a scan candidate, because the selector reads only `.sfmsidecar` names. Two resolutions are possible, and the choice belongs to Astra and the owner:

- **Recognize in place:** treat `publisher.lock` by exact name and location as an inert legacy publisher file and leave it.
- **Migrate:** move it out of the scan root with authorization.

Optional hardening: the legacy publisher locks a byte range of that file while publishing (repo). The updater could take the same byte lock during activation, so an accidentally running legacy publisher is refused rather than merely detected afterward. This does not make legacy publishing a supported writer (R2 C5). The owner should also confirm whether the legacy publisher still targets the live folder in daily work, because R2 C5 forbids that.

**Real-artifact admission.** A matching file is not admission. Following R2 E4, the updater may claim only that files are verified, bound to the active TXT and statically eligible under the installed profile, never that every SFM workload will be admitted. In the product, final verification checks the exact inventory (one active artifact), source binding and hashes through held handles. In qualification, the unchanged selector and its resource preflight should be run against every step state, under SFM's embedded Python 2.7.5 outside SFM. Existing offline suites already run under that interpreter (repo).

**U0A tally.** The raw verdicts and per-family table give 256 PASS and 1 NOT RUN (257 cases). The U0A report (line 9) and `CPM_CONVERGENCE_LEDGER.md` (line 17) say 255 PASS, and Astra's U0B runbook repeated the figure (repo). The bounded verdict is unchanged. The owner or coder should correct the count at the next Ledger checkpoint; this audit changes nothing.

## Native-SFM safety: four observable conditions

**Native SFM can observe only four Master conditions under R2. Two are ordinary use; two (locked, absent) are unknown and can be reproduced statically, without racing the updater.**

Native Rebuild reads the effective TXT at its fixed path (R2 B); it does not read sidecars or the manifest. When native SFM opens that path during or after an R2 transaction, it can find exactly one of:

1. **Old Master, complete:** ordinary use.
2. **New Master, complete:** ordinary use.
3. **Locked:** the updater holds the file exclusively, so the open fails with a sharing violation. This applies throughout live activation.
4. **Absent:** live, between the two Master renames; or after termination at that step.

Native cannot see a half-written or mixed Master. R2 never writes into the live file; it only renames complete files. If native already had the Master open before protection, its handle blocks the updater's exclusive open, and the updater stops before changing anything (C7). If native opens with delete sharing (unknown), a rename does not alter the bytes it is reading. (Inference from documented sharing and rename behavior.)

Timing races therefore add nothing for native SFM beyond which condition it meets when it opens the file. The one exception: if SFM reads the Master once at startup and caches it, the condition met at startup governs the whole session. N1 must therefore test both **startup under the condition** and **native Rebuild under the condition**.

**What Checkpoint I established and did not.** It showed that SFM, running idle, held no conflicting Master handle at the moment of replacement (inference from the replace succeeding) and that guarded tools adopted the new generation on their next command (repo). It did not show how native SFM opens the Master, when it reads it, or what it does under conditions 3 or 4.

**Guarded tools under the same conditions.** The Normalizer refuses before native entry when its protection open fails (repo, Checkpoint J), and detects a mid-command change (Checkpoint I2). CPM rereads the Master at each authorization. Still unshown: that a sharing-violation read in the broker is classified as a refusal and not an unhandled exception. That can be checked offline, under SFM's own interpreter, against a scratch Master held by another process.

Not running an experiment is not evidence of safety. Until N1 reports, native behavior under conditions 3 and 4 is unknown, and R2 C11 keeps shipping blocked.

## Matter 3: R2 qualification requirements vs one installation

**Revision 1's reduced plan contradicted R2. It dropped two shipping blockers (C11 suite concurrency, C10/G power interruption) and several G blockers without saying so. This revision meets most R2 requirements as written and names four amendments that need Astra's and the owner's approval. None is assumed approved.**

One finding cuts the other way. R2 Stage 0 asks for "a bounded real-SFM concurrency test on recoverable fixtures" and mentions a VM only for power interruption. The isolation HOLD in Astra's U0B runbook therefore goes beyond R2 itself and should be reconciled by Astra.

| R2 requirement | Single-installation method | Meets R2 as written? |
| --- | --- | --- |
| Stage 0 primitive experiment (C6 own-handle renames) | Repeat with real artifacts in a scratch folder on the installation volume `E:` (U0A used synthetic files on `C:`) | Yes |
| G blocker: protected source identity (in-place writer and save-by-replace editor at each barrier) | Scratch folder | Yes |
| G blocker: no-clobber at every destination | Scratch folder | Yes |
| G blocker: one publication owner (aliases, cross-user) | Aliases in scratch; cross-user needs a second Windows account, not a second SFM | Yes if the owner permits a temporary local account; otherwise **amendment A4** |
| G blocker: safe suite concurrency (launch SFM at protection and every rename; both consumers; retained CPM scope) | Static decomposition: N1 for native SFM under locked and absent; offline guarded-tool classification of every step state; Checkpoints I, J and K for consumer generation rules | **No: amendment A1** |
| C11: refuse when SFM is running | Product logic plus offline fault injection | Yes, with **clarification A3** |
| G blocker: process-crash recovery, recovered twice | Scratch folder, real artifacts | Yes |
| G required: power interruption (VM hard resets) | Synthetic post-power-loss state injection, plus no durability claim beyond "originals are renamed, never rewritten" | **No: amendment A2** |
| G blockers: post-crash edit preservation; complete recovery evidence; deterministic selection; path confinement | Scratch folder; unchanged selector run offline | Yes |
| G required: resource and UI containment (antivirus, disk full, killed worker) | Scratch folder and L Stage 2 | Yes |
| G blockers: authenticity, ordering, compatibility, clean-machine portability | L Stages 1–3; clean-machine via a clean folder or Windows Sandbox if the Windows edition has it (no SFM needed) | Yes in principle; feasibility unconfirmed |
| C11: unsafe native behavior blocks shipping | Retained; answered by N1 | Yes |
| Stage 3: actual installed suite | One ordinary update and reverse update on the owner's installation | Yes |

**Proposed amendments (each needs Astra's assimilation and owner approval):**

- **A1, suite concurrency method.** Replace live launch races with static decomposition: native SFM under the two unknown conditions (N1), plus offline classification of guarded tools in every step state including "locked." Pass criteria stay R2's: coherent completion, explicit refusal or verified new generation; no mixed mutation; no unsafe native behavior. A retained CPM scope across activation is reachable only if SFM launches after the final process check. It becomes a disclosed limitation, not a tested case.
- **A2, power-interruption method.** Replace VM hard resets with injected post-power-loss states: every step state, with the journal ahead of and behind the disk, and placed files with wrong bytes. Recovery runs twice on each. First release makes no power-loss durability claim beyond what R2 C10 already limits.
- **A3, process-check clarification.** State in C11 that an UNKNOWN or failed process query refuses activation, as Astra's U0B runbook already requires. The U0A code currently fails open twice (repo).
- **A4, support boundary.** If no second Windows account is used, restrict the first release to a single Windows user per installation and drop the cross-user blocker for that release.

The `publisher.lock` and historical-artifact rules are separate design gaps, listed under disagreements.

## Failure risks, ranked by consequence

Ranking follows the worst outcome, not how long a file inconsistency lasts. Three classes can destroy user work that cannot be regenerated: overwritten TXT edits, damaged user files, and scenes altered and then saved.

| # | Failure | Consequence class | Severity | Conditions | Evidence now | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Updater overwrites a concurrent TXT edit | Loss of authored TXT bytes | Critical | Editor saves during activation | R2 design prevents it through exclusive handles and no-clobber; unqualified against real editors on `E:` | G identity blocker, scratch folder |
| 2 | Updater writes outside its allowlist (path error, junction swap, alias) | Loss of presets, settings or other user files | Critical | Defect or path change mid-run | Synthetic paths on `C:` only (repo) | G path-confinement blocker, scratch folder on `E:` |
| 3 | Qualification work damages the owner's data | Loss of projects, presets or settings | Critical | Real project opened, a save, or an SFM crash during its exit-time writes | Not yet controlled | Verified backups, disposable sessions, N1 stop rules |
| 4 | Native SFM, finding the Master locked or absent, alters a scene the user then saves | Persistent project damage | High | Termination at the Master gap, or SFM launched during activation, then native Rebuild and a save | Unknown | N1; shipping blocker under C11 |
| 5 | False success: completion recorded for a set that is not in place | False installation claim | High | Verification on unprotected files, or wrong artifact | R2 verifies through held handles; early release would break this (Matter 1) | Keep R2 handle timing; scratch qualification |
| 6 | Recovery misjudges real artifacts or journal/disk disagreement | False success or stranded authority | High | Interruption or power loss | Process kills on synthetic data only (repo) | Scratch qualification plus A2 injection |
| 7 | Process check fails open | Enables every concurrency unknown at once | High | Query exception, or nonzero exit with empty output | Two fail-open paths in U0A code (repo) | Fix, offline fault injection, A3 |
| 8 | A guarded tool hits a sharing-violation read and fails with an unhandled error, not a refusal | Temporary inability; confusing error | Medium | SFM launched during activation | Unshown | Offline classification under SFM's interpreter |
| 9 | Pre-existing historical artifacts make selection depend on name order | Incorrect but recoverable generation selection | Medium | Installations with legacy publishing history | Selector behavior verified (repo) | Recognition and migration rule before first activation |
| 10 | Device ignores flush; a placed file holds wrong bytes after power loss | Temporary inability; original preserved | Medium | Power loss, non-compliant storage | Untested | Hash check in recovery; A2; disclosure |
| 11 | Legacy publisher runs during activation | Preserved conflict or refusal | Medium | Owner's development workflow | Outside R2 C5's supported writers | Contract; optional cooperative byte lock |
| 12 | Every activation refused because `publisher.lock` is unfamiliar | Updater unusable on the owner's installation | Low severity, certain to occur | Always, as R2 stands | U0A case 6h (repo) | Design gap resolution before L |
| 13 | Honest, preserved recovery conflict | Temporary inability by design | Low | Unexpected occupant or post-crash edit | U0A behavior (repo) | Intended outcome |

## Required release qualification vs optional hardening

**Ten qualifications are required for the first release under R2 as amended. Eight run in a scratch folder or offline. Two touch the live installation: N1 (bounded, more hazardous than ordinary use) and one ordinary update with SFM closed.** The scratch work must use the exact build later used live, pinned by hash.

| ID | Qualification | Where | Risk to the installation | Pass condition |
| --- | --- | --- | --- | --- |
| Q1 | Process check: RUNNING, CLEAR or UNKNOWN; inject an exception and a nonzero exit. Harness barriers need exact tokens; end of input, a bad token or controller loss stop mutation | Offline and scratch | None | UNKNOWN refuses before protection; no mutation without a token |
| Q2 | In-place writer and save-by-replace editor at every barrier; occupant at every destination; junction and alias swaps | Scratch on `E:` | None | Writer refused or updater stops with both versions kept; occupant preserved; no write outside the slot |
| Q3 | Replacement, import, rebuild with a different artifact, and rebuild no-op, using canonical compiler output, real names and the agreed `publisher.lock` rule. Measure protection-to-release time | Scratch on `E:` | None | Exact final inventory with one active artifact; source binding and hashes verified through handles; no-op performs no moves |
| Q4 | Kill after every write and rename; recover twice; edit the TXT in every partial state; remove or corrupt each recovery component; interrupt rollback | Scratch on `E:` | None | Verified old or new set, or preserved conflict; second recovery changes nothing; no false success; newer bytes kept |
| Q5 | Injected post-power-loss states (A2) | Scratch on `E:` | None | Same as Q4; no working-restore claim when a component is missing |
| Q6 | Unchanged selector, resource preflight and broker observation against every step state, including "locked" by an external holder | SFM's Python 2.7.5, outside SFM | None | Intended artifact selected or explicit refusal; no unhandled exception |
| Q7 | Lock ownership through aliases; cross-user if A4 is not adopted | Scratch | None | One live owner; denied access never creates a second lock |
| Q8 | Real SFM open and idle; updater pointed at the scratch root | Scratch root | None, even if refusal fails | Refuses before protection |
| Q9 | **N1**: native SFM at startup and during native Rebuild with the Master locked, then absent | Live installation, disposable session | Bounded; comparable to a user deleting or locking a config file | Explicit harmless refusal, or coherent correct result; no silent default reorganization, crash or hang |
| Q10 | One ordinary update and its reverse, SFM closed; launch and verify both tools on a disposable session | Live installation | Low | Final inventory equals preflight hashes, checked independently of the transaction's own report; provenance logs show the intended artifact |

R2 Stages 1–3 items (signatures, ordering, compatibility profile, clean-machine packaging) remain required before release but belong to L, not U0B.

**Optional hardening, not first release:**

- prepublish ordering, for guarded-tool availability after a crash;
- a single journal record for the Master pair, to shrink the kill window;
- the cooperative `publisher.lock` byte lock;
- hard-reset testing if a spare machine ever becomes available;
- wider editor-pattern coverage.

If N1 shows harmful native behavior, M-P research is not hardening: it becomes a design question for Astra and the owner.

**Not required:** the U0B runbook's live races C1, C2, C4, D1–D3 and E1–E6; the Script Editor observer; any VM or isolated environment.

## Disagreements, residual risk and decisions

### Unresolved disagreements with R2

This audit agrees with R2's file protocol (C6–C8), durability statements (C10), recovery matrix (C12) and one-active-artifact rule (G). It disagrees on seven points:

| # | R2 position | Audit position |
| --- | --- | --- |
| D1 | Suite concurrency proven by live launches at protection and every rename (C11, G) | Static decomposition proves the same pass criteria with less hazard (A1) |
| D2 | Power interruption proven by VM hard resets (G) | Injected post-power-loss states plus no durability claim; no VM exists (A2) |
| D3 | Process detection is "advisory" (C11); UNKNOWN not addressed | UNKNOWN must refuse (A3) |
| D4 | Layout lists no `publisher.lock`; unfamiliar content refuses (C2, C12) | R2 as written refuses every activation on the owner's installation; a recognition rule is needed before L |
| D5 | Historical artifacts migrate "after explicit migration authorization" (G) | The first-activation recognition rule is unspecified; without it, selection on legacy installations depends on name order |
| D6 | Replace semantics prohibited outright (C6) | Correct for now; must be reopened if N1 shows silent native damage, since that would weigh a rare clobber against rare silent scene damage |
| D7 | Live protection prevents new suite reads (C8); duration unstated | The protected interval also blocks native reads; it should be measured (Q3) and disclosed |

One disagreement is with Astra's U0B runbook rather than R2: its isolation HOLD exceeds R2 Stage 0, which asks only for recoverable fixtures.

### Residual-risk statement

**Acceptable for a hobbyist first release, if disclosed:**

- after an interrupted update the Master may be missing until the updater's recovery runs;
- native SFM behavior if launched during activation, provided N1 shows it fails safely;
- no power-loss durability claim beyond "originals are renamed, never rewritten";
- storage that ignores flush requests is outside all guarantees;
- one Windows build and one installation tested; single user if A4 is adopted;
- no control over noncooperating writers or administrators;
- a CPM scope retained across activation is untested, being outside the SFM-closed contract;
- legacy publisher use is excluded by contract, not enforced.

**Never acceptable, regardless of convenience:**

- silent loss of authored TXT edits;
- writes outside the verified allowlist;
- a success report for a set not verified through protecting handles;
- automatic destructive restore over newer user bytes;
- deletion of unfamiliar files;
- shipping with known silent native scene damage.

### Decisions only the owner can make

1. Authorize or decline N1 on the live installation. Declining leaves C11's blocker unanswerable and the design on HOLD.
2. Submit amendments A1–A4 to Astra, then accept or reject Astra's disposition.
3. Choose the `publisher.lock` rule (recognize in place or migrate), and confirm whether the legacy publisher will stop targeting the live folder (R2 C5).
4. Permit a temporary second Windows account for cross-user lock tests, or adopt the single-user boundary (A4).
5. Approve installing a passive file-trace tool such as Process Monitor for N1.
6. Correct the U0A tally at the next Ledger checkpoint.

### Questions evidence can settle (designer or coder)

- When native SFM reads the Master: startup, session load or Rebuild.
- The filesystem and drive type of `E:`.
- The measured protection-to-release interval.
- Whether the packaged compiler reproduces existing artifacts byte for byte.
- How the broker classifies a sharing-violation read.
- What SFM writes at exit, and where.
- Whether the Windows edition offers Windows Sandbox for clean-machine tests.

## Next milestone: N1, static native characterization

**N1 answers the one question that decides the architecture: what native SFM does at startup and during native Rebuild when the Master is locked or absent.** It needs no updater code and no timing race. It runs only after Astra's assimilation and the owner's written authorization.

**Why first.** If native SFM fails safely, R2's protocol stands and the scratch qualification (Q1–Q8) can be built with confidence. If it fails silently, D6 reopens before any harness work is wasted.

**Preconditions (all required):**

1. SFM closed. Read-only inventory with SHA-256 of `game\usermod\cfg` (Master, authority folder including `publisher.lock`, config files), the CPM and Normalizer logs in Public Documents, the CPM preset root and the SFM executable. Independent copies on a different drive, verified by hash.
2. Installed Master equals `ac45e5c1…`, 3,972,355 bytes.
3. A disposable session, copied from the J/K fixture under a new name, with an agreed target animation set. No real project is opened at any point.
4. A scene oracle for that target, covering control-group tree, channels and keys, chosen and approved in advance: an existing qualified read-only capture if one exists, otherwise specified before N1 begins.
5. An approved passive file-trace tool, filtered to the Master path.

**Conditions (fresh SFM process each, one attempt each, in this order):**

| Condition | How the state is produced | Actions |
| --- | --- | --- |
| B, baseline | Master normal | Start SFM; open the disposable session; native Rebuild Control Groups on the target; capture the oracle; close without saving |
| L, locked | An approved external holder opens the Master with no sharing before SFM starts | Same actions; release the holder after SFM closes |
| A, absent | With SFM closed, the Master is moved to the backup folder, its identity recorded | Same actions; with SFM closed, return the Master by identity and verify its hash |

**Observables for each condition:**

- startup outcome and time to idle;
- every open of the Master path in the trace, with result code and timing relative to startup and Rebuild (this also answers when native SFM reads the Master);
- SFM console and log text;
- the native Rebuild outcome;
- the oracle difference from baseline;
- any new file in `cfg` or the authority folder;
- process exit status.

**Classification for L and A:**

- **SAFE:** a visible error with no scene change, or a result identical to baseline.
- **HARMFUL:** a silent group-tree change, any channel or key change, a partial tree, a crash or a hang.
- **INCONCLUSIVE:** the oracle or trace cannot decide.

**Acceptance:** B, L and A each run once with complete evidence. L and A are classified. The final inventory matches every preflight hash exactly.

**Stop conditions.** Halt, preserve evidence and return to the owner if:

- a real project would be opened;
- any write appears outside the allowlist (the Master's move and return, the disposable session, SFM's own logs and config already inventoried, the trace output);
- a file appears at the Master path while it is absent (preserve it);
- SFM hangs past the agreed timeout (terminate only the recorded process ID);
- any restoration fails, or any hash differs after restoration.

Condition A runs after a HARMFUL result in L only if L's restoration verified exactly, because A answers the separate post-crash question.

**Permission boundary.** No updater or harness code, no repository, Blueprint or Ledger change, no edits to SFM binaries or settings, no Script Editor probes, no injection into SFM, and at most one attempt per condition. The result goes to Astra for disposition of D6 and of amendments A1–A4.
