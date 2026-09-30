# R15 Implementation Blueprint (authoritative)

> **Repository status.** This is the single authoritative R15 design, frozen from the Final R15 Implementation Blueprint (2026-09-30) at checkpoint `bd16940`. It supersedes `cpm/qualification/R15_NAMESPACE_ISOLATION_PROPOSAL.md` (fresh module per click), which is historical only. R15 remains OPEN. Session 2 remains NOT STARTED and blocked on R15.
>
> Repository edits relative to the attached original, none of which change the architecture:
> 1. local workstation paths and local-file links are written as repository-relative paths or `<SFM game>`-relative install paths;
> 2. **Clarification A** (§3, §5): the `sys.path` prohibition is scoped to the new launcher/private-module mechanism;
> 3. **Clarification B** (§12 step 7): settled resource-trend telemetry across the repeated launch/close/reopen qualification.
>
> Everything below is otherwise preserved as authored.

---

# Final R15 Implementation Blueprint

**Freeze R15 on the stable private-module architecture.** Claude’s audit strengthens it; it does not justify another architecture search.

Three proposed details need correction: the one-line Escape fix is incomplete, failed UI construction must not permit uncontrolled retries, and non-modal notifications need explicit ownership. Your corrected post-Normalizer acceptance criterion is binding.

This blueprint is based on repository checkpoint `bd169401fba1c04bf24a148cd8e65748ae757912`, Claude’s audit, and inspection of the current launch/close paths. It authorizes the bounded implementation below—not R15 closure or Session 2.

### 1. Final architecture and rationale

Use exactly:

**One thin SFM menu launcher → one stable private CPM application module per SFM process → explicit compatible-window reuse.**

The private module owns CPM’s functions, classes, configuration and permitted process-lifetime state. Windows own their scope, operation state, timers and transient consumer state.

This prevents another menu script from rebinding the globals used by CPM’s existing callbacks. It also prevents repeated CPM clicks from re-executing module initialization and resetting `OUTPUT_PATH`, provider counters or `PROD_RUN_ID`.

Retain these boundaries:

- Canonical broker acquisition and existing CPM projection remain unchanged.
- Initial scope remains pure.
- No idle provider or lease.
- No fresh module per click.
- No hot reload.
- No renaming hundreds of globals.
- No Normalizer isolation changes in R15.

Stable module retention is intentional. **It is not evidence of an exact memory upper bound relative to today’s implementation**; qualification must check that repeated launches do not accumulate additional application/window graphs.

### 2. Exact launcher/module lifecycle

Module lifecycle:

**ABSENT → LOADING → READY**

`READY` is permanent until process exit. Window creation and teardown do not change it.

| Encountered state | Required action |
|---|---|
| No reserved module | Read exact installed bytes; create/register `LOADING` module; compile and execute; verify successful initialization; mark `READY`; invoke startup. |
| Compatible `READY`, matching installed bytes | Invoke startup/window-reuse decision. |
| Compatible `READY`, different or unreadable installed bytes | Refuse this launch; require restart. Leave module and existing window intact. |
| `LOADING` already present | Refuse; leave untouched; require restart. |
| Foreign, malformed or incompatible reserved entry | Refuse; leave untouched; require restart. |
| Exception before `READY` | Remove only the entry created by this attempt, and only if it still refers to that exact module. Report failure. A later explicit click may retry. |
| Exception after `READY` | Never remove or replace the module. Apply the UI-failure rule below. |

Do not describe encountering `LOADING` as ordinary “busy, retry.” Also, Claude’s claim that it can *only* mean an aborted load is unnecessarily absolute: synchronous loading does not justify ignoring every possible re-entry mechanism. The refusal rule makes that distinction immaterial.

Separate UI startup state:

- **IDLE:** startup/reuse may be evaluated.
- **STARTING:** refuse another startup; do not construct a second dialog.
- **FAILED_RESTART_REQUIRED:** refuse subsequent startup attempts.

Expected refusals—foreign window, closing window, modal yield—do not set the failure latch.

An unexpected failure after window construction begins **does** set it. Keep the ready module, close a known, safely accessible owned partial window where possible, and require restart. Do not sweep arbitrary Qt widgets.

This replaces Claude’s unconditional “next click retries” recommendation. A failed constructor can leave a parented dialog behind; repeated retries would not make that residual bounded.

