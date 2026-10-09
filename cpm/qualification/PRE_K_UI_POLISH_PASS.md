# Pre-K CPM UI polish pass — design and implementation evidence

**Status: LIVE VERIFIED / PASS (2026-10-09; attempt U2).** The refined candidate
**`7e4686d7c6fe699743a1f611e50d7adce030037f147c5d6c7654c589f30bdb36`** is installed. It is **the
exact CPM build eligible to enter K**. **K: NOT STARTED** (needs separate authorization). L: not
started.

This is a presentation-only pass. `7e4686d7…` **supersedes** the first visual candidate `5c6e2789…`;
§1–§4 are kept unchanged as that candidate's record. Item 8's functional qualification of
`bfba4d3a…` is unchanged. The UI pass is byte-bounded against it: only declared presentation edits
differ.

## 0. Final visual refinement (current candidate `7e4686d7…`)

The owner viewed `5c6e2789…` in real SFM during live check U1 (§0.3). The semantic assignments were
correct, but the solid blue/gold/red fills were too loud for SFM's subdued dark interface. This
bounded refinement changes only two things in `cpm/app/SFM_Character_Preset_Manager.py`:
- the Help opening (in `ProdWindow.open_help`);
- the values of `PROD_ACTION_BUTTON_PALETTES`, with its comment.

The helper function, role assignments, layout, wording elsewhere, icon, dimensions and all behavior
are unchanged. Diff against `5c6e2789…`: 25 lines added, 23 removed.

The principle is that layout establishes hierarchy and color only reinforces meaning.

**Help.** The first heading is now **Getting started**, followed by:
- "Choose the character you want to edit. Body Presets and Expressions change that character. In
  Clothing Fit, choose clothing or accessories to fit to it."
- "CPM lists models from the shot under the playhead. To work in another shot, move the playhead
  there, click **Refresh Model List**, then choose your character."

### 0.1 Final semantic palette

Normal fill and text are neutral; the border carries the role.

| Role (buttons unchanged) | Normal bg / text | Border | Hover bg / border | Pressed | Disabled |
|---|---|---|---|---|---|
| primary — Apply Preset (Body, Expressions), Fit Selected to Model | `#494949` / `#d8d8d8` | `#4f7594` | `#515151` / `#5b88ad` | `#3e4247` (subtle blue cast) | `#393939` bg, `#858585` text, `#484848` border |
| favorite — Add/Remove Favorite (Body, Expressions) | `#494949` / `#d8d8d8` | `#806d43` | `#515151` / `#947d4b` | `#45423c` (subtle warm cast) | same |
| destructive — Delete Preset (Body, Expressions) | `#494949` / `#d8d8d8` | `#7a4d4d` | `#515151` / `#8d5959` | `#463e3e` (subtle red cast) | same |
| neutral — every other button (unchanged) | `#494949` / theme | `#5b5b5b` | `#535353` / `#666666` | `#414141` | same |

No colored text and no saturated fill in any state. Disabled semantic buttons are identical to
disabled neutral buttons.

### 0.2 Offline qualification of `7e4686d7…`

The commands and interpreters are the same as in §3. Outputs are in `pre_k_ui_polish_outputs_r2/`.
The first candidate's outputs in `pre_k_ui_polish_outputs/` are unchanged.

| Suite | Result |
|---|---|
| projection · adapter · canonical route · operation context · Clothing Fit · convergence gates | 196/196·196/196·3/3 · 205/205·205/205·3/3 · 85/85·85/85·3/3 · 108/108·108/108·3/3 · 95/95·95/95·3/3 · 152/152·152/152·3/3 |
| R14 · R15 | 2.7.5 18/18 · 3.10 15/15 · 2.7.5 345/345 · 3.10 188/188 |
| `test_cpm_app_ui_polish_pass.py` | **2.7.5 99/99 (real Qt + model) · 3.10 64/64 (model)** |

Test updates:
- new pins: candidate `7e4686d7…` and helper text `6df2c300…`; the superseded `5c6e2789…` is
  recorded in the test;
- exact **Getting started** heading first, and the approved opening wording;
- new palette checks: neutral fill and text for every role, border accents distinct with
  blue/warm/red casts, hover neutral `#515151` with a stronger border, pressed near-neutral (channel
  spread ≤ 12), no colored text or solid fill;
