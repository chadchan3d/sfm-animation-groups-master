# R15 — shared Scripts-menu namespace: investigation and fix proposal

> **SUPERSEDED — historical record only (2026-09-30).** This proposal is superseded by
> `cpm/qualification/R15_IMPLEMENTATION_BLUEPRINT.md`, the single authoritative R15 design (one
> thin SFM menu launcher → one stable private CPM application module per SFM process → explicit
> compatible-window reuse). The fresh-module-per-click launcher described below (§3, §5) is **no
> longer authoritative** and must not be implemented. The investigation evidence (§1–§2) remains
> valid history. The contents below are preserved unchanged.

Written against `master` `be5122e`. **Proposal only; nothing is implemented.**

Verified identities:
- app `664a660c…` (repo equals deployed);
- production Normalizer `1f4ec5a2…` (repo audit snapshot equals deployed);
- frozen G18AN baseline `3326024d…`.

## 1. Mechanism

**Evidence (strong, but not yet directly observed):**

1. **Binary.** SFM's Scripts menu is native: `ifm.dll`'s `ScriptController` contains
   `scripts\sfm\mainmenu`, `"%d> Running script '%s' ..."`, `"Couldn't open python script file
   '%s'"` and `__main__`. It imports `PyImport_AddModule`, `PyModule_GetDict` and
   `PyRun_FileExFlags`. No Python-side loader exists in SFM's Python tree.

   That is the standard embedding pattern: run each menu file with
   `PyRun_FileExFlags(..., main_dict, main_dict)`, where `main_dict` is `__main__`'s dictionary.
   Every menu script therefore executes with the **same process-lifetime globals dict**, and every
   function it defines keeps that dict as its `__globals__`.
2. **Behavior (real SFM, 2026-09-29).**
   - After the Normalizer ran, the still-open CPM window's `log_line` wrote into the Normalizer's
     log.
   - The Normalizer's module-level `OUTPUT_PATH = …` had rebound the name that CPM's function
     resolves at call time.
   - Nothing else can rebind another script's global.

Consequence: whichever script ran last owns every shared name. Long-lived objects look globals up
at call time through that dict:
- Qt callbacks;
- `QTimer` lambdas;
- window methods.

So they execute another tool's definitions.

The first requalification step (§5) confirms this directly: the probe records `__name__` and
`globals() is sys.modules['__main__'].__dict__`. The fix below does not depend on the exact
mechanism.

## 2. Collision / risk inventory

Method: `symtable` over both sources. Bindings are top-level names plus function-level `global`
assignments; lookups are every function's implicit and declared global reads.

**Converged CPM vs production Normalizer** (627 and 208 global bindings; 18 shared):

| Class | Names | Risk |
|---|---|---|
| Identical module objects | `os`, `sys`, `re`, `time`, `traceback`, `hashlib`, `ctypes`, `QtCore`, `QtGui`, `sfmApp`, `vs` | Harmless (the same module either way) |
| Py3-only fallbacks (inside `except NameError`, not executed under 2.7) | `unicode`, `long` (Normalizer also has `xrange`) | Harmless under 2.7.5 |
| **Mutable configuration** | `OUTPUT_PATH` (CPM also assigns it via `global` in `StartProdTool`) | **Observed:** log contamination in both directions |
| **Different implementations** | `arr`, `handle`, `name`, `typ` | **Dangerous.** The Normalizer's `handle(None)` raises (CPM's returns `None`); its `typ(None)` returns `"NoneType"` (CPM's returns `None`); its `arr` raises `ProbeError` (CPM's returns `[]`); `name` differs. CPM has 20/11/30/29 functions reading these; the Normalizer has 8/16/26/6 |

- **Builtin shadowing across the two scripts:** none.
- **Names either script reads without binding them and the other binds:** none.
- **CPM runtime-assigned globals** (`_SEMANTIC_PROVIDER*` counters, window-icon cache,
  `OUTPUT_PATH`): mutable state, exposed to any script that binds the same names.

