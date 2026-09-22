# -*- coding: utf-8 -*-
"""Small JSON pointer manifest: build, serialize, and hardened-parse.

Python 3 only (compiler/publisher-side; the embedded runtime reader never
reads a manifest -- resolving which generation is active is a
host-application/Normalizer concern, entirely outside `reader.py`'s job).

Manifest content (final spec Section 33): a diagnostic pointer meaning only
"generation G was compiled from source hash X" -- never validation
authority, never re-derived as semantic truth. `counts` and
`compiler_build_version` are diagnostic only.
"""

import json
import re

from . import format as fmt

MAX_MANIFEST_BYTES = 64 * 1024  # generous; a manifest is a few hundred bytes in practice

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")

_REQUIRED_KEYS = {
    "generation_basename": str,
    "sidecar_sha256": str,
    "source_sha256": str,
    "source_byte_length": int,
    "format_contract_version": int,
    "authority_semantics_version": int,
    "counts": dict,
}

_REQUIRED_COUNT_KEYS = {"groups": int, "occurrences": int, "folds": int}

COMPILER_BUILD_VERSION = "0.1.0-experimental"


class ManifestError(Exception):
    """Base class for every manifest build/parse error."""


class ManifestData(object):
    __slots__ = (
        "generation_basename", "sidecar_sha256", "source_sha256", "source_byte_length",
        "format_contract_version", "authority_semantics_version", "counts",
        "compiler_build_version", "raw",
    )

    def __init__(self, d):
        self.generation_basename = d["generation_basename"]
        self.sidecar_sha256 = d["sidecar_sha256"]
        self.source_sha256 = d["source_sha256"]
        self.source_byte_length = d["source_byte_length"]
        self.format_contract_version = d["format_contract_version"]
        self.authority_semantics_version = d["authority_semantics_version"]
        self.counts = d["counts"]
        self.compiler_build_version = d.get("compiler_build_version")
        self.raw = d


def build_manifest_dict(outcome, generation_basename):
    """`outcome` is a `compiler.CompileOutcome`. Never includes anything
    that changes canonical binary bytes -- purely diagnostic fields plus the
    identity fields a consumer needs to locate/verify the generation."""
    result = outcome.result
    from . import writer as writer_module

    fams_count = len(_lazy_fold_families(result))
    return {
        "generation_basename": generation_basename,
        "sidecar_sha256": outcome.ordinary_sha256,
        "source_sha256": outcome.snapshot.sha256_hex,
        "source_byte_length": len(outcome.snapshot.bytes),
        "format_contract_version": fmt.FORMAT_CONTRACT_VERSION_EXPERIMENTAL,
        "authority_semantics_version": fmt.AUTHORITY_SEMANTICS_VERSION_EXPERIMENTAL,
        "compiler_build_version": COMPILER_BUILD_VERSION,
        "counts": {
            "groups": len(result.groups),
            "occurrences": len(result.occurrences),
            "folds": fams_count,
        },
    }


def _lazy_fold_families(result):
    import sfm_master_core as core
    return core.build_fold_families(result.occurrences)


def serialize_manifest(d):
    """Deterministic, human-readable JSON bytes. `sort_keys=True` so two
    manifests built from equal input dicts are byte-identical (diagnostic
    convenience, not a normative requirement)."""
    text = json.dumps(d, sort_keys=True, indent=2, ensure_ascii=True)
    if not text.endswith("\n"):
        text += "\n"
    return text.encode("utf-8")


class _DuplicateKeyError(ValueError):
    pass


def _no_duplicate_keys_hook(pairs):
    seen = set()
    d = {}
    for k, v in pairs:
        if k in seen:
            raise _DuplicateKeyError("duplicate JSON key %r" % (k,))
        seen.add(k)
        d[k] = v
    return d


def _is_safe_generation_basename(name):
    """Bare basename only -- no path separators, no `..`, no drive prefix,
    no leading slash/backslash, non-empty (Phase B2E Part 12)."""
    if not name or not isinstance(name, str):
        return False
    if "/" in name or "\\" in name:
        return False
    if name in (".", ".."):
        return False
    if ":" in name:  # rejects Windows drive prefixes like "C:"
        return False
    if name != name.strip():
        return False
    return True


