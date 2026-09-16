# -*- coding: utf-8 -*-
"""Bounded pointer file parsing -- ASTRA_CORRECTED.md Section 13.

Parsing/reading scope ONLY. B2A never writes/replaces a pointer -- that
is B2E's responsibility (rebuild publication + mutex), not implemented
here.
"""
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
    "master_sha256", "master_byte_length", "artifact_sha256",
    "artifact_relative_path", "format_contract_version",
    "authority_semantics_version",
)


class PointerRecord(object):
    __slots__ = _REQUIRED_FIELDS

    def __init__(self, **kwargs):
        for f in _REQUIRED_FIELDS:
            setattr(self, f, kwargs[f])

    def __repr__(self):
        return "PointerRecord(master_sha256=%r, artifact_sha256=%r)" % (
            self.master_sha256, self.artifact_sha256,
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

    if not _HEX64_RE.match(str(data["master_sha256"])):
        raise errors.LocalPointerCorrupt("pointer %r master_sha256 is not 64 hex characters" % (path,))
    if not _HEX64_RE.match(str(data["artifact_sha256"])):
        raise errors.LocalPointerCorrupt("pointer %r artifact_sha256 is not 64 hex characters" % (path,))

    mbl = data["master_byte_length"]
    if not isinstance(mbl, _INTEGER_TYPES) or isinstance(mbl, bool) or mbl < 0:
        raise errors.LocalPointerCorrupt("pointer %r master_byte_length must be a non-negative integer" % (path,))

    for field in ("format_contract_version", "authority_semantics_version"):
        v = data[field]
        if not isinstance(v, _INTEGER_TYPES) or isinstance(v, bool):
            raise errors.LocalPointerCorrupt("pointer %r %s must be an integer" % (path, field))

    rel_path = data["artifact_relative_path"]
    _reject_unsafe_relative_path(path, rel_path)

    return PointerRecord(
        master_sha256=str(data["master_sha256"]).lower(),
        master_byte_length=mbl,
        artifact_sha256=str(data["artifact_sha256"]).lower(),
        artifact_relative_path=rel_path,
        format_contract_version=data["format_contract_version"],
        authority_semantics_version=data["authority_semantics_version"],
    )


def _reject_unsafe_relative_path(pointer_path, rel_path):
    if not isinstance(rel_path, _STRING_TYPES):
        raise errors.LocalPointerCorrupt(
            "pointer %r artifact_relative_path must be a string" % (pointer_path,)
        )
    if os.path.isabs(rel_path):
        raise errors.LocalPointerCorrupt(
            "pointer %r artifact_relative_path must not be absolute" % (pointer_path,)
        )
    if ":" in rel_path:  # drive letters ("C:...") and Alternate Data Streams ("file.txt:stream")
        raise errors.LocalPointerCorrupt(
            "pointer %r artifact_relative_path must not contain ':'" % (pointer_path,)
        )
    if rel_path.startswith("\\\\") or rel_path.startswith("//"):
        raise errors.LocalPointerCorrupt(
            "pointer %r artifact_relative_path must not be a UNC path" % (pointer_path,)
        )
    normalized = rel_path.replace("\\", "/")
    parts = normalized.split("/")
    if any(p == ".." for p in parts):
        raise errors.LocalPointerCorrupt(
            "pointer %r artifact_relative_path contains '..'" % (pointer_path,)
        )


def derive_artifact_path(generated_root, pointer_record):
    """Prefer deriving the path from (namespace, artifact SHA) rather
    than trusting the pointer's own free-form relative-path text --
    ASTRA_CORRECTED.md Section 13. B2A uses a single fixed namespace;
    multi-namespace support is a later (B2E) concern. The pointer's own
    `artifact_relative_path` is retained on the record for a future
    cross-check, never used here as the sole path authority."""
    return os.path.join(generated_root, "sfmsidecar_v1", pointer_record.artifact_sha256 + ".sfmsidecar")
