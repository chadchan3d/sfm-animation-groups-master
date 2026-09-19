# -*- coding: utf-8 -*-
"""Effective Master path resolver -- ASTRA_CORRECTED.md Section 3.

Takes an already-discovered ifm.dll path and an optional
already-discovered SFM-mod-directory path as PARAMETERS (never discovers
either itself) so this module stays fully offline-testable; real
discovery of those two inputs lives in `native_discovery.py`, used only
by the SFM runtime identity probe.
"""
import os

from . import errors
from . import win_file_identity

RESOLVED_CORROBORATED = "RESOLVED_CORROBORATED"
RESOLVED_PRIMARY_QUALIFIED = "RESOLVED_PRIMARY_QUALIFIED"

_RELATIVE_MASTER_PATH = ("usermod", "cfg", "sfm_defaultanimationgroups.txt")
_RELATIVE_MASTER_PATH_FROM_MOD = ("cfg", "sfm_defaultanimationgroups.txt")


class ResolvedMaster(object):
    __slots__ = ("path", "outcome", "primary_path", "corroborator_path", "identity")

    def __init__(self, path, outcome, primary_path, corroborator_path, identity):
        self.path = path
        self.outcome = outcome
        self.primary_path = primary_path
        self.corroborator_path = corroborator_path
        self.identity = identity

    def __repr__(self):
        return "ResolvedMaster(path=%r, outcome=%r)" % (self.path, self.outcome)


def derive_primary_path(ifm_dll_path):
    """A1-qualified derivation, reproduced verbatim from production
    `Rebuild_Control_Groups_Normalizer.derive_paths()`'s own directory
    validation: ifm.dll path -> tools_dir -> bin_dir -> game_dir ->
    game_dir/usermod/cfg/sfm_defaultanimationgroups.txt. This is the path
    empirically proven (R3-A1) to govern the tested native Rebuild
    Control Groups action -- never reinvented here, only reused."""
    tools_dir = os.path.dirname(ifm_dll_path)
    bin_dir = os.path.dirname(tools_dir)
    game_dir = os.path.dirname(bin_dir)

    if os.path.normcase(os.path.basename(tools_dir)) != os.path.normcase("tools"):
        raise errors.AmbiguousMasterPath(
            "loaded ifm.dll (%r) is not under a 'tools' directory -- cannot derive an "
            "installation root; refusing to guess." % (ifm_dll_path,)
        )
    if os.path.normcase(os.path.basename(bin_dir)) != os.path.normcase("bin"):
        raise errors.AmbiguousMasterPath(
            "loaded ifm.dll (%r) is not under 'game\\bin\\tools' -- cannot derive an "
            "installation root; refusing to guess." % (ifm_dll_path,)
        )

    return os.path.join(game_dir, *_RELATIVE_MASTER_PATH)


def derive_corroborator_path(valve_mod_dir):
    return os.path.join(valve_mod_dir, *_RELATIVE_MASTER_PATH_FROM_MOD)


def resolve_effective_master(ifm_dll_path, valve_mod_dir=None):
    """Implements the corrected-B1 resolver outcomes exactly:

    - both signals present + same file identity -> RESOLVED_CORROBORATED
    - primary present, corroborator unavailable -> RESOLVED_PRIMARY_QUALIFIED
    - both present but disagree -> AmbiguousMasterPath, fail closed
    - primary path missing -> MasterAbsent
    - primary path unreadable -> MasterUnreadable

    Never uses realpath()+lowercasing as identity proof -- disagreements
    are resolved (or confirmed) via `win_file_identity`'s handle-based
    comparison only.
    """
    primary_path = derive_primary_path(ifm_dll_path)

    if not os.path.isfile(primary_path):
        raise errors.MasterAbsent("primary-resolved Master not found: %r" % (primary_path,))

    try:
        primary_identity = win_file_identity.get_existing_file_identity(primary_path)
    except win_file_identity.FileIdentityUnavailable as exc:
        raise errors.MasterUnreadable(str(exc))

    if valve_mod_dir is None:
        return ResolvedMaster(
            primary_path, RESOLVED_PRIMARY_QUALIFIED, primary_path, None, primary_identity,
        )

    corroborator_path = derive_corroborator_path(valve_mod_dir)
    if not os.path.isfile(corroborator_path):
        return ResolvedMaster(
            primary_path, RESOLVED_PRIMARY_QUALIFIED, primary_path, None, primary_identity,
        )

    try:
        corroborator_identity = win_file_identity.get_existing_file_identity(corroborator_path)
    except win_file_identity.FileIdentityUnavailable:
        # Corroborator exists but could not be opened/queried -- treat as
        # an unavailable signal, not a disagreement; primary alone stands.
        return ResolvedMaster(
            primary_path, RESOLVED_PRIMARY_QUALIFIED, primary_path, corroborator_path, primary_identity,
        )

    if primary_identity.same_file_as(corroborator_identity):
        return ResolvedMaster(
            primary_path, RESOLVED_CORROBORATED, primary_path, corroborator_path, primary_identity,
        )

    raise errors.AmbiguousMasterPath(
        "primary (%r) and corroborating (%r) resolved Master paths refer to DIFFERENT "
        "files (volume/file-index mismatch: %r vs %r) -- failing closed, no unchecked "
        "override." % (primary_path, corroborator_path, primary_identity, corroborator_identity)
    )