def parse_manifest_bytes(data):
    """Hardened manifest parse. Raises `ManifestError` with a specific
    reason for any violation. Returns a `ManifestData` only if every check
    passes."""
    if len(data) > MAX_MANIFEST_BYTES:
        raise ManifestError("manifest exceeds maximum size (%d > %d bytes)" % (len(data), MAX_MANIFEST_BYTES))

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ManifestError("manifest is not valid UTF-8: %r" % (exc,))

    try:
        obj = json.loads(text, object_pairs_hook=_no_duplicate_keys_hook)
    except _DuplicateKeyError as exc:
        raise ManifestError(str(exc))
    except json.JSONDecodeError as exc:
        raise ManifestError("manifest is not valid JSON: %r" % (exc,))

    if not isinstance(obj, dict):
        raise ManifestError("manifest top level must be a JSON object")

    for key, expected_type in _REQUIRED_KEYS.items():
        if key not in obj:
            raise ManifestError("manifest missing required key %r" % (key,))
        if not isinstance(obj[key], expected_type) or isinstance(obj[key], bool):
            raise ManifestError("manifest key %r has wrong type (expected %s)" % (key, expected_type.__name__))

    counts = obj["counts"]
    for key, expected_type in _REQUIRED_COUNT_KEYS.items():
        if key not in counts:
            raise ManifestError("manifest counts missing required key %r" % (key,))
        if not isinstance(counts[key], expected_type) or isinstance(counts[key], bool):
            raise ManifestError("manifest counts key %r has wrong type" % (key,))

    for key in ("sidecar_sha256", "source_sha256"):
        value = obj[key]
        if not _SHA256_HEX_RE.match(value):
            raise ManifestError("manifest key %r is not a valid lowercase 64-hex-character SHA-256: %r" % (key, value))

    if obj["source_byte_length"] < 0:
        raise ManifestError("manifest source_byte_length must be non-negative")

    if obj["format_contract_version"] not in fmt.NORMATIVE_ROW_SIZES:
        raise ManifestError("manifest format_contract_version %r is not a supported version" % (
            obj["format_contract_version"],
        ))
    if obj["authority_semantics_version"] != fmt.AUTHORITY_SEMANTICS_VERSION_EXPERIMENTAL:
        raise ManifestError("manifest authority_semantics_version %r is not a supported version" % (
            obj["authority_semantics_version"],
        ))

    if not _is_safe_generation_basename(obj["generation_basename"]):
        raise ManifestError(
            "manifest generation_basename %r is not a safe bare basename (no path separators, no '..', "
            "no drive prefix)" % (obj["generation_basename"],)
        )
    expected_prefix = "sfm_master_%d_" % obj["format_contract_version"]
    # Package-Boundary Correction (2026-09-21): required suffix changed
    # from `.bin` to `.sfmsidecar` in lockstep with `compiler.
    # generation_basename()` -- see that function's own docstring.
    if not obj["generation_basename"].startswith(expected_prefix) or not obj["generation_basename"].endswith(".sfmsidecar"):
        raise ManifestError("manifest generation_basename %r does not match the expected naming scheme" % (
            obj["generation_basename"],
        ))

    return ManifestData(obj)


def resolve_generation_path(output_dir, manifest_data):
    """Safely joins `output_dir` with the manifest's basename-only
    reference -- the basename was already confirmed to contain no path
    separators / `..` / drive prefix by `parse_manifest_bytes`, so this can
    never escape `output_dir`."""
    import os as _os
    path = _os.path.join(str(output_dir), manifest_data.generation_basename)
    # Defense in depth: confirm the resolved path's parent really is
    # output_dir (catches any future basename-validation regression).
    if _os.path.dirname(_os.path.abspath(path)) != _os.path.abspath(str(output_dir)):
        raise ManifestError("resolved generation path escaped the output namespace")
    return path
