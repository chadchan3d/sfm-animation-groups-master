# F1-2 Production-Internal Static Audit: What Survives Through FINAL_REPORT_ENTRY Within a Single All-Shots Command

Performed per explicit instruction after F1-2's confirmed evidence: production's own
**All-Shots command 3** showed large growth **within its own single run**
(`CP0_COMMAND_START` → `FINAL_REPORT_ENTRY`: private `+238,366,720` bytes / `~227.32 MiB`,
free VAS `-233,242,624` bytes / `~222.44 MiB`, largest free block
`-111,017,984` bytes / `~105.88 MiB`), while Selected commands 1–2 showed only small
(~13.8 MiB / ~3.1 MiB) private growth with **zero** free-VAS loss. This is **not** the
same phenomenon F1-R1 attributed to the harness (F1-2 already eliminated the harness's
own whole-85-target capture) — this growth occurs **inside production's own command**,
between its own two log checkpoints. This audit traces production's own source
(`Rebuild_Control_Groups_Normalizer.py`, SHA-256
`cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`) for anything whose
lifetime scales with completed targets/shots and survives through `FINAL_REPORT_ENTRY`.
**This is a read-only trace. No production file was modified.**

## Method

Searched `RebuildControlGroupsProductionRun.__init__` (line 9013) for every `self.*`
attribute assignment, then traced which of those attributes are written to (appended,
keyed, or reassigned) during the per-shot/per-target processing loop, and whether any
are cleared/shrunk before the command's own `final_report()`/`FINAL_REPORT_ENTRY` point.

## Primary finding: `self.work` holds live native DME references for every target, for the whole command

- **`self.work = self.snapshot_work()`** (line 13665) is called **once**, near the start
  of the command (right after `CP1_BEFORE_INVENTORY_GATE`, before `CP2_AFTER_INVENTORY_GATE`).
- `snapshot_work()` (line 9828) builds, for **every** shot in scope, a `rows` list where
  each `row` dict (line 9950) explicitly stores:
  ```python
  row = {
      "aset": aset,                    # the LIVE DmeAnimationSet native element
      "game_model": game_model,        # the LIVE game-model native element
      "transform_names": transform_names,
      "header": header,
      ...
  }
  ```
  `aset` and `game_model` are **direct references to live native DME objects**, not
  pointers/IDs — confirmed by their use elsewhere in the file to perform the actual
  Rebuild operation on that target.
- Confirmed by grep: **no code path ever does `del self.work[...]` or otherwise shrinks
  `self.work`** during the run. Every access (lines 12397, 12464, 12591, 12657) is an
  **indexed read** (`record = self.work[...]`), never a removal. `self.work` therefore
  holds live references to **every eligible target's own `aset`/`game_model` DME
  elements simultaneously, for the entire command**, from `snapshot_work()` near the
  start through whatever point the command object itself is released.
- **This is architecturally necessary** (the command needs stable, indexed access to
  resume/reference any target throughout the run) — it is a case of **live-reference
  retention** (category 1), not allocator high-water retention or a leak. The open
  question this raises, and which F1-2's own evidence cannot answer by itself, is
  **whether the underlying native DME objects these references pin actually grow larger
  as a direct, legitimate consequence of being rebuilt** (e.g. a target's own control-group
  hierarchy gaining attributes/elements during normalization) — i.e., whether the ~227 MiB
  growth is the natural, one-time cost of the scene itself becoming more complex as each
  of the (per this run) 62 production targets is rebuilt, which would show up in a saved
  copy of the scene too (hypothesis A), as opposed to a per-run allocator/native artifact
  that a saved-and-reloaded copy would **not** reproduce on a second, idempotent pass
  (hypothesis B). **This is exactly what F1-R2 is designed to test empirically** — this
  audit cannot resolve it by static reading alone.

## Secondary candidates (bounded, unlikely to be the dominant cause)

| Attribute | Line(s) | Shape | Scales with | Assessment |
|---|---|---|---|---|
| `self.production_terminal_results` | init 9132, write 12082 | dict, one entry per target | completed targets (≤85) | Small per-entry payload (terminal status/category strings, not raw DME data) — bounded, not a plausible dominant cause at this scale |
| `self.production_mixed_direct_by_target` | init 9135, write 10785 | dict, one entry per target | completed targets | Same class as above — small |
| `self.production_supported_plan_pairs` / `production_composer_pairs` / `production_inventory_pairs` / `production_final_semantic_capture_pairs` | init 9128–9134, `.add()` at 11888/11954/12139 | sets of small tuples (shot/target identity pairs) | completed targets | Trivial size (short string tuples), not a plausible dominant cause |
| `self.session_expected` | init 9059, write 12159 | dict | session-scoped (bounded by shot/target count) | Not observed to hold raw native or bulk payload data at these write sites |
| `self.gate_mdl_cache` | init 9119, used via `_gate_consensus_header()`/`_gate_loose_candidates()` (9930–9936) | dict, one entry per **distinct model** (not per target) | distinct model count (22 in this fixture) — **not** per-target | Backed by `_gate_read_mdl_header()` (line 8233), which reads only a **header** (small, bounded), not full mesh/vertex data — not a plausible dominant cause |
| `self.gate_content_dirs` | init 9120 | list of content-directory search paths | fixed, set once | Trivial |
| `self.class_totals` | init 9138 | dict of scalar counters | fixed keys | Trivial |
| `self.master_index` | init 9083 | — | — | Explicitly documented in-source as "Pure Python only; no DME refs" (comment at line 9082) — ruled out by production's own stated design |

## What this audit does and does not establish

- **Established**: the one clear, architecturally-significant candidate for "a native
  wrapper whose Python object may pin DME state, scaling with completed targets, and
  surviving through `FINAL_REPORT_ENTRY`" is `self.work`'s own per-target `aset`/
  `game_model` live references — necessary by design, not a bug, but the thing that
  keeps every target's underlying native DME object reachable (and therefore whatever
  memory it occupies, committed) for the whole command.
- **Not established, and not resolvable by static reading alone**: whether the ~227 MiB
  growth reflects (a) those underlying DME objects legitimately growing larger as
  normalization restructures them (scene-resident, one-time, would reload with the
  saved scene), (b) native/allocator-side retention that is an artifact of the Rebuild
  process itself and would recur on every run regardless of prior normalization state,
  or (c) a mix of both. No code change is proposed here — per instruction, production
  is not modified based on this audit alone. Checkpoint F1-R2 (prepared separately) is
  designed to empirically separate these hypotheses via a scene-resident-vs-per-run
  comparison.
