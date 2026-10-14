# Ledger

## Coder gate
Before editing, compare the assignment with the Blueprint and this Ledger.
Verify the current code state and relevant claims.
If the assignment assumes unfinished work is complete, contradicts the
Blueprint, or expands scope, report the conflict before dependent edits.
Otherwise proceed with the assigned milestone.

## Current milestone
**U0B-P1 — Real-artifact scratch qualification (ruling §6): COMPLETE / PASS (bounded), 2026-10-14.**
Owner-approved after the C1 correction and an independent audit (Astra; private, not committed), which
found both reopening defects resolved: bounded technical PASS for the no-op correction, broker
qualification and regression sufficiency. Scope: R2 activation/recovery on real SFM Master and sidecar
artifacts in disposable scratch roots on the installation volume (fixed NTFS), plus the broker entry point
under SFM's Python 2.7.5 outside SFM. **Not** native SFM, consumer-UI, concurrency, durability or release
qualification. P1/C1 is **not** fully procedurally compliant (see Procedural).
- **Original campaign (2026-10-12; prototype `537739ff…`, controller `4affc60b…`):** 130 final PASS =
  125 initial PASS + 5 fresh reruns after a harness selector-oracle correction; the 5 original FAIL
  records are preserved. No demonstrated data-loss finding.
  - Cases by ruling §6 category: canonical import/rebuild/no-op/custom source 7; interrupted
    forward/reverse and killed recovery 66; newer-data preservation 5; occupied
    destinations/substitution/competitors 10; malformed/inconsistent 12; alias/single owner 5; legacy
    `publisher.lock` 9; selection 2 (+70 embedded selector checks); sharing classification 2
    (library/file level only); process status/barriers 10; path length 2.
  - These results stay attributed to `537739ff…`. A3/A4 (no-op) are superseded by C1 N1/N2.
- **Reopened 2026-10-13** on two gaps (verified-no-op bypass of the process gate and transaction
  records; sharing classification below broker entry-point level). **C1 correction, 2026-10-14**
  (corrected prototype `8871f13756d132eae0584190885198c7b6f2c8c62b3bd543a809d64660b4b425`; diff local
  to the no-op branch plus three helper functions):
  - **10 targeted no-op PASS:** CLEAR no-op (rebuild; import of identical bytes); injected RUNNING
    and UNKNOWN (zero exclusive authority opens); pending transaction before and after protection
    (refuse, existing recovery, then NOOP); unknown schema; finished records; unfamiliar entry;
    protection conflict (sharing violation).
  - **2 regression PASS** (import G3; RUNNING full activation) and **1 broker-entry PASS** (14 checks).
  - **2 controls** on the original prototype reproduced both defects; they are not counted as C1
    passes. Shakedown and final runs gave identical verdicts.
- **Gaps CLOSED within P1's tested scope:**
  1. **No-op (R2 C4/C7/C8, A3):** installation lock → transaction inspection → CLEAR process decision →
     exclusive identity-bound Master/sidecar/manifest verification → final inventory verification
     precede a truthful NOOP. Pending or unfamiliar transactions refuse until handled through the
     existing recovery.
  2. **Broker:** real `get_broker()` / `acquire_or_reuse_views()` (Normalizer call shape) under Python
     2.7.5 outside SFM: protected sidecar on a cold broker → `SidecarMissing` with no provider or cache
     admission; reacquisition after release; warm reuse of the same view with no provider open;
     protected Master → `MasterUnreadable` at H0, warm or cold.
- **Audit qualifications (carried):**
  - scratch authority file bytes were not independently rehashed from the audit archive; identities,
    manifests, source and traces were verified;
  - the 49th C1 harness file is the closeout summarizer; the original-prototype reference is inside
    the verified 48-file frozen manifest;
  - protected-Master results show broker behavior at H0, not that all existing detached consumer
    operations stop;
  - ordinary shared previews and a brief legacy `publisher.lock` probe precede the process gate; the
    exclusive Master/sidecar/manifest verification does not;
  - file hashes establish content identity, not independently authenticated test-plan creation times;
  - `intent_schema()` has a non-blocking diagnostic weakness for JSON scalar/list input; it remains
    fail-closed. Pre-production diagnostic hardening, not a P1 blocker;
  - the protected-sidecar `SidecarMissing` diagnostic remains potentially misleading.
- **Real artifacts:** compiling the preserved G1 Master in scratch reproduced the live sidecar
  `bcd97641…` and manifest `d810d648…` byte-for-byte (G1 is regenerable); G2 compiled to `cd370f67…`;
  the semantic test Master **G3** (`5635ecf3…`, sidecar `3a16e945…`) moves exactly one control
  (`Left PupilDown`, `Face/Eyes` → `Face/Expressions`).
- **Claims, limited to the tested cases and interfaces:** interruption at the tested barriers and during
  recovery recovered to the exact old or new set, idempotently; user edits after interruption gave a
  truthful CONFLICT; occupants at tested destinations were never overwritten; the 15 tested competing
  operations during protection were refused; tested malformed states were refused or reconciled; one
  lock owner across the tested aliases. `publisher.lock`: recognized and preserved in place; tested
  results cover **lock acquisition only, not full legacy-publisher exclusion**. RUNNING/UNKNOWN cases
  were **injected process-query responses**, not real running-SFM detection.
- **Findings for P2/L:** F1: the Python 2.7 consumer libraries failed to open the tested **sidecar** path
  at 260 characters (259 worked); no Master threshold was measured; the live maximum is 175. F2: a
  protected sidecar is reported as `SidecarMissing` (library and broker level). F3: an occupant in an
  authority slot yields a truthful CONFLICT, not ROLLED_BACK. F4: holding `publisher.lock` makes a
  legacy lock acquisition fail at open with a generic message. C1: while the Master is protected even a
  valid cached view is refused at H0.
- **Live installation:** never written or locked. Fingerprints (4 authority files vs pins, 235 closure
  files, `gameinfo.txt`, `cfg` listing) showed no detected change at every P1 and C1 check; this is not
  continuous proof of no transient write.
- **Evidence (local only, not committed):** in the operator's approved local Codex evidence directory.
  - P1: report `bb91b373e89a097187140587583adc115924bfca23006f3b97e25cdf63e62c6f`, case matrix
    `0aaa4da8…`, I/O manifest `ac0a27ac…`, scratch inventory `1928aab8…`, footprint log `22daffb6…`,
    harness list `db043719…`.
  - C1: report `36b9acf24cef8dfdf7139f4c5a2f9cec0f4680ae0fcaffb41117ebf61292c756`, case matrix
    `00a7e1e3790a820ff4a1d725b3ad376ac01060a10fbb1ee8710be868d633e87d`, frozen harness list
    `377d84418268f3d7974f83879db33d2258589d312b75529229d39b494e99f431`, test plan `3cae5d16…`,
    prototype diff `20f6ce4e…`, final preflight `cb6cc13d…`.

  The P1 report's "broker-level" (I1/I2) and "Master or sidecar" (F1) wording is superseded by this
  entry; hashed reports are not edited.