- **real-Qt pixels:** every semantic button renders the neutral fill `#494949` with its role border
  when enabled, and `#393939` with border `#484848` when disabled. Neutral buttons render the same
  as the reference.

The byte reconstruction from `bfba4d3a…` still proves that nothing else changed. The canonical-route
bounded sets are unchanged, because the same names are touched.

Sensitivity:
- the superseded `5c6e2789…` is rejected on 11 checks: pins, reconstruction, the Help heading and
  paragraphs, and every palette check;
- a vivid-hover mutation is rejected by the palette and hover checks.

### 0.3 Live checks (U1, U2)

Each attempt was deployed with SFM closed. Its evidence folder holds the deployment record,
backups, Scripts inventories, the CPM-log excerpt, the disposition and `SHA256SUMS.txt`. These local
attempt folders are not committed, because the logs contain workstation paths. Each deployment was
verified the same way:
- the Scripts difference was exactly the private-app line, so the launcher, adapter, projection,
  shared package, Normalizer and sidecar reader were unchanged;
- the live authority stayed exact G1 (Master `ac45e5c1…`, manifest `d810d648…`, one sidecar
  `bcd97641…`).

| Attempt | Build | Disposition | Observations |
|---|---|---|---|
| U1 | `5c6e2789…` (replacing `bfba4d3a…`; verified backup kept in U1) | **SUPERSEDED / NO QUALIFICATION VERDICT** | PID 31960, run `20261009-091854-pid31960`. Build loaded `ready`. Window shown with 2 models; Refresh once; 2 model selections. Close finalized. No errors or refusals. Owner: the role assignments were correct, but the solid fills were too loud, which led to §0. Not classified PASS or FAIL. |
| U2 | **`7e4686d7…`** (replacing `5c6e2789…`; the U1 `bfba4d3a…` backup was verified intact) | **PASS** | The owner reviewed it hands-on in real SFM ("Looks good") and asked for a light-touch check instead of the step-by-step checklist. Log for PID 40816, run `20261009-125852-pid40816`: build `7e4686d7…` loaded `ready`, window shown, Help opened twice, close finalized, with 0 authorizations, mutations or refusals. |

The U2 log also shows two expected guard messages from code that is byte-identical to `bfba4d3a…`:
- Refresh at launch: "No current shot." The playhead was not in a shot, so the list was empty.
- Model Info with no model: "Choose a model first."

**Not observed live in U2** (no model was selected):
- enabled border colors;
- the Update Preset confirmation;
- the Review tab.

These are covered by the offline real-Qt pixel and state checks of `7e4686d7…` (§0.2) and by the
owner's hands-on use of the same layout in U1.

**Disposition:** `7e4686d7…` stays installed. No qualification-only material was deployed in U1 or
U2. If `bfba4d3a…` is ever needed, its verified backup is in the U1 attempt folder and it can also be
restored from git (`2fe9a27`).

---

## First visual candidate `5c6e2789…` (superseded; record unchanged below)

| Item | Value |
|---|---|
| Starting checkpoint | `2fe9a275276963b0dc6ef901ec829422948d32b7` (HEAD = `origin/master`; tracked worktree clean) |
| Reference app (item 8 COMPLETE / PASS) | `bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5`, which stays the historical item-8 qualification |
| **New candidate** | **`5c6e27895920f27100f0692ef3a5565888463d5da453f3c9303ebb67c766b58e`** (791,837 bytes, UTF-8, LF) |
| Owner-supplied icon source | `SFMCPMIconWoman.png`, 1254×1254 RGBA, SHA-256 `c466919c137128d081e652d5c6b3e4404a8f463f14cc23b100cc35d380014c0d` |

Only `cpm/app/SFM_Character_Preset_Manager.py` changed in product code. The changes are confined to:
- the window icon constants;
- one new palette constant and one style helper;
- seven `ProdWindow` methods: `__init__`, `populate`, `clear_model_selection`, `review_changed`,
  `operation_default_error_copy`, `update_kind` and `open_help`.

Every other byte equals `bfba4d3a…`, and the new test proves this by byte-exact reconstruction.

## 1. Changes

