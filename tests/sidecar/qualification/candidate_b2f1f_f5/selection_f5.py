# -*- coding: utf-8 -*-
"""R3-B2F1F Stage F5: candidate selection module -- preserves EXACT
precedence/error/recovery semantics of the frozen selection.py, but
selection and opening are now ONE unified step per candidate scanned
(via preflight_gate_f5.candidate_open_and_identify_with_preflight),
never a separate identify-then-reopen pair. Returns the WINNING
candidate's ALREADY-OPEN provider directly -- the caller (cohort_f5)
never calls BoundedProvider.open_path a second time.

Not a frozen-file edit -- a candidate copy, isolated under
tests/sidecar/qualification/candidate_b2f1f_f5/. Imports the REAL,
unmodified errors/pointer/sidecar_contract/descriptors modules; adds no
second authored validator and no new exception types.
"""
import os

from preflight_gate_f5 import candidate_open_and_identify_with_preflight, CandidateOpenInstrumentation

SOURCE_LOCAL = "local"
SOURCE_SHIPPED = "shipped"


class SelectionResultF5(object):
    """Like the original SelectionResult, PLUS the already-open
    provider -- the winning candidate's ownership transfers to the
    caller from here; the caller (cohort_f5) is responsible for
    eventually closing it exactly once."""
    __slots__ = ("provider", "artifact_identity", "source_kind", "artifact_path", "instrumentation")

    def __init__(self, provider, artifact_identity, source_kind, artifact_path, instrumentation):
        self.provider = provider
        self.artifact_identity = artifact_identity
        self.source_kind = source_kind
        self.artifact_path = artifact_path
        self.instrumentation = instrumentation

    def __repr__(self):
        return "SelectionResultF5(source=%r, path=%r)" % (self.source_kind, self.artifact_path)


def select_sidecar_candidate_f5(h0, errors_mod, pointer_mod, sidecar_contract_mod, descriptors_mod,
                                 allow_local_candidates=False, local_pointer_path=None,
                                 generated_root=None, shipped_root=None, runtime_cap_bytes=None,
                                 diagnostics=None):
    """EXACT same precedence order as the frozen select_sidecar_candidate:
    local pointer/artifact (qualification-mode only) -> shipped artifact
    -> SidecarMissing/ResourceAdmissionRefusal. No TXT fallback. Resource
    refusal is NEVER collapsed into SidecarMissing (preserves the
    earlier B2F correction) -- same tracked-last-resource-refusal
    pattern as the frozen _find_matching_artifact."""
    if diagnostics is None:
        diagnostics = []

    if allow_local_candidates and local_pointer_path is not None:
        local_result = _try_local_candidate_f5(
            local_pointer_path, generated_root, h0, runtime_cap_bytes, diagnostics,
            errors_mod, pointer_mod, sidecar_contract_mod, descriptors_mod,
        )
        if local_result is not None:
            return local_result

    if not shipped_root or not os.path.isdir(shipped_root):
        raise errors_mod.SidecarMissing(
            "no shipped SIDECAR root available and no valid local candidate (H0=%s)." % h0.sha256
        )

    result, resource_refusal, _last_instrumentation = _find_and_open_matching_artifact_f5(
        shipped_root, h0.sha256, runtime_cap_bytes, errors_mod, sidecar_contract_mod, descriptors_mod,
    )
    if result is None:
        if resource_refusal is not None:
            # R3-B2F correction, preserved exactly: do not conflate
            # "a candidate exists but was refused purely for resource
            # cost" with "nothing exists at all". `resource_refusal`
            # carries `.instrumentation` (set above) for F6 reporting.
            raise resource_refusal
        raise errors_mod.SidecarMissing("no shipped SIDECAR matches current Master (H0=%s)." % h0.sha256)

    provider, identity, artifact_path, inst = result
    return SelectionResultF5(provider, identity, SOURCE_SHIPPED, artifact_path, inst)


def _find_and_open_matching_artifact_f5(root, expected_source_sha256, runtime_cap_bytes,
                                         errors_mod, sidecar_contract_mod, descriptors_mod):
    """Scan `root` for the first .sfmsidecar file whose embedded
    source_sha256 matches. EXACT same skip semantics as the frozen
    _find_matching_artifact: a resource-refused candidate is tracked
    (last-seen wins, same as before) and scanning continues; a corrupt/
    mismatched candidate is simply skipped. The KEY difference: each
    candidate is opened EXACTLY ONCE (via the unified preflight+open
    primitive) regardless of outcome -- no separate identify-then-reopen
    pair for the eventual winner. A non-winning candidate's provider (if
    admitted but not matching -- cannot happen here since match is
    checked by BoundedProvider._open_from_buf's own source_sha256 check,
    so any candidate that reaches provider construction here EITHER
    matches and wins OR raises SourceGenerationMismatch) is never left
    open."""
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return None, None, None
    resource_refusal_seen = None
    last_instrumentation = None
    for name in names:
        if not name.endswith(".sfmsidecar"):
            continue
        candidate_path = os.path.join(root, name)
        inst = CandidateOpenInstrumentation()
        try:
            provider, identity, inst = candidate_open_and_identify_with_preflight(
                candidate_path, expected_source_sha256, runtime_cap_bytes,
                sidecar_contract_mod, errors_mod, descriptors_mod, inst,
            )
            return (provider, identity, candidate_path, inst), None, inst
        except errors_mod.ResourceAdmissionRefusal as exc:
            # `inst` is mutated in place by candidate_open_and_identify_
            # with_preflight even on this raise path (outcome/reason/
            # counters set before the raise) -- attach it to the
            # exception so F6's launchers can report genuine refusal-
            # path instrumentation, not just infer it.
            exc.instrumentation = inst
            resource_refusal_seen = exc
            last_instrumentation = inst
            continue
        except (errors_mod.SourceGenerationMismatch, errors_mod.SidecarCorrupt):
            continue
    return None, resource_refusal_seen, last_instrumentation


def _try_local_candidate_f5(local_pointer_path, generated_root, h0, runtime_cap_bytes, diagnostics,
                             errors_mod, pointer_mod, sidecar_contract_mod, descriptors_mod):
    try:
        ptr = pointer_mod.load_pointer(local_pointer_path)
    except errors_mod.LocalPointerCorrupt as exc:
        diagnostics.append({"event": "local_pointer_corrupt", "detail": str(exc)})
        return None

    if ptr.master_sha256 != h0.sha256:
        return None  # stale pointer -- not selected, not an error

    artifact_path = pointer_mod.derive_artifact_path(generated_root, ptr)
    inst = CandidateOpenInstrumentation()
    try:
        provider, identity, inst = candidate_open_and_identify_with_preflight(
            artifact_path, h0.sha256, runtime_cap_bytes,
            sidecar_contract_mod, errors_mod, descriptors_mod, inst,
        )
        return SelectionResultF5(provider, identity, SOURCE_LOCAL, artifact_path, inst)
    except errors_mod.ResourceAdmissionRefusal:
        raise  # explicitly NOT corruption -- must not trigger shipped-recovery
    except (errors_mod.SidecarCorrupt, errors_mod.SourceGenerationMismatch) as exc:
        diagnostics.append({
            "event": "local_sidecar_corrupt_passive_notice",
            "message": "Local compiled Master is damaged; using the matching shipped copy. Rebuild to repair.",
            "cause": str(exc),
        })
        return None
