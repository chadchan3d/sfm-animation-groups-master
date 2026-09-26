# Checkpoint I — Master Generation Replacement — Instructions

**Prepared 2026-09-25. CORRECTION ROUND 1 applied 2026-09-25 (independent review, 11 blockers). CORRECTION
ROUND 2 applied 2026-09-25 (second independent review, 8 blockers). CORRECTION ROUND 3 applied 2026-09-25
(third independent review, 5 blockers + 1 hardening). NOT yet run against real SFM. Fourth independent
review required before execution.**

## Correction round 1 — eleven blockers fixed before any real-SFM run

1. **Atomic Master replacement (was NOT atomic).** The old `_atomic_write_bytes()` did temp-write →
   `os.remove(live_master)` → `os.rename(temp, live_master)` — an interval existed where the canonical path
   did not exist, and a rename failure after deletion could leave the Master missing. Replaced with a
   genuine Windows `MoveFileExW` (`MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH`) call — no pre-delete
   of the destination, no interval where it is missing, and a failure leaves the destination completely
   untouched.
2. **Narrowed live-mutation API.** The old `install_generation(master_path, expected_current_sha256,
   new_bytes, ...)` accepted arbitrary caller-supplied replacement bytes. Now the ONLY sanctioned public
   operations are `perform_g1_to_g2_replacement()` (constructs G2 internally as exactly G1+LF — no caller
   bytes reach the live Master) and `perform_g2_to_g1_restoration()` (refuses BEFORE any write if the
   proposed G1 backup does not hash to the exact pinned canonical G1). The old generic primitive is now
   private. `remove_exact_sidecar()` now also rejects any basename containing path separators, a drive/colon,
   or `.`/`..` traversal.
3. **Replaced the impossible human I2 arming window.** The old design required the operator to manually
   invoke the checkpoint again "before target 1" — with `DEFER_MS=100` for the first target and
   `CONTEXTUALIZER_TARGET_CALLBACK_DEFER_MS=0` for later ones, that window does not exist for a human. I2
   arming is now a **retained, bounded Qt timer/observer** (`_I2PrearmObserver`, ~25ms poll interval,
   5-second timeout), installed **before** the operator ever starts the command. It detects the newly-created
   run instance, mechanically validates it is exactly the expected run, installs the wrapper, and persists
   immutable evidence — all asynchronously, never claimed from timing reasoning alone.
4. **Every consequential stage now re-gates identities/state.** i1_02, i1_03, i1_04, i2_00, and i2_02 all now
   independently re-verify production/runtime/fixture identity, guard/run-lock state, and the live Master
   generation — never relying on "baseline passed earlier" for a fact that can change.
5. **No `eval()` anywhere.** The G1 cache key is reconstructed directly from its own stored components
   (G1 SHA, shot9 fold set, consumer kind), never from a `repr()` string passed through `eval()`.
