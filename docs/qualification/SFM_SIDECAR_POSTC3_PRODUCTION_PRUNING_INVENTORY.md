# SFM Sidecar — Production-Pruning Inventory

Every current sidecar-related module/artifact, classified. Nothing was deleted to
produce this document.

| Path | Classification | Why |
|---|---|---|
| `tools/sfm_master_sidecar/reader.py` | **KEEP for likely production** | The sole validation implementation; already production code; Python-2/3 compatible |
| `tools/sfm_master_sidecar/format.py` | **KEEP for likely production** | Binary layout contract; unchanged throughout the arc |
| `tools/sfm_master_sidecar/manifest.py` | **DEFER** | Production-quality for its OWN (offline/build) purpose, but Python-3-only — cannot run inside embedded SFM as-is; whether/how it participates in a real Normalizer-facing design is undecided (see the manifest-seam finding) |
| `tools/sfm_master_sidecar/compiler.py` | **KEEP for likely production** | Offline compile orchestration; unmodified, self-validating |
| `tools/sfm_master_sidecar/writer.py` | **KEEP for likely production** | The actual serializer |
| `tools/sfm_master_sidecar/publisher.py`, `cli.py` | **DEFER** | Offline publication tooling; not exercised or reviewed in this arc beyond existing |
| `tests/sidecar/qualification/session_owner.py` | **DEFER** | The central open question — owner/lease/view architecture, undecided for production per every audit in this arc |
| `tests/sidecar/qualification/command_boundary.py` | **DEFER, with an explicit known gap** | Freshness/retirement orchestration; its own manifest reader is qualification-only and less hardened than production `manifest.py` (see architecture doc §5) — must NOT be promoted as-is |
| `tests/sidecar/qualification/resource_budgets.py` | **TEST-ONLY** | Explicitly provisional constants, never validated as a production SLA |
| `tests/sidecar/qualification/bounded_provider.py` | **TEST-ONLY** | Qualification stand-in ("S1"); delegates validation to production `reader.py` but is not itself a shipped module |
| `tests/sidecar/qualification/bounded_view.py` | **TEST-ONLY** | Fast view-builder used to prove the bounded-decode concept; the Normalizer has its own independent `parse_targeted_master`/`master_lookup` |
| `tests/sidecar/qualification/normalizer_source_profile.py` | **TEST-ONLY** | A compatibility-profile gate for the qualification path specifically |
| `tests/sidecar/qualification/shared_txt_session.py` | **TEST-ONLY** | The TXT counterfactual object, used only for fair comparison |
| `tests/sidecar/qualification/desktop_*.py` (5 harnesses) | **TEST-ONLY, permanently** | Development/regression evidence; never intended to ship |
| `tests/sidecar/qualification/round3_embedded_evidence/`, `minimum_c3_embedded_evidence/` | **HISTORICAL EVIDENCE** | Preserved exact embedded probe scripts + raw logs; committed for auditability, not runtime artifacts |
| `tests/sidecar/official_master_fixture.py` | **TEST-ONLY** | Shared test fixture cache |
| `SFM_MASTER_SIDECAR_PHASE_B1_DESIGN.md`, `..._B1_1_REVISED_DESIGN.md` | **HISTORICAL EVIDENCE** | Superseded design documents, kept for record only |
| `SFM_MASTER_SIDECAR_GATE2A_CANDIDATE_A_EMBEDDED_BASELINE_AUDIT.md` (+ rerun), `..._GATE2C_BACKING_STRATEGY_COMPARISON_AUDIT.md` | **HISTORICAL EVIDENCE** | Superseded candidate-comparison audits from before Gate B's final direction |
| `SFM_MASTER_SIDECAR_GATE_C0_PROMOTION_PREREQUISITES_AUDIT.md`, `..._GATE_C1_SHARED_OWNER_FOUNDATION_AUDIT.md`, `..._GATE_C2_VIEW_EXPANSION_AUDIT.md` | **HISTORICAL EVIDENCE** | Committed gate audits, each later superseded in part (see chronology) but kept as the record of what was claimed and when |
| `SFM_SIDECAR_ASTRA_ROUND3_HOLISTIC_AUDIT_2026-09-13.md` | **HISTORICAL EVIDENCE / controlling document** | The controlling architecture decision for everything since |
| `SFM_MASTER_SIDECAR_ROUND3_FOUNDATION_SIMPLIFICATION_REPAIR_AUDIT.md`, `SFM_MASTER_SIDECAR_MINIMUM_C3_FRESHNESS_INVALIDATION_AUDIT.md` | **HISTORICAL EVIDENCE / current controlling audits** | The two most recent gate audits, both committed |
| `_EpochCoverage` mechanism (Gate C2/C2R) | **DELETE/PRUNE — already done** | Fully removed from `session_owner.py`; listed here only for completeness of the historical inventory |
| Registration-install claim / fourth guard criterion (Gate C1/C1R) | **DELETE/PRUNE — already done** | Same disposition |
| Candidate B/C (file-backed reads, mmap) | **N/A — never built** | No source exists; historical audits reference them only as considered-and-deferred alternatives |
| `Rebuild_Control_Groups_Normalizer.py` (current, external) | **KEEP (production, unmodified)** | The real shipping Normalizer; zero sidecar integration present; not a candidate for pruning, listed here only for completeness |

**Summary for Astra's "how much code would actually ship" question:** if the
sidecar direction survives as-is today, the modules genuinely eligible for
production promotion are limited to the already-production
`reader.py`/`format.py`/`compiler.py`/`writer.py` (unchanged since before Gate B)
plus a yet-to-be-designed, yet-to-be-hardened adapter layer — none of
`session_owner.py`, `command_boundary.py`, or any desktop/embedded harness is
proposed for production promotion by any audit in this arc; every one of them is
explicitly labeled TEST-ONLY or DEFER, including in this document.
