# -*- coding: utf-8 -*-
"""Minimum C3 -- QUALIFICATION-ONLY command-boundary freshness/retirement
orchestration. NOT production code. Never imported by
`tools/sfm_master_sidecar/*.py`, never imported by the production
Normalizer, never placed in any real SFM startup path, never a
filesystem watcher or poller.

Distinguishes, per the C3 brief, three facts that must never be conflated:

  - SOURCE IDENTITY: SHA-256 of the actual Master TXT bytes, hashed fresh
    at THIS explicit command boundary. Never mtime/size.
  - CANDIDATE GENERATION IDENTITY: the manifest-declared `source_sha256`/
    `format_contract_version`/`authority_semantics_version` a compiled
    sidecar artifact claims to embed -- read via the already-qualified,
    unmodified production `tools/sfm_master_sidecar/manifest.py` (never a
    second hand-copied manifest parser).
  - AUTHORIZATION GENERATION: the currently admitted owner's own epoch,
    owned entirely by `session_owner.py` and untouched by this module.

This module is called ONLY at an explicit command/preparation boundary by
a caller (a test here; in a real Normalizer, an explicit user-initiated
command) that has already decided "now" is the moment to check freshness.
It never runs on a timer, a background thread, or a file-change
notification -- there is no such mechanism anywhere in this codebase.
"""

import hashlib
import json
import os

from sfm_master_sidecar import manifest as sidecar_manifest  # noqa: E402 -- only `resolve_generation_path` is reused (syntax-safe on both runtimes); see ManifestError below for why parsing itself is NOT reused

import session_owner as so

try:
    _STRING_TYPES = (str, unicode)  # noqa: F821 -- Python 2
except NameError:
    _STRING_TYPES = (str,)


class ManifestError(Exception):
    """Qualification-only, Python-2/3-compatible manifest READ error.

    Distinct from `tools.sfm_master_sidecar.manifest.ManifestError` (the
    PRODUCTION hardened manifest validator/builder -- explicitly
    Python-3-only by its own docstring: "the embedded runtime reader
    never reads a manifest -- resolving which generation is active is a
    host-application/Normalizer concern, entirely outside reader.py's
    job"). That module's `parse_manifest_bytes` cannot run correctly
    under embedded Python 2.7 (its `isinstance(value, str)` checks reject
    the `unicode` objects Python 2's own `json` module produces for JSON
    string values -- a real cross-version incompatibility, not a bug in
    this qualification module). Since every other qualification module in
    this package is deliberately embedded-Python-2.7-compatible, this
    minimal reader exists so `command_boundary.py` is too -- it is NEVER
    used to BUILD a manifest (that remains exclusively the production
    `manifest.build_manifest_dict`/`serialize_manifest`, used unmodified
    by desktop qualification's own fixture-building helper), only to READ
    one that already exists on disk."""


class _QualManifestData(object):
    __slots__ = ("source_sha256", "sidecar_sha256", "generation_basename",
                 "format_contract_version", "authority_semantics_version", "raw")

    def __init__(self, d):
        self.source_sha256 = d["source_sha256"]
        self.sidecar_sha256 = d["sidecar_sha256"]
        self.generation_basename = d["generation_basename"]
        self.format_contract_version = d["format_contract_version"]
        self.authority_semantics_version = d["authority_semantics_version"]
        self.raw = d


