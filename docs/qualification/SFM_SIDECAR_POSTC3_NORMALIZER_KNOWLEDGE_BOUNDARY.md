# SFM Sidecar — Normalizer Knowledge Boundary

Mandatory section per the evidence-collection brief. This document reports ONLY
what is directly visible in the current `Rebuild_Control_Groups_Normalizer.py`
source (339,944 bytes, SHA-256 `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e`,
at `usermod/scripts/sfm/mainmenu/ChadChan3D/`). **No Normalizer integration
architecture is proposed here** — this is inspection only, and it deliberately
stops short of designing anything.

## Confirmed: zero sidecar/qualification integration exists today

`grep -i "sidecar\|session_owner\|command_boundary\|bounded_provider\|MasterAuthorityOwner"`
across the entire file returns no matches. The Normalizer imports only `ctypes`,
`hashlib`, `os`, `re`, `struct`, `sys`, `time`, `traceback`, `sfmApp`,
`sfmClipEditor`, `vs`, and PySide's `QtCore`/`QtGui`.

## Known from current source

### Actual Master parsing/lookup functions present

- `stream_tokens(path)` (line 1204) / `BufferedChars` (1169) — a hand-written
  streaming tokenizer that reads the Master TXT directly, one token at a time.
- `parse_targeted_master(path, wanted_folds, validate_conflicts=True)` (line 1416)
  — builds a scoped in-memory index (`mappings`, `exact_literals`,
  `group_sibling_order`, `group_metadata`, etc.) by streaming tokens and only
  retaining data relevant to `wanted_folds` — i.e., the Normalizer's OWN existing,
  independent implementation of a "scoped Master view," conceptually similar to
  (but not sharing code with) this project's own `bounded_view.build_view_bounded`.
- `master_lookup(master, literal)` (line 1767) — looks up a single literal against
  an already-built `master` index. Called from 8 separate sites throughout the file
  (lines 2333, 3650, 3807, 4045, 5733, 5988, 6893, 8426).
- `validate_master_subset_conflicts(...)` (line 1726) — called once (line 9453).
- `sha256_stream(path)` (line 1149) — a streaming SHA-256 of a file.

### Where/when Master authority is built

Exactly once per command, inside a section literally logged as `"CONTEXTUALIZER
BUILD ONE SCOPED CANONICAL MASTER INDEX"` (around line 13171):

```text
self.master_index_scope_folds = self.collect_scope_master_wanted_folds()
...
self.contextualizer_assert_master_stable_for_index_use("BUILD")
...
self.master_index = parse_targeted_master(
    self.master_path, self.master_index_scope_folds, validate_conflicts=False,
)
self.master_index_builds = 1
```

Memory is sampled immediately before and after this build
(`contextualizer_process_memory_sample()`), and the elapsed build time is recorded
(`self.master_index_build_seconds`). This means **the Normalizer already measures
its own Master-index build cost/memory delta today**, independent of anything in
this qualification arc.

### How authority is passed to operations

The single `self.master_index` object built above is passed by reference into
`master_lookup(self.master_index, literal)` at every one of the 8 call sites listed
above — i.e., "build once, look up many times," the same shape the qualification
owner/view architecture also assumes, but implemented as a plain instance attribute
with no lease/view/lifecycle object of any kind.

### Existing live/observer/coordinator authority behavior

No `observer`/watcher/background-thread pattern was found (`grep` for
`Observer|watcher|threading` finds nothing resembling a persistent background
process). The Normalizer is a one-shot, command-invoked script triggered from the
Scripts menu (the same mechanism this project's own embedded probes use), not a
persistent service.

**A real, already-shipping freshness/staleness check exists**, independent of this
project's qualification work:

```text
self.master_hash = sha256_stream(self.master_path)     # computed once, near startup (line 9225)

def contextualizer_assert_master_stable_for_index_use(self, phase):   # line 9402
    current_hash = sha256_stream(self.master_path)
    if current_hash.lower() != self.master_hash.lower():
        raise ProbeError("Live Master changed before scoped-index %s use." % phase)
```

and a coverage check against the already-built scoped index:

```text
def contextualizer_validate_master_index_subset(self, wanted_folds, phase):   # line 9427
    self.contextualizer_assert_master_stable_for_index_use(phase)
    missing = set(wanted_folds) - self.master_index_scope_folds
    if missing:
        raise ProbeError("CONTEXTUALIZER scoped Master index does not cover runtime %s fold(s): %r." % (phase, missing))
```

A validation gate elsewhere (around line 12794) requires `self.master_index_builds
== 1` plus matching validation/opportunity counters before allowing some later
operation to proceed — visible in source, not further interpreted here.

### Transaction/mutation boundaries visible in source

`read_undo_ledger(dm)` (line 5307, called at lines 11044 and 11689) references
SFM's own native undo/data-model (`dm`) system. Model mutation appears to go through
SFM's native undo tracking, not through anything this qualification arc has
touched. No further interpretation is offered — a full mutation-boundary audit was
out of scope for this evidence collection.

## Not yet established

- Whether the current sidecar owner/service shape (`session_owner.py`,
  `command_boundary.py`) fits the real Normalizer's ALREADY-EXISTING
  build-once-per-command / hard-fail-on-change model cleanly, or would need to
  replace/coexist with it awkwardly. The two models solve related but
  **differently-shaped** problems (see the architecture/verification document §5)
  — this has not been reconciled.
- What a production adapter should look like. Not designed, and this document
  deliberately does not propose one.
- Whether the Normalizer's existing per-command rebuild pattern can consume a
  prepared/persistent sidecar authority without a redesign of
  `contextualizer_assert_master_stable_for_index_use` and
  `parse_targeted_master`'s call site — unknown; not investigated further, since
  that would be integration design, out of scope here.
- Whole-command product timing (the Normalizer's own `master_index_build_seconds`
  figures for a REAL run were not reproduced or captured in this evidence pass —
  only this project's own qualification-layer timings were measured).
- Real fallback UX (what an artist actually sees if sidecar admission/freshness
  fails) — no UI-layer code was inspected.
- Production memory impact of adding an owner/lease/view layer ON TOP OF the
  Normalizer's existing `master_index` object and memory-sampling calls — not
  measured.
- Real late-vocabulary frequency in actual artist usage — no usage telemetry
  exists or was inspected; every "late vocabulary" measurement in this arc has used
  synthetic qualification fixtures.

## Explicit caution

Qualification success (342+53 desktop / 26+24 embedded PASS across Round 3 and
Minimum C3) is **not** the same claim as Normalizer integration success. The
Normalizer already has its own working, shipping mechanisms for Master parsing,
scoped indexing, and change-detection; none of them import or depend on anything
qualified in this arc. Whether the qualified owner/command-boundary architecture
should replace, wrap, or coexist with those existing mechanisms is the explicit
open question this whole evidence package exists to let Astra examine — not
something this document (or any other in this package) answers.