6. **Exact G2 publication evidence.** i1_03's "G2 ready" gate previously accepted ANY
   `sfm_master_*.sfmsidecar` file as sufficient (G1's own sidecar already satisfied that). It now consumes
   and mechanically verifies the EXACT immutable publication record the external, repo-side
   `I_Generation_Publisher.py` writes (generation basename, exact sidecar SHA, exact manifest SHA/fields) —
   "any sidecar exists" is never sufficient again.
7. **Proven G1/G2 semantic equivalence.** `I_Generation_Publisher.check_only_source()` now also returns
   semantic counts (groups/occurrences/fold-families) and a deterministic semantic digest, computed directly
   from the already-accepted compiler's own parsed result (no new parser). `compare_semantic_parity()` proves
   G1 and G2 are semantically identical despite different SHA-256.
8. **Restoration is mandatory before `I_PASS`.** The final rollup's own `final_i_verdict` is now
   `I_RUNTIME_PASS_RESTORATION_REQUIRED` immediately after I1+I2 succeed, and only becomes `I_PASS` after a
   new, final, read-only snapshot (`i_08_finalize_verify`) independently confirms the external finalizer's
   own restoration record reports `exact_match=True`.
9. **Recovery exists for every post-mutation stop.** `I_Generation_Publisher.finalize_restoration()` is
   usable even if I2 never began — it handles the live Master safely (already-G1 ⇒ no rewrite; exact-G2 ⇒
   restore; anything else ⇒ STOP), republishes G1, removes only the exact recorded G2 sidecar, and requires
   exact-match against the pre-I baseline.
10. **Fail-closed `main()`-stripping.** The offline suite's own stripping logic previously used a non-fatal
    `expect()` that let execution continue past a `[FAIL]` straight into a dangerous `exec()` — this is
    exactly what caused the round-1 offline incident (see the round-1 review bundle's own
    `OFFLINE_MAIN_EXECUTION_INCIDENT.txt`). `strip_trailing_main_call()` now normalizes CRLF→LF and **raises
    immediately**, before any `exec()` is attempted, if the trailing call cannot be located.
11. **Unambiguous external Python-3 publisher path.** `I_Generation_Publisher.py` is now a **separate,
    repo-side-only** file, never copied to the live MAINMENU directory, requiring an explicit, validated
    `--repo-root` (checked to actually contain `tools/sfm_master_sidecar/publisher.py` before anything else
    is attempted) rather than a relative-path guess from its own file location.

## Correction round 2 — eight blockers fixed before any real-SFM run

A second independent review found round 1's own documentation **factually wrong**: it claimed `publish-g2`
performed the live G1→G2 Master replacement. It never did, and never called `perform_g1_to_g2_replacement()`
— the documented sequence would have left the live Master at G1 and caused I1-03 to fail. This round
restructures the publisher into an explicit two-phase design and hardens five further blockers.

1. **Documented `publish-g2` never activated the live Master — now an explicit two-phase design.**
   **Phase A** (`prepare_and_publish_g2()` / CLI `prepare-publish-g2`) constructs G2, writes an immutable
   plan record, publishes the G2 sidecar, and writes the immutable publication record — **never touches the
   live Master**. **Phase B** (`activate_g2_master()` / CLI `activate-g2`) is the **only** function in this
   entire deliverable that ever calls `perform_g1_to_g2_replacement()`; it binds paths to the I1 baseline,
   verifies the live Master is currently exact G1, re-derives G2 from the *current* live G1 bytes, confirms
   the recorded G2 authority artifact exists and matches, then performs the one sanctioned atomic
   replacement and writes an immutable **activation record**. I1-03/I2-00/I2-01 now all require **both** an
   exact valid publication record **and** an exact valid activation record — a published sidecar alone is
   never sufficient again.
2. **No manually-prepared `--g2-source` file.** `construct_and_write_g2_source()` builds G2 **itself**, from
   exact canonical G1 bytes; the `--g2-source` CLI argument is gone entirely.
3. **I2 prearm now re-gates the full governing identity.** `_snapshot_i2_01_prearm()` previously did **not**
   call `_common_identity_gates()`. It now does, plus: both evidence-chain records (publication *and*
   activation), zero open providers/leases, and a **hash-verified** (not merely existence-checked) G1
   backup — all before the observer is ever installed. Any failure: `INCONCLUSIVE_BEFORE_EXECUTION`, observer
   NOT installed.
4. **Prearm timeout raised from 5s to 60s.** `_PREARM_TIMEOUT_MS` is now `60000` (poll cadence unchanged at
   `25ms`) — round 1's 5-second window required the operator to navigate the SFM menu and scope dialog
   inside five seconds. The longer window does not weaken the proof that the wrapper armed strictly before
   target 1; that proof is still the observer's own persisted evidence.
5. **Live-mutation paths are bound to the I1 baseline.** `I_Generation_Helper.path_matches_baseline()`
   (normalized, case-insensitive absolute-path comparison) is now checked, **before any write**, by
   `activate_g2_master()`, `finalize_restoration()`, and the checkpoint's own I2 wrapper
   (`_install_i2_wrapper()`) — a wrong/arbitrary `--master` or `--authority-dir` argument is never sufficient
   authorization by itself; the baseline inventory is the qualification's own path authority.
6. **Baseline inventory is its own standalone, immutable artifact.** i1_01 now writes
   `sfm_checkpoint_i_baseline_inventory.json` (write-once, round-trip verified against the embedded value) in
   addition to the snapshot/continuation-state copies. `i_08_finalize_verify` now consumes this **file**
   directly — never the operator manually extracting nested JSON from Snapshot 01, and never only this
   process's own in-memory continuation state.
7. **An immutable plan record exists before the first live authority mutation.**
   `write_g2_plan_record()` computes and writes an immutable PLAN record — canonical G1 SHA, expected G2 SHA,
   expected semantic parity, the expected sidecar SHA-256 and generation basename (both independently
   derivable from the already-accepted `check_only()` operation's own `ordinary_sha256`, since
   `manifest.py` sets `sidecar_sha256 = outcome.ordinary_sha256` — confirmed by direct source inspection, so
   this is the *real* eventual sidecar identity, never a guess) — **before** `publish_generation()` ever
   writes into the authority directory. A failure during publication therefore never leaves recovery
   dependent on a record that had not yet been created.
8. **Finalizer independently re-verifies the publication record before it may authorize sidecar deletion.**
   `finalize_restoration()` now re-derives `SHA(G1+LF)` and compares it to the record's own `g2_source_sha256`,
   confirms the basename is safe, confirms the exact on-disk sidecar SHA still matches, and confirms the
   recorded semantic parity is `True` — **before** ever calling `remove_exact_sidecar()`. A tampered or wrong
   publication record can no longer authorize a deletion merely because the file exists; Master restoration
   itself is unaffected (it never depended on the sidecar-deletion decision).

## Correction round 3 — five blockers + one hardening fixed before any real-SFM run

A third independent review accepted the round-2 architecture but found it still not authorized for
deployment.

1. **Phase A authority mutation was NOT baseline-path-bound.** Phase A publishes a sidecar and replaces
   `manifest.json` — that is itself a live mutation, but `prepare_and_publish_g2(... output_dir ...)` could
   publish into an arbitrary caller-supplied directory. `write_g2_plan_record()` now ALSO requires the I1
   baseline inventory, validates its own recorded `master_sha256` equals canonical G1, and records both the
   baseline Master path and baseline authority path **into the plan itself**. `publish_g2_with_record()`
   binds the caller's actual `output_dir` to the plan's own recorded baseline authority path **before**
   `publish_generation()` is ever permitted to run — a wrong `output_dir` STOPs before the first
   authority-directory write, creating/modifying nothing there.
2. **Recovery required the publication record, which could be the exact thing a partial failure destroyed.**
   The old order was plan record → `publish_generation()` mutates authority → publication record written
   afterward — so a failure writing the publication record could leave an exact G2 sidecar present, a
   manifest possibly activated to G2, and NO publication record. `finalize_restoration()` now takes an
   explicit `plan_record` parameter (the plan record survives exactly this failure window, since it is
   written **before** any authority mutation) and can recover using the plan record **alone** —
   `publication_record` is now optional (may be `None`).
3. **Master restoration trusted the publication record for G2 identity.** The old finalizer read
   `expected_g2_sha = publication_record["g2_source_sha256"]` before even validating the record — a
   corrupt/tampered publication record could have blocked a safe restoration. `finalize_restoration()` now
   independently re-derives `derived_g2_bytes = construct_g2_bytes(g1_bytes)` from the G1 bytes it already
   verified, and treats the live Master as G2 **only** if it equals this independently re-derived hash —
   never the record's own claim. The new `_determine_sidecar_removal()` then recovers the sidecar's own
   identity from **either** record independently (plan or publication), and refuses outright — never
   guessing — if the two disagree on that identity.
4. **The SFM-deployable helper's own CLI bypassed the baseline-path authority.** `I_Generation_Helper.py`
   still exposed `advance-g1-to-g2`/`restore-g2-to-g1`/`remove-sidecar` as CLI subcommands, none of them
   path-bound — an unbound mutation escape hatch alongside the real, path-bound orchestration. Its CLI now
   exposes **only** `inventory`/`compare` (both read-only); the underlying Python functions remain (called
   in-process by the publisher and by this checkpoint's own I2 wrapper). `activate_g2_master()` is now
   literally the only external G1→G2 activation surface.
5. **`i_08_finalize_verify` is unreachable for an early-aborted campaign.** It is schedule position 8 —
   naturally reachable only after snapshots 1–7 have run in sequence — so "run the checkpoint again for
   i_08 after any post-G2 stop" was false for a campaign that aborted earlier (e.g. I1 failed at i1_02, or
   i1_03 never passed). A new, separate, read-only tool, `Checkpoint_I_Restoration_Verify.py`, exists
   specifically for that case (see the new Restoration/Recovery section below) — it never advances or
   depends on the primary continuation state.
6. **R3 HARDENING**: `_validate_g2_publication_record()` now also mechanically requires the record's own
   recorded `semantic_parity` to report `all_parity_checks_pass=True` (Phase A already required this
   internally — the consumer now verifies it too, rather than merely assuming the producer succeeded), and
   corroborates the active manifest's current on-disk SHA-256 against the record's own
   `manifest_sha256_after_publication`.

## Scope

`I` establishes two separate propositions, and ONLY these:

- **I1 — a later command adopts a new generation.** Command A completes under G1; while SFM sits idle, the
  Master is legitimately replaced with G2 and a matching G2 sidecar is published; command B (same shot,
  same process) must pin/acquire G2 and complete entirely under G2 — the earlier G1 authority must never
  remain valid for command B.
- **I2 — an active command cannot straddle generations.** A command begins under G2, completes target 1,
  and — before target 2 resumes — the live Master is changed back to G1. The active command must fail
  closed (its pinned generation is still G2); it must never silently reacquire G1 or continue using G2
  authority against a now-G1 Master; target 2 must never reach native Rebuild.

Governing invariant: **one command = one Master generation; a later command may adopt a later generation,
an active command may not.**

This is explicitly **not** another later-vocabulary test (that is `G`, PASS/CLOSED — see
`../checkpoint_g_later_vocabulary/`). I1 deliberately reuses the same shot (`shot9`) for both commands so
vocabulary is never a variable — only the Master generation changes.

## Roles (this checkpoint is NOT a pure read-only observer like G's own)

- **I1 (snapshots i1_01 – i1_04)**: a pure read-only observer, exactly like `Checkpoint_G_Later_Vocabulary.py`.
  It never invokes the Normalizer, never invokes native Rebuild, never mutates the scene, never opens a
  provider, never saves. The G1↔G2 Master swap and sidecar publish/finalize is performed by a **separate,
  external, ordinary Python 3 invocation of the repo-side-only `I_Generation_Publisher.py`**, outside SFM,
  while SFM sits idle — never by this checkpoint.
- **I2 prearm (i2_00, i2_01)**: i2_00 is a pure read-only baseline. **i2_01 ("prearm") installs a retained,
  bounded Qt timer/observer** — never blocks, never busy-waits — that will, asynchronously and entirely in
  the background, locate the live command instance the MOMENT it appears, mechanically validate it, install
  the wrapper, and persist immutable arming evidence.
- **I2 verify (i2_02)** and **the final restoration check (i_08)** are again pure read-only observers, run
  only after the relevant real-world action (the command finishing; the external restoration) has already
  happened.

## Architecture facts this design relies on (independently verified by direct source inspection)

- `self.master_hash` is set once, inside `derive_paths()` (called synchronously from `start()`, lines
  ~9878-9886, ~13949), well before `start()` eventually reaches `activate_next_shot()` and returns control
  to Qt — so by the time ANY Qt timer could fire, `master_hash` is already set.
- `DEFER_MS = 100` (line 136) is the delay used to schedule the FIRST shot's own deferred entry callback;
  `CONTEXTUALIZER_TARGET_CALLBACK_DEFER_MS = 0` (line 137) is the delay used for every LATER target's resume
  callback. `start()` itself runs entirely synchronously and is substantially longer than one ~25ms observer
  poll interval, so a retained observer polling every ~25ms, started BEFORE the operator invokes the
  command, is already overdue (multiple poll opportunities already elapsed) by the time control first
  returns to Qt and the 100ms first-target timer even begins counting down.
- `RebuildControlGroupsProductionRun.__init__` (lines ~9464-9520) initializes `self.current_target_index =
  0`, `self.telemetry_native_attempts = 0`, `self.total_native_rebuilt = 0`, `self.scope_mode`,
  `self.scope_shots`, `self.requested_scope_class`, ALL synchronously at construction, and
  `self.setObjectName(RUN_LOCK_NAME)` — so a newly-detected instance's exact scope/progress can be validated
  immediately, before any target has run.
- `contextualizer_resolve_resume_target(self, record, target)` calls `self.assert_master_stable()` as its
  first action, and is called exactly once per target (including target 1) from `process_current_target()`
  (lines ~12722-12727, ~12922-12957) — never skipped, never batched.
- `process_current_target()`'s own try/except (lines ~12926-13034) catches any exception raised inside it
  and calls `self.abort("Exception during CONTEXTUALIZER target-level Qt callback transaction: %r" % exc)`,
  eventually reaching `final_report(False)` — production itself detects and fails closed; this checkpoint
  only observes the resulting log.
- the per-target native-Rebuild window logs `"...phase=PRE_NATIVE..."` then, after `self.rebuild(...)`,
  `"NATIVE_REBUILD_RETURNED = PASS"` (lines ~11882-11937) — each exactly once per target that reaches it.
- the live Master SHA-256 is logged once per command: `"live Master SHA256=%s" % self.master_hash` (line
  ~13978).
- the broker's own `invalidate_generation()` (`view_cache.py`) marks stale — via each view's shared
  `LiveAuthorizationToken` — every cached view of a superseded generation; it does not evict them. A stale
  view becomes unreachable via `broker.cached_view()` once a newer generation is acquired.
- the official sidecar compiler/publisher (`tools/sfm_master_sidecar/publisher.py`, **Python 3 only**,
  imported ONLY from `I_Generation_Publisher.py` — never from the SFM-side files) is the same real, accepted
  code used to publish the live G1 generation originally.

## Files

- `Checkpoint_I_Generation_Replacement.py` — SFM-side (Python 2.7.5), deployed to MAINMENU. Runs the 8-step
  I1/I2/finalize-verify schedule.
- `I_Generation_Helper.py` — **SFM-deployable core**, dual Python 2.7.5 / Python 3 compatible, deployed to
  MAINMENU alongside the checkpoint. Contains only the narrow, hash-gated primitives
  (`perform_g1_to_g2_replacement`, `perform_g2_to_g1_restoration`, `capture_live_state_inventory`,
  `compare_inventories`, `remove_exact_sidecar`, `is_safe_bare_basename`, `construct_g2_bytes`,
  `path_matches_baseline` (R2 BLOCKER 5), `read_manifest_source_sha256_plain`,
  `read_publication_record_plain`, `read_finalization_record_plain`). Has **zero reference** to
  `tools/sfm_master_sidecar` (BLOCKER 11). Its own CLI exposes **only** `inventory`/`compare` (both
  read-only) — no mutation subcommand at all (R3 BLOCKER 4).
- `I_Generation_Publisher.py` — **repo-side only, Python 3 only, never deployed to MAINMENU.** Imports
  `I_Generation_Helper.py` as a sibling and the real, accepted `tools/sfm_master_sidecar` package via an
  explicit, validated `repo_root`. Two-phase design (R2 BLOCKER 1): **Phase A** —
  `construct_and_write_g2_source`, `write_g2_plan_record` (the pre-mutation plan record, now also
  baseline-path-bound, R2 BLOCKER 7 / R3 BLOCKER 1), `publish_g2_with_record` (re-derives everything fresh
  against the plan and binds `output_dir` to the plan's own recorded baseline authority path before any
  authority write, R3 BLOCKER 1), and `prepare_and_publish_g2` (chains all three; never touches the live
  Master). **Phase B** — `activate_g2_master` (the *only* function in this entire deliverable that ever
  calls `perform_g1_to_g2_replacement`; binds paths to the baseline, R2 BLOCKER 5). Also provides
  `check_only_source` (with semantic counts/digest), `compare_semantic_parity`, and `finalize_restoration`
  (the mandatory closure step; now takes an explicit `plan_record` parameter and can recover using it
  ALONE, `publication_record` is optional, R3 BLOCKER 2; independently re-derives G2 identity as G1+LF
  rather than trusting the publication record, R3 BLOCKER 3; pre-delete revalidation, R2 BLOCKER 8).
- `Checkpoint_I_Restoration_Verify.py` — **NEW (R3 BLOCKER 5).** SFM-side (Python 2.7.5), deployed to
  MAINMENU alongside the checkpoint. A separate, read-only, one-shot recovery-verification tool for an
  EARLY-ABORTED I1/I2 campaign (one that never reaches the primary checkpoint's own scheduled
  `i_08_finalize_verify`, which is schedule position 8). Never reads, advances, or writes the primary
  continuation state.
- `test_checkpoint_i_generation_replacement_dryrun.py` — the main offline suite, run under the real embedded
  Python 2.7.5 (execs the checkpoint's own Python-2-only source; can never itself run under Python 3). Also
  execs `Checkpoint_I_Restoration_Verify.py`'s own source, via the same fail-closed stripping technique.
- `test_i_generation_publisher_py3.py` — a separate Python-3-only test for `I_Generation_Publisher.py`
  (renamed from `test_i_generation_helper_publisher_py3.py`, since the functions it tests moved out of
  `I_Generation_Helper.py` per BLOCKER 11).

## G2 construction

G2 changes generation **identity** without materially changing Master **semantics**: exact G1 bytes plus
exactly one trailing ASCII LF (`0x0A`) byte. Deterministic, reversible, and its SHA-256 is computable offline
before ever writing anything. `perform_g1_to_g2_replacement()` constructs G2 **internally** this way — no
caller-supplied replacement bytes ever reach the live Master (BLOCKER 2). G1/G2 semantic equivalence is
proven via `compare_semantic_parity()` (BLOCKER 7) before any publication is attempted.

G2 is **not** created or installed in the live SFM tree during this preparation task.

## Generation helper safety contract

- `perform_g1_to_g2_replacement(master_path, expected_g1_sha256)`: current live Master **must** hash exactly
  to G1; G2 is constructed internally; refuses (no write) on any mismatch.
- `perform_g2_to_g1_restoration(master_path, g1_backup_bytes, expected_g2_sha256)`: current live Master
  **must** hash exactly to G2, **and** the proposed G1 backup bytes must hash exactly to the pinned canonical
  G1 SHA-256 — a tampered/wrong backup is refused **before** touching the live Master.
- Every mutation is a genuine OS-backed atomic replacement (`MoveFileExW`,
  `MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH`) — never a remove-then-rename sequence; a failure
  leaves the destination completely untouched (BLOCKER 1).
- `remove_exact_sidecar()` requires a **safe bare basename** (no separators, no drive/colon, no `.`/`..`)
  **and** an exact expected SHA-256, re-verified immediately before deletion — never a wildcard.
- Every operation returns a structured record (pre-hash, post-hash, source-bytes hash, timestamp, operation
  type, success/failure) — never a bare boolean.
- `path_matches_baseline(actual_path, baseline_path)` (R2 BLOCKER 5): normalized, case-insensitive absolute-
  path comparison, checked before any write by `activate_g2_master()`, `finalize_restoration()`, and the
  checkpoint's own I2 wrapper — a wrong/arbitrary Master or authority-directory path is never sufficient
  authorization by itself.

## Pre-I live-state inventory

Before any live I run, `capture_live_state_inventory(master_path, authority_dir)` must record an immutable
baseline: exact canonical Master bytes/hash/size, exact `manifest.json` bytes/hash, and every `.sfmsidecar`
filename/size/SHA-256 in the shipped authority namespace. This becomes the restoration target. i1_01 now
ALSO writes this inventory as its own standalone, write-once artifact
(`sfm_checkpoint_i_baseline_inventory.json`, R2 BLOCKER 6) — round-trip verified against the value embedded
in the snapshot itself. Every subsequent live-mutation/finalization operation binds its
`--master`/`--authority-dir` arguments to the paths recorded in this exact artifact via
`I_Generation_Helper.path_matches_baseline()` (R2 BLOCKER 5) — the baseline inventory is the qualification's
own path authority; an arbitrary/wrong path is never sufficient authorization by itself.

## I1 checkpoint contract (real-SFM sequence)

1. **RESTART SFM.** Open only `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx`.
2. Run `Checkpoint_I_Generation_Replacement.py`. **[Snapshot i1_01 — baseline G1.]** Confirm
   `classification = I1_BASELINE_PASSED`. If `INCONCLUSIVE_BEFORE_EXECUTION`, **STOP** — report `failed_gates`
   — do not run command A.
3. Invoke **Rebuild Control Groups → Selected Shot(s) → `shot9`** only. Let it complete.
4. Run the checkpoint again. **[Snapshot i1_02 — after G1 command.]** Confirm
   `classification = I1_G1_STAGE_PASSED`. If `FAIL`, **STOP** and report `failed_gates`. Phase A has not run,
   so neither the authority namespace nor the live Master has been changed by `I`; no restoration/
   finalization command is required.
5. **With SFM left open and idle**, from an ordinary Python 3 shell **outside SFM**, from the repository
   root, run **Phase A** — prepare + publish the G2 authority (never touches the live Master):
   ```
   python I_Generation_Publisher.py --repo-root <repo-root> prepare-publish-g2 \
       --g1-source <path to a byte-identical G1 copy> \
       --g2-source-out <evidence path>/sfm_checkpoint_i_generated_g2_source.txt \
       --plan-out <evidence path>/sfm_checkpoint_i_g2_plan_record.json \
       --output-dir <live usermod/cfg/sfm_shared_authority path> \
       --record-out <evidence path>/sfm_checkpoint_i_g2_publication_record.json \
       --baseline-inventory <evidence path>/sfm_checkpoint_i_baseline_inventory.json
   ```
   G2 is constructed **internally** — never supply a manually-prepared `--g2-source` file (R2 BLOCKER 2).
   `--baseline-inventory` is the standalone artifact i1_01 itself wrote (R2 BLOCKER 6); the plan record
   records its own recorded baseline Master/authority paths, and publication refuses a wrong `--output-dir`
   **before** the first authority-directory write (R3 BLOCKER 1). This writes the immutable plan record
   (before any authority-directory write, R2 BLOCKER 7) and the immutable publication record. **The live
   Master is still exactly G1 after this step.**
5b. Now run **Phase B** — activate the live G2 Master (the only step that ever mutates it):
   ```
   python I_Generation_Publisher.py --repo-root <repo-root> activate-g2 \
       --master <live Master path> --authority-dir <live usermod/cfg/sfm_shared_authority path> \
       --baseline-inventory <evidence path>/sfm_checkpoint_i_baseline_inventory.json \
       --publication-record <evidence path>/sfm_checkpoint_i_g2_publication_record.json \
       --out <evidence path>/sfm_checkpoint_i_g2_activation_record.json
   ```
   This binds `--master`/`--authority-dir` to the I1 baseline inventory (R2 BLOCKER 5; a mismatch STOPs with
   no write), re-derives G2 from the *current* live G1 bytes, confirms the recorded G2 sidecar exists and
   matches, then performs the one sanctioned, hash-gated, atomic `perform_g1_to_g2_replacement` and writes
   the immutable activation record. **Only after this step is the live Master actually G2.**
6. Run the checkpoint again. **[Snapshot i1_03 — G2 ready.]** Confirm `classification = I1_G2_READY`. This
   now REQUIRES both the publication record **and** the activation record (R2 BLOCKER 1) — a published
   sidecar with no activation record is `INCONCLUSIVE_BEFORE_EXECUTION`. If `INCONCLUSIVE_BEFORE_EXECUTION`,
   **STOP** — do not run command B — proceed to Recovery below.
7. Invoke **Rebuild Control Groups → Selected Shot(s) → `shot9`** again, in the **same SFM process**.
8. Run the checkpoint again. **[Snapshot i1_04 — after G2 command.]** Confirm `classification = I1_PASS`. If
   `FAIL`, report `failed_gates` — this indicates a genuine authority-behavior defect. Either way, once G2
   has been installed, Restoration (below) is now mandatory before `I` can close.

**Do not restart SFM between steps 3 and 8** — I1 specifically requires one unchanged process across the
generation swap.

## I2 checkpoint contract (real-SFM sequence, continuing from I1's own G2 state)

9. **RESTART SFM** (a fresh process). Open the same fixture. The live Master remains G2 (left there by I1's
   own campaign — do not swap it back before I2).
10. Run the checkpoint. **[Snapshot i2_00 — baseline G2.]** Confirm `classification = I2_BASELINE_PASSED`
    (guard `UNUSED`, live Master == G2 with a valid publication record **and** a valid activation record — R2
    BLOCKER 1, `shot3` resolves uniquely with ≥2 animation sets). If `INCONCLUSIVE_BEFORE_EXECUTION`, **STOP**.
11. Run the checkpoint again. **[Snapshot i2_01 — prearm.]** This now re-gates the FULL governing identity
    (production/runtime/fixture, both evidence-chain records, zero open providers/leases, a hash-verified G1
    backup — R2 BLOCKER 3) before installing the retained observer, and returns immediately. Confirm
    `classification = PREARM_INSTALLED`. If `INCONCLUSIVE_BEFORE_EXECUTION`, **STOP**.
12. **Now** invoke **Rebuild Control Groups → Selected Shot(s) → `shot3`** — the operator has up to **60
    seconds** (R2 BLOCKER 4) to do so. Do nothing further — the observer (already running in the background
    since step 11) will detect the new run instance, validate it, and install the wrapper before target 1,
    entirely on its own. Target 1 completes unaffected; target 2 triggers the wrapper's G2→G1 restore (path-
    bound to the I1 baseline, R2 BLOCKER 5) and production's own, unmodified stability check. The command
    finishes on its own with an explicit `PRODUCTION_REBUILD_CONTROL_GROUPS = FAIL`.
13. Run the checkpoint one more time. **[Snapshot i2_02 — verify.]** Confirm
    `classification = I2_FAIL_CLOSED_PASS`. This REQUIRES the observer's own persisted arming evidence (never
    timing reasoning) proving the wrapper was installed before target 1. If `FAIL`, report `failed_gates`.

