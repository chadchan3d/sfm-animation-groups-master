# SFM Character Tools Updater — Final Architectural Assimilation

**Date:** 2026-10-12  
**Evidence checkpoint:** `1a2bbd18066a670f56ad2d407c81d028eb1695a5`  
**Disposition:** Retain R2's protected activation architecture; revise its qualification plan subject to owner approval. **HOLD live fault injection and release authorization.**

## 1. Final architectural ruling

Keep one external utility, one canonical compiler, and one installed activation/recovery backend. Retain C6–C8's protected, identity-checked, no-clobber moves and C12's evidence-based recovery. Do not substitute hash-then-overwrite, early Master-handle release, a manifest switch, or a new runtime handshake.

**Reject Claude's proposal to make N1 the next milestone.** Deliberately starting SFM with its effective Master locked or absent is a hazardous experiment on the only installation. It may eventually be warranted, but it is neither the first useful investigation nor sufficient proof of safe concurrency.

I also revise my earlier runbook: **a VM or second installation is not an unconditional architectural requirement.** R2 Stage 0 required recoverable fixtures, not a second machine. My runbook turned a preferred containment method into a blanket prerequisite. That was too restrictive for this project. A sole-installation qualification can be considered after a specific recovery, exposure and observation assessment—but backups must not be described as isolation, and no such assessment has yet authorized fault injection.

The recommended path is therefore:

> Read-only installation and evidence preflight → real-artifact scratch qualification → approved passive characterization of ordinary SFM behavior → only the unresolved, separately authorized native fault/concurrency cases → final packaged normal-operation qualification.

This is one staged path, not authorization for the entire sequence. It preserves K COMPLETE/PASS, U0A PASS (bounded), and the frozen R15 Blueprint. It does not begin L.

### Evidence checked for this ruling

I read the assimilation packet, including Claude's revised audit, original R2 and the previous runbook. I independently checked the current repository identity, raw U0A verdict counts, actual sidecar naming, the legacy publisher's ordering, and the current installed authority-directory listing. A read-only .NET drive query reports **E: as a ready, fixed NTFS volume**. A preceding `Get-Volume` query was denied; no elevation was attempted. Neither observation qualifies E:'s interruption behavior.

The present authority listing contains `manifest.json`, a zero-byte `publisher.lock`, and:

```text
sfm_master_0_bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b.sfmsidecar
```

That listing is not a new runtime-admission or complete installation-integrity result.

## 2. R2 requirements: what stands and what changes

| R2 element | Final recommendation |
|---|---|
| C6–C8: protected file moves and order | **Retain.** No overwrite, cross-volume fallback, early release or live-file rewriting. Carry U0A's corrected handle permissions and recovery journaling forward. |
| C4/C5: one installed publisher | **Retain.** All supported installed writes use the same physical installation lock/backend. Old publishers remain export/development tools, not alternate installed routes. |
| C10: flush, preserve originals, revalidate after interruption | **Retain.** Do not infer storage durability from successful flushing or from no-clobber renames. |
| C10/G: mandatory hard resets | **Recommend a narrower first-release qualification standard, requiring owner approval.** Keep the requirement outstanding until that amendment is explicitly approved; injected states do not satisfy it. |
| C11: refuse SFM already running; account for a later launch | **Retain and clarify UNKNOWN refusal.** Process checks do not provide positive launch exclusion. |
| C11/G: safe suite concurrency | **Retain the safety requirement; reduce redundant experiments only with a documented evidence argument.** Static tests cannot be relabeled a full concurrency PASS. |
| C12: recover from verified disk state, preserve conflicts | **Retain.** Recovery success must identify whether it restored working authority or merely the exact, possibly stale, previous files. |
| Stage 0 | **Resequence.** Low-risk, real-artifact and observation prerequisites precede hazardous native cases. No GUI/backend production implementation to evade a failed prerequisite. |
| G: identity, no-clobber, recovery, selection, confinement | **Retain as release blockers.** U0A supports the mechanisms; the real artifact and deployment boundary still need qualification. |
| G: authenticity, compatibility, portability | **Retain for L.** A clean directory proves dependency closure, not all clean-machine Windows behavior. Windows Sandbox availability must not be assumed. |

C6–C8 is the best-supported mechanism among the alternatives actually examined. That is not proof that every possible continuously occupied-path architecture is impossible. There is no demonstrated superior alternative that preserves the current guarantees and scope, so a new architecture search is unwarranted now.