| # | Change | Exact result |
|---|---|---|
| 1 | Window icon | `PROD_WINDOW_ICON_NAME = u"SFMCPMIconWoman.png"`. `PROD_WINDOW_ICON_PNG_BASE64` now holds the owner's icon at 64×64 (below). The path is unchanged: embedded PNG → `QPixmap.loadFromData` → `QIcon` through `tool_window_icon()` / `tool_apply_window_icon()`. There is no file lookup, so every window or dialog that already receives the icon gets the new one. |
| 2 | Selector wording | Label `Model:` → **`Character Model:`**. Placeholder `Choose a model` → **`Choose a character model`**. The same selection's empty/status copy now reads `Choose a character model.` (Body/Expression summaries), `%d model(s) found. Choose a character model.` and `Choose a character model to begin.`. **`Refresh Model List` is unchanged.** Logs, internal identities, RuntimeError texts, Model Info's `Model:` path row and APIs are unchanged. The model list is not filtered. |
| 3 | Help | The first section is now **Choose a character**: "Choose the character you want to edit. Body Presets and Expressions change that character. In Clothing Fit, choose clothing or accessories to fit to that character." It is followed by: "CPM lists models from the shot under the playhead. To work in another shot, move the playhead into that shot, click **Refresh Model List**, then choose the character you want to edit." The Review help now names **Clear Classification**. Nothing was added to the main window. |
| 4 | Semantic button colors | New `PROD_ACTION_BUTTON_PALETTES` and `tool_apply_semantic_action_button(button, role)` (table below). **Blue:** Body/Expression **Apply Preset**, Clothing Fit **Fit Selected to Model**. **Gold:** Body/Expression **Add/Remove Favorite**. **Red:** Body/Expression **Delete Preset**. Everything else stays neutral and unchanged. |
| 5 | Width | Minimum `500×650` → **`540×650`**. Default `520×800` → **`580×800`**. Font unchanged. |
| 6 | Update Preset confirmation | Informative text → **"The preset's current values will be overwritten."** The question-mark icon was removed (no `setIcon`). The title, question text, `Update Preset` / `Cancel` buttons (Cancel default) and all Update behavior are unchanged. |
| 7 | Review layout | One row of four → `QGridLayout` 2×2. Row 1: **Classify as Expression** \| **Classify as Body**. Row 2: **Exclude from Presets** \| **Clear Classification**. No semantic colors. |
| 8 | Reclassification wording | Button `Reclassify Flex` → **`Clear Classification`**. Status: **"Classified as Body. Click Clear Classification, then choose a new classification under Needs review."** (the same form for Expression), and **"Excluded from presets. Click Clear Classification, then choose a new classification under Needs review."**. The failure dialog title is now "Can't clear classification". The clear → rebuild → Needs review → classify behavior is unchanged. The internal operation label `Reclassify Flex` (authorization operation name and log `kind`) is unchanged. |

### Icon treatment

I made a deterministic 64×64 representation, the same size as the previous embedded icon:
- exact fractional box-filter area averaging in premultiplied alpha, so transparent pixels never bleed
  into the outline;
- re-encoded as 8-bit RGBA PNG with only `IHDR`/`IDAT`/`IEND`.

Result: **3,777 bytes**, SHA-256 `65cd4fb31059652537b7e4146c4a5c02e82d00104bb3d0d41d70034e80b21185`
(the previous gear icon was 6,218 bytes).

Transparency and the 1:1 aspect ratio are preserved: all four corners are alpha 0. The maximum alpha is
254, because the source's opaque area is itself alpha 254. Qt down-scales the single 64-px pixmap for
title-bar and taskbar sizes. Embedding the 1254-px source (632 KB) was not necessary.

### Action palette

All roles share the neutral main-action sizing (min height 30, padding 5×10, no auto-default).

| Role | Background | Border | Text | Hover bg / border | Pressed | Disabled (all roles) |
|---|---|---|---|---|---|---|
| primary (blue) | `#2f76b5` | `#4b8fc7` | `#ffffff` | `#377fbd` / `#5a9bd0` | `#28679d` | `#393939` bg, `#858585` text, `#484848` border |
| favorite (gold) | `#54472a` | `#8c7442` | `#f3e3b5` | `#5f5030` / `#a3874d` | `#483c24` | same |
| destructive (red) | `#583434` | `#875050` | `#f4dede` | `#643a3a` / `#9c5c5c` | `#4a2c2c` | same |
| neutral (unchanged) | `#494949` | `#5b5b5b` | theme | `#535353` / `#666666` | `#414141` | same |

