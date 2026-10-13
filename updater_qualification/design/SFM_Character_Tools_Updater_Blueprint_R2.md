# Updater Blueprint — Revision 2

**Design verdict: retain the external updater, but replace Revision 1’s directory-swap transaction and narrow its concurrency and durability claims.**

The recommended architecture remains small: one GUI, one canonical compiler, one installed-publication backend. It is **not yet ready for implementation freeze**. One bounded Windows filesystem/concurrency experiment must establish the activation primitives before the broader L implementation plan is frozen.

This review inspected the repository at `af4c8d6245f3850460fae78e3f108b150d2f092a`, relevant consumer code, and Microsoft/GitHub/cryptographic-library documentation. **No qualification experiments were executed.** The matrices below specify future proof obligations, not completed stress-test results.

Classification:

- **Verified:** inspected source or documented API behavior.
- **Inference:** engineering conclusion from that evidence.
- **Proposed:** recommended contract.
- **Unresolved:** qualification or owner decision remains.

## A. Rebuttal disposition

| Objection | Disposition |
|---|---|
| **A1 — Exact Windows operations** | **Accept and revise.** Remove whole-directory swapping. Use protected, individually inventoried file renames into vacant destinations. Specify the primitives below. |
| **A2 — No-clobber guarantee** | **Accept.** Use `FileRenameInfo` with `ReplaceIfExists=FALSE`. Never substitute overwrite after a collision. |
| **A3 — Protecting the TXT** | **Accept and narrow.** An exclusive file handle can exclude ordinary conflicting file opens while held. It does not control privileged tampering, every ancestor namespace, or future edits after release. |
| **A4 — Runtime selection during transitions** | **Accept.** Model selection after each operation. Manifest publication is never the activation switch. |
| **A5 — Ambiguous completion** | **Accept.** Recovery derives state from file identity, hashes and validation; journal entries alone never establish completion. |
| **B — Updater lock versus SFM** | **Accept and narrow.** Choose bounded fail-closed behavior for the qualified suite, not positive SFM launch exclusion. Concurrent-launch qualification remains a shipping blocker. |
| **C — Locking architecture** | **Accept.** One installed-publication protocol. Existing generic publishers remain build/development tools and must not be supported alternate writers to the live installation. |
| **D — Recovery guarantees** | **Accept.** Separate preservation, restoration of the pre-operation state, and restoration of working authority. They are different outcomes. |
| **E — Signing operations** | **Accept and narrow.** Recommend Ed25519 signatures, simple offline key custody, updater-delivered key changes, and explicit limits on freshness/revocation knowledge. |
| **F — Compatibility profiles** | **Accept.** A profile string alone is insufficient. Bind a supported contract to a signed software inventory and verify installed files. |
| **G — Overengineering** | **Accept in part.** Remove directory transactions, competing locks, automatic repair of unfamiliar content, and a growing updater-side application-hash registry. Retain one bounded worker process for compiler isolation. |
| **H — Discovery/customization** | **Accept.** Official and custom preparation converge on the same activation backend; their provenance remains distinct. |
| **I — Planned versus executed tests** | **Accept completely.** Revision 1’s matrix was a qualification plan, not executed stress testing. |
| **One-active-sidecar challenge** | **Retain with a narrower rationale.** It is an updater-owned release invariant, not a runtime requirement or permission to delete unfamiliar files. |
| **Governance correction** | **Accept.** All implementation belongs to an explicitly approved L plan. The prerequisite experiment requires separate authorization if performed before that plan. |

Two claims from Revision 1 are withdrawn:

1. **A directory swap protected by directory handles is not an established whole-tree transaction.**
2. **Two process checks do not establish comprehensive concurrent-launch safety.**

## B. Revised recommended architecture

### One concrete design

**Proposed:**

```text
Small Tkinter GUI
        │
        ▼
One bounded worker process
        │
        ├── Official package verification
        │
        └── Existing canonical compiler
                    │
                    ▼
          Validated candidate data set
                    │
                    ▼
       One installed activation/recovery backend
                    │
                    ▼
     Effective TXT + sole active sidecar + manifest
```

The two primary actions remain:

- **Get Official Data**
- **Rebuild My Data**

No service, automatic startup compilation, background update checker, software self-updater, or runtime lock handshake is introduced.

### Principal revision: leave the authority directory in place

Instead of moving the entire authority directory:

- inventory the supported data files;
- protect those files individually;
- move the old files into a transaction-specific recovery directory;
- move validated new files into vacant destinations;
- preserve the authority directory itself.

This removes directory-rename behavior, open-descendant complications and whole-directory ownership assumptions from the critical mechanism.

**Verified:** Windows exposes a handle-based file rename with explicit refusal when the destination exists. That is a smaller primitive to qualify than replacing a populated directory. [Microsoft `FILE_RENAME_INFO`](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_rename_info)

### Strongest materially different alternative