- **Procedural (owner dispositions: P1 2026-10-13, C1 2026-10-14; both accepted as non-blocking).**
  - P1: a `git fetch` rewrote `FETCH_HEAD` before closeout; a mistaken empty shell here-document used a
    transient temporary file; agent-harness session files. Unattributed: 58 empty temporary
    directories and a `.ses` modification in the user temp folder. Unresolved: the footprint log
    records its audit at about 22:15 local but lists a 22:47 `.ses` change.
  - C1: the first C1 preflight found SFM running (not agent-started) and stopped before any scratch
    execution. Execution resumed under a separately issued designer authorization to resume after SFM
    closure; the resume preflight found process status CLEAR. Writes outside scope: agent-harness
    session files (including one background task output). Two empty temporary directories appeared in
    the user temp folder during C1 activity; no creator is established. Recurring background temp-file
    activity was also observed and is unattributed.

  P1/C1 is **not** fully procedurally compliant. The dispositions attribute no unexplained activity,
  waive no technical requirement and authorize no future out-of-scope write.
- **U0B-P2, P3 and L: NOT STARTED.**

Previous milestone: **U0B-P0 — Read-only installation, exposure and evidence preflight (ruling §7):
technical acceptance PASS (bounded), 2026-10-12.** Owner disposition (2026-10-12): the
write-footprint deviation is accepted as non-blocking. P0 keeps its bounded technical PASS but is not
described as fully procedurally compliant, and its evidence and temporary files are preserved.
- **Scope held:** run from `a274b7c…`. SFM was not running and was never launched. Non-elevated; no
  tracing, compilation, tests, settings, installed-file or authority change. The live authority was
  hashed three times during the inventory and was unchanged.
- **Acceptance:** the designer found all seven ruling §7 acceptance items satisfied. PASS is not
  native safety, backup recoverability, U0B or release qualification.
- **Evidence (local only, not committed):** the P0 report (`7f3b26e2672af6101ffc7d7d1b8a33fd31daeb906adcd2b120f61044c6fe8a14`)
  and inventory (`6516bdb3c66e29843c45911599294b42c840eecf8e10bb2c375951d9987594d1`), plus a private
  write-footprint note, in the operator's approved local Codex evidence directory. They contain
  workstation paths and installation details, so they stay out of GitHub.
- **Procedural finding (owner-accepted as non-blocking):** P0 permitted writes to one evidence folder
  only. Outside it, during P0:
  1. two working hash-list files in the agent session's temporary scratchpad (disclosed in the
     report);
  2. two tool-output files saved automatically by the agent harness in its session store, one a
     duplicate of item 1 (not disclosed in the report);
  3. a `git fetch` at P0 start rewrote repository metadata (`FETCH_HEAD`); no tracked file, ref,
     index or object changed.

  All still exist, unmodified. They contain hashes, file names and listings, with no credentials. P0
  is therefore **not** described as fully compliant.
- **Verified installation identities** (all match pins and repository bytes):
  - Authority: G1 Master `ac45e5c1…`, `manifest.json` `d810d648…`, the only sidecar `bcd97641…`,
    and an empty `publisher.lock` (`e3b0c442…`).
  - Consumers: CPM `4e35f292…`, launcher `996ca483…`, Normalizer `1f4ec5a2…`, adapter
    `e96e21b5…`, projection `9b077a1b…`, probe v3 `ce4ace98…`, and the shared authority package and
    reader.
  - Bytecode: 25 `.pyc` files carry Python 2.7 magic and timestamps matching their sources.
- **Findings:**
  - **Effective Master:** statically `usermod/cfg/sfm_defaultanimationgroups.txt` (usermod first in
    `gameinfo.txt` SearchPaths; launch options set no `-game`/search path). The Normalizer's
    absolute path is demonstrated in I/J logs. CPM logs a relative path, and the process working
    directory has never been recorded.
  - **Stray copies:** 19 other Master-like files are inert by search-path rules (statically): 12
    outside the live `cfg` (stock `platform`, model packs, a probe backup) and 7 differently named
    TXT files in `cfg`. The P0 report says "eight" for the latter; the inventory shows seven.
  - **Selector:** reads only `*.sfmsidecar` (first matching source hash wins). It ignores
    `publisher.lock` and `manifest.json`, and the winning artifact is not logged.
  - **`publisher.lock`:** created by `tools/sfm_master_sidecar/publisher.py`. Proposed rule:
    recognize in place, never move or delete, and refuse if it is held. Implementation remains to
    qualify.
  - **Ordinary SFM writes:** `cfg` config files and stats at exit; HKCU Qt settings;
    `<document>.autosave` beside the open document (from timestamps, not traced); product logs (the
    Normalizer log is truncated on each run).
  - **G1 sidecar:** `bcd97641…` existed only in the live installation, not in the repository. A
    hash-verified second-volume copy is required before any step that could touch the authority.
    (Since P1: preserved locally and shown to be regenerable from the Master.)
  - **Path budget:** the live sidecar path is 175 characters; with about 172 of transaction overhead
    that is about 347 (over 260). Long paths are enabled on this machine.
  - **Fixture:** the K/item-8 fixture is still at its pin `197e6011…`.
- **Unresolved after P0:**
  - **Native Master access:** path, timing, share mode, and behavior when the Master is locked,
    absent or mid-replacement are UNKNOWN; no file-access trace exists. Observing them needs
    elevation (built-in WPR), a tracer install, or a test-only probe, and each needs approval.
  - **CPM absolute Master target:** inferred only.
  - **Semantic oracle:** there is no Master pair with a deliberate semantic difference (G2 is G1
    plus one LF), no oracle combining group tree and channels/keys, and no real sidecar bytes in the
    repository. (Since P1: the scratch G3 pair exists locally; the native group-tree plus
    channel/key oracle remains for P2.)
  - **Bytecode:** content equivalence is shown by timestamps only.
  - **Antivirus:** Defender real-time protection is on; exclusions are unreadable without elevation;
    interference is untested.
  - **Concurrency (C11/G), durability (C10/G hard reset) and cross-user contention:** unqualified,
    not waived.
  - **Restoration:** plans are proposed only; backup recoverability is unproven.
  - **R3-A1 evidence:** the source document behind "native rereads the Master" is absent from the
    repository.
- **Next proposal (at P0):** P1, real-artifact scratch qualification. It was since authorized and
  executed (see Current milestone).

