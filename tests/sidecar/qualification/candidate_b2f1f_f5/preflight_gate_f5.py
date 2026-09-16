# -*- coding: utf-8 -*-
"""R3-B2F1F Stage F5: the single canonical open-and-identify primitive.

Collapses what the CURRENT frozen call graph does for a winning
candidate -- FIVE full reads (see Section 1 of the F5 report for the
exact accounting) -- into exactly ONE open, ONE preflight parse (<=360
bytes), and (only if admitted) ONE full bounded read, ONE structural
validation. Returns an ALREADY-OPEN, caller-owned provider plus its
ArtifactIdentity -- never a bare path requiring a second open.

Reuses the EXISTING, unmodified BoundedProvider._open_from_buf (hence
the EXACT SAME candidate_packed_validator.validate_packed) and the
EXISTING errors.ResourceAdmissionRefusal/SourceGenerationMismatch/
SidecarCorrupt classes -- no second authored validator, no new
exception types reaching callers. Never edits any frozen file.

`sidecar_artifact_sha256` is computed from the ALREADY-READ in-memory
buffer (hashlib.sha256(data)), not a second disk read -- mathematically
identical result to the current sidecar_contract._sha256_of_file(path),
zero behavior change, one fewer full read.
"""
import binascii
import hashlib
import os
import sys

sys.path.insert(0, r"E:\SFM Animation Group Master\tests\sidecar\qualification")
from b2f1f_resource_shape_estimator import (  # noqa: E402
    parse_resource_shape, preflight_region_size, estimate_retained, estimate_transient,
    PreflightCorruptOrIncompatible, ESTIMATOR_MODEL_VERSION, fmt,
)

RETAINED_GATE_BYTES = 16 * 1024 * 1024
TRANSIENT_GATE_BYTES = 32 * 1024 * 1024  # 33,554,432 bytes exactly (32 MiB)


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
        self.estimator_model_version = ESTIMATOR_MODEL_VERSION
        self.retained_gate_bytes = RETAINED_GATE_BYTES
        self.transient_gate_bytes = TRANSIENT_GATE_BYTES

    def to_dict(self):
        return dict((k, getattr(self, k)) for k in self.__slots__)


def candidate_open_and_identify_with_preflight(path, expected_source_sha256, runtime_cap_bytes,
                                                sidecar_contract_mod, errors_mod, descriptors_mod,
                                                inst=None):
    """Returns (provider, identity) with `provider` left OPEN -- caller
    owns it and must eventually .close() it. Raises the EXISTING, real
    error classes (never a locally-invented type):
      errors.ResourceAdmissionRefusal  -- valid but resource-expensive
      errors.SourceGenerationMismatch  -- embedded source_sha256 mismatch
      errors.SidecarCorrupt            -- malformed/fails structural validation

    `sidecar_contract_mod`/`errors_mod`/`descriptors_mod` are passed in
    explicitly (the real, unmodified sfm_master_authority modules) so
    this file never hardcodes its own import path assumptions about
    where the authority package lives -- callers (candidate selection/
    cohort modules) already have them loaded."""
    if inst is None:
        inst = CandidateOpenInstrumentation()
    inst.candidate_path = path
    inst.runtime_cap_bytes = runtime_cap_bytes

    f = open(path, "rb")
    inst.file_open_count += 1
    try:
        artifact_bytes = os.fstat(f.fileno()).st_size
        inst.raw_artifact_bytes = artifact_bytes
        if artifact_bytes > runtime_cap_bytes:
            inst.outcome = "refused"
            inst.reason = "artifact_bytes"
            raise errors_mod.ResourceAdmissionRefusal(
                "sidecar file size %d exceeds runtime admission cap %d bytes -- refusing to read "
                "(preflight Gate A, no estimator parse needed)" % (artifact_bytes, runtime_cap_bytes)
            )

        header_bytes = f.read(fmt.HEADER_SIZE)
        shape = None
        try:
            region_size = preflight_region_size(header_bytes)
            f.seek(0)
            prefix = f.read(region_size)
            inst.preflight_bytes_read = len(prefix)
            shape = parse_resource_shape(prefix, artifact_bytes)
        except PreflightCorruptOrIncompatible:
            inst.preflight_parse_deferred = True
            shape = None
        except Exception:
            inst.preflight_parse_deferred = True
            shape = None

        if shape is not None:
            est_retained = estimate_retained(shape)
            est_transient = estimate_transient(shape, runtime_cap_bytes)
            inst.estimated_retained_bytes = est_retained
            inst.estimated_transient_bytes = est_transient
            if est_retained > RETAINED_GATE_BYTES:
                inst.outcome = "refused"
                inst.reason = "estimated_retained"
                raise errors_mod.ResourceAdmissionRefusal(
                    "preflight estimated retained charge %d bytes exceeds retained gate %d bytes "
                    "(estimator_model_version=%s)" % (est_retained, RETAINED_GATE_BYTES, ESTIMATOR_MODEL_VERSION)
                )
            if est_transient > TRANSIENT_GATE_BYTES:
                inst.outcome = "refused"
                inst.reason = "estimated_transient"
                raise errors_mod.ResourceAdmissionRefusal(
                    "preflight estimated transient delta %d bytes exceeds transient gate %d bytes "
                    "(estimator_model_version=%s)" % (est_transient, TRANSIENT_GATE_BYTES, ESTIMATOR_MODEL_VERSION)
                )

        f.seek(0)
        data = f.read(runtime_cap_bytes + 1)
        inst.full_bounded_read_call_count += 1
        inst.full_bounded_read_bytes_returned = len(data)
        if len(data) > runtime_cap_bytes:
            inst.outcome = "refused"
            inst.reason = "post_read_length"
            raise errors_mod.ResourceAdmissionRefusal(
                "sidecar content exceeds runtime admission cap %d bytes" % runtime_cap_bytes
            )
    finally:
        f.close()
        inst.file_close_count += 1

    sidecar_contract_mod.ensure_loaded()
    provider_mod = sidecar_contract_mod._provider_module
    try:
        provider = provider_mod.BoundedProvider._open_from_buf(data, expected_source_sha256, bound=True)
    except provider_mod.SourceMismatchError as exc:
        inst.outcome = "refused"
        inst.reason = "source_generation_mismatch"
        raise errors_mod.SourceGenerationMismatch(str(exc))
    except provider_mod.AuthorityUnavailable as exc:
        msg = str(exc)
        inst.outcome = "refused"
        if "admission cap" in msg:
            inst.reason = "estimated_transient_post_read"
            raise errors_mod.ResourceAdmissionRefusal(msg)
        inst.reason = "corrupt"
        raise errors_mod.SidecarCorrupt(msg)
    inst.validator_call_count += 1
    inst.outcome = "accepted"
    inst.reason = None

    header = provider._header
    embedded_source_hex = binascii.hexlify(header.source_sha256).decode("ascii").lower()
    identity = descriptors_mod.ArtifactIdentity(
        sidecar_artifact_sha256=hashlib.sha256(data).hexdigest(),  # in-memory -- no second disk read
        format_contract_version=header.format_contract_version,
        authority_semantics_version=header.authority_semantics_version,
        projection_contract_version=None,
        embedded_source_sha256=embedded_source_hex,
        embedded_source_byte_length=header.source_byte_length,
    )
    return provider, identity, inst
