# O3 — Theoretical Savings Ceiling

**Status: DESIGN/PROOF ONLY.** No production, integration, or lifecycle code has been modified. Figures
below are calculated from O2-R1's own real measured timings; nothing here is a new measurement. Extrapolation
beyond the measured fixture is explicitly labeled as such, not presented as fact.

## Measured basis (O2-R1, real SFM run, `shot3`, Selected Shots, Fox + Mia)

| | Fresh Selected | Already-normalized Selected |
|---|---|---|
| Production command → `FINAL_REPORT_ENTRY` | ~7.13 s | ~6.56 s |
| Native Rebuild | 2 calls, ~2.179 s total | 2 calls, ~2.400 s total |
| Discovery (`discover_rig_context`) | 10 calls, ~1.729 s total (~0.173 s mean) | 10 calls, ~1.891 s total (~0.189 s mean) |
| Tree construction (`capture_tree`) | 10 calls, ~0.020-0.025 s total | 10 calls, ~0.023-0.028 s total |

10 discovery calls = 5 per target (PRE, NATIVE_POST, COMPOSER_PRE, COMPOSER_POST, TERMINAL) × 2 targets
(Fox, Mia), both reaching the reconciled path in this measured run. Tree-construction cost is **not**
counted as material savings anywhere below, per the already-established `IMMATERIAL` disposition and per
explicit instruction.

## Per-candidate savings

### Candidate 1 — Outer POST → composer-before discovery reuse only (`O3_OUTER_POST_COMPOSER_BEFORE_DESIGN.md`, Design B)

Eliminates exactly one discovery call per target (call #3, COMPOSER_PRE) on the reconciled path.

| | Fresh | Already-normalized |
|---|---|---|
| Current discovery calls/target | 5 | 5 |
| Proposed discovery calls/target | 4 | 4 |
| Eliminated calls/target | 1 | 1 |
| Eliminated calls, this 2-target fixture | 2 | 2 |
| Estimated savings, this fixture | ~2 × 0.173 s ≈ **0.35 s** | ~2 × 0.189 s ≈ **0.38 s** |
| % of measured production command runtime | 0.35 / 7.13 ≈ **4.9%** | 0.38 / 6.56 ≈ **5.8%** |

### Candidate 2 — Terminal discovery reuse only, reconciled path + fallback sub-case A (`O3_TERMINAL_DISCOVERY_REUSE_DESIGN.md`)

Eliminates exactly one discovery call per target (call #5, TERMINAL) on the reconciled path and on
native-only-fallback sub-case A; no elimination on fallback sub-case B (PRE-unsupported, no safe reuse
basis exists there). For this measured fixture (both targets reconciled), the arithmetic is identical to
Candidate 1:

| | Fresh | Already-normalized |
|---|---|---|
| Eliminated calls, this 2-target fixture | 2 | 2 |
| Estimated savings, this fixture | ~**0.35 s** | ~**0.38 s** |
| % of measured production command runtime | ~**4.9%** | ~**5.8%** |

### Candidate 3 — Both (informational ceiling only — NOT a single implementation candidate)

Presented for context only. `O3_IMPLEMENTATION_RECOMMENDATION.md` recommends **at most one** candidate
for the next implementation round, per explicit instruction not to bundle optimizations. If both
Candidate 1 and Candidate 2 were eventually implemented (in separate, separately-qualified rounds):

| | Fresh | Already-normalized |
|---|---|---|
| Eliminated calls/target | 2 | 2 |
| Eliminated calls, this 2-target fixture | 4 | 4 |
| Estimated savings, this fixture | ~4 × 0.173 s ≈ **0.69 s** | ~4 × 0.189 s ≈ **0.76 s** |
| % of measured production command runtime | 0.69 / 7.13 ≈ **9.7%** | 0.76 / 6.56 ≈ **11.5%** |

## Rough per-target scaling — LABELED EXTRAPOLATION, NOT A MEASUREMENT

The measured fixture is exactly 2 targets (Fox: 136 controls; Mia: 174 controls). Naively scaling
Candidate 1's or Candidate 2's own per-call savings (~0.173-0.189 s/eliminated call) linearly to a
hypothetical 85-eligible-target All-Shots scope would suggest:

> 85 targets × 1 eliminated call/target × ~0.18 s/call (rough average of the two measured means) ≈ **~15.3 s**
> of discovery cost eliminated across a full All-Shots command, for ONE candidate.

**This is an unverified extrapolation, not a measured fact**, for at least three reasons this document
does not paper over: (1) `discover_rig_context()`'s own cost is a function of the *shot's total scene
size* (`reachable(scene)`, an O(scene size) traversal), not the target's own control count — Fox and
Mia's own measured ~0.17-0.19s reflects `shot3`'s own scene complexity, which may not represent the
other 14 shots in the qualification fixture, let alone a production scene of different composition; (2)
this measurement is Selected-Shots-scoped (`shot3` only); an All-Shots command's own per-call discovery
cost was never independently measured — F1/F1-2's own All-Shots evidence measured whole-command
memory/VAS, not per-discovery-call timing; (3) the reconciled-vs-fallback branch mix across a real
85-target fixture is unknown — this measured fixture happened to put both Fox and Mia on the reconciled
path, but Candidate 2's own savings depend on which fallback sub-case (if any) a given target takes.

No optimization is sized or authorized based on this extrapolation. It is included only to give a rough
sense of scale for `O3_IMPLEMENTATION_RECOMMENDATION.md`'s own "theoretical saving" field, explicitly
caveated there as unverified.
