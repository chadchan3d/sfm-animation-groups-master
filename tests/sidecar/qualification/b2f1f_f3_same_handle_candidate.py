# -*- coding: utf-8 -*-
"""R3-B2F1F Stage F3: test-only same-open-handle pre-admission
integration prototype. NOT production code. Never edits any frozen
file; reuses the EXISTING, unmodified BoundedProvider._open_from_buf
(hence the EXACT same candidate_packed_validator.validate_packed
structural validation -- no duplicate parser, no second decoder) and
the EXISTING sfm_master_authority.errors.ResourceAdmissionRefusal type
(never a locally-invented exception reaching the caller).

Flow (design doc Section 2 / prompt Section 2):
  1. open the candidate path ONCE
  2. fstat the OPEN handle for raw artifact_bytes (Gate A)
  3. read the preflight region (<=360 bytes) from the SAME handle
  4. parse ResourceShape (B2F1F F1/F2, unmodified) -- on any parse
     failure (malformed header/directory), DO NOT invent a corruption
     verdict here: rewind and fall through to the existing full
     validation path, which remains the sole authority on
     corruption/incompatibility (preflight is a negative filter only,
     per the design doc's own Decision statement)
  5. compute estimated retained/transient (B2F1F F1/F2, unmodified)
  6. Gate B/C: refuse (ResourceAdmissionRefusal) before any full read
  7. if admitted: reposition the SAME handle, perform the bounded read
     with the SAME cap+1/length-check discipline _read_path_bounded
     itself uses (mirrored here only because that function is private
     and path-opening; the design doc's own Section 2 explicitly
     allows an "internal open-handle path" for this reason), close the
     handle (bytes are now in memory, exactly matching
     _read_path_bounded's own close-after-read timing), then hand the
     buffer to the EXISTING BoundedProvider._open_from_buf
"""
import os
import sys

B2A_DEPLOY_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r3_b2a_broker_deploy"
)
GATE_R2_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r2_formal_deploy"
)
if B2A_DEPLOY_DIR not in sys.path:
    sys.path.insert(0, B2A_DEPLOY_DIR)
if GATE_R2_DIR not in sys.path:
    sys.path.insert(0, GATE_R2_DIR)