A runtime-authoritative generation pointer could make activation much smaller: prepare an immutable generation directory and switch one pointer.

I reject that alternative **for this release**, because:

- the current selector does not use the manifest as that pointer;
- native Rebuild reads the effective TXT at its established path;
- switching a pointer would not by itself switch that native source;
- implementing the alternative would change qualified runtime and installation semantics.

The fixed-path, recoverable file transaction is preferable within current scope.

### Why retain a worker process?

A GUI worker thread would be sufficient for responsiveness during ordinary I/O. It would not isolate a large compiler allocation or allow that work to be terminated independently.

**Proposed:** retain exactly one worker process, with a measured memory ceiling and bounded input sizes. It owns compilation and activation; there is no worker pool or general job framework. Windows Job Objects provide process-limit facilities if used for that ceiling. [Microsoft Job Object limits](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-setinformationjobobject)

The process is a resource boundary, not a claim of a security sandbox. Its limit must be qualified against supported custom inputs.

## C. Exact installation and activation contract

### C1. Support boundary

**Proposed first-release contract:**

- Supported Windows versions, explicitly listed by L.
- Local NTFS installation and transaction storage on the same volume.
- Standard qualified `usermod` Master resolution.
- No active software installation/update in parallel.
- SFM closed before activation.
- No simultaneous third-party writer to the managed authority directory.
- No symlink/reparse-point files inside the managed Master/authority/transaction slots.
- Installation aliases may resolve to the same physical installation; operations use the resolved, verified target.
- Unknown installation configuration refuses activation.

This does not change which models the Normalizer supports. It limits the external updater’s installation environments.

Do not use elevated privileges to force through denied file access. An administrator repairing installation permissions is a separate operation.

### C2. Filesystem layout

```text
<game>\usermod\cfg\
    sfm_defaultanimationgroups.txt
    sfm_shared_authority\
        sfm_master_<format>_<artifact-sha256>.sfmsidecar
        manifest.json

    sfm_character_tools_updater\
        installation.lock
        transactions\
            <unique-transaction-id>\
                intent.json
                journal
                candidate\
                snapshot\
                retired\
```

- `candidate`: validated new files.
- `snapshot`: verified copies of the pre-operation files.
- `retired`: original files moved out of active locations.
- None of these directories is scanned by the runtime.
- Recovery paths are derived from fixed layout rules and transaction IDs, never trusted arbitrary paths from a journal.

The initial product does not automatically prune recovery data.

### C3. Source selection

**Rebuild active TXT:** capture its exact bytes. The final activation must confirm those same bytes are still active. The TXT is not rewritten.

**Import another TXT:** capture an immutable copy, identify the target installation, and obtain explicit replacement consent. The external original is never modified. A changed input before final confirmation requires a new preview; after confirmation the selected snapshot, not a silently reread file, is the import authority.

**Official installation:** the authenticated package supplies both TXT and sidecar. Never combine its sidecar with unrelated current TXT bytes.

Replacement consent binds to the observed destination generation. If the destination changes before protection is acquired, re-present the decision rather than silently replacing the new contents.

### C4. One authoritative installed-publication lock

Open the permanent installation lock with:

- `CreateFileW`;
- `GENERIC_READ | GENERIC_WRITE`;
- sharing mode `0`;
- `OPEN_ALWAYS`;
- non-inheritable handle.

Ownership is the live handle. File existence is irrelevant.

The lock’s containing directory is not renamed or deleted. Alias resolution must reach the same physical lock file. A user without access refuses; the application does not create a per-user substitute.

On acquiring the lock:

1. Check transaction records.
2. Refuse an unknown transaction schema.
3. Reconcile interrupted work before starting another activation.

Process termination releases the OS handle; it does not erase the journal.

**Verified correction:** the existing named-mutex name incorporates a user SID, so it is not sufficient by itself to serialize different users modifying one installation. [Existing mutex construction](</E:/SFM Animation Group Master/tools/sfm_master_sidecar/win_named_mutex.py:119>)

### C5. Supported publication paths

The shipped GUI and any later advanced installed-update CLI must call this same activation backend.

The existing `publisher.py`, `mutex_publisher.py`, and compiler CLI remain:

- usable for building/exporting into non-live output directories;
- development infrastructure where appropriate;
- **not supported alternate installed-publication paths**.

Do not ship a shortcut or instruction that points the old CLI at the active authority directory.

An old development program can still bypass the protocol if deliberately used. The new lock cannot retroactively control it. Detect resulting unexpected state and refuse; do not claim mutual exclusion with nonparticipants.

### C6. Windows primitives

The critical file-operation proposal is:

