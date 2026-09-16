# -*- coding: utf-8 -*-
"""R3-B2C productionized single canonical open-and-identify primitive.
Ports R3-B2F1F Stage F5's `preflight_gate_f5.candidate_open_and_identify_
with_preflight` into the shared authority package namespace -- same
logic, package-relative imports instead of dependency injection (this
module lives INSIDE sfm_master_authority now, not loaded from outside
it via sys.path the way the F5 candidate was).

Collapses what the frozen call graph does for a winning candidate --
FIVE full reads (F5 report Section 1: two full reads inside
sidecar_contract.validate_selected_artifact, called twice for the
winner via selection.py's scan-then-reidentify pattern, plus a fifth
via cohort.py's own separate BoundedProvider.open_path) -- into exactly
ONE open, ONE preflight parse (<=360 bytes), and (only if admitted) ONE
full bounded read, ONE structural validation. Returns an ALREADY-OPEN,
caller-owned provider plus its ArtifactIdentity.

Reuses the EXISTING, unmodified BoundedProvider._open_from_buf (hence
the EXACT SAME candidate_packed_validator.validate_packed) and the
EXISTING errors.ResourceAdmissionRefusal/SourceGenerationMismatch/
SidecarCorrupt classes -- no second authored validator, no new
exception types reaching callers.

`sidecar_artifact_sha256` is computed from the ALREADY-READ in-memory
buffer (hashlib.sha256(data)), not a second disk read -- mathematically
identical to sidecar_contract._sha256_of_file(path), zero behavior
change, one fewer full read.

STILL A CANDIDATE, isolated under tests/sidecar/qualification/
candidate_b2c/ -- not yet the frozen production package.
"""
import binascii
import hashlib
import os

from . import errors
from . import descriptors
from . import sidecar_contract
from . import resource_estimator

fmt = resource_estimator.fmt

RETAINED_GATE_BYTES = 16 * 1024 * 1024
TRANSIENT_GATE_BYTES = 32 * 1024 * 1024  # 33,554,432 bytes exactly (32 MiB) -- see B2F1F F6 note on the
                                          # earlier "33 MiB" mislabeling bug, corrected before F6 and carried
                                          # forward here unchanged.


class CandidateOpenInstrumentation(object):
    __slots__ = (
        "candidate_path", "file_open_count", "file_close_count",
        "raw_artifact_bytes", "preflight_bytes_read", "preflight_parse_deferred",
        "full_bounded_read_call_count", "full_bounded_read_bytes_returned",
        "validator_call_count", "estimator_model_version",
        "estimated_retained_bytes", "estimated_transient_bytes",
        "retained_gate_bytes", "transient_gate_bytes", "runtime_cap_bytes",
        "outcome", "reason",
    )

    def __init__(self):
        for k in self.__slots__:
            setattr(self, k, None)
        self.file_open_count = 0
        self.file_close_count = 0
        self.preflight_bytes_read = 0
        self.preflight_parse_deferred = False
        self.full_bounded_read_call_count = 0
        self.validator_call_count = 0
        self.estimator_model_version = resource_estimator.ESTIMATOR_MODEL_VERSION
        self.retained_gate_bytes = RETAINED_GATE_BYTES
        self.transient_gate_bytes = TRANSIENT_GATE_BYTES

    def to_dict(self):
        return dict((k, getattr(self, k)) for k in self.__slots__)


