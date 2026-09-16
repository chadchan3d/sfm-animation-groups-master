# -*- coding: utf-8 -*-
"""B2B fixture builder (Python 3 only -- uses corruption_helpers.py,
which requires pathlib). Produces a REAL, genuinely byte-different,
fully-validator-accepted "artifact B" sharing the exact same
`source_sha256` as the real official artifact ("artifact A"), by
reordering the SECTION DIRECTORY's own row positions (semantically
invisible to the validator, which looks sections up by section_id in a
dict, never by positional order) -- proven for real in this same session
before being adopted here, not assumed."""
import hashlib
import json
import os
import shutil
import sys

FIXROOT = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures_b2b"
if os.path.isdir(FIXROOT):
    shutil.rmtree(FIXROOT)
os.makedirs(FIXROOT)

sys.path.insert(0, r"E:\SFM Animation Group Master\tests\sidecar")
sys.path.insert(0, r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm\gate_r2_formal_deploy")
from corruption_helpers import MutableSidecar  # noqa: E402
import candidate_packed_validator as validator  # noqa: E402

REAL_ARTIFACT_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r2_formal_deploy\official_sidecar_artifact.bin"
)
REAL_MASTER_SHA = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"

with open(REAL_ARTIFACT_PATH, "rb") as f:
    bytes_a = f.read()

ms = MutableSidecar(bytes_a)
rows = ms.directory_rows()
row0 = rows[0][1]
row1 = rows[1][1]
ms.set_directory_row_at_index(0, section_id=row1.section_id, offset=row1.offset,
                               length=row1.length, row_count=row1.row_count, row_size=row1.row_size)
ms.set_directory_row_at_index(1, section_id=row0.section_id, offset=row0.offset,
                               length=row0.length, row_count=row0.row_count, row_size=row0.row_size)
ms.recompute_checksum()
bytes_b = ms.bytes()

header_a, _ = validator.validate_packed(bytes_a)
header_b, _ = validator.validate_packed(bytes_b)
assert header_a.source_sha256 == header_b.source_sha256, "fixture build invariant violated"
assert hashlib.sha256(bytes_a).hexdigest() != hashlib.sha256(bytes_b).hexdigest(), "fixture build invariant violated"

sha_a = hashlib.sha256(bytes_a).hexdigest()
sha_b = hashlib.sha256(bytes_b).hexdigest()

shipped_two_artifacts = os.path.join(FIXROOT, "shipped_two_artifacts")
os.makedirs(shipped_two_artifacts)
with open(os.path.join(shipped_two_artifacts, "artifact_a.sfmsidecar"), "wb") as f:
    f.write(bytes_a)
with open(os.path.join(shipped_two_artifacts, "artifact_b.sfmsidecar"), "wb") as f:
    f.write(bytes_b)

with open(os.path.join(FIXROOT, "identities.json"), "w") as f:
    json.dump({
        "real_master_sha256": REAL_MASTER_SHA,
        "artifact_a_sha256": sha_a,
        "artifact_b_sha256": sha_b,
        "shipped_two_artifacts_root": shipped_two_artifacts,
    }, f, indent=2)

print("B2B fixtures built under", FIXROOT)
print("artifact A sha256:", sha_a)
print("artifact B sha256:", sha_b)
print("both share source_sha256:", REAL_MASTER_SHA)