Previous milestone: **Updater design checkpoint (documentation only), 2026-10-12** (U0B-P0 was
authorized there and has since been executed, above).
The owner approved the updater design adjudication and authorized U0B-P0 as the next milestone. No
code, test, SFM launch or installed-file change was made; baseline `1a2bbd1…`; committed and
verified on GitHub as `a7739736366bb057d51bffe4e74d1a5c74614024`.
- **Authority (GitHub, `updater_qualification/`):**
  - `design/OWNER_DECISION_2026-10-12.md`: the owner record; governs only its explicitly
    approved items and lists original and committed SHA-256s;
  - `design/SFM_Character_Tools_Updater_Blueprint_R2.md`: governs the updater protocol except as
    approved in the owner record; byte-identical to the original (`61cf8ed5…`, CRLF, `-text`);
  - `design/SFM_Updater_Final_Architectural_Ruling_2026-10-12.md`: Astra's final ruling; a
    **sanitized derivative** (original `b985e868…`, copy `d63b886b…`; one workstation path on
    line 213 replaced);
  - `reviews/U0B_Independent_Adversarial_Audit_R2_Reconciled.md`: evidence, not approval; sanitized
    (original `7c552f74…`, copy `c5ab370c…`; one personal name on line 3 → `@OWNER`);
  - `SHA256SUMS.txt`: committed-copy digests.
- **Approved:** keep R2 C6–C8 and C12 unchanged; A3 (UNKNOWN process status refuses; barriers fail
  closed); `publisher.lock` direction: preserve and recognize a verified legacy file in place (no
  migration or deletion).
- **Not approved / on HOLD:** A1 and A2 directions only, with no qualification or hard-reset waiver;
  A4 deferred (cross-user unqualified, no test account); N1-first rejected; R2 C10/G hard-reset and
  C11/G concurrency blockers not waived; live fault injection HOLD.
- **U0B-P0** (ruling §7): read-only preflight, authorized to write only its report and inventory,
  to one new folder in the operator's approved local Codex evidence directory, outside the
  repository. It has since been executed (see Current milestone).
- **U0B-P1, P2, P3:** each needs separate authorization.

**U0A — Disposable Windows activation feasibility (pre-L; Astra Updater Blueprint R2, Stage 0
file half): PASS (bounded), 2026-10-12.** This is experimental evidence, **not** production
qualification. No updater, GUI, packaging or install exists; no product, authority or SFM file was
touched (production fingerprint unchanged).
- **Setup:** baseline `af4c8d6…`; R2 sha `61cf8ed5…` (owner-supplied; committed byte-identical at
  the updater design checkpoint); Windows 10 22H2 19045.6466, NTFS, non-elevated; disposable
  synthetic `usermod\cfg` trees only.
- **Results:** 256 PASS, 1 NOT RUN, 0 FAIL (257 recorded). U0A-1 6/6, U0A-2 83/83, U0A-3 8/9
  (cross-user NOT RUN), U0A-4 5/5, U0A-5 134/134, U0A-6 20/20.
  - *Correction (2026-10-12):* the grand total first recorded as 255 PASS was an arithmetic error.
    The raw verdicts always summed to 256. Documentation-only correction; no rerun; verdict
    unchanged.
- **Confirmed under process termination:**
  - protected own-handle no-clobber rename (`GENERIC_READ|DELETE`, share 0; `FileRenameInfo`,
    `ReplaceIfExists=FALSE` → 183 on an occupied destination; 17 cross-volume, no copy);
  - every racer refused during protection, and every pre-protection mutation detected through the
    held handles;
  - one lock owner across 8 path aliases;
  - an exact final set verified independently;
  - every kill point (including during recovery) recovers to a verified old or new state, or to a
    preserved conflict; recovery is idempotent.
- **Unproven:** power-loss durability, cross-user and standard-user tokens, real disk-full, AV
  interference, and all real-SFM behavior (U0B).
- **R2 remains viable.** Refinements F1–F9 are for L. Notably, F4: the live `publisher.lock` in
  `sfm_shared_authority` would be refused as unfamiliar content (owner direction since approved:
  preserve and recognize it in place; see above); F7: transaction paths add ~172 characters.
- **Evidence:** `updater_qualification/u0a/U0A_WINDOWS_ACTIVATION_FEASIBILITY_REPORT.md`, plus
  `harness/` and `evidence/` (redacted).
- **U0B:** P0 technical PASS (bounded; deviation owner-accepted as non-blocking); P1 COMPLETE /
  PASS (bounded, scratch + broker entry point; reopened 2026-10-13, corrected by C1 2026-10-14);
  P2–P3 NOT STARTED.

**K — Integrated CPM/Normalizer product workflow qualification: COMPLETE / PASS (2026-10-10).**
K PASS = K1 PASS (K1A2, 53/53) + K2 PASS (K2A1, 39/39), on CPM `4e35f292…` and Normalizer
`1f4ec5a2…`. Exact production CPM/Normalizer and exact G1 authority remain installed. **L: NOT
STARTED.**
- **K2A1:** one fresh SFM process (PID 41240) from `13f57c1e…`:
  - **CPM first:** CPM created the one broker `0x3101aa50`; Save and the Normalizer's `shot9` run
    on G1 followed.
  - **G1→G2 switch:** exact G2 via the frozen tooling with both tools idle. The change alone
    caused no acquisition or rebuild.
  - **Normalizer touched G2 first:** a new G2 cohort, no G1 reuse.
  - **CPM recovery:** exactly one `generation-mismatch` refusal (no mutation, no replay), then one
    rebuild to healthy G2. The deliberate G2 Apply committed a real change and its Undo restored
    the operator's value.
  - **G2 alternation:** the Normalizer's `shot3` run passed on G2; Delete passed; CPM closed; exit.
  - **Restoration:** `S2 RESTORED EXACT G1`; app and fixture unchanged; idle at every probe;
    `mem_ok` never False. The adjudication-script correction is recorded (design §18).
- **Evidence:** design §17 (K1), §18 (K2 and K completion); redacted raw copies in
  `real_sfm_qualification/cpm_k_integrated/raw/` (K1A1, K1A2, K2A1; `MANIFEST.md`).

Earlier K1 record:
- **K1A2:** one fresh SFM process (PID 36888) from the K-0-amended checkpoint `93317866…`.
  Mechanical adjudication **53/53 PASS** over the sealed evidence; disposition PASS. Proven:
  - **Normalizer first:** it created the one canonical broker `0x338d0630` before CPM existed, and
    CPM then joined it.
  - **Coexistence:** divergent shots (CPM playhead `shot10`, Normalizer selection `shot9`) and the
    same shot (`shot3`/`shot3`).
  - **Alternation:** 4 Normalizer Selected runs, all PASS on G1 with `mem_ok` True. CPM Body Save,
    Fit + Undo, Body Apply + Undo, Expression Save, Apply + Undo and Delete ×2, all on G1 with 0
    refusals, 0 stale events and no rescope.
  - **Close orders and lifetimes:** close order X (CPM closed after Normalizer runs) and Y
    (Normalizer run while CPM closed); reopen with the same module and run in a new window; exit
    with CPM open. Idle at every probe; both consumers' views were retained.
  - **Resources:** no STOP; private 3,074 → 3,111 MB.
  - **Closeout:** exact G1 untouched; app and fixture unchanged; expected inventory restored.
