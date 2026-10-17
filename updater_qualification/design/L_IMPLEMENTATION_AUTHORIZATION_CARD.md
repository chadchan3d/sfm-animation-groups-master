# L Implementation Authorization Card — Offline Updater v1

**Status: APPROVED by the owner on 2026-10-16,** together with the Offline Updater v1 Contract Amendment (the
"Amendment"). Approving this card authorizes no increment. Each of L-1 … L-6 requires its own authorization.
L-1 (§8) is **ready for authorization; it is not authorized and not started.**

**Date:** 2026-10-16. **Repository checkpoint:** `27aa6727902e674641ce8ea637a81058b2d5640b`.

**Governing documents:** R2 `61cf8ed5…` as amended; R15 `f6b3580c…`, which is unchanged.

## 1. Purpose and boundary

This card builds the usable first-release External Updater described by R2 §B, under the Amendment's offline
contract. It contains:
- a small Tkinter GUI;
- **three equally prominent primary buttons**, labeled exactly **Get Official Data**, **Rebuild My Data** and
  **Use Another TXT** (no ellipses). All three are in the initial release and all three converge on the same
  backend (Amendment §2.1);
- the existing canonical compiler and validator;
- one bounded worker process;
- one protected installed-publication backend;
- customization preservation and no-clobber installation;
- interrupted-transaction reconciliation and recovery;
- signed official package verification;
- compatibility and installation validation;
- final one-folder packaging.

**Not in scope:**
- redesign or a new architecture search;
- live or concurrent updating;
- a service, launch interceptor or background polling;
- any publication path for a primary action other than the one backend;
- a software self-updater;
- automatic pruning or merging;
- a runtime handshake;
- native-concurrency, WPR/ETW or DMX-oracle campaigns;
- any change to R15, CPM, the Normalizer, the production authority package or the sidecar format.

## 2. Reuse map

There are three reuse classes:
- **Unchanged dependency:** imported as-is and pinned by hash.
- **Ported mechanism:** code moved from the prototype into the product with a recorded diff. Its equivalence is
  established by re-running the ported P1 case suite against product code. P1 results are **not** carried over
  by assertion.
- **New:** no prior equivalent exists.

| Product responsibility | Source | Class | Identity |
|---|---|---|---|
| Canonical compile | `tools/sfm_master_sidecar/compiler.py`: `SourceSnapshot`/`capture_source_snapshot`, `parse_and_compile(snapshot, official_policy)`, `self_validate_from_bytes`, `self_validate_from_path`, `generation_basename` | Unchanged dependency | `50dd1804…` |
| Manifest | `tools/sfm_master_sidecar/manifest.py`: `build_manifest_dict`, `serialize_manifest`, `parse_manifest_bytes` | Unchanged dependency | `edc64667…` |
| Reader and format, Master core | `tools/sfm_master_sidecar/{reader,format,writer}.py`, `tools/sfm_master_core.py` | Unchanged dependency | reader `1b95261c…`, core `a76e7e4e…` |
| FINAL R3-A2B admission | `candidate_packed_validator_r3a2b.py`, `candidate_packed_provider_r3a2b.py` (production authority package) | Unchanged dependency, hash-pinned as in P1 `_load_provider()` | `74fe8d96…`, `d6ef9650…` |
| Win32 primitives | U0A/P1 `w32.py`: `create_file`, `rename_by_handle(ReplaceIfExists=FALSE)`, `flush`, `file_id`, `std_info`, `final_path`, `open_dir`, `path_identity`, `write_new_file`, `sha_handle` | Ported mechanism (byte-identical start; trace made optional) | `c7c21a5f…` |
| Layout, alias resolution, reparse refusal | P1 `p1proto.py` `resolve_installation`, `Layout` | Ported mechanism; the scratch-root refusal becomes a configured-installation check | `537739ff…` |
| Journal | P1 `_line`, `parse_journal`, `Journal` | Ported mechanism; the product schema ID is new | `537739ff…` |
| Plan, transitions and final verification | P1 `make_plan`, `expected_states`, `observe_slots`, `match_state`, `describe_divergence`, `execute`, `verify_final`, `activate` | Ported mechanism (C6–C8 order unchanged) | `537739ff…` |
| Recovery | P1 `transaction_status`, `recover`, `recover_one` | Ported mechanism (C12) | `537739ff…` |
| Candidate compile and validation | P1 `compile_real`, `validate_candidate_files` | Ported mechanism | `537739ff…` |
| Replacement route: captured immutable source copy; M0 retired, M1 moved into the vacant Master path (used by Use Another TXT and Get Official Data) | P1 `activate` replace kind with `--source` (P1 A1 import, D source-change-after-capture cases) | Ported mechanism; ported in L-1, exposed in L-2 | `537739ff…` |
| Legacy `publisher.lock` | P1 `classify_legacy_lock`, `hold_legacy_lock` | Ported mechanism | `537739ff…` |
| A3 process gate | P1 `p1common.process_status`, `process_gate` (tasklist CSV; RUNNING/CLEAR/UNKNOWN) | Ported mechanism; injection hooks are test-only | `db95a42d…` |
| Messages | P1/U0A `MESSAGES` plus the Amendment §2.1 step 6/7 text | Ported, then extended | — |
| Exact-token barriers and kill harness | U0A `racer.py`, P1 `p1run.py` | Test infrastructure only; not shipped | `c74c32ad…` |
| Correspondence verification (Amendment step 7) | Composed from the compiler, reader, R3-A2B and the path budget | New, built on existing parts | — |
| Worker process and Job Object memory ceiling | — | New | — |
| Tkinter GUI (three primary buttons, file picker for Use Another TXT, consent preview) | — | New | — |
| Official package parse, Ed25519 verification and high-water mark | — | New (R2 D1–D5; `cryptography` dependency) | — |
| Release producer (build, sign and record a package; key outside the repository) | — | New, development-side | — |
| GitHub discovery and download (explicit user action only) | — | New | — |
| Authority profile and signed software inventory check | — | New (R2 E2–E3) | — |
| One-folder packaging and clean-directory closure | — | New | — |

