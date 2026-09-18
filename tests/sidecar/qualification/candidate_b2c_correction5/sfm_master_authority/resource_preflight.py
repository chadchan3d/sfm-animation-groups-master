# -*- coding: utf-8 -*-
"""R3-B2C productionized single canonical open-and-identify primitive.

=== Independent RE-AUDIT of 6e942f6 (2026-09-18) -- Correction5 ===

The Correction4 preliminary (pre-full-read) gate correctly folded
`aggregate_existing_retained_bytes` into its RETAINED comparison, but
its TRANSIENT comparison compared the incoming/preliminary transient
estimate alone against `TRANSIENT_GATE_BYTES` -- omitting the same
`aggregate_existing_retained_bytes` term that the authoritative,
post-full-read `resource_estimator.evaluate_cumulative_admission`
already includes in its own transient sum (interpretation B, added in
Correction3). Independently reproduced: preliminary incoming transient
~23,075,300 B + existing retained 10,485,760 B = 33,561,060 B, over the
32 MiB (33,554,432 B) gate -- yet the one full bounded read still ran
once before the later, correctly-aggregated Stage 3 check refused.
Fixed by computing the same aggregate sum (`aggregate_existing_
retained_bytes + prelim_transient`) BEFORE deciding whether the full
read is allowed, using the identical `aggregate_existing_retained_
bytes` input already passed into this function -- no second,
independent notion of retained authority.

=== Independent RE-AUDIT of 6bf803f (2026-09-18) -- BLOCKER 1 ===

The prior (Correction3) fix bounded the directory-region READ, but this
module still reassembled a SPARSE prefix buffer (`bytearray(dir_region_
end)`) purely so `parse_resource_shape`'s absolute-offset indexing would
line up -- `dir_region_end` includes the file-controlled `section_
directory_offset`, so a genuinely valid artifact under the 16 MiB raw
cap with a large directory offset (e.g. 15.9 MiB) still forced an
allocation of comparable size BEFORE any resource-admission decision
(independently reproduced: ~8 MiB offset -> ~16 MiB peak, ~15.9 MiB ->
~31.8 MiB). Fixed by never reconstructing that sparse buffer at all:
`resource_estimator.parse_resource_shape_parts(header_bytes,
directory_bytes, artifact_bytes)` consumes the two already-separately-
bounded buffers directly, indexing directory rows at LOCAL offsets
within `directory_bytes` rather than the file's absolute offset.
Preliminary-stage allocation here is now proportional only to
HEADER_SIZE + the bounded directory region, never to `section_
directory_offset` itself -- a `seek()` costs nothing to allocate for,
only to move to.

=== Astra SECOND correction gate (2026-09-16) -- re-opening F1/F2/F5 ===

F1 (re-opened): the FIRST correction's `checked_preflight_region_size`
correctly BOUNDED the directory-region size to `_MAX_PREFLIGHT_REGION_
BYTES` (64 KiB) and validated it against `artifact_bytes` -- but the
actual READ this module issued still spanned from byte 0 through
`section_directory_offset + directory_size`, i.e. the WHOLE prefix up
to wherever the directory happens to sit. A valid file with a
`section_directory_offset` of, say, 8 MiB (still comfortably under the
16 MiB raw-artifact cap, still a genuinely small, well-formed
directory region once you get there) therefore still caused an ~8 MiB
preflight read, before any admission decision -- Astra's exact
reproduction. Fixed here: after validating the header, this module now
`seek()`s DIRECTLY to `section_directory_offset` and reads ONLY the
bounded directory-row bytes (`section_count * DIRECTORY_ROW_SIZE`,
capped at `_MAX_PREFLIGHT_REGION_BYTES` = 64 KiB) -- never the bytes in
between. The fixed-header read and the directory read are now two
SEPARATE, individually bounded reads, both recorded distinctly in
`CandidateOpenInstrumentation` (`header_bytes_read`,
`directory_bytes_read`, `preflight_bytes_read` = their sum) -- no
mixing of the later full-read size into the preflight assertion.

F2/F5 (re-opened together, since they turned out to share one root
cause): the FIRST correction's "snapshot re-admission" called the
estimator with a REDUCED signature (missing requested_fold_count and
the aggregate ledger), so a full-read snapshot that genuinely changed
into a shape the corrected, request-aware estimator would otherwise
have refused could still slip through. Rather than patching that
reduced path to remember to pass the same arguments (which is exactly
the kind of duplication that caused the original gap), this module was
restructured so there is only ONE way admission ever happens: after the
one full bounded read, `resource_estimator.parse_resource_shape` is
(re)computed from the ACTUAL read buffer (never the earlier, smaller
preflight prefix), REAL packed per-family occurrence counts are
obtained from that SAME buffer via `packed_family_counts.py` (before
the frozen structural validator ever runs -- see that module's own
docstring for why), and `resource_estimator.evaluate_cumulative_
admission` is called EXACTLY ONCE, unconditionally, every time -- there
is no separate/parallel "preflight-only" admission decision left in
this file at all; the header+directory-only preliminary estimate
(`estimate_retained_preliminary`/`estimate_transient_preliminary`) is
retained ONLY as an optional early-rejection filter for a candidate
whose fixed header/directory ALONE already prove it structurally
hopeless (e.g. an absurd raw group/metadata/occurrence/fold count) --
explicitly documented as non-authoritative, and even when it fires
early, the real full read + real cumulative check is what a later
snapshot-replacement scenario would still have to pass, since the
early filter can only REJECT early, never ADMIT early.

Reuses the EXISTING, unmodified BoundedProvider._open_from_buf (hence
the EXACT SAME candidate_packed_validator.validate_packed) and the
EXISTING errors.ResourceAdmissionRefusal/SourceGenerationMismatch/
SidecarCorrupt/FormatUnsupported classes -- no second authored
validator, no new exception types reaching callers.

`sidecar_artifact_sha256` is computed from the ALREADY-READ in-memory
buffer (hashlib.sha256(data)), not a second disk read.

STILL A CANDIDATE, isolated under tests/sidecar/qualification/
candidate_b2c_correction2/ -- a NEW isolated candidate derived from the
first correction (candidate_b2c_correction/), which itself remains
unmodified as historical evidence, and the frozen production package,
always untouched.
"""
import binascii
import hashlib
import os

