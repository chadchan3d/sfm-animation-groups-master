# CPM Real-SFM Session 1 — first run, reconciled evidence

**Sources:**
- probe `CPM_Session1_Probe.jsonl`: 11 records, probe v1, SHA `d7f16fac…`;
- the CPM log `SFM_CSP_G18AN_SaveNewCopy.log`;
- the production Normalizer's log `sfm_rebuild_control_groups.txt` (path defined in its source;
  it holds the latest run only);
- the owner's notes. No separate run sheet or console file was provided; timestamps are the run
  sheet.

**Deployment:**

| Item | Identity |
|---|---|
| App | `945eab6c…` |
| Adapter | `e96e21b5…` |
| Projection | `9b077a1b…` |
| Normalizer | `1f4ec5a2…` |
| Shared package | canonical 23 files, API `1.0.0-b2a`, build `package-boundary-corrected-2026-09-22` |
| Master | `ac45e5c1…904d93` |

One SFM process throughout (pid 25896, one broker object).

## Reconstructed timeline (2026-09-28)

| Time | Evidence | Event | Intended |
|---|---|---|---|
| 22:56:26 | probe seq 1 | Before CPM: runtime not loaded, no broker; memory read valid | P0 ✓ |
| 23:00:56 | log | CPM opened (pid 25896) | A |
| 23:01:03 | log | Scope for `foxmccouldwm1`: 40 literals, healthy, 0 Master-unknown, `semantic-scope` 1.539 s | A |
| 23:02:03 | log | Switched to `mia1`: 108 literals, healthy, 0 Master-unknown, 1.173 s. Counts: face 58, body 46, other 4, miss 0, conflict 0 | A |
| 23:02:19 | log | Body **Save** "Body": authorized → durable commit → verified | B |
| 23:03:45 | probe seq 2 | Converged app; historical provider 0 opens; leases 0; open providers 0; opens 2 = closes 2; broker `0x30fd2a50` | P1 ✓ |
| 23:05:31 | probe seq 3 | Idle: leases 0, open providers 0 | P2 ✓ |
| 23:06:02 | log | Body **Save** "BodyTest". This is a second Save, **not an Update** | B (Update missing) |
| 23:06:10 | probe seq 4 | Leases 0, open providers 0 | P3 |
| 23:06:21 | log | Expression **Save**: authorized → commit → verified | C |
| 23:06:46 | log | Expression **Update**: authorized → commit → verified | C |
| 23:08:13 | probe seq 5 | Leases 0, open providers 0 | P4 |
| 23:08:55 | log | Body **Apply** committed: 4 sides changed; Undo count before = 59; pinned postcommit `flex_verify ok` | D |
| 23:09:37 | log | Body Apply committed again: Undo count before = **59** again and 4 sides changed again, so Undo had restored the pre-Apply state | D (Undo) |
| 23:09:40, 23:09:45 | log | Two **no-op** Applies: Undo count 71 before = 71 after; "Already matches this preset." | D ✓ |
| 23:10:21 | probe seq 6 | Leases 0, open providers 0 | P5 |
| 23:11:00 | log | **Expression Apply** committed: 1 side changed; pinned postcommit `flex_verify ok` | E ✓ |
| 23:11:19 | probe seq 7 | Leases 0, open providers 0 | P6 |
| 23:13:26 | probe seq 8 | Leases 0, open providers 0. No Review items existed; no Fit was run | P7/P8 (not exercised) |
| 23:13:38 | log | **CPM closed** | — |
| 23:13–23:15 | probe seq 9 | Production Normalizer run #1: provider opens 3 → 4 | H1 |
| 23:15:10 | probe seq 9 | CPM window closed; **same broker `0x30fd2a50`**; consumers served: `cpm_compat_v1` **and** `normalizer_compat`; leases 0 | P9 ✓ |
| 23:15:36 | log | CPM reopened in the **same process**: `mia1` healthy from cache (0.073 s, no provider open); 4 Body Applies committed with pinned postcommit verification | P10 (sequential) |
| 23:15:56 | log | CPM closed | — |
| 23:16:17 | probe seq 10 | Leases 0; opens 4 = closes 4 | — |
| ~23:16 | Normalizer log | Normalizer run #2: `PRODUCTION_REBUILD_CONTROL_GROUPS = PASS`, targets RECONCILED, Undo restored, zero Undo-ledger delta | H4 |
| 23:17:28 | probe seq 11 | Same broker; both consumers; leases 0 | P11 |

