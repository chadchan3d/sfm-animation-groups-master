# Ledger

## Coder gate
Before editing, compare the assignment with the Blueprint and this Ledger.
Verify the current code state and relevant claims.
If the assignment assumes unfinished work is complete, contradicts the
Blueprint, or expands scope, report the conflict before dependent edits.
Otherwise proceed with the assigned milestone.

## Current milestone
Real-SFM Qualification Session 1:
- normal CPM operation;
- native Apply + Undo;
- one ordinary Fit target + Undo;
- the C10 same-process broker check;
- minimal Normalizer coexistence;
- resources and latency.

**Status: prepared and deployed; BLOCKED on operator execution in SFM.** No Session 1 result
exists yet.

## Current state
`master` at the Ledger commit that follows `1b78eac` (Session 1 probe + runbook). No product code
changed since `cefa882`.

The qualification deployment is placed in `<game>\usermod\scripts\sfm\mainmenu\ChadChan3D\` (the
interim layout, qualification only). It consists of four new files; nothing was overwritten, and
it is reversible by deleting them.

| Deployed file | SHA-256 | Source |
|---|---|---|
| `SFM_Character_Preset_Manager.py` | `945eab6c…af8a` | blob `56286dd9` |
| `cpm_authority_adapter.py` | `e96e21b5…6607` | blob `f2ea7588` |
| `cpm_compat_v1_projection.py` | `9b077a1b…ffc1` | blob `50caf702` |
| `CPM_Session1_Probe.py` (test-only) | `d7f16fac…3cd6` | — |

Verified already present in the deployment folder:
- **Normalizer:** `1f4ec5a2…` (matches the audit snapshot).
- **Shared package:** 23 files identical to the canonical correction6 copy (`projections.py`
  correctly absent); API `1.0.0-b2a`, build `package-boundary-corrected-2026-09-22`.
- **Master:** `ac45e5c1…904d93`, the same as the repo Master.
- **Sidecar:** `bcd97641…`, source-matched to that Master.
- **Interpreter:** SDK Python 2.7.5 (MSC v.1600, 32-bit). The probe records SFM's own runtime
  version.

## Verified
- Probe dry run under 2.7.5, offline:
  - with no broker it constructs nothing and reports none;
  - once the singleton exists it reports that same object id, 0 leases and 0 open providers;
  - the JSONL record is written.

  Its CPM-window path can only run inside SFM.
- The runbook (`real_sfm_qualification/cpm_session1/INSTRUCTIONS.md`) maps each Session 1
  requirement (A–I) to probe checkpoints P0–P12 and to log evidence.
- Offline evidence from earlier milestones is unchanged: Suites 1–4, C7–C9 PASS offline, and C10
  PASS offline except the same-process item.

## Unresolved
- **Session 1 verdicts: all PENDING (not run):**
  - normal CPM operation;
  - native Apply + Undo;
  - ordinary native Fit + Undo;
  - C10 same-process broker;
  - Normalizer coexistence;
  - resource/latency measurement.
- **Observations for the owner (not defects; unchanged G18AN behavior):**
  - The converged app keeps G18AN's window slot (`_sfm_character_slider_preset_tool_window`), its
    log file name and `PROD_VERSION`. Many older CPM builds in the mainmenu root share that slot,
    so the runbook requires a fresh SFM process opening only the converged app. Product identity
    strings are a K/L decision.
  - In the interim layout the two CPM modules sit beside the app, so they may appear as extra
    Scripts-menu entries (L).
- **Reserved for Sessions 2–3 and the failure gates:**
  - G1→G2 with CPM open, and during a Save/Update prompt;
  - the queued Fit target-1 G1 → target-2 G2 transition, and target 1's Undo after it;
  - the forced Apply and forced Fit rollback-verification failures.
- Stale-scope UI presentation and `SidecarMissing` messaging: undecided. Cleanup, K, L: not
  started.

## Next
Operator: run Session 1 per `real_sfm_qualification/cpm_session1/INSTRUCTIONS.md` in a fresh SFM
process. Return the probe JSONL, the CPM log, the Normalizer log and the run sheet. I then
evaluate the evidence and record the verdicts. No Session 2 work.

## Checkpoints
Update this Ledger and output its complete, concise contents when:
- The milestone is complete and checked.
- Progress is blocked or requires an owner decision.
- A Blueprint conflict, scope expansion, or unmet prerequisite is found.
- Work is being paused or transferred.

State why the checkpoint occurred. Stop at milestone completion.
For blockers or conflicts, pause affected work until resolved.
The owner relays the updated Ledger to the designer, or the designer
retrieves that same version from the shared repository.

## Maintenance
Replace stale entries; keep checkpoint content about one screen.
Preserve unresolved issues. Label uncertainty and untested claims.
Keep history in Git or an archive. Routine edits do not require a
full Ledger report.