- **Runbook clarifications** recorded in K1A2: clip-click selection; slider change before a
  same-value Apply; Delete's Favorites `library.json` cleanup (owner option 1). They are carried
  into K2-D4/K2-E4.
- **Evidence:** design §17; redacted raw copies in `real_sfm_qualification/cpm_k_integrated/raw/`
  (K1A1 and K1A2, `MANIFEST.md`).
- **K1 authorized (K2 is not).**
  - **K1A1 — INCONCLUSIVE:** a qualification-tooling false STOP before either product consumer
    executed; not a CPM or Normalizer failure. The baseline probe in a fresh fixture-loaded process
    showed 528 MB free VAS, which tripped the K rule "free VAS < 600 MB". Item 8 D's Normalizer had
    begun with 421 MB free and finished `mem_ok=True`.
  - **K1A1 closeout:** SFM closed with Don't Save; exact G1 untouched; probe removed; expected
    inventory restored; app and fixture unchanged; sealed (local evidence). It is not reused.
- **K-0 amendment:**
  - the VAS STOP is removed and free VAS (probe, Normalizer samples) is recorded as telemetry only;
  - the Normalizer's own `mem_ok=False` is the primary memory/VAS STOP, and the private-bytes
    safeguards are retained;
  - a regression check was added;
  - reader `e137536d…`, manifest `7bf1683a…`, driver `8b302a96…` (manifest pin only); probe
    unchanged;
  - tests: **2.7.5 160/160**, **3.10 191/191**.
  - Design §5.4 and §16.

**Pre-K CPM UI polish pass — LIVE VERIFIED / PASS (2026-10-09).** The final build
**`4e35f29242351317f2f961c27e19d66fcd3355cff964b081431fc2fff1f5b9d7`** is installed and is **the
exact CPM candidate eligible to enter K**.
- **U3** verified it live as a Help wording delta from U2: owner review of the Getting started Help
  ("good looks"), plus a log showing the exact build loaded, Help opened and the close finalized,
  with no authorizations, mutations or refusals.
- It supersedes `7e4686d7…` (U2 LIVE VERIFIED / PASS) only in those two Help paragraphs. The offline
  UI test passes 100/100 and 65/65, and all existing suites PASS.
- Record: `PRE_K_UI_POLISH_PASS.md` §H; outputs in `pre_k_ui_polish_outputs_r3/`.
- K has since run on this build and is COMPLETE / PASS (see above). L: not started.
- Superseded candidates are retained with their records: `7e4686d7…` (U2 PASS) and `5c6e2789…`
  (U1 SUPERSEDED / NO QUALIFICATION VERDICT).
- Item 8 qualified `bfba4d3a…` functionally. That evidence is unchanged, and the UI pass is
  byte-bounded against it.

The pass makes eight presentation changes:
1. the owner-supplied woman icon, embedded at 64×64;
2. **Character Model:** and "Choose a character model" (Refresh Model List unchanged);
3. Help opens with **Getting started**: the character and the playhead workflow;
4. semantic buttons: blue Apply/Fit, gold Favorite, red Delete. In the refinement these are
   **neutral fills with restrained role-colored borders**, and every role uses the neutral disabled
   state;
5. window 580×800, minimum 540×650 (the four tabs fit);
6. Update confirmation copy, with no question icon;
7. Review buttons in a 2×2 grid;
8. **Clear Classification** wording.

No scope, authority, lifecycle, preset, Fit, generation or Normalizer behavior changed.

Offline results for `7e4686d7…`:
- all existing convergence/R14/R15 suites PASS under 2.7.5 (real Qt) and 3.10;
- `test_cpm_app_ui_polish_pass.py` passes **99/99** (2.7.5) and **64/64** (3.10), including byte
  reconstruction from `bfba4d3a…` and real-Qt pixel checks of fills, borders and disabled states.

(First candidate `5c6e2789…`: 96/96 and 61/61.)

The exact-build historical tests (item 6, item 7 reconstruction, item-8 probe/driver) refuse the new
bytes by design and were not edited. Record: `cpm/qualification/PRE_K_UI_POLISH_PASS.md`; outputs
in `pre_k_ui_polish_outputs_r2/` (first candidate: `pre_k_ui_polish_outputs/`).

**Live checks:**
- **U1** (`5c6e2789…`): SUPERSEDED / NO QUALIFICATION VERDICT.
- **U2** (`7e4686d7…`): **PASS**, on the owner's hands-on review ("Looks good") plus the log. The log
  shows the exact build loaded, the window shown, Help opened, and the close finalized, with no
  authorizations, mutations or refusals. Its only messages were the unchanged "No current shot." and
  "Choose a model first." guards.
- **U3** (`4e35f292…`): **PASS** as a Help wording delta from U2. The owner reviewed the Getting
  started Help; the log shows the exact build loaded, Help opened and the close finalized. Its only
  message was the expected "No current shot." at launch.

No model was selected in U2. Enabled border colors, the Update confirmation and Review rest on the
offline real-Qt checks and on U1 hands-on use. Each deployment was verified with SFM closed: Scripts
difference = the app line only; authority exact G1. Details: `PRE_K_UI_POLISH_PASS.md` §0.3.

Previous milestone: **§22 item 8 — COMPLETE / PASS** (qualifies `bfba4d3a…` only; unchanged). Exact candidate
`bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5` was qualified in one fresh
real-SFM Python 2.7.5 process. The campaign covered:
- focused post-cleanup operation;
- persistence and native Undo;
- ordinary Fit;
- generation refusal and rebuild;
- canonical idle ownership;
- Normalizer coexistence;
- close/reopen behavior.

Historical forced-rollback and queued-Fit evidence is retained with its existing qualifications.
Exact G1 was restored. The temporary item-8 probe, campaign pointer and other qualification-only
deployment were removed. **The exact qualified candidate remains installed.** No new convergence
blocker was found. At that checkpoint CPM was eligible to enter K, and K and L had not started (K
has since completed, PASS, in fresh SFM processes; L is NOT STARTED). This checkpoint does not
decide L's final installation layout.
(Superseded for K entry by the pre-K UI pass: the build eligible to enter K is now the live-verified
`4e35f292…`.)