## Restoration / recovery (MANDATORY once G2 has been installed — BLOCKER 8/9)

Applies after ANY stop past step 5 (Phase A), whether I1 completed, I1 failed mid-way, or I2 never began.
**If I1 fails before step 5 ever runs (no G2 authority/Master mutation has occurred at all), no restoration
command and no restoration-verification run are necessary — the live Master was never touched (R3 BLOCKER
5).**

1. Close SFM.
2. From the same Python 3 shell, from the repository root, run:
   ```
   python I_Generation_Publisher.py --repo-root <repo-root> finalize \
       --master <live Master path> --authority-dir <live shipped-authority path> \
       --g1-source <path to a byte-identical G1 copy> \
       --plan-record <evidence path>/sfm_checkpoint_i_g2_plan_record.json \
       --publication-record <evidence path>/sfm_checkpoint_i_g2_publication_record.json \
       --baseline-inventory <evidence path>/sfm_checkpoint_i_baseline_inventory.json \
       --out <evidence path>/sfm_checkpoint_i_finalization_record.json
   ```
   `--baseline-inventory` is the standalone artifact i1_01 itself wrote (R2 BLOCKER 6) — never manually
   extracted nested JSON from Snapshot 01. `--plan-record` and `--publication-record` are both optional
   (omit whichever does not exist) — `finalize_restoration()` can recover using the **plan record alone**
   if the publication record was never written or its own write failed after Phase A had already mutated
   the authority directory (R3 BLOCKER 2). `finalize_restoration()` first binds `--master`/`--authority-dir`
   to the baseline (R2 BLOCKER 5; a mismatch STOPs with no write), then independently RE-DERIVES G2 as
   `G1+LF` from the G1 bytes it just verified — never from either record's own claimed hash (R3 BLOCKER 3) —
   and treats the live Master as G2 only if it matches that re-derived hash. It then handles the current
   Master safely (already-G1 ⇒ no rewrite; exact re-derived-G2 ⇒ restore; anything else ⇒ STOP with no
   write), republishes G1, and recovers the orphaned G2 sidecar's own identity from **either** record
   independently (never guessing when the two disagree, R3 BLOCKER 3) before removing it, and requires the
   final live inventory to exactly equal the pre-I baseline.
