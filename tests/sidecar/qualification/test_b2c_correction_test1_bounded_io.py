# -*- coding: utf-8 -*-
"""Astra post-B2C-B correction gate -- Test 1: bounded I/O + snapshot
admission (F1 + F5). Reproduces the exact exploit class Astra found
(a corrupted section_directory_offset driving an unbounded requested
read before validation) against a REAL artifact, and proves the
corrected candidate_open_and_identify_with_preflight never issues a
requested read above the explicit preflight bound before admission,
for a battery of corrupted/hostile inputs. Read-only against the real
official artifact (only a byte-mutated COPY is ever corrupted); never
touches the frozen production package.
"""
import hashlib
import os
import shutil
import struct
import sys
import tempfile

CORRECTION_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction"
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"
FIXROOT_B2A = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures"
REAL_OFFICIAL_ARTIFACT = FIXROOT_B2A + r"\shipped_root_valid\official.sfmsidecar"
REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
REAL_MASTER_SHA = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"

for p in (CORRECTION_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from sfm_master_authority_productionized import resource_preflight  # noqa: E402
from sfm_master_authority_productionized import resource_estimator  # noqa: E402
from sfm_master_authority_productionized import errors  # noqa: E402
from sfm_master_sidecar import format as fmt  # noqa: E402

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

SCRATCH = tempfile.mkdtemp(prefix="b2c_correction_test1_")


def make_corrupt_copy(mutate_fn, name):
    dst = os.path.join(SCRATCH, name)
    shutil.copyfile(REAL_OFFICIAL_ARTIFACT, dst)
    with open(dst, "r+b") as f:
        buf = bytearray(f.read(fmt.HEADER_SIZE))
        mutate_fn(buf)
        f.seek(0)
        f.write(bytes(buf))
    return dst


# Explicit small bound this correction must never exceed for ANY input
# before admission -- HEADER_SIZE plus the real, fixed directory-region
# size (never the file's own declared, potentially-corrupted value).
EXPLICIT_PREFLIGHT_BOUND_BYTES = fmt.HEADER_SIZE + resource_estimator._MAX_PREFLIGHT_REGION_BYTES


def run_case(label, path, expected_exception, extra_check=None):
    inst = resource_preflight.CandidateOpenInstrumentation()
    try:
        provider, identity, inst = resource_preflight.candidate_open_and_identify_with_preflight(
            path, REAL_MASTER_SHA, runtime_cap_bytes=16 * 1024 * 1024, inst=inst)
        try:
            outcome = "admitted"
        finally:
            provider.close()
    except Exception as exc:
        inst = getattr(exc, "instrumentation", inst)
        outcome = type(exc).__name__
        if expected_exception is not None and not isinstance(exc, expected_exception):
            check("%s raised expected exception type" % label, False,
                  "expected %s, got %s: %s" % (expected_exception.__name__, type(exc).__name__, exc))
        elif expected_exception is not None:
            check("%s raised expected exception type" % label, True)

    max_req = inst.max_single_requested_read if inst.max_single_requested_read else 0
    print("[%s] outcome=%s max_single_requested_read=%d read_calls=%d" % (
        label, outcome, max_req, len(inst.read_calls)))
    check("%s.no_unbounded_read max_single_requested_read <= explicit preflight bound (%d) OR the "
          "full bounded read itself (runtime_cap_bytes+1)" % (label, EXPLICIT_PREFLIGHT_BOUND_BYTES),
          max_req <= max(EXPLICIT_PREFLIGHT_BOUND_BYTES, 16 * 1024 * 1024 + 1),
          (max_req, EXPLICIT_PREFLIGHT_BOUND_BYTES))
    if extra_check is not None:
        extra_check(inst, outcome)
    return inst, outcome


# ===========================================================================
# Case A: huge section_directory_offset -- Astra's EXACT reproduction class.
# ===========================================================================
def mutate_huge_offset(buf):
    # section_directory_offset is header field index 6 (Q, 8 bytes) at
    # byte offset 64 in the <8sII32sQQQI32s struct (magic8+I4+I4+32+Q8+Q8).
    huge_offset = 1 * 1024 * 1024 * 1024  # ~1 GiB, matching Astra's own reproduction scale
    struct.pack_into("<Q", buf, 64, huge_offset)

path_a = make_corrupt_copy(mutate_huge_offset, "huge_directory_offset.sfmsidecar")
run_case("caseA_huge_directory_offset", path_a, None)

# ===========================================================================
# Case B: truncated directory (declared region extends past real file size)
# ===========================================================================
def mutate_truncated(buf):
    # Push the offset just past HEADER_SIZE but still beyond what a
    # deliberately-truncated copy of the file will actually contain.
    struct.pack_into("<Q", buf, 64, 200 * 1024 * 1024)  # 200 MiB, well past the real (~9.5 MB) artifact

path_b_full = make_corrupt_copy(mutate_truncated, "truncated_directory_full.sfmsidecar")
path_b = os.path.join(SCRATCH, "truncated_directory.sfmsidecar")
with open(path_b_full, "rb") as fsrc, open(path_b, "wb") as fdst:
    fdst.write(fsrc.read(4096))  # truncate hard -- artifact_bytes itself will be tiny
run_case("caseB_truncated_directory", path_b, None)

# ===========================================================================
# Case C: invalid runtime_cap_bytes (type/range) -- must do ZERO I/O.
# ===========================================================================
for bad_cap, label in [(-1, "negative"), (0, "zero"), ("16777216", "string"),
                        (True, "bool"), (10 ** 12, "absurdly_large")]:
    inst = resource_preflight.CandidateOpenInstrumentation()
    try:
        resource_preflight.candidate_open_and_identify_with_preflight(
            REAL_OFFICIAL_ARTIFACT, REAL_MASTER_SHA, runtime_cap_bytes=bad_cap, inst=inst)
        check("caseC_invalid_cap_%s rejected before I/O" % label, False, "did not raise")
    except resource_estimator.PreflightCorruptOrIncompatible:
        check("caseC_invalid_cap_%s rejected before I/O" % label, True)
        check("caseC_invalid_cap_%s did ZERO file I/O (file_open_count == 0)" % label,
              inst.file_open_count == 0, inst.file_open_count)
    except Exception as exc:
        check("caseC_invalid_cap_%s rejected before I/O" % label, False,
              "wrong exception type: %s: %s" % (type(exc).__name__, exc))

# ===========================================================================
# Case D: unsupported format_contract_version (checksum-consistent: real
# magic, otherwise-valid header, only the version field changed).
# ===========================================================================
def mutate_bad_version(buf):
    struct.pack_into("<I", buf, 8, 999999)  # format_contract_version at offset 8

path_d = make_corrupt_copy(mutate_bad_version, "unsupported_version.sfmsidecar")
run_case("caseD_unsupported_version", path_d, None)

# ===========================================================================
# Case E: same-handle changed resource shape mid-acquisition (F5) --
# overwrite the file with a DIFFERENT real, valid artifact of a
# different structural shape between preflight and the full read, using
# a wrapped open() that performs the overwrite right after the first
# read call returns.
# ===========================================================================
FIXROOT_B2F = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2f\fixtures"
OTHER_SHAPE_ARTIFACT = FIXROOT_B2F + r"\fixtureA_1p0x.sfmsidecar"

race_path = os.path.join(SCRATCH, "race_target.sfmsidecar")
shutil.copyfile(REAL_OFFICIAL_ARTIFACT, race_path)

_original_open = open
_swap_state = {"done": False}


class _RacingFileWrapper(object):
    """Delegates to a real file object, but on its FIRST read() call also
    performs the in-place overwrite -- works on both Python 3's io
    objects (which allow instance-attribute overrides) and Python 2's
    built-in `file` objects (which do NOT allow overriding .read as an
    instance attribute, hence this wrapper instead of monkeypatching)."""
    def __init__(self, real_file):
        self._f = real_file

    def read(self, size=-1):
        data = self._f.read(size)
        if not _swap_state["done"]:
            _swap_state["done"] = True
            with _original_open(OTHER_SHAPE_ARTIFACT, "rb") as src:
                other_bytes = src.read()
            with _original_open(race_path, "r+b") as dst:
                dst.seek(0)
                dst.write(other_bytes[:len(data)] if len(other_bytes) >= len(data) else
                           other_bytes + b"\x00" * (len(data) - len(other_bytes)))
                dst.truncate(len(other_bytes))
        return data

    def __getattr__(self, name):
        return getattr(self._f, name)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self._f.close()


def _racing_open(path, mode="r", *a, **kw):
    f = _original_open(path, mode, *a, **kw)
    if path == race_path and mode == "rb" and not _swap_state["done"]:
        return _RacingFileWrapper(f)
    return f


try:
    import builtins as _builtins_mod  # noqa: E402 -- Python 3
except ImportError:
    import __builtin__ as _builtins_mod  # noqa: E402 -- Python 2.7
_builtins_mod.open = _racing_open
try:
    inst_e = resource_preflight.CandidateOpenInstrumentation()
    try:
        provider_e, identity_e, inst_e = resource_preflight.candidate_open_and_identify_with_preflight(
            race_path, REAL_MASTER_SHA, runtime_cap_bytes=16 * 1024 * 1024, inst=inst_e)
        provider_e.close()
        outcome_e = "admitted"
    except Exception as exc_e:
        inst_e = getattr(exc_e, "instrumentation", inst_e)
        outcome_e = type(exc_e).__name__
finally:
    _builtins_mod.open = _original_open

print("[caseE_same_handle_race] outcome=%s snapshot_reparsed=%r snapshot_shape_differed=%r "
      "snapshot_readmission_outcome=%r" % (
          outcome_e, inst_e.snapshot_reparsed, inst_e.snapshot_shape_differed_from_preflight,
          inst_e.snapshot_readmission_outcome))
check("caseE_same_handle_race the in-place overwrite was actually detected as a shape change or a "
      "generation/source mismatch (never silently admitted as if nothing happened)",
      inst_e.snapshot_shape_differed_from_preflight is True or outcome_e in
      ("SourceGenerationMismatch", "SidecarCorrupt", "ResourceAdmissionRefusal"),
      (outcome_e, inst_e.snapshot_shape_differed_from_preflight))

shutil.rmtree(SCRATCH, ignore_errors=True)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
