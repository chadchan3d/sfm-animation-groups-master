# -*- coding: utf-8 -*-
"""Bounded pointer file parsing -- ASTRA_CORRECTED.md Section 13.

Parsing/reading scope ONLY. B2A never writes/replaces a pointer -- that
is B2E's responsibility (rebuild publication + mutex), not implemented
here.

Package-Boundary Correction (2026-09-21), Astra-reproduced defect B:
this module's field schema (`master_sha256`/`master_byte_length`/
`artifact_sha256`/`artifact_relative_path`) was never reconciled with
the ONE real, supported publication format `tools/sfm_master_sidecar/
publisher.py`/`manifest.py` actually produce (`source_sha256`/
`source_byte_length`/`sidecar_sha256`/`generation_basename`) -- nothing
in this project ever wrote a pointer file this module's OLD schema
could parse; a real `manifest.json` from the real publisher raised
`LocalPointerCorrupt: missing required field 'master_sha256'`. Fields
below are renamed to match `manifest.py` EXACTLY -- `manifest.json`
IS the pointer file for both the local-candidate (qualification-mode)
and shipped-root paths now; there is no second, independent pointer
schema."""
import json
import os
import re

from . import errors

try:
    _STRING_TYPES = (str, unicode)  # noqa: F821 -- Python 2.7 only
except NameError:
    _STRING_TYPES = (str,)

try:
    _INTEGER_TYPES = (int, long)  # noqa: F821 -- Python 2.7 only
except NameError:
    _INTEGER_TYPES = (int,)

MAX_POINTER_FILE_BYTES = 8192
_HEX64_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_REQUIRED_FIELDS = (
    "source_sha256", "source_byte_length", "sidecar_sha256",
    "generation_basename", "format_contract_version",
    "authority_semantics_version",
)


class PointerRecord(object):
    __slots__ = _REQUIRED_FIELDS

    def __init__(self, **kwargs):
        for f in _REQUIRED_FIELDS:
            setattr(self, f, kwargs[f])

    def __repr__(self):
        return "PointerRecord(source_sha256=%r, sidecar_sha256=%r)" % (
            self.source_sha256, self.sidecar_sha256,
        )


def _reject_duplicate_keys(path, pairs):
    seen = set()
    result = {}
    for k, v in pairs:
        if k in seen:
            raise errors.LocalPointerCorrupt("pointer %r has a duplicate key %r" % (path, k))
        seen.add(k)
        result[k] = v
    return result