- **Attempt `I8A1` (2026-10-08, from `d4ad3cf`):**
  - one SFM process, PID 36912;
  - module `0x30b6b490`, class `0x307ed158`, run `20261008-135639-pid36912`;
  - broker `0x310a7810`;
  - windows `0xce494350` → `0x310bea30` → `0x30b87418`;
  - fixture `testscripts.dmx` (`197e6011…`): Krystal on `shot10`, Mia on `shot3`; not saved.
- **Phases A–F PASS.** Mechanical adjudication 34/34, from 30 probe records, the CPM-log excerpt,
  the Normalizer log, and the generation and library records.
  - **A — load and reuse:** `bfba4d3a…` loaded through the private loader; the second click gave
    `PROD_R15_WINDOW_REUSED` with no acquisition.
  - **B — Fit:** authorized on G1; 34 literals; committed-verified with 26 mappings and 7 warnings;
    one release `ok=True`; `changed=1 partial_changed=1 failed=0 unattempted=0`. Only the target
    changed, and Undo restored exactly.
  - **C — persistence and Undo:** Mia scope 46/58/4. Body Save/Update/Apply and Expression
    Save/Apply all equal their readbacks; each Undo restored exactly; library changes stayed within
    the footprint.
  - **D — Normalizer:** Selected `shot3` PASS/PASS, `mem_ok` True 15 / False 0. One broker served
    both projections. Apply and Save continued without reselection, refusal or rebuild.
  - **E — generation transition:** a Save opened under G1 and G2 was activated at 19:46:45 with the
    prompt open. The Save was refused with `generation-mismatch`: no `PROD_SAVE`,
    `durable_commit=None`, libraries E1 = E2 = E3. Only then did one rebuild to healthy G2 happen.
    A deliberate G2 Save was authorized on G2.
  - **F — close/reopen and exit:** Escape and ✕ closes finalized; the reopen kept the same
    module/run under the G2 scope. Idle 0/0/0 at every checkpoint (broker totals: opens/closes
    7/7, views 5).
- **Resources:** private bytes 3,067.8 → 3,103.3 MB (about +35 MB over about 6.5 hours, including
  about 9 MB for the Normalizer). The two closed states after the reopen were equal, with handles,
  GDI and USER flat.
- **Restoration and disposition:** exact G1 restored (Master `ac45e5c1…`, manifest `d810d648…`,
  sidecar `bcd97641…`). The probe and pointer were removed. PASS disposition: the installed app is
  `bfba4d3a…`. The final Scripts inventory differs from the accepted Session 4 inventory only by the
  app line.
- **OWNER-1 historical files:** present and inert; never loaded, never used as authority.
- **Deviation (no effect):** the operator ran the installed Session 1 probe once before A5. Its
  broker counters were unchanged and it caused no acquisition.
- **Evidence:**
  - `real_sfm_qualification/cpm_item8_post_cleanup/ITEM8_EVIDENCE.md` §6;
  - redacted raw files in `raw/I8A1/` (82 files; `raw/MANIFEST.md`).