3. **If the campaign reached `I1_PASS` + `I2_FAIL_CLOSED_PASS`** (the intended, successful case): reopen SFM
   (fresh restart) with the same fixture and run the PRIMARY checkpoint. **[Snapshot i_08 —
   finalize-verify.]** Confirm `classification = RESTORATION_CONFIRMED` — this independently re-verifies
   live Master == exact G1 AND re-derives its own fresh inventory comparison against the baseline, never
   merely trusting the external record's own claim. Only once `i_08` reports `RESTORATION_CONFIRMED` does
   the checkpoint's own `final_i_verdict` (in `sfm_checkpoint_i_final_result.json`) become `I_PASS`. Before
   that, if I1+I2 both succeeded, it reads `I_RUNTIME_PASS_RESTORATION_REQUIRED` — never `I_PASS`
   prematurely.
4. **If the campaign ABORTED EARLY** (never reached `I1_PASS` + `I2_FAIL_CLOSED_PASS` — e.g. I1 failed at
   i1_02, or i1_03 never passed): **do NOT** run the primary checkpoint expecting to reach i_08 — it is
   schedule position 8, naturally reachable only after snapshots 1–7 have run in sequence, so the primary
   continuation state will still be sitting wherever the abort left it (R3 BLOCKER 5). Instead, reopen SFM
   (fresh restart) with the same fixture and run the new, separate
   **`Checkpoint_I_Restoration_Verify.py`**. Confirm `classification = RESTORATION_CONFIRMED` in its own
   `sfm_checkpoint_i_restoration_verify_result.json`. This tool never reads, advances, or writes the primary
   continuation state, and never sets `final_i_verdict` — the campaign itself remains
   `I_INCOMPLETE_OR_FAILED` (or whatever the primary rollup already recorded); this step only mechanically
   proves recovery succeeded.