def load_pointer(path):
    """Read + parse a pointer file under strict bounds. Any structural
    problem is reported as LocalPointerCorrupt -- callers treat this as
    'no usable local pointer' (falls through to shipped), never as a
    reason to trust a partially-parsed result."""
    try:
        size = os.path.getsize(path)
    except OSError as exc:
        raise errors.LocalPointerCorrupt("cannot stat pointer %r: %r" % (path, exc))
    if size > MAX_POINTER_FILE_BYTES:
        raise errors.LocalPointerCorrupt(
            "pointer file %r is %d bytes, exceeding the %d-byte bound"
            % (path, size, MAX_POINTER_FILE_BYTES)
        )

    try:
        with open(path, "rb") as f:
            raw = f.read(MAX_POINTER_FILE_BYTES + 1)
    except (IOError, OSError) as exc:
        raise errors.LocalPointerCorrupt("cannot read pointer %r: %r" % (path, exc))
    if len(raw) > MAX_POINTER_FILE_BYTES:
        raise errors.LocalPointerCorrupt("pointer file %r exceeds the bounded read cap" % (path,))

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise errors.LocalPointerCorrupt("pointer %r is not valid UTF-8: %r" % (path, exc))

    try:
        data = json.loads(text, object_pairs_hook=lambda pairs: _reject_duplicate_keys(path, pairs))
    except ValueError as exc:  # json.JSONDecodeError is a ValueError subclass (both interpreters)
        raise errors.LocalPointerCorrupt("pointer %r is not valid JSON: %r" % (path, exc))

    if not isinstance(data, dict):
        raise errors.LocalPointerCorrupt("pointer %r top-level JSON value must be an object" % (path,))

    for field in _REQUIRED_FIELDS:
        if field not in data:
            raise errors.LocalPointerCorrupt("pointer %r missing required field %r" % (path, field))

    if not _HEX64_RE.match(str(data["source_sha256"])):
        raise errors.LocalPointerCorrupt("pointer %r source_sha256 is not 64 hex characters" % (path,))
    if not _HEX64_RE.match(str(data["sidecar_sha256"])):
        raise errors.LocalPointerCorrupt("pointer %r sidecar_sha256 is not 64 hex characters" % (path,))

    sbl = data["source_byte_length"]
    if not isinstance(sbl, _INTEGER_TYPES) or isinstance(sbl, bool) or sbl < 0:
        raise errors.LocalPointerCorrupt("pointer %r source_byte_length must be a non-negative integer" % (path,))

    for field in ("format_contract_version", "authority_semantics_version"):
        v = data[field]
        if not isinstance(v, _INTEGER_TYPES) or isinstance(v, bool):
            raise errors.LocalPointerCorrupt("pointer %r %s must be an integer" % (path, field))

    basename = data["generation_basename"]
    _reject_unsafe_generation_basename(path, basename)

    return PointerRecord(
        source_sha256=str(data["source_sha256"]).lower(),
        source_byte_length=sbl,
        sidecar_sha256=str(data["sidecar_sha256"]).lower(),
        generation_basename=basename,
        format_contract_version=data["format_contract_version"],
        authority_semantics_version=data["authority_semantics_version"],
    )


def _reject_unsafe_generation_basename(pointer_path, basename):
    """`generation_basename` (Package-Boundary Correction, 2026-09-21:
    renamed from `artifact_relative_path` to match the real publisher's
    `manifest.py` schema exactly) is a BARE basename, never a path with
    directory components -- the real compiler's own `generation_
    basename()` never emits one, and `manifest.py`'s own `_is_safe_
    generation_basename` enforces the same rule on the publisher side.
    Stricter than the old "reject '..' segments" check this replaces:
    ANY path separator at all is rejected, not just traversal."""
    if not isinstance(basename, _STRING_TYPES):
        raise errors.LocalPointerCorrupt(
            "pointer %r generation_basename must be a string" % (pointer_path,)
        )
    if not basename or basename in (".", ".."):
        raise errors.LocalPointerCorrupt(
            "pointer %r generation_basename must be a non-empty bare basename" % (pointer_path,)
        )
    if os.path.isabs(basename):
        raise errors.LocalPointerCorrupt(
            "pointer %r generation_basename must not be absolute" % (pointer_path,)
        )
    if ":" in basename:  # drive letters ("C:...") and Alternate Data Streams ("file.txt:stream")
        raise errors.LocalPointerCorrupt(
            "pointer %r generation_basename must not contain ':'" % (pointer_path,)
        )
    if "/" in basename or "\\" in basename:
        raise errors.LocalPointerCorrupt(
            "pointer %r generation_basename must be a bare basename with no path separators" % (pointer_path,)
        )


def derive_artifact_path(generated_root, pointer_record):
    """Package-Boundary Correction (2026-09-21): the artifact lives
    directly alongside its manifest/pointer, in `generated_root` itself
    -- matching exactly where the real, ONE supported publisher (`tools/
    sfm_master_sidecar/publisher.py`) actually writes both the manifest
    and the immutable generation artifact together (the same directory
    `manifest.resolve_generation_path(output_dir, manifest_data)` uses
    on the publisher side). The previous `<generated_root>/sfmsidecar_v1/
    <artifact_sha256>.sfmsidecar` convention was never written by
    anything -- no publisher ever created that subdirectory or that
    naming scheme, so this path never resolved to a real file."""
    return os.path.join(generated_root, pointer_record.generation_basename)
