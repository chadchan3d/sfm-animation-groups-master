# -*- coding: utf-8 -*-
"""Final targeted infrastructure correction -- BLOCKER 1 fixture builder.

Builds ONE real, compiled, self-validated small artifact, then produces
six RELOCATED-DIRECTORY variants (same technique as the second-
correction gate's original F1 reproduction: patch `section_directory_
offset` in the header directly, copy the real directory-row bytes to
the new location, leave the embedded integrity digest stale -- these
fixtures are for PREFLIGHT READ-SIZE/ALLOCATION measurement only, never
expected to reach final admission, so a stale digest is fine and
deliberate), at directory offsets: 64 KiB, 1 MiB, 8 MiB, 12 MiB, 15 MiB,
and 15.9 MiB (near 16 MiB while still comfortably under the raw cap).
Every artifact stays under the 16 MiB raw cap itself.

Path-relative (Astra Narrow Issue E / Blocker 3.E): repo root derived
from `__file__`.
"""
import hashlib
import json
import os
import shutil
import struct
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
FIXROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction4", "fixtures_offset_sweep")

if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from sfm_master_sidecar import compiler  # noqa: E402
from sfm_master_sidecar import format as fmt  # noqa: E402

if os.path.isdir(FIXROOT):
    shutil.rmtree(FIXROOT)
os.makedirs(FIXROOT)

# A small but non-trivial base artifact -- a handful of groups/controls,
# genuinely compiled and self-validated.
BASE_MASTER_TEXT = (
    '"groupFile"\n{\n'
    + "".join('\t"control"\t\t"OffsetSweepControl%03d"\n' % i for i in range(50))
    + "\n}\n"
)
base_data = BASE_MASTER_TEXT.encode("utf-8")
snapshot = compiler.SourceSnapshot(path="<synthetic:offset_sweep_base>", data=base_data)
outcome = compiler.parse_and_compile(snapshot)
compiler.self_validate_from_bytes(outcome)
base_blob = outcome.blob
print("[base] master_sha=%s artifact_bytes=%d" % (hashlib.sha256(base_data).hexdigest()[:16], len(base_blob)))

with open(os.path.join(FIXROOT, "base_master.txt"), "wb") as f:
    f.write(base_data)

OFFSETS = [
    ("64KiB", 64 * 1024),
    ("1MiB", 1 * 1024 * 1024),
    ("8MiB", 8 * 1024 * 1024),
    ("12MiB", 12 * 1024 * 1024),
    ("15MiB", 15 * 1024 * 1024),
    ("15p9MiB", int(15.9 * 1024 * 1024)),
]

RAW_CAP_BYTES = 16 * 1024 * 1024
MANIFEST = {"base_master_sha256": hashlib.sha256(base_data).hexdigest(), "raw_cap_bytes": RAW_CAP_BYTES, "offsets": {}}

header = fmt.unpack_header(base_blob[:fmt.HEADER_SIZE], 0)
dir_size = header.section_count * fmt.DIRECTORY_ROW_SIZE
old_dir_bytes = base_blob[header.section_directory_offset:header.section_directory_offset + dir_size]

for label, new_offset in OFFSETS:
    new_total_size = new_offset + dir_size + 4096  # pad a little past the relocated directory
    if new_total_size >= RAW_CAP_BYTES:
        raise RuntimeError("offset %r would push the fixture over the raw cap" % (label,))
    buf = bytearray(base_blob)
    if len(buf) < new_total_size:
        buf.extend(b"\x00" * (new_total_size - len(buf)))
    buf[new_offset:new_offset + dir_size] = old_dir_bytes
    struct.pack_into("<Q", buf, 64, new_offset)  # section_directory_offset field
    out_path = os.path.join(FIXROOT, "offset_%s.sfmsidecar" % label)
    with open(out_path, "wb") as f:
        f.write(bytes(buf))
    MANIFEST["offsets"][label] = {
        "artifact_relative_path": os.path.basename(out_path),
        "directory_offset_bytes": new_offset,
        "artifact_bytes": len(buf),
    }
    print("[built] offset=%-9s directory_offset=%10d artifact_bytes=%d" % (label, new_offset, len(buf)))

with open(os.path.join(FIXROOT, "manifest.json"), "w") as f:
    json.dump(MANIFEST, f, indent=2, sort_keys=True)

print("\nFixture root:", FIXROOT)
