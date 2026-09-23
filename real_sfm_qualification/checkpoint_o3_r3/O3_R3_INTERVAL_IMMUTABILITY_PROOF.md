# O3-R3 — Interval Immutability Proof

**Status: DESIGN/PROOF ONLY.** No production, integration, or lifecycle code has been modified. This
document investigates whether the native-POST → composer-before interval can be proven, source- or
runtime-contract-wise, incapable of scene mutation or Qt reentrancy — the second of the two routes that
could justify Option C per the complexity gate in `O3_R3_ENUMERATION_VALIDITY_DECISION.md` section 8.

## The interval, precisely bounded

Start: `post_rig = discover_rig_context(shot, aset)` (`run_target_transaction`, line 11482), immediately
following `self.rebuild(...)`'s own return (line 11464-11474, `NATIVE_REBUILD_RETURNED = PASS`).

End: `before_rig = discover_rig_context(shot, aset)` (`production_generic_composer`, line 7175), the first
statement of the function called from `run_target_transaction` line 11897
(`composer_result = production_generic_composer(...)`).

This is a **larger** interval than the one O2-R1's own static proofs (`O2_R1_OUTER_POST_TO_COMPOSER_
BEFORE_PROOF.md`) characterized as "no explicit DME write / native mutation / Qt-yield anywhere in the
interval." That proof is correct as far as it goes — re-confirmed here — but Astra's objection is precise:
absence of an *explicit* write/yield does not establish absence of an *implicit* one reachable through a
native getter or `sys.stdout.write()`, both of which this interval calls repeatedly.

## Full inventory of calls in this interval (direct source reading, lines 11492-11897 and 7162-7185)

- **15 `self.log(...)` calls** (exact line numbers: 11619, 11682, 11709, 11753, 11775, 11786, 11800, 11806,
  11814, 11820, 11828, 11836, 11842, 11864, 11893 — not all execute on every branch, since some are inside
  conditional blocks, but the supported-active-rig composer-entry path this candidate applies to executes
  the large majority of them). Each calls `self.log()` (class method, line 9151-9182), whose own body calls
  `sys.stdout.write(data + "\n")` (line 9168-9170, wrapped in its own bare `try/except`) and, if
  `self.fp is not None`, `self.fp.write(...)` + `self.fp.flush()` (line 9176-9179, a plain Python file
  object opened by this script itself — not a scene/DME object, not a reentrancy concern).
- **Four native getter calls**, none in the `arr`/`scalar`/`handle`/`typ`/`reachable`/discovery family
  already covered by `O3_R2_DISCOVERY_PHASE_MAP.md`:
  - `self.get_root_group(aset)` (line 11714) → `aset.GetRootControlGroup()` (line 9244), wrapped in its own
    `try/except`.
  - `find_direct_child(root, RIG_RECON_ROOT)` and `find_direct_child(root, MASTER_RECON_ROOT)` (lines
    11719, 11724) → each calls `children(parent)` (a native array read) and `name(group)` per child (a
    native `GetName()` read, itself wrapped by `name()`'s own `try/except`, line 863-867).
  - `live_control_map(aset)` (line 11736) → `arr(aset, "controls")` (native array read) plus `name(control)`
    per control.
- **Zero** `QCoreApplication.processEvents()`, `QTimer.singleShot()`, or any other Qt-deferred-callback
  construct anywhere in this interval — confirmed by the same exhaustive whole-file-grep technique
  O2-R1's own proofs already established (the three `QTimer.singleShot()` call sites in this file, lines
  12556/12646/12758, are all in the per-target-loop scheduling code, outside this interval, already
  documented). This remains source-proven.
- **Zero** explicit DME write, native Rebuild call, shot activation, target re-resolution, or Undo
  transition anywhere in this interval — re-confirmed directly, matching O2-R1's own established finding.
  Undo remains explicitly disabled (`dm.SetUndoEnabled(False)`, line 11396) for this entire interval, only
  restored in the `finally:` block (line 12005) that runs strictly after composer-before's own capture.

## Classification of each risk surface

### `sys.stdout.write()` — MERELY OBSERVED, not proven either way

`sys.stdout` is never reassigned anywhere in this codebase (confirmed by an exhaustive grep for
`sys.stdout\s*=` across the entire production source: zero matches). Its actual bound object is therefore
whatever the SFM host application's own embedded-Python console redirection installs — this project has no
access to that host application's C++ source, headers, or documented API contract for what that stream
object's `write()` method does internally (e.g., whether it synchronously repaints a console widget via a
mechanism that could pump Qt events). **This cannot be determined from this file's own source, and no
documented SFM/API contract establishing its behavior is available anywhere in this project's evidence
base.** Fifteen calls to a method with this property occur in the interval under study — this is a larger
surface than O3-R1's own more limited citation of this risk implied.

### Native getters (`GetRootControlGroup()`, `children()`, `GetName()`, array reads via `arr()`) — MERELY OBSERVED, not proven either way

Every one of these is a SWIG-bound call into compiled C++. The Python source contains no evidence any of
them triggers a Python-level callback, and (as established above) no Qt-yield construct exists anywhere in
the traced interval at the **Python** level. But — exactly as O3-R1 already honestly stated for the
narrower interval it examined — **whether the underlying compiled implementation of any of these methods
could internally pump the Qt event loop, process a Windows message, or otherwise reenter is not
determinable from this project's available evidence.** No SFM SDK header, no documented API contract, and
no prior test in this project's history establishes non-reentrancy for these specific calls.

### Source-proven facts (the only category that counts toward "cannot mutate")

- No explicit DME write, native Rebuild call, shot/target re-resolution, or Undo transition anywhere in the
  interval (re-confirmed).
- No Qt-deferred-callback construct (`QTimer.singleShot`, `processEvents`) anywhere in the interval
  (re-confirmed).
- The transaction remains on a single, synchronous Python call stack throughout this interval — every call
  in the inventory above is a plain, synchronous function call; there is no `yield`, no coroutine, no
  thread creation, no queued-connection Qt signal anywhere in this code path.

### Runtime-contract-proven facts

**None found.** No SFM/Source-engine API documentation, header, or established project evidence anywhere
in this project's history documents that native getters or `sys.stdout.write()` cannot pump Qt events or
invoke registered callbacks. This project has never had access to such documentation; none is invented
here to fill the gap.

### Merely observed

Every real-SFM run performed across O2, O2-R1, O3-R2, and every earlier checkpoint has completed this
interval without any observed anomaly. Per explicit instruction, **this does not count as proof** —
"do not infer non-reentrancy merely because previous runs were stable."

## Conclusion

The interval's **explicit** mutation-free property remains source-proven, unchanged from O2-R1's own
established finding, now re-verified over the correct, larger interval (through the 15 `self.log()` calls
and 4 additional native getter calls this document newly inventories, not just the narrower span O2-R1's
own proof examined). But the **stronger** claim Option C's enumeration-validity question actually requires
— that nothing in this interval can reenter Python, pump Qt events, or otherwise create an opportunity for
scene topology to change between native POST and composer-before — is **not** established, at either the
source level or the runtime-contract level, and no available evidence in this project closes that gap.

**Classification: `UNRESOLVED`**, honestly, consistent with O3-R1's own prior classification of the same
underlying question, now confirmed to cover a materially larger call surface than previously enumerated (15
logging calls plus 4 additional native getters, not previously itemized together in one place).

This closes the second of the two routes the complexity gate (`O3_R3_ENUMERATION_VALIDITY_DECISION.md`
section 8) requires: neither an authoritative mechanism (`O3_R3_ENUMERATION_VALIDITY_MECHANISM_SEARCH.md`)
nor a provable immutable interval exists.
