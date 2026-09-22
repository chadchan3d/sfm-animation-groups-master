# -*- coding: utf-8 -*-
"""SIDECAR candidate selection -- ASTRA_CORRECTED.md Section 10.

Selection order: local pointer/artifact (qualification-mode only -- see
below) -> shipped artifact -> SidecarMissing/RebuildRequired. No TXT
fallback anywhere in this module.

Arbitrary local/custom generations remain production-gated until B2F
(ASTRA_CORRECTED.md Section 14). This module therefore only exercises
local candidates when the caller explicitly passes
`allow_local_candidates=True` (a qualification/test-mode switch) -- normal
production-facing broker policy (the default, `allow_local_candidates=False`)
never inspects a local pointer at all.

R3-B2C productionization of the R3-B2F1F Stage F5 qualified candidate
(`selection_f5.py`): selection and opening are now ONE unified step per
candidate scanned, via resource_preflight.candidate_open_and_identify_
with_preflight -- never a separate identify-then-reopen pair. The
winning candidate's ALREADY-OPEN provider is returned directly on
`SelectionResult.provider`.

=== Astra second-correction-gate F7 (real bugs found and fixed) ===
1. `Cohort._open_provider_once` (the REAL acquisition route used by
   acquire_cohort/acquire_or_reuse_views -- i.e. what the Normalizer
   candidate actually calls) never passed the broker's own diagnostics
   list through to this module AT ALL before this correction -- `
   select_sidecar_candidate`'s own `if diagnostics is None: diagnostics
   = []` then silently created a throwaway list nothing ever read again,
   so any recovery/corruption notice this module logged was discarded
   the instant the call returned. Fixed at the Cohort call site (passes
   `self._broker._diagnostics` now); this module's own contract is
   unchanged (it always appends to whatever list it is given).
2. A matching local pointer whose referenced artifact FILE is actually
   missing (`open()` raising IOError/OSError) was not caught by ANY
   `except` clause in `_try_local_candidate` -- it propagated as a raw,
   unclassified IOError even though the module's own declared policy is
   "local sidecar missing/corrupt -> recover to shipped." Fixed: treated
   identically to a corrupt local candidate (logged diagnostic, falls
   through to shipped).
3. A corrupt/mismatched SHIPPED candidate, when it is the only one
   present, silently became indistinguishable from "nothing was ever
   shipped at all" (`SidecarMissing`, with the corruption fact
   discarded). Fixed: `_find_and_open_matching_artifact` now also
   accepts `diagnostics` and logs a `shipped_candidate_skipped` entry
   for every corrupt/mismatched candidate it skips, so the underlying
   reason survives even though the FINAL exception classification
   (`SidecarMissing`, when nothing else matches either) is unchanged --
   "no shipped candidate validly matches" remains the correct top-level
   classification; what changes is that WHY is no longer silently lost.
"""
import os

from . import errors
from . import pointer as pointer_mod
from . import resource_preflight

SOURCE_LOCAL = "local"
SOURCE_SHIPPED = "shipped"


class SelectionResult(object):
    __slots__ = ("artifact_identity", "source_kind", "artifact_path", "provider", "instrumentation")

    def __init__(self, artifact_identity, source_kind, artifact_path, provider=None, instrumentation=None):
        self.artifact_identity = artifact_identity
        self.source_kind = source_kind
        self.artifact_path = artifact_path
        # `provider` is the ALREADY-OPEN provider for the winning
        # candidate. Ownership transfers to the caller (cohort.py),
        # which must eventually close it exactly once. `instrumentation`
        # is the CandidateOpenInstrumentation object from the same open,
        # for qualification/diagnostic reporting only.
        self.provider = provider
        self.instrumentation = instrumentation

    def __repr__(self):
        return "SelectionResult(source=%r, path=%r)" % (self.source_kind, self.artifact_path)


