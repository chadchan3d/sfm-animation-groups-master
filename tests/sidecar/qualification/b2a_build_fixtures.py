# -*- coding: utf-8 -*-
"""One-time fixture builder for B2A offline tests. Python 3 only (uses
os.link for real hardlinks -- Python 2.7 on Windows has no os.link, but
the ACTUAL test assertions only ever READ these pre-built fixtures, never
create hardlinks themselves, so this asymmetry is fine)."""
import os
import shutil

FIXROOT = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures"

if os.path.isdir(FIXROOT):
    shutil.rmtree(FIXROOT)
os.makedirs(FIXROOT)

# --- install_a: a fake SFM install tree with a real Master file ---
install_a_tools = os.path.join(FIXROOT, "install_a", "bin", "tools")
os.makedirs(install_a_tools)
ifm_a = os.path.join(install_a_tools, "ifm.dll")
with open(ifm_a, "wb") as f:
    f.write(b"FAKE_IFM_DLL_PLACEHOLDER")

master_a_dir = os.path.join(FIXROOT, "install_a", "usermod", "cfg")
os.makedirs(master_a_dir)
master_a = os.path.join(master_a_dir, "sfm_defaultanimationgroups.txt")
with open(master_a, "wb") as f:
    f.write(b'"RigArms"\n{\n\t"control"\t\t"Example"\n}\n')

# --- mod_a: corroborating valve-mod path, HARDLINKED to the SAME file as install_a's Master ---
mod_a_cfg = os.path.join(FIXROOT, "mod_a", "cfg")
os.makedirs(mod_a_cfg)
mod_a_master = os.path.join(mod_a_cfg, "sfm_defaultanimationgroups.txt")
os.link(master_a, mod_a_master)  # real hardlink -- same file, different path string

# --- mod_b: a DIFFERENT, independently-created file (disagreement case) ---
mod_b_cfg = os.path.join(FIXROOT, "mod_b", "cfg")
os.makedirs(mod_b_cfg)
mod_b_master = os.path.join(mod_b_cfg, "sfm_defaultanimationgroups.txt")
with open(mod_b_master, "wb") as f:
    f.write(b'"RigArms"\n{\n\t"control"\t\t"Example"\n}\n')  # same CONTENT, different actual file

# --- mod_empty: valve-mod dir with NO Master file (corroborator "unavailable" case) ---
os.makedirs(os.path.join(FIXROOT, "mod_empty", "cfg"))

# --- install_no_master: ifm.dll present, but no Master file at all ---
install_nm_tools = os.path.join(FIXROOT, "install_no_master", "bin", "tools")
os.makedirs(install_nm_tools)
with open(os.path.join(install_nm_tools, "ifm.dll"), "wb") as f:
    f.write(b"FAKE_IFM_DLL_PLACEHOLDER")
os.makedirs(os.path.join(FIXROOT, "install_no_master", "usermod", "cfg"))

# --- install_bad_layout: ifm.dll NOT under tools/bin (AmbiguousMasterPath case) ---
bad_dir = os.path.join(FIXROOT, "install_bad_layout", "not_bin", "not_tools")
os.makedirs(bad_dir)
with open(os.path.join(bad_dir, "ifm.dll"), "wb") as f:
    f.write(b"FAKE_IFM_DLL_PLACEHOLDER")

# --- a standalone Master fixture for H0/H1 tests (freely mutable) ---
h01_dir = os.path.join(FIXROOT, "h01")
os.makedirs(h01_dir)
h01_master = os.path.join(h01_dir, "master.txt")
with open(h01_master, "wb") as f:
    f.write(b"ORIGINAL_MASTER_CONTENT_V1")

# --- shipped_root_valid: a copy of the REAL official sidecar artifact ---
real_artifact = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r2_formal_deploy\official_sidecar_artifact.bin"
)
shipped_valid = os.path.join(FIXROOT, "shipped_root_valid")
os.makedirs(shipped_valid)
shutil.copyfile(real_artifact, os.path.join(shipped_valid, "official.sfmsidecar"))

# --- shipped_root_empty: exists but has no .sfmsidecar files ---
os.makedirs(os.path.join(FIXROOT, "shipped_root_empty"))

# --- local_corrupt_test: pre-built corrupt + valid local generation store,
#     built ONCE here under Python 3 (uses corruption_helpers.py, which
#     itself requires pathlib and is by-design Python 3+ only), so the
#     shared dual-interpreter test file never needs to import
#     corruption_helpers/pathlib under Python 2.7 -- it only READS these
#     already-built files. ---
import hashlib
import json
import sys

sys.path.insert(0, r"E:\SFM Animation Group Master\tests\sidecar")
from corruption_helpers import MutableSidecar  # noqa: E402

with open(os.path.join(shipped_valid, "official.sfmsidecar"), "rb") as f:
    real_bytes = f.read()

REAL_MASTER_SHA = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"

ms = MutableSidecar(real_bytes)
ms.set_group_row(0, occ_by_group_count=0xFFFFFFF0)
ms.recompute_checksum()
corrupt_bytes = ms.bytes()
corrupt_sha = hashlib.sha256(corrupt_bytes).hexdigest()
valid_sha = hashlib.sha256(real_bytes).hexdigest()

lct_root = os.path.join(FIXROOT, "local_corrupt_test")
lct_store = os.path.join(lct_root, "generated", "sfmsidecar_v1")
os.makedirs(lct_store)

with open(os.path.join(lct_store, corrupt_sha + ".sfmsidecar"), "wb") as f:
    f.write(corrupt_bytes)
with open(os.path.join(lct_store, valid_sha + ".sfmsidecar"), "wb") as f:
    f.write(real_bytes)


def _write_pointer(path, artifact_sha):
    with open(path, "w") as f:
        json.dump({
            "master_sha256": REAL_MASTER_SHA,
            "master_byte_length": 123,
            "artifact_sha256": artifact_sha,
            "artifact_relative_path": "sfmsidecar_v1/%s.sfmsidecar" % artifact_sha,
            "format_contract_version": 1,
            "authority_semantics_version": 1,
        }, f)


_write_pointer(os.path.join(lct_root, "current_pointer_corrupt.json"), corrupt_sha)
_write_pointer(os.path.join(lct_root, "current_pointer_valid.json"), valid_sha)

with open(os.path.join(lct_root, "identities.json"), "w") as f:
    json.dump({
        "real_master_sha256": REAL_MASTER_SHA,
        "corrupt_artifact_sha256": corrupt_sha,
        "valid_artifact_sha256": valid_sha,
        "corrupt_artifact_path": os.path.join(lct_store, corrupt_sha + ".sfmsidecar"),
        "valid_artifact_path": os.path.join(lct_store, valid_sha + ".sfmsidecar"),
        "generated_root": os.path.join(lct_root, "generated"),
        "pointer_corrupt_path": os.path.join(lct_root, "current_pointer_corrupt.json"),
        "pointer_valid_path": os.path.join(lct_root, "current_pointer_valid.json"),
    }, f, indent=2)

print("fixtures built under", FIXROOT)
for root, dirs, files in os.walk(FIXROOT):
    for name in files:
        p = os.path.join(root, name)
        print(" ", p, os.path.getsize(p), "bytes")
