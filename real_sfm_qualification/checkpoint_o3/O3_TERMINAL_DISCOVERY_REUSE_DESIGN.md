# O3 — Terminal Discovery Reuse Design

**Status: DESIGN/PROOF ONLY.** No production, integration, or lifecycle code has been modified. Nothing
here authorizes an optimization. This is treated as a **separate and weaker** candidate than
outer-POST→composer-before — terminal validation itself is not proposed for removal.

## Basis

`O2_R1_COMPOSER_AFTER_TO_TERMINAL_PROOF.md` (`RECONCILED_PATH_REUSE_PLAUSIBLE`) and
`O3_DISCOVERY_CALL_MAP.md` (discovery call #5) jointly establish: the interval between
`production_generic_composer`'s own `PRODUCTION_GENERIC_COMPOSER_POST` capture and the terminal
(`semantic_target_fingerprint`) capture contains no DME content write — only Python-only bookkeeping, a
native protect-handle *release* (not a mutation), an undo-tracking *flag* restore (not scene content),
and a Master-*file* stability re-assertion (reads the Master file's own SHA-256, does not touch the
target's DME at all).

## Answers to the required questions

**1. Can terminal reuse the same rig identity discovered at composer-after?**
Yes, on the reconciled path — the interval between composer-after's own discovery and terminal's own
discovery is proven mutation-free at the DME level (same proof cited above).

**2. Does Undo restoration alter the rig/group/control object topology or only bookkeeping?**
Only bookkeeping. `dm.SetUndoEnabled(undo_prior)` (line ~12005) restores a tracking *flag*; it does not
touch DME content. Confirmed by direct trace in `O2_R1_COMPOSER_AFTER_TO_TERMINAL_PROOF.md`.

**3. Does protection release alter DME structure?**
No. `native_master_protect_release(...)` (line ~11996-12069 region) releases an earlier-acquired native
*guard handle* — a resource-lifecycle operation, not a content mutation.

**4. Does Master/source reassertion alter DME structure?**
No. `self.assert_master_stable()` (def line 9436-9449) recomputes the canonical Master **file's own**
SHA-256 and compares it to `self.master_hash` — this is a read of the Master file on disk, entirely
disjoint from the target's own DME graph.

**5. Is there any callback/yield between composer-after and terminal?**
No — confirmed by the same static proof (no `processEvents`/`singleShot` call exists anywhere in this
interval).

**6. Could terminal target identity differ?**
No, within the scope this reuse design is proposed for (strictly within one target's own transaction —
`shot`/`aset` are the same Python objects throughout `run_target_transaction`'s own single call; target
re-resolution only happens *between* targets, via `contextualizer_resolve_resume_target()`, never mid-
transaction).

**7. What exact stale-state guard would be required before reuse?**
The same guard as `O3_MINIMAL_DISCOVERY_REUSE_OBJECT.md`'s own general design: re-verify `handle(aset)`
matches the target identity the token was computed for, and that the token's own `status` is still a
usable value. No *additional* guard is required for the undo-restore/protect-release/Master-reassert
steps specifically, because each of those is already independently fail-closed (`raise ProbeError` on
failure, confirmed in the proof) — if any of them had failed, execution would never reach terminal at
all, so reaching terminal already implies they succeeded.

## Preferred target vs. what is NOT proposed

**Preferred, and supported by this analysis**: fresh terminal semantic *capture* (unchanged — terminal's
own `capture_snapshot_explicit`/`capture_tree` call still runs, still independently validates
missing-root/duplicate-path/group-control integrity, still produces its own fresh content) **+** reused
same-target rig *discovery* (skip terminal's own redundant `reachable(scene)` walk, reuse the identity
token from the immediately-preceding discovery in the same branch).

**Not proposed**: removing terminal validation. Terminal's own distinct procedural purpose — attesting
the DME remains cleanly capturable *after* the undo-restore/protect-release/Master-reassert sequence —
is preserved in full, because the *capture* itself still runs fresh; only the *discovery* identity is
reused, and discovery identity reuse does not touch what terminal's capture is actually attesting to
(that the capture machinery still succeeds at this late point).

## Native-only fallback: must remain independently correct, per sub-case

Per `O3_DISCOVERY_CALL_MAP.md`, terminal is reached on **all three** branch shapes, not just the
reconciled path:

- **Sub-case A (policy/wrapper fallback)**: PRE → NATIVE_POST → TERMINAL. No composer runs in this
  sub-case at all, so the interval between NATIVE_POST's own discovery and terminal's own discovery is
  **even more strongly** mutation-free (no composer-writes phase exists to have occurred). The same
  reuse design applies, reusing NATIVE_POST's own discovery token instead of composer-after's.
- **Sub-case B (PRE-unsupported)**: PRE (capture already failed) → TERMINAL. **No safe reuse basis
  exists here** — NATIVE_POST's own discovery/capture never ran at all in this sub-case, so there is no
  prior *successful* discovery to reuse from. Terminal's own discovery in this sub-case **must remain
  `FRESH_DISCOVERY_REQUIRED`**, unconditionally, regardless of what design is chosen for the other two
  branch shapes. Any implementation of terminal-discovery reuse must explicitly gate on "did a prior
  successful discovery actually occur in this branch" before attempting reuse, defaulting to fresh
  discovery when it did not.

This is the concrete meaning of "native-only fallback terminal behavior must remain independently
correct": sub-case A gets the reuse optimization (on the same terms as the reconciled path), sub-case B
does not, and any implementation must distinguish them explicitly rather than applying one rule
uniformly to "the fallback branch."

## Classification

**`TERMINAL_DISCOVERY_REUSE_SAFE_ON_RECONCILED_PATH`** — and, by the same proof, safe on native-only
fallback sub-case A. Sub-case B remains `FRESH_TERMINAL_DISCOVERY_REQUIRED`, not a failure of this
classification but a distinct, narrower carve-out within it.

This is a **weaker** candidate than outer-POST→composer-before (`O3_OUTER_POST_COMPOSER_BEFORE_DESIGN.md`)
for two reasons: (1) it requires branch-aware gating (three-way, not two-way) rather than a single
uniform rule; (2) it saves exactly one discovery call regardless of branch, versus
outer-POST→composer-before's own single-call savings applying uniformly on the reconciled path only —
the two candidates are not additive in a simple way without careful implementation, since a single
target's own transaction could plausibly realize *both* savings if both are implemented, but that
compounds implementation complexity beyond what `O3_IMPLEMENTATION_RECOMMENDATION.md`'s "at most one
candidate" constraint allows for this round.

No code change is proposed or authorized by this document.
