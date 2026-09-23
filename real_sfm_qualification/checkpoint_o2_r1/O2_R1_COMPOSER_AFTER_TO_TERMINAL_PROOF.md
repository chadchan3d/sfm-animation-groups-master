# O2-R1 Narrow Static Proof: Composer-After → Terminal Capture

Read-only source analysis of `Rebuild_Control_Groups_Normalizer.py` (production Normalizer, SHA-256
`cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`), reconciled path only. This does
**not** propose global terminal removal and does **not** authorize any code change — proof-gathering
only, feeding a decision made elsewhere. Corroborating context (not proof): O2's real-SFM run found the
composer-after and terminal captures produce hash-equivalent results for Fox and Mia, both commands.

## Interval traced

From the composer-after capture completing (`production_generic_composer`'s own
`"PRODUCTION_GENERIC_COMPOSER_POST"` capture, line ~7524-7534) through to the terminal capture being
invoked (`semantic_target_fingerprint()` call at line 12129, inside `run_target_transaction`).

## Itemized trace

| Region | Lines | Classification |
|---|---|---|
| Rest of `production_generic_composer`'s own body: destination/membership/ordering/visibility/ownership/duplicate comparison against `desired` | 7536-7994 | Pure read-only comparison + native GETTER reads (`production_resolve_group_path`, `production_raw_selectable`, `is_selectable`, `children(root)`) — no writes |
| Fail-closed abort on mismatch | 7996-8010 | Exception-producing validation (`raise ProbeError`), aborts, never mutates |
| Composer's own return (`desired_count`, `moved_count`, `already_correct_count`, ...) | 8012-8090 | Pure read-only construction of the return dict |
| Back in `run_target_transaction`: bookkeeping/logging (`production_composer_pairs.add(...)`, counters) | 11908-11972 | Python allocation/bookkeeping only — no DME access |
| `raise ContextualCompositionSuccess("RECONCILED")`, immediately caught | 11974-11985 | Deliberate control-flow jump (not an error, not a mutation) |
| `finally:` block: `native_master_protect_release(...)` | 11996-12069 (part) | Native state release — releases an earlier-acquired guard handle; not a DME content mutation |
| `finally:` block: `dm.SetUndoEnabled(undo_prior)` + `dm.IsUndoEnabled()` verification, fail-closed | 11996-12069 (part) | Restores/verifies the undo-**tracking flag**, not scene content; `raise ProbeError` on restoration failure |
| `finally:` block: `read_undo_ledger(dm)`, fail-closed check ledger unchanged | 11996-12069 (part) | Native read + validation |
| Bookkeeping/logging | 12071-12098 | Python allocation only |
| `self.assert_master_stable()` (def line 9436-9449) | ~12098 | Pure read-only re-check: recomputes the canonical Master **file's** own SHA-256 and compares to `self.master_hash` — not a DME operation at all |
| `target_fingerprint = isolation_fingerprint(aset)`, fail-closed check | 12112-12121 | Lighter, read-only walk (not `capture_tree`) |
| Terminal capture (`semantic_target_fingerprint(shot, aset)`) | 12129 | The boundary this proof traces to |

**No DME content write occurs anywhere in this interval.** Every operation is pure Python bookkeeping, a
native read, a native non-content state/flag change (undo-tracking flag, protect-handle release), or
fail-closed validation that aborts rather than mutates.

## Answers

**1. Does terminal observe a semantically later state than composer-after?**
No — terminal observes the identical, already-finalized post-composer state; no DME write occurs
anywhere between composer-after and terminal.

**2. Can any mutation occur in this interval, even under some non-happy-path condition?**
No mutation occurs on the traced path. The only state changes are the undo-flag restore and
protect-handle release, neither touching DME content; every `raise ProbeError` in this interval is an
abort, not a retry/recovery path that could leave altered state.

**3. What does terminal uniquely validate that composer-after does not?**
Terminal's own log line (`PRODUCTION_FINAL_SEMANTIC_FINGERPRINT_CAPTURE = PASS`) does **not** prove
different *content* than composer-after already captured (content is identical, per the trace). It
proves the capture machinery **still succeeds after** the undo-restore, protect-handle-release,
Master-stability-reassert, and isolation-fingerprint steps ran — none of which composer-after's own
(earlier) capture could have attested to, since they had not executed yet at that point.

**4. Does composer-after's own success already prove the same invariant(s)?**
Composer-after's own success already proves the **content** invariants (its own extensive `failures`
check at lines 7996-8010: destinations, memberships, ordering, visibility, ownership, duplicates,
`rig_status`). It does **not** prove the DME graph remains cleanly capturable **after** the later
undo/protect-release/Master-assert steps — that is what terminal's own successful re-capture uniquely
attests to.

**5. Why does native-only fallback still need terminal coverage?**
Confirmed unconditional for both branches: the reconciled path (`except ContextualCompositionSuccess`,
line 11978) and the native-only-fallback path (`except NativePostFallback`, line 11987) both set
`terminal_status` and fall through into the **same** subsequent code — the `finally:` block, then lines
12071 onward, including the terminal capture at line 12129 — with no branch-conditional guard around it.
Terminal is the one validation point **shared by both branches**; composer-after exists only on the
reconciled branch, so terminal cannot be replaced by composer-after's own data for the fallback branch
at all.

## Mechanical conclusion

**`RECONCILED_PATH_REUSE_PLAUSIBLE`** — for the reconciled branch only.

Source-level *content*-equivalence between composer-after and terminal is fully explained: no DME
mutation occurs anywhere in the traced interval. However, any reuse design must independently account
for terminal's narrower, distinct **procedural** purpose — attesting that the DME remains cleanly
capturable *after* the undo-restore/protect-release/Master-stability-assert steps, something
composer-after's earlier capture cannot attest to by itself, since those steps had not yet run. A design
that reused composer-after's own data in place of a fresh terminal capture would need to separately
preserve (or replace with an equivalent, cheaper check) this "still capturable after cleanup" guarantee,
not just the content match.

This conclusion explicitly does **not** generalize to the native-only-fallback path, where terminal is
the sole validation point and has no composer-after counterpart at all — confirmed by the unconditional,
branch-independent placement of the terminal capture call.

No code change is proposed or authorized by this document.