## 3. Claude A1–A4: explicit adjudication

### A1 — Substitute static decomposition for suite concurrency: MODIFY

Accept decomposition to eliminate redundant live cases. Use the actual selector, broker and consumer adapters against scratch states, including real sharing violations. Reuse K/I/J only for the contracts their evidence actually exercises.

Reject the assertion that this establishes the same release properties as every relevant live ordering. Four pathname conditions are a useful list of inputs; they are not a complete model of an operation that may open files more than once, retain parsed data, yield, retry, or encounter another generation later.

In particular, static N1 does not independently establish:

- a healthy-started SFM process encountering a later unavailable Master;
- a transition between native opens or phases;
- Normalizer protection acquisition/release relative to updater protection;
- an authorized CPM operation completing through the actual protected transition;
- Clothing Fit's next-stage behavior after that transition;
- actual startup behavior while availability changes rather than remaining fixed.

Not every item needs another live experiment. Exact source contracts plus existing qualified evidence can close some. The release evidence map must identify which are closed, which receive one decisive test, and which remain unqualified. “SFM should be closed” does not itself resolve the accidental-launch path C11 expressly addresses.

**Change to R2:** recommend replacing “launch at every rename” with coverage of distinct consumer-relevant states and meaningful ordering boundaries. Do not drop the safety blocker or call retained-operation coverage unnecessary by declaration. An owner-approved narrower support claim is a qualification amendment, not a U0B PASS.

### A2 — Substitute injected states for hard resets: MODIFY

Accept scratch tests of missing/corrupt components, torn journals, journal/disk disagreement and interrupted recovery. They are valuable recovery-algorithm tests.

Reject the labels “equivalent power-interruption test” and “post-power-loss states” when they suggest those are the states the actual storage stack has been observed to leave. They are **constructed inconsistent states**. Test non-prefix and ambiguous states as refusal cases rather than assuming every persistent result is a clean prefix of the move list.

Recommend that the owner approve a proportionate first-release standard:

- qualify ordinary process termination and conservative recovery from constructed inconsistent states;
- preserve checked writes, flushing, original retention and post-reboot validation;
- explicitly leave power-loss durability unqualified;
- make no guarantee that originals or backup copies survive arbitrary storage loss;
- do not deliberately hard-reset the owner's only machine for this release.

This changes the mandatory hard-reset requirement in C10/G. **It is not effective until approved.** The no-silent-overwrite and no-false-success requirements remain unchanged. If the required product promise includes demonstrated hard-power-loss preservation, the current hardware constraints leave that promise on HOLD.

### A3 — UNKNOWN process query refuses: ACCEPT

Require RUNNING / CLEAR / UNKNOWN. Exceptions, nonzero query exit, incomplete visibility and unparseable results are UNKNOWN, never CLEAR. Refuse before protection or active mutation. A final successful check still cannot exclude a subsequent launch.

Also retain exact-token barriers: EOF, malformed release, timeout or controller loss must not resume mutation. These corrections belong to any subsequently approved harness/backend, not to a rewrite of preserved U0A evidence.

### A4 — Drop cross-user proof under a single-user restriction: MODIFY

A second Windows account does not require a second machine or SFM installation. Prefer one bounded scratch contention test on this computer if the owner authorizes access to an appropriate second account. Do not create accounts, change ACLs or elevate spontaneously.

If that is unavailable, recommend an explicitly owner-approved **single-account qualification boundary**, with cross-user behavior UNKNOWN. Retain the physical installation lock, alias resolution and access-denied refusal. Never introduce a per-user substitute lock or imply that documentation prevents another account from running a writer.

Dropping the cross-user G blocker is a support/qualification amendment. It is not justified merely because the intended operator normally uses one account. No multi-user safety claim follows from a single-user release.

## 4. N1: necessary, safe enough, sufficient?

**Necessary next? No. Safe enough now? Not established. Sufficient for C11/G? No.**

Native handling of an inaccessible effective Master remains a material release question. Controlled fault characterization may be the shortest eventual way to answer it if existing implementation evidence and passive observations cannot. However, the proposed N1 should not precede the lower-risk work that establishes where SFM reads and writes, what the fixture can detect, and how restoration would work.

### Why N1-first is rejected

