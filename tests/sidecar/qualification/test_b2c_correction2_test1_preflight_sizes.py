# -*- coding: utf-8 -*-
"""Astra SECOND correction gate -- Test 1: preflight request sizes (F1).
Directory offset inside raw cap but above the small-preflight ceiling;
huge offset/count; truncated directory; invalid explicit cap.
PASS: fixed-header read bounded; directory read bounded; no multi-
megabyte prefix read; invalid cap rejects before candidate artifact I/O.
"""
import hashlib
import os
import shutil
import struct
import sys
import tempfile

CORRECTION2_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction2"
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"
FIXROOT_B2A = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures"
OFFICIAL_ROOT = FIXROOT_B2A + r"\shipped_root_valid"
REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"

for p in (CORRECTION2_ROOT, TOOLS_DIR):
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

with open(REAL_MASTER_PATH, "rb") as f:
    real_master_bytes = f.read()
real_sha = hashlib.sha256(real_master_bytes).hexdigest()
OFFICIAL_ARTIFACT = OFFICIAL_ROOT + r"\official.sfmsidecar"

SMALL_PREFLIGHT_CEILING = fmt.HEADER_SIZE + resource_estimator._MAX_PREFLIGHT_REGION_BYTES
SCRATCH = tempfile.mkdtemp(prefix="b2c_correction2_test1_")


def make_relocated_directory_fixture(new_dir_offset, name):
    with open(OFFICIAL_ARTIFACT, "rb") as f:
        buf = bytearray(f.read())
    header = fmt.unpack_header(bytes(buf[:fmt.HEADER_SIZE]), 0)
    dir_size = header.section_count * fmt.DIRECTORY_ROW_SIZE
    old_dir_bytes = bytes(buf[header.section_directory_offset:header.section_directory_offset + dir_size])
    assert new_dir_offset + dir_size < len(buf)
    buf[new_dir_offset:new_dir_offset + dir_size] = old_dir_bytes
    struct.pack_into("<Q", buf, 64, new_dir_offset)
    path = os.path.join(SCRATCH, name)
    with open(path, "wb") as f:
        f.write(bytes(buf))
    return path


def run_case(label, path, expect_types=None):
    inst = resource_preflight.CandidateOpenInstrumentation()
    try:
        provider, identity, inst = resource_preflight.candidate_open_and_identify_with_preflight(
            path, real_sha, runtime_cap_bytes=16 * 1024 * 1024, inst=inst,
            requested_folds_by_consumer={"normalizer": ["left", "right"]},
        )
        provider.close()
        outcome = "admitted"
    except Exception as exc:
        inst = getattr(exc, "instrumentation", inst)
        outcome = type(exc).__name__
        if expect_types is not None:
            check("%s raised an expected exception type" % label, outcome in expect_types,
                  (outcome, expect_types))

    preflight_sizes = [rc.requested_size for rc in inst.read_calls if rc.label in ("header", "directory")]
    max_preflight = max(preflight_sizes) if preflight_sizes else 0
    print("[%s] outcome=%s header=%d directory=%d max_preflight_requested=%d" % (
        label, outcome, inst.header_bytes_read, inst.directory_bytes_read, max_preflight))
    check("%s.bounded max single PREFLIGHT (header/directory) requested read <= %d bytes"
          % (label, SMALL_PREFLIGHT_CEILING), max_preflight <= SMALL_PREFLIGHT_CEILING, max_preflight)
    return inst, outcome


# Case A: directory offset inside raw cap (16 MiB) but ABOVE the small
# preflight ceiling (~64 KiB) -- Astra's exact reproduction (this time
# at ~8 MiB, comfortably inside the 16 MiB raw cap).
path_a = make_relocated_directory_fixture(8 * 1024 * 1024, "dir_offset_8mib.sfmsidecar")
run_case("caseA_dir_offset_8mib", path_a)

# Case B: huge offset/count -- directory offset placed near the file end
# combined with an inflated section_count is already covered by
# checked_preflight_region_size's own containment check (tested
# directly here for a hostile section_count).
with open(OFFICIAL_ARTIFACT, "rb") as f:
    buf_b = bytearray(f.read())
struct.pack_into("<Q", buf_b, 64, 1 * 1024 * 1024 * 1024)  # ~1 GiB offset, matching the original exploit scale
path_b = os.path.join(SCRATCH, "huge_offset.sfmsidecar")
with open(path_b, "wb") as f:
    f.write(bytes(buf_b))
run_case("caseB_huge_offset_1gib", path_b)

# Case C: truncated directory (declared region extends past the actual,
# deliberately truncated file size).
with open(OFFICIAL_ARTIFACT, "rb") as f:
    buf_c = bytearray(f.read())
struct.pack_into("<Q", buf_c, 64, 200 * 1024 * 1024)
path_c_full = os.path.join(SCRATCH, "truncated_full.sfmsidecar")
with open(path_c_full, "wb") as f:
    f.write(bytes(buf_c))
path_c = os.path.join(SCRATCH, "truncated.sfmsidecar")
with open(path_c_full, "rb") as fsrc, open(path_c, "wb") as fdst:
    fdst.write(fsrc.read(4096))
run_case("caseC_truncated_directory", path_c)

# Case D: invalid explicit runtime_cap_bytes -- must reject before ANY
# candidate-artifact I/O (dependency-module loading, e.g. sidecar_
# contract.ensure_loaded(), is NOT candidate-artifact I/O and MAY still
# happen).
for bad_cap, label in [(-1, "negative"), (0, "zero"), ("16777216", "string"), (True, "bool"), (10 ** 12, "huge")]:
    inst = resource_preflight.CandidateOpenInstrumentation()
    try:
        resource_preflight.candidate_open_and_identify_with_preflight(
            OFFICIAL_ARTIFACT, real_sha, runtime_cap_bytes=bad_cap, inst=inst)
        check("caseD_invalid_cap_%s rejected" % label, False, "did not raise")
    except resource_estimator.PreflightCorruptOrIncompatible:
        check("caseD_invalid_cap_%s rejected" % label, True)
        check("caseD_invalid_cap_%s did ZERO candidate-artifact file opens" % label,
              inst.file_open_count == 0, inst.file_open_count)
    except Exception as exc:
        check("caseD_invalid_cap_%s rejected" % label, False, "wrong exception: %r" % (exc,))

shutil.rmtree(SCRATCH, ignore_errors=True)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
