# O3-R3 — Enumeration Validity Mechanism Search

**Status: DESIGN/PROOF ONLY.** No production, integration, or lifecycle code has been modified. This
document searches the actual Normalizer, the SFM Python/datamodel API surface this project has ever
exercised, and the already-established runtime architecture for an existing, cheap, authoritative
mechanism that would let a reused candidate enumeration (see `O3_R3_REUSE_OBJECT_DECISION.md`) be proven
still complete and applicable at composer entry. **No candidate mechanism is invented here** — only
searched for.

## Method

Three independent searches were run directly against the pinned production source
(`audit_external_runtime/Rebuild_Control_Groups_Normalizer.py`, SHA-256
`cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`, confirmed matching the accepted,
integrated production identity) and against this project's own accumulated evidence base (every prior
checkpoint's own source citations and diagnostics):

1. **Case-insensitive text search** across the entire production source for every term suggestive of a
   mutation/version-tracking concept: `generation`, `revision`, `serial`, `GetModification`,
   `ModificationCount`, `dirty`, `.Version(`, `VersionNumber`, `ChangeCount`, `EditCount`. Matches: only
   `PRODUCTION_REVISION` (the Normalizer's own source-version string constant, unrelated to scene state)
   and `expected_generation=self.master_hash` (the authority broker's own generation concept, tied to the
   **canonical Master file's own hash**, not to scene/DME topology at all — already fully documented in
   earlier checkpoints, unrelated to this question).
2. **Exhaustive enumeration of every `DataModel`-singleton method this codebase has ever called.** A
   targeted grep for every `dm.<Method>(` / `g_pDataModel.<Method>(` call site across the entire file
   returns exactly six call sites, all four distinct methods: `IsUndoEnabled()`, `SetUndoEnabled()`,
   `GetUndoItemCount()`, `GetUndoDesc()`. **No modification-count, generation, serial, or change-tracking
   method of `vs.g_pDataModel` has ever been called anywhere in this codebase.**
3. **Repository-wide search** (`.py`, `.md`, `.txt`, across every checkpoint directory, all prior Astra
   review artifacts, all prior audits) for `Serial`, `Dirty`, `ModificationCount`. Every match is either an
   unrelated control-name literal (`mp_SerialDesignation...`, present in the Master file itself), an
   unrelated use of the English word "serialize" in a JSON/file-writing context, or the authority broker's
   own Master-hash-based generation concept (already covered by search 1). **No hit anywhere in this
   project's accumulated evidence describes a scene-topology or DME-element mutation-tracking primitive.**

## Result

**No existing authoritative mechanism was found.** This project has never called, referenced, tested, or
documented any SFM/DME API that exposes scene generation, element-list mutation count, rig-attachment
generation, or any other mutation serial. The `vs.g_pDataModel` API surface this codebase actually
exercises is narrowly undo-related and provides no topology-change signal whatsoever.

This does **not** mean such a primitive is provably absent from the underlying, closed-source SFM/Source
engine's C++ `DmElement`/`CDmeElement` implementation — this project has no access to that engine's header
files or SDK documentation, only to the Python-visible surface this Normalizer itself uses. The honest
statement is: **no such mechanism is known, used, or documented anywhere in this project's own evidence
base**, and per explicit instruction, none is invented here to fill that gap.

## Classification of every candidate actually found

| Candidate | Where it comes from | Available in SFM Python 2.7.5 (as used by this codebase)? | Covers element add/remove? | Covers reachability changes? | Covers new matching rig appearance? | Covers old rig becoming unreachable? | Covers registry rebinding? | Cheap to read at both native POST and composer entry? | Equality implies enumeration validity? | Classification |
|---|---|---|---|---|---|---|---|---|---|---|
| `PRODUCTION_REVISION` (source-version string) | This Normalizer's own module-level constant | Yes, but semantically irrelevant | No | No | No | No | No | N/A | No — describes the *script's own version*, not scene state | `INSUFFICIENT` |
| `self.master_hash` / authority-broker "generation" | Canonical Master **file's own SHA-256**, read from disk | Yes, already in active use — but for a completely different purpose (protecting the Master text file from concurrent writers) | No — tracks the Master text file, not the DME scene | No | No | No | No | Cheap, but answers an unrelated question | No | `INSUFFICIENT` |
| `dm.IsUndoEnabled()` / `dm.GetUndoItemCount()` / `dm.GetUndoDesc()` | The only other `g_pDataModel` surface this codebase touches | Yes | Partially — an undo-item count change *could* correlate with *some* mutations, but undo is explicitly disabled (`dm.SetUndoEnabled(False)`) for the entire native-POST-through-composer interval this checkpoint concerns (see `O3_R3_INTERVAL_IMMUTABILITY_PROOF.md`), so `GetUndoItemCount()` cannot move during that interval **by construction of the existing code**, whether or not scene topology changed outside of undo tracking | No — reachability/rig-attachment changes made without going through the undo-recorded operations this system tracks would not register | No — a rig attached via a code path not creating an undo-tracked operation would not register; not proven either way | No | No | Cheap, but semantically the wrong question, and disabled during the exact interval in question | No — even if it moved, it would only prove *an undone-recorded edit happened*, not that rig enumeration specifically changed | `INSUFFICIENT` (and inapplicable while undo is disabled) |
| Any DME element/scene modification-serial, generation counter, or dirty flag | Would have to come from the underlying C++ `DmElement`/scene API | **Not found** — no call site anywhere in this codebase's history ever reads such a value | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | `UNPROVEN` — not established as existing or available; not invented |

No candidate reaches `AUTHORITATIVE`.

## Consequence

Per section 8's complexity gate (`O3_R3_ENUMERATION_VALIDITY_DECISION.md`), an `AUTHORITATIVE` mechanism
is one of exactly two routes that could justify Option C. This search closes that route: none exists in
this project's evidence base, and none may be invented to manufacture one. The remaining route — a strong
proof that the native-POST → composer-before interval cannot mutate or reenter in the relevant way — is
addressed independently in `O3_R3_INTERVAL_IMMUTABILITY_PROOF.md`.