### 3. Module identity, registration and failure cleanup

Reserve:

| Field | Required value |
|---|---|
| `sys.modules` key | `chadchan3d_cpm_app` |
| `__name__` | `chadchan3d_cpm_app` |
| `__file__` | Normalized absolute deterministic implementation path |
| `__chadchan3d_cpm_loader__` | `cpm-private-loader-v1` |
| `__chadchan3d_cpm_build_sha256__` | SHA-256 of the exact bytes compiled |
| `__chadchan3d_cpm_state__` | `loading`, then `ready` |

Rules:

- Create a real `types.ModuleType`.
- Register it before execution.
- Hash and compile the **same byte buffer**.
- Compile with `compile(source_bytes, impl_path, "exec", 0, True)`.
- Execute with the module dictionary as both globals and locals.
- Do not add `__path__`, customize `__package__`/`__loader__`, or supply a custom `__builtins__`.
- Do not introduce relative imports or `sys.path` changes.
  - **Clarification A (repository synchronization, 2026-09-30):** this prohibition applies to the new R15 launcher and its private-module loading mechanism only. The existing qualified CPM adapter/bootstrap behavior, including its established MAINMENU `sys.path` insertion (handoff §16), is unchanged and is **not** authorized for modification.
- Verify the registered object and required identity fields before reuse.
- Qualify that CPM functions’ `func_globals` are this dictionary under Python 2.7.5.
- Keep all launcher imports and working variables local. Delete the uniquely named launcher function in `finally`.
- No launcher-defined Python callback may escape into Qt.

A pre-ready cleanup must cover `BaseException`, including interruption, without deleting a foreign replacement entry. Store formatted diagnostics, not retained exception/traceback objects.

Correct Claude’s “no side effects” wording to:

> Module loading must create no escaped CPM window, timer, callback, authority acquisition or mutable scene state.

Imports execute code; initialization is not literally side-effect-free. The narrower invariant is what makes pre-ready retry defensible.

### 4. Window ownership, reuse and notification lifetime

Set private CPM `OUTPUT_PATH = PROD_OUTPUT_PATH` before startup logging or window decisions. Do not reset the existing log, counters or run ID on reuse.

Use the existing application window slot. Ownership requires the stable private module’s `ProdWindow` class and a valid Qt object.

| Slot/window condition | Action |
|---|---|
| Empty | Construct one window. |
| Owned, alive, eligible for presentation | Reuse it; preserve active scope and operation state. |
| Owned, closing | Do not show or replace it. Report “still closing”; require another deliberate click later. |
| Owned, yielding to a foreign modal | Do not show it. Existing watcher retains restoration responsibility. |
| Foreign modal currently active | Do not create/re-show CPM across it, including before the watcher has observed it. |
| Owned, definitively deleted Qt object | Clear only if the slot still contains that object; then create. |
| Foreign live window, visible or hidden | Refuse; do not close, adopt or replace it. |
| Foreign, definitively deleted Qt object | Clear by identity and create. |
| Malformed occupant or uncertain liveness | Refuse; do not interpret uncertainty as an empty slot. |

A hidden window is not a dead window. Arbitrary exceptions are not proof of Qt deletion.

**Notification mechanism**

Use one reusable, ordinary non-modal `QMessageBox`, strongly retained on `QApplication` under:

`_chadchan3d_cpm_launch_notice_v1`

Its contract:

- At most one notice widget per process.
- Parentless; explicitly non-modal.
- `WA_DeleteOnClose` disabled: acknowledgement hides it for reuse.
- `WA_QuitOnClose` disabled.
- No custom Python signal callbacks, timers, provider references or CPM-window references.
- No `exec_()` or `processEvents()`.
- No forced activation over a foreign modal.
- If a foreign modal is active, log the refusal without queuing an automatic later popup.
- If the notification slot is foreign or malformed, leave it untouched and use console diagnostics.

This intentionally retains one small notification widget. Count it separately from CPM windows during qualification. It solves the lifetime problem without retaining a launcher closure or creating a second application module.

### 5. Deployment layout

Retain the canonical mutable source:

`cpm/app/SFM_Character_Preset_Manager.py`

Add the launcher source at:

`cpm/app/launcher/SFM_Character_Preset_Manager.py`

Deploy:

| Purpose | Installed path |
|---|---|
| Menu launcher | `<SFM game>\usermod\scripts\sfm\mainmenu\ChadChan3D\SFM_Character_Preset_Manager.py` |
| Private implementation | `<SFM game>\usermod\scripts\ChadChan3D_CPM\SFM_Character_Preset_Manager.py` |

Derive the runtime location from the established `sys.executable`-based game-root resolution, not the working directory or the menu host’s `__file__`.

The implementation directory:

- Is outside the entire `scripts\sfm` discovery tree.
- Has no `__init__.py`.
- Is not added to `sys.path` by the launcher (Clarification A in §3: the existing adapter/bootstrap MAINMENU `sys.path` insertion is unchanged and not authorized for modification).
- Contains deployed bytes identical to the canonical source.

Replace the existing menu entry’s implementation bytes with the launcher. Do not leave another unguarded production implementation in the menu tree.

Existing adapter/shared-package deployment is unchanged. Broader packaging cleanup remains separate.

### 6. Direct-execution guard contract

The implementation must begin, immediately after its docstring and before imports or application definitions, with an **allow-guard** requiring:

- Reserved module name.
- Exact loader marker.
- Loading state.

Otherwise it raises a clear “launch through the CPM menu entry” error.

Remove the unconditional bottom-of-file `StartProdTool()` call.

Loading defines the application; only the launcher requests startup after `READY`.

Update the whole-file test harness to establish the approved loading context explicitly. Do not weaken the guard for tests.

This protects against accidental direct execution. It is not a security boundary against another script deliberately modifying process internals.

### 7. Installed-build-change/restart policy

On every menu click, compare the current installed implementation’s exact-byte SHA with the loaded module’s SHA.

- Matching bytes: normal reuse/startup.
- Different bytes: refuse launch/reopen and request restart.
- Unreadable or missing implementation: refuse; report the installation problem.
- Never reload, replace or delete a ready module.

An already-open window continues using its loaded implementation. Do not disable it merely because installation bytes changed. Its existing authority and scene guards still apply.

Changes to the loader contract require a loader-marker revision; an older loaded module must then be refused, not migrated.

Record both launcher and implementation hashes in qualification. Application build identity is distinct from Master/sidecar generation identity.

### 8. Escape teardown finding

**Accept the finding; correct the proposed repair.**

The current key handler (`ProdWindow.keyPressEvent`, `cpm/app/SFM_Character_Preset_Manager.py` line 29389 at `bd16940`) delegates Escape, while `ProdWindow.closeEvent` (line 35439 at `bd16940`) holds CPM teardown.