| Purpose | Required operation |
|---|---|
| Create a candidate or backup file | `CreateFileW(..., CREATE_NEW, ...)`; write, check complete writes, flush and verify. |
| Protect an existing TXT being retained | `CreateFileW(GENERIC_READ, share=0, OPEN_EXISTING, ...)`. |
| Protect a file that will be moved | `CreateFileW(GENERIC_READ | DELETE, share=0, OPEN_EXISTING, ...)`. |
| Move that protected file | `SetFileInformationByHandle(FileRenameInfo)` with `ReplaceIfExists=FALSE`. |
| Pin/check directory identity | Directory handles using `FILE_FLAG_BACKUP_SEMANTICS`; identity inspection and no-delete sharing where applicable. |
| Commit journal content | Checked writes and `FlushFileBuffers` on a writable journal handle. |
| Release ownership | Explicit `CloseHandle` in release-owning cleanup. |

No `REPLACE_EXISTING`, cross-volume copy fallback, delete-on-close, POSIX replacement flags, or delayed-reboot move is allowed in this protocol.

Exclusive sharing excludes ordinary conflicting read/write/delete opens. Directory handles do **not** recursively lock their contents. [Microsoft `CreateFileW`](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)

The rename API reports success/failure through its return value and `GetLastError`; errors are followed by reconciliation where completion is uncertain. [Microsoft `SetFileInformationByHandle`](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-setfileinformationbyhandle)

**Unresolved:** the complete own-handle rename sequence, with these exact permissions and supported Windows/filesystem combinations, needs the prerequisite experiment. If it fails, do not weaken it to hash-then-overwrite.

### C7. Preparation and protection

Preparation performs all expensive work before activation:

1. Compile or verify the candidate.
2. Validate format, source binding, semantic parity and static runtime eligibility.
3. Write candidates outside the active directory.
4. Create verified snapshot copies.
5. Obtain confirmation.
6. Acquire installation lock and check SFM/process status.
7. Acquire all required protected file handles.
8. Revalidate bytes and physical identities through those handles.
9. Recheck the active-directory inventory.

Validation through ordinary path-based readers occurs before exclusive handles are taken. After protection, byte identity is checked through the held handles; do not reopen a file in a way that conflicts with the updater’s own sharing restrictions.

If any existing handle prevents acquisition, fail before changing active files.

### C8. Activation transitions and selection

Let:

- `M0`, `S0` be the old Master and selected sidecar;
- `M1`, `S1` be the candidate;
- `P` be the manifest.

All transitions are journaled before execution. Old files are moved, never deleted or overwritten.

| Transition | Active state if the updater dies immediately afterward | Runtime selection consequence |
|---|---|---|
| Protected and verified; no moves | Original files | Original behavior resumes after handles close. |
| Move old sidecar files individually to `retired` | `M0`, remaining old artifacts or none | An old matching artifact may remain selectable; otherwise unavailable. |
| Move old manifest to `retired` | `M0`, no old sidecars | No new authority is available. |
| Replacement/import only: move `M0` to `retired` | Master absent, no active sidecar | Suite authority acquisition must refuse. |
| Move `M1` into vacant Master path | `M1`, no active sidecar | Unavailable. For rebuild, the unchanged protected Master already occupies this role. |
| Move `S1` into its vacant active filename | `M1` and valid `S1`, manifest possibly absent | **The runtime can now select `S1` after protection disappears.** |
| Move candidate manifest into vacant `manifest.json` | Complete candidate set | Candidate is selectable; transaction still needs final verification. |
| Verify and record completion; release handles | Complete candidate set | Intended generation available. |

During live activation, the exclusive Master handle prevents new ordinary suite reads. The table deliberately describes **post-crash** states, when those handles have disappeared.

A valid new pair becoming usable before the manifest is installed is not mixed semantic authority. It is an incomplete updater transaction. Recovery can finish its metadata; the updater must not have reported completion already.

If `M0 == M1`, the TXT need not move. This includes ordinary local rebuilding.

If the existing set is already exactly the validated candidate, return a verified no-op rather than performing unnecessary moves.

### C9. Expected failures

- Sharing violation/access denied: no force-open; bounded retry only where justified.
- Destination already exists: preserve it; enter conflict handling.
- Missing source after an attempted rename: inspect both locations and their identities.
- Disk full/write fault: stop; use verified existing material only.
- Unknown error: preserve the error and observed state; do not translate it into “nothing changed.”

Unexpected files are never overwritten merely because the transaction expected an empty destination.

### C10. Durability

**Ordinary process termination:** recover from surviving files and the last complete journal records. This is the primary deterministic guarantee to qualify.

**Power loss/cache loss:** flush candidates, snapshots and journal records before advancing. Nevertheless, flushing a file is not proof that every related directory operation and storage-device cache has become durable. [Microsoft `FlushFileBuffers`](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)

**Storage failure:** the updater cannot guarantee preservation when the medium loses both originals and backups.

Therefore:

- promise verified preservation and recoverable interruption within the qualified storage boundary;
- do not promise unconditional power-loss immunity;
- never delete the last known original merely because another copy was once validated;
- after reboot, validate again rather than trusting `COMMITTED` text alone.