Where the colors come from:
- **Blue** is the existing primary family (`tool_apply_primary_button`, list selection `#2f76b5`).
- **Gold** is a dark, desaturated relative of the Favorite star `#d6ad4b` and the warning status palette
  (`#4a4130` / `#746542` / `#f0e6c8`).
- **Red** follows the error status palette (`#4b3232` / `#754a4a` / `#f0dddd`).

A disabled colored button is visually identical to a disabled neutral button.

### Window dimensions (real PySide 1.2 / Qt 4.8, CPM tab style, CPM +3 pt font)

The four tabs measure 127 px each, so the bar needs **508 px**.

| Window | Tab-bar width | Result |
|---|---|---|
| Old default 520×800 | 498 px | scrolls |
| New default **580×800** | 508 px | **fits** |
| New minimum **540×650** | 508 px | **fits** |

Tab text is shorter than the tab style's 96-px minimum at both the base and the +3 pt font, so the
widths did not change with font size. The live SFM application font was not measured. The default
leaves 50 px of headroom for a larger host font, and the live sanity check should confirm it.

## 2. Non-goals held

- No change to `sfmApp.GetShotAtCurrentTime()` use, Selected Shots, the Normalizer, the model list,
  scope publication/rebuild, broker/provider/lease ownership, generation checks, Apply/Save/Update/Fit
  semantics, preset formats/libraries, Master/sidecar/shared authority, logging, or the launcher.
- Mechanically checked:
  - whole-file counts are equal for `QTimer`, `singleShot`, `startTimer`, `setInterval`,
    `QFileSystemWatcher`, `installEventFilter`, `GetShotAtCurrentTime`, `GetSelected`, `SelectedShots`,
    `prod_scope(`, `prod_cpm_authorize_operation(`, `modal_watch_timer`, `QSettings` and `setProperty`;
  - the constructed real `ProdWindow` has exactly the same instance attributes and live `QTimer`
    count as the `bfba4d3a…` window;
  - the module gains exactly the two new names.
- Not deployed. No real-SFM run. K and L not started.

## 3. Offline qualification

Commands, from `cpm/convergence/tests` with `PYTHONDONTWRITEBYTECODE=1`:
- each phased suite: `<py3.10> --phase=publish`, `<py2.7.5> --phase=suite`, `<py3.10> --phase=compare`;
- R14 and R15: `--phase=run` under each interpreter;
- the new test: `--reference=<pinned bfba4d3a app>` under each interpreter.

Interpreters: embedded Python 2.7.5 (production; real PySide 1.2 / Qt 4.8) and Python 3.10.6 (Qt model
only). Outputs are in `pre_k_ui_polish_outputs/`, with carriage returns removed and no workstation paths.

| Suite | `bfba4d3a…` (before) | New candidate `5c6e2789…` |
|---|---|---|
| `test_cpm_compat_v1_projection.py` | 196 · 196 · 3 | **196/196 · 196/196 · 3/3** |
| `test_cpm_authority_adapter.py` | 205 · 205 · 3 | **205/205 · 205/205 · 3/3** |
| `test_cpm_app_canonical_route.py` | 85 · 85 · 3 | **85/85 · 85/85 · 3/3** |
| `test_cpm_app_operation_context.py` | 108 · 108 · 3 | **108/108 · 108/108 · 3/3** |
| `test_cpm_app_clothing_fit.py` | 95 · 95 · 3 | **95/95 · 95/95 · 3/3** |
| `test_cpm_convergence_gates.py` | 152 · 152 · 3 | **152/152 · 152/152 · 3/3** |
| `test_cpm_app_r14_ctypes_isolation.py` | 18 · 15 | **2.7.5 18/18 · 3.10 15/15** |
| `test_cpm_app_r15_namespace_isolation.py` | 345 · 188 | **2.7.5 345/345 (real Qt + model) · 3.10 188/188 (model)** |
| `test_cpm_app_ui_polish_pass.py` (new) | — | **2.7.5 96/96 (real Qt + model) · 3.10 61/61 (model)** |

