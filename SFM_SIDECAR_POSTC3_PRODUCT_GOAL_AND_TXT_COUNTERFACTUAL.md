# SFM Sidecar — Original Product-Goal Comparison and Strongest Fair TXT Counterfactual

## Original product goal (unchanged, not reinterpreted here)

Stated consistently across the project's own prior documents/audits (Gate B brief,
Astra Round 2/3 briefs, the Round 3 controlling audit):

- the authored Master TXT (`sfm_defaultanimationgroups.txt`) remains the single
  editable semantic authority — nothing in this arc has ever proposed changing that;
- the first real consumer is the Normalizer (`Rebuild_Control_Groups_Normalizer.py`);
- the sidecar exists only if it materially improves practical authority acquisition
  for that consumer — it is not infrastructure for its own sake;
- x86 SFM resource safety matters (the embedded target is a 32-bit process);
- advanced-modeler usability matters (an editable-TXT workflow must remain
  understandable even to someone who edits the Master directly);
- infrastructure is subordinate to artist-facing tooling — the product is reliable,
  taxonomically uniform SFM tooling, not a database/cache platform.

## Current architecture mapped against that goal

Classification of every current mechanism, using current source (not historical
labels):

| Mechanism | Classification | Why |
|---|---|---|
| Offline compiler/writer/manifest (`compiler.py`, `writer.py`, `manifest.py`) | **Essential product architecture, IF the sidecar concept is kept** | This is the actual thing that would need to exist for any sidecar-based approach at all; unmodified, production-quality, already self-validating |
| Packed sidecar binary format (`format.py`) | **Essential product architecture, IF kept** | Same reasoning; unchanged since before Gate B |
| Production reader (`reader.py`) | **Essential product architecture, IF kept** | The one validation implementation every qualification module delegates to |
| Process-wide owner (`session_owner.py`'s `MasterAuthorityOwner`) | **Qualification-only scaffolding, undecided for production** | No equivalent persists in the real Normalizer today (it rebuilds fresh per command); this is new machinery whose necessity has not been established against real Normalizer behavior |
| Pre-admission resource guard (`GuardPolicy`) | **Necessary safety, IF an owner is kept; otherwise moot** | 32-bit memory safety matters per the product goal, but the guard's own thresholds are explicitly provisional, never validated against real SFM telemetry beyond the original C0 measurements |
| Leases | **Qualification-only scaffolding, undecided** | A GC-independent authority-lifetime mechanism; the real Normalizer has no equivalent concept (it just holds a local dict) |
| Detached action views | **Qualification-only scaffolding, undecided** | Same reasoning |
| Command-boundary freshness/retirement (`command_boundary.py`, `RETIRED` state) | **Qualification-only scaffolding, undecided; and duplicates an existing production mechanism** (see architecture/verification doc §5) | The Normalizer already hard-fails on a mid-command source change via its own `sha256_stream`/`contextualizer_assert_master_stable_for_index_use` — this qualification path solves a related but not identical problem (retire-and-later-readmit vs. hard-fail-now) that has not been shown to be needed |
| Resource budgets (`resource_budgets.py`) | **Optional optimization / qualification-only** | Explicitly provisional; the Normalizer measures memory deltas today but does not appear to enforce a budget |
| Desktop/embedded qualification harnesses | **Qualification-only scaffolding, permanently** | Never intended for production; their value is in what they proved, not in shipping |
| Reusable cross-action coverage cache (`_EpochCoverage`) | **Complexity drift — already removed** | Astra Round 3 found it added more retained-state risk than benefit; Round 3 foundation repair deleted it |
| Fourth guard criterion, registration-install claim | **Complexity drift — already removed** | Same disposition |

## Strongest fair TXT counterfactual

The alternative this project has itself already built and measured, not a
newly-invented one:

- **Source-bound scoped TXT authority**: `shared_txt_session.py`'s `SharedTxtSession`
  — acquires a bounded, per-fold-scoped view directly from the TXT source, no
  compiled artifact involved.
- **Reuse of covered positives/negatives where applicable**: `SharedTxtSession`
  tracks `covered_folds`/`proven_absent` and can serve a second request from the
  same warm session without a second full scan, as long as the requested vocabulary
  is already covered.
- **Full TXT scan when genuinely uncovered vocabulary arrives**: the fallback for
  anything outside the already-covered scope, exactly the cost the sidecar exists to
  avoid paying repeatedly.
- **No sidecar publication/lifecycle machinery of any kind**: no compiler, no
  manifest, no owner, no lease, no retirement — the TXT counterfactual's entire
  "lifecycle" is: open the file, scan what's needed, done.

### What sidecar benefit remains genuinely differentiated

Resolving a fold that was NEVER touched before (a genuinely new/late vocabulary
item, C0.6's "genuinely withheld" proof) without paying for a fresh full-file scan
of the ENTIRE Master, once a sidecar generation is already admitted. This is real
and was proven in Gate B and never withdrawn.

### What warm/shared TXT already makes cheap

Repeated requests for ALREADY-covered vocabulary — `SharedTxtSession` already
serves these cheaply, with no compiled artifact, no manifest, no owner lifecycle at
all. Critically, this is now the SAME cost shape the sidecar itself has for
repeated requests since Round 3's Repair F removed the owner-level cross-action
cache: both paths now re-resolve (TXT: nothing to reuse across calls beyond the
already-scanned session state; sidecar: nothing to reuse across calls at all,
per-call, since Repair F). The sidecar's repeated-request advantage that Gate B
originally measured has been narrowed by Round 3's own subtraction (see the claims
ledger).

### What sidecar costs/complexity remain

An offline compile step; a manifest/pointer resolution step (with its own not-yet
-hardened Python-2 seam); an owner/lease/view lifecycle with a resource guard,
retirement state, and per-request accounting — none of which the TXT counterfactual
needs at all.

### Whether new evidence since Astra Round 3 materially changes the comparison

**Yes, narrowly.** Round 3's own subtraction (removing the reusable cross-action
cache) means the sidecar no longer has a "repeated request is cheaper than TXT"
advantage — only the "first touch of genuinely new vocabulary avoids a full rescan"
advantage remains differentiated. This is a smaller gap than the project's earlier
audits (pre-Round-3) implied, and should be weighed as such, not with the original
Gate B framing. No sunk-cost claim is made either way here — this section reports
the comparison, not a recommendation.
