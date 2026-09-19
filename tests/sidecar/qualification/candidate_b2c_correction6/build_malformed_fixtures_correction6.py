# -*- coding: utf-8 -*-
"""Correction6 deterministic malformed-fixture builder.

Builds three fixtures used by the Correction6 decisive regressions
(`test_b2c_correction6_preread_floor.py`), each failing preflight
parsing for a DIFFERENT reason, so the new shape-independent floor
check's ordering (Section 3 of the governing prompt) is exercised
against more than one failure mode:

- `malformed_1kib.sfmsidecar`  -- 1024 bytes, bad magic (all zero
  bytes). Fails at the very first check in
  `_validate_header_and_bound_directory_region` ("magic mismatch").
  Used for Section 5.A (decisive) and 5.B (low-retained, corruption
  classification still observable).
- `unsupported_format.sfmsidecar` -- valid magic, valid-size header,
  but `format_contract_version=999` (not in `NORMATIVE_ROW_SIZES`).
  Fails on the "unsupported format_contract_version" check -- one step
  further into header validation than the bad-magic case. Used for
  Section 5.C.
- `truncated_directory.sfmsidecar` -- valid magic, valid
  format_contract_version=0, valid section_count=9, but the file is
  deliberately too short for the declared directory region to fit
  (`section_directory_offset + section_count*DIRECTORY_ROW_SIZE >
  artifact_bytes`). Fails on the "section directory region extends
  past artifact_bytes" check -- reachable only once magic/version/
  section_count all pass. Used for Section 5.D.

None of these fixtures need be REAL, validator-passing sidecars --
every one of them is deliberately malformed at the preflight stage,
never intended to reach the frozen structural validator successfully.

Deterministic, idempotent (re-running overwrites with byte-identical
output), no dependency on any other candidate directory.
"""
import json
import os
import struct
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.normpath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir, os.pardir))
_TOOLS_DIR = os.path.join(_REPO_ROOT, "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from sfm_master_sidecar import format as fmt  # noqa: E402

FIXROOT = os.path.join(_THIS_DIR, "fixtures_malformed")


def build_malformed_1kib():
    """1024 bytes, all zero -- magic mismatch (0x00*8 != b'SFMMSTR\\x00')."""
    return b"\x00" * 1024


def build_unsupported_format():
    """A minimal, valid-size (>= HEADER_SIZE) buffer with correct magic,
    an unsupported format_contract_version, and otherwise-plausible
    header fields. Total size 1024 bytes (comfortably >= HEADER_SIZE=108,
    well under any runtime cap used by the decisive tests)."""
    header = fmt.Header(
        magic=fmt.MAGIC,
        format_contract_version=999,  # not in fmt.NORMATIVE_ROW_SIZES
        authority_semantics_version=0,
        source_sha256=b"\x00" * 32,
        source_byte_length=0,
        payload_length=0,
        section_directory_offset=fmt.HEADER_SIZE,
        section_count=len(fmt.SECTION_ORDER),
        embedded_integrity_digest=b"\x00" * 32,
    )
    packed = fmt.pack_header(header)
    return packed + b"\x00" * (1024 - len(packed))


def build_truncated_directory():
    """Valid magic, valid format_contract_version=0, valid
    section_count=9 (so the FIRST two checks in `_validate_header_and_
    bound_directory_region` both pass) -- but the file is deliberately
    only HEADER_SIZE + 4 bytes long, far short of HEADER_SIZE + 9 *
    DIRECTORY_ROW_SIZE (252) bytes the declared directory region would
    require. Fails on 'section directory region extends past
    artifact_bytes' specifically -- a distinct failure point from both
    other fixtures, reachable only once magic/version/section_count
    have already passed."""
    header = fmt.Header(
        magic=fmt.MAGIC,
        format_contract_version=fmt.FORMAT_CONTRACT_VERSION_EXPERIMENTAL,
        authority_semantics_version=fmt.AUTHORITY_SEMANTICS_VERSION_EXPERIMENTAL,
        source_sha256=b"\x00" * 32,
        source_byte_length=0,
        payload_length=0,
        section_directory_offset=fmt.HEADER_SIZE,
        section_count=len(fmt.SECTION_ORDER),
        embedded_integrity_digest=b"\x00" * 32,
    )
    packed = fmt.pack_header(header)
    # HEADER_SIZE + 4 bytes total -- nowhere near enough for the
    # declared 9 * 28 = 252-byte directory region starting right after
    # the header.
    return packed + b"\x00" * 4


def main():
    if not os.path.isdir(FIXROOT):
        os.makedirs(FIXROOT)

    fixtures = {
        "malformed_1kib": build_malformed_1kib(),
        "unsupported_format": build_unsupported_format(),
        "truncated_directory": build_truncated_directory(),
    }
    manifest = {"fixtures": {}}
    for name, data in fixtures.items():
        rel_path = "%s.sfmsidecar" % name
        with open(os.path.join(FIXROOT, rel_path), "wb") as f:
            f.write(data)
        manifest["fixtures"][name] = {
            "artifact_relative_path": rel_path,
            "artifact_bytes": len(data),
        }
    with open(os.path.join(FIXROOT, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")

    for name, entry in sorted(manifest["fixtures"].items()):
        print("%-20s %5d bytes -> %s" % (name, entry["artifact_bytes"], entry["artifact_relative_path"]))


if __name__ == "__main__":
    main()
