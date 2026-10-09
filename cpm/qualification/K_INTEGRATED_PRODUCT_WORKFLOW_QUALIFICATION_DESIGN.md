# K — Integrated CPM/Normalizer product workflow qualification (design and runbook)

**Status: DESIGN PREPARED FOR REVIEW — not executed.** No SFM process has been started for K. Nothing
was deployed. The K tooling (K-0, §6) has not been built, and no production code was changed. K and L
have not started.

| Item | Value |
|---|---|
| Design checkpoint | `241ce1c9c142f384dcf07dba28e21f974c45d2ac` (HEAD = `origin/master` when this design was written) |
| Exact CPM build under K | `4e35f29242351317f2f961c27e19d66fcd3355cff964b081431fc2fff1f5b9d7` (pre-K U3 LIVE VERIFIED / PASS; installed) |
| Governing obligations | `docs/qualification/CPM_CONVERGENCE_INTEGRATION_HANDOFF.md` §21 (last line), §23, §24 |
| Status of record | `cpm/qualification/CPM_CONVERGENCE_LEDGER.md` |

K is the integrated product-workflow stage. It shows that the final CPM and the production Normalizer
behave coherently as **two consumers of one authority** in ordinary real-SFM use. K changes no
product code. It does not change:
- the CPM app or launcher;
- the Normalizer;
- the CPM adapter or projection;
- the shared authority package;
- the Master, manifest or sidecar generation rules;
- the UI, installation layout, packaging or product identity strings.

K does not begin L, and it is not a replay of Sessions 1–4 or item 8.

---

## 1. Starting identities (pinned; verified read-only by `K-Preflight` before every K process)