def select_sidecar_candidate(h0, allow_local_candidates=False, local_pointer_path=None,
                              generated_root=None, shipped_root=None, runtime_cap_bytes=None,
                              diagnostics=None, requested_folds_by_consumer=None,
                              aggregate_existing_retained_bytes=0):
    """`requested_folds_by_consumer`/`aggregate_existing_retained_bytes`
    (Astra second-correction-gate F2): forwarded to the preflight/
    admission layer so a candidate's resource decision reflects the
    caller's REAL per-consumer requested fold sets (packed-count-based,
    never an average) and the broker's own aggregate ledger state --
    never a single-artifact-in-isolation check alone.

    `diagnostics`: a list APPENDED TO in place -- pass the broker's own
    real diagnostics list (never a throwaway) so recovery/corruption
    notices survive past this call (Astra F7 fix #1)."""
    if diagnostics is None:
        diagnostics = []
    if requested_folds_by_consumer is None:
        requested_folds_by_consumer = {}

    if allow_local_candidates and local_pointer_path is not None:
        local_result = _try_local_candidate(
            local_pointer_path, generated_root, h0, runtime_cap_bytes, diagnostics,
            requested_folds_by_consumer, aggregate_existing_retained_bytes,
        )
        if local_result is not None:
            return local_result

    if not shipped_root or not os.path.isdir(shipped_root):
        raise errors.SidecarMissing(
            "no shipped SIDECAR root available and no valid local candidate (H0=%s)." % h0.sha256
        )

    result, resource_refusal = _find_and_open_matching_artifact(
        shipped_root, h0.sha256, runtime_cap_bytes, diagnostics,
        requested_folds_by_consumer, aggregate_existing_retained_bytes,
    )
    if result is None:
        if resource_refusal is not None:
            # R3-B2F finding, preserved exactly: do not silently conflate
            # "a candidate exists but was refused purely for size" with
            # "nothing exists at all" -- ResourceAdmissionRefusal remains
            # distinctly observable, never collapsed into
            # SidecarMissing/corruption/format-unsupported/source-mismatch.
            raise resource_refusal
        raise errors.SidecarMissing("no shipped SIDECAR matches current Master (H0=%s)." % h0.sha256)

    provider, identity, artifact_path, inst = result
    return SelectionResult(identity, SOURCE_SHIPPED, artifact_path, provider=provider, instrumentation=inst)


def _find_and_open_matching_artifact(root, expected_source_sha256, runtime_cap_bytes, diagnostics,
                                      requested_folds_by_consumer=None, aggregate_existing_retained_bytes=0):
    """Scan `root` for the first .sfmsidecar file whose embedded
    source_sha256 matches. EXACT same skip semantics as before: a
    resource-refused candidate is tracked (last-seen wins) and scanning
    continues; a corrupt/mismatched candidate is simply skipped --
    ordinary multi-candidate scanning WITHIN one source kind (shipped),
    not the corrupt-local -> shipped recovery path, which only applies
    when the SELECTED local candidate itself is corrupt. Each candidate
    is opened EXACTLY ONCE (via the unified preflight+open primitive)
    regardless of outcome -- no separate identify-then-reopen pair for
    the eventual winner. A non-winning candidate's provider is never
    left open (closed inside candidate_open_and_identify_with_preflight
    itself, in its own finally block, before this loop ever sees it).

    Astra F7 fix #3: every corrupt/mismatched candidate skipped here now
    logs a diagnostic entry BEFORE continuing the scan, so that
    information survives even when the final classification collapses
    to SidecarMissing (nothing else matched either)."""
    if requested_folds_by_consumer is None:
        requested_folds_by_consumer = {}
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return None, None
    resource_refusal_seen = None
    for name in names:
        if not name.endswith(".sfmsidecar"):
            continue
        candidate_path = os.path.join(root, name)
        try:
            provider, identity, inst = resource_preflight.candidate_open_and_identify_with_preflight(
                candidate_path, expected_source_sha256, runtime_cap_bytes,
                requested_folds_by_consumer=requested_folds_by_consumer,
                aggregate_existing_retained_bytes=aggregate_existing_retained_bytes,
            )
            return (provider, identity, candidate_path, inst), None
        except errors.ResourceAdmissionRefusal as exc:
            resource_refusal_seen = exc
            diagnostics.append({
                "event": "shipped_candidate_skipped", "reason": "resource_admission_refusal",
                "candidate_path": candidate_path, "detail": str(exc),
            })
            continue
        except (errors.SourceGenerationMismatch, errors.SidecarCorrupt, errors.FormatUnsupported) as exc:
            diagnostics.append({
                "event": "shipped_candidate_skipped", "reason": type(exc).__name__,
                "candidate_path": candidate_path, "detail": str(exc),
            })
            continue
        except (IOError, OSError) as exc:
            # Defensive: a candidate found by listdir() could still
            # vanish/become unreadable by the time it is opened (a real,
            # if rare, race). Treated the same as any other skippable
            # per-candidate failure -- never lets a raw IOError/OSError
            # escape this scan.
            diagnostics.append({
                "event": "shipped_candidate_skipped", "reason": "io_error",
                "candidate_path": candidate_path, "detail": str(exc),
            })
            continue
    return None, resource_refusal_seen