**Sanitization for the port:** the P1 harness is private evidence. The ported product code must contain:
- no scratch-root or evidence constants, workstation paths or user names;
- no test-injection paths reachable in the shipped build.

Injection exists only behind a test-only module.

## 3. Planned source layout (new; existing files untouched)

```text
updater/
  sfm_character_tools_updater/
    __init__.py         version, product schema IDs
    w32.py              ported Win32 primitives
    layout.py           C1/C2 resolution, alias identity, reparse/hardlink refusal, consumer path budget
    process_gate.py     A3 RUNNING / CLEAR / UNKNOWN
    journal.py          journal format, torn-tail handling, unknown-schema refusal
    candidate.py        compile and validation through the unchanged compiler + pinned R3-A2B admission
    legacy_lock.py      publisher.lock classify / hold / verify
    backend.py          prepare() for rebuild / another TXT / official, install() (C7–C8),
                        verify_correspondence() (Amendment step 7)
    recovery.py         status(), recover() (C12)
    messages.py         truthful outcome text
    worker.py           the bounded worker entry: one JSON request in, one JSON result out
    official/           (L-2/L-3) package.py, signature.py, highwater.py, discovery.py
    compat/             (L-5) profile.py, inventory.py
    gui/                (L-4) app.py
  tests/                scratch-only suites; never touch a live installation
  packaging/            (L-5) build recipe
```

**Dependency rule:** `tools/sfm_master_sidecar`, `tools/sfm_master_core.py` and the production authority package
are consumed by **pinned copy or import, never modified**. L-5 decides how the shipping bundle carries them.

## 4. Integration points

1. **The installed layout (R2 C2):**
   - `<game>\usermod\cfg\sfm_defaultanimationgroups.txt`;
   - `sfm_shared_authority\{sfm_master_0_<sha>.sfmsidecar, manifest.json, publisher.lock}`;
   - the new `sfm_character_tools_updater\{installation.lock, transactions\…}`.
2. **The consumers, read-only (no change):**
   - the selector's source-hash rule, which reads only `*.sfmsidecar`;
   - the CPM relative Master path (`filesystem.valve.mod()` + `cfg`);
   - the Normalizer `native_master_protect_acquire` read handle. The updater sees it as a sharing violation and
     abandons before any move.
3. **The legacy publishers.** These are export and development tools only (C5). The updater recognizes
   `publisher.lock` and holds it during protection.
4. **The installed software inventory (L-5):** a hash check of the installed CPM, Normalizer and authority
   package closure against the signed inventory, together with the runtime API `1.0.0-b2a` and the build
   `package-boundary-corrected-2026-09-22`.
5. **The release producer (L-2):** a repository-side tool that compiles with `official_policy=True`, writes the
   five-file package and signs `release.json`. The private key lives outside the repository.