def _parse_manifest_bytes_compat(data):
    """Minimal, deliberately narrow manifest read: just enough field
    presence/type checking to safely drive freshness/compatibility
    decisions, on both Python 2.7 and Python 3. NOT a replacement for the
    production validator's full hardening (duplicate-key detection, exact
    SHA-256 hex-regex checks, safe-basename checks, etc.) -- those remain
    exclusively enforced by `manifest.py` at BUILD time; this is a READ
    -only qualification convenience for an already-trusted-to-exist-on
    -disk manifest file."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ManifestError("manifest is not valid UTF-8: %r" % (exc,))
    try:
        obj = json.loads(text)
    except ValueError as exc:  # covers both Python 2's ValueError and Python 3's json.JSONDecodeError (a ValueError subclass)
        raise ManifestError("manifest is not valid JSON: %r" % (exc,))
    if not isinstance(obj, dict):
        raise ManifestError("manifest top level must be a JSON object")
    for key in ("generation_basename", "sidecar_sha256", "source_sha256"):
        if key not in obj or not isinstance(obj[key], _STRING_TYPES):
            raise ManifestError("manifest missing/invalid required string key %r" % (key,))
    for key in ("format_contract_version", "authority_semantics_version"):
        if key not in obj or not isinstance(obj[key], int) or isinstance(obj[key], bool):
            raise ManifestError("manifest missing/invalid required integer key %r" % (key,))
    return _QualManifestData(obj)


def hash_source_file(source_path):
    """The ACTUAL current byte identity of the Master TXT, hashed fresh at
    this command boundary. Never mtime/size -- per the brief, a pointer
    timestamp or file mtime is not semantic truth."""
    try:
        with open(source_path, "rb") as f:
            data = f.read()
    except (IOError, OSError) as exc:
        raise so.ResourceRefused("source unreadable at command boundary: %r" % (exc,))
    return hashlib.sha256(data).hexdigest()


def _read_manifest(manifest_path):
    try:
        with open(manifest_path, "rb") as f:
            data = f.read()
    except (IOError, OSError) as exc:
        raise so.ResourceRefused("manifest/pointer missing or unreadable: %r" % (exc,))
    try:
        return _parse_manifest_bytes_compat(data)
    except ManifestError as exc:
        raise so.ResourceRefused("candidate manifest corrupt/invalid: %r" % (exc,))


def resolve_candidate(manifest_path, generation_dir, expected_format_version,
                       expected_authority_version, current_source_sha256):
    """Reads+validates the manifest, resolves the candidate artifact path,
    and checks BOTH profile/version compatibility and source freshness --
    all BEFORE any admission is attempted (this is the "verify candidate
    binds to that exact source identity and expected profile/version"
    step from the brief's freshness model). Returns
    `(artifact_path, manifest_data)` on success.

    Every failure raises `session_owner.ResourceRefused` -- never a new
    exception type (per the brief's "do not create a large exception
    hierarchy"), never a fabricated `MasterUnknown`/semantic fallback."""
    manifest_data = _read_manifest(manifest_path)

    if manifest_data.format_contract_version != expected_format_version:
        raise so.ResourceRefused(
            "candidate incompatible: format_contract_version %r != expected %r" % (
                manifest_data.format_contract_version, expected_format_version,
            )
        )
    if manifest_data.authority_semantics_version != expected_authority_version:
        raise so.ResourceRefused(
            "candidate incompatible: authority_semantics_version %r != expected %r" % (
                manifest_data.authority_semantics_version, expected_authority_version,
            )
        )

    if manifest_data.source_sha256 != current_source_sha256:
        raise so.ResourceRefused(
            "candidate source stale: manifest declares source_sha256=%r, current Master TXT "
            "hashes to %r -- refused, never silently admitted, never a revived old generation" % (
                manifest_data.source_sha256, current_source_sha256,
            )
        )

    try:
        artifact_path = sidecar_manifest.resolve_generation_path(generation_dir, manifest_data)
    except sidecar_manifest.ManifestError as exc:
        raise so.ResourceRefused("candidate manifest resolution failed: %r" % (exc,))

    if not os.path.isfile(artifact_path):
        raise so.ResourceRefused("candidate artifact missing: %r" % (artifact_path,))

    return artifact_path, manifest_data


def _logical_namespace_key(namespace_identity):
    """Identifies "the same logical authority slot" -- deliberately
    EXCLUDES both `source_sha256` and `artifact_sha256` (both are
    per-generation identity: they are EXPECTED to differ between an old
    and a new generation of the same logical Master/profile). Only
    `source_path` (which logical file this is), the static format/
    authority contract versions, and `profile_version` (which
    consumer/test scenario this is) identify the slot itself."""
    return (
        namespace_identity.source_path, namespace_identity.format_version,
        namespace_identity.authority_version, namespace_identity.profile_version,
    )


def prepare_command_boundary(source_path, manifest_path, generation_dir,
                              resource_snapshot_fn, guard_policy, view_budgets,
                              bounded_provider_module, bounded_view_module,
                              expected_format_version, expected_authority_version,
                              profile_version):
    """THE single entry point a real command boundary calls instead of
    `session_owner.get_or_create_owner` directly.

    1. Hashes the actual current Master TXT bytes (source identity).
    2. Resolves+validates the candidate manifest/pointer (generation
       identity + compatibility + freshness) -- refuses recoverably for
       every failure case, never partially admitting anything.
    3. Retires any existing owner for the SAME logical namespace bound to
       a DIFFERENT (now-stale) `source_sha256` -- before creating/reusing
       the owner for the CURRENT namespace identity. Retirement never
       destroys an owner with active leases; it only prevents it from
       being reused/discoverable for NEW work (see
       `MasterAuthorityOwner.retire`).
    4. Delegates to the existing, unmodified `get_or_create_owner` for the
       (possibly brand new, possibly reused-unchanged) current namespace
       identity -- admission itself remains lazy, unchanged from Round 3.

    Returns `(owner, manifest_data)` on success. Raises
    `session_owner.ResourceRefused` for every recoverable failure case."""
    current_source_sha256 = hash_source_file(source_path)
    artifact_path, manifest_data = resolve_candidate(
        manifest_path, generation_dir, expected_format_version, expected_authority_version,
        current_source_sha256,
    )

    namespace_identity = so.NamespaceIdentity(
        source_path=source_path, source_sha256=current_source_sha256,
        artifact_sha256=manifest_data.sidecar_sha256,
        format_version=expected_format_version, authority_version=expected_authority_version,
        profile_version=profile_version,
    )
    logical_key = _logical_namespace_key(namespace_identity)
    for existing_ns, existing_owner in list(so._OWNER_REGISTRY.items()):
        if existing_ns == namespace_identity:
            continue  # exact match -- handled as ordinary reuse by get_or_create_owner below
        if _logical_namespace_key(existing_ns) == logical_key:
            existing_owner.retire()

    owner = so.get_or_create_owner(
        namespace_identity, artifact_path, resource_snapshot_fn, guard_policy,
        view_budgets, bounded_provider_module, bounded_view_module,
    )
    return owner, manifest_data