Hard-reset testing is required, but a successful finite campaign does not prove every storage controller honors persistence requests.

### C11. Concurrent SFM contract

**Decision: bounded fail-closed behavior, not launch exclusion.**

| Situation | Contract |
|---|---|
| SFM already running | Refuse activation. |
| SFM starts after initial check | Final check may detect it; otherwise file protection and consumer guards must determine safe ordering. |
| SFM starts between final check and protection | Either an existing conflicting operation prevents protection, or updater protection wins. Exact behavior requires qualification. |
| SFM starts while files are moving | New suite authority acquisition is blocked or sees unavailable/complete source-matching authority, depending on interruption/release timing. |
| A consumer already holds detached old authority | No updater promise of forcibly revoking it. Its existing operation-generation rules remain authoritative. |

The current Normalizer has a useful interlock: `native_master_protect_acquire()` holds a read handle denying writes/deletion across its protected hash, native Rebuild and contextual reconciliation. The updater’s exclusive/delete-access open conflicts with that handle.

I verified the inspected Normalizer file’s SHA matches the recorded `1f4ec5a2…` build. See [protection primitive](</E:/SFM Animation Group Master/audit_external_runtime/Rebuild_Control_Groups_Normalizer.py:356>) and [transaction gate](</E:/SFM Animation Group Master/audit_external_runtime/Rebuild_Control_Groups_Normalizer.py:11837>).

CPM uses operation-time generation authorization and then detached operation authority. It does not provide the same long-held Master file protection. An operation authorized before cutover may finish using that coherent old operation context; it is not automatically a mixed-generation operation. [CPM operation authorization](</E:/SFM Animation Group Master/cpm/app/SFM_Character_Preset_Manager.py:16361>)

**Limits:**

- This is not a guarantee about every native SFM menu action or third-party script.
- Process detection is advisory exclusion; file protection is access coordination.
- Unexpected launch must be qualified against both actual tools and SFM startup.
- If that test exposes unsafe native behavior, shipping is blocked. A runtime handshake or stronger exclusion would then require separate scope approval.

### C12. Recovery matrix

Recovery uses the same protected no-clobber move primitive. Rollback is not a separate unjournaled repair script.

| Observed state | Automatic action allowed | Preserve | Truthful result |
|---|---|---|---|
| Original state intact; activation never started | Abandon candidate transaction | Original and candidate evidence | “Nothing was installed.” |
| Complete validated candidate set | Finish transaction receipt | Old snapshot/retired files | “Installation recovered.” |
| Candidate Master and sidecar valid, manifest missing | Install the exact validated candidate manifest into a vacant path | Old state | “Installation recovered.” |
| Known partial transition; all required files verified | Resume recorded direction or restore original locations using no-clobber moves | Both generations | Report only after full-set verification. |
| TXT was already edited/stale before the attempt | Restore its exact pre-operation bytes if necessary | Edited TXT and stale prior artifacts | “Your previous files were restored; the data still needs rebuilding.” |
| TXT changed after crash | No automatic overwrite | New TXT, candidates and old copies | “Your TXT changed after the interruption. Choose which version to keep.” |
| Manifest backup exists but TXT/artifact is missing | No “working restore” claim | Everything available | “Automatic recovery is unavailable; required files are missing.” |
| Unfamiliar active files or hashes | Stop | All unfamiliar content | “The data folder changed. No files were overwritten.” |
| Rollback interrupted | Reconcile recorded reverse transitions against disk | Remaining copies and originals | Continue only when each move is unambiguous. |
| Unknown journal version | No mutation | Entire transaction | “Use a compatible updater to recover this installation.” |

An interrupted rollback records its target direction in the same transaction and preserves previous records. A second recovery attempt must be idempotent.

“No lost user data” and “automatically restored normal operation” are separate acceptance conditions. A preserved conflict is an acceptable outcome; fabricated automatic recovery is not.

## D. Standard official-release format

### D1. Version-1 distribution schema

Retain a five-file package:

```text
release.json
release.sig
sfm_defaultanimationgroups.txt
manifest.json
sfm_master_<format>_<artifact-sha256>.sfmsidecar
```

Proposed descriptor structure:

```text
schema: 1
object_type: "sfm-character-tools-data"
repository: fixed owner/name and repository identity
channel: "stable"
sequence: positive integer
data_version: display string
release_tag: exact tag
source_commit: full commit ID
published_at: UTC timestamp
minimum_updater_contract: integer
compatible_authority_profiles: list of supported profile IDs
sidecar_contract:
    format: integer
    semantics: integer
compiler_build: provenance identifier
signing_key_id: embedded-trust-store identifier
files:
    master:   {name, byte_length, sha256}
    manifest: {name, byte_length, sha256}
    sidecar:  {name, byte_length, sha256}
```