**The wider surface (the larger hazard):** every Scripts-menu script shares the same dict.

| Script | Names shared with the converged app |
|---|---|
| CPM RC7 release (`SFM_Character_Slider_Preset_Tool_0.2.0_RC7.py`) | 470 |
| G18AM-era build | 585 |
| Frozen G18AN baseline | 600 of 627 |
| Session 1 probe | 5, all module imports (harmless) |

If any older CPM build runs in the same process, the converged window's callbacks execute
pre-convergence code. That includes `prod_scope`, which leads to `get_semantic_provider` and the
historical provider. This would silently defeat Step 2b's historical-authority-unreachable
guarantee (R6/R13). A manual rename list cannot close this surface.

**Not implicated:**
- the shared authority package, `cpm_authority_adapter` and `cpm_compat_v1_projection`: all are
  real imported modules with their own namespaces;
- the canonical broker (one `sys.modules` runtime).

## 3. Recommended fix: a private-namespace launcher for CPM

Make CPM's Scripts-menu entry a tiny launcher. On each invocation it compiles the CPM
implementation into a **fresh private module** (`imp.new_module`, then `exec` into
`module.__dict__`), rather than into SFM's shared `__main__` dict.

```text
SFM_Character_Preset_Manager.py   (menu entry = launcher; runs in the shared dict)
  def _chadchan3d_cpm_launch():
      locate the MAINMENU dir via the same sys.executable formula (handoff §16)
      impl = <that dir>/cpm_character_preset_manager_impl.py   # origin-checked
      module = imp.new_module("chadchan3d_cpm_app"); module.__file__ = impl
      exec(compile(<impl bytes>, impl, "exec"), module.__dict__)  # the impl's own StartProdTool() runs
      sys.modules["chadchan3d_cpm_app"] = module                   # diagnostics
  _chadchan3d_cpm_launch(); del _chadchan3d_cpm_launch             # leaves nothing behind
```

**Why this fix:**
- **Isolation by construction.** All ~627 CPM names and every CPM callback's `__globals__` live
  in CPM's own module. Nothing CPM defines can be rebound by the Normalizer, old CPM builds, the
  probe or any other menu script, and CPM rebinds nothing of theirs. It needs no blacklist and
  no renames.
- **Semantics are preserved exactly:**
  - still **fresh per invocation** (a new module each click, as today's re-execution);
  - `StartProdTool` still reuses an existing window;
  - the window slot, log file and version strings are unchanged;
  - the menu entry name is unchanged;
  - the app code runs unchanged apart from the guard below.
- **Minimal product change:** a new launcher file, plus a single guard statement at the top of
  the canonical app:

  ```python
  if __name__ == "__main__": raise RuntimeError("... private implementation module; start it from the SFM Character Preset Manager launcher")
  ```

  If someone runs the implementation file directly from the menu, the guard refuses before
  anything is defined in the shared dict.
- **CPM-only.** The Normalizer is qualified (F/G/I/J) and pinned (`1f4ec5a2…`) and is left
  untouched. CPM's isolation removes the whole CPM↔Normalizer surface from both sides.
- **Residual (recorded, not in scope):** the Normalizer still shares `__main__` with other
  non-CPM scripts, including old CPM builds. The Normalizer is re-executed each invocation, so its
  exposure is limited to its own deferred callbacks within one command. Normalizer isolation would
  be a separately qualified change (K/L).

## 4. Files an implementation would change

| File | Change |
|---|---|
| `cpm/app/SFM_Character_Preset_Manager.py` | Canonical implementation (R13 path unchanged): add the one-line direct-execution guard at the top |
| `cpm/app/launcher/SFM_Character_Preset_Manager.py` (new) | The launcher. Deployed under the unchanged menu name; the implementation is deployed as `cpm_character_preset_manager_impl.py` beside the adapter modules (interim layout; L owns the final layout) |
| `.gitattributes` | LF pin for the launcher |
| `cpm/convergence/tests/test_cpm_app_r15_namespace_isolation.py` (new) | Offline R15 suite |
| `real_sfm_qualification/cpm_session1/CPM_Session1_Probe.py` → v3 | Add mechanism fields: `__name__`, `globals() is sys.modules['__main__'].__dict__`, whether CPM names exist in `__main__`, and the window-function globals' `__name__`. Test-only |
| A Session 1 addendum runbook | New file |
| `cpm/qualification/CPM_CONVERGENCE_LEDGER.md` | Update |

**Not changed:** the Normalizer, the shared package, the frozen baseline, the adapter/projection,
the Master/sidecar.

## 5. Qualification after the fix

### Offline (embedded 2.7.5 and Python 3.10)

The harness emulates SFM: one shared `__main__`-style dict, with fake `sfmApp`/`vs`/`PySide`
modules.

1. **Launcher isolation.** After a launch, the shared dict gains no CPM names (the launcher
   removes itself). The private module holds all app bindings. `StartProdTool` ran inside the
   private module.
2. **Normalizer → CPM.** Exec the Normalizer's verbatim `OUTPUT_PATH`, `arr`, `handle`, `name`
   and `typ` into the shared dict after the CPM launch. Every CPM function's `__globals__` is
   still CPM's, and `log_line` still targets CPM's `OUTPUT_PATH`.
3. **CPM → Normalizer.** A launch after the Normalizer's definitions leaves them intact in the
   shared dict.
4. **Old build → CPM.** Exec the frozen baseline's top-level definitions (e.g. `prod_scope`,
   `get_semantic_provider`) into the shared dict. The converged module's `prod_scope` is still
   the canonical-route one.
