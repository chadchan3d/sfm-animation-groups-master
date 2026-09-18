# -*- coding: utf-8 -*-
"""Loads the FINAL exported R3-A2B validator/provider contract by exact
path + SHA-256 verification, and exposes ONE function --
`validate_selected_artifact` -- that opens, fully validates, and
IMMEDIATELY closes a candidate artifact, returning only its
ArtifactIdentity. The provider object itself is never retained or
returned: B2A must not retain a packed provider (ASTRA_CORRECTED.md
Section 4 -- at most one open backing at a time, and even that one must
not survive past this module's own function calls).
"""
import binascii
import hashlib
import os
import sys
import types

from . import descriptors
from . import errors

# Independent-re-audit BLOCKER 3.D (2026-09-18): none of the three paths
# below are hardcoded machine/developer-specific strings any more --
# all three are derived from THIS file's own on-disk location, so
# offline qualification works identically from any checkout location
# or extracted archive root. Callers that explicitly need a DIFFERENT
# source (e.g. a real installed-SFM deployment root, a separate concern
# left for later production packaging) may still override each value
# after import, before calling `ensure_loaded()` -- these remain plain
# module attributes, not baked-in constants.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
# .../<candidate root>/sfm_master_authority_productionized/<this file>
# -- the qualification/ directory containing the frozen validator/
# provider source is two levels up.
_QUALIFICATION_ROOT = os.path.normpath(os.path.join(_THIS_DIR, os.pardir, os.pardir))
# qualification/ -> sidecar/ -> tests/ -> repo root (three levels up).
_REPO_ROOT = os.path.normpath(os.path.join(_QUALIFICATION_ROOT, os.pardir, os.pardir, os.pardir))

FINAL_R3A2B_VALIDATOR_PATH = os.path.join(_QUALIFICATION_ROOT, "candidate_packed_validator_r3a2b.py")
FINAL_R3A2B_PROVIDER_PATH = os.path.join(_QUALIFICATION_ROOT, "candidate_packed_provider_r3a2b.py")
FINAL_R3A2B_VALIDATOR_SHA256 = "74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f"
FINAL_R3A2B_PROVIDER_SHA256 = "d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677"

# The provider's own source imports `sfm_master_sidecar.format`/`reader`
# via `from sfm_master_sidecar import ...` -- this directory must be on
# sys.path for that import to resolve. Independent-re-audit BLOCKER
# 3.D: for OFFLINE QUALIFICATION this now resolves to the REPO's own
# tools/ directory (verified byte-identical, module-source-wise, to the
# installed-SFM gate_r2_formal_deploy/sfm_master_sidecar/ copy this
# constant previously hardcoded) rather than any installed, developer-
# specific SFM deployment path. Real production installed-root
# resolution remains a separate, later deployment concern -- not solved
# here, and not needed for offline qualification.
_GATE_R2_DEPLOY_DIR = os.path.join(_REPO_ROOT, "tools")

_validator_module = None
_provider_module = None


def _sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_module_verified(path, expected_sha256, module_name):
    actual = _sha256_of_file(path)
    if actual != expected_sha256:
        raise errors.BrokerInitializationFailed(
            "governing sidecar contract file %r SHA-256 mismatch: expected %s, found %s -- "
            "refusing to load an unverified validator/provider." % (path, expected_sha256, actual)
        )
    with open(path, "rb") as f:
        src = f.read()
    module = types.ModuleType(module_name)
    module.__file__ = path
    sys.modules[module_name] = module
    code = compile(src, path, "exec")
    exec(code, module.__dict__)
    return module


def ensure_loaded():
    """Idempotent: loads + SHA-verifies the FINAL R3-A2B validator and
    provider exactly once per process, reused on subsequent calls."""
    global _validator_module, _provider_module
    if _validator_module is not None and _provider_module is not None:
        return
    if _GATE_R2_DEPLOY_DIR not in sys.path:
        sys.path.insert(0, _GATE_R2_DEPLOY_DIR)
    _validator_module = _load_module_verified(
        FINAL_R3A2B_VALIDATOR_PATH, FINAL_R3A2B_VALIDATOR_SHA256,
        "sfm_master_authority_final_r3a2b_validator",
    )
    # The provider's own source does `import candidate_packed_validator_r3a2b
    # as candidate_packed_validator` -- satisfy that exact import name.
    sys.modules["candidate_packed_validator_r3a2b"] = _validator_module
    _provider_module = _load_module_verified(
        FINAL_R3A2B_PROVIDER_PATH, FINAL_R3A2B_PROVIDER_SHA256,
        "sfm_master_authority_final_r3a2b_provider",
    )


def validate_selected_artifact(artifact_path, expected_source_sha256, runtime_cap_bytes=None):
    """Bounded read + complete Section 20 A-J structural validation of
    `artifact_path` via the FINAL R3-A2B contract, unchanged. Opens,
    validates, closes -- returns only an immutable ArtifactIdentity,
    never the provider object itself."""
    ensure_loaded()
    kwargs = {}
    if runtime_cap_bytes is not None:
        kwargs["runtime_cap_bytes"] = runtime_cap_bytes

    try:
        provider = _provider_module.BoundedProvider.open_path(
            artifact_path, expected_source_sha256, **kwargs
        )
    except _provider_module.SourceMismatchError as exc:
        raise errors.SourceGenerationMismatch(str(exc))
    except _provider_module.AuthorityUnavailable as exc:
        msg = str(exc)
        if "admission cap" in msg:
            raise errors.ResourceAdmissionRefusal(msg)
        raise errors.SidecarCorrupt(msg)

    try:
        header = provider._header
        embedded_source_hex = binascii.hexlify(header.source_sha256).decode("ascii").lower()
        identity = descriptors.ArtifactIdentity(
            sidecar_artifact_sha256=_sha256_of_file(artifact_path),
            format_contract_version=header.format_contract_version,
            authority_semantics_version=header.authority_semantics_version,
            projection_contract_version=None,  # not present in the current header format -- honestly None, not guessed
            embedded_source_sha256=embedded_source_hex,
            embedded_source_byte_length=header.source_byte_length,
        )
        return identity
    finally:
        provider.close()
