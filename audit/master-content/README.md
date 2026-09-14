# Master-content audit trail

Classification ledgers, human-review records, and reconciliation reports
produced while building and re-taxonomizing `sfm_defaultanimationgroups.txt`
itself. This is content-editorial history — decisions about *where a
control belongs* — not software test or qualification material; see
`docs/qualification/` for the sidecar's own qualification history.

- `phase2/` — the large-scale production-order classification pass (batch
  and tranche outputs, semantic pilot/rulebook iterations, the residual
  census, and the independently-verifiable production-order spec/sequence
  files consumed by `tools/verify_phase2_production_order.py`).
- `flex-bone/` — flex/bone active and final classification passes.
- `imports/` — the original Master import/reconciliation pass and its
  presentation-ordering refinement.
- `helpers/` — rig-helper human-review and casefold-family resolution
  passes.
- `sexual-bones/` — the sexual-bone migration review and post-edit audits.
- `whole-master/` — whole-file limb-side normalization.
- `SFM_LIVE_RENDER_TOUCHUPS_POST_EDIT_AUDIT.txt` — a standalone post-edit
  audit that doesn't belong to any of the above series.

None of this is consumed by `tools/sfm_master_sidecar/` or by SFM at
runtime; it is kept as the record of how the current Master taxonomy was
reached.