1. **“Same result as baseline” can be a weak oracle.** An already-normalized fixture may produce the same tree after a no-op, cached read or fallback. A valid oracle needs a known, observable Master-dependent transformation, untouched peers, and preserved controls/channels/keys. Existing suitable fixtures should be reused; do not alter the live Master merely to improve the oracle.
2. **A Master-only trace filter is insufficient.** It may show the canonical open failing while omitting reads from a fallback path, prior configuration reads, or settings/autosave writes. Observation must cover the relevant alternative reads and writable locations without collecting unrelated user data.
3. **Starting under a fault differs from encountering one later.** Testing startup and Rebuild in the same fault-started process does not cover healthy startup followed by a fault. Passive normal-use tracing should determine which distinction matters.
4. **The installation is not the only exposed data.** Public Documents logs, preset files, settings, recent-session/autosave behavior and exit-time writes need an explicit exposure map. Backups provide restoration material; they do not prevent writes or guarantee a recoverable native crash.
5. **A harmful locked result is a stop.** Do not automatically proceed to absent-Master testing just because filesystem restoration succeeded. The architecture is already challenged; further hazardous testing needs a new decision.
6. **A native failure does not authorize clobber risk.** Reject the suggested automatic progression to a “rare clobber versus rare scene damage” trade. The stated requirements reject both. A harmful result calls for HOLD or a separately approved architecture/scope change, not immediate replacement semantics.

### Conditions for considering a later N1 revision

After the preceding evidence is available, submit a separate, exact scenario card for owner approval. It must specify the effect to detect, retained evidence, timeout/abort procedure, ordinary SFM write locations, and restoration procedure. Begin with a healthy baseline, then the least disruptive unresolved condition. Permit no real project to be opened and no original project/preset to be a save target. Validate fixture save/autosave destinations rather than relying only on “close without saving.”

For any absent-Master case:

- retire the exact protected original by a **same-volume no-clobber move**, preserving FileId;
- keep independently verified backup copies separate from that retired original, preferably on another volume where available;
- do not use a generic cross-volume “move to backup” as identity preservation;
- return the original only into a verified vacant canonical path with SFM closed;
- preserve any newly created occupant and stop; never overwrite it to restore the expected appearance.

Do not require the owner's live source to equal official G1. Inventory the actual source first. Customized bytes are authoritative user data; a mismatch stops a fixture assumption, not a justification for installing G1.

The final classification must distinguish safe refusal, coherent observed completion, harmful behavior and inconclusive evidence. A missing/erroring observation is not safety evidence. Known harmless UI differences do not equal corruption; silent default reorganization, channel/key loss, unexplained partial mutation or a native crash cannot be waved away as “filesystem recovery passed.”

## 5. Remaining design details resolved or carried forward

### `publisher.lock` and older publishers

**Recommendation: recognize the verified legacy lock in place; do not migrate or delete it for the first release.** Add it to the exact completed-state inventory as a preserved non-authority support file. Require its expected location, regular-file identity, no reparse/hardlink substitution, and confirmed publisher provenance. Name alone does not establish ownership. An unexplained variant refuses automatic activation.

There is a substantive limit to Claude's optional byte-lock proposal. In [the current publisher](</E:/SFM Animation Group Master/tools/sfm_master_sidecar/publisher.py:197>), temporary sidecar writing, validation and immutable generation publication happen **before** `PublisherLock` acquisition. The byte lock covers the later source recheck/manifest section. Acquiring it in the updater would not serialize the complete old publication flow.

Therefore do not add a second lock and claim full coordination. Retain C5: no supported legacy installed-write path; all shipped installed writers use the new backend. A known active legacy writer refuses activation. Final inventory checks catch observable interference but do not provide perpetual namespace exclusion. If the owner's normal workflow must retain direct old-CLI publication to the live root, resolve that workflow before activation support is approved.

### Historical artifacts and deterministic selection

Canonical names come from `compiler.generation_basename()`: currently `sfm_master_0_<full-artifact-sha256>.sfmsidecar`. Do not use U0A's synthetic `v1` naming in real qualification or freeze a new format version.

A matching basename plus structural validity identifies a plausible artifact, not permission to dispose of it. Recognize historical artifacts using verified embedded identities, full file hash, supported structure and known receipt/compiler provenance where available. Bind any migration approval to the exact inventory; preserve those files outside the runtime scan root. Unknown files refuse automatic activation; no wildcard cleanup.

Keep exactly **one active selectable sidecar** after a completed updater transaction, plus its manifest and the explicitly recognized inert lock. Test two valid same-source artifacts whose lexical order would select the unintended one. Source SHA equality does not establish interchangeable compiler/semantic content. Manifest content is not proof of which artifact runtime actually selected.

