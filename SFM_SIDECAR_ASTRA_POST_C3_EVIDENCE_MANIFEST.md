# SFM Sidecar — Astra Post-C3 Holistic Evidence Manifest

Current HEAD: `e1ef50e3990a9773760e0d92a1d9d3380cd3e9d7`
Current subject: `Qualify sidecar source freshness lifecycle`
Branch: `master`
Collected: 2026-09-13. Evidence-collection only.

**No implementation code changed while collecting this evidence.**
**Normalizer production integration has not begun.**
**The package does not claim that qualification-only owner/command-boundary modules are production-ready.**

## Package identity

- Package filename: `SFM_SIDECAR_ASTRA_POST_C3_EVIDENCE.zip`
- Package SHA-256: **see the evidence-collection final response** — a manifest
  packaged inside its own zip cannot self-referentially state that zip's hash
  without a fixed-point rebuild loop (updating this line changes the zip, which
  changes the hash, which would require updating this line again). This is stated
  explicitly here as a known limitation, not silently omitted; the authoritative
  value is reported in the final chat response for this task and is reproducible
  by hashing the delivered file directly.
- File count inside the package: **47** (all listed below, with repo/original path
  and SHA-256).

## Full file listing

Format: `package path` | `original/repo location` | `bytes` | `SHA-256` | `why included`

### 00_MANIFEST/

| Package path | Original location | Bytes | SHA-256 | Why included |
|---|---|---|---|---|
| `SFM_SIDECAR_POSTC3_ARCHITECTURE_AND_VERIFICATION.md` | repo root (this evidence pass) | 28,239 | `dda9afa6508a494ba2e800d1282838420864d832e93ad4384bd9c7546ebcf04a` | Architecture map + direct source verification of every Astra Round 3 finding and every Minimum C3 claim, plus the Python-2 manifest-seam analysis (brief §§2-5) |

### 01_CURRENT_PRODUCTION_REFERENCE/