5. **Pre-fix contrast.** Exec the app directly into the shared dict, then the Normalizer names.
   CPM's `typ`/`handle` are rebound. This reproduces R15.
6. **Direct execution of the implementation** into the shared dict raises the guard before
   binding anything.
7. **Freshness and reuse.** Two launches give two distinct modules; the second
   `StartProdTool` reuses the existing window (fake `QApplication`).
8. **Origin.** The launcher loads only from the `sys.executable`-derived directory (child
   interpreter, as in Step 2b).
9. **Regression.** Step 1–4, gates and R14 suites. The Step 2b bounded-derivation check is
   updated only for the guard.

### Real SFM (Session 1 addendum; required before Session 2)

1. Fresh SFM. **Probe v3** reports `__name__ == "__main__"` and shared-dict identity for menu
   scripts. This confirms §1 directly.
2. Open CPM (launcher), select a character, and wait for the canonical scope to be built. The
   probe must show:
   - the CPM window's function globals are the private module (`__name__ != "__main__"`);
   - no CPM names in `__main__`;
   - leases 0, providers 0.
3. **With that active scope and window still open,** run `Rebuild_Control_Groups_Normalizer.py`.
   It must complete normally, with `mem_ok=True` at its checkpoints.
4. **No cross-script logging:**
   - the Normalizer's log contains no CPM `[HH:MM:SS]` lines;
   - CPM's own log keeps receiving CPM lines after the Normalizer ran.
5. **Probe:**
   - the same canonical broker;
   - `cpm_compat_v1` and `normalizer_compat` both served;
   - leases 0 and providers 0 when idle.
6. **Return to the still-open CPM.** Re-select the character, then Apply and Save. Both work and
   log to CPM's log.

This one addendum also closes the preserved nuance: active-scope simultaneous coexistence.

## 6. Blueprint / Ledger consequences

- **The CPM entry point becomes launcher + private implementation.** The canonical evolving
  source stays `cpm/app/SFM_Character_Preset_Manager.py` (R13 unchanged). The deployed
  implementation filename is an interim qualification-layout choice (L).
- **Handoff §16:** the launcher intentionally duplicates the tiny pre-import MAINMENU locator; an
  offline equivalence check already exists for the formula.
- **Session 2 is gated** on the R15 fix and the Session 1 addendum (active-scope coexistence).
- **Recorded residuals for K/L:**
  - Normalizer namespace isolation;
  - the shared window slot, log name and version strings, which old CPM builds also claim.