The current runtime may legitimately serve a warm detached view when backing is absent but its exact Master remains readable and unchanged. That is not a new cold admission. Conversely, a readable matching pair may work without a manifest. Maintain these distinctions in test verdicts.

### Recovery and truthful success

Retain through-handle verification before recording completion and explicit handle release before reporting successful activation to the user. Do not claim future immunity to external edits after release. Share restrictions last for the lifetime of each handle; that is an access guarantee, not a directory-wide transaction. [Microsoft CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)

Recovery must derive fixed, confined paths, verify actual bytes and identities, preserve post-interruption edits, and reconcile direction and journal progress. A valid journal or manifest is insufficient. Unambiguous valid old/new state may be recovered; ambiguous, missing, corrupt or unexpected material is preserved with an explicit refusal. Include recovery interruption and a second idempotence attempt.

“The originals were renamed, never rewritten” describes updater operations. It is not proof their bytes survive power or storage failure. Flushing and recovery validation remain necessary; injected corruption tests do not measure persistence. [Microsoft FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)

### Installation confinement and path budget

E: is observed as fixed NTFS, but U0A exercised C:. Qualify the transaction on a dedicated E: scratch root outside all SFM search/config/script roots. Verify physical containment, no reparses/hardlinks in managed slots, alias identity, permissions and actual maximum path lengths. The known `cfg` path is 65 characters; the approximate additional 172 is not a complete path-budget proof.

Directory handles do not stop new children. Keep final exact-inventory verification. No cross-volume copy fallback, force-through elevation, automatic ACL repair, installation renaming, or broad recursive cleanup.

### U0A tally correction

**Claude is correct.** Independently grouping `u0a_results.json` by verdict gives **256 PASS, one NOT RUN, zero FAIL: 257 recorded cases**. The per-family PASS totals also sum to 256:

```text
6 + 83 + 8 + 5 + 134 + 20 = 256
```

My earlier runbook's 255 total was wrong, despite reproducing the correct family counts. Correct the report/Ledger/runbook through the next authorized documentation change, preserving the correction history. U0A PASS (bounded) is unchanged. No Ledger or prior document was edited in this review.

## 6. Minimum defensible release-qualification plan

This is a finite sequence with separate authorization gates. It is not a request to repeat the entire historical campaign.

| Gate | Minimum evidence | Claim authorized by PASS |
|---|---|---|
| **P0 — Read-only feasibility and evidence certificate** | Paths, installed identities, writable exposure map, available baseline/native traces and fixture oracle, exact outstanding claims, approved-scope proposal | A concrete decision about scratch preparation and passive observation; no live fault permission |
| **P1 — Real-artifact scratch qualification on E:** | Canonical real outputs; import/rebuild/replacement/no-op; custom-source preservation; occupied destinations and source substitution; interrupted forward/reverse recovery; malformed/conflicting states; alias ownership; selector identity; broker sharing-violation classification; UNKNOWN and barrier failure paths | The proposed backend/harness preserves the tested real bytes and reports truthful state on this volume/profile |
| **P2 — Passive ordinary-SFM characterization** | Separately approved normal startup/native action on a disposable fixture with unchanged live authority; native open/read pattern, alternative paths, normal writes and a sensitive scene oracle | Whether and how a minimal live fault test can be conducted and what it would establish |
| **P3 — Only unresolved native/concurrency boundaries** | Separately approved revised fault tests and any irreducible real transition ordering; reuse existing consumer evidence where exact equivalence is shown | The explicitly tested C11 safety scope; no universal concurrency claim |
| **L final candidate** | Exact shipping backend/GUI/dependency identities; remaining authenticity/compatibility/confinement/failure checks; ordinary SFM-closed activation and verified reverse recovery; actual intended artifact consumed by both tools | Release eligibility within the owner-approved qualification/support boundary |

P1 is scratch mutation, not read-only work. P2 runs SFM, which can write settings/logs even though authority is unchanged. Both require their own explicit execution approval; neither is included in P0.

P1 should reuse U0A cases where mechanisms are unchanged, extending the material boundary to real names/content and E:, not multiplying every case without purpose. Injected inconsistent states remain a separate evidence category. Running Python 2.7.5 outside SFM qualifies those Python paths, not Qt integration or embedded-host behavior.

If exact sharing-violation classification is exercised only at broker level, do not claim both tools' UI refusal paths passed. If a fixture uses the old and new Master with identical semantics, use generation/context provenance to establish continuity; output equality alone cannot expose semantic mixing.