**Canonical-route edit (bounded, not weakened).** Following the item-6/7 precedent,
`UIPASS_CHANGED_TOP` (`PROD_WINDOW_ICON_NAME`, `PROD_WINDOW_ICON_PNG_BASE64`), `UIPASS_NEW_TOP`
(`PROD_ACTION_BUTTON_PALETTES`, `tool_apply_semantic_action_button`) and `UIPASS_CHANGED_METHODS`
(`operation_default_error_copy`, `review_changed`) were added to the cumulative expected sets. The
other UI-touched methods were already listed. R14 consumes the same set unedited. The equality
assertions are unchanged.

**New test `test_cpm_app_ui_polish_pass.py`:**
- **Pins:** reference `bfba4d3a…`, candidate, icon PNG, and the inserted helper text
  (`bcd6b49a…`).
- **Reconstruction:** applying the declared edit list to the reference, scoped per `ProdWindow`
  method, plus the pinned icon block and the pinned helper text, reproduces the candidate **byte for
  byte**. Name-level bounds and the unchanged style/icon helpers are also checked.
- **Icon:** 64×64 RGBA8, no ancillary chunks, transparency kept, under 8 KB, gear removed, no file
  dependency.
- **Wording:** label, placeholder, empty/status copy, unchanged Refresh Model List, Clear
  Classification, status copy, Update copy with no question icon and the confirmation kept, and the
  Help text (exact plain text) not added to the main window. The internal `Reclassify Flex` label is
  unchanged.
- **Roles:** an AST census of exactly the 7 semantic calls, neutral controls untouched, palette
  pinned, the shared neutral disabled block, and all four states defined.
- **Mechanism:** token counts equal.
- **Runtime:** the real `ProdWindow` is launched through the R15 harness, both candidate and
  reference, under real Qt and the model. Checked:
  - instance attributes and timers equal, and module names differ only by the two new ones;
  - in real Qt: dimensions; label; placeholder; Refresh text; window icon non-null, 64 px, with alpha;
  - the Review grid positions are 2×2, where the reference was not a grid;
  - **rendered pixels:** each colored button shows its palette background when enabled and `#393939`
    when disabled, and the neutral buttons render the same as in the reference;
  - the tabs fit at the default and minimum sizes, and the reference scrolled at 520.
- **Sensitivity**, checked on throwaway copies that were not committed, all rejected:
  - an unrelated one-character edit;
  - a wrong role (Apply as favorite);
  - an added `QTimer`;
  - an extra statement in the helper;
  - a vivid disabled state. Static checks caught it, and in real Qt all 7 disabled-pixel checks
    failed.

**Exact-build historical tests (not edited; not weakened).** These tests qualify one exact earlier
build and correctly refuse other bytes:
- `test_cpm_app_authority_cleanup.py` (item 6, `1e866871…`): 46/46 on `1e866871…`. On both
  `bfba4d3a…` and the new candidate it fails the same 4 item-6-only checks, because item 7 superseded
  them. This was already true before this pass.
- `test_cpm_app_logging_cleanup.py --reference=<item-6 app>` (item 7, `bfba4d3a…`): 144/144 on
  `bfba4d3a…`. On the new candidate it is 143/144 (2.7.5) and 116/117 (3.10). The single failure is
  its exact reconstruction gate tied to `bfba4d3a…`. Every item-7 invariant passes: closure, removed
  symbols, wrappers, logging-sink containment, route injection and the window gates. Item-7 bytes
  outside the UI blocks are carried by this pass's byte reconstruction.
- `real_sfm_qualification/cpm_item8_post_cleanup/`:
  - `test_cpm_item8_probe.py` is 164/167: `pins.candidate_app_is_bfba4d3a` and two module-identity
    checks fail.
  - `test_item8_generation_driver.py` stops at preflight with "the repository app is not the candidate
    bfba4d3a…".

  Both are item-8 exact-build tooling. They fail closed as designed and stay the historical record
  of `bfba4d3a…`. A live check of the new candidate needs its own authorized preparation.

## 4. Limitations and next

- Offline only. Real DME, SFM's own host font and stylesheet, Windows title-bar/taskbar icon
  rendering and operator perception are not qualified.
- The next separate authorization decides two things:
  - a focused live presentation sanity check of `5c6e2789…`, in a fresh SFM process, deployed through
    the R15 restart rule;
  - promotion of this candidate into K.
