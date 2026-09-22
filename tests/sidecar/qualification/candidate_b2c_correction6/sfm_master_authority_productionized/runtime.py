# -*- coding: utf-8 -*-
"""sfm_master_authority_productionized.runtime -- THE canonical owner of
live broker runtime state. ASTRA_CORRECTED.md Section 2.

Ownership contract enforced by this module:
  - only THIS module (imported under exactly this dotted name) owns the
    broker factory and its INITIALIZING/READY/FAILED state;
  - every caller must use the exact absolute import
    `import sfm_master_authority_productionized.runtime` (or the
    equivalent `from sfm_master_authority_productionized import
    runtime`) -- never a relative import, never `execfile()`, never a
    differently-aliased path;
  - alternate-name execution/import is rejected HERE, at import time,
    before any broker/provider side effect is created;
  - a second, incompatible package/build fails clearly via the API-
    version check in `get_broker()`, never silently constructing a
    second broker;
  - initialization happens on SFM's main Python/Qt thread only (checked,
    not merely assumed -- see `assert_main_thread_context()`);
  - reentry during INITIALIZING never observes/returns a half-constructed
    broker;
  - this module is never hot-reloaded/deleted from `sys.modules` as a
    supported operation while a broker is live.

Importing this module, or calling `get_broker()`, NEVER opens a sidecar
or performs any I/O against the Master -- broker construction is a pure,
side-effect-free (with respect to filesystem/sidecar state) object
creation. Only an explicit `broker.acquire_generation(...)` call touches
the filesystem.
"""
import os
import sys

RUNTIME_API_VERSION = "1.0.0-b2a"

# Astra second-correction-gate F6/F8: a SEPARATE, more granular build
# identity, distinct from RUNTIME_API_VERSION. RUNTIME_API_VERSION names
# the broad B2A generation of the acquire_generation/acquire_cohort
# calling contract (unchanged since B2A); RUNTIME_BUILD_ID names THIS
# specific package build/implementation, which real bootstrap code can
# check to reject a build that shares the same API generation but is
# NOT the exact corrected implementation it requires (e.g. the
# pre-correction B2C-A/B candidate at candidate_b2c/, which shares
# RUNTIME_API_VERSION "1.0.0-b2a" but lacks the lease/generation-binding
# API this build adds -- a caller checking ONLY RUNTIME_API_VERSION
# could not tell the two apart, which is exactly how the corrected
# Normalizer candidate ended up bootstrapping the WRONG package build in
# the first correction attempt). Bump this string whenever a build adds
# or changes an API surface that callers depend on, even if
# RUNTIME_API_VERSION does not change.
#
# Independent-audit targeted correction (2026-09-18): bumped again --
# this build closes Blockers A/B/C and Narrow Issues D/E found in the
# independent audit of commit 743cad6bc645ae1aba48d6976f7eb318c859c778
# (expected-generation forwarding into acquire_cohort, the release-
# failure cleanup-handle-retention contract, and the documented
# retained+incoming transient semantics) -- a caller checking only
# RUNTIME_API_VERSION could not tell this build apart from the second
# correction's build, which lacks those fixes.
#
# Package-Boundary Targeted Correction (2026-09-22): bumped again --
# the intervening package-boundary correction commits (d039c92, 1abe914)
# added real API-surface-adjacent behavior a caller depends on even
# though RUNTIME_API_VERSION itself did not change: `ViewCache.
# invalidate_generation()` now also revokes leased-orphan tokens (a
# correctness fix a caller relying on the OLD, incomplete revocation
# behavior would need to know about); `Broker.acquire_generation()`'s
# call contract to `select_sidecar_candidate` was repaired (previously
# always raised TypeError); `sidecar_contract.py` now resolves its
# validator/provider dependency from within this package itself rather
# than a repository-relative qualification path; this file's own
# canonical-module-name self-check was repaired (previously this exact
# module could not be imported under its real name at all). A caller
# checking only RUNTIME_API_VERSION could not tell this build apart from
# the pre-package-boundary build, which lacks all of the above.
RUNTIME_BUILD_ID = "package-boundary-corrected-2026-09-22"

STATE_UNINITIALIZED = "UNINITIALIZED"
STATE_INITIALIZING = "INITIALIZING"
STATE_READY = "READY"
STATE_FAILED = "FAILED"