Strict schema rules:

- reject duplicate keys, unknown required semantics, wrong types and unsafe names;
- bound metadata before parsing;
- no executable hooks or installation paths;
- SHA-256 covers exact bytes;
- package filenames are fixed or derived from authenticated identities;
- descriptor compatibility cannot increase built-in admission limits.

The outer schema is independent of the existing sidecar format. Current format/semantics identifiers remain `0` unless separately changed and qualified.

### D2. Signature mechanism

**Recommended:** Ed25519 through the maintained Python `cryptography` library.

- `release.sig` is the detached signature over the **exact distributed `release.json` bytes**.
- The verifier does not parse and reserialize before checking.
- Producer serialization is deterministic UTF-8 with a documented newline policy.
- No Unicode normalization or alternate JSON interpretation is allowed.
- The bounded `signing_key_id` chooses only among embedded trusted keys.
- Verification failure, unsupported algorithm or unknown key refuses official installation.

The library supplies the signing/verification primitive and reports invalid signatures directly. No new cryptographic algorithm or key-exchange protocol is needed. [Cryptography Ed25519 documentation](https://cryptography.io/en/stable/hazmat/primitives/asymmetric/ed25519/)

### D3. Operational key model

For this project’s scale:

- One active release-signing key.
- Encrypted private key stored outside the repository and ordinary release-upload credentials.
- Offline encrypted backup held by the owner.
- Signing occurs after final artifact verification, before upload.
- Record descriptor hash, sequence, artifact hashes and signer in the release record.
- Never reuse a sequence for different descriptor bytes.

**Rotation:** ship an updater trust-store update first, then sign future releases with the new key.

**Loss:** restore the offline backup; if unavailable, issue a software update establishing a new trusted key.

**Compromise:** stop releases, publish an advisory and distribute an updater that revokes the compromised key. Do not authenticate emergency replacement trust solely with the compromised key.

**Bounded limitation:** an old/offline updater cannot magically learn a revocation. No claim otherwise.

This entails real maintenance, but remains proportionate if independent protection from compromised release-upload credentials is desired.

### D4. Freshness and ordering

Separate the five properties:

| Property | Evidence |
|---|---|
| Integrity | Payload hashes and binary integrity checks |
| Authenticity | Trusted signature |
| Provenance | Signed source/compiler metadata; optional attestations |
| Freshness | Release discovery and previously observed ordering |
| Compatibility | Installed-profile and artifact validation |

The signature authenticates `sequence`; it does not prove that a higher sequence has not been hidden.

**Proposed behavior:**

- Check GitHub only on explicit user action.
- Enumerate the applicable data releases; never use generic software “latest” as the decision.
- Persist the highest authenticated sequence/descriptor digest seen, separately from the installed version.
- A lower result never silently becomes the newest known release.
- Same sequence with different descriptor bytes is an error.
- An incomplete query is “Couldn’t check for updates.”
- Explicit offline install/downgrade does not lower the remembered high-water mark.
- A known newer but incompatible release produces “A newer release needs newer SFM Character Tools,” not “You have the latest data.”

**Important narrowing:** without a trusted freshness service or an established update framework providing that function, a first-time client cannot detect all suppression/replay by a compromised distribution account.

The ordinary UI should say **“Official data [version] is available”**, not make a cryptographic claim that it is globally newest. The normal online path selects the highest compatible release returned by a complete discovery.

If resistance to first-contact freeze attacks is required, that is a stronger product requirement; adopt an established update framework rather than inventing a signed timestamp protocol here.

### D5. Deleted, replaced and immutable releases

- Download disappearance: leave installed data alone.
- New authenticated replacement: new sequence and tag.
- Different bytes under a previously observed identity: refuse.
- Offline signed package: same validation and activation path, with freshness/revocation knowledge explicitly limited.
- Removed GitHub release: removal alone does not prove cryptographic revocation of an offline copy.

Enable immutable GitHub releases where available. They protect published assets/tags and provide release attestations, but their “latest” designation remains editable. They supplement, rather than replace, local signature verification and compatibility checks. [GitHub immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)

### D6. Why not GitHub-only trust?

GitHub-only trust removes private-key management and a signature dependency. It still supports TLS, checksums and immutable releases.

What it loses is independent rejection when an attacker controlling release publication supplies both altered payloads and matching hashes.

**Recommendation: retain independent signatures**, with the limited key-management model above. Do not add a custom online revocation hierarchy.

## E. Runtime compatibility contract

### E1. Actual boundaries

The inspected system distinguishes:

- binary format and authority semantics;
- exact validator/provider implementations;
- runtime API/build identity;
- installed import/origin/layout;
- consumer projection and generation contracts;
- request-aware and aggregate resource admission.

The runtime API is `1.0.0-b2a`; its build identity is `package-boundary-corrected-2026-09-22`. CPM checks these independently rather than accepting whatever the loaded package declares. [CPM canonical bootstrap](</E:/SFM Animation Group Master/cpm/convergence/cpm_authority_adapter.py:53>)

The provider/validator dependency loader additionally verifies exact source hashes. [Sidecar contract loader](</E:/SFM Animation Group Master/tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/sidecar_contract.py>)

Therefore optimistic version comparison is insufficient.

### E2. Minimal profile plus signed software inventory

**Proposed:**

1. The software release producer creates a signed installation inventory.
2. It lists the immutable shipping files, hashes, layout contract, authority profile ID and consumer contracts.
3. The updater verifies that signature.
4. It hashes the installed executable dependency closure against that inventory.
5. It accepts only authority profile contracts it implements.

Mutable TXT, compiled artifacts, presets and logs are not immutable application files.

This avoids embedding an ever-growing list of full application hashes inside the updater. Hashes live with the signed software release; the updater recognizes a small set of authority contracts.

For the present monolithic consumers, verifying the complete relevant app/launcher files is preferable to brittle “hash these selected functions” extraction.

### E3. Profile contents

A profile must bind:

- profile schema/ID;
- supported installation-layout contract;
- sidecar format/semantics;
- validator/provider contract identity;
- runtime API/build compatibility;
- Normalizer and CPM consumer/projection contract IDs;
- Master path-resolution contract;
- static admission implementation and configured limits;
- installed-publication protocol version;
- accepted executable/source/bytecode deployment policy.

The installed receipt is not self-authenticating. A signed inventory plus matching files establishes a known on-disk release; an unsigned version string does not.

Future software releases can use an existing profile only when their release qualification justifies that declaration. A new contract requires updater support.

Unofficially modified scripts: refuse automatic installed activation under a claimed official profile. Compilation/export can remain available without claiming that installation is supported.

### E4. What the updater can and cannot establish

| Layer | Updater claim |
|---|---|
| Release metadata says compatible | Verified statement from authenticated metadata |
| Installed software matches known profile | Verified inventory and file identity |
| Sidecar matches TXT and semantics | Structural/integrity/source/parity validation |
| Artifact passes static resource eligibility | Verified against that profile’s bounded admission rules |
| Arbitrary future SFM workload succeeds | **Not established** |

A correction to the earlier design is necessary: the 20,000-occurrence family check is applied to requested families in cumulative admission. It must not silently become a new global compiler rejection rule.

Likewise, empty-request admission is not proof that every future projection or combined retained view will fit. The live broker remains responsible for live request admission. [Cumulative resource admission](</E:/SFM Animation Group Master/tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/resource_estimator.py:678>)

The updater’s external 64-bit success cannot be presented as a measurement of embedded 32-bit SFM headroom.

## F. User workflow

### Official update

1. User chooses **Get Official Data**.
2. The updater checks compatible official releases.
3. It displays version and target installation.
4. If replacing modified/unrecognized source, it asks explicitly.
5. It prepares everything before requesting SFM closure.
6. It activates and verifies.

Declining replacement changes nothing. A newer official version does not mean customized data is defective.

“Recognized official TXT” means its exact SHA matches authenticated official metadata. A receipt alone is insufficient. The artifact may still be locally rebuilt; source provenance and artifact provenance are recorded separately.

### Rebuild

**Rebuild My Data** compiles the active TXT using generic compiler acceptance, not stricter official-release policy.

If the TXT is valid but the sidecar is missing, this is the normal repair path.

A local result is labeled **locally rebuilt**, even if the source happens to be byte-identical to an official Master.

### Import

**Use Another TXT…** shows:

> Use this file as the animation-group data for this SFM installation? Your current file will be kept in a backup.

The selected external file is never treated as active until installed successfully.

### Recovery

When an unfinished transaction exists, replace the normal actions with one relevant recovery action and a short explanation.

Examples:

- “The update was interrupted. Close SFM, then recover the installation.”
- “Your TXT changed after the interruption. Both versions have been kept.”
- “Your previous files were restored. Rebuild the data before using the tools.”

Do not say “restored successfully” when only a stale pre-operation arrangement was restored.

### Minimal interface retained

Two primary buttons, installation selector, occasional confirmation, progress and Details.

No background GitHub polling, persistent warning panel, automatic merging or maintenance dashboard.

## G. Adversarial evidence and qualification matrix

**All experiments below are proposed. None ran during this review.**

| Rank / guarantee | Violation and relevant evidence | Deterministic proof required | PASS / FAIL and consequence |
|---|---|---|---|
| **Blocker — protected source identity** | Editor writes/replaces TXT between recheck and move. Exclusive sharing is documented; full own-handle sequence unqualified. | Competing in-place writer and atomic-save editor at each barrier; rename using the held handle. | PASS: writer refused or updater stops without losing either version. FAIL: unseen overwrite or stale activation; reject primitive. |
| **Blocker — no-clobber** | File appears at a destination just before rename. API supports refusal. | Create occupied TXT, sidecar and manifest destinations immediately before each move. | PASS: occupant preserved and transaction conflicts. Any overwritten occupant rejects implementation. |
| **Blocker — one publication owner** | Two users/aliases/versions obtain different locks. Existing named mutex is per-user. | Race processes through same physical slot, including alias and cross-user cases. | PASS: one live owner; denied permissions never create another lock location. |
| **Blocker — safe suite concurrency** | SFM or an operation starts during activation. Normalizer interlock verified; whole scenario unproven. | Pause at protection and every rename; launch actual SFM and exercise both consumers, including retained CPM scope. | PASS: coherent completed operation, explicit refusal, or verified new generation; no mixed mutation or unsafe native behavior. Otherwise shipping blocked. |
| **Blocker — process-crash recovery** | Process dies after a successful rename but before journal update. | Terminate after every write/rename boundary, then recover twice. | PASS: verified old/new state or preserved conflict; second recovery changes nothing. No false success. |
| **Required qualification — power interruption** | Data/journal/namespace persistence differs. File flush is not universal storage durability. | VM hard resets at persistent boundaries; inspect all copies before recovery. | PASS: documented recovery behavior within tested storage assumptions. Missing irreplaceable data prevents durability claims and may block chosen protocol. |
| **Blocker — post-crash edit preservation** | User changes TXT before recovery. | Edit/replace it in every partial state and interrupt recovery again. | PASS: newer bytes retained; no automatic destructive restore. |
| **Blocker — complete recovery evidence** | Manifest present but required source/artifact missing or corrupt. | Remove/corrupt each recovery component independently. | PASS: no working-restore claim; surviving files preserved. |
| **Blocker — deterministic active selection** | Multiple matching artifacts or an unreferenced candidate wins. Selector behavior verified. | Seed lexical-order conflicts; inspect exact final inventory and run unchanged selector. | PASS: intended sole active artifact selected. Unexpected content causes refusal, not deletion. |
| **Blocker — authenticity/integrity** | Correct names, wrong content; coordinated asset replacement. | Alter each payload, metadata, signature and key ID; use valid wrong-source binary. | PASS: official activation refused before live writes. |
| **Required qualification — ordering honesty** | Replay older signed release or hide known newer one. | Feed lower sequence, conflicting same sequence, partial listings and offline downgrade. | PASS: no silent rollback/newest claim; explicit older installation possible. First-contact suppression remains a disclosed limit. |
| **Blocker — compatibility** | Signed metadata but modified installed provider/consumer, unsupported profile or oversized artifact. | Change each compatibility-bound file; exercise profile and resource boundaries. | PASS: refuse or report exactly bounded eligibility; never equate compile success with universal SFM admissibility. |
| **Blocker — path confinement** | Junction change, archive traversal, misleading installation or hard-linked mutable target. | Replace path components at barriers; malformed ZIP/path fixtures. | PASS: no write outside verified slot; unsafe target refused. |
| **Required qualification — resource/UI containment** | Compiler allocations exhaust worker, GUI closes, antivirus blocks rename, disk fills. | Force allocation limit, kill GUI/worker, deny each operation and exhaust staging space. | PASS: no false success; recoverable transaction; supported inputs still complete. |
| **Blocker — clean-machine portability** | Hidden repository imports or alternate publisher entry point. | Shipping bundle without Python/Git/developer paths; inspect all installed-write routes. | PASS: both workflows use one activation backend. |
| **Accepted bounded limitation — noncooperating actors** | Third-party program or administrator changes files outside protocol. | Inject detectable changes; verify preservation/refusal. | No promise of control over arbitrary privileged mutation. Unsupported simultaneous writers must not be advertised as safe. |
| **Deferred — full freshness/revocation service** | Offline or first-time client lacks current trust information. | Not required for first release’s stated trust boundary. | Add an established update framework only if owner requires stronger freshness guarantees. |

### One-active-sidecar disposition

The runtime can legitimately encounter multiple generations under historical publishing arrangements. Same-source artifacts are not proven interchangeable merely by sharing a source hash: different compiler semantics or malformed-but-structurally-valid content can matter.

A narrower rule—“the intended artifact sorts first”—would be fragile and preserve unnecessary scan cost.

**Retain one active artifact as the updater’s completed-state invariant.** But:

- unfamiliar content is not automatically garbage;
- recognized historical data can be preserved outside the scan root after explicit migration authorization;
- first-release automatic activation should refuse unrecognized content;
- directory handles do not prevent every new child insertion;
- third-party simultaneous publication remains outside the supported ownership contract.

## H. Reduced-complexity assessment

| Revision | Reason and preserved guarantee |
|---|---|
| **Remove whole-directory swaps** | Avoid populated-directory rename assumptions. Protected file moves retain no-clobber and recovery behavior. |
| **Use one installed-publication lock** | Eliminate conflicting supported ownership schemes. |
| **Keep one activation backend for both workflows** | Download and compile differ only in candidate preparation/provenance. |
| **Use one transaction journal for forward and reverse recovery** | Avoid separate repair machinery with different safety rules. |
| **Refuse unfamiliar layouts/content** | Avoid becoming a general reconciliation or mod-management tool. |
| **Signed software inventory instead of updater hash registry** | Verify real installed bytes without updating the updater for every unrelated UI edit. |
| **Keep one bounded worker process** | Resource containment is material; no pool, service or complex scheduling. |
| **Keep Tkinter and one-folder packaging** | Adequate interface with no SFM/Qt coupling. Final bundle size/startup behavior remains packaging evidence. |
| **No online key-management subsystem** | Key changes arrive through software releases; limitations are explicit. |
| **No automatic backup pruning or merging** | Avoid irreversible policy unrelated to the two essential workflows. |
| **No runtime handshake yet** | Existing qualified semantics remain unchanged unless the concurrency experiment proves a specific need. |

The hardened publisher should supply reusable compilation, validation and reconciliation primitives. Its manifest-only transaction must not be copied into a second “almost identical” installed publisher.

## I. L integration roadmap

All stages below are **unapproved proposals**.

### Stage 0 — Resolve the Windows primitive and concurrency prerequisites

**Permitted scope:** a separately authorized disposable-file Windows experiment, followed by a bounded real-SFM concurrency test on recoverable fixtures.

**Deliverable:** exact operation trace, handles/flags, outcomes and recovery states.

**Tests:** protected own-handle rename, destination collision, editor race, process kill, alias/user lock contention, Normalizer protection overlap, CPM operation overlap and unexpected SFM launch.

**Acceptance:** file primitives establish the stated invariants; actual consumers complete coherently or refuse.

**Stop:** any lost edit, silently overwritten destination, accepted mixed authority, or unsafe native behavior. Do not proceed to a GUI implementation to work around a failed transaction proof.

This is the prerequisite experiment I recommend authorizing separately if L cannot yet include it. It has not been initiated.

### Stage 1 — Freeze L’s portable packaging and trust contracts

**Scope:** final layout, signed software inventory, compatibility profile, official package/signature format, canonical compiler/validator closure, and menu-path migration plan.

**Deliverable:** one release specification and reproducible build recipe.

**Tests:** clean-directory imports, deterministic compilation/parity, profile verification and dependency inventory.

**Acceptance:** no developer paths; one compiler; no conflicting live publisher; no duplicate authority package.

**Stop:** missing portable validation closure, unresolved import ownership or unsupported installed identity.

### Stage 2 — Implement the backend and minimal GUI

**Scope:** only the approved two-workflow utility and shared activation/recovery backend.

**Deliverable:** packaged candidate plus offline fault-injection results.

**Tests:** remaining matrix rows, including interrupted rollback, source races, corruption, disk/access failures and offline installation.

**Acceptance:** truthful outcomes, preserved customizations, supported-data success, no runtime fallback.

**Stop:** any false success, data-loss path, or unbounded recovery retry.

### Stage 3 — Qualify the actual installed suite in L

**Scope:** clean install, upgrade, `SFM Character Tools` menu migration, official update, custom rebuild/import, recovery and shipping-artifact use by both tools.

**Deliverable:** exact shipping hashes and installed-release evidence.

**Acceptance:** both tools import one canonical authority package and consume the intended generation; custom data survives upgrades; no stale menu/package copies or workstation dependencies.

**Stop:** installed-artifact regression, duplicate ownership, authority mismatch, or publication bypass.

K remains closed. R15’s module/window lifecycle remains unchanged. Any necessary path adaptation belongs to L and gets targeted qualification.

## J. Owner approval decisions

**Already approved:** SFM Character Tools branding/menu direction, external utility, official downloads, local rebuilding, preservation of custom data, and no runtime fallback.

**Still pending:**

1. **Authorize the bounded prerequisite experiment**, either separately or as the first explicit L milestone. It is needed before the activation design can be frozen.
2. **Approve the first-release support boundary:** standard qualified `usermod`, local NTFS, specified Windows versions, SFM closed, and refusal of unknown layouts or simultaneous nonparticipating writers.
3. **Approve independent signatures and key custody**, including the explicit limitation that old/offline clients cannot obtain instantaneous revocation or absolute freshness knowledge.
4. **Approve the revised failure policy:** preserving a conflict or restoring an already-stale pre-operation state is acceptable when automatic repair would risk losing edits.
5. **Approve the bounded L roadmap**, including one installed-publication protocol and signed installed-software inventory.

**Final position:** Revision 2 is a defensible candidate design, with a materially smaller activation mechanism. It is not yet a proven Windows transaction. The next decision should authorize the narrow prerequisite experiment—not production implementation or a broader architecture search.