Qt’s base `closeEvent()` calls virtual `reject()`. Therefore, adding `reject() → close()` while retaining the existing base-close call can re-enter closing without hiding the window, causing the outer event to be ignored. [Qt dialog source](https://github.com/qt/qt/blob/4.8/src/gui/dialogs/qdialog.cpp), [widget close implementation](https://github.com/qt/qt/blob/4.8/src/gui/kernel/qwidget.cpp).

Freeze this repair:

1. `ProdWindow.reject()` requests `self.close()`.
2. Existing operation-unwind/deferred-close branches remain authoritative.
3. Only after safe teardown: clear the application slot by identity and accept the close event.
4. Finalize through explicit **base `QtGui.QDialog.reject(self)`**, without calling `QtGui.QDialog.closeEvent(self, event)` afterward.
5. Do not access window state after that terminal call.

This preserves rejection finalization while avoiding dispatch back through the override. Real SFM must confirm the PySide path.

Record this separately as **pre-existing Escape/reject teardown defect, discovered during R15**. It is not the cause of shared-namespace corruption.

### 9. Exact files allowed to change

The bounded implementation allowlist is:

**Production and tests**

- `cpm/app/SFM_Character_Preset_Manager.py` (canonical CPM app) — guard, startup/reuse/failure handling, minimal lifecycle state, rejection/close finalization only.
- `cpm/app/launcher/SFM_Character_Preset_Manager.py` — new.
- `cpm/convergence/tests/test_cpm_app_r15_namespace_isolation.py` — new.
- `cpm/convergence/tests/test_cpm_app_canonical_route.py` (canonical-route tests) — loading harness and exact expected-diff inventory.
- `.gitattributes` — narrowly scoped launcher line-ending rule, if needed.

**Qualification and records**

- `real_sfm_qualification/cpm_session1/CPM_Session1_Probe.py` (Session 1 probe) — observational R15 additions only.
- `real_sfm_qualification/cpm_session1/R15_SESSION1_ADDENDUM_RUNBOOK.md` — new.
- `real_sfm_qualification/cpm_session1/R15_SESSION1_ADDENDUM_EVIDENCE.md` — new; actual results only.
- `cpm/qualification/R15_IMPLEMENTATION_BLUEPRINT.md` — new authoritative design (this file).
- `cpm/qualification/R15_NAMESPACE_ISOLATION_PROPOSAL.md` (R15 proposal) — mark superseded.
- `cpm/qualification/CPM_CONVERGENCE_LEDGER.md` (Convergence Ledger).
- `docs/qualification/CPM_CONVERGENCE_INTEGRATION_HANDOFF.md` (integration handoff) — reconcile entrypoint/deployment/status.

Raw addendum outputs may be added under one designated R15 evidence directory. Existing historical evidence must remain intact.

### 10. Files/components forbidden to change

Do not change:

- Frozen G18AN baseline.
- Production Normalizer or its guards.
- Shared authority package, canonical bootstrap/broker semantics or sidecar reader.
- CPM authority adapter or `cpm_compat_v1` projection.
- Master TXT, compiled authority artifacts or generation rules.
- Preset formats, storage policy, classification, scope semantics or mutation behavior.
- R14 private-ctypes isolation.
- Existing qualification assertions merely to accommodate a regression.
- Session 2 scripts, procedures or status.

No second provider/discovery path, cached-payload expansion, fallback producer or UI redesign.

### 11. Offline qualification gates: Python 2.7.5 and 3.10

Run the actual launcher through the new suite under both interpreters. Python 2.7.5 is the production gate; 3.10 is compatibility evidence.

| Gate | Required proof |
|---|---|
| Namespace isolation | Poison shared-host collision names; private callbacks retain their correct globals. Launcher leaves no retained host callback or temporary binding. |
| Stable lifetime | Repeated clicks preserve module/class/function identities and run ID. Closing/reopening does not replace the module. Retained callbacks still resolve intact globals. |
| Compilation | Exact bytes; coding-cookie compatibility; inherited future flags do not alter private code. |
| Loading failures | Late-import failure and interruption remove only the owned pre-ready entry; subsequent explicit retry works. No escaped CPM runtime objects. |
| Identity refusals | Foreign/loading/incompatible/wrong-origin entries remain untouched. Changed/unreadable installed bytes never trigger reload. |
| Window decisions | Exercise every table row, including hidden foreign window, uncertain liveness, closing and modal-yield states. |
| Startup failures | Inject constructor/show failure; ready module survives; failure latch prevents additional construction attempts. |
| Teardown | Model the base Qt rejection behavior, not a no-op fake. Verify deferred-close branches and absence of recursive finalization. |
| Notification ownership | One retained notice; acknowledgement/reuse; no nested event loop or retained Python callback; foreign notification-slot handling. |
| State preservation | No provider-counter/run-ID reset; correct CPM log on creation, reuse and refusal. No adapter/provider/lease retained by launcher state. |
| Regression | Existing convergence, operation-context, Clothing Fit and R14 checks pass; expected source differences match the allowlist. |

Mocks cannot qualify actual Qt deletion, menu discovery or live coexistence. Those belong to the addendum.

### 12. Real-SFM Session 1 addendum

Use a fresh SFM process and the established qualified fixture. Keep Master and sidecar generation unchanged.

**Sequence**

1. **Verify deployment and identities.** Confirm Python 2.7.5, launcher/app hashes, unchanged forbidden components, and absence of the private implementation from both Scripts and animation-set menus.

2. **Confirm host context observationally.** Run the probe twice. Record the menu execution dictionary and function-global identities without leaving application callbacks in that dictionary.

3. **Open CPM and establish an active scope.** Record private module identity/origin/build/state, window identity, function-global ownership, broker identity and idle provider/lease counts. Perform the established successful Apply/Save baseline using disposable qualification data.

4. **Click the CPM launcher again.** Require the same module and same window, unchanged active scope/run ID, no additional watcher, no additional CPM window and no authority acquisition caused merely by reuse.

5. **Run one production Normalizer command on the relevant shot.** Respect its existing admission guard. Do not add repeated normalization stress runs.

6. **Return to the same CPM window and existing active scope, without reselection. Run normal Apply and Save.**
   - **PASS requires successful continuation with the existing semantic checks intact.**
   - Stale-authority or stale-scope refusal is **not PASS**.
   - Any independently legitimate scene-state refusal stops the sequence for explicit adjudication; it is neither waived nor automatically classified as namespace failure.
   - Check expected application/save results, log separation, intact globals, unchanged authority generation and no historical provider invocation.

7. **Perform three close/reopen cycles.** Include title-bar close and Escape. Each close must finish teardown after event-loop settling; each reopen uses the same module with a fresh window lifecycle. Require no orphan CPM window, watcher or queued Fit activity and zero idle providers/leases. Do not rely solely on differing numeric `id()` values, which can be reused.
   - **Clarification B — resource-trend telemetry (repository synchronization, 2026-09-30):** record settled process resource telemetry at: the initial CPM open (step 3); the second launcher click (step 4); each of the three close/reopen cycles; and the final settled state. Record working set and private commit, plus handle, GDI and User object counts where available. The purpose is to detect accumulation across repeated launches (§1). There is no hard MB threshold, and this is not a broad performance campaign.

8. **Verify notice lifetime in SFM.** Exercise a controlled launcher refusal through the observational qualification harness, show/acknowledge/repeat, and confirm one reusable non-modal notice, no blocked event loop and no additional CPM window. The harness must not alter broker, authority or scene state.

9. **Separate fresh-process legacy-slot check.** Archive logs first. Open frozen G18AN, then invoke the new launcher: require refusal and preservation of the foreign window/slot. Close it normally; launch again and require the isolated CPM to open. Do not run another Normalizer command in this check.

**Failure criteria**

Any namespace contamination, module replacement, duplicate live CPM window, reset lifecycle state, incorrect log destination, failed intended Apply/Save continuation, broken close/unwind, leaked authority ownership or modal refusal loop keeps R15 open.

No build-generation transition is part of this addendum. Session 2 remains separate.

### 13. Ledger and Blueprint consequences

Record explicitly:

- **R15 design frozen: stable private module.**
- Fresh-module-per-click proposal superseded.
- Session 1’s existing PASS remains historical evidence; active-scope coexistence requires this addendum.
- R14 remains CLOSED.
- R15 remains OPEN until implementation and qualification pass.
- Session 2 remains NOT STARTED and blocked.

Preserve three distinct findings:

1. **R15:** shared Scripts-menu namespace corrupts long-lived CPM global resolution.
2. **Repeated-click initialization defect:** inferred reset/logging behavior in the old execution model.
3. **Escape teardown defect:** pre-existing close-path issue discovered during R15.

Correct these overstatements:

- Module loading is not literally side-effect-free.
- Stable-module memory use has no measured “at most status quo” guarantee.
- A leftover `LOADING` entry need not have one uniquely proven cause.
- Unexpected UI-construction retries are not inherently bounded.
- Stale-scope refusal is not successful post-Normalizer continuation.

### 14. One bounded implementation assignment for Claude

> Implement this R15 blueprint at checkpoint `bd169401fba1c04bf24a148cd8e65748ae757912`, using only the allowlisted files and deployment destinations.
>
> Add the thin launcher and stable private application module lifecycle; enforce exact-byte compilation, module identity, no reload, compatible-window reuse and explicit notification ownership. Separate pre-ready load cleanup from post-ready UI failure. Repair Escape/reject teardown through the non-recursive finalization path specified above, recording its separate provenance.
>
> Preserve all shared-authority, projection, Normalizer, R14 and frozen-baseline behavior. Update the narrowly affected harnesses and run the offline gates under Python 2.7.5 and 3.10. Report exact hashes, changes and results before deployment.
>
> Then conduct only the specified Session 1 addendum, preserving raw evidence. Do not classify refusal as successful post-Normalizer Apply/Save continuation. Stop on a failed prerequisite or scope conflict.
>
> Close R15 only after the offline gates and real-SFM addendum pass. Do not begin or prepare Session 2.

**Confidence:** High in the architecture and bounded correction scope. Actual PySide teardown, notification behavior and active-scope continuation remain qualification outcomes—not claims established by this review.
