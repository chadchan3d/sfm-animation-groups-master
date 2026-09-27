# CPM G18AN Migration Baseline Manifest

This directory holds a **frozen, read-only migration baseline** copied verbatim from the
Character Preset Manager (CPM) source repository, `chadchan3d/sfm-character-preset-manager`,
now closed as a source archive (see
`docs/qualification/CPM_CONVERGENCE_INTEGRATION_HANDOFF.md`).

**This is not editable CPM production source and not a second place CPM code is developed.**
Migrated CPM code for the shared-authority convergence work goes in a new file elsewhere in
this repository, never here and never inside `sfm_master_authority_productionized/`.

## Snapshotted file

| Field | Value |
|---|---|
| Source repository | `chadchan3d/sfm-character-preset-manager` |
| Source commit | `390e01e` (`390e01eb7ac1ceb220e480126f40077703acb0f4`) |
| Source path | `src/SFM_CSP_G18AN_SaveNewCopy.py` |
| Imported path | `cpm/baseline/SFM_CSP_G18AN_SaveNewCopy.py` |
| SHA-256 | `3326024ddecd544ad1e10659bbf7b98420b5f147fca775433878c19fd9e66b3e` |
| Git blob (this repository) | `e8c1bceecdd2d3569168a35b27b8e49d7a38b911` |
| Byte size | 846,628 bytes |
| Line count | 34,898 |
| Encoding | ASCII |
| Newline style | pure LF |
| Internal version | `0.2.0-rc7-g18an-save-new-copy` |
| License | CC0 1.0 Universal (per the source repository's own `LICENSE_SCOPE.md`) |

## Status

**Frozen behavioral migration baseline and parity oracle** for the CPM convergence work
(`docs/qualification/CPM_CONVERGENCE_INTEGRATION_HANDOFF.md` §2, §4).

- **Never edited.** This file must remain byte-identical to the SHA-256 above for as long as
  it serves as the parity oracle; any actual behavior change belongs in a new, migrated file,
  not here.
- **Not a release candidate.** G18AN is a development baseline in its own source repository,
  not a public 1.0 release artifact.
- **Latest CPM version.** G18AN is the current and latest version in both the CPM repository
  and the local SFM install: it follows G18AM, an ineffective equal-column layout experiment
  that was reverted; no later version exists anywhere. G18AN's own product-facing change from
  the preceding lineage was intentionally small (concise **Save New** button labels); it
  otherwise inherits the qualified semantic scope, persistence, generic bone scaling, Clothing
  Fit, Review, model-identity, modal-yield, and native mutation behavior of the production
  lineage before it.
- **Qualification status.** G18AN has a static checkpoint
  (`SFM_CSP_G18AN_SaveNewCopy_StaticCheckpoint_2026-09-16.md`, documented in the source
  repository), not a real-SFM run of its own -- it inherits the already-qualified real-SFM
  behavior of the lineage before it rather than being independently re-qualified end-to-end
  itself.

## Verification

```python
import hashlib
with open("cpm/baseline/SFM_CSP_G18AN_SaveNewCopy.py", "rb") as f:
    data = f.read()
assert hashlib.sha256(data).hexdigest() == "3326024ddecd544ad1e10659bbf7b98420b5f147fca775433878c19fd9e66b3e"
assert len(data) == 846628
```

An independent auditor can also compare this file's git blob hash directly against the source
repository's own blob hash for `src/SFM_CSP_G18AN_SaveNewCopy.py` at commit `390e01e` -- both
are `e8c1bceecdd2d3569168a35b27b8e49d7a38b911`.