Checkpoint numbering: the operator's labels drifted by about one around P3/P4. Timestamps give an
unambiguous mapping, so this is not a failure.

## Verdicts

| Item | Status | Basis |
|---|---|---|
| Startup / canonical scope / historical route unused | **PASS** | health `canonical-admission-and-view-validated`; probe `converged true`; 0 historical opens; 0 historical log lines |
| Idle lease/provider | **PASS** | all 11 probes: leases 0, open providers 0, opens = closes, unreleased registry 0 |
| Body Save | **PASS** | 2 Saves; each authorized before the durable write |
| Body Update | **PENDING — operator action not performed** | the second Body operation was a Save |
| Expression Save / Update | **PASS** | each authorized before the durable write |
| Native Body Apply (changed) | **PASS** | 6 committed Applies. Each has exactly one authorization before preflight and pinned postcommit verification `ok`, with no authority access inside the transaction |
| Native Body Apply Undo | **PASS (log-evidenced)** | after the first Apply, the Undo depth returned to 59 and the next Apply again changed the same 4 sides |
| No-op Body Apply | **PASS** | Undo count unchanged (71 → 71); status "Already matches this preset." |
| Expression Apply | **PASS** | committed; pinned postcommit verification `ok`; visibly correct (owner) |
| Review / Reclassify | **PENDING — fixture unavailable** | both models had 0 Master-unknown (no Needs review items) |
| Ordinary Clothing Fit + Undo | **PENDING — fixture unavailable** | no source/target pair where the target has flexes the source lacks |
| C10 same-process broker | **PASS** | one broker object `0x30fd2a50` from seq 2–11 served both `cpm_compat_v1` and `normalizer_compat` in pid 25896, via each production acquisition path |
| Normalizer coexistence (sequential, same process) | **PASS** | Normalizer PASS after CPM use; CPM reopened after the Normalizer and worked (scope + 4 Applies) |
| Normalizer coexistence (CPM open while the Normalizer runs) | **PENDING — operator action not performed** | CPM was closed before the Normalizer ran |
| Latency and retention | **PASS (measured)** | see the Ledger |
| Process memory | **PENDING — probe defect (fixed in probe v2)** | v1's `GetProcessMemoryInfo` call was rejected once CPM had loaded |

**No CPM convergence defect was found.**

## Findings

1. **Probe defect (fixed).** The CPM app sets `argtypes` on the process-shared
   `ctypes.windll.psapi.GetProcessMemoryInfo`, using its own structure type. Probe v1 used that
   shared function with a different structure and was rejected. Probe v2 uses private `WinDLL`
   instances.
2. **New coexistence finding (R14; pre-existing G18AN behavior, not a convergence regression).**
   The same shared-prototype mutation makes the **production Normalizer's** own memory telemetry
   fail after CPM has run in the process.
   - Normalizer run #2 logged `mem_ok=False` at all 15 resource checkpoints.
   - Checkpoint J (no CPM) logged `mem_ok=True`.
   - The Normalizer uses these values for telemetry only; VAS gating remained `vas_ok=True`, and
     its run passed.
   - The code is present verbatim in the G18AN baseline.
   - The fix would be a small CPM product change (use a private `WinDLL`). That is outside this
     milestone and needs an owner decision.
3. **The probe's own cache footprint.** The probe's timing stage created one extra cached
   `cpm_compat_v1` view (46 folds, 53,002 B). It is test-only and holds no lease. Its first
   timing (1.224 s) was that cold acquisition.