P3 is not automatically a large launch-at-every-rename campaign. Passive observations and existing evidence should reduce it to material distinctions. If those distinctions cannot safely be tested on the sole installation, the relevant C11 claim remains on HOLD. An owner may approve a narrower qualification standard, but that must state the untested behavior explicitly and must not authorize shipping known silent data damage.

Until the owner approves A2/A4's modified standards, their original hard-reset/cross-user requirements remain outstanding. No release blocker is waived by this document.

## 7. One bounded next milestone

### U0B-P0 — Read-only installation, exposure and evidence preflight

**Purpose:** Produce the smallest concrete evidence package needed to decide whether safe scratch work and passive native characterization can proceed on this single installation. Do not lock or remove the effective Master to answer a question that can first be narrowed read-only.

**Owner authorization before execution: required.** This ruling proposes P0; it does not initiate it. No code-writing or later execution authorization is bundled with it.

**Permitted scope after approval:**

- Read the checkpoint repository, existing qualification artifacts, installed path metadata and exact installed file bytes relevant to the updater and both consumers.
- Inventory the actual Master, authority namespace, launchers, CPM/Normalizer/adapter/shared-package closure, `gameinfo`/search configuration and identified log/settings/preset/autosave locations. Avoid reading unrelated project content.
- Identify a running SFM process only if one already exists and its metadata is accessible without intrusion. Do not start, stop, attach to, suspend or interact with it. Missing dynamic identity remains UNKNOWN.
- Review existing native traces and existing fixture/oracle evidence. Specify the smallest subsequent passive observation needed where records are absent.
- Describe, but do not create, the E: scratch-root allowlist and restoration/backup plan.
- Write only the report and inventory in one new evidence folder under the operator's approved local Codex evidence directory, outside the repository; no repository or SFM writes.

**Acceptance evidence:**

1. Exact checkpoint and observed installed-file identities, with discrepancies explicitly listed.
2. An installation map distinguishing statically resolved paths from paths demonstrated by prior actual native reads.
3. A concrete write-exposure/restoration map covering settings, presets, Public Documents logs and autosaves; no assertion that backups equal isolation.
4. A classified authority inventory, proposed preservation rule for `publisher.lock`, and exact historical-artifact handling—no deletion or migration performed.
5. A source-linked claim matrix separating U0A/K/I/J evidence from unknown sharing/native/transition behavior, including the corrected U0A tally.
6. Identification of an existing fixture/oracle that detects meaningful Master-driven changes and preserved channels/keys, or the exact missing oracle evidence.
7. A bounded P1/P2 authorization card with paths, expected writes, required existing tools and STOP/restoration rules. Missing tools or privilege requirements are surfaced, not installed or bypassed.

P0 PASS means this package is complete and sufficiently concrete for the next authorization decision. It does **not** mean native safety, backup recoverability, U0B or release qualification passed. If a critical restoration or observation dependency cannot be identified, return P0 BLOCKED with that precise gap; do not turn UNKNOWN into acceptance.

**STOP conditions:**

- Read access requires elevation, ACL changes or installation of a tracing service/driver.
- Any proposed read resolves outside the approved relevant paths or encounters an unexplained reparse/alias.
- Protected files change during inventory, making the snapshot inconsistent.
- Effective source/consumer origins conflict with the stated configuration.
- Completing the task would require launching SFM, locking/renaming data, testing recovery, compiling/publishing artifacts, changing settings or opening a user project.

Preserve the partial read-only evidence and report the gap. Do not escalate automatically.

**Forbidden:** code or harness development; scratch tests; file-lock experiments; sidecar compilation/publication; SFM startup/native calls; tracing installation; account creation; live data moves; Ledger/Blueprint edits; U0B execution; L implementation.

## Final decision

**Retain R2 C6–C8/C12. Accept A3. Modify A1, A2 and A4 as specified, subject to owner approval. Reject N1-first sequencing and reject claims that static faults or injected recovery states are equivalent to concurrency or power-loss qualification.**

**The sole next proposed milestone is U0B-P0, read-only preflight, requiring owner authorization before execution. Live fault injection and release remain on HOLD.**

Confidence is high in the source/evidence corrections and this sequencing decision. Native behavior with the effective Master locked or absent remains UNKNOWN. No implementation, qualification, SFM mutation, Ledger change or R15 change was performed.