# Package-Boundary Correction (2026-09-21): this constant still said
# "sfm_master_authority.runtime" -- the OLD, pre-productionized package
# name -- inside the `sfm_master_authority_productionized` copy of this
# file. Since `__name__` for a real import of this copy is always
# "sfm_master_authority_productionized.runtime", the self-check below
# UNCONDITIONALLY raised ImportError on every real import attempt --
# `runtime.get_broker()` ("the one canonical broker-factory entry point
# ... every caller must call") was completely unreachable from this
# package the entire time, undiscovered because no B2C-B/B2C-C test
# ever imported it (every existing test constructs `Broker()` directly
# or uses `sidecar_contract`/`normalizer_compat_adapter` instead).
# Found and fixed while closing Section 8's "canonical package/import
# owner" requirement.
_CANONICAL_MODULE_NAME = "sfm_master_authority_productionized.runtime"

if __name__ != _CANONICAL_MODULE_NAME:
    raise ImportError(
        "sfm_master_authority_productionized.runtime was imported/executed under the wrong "
        "module name (%r, expected %r). This module must only ever be "
        "imported via `import sfm_master_authority_productionized.runtime` -- never "
        "execfile()'d, never aliased, never vendored under a different "
        "package name. Refusing before any broker/provider side effect is "
        "created." % (__name__, _CANONICAL_MODULE_NAME)
    )

from . import errors  # noqa: E402
from .broker import Broker  # noqa: E402

# Astra F6 correction: capture a DIRECT REFERENCE to this exact module
# object ONCE, at initialization time, right after the canonical-name
# check above has already passed. The pre-correction is_canonical()
# instead did `sys.modules.get(_CANONICAL_MODULE_NAME) is
# sys.modules.get(__name__)` -- but by this point `__name__` is ALREADY
# guaranteed to equal `_CANONICAL_MODULE_NAME` (the check above would
# have raised otherwise), so that comparison looked up the SAME dict key
# on both sides and compared it to itself: a tautology, ALWAYS True,
# incapable of ever detecting that a stale/frozen package (or any other
# module object) had already claimed the canonical name before this one
# finished loading. Comparing against this CAPTURED reference instead
# correctly detects that case: if some earlier-loaded module object is
# what `sys.modules[_CANONICAL_MODULE_NAME]` actually holds, THIS
# module's own is_canonical() now correctly reports False.
_this_module = sys.modules[__name__]

# Astra F6: the expected on-disk directory this module should be loaded
# from, for real production bootstrap code that wants to assert its
# origin -- deliberately NOT hardcoded here (no personal/temp absolute
# path baked into reusable source, Astra F8) and NOT enforced
# unconditionally (a real, single universal path does not exist while
# both the frozen deploy location and any given candidate/test location
# are legitimate origins depending on context). Real bootstrap code
# supplies its OWN expected value via assert_expected_origin() below;
# this module only provides the mechanism.
_actual_origin_dir = os.path.dirname(os.path.abspath(getattr(_this_module, "__file__", "") or ""))

_state = STATE_UNINITIALIZED
_broker = None
_construction_in_progress = False


def get_state():
    return _state


def get_runtime_api_version():
    return RUNTIME_API_VERSION


def get_runtime_build_id():
    return RUNTIME_BUILD_ID


def get_actual_origin_dir():
    """The real, on-disk directory this module was actually loaded
    from (captured once, at initialization, from `_this_module.__file__`
    -- never re-derived from a fresh sys.modules lookup on demand)."""
    return _actual_origin_dir


def assert_expected_origin(expected_origin_dir):
    """Astra F6: real production bootstrap code that KNOWS where the
    canonical package should be installed can call this to reject a
    stale/frozen/wrong-location copy being loaded first -- e.g. an old
    package left on sys.path ahead of the real deployed one. Purely
    additive/opt-in (no call site in this package invokes it
    automatically): the module itself cannot know what "the right
    location" is for every embedding context, so it never hardcodes or
    silently assumes one."""
    actual_norm = os.path.normcase(os.path.normpath(_actual_origin_dir))
    expected_norm = os.path.normcase(os.path.normpath(expected_origin_dir))
    if actual_norm != expected_norm:
        raise errors.BrokerIdentityConflict(
            "sfm_master_authority_productionized.runtime was loaded from %r, not the expected "
            "origin %r -- refusing (a stale/frozen/wrong-location package copy "
            "may have been preloaded first)." % (_actual_origin_dir, expected_origin_dir)
        )


def is_canonical():
    """True iff `sys.modules[_CANONICAL_MODULE_NAME]` is literally the
    SAME module object THIS module captured a direct reference to at its
    own initialization (`_this_module`) -- the direct, checkable proof
    that no second, differently-imported copy has silently taken over
    the canonical name. See the `_this_module` capture above for why a
    same-string double-lookup (the pre-correction implementation) cannot
    actually detect this."""
    return sys.modules.get(_CANONICAL_MODULE_NAME) is _this_module