sys.path.insert(0, r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\67454949-e69f-4280-93d9-87c1f4464330\scratchpad")
from b2f1f_resource_shape_estimator import (  # noqa: E402
    parse_resource_shape, preflight_region_size, estimate_retained, estimate_transient,
    PreflightCorruptOrIncompatible, ESTIMATOR_MODEL_VERSION, fmt,
)

from sfm_master_authority import sidecar_contract, errors  # noqa: E402

RETAINED_GATE_BYTES = 16 * 1024 * 1024
TRANSIENT_GATE_BYTES = 32 * 1024 * 1024  # 33,554,432 bytes -- this IS 32 MiB exactly (not 33 MiB;
# an earlier comment here mislabeled it and added a spurious extra 1 MiB via "+ 1024*1024",
# making the actual threshold used 34,603,008 instead of the intended 33,554,432. Caught and
# fixed in R3-B2F1F Stage F4; verified against the full F1-F3 qualification corpus that no
# fixture's estimated_transient fell in that 1 MiB band, so no prior classification changes.


class Instrumentation(object):
    def __init__(self):
        self.candidate_path = None
        self.file_open_count = 0
        self.file_close_count = 0
        self.handle_identity_before = None
        self.handle_identity_after = None
        self.raw_artifact_bytes = None
        self.preflight_bytes_read = 0
        self.full_bounded_read_call_count = 0
        self.full_bounded_read_bytes_returned = None
        self.validator_call_count = 0
        self.projection_builder_call_count = 0
        self.estimator_model_version = ESTIMATOR_MODEL_VERSION
        self.estimated_retained_bytes = None
        self.retained_gate_bytes = RETAINED_GATE_BYTES
        self.estimated_transient_bytes = None
        self.transient_gate_bytes = TRANSIENT_GATE_BYTES
        self.runtime_cap_bytes = None
        self.outcome = None
        self.reason = None
        self.published_detached_view_count = 0
        self.post_build_retained_charge = None
        self.preflight_parse_deferred = False

    def to_dict(self):
        return dict(self.__dict__)


def _file_identity(f):
    """Windows file-identity tuple derived from the already-open handle
    (fileno + fstat), never a second pathname-based stat -- used only to
    PROVE same-handle use before/after positioning, per the prompt's
    Section 2 'Hard same-handle proof'."""
    st = os.fstat(f.fileno())
    return (f.fileno(), st.st_dev, st.st_ino, st.st_size, st.st_mtime)


def candidate_open_path_with_preflight(path, expected_source_sha256, runtime_cap_bytes, inst=None):
    """Returns an opened BoundedProvider (caller must .close() it) on
    admission. Raises errors.ResourceAdmissionRefusal (the REAL, frozen
    exception type) on any gate failure -- never a locally-invented
    exception reaching the caller."""
    if inst is None:
        inst = Instrumentation()
    inst.candidate_path = path
    inst.runtime_cap_bytes = runtime_cap_bytes

    f = open(path, "rb")
    inst.file_open_count += 1
    inst.handle_identity_before = _file_identity(f)
    try:
        # Gate A -- raw artifact size, via fstat on the ALREADY-OPEN handle.
        artifact_bytes = os.fstat(f.fileno()).st_size
        inst.raw_artifact_bytes = artifact_bytes
        if artifact_bytes > runtime_cap_bytes:
            inst.outcome = "refused"
            inst.reason = "artifact_bytes"
            raise errors.ResourceAdmissionRefusal(
                "sidecar file size %d exceeds runtime admission cap %d bytes -- refusing to read "
                "(preflight Gate A, no estimator parse needed)" % (artifact_bytes, runtime_cap_bytes)
            )

        # Preflight region, read from the SAME handle.
        header_bytes = f.read(fmt.HEADER_SIZE)
        shape = None
        try:
            region_size = preflight_region_size(header_bytes)
            f.seek(0)
            prefix = f.read(region_size)
            inst.preflight_bytes_read = len(prefix)
            shape = parse_resource_shape(prefix, artifact_bytes)
        except PreflightCorruptOrIncompatible:
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
            est_retained = estimate_retained(shape)
            est_transient = estimate_transient(shape, runtime_cap_bytes)
            inst.estimated_retained_bytes = est_retained
            inst.estimated_transient_bytes = est_transient
            if est_retained > RETAINED_GATE_BYTES:
                inst.outcome = "refused"
                inst.reason = "estimated_retained"
                raise errors.ResourceAdmissionRefusal(
                    "preflight estimated retained charge %d bytes exceeds retained gate %d bytes "
                    "(estimator_model_version=%s)" % (est_retained, RETAINED_GATE_BYTES, ESTIMATOR_MODEL_VERSION)
                )
            if est_transient > TRANSIENT_GATE_BYTES:
                inst.outcome = "refused"
                inst.reason = "estimated_transient"
                raise errors.ResourceAdmissionRefusal(
                    "preflight estimated transient delta %d bytes exceeds transient gate %d bytes "
                    "(estimator_model_version=%s)" % (est_transient, TRANSIENT_GATE_BYTES, ESTIMATOR_MODEL_VERSION)
                )

        # Admitted (or preflight deferred) -- reposition the SAME handle
        # and perform the existing bounded-read discipline exactly
        # (cap+1 request, length check) -- mirrors _read_path_bounded's
        # own enforcement, on this already-open handle.
        f.seek(0)
        data = f.read(runtime_cap_bytes + 1)
        inst.full_bounded_read_call_count += 1
        inst.full_bounded_read_bytes_returned = len(data)
        inst.handle_identity_after = _file_identity(f)
        if len(data) > runtime_cap_bytes:
            inst.outcome = "refused"
            inst.reason = "post_read_length"
            raise errors.ResourceAdmissionRefusal(
                "sidecar content exceeds runtime admission cap %d bytes" % runtime_cap_bytes
            )
    finally:
        f.close()
        inst.file_close_count += 1

    # Hand off to the EXISTING, unmodified provider construction -- runs
    # the EXACT same candidate_packed_validator.validate_packed. Error
    # mapping below mirrors sidecar_contract.validate_selected_artifact's
    # OWN mapping exactly (same except clauses, same classification
    # logic) -- not reinvented, so corruption vs. resource-refusal
    # classification stays identical to the existing pipeline's.
    sidecar_contract.ensure_loaded()
    provider_mod = sidecar_contract._provider_module
    try:
        provider = provider_mod.BoundedProvider._open_from_buf(data, expected_source_sha256, bound=True)
    except provider_mod.SourceMismatchError as exc:
        inst.outcome = "refused"
        inst.reason = "source_generation_mismatch"
        raise errors.SourceGenerationMismatch(str(exc))
    except provider_mod.AuthorityUnavailable as exc:
        msg = str(exc)
        inst.outcome = "refused"
        if "admission cap" in msg:
            inst.reason = "estimated_transient_post_read"  # the frozen post-read len(data)>cap check
            raise errors.ResourceAdmissionRefusal(msg)
        inst.reason = "corrupt"
        raise errors.SidecarCorrupt(msg)
    inst.validator_call_count += 1
    inst.outcome = "accepted"
    inst.reason = None
    return provider, inst