## 5. Increments

Each increment requires a separate authorization and returns a report with hashes. Each later increment
builds on the committed previous one.

| Increment | Deliverable | Acceptance | STOP |
|---|---|---|---|
| **L-1** Activation backend and Rebuild My Data (headless) | The backend package (layout, gate, journal, candidate, legacy lock, backend, recovery, messages, worker entry) and the ported P1 suite | §8 | §8 |
| **L-2** Replacement workflows: Use Another TXT, and official package from a local file | **Use Another TXT** backend path: an immutable captured copy, compiled by the same canonical compiler, with a destination preview and consent bound to the observed destination generation, installed through the same backend replace route. The external file is never modified. **Official package**: the package parser (strict D1 schema; bounded, no duplicate keys); Ed25519 verification against embedded keys; the high-water store; the Get Official Data backend path from a **local package file** through the same replace route. Also the release-producer tool and a test key that is never a release key. | Group 1 package and import-source cases; tamper of each file, signature and key ID refused before any live write; sequence and replay rules; replacement of customized TXT only with consent; the external source unchanged and the previous Master preserved and recoverable; a change to the source after capture installs the captured copy | A verifier accepts an altered package. The key appears in the repository. A second publication mechanism is introduced. The external source is modified. |
| **L-3** Discovery and download | Explicit-action GitHub release enumeration; bounded download into staging; "Couldn't check for updates" on any incomplete query | Partial or failed listing is truthful; no generic "latest"; the newer-incompatible message | Network on any path other than explicit user action |
| **L-4** GUI and bounded worker | Tkinter GUI with **three equally prominent primary buttons** labeled exactly "Get Official Data", "Rebuild My Data" and "Use Another TXT" (no ellipses, none in a menu). Also: an installation selector, the Use Another TXT file picker and the consent preview, progress, Details and the recovery mode. A worker process under a Job Object memory ceiling. Truthful step-6 and step-7 messages. | All three actions run end-to-end through the worker and the one backend. Group 4 containment: worker killed or over its limit and GUI closed mid-run → recoverable, no false success. Supported inputs complete under the ceiling. | The GUI reports success without verified state. Any action bypasses the backend. |
| **L-5** Compatibility and packaging | Authority profile; signed software inventory check; one-folder bundle; clean-directory dependency closure; a reproducible build recipe | Group 1 compatibility cases; no developer paths or repository imports; one compiler; one backend; no installed-write route other than the backend | Unresolved import ownership or missing validation closure |
| **L-6** Release qualification | The five groups (§6) on the exact shipping candidate | All five groups PASS | Any false success, data-loss path, overwritten occupant, mixed authority or unsafe native behavior observed during closed-SFM use |

## 6. Finite release qualification (L-6)

Every group is run against the **exact shipping candidate**. In L-1 to L-5, the same cases run against the
development tree as development evidence. **Every group covers all three primary actions**, so the matrix is
finite: the cases below, each run per relevant action, plus nothing open-ended.

### Group 1 — Candidate and package acceptance

- **Cases:**
  - real compilation of the live-equivalent G1 Master; it must reproduce the known sidecar and manifest
    byte-for-byte, as in P1-F5;
  - a CRLF custom source, through Rebuild My Data and through Use Another TXT;
  - malformed, truncated and oversized sources, through Rebuild My Data and Use Another TXT, refused with
    nothing created;
  - Use Another TXT: an unreadable or vanished selected file, refused; the external file is unchanged in every
    case;
  - official package tamper: each of the five files, the signature, the key ID, an unknown key and a valid
    package from the wrong source;
  - sequence replay or downgrade, and the same sequence with different bytes;
  - compatibility: a changed installed consumer file and an unsupported profile;
  - a consumer path budget of 260 characters or more, refused.
- **Reuse:** P1 A1–A7 and E1–E12 mechanisms, through the ported suite.
- **Release decision affected:** whether the updater installs only authentic, compatible, valid data.

### Group 2 — Offline activation and refusal

- **Cases:**
  - both A3 gates for RUNNING and every UNKNOWN form (P1 J1–J10, ported), for each of the three actions;
  - **real detection:** with an actual SFM open (ordinary launch, no fixture, no authority change, closed without
    saving), Install refuses at the first gate and Recovery refuses, with nothing changed;
  - lock held by another process;
  - same-account alias races (P1 F1–F5);
  - a held legacy `publisher.lock` (P1 G1–G9);
  - a Normalizer-style share-read handle on the Master, refused before any move (P1 I2);
  - preparation for each of the three actions while SFM runs writes nothing to the Master or authority paths.