def candidate_open_and_identify_with_preflight(path, expected_source_sha256, runtime_cap_bytes=None, inst=None):
    """Returns (provider, identity, instrumentation) with `provider` left
    OPEN -- caller owns it and must eventually .close() it. Raises the
    EXISTING, real error classes (never a locally-invented type):
      errors.ResourceAdmissionRefusal  -- valid but resource-expensive
      errors.SourceGenerationMismatch  -- embedded source_sha256 mismatch
      errors.SidecarCorrupt            -- malformed/fails structural validation
    On a ResourceAdmissionRefusal, the instrumentation is attached to the
    raised exception as `.instrumentation` so callers/scanners can report
    genuine refusal-path counters without a second call.

    `runtime_cap_bytes=None` (the caller omits it) is a REAL, pre-existing
    contract preserved from the frozen path: sidecar_contract.
    validate_selected_artifact only forwards runtime_cap_bytes when it is
    not None, letting BoundedProvider.open_path's own default
    (DEFAULT_RUNTIME_ADMISSION_CAP_BYTES, 16 MiB) apply. This function
    resolves that SAME default here (via the frozen provider module
    itself, not a re-typed constant) before doing anything cap-dependent,
    so a None cap behaves identically to the frozen call graph rather
    than crashing."""
    if inst is None:
        inst = CandidateOpenInstrumentation()
    inst.candidate_path = path

    sidecar_contract.ensure_loaded()
    if runtime_cap_bytes is None:
        runtime_cap_bytes = sidecar_contract._provider_module.DEFAULT_RUNTIME_ADMISSION_CAP_BYTES
    inst.runtime_cap_bytes = runtime_cap_bytes

    f = open(path, "rb")
    inst.file_open_count += 1
    try:
        artifact_bytes = os.fstat(f.fileno()).st_size
        inst.raw_artifact_bytes = artifact_bytes
        if artifact_bytes > runtime_cap_bytes:
            inst.outcome = "refused"
            inst.reason = "artifact_bytes"
            exc = errors.ResourceAdmissionRefusal(
                "sidecar file size %d exceeds runtime admission cap %d bytes -- refusing to read "
                "(preflight Gate A, no estimator parse needed)" % (artifact_bytes, runtime_cap_bytes)
            )
            exc.instrumentation = inst
            raise exc

        header_bytes = f.read(fmt.HEADER_SIZE)
        shape = None
        try:
            region_size = resource_estimator.preflight_region_size(header_bytes)
            f.seek(0)
            prefix = f.read(region_size)
            inst.preflight_bytes_read = len(prefix)
            shape = resource_estimator.parse_resource_shape(prefix, artifact_bytes)
        except resource_estimator.PreflightCorruptOrIncompatible:
            # Do NOT invent a corruption verdict here -- preflight is a
            # negative admission filter only. Fall through to the
            # existing full validation path, which remains the sole
            # authority on corruption/incompatibility.
            inst.preflight_parse_deferred = True
            shape = None
        except Exception:
            inst.preflight_parse_deferred = True
            shape = None

        if shape is not None:
            est_retained = resource_estimator.estimate_retained(shape)
            est_transient = resource_estimator.estimate_transient(shape, runtime_cap_bytes)
            inst.estimated_retained_bytes = est_retained
            inst.estimated_transient_bytes = est_transient
            if est_retained > RETAINED_GATE_BYTES:
                inst.outcome = "refused"
                inst.reason = "estimated_retained"
                exc = errors.ResourceAdmissionRefusal(
                    "preflight estimated retained charge %d bytes exceeds retained gate %d bytes "
                    "(estimator_model_version=%s)" % (
                        est_retained, RETAINED_GATE_BYTES, resource_estimator.ESTIMATOR_MODEL_VERSION)
                )
                exc.instrumentation = inst
                raise exc
            if est_transient > TRANSIENT_GATE_BYTES:
                inst.outcome = "refused"
                inst.reason = "estimated_transient"
                exc = errors.ResourceAdmissionRefusal(
                    "preflight estimated transient delta %d bytes exceeds transient gate %d bytes "
                    "(estimator_model_version=%s)" % (
                        est_transient, TRANSIENT_GATE_BYTES, resource_estimator.ESTIMATOR_MODEL_VERSION)
                )
                exc.instrumentation = inst
                raise exc

        f.seek(0)
        data = f.read(runtime_cap_bytes + 1)
        inst.full_bounded_read_call_count += 1
        inst.full_bounded_read_bytes_returned = len(data)
        if len(data) > runtime_cap_bytes:
            inst.outcome = "refused"
            inst.reason = "post_read_length"
            exc = errors.ResourceAdmissionRefusal(
                "sidecar content exceeds runtime admission cap %d bytes" % runtime_cap_bytes
            )
            exc.instrumentation = inst
            raise exc
    finally:
        f.close()
        inst.file_close_count += 1

    sidecar_contract.ensure_loaded()
    provider_mod = sidecar_contract._provider_module
    try:
        provider = provider_mod.BoundedProvider._open_from_buf(data, expected_source_sha256, bound=True)
    except provider_mod.SourceMismatchError as exc2:
        inst.outcome = "refused"
        inst.reason = "source_generation_mismatch"
        raise errors.SourceGenerationMismatch(str(exc2))
    except provider_mod.AuthorityUnavailable as exc2:
        msg = str(exc2)
        inst.outcome = "refused"
        if "admission cap" in msg:
            inst.reason = "estimated_transient_post_read"
            raise errors.ResourceAdmissionRefusal(msg)
        inst.reason = "corrupt"
        raise errors.SidecarCorrupt(msg)
    inst.validator_call_count += 1
    inst.outcome = "accepted"
    inst.reason = None

    header = provider._header
    embedded_source_hex = binascii.hexlify(header.source_sha256).decode("ascii").lower()
    identity = descriptors.ArtifactIdentity(
        sidecar_artifact_sha256=hashlib.sha256(data).hexdigest(),  # in-memory -- no second disk read
        format_contract_version=header.format_contract_version,
        authority_semantics_version=header.authority_semantics_version,
        projection_contract_version=None,
        embedded_source_sha256=embedded_source_hex,
        embedded_source_byte_length=header.source_byte_length,
    )
    return provider, identity, inst