def _try_local_candidate(local_pointer_path, generated_root, h0, runtime_cap_bytes, diagnostics,
                          requested_folds_by_consumer=None, aggregate_existing_retained_bytes=0):
    if requested_folds_by_consumer is None:
        requested_folds_by_consumer = {}
    try:
        ptr = pointer_mod.load_pointer(local_pointer_path)
    except errors.LocalPointerCorrupt as exc:
        diagnostics.append({"event": "local_pointer_corrupt", "detail": str(exc)})
        return None  # corrected B1: treated as "no usable local pointer", falls through silently

    if ptr.source_sha256 != h0.sha256:
        return None  # stale pointer -- simply not selected, not an error

    artifact_path = pointer_mod.derive_artifact_path(generated_root, ptr)
    try:
        provider, identity, inst = resource_preflight.candidate_open_and_identify_with_preflight(
            artifact_path, h0.sha256, runtime_cap_bytes,
            requested_folds_by_consumer=requested_folds_by_consumer,
            aggregate_existing_retained_bytes=aggregate_existing_retained_bytes,
        )
        # Astra F7 (retained from first correction): the artifact path is
        # DERIVED from the pointer's own declared artifact_sha256
        # (pointer.derive_artifact_path) -- a filename collision or an
        # in-place tamper of the file at that exact path is cross-
        # checked here (hard failure, treated as local corruption ->
        # shipped recovery, never silently trusted). format_contract_
        # version/authority_semantics_version disagreements are logged
        # as ADVISORY-ONLY diagnostics, not enforced -- the real full
        # validator independently re-derives and checks these fields
        # from the artifact's own bytes regardless of what the pointer
        # claims.
        if identity.sidecar_artifact_sha256 != ptr.sidecar_sha256:
            try:
                provider.close()
            finally:
                pass
            diagnostics.append({
                "event": "local_pointer_artifact_disagreement",
                "message": "Local compiled Master is damaged (pointer/artifact SHA disagreement); "
                           "using the matching shipped copy. Rebuild to repair.",
                "pointer_declared_artifact_sha256": ptr.sidecar_sha256,
                "actual_artifact_sha256": identity.sidecar_artifact_sha256,
            })
            return None
        if (identity.format_contract_version != ptr.format_contract_version
                or identity.authority_semantics_version != ptr.authority_semantics_version):
            diagnostics.append({
                "event": "local_pointer_version_advisory_mismatch",
                "message": "Pointer-declared format_contract_version/authority_semantics_version "
                           "disagrees with the actual selected artifact -- ADVISORY ONLY, not "
                           "enforced (the real validator independently re-derives these fields from "
                           "the artifact's own bytes).",
                "pointer_declared": (ptr.format_contract_version, ptr.authority_semantics_version),
                "actual": (identity.format_contract_version, identity.authority_semantics_version),
            })
        return SelectionResult(identity, SOURCE_LOCAL, artifact_path, provider=provider, instrumentation=inst)
    except errors.ResourceAdmissionRefusal:
        # Explicitly NOT corruption -- must not automatically trigger the
        # shipped-recovery path (ASTRA_CORRECTED.md Section 10).
        raise
    except (errors.SidecarCorrupt, errors.SourceGenerationMismatch, errors.FormatUnsupported) as exc:
        diagnostics.append({
            "event": "local_sidecar_corrupt_passive_notice",
            "message": "Local compiled Master is damaged; using the matching shipped copy. Rebuild to repair.",
            "cause": str(exc),
        })
        return None
    except (IOError, OSError) as exc:
        # Astra F7 fix #2: a matching pointer whose referenced artifact
        # FILE is actually missing/unreadable (open() itself raising)
        # was NOT previously caught here at all -- it escaped as a raw,
        # unclassified IOError/OSError even though this module's own
        # declared policy is "local sidecar missing/corrupt -> recover
        # to shipped." Treated identically to a corrupt local candidate.
        diagnostics.append({
            "event": "local_sidecar_missing_passive_notice",
            "message": "Local compiled Master is missing or unreadable; using the matching shipped "
                       "copy. Rebuild to repair.",
            "cause": str(exc),
        })
        return None