## Exact I1 PASS contract

`I1_PASS` requires, mechanically, at snapshot i1_04: continuity (same PID as baseline); identities correct;
guard `SELECTED_USED`; run lock absent; **live Master still exactly G2**; run-02 log verified with explicit
`PRODUCTION_REBUILD_CONTROL_GROUPS = PASS` and `logged Master SHA256 == G2`; the G2 `shot9` view
present/fresh/exactly-covered/zero-Uncovered; the G1 view no longer a usable cache hit; provider counters +1
open/+1 close since G2-ready; diagnostics delta contains a fresh `cohort_acquired` and excludes
`fully_reused_no_provider_open`; zero outstanding/unreleased leases.

## Exact I2 FAIL-CLOSED PASS contract

`I2_FAIL_CLOSED_PASS` requires, mechanically, at snapshot i2_02: continuity; identities correct; guard
remains `SELECTED_USED`; run lock absent; **live Master now exactly canonical G1** (the injected swap put it
there); the persisted prearm evidence reports `outcome=ARMED` with `no_target_completed_yet`,
`zero_native_attempts_so_far`, `zero_native_rebuilt_so_far`, `scope_shot_matches_expected`, and
`master_hash_matches_g2` all `True` (proving the wrapper was installed before target 1, from real evidence,
never reasoning); the run-03 log shows `FINAL_REPORT_ENTRY`, explicit `= FAIL` (never `= PASS`), the literal
text `"Live Master changed during the run."` and `"Exception during CONTEXTUALIZER target-level Qt callback
transaction"` (production's own detection, never synthetic), exactly one `phase=PRE_NATIVE` and exactly one
`NATIVE_REBUILD_RETURNED = PASS`; the injection evidence records `call_index=2`,
`pre_swap_matches_expected_g2=True`, `swap_performed=True`, and the swap's own post-hash equals G1; the
diagnostics delta since arming contains exactly one `cohort_acquired`; zero outstanding/unreleased leases.

## Final I mechanical verdict

`I` closes only if **all three** hold: `I1_PASS`, `I2_FAIL_CLOSED_PASS`, and
`i_08_finalize_verify == RESTORATION_CONFIRMED`. The checkpoint's own `sfm_checkpoint_i_final_result.json`
exposes `i1_verdict`, `i2_verdict`, `finalize_verdict`, and `final_i_verdict` directly.

## Evidence-file discipline

Matches this project's established convention: every snapshot/run is written to a new, uniquely-numbered,
immutable file (`write_evidence_json_once` / `write_evidence_bytes_once`, refuse-to-overwrite); only the
small continuation-state pointer file and the freely-overwritten final rollup are ever replaced. Before any
live run, the operator must confirm no pre-existing `sfm_checkpoint_i_*` files exist in the evidence
directory (a prior attempted campaign's leftovers must be reported, never silently overwritten or deleted).

## Offline qualification already performed (before this correction was prepared)

- `test_checkpoint_i_generation_replacement_dryrun.py` — **174/174 PASS** under the real embedded Python
  2.7.5 (up from round 2's 149/149). Round 1/round 2's own coverage (see below) remains fully intact and
  re-confirmed passing. New this round: a static proof that the deployed helper's own CLI exposes only
  `inventory`/`compare`, with the three forbidden mutation-subcommand literals confirmed absent (R3
  BLOCKER 4); a static proof, via `SNAPSHOT_SCHEDULE` indexing, that `i_08_finalize_verify` is reachable
  ONLY at index 8, never earlier (R3 BLOCKER 5); a full offline harness for the NEW
  `Checkpoint_I_Restoration_Verify.py` (mirroring `fresh_ns()`), proving its happy path
  (`RESTORATION_CONFIRMED`), its refusal without the baseline-inventory artifact, its refusal when the
  live Master is not exactly canonical G1, and that it never writes the primary continuation-state file at
  all (R3 BLOCKER 5); and a publication record whose own recorded `semantic_parity.all_parity_checks_pass`
  is `False` correctly refusing at i1-03 (R3 HARDENING). Round 1's own coverage (fail-closed
  `strip_trailing_main_call` regressions, BLOCKER 10; the real `MoveFileExW` atomic-replacement path
  including a simulated failure, BLOCKER 1; the narrowed G1/G2 mutation API including a tampered-backup
  refusal, BLOCKER 2; `is_safe_bare_basename()` rejections, BLOCKER 2; every consequential stage's own
  re-gating, BLOCKER 4; no `eval(` call anywhere, BLOCKER 5; exact G2 publication-record consumption at
  i1-03, BLOCKER 6; the real PySide `QTimer`-driven prearm observer, BLOCKER 3; `i_08_finalize_verify`'s
  own independent re-verification and `main()`'s `final_i_verdict` aggregation, BLOCKER 8) and round 2's
  own coverage (full identity re-gating at `_snapshot_i2_01_prearm()`, R2 BLOCKER 3; the dedicated
  I2-baseline test section and its activation-record requirement, R2 BLOCKER 1; the `_PREARM_TIMEOUT_MS`
  regex proof, R2 BLOCKER 4; the I2 wrapper's own path-binding refusal, R2 BLOCKER 5; the standalone
  baseline-inventory artifact, R2 BLOCKER 6) both remain fully intact and re-confirmed passing.
- `test_i_generation_publisher_py3.py` — **139/139 PASS** (up from round 2's 107/107) under a real Python 3
  interpreter against the REAL, accepted `tools/sfm_master_sidecar` publisher. Round 1/round 2 coverage (`validate_repo_root()` refusing a fake
  root, BLOCKER 11; semantic counts/digest proving G1/G2 parity, BLOCKER 7; the full publication record's
  required fields, BLOCKER 6; `activate_g2_master()` actually changing the live Master to G2 and its own
  path-binding adversarial refusals, R2 BLOCKERS 1/5; two tampered-publication-record cases refusing
  sidecar deletion while Master restoration still succeeds, R2 BLOCKER 8) remains intact. New this round:
  `write_g2_plan_record()` refusing a baseline whose own recorded `master_sha256` is not canonical G1, and
  recording the baseline's own Master/authority paths into the plan (R3 BLOCKER 1); `publish_g2_with_
  record()` refusing a wrong `output_dir` before `publish_generation()` ever runs, creating/modifying
  nothing there and leaving the real, plan-recorded authority namespace untouched (R3 BLOCKER 1);
  `finalize_restoration()` recovering using the plan record ALONE (`publication_record=None`) for both "the
  publication-record write itself failed" and "the publication record is simply absent after a partial
  Phase-A mutation," with no live Master activation ever occurring in either case (R3 BLOCKER 2); a
  tampered publication-record `g2_source_sha256` failing to prevent Master restoration, with the
  independently-verified plan record still permitting authority cleanup since the tamper does not touch
  the sidecar's own identity fields (R3 BLOCKER 3); and a plan/publication disagreement on the sidecar's
  own identity correctly failing closed for destructive cleanup while leaving Master restoration unaffected
  (R3 BLOCKER 3).

## Explicit non-authorization

This preparation does not modify production, the authority runtime/broker/cache implementation, or the
canonical Master. It does not create, install, or publish G2 in the live SFM tree. It does not run SFM. It
does not stage, commit, or push. **The real-SFM I campaign has not been run.**