Previous milestone: **§22 item 7 — COMPLETE: diagnostic/development logging reduction; offline
qualification PASS** (candidate `bfba4d3a…`; design and evidence
`ITEM7_DIAGNOSTIC_LOGGING_REDUCTION_*.md`; manifest `cbb3010b…`; reporting constants removed,
superseding item 6's retention; Q1 parity oracle retained disabled). Its qualification is unchanged.

Previous milestone: **§22 item 6 — COMPLETE: historical authority cleanup; offline qualification
PASS** (candidate `1e866871…`; design and evidence `ITEM6_HISTORICAL_AUTHORITY_CLEANUP_*.md`;
manifest `a9264794…`). Its qualification is unchanged.

Previous milestone: Real-SFM Session 4 (forced rollback-verification qualification, handoff §22
blockers 4–5). **Status: COMPLETE — PASS.**
- S4A (Body Apply): PASS — CONTROL (authentic Abort, rollback verified), GATE (authentic verifier
  True, harness substitutes False → production recovery-unverified), ordinary Apply.
- S4F (Clothing Fit): PASS — CONTROL (`not-committed`), GATE (`abort-unverified`), ordinary Fit and
  Undo.

Evidence: `real_sfm_qualification/cpm_session4/SESSION4_EVIDENCE.md`, raw outputs in `raw/`.
Runbook: `SESSION4_RUNBOOK.md` at `b65c085`; harness `45c44f3d…`.

Sessions 1–4 remain complete (evidence for app `9a78fc96…`). R15 and R14 remain CLOSED.

## Current state
`master`. Before item 6 the product was unchanged since `00d0d83` (last commit touching `cpm/app`,
`cpm/baseline` or the adapter/projection). Items 6 and 7 changed only the mutable app
(`9a78fc96…` → `1e866871…` → `bfba4d3a…`); the launcher, baseline, adapter/projection, shared
package, Normalizer, Master and sidecars are unchanged. Item 8 (real SFM) changed no repository
product file. The pre-K UI polish pass changed only presentation in the app (`bfba4d3a…` → `5c6e2789…`, refined to
`7e4686d7…`, then the Help-wording build `4e35f292…`, which is installed and was K-qualified). U0A
added only experiment/documentation files under `updater_qualification/u0a/` (plus a scoped LF
`.gitattributes` entry for them). The updater design checkpoint added only documents under
`updater_qualification/design/` and `reviews/` plus `SHA256SUMS.txt`, scoped `.gitattributes`
entries, the U0A report's tally correction and this Ledger. U0B-P0 changed no tracked repository
file or installed file; its evidence is local only, and the P0 closeout changed only this Ledger.
U0B-P1 likewise changed no tracked repository file or installed file. Its harness, scratch run and
evidence are local only. Its closeout, the 2026-10-13 reopening reconciliation and the 2026-10-14
final closeout changed only this Ledger. The C1 correction (2026-10-14) likewise changed no tracked or
installed file; its corrected prototype, harness, scratch run and evidence are local only.

**References for transfer:**
- Authoritative R15 design: `cpm/qualification/R15_IMPLEMENTATION_BLUEPRINT.md`, frozen from
  checkpoint `bd169401fba1c04bf24a148cd8e65748ae757912` (unchanged since `382c79b`). Its §13 line
  "R15 remains OPEN…" predates R15 closure; this Ledger is authoritative for status.
- Updater design authority: `updater_qualification/design/OWNER_DECISION_2026-10-12.md` (with R2 and
  Astra's ruling beside it; see Current milestone). It does not change the frozen R15 Blueprint.
- `cpm/qualification/R15_NAMESPACE_ISOLATION_PROPOSAL.md`: superseded, historical only.
- Convergence requirements and the §22 sequence:
  `docs/qualification/CPM_CONVERGENCE_INTEGRATION_HANDOFF.md`.

The Session 4 campaign folders (`S4A`, `S4F`), the probe JSONL and the CPM log are copied,
redacted, into `real_sfm_qualification/cpm_session4/raw/`. The qualification-only rollback harness
was removed after each campaign; the Scripts deployment equals its pre-harness baseline exactly
(`cefc2b88…`), and no `ACTIVE_CAMPAIGN.txt` remains.

The live authority is exact production G1 (Master `ac45e5c1…`, manifest `d810d648…`, one sidecar
`bcd97641…`), last restored and confirmed at K2A1 closeout (`S2 RESTORED EXACT G1`, 2026-10-10),
and re-verified unchanged, read-only, by U0B-P0 (2026-10-12).

**Deployed and verified** (runbook §0; re-verified at the 2026-10-06 transfer checkpoint and by
item-8 `I8-Preflight`/disposition on 2026-10-08 and the U1–U3 deployments on 2026-10-09; the shared package's qualification-only
`projections.py` is intentionally not deployed):
- launcher `996ca483…` as the Scripts-menu entry;
- private app **`4e35f292…`** (final pre-K UI build, LIVE VERIFIED / PASS in U3, 2026-10-09; the
  builds it replaced, `7e4686d7…`, `5c6e2789…` and the item-8-qualified `bfba4d3a…`, are
  preserved, see below) in
  `usermod/scripts/ChadChan3D_CPM/` (outside `scripts/sfm`, no `__init__.py`);
- probe v3 `ce4ace98…`.

Rollback chain, held in the local U3/U2/U1 attempt folders: `7e4686d7…` → `5c6e2789…` →
`bfba4d3a…`. `bfba4d3a…` can also be restored from git (`2fe9a27`). The previous app `9a78fc96…` remains restorable from git (`9d405c8`). The item-8 probe and campaign
pointer are not deployed. The Scripts deployment equals the accepted Session 4 inventory
(`cefc2b88…`) except the private-app line (U3 inventory `59b8f28b…`). The live authority is exact
production G1. Any later deployment change follows the R15 restart rule.

The step-9 G18AN menu copy has been removed. The pre-R15 app `664a660c…` and probe v2 are archived
outside `usermod/scripts`.

Unchanged (byte-pinned by the R15 suite):
- the baseline `3326024d…`;
- the Normalizer `1f4ec5a2…`;
- the adapter `e96e21b5…` and projection `9b077a1b…`;
- the shared package;
- the Master `ac45e5c1…`;
- R14 private ctypes.

## Verified (real SFM)
Evidence:
- `SESSION1_RUN1_RECONCILIATION.md` (2026-09-28);
- `SESSION1_COMPLETION_EVIDENCE.md` (2026-09-29);
- `R15_SESSION1_ADDENDUM_EVIDENCE.md` (2026-09-30; raw outputs in `cpm_session1/r15_addendum/`).

| Session 1 item | Status |
|---|---|
| Normal CPM operation | PASS |
| Native Apply + Undo (incl. no-op) | PASS |
| Body Save / Update | PASS |
| Expression Save / Update / Apply | PASS |
| Review / Reclassify (Ayane, genuine miss; durable edit and rebuilt classification reported) | PASS |
| Ordinary Clothing Fit + Undo | PASS |
| C10 same-process broker | PASS |
| Simultaneous Normalizer coexistence | PASS, with no CPM scope selected (Session 1) **and with an active CPM scope (R15 addendum)** |
| Resource / latency | PASS (complete) |
| R14 ctypes isolation | CLOSED |
| R15 namespace isolation (Session 1 addendum, P1–P15) | **CLOSED — PASS** |
| Session 2 S2-A_R2: open-window G1→G2 replacement (2026-10-05) | **PASS** |
| Session 2 S2-B_R2: G1→G2 during a Save prompt (2026-10-05) | **PASS** |
| Session 3 S3: queued Fit, G1→G2 between targets (2026-10-06) | **CORE PASS** |
| Session 3 S3_ADD: fresh Fit committing under G2 (2026-10-06) | **PASS** |
| Session 4 S4A: forced Body Apply rollback-verification control + gate (2026-10-06) | **PASS** |
| Session 4 S4F: forced Clothing Fit rollback-verification control + gate (2026-10-06) | **PASS** |
| §22 item 8 `I8A1`: post-cleanup candidate `bfba4d3a…`, Phases A–F (2026-10-08) | **PASS** |

- **Clothing Fit detail:**
  - `Gfit` was authorized.
  - The stage requested 34 literals, more than the 26 source literals, so target-only vocabulary
    was included.
  - The planner produced 26 valid mappings (7 unmatched-target warnings).
  - The stage committed and verified, and its lease was released.
  - Undo visually restored the target.
- **R14:** CPM's resource snapshot ran first, then the Normalizer logged `mem_ok=True` at 13/13
  checkpoints (the first run logged `False` at 15/15).
- **R15 addendum (2026-09-30):**
  - **Design:** one thin menu launcher → one stable private `chadchan3d_cpm_app` module per SFM
    process → explicit compatible-window reuse (`R15_IMPLEMENTATION_BLUEPRINT.md`).
  - **Offline:** R15 suite 345/345 (2.7.5: real PySide/Qt 4.8 plus a model), 188/188 (3.10); all
    regressions PASS.
  - **Isolation:** `__main__` held no CPM names; private function globals.
  - **Stable identity:** one stable module, run ID and class across:
    - the reused second click (no authority acquired);
    - three close/reopen cycles (✕, Escape, Escape; one close request and one finalization each);
    - the notice step.
  - **Normalizer:** Rebuild Selected Shots on `shot3` with CPM's Mia scope active → PASS,
    `mem_ok=True` 15/15; 0 cross-log lines either way.
  - **Continuation:** without reselection, Apply ×2 committed and disposable Save PASS; no stale
    refusal and no scope rebuild.
  - **Notice and legacy slot:**
    - one reusable non-modal notice;
    - frozen G18AN in the slot was refused and preserved, then isolated CPM opened.
  - **Authority and resources:**
    - idle leases/providers 0;
    - across the cycles: private commit −0.5 MB, handles −10, GDI 0, USER −1 (no accumulation).
  - **Recorded deviations (benign):** the baseline ran before P3; one extra observational probe
    before P15; the console transcript was not retained.
  - **Observation:** one no-op Apply began about 0.2 s before the Normalizer's final report write.
    The PASS rests on later actions; alternation stays with K.
  - **Three findings, all resolved by R15, kept distinct:**
    1. the shared Scripts-menu namespace defect;
    2. the repeated-click re-initialization defect;
    3. the pre-existing Escape/reject teardown defect (discovered during R15).
- **Session 2 S2-A_R2 (2026-10-05, pid 25844, broker `0x32def250`, window `0x3210f580`):**
  - **Generation switch:** G1 `ac45e5c1…` → exact G2 `54413b6c…`, using the frozen Checkpoint I
    functions (complete write-once record set).
  - **No-interaction window held:** no CPM activity between G2 activation (17:55:09) and the
    stale Apply (17:56:10).
  - **A8 stale Apply refused before mutation:** `PROD_CPM_OPERATION_AUTHORIZATION_REFUSED …
    reason=u'generation-mismatch'`; no Undo, mutation, native-commit or Apply outcome;
    `native_commit=None`.
  - **Rebuild only after the refusal:** `…REBUILD_SCHEDULED` at 17:57:17, after the dialog was
    dismissed; one automatic Select Model to G2 `54413b6c…`; the same window; no replay.
  - **A10 deliberate Apply:** authorized under G2 and committed (`BodyTest`, `changed_sides=1`).
  - **Idle authority:** P2–P5 leases 0, providers 0, one window / one watcher.
  - **Restoration:** exact G1 (`exact_match: true` in both the finalization record and the
    independent comparison).
  - **First S2-A attempt (folder `S2A`, 2026-10-01):** procedurally invalid (runbook design
    error). Selecting a preset after G2 activation re-evaluated readiness and rebuilt the scope
    under G2 before Apply. That path behaved correctly but does not qualify the stale-action
    boundary. The folder is preserved; its restoration was exact.
  - **Observation:** the refusal dialog shows the guard's generic copy ("Preset could not be
    applied safely. This preset was not applied."), not the stale-scope message, which is logged
    only. See the stale-scope UI presentation item.
- **Session 2 S2-B_R2 (2026-10-05, pid 23944, broker `0x31141250`, window `0x30466580`):**
  - **Save opened under G1:** Save and its prompt opened at 18:36:40, under G1.
  - **Exact G2 while the prompt was open:** activated 18:40:42; no CPM activity until the prompt
    returned (`Q2_SAVE_POST_CONFIRM` 18:41:04).
  - **Stale Save refused:** the stale G1 Save authorization was refused with
    `generation-mismatch` (18:41:09); no `PROD_SAVE`, no durable phase, `durable_commit=None`;
    library inventories 1 = 2 = 3 byte-identical.
  - **Rebuild without replay:** one automatic rebuild to G2 after the refusal; the same window;
    no replay.
  - **Deliberate G2 Save:** passed, with the library diff exactly the three allowed entries.
  - **Idle authority and restoration:** P2–P4 leases and providers 0; exact G1 restoration.
  - **Aborted `S2B` attempt:** confirmed a normal G1 Save before any switch; the authority was
    untouched and the preset was removed. Its residual `character.json` metadata (`updated_at`,
    `last_validated_provider`) is never read for a decision and `semantic_overrides` is empty, so
    it cannot confound the tested boundary (adjudicated in `SESSION2_EVIDENCE.md`).
- **Session 3 S3 (2026-10-06, pid 26156, broker `0x314d92b0`, window `0x30ee7698`):**
  - **Target 1 under G1:** authorized and staged under G1, committed, released ok before target 2.
  - **G2 between targets:** the Fit was deferred at index 1 behind a modal; exact G2 was activated
    and proven live before resume.
  - **Refused, not mutated:** at resume, the target-2 stage proof was refused
    (`generation-mismatch`); no index-1 stage or commit; no continuation under G2.
  - **Truthful stop:** "Clothing Fit stopped" reported 1 committed target and Undo 1 time
    (`verified_changed=[assaultsuitbody1]`, target 2 unattempted). The target was committed with
    plan warnings, so it is accounted as partial rather than in `changed`.
  - **Undo, rebuild and idle state:** one Undo restored target 1 to pre-Fit (snapshot and visual).
    CPM rebuilt to G2 in the same window. P2–P4 were 0/0/0.
  - **Later G2 Fit:** authorized and staged under G2, then an expected structural skip
    (`loinclothbra_chadfix_071` has no compatible Body mappings). The G2 commit is carried by
    S3_ADD.
- **Session 3 S3_ADD (2026-10-06, pid 2324, broker `0x31419270`, window `0xb92d1c60`):** exact G2
  active before SFM started;
  `assaultsuitbody1` authorized, staged, committed and verified under G2 (`committed-verified`,
  26 mappings, 7 warnings), released ok; result PASS `partial_changed=1 failed=0 unattempted=0`;
  P2–P4 0/0/0; one Undo; exact G1 restoration.
- **Session 4 S4A (2026-10-06, pid 2540, broker `0x30fab290`, window `0x309ae698`):**
  - both injected `BodyTest` Applies authorized under G1, writes inside the open Undo
    (`changed_sides=1`, real precommit predicate True);
  - CONTROL: `PROD_APPLY_ABORT_VERIFY restored=True`, "Can't apply preset";
  - GATE: real verifier True, harness substituted False → `restored=False`,
    `ProdRecoveryUnverifiedError`, "Recovery could not be verified";
  - no `native-commit` or committed outcome; Undo state and `mia1` values equal ARM; 0 adapter
    calls during rollback verification; P2–P5 0/0/0; ordinary `BodyTest` Apply committed.
- **Session 4 S4F (2026-10-06, pid 17544, broker `0x311d72b0`, window `0x30bea698`):**
  - both injected Fits authorized under G1, stage `index=0 gfit=ac45e5c1… literals=34`, writes
    inside the open Undo (`changed_sides=3`, real predicate True);
  - CONTROL: `PROD_CLOTHING_FIT_ABORT_VERIFY … restored=True`, `not-committed`, "Nothing changed";
  - GATE: real verifier True, substituted False → `restored=False`, `abort-unverified`, dialog
    `recovery_unverified=[assaultsuitbody1] unattempted=[loinclothbra_chadfix_071] undo_count=0`;
  - stage lease outstanding (1) during rollback verification, 0 adapter calls, exactly one
    successful `release()`; target 2 never staged; nothing committed; P2–P6 0/0/0;
  - ordinary Fit committed-verified and released ok; one Undo restored it visually.
- **§22 item 8 `I8A1` (2026-10-08, pid 36912, broker `0x310a7810`):** see Current milestone and
  `ITEM8_EVIDENCE.md` §6. Sessions 1–4 above qualify `9a78fc96…`; `I8A1` qualifies `bfba4d3a…`.
- **Measurements (Session 1):**
  - process working set +36 MB across the session;
  - CPM scope 107–166 KB;
  - broker retained 666–888 KB;
  - authorization about 0.02 s; warm stage about 0.02 s; one Fit target 0.146 s; scope build
    1.2–1.5 s.

## Unresolved
- **U0A residuals (updater; experimental, pre-L):**
  - Unproven:
    - power/cache-loss durability (R2 C10; a hard-reset campaign is still required, not waived;
      no hard reset of this machine is authorized);
    - cross-user and standard-user lock contention (A4 deferred; not waived);
    - real disk-full (simulated only);
    - AV/indexer interference.
  - L design inputs:
    - F4: the live `publisher.lock` inside `sfm_shared_authority`: approved direction is preserve
      and recognize a verified legacy file in place; implementation details are unqualified;
    - F7: path-length budget at the real installation depth (U0A ran on C:, not E:).
  - U0B questions are in report §8; the P0 acceptance evidence is ruling §7.
- **U0B unqualified boundaries (separately gated; no waiver of C10, C11 or any other approved
  requirement follows from the P1 PASS):**
  - native SFM authority-open behavior and actual transition concurrency;
  - CPM and Normalizer UI refusal handling;
  - full legacy-publisher exclusion (only lock acquisition tested);
  - power-loss durability and cross-user contention;
  - final updater/installer integration, packaging and release qualification.
- **U0B open items:** native Master access; the CPM working directory; the native channel/key
  oracle (a scratch G3 pair now exists); bytecode content; AV interference; restoration
  recoverability; consumer MAX_PATH (P1-F1, sidecar path tested; Master threshold not measured);
  busy-versus-missing messaging (P1-F2, still potentially misleading at broker level); real
  running-SFM detection (P1/C1 used injected responses); `intent_schema()` diagnostic hardening for
  JSON scalar/list input (pre-production, non-blocking; fail-closed). See Current milestone and
  Previous milestone (P0).
- **K/L residuals from R15 (not in R15 scope, unchanged):**
  - Normalizer namespace isolation (the Normalizer still runs in the shared `__main__`);
  - the shared window slot, log name and identity strings that old CPM builds also claim.
- **Deferred UI findings (product/UI work; none are Session 1 blockers):**
  1. **Legacy preset.** Still open. Apply of an old `body.scale.head` preset is refused. Future
     message: "This preset uses an outdated scale format. Delete this preset and save a new Body
     preset." This is a legacy edge case only; generic bone-scale persistence works.
  2. **Implemented in the pre-K UI polish pass, LIVE VERIFIED / PASS (final build `4e35f292…`,
     U2 + U3):**
     - Update Preset confirmation copy, with no question icon;
     - wider window with all tabs visible;
     - semantic button colors;
     - 2×2 Review grid;
     - Clear Classification wording.
- **Stale-scope UI presentation** and **`SidecarMissing` messaging:** undecided.
  - Real SFM shows that a stale-generation refusal is presented through the guard's generic copy.
    For Apply this is "Preset could not be applied safely…"; for Save it is "Can't save preset —
    Preset could not be saved. Nothing was saved."
  - The stale-scope reason is logged only, and CPM then rebuilds automatically.
- **Product identity strings** (window slot, log name, `PROD_VERSION`) are unchanged from G18AN
  (K/L).
- **Item-8 findings (K/L; user-facing, not failures):**
  1. **Scene source.** CPM resolves its scene from the shot under the playhead
     (`sfmApp.GetShotAtCurrentTime()`). The Normalizer uses the Clip Editor selection. The UI pass
     explains the playhead workflow in Help only; the behavior is unchanged by design.
  2. **Normalizer success.** A successful Normalizer run shows no visible completion confirmation.
     Recommendation: a non-blocking success notice, with modals only for failures or decisions.
- **Remaining pre-K qualification:**
  - Session 2: **COMPLETE — PASS** (S2-A_R2 and S2-B_R2).
  - Session 3: **COMPLETE — PASS** (S3 CORE PASS and S3_ADD).
  - the forced Apply and forced Fit rollback-verification failure gates: **Session 4 COMPLETE —
    PASS** (S4A, S4F);
  - §22 item 6 (historical authority cleanup): **COMPLETE — offline qualification PASS**
    (candidate `1e866871…`; not real-SFM qualified);
  - §22 item 7 (diagnostic/development logging reduction): **COMPLETE — offline qualification
    PASS** (candidate `bfba4d3a…`; not real-SFM qualified);
  - §22 item 8 (focused post-cleanup regression, including post-cleanup real-SFM qualification):
    **COMPLETE / PASS** (`I8A1`, 2026-10-08; candidate `bfba4d3a…` real-SFM qualified and
    installed).

  - Pre-K CPM UI polish pass: **LIVE VERIFIED / PASS** (`7e4686d7…`, U2; supersedes `5c6e2789…`,
    whose U1 attempt was closed as SUPERSEDED / NO QUALIFICATION VERDICT). It is superseded in the
    repository by the Help-wording-only candidate `4e35f292…` (U3 LIVE VERIFIED / PASS; installed).

  - Final pre-K UI build `4e35f292…`: **LIVE VERIFIED / PASS** (U3, Help wording delta from U2).

  **Pre-K complete. `4e35f292…` is the exact CPM candidate eligible to enter K.**
  - **K — COMPLETE / PASS** (K1A2 + K2A1, 2026-10-10).

  L has not started; it needs separate authorization. L's final installation layout is undecided.
- **Session 4 notes (not failures; carried to K; unchanged by items 7–8):**
  - Fit's exception path releases the stage with a bare `release()` (no
    `PROD_CPM_FIT_STAGE_RELEASED` line; result discarded); a raising success-path release could in
    theory be followed by a second `release()`. Live S4F shows exactly one successful release per
    injected stage.
  - The Body bone-scale branch of rollback verification is covered offline only (`BodyTest` changes
    no bone scales); Expression Apply shares `prod_apply` and is covered offline.
- R3, R6, R9, R13, R14, R15: CLOSED. Offline: Suites 1–4 PASS; C7–C10 PASS (C10 also real-SFM);
  R15 suite PASS.

## Next
Stop. This is the U0B-P1 final closeout checkpoint (documentation only, 2026-10-14).
- **Next action:** a **U0B-P2 design conference** on passive ordinary-SFM observation under unchanged
  G1 authority.
- **P2 execution is NOT AUTHORIZED.** No observation method, elevation, tracer installation, G3
  deployment or live fault experiment is approved.

U0B-P2 execution, P3 and L (installation/coexistence/release qualification, handoff §24) are NOT STARTED and
each need separate authorization; live fault injection is on HOLD. K is COMPLETE / PASS; U0A is PASS (bounded). `4e35f292…`, the production
Normalizer `1f4ec5a2…` and exact G1 authority remain installed.

## Checkpoints
Update this Ledger and output its complete, concise contents when:
- The milestone is complete and checked.
- Progress is blocked or requires an owner decision.
- A Blueprint conflict, scope expansion, or unmet prerequisite is found.
- Work is being paused or transferred.

State why the checkpoint occurred. Stop at milestone completion.
For blockers or conflicts, pause affected work until resolved.
The owner relays the updated Ledger to the designer, or the designer
retrieves that same version from the shared repository.

## Maintenance
Replace stale entries; keep checkpoint content about one screen.
Preserve unresolved issues. Label uncertainty and untested claims.
Keep history in Git or an archive. Routine edits do not require a
full Ledger report.