| Identity | SHA-256 / value |
|---|---|
| Repository | HEAD = `origin/master` = the K-0 checkpoint that commits the K tooling (§6). Tracked worktree clean. |
| CPM private app (installed `usermod/scripts/ChadChan3D_CPM/SFM_Character_Preset_Manager.py`) | `4e35f29242351317f2f961c27e19d66fcd3355cff964b081431fc2fff1f5b9d7` (= repository `cpm/app/…`) |
| CPM launcher (Scripts menu `ChadChan3D/SFM_Character_Preset_Manager.py`) | `996ca483d625d37feb8d8f38a8d13db16f999d4189d98434db9c284a0a458c51` |
| Production Normalizer (`ChadChan3D/Rebuild_Control_Groups_Normalizer.py`) | `1f4ec5a26605aa90380eb0532fec3915d2cc24a3a20473ed70d57198bd995db7` (= `audit_external_runtime/…`) |
| CPM authority adapter / projection | `e96e21b537b5892fc5c1139b2396bbf5e3ce48a521b45876035d78789f126607` / `9b077a1baf491262901812620c380a45eeb9cb2bf75ddc28a08ab18612faffc1` |
| Shared authority package (`sfm_master_authority_productionized`, 23 files) + `sfm_master_sidecar` (3 files) | Equal to the accepted installed manifest. CRLF-normalized `.py` digest `97ec7baf8980411f06a61031fc215e978e80ed999196679a37ddc7bb6da73c28`. API `1.0.0-b2a`, build `package-boundary-corrected-2026-09-22`. |
| Live Master G1 / manifest / single sidecar | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` / `d810d6486305a098d4855eea15f6feea3dc7fe7f7aaf97a08415fcac8e7701d6` / `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` |
| G2 (K2 only; frozen Session 2 generation tooling) | Master `54413b6ca618f73733b6624e1d2411a6cfb00a24489330ccbfc153760f3486e7` (G1 + one trailing LF). Sidecar `cd370f67bfd4db6a17fdc3d425ffae6934ad223c2f5519eda99e3f5b2264ffe3`. Manifest after publication `9da5057f810e530d363a016289301fb3c8c1b2fe21f69d8fe10bfd86620bfda1`. |
| Scripts deployment before K | 1,511 files; the U3 inventory `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086`. This equals the accepted Session 4 inventory (`cefc2b88…`) except the private-app line. It includes the OWNER-1 historical files: present, inert, never invoked. |
| Fixture document | `testscripts.dmx` (local SFM sessions folder), `197e6011faae2da539d0a06ae4924288104b956348cd1c4e0ef80618f9e4e16f`, 16 film clips. **Never saved.** |
| Logs | CPM: `%PUBLIC%\Documents\SFM_CSP_G18AN_SaveNewCopy.log` (cumulative; read from the preflight offset). Normalizer: `%PUBLIC%\Documents\sfm_rebuild_control_groups.txt`, **which is truncated at the start of every run**, so it is collected after every run. |

Any mismatch is a read-only STOP. Resolve it and rerun the preflight. K never repairs a mismatch in
place.

## 2. What K proves, and what it reuses

### 2.1 Reused (decisively qualified; not rerun)

| Behavior | Evidence reused |
|---|---|
| Canonical runtime; one process broker shared by CPM and the Normalizer (C10) | Session 1 C10; R15 addendum; item 8 D5 (`cpm_compat_v1` and `normalizer_compat` on one broker) |
| CPM Body/Expression Save/Update/Apply, native Undo, ordinary Fit, persistence | Sessions 1–4; item 8 B–C (exact build lineage, byte-bounded through the pre-K UI pass) |
| CPM stale-generation refusal: open window (Apply), Save prompt, Fit between targets; no replay; rebuild | Session 2 (S2-A_R2, S2-B_R2); Session 3; item 8 E. Item 8 E is also the **CPM-first-after-transition with Normalizer G1 views present** case (§3.4). |
| CPM rollback-verification failure gates | Session 4 (S4A, S4F) |
| CPM close/reopen lifecycle, R15 isolation, repeated launcher clicks | R15 addendum; item 8 A/F |
| Normalizer single-command correctness (Selected and All Shots) | C2-1, D2-2 |
| Normalizer later-vocabulary freshness | G-1 |
| Normalizer generation replacement: next command pins G2 (I1); a change during a command fails closed (I2) | I-1 |
| Normalizer protected Master handle | J-1 |
| Normalizer process-lifetime scope guard; repeated Selected runs | F3-Guard; F1/F2 |
| Presentation of the final build | pre-K U2 + U3 |

### 2.2 Proven in K (unproven integration relationships)

1. **Normalizer first → CPM.** The Normalizer constructs the process broker (cold); CPM later joins
   the same broker. Every earlier campaign had CPM first.
2. **CPM first → Normalizer**, in K2 (cold CPM start) and repeatedly in K1.
3. **Repeated alternation** in one process: at least two complete N→C and C→N cycles, with CPM idle
   between consumers and no refusal, stale state, rebuild or lease left behind.
4. **CPM open while the Normalizer operates**, both on a different shot (divergent ingress) and on
   the shot that holds CPM's scoped character (convergent ingress).
5. **Close orders:**
   - **X:** CPM stays open across Normalizer commands and closes afterwards.
   - **Y:** CPM closes, the Normalizer runs, CPM reopens.
   - **Process exit:** SFM exits with the CPM window open (K1) and with it closed (K2).
6. **Independent consumer/view lifetimes:**
   - each consumer's broker views persist or are replaced independently of the other consumer's
     window or command lifetime;
   - no consumer leaves a lease;
   - CPM close/reopen does not disturb Normalizer views, and Normalizer commands do not disturb
     CPM's pure scope.
7. **Joint generation transition** (K2): both consumers hold G1 state; exact G2 is activated with the
   frozen Session 2 tooling; the **Normalizer touches G2 first**, then CPM is refused and rebuilds;
   both then alternate under G2.
8. **Shared failure/recovery:** the stale-generation boundary as experienced by both consumers in
   one process (§3.5; see decision D1 for authority-unavailable).
9. **Aggregate resources** across the integrated workflow at settled checkpoints (§5.4).
10. **Representative ordinary workflows** for each tool:
    - CPM: Body Save New / Apply / Undo, Expression Save New / Apply / Undo, Clothing Fit / Undo,
      Refresh Model List, Delete Preset;
    - Normalizer: Rebuild Selected Shot(s) on a one-target shot, on the two-target shot that holds
      CPM's character, and repeated on the same shot.

## 3. Ingress model, fixture and scope assignments

### 3.1 The two ingress rules (preserved by design, never unified)

- **CPM** takes its scene from the shot **under the playhead** (`sfmApp.GetShotAtCurrentTime()`) when
  the model list is built (launch or **Refresh Model List**).
- **Normalizer** operates on the **Clip Editor selection** (`sfmClipEditor.GetSelectedShots()`;
  Rebuild Selected Shot(s) requires at least one selected shot).

Every operator step names both the **playhead shot** and the **selected shot(s)** that must hold.
The operator confirms them visually before any consumer action.

### 3.2 Fixture inventory (read-only `dmxconvert` of a temporary copy; source unchanged)

| Shot | Animation sets (model) | Role in K |
|---|---|---|
| `shot10` | `krystal20201` (krystal2020), `assaultsuitbody1`, `loinclothbra_chadfix_071` | **CPM-only** playhead shot: Krystal Body/Fit workflows. The Normalizer never selects it. |
| `shot3` | `foxmccouldwm1`, `mia1` | **Shared** shot: CPM Mia playhead scope and the Normalizer convergent selection. The Normalizer rebuilds 2 targets here (item 8 D). |
| `shot9` | `krystalv21` (krystalv2) | **Normalizer-only** selection shot: one target, a different model from CPM's Krystal. Used in G-1/I-1. |
| `shot12` | the same three Krystal sets as `shot10` | **Excluded.** It duplicates `shot10`'s identities, so a wrong playhead could silently scope the wrong instance. The playhead must never be in `shot12`. |
| others | various | Excluded from K. |

### 3.3 Divergent and convergent states

| State | Playhead (CPM) | Selection (Normalizer) | Purpose |
|---|---|---|---|
| **DIV** | `shot10` (Krystal scope) | `shot9` only | The two products act on different shots and models. CPM must be unaffected by the run. |
| **CONV** | `shot3` (Mia scope after Refresh) | `shot3` only | The Normalizer rebuilds the control groups of CPM's scoped character. CPM must continue without stale refusal or rescope (extends item 8 D to repetition). |

### 3.4 Generation-transition order coverage

| First consumer to touch G2 | Evidence |
|---|---|
| CPM, with Normalizer G1 views present | **Reused:** item 8 E (Normalizer ran under G1 in D; CPM refused/rebuilt under G2 in E) |
| Normalizer, with CPM holding G1 scope | **K2** (new) |

After the first touch, K2 alternates both consumers under G2, so both relative orders of subsequent
use are covered.

The frozen tooling supports exactly one in-process transition: G1 → exact G2. Restoration to G1 is
SFM-closed only (`S2-Finalize`). K invents no other transition method. This is why K needs one
dedicated process for the joint transition, and why the second first-touch order is reused rather
than rerun.

### 3.5 Shared failure/recovery

- **Exercised:** the stale-generation boundary in K2.
  - **Normalizer:** pins the generation at command start, so it never uses G1 under G2 (fresh G2
    pin).
  - **CPM:** exactly one generation-mismatch refusal before mutation, then an automatic rebuild,
    then a deliberate action that commits under G2.
  - **Recovery:** both consumers then work normally under G2 in the same process.
- **Not exercised:** a shared **authority-unavailable** state (for example a Master with no matching
  sidecar). There is no qualified mechanism to create it: the frozen tooling has only
  `check-only`, `prepare-publish-g2`, `activate-g2` and `finalize`. See **D1**.
- **Not exercised:** a mid-command Master change (I2 needed a method injector) and Normalizer
  mid-command cancellation (not a product contract; the ledger records N/A).

### 3.6 Disposable mutations (all reversible or discarded)

- **Scene:** CPM Apply/Fit are native-undoable, and every one is undone in K. Normalizer rebuilds are
  not single-step undoable (ledger: N/A by contract); they live only in the open session, which is
  **never saved**. Every process ends with SFM exit and **Don't Save**. The fixture SHA-256 is
  verified unchanged after each process.
- **Preset libraries:**
  - K creates only presets named `K <attempt> <step>` (for example `K K1A1 B1 BODY`) in the Krystal
    and Mia libraries;
  - each library change is inventoried before and after, with footprint rules as in item 8;
  - K1 ends by deleting its own presets with CPM's **Delete Preset**, which moves them to Trash;
  - existing presets (including item-8 `I8 I8A1 …`) are never touched.
- **Authority:** K1 leaves it untouched (G1 throughout). K2 restores exact G1 with `S2-Finalize`,
  SFM closed.

## 4. Process plan

| Process | Purpose | Normalizer commands | Why separate |
|---|---|---|---|
| **K1** (fresh; G1) | Normalizer-first cold start; CPM joins; divergent and convergent ingress; repeated alternation; close orders X and Y; exit with CPM open; aggregate resources | 4 × Selected (`shot9`, `shot9`, `shot3`, `shot3`) | — |
| **K2** (fresh; G1 → G2) | CPM-first cold start; joint generation transition with the Normalizer touching G2 first; shared stale-generation recovery; G2 alternation; exit with CPM closed; exact G1 restoration | 3 × Selected (`shot9` G1, `shot9` G2, `shot3` G2) | The only qualified in-process transition is one-way and its restoration is SFM-closed. Combining it with K1 would push the Normalizer count past the bounded budget (§5.4). |
| **K3** (optional; fresh; G1) | All Shots with CPM resident | 1 × All Shots | See **D2**. The admission guard allows All Shots only as the first Normalizer use in a process, and its memory demand is near the 32-bit ceiling. |

**Fresh SFM processes: 2 required (K1, K2), plus 1 if D2 includes K3.** One process cannot hold
Normalizer-first cold start and CPM-first cold start together. The transition's prerequisites (both
consumers in G1 state, a bounded Normalizer count, SFM-closed restoration) conflict with K1's
budget.

## 5. Instrumentation and evidence

### 5.1 Automatic evidence (driver and probe; no owner judgment)

- **Attempt folder:** `%PUBLIC%\Documents\CPM_K\<attempt>\`, write-once, sealed by `SHA256SUMS.txt`.
  Attempt IDs are `K1A1`, `K2A1`, … (a retry is a new ID in a new fresh process).
- **Preflight/deployment records:** identities (§1); Scripts inventories; dependency verification;
  CPM log offset; exact G1 inventory. **Only the probe and the attempt pointer are deployed. The CPM
  app is not redeployed.**
- **K probe `P`** (Scripts > ChadChan3D > `CPM_K_Probe`), observation-only and derived from the
  item-8 probe. Each run writes one JSONL record and one scene snapshot. Captured:
  - PID;
  - CPM private-module identity, run ID, window class/ids, census, watchers;
  - historical-provider inactivity;
  - broker id and canonical origin;
  - outstanding and unreleased leases, provider counters (opens/closes/current);
  - view-cache entry count;
  - **ledger snapshot decomposed per cache key (generation SHA, consumer kind, coverage size)**;
  - the tail of `recent_diagnostics()` (for example `cohort_acquired`, `fully_reused_no_provider_open`);
  - `__main__` name census (CPM names absent; the Normalizer's shared-`__main__` names recorded);
  - CPM scope generation and counts;
  - fixture snapshot (the named sets' controls and values, Undo count/description);
  - process resources (private bytes, working set, handles, GDI, USER, free VAS).

  It calls only read accessors, never acquires, constructs, releases or mutates, and records "no
  acquisition by probe" mechanically.
- **Normalizer log, collected after every run (it truncates per run):** `SELECTED_SHOTS` and scope
  shot names; eligible/changed targets; `PRODUCTION_REBUILD_CONTROL_GROUPS` and `PRODUCTION_CONTEXTUALIZER`
  results; logged live Master SHA (generation pin); `mem_ok` counts and VAS; absence of `PROD_` (CPM)
  lines.
- **CPM log excerpt since the offset:**
  - `PROD_R15_MODULE` build (exactly `4e35f292…`), one run ID;
  - `PROD_PROVIDER_HEALTH` and its generation;
  - authorizations and refusals;
  - Save/Update/Apply/Fit results;
  - `MODAL_YIELD_ENTER/EXIT` around the Normalizer scope dialog;
  - close request/finalized;
  - no historical or removed formats.
- **Library inventories and readbacks** around every CPM Save/Delete (footprint rules from item 8).
- **Generation records** (K2): the frozen `S2-PhaseA`/`S2-PhaseB`/`S2-Finalize` record set.

### 5.2 Owner visual confirmation (stated per step)

- The playhead shot and selected shot match the step (Clip Editor and Animation Set Editor).
- A CPM dialog appeared with the stated text (for example "Body Preset saved"), and Undo visibly
  restored the character.
- The Normalizer completed: SFM becomes responsive again. **No completion notice is expected**
  (carried behavior); completion is adjudicated from its log.
- No unexpected dialog, error or freeze. Any one of these is a STOP.

### 5.3 Idle and lifetime expectations at integration boundaries

- **Idle** = no CPM operation, no Normalizer command running, and broker outstanding = 0,
  unreleased = 0, current open providers = 0.
- Every `P` after a consumer action must be idle.

| Boundary | Expectation |
|---|---|
| After a Normalizer command | +1 Normalizer view for the command's coverage/generation, or a reuse diagnostic for identical coverage and generation. CPM window, module, run, scope generation and fixture values for non-target sets unchanged. |
| After a CPM scope build | A `cpm_compat_v1` view for the current generation; Normalizer views still present. |
| CPM close / reopen | Same module, class and run; new window; Normalizer views unaffected. |
| After G2 activation, before any touch | No acquisition, no refusal (the CPM log is quiet). |
| After the first Normalizer G2 command | G2 `normalizer_compat` view; no G1 reuse for it. CPM still shows its G1 scope, holding no lease. |

### 5.4 Resource checkpoints (aggregate, not a benchmark)

- **Settled checkpoints:** every `P` taken after a Normalizer command completes and after each CPM
  close.
- **Comparisons:**
  - equivalent closed-CPM states across cycles: private bytes, handles, GDI and USER;
  - the Normalizer's own `mem_ok`/VAS per run.
- **Accepted known behavior (F, not attributed to CPM):** the Normalizer's per-command retained
  growth from fresh discovery. K records it; it is not a CPM defect.
- **STOP (before the next Normalizer command) on any of:**
  - `mem_ok=False` in any Normalizer run;
  - free VAS reported by `P` below 600 MB;
  - process private bytes above 3,600 MB.
- **CPM-attributable accumulation is FAIL:** across two equivalent closed-CPM states with no
  Normalizer command between them, private bytes +>10 MB, or handles/GDI/USER growing by more than
  10 per cycle in the same direction twice.
- **Budget:** at most 4 Selected commands per process, on one- or two-target shots only (inside the
  F3-qualified envelope).

### 5.5 Adjudication

After each process, a reviewer adjudicates mechanically from the sealed folder. This is never done
during SFM manipulation, and no step is waived or reinterpreted in place.

## 6. K-0 — tooling preparation (separate step, after this design is approved)

These files go under `real_sfm_qualification/cpm_k_integrated/` and are qualification-only. No
production file is changed.
- `CPM_K_Probe.py`: the item-8 probe with K pins (`4e35f292…`, K attempt root and pointer). Adds the
  per-cache-key ledger decomposition, the `recent_diagnostics()` tail, the free-VAS sample and the
  `__main__` census of non-CPM names. All reads stay read-only.
- `K_DRIVER.ps1`:
  - the frozen Session 2 §2.1 block, byte-identical;
  - `K-New` (write-once attempt);
  - `K-Preflight` (read-only identity gates §1, Scripts inventory = U3 inventory, exact G1, library
    inventories, CPM log offset);
  - `K-DeployProbe` (probe + pointer only; exact two-line Scripts difference);
  - `K-CollectLogs <label>` (CPM excerpt; Normalizer log copy; fingerprints);
  - `K-Library`, `K-Readback`;
  - `K-GenerationSwitch` (frozen `S2-PhaseA` + `S2-PhaseB`);
  - `K-Finalize` (frozen `S2-Finalize`, K2 only);
  - `K-RemoveProbe` (exact restoration of the U3 inventory);
  - `K-Seal`;
  - `K-Disposition`.
- `k_evidence_reader.py` (offline parser/adjudicator), `K_FIXTURE_MANIFEST.json`, an operator-record
  template.
- Offline qualification under Python 2.7.5 (real PySide/Qt 4.8 + model) and 3.10, following the
  item-8 precedent. It covers:
  - probe purity (no acquisition, no mutation, write-once/append-only);
  - ledger/diagnostic decomposition;
  - reader formats against the real CPM and Normalizer format strings;
  - driver sandbox end-to-end, including G1→G2→G1 with the real frozen tooling.
- K-0 ends with a commit and push marked **K PREPARED, NOT RUN**, then stops for execution
  authorization.

## 7. Global operator rules

1. One fresh SFM process per K process. Start SFM only when the driver prints `K READY … Start a
   FRESH SFM process`.
2. **One exact human action at a time.** The executor gives the next action only after the operator
   reports the previous one and the executor has verified the evidence on disk.
3. Before every consumer action, confirm the stated **playhead shot** and **selected shot(s)**. If
   either is wrong, STOP; do not "fix and continue" silently.
4. Never move the playhead into `shot12`, never use **Rebuild All Shots** (except K3), never save the
   document, never run other scripts (including `CPM_Session1_Probe`), and never touch historical
   menu builds.
5. Expected refusals are listed per step. **Any other refusal, error dialog, stale-generation event,
   rebuild, authority mismatch, unexpected scene value or freeze → STOP.** Do not retry, dismiss and
   continue, or reinterpret. The executor collects evidence (`P` if possible, `K-CollectLogs`) and
   reports to the owner, who decides.
6. Normalizer completion is the return of SFM responsiveness plus the executor's log verification.
   No completion dialog is expected.

## 8. K1 runbook (fresh process; G1; Normalizer-first)

Shell steps run with SFM closed unless stated. **P** = run `CPM_K_Probe`; the executor verifies the
record before the next step.

| Step | Actor | Action | PASS / expected | STOP if |
|---|---|---|---|---|
| K1-S1 | Shell | `K-New K1A1 <fixture>`; `K-Preflight K1A1 -Owner1Recorded`; `K-DeployProbe K1A1` | `K READY` with all §1 identities exact | any gate fails |
| K1-S2 | Owner | Start SFM fresh. **File > Open** `testscripts.dmx`. Move the playhead into **`shot9`**. In the Clip Editor, select **only `shot9`**. Do not open CPM. | Document open; `krystalv21` listed; `shot9` sole selection | a load error, or SFM not fresh |
| K1-S3 | Owner | P | P0: no CPM module, **no broker constructed**, Normalizer marker unused; resource baseline | a broker already exists, or CPM is loaded |
| **K1-A1** | Owner | Scripts > ChadChan3D > `Rebuild_Control_Groups_Normalizer` → **Rebuild Selected Shot(s)**. Wait until SFM responds. | — | any dialog other than the scope dialog |
| K1-A2 | Shell | `K-CollectLogs N1` | Normalizer: `SELECTED_SHOTS` 1 [`shot9`]; PASS/PASS; live Master G1; `mem_ok` all True; no CPM lines | any other result |
| K1-A3 | Owner | P | **Broker constructed by the Normalizer** (canonical origin); one G1 `normalizer_compat` view; idle 0/0/0 | lease outstanding, or not idle |
| **K1-B1** | Owner | Move the playhead into **`shot10`**. Do not change the Clip Editor selection. Scripts > ChadChan3D > `SFM_Character_Preset_Manager`. Choose **`krystal20201`** in Character Model. | One CPM window; counts appear | a dialog or error |
| K1-B2 | Owner | P | CPM module `4e35f292…`; **same broker id as K1-A3**; `cpm_compat_v1` G1 view added; Normalizer view still present; idle | different broker; Normalizer view gone; not idle |
| K1-B3 | Owner | Body Presets → **Save New** `K K1A1 B3 BODY` → OK. | "Body Preset saved" | other text |
| K1-B4 | Shell | `K-Library`, `K-Readback B3` | Exactly one new preset (Krystal library); within footprint | anything else |
| K1-B5 | Owner | Clothing Fit tab: check only `assaultsuitbody1`; **Fit Selected to Model**. | "1 item updated" | other text |
| K1-B6 | Owner | **Edit > Undo** once. Then P. | The suit visibly returns. P: fixture equals the pre-Fit values; idle | a value difference; not idle |
| **K1-C1** | Owner | **DIV state:** confirm the playhead is in `shot10` and the selection is only `shot9`. Leave CPM open on Krystal. Run the Normalizer → **Rebuild Selected Shot(s)**. Wait. | CPM palette hides during the scope dialog and returns | a dialog or error |
| K1-C2 | Shell | `K-CollectLogs N2` | Normalizer `shot9` PASS/PASS G1; `mem_ok` True. CPM log: `MODAL_YIELD_ENTER/EXIT restored=True` only, no authorization or refusal. | any CPM refusal or stale event |
| K1-C3 | Owner | P | Same broker; Normalizer `shot9` view reused or replaced per diagnostics; CPM scope generation and Krystal fixture values unchanged; idle | anything else |
| K1-C4 | Owner | In CPM (still Krystal), Body Presets → select `K K1A1 B3 BODY` → **Apply Preset**. Then **Edit > Undo** once. | "Body Preset applied"; then visual return | any refusal or "can't" dialog |
| K1-C5 | Owner | P | Apply committed under G1 with **no stale refusal or rescope**; after Undo the values equal K1-C3; idle | anything else |
| **K1-D1** | Owner | **CONV state:** move the playhead into **`shot3`**. In CPM click **Refresh Model List**, then choose **`mia1`**. | Mia counts appear | a dialog or error |
| K1-D2 | Owner | Expressions → **Save New** `K K1A1 D2 EXPR` → OK. | "Expression preset saved" | other text |
| K1-D3 | Shell | `K-Library`, `K-Readback D2` | One new preset (Mia library); within footprint | anything else |
| K1-D4 | Owner | In the Clip Editor, select **only `shot3`**; the playhead stays in `shot3`. Run the Normalizer → **Rebuild Selected Shot(s)**. Wait. | Returns responsive | a dialog or error |
| K1-D5 | Shell | `K-CollectLogs N3` | Normalizer `shot3` (2 targets) PASS/PASS G1; `mem_ok` True; CPM log quiet apart from the modal yield | anything else |
| K1-D6 | Owner | P | Same broker; CPM Mia scope intact; idle | anything else |
| K1-D7 | Owner | Change one Mia face slider (Animation Set Editor) to a clearly different value. In CPM, Expressions → `K K1A1 D2 EXPR` → **Apply Preset**. Then **Edit > Undo** once. | "Expression applied"; then the slider returns | any refusal |
| K1-D8 | Owner | P | Apply committed G1 with no rescope; Undo restored; idle | anything else |
| **K1-E1** | Owner | Close CPM with the title-bar **X** (close order X: CPM outlived N2 and N3). P. | Slot empty; module resident; Normalizer views present; idle | anything else |
| K1-E2 | Owner | With CPM closed (close order Y), selection **only `shot3`**, run the Normalizer → **Rebuild Selected Shot(s)**. Wait. | Responsive | a dialog or error |
| K1-E3 | Shell | `K-CollectLogs N4` | `shot3` PASS/PASS G1; `mem_ok` True | anything else |
| K1-E4 | Owner | P (settled resource checkpoint) | Idle; resource rules §5.4 | any §5.4 STOP |
| K1-E5 | Owner | Reopen CPM (Scripts menu); choose **`mia1`** (playhead still `shot3`). P. | Same module/run, new window; G1 scope; idle | anything else |
| K1-E6 | Owner | Expressions → `K K1A1 D2 EXPR` → **Delete Preset** → confirm. Move the playhead into **`shot10`**, **Refresh Model List**, choose **`krystal20201`**, Body Presets → `K K1A1 B3 BODY` → **Delete Preset** → confirm. | Both moved to Trash | anything else |
| K1-E7 | Shell | `K-Library` | Libraries equal their pre-K state apart from the Trash entries | any other difference |
| **K1-F1** | Owner | P (final settled checkpoint). Then, **with CPM still open**, exit SFM (**File > Exit**) and choose **Don't Save**. | SFM exits normally | a hang, crash or extra dialog |
| K1-F2 | Shell | `K-CollectLogs final`; `K-RemoveProbe K1A1`; fixture hash check; `K-Seal K1A1` | U3 inventory restored exactly; fixture unchanged; G1 untouched | anything else |

**K1 PASS:** every step as stated in PID-continuous K1; one run ID; one broker for both consumers
throughout; 4 Normalizer PASS with `mem_ok` True; every CPM action committed with no refusal, stale
event or rescope; idle at every P; §5.4 rules hold.

## 9. K2 runbook (fresh process; joint generation transition)

| Step | Actor | Action | PASS / expected | STOP if |
|---|---|---|---|---|
| K2-S1 | Shell | `K-New K2A1 <fixture>`; `K-Preflight K2A1 -Owner1Recorded` (includes `S2 BASELINE OK`); `K-DeployProbe K2A1` | `K READY` | any gate |
| K2-S2 | Owner | Start SFM fresh; open `testscripts.dmx`; playhead in **`shot10`**; Clip Editor selection **only `shot9`**. | — | — |
| K2-S3 | Owner | P | No broker yet | a broker exists |
| **K2-A1** | Owner | Open CPM (CPM first, cold); choose **`krystal20201`**. P. | CPM constructs the broker; G1 scope; idle | anything else |
| K2-A2 | Owner | Body Presets → **Save New** `K K2A1 A2 BODY`. | "Body Preset saved" | — |
| K2-A3 | Shell | `K-Library`, `K-Readback A2` | One new preset | — |
| K2-A4 | Owner | (DIV) Run the Normalizer → **Rebuild Selected Shot(s)** (`shot9`). Wait. | — | — |
| K2-A5 | Shell | `K-CollectLogs N1` | `shot9` PASS/PASS **G1** | — |
| K2-A6 | Owner | P | Same broker; G1 views for both kinds; idle | — |
| **K2-B1** | Shell | With SFM open and both consumers idle (CPM open on Krystal, no prompt): `K-GenerationSwitch K2A1` | `S2 PHASE A OK`, `S2 G2 ACTIVE OK` (exact G2) | any STOP from the frozen tooling: follow its printed instruction |
| K2-B2 | Owner | P | Live Master G2; **no acquisition, no refusal**; CPM still shows its G1 scope; leases 0 | any acquisition |
| **K2-C1** | Owner | (Normalizer touches G2 first) Run the Normalizer → **Rebuild Selected Shot(s)** (`shot9`). Wait. | — | — |
| K2-C2 | Shell | `K-CollectLogs N2` | `shot9` PASS/PASS with logged live Master **G2**; `cohort_acquired` for G2 (no G1 reuse) | G1 used, or FAIL |
| K2-C3 | Owner | P | A G2 `normalizer_compat` view; CPM window still G1 scope (pure, no lease); idle | a lease, or a CPM rebuild already happened |
| **K2-D1** | Owner | In CPM (still Krystal) Body Presets → `K K2A1 A2 BODY` → **Apply Preset**. | **Expected refusal:** "Preset could not be applied safely…" (generic guard copy). Dismiss it. CPM rebuilds and counts return. | no refusal, a different text, or a mutation |
| K2-D2 | Shell | `K-CollectLogs D1` | Exactly one `AUTHORIZATION_REFUSED … generation-mismatch`; no Apply outcome; `REBUILD_SCHEDULED` → `REBUILD` → one Select Model to healthy **G2**; no replay | anything else |
| K2-D3 | Owner | P | CPM G2 scope (same window); both kinds have G2 views; fixture unchanged since K2-B2; idle | anything else |
| K2-D4 | Owner | Deliberately **Apply Preset** `K K2A1 A2 BODY` again; then **Edit > Undo** once. | "Body Preset applied" (G1-provenance preset, compatible semantic set, §17); then visual return | any refusal |
| K2-D5 | Owner | P | Authorized **G2**, committed; Undo restored; idle | anything else |
| **K2-E1** | Owner | Select **only `shot3`** (playhead stays `shot10`, so the state is DIV). Run the Normalizer → **Rebuild Selected Shot(s)**. Wait. | — | — |
| K2-E2 | Shell | `K-CollectLogs N3` | `shot3` PASS/PASS **G2**; `mem_ok` True | — |
| K2-E3 | Owner | In CPM, **Delete Preset** `K K2A1 A2 BODY` → confirm. Close CPM with **X**. P. | Moved to Trash; closed; idle under G2 | — |
| K2-E4 | Shell | `K-Library` | Equal to pre-K2 apart from the Trash entry | — |
| **K2-F1** | Owner | With CPM closed, exit SFM; **Don't Save**. | Normal exit | — |
| K2-F2 | Shell | `K-CollectLogs final`; **`K-Finalize K2A1`** (`S2 RESTORED EXACT G1`); `K-RemoveProbe K2A1`; fixture check; `K-Seal K2A1` | Exact G1; U3 inventory; fixture unchanged | restoration not exact: do not start SFM; report |

**K2 PASS:**
- G1 → exact G2 is proven.
- The Normalizer's first G2 command pinned G2 and reused nothing from G1.
- CPM saw exactly one generation-mismatch refusal before any mutation, then exactly one rebuild with
  no replay.
- The deliberate G2 Apply committed.
- Both consumers then alternated under G2.
- Idle at every P.
- Exact G1 was restored.

## 10. K3 (optional, D2) — All Shots with CPM resident

Fresh process, G1. Open CPM first (Krystal, `shot10`), then **Rebuild All Shots** once: the first
Normalizer use, so the admission guard allows it. Then CPM: one Body Apply and Undo. Then exit with
**Don't Save**.

PASS:
- the All Shots PASS matches D2-2's target classes for this fixture;
- `mem_ok` True throughout;
- CPM continuation is unrefused;
- idle.

The §5.4 thresholds are **observational** in K3: a crash or `mem_ok=False` is a recorded K finding
(FAIL) for the owner's disposition, not something K repairs.

## 11. PASS / FAIL / INCONCLUSIVE / STOP and disposition

- **PASS (K):** K1 and K2 PASS (plus K3 if D2 includes it), with every observation present and every
  §5.4 rule holding.
- **FAIL:** a product behavior contradicts an expectation. Examples:
  - an unexpected refusal, rescope or stale event;
  - a lease left outstanding;
  - two brokers;
  - a wrong generation;
  - CPM-attributable accumulation;
  - a crash.
- **INCONCLUSIVE:** a required observation is missing, or an operator/procedure deviation prevents
  adjudication. A retry is a new attempt in a new fresh process.
- **STOP:** handled per §7 rule 5. There is never an in-place reinterpretation.
- **Disposition:**
  - authority is always restored to exact G1 (K2 by `K-Finalize`);
  - qualification-only material is always removed;
  - the installed CPM `4e35f292…` is not changed by K, on PASS or otherwise;
  - any product change after a FAIL needs a separate owner decision.
- **K PASS means:** "K — COMPLETE / PASS: integrated CPM/Normalizer product workflow qualified on
  CPM `4e35f292…` and Normalizer `1f4ec5a2…`." L remains not started.

## 12. Unresolved K/L notes — classification

| Note | Classification | Treatment |
|---|---|---|
| Normalizer executes in the shared `__main__` | **Carried as accepted known behavior; non-interference tested in K** | `P` records the Normalizer's shared-`__main__` names after each command and proves CPM's private module, globals and `__main__` absence are unaffected across every alternation. No Normalizer change in K. Any isolation change is a separate post-K product decision. |
| Old CPM/Normalizer generations share window-slot, log and identity naming | **Deferred to L** | Historical builds stay present and inert (OWNER-1). K proves none is invoked or loaded (probe historical check; log formats). Identity strings are not changed in K. |
| Different scene-selection semantics (playhead vs Clip Editor selection) | **Tested in K** (DIV and CONV states, §3.3) | This is accepted by design and documented in CPM Help. |
| No visible Normalizer completion notice | **Carried as accepted known behavior** | The K procedure accounts for it (completion = responsiveness + log). Any UX change is post-K/L product work. |
| Session 4 Fit release notes (bare `release()` on the exception path) | **Carried as a historical note** | K performs only ordinary Fit and never induces a Fit exception. |
| Body bone-scale rollback-verification branch covered offline only | **Carried as a historical note** | K's ordinary Body Apply may write bone scales but never fails, so the rollback branch is not exercised. |
| Stale-scope UI presentation (generic guard copy) | **Carried as accepted known behavior; observed in K2-D1** | — |
| `SidecarMissing` messaging undecided | **Carried; not exercised unless D1 chooses (b)** | — |
| Legacy `body.scale.head` preset message | **Carried** (legacy edge case) | — |
| Product identity strings (window slot, log name, `PROD_VERSION`) | **Deferred to L** | — |
| R15 note: the no-op Apply 0.2 s before a Normalizer report write ("alternation stays with K") | **Tested in K** | Repeated alternation in K1 and K2. |
| Normalizer repeated-command retained memory (F) | **Carried as accepted known behavior; bounded and recorded** | Command budget and §5.4 STOP thresholds. |

None is a genuine blocker to K execution. D1 and D2 are design decisions, not defects.

## 13. Decisions required before K-0 / execution

- **D1 — shared authority-unavailable failure.** No qualified mechanism creates it.
  - **(a) Recommended:** carry offline C7 (CPM fail-closed before mutation), I-1 I2 (Normalizer
    fail-closed) and the Normalizer's pre-mutation `ProbeError` path as the evidence. K exercises
    the stale-generation shared failure/recovery only.
  - **(b)** Authorize K-0 to prepare and offline-qualify a new controlled authority-unavailable state
    (for example a Master with no published sidecar, restored by the frozen finalize). That is a new
    mechanism, would extend K by one process, and would also settle the `SidecarMissing` messaging
    observation.
- **D2 — All Shots with CPM resident (K3).**
  - **Include** (recommended if a real heavy workflow must be covered): accept the 32-bit memory risk
    (D1-3 reached about 3.42 GB working set within one command) as an observational K finding.
  - **Or exclude:** carry D2-2 and F3 as Normalizer evidence and leave heavy-scene coexistence as
    accepted known behavior for L/user guidance.
- **D3 — divergent-ingress operation.** Can the operator select the `shot9` clip in the Clip Editor
  while the playhead stays in `shot10`, and the reverse, in this SFM build? If selecting a clip moves
  the playhead, K-0 rewrites K1-C1/K2-A4 to set the selection first and then the playhead, and each
  step's visual confirmation still applies. **The owner should confirm the exact SFM gesture.**
- **D4 — K-0 approval.** Approve preparing the qualification-only K tooling (§6) with a commit and
  push "K PREPARED, NOT RUN" before any execution authorization.

**Prerequisite noted, not a decision:** SFM was running (PID 14316, from pre-K U3) when this design was
written. It must be closed before `K-Preflight`.

## 14. Human checkpoints (expected)

Multi-part owner rows are split into single exact actions during execution (§7 rule 2).

| Process | Owner checkpoint rows | Single owner actions after splitting (including probes) | Shell steps |
|---|---|---|---|
| K1 | 19 | about 30 | 9 |
| K2 | 11 | about 18 | 8 |
| K3 (if included) | about 5 | about 8 | about 4 |