def assert_main_thread_context(is_main_thread_fn):
    """Corrected-B1 main-thread requirement, made explicit and testable
    rather than assumed. `is_main_thread_fn` is a caller-supplied
    zero-arg callable returning bool -- in real SFM this should check
    against Qt's main-thread identity; offline (no Qt), callers pass a
    fixture returning True/False so this check is exercised without
    falsely claiming SFM main-thread qualification from an offline run.
    Raises BrokerInitializationFailed if the callable reports False."""
    if not is_main_thread_fn():
        raise errors.BrokerInitializationFailed(
            "broker construction was attempted off SFM's main Python/Qt "
            "thread -- refusing (corrected-B1 main-thread ownership "
            "contract)."
        )


def get_broker(expected_api_version=None, expected_build_id=None, is_main_thread_fn=None):
    """The one canonical broker-factory entry point. Every caller --
    Normalizer, Character Preset, Autoinit, direct menu invocation, the
    runtime identity probe -- must call exactly this function (via the
    canonical import) to obtain the broker. Returns the SAME broker
    object on every call once READY.

    `is_main_thread_fn`, if given, is checked only on the FIRST
    (constructing) call in a process; once READY, subsequent calls do not
    re-check it (the broker already exists; re-checking thread identity
    on every read would be a needless per-call cost with no correctness
    benefit -- the state that must be main-thread-created is the
    construction itself, not each lookup of an already-constructed
    object).
    """
    global _state, _broker, _construction_in_progress

    if expected_api_version is not None and expected_api_version != RUNTIME_API_VERSION:
        raise errors.BrokerIdentityConflict(
            "caller expects sfm_master_authority_productionized runtime API version %r, but "
            "the loaded runtime is %r -- refusing to hand out a broker under "
            "mismatched API expectations (a second, incompatible package is "
            "likely on sys.path)." % (expected_api_version, RUNTIME_API_VERSION)
        )
    if expected_build_id is not None and expected_build_id != RUNTIME_BUILD_ID:
        raise errors.BrokerIdentityConflict(
            "caller expects sfm_master_authority_productionized runtime build id %r, but "
            "the loaded runtime is build %r -- refusing (same API generation, "
            "different/incompatible implementation build)." % (expected_build_id, RUNTIME_BUILD_ID)
        )

    if not is_canonical():
        raise errors.BrokerIdentityConflict(
            "sys.modules[%r] does not refer to this module object -- a "
            "second, non-canonical sfm_master_authority_productionized.runtime appears to "
            "be loaded in this process." % (_CANONICAL_MODULE_NAME,)
        )

    if _state == STATE_READY:
        return _broker

    if _state == STATE_INITIALIZING:
        raise errors.BrokerInitializationFailed(
            "get_broker() reentered while broker construction is already "
            "INITIALIZING -- refusing to return a partially constructed "
            "broker (reentrant call, e.g. a side effect during construction "
            "calling back into get_broker())."
        )

    if _state == STATE_FAILED:
        raise errors.BrokerInitializationFailed(
            "sfm_master_authority broker previously failed to initialize in "
            "this process; not retried automatically."
        )

    # _state == STATE_UNINITIALIZED here.
    if _construction_in_progress:
        raise errors.BrokerInitializationFailed(
            "get_broker() reentered during its own UNINITIALIZED-state "
            "construction attempt."
        )
    _construction_in_progress = True
    _state = STATE_INITIALIZING
    try:
        if is_main_thread_fn is not None:
            assert_main_thread_context(is_main_thread_fn)
        broker = Broker(api_version=RUNTIME_API_VERSION)
        _broker = broker
        _state = STATE_READY
        return _broker
    except Exception:
        _state = STATE_FAILED
        _broker = None
        raise
    finally:
        _construction_in_progress = False


def _reset_for_test_only():
    """Test-only escape hatch -- NOT part of the ownership contract, NOT
    callable from any production path, and never used by the runtime
    identity probe. Exists solely so offline unit tests can exercise
    UNINITIALIZED -> INITIALIZING -> READY/FAILED transitions repeatedly
    within one process without the hot-reload this module otherwise
    forbids. A real running broker is never reset this way outside a
    test harness."""
    global _state, _broker, _construction_in_progress
    _state = STATE_UNINITIALIZED
    _broker = None
    _construction_in_progress = False
