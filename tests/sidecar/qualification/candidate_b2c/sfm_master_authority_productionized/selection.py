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
`SelectionResult.provider` (a new, additive attribute -- existing
callers reading only `.artifact_identity`/`.source_kind`/`.artifact_path`
are unaffected). STILL A CANDIDATE, isolated under tests/sidecar/
qualification/candidate_b2c/ -- not yet the frozen production package.
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
        # candidate -- new in the B2C productionization. Ownership
        # transfers to the caller (cohort.py), which must eventually
        # close it exactly once. `instrumentation` is the
        # CandidateOpenInstrumentation object from the same open, for
        # qualification/diagnostic reporting only.
        self.provider = provider
        self.instrumentation = instrumentation

    def __repr__(self):
        return "SelectionResult(source=%r, path=%r)" % (self.source_kind, self.artifact_path)


def select_sidecar_candidate(h0, allow_local_candidates=False, local_pointer_path=None,
                              generated_root=None, shipped_root=None, runtime_cap_bytes=None,
                              diagnostics=None):
    if diagnostics is None:
        diagnostics = []

    if allow_local_candidates and local_pointer_path is not None:
        local_result = _try_local_candidate(
            local_pointer_path, generated_root, h0, runtime_cap_bytes, diagnostics,
        )
        if local_result is not None:
            return local_result

    if not shipped_root or not os.path.isdir(shipped_root):
        raise errors.SidecarMissing(
            "no shipped SIDECAR root available and no valid local candidate (H0=%s)." % h0.sha256
        )

    result, resource_refusal = _find_and_open_matching_artifact(shipped_root, h0.sha256, runtime_cap_bytes)
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


def _find_and_open_matching_artifact(root, expected_source_sha256, runtime_cap_bytes):
    """Scan `root` for the first .sfmsidecar file whose embedded
    source_sha256 matches. EXACT same skip semantics as the pre-B2C
    _find_matching_artifact: a resource-refused candidate is tracked
    (last-seen wins) and scanning continues; a corrupt/mismatched
    candidate is simply skipped -- ordinary multi-candidate scanning
    WITHIN one source kind (shipped), not the corrupt-local -> shipped
    recovery path (Section 10), which only applies when the SELECTED
    local candidate itself is corrupt. THE B2C CHANGE: each candidate is
    opened EXACTLY ONCE (via the unified preflight+open primitive)
    regardless of outcome -- no separate identify-then-reopen pair for
    the eventual winner. A non-winning candidate's provider is never
    left open (closed inside candidate_open_and_identify_with_preflight
    itself, in its own finally block, before this loop ever sees it)."""
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
            )
            return (provider, identity, candidate_path, inst), None
        except errors.ResourceAdmissionRefusal as exc:
            resource_refusal_seen = exc
            continue
        except (errors.SourceGenerationMismatch, errors.SidecarCorrupt):
            continue
    return None, resource_refusal_seen


def _try_local_candidate(local_pointer_path, generated_root, h0, runtime_cap_bytes, diagnostics):
    try:
        ptr = pointer_mod.load_pointer(local_pointer_path)
    except errors.LocalPointerCorrupt as exc:
        diagnostics.append({"event": "local_pointer_corrupt", "detail": str(exc)})
        return None  # corrected B1: treated as "no usable local pointer", falls through silently

    if ptr.master_sha256 != h0.sha256:
        return None  # stale pointer -- simply not selected, not an error

    artifact_path = pointer_mod.derive_artifact_path(generated_root, ptr)
    try:
        provider, identity, inst = resource_preflight.candidate_open_and_identify_with_preflight(
            artifact_path, h0.sha256, runtime_cap_bytes,
        )
        return SelectionResult(identity, SOURCE_LOCAL, artifact_path, provider=provider, instrumentation=inst)
    except errors.ResourceAdmissionRefusal:
        # Explicitly NOT corruption -- must not automatically trigger the
        # shipped-recovery path (ASTRA_CORRECTED.md Section 10).
        raise
    except (errors.SidecarCorrupt, errors.SourceGenerationMismatch) as exc:
        diagnostics.append({
            "event": "local_sidecar_corrupt_passive_notice",
            "message": "Local compiled Master is damaged; using the matching shipped copy. Rebuild to repair.",
            "cause": str(exc),
        })
        return None