from . import errors
from . import descriptors
from . import sidecar_contract
from . import resource_estimator
from . import packed_family_counts

fmt = resource_estimator.fmt

RETAINED_GATE_BYTES = 16 * 1024 * 1024
TRANSIENT_GATE_BYTES = 32 * 1024 * 1024  # exactly 32 MiB -- see B2F1F F6's "33 MiB" mislabeling note, carried
                                          # forward corrected.


class ReadCallRecord(object):
    __slots__ = ("label", "requested_size", "bytes_returned", "position_before", "position_after")

    def __init__(self, label, requested_size, bytes_returned, position_before, position_after):
        self.label = label
        self.requested_size = requested_size
        self.bytes_returned = bytes_returned
        self.position_before = position_before
        self.position_after = position_after

    def to_dict(self):
        return {
            "label": self.label, "requested_size": self.requested_size, "bytes_returned": self.bytes_returned,
            "position_before": self.position_before, "position_after": self.position_after,
        }


class CandidateOpenInstrumentation(object):
    __slots__ = (
        "candidate_path", "file_open_count", "file_close_count",
        "raw_artifact_bytes",
        # Astra F1: fixed-header and directory reads recorded SEPARATELY
        # -- never mixed with the later full-read size.
        "header_bytes_read", "directory_bytes_read", "preflight_bytes_read",
        "preflight_parse_deferred",
        "full_bounded_read_call_count", "full_bounded_read_bytes_returned",
        "validator_call_count", "estimator_model_version",
        "retained_gate_bytes", "transient_gate_bytes", "runtime_cap_bytes",
        "outcome", "reason",
        "read_calls", "max_single_requested_read",
        # Astra F2: the REAL, authoritative cumulative-admission result
        # (resource_estimator.CumulativeAdmissionResult.to_dict()) --
        # None if the candidate never reached that stage (e.g. refused
        # by the cheap preliminary filter, or by structural corruption).
        "cumulative_admission",
        # Astra F5: whether the shape derived from the FULL read buffer
        # differed from the (optional) cheap preliminary shape --
        # diagnostic only; does not gate anything separately, since the
        # cumulative admission check always runs against the ACTUAL
        # final buffer regardless.
        "preliminary_shape_present", "final_shape_differed_from_preliminary",
    )

    def __init__(self):
        for k in self.__slots__:
            setattr(self, k, None)
        self.file_open_count = 0
        self.file_close_count = 0
        self.header_bytes_read = 0
        self.directory_bytes_read = 0
        self.preflight_bytes_read = 0
        self.preflight_parse_deferred = False
        self.full_bounded_read_call_count = 0
        self.validator_call_count = 0
        self.estimator_model_version = resource_estimator.ESTIMATOR_MODEL_VERSION
        self.retained_gate_bytes = RETAINED_GATE_BYTES
        self.transient_gate_bytes = TRANSIENT_GATE_BYTES
        self.read_calls = []
        self.max_single_requested_read = 0
        self.preliminary_shape_present = False
        self.final_shape_differed_from_preliminary = False

    def record_read(self, label, requested_size, bytes_returned, position_before, position_after):
        rec = ReadCallRecord(label, requested_size, bytes_returned, position_before, position_after)
        self.read_calls.append(rec)
        if requested_size > self.max_single_requested_read:
            self.max_single_requested_read = requested_size

    def to_dict(self):
        d = dict((k, getattr(self, k)) for k in self.__slots__ if k != "read_calls")
        d["read_calls"] = [r.to_dict() for r in self.read_calls]
        return d