| Package path | Original location | Bytes | SHA-256 | Why included |
|---|---|---|---|---|
| `reader.py` | `tools/sfm_master_sidecar/reader.py` | 44,993 | `1b95261c52d95c306b28fc6e5e9340afa65de4ea2574ed29c2bab427d252719f` | Sole production validator/reader |
| `format.py` | `tools/sfm_master_sidecar/format.py` | 14,249 | `b401967db8d07943e9f171058a006c30f0e23eb70a7b43bb5ab950203a3c3259` | Binary format contract |
| `manifest.py` | `tools/sfm_master_sidecar/manifest.py` | 8,102 | `bfe09c4188ec2c27de95a35d38053b3823a4a8296fc7ba6e2060ec2c3d0ec413` | The Python-3-only production manifest reader/builder central to §5's finding |
| `compiler.py` | `tools/sfm_master_sidecar/compiler.py` | 10,762 | `b973b78d0ea9953c3579430c9f54d2c12f59d4608e38ac75ba2e0dbe484f4e46` | Offline compile orchestration used unmodified by this gate's own fixture builder |
| `writer.py` | `tools/sfm_master_sidecar/writer.py` | 15,995 | `770d5beb1809e425869d12cd697e87fa741f085078589bcb982be8279f07d55d` | The actual binary serializer |
| `Rebuild_Control_Groups_Normalizer.py` | `usermod/scripts/sfm/mainmenu/ChadChan3D/` (external, current shipping copy) | 339,944 | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` | The real current Normalizer — for the mandatory knowledge-boundary inspection |

### 02_CURRENT_QUALIFICATION_SOURCE/

| Package path | Bytes | SHA-256 | Why included |
|---|---|---|---|
| `session_owner.py` | 42,425 | `59ce0a0fc8adfcf4df948859201a3b6012d107dd8531926b67179ddb371b17f7` | The owner/lease/view/retirement implementation under review |
| `command_boundary.py` | 11,556 | `a319a210eaafd02df94bd129618df867fb9fc1f4e65a08704eb5acdc5d2b0056` | Freshness/retirement orchestration + the qualification-only manifest reader |
| `resource_budgets.py` | 6,029 | `077b7cd9454f6613ecd482a35b8f11ac7d9e27c3547410aa71314f7b509f106a` | Provisional qualification budgets |
| `bounded_provider.py` | 20,689 | `8e70a47a5e657781f6047a0c50635904ba08894ff2a467f49420ff9a1fcea979` | S1 bounded-decode provider |
| `bounded_view.py` | 7,679 | `1ea9899471cfee2ab41594f6a4bd702fd9bbc22b5ef6debf0cc3c4b34a753dcd` | Fast view-builder reference implementation |
| `normalizer_source_profile.py` | 3,831 | `f7cc9e3f88936932f678b5b48dac40864c557b4d8e5c0a5f1c9283c286740ff9` | Source-profile compatibility gate |
| `shared_txt_session.py` | 3,527 | `ef78eb5d9f7ff1c4c113fb43fa7393b23b3084c9b58de113240c58b08451c842` | The TXT counterfactual object |
| `desktop_session_owner_qualification.py` | 33,624 | `e24e4c1602812f9aad436273a06b2b011ab2e27b1fb5818a7edadec39debc783` | C1/C1R historical harness (75 PASS) |
| `desktop_view_expansion_qualification.py` | 31,196 | `ad3d47d5aa3ff707624c5cabb5065e0e898a3cbb181b1a82928196d12e66a4e7` | C2/C2R historical harness (44 PASS) |
| `desktop_round3_foundation_qualification.py` | 18,975 | `23a4f5926ad887780dc1114766088312b4b3d889b890d1f1f4c3a311f519d7fc` | Round 3 foundation harness (40 PASS) |
| `desktop_minimum_c3_qualification.py` | 24,393 | `231a2ab0192f1cefcf2db21f45711c52426ca26f213841bf72dee15ff6194171` | Minimum C3 harness (53 PASS) |
| `desktop_parity_and_timing.py` | 12,917 | `493c08a088577809d4208c25ca8515ea7bac53a9f0ce73ef00827d87c5c2deda` | Semantic-parity harness (183 PASS) |
| `official_master_fixture.py` | 4,080 | `f2914aa637e8da897b4252ff08ff77e565565c550f9c12767042bb0c839c8f24` | Shared real-Master fixture used by every harness above |

### 03_ASTRA_ROUND3/, 04_ROUND3_FOUNDATION/, 05_MINIMUM_C3/

| Package path | Bytes | SHA-256 | Why included |
|---|---|---|---|
| `03_ASTRA_ROUND3/SFM_SIDECAR_ASTRA_ROUND3_HOLISTIC_AUDIT_2026-09-13.md` | 43,424 | `766ae839e88f9e6f8268b229981d03f70d5e8cf6180307c929c2369707552825` | The controlling architecture decision |
| `04_ROUND3_FOUNDATION/SFM_MASTER_SIDECAR_ROUND3_FOUNDATION_SIMPLIFICATION_REPAIR_AUDIT.md` | 28,214 | `f28ed1f015e38d3edede9984b2bc25f173f8e22d9294da843b3c6f83c44ebd7e` | The subtractive repair audit |
| `05_MINIMUM_C3/SFM_MASTER_SIDECAR_MINIMUM_C3_FRESHNESS_INVALIDATION_AUDIT.md` | 27,134 | `cade9508e5ba87e2fa81d8060b8b22fd94f8ce9a0a16e37b9ecbd43305f5ff60` | The freshness/retirement audit (amended before its own checkpoint to carry forward the manifest-seam caveat) |

### 06_RAW_EMBEDDED_EVIDENCE/

All 8 files are the exact, previously-committed, byte-verified embedded Python 2.7
probe scripts and raw logs/results — **not regenerated for this package**, copied
directly from their committed repo locations and reverified byte-identical (see the
architecture/verification document §6 for the reverification transcript).

| Package path | Bytes | SHA-256 |
|---|---|---|
| `round3_embedded_evidence/gate_round3_embedded_probe.py` | 16,398 | `326b672b7dd8d1d3c19288f54b8bba6e0aab2b00729db5241eb4a077c17ec312` |
| `round3_embedded_evidence/gate_round3_embedded_result.log` | 3,444 | `b95c12fab69ccdecd0e01c9939b84c64065c6f8b086e32308d788cf32ac798da` |
| `round3_embedded_evidence/gate_round3_embedded_results.json` | 42 | `17a1c12e6372c0bbf5b268f3b3cb559902ec1aa7709a5df45de7b87058700b88` |
| `round3_embedded_evidence/gate_round3_embedded_stage_markers.log` | 588 | `acd6210562578f04736362e9a54b4f9d74efb536fc7677233da4f188ee0f935b` |
| `minimum_c3_embedded_evidence/gate_c3_embedded_probe.py` | 11,715 | `02ee4b611652457d756ed9e4ee8ab6f5885ade2300b1a0498277216a01f878b8` |
| `minimum_c3_embedded_evidence/gate_c3_embedded_result.log` | 3,140 | `481e5bd3fd1d09054f4b40e90c573eec53f4aa4de00841303b704e11265b5fd3` |
| `minimum_c3_embedded_evidence/gate_c3_embedded_results.json` | 42 | `2c8cb5c9b4f830e958e93700d2620ba34a01054aa4d80dc54644fa77fef4f7e6` |
| `minimum_c3_embedded_evidence/gate_c3_embedded_stage_markers.log` | 498 | `346a165b723746b390126161ee77d6ed0f7d6d383eae8c8f39998c3b97b22f73` |

Both embedded results.json files' pass/fail counts (26/0 and 24/0 respectively) were
cross-checked against their respective audit's claimed counts in this session and
match exactly.

### 07_REGRESSION_OUTPUT/ (fresh transcripts from THIS evidence-collection session)

| Package path | Bytes | SHA-256 | Result |
|---|---|---|---|
| `desktop_round3_foundation_qualification.log` | 5,447 | `3aac3881210343f3789649b0dd3432250730384a324545b9c0e8953f36d4f5a2` | 40 PASS / 0 FAIL |
| `desktop_minimum_c3_qualification.log` | 8,580 | `9e9945997a671ea13f7294af4a5e3268011a68516367866d6b0089285e2baf98` | 53 PASS / 0 FAIL |
| `desktop_parity_and_timing.log` | 20,431 | `ec7c1553eb980e2ea616d0a954824b8369a343cd5d568a5657a5bf60a47f2ccc` | 183 PASS / 0 FAIL |
| `postc3_pytest_sidecar.log` | 500 | `8dd2b86dee371bb2f385e0fddc5528e27a3a2caf9374b47fd77ff584ff6bb1db` | 369 passed, 265 subtests passed |
| `postc3_pytest_full.log` | 581 | `37f65e565612f69521f29d4cce3d7fac686f16e90ad4879099b6e2fc33afaa4e` | 421 passed, 265 subtests passed |
| `postc3_validator.log` | 555 | `ce9e100e1f3f1f7fcb9a6b821c52d636fab4a186f22aba92a696945cbd6a7c47` | PASS, 0 duplicates, 0 cross-path violations |

### 08_CLAIMS_AND_CHRONOLOGY/

| Package path | Bytes | SHA-256 | Why included |
|---|---|---|---|
| `SFM_SIDECAR_POSTC3_CLAIMS_LEDGER.md` | 10,340 | `beceb97ddc6826dda978fe0f4c11d2beac92f45f5569913b491d784021e14b75` | Strict supported/narrowed/withdrawn/unproven table (brief §7) |
| `SFM_SIDECAR_POSTC3_CHRONOLOGY.md` | 10,870 | `acaad98317a7dbd4214ee667ab314c7ea0903707a0ea8d879a74078909160f1b` | B0-through-C3 correction history (brief §8) |
| `SFM_SIDECAR_POSTC3_PRODUCT_GOAL_AND_TXT_COUNTERFACTUAL.md` | 6,953 | `25081f44b4d1b48beb63cfabe634a2e1179eff40daaef0f8cecd58fe05f89d74` | Product-goal comparison + strongest fair TXT counterfactual (brief §9-10) |
| `SFM_SIDECAR_POSTC3_PRODUCTION_PRUNING_INVENTORY.md` | 5,300 | `ab74b0e286d0983df618af8a2bc0393920e0cde10f1d7e47974c95d042b72514` | Every sidecar-related artifact, classified (brief §12) |

### 09_NORMALIZER_REFERENCE/

| Package path | Bytes | SHA-256 | Why included |
|---|---|---|---|
| `SFM_SIDECAR_POSTC3_NORMALIZER_KNOWLEDGE_BOUNDARY.md` | 7,452 | `a03f205e95cb4f936a49a5cb205df59c47403bf91cf9f2de407897d62c8a655e` | Known-from-source / not-yet-established boundary (brief §11, mandatory) |

### 10_PRIOR_CONTINUITY/

| Package path | Bytes | SHA-256 | Why included |
|---|---|---|---|
| `SFM_MASTER_SIDECAR_GATE_C0_PROMOTION_PREREQUISITES_AUDIT.md` | 33,460 | `cbb242610462f26f6a0077bf8bea67fb1815950efa92eb10feb2ab110a08225d` | C0 closure record, needed for chronology |
| `SFM_MASTER_SIDECAR_GATE_C1_SHARED_OWNER_FOUNDATION_AUDIT.md` | 34,441 | `74caa2d8293b52c291c8f2b254712153eb9ac7dcd38bc818866677dcbd70233d` | C1/C1R record (includes the preserved §27 post-review-correction section) |
| `SFM_MASTER_SIDECAR_GATE_C2_VIEW_EXPANSION_AUDIT.md` | 27,607 | `217233737cc471a3068f317868b8ee4c4647d995e768171de24303c6c153d053` | C2/C2R record (includes the preserved §24 post-review-correction section) |
| `SFM_SIDECAR_ASTRA_ROUND2_AUDIT_2026-09-12.md` | 60,208 | `c2b7a93abde0fc2d8a5006ab6757342efb23d95350633c3f993e76d20c0be7a6` | The actual Astra Round 2 review, located at `C:/Users/REDACTED/Documents/Codex/2026-09-07/files-pasted-by-the-user-use/outputs/` — the prior baseline recommendation |
| `SFM_Sidecar_Progress_Ledger_2026-09-13_c2_checkpoint.md` | 64,561 | `b6092630bea02b4173e07058cbee57b80c2664236525a1a67868be73970f6930` | The standing project ledger available at collection time, for chronology/context only |

## Evidence gaps

- The zip's own SHA-256 cannot be embedded in this manifest without a rebuild loop
  (see "Package identity" above) — reported in the final response instead.
- Gate B's original detailed timing measurements (fresh vs. late-vocabulary
  acquisition costs) were **not** re-run in this evidence pass (out of scope for a
  post-C3 evidence collection); the claims ledger marks the late-vocabulary-value
  claim "NARROWED" partly for this reason.
- C0.4/C0.5's original resource measurements (steady/peak SFM memory) were **not**
  re-measured in this pass; cited historically only.
- No real Normalizer command was actually run/profiled during this evidence
  collection — the Normalizer's own `master_index_build_seconds`/memory-delta
  figures for a live run were not captured here (only its SOURCE was inspected).
- A genuinely malformed-JSON-syntax manifest was never tested under embedded Python
  2.7 (only on desktop) — noted explicitly in both the architecture/verification
  document and the claims ledger.
- Historical B1/B1.1 design documents and Gate2A/2C candidate-comparison audits
  were deliberately excluded from the package proper (available on request) per the
  brief's "do not include ... large historical files that add no review value"
  instruction; they are referenced, not included.

## Known limitations

- This package is a snapshot at one HEAD; it does not attempt to re-litigate
  whether Round 3's or Minimum C3's OWN provisional threshold values (guard
  minimums, budget defaults, per-fold overhead estimates) are correct — only that
  they are enforced as documented.
- The claims ledger and architecture/verification documents were authored by the
  same agent that performed the underlying qualification work across this entire
  arc; they are source-first and directly re-verified in this session, but Astra
  should still independently spot-check rather than treat them as a neutral
  third-party audit.

No implementation code changed while collecting this evidence.
Normalizer production integration has not begun.
The package does not claim that qualification-only owner/command-boundary modules are production-ready.
