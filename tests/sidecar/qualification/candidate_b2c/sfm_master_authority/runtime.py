# -*- coding: utf-8 -*-
"""sfm_master_authority.runtime -- THE canonical owner of live broker
runtime state. ASTRA_CORRECTED.md Section 2.

Ownership contract enforced by this module:
  - only THIS module (imported under exactly this dotted name) owns the
    broker factory and its INITIALIZING/READY/FAILED state;
  - every caller must use the exact absolute import
    `import sfm_master_authority.runtime` (or the equivalent
    `from sfm_master_authority import runtime`) -- never a relative
    import, never `execfile()`, never a differently-aliased path;
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
import sys

RUNTIME_API_VERSION = "1.0.0-b2a"

STATE_UNINITIALIZED = "UNINITIALIZED"
STATE_INITIALIZING = "INITIALIZING"
STATE_READY = "READY"
STATE_FAILED = "FAILED"

_CANONICAL_MODULE_NAME = "sfm_master_authority.runtime"

if __name__ != _CANONICAL_MODULE_NAME:
    raise ImportError(
        "sfm_master_authority.runtime was imported/executed under the wrong "
        "module name (%r, expected %r). This module must only ever be "
        "imported via `import sfm_master_authority.runtime` -- never "
        "execfile()'d, never aliased, never vendored under a different "
        "package name. Refusing before any broker/provider side effect is "
        "created." % (__name__, _CANONICAL_MODULE_NAME)
    )

from . import errors  # noqa: E402
from .broker import Broker  # noqa: E402

_state = STATE_UNINITIALIZED
_broker = None
_construction_in_progress = False


def get_state():
    return _state


def get_runtime_api_version():
    return RUNTIME_API_VERSION


def is_canonical():
    """True iff `sys.modules[_CANONICAL_MODULE_NAME]` is literally this
    module object -- the direct, checkable proof that no second,
    differently-imported copy has silently taken over the canonical
    name."""
    return sys.modules.get(_CANONICAL_MODULE_NAME) is sys.modules.get(__name__)


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


def get_broker(expected_api_version=None, is_main_thread_fn=None):
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
            "caller expects sfm_master_authority runtime API version %r, but "
            "the loaded runtime is %r -- refusing to hand out a broker under "
            "mismatched API expectations (a second, incompatible package is "
            "likely on sys.path)." % (expected_api_version, RUNTIME_API_VERSION)
        )

    if not is_canonical():
        raise errors.BrokerIdentityConflict(
            "sys.modules[%r] does not refer to this module object -- a "
            "second, non-canonical sfm_master_authority.runtime appears to "
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