def _instrumented_read(f, size, inst, label):
    """The ONLY way this module reads from an open file handle -- every
    call is labeled and recorded (requested size, bytes actually
    returned, position before/after)."""
    position_before = f.tell()
    data = f.read(size)
    position_after = f.tell()
    inst.record_read(label, size, len(data), position_before, position_after)
    return data


def candidate_open_and_identify_with_preflight(path, expected_source_sha256, runtime_cap_bytes=None, inst=None,
                                                requested_folds_by_consumer=None,
                                                aggregate_existing_retained_bytes=0):
    """Returns (provider, identity, instrumentation) with `provider` left
    OPEN -- caller owns it and must eventually .close() it. Raises the
    EXISTING, real error classes:
      errors.ResourceAdmissionRefusal  -- valid but resource-expensive
      errors.SourceGenerationMismatch  -- embedded source_sha256 mismatch
      errors.SidecarCorrupt            -- malformed/fails structural validation
      errors.FormatUnsupported         -- checksum-consistent but declares
                                           an unsupported format_contract_version

    `requested_folds_by_consumer` (Astra F2): {consumer_kind:
    iterable_of_already_folded_keys} -- the REAL per-consumer requested
    fold sets for this acquisition. None/empty means "no requested
    vocabulary is known" (e.g. a pure identity probe) -- the cumulative
    admission check then has zero folded-payload cost to add (still
    correctly charges hierarchy/metadata/provider-decode/validator-
    scratch costs, which are independent of any request).

    `aggregate_existing_retained_bytes` (Astra F2): the broker's own
    ledger total BEFORE this acquisition, so admission reflects what the
    process ALREADY retains, not a single-artifact-in-isolation view."""
    if inst is None:
        inst = CandidateOpenInstrumentation()
    inst.candidate_path = path
    if requested_folds_by_consumer is None:
        requested_folds_by_consumer = {}

    sidecar_contract.ensure_loaded()
    if runtime_cap_bytes is None:
        runtime_cap_bytes = sidecar_contract._provider_module.DEFAULT_RUNTIME_ADMISSION_CAP_BYTES
    else:
        runtime_cap_bytes = resource_estimator.validate_runtime_cap_bytes(runtime_cap_bytes)
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

        # --- Stage 1 (Astra F1): fixed-header read, then seek DIRECTLY
        # to the validated directory offset and read ONLY the bounded
        # directory-row bytes. Never the whole prefix in between. ---
        header_bytes = _instrumented_read(f, fmt.HEADER_SIZE, inst, "header")
        inst.header_bytes_read = len(header_bytes)
        preliminary_shape = None
        try:
            if len(header_bytes) < fmt.HEADER_SIZE:
                raise resource_estimator.PreflightCorruptOrIncompatible("buffer shorter than fixed header size")
            header = fmt.unpack_header(header_bytes, 0)
            dir_region_end = resource_estimator._validate_header_and_bound_directory_region(header, artifact_bytes)
            directory_size = dir_region_end - header.section_directory_offset
            f.seek(header.section_directory_offset)
            directory_bytes = _instrumented_read(f, directory_size, inst, "directory")
            inst.directory_bytes_read = len(directory_bytes)
            inst.preflight_bytes_read = inst.header_bytes_read + inst.directory_bytes_read
            if len(directory_bytes) < directory_size:
                raise resource_estimator.PreflightCorruptOrIncompatible(
                    "directory read returned fewer bytes than the validated directory region size"
                )
            # Independent-re-audit BLOCKER 1 fix: the prior version
            # reconstructed a SPARSE prefix (`bytearray(dir_region_end)`)
            # purely so parse_resource_shape's absolute-offset indexing
            # would line up -- `dir_region_end` includes the file-
            # controlled `section_directory_offset`, so a valid artifact
            # under the raw cap with a large directory offset (e.g. 15.9
            # MiB) still forced an allocation of comparable size before
            # any admission decision. Fixed: parse_resource_shape_parts
            # consumes `header_bytes`/`directory_bytes` as two SEPARATE,
            # already-bounded buffers (never reassembled into one sparse
            # buffer) -- allocation here is proportional only to
            # HEADER_SIZE + the bounded directory region, never to
            # section_directory_offset itself.
            preliminary_shape = resource_estimator.parse_resource_shape_parts(
                header_bytes, directory_bytes, artifact_bytes)
            inst.preliminary_shape_present = True
        except resource_estimator.PreflightCorruptOrIncompatible:
            # Do NOT invent a corruption verdict here -- preflight is a
            # negative admission filter only. Fall through to the real
            # full validation path, which remains the sole authority on
            # corruption/incompatibility.
            inst.preflight_parse_deferred = True
            preliminary_shape = None
        except Exception:
            inst.preflight_parse_deferred = True
            preliminary_shape = None

        if preliminary_shape is not None:
            # Cheap, EARLY, NON-AUTHORITATIVE rejection only -- can only
            # REFUSE early (an obviously-hopeless whole-artifact shape,
            # using the file-wide average); never ADMITS on its own. The
            # real, authoritative decision always happens later, against
            # the actual full-read buffer.
            total_requested_folds = sum(len(v) for v in requested_folds_by_consumer.values())
            prelim_retained = resource_estimator.estimate_retained_preliminary(
                preliminary_shape, requested_fold_count=total_requested_folds)
            prelim_transient = resource_estimator.estimate_transient_preliminary(
                preliminary_shape, runtime_cap_bytes, requested_fold_count=total_requested_folds)
            if (aggregate_existing_retained_bytes + prelim_retained) > RETAINED_GATE_BYTES:
                inst.outcome = "refused"
                inst.reason = "preliminary_estimated_retained"
                exc = errors.ResourceAdmissionRefusal(
                    "preliminary (header+directory-only) estimate: retained charge %d bytes plus "
                    "existing %d bytes would exceed the retained gate %d bytes -- refusing before "
                    "the full read (estimator_model_version=%s)" % (
                        prelim_retained, aggregate_existing_retained_bytes, RETAINED_GATE_BYTES,
                        resource_estimator.ESTIMATOR_MODEL_VERSION)
                )
                exc.instrumentation = inst
                raise exc
            # Independent-re-audit Correction5 fix: the aggregate
            # cumulative transient model (resource_estimator.
            # evaluate_cumulative_admission, "interpretation B") counts
            # aggregate_existing_retained_bytes as part of the 32 MiB
            # transient envelope, because that many bytes are already
            # resident authority state for the whole acquisition window.
            # This preliminary, PRE-FULL-READ gate must apply that same
            # aggregate figure BEFORE deciding whether the one full
            # bounded read (`f.read(runtime_cap_bytes + 1)` below) is
            # even allowed to happen -- otherwise a request whose
            # preliminary/incoming transient estimate alone is under the
            # gate can still perform the full read once, and only refuse
            # afterward, once the final Stage 3 cumulative check adds
            # existing retained state. Uses the SAME
            # aggregate_existing_retained_bytes input the caller already
            # passed in (the broker's own ledger figure) -- no second,
            # independent notion of retained authority is introduced.
            prelim_total_transient = aggregate_existing_retained_bytes + prelim_transient
            if prelim_total_transient > TRANSIENT_GATE_BYTES:
                inst.outcome = "refused"
                inst.reason = "preliminary_estimated_transient"
                exc = errors.ResourceAdmissionRefusal(
                    "preliminary (header+directory-only) estimate: transient delta %d bytes plus "
                    "existing %d bytes would exceed the transient gate %d bytes -- refusing before "
                    "the full read (estimator_model_version=%s)" % (
                        prelim_transient, aggregate_existing_retained_bytes, TRANSIENT_GATE_BYTES,
                        resource_estimator.ESTIMATOR_MODEL_VERSION)
                )
                exc.instrumentation = inst
                raise exc

        # --- Stage 2: the ONE full bounded read (bounded by
        # runtime_cap_bytes+1 regardless, per Gate A above -- not new,
        # not caused by resource estimation). ---
        f.seek(0)
        data = _instrumented_read(f, runtime_cap_bytes + 1, inst, "full_bounded_read")
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

    # --- Stage 3 (Astra F2+F5): THE canonical, authoritative admission,
    # against the ACTUAL final buffer, BEFORE the frozen structural
    # validator runs -- unconditional, always run exactly this one way,
    # regardless of what the preliminary stage saw or skipped. ---
    try:
        final_header = fmt.unpack_header(data[:fmt.HEADER_SIZE], 0)
        dir_end = resource_estimator._validate_header_and_bound_directory_region(final_header, len(data))
        # Same BLOCKER 1 fix applied here too: `data[:dir_end]` would
        # copy up to the whole directory-offset-sized prefix out of the
        # already-fully-read buffer; slicing out only the bounded
        # directory region (≤ _MAX_PREFLIGHT_REGION_BYTES) and using
        # parse_resource_shape_parts avoids that redundant large copy.
        final_directory_bytes = data[final_header.section_directory_offset:dir_end]
        final_shape = resource_estimator.parse_resource_shape_parts(
            data[:fmt.HEADER_SIZE], final_directory_bytes, len(data))
    except resource_estimator.PreflightCorruptOrIncompatible:
        final_shape = None
    except Exception:
        final_shape = None

    if preliminary_shape is not None and final_shape is not None:
        differed = any(
            getattr(final_shape, field) != getattr(preliminary_shape, field)
            for field in final_shape.__slots__ if field != "directory_rows"
        )
        inst.final_shape_differed_from_preliminary = differed
    elif preliminary_shape is not None and final_shape is None:
        # Preflight parsed a shape, but the SAME header region within the
        # full-read snapshot no longer parses at all -- the candidate
        # changed into something structurally broken between the two
        # reads. Fail closed.
        inst.final_shape_differed_from_preliminary = True
        inst.outcome = "refused"
        inst.reason = "snapshot_unparseable_after_preliminary"
        exc = errors.SidecarCorrupt(
            "full-read snapshot no longer parses as the structurally valid shape the preliminary "
            "stage saw -- the candidate changed between the header/directory read and the full read"
        )
        exc.instrumentation = inst
        raise exc

    if final_shape is not None:
        packed_counts_by_consumer = dict(
            (consumer_kind, packed_family_counts.get_packed_family_counts_batch(data, final_shape, folds))
            for consumer_kind, folds in requested_folds_by_consumer.items()
        )
        admission = resource_estimator.evaluate_cumulative_admission(
            final_shape, packed_counts_by_consumer, runtime_cap_bytes,
            RETAINED_GATE_BYTES, TRANSIENT_GATE_BYTES,
            aggregate_existing_retained_bytes=aggregate_existing_retained_bytes,
        )
        inst.cumulative_admission = admission.to_dict()
        if not admission.admitted:
            inst.outcome = "refused"
            inst.reason = admission.reason
            exc = errors.ResourceAdmissionRefusal(
                "cumulative admission refused: reason=%s total_retained=%d total_transient=%d "
                "aggregate_existing=%d max_single_family=%r (estimator_model_version=%s)" % (
                    admission.reason, admission.total_retained_bytes, admission.total_transient_bytes,
                    admission.aggregate_existing_retained_bytes, admission.max_single_family_fold,
                    resource_estimator.ESTIMATOR_MODEL_VERSION)
            )
            exc.instrumentation = inst
            raise exc
    # else: neither preliminary nor final could parse a shape at all --
    # unchanged from prior behavior of deferring entirely to the full
    # validator as sole authority on corruption.

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
        try:
            header_for_classification = fmt.unpack_header(data[:fmt.HEADER_SIZE], 0)
            if (header_for_classification.magic == fmt.MAGIC
                    and header_for_classification.format_contract_version not in fmt.NORMATIVE_ROW_SIZES):
                inst.reason = "format_unsupported"
                raise errors.FormatUnsupported(msg)
        except errors.FormatUnsupported:
            raise
        except Exception:
            pass
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