- **Decision:** whether the offline boundary is enforced as stated.
- **Reason for the one new real-SFM case:** real detection was never exercised. P1 used injected responses. It
  is the only enforcement of the boundary.

### Group 3 — Preservation and interrupted-operation recovery

- **Cases:**
  - kill at every journaled barrier for the rebuild route and the replace route. The replace route serves both
    Use Another TXT and Get Official Data, and each action is exercised at least at the barriers around
    the M0 and M1 moves;
  - rollback at each moved point;
  - recovery killed and then recovered;
  - a second recovery is a no-op (P1 B, 66 cases);
  - newer TXT edits preserved as CONFLICT (P1 C1–C5);
  - occupied destinations and substitutions (P1 D);
  - torn or missing journal, unknown schema, and missing or corrupt recovery components (P1 E);
  - recovery after a process restart revalidates disk state without trusting the journal text;
  - customized TXT survives a declined official or Use Another TXT replacement byte-for-byte;
  - after Use Another TXT, the previous Master and its authority are preserved in recovery storage and verified.
- **Decision:** whether user data survives interruption and whether recovery is truthful.
- **Note:** this group replaces hard-reset testing; it is **not** power-loss evidence (L-B).

### Group 4 — Failure containment and truthful reporting

- **Cases:**
  - worker killed or over its memory limit, and GUI closed during preparation and during installation;
  - disk-full simulation in staging;
  - sharing violation or access denial on each protected file;
  - a step-7 correspondence failure;
  - the step-7 report when the status changed;
  - the message for every C12 row (including stale restoration and CONFLICT locations, P1-F3);
  - no outcome text claims success without verified state;
  - the provenance wording is correct for each action ("official [version]", "locally rebuilt", "installed from
    another TXT").
- **Decision:** whether every failure is contained and reported truthfully.

### Group 5 — Final installed-product qualification with both SFM tools

- **Setup:**
  - the packaged updater runs on the real installation with SFM closed;
  - Rebuild My Data on the current G1 gives a verified NOOP;
  - **Get Official Data** with an L-2-produced test-signed package of a semantically changed generation (a G3
    pair, or an owner-approved equivalent);
  - **Use Another TXT** with a preserved copy of the G1 Master selected from outside the installation, which
    restores G1. The selected file must be unchanged afterwards.
- **Cases:** after each install, reopen SFM on a disposable session (no real project, no save) and confirm:
  - CPM and the Normalizer each acquire authority for the installed generation, through their ordinary
    operations and logs;
  - the changed control resolves to its new group in the tools' lookup;
  - after restoring G1, the installation is exactly G1 again (byte-identical Master, sidecar and manifest).
- **Not included:**
  - no DMX oracle;
  - no tracing;
  - no SFM launched during installation;
  - native channel and key preservation under Rebuild is the existing Normalizer behavior qualified in K, not an
    updater claim.
- **Decision:** whether both shipped tools consume the updater's installed authority.
- **Before execution:** this group requires its own execution authorization, with an exact restoration plan.

**Additional qualification:** permitted only under the Amendment §6 rule, naming the risk, the release
decision and the smallest decisive test.

## 7. Dependencies and preconditions

- **Python runtime:** Python 3.10 x64 for the updater, as used in P1. The `cryptography` package is needed from
  L-2.
- **Packaging tool:** chosen in L-5.
- **Signing:** an owner-held release key before the first real release. L-2 to L-5 use a test key only.
- **Scratch qualification:** a dedicated E: scratch root outside every SFM search, config and script root, plus
  a write guard, as in P1.
- **No live installation write** until L-6 group 5 is authorized.

## 8. L-1 coding assignment (ready for authorization; NOT AUTHORIZED, NOT STARTED)

L-1 is the first substantive coding milestone. **Get Official Data** and **Use Another TXT** follow in L-2 (their
backend paths) and L-4 (their GUI buttons). Both are required before release.

### L-1 — Activation backend and Rebuild My Data (headless)

**Objective:** produce the working product backend that performs Rebuild My Data end-to-end on a scratch
installation:
- prepare;
- process gate;
- installation lock;
- protected journaled installation;
- final verification;
- TXT/SIDECAR correspondence check;
- truthful report;
- recovery.

It is driven by the worker entry point. The GUI comes later and calls this same backend.

**Build** (`updater/sfm_character_tools_updater/`, Python 3.10):
1. Port `w32.py` and the P1 activation and recovery mechanism into:
   - `layout.py`, `journal.py`, `candidate.py`, `legacy_lock.py`;
   - `backend.py`, `recovery.py`, `process_gate.py`, `messages.py`.
2. Keep the C6–C8 move order, the own-handle no-clobber rename, protection through final verification, and C12
   recovery **semantically unchanged**.
3. Record every non-mechanical change from `p1proto.py` `537739ff…` in an equivalence table.
4. Split `prepare()` from `install()`:
   - `prepare()` compiles and validates into updater-private staging. It is permitted with SFM running.
   - `install()` runs gate → lock → gate → protection → moves → verification → release, and then
     `verify_correspondence()`.
5. The product transaction schema has a new ID. A P1 or U0A schema is treated as unknown: recovery refuses
   without mutation.
6. Add the Amendment §2.3 consumer path budget (refuse at 260 characters or more) and the step-7 post-install
   process-status recheck.
7. Port the replace route (captured-source replacement), and exercise it with the ported P1 import and
   source-change cases. It is not exposed as a worker command in L-1. L-2 exposes it for Use Another TXT and
   Get Official Data, unchanged.
8. `worker.py`: `python -m sfm_character_tools_updater.worker {status|prepare-rebuild|install|recover}
   --installation <cfg> --result <json>`, with exactly one JSON result. Per R2 C5 this is the backend's own
   entry, not an alternate publisher.
9. Use the unchanged compiler, manifest and reader, and hash-pinned R3-A2B admission. Do not modify `tools/`.

**Tests** (`updater/tests/`, scratch only):
- Port the P1 controller and cases for categories A, B, C, D, E, F, G, J and K to run against the product
  worker.
- Port H1–H2 and I1–I2 the same way, run as in P1: the SFM-bundled Python 2.7 is run **outside SFM**, read-only,
  with `-B`, in scratch.
- Add cases for:
  - `prepare()` with an injected RUNNING status writing nothing to the managed paths;
  - path-budget refusal;
  - the post-install status recheck;
  - refusal of the old schema.
- Fixtures are the P1 G1/G2/G3 sets. G1 is regenerated from the preserved Master copy by the unchanged compiler,
  not copied from the live installation at test time.

**Evidence and deliverables:**
- **Source:** in the working tree, uncommitted until approved.
- **Report:** an L-1 report in a new private evidence folder, containing:
  - source and test hashes;
  - the equivalence table;
  - a per-case results JSON;
  - a live-installation fingerprint taken before and after, read-only, with hashes of the Master, the authority
    files and `publisher.lock`;
  - a footprint log.
- **Commit and push:** only on separate owner approval after review. The commit message must end with the
  required Co-Authored-By line, and paths must be staged explicitly.

**Acceptance:**
- every ported and new case PASSES against the product code;
- every non-mechanical deviation from P1 is justified in the equivalence table;
- the live fingerprint is unchanged;
- no write occurs outside the scratch root, the evidence folder and the new `updater/` source tree;
- no import from private evidence paths;
- sanitation rules are met for all new tracked files.

**Forbidden in L-1:**
- GUI, Job Object, official packages, network, packaging;
- any write to the live installation;
- launching SFM, CPM or the Normalizer;
- WPR/ETW work;
- changes to `tools/`, CPM, the Normalizer, the authority package, R15, R2, the Amendment or the Ledger;
- elevation or ACL changes;
- commit or push without approval.

**STOP and preserve evidence (no retry or reinterpretation in place) if:**
- a ported mechanism case fails in a way that would require changing C6–C8 or C12 semantics;
- any overwritten occupant, lost edit or false success occurs;
- the live fingerprint changes;
- a needed capability requires elevation or a live-installation write;
- the pinned dependency hashes do not match.

## 9. Repository copy record

This repository copy was derived from the approved draft (SHA-256 `d540d0ef8229f3ba6320c03e4b316e288a250841e23fc810aecc8df648e777eb`). It differs only in two respects:
- the approval-status wording;
- the §3 heading wording ("Proposed" became "Planned"). The draft contained no placeholders.

The owner approved it on 2026-10-16, through the designer's acceptance of the reconciled drafts. Its own SHA-256 is
listed in `updater_qualification/SHA256SUMS.txt`.
