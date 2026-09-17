# -*- coding: ascii -*-
r"""
SFM Rebuild Control Groups - Production Candidate

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: MUTATING PRODUCTION CANDIDATE

Purpose:
  Production-candidate Source Filmmaker Rebuild Control Groups contextualizer.

  The command supports either:
    - one or more Clip Editor-selected shots; or
    - all shots in the loaded session.

  For every model-backed animation set in the selected command scope:
    1. apply the proven cheap eligibility gate;
    2. skip targets proven irrelevant before native Rebuild is called;
    3. run the unchanged native/contextual transaction for every eligible
       target;
    4. preserve native POST for unrigged targets;
    5. reconcile supported active rigs from current Master plus fresh PRE
       runtime evidence;
    6. fail closed on unsupported, stale, ambiguous, or insufficient rig
       evidence.

  Responsiveness policy:
    - one eligible target transaction per Qt callback;
    - after a successful same-shot target, return normally to the Qt event
      loop before starting the next eligible target;
    - the target transaction itself remains atomic;
    - resume is guarded by the production run lock, expected shot identity,
      live Master SHA-256 stability, previous-target terminal state, and unique
      re-resolution of the next animation set.

  Settled resource architecture retained:
    - pre-Rebuild eligibility exclusion;
    - streaming whole-session verification;
    - terminal-semantic rich-payload non-retention;
    - compact whole-session isolation digests;
    - one immutable scoped canonical Master index.

  No semantic runtime DME cache, no PRE/POST hierarchy cache, no active-rig
  cache, no planner/composer-result cache, no gc.collect(), no processEvents(),
  and no sleep-based scheduling are used.

  The Cancel button is a pre-launch dialog dismissal only. Once a rebuild
  scope is chosen, there is no mid-operation cancellation.


Core policy:
  - native Rebuild remains the canonical compatibility/taxonomy operation;
  - unrigged targets remain native POST;
  - unsupported, stale, ambiguous, duplicate-semantic, or insufficiently
    evidenced contexts fail closed to native POST;
  - supported active rigs may compose current Master taxonomy with fresh PRE
    rig presentation evidence;
  - no model-name or fixture-name routing exists.

Current generic corrections include:
  1. PRE-hidden Master-active repair:
     a hidden fresh-PRE rig-owned DmeTransformControl may use an exact
     current-Master RigBody/RigArms/RigLegs destination only when that active
     root is visibly present and at least two visible rig-owned transform
     peers independently map to the exact same Master destination.

  2. Exact-Master destination direct-order convergence:
     once final contextual destinations are resolved, if every direct-control
     candidate in one final destination cohort is Master-known and every exact
     Master destination is that same final path, order that cohort by current
     Master direct-control order. Mixed Master-known/Master-unknown cohorts
     continue to use the proven fresh-PRE total-order rule.

Safety / CONTEXTUALIZER layered-isolation boundary:
  - shot activation still returns to SFM through the proven 100 ms Qt defer;
  - one eligible target transaction runs per Qt callback;
  - after each successful same-shot target, the next target is deferred through
    a guarded 0 ms Qt callback so the UI can visibly remain responsive;
  - entire per-target native + reconciliation transaction is non-undoable and
    the prior undo state is restored;
  - zero undo-ledger delta is required;
  - processed targets still receive direct semantic/fingerprint validation;
  - after every processed target, ALL other animation sets in the current shot
    are deeply fingerprinted and compared with their expected state;
  - after every completed shot, a compact whole-session shot/aset identity
    census must remain unchanged;
  - every 12 completed non-final shots, one exhaustive whole-session deep
    verification is performed; one exhaustive verification also runs at end;
  - follower/overlap heuristics are NOT used to define isolation peers;
  - the live Master hash is captured at run start and must remain unchanged;
  - the original playhead is restored and verified at completion or abort.

OUTPUT:
  C:\Users\Public\Documents\sfm_rebuild_control_groups.txt
"""

import ctypes
import hashlib
import os
import re
import struct
import sys
import time
import traceback

import sfmApp
import sfmClipEditor
import vs

from PySide import QtCore
from PySide import QtGui

try:
    xrange
except NameError:
    xrange = range

try:
    unicode
except NameError:
    unicode = str

try:
    long
except NameError:
    long = int

# ===========================================================================
# R3-B2C-B (candidate-only; frozen production file unaffected -- see
# tests/sidecar/qualification/R3_B2C_B_Normalizer_ReadOnly_Migration_
# Report.md for the exact diff). Minimal plumbing so the single
# parse_targeted_master(...) authority-acquisition call site below can
# be replaced with the qualified shared-authority compatibility adapter.
# parse_targeted_master itself is left fully intact (see its own
# definition, unchanged) -- kept callable for A/B read-only comparison,
# simply no longer reached by the production call site.
#
# Astra second-correction-gate F6/F8 finding (real, confirmed): the
# FIRST correction attempt fixed sfm_master_authority.runtime's
# is_canonical() tautology but never actually pointed THIS bootstrap at
# the corrected package -- _B2C_QUALIFIED_AUTHORITY_ROOT still named
# candidate_b2c/ (the pre-correction B2C-A/B package), not
# candidate_b2c_correction2/. Every offline test that exercised
# acquire_master_index_via_qualified_authority did so by extracting the
# function's SOURCE via line-range exec() and INJECTING a fake
# `_b2c_authority_runtime` directly into the exec namespace -- which
# bypassed this module-level import/bootstrap entirely, so no test ever
# actually ran this file's own bootstrap and caught the wrong path. This
# correction fixes the path AND adds real, enforced identity checks at
# this actual entry point (never merely defined-but-unused), so a wrong
# package can no longer silently load here again.
# ===========================================================================
_B2C_QUALIFIED_AUTHORITY_ROOT = (
    r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction2"
)
_B2C_EXPECTED_ORIGIN_DIR = (
    r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction2"
    r"\sfm_master_authority"
)
_B2C_EXPECTED_API_VERSION = "1.0.0-b2a"
_B2C_EXPECTED_BUILD_ID = "b2c-correction2-lease-generation-binding-2026-09-16"

if _B2C_QUALIFIED_AUTHORITY_ROOT not in sys.path:
    sys.path.insert(0, _B2C_QUALIFIED_AUTHORITY_ROOT)

_B2C_SIDECAR_TOOLS_ROOT = r"E:\SFM Animation Group Master\tools"
if _B2C_SIDECAR_TOOLS_ROOT not in sys.path:
    sys.path.insert(0, _B2C_SIDECAR_TOOLS_ROOT)

from sfm_master_authority import runtime as _b2c_authority_runtime
from sfm_master_authority import normalizer_compat_adapter as _b2c_normalizer_adapter
from sfm_master_authority import errors as _b2c_authority_errors


def _b2c_verify_bootstrap_identity():
    """Astra F6/F8 correction: verify, at this REAL entry point (not
    merely in a test harness that bypasses the import), that the loaded
    sfm_master_authority package is genuinely the exact corrected build
    this Normalizer candidate requires -- never the frozen production
    package, never the pre-correction candidate_b2c/ build, never a
    stale preloaded copy, never an alternate/replaced canonical module
    object. Raises errors.BrokerIdentityConflict on any mismatch, before
    any broker is ever constructed. Called unconditionally at import
    time, immediately below."""
    _b2c_authority_runtime.assert_expected_origin(_B2C_EXPECTED_ORIGIN_DIR)
    if _b2c_authority_runtime.get_runtime_api_version() != _B2C_EXPECTED_API_VERSION:
        raise _b2c_authority_errors.BrokerIdentityConflict(
            "expected sfm_master_authority runtime API version %r, loaded "
            "package reports %r" % (
                _B2C_EXPECTED_API_VERSION, _b2c_authority_runtime.get_runtime_api_version())
        )
    if not hasattr(_b2c_authority_runtime, "RUNTIME_BUILD_ID"):
        raise _b2c_authority_errors.BrokerIdentityConflict(
            "loaded sfm_master_authority.runtime has no RUNTIME_BUILD_ID attribute -- "
            "this is a PRE-CORRECTION package build (e.g. candidate_b2c/), which lacks "
            "the lease/generation-binding API this Normalizer candidate build requires."
        )
    if _b2c_authority_runtime.get_runtime_build_id() != _B2C_EXPECTED_BUILD_ID:
        raise _b2c_authority_errors.BrokerIdentityConflict(
            "expected sfm_master_authority runtime build id %r, loaded package "
            "reports build %r" % (
                _B2C_EXPECTED_BUILD_ID, _b2c_authority_runtime.get_runtime_build_id())
        )
    if not _b2c_authority_runtime.is_canonical():
        raise _b2c_authority_errors.BrokerIdentityConflict(
            "sfm_master_authority.runtime is not canonical at this bootstrap point -- "
            "a second, non-canonical module object has taken over the canonical name."
        )


_b2c_verify_bootstrap_identity()

EXPECTED_SHA256 = (
    "12504c248047e181d31a8500fb6693d1"
    "a2d3c805e841fc2227e41aa4e2d2b47e"
)
REBUILD_RVA = 0x0008C820
EXPECTED_PROLOGUE = (
    "\x55\x8B\xEC\x56\x8B\x75\x08\x85\xF6\x74\x35"
)

DEFER_MS = 100
CONTEXTUALIZER_TARGET_CALLBACK_DEFER_MS = 0
READ_BLOCK = 65536

# Settled layered-isolation cadence.
# Exhaustive whole-session deep verification runs every 12 non-final shots,
# providing evenly spaced cross-shot checkpoints with low expected overhead.
CONTEXTUALIZER_PERIODIC_GLOBAL_SHOT_INTERVAL = 12

# CONTEXTUALIZER observational telemetry cadence.
# VirtualQuery is deliberately NOT run per target. It is sampled at startup,
# major construction/verifier boundaries, every normal 12-shot checkpoint,
# and every shot in the final six target-containing shots.
CONTEXTUALIZER_VAS_LAST_SHOTS = 6

# Selected Master-parse calls receive one concise row in the log. Every parse
# is sampled with cheap GetProcessMemoryInfo; only these calls are printed
# individually so the telemetry itself does not create a giant output stream.

RIG_RECON_ROOT = "__RIG_VISIBLE_RECON__"
MASTER_RECON_ROOT = "__MASTER_VISIBLE_RECON__"

RUN_LOCK_NAME = (
    "__SFM_REBUILD_CONTROL_GROUPS_CONTEXTUALIZER_RUNNING__"
)

OUTPUT_PATH = (
    "C:\\Users\\Public\\Documents\\"
    "sfm_rebuild_control_groups.txt"
)

PRODUCTION_REVISION = (
    "SFM_REBUILD_CONTROL_GROUPS_CONTEXTUALIZER_PRODUCTION_2026_09_05"
)


DIRECT_ANCHOR_NAMES = (u"RigBody", u"RigArms", u"RigLegs")

MASTER_PATH = None



class _ProcessMemoryCountersEx(
        ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


def contextualizer_process_memory_sample():
    """
    O(1) diagnostic telemetry only.

    Returns primitive byte counts. Failure is non-fatal so telemetry cannot
    change the Rebuild/contextualizer runtime semantics.
    """
    try:
        kernel32 = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi

        process = kernel32.GetCurrentProcess()

        counters = _ProcessMemoryCountersEx()
        counters.cb = ctypes.sizeof(
            _ProcessMemoryCountersEx
        )

        ok = psapi.GetProcessMemoryInfo(
            process,
            ctypes.byref(counters),
            counters.cb,
        )

        if not ok:
            return {
                "ok": False,
                "working_set": None,
                "peak_working_set": None,
                "pagefile": None,
                "peak_pagefile": None,
                "private": None,
            }

        return {
            "ok": True,
            "working_set": int(
                counters.WorkingSetSize
            ),
            "peak_working_set": int(
                counters.PeakWorkingSetSize
            ),
            "pagefile": int(
                counters.PagefileUsage
            ),
            "peak_pagefile": int(
                counters.PeakPagefileUsage
            ),
            "private": int(
                counters.PrivateUsage
            ),
        }

    except Exception:
        return {
            "ok": False,
            "working_set": None,
            "peak_working_set": None,
            "pagefile": None,
            "peak_pagefile": None,
            "private": None,
        }


class _MemoryBasicInformation(
        ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_ulong),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.c_ulong),
        ("Protect", ctypes.c_ulong),
        ("Type", ctypes.c_ulong),
    ]


class _SystemInfo(
        ctypes.Structure):
    _fields_ = [
        ("wProcessorArchitecture", ctypes.c_ushort),
        ("wReserved", ctypes.c_ushort),
        ("dwPageSize", ctypes.c_ulong),
        ("lpMinimumApplicationAddress", ctypes.c_void_p),
        ("lpMaximumApplicationAddress", ctypes.c_void_p),
        ("dwActiveProcessorMask", ctypes.c_size_t),
        ("dwNumberOfProcessors", ctypes.c_ulong),
        ("dwProcessorType", ctypes.c_ulong),
        ("dwAllocationGranularity", ctypes.c_ulong),
        ("wProcessorLevel", ctypes.c_ushort),
        ("wProcessorRevision", ctypes.c_ushort),
    ]


def _contextualizer_pointer_integer(value):
    if value is None:
        return 0

    try:
        return int(value)
    except Exception:
        try:
            return int(
                ctypes.cast(
                    value,
                    ctypes.c_void_p,
                ).value
            )
        except Exception:
            return 0


def contextualizer_process_architecture_sample():
    """
    Read process-width and executable PE facts once.

    This is observational only. It does not infer architecture/LAA from
    process-memory totals.
    """
    result = {
        "ok": False,
        "pointer_bits": (
            int(
                ctypes.sizeof(
                    ctypes.c_void_p
                )
            )
            * 8
        ),
        "exe_path": None,
        "machine": None,
        "characteristics": None,
        "large_address_aware": None,
        "image_file_32bit_machine": None,
        "error": None,
    }

    try:
        kernel32 = ctypes.windll.kernel32

        buffer_size = 32768
        path_buffer = ctypes.create_unicode_buffer(
            buffer_size
        )

        count = kernel32.GetModuleFileNameW(
            None,
            path_buffer,
            buffer_size,
        )

        if not count:
            raise RuntimeError(
                "GetModuleFileNameW failed."
            )

        exe_path = to_unicode(
            path_buffer.value
        )
        result["exe_path"] = exe_path

        fp = open(
            exe_path,
            "rb",
        )

        try:
            dos = fp.read(
                64
            )

            if (
                len(dos) < 64
                or dos[:2] != "MZ"
            ):
                raise RuntimeError(
                    "Executable does not have an MZ header."
                )

            pe_offset = struct.unpack(
                "<I",
                dos[60:64],
            )[0]

            fp.seek(
                pe_offset
            )
            pe_header = fp.read(
                24
            )

        finally:
            fp.close()

        if (
            len(pe_header) < 24
            or pe_header[:4] != "PE\x00\x00"
        ):
            raise RuntimeError(
                "Executable does not have a valid PE signature."
            )

        machine = struct.unpack(
            "<H",
            pe_header[4:6],
        )[0]

        characteristics = struct.unpack(
            "<H",
            pe_header[22:24],
        )[0]

        result["machine"] = int(
            machine
        )
        result["characteristics"] = int(
            characteristics
        )
        result["large_address_aware"] = bool(
            characteristics
            & 0x0020
        )
        result["image_file_32bit_machine"] = bool(
            characteristics
            & 0x0100
        )
        result["ok"] = True

    except Exception as exc:
        result["error"] = repr(
            exc
        )

    return result


def contextualizer_virtual_address_sample():
    """
    Low-cadence VirtualQuery census of the current process address space.

    Returns primitive totals only. Largest-free-region is a headroom signal,
    not a deterministic predictor of whether native Rebuild will succeed.
    """
    started = time.time()

    result = {
        "ok": False,
        "min_address": None,
        "max_address": None,
        "free": None,
        "reserve": None,
        "commit": None,
        "largest_free": None,
        "free_regions": None,
        "query_count": 0,
        "elapsed": None,
        "error": None,
    }

    try:
        kernel32 = ctypes.windll.kernel32

        system_info = _SystemInfo()
        kernel32.GetSystemInfo(
            ctypes.byref(
                system_info
            )
        )

        min_address = _contextualizer_pointer_integer(
            system_info.lpMinimumApplicationAddress
        )
        max_address = _contextualizer_pointer_integer(
            system_info.lpMaximumApplicationAddress
        )

        if (
            max_address <= min_address
            or max_address <= 0
        ):
            raise RuntimeError(
                "Invalid application-address bounds."
            )

        MEM_COMMIT = 0x1000
        MEM_RESERVE = 0x2000
        MEM_FREE = 0x10000

        address = min_address
        total_free = 0
        total_reserve = 0
        total_commit = 0
        largest_free = 0
        free_regions = 0
        query_count = 0

        mbi_size = ctypes.sizeof(
            _MemoryBasicInformation
        )

        # Do not build a region list. Keep only primitive counters so the
        # telemetry itself has a bounded, tiny footprint.
        while address <= max_address:
            mbi = _MemoryBasicInformation()

            queried = kernel32.VirtualQuery(
                ctypes.c_void_p(
                    address
                ),
                ctypes.byref(
                    mbi
                ),
                mbi_size,
            )

            if not queried:
                break

            query_count += 1

            region_size = int(
                mbi.RegionSize
            )
            base_address = _contextualizer_pointer_integer(
                mbi.BaseAddress
            )
            state = int(
                mbi.State
            )

            if region_size <= 0:
                raise RuntimeError(
                    "VirtualQuery returned a zero-sized region."
                )

            if state == MEM_FREE:
                total_free += region_size
                free_regions += 1
                if region_size > largest_free:
                    largest_free = region_size

            elif state == MEM_RESERVE:
                total_reserve += region_size

            elif state == MEM_COMMIT:
                total_commit += region_size

            next_address = (
                base_address
                + region_size
            )

            if (
                next_address <= address
                or next_address <= base_address
            ):
                raise RuntimeError(
                    "VirtualQuery address walk did not advance."
                )

            address = next_address

        if query_count <= 0:
            raise RuntimeError(
                "VirtualQuery returned no regions."
            )

        result.update({
            "ok": True,
            "min_address": int(
                min_address
            ),
            "max_address": int(
                max_address
            ),
            "free": int(
                total_free
            ),
            "reserve": int(
                total_reserve
            ),
            "commit": int(
                total_commit
            ),
            "largest_free": int(
                largest_free
            ),
            "free_regions": int(
                free_regions
            ),
            "query_count": int(
                query_count
            ),
        })

    except Exception as exc:
        result["error"] = repr(
            exc
        )

    result["elapsed"] = (
        time.time()
        - started
    )

    return result



class ProbeError(Exception):
    pass


class NativePostFallback(Exception):
    pass


class ContextualCompositionSuccess(Exception):
    pass

def native_ptr(obj):
    if obj is None:
        return None

    try:
        return long(obj.this)
    except Exception:
        try:
            return int(obj.this)
        except Exception:
            return None

def validate_model_backed(aset):
    try:
        if not aset.HasAttribute(
                "gameModel"):
            return False
    except Exception:
        return False

    try:
        game_model = aset.gameModel
    except Exception:
        return False

    return bool(
        game_model is not None
        and native_ptr(
            game_model
        )
    )

def to_unicode(value):
    if isinstance(value, unicode):
        return value

    try:
        return value.decode("utf-8")
    except Exception:
        try:
            return value.decode("latin-1")
        except Exception:
            return unicode(value)

def ascii_fold(value):
    s = to_unicode(value)
    out = []

    for ch in s:
        o = ord(ch)

        if 65 <= o <= 90:
            out.append(chr(o + 32))
        else:
            out.append(ch)

    return u"".join(out)

def handle(obj):
    return int(obj.GetHandle())

def name(obj):
    try:
        return to_unicode(obj.GetName())
    except Exception:
        return u"<UNNAMED>"

def typ(obj):
    try:
        return to_unicode(obj.GetTypeString())
    except Exception:
        return to_unicode(obj.__class__.__name__)

def attr(obj, attr_name):
    try:
        return obj.GetAttribute(attr_name)
    except Exception:
        return None

def scalar(obj, attr_name):
    a = attr(obj, attr_name)

    if a is not None:
        try:
            return a.GetValue()
        except Exception:
            pass

    try:
        return getattr(obj, attr_name)
    except Exception:
        return None

def arr(obj, attr_name):
    a = attr(obj, attr_name)

    if a is None:
        return []

    try:
        count = int(a.Count())
    except Exception:
        try:
            count = len(a)
        except Exception:
            return []

    out = []

    for i in xrange(count):
        try:
            out.append(a[i])
        except Exception:
            try:
                out.append(a.GetValue(i))
            except Exception:
                raise ProbeError(
                    "Cannot read %s[%d] on %r."
                    % (
                        attr_name,
                        i,
                        name(obj),
                    )
                )

    return out

def attribute_name(a):
    try:
        return to_unicode(a.GetName())
    except Exception:
        return u"<ATTR>"

def attribute_type(a):
    try:
        return to_unicode(a.GetTypeString())
    except Exception:
        return u"<TYPE>"

def iter_attributes(element):
    try:
        a = element.FirstAttribute()
    except Exception:
        a = None

    seen = set()

    while a is not None:
        try:
            key = handle(a)
        except Exception:
            key = repr(a)

        if key in seen:
            break

        seen.add(key)
        yield a

        try:
            a = a.NextAttribute()
        except Exception:
            break

def element_ref_pairs(element):
    for a in iter_attributes(element):
        aname = attribute_name(a)
        atype = attribute_type(a).lower()

        if atype == u"element":
            try:
                value = a.GetValue()
            except Exception:
                try:
                    value = a.GetValueUntyped()
                except Exception:
                    value = None

            if value is not None:
                yield aname, value

        elif atype == u"element_array":
            try:
                count = int(a.Count())
            except Exception:
                try:
                    count = len(a)
                except Exception:
                    continue

            for i in xrange(count):
                try:
                    value = a[i]
                except Exception:
                    try:
                        value = a.GetValue(i)
                    except Exception:
                        value = None

                if value is not None:
                    yield (
                        u"%s[%d]" % (aname, i)
                    ), value

def reachable(start, max_elements=50000):
    stack = [start]
    seen = set()
    out = []

    while stack:
        obj = stack.pop()

        try:
            h = handle(obj)
        except Exception:
            continue

        if h in seen:
            continue

        seen.add(h)
        out.append(obj)

        if len(out) > max_elements:
            raise ProbeError(
                "DME traversal exceeded safety cap."
            )

        for unused_attr, child in element_ref_pairs(obj):
            try:
                ch = handle(child)
            except Exception:
                continue

            if ch not in seen:
                stack.append(child)

    return out

def is_visible(group):
    try:
        return bool(group.IsVisible())
    except Exception:
        value = scalar(group, "visible")

        if value is None:
            raise ProbeError(
                "Cannot determine visibility for %r."
                % name(group)
            )

        return bool(value)

def is_selectable(group):
    try:
        return bool(group.IsSelectable())
    except Exception:
        value = scalar(group, "selectable")

        if value is None:
            return None

        return bool(value)

def is_snappable(group):
    try:
        return bool(group.IsSnappable())
    except Exception:
        value = scalar(group, "snappable")

        if value is None:
            return None

        return bool(value)

def _component_value(value, component):
    try:
        out = getattr(value, component)
    except Exception:
        return None

    try:
        if callable(out):
            out = out()
    except Exception:
        return None

    try:
        return int(out)
    except Exception:
        return None

def _parse_rgba_text(value):
    try:
        text = str(value)
    except Exception:
        return None

    nums = re.findall(
        r"-?\d+",
        text
    )

    if len(nums) != 4:
        return None

    try:
        rgba = [int(x) for x in nums]
    except Exception:
        return None

    for x in rgba:
        if x < 0 or x > 255:
            return None

    return rgba

def group_color_rgba(group):
    try:
        value = group.GroupColor()
    except Exception:
        value = None

    if value is not None:
        rgba = []

        for component in ("r", "g", "b", "a"):
            part = _component_value(
                value,
                component
            )

            if part is None:
                rgba = []
                break

            rgba.append(part)

        if len(rgba) == 4:
            return rgba

        parsed = _parse_rgba_text(value)

        if parsed is not None:
            return parsed

    color_attr = attr(group, "groupColor")

    if color_attr is not None:
        try:
            value = color_attr.GetValue()
        except Exception:
            value = None

        if value is not None:
            rgba = []

            for component in ("r", "g", "b", "a"):
                part = _component_value(
                    value,
                    component
                )

                if part is None:
                    rgba = []
                    break

                rgba.append(part)

            if len(rgba) == 4:
                return rgba

            parsed = _parse_rgba_text(value)

            if parsed is not None:
                return parsed

    raise ProbeError(
        "Could not serialize GroupColor for %r."
        % name(group)
    )

def children(group):
    return [
        obj
        for obj in arr(group, "children")
        if typ(obj) == u"DmeControlGroup"
    ]

def direct_controls(group):
    return arr(group, "controls")

def path_string(parts):
    if not parts:
        return u"<ROOT>"

    return u"/".join(parts)

def capture_tree(root):
    groups = {}
    memberships = {}
    duplicate_siblings = []
    duplicate_direct_controls = []

    def walk(
        group,
        parts,
        parent_path,
        ancestor_visible,
    ):
        path = path_string(parts)

        if path in groups:
            raise ProbeError(
                "Duplicate semantic group path encountered: %r"
                % path
            )

        visible = is_visible(group)
        effective_visible = bool(
            ancestor_visible
            and visible
        )

        child_groups = children(group)
        child_names = [
            name(child)
            for child in child_groups
        ]

        sibling_counts = {}

        for child_name in child_names:
            sibling_counts[child_name] = (
                sibling_counts.get(
                    child_name,
                    0
                )
                + 1
            )

        for child_name, count in sibling_counts.items():
            if count > 1:
                duplicate_siblings.append({
                    "parent": path,
                    "name": child_name,
                    "count": count,
                })

        control_objs = direct_controls(group)
        control_names = [
            name(control)
            for control in control_objs
        ]

        direct_counts = {}

        for control_name in control_names:
            direct_counts[control_name] = (
                direct_counts.get(
                    control_name,
                    0
                )
                + 1
            )

        for control_name, count in direct_counts.items():
            if count > 1:
                duplicate_direct_controls.append({
                    "path": path,
                    "name": control_name,
                    "count": count,
                })

        for control_name in control_names:
            memberships.setdefault(
                control_name,
                []
            ).append(path)

        groups[path] = {
            "path": path,
            "name": (
                u"<ROOT>"
                if not parts
                else parts[-1]
            ),
            "parent_path": parent_path,
            "visible": visible,
            "effective_visible": effective_visible,
            "selectable": is_selectable(group),
            "snappable": is_snappable(group),
            "group_color": group_color_rgba(group),
            # IMPORTANT: deliberately unsorted.
            "child_names_in_order": child_names,
            "direct_control_names_in_order": control_names,
        }

        for child in child_groups:
            child_parts = list(parts)
            child_parts.append(name(child))

            walk(
                child,
                child_parts,
                path,
                effective_visible,
            )

    walk(
        root,
        [],
        None,
        True,
    )

    duplicate_memberships = dict([
        (
            control_name,
            paths,
        )
        for control_name, paths in memberships.items()
        if len(paths) > 1
    ])

    return {
        "groups": groups,
        "memberships": memberships,
        "group_count": len(groups),
        "duplicate_sibling_groups": duplicate_siblings,
        "duplicate_direct_controls": duplicate_direct_controls,
        "duplicate_memberships": duplicate_memberships,
    }

def sha256_stream(path):
    h = hashlib.sha256()

    f = open(path, "rb")

    try:
        while True:
            block = f.read(READ_BLOCK)

            if not block:
                break

            h.update(block)

    finally:
        f.close()

    return h.hexdigest()


class BufferedChars(object):
    def __init__(self, path):
        self.f = open(path, "rb")
        self.buf = ""
        self.pos = 0
        self.pushback = []

    def close(self):
        try:
            self.f.close()
        except Exception:
            pass

    def get(self):
        if self.pushback:
            return self.pushback.pop()

        if self.pos >= len(self.buf):
            self.buf = self.f.read(
                READ_BLOCK
            )
            self.pos = 0

            if not self.buf:
                return None

        ch = self.buf[self.pos]
        self.pos += 1
        return ch

    def unget(self, ch):
        if ch is not None:
            self.pushback.append(ch)


def stream_tokens(path):
    chars = BufferedChars(path)

    try:
        first = chars.get()

        if first == "\xef":
            second = chars.get()
            third = chars.get()

            if not (
                second == "\xbb"
                and third == "\xbf"
            ):
                chars.unget(third)
                chars.unget(second)
                chars.unget(first)
        else:
            chars.unget(first)

        while True:
            ch = chars.get()

            if ch is None:
                return

            if ch.isspace():
                continue

            if ch == "/":
                nxt = chars.get()

                if nxt == "/":
                    while True:
                        c = chars.get()

                        if (
                            c is None
                            or c in (
                                "\r",
                                "\n",
                            )
                        ):
                            break

                    continue

                chars.unget(nxt)

            if ch in "{}":
                yield ch
                continue

            if ch == '"':
                buf = []

                while True:
                    c = chars.get()

                    if c is None:
                        raise ProbeError(
                            "Unterminated quoted string in Master."
                        )

                    if c == '"':
                        break

                    if c == "\\":
                        nxt = chars.get()

                        if nxt is None:
                            raise ProbeError(
                                "Unterminated escape in Master."
                            )

                        if nxt == "n":
                            buf.append("\n")
                        elif nxt == "r":
                            buf.append("\r")
                        elif nxt == "t":
                            buf.append("\t")
                        else:
                            buf.append(nxt)

                        continue

                    buf.append(c)

                yield "".join(buf)
                continue

            buf = [ch]

            while True:
                c = chars.get()

                if c is None:
                    break

                if c.isspace():
                    break

                if c in '{}"':
                    chars.unget(c)
                    break

                if c == "/":
                    nxt = chars.get()

                    if nxt == "/":
                        while True:
                            cc = chars.get()

                            if (
                                cc is None
                                or cc in (
                                    "\r",
                                    "\n",
                                )
                            ):
                                break

                        break

                    chars.unget(nxt)

                buf.append(c)

            yield "".join(buf)

            if c is None:
                return

    finally:
        chars.close()

def parse_master_bool_text(
        value,
        label):
    if value is None:
        return None

    folded = to_unicode(
        value
    ).strip().lower()

    if folded in (
        u"1",
        u"true",
        u"yes",
    ):
        return True

    if folded in (
        u"0",
        u"false",
        u"no",
    ):
        return False

    raise ProbeError(
        "Cannot parse Master boolean %s=%r."
        % (
            label,
            value,
        )
    )


def parse_master_rgba_text(
        value,
        label):
    if value is None:
        return None

    nums = re.findall(
        r"-?\d+",
        to_unicode(
            value
        )
    )

    if len(nums) != 4:
        raise ProbeError(
            "Cannot parse Master RGBA %s=%r."
            % (
                label,
                value,
            )
        )

    rgba = [
        int(x)
        for x in nums
    ]

    for component in rgba:
        if (
            component < 0
            or component > 255
        ):
            raise ProbeError(
                "Out-of-range Master RGBA %s=%r."
                % (
                    label,
                    value,
                )
            )

    return rgba


def acquire_master_index_via_qualified_authority(
        master_path,
        wanted_folds,
        shipped_root,
        allow_local_candidates=False,
        local_pointer_path=None,
        generated_root=None,
        runtime_cap_bytes=None,
        expected_generation=None):
    """R3-B2C-B migrated authority acquisition -- replaces the single
    parse_targeted_master(...) call site below. Returns
    (payload, lease): `payload` is the EXACT SAME return-dict contract
    (mapping_count, destination_count, folded, exact_literals,
    group_sibling_order, group_metadata) -- see normalizer_compat_
    adapter.py's module docstring for field-by-field provenance and the
    real-Python-2.7.5 full-corpus equivalence proof (combined canonical
    structure hash
    3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2,
    matched exactly on both sides across all 124,728 real folds).

    Astra F3 correction: `lease` is a views.ViewLease the caller now
    holds explicit, trackable ownership of `payload` through -- the
    pre-correction version returned the bare payload dict alone, so a
    consumer's continued use of it after the underlying view was evicted
    from the broker's cache (e.g. by a later, unrelated acquisition
    under memory pressure) was invisible to the ledger: a real,
    reproduced undercount. The caller MUST release this lease
    deterministically once done with `payload` (command completion,
    cancellation, failure, or dialog/operation close) via
    `broker.release_view_lease(lease)` -- never relying on Python
    garbage-collection timing. `payload` itself remains the SAME plain
    dict as before (no wrapper), preserving existing downstream
    GATE/TARGET/reconciliation code unchanged; only the call site needs
    to additionally hold and release the lease.

    Uses the ONE canonical broker (authority_runtime.get_broker) and
    acquire_or_reuse_views -- generation-stable cache reuse, at most one
    provider open for a cache miss, zero for a cache hit; never a second,
    ad hoc broker instance. is_main_thread_fn is intentionally omitted:
    this function is only ever reached from the Normalizer's own single
    Qt/Python thread, by the whole file's existing architecture (see
    module docstring's Qt-callback responsiveness policy) -- there is no
    separate thread-identity claim to make here that isn't already true
    of every other call in this file.

    `shipped_root` MUST be supplied by the caller -- there is deliberately
    no built-in default. Real-production shipped-sidecar deployment
    location has not yet been finalized by any prior B2 stage (see the
    B2C-B report's "open item" note); the production call site below
    passes a provisional, clearly-flagged path derived from the already-
    resolved usermod_dir, not a settled production convention.

    Astra F6 correction: main-thread policy is now enforced at this REAL
    entry point via the standard Qt idiom (is the current thread the
    same thread QCoreApplication itself lives on) instead of being
    silently omitted (the pre-correction call passed no
    is_main_thread_fn at all, so get_broker()'s own main-thread check
    was skipped entirely on first construction). NOTE: this idiom is
    the well-established, standard PySide/Qt pattern, but has not been
    exercised against a live real-SFM Qt event loop by this offline
    correction gate ("Do not run SFM") -- flagged explicitly rather than
    silently assumed correct; real-SFM verification remains an open item
    before B2C-R.

    Astra second-correction-gate F4: `expected_generation`, when given,
    is the COMMAND's own pinned expected source generation (real
    production call site passes `self.master_hash`, captured once at
    command start in derive_paths()) -- forwarded to broker.acquire_or_
    reuse_views, which now verifies EVERY returned view (reused AND
    freshly acquired alike) carries exactly this generation before ever
    returning, retrying once (the SAME single combined retry budget that
    also covers H0/H1 instability) or raising
    errors.AuthorityChangedDuringAcquisition -- never silently handing a
    command pinned to generation A a view of generation B. Do NOT treat
    this (or the underlying H0/H1 SHA comparison) as a file lock -- it
    is a content-hash observation with the documented edit-then-exact-
    restore blind spot already established in B2A; it detects drift, it
    does not prevent it."""
    broker = _b2c_authority_runtime.get_broker(
        expected_api_version=_B2C_EXPECTED_API_VERSION,
        expected_build_id=_B2C_EXPECTED_BUILD_ID,
        is_main_thread_fn=lambda: (
            QtCore.QThread.currentThread() is QtCore.QCoreApplication.instance().thread()
            if QtCore.QCoreApplication.instance() is not None else True
        )
    )
    folded_key = frozenset(wanted_folds)
    builder = _b2c_normalizer_adapter.build_targeted_master_compatible_projection(folded_key)
    request_specs = {"normalizer_compat": (folded_key, builder)}
    detached = broker.acquire_or_reuse_views(
        master_path, request_specs,
        allow_local_candidates=allow_local_candidates,
        local_pointer_path=local_pointer_path,
        generated_root=generated_root,
        shipped_root=shipped_root,
        runtime_cap_bytes=runtime_cap_bytes,
        expected_generation=expected_generation,
    )
    view = detached["normalizer_compat"]
    lease = broker.lease_view(view)
    return view.payload, lease


def parse_targeted_master(
    path,
    wanted_folds,
    validate_conflicts=True,
):
    token_iter = stream_tokens(path)

    def take():
        try:
            return token_iter.next()
        except AttributeError:
            try:
                return next(token_iter)
            except StopIteration:
                raise ProbeError(
                    "Unexpected end of Master token stream."
                )
        except StopIteration:
            raise ProbeError(
                "Unexpected end of Master token stream."
            )

    if take() != "groupFile":
        raise ProbeError(
            "Master root is not groupFile."
        )

    if take() != "{":
        raise ProbeError(
            "Missing opening groupFile brace."
        )

    stack = []
    mappings = {}
    exact_literals = set()
    total_mapping_count = 0
    destination_set = set()
    local_counts = {}
    group_sibling_order = {
        u"<ROOT>": []
    }
    group_metadata = {}
    seen_group = set()

    while True:
        key = take()

        if key == "}":
            if not stack:
                break

            stack.pop()
            continue

        value = take()

        if value == "{":
            parent = (
                u"<ROOT>"
                if not stack
                else u"/".join([
                    to_unicode(x)
                    for x in stack
                ])
            )

            group_name = to_unicode(key)
            group_sibling_order.setdefault(
                parent,
                []
            )

            marker = (
                parent,
                group_name,
            )

            if marker not in seen_group:
                seen_group.add(marker)
                group_sibling_order[
                    parent
                ].append(group_name)

            stack.append(group_name)

            current_path = u"/".join([
                to_unicode(x)
                for x in stack
            ])

            group_sibling_order.setdefault(
                current_path,
                []
            )

            if current_path in group_metadata:
                raise ProbeError(
                    "Duplicate Master semantic group path: %r."
                    % current_path
                )

            group_metadata[
                current_path
            ] = {
                "path": current_path,
                "groupColor_raw": [],
                "selectable_raw": [],
                "visible_raw": [],
                "snappable_raw": [],
            }
            continue

        if value == "}":
            raise ProbeError(
                "Unexpected closing brace after %r."
                % key
            )

        current_path = u"/".join([
            to_unicode(x)
            for x in stack
        ])

        if key == "control":
            destination = current_path

            local_index = local_counts.get(
                destination,
                0,
            )
            local_counts[
                destination
            ] = local_index + 1

            literal = to_unicode(value)
            folded = ascii_fold(literal)
            global_index = total_mapping_count

            total_mapping_count += 1
            destination_set.add(destination)

            if folded not in wanted_folds:
                continue

            exact_literals.add(literal)

            mappings.setdefault(
                folded,
                []
            ).append({
                "literal": literal,
                "destination": destination,
                "global_index": global_index,
                "local_index": local_index,
            })

            continue

        if not current_path:
            continue

        meta = group_metadata.get(
            current_path
        )

        if meta is None:
            raise ProbeError(
                "Master scalar metadata has no current group: %r=%r."
                % (
                    key,
                    value,
                )
            )

        field_map = {
            "groupColor": "groupColor_raw",
            "selectable": "selectable_raw",
            "visible": "visible_raw",
            "snappable": "snappable_raw",
        }

        target_field = field_map.get(
            key
        )

        if target_field is not None:
            meta[
                target_field
            ].append(
                to_unicode(
                    value
                )
            )

    conflicts = []

    for folded, rows in mappings.items():
        destinations = sorted(
            set([
                row["destination"]
                for row in rows
            ])
        )

        if len(destinations) > 1:
            conflicts.append(
                (
                    folded,
                    destinations,
                )
            )

    if (
        conflicts
        and validate_conflicts
    ):
        raise ProbeError(
            "Targeted live-Master casefold conflict(s): %r"
            % conflicts[:10]
        )

    # Normalize only the metadata whose semantics are now promoted.
    for path_key, meta in group_metadata.items():
        for raw_key in (
            "groupColor_raw",
            "selectable_raw",
            "visible_raw",
            "snappable_raw",
        ):
            rows = meta[
                raw_key
            ]

            if len(rows) > 1:
                raise ProbeError(
                    "Master group %r has duplicate %s metadata: %r."
                    % (
                        path_key,
                        raw_key,
                        rows,
                    )
                )

        color_raw = (
            meta[
                "groupColor_raw"
            ][0]
            if meta[
                "groupColor_raw"
            ]
            else None
        )

        selectable_raw = (
            meta[
                "selectable_raw"
            ][0]
            if meta[
                "selectable_raw"
            ]
            else None
        )

        meta[
            "group_color_explicit"
        ] = (
            None
            if color_raw is None
            else parse_master_rgba_text(
                color_raw,
                path_key
                + u".groupColor",
            )
        )

        # Preserve absence. Explicit 1/0 is Master-authoritative; omitted
        # selectable is resolved later from the fresh canonical native-POST
        # semantic counterpart for this exact transaction.
        meta[
            "selectable_explicit"
        ] = (
            None
            if selectable_raw is None
            else parse_master_bool_text(
                selectable_raw,
                path_key
                + u".selectable",
            )
        )

        meta[
            "selectable_authority"
        ] = (
            "CANONICAL_NATIVE_POST_DEFAULT"
            if selectable_raw is None
            else "EXPLICIT_MASTER_FIELD"
        )

    return {
        "mapping_count": total_mapping_count,
        "destination_count": len(
            destination_set
        ),
        "folded": mappings,
        "exact_literals": exact_literals,
        "group_sibling_order": group_sibling_order,
        "group_metadata": group_metadata,
    }


def validate_master_subset_conflicts(
        master,
        wanted_folds):
    conflicts = []

    for folded in wanted_folds:
        rows = master[
            "folded"
        ].get(
            folded,
            [],
        )

        if not rows:
            continue

        destinations = sorted(
            set([
                row[
                    "destination"
                ]
                for row in rows
            ])
        )

        if len(
                destinations) > 1:
            conflicts.append(
                (
                    folded,
                    destinations,
                )
            )

    if conflicts:
        raise ProbeError(
            "Targeted live-Master casefold conflict(s): %r"
            % conflicts[:10]
        )


def master_lookup(master, literal):
    folded = ascii_fold(literal)
    rows = master[
        "folded"
    ].get(
        folded,
        [],
    )

    if not rows:
        return {
            "known": False,
            "destination": None,
            "mode": "NONE",
            "global_index": None,
            "local_index": None,
        }

    destinations = sorted(
        set([
            row["destination"]
            for row in rows
        ])
    )

    if len(destinations) != 1:
        raise ProbeError(
            "Multiple targeted Master destinations for %r: %r"
            % (
                literal,
                destinations,
            )
        )

    first = sorted(
        rows,
        key=lambda row: (
            row["global_index"],
            row["local_index"],
        )
    )[0]

    return {
        "known": True,
        "destination": destinations[0],
        "mode": (
            "EXACT"
            if to_unicode(literal)
            in master["exact_literals"]
            else "ASCII_CASEFOLD"
        ),
        "global_index": first[
            "global_index"
        ],
        "local_index": first[
            "local_index"
        ],
    }

def one_membership(snap, control_name):
    rows = snap[
        "memberships"
    ].get(
        to_unicode(control_name),
        [],
    )

    if len(rows) != 1:
        return None

    return to_unicode(rows[0])

def immediate_parent_path(path):
    p = to_unicode(path)

    if p in (
        u"",
        u"<ROOT>",
    ):
        return None

    if u"/" not in p:
        return u"<ROOT>"

    return p.rsplit(
        u"/",
        1
    )[0]

def first_path_part(path):
    if path is None:
        return None

    p = to_unicode(path)

    if p in (
        u"",
        u"<ROOT>",
    ):
        return None

    return p.split(
        u"/",
        1
    )[0]

def find_direct_child(parent, child_name):
    target = to_unicode(child_name)

    matches = [
        group
        for group in children(parent)
        if name(group) == target
    ]

    if len(matches) > 1:
        raise ProbeError(
            "Duplicate direct child %r under %r."
            % (
                child_name,
                name(parent),
            )
        )

    return (
        matches[0]
        if matches
        else None
    )

def set_visible(group, value):
    try:
        group.SetVisible(
            bool(value)
        )
        return
    except Exception:
        pass

    a = attr(group, "visible")

    if a is not None:
        try:
            a.SetValue(
                bool(value)
            )
            return
        except Exception:
            pass

    raise ProbeError(
        "Cannot set visibility on %r."
        % name(group)
    )

def set_selectable(group, value):
    if value is None:
        return

    try:
        group.SetSelectable(
            bool(value)
        )
    except Exception as exc:
        raise ProbeError(
            "SetSelectable failed for %r: %s"
            % (
                name(group),
                str(exc),
            )
        )

def set_snappable(group, value):
    if value is None:
        return

    try:
        group.SetSnappable(
            bool(value)
        )
    except Exception as exc:
        raise ProbeError(
            "SetSnappable failed for %r: %s"
            % (
                name(group),
                str(exc),
            )
        )

def set_group_color(group, rgba):
    if rgba is None:
        return

    color = vs.Color(
        int(rgba[0]),
        int(rgba[1]),
        int(rgba[2]),
        int(rgba[3]),
    )

    try:
        group.SetGroupColor(
            color,
            False,
        )
    except Exception as exc:
        raise ProbeError(
            "SetGroupColor failed for %r: %s"
            % (
                name(group),
                str(exc),
            )
        )

    actual = group_color_rgba(group)

    if list(actual) != list(rgba):
        raise ProbeError(
            "GroupColor verification failed for %r."
            % name(group)
        )

def apply_source_metadata(
    group,
    source_meta,
):
    if source_meta is None:
        raise ProbeError(
            "Missing source metadata for %r."
            % name(group)
        )

    set_visible(group, True)
    set_selectable(
        group,
        source_meta.get("selectable"),
    )
    set_snappable(
        group,
        source_meta.get("snappable"),
    )
    set_group_color(
        group,
        source_meta.get("group_color"),
    )

def create_independent_group(
    root,
    parent,
    technical_name,
):
    try:
        group = root.CreateControlGroup(
            str(technical_name)
        )
    except Exception as exc:
        raise ProbeError(
            "CreateControlGroup(%r) failed: %s"
            % (
                technical_name,
                str(exc),
            )
        )

    if group is None:
        raise ProbeError(
            "CreateControlGroup(%r) returned None."
            % technical_name
        )

    if handle(parent) != handle(root):
        try:
            parent.AddChild(group)
        except Exception as exc:
            raise ProbeError(
                "AddChild failed for %r: %s"
                % (
                    technical_name,
                    str(exc),
                )
            )

    found = [
        child
        for child in children(parent)
        if handle(child) == handle(group)
    ]

    if len(found) != 1:
        raise ProbeError(
            "Created group %r not present exactly once under intended parent."
            % technical_name
        )

    set_visible(group, True)

    return group

def add_control_to_group(group, control):
    try:
        group.AddControl(control)
    except Exception as exc:
        raise ProbeError(
            "AddControl failed for %r -> %r: %s"
            % (
                name(control),
                name(group),
                str(exc),
            )
        )

def rename_group(group, final_name):
    old_handle = handle(group)

    try:
        group.SetName(
            str(final_name)
        )
    except Exception as exc:
        raise ProbeError(
            "SetName failed for handle=%d -> %r: %s"
            % (
                old_handle,
                final_name,
                str(exc),
            )
        )

    if handle(group) != old_handle:
        raise ProbeError(
            "Group handle changed during rename."
        )

    if name(group) != to_unicode(final_name):
        raise ProbeError(
            "Rename did not stick for handle=%d."
            % old_handle
        )

def technical_group_name(
    layer_tag,
    depth,
    canonical_prefix,
):
    encoded = u"__".join([
        to_unicode(x)
        for x in canonical_prefix
    ])

    return u"__E2E_%s_%02d__%s" % (
        to_unicode(layer_tag),
        int(depth),
        encoded,
    )

def live_control_map(aset):
    return dict([
        (
            name(control),
            control,
        )
        for control in arr(aset, "controls")
    ])

def target_tree_from_rows(candidate_rows):
    tree = {
        u"<ROOT>": []
    }

    for row in candidate_rows:
        path = to_unicode(
            row["relative_path"]
        )

        # <ROOT> means the control is directly on the animation-set root.
        # It is not a child group and must never become <ROOT> -> <ROOT>.
        if path == u"<ROOT>":
            continue

        parts = path.split(u"/")
        parent = u"<ROOT>"
        prefix = []

        for part in parts:
            prefix.append(part)
            child_path = u"/".join(prefix)
            tree.setdefault(
                parent,
                []
            )

            if child_path not in tree[parent]:
                tree[parent].append(
                    child_path
                )

            tree.setdefault(
                child_path,
                []
            )
            parent = child_path

    return tree

def source_child_name(
    parent_path,
    child_path,
):
    if parent_path == u"<ROOT>":
        return to_unicode(
            child_path
        ).split(u"/", 1)[0]

    prefix = to_unicode(
        parent_path
    ) + u"/"

    remainder = to_unicode(
        child_path
    )[len(prefix):]

    return remainder.split(
        u"/",
        1,
    )[0]

def pre_child_order(
    pre,
    parent_path,
    child_names,
):
    meta = pre[
        "groups"
    ].get(
        parent_path
    )

    if meta is None:
        raise ProbeError(
            "PRE has no source parent %r."
            % parent_path
        )

    order = [
        to_unicode(x)
        for x in meta[
            "child_names_in_order"
        ]
        if to_unicode(x)
        in child_names
    ]

    if set(order) != set(child_names):
        raise ProbeError(
            "PRE child-order projection incomplete for %r."
            % parent_path
        )

    return order

def policy_child_order(
    master,
    pre,
    parent_path,
    child_names,
):
    child_names = [
        to_unicode(x)
        for x in child_names
    ]

    master_siblings = [
        to_unicode(x)
        for x in master[
            "group_sibling_order"
        ].get(
            parent_path,
            [],
        )
    ]

    known = [
        child
        for child in child_names
        if child in master_siblings
    ]

    contextual = [
        child
        for child in child_names
        if child not in master_siblings
    ]

    ordered_known = [
        child
        for child in master_siblings
        if child in known
    ]

    ordered_contextual = []

    if contextual:
        meta = pre[
            "groups"
        ].get(
            parent_path
        )

        if meta is None:
            raise ProbeError(
                "PRE has no source parent %r for contextual sibling ordering."
                % parent_path
            )

        wanted = set(
            contextual
        )

        ordered_contextual = [
            to_unicode(x)
            for x in meta[
                "child_names_in_order"
            ]
            if to_unicode(x)
            in wanted
        ]

        if set(
                ordered_contextual
                ) != wanted:
            raise ProbeError(
                "PRE contextual child-order projection incomplete for %r."
                % parent_path
            )

    if known and contextual:
        return (
            "MASTER_PLUS_CONTEXTUAL_PRE",
            ordered_known
            + ordered_contextual,
        )

    if known:
        return (
            "MASTER",
            ordered_known,
        )

    return (
        "RIG_PRE_FALLBACK",
        ordered_contextual,
    )

def policy_direct_order(
    master,
    pre,
    source_path,
    control_names,
):
    known = []
    unknown = []

    for control_name in control_names:
        control_name = to_unicode(
            control_name
        )
        lookup = master_lookup(
            master,
            control_name,
        )

        if lookup["known"]:
            known.append((
                lookup[
                    "global_index"
                ],
                lookup[
                    "local_index"
                ],
                control_name,
            ))
        else:
            unknown.append(
                control_name
            )

    if known and unknown:
        meta = pre[
            "groups"
        ].get(
            source_path
        )

        if meta is None:
            raise ProbeError(
                "PRE has no source group %r for mixed direct ordering."
                % source_path
            )

        wanted = set([
            to_unicode(x)
            for x in control_names
        ])

        projected = [
            to_unicode(x)
            for x in meta[
                "direct_control_names_in_order"
            ]
            if to_unicode(x)
            in wanted
        ]

        if set(projected) != wanted:
            raise ProbeError(
                "PRE mixed direct-control projection incomplete for %r."
                % source_path
            )

        return (
            "MIXED_MASTER_KNOWN_UNKNOWN_PRE_TOTAL_ORDER",
            projected,
        )

    if known:
        known.sort(
            key=lambda row: (
                row[0],
                row[1],
            )
        )

        return (
            "MASTER",
            [
                row[2]
                for row in known
            ],
        )

    meta = pre[
        "groups"
    ].get(
        source_path
    )

    if meta is None:
        raise ProbeError(
            "PRE has no source group %r."
            % source_path
        )

    wanted = set([
        to_unicode(x)
        for x in control_names
    ])

    projected = [
        to_unicode(x)
        for x in meta[
            "direct_control_names_in_order"
        ]
        if to_unicode(x)
        in wanted
    ]

    if set(projected) != wanted:
        raise ProbeError(
            "PRE direct-control projection incomplete for %r."
            % source_path
        )

    return (
        "RIG_PRE_FALLBACK",
        projected,
    )

def hierarchical_path_rank(
    master,
    pre,
    tree,
    source_path,
):
    if source_path == u"<ROOT>":
        return ()

    parts = to_unicode(
        source_path
    ).split(u"/")

    rank = []
    parent = u"<ROOT>"
    prefix = []

    for part in parts:
        prefix.append(part)
        siblings = tree.get(
            parent,
            []
        )
        child_names = [
            source_child_name(
                parent,
                child_path,
            )
            for child_path in siblings
        ]

        unused_authority, ordered_names = policy_child_order(
            master,
            pre,
            parent,
            child_names,
        )

        if part not in ordered_names:
            raise ProbeError(
                "Cannot rank child %r under %r."
                % (
                    part,
                    parent,
                )
            )

        rank.append(
            ordered_names.index(
                part
            )
        )

        parent = u"/".join(prefix)

    return tuple(rank)

def order_candidate_rows_by_policy(
    candidate_rows,
    master,
    pre,
):
    tree = target_tree_from_rows(
        candidate_rows
    )

    by_path = {}

    for row in candidate_rows:
        path = to_unicode(
            row["relative_path"]
        )
        by_path.setdefault(
            path,
            []
        ).append(
            to_unicode(
                row["name"]
            )
        )

    direct_rank = {}
    authority = {}

    for path, control_names in by_path.items():
        auth, ordered = policy_direct_order(
            master,
            pre,
            path,
            control_names,
        )
        authority[path] = auth

        for index, control_name in enumerate(
                ordered):
            direct_rank[
                (
                    path,
                    control_name,
                )
            ] = index

    decorated = []

    for row in candidate_rows:
        path = to_unicode(
            row["relative_path"]
        )
        control_name = to_unicode(
            row["name"]
        )

        decorated.append((
            hierarchical_path_rank(
                master,
                pre,
                tree,
                path,
            ),
            direct_rank[
                (
                    path,
                    control_name,
                )
            ],
            row,
        ))

    decorated.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    return (
        [
            item[2]
            for item in decorated
        ],
        tree,
        authority,
    )

def build_visible_layer(
    root,
    wrapper_name,
    layer_tag,
    candidate_rows,
    live_controls,
    source_snapshot,
):
    if find_direct_child(
            root,
            wrapper_name) is not None:
        raise ProbeError(
            "Wrapper %r already exists before mutation."
            % wrapper_name
        )

    wrapper = create_independent_group(
        root,
        root,
        wrapper_name,
    )

    set_visible(wrapper, True)

    nodes = {}
    created = []

    for row in candidate_rows:
        control_name = to_unicode(
            row["name"]
        )

        control = live_controls.get(
            control_name
        )

        if control is None:
            raise ProbeError(
                "Live candidate %r disappeared."
                % control_name
            )

        relative_path = to_unicode(
            row["relative_path"]
        )

        parts = relative_path.split(u"/")

        parent = wrapper
        prefix = []

        for depth in xrange(
            1,
            len(parts) + 1,
        ):
            prefix.append(
                parts[depth - 1]
            )

            key = u"/".join(prefix)
            node = nodes.get(key)

            if node is None:
                source_meta = source_snapshot[
                    "groups"
                ].get(key)

                if source_meta is None:
                    raise ProbeError(
                        "No PRE metadata for required path %r."
                        % key
                    )

                technical = technical_group_name(
                    layer_tag,
                    depth,
                    prefix,
                )

                node = create_independent_group(
                    root,
                    parent,
                    technical,
                )

                apply_source_metadata(
                    node,
                    source_meta,
                )

                nodes[key] = node

                created.append({
                    "obj": node,
                    "source_path": key,
                    "depth": depth,
                    "final_name": parts[
                        depth - 1
                    ],
                })

            parent = node

        add_control_to_group(
            parent,
            control,
        )

    for row in sorted(
        created,
        key=lambda item: -item["depth"],
    ):
        rename_group(
            row["obj"],
            row["final_name"],
        )

    return {
        "wrapper": wrapper,
        "created": created,
    }


def capture_direct_anchor_state(group):
    return {
        "handle": handle(group),
        "name": name(group),
        "visible": is_visible(group),
        "selectable": is_selectable(group),
        "snappable": is_snappable(group),
        "group_color": list(group_color_rgba(group)),
        "direct_handles": [handle(x) for x in direct_controls(group)],
        "direct_names": [name(x) for x in direct_controls(group)],
        "child_handles": [handle(x) for x in children(group)],
        "child_names": [name(x) for x in children(group)],
    }


def direct_anchor_preflight(
        root,
        rig_rows,
        master_rows,
        classified,
        rig_source,
        post):
    # Phase-2 cross-model generalization remains intentionally narrow: only
    # modern RIG_OWNED_EFFECTIVE_CONTROL rows whose captured contextual
    # destination is exactly one top-level rig family anchor are direct-eligible.
    # Parent-collapse, strong-unknown, Master-stranded, and nested paths remain
    # outside this direct-anchor scope and therefore retain validated legacy behavior.
    if master_rows:
        return {
            "status": "LEGACY_WRAPPER",
            "reason": "Master-stranded rows are outside this simple-direct generalization scope.",
        }

    rig_loss_names = set([
        to_unicode(row["name"])
        for row in classified["rig_losses"]
        if to_unicode(row["pre_path"]) in DIRECT_ANCHOR_NAMES
    ])

    ordered_names = [
        to_unicode(row["name"])
        for row in rig_rows
    ]

    if len(set(ordered_names)) != len(ordered_names):
        return {
            "status": "LEGACY_WRAPPER",
            "reason": "Duplicate candidate names in ordered rig rows.",
        }

    if set(ordered_names) != rig_loss_names:
        return {
            "status": "LEGACY_WRAPPER",
            "reason": (
                "Rig rows are not exactly the simple direct-anchor rig-loss set."
            ),
        }

    if not ordered_names:
        return {
            "status": "LEGACY_WRAPPER",
            "reason": "No direct-anchor rig-loss rows.",
        }

    if len(classified["rig_losses"]) != len(ordered_names):
        return {
            "status": "LEGACY_WRAPPER",
            "reason": "At least one rig-loss row is nested or outside simple top-level direct anchors.",
        }

    if (
        classified["parent_collapses"]
        or classified["master_unknown_unknown"]
    ):
        return {
            "status": "LEGACY_WRAPPER",
            "reason": "Other contextual rig classes are present.",
        }

    rows_by_anchor = {}
    for row in rig_rows:
        anchor = to_unicode(row["relative_path"])
        if anchor not in DIRECT_ANCHOR_NAMES:
            return {
                "status": "LEGACY_WRAPPER",
                "reason": "Nested or noncanonical direct destination %r." % anchor,
            }
        rows_by_anchor.setdefault(anchor, []).append(row)

    plan = {
        "status": "DIRECT",
        "reason": None,
        "anchors": {},
        "rows_by_anchor": rows_by_anchor,
    }

    for anchor in DIRECT_ANCHOR_NAMES:
        rows = rows_by_anchor.get(anchor, [])
        if not rows:
            continue

        source_meta = rig_source["groups"].get(anchor)
        if source_meta is None:
            return {
                "status": "LEGACY_WRAPPER",
                "reason": "Fresh rig PRE has no source metadata for %r." % anchor,
            }

        existing = find_direct_child(root, anchor)
        candidate_names = [to_unicode(row["name"]) for row in rows]

        if existing is not None:
            state = capture_direct_anchor_state(existing)
            existing_names = list(state["direct_names"])

            # A modern rig-loss should not already be a direct member of the
            # final anchor after native Rebuild. If it is, refuse to improvise.
            overlap = sorted(set(existing_names).intersection(candidate_names))
            if overlap:
                return {
                    "status": "LEGACY_WRAPPER",
                    "reason": "Direct candidate already present in %r: %r" % (
                        anchor,
                        overlap,
                    ),
                }

            plan["anchors"][anchor] = {
                "existing": True,
                "group": existing,
                "before": state,
                "source_meta": source_meta,
                "candidate_names": candidate_names,
                # Simple-direct composed order: preserve every pre-existing direct
                # member in its exact current order, then append the already
                # policy-ordered direct candidates. No eager reorder pass.
                "expected_direct_names": existing_names + candidate_names,
            }
            continue

        # Phase-2 generalization permits any supported simple top-level final
        # anchor to be genuinely absent after native Rebuild. The source anchor
        # must have existed in fresh contextual PRE (source_meta above), and the
        # new object is created only through the globally unique technical-name
        # discipline before exact-object rename.
        technical = technical_group_name(
            "DIRECT_ANCHOR",
            1,
            [anchor],
        )

        if find_direct_child(root, technical) is not None:
            return {
                "status": "LEGACY_WRAPPER",
                "reason": "Technical direct-anchor name already exists for %r." % anchor,
            }

        plan["anchors"][anchor] = {
            "existing": False,
            "group": None,
            "before": None,
            "source_meta": source_meta,
            "technical_name": technical,
            "candidate_names": candidate_names,
            "expected_direct_names": list(candidate_names),
        }

    # Every candidate must currently have a single native-POST membership and
    # every planned source path must still be the exact captured PRE path.
    for row in rig_rows:
        control_name = to_unicode(row["name"])
        anchor = to_unicode(row["relative_path"])

        pre_membership = one_membership(rig_source, control_name)
        post_membership = one_membership(post, control_name)

        if pre_membership != anchor:
            return {
                "status": "LEGACY_WRAPPER",
                "reason": "Fresh contextual PRE destination changed for %r." % control_name,
            }

        if post_membership is None:
            return {
                "status": "LEGACY_WRAPPER",
                "reason": "Native POST membership is ambiguous for %r." % control_name,
            }

    return plan


def build_direct_anchor(
        root,
        direct_plan,
        live_controls):
    result = {
        "anchors": {},
        "created": [],
    }

    # Resolve/create every final anchor before moving the first candidate.
    for anchor in DIRECT_ANCHOR_NAMES:
        info = direct_plan["anchors"].get(anchor)
        if info is None:
            continue

        group = info["group"]

        if group is None:
            group = create_independent_group(
                root,
                root,
                info["technical_name"],
            )
            apply_source_metadata(
                group,
                info["source_meta"],
            )
            rename_group(
                group,
                anchor,
            )

            resolved = find_direct_child(root, anchor)
            if resolved is None or handle(resolved) != handle(group):
                raise ProbeError(
                    "Created direct anchor %r did not resolve uniquely after rename."
                    % anchor
                )

            result["created"].append(anchor)

        result["anchors"][anchor] = group

    # Only after all anchors resolve do we move the authorized controls.
    for anchor in DIRECT_ANCHOR_NAMES:
        rows = direct_plan["rows_by_anchor"].get(anchor, [])
        if not rows:
            continue

        group = result["anchors"][anchor]

        for row in rows:
            control_name = to_unicode(row["name"])
            control = live_controls.get(control_name)
            if control is None:
                raise ProbeError(
                    "Live direct-anchor candidate %r disappeared."
                    % control_name
                )
            add_control_to_group(group, control)

    return result


def validate_direct_anchor(
        post,
        after,
        rig_rows,
        direct_plan,
        direct_build):
    candidate_names = set([
        to_unicode(row["name"])
        for row in rig_rows
    ])

    failures = []

    # Candidate placement and accessibility.
    for row in rig_rows:
        control_name = to_unicode(row["name"])
        expected = to_unicode(row["relative_path"])
        actual = one_membership(after, control_name)
        meta = None if actual is None else after["groups"].get(actual)

        if (
            actual != expected
            or meta is None
            or not bool(meta["effective_visible"])
        ):
            failures.append(("candidate", control_name, expected, actual))

    # Final semantic membership of every noncandidate remains native POST.
    for control_name in post["control_names_in_animation_set_order"]:
        control_name = to_unicode(control_name)
        if control_name in candidate_names:
            continue
        before = list(post["memberships"].get(control_name, []))
        actual = list(after["memberships"].get(control_name, []))
        if before != actual:
            failures.append(("noncandidate", control_name, before, actual))

    # Existing-anchor preservation plus exact composed direct-control order.
    for anchor in DIRECT_ANCHOR_NAMES:
        info = direct_plan["anchors"].get(anchor)
        if info is None:
            continue

        # Retain the exact live anchor object resolved/created by the builder.
        # Object identity is part of the anchor-preservation validation.
        actual_group = direct_build["anchors"][anchor]
        actual_state = capture_direct_anchor_state(actual_group)

        after_meta = after["groups"].get(anchor)
        if after_meta is None:
            failures.append(("anchor_missing", anchor))
            continue

        if info["existing"]:
            before = info["before"]

            if actual_state["handle"] != before["handle"]:
                failures.append(("anchor_handle", anchor))

            if (
                actual_state["visible"] != before["visible"]
                or actual_state["selectable"] != before["selectable"]
                or actual_state["snappable"] != before["snappable"]
                or list(actual_state["group_color"]) != list(before["group_color"])
            ):
                failures.append(("anchor_metadata", anchor))

            # Child topology/order must be completely untouched by direct
            # AddControl placement.
            if actual_state["child_handles"] != before["child_handles"]:
                failures.append(("anchor_children", anchor))

            # Every old direct member remains, in its original relative order.
            old_handles = list(before["direct_handles"])
            projected_old = [
                h for h in actual_state["direct_handles"] if h in set(old_handles)
            ]
            if projected_old != old_handles:
                failures.append(("anchor_old_direct_order", anchor))

        else:
            source = info["source_meta"]
            if not (
                list(source["group_color"]) == list(after_meta["group_color"])
                and source["selectable"] == after_meta["selectable"]
                and source["snappable"] == after_meta["snappable"]
                and bool(after_meta["effective_visible"])
            ):
                failures.append(("created_anchor_metadata", anchor))

        # This direct-anchor path deliberately avoids an eager reorder mutation.
        # AddControl must naturally yield: prior direct members unchanged,
        # followed by the already policy-ordered candidates.
        if actual_state["direct_names"] != info["expected_direct_names"]:
            failures.append((
                "anchor_direct_order",
                anchor,
                info["expected_direct_names"],
                actual_state["direct_names"],
            ))

    ownership_unchanged = bool(
        after["owned_control_name_set"] == post["owned_control_name_set"]
    )
    hidden_unchanged = bool(
        after["hidden_groups"] == post["hidden_groups"]
    )
    duplicates_clean = bool(
        not after["duplicate_control_names"]
        and not after["duplicate_sibling_groups"]
        and not after["duplicate_direct_controls"]
        and not after["duplicate_memberships"]
    )
    animset_order_unchanged = bool(
        after["control_names_in_animation_set_order"]
        == post["control_names_in_animation_set_order"]
    )

    if not ownership_unchanged:
        failures.append(("ownership_changed",))
    if not hidden_unchanged:
        failures.append(("hiddenGroups_changed",))
    if not duplicates_clean:
        failures.append(("duplicates",))
    if not animset_order_unchanged:
        failures.append(("animation_set_control_order",))

    # No reconciliation wrapper should exist for this all-direct simple-anchor case.
    if after["groups"].get(to_unicode(RIG_RECON_ROOT)) is not None:
        failures.append(("rig_wrapper_visible",))
    if after["groups"].get(to_unicode(MASTER_RECON_ROOT)) is not None:
        failures.append(("master_wrapper_visible",))

    if failures:
        raise ProbeError(
            "Direct-anchor validation failed: %r"
            % failures[:20]
        )

    return {
        "candidate_count": len(rig_rows),
        "anchors": sorted(direct_plan["anchors"].keys()),
        "created": list(direct_build["created"]),
    }


def discover_rig_context(shot, aset):
    result = {
        "status": "UNRIGGED",
        "rig": None,
        "registry": None,
        "rig_handle": None,
        "registry_handle": None,
        "matching_rig_count": 0,
        "reachable_rig_count": 0,
        "owned_handles": set(),
        "owned_names_in_order": [],
        "hidden_groups": [],
    }

    scene = scalar(shot, "scene")

    if scene is None:
        try:
            scene = shot.scene
        except Exception:
            scene = None

    if scene is None:
        result["status"] = "RIG_CONTEXT_UNAVAILABLE"
        return result

    rigs = []
    matches = []

    try:
        objs = reachable(scene)
    except Exception:
        result["status"] = "RIG_TRAVERSAL_FAILED"
        return result

    for obj in objs:
        if typ(obj) != u"DmeRig":
            continue

        rigs.append(obj)

        try:
            if bool(obj.HasAnimationSet(aset)):
                matches.append(obj)
        except Exception:
            pass

    result["reachable_rig_count"] = len(rigs)
    result["matching_rig_count"] = len(matches)

    if not matches:
        result["status"] = "UNRIGGED"
        return result

    if len(matches) != 1:
        result["status"] = "AMBIGUOUS_MULTIPLE_RIGS"
        return result

    rig = matches[0]

    registry_matches = []

    for rec in arr(rig, "animSetList"):
        if typ(rec) != u"DmeRigAnimSetElements":
            continue

        linked = scalar(rec, "animationSet")

        try:
            same = bool(
                linked is not None
                and handle(linked) == handle(aset)
            )
        except Exception:
            same = False

        if same:
            registry_matches.append(rec)

    if len(registry_matches) != 1:
        result["status"] = "AMBIGUOUS_RIG_REGISTRY"
        result["rig"] = rig
        result["rig_handle"] = handle(rig)
        return result

    registry = registry_matches[0]

    control_objs = arr(aset, "controls")
    control_handles = set([
        handle(control)
        for control in control_objs
    ])

    registry_handles = set()

    for obj in arr(registry, "elementList"):
        try:
            registry_handles.add(handle(obj))
        except Exception:
            pass

    owned_handles = (
        control_handles
        .intersection(registry_handles)
    )

    if not owned_handles:
        result["status"] = "STALE_ZERO_OWNERSHIP_RIG"
        result["rig"] = rig
        result["registry"] = registry
        result["rig_handle"] = handle(rig)
        result["registry_handle"] = handle(registry)
        return result

    owned_names = []

    for control in control_objs:
        if handle(control) in owned_handles:
            owned_names.append(name(control))

    result.update({
        "status": "SUPPORTED_ACTIVE_RIG",
        "rig": rig,
        "registry": registry,
        "rig_handle": handle(rig),
        "registry_handle": handle(registry),
        "owned_handles": owned_handles,
        "owned_names_in_order": owned_names,
        "hidden_groups": [
            to_unicode(x)
            for x in arr(
                registry,
                "hiddenGroups"
            )
        ],
    })

    return result


def strip_reconciliation_wrapper(path):
    p = to_unicode(path)

    for wrapper in (
        to_unicode(RIG_RECON_ROOT),
        to_unicode(MASTER_RECON_ROOT),
    ):
        if p == wrapper:
            return u"<ROOT>"

        prefix = wrapper + u"/"

        if p.startswith(prefix):
            return p[len(prefix):]

    return p


def canonicalize_rig_source_snapshot(pre):
    # Build a semantic PRE view in which a prior __RIG_VISIBLE_RECON__
    # wrapper is treated as presentation scaffolding rather than as part
    # of the animator-facing hierarchy. This prevents wrapper nesting on
    # a later run.
    result = dict(pre)
    new_groups = {}
    wrapper_paths = []

    for raw_path in pre["groups"].keys():
        raw_path = to_unicode(raw_path)

        if (
            raw_path == to_unicode(RIG_RECON_ROOT)
            or raw_path.startswith(
                to_unicode(RIG_RECON_ROOT) + u"/"
            )
        ):
            wrapper_paths.append(raw_path)

    # Wrapper-derived presentation wins when present.
    for raw_path in sorted(
            wrapper_paths,
            key=lambda p: (
                p.count(u"/"),
                p,
            )):
        meta = dict(
            pre["groups"][raw_path]
        )

        canonical = strip_reconciliation_wrapper(
            raw_path
        )

        parent = meta.get(
            "parent_path"
        )

        if parent is not None:
            parent = strip_reconciliation_wrapper(
                parent
            )

        meta["path"] = canonical
        meta["parent_path"] = parent

        if canonical == u"<ROOT>":
            meta["name"] = u"<ROOT>"
        else:
            meta["name"] = canonical.split(u"/")[-1]

        new_groups[canonical] = meta

    for raw_path, raw_meta in pre["groups"].items():
        raw_path = to_unicode(raw_path)

        if (
            raw_path == to_unicode(RIG_RECON_ROOT)
            or raw_path.startswith(
                to_unicode(RIG_RECON_ROOT) + u"/"
            )
        ):
            continue

        if raw_path in new_groups:
            continue

        new_groups[raw_path] = dict(raw_meta)

    new_memberships = {}

    for control_name, paths in pre["memberships"].items():
        new_memberships[
            to_unicode(control_name)
        ] = [
            strip_reconciliation_wrapper(path)
            for path in paths
        ]

    result["groups"] = new_groups
    result["memberships"] = new_memberships
    result["group_count"] = len(new_groups)

    return result


def capture_snapshot_explicit(
    shot,
    aset,
    label,
    rig_context=None,
):
    if rig_context is None:
        rig_context = discover_rig_context(
            shot,
            aset,
        )

    try:
        root = aset.GetRootControlGroup()
    except Exception:
        root = scalar(
            aset,
            "rootControlGroup"
        )

    if root is None:
        raise ProbeError(
            "Animation set has no root control group."
        )

    control_objs = arr(
        aset,
        "controls"
    )
    control_names = [
        name(control)
        for control in control_objs
    ]

    exact_counts = {}

    for control_name in control_names:
        exact_counts[control_name] = (
            exact_counts.get(
                control_name,
                0
            )
            + 1
        )

    duplicate_control_names = dict([
        (
            control_name,
            count,
        )
        for control_name, count
        in exact_counts.items()
        if count > 1
    ])

    controls_by_name = {}

    if not duplicate_control_names:
        controls_by_name = dict([
            (
                name(control),
                control,
            )
            for control in control_objs
        ])

    control_handles = {}

    control_types = {}

    if not duplicate_control_names:
        control_handles = dict([
            (
                control_name,
                handle(control),
            )
            for control_name, control
            in controls_by_name.items()
        ])

        control_types = dict([
            (
                control_name,
                typ(control),
            )
            for control_name, control
            in controls_by_name.items()
        ])

    tree = capture_tree(root)

    owned_names = []

    if (
        rig_context["status"]
        == "SUPPORTED_ACTIVE_RIG"
    ):
        owned_handles = rig_context[
            "owned_handles"
        ]

        for control in control_objs:
            if handle(control) in owned_handles:
                owned_names.append(
                    name(control)
                )

    return {
        "label": label,
        "shot_name": name(shot),
        "shot_handle": handle(shot),
        "animation_set_name": name(aset),
        "animation_set_handle": handle(aset),
        "root_handle": handle(root),
        "rig_status": rig_context[
            "status"
        ],
        "rig_name": (
            None
            if rig_context["rig"] is None
            else name(
                rig_context["rig"]
            )
        ),
        "rig_handle": rig_context[
            "rig_handle"
        ],
        "registry_handle": rig_context[
            "registry_handle"
        ],
        "matching_rig_count": rig_context[
            "matching_rig_count"
        ],
        "reachable_rig_count": rig_context[
            "reachable_rig_count"
        ],
        "control_count": len(
            control_names
        ),
        "control_names_in_animation_set_order": control_names,
        "duplicate_control_names": duplicate_control_names,
        "control_handles": control_handles,
        "control_types": control_types,
        "owned_control_names_in_animation_set_order": owned_names,
        "owned_control_name_set": sorted(
            owned_names
        ),
        "hidden_groups": list(
            rig_context[
                "hidden_groups"
            ]
        ),
        "group_count": tree[
            "group_count"
        ],
        "groups": tree[
            "groups"
        ],
        "memberships": tree[
            "memberships"
        ],
        "duplicate_sibling_groups": tree[
            "duplicate_sibling_groups"
        ],
        "duplicate_direct_controls": tree[
            "duplicate_direct_controls"
        ],
        "duplicate_memberships": tree[
            "duplicate_memberships"
        ],
        "rig_recon_exists": bool(
            RIG_RECON_ROOT
            in tree[
                "groups"
            ]
        ),
        "master_recon_exists": bool(
            MASTER_RECON_ROOT
            in tree[
                "groups"
            ]
        ),
    }


def classify_production(
    pre,
    post,
    master,
):
    pre_source = (
        canonicalize_rig_source_snapshot(
            pre
        )
    )

    owned = set([
        to_unicode(x)
        for x in pre[
            "owned_control_name_set"
        ]
    ])

    hidden = set([
        to_unicode(x)
        for x in pre[
            "hidden_groups"
        ]
    ])

    if (
        pre["duplicate_control_names"]
        or post["duplicate_control_names"]
    ):
        raise ProbeError(
            "Exact duplicate control names make contextual "
            "classification ambiguous."
        )

    ordered_controls = sorted(
        [
            (
                int(
                    post[
                        "control_handles"
                    ][
                        control_name
                    ]
                ),
                to_unicode(
                    control_name
                ),
            )
            for control_name
            in post[
                "control_names_in_animation_set_order"
            ]
        ],
        key=lambda row: row[0],
    )

    losses = []
    pre_hidden_master_active = []
    parent_collapses = []
    master_normalizations = []
    unknown_potentials = []
    unresolved_owned_drift = []

    for unused_handle, control_name in ordered_controls:
        pre_path = one_membership(
            pre_source,
            control_name,
        )
        post_path = one_membership(
            post,
            control_name,
        )

        if (
            pre_path is None
            or post_path is None
        ):
            continue

        pre_group = pre_source[
            "groups"
        ].get(
            pre_path
        )
        post_group = post[
            "groups"
        ].get(
            post_path
        )

        if (
            pre_group is None
            or post_group is None
        ):
            continue

        control_type = to_unicode(
            post[
                "control_types"
            ][
                control_name
            ]
        )

        is_owned = bool(
            control_name in owned
        )

        ml = master_lookup(
            master,
            control_name,
        )

        row = {
            "handle": int(
                post[
                    "control_handles"
                ][
                    control_name
                ]
            ),
            "name": control_name,
            "type": control_type,
            "owned": is_owned,
            "pre_path": pre_path,
            "post_path": post_path,
            "post_visible": bool(
                post_group[
                    "effective_visible"
                ]
            ),
            "master_known": bool(
                ml["known"]
            ),
            "master_destination": ml[
                "destination"
            ],
            "master_global_index": ml[
                "global_index"
            ],
            "master_local_index": ml[
                "local_index"
            ],
            "post_matches_master": bool(
                ml["known"]
                and post_path
                == to_unicode(
                    ml[
                        "destination"
                    ]
                )
            ),
            "post_under_hidden_group": bool(
                first_path_part(
                    post_path
                )
                in hidden
            ),
        }

        # Production: fresh-PRE hidden active-rig completion.  This is deliberately
        # stricter than ordinary rig-loss classification.  A hidden rig-owned
        # transform is eligible only when current Master explicitly names an
        # active RigBody/RigArms/RigLegs destination, that active root is
        # already effectively visible in fresh PRE, and at least two other
        # visible rig-owned transforms independently resolve to the exact same
        # Master destination.  If native POST already reaches that visible
        # authoritative destination, no contextual repair is needed.
        if not bool(
                pre_group[
                    "effective_visible"
                ]
                ):
            master_destination = (
                to_unicode(
                    ml["destination"]
                )
                if ml["known"]
                else None
            )

            active_root = None

            if master_destination is not None:
                for candidate_root in (
                        u"RigBody",
                        u"RigArms",
                        u"RigLegs"):
                    if (
                        master_destination
                        == candidate_root
                        or master_destination.startswith(
                            candidate_root + u"/"
                        )
                    ):
                        active_root = candidate_root
                        break

            active_root_meta = (
                pre_source["groups"].get(
                    active_root
                )
                if active_root is not None
                else None
            )

            corroborating_peers = []

            if (
                is_owned
                and control_type
                == u"DmeTransformControl"
                and ml["known"]
                and ml["mode"] == "EXACT"
                and active_root is not None
                and active_root_meta is not None
                and bool(
                    active_root_meta[
                        "effective_visible"
                    ]
                )
            ):
                for peer_name in pre[
                        "owned_control_names_in_animation_set_order"]:
                    peer_name = to_unicode(
                        peer_name
                    )

                    if peer_name == control_name:
                        continue

                    if to_unicode(
                            post[
                                "control_types"
                            ].get(
                                peer_name,
                                u"",
                            )
                            ) != u"DmeTransformControl":
                        continue

                    peer_path = one_membership(
                        pre_source,
                        peer_name,
                    )

                    if peer_path is None:
                        continue

                    peer_group = pre_source[
                        "groups"
                    ].get(
                        peer_path
                    )

                    if (
                        peer_group is None
                        or not bool(
                            peer_group[
                                "effective_visible"
                            ]
                        )
                    ):
                        continue

                    peer_lookup = master_lookup(
                        master,
                        peer_name,
                    )

                    if (
                        peer_lookup["known"]
                        and to_unicode(
                            peer_lookup[
                                "destination"
                            ]
                        )
                        == master_destination
                    ):
                        corroborating_peers.append(
                            peer_name
                        )

            if (
                len(corroborating_peers) >= 2
                and not (
                    row["post_matches_master"]
                    and row["post_visible"]
                )
            ):
                row[
                    "category"
                ] = "RIG_OWNED_PRE_HIDDEN_MASTER_ACTIVE"
                row[
                    "active_root"
                ] = active_root
                row[
                    "corroborating_visible_same_destination_peers"
                ] = list(
                    corroborating_peers
                )
                pre_hidden_master_active.append(
                    row
                )

            continue

        if not row["post_visible"]:
            if (
                is_owned
                and control_type
                == u"DmeTransformControl"
            ):
                row[
                    "category"
                ] = "RIG_OWNED_EFFECTIVE_CONTROL"
            elif (
                (not is_owned)
                and control_type
                == u"DmeTransformControl"
                and row[
                    "master_known"
                ]
                and row[
                    "post_matches_master"
                ]
                and row[
                    "post_under_hidden_group"
                ]
            ):
                row[
                    "category"
                ] = "MASTER_KNOWN_BUT_STRANDED"
            else:
                row[
                    "category"
                ] = "AMBIGUOUS_DIAGNOSTIC_ONLY"

            losses.append(row)
            continue

        if (
            not is_owned
            or pre_path == post_path
        ):
            continue

        if (
            control_type
            == u"DmeTransformControl"
            and immediate_parent_path(
                pre_path
            )
            == post_path
        ):
            row[
                "category"
            ] = "RIG_OWNED_VISIBLE_PARENT_COLLAPSE"
            parent_collapses.append(
                row
            )
            continue

        if (
            row[
                "master_known"
            ]
            and row[
                "post_matches_master"
            ]
        ):
            row[
                "category"
            ] = "RIG_OWNED_VISIBLE_MASTER_NORMALIZATION"
            master_normalizations.append(
                row
            )
            continue

        if (
            not row[
                "master_known"
            ]
            and control_type
            == u"DmeTransformControl"
            and post_path
            == u"Unknown"
            and pre_path
            not in (
                u"<ROOT>",
                u"Unknown",
            )
        ):
            row[
                "category"
            ] = "MASTER_UNKNOWN_RESIDUAL_CANDIDATE"
            unknown_potentials.append(
                row
            )
            continue

        row[
            "category"
        ] = "AMBIGUOUS_DIAGNOSTIC_ONLY"
        unresolved_owned_drift.append(
            row
        )

    # Narrow the Master-unknown class. The entire exact PRE leaf must be
    # a coherent residual cohort after Master authority is applied.
    potential_by_path = {}

    for row in unknown_potentials:
        potential_by_path.setdefault(
            row[
                "pre_path"
            ],
            [],
        ).append(row)

    master_unknown_unknown = []
    weak_unknown_diagnostics = []

    for pre_path, rows in potential_by_path.items():
        group_meta = pre_source[
            "groups"
        ].get(
            pre_path
        )

        direct_names = []

        child_names = []

        if group_meta is not None:
            direct_names = [
                to_unicode(x)
                for x in group_meta[
                    "direct_control_names_in_order"
                ]
            ]
            child_names = [
                to_unicode(x)
                for x in group_meta[
                    "child_names_in_order"
                ]
            ]

        owned_visible_transform_peers = []

        for peer_name in direct_names:
            if peer_name not in owned:
                continue

            peer_type = post[
                "control_types"
            ].get(
                peer_name
            )

            if (
                to_unicode(
                    peer_type
                )
                != u"DmeTransformControl"
            ):
                continue

            owned_visible_transform_peers.append(
                peer_name
            )

        candidate_names = set([
            to_unicode(
                row[
                    "name"
                ]
            )
            for row in rows
        ])

        peer_names = set(
            owned_visible_transform_peers
        )

        strong = bool(
            group_meta is not None
            and bool(
                group_meta[
                    "effective_visible"
                ]
            )
            and len(rows) >= 2
            and not child_names
            and candidate_names
            == peer_names
        )

        # Every peer must independently remain Master-unknown and land
        # in native POST Unknown. This rejects mixed/weak
        # miscellaneous groups where Master-known peers normalize away.
        if strong:
            for peer_name in owned_visible_transform_peers:
                ml = master_lookup(
                    master,
                    peer_name,
                )
                peer_post = one_membership(
                    post,
                    peer_name,
                )

                if (
                    ml[
                        "known"
                    ]
                    or peer_post
                    != u"Unknown"
                ):
                    strong = False
                    break

        for row in rows:
            row[
                "residual_cohort_size"
            ] = len(rows)
            row[
                "residual_peer_count"
            ] = len(
                owned_visible_transform_peers
            )
            row[
                "residual_strong"
            ] = strong

            if strong:
                row[
                    "category"
                ] = (
                    "RIG_OWNED_MASTER_UNKNOWN_VISIBLE_UNKNOWN_DRIFT"
                )
                master_unknown_unknown.append(
                    row
                )
            else:
                row[
                    "category"
                ] = "AMBIGUOUS_DIAGNOSTIC_ONLY"
                row[
                    "diagnostic_reason"
                ] = (
                    "weak/singleton/mixed Master-unknown residual cohort"
                )
                weak_unknown_diagnostics.append(
                    row
                )

    rig_losses = [
        row
        for row in losses
        if row[
            "category"
        ]
        == "RIG_OWNED_EFFECTIVE_CONTROL"
    ]

    master_stranded = [
        row
        for row in losses
        if row[
            "category"
        ]
        == "MASTER_KNOWN_BUT_STRANDED"
    ]

    ambiguous_losses = [
        row
        for row in losses
        if row[
            "category"
        ]
        == "AMBIGUOUS_DIAGNOSTIC_ONLY"
    ]

    unresolved_owned_drift.extend(
        weak_unknown_diagnostics
    )

    return {
        "pre_source": pre_source,
        "pre_hidden_master_active": pre_hidden_master_active,
        "rig_losses": rig_losses,
        "master_stranded": master_stranded,
        "ambiguous_losses": ambiguous_losses,
        "parent_collapses": parent_collapses,
        "master_normalizations": master_normalizations,
        "master_unknown_unknown": master_unknown_unknown,
        "weak_unknown_diagnostics": weak_unknown_diagnostics,
        "unresolved_owned_drift": unresolved_owned_drift,
    }

def policy_ordering_comparison_for_wrapper(
    source,
    after,
    candidate_rows,
    master,
    wrapper_name,
):
    tree = target_tree_from_rows(
        candidate_rows
    )

    by_path = {}

    for row in candidate_rows:
        path = to_unicode(
            row[
                "relative_path"
            ]
        )
        by_path.setdefault(
            path,
            [],
        ).append(
            to_unicode(
                row[
                    "name"
                ]
            )
        )

    direct_rows = []
    direct_failures = []

    for source_path in sorted(
            by_path.keys()):
        authority, expected = policy_direct_order(
            master,
            source,
            source_path,
            by_path[
                source_path
            ],
        )

        final_path = (
            to_unicode(
                wrapper_name
            )
            + u"/"
            + source_path
        )

        meta = after[
            "groups"
        ].get(
            final_path
        )

        actual = (
            None
            if meta is None
            else [
                to_unicode(x)
                for x in meta[
                    "direct_control_names_in_order"
                ]
            ]
        )

        passed = bool(
            actual == expected
        )

        row = {
            "source_path": source_path,
            "authority": authority,
            "expected": expected,
            "actual": actual,
            "pass": passed,
        }

        direct_rows.append(
            row
        )

        if not passed:
            direct_failures.append(
                row
            )

    child_rows = []
    child_failures = []

    for parent_path in sorted(
            tree.keys()):
        child_paths = tree[
            parent_path
        ]

        if not child_paths:
            continue

        child_names = [
            source_child_name(
                parent_path,
                child_path,
            )
            for child_path
            in child_paths
        ]

        authority, expected = policy_child_order(
            master,
            source,
            parent_path,
            child_names,
        )

        final_parent = (
            to_unicode(
                wrapper_name
            )
            if parent_path
            == u"<ROOT>"
            else to_unicode(
                wrapper_name
            )
            + u"/"
            + parent_path
        )

        meta = after[
            "groups"
        ].get(
            final_parent
        )

        actual = (
            None
            if meta is None
            else [
                to_unicode(x)
                for x in meta[
                    "child_names_in_order"
                ]
            ]
        )

        passed = bool(
            actual == expected
        )

        row = {
            "source_parent": parent_path,
            "authority": authority,
            "expected": expected,
            "actual": actual,
            "pass": passed,
        }

        child_rows.append(
            row
        )

        if not passed:
            child_failures.append(
                row
            )

    animation_set_order_pass = bool(
        [
            to_unicode(x)
            for x in source[
                "control_names_in_animation_set_order"
            ]
        ]
        ==
        [
            to_unicode(x)
            for x in after[
                "control_names_in_animation_set_order"
            ]
        ]
    )

    # The source snapshot for MASTER rows may not have active-rig
    # ownership semantics. Only require owned-order equality when both
    # snapshots expose a list.
    owned_source = source.get(
        "owned_control_names_in_animation_set_order",
        [],
    )
    owned_after = after.get(
        "owned_control_names_in_animation_set_order",
        [],
    )

    owned_order_pass = bool(
        [
            to_unicode(x)
            for x in owned_source
        ]
        ==
        [
            to_unicode(x)
            for x in owned_after
        ]
    )

    return {
        "animation_set_order_pass": animation_set_order_pass,
        "owned_order_pass": owned_order_pass,
        "direct_rows": direct_rows,
        "direct_failures": direct_failures,
        "child_rows": child_rows,
        "child_failures": child_failures,
        "pass": bool(
            animation_set_order_pass
            and owned_order_pass
            and not direct_failures
            and not child_failures
        ),
    }


def isolation_fingerprint(aset):
    try:
        root = aset.GetRootControlGroup()
    except Exception:
        root = None

    controls = []

    for control in arr(
            aset,
            "controls"):
        controls.append(
            (
                handle(control),
                name(control),
                typ(control),
            )
        )

    groups = []

    if root is not None:
        stack = [
            (
                root,
                None,
            )
        ]
        seen = set()

        while stack:
            group, parent_handle = stack.pop()

            gh = handle(group)

            if gh in seen:
                continue

            seen.add(gh)

            child_objs = children(group)

            groups.append(
                (
                    gh,
                    name(group),
                    parent_handle,
                    is_visible(group),
                    is_selectable(group),
                    is_snappable(group),
                    tuple(
                        group_color_rgba(
                            group
                        )
                    ),
                    tuple([
                        handle(child)
                        for child in child_objs
                    ]),
                    tuple([
                        handle(control)
                        for control
                        in direct_controls(
                            group
                        )
                    ]),
                )
            )

            for child in reversed(
                    child_objs):
                stack.append(
                    (
                        child,
                        gh,
                    )
                )

    groups.sort(
        key=lambda row: row[0]
    )

    return (
        handle(aset),
        (
            None
            if root is None
            else handle(root)
        ),
        tuple(controls),
        tuple(groups),
    )


CONTEXTUALIZER_IFP_SCHEMA_PREFIX = "SFM_IFP_SHA256_V1\x00"
CONTEXTUALIZER_IFP_U64_MAX = (1 << 64) - 1
CONTEXTUALIZER_IFP_U32_MAX = (1 << 32) - 1


class FingerprintDigestEncoder(object):
    """
    Typed production isolation-fingerprint SHA-256 encoder.

    Input remains the existing expanded isolation_fingerprint tuple. This
    class changes only retained representation, not fingerprint semantics.
    """

    def __init__(self):
        self.h = hashlib.sha256()
        self.h.update(
            CONTEXTUALIZER_IFP_SCHEMA_PREFIX
        )


    def emit_tag(
            self,
            tag):
        if (
            not isinstance(
                tag,
                str,
            )
            or len(
                tag
            ) != 1
        ):
            raise ProbeError(
                "Invalid one-byte isolation digest tag: %r."
                % (
                    tag,
                )
            )

        self.h.update(
            tag
        )


    def emit_u8(
            self,
            value):
        if (
            not isinstance(
                value,
                (int, long),
            )
            or isinstance(
                value,
                bool,
            )
            or value < 0
            or value > 255
        ):
            raise ProbeError(
                "Isolation digest u8 out of range: %r."
                % (
                    value,
                )
            )

        self.h.update(
            struct.pack(
                "<B",
                int(
                    value
                ),
            )
        )


    def emit_u32(
            self,
            value):
        if (
            not isinstance(
                value,
                (int, long),
            )
            or isinstance(
                value,
                bool,
            )
            or value < 0
            or value > CONTEXTUALIZER_IFP_U32_MAX
        ):
            raise ProbeError(
                "Isolation digest u32 out of range: %r."
                % (
                    value,
                )
            )

        self.h.update(
            struct.pack(
                "<I",
                int(
                    value
                ),
            )
        )


    def emit_handle(
            self,
            value):
        if (
            not isinstance(
                value,
                (int, long),
            )
            or isinstance(
                value,
                bool,
            )
            or value < 0
            or value > CONTEXTUALIZER_IFP_U64_MAX
        ):
            raise ProbeError(
                "DME handle outside production isolation unsigned-64 schema: %r."
                % (
                    value,
                )
            )

        self.h.update(
            struct.pack(
                "<Q",
                long(
                    value
                ),
            )
        )


    def emit_optional_handle(
            self,
            value):
        if value is None:
            self.emit_tag(
                "0"
            )
            return

        self.emit_tag(
            "1"
        )
        self.emit_handle(
            value
        )


    def emit_unicode(
            self,
            value):
        if not isinstance(
                value,
                unicode):
            raise ProbeError(
                "Isolation digest expected unicode, got %r."
                % (
                    type(
                        value
                    ),
                )
            )

        try:
            encoded = value.encode(
                "utf-8",
                "strict",
            )
        except Exception as exc:
            raise ProbeError(
                "Isolation digest strict UTF-8 encoding failed: %r."
                % (
                    exc,
                )
            )

        self.emit_u32(
            len(
                encoded
            )
        )
        self.h.update(
            encoded
        )


    def emit_tristate(
            self,
            value):
        if value is None:
            self.emit_tag(
                "N"
            )
        elif value is False:
            self.emit_tag(
                "F"
            )
        elif value is True:
            self.emit_tag(
                "T"
            )
        else:
            raise ProbeError(
                "Isolation digest expected True/False/None, got %r."
                % (
                    value,
                )
            )


    def encode(
            self,
            fp):
        if (
            not isinstance(
                fp,
                tuple,
            )
            or len(
                fp
            ) != 4
        ):
            raise ProbeError(
                "Isolation fingerprint root must be a 4-tuple."
            )

        (
            aset_handle,
            root_handle,
            controls,
            groups,
        ) = fp

        self.emit_tag(
            "A"
        )
        self.emit_handle(
            aset_handle
        )

        self.emit_tag(
            "R"
        )
        self.emit_optional_handle(
            root_handle
        )

        if not isinstance(
                controls,
                tuple):
            raise ProbeError(
                "Isolation fingerprint controls must be a tuple."
            )

        self.emit_tag(
            "C"
        )
        self.emit_u32(
            len(
                controls
            )
        )

        for row in controls:
            if (
                not isinstance(
                    row,
                    tuple,
                )
                or len(
                    row
                ) != 3
            ):
                raise ProbeError(
                    "Isolation fingerprint control row must be a 3-tuple."
                )

            (
                control_handle,
                control_name,
                control_type,
            ) = row

            self.emit_tag(
                "c"
            )
            self.emit_handle(
                control_handle
            )

            self.emit_tag(
                "n"
            )
            self.emit_unicode(
                control_name
            )

            self.emit_tag(
                "t"
            )
            self.emit_unicode(
                control_type
            )

        if not isinstance(
                groups,
                tuple):
            raise ProbeError(
                "Isolation fingerprint groups must be a tuple."
            )

        self.emit_tag(
            "G"
        )
        self.emit_u32(
            len(
                groups
            )
        )

        for row in groups:
            if (
                not isinstance(
                    row,
                    tuple,
                )
                or len(
                    row
                ) != 9
            ):
                raise ProbeError(
                    "Isolation fingerprint group row must be a 9-tuple."
                )

            (
                group_handle,
                group_name,
                parent_handle,
                visible,
                selectable,
                snappable,
                rgba,
                child_handles,
                direct_handles,
            ) = row

            self.emit_tag(
                "g"
            )
            self.emit_handle(
                group_handle
            )

            self.emit_tag(
                "n"
            )
            self.emit_unicode(
                group_name
            )

            self.emit_tag(
                "p"
            )
            self.emit_optional_handle(
                parent_handle
            )

            self.emit_tag(
                "v"
            )
            if visible is True:
                self.emit_tag(
                    "T"
                )
            elif visible is False:
                self.emit_tag(
                    "F"
                )
            else:
                raise ProbeError(
                    "Isolation fingerprint visibility must be bool."
                )

            self.emit_tag(
                "s"
            )
            self.emit_tristate(
                selectable
            )

            self.emit_tag(
                "q"
            )
            self.emit_tristate(
                snappable
            )

            if (
                not isinstance(
                    rgba,
                    tuple,
                )
                or len(
                    rgba
                ) != 4
            ):
                raise ProbeError(
                    "Isolation fingerprint RGBA must be a 4-tuple."
                )

            self.emit_tag(
                "a"
            )

            for component in rgba:
                self.emit_u8(
                    component
                )

            if not isinstance(
                    child_handles,
                    tuple):
                raise ProbeError(
                    "Isolation child handles must be a tuple."
                )

            self.emit_tag(
                "h"
            )
            self.emit_u32(
                len(
                    child_handles
                )
            )

            for child_handle in child_handles:
                self.emit_handle(
                    child_handle
                )

            if not isinstance(
                    direct_handles,
                    tuple):
                raise ProbeError(
                    "Isolation direct-control handles must be a tuple."
                )

            self.emit_tag(
                "d"
            )
            self.emit_u32(
                len(
                    direct_handles
                )
            )

            for direct_handle in direct_handles:
                self.emit_handle(
                    direct_handle
                )

        self.emit_tag(
            "Z"
        )

        digest = self.h.digest()

        if len(
                digest) != 32:
            raise ProbeError(
                "Isolation SHA-256 digest length is not 32 bytes."
            )

        return digest


def isolation_fingerprint_digest(fp):
    return FingerprintDigestEncoder().encode(
        fp
    )


def capture_session_fingerprint_digests():
    """
    Build the compact retained baseline one animation set at a time.

    The expanded fingerprint exists only as a local transient for the current
    animation set. The retained value is exactly one 32-byte production isolation digest.
    """
    result = {}

    shape = {
        "fingerprints": 0,
        "controls": 0,
        "groups": 0,
        "child_refs": 0,
        "direct_refs": 0,
    }

    for shot in list(
            sfmApp.GetShots()):
        shot_handle = native_ptr(
            shot
        )

        for aset in shot.animationSets:
            key = (
                shot_handle,
                native_ptr(
                    aset
                ),
            )

            fp = isolation_fingerprint(
                aset
            )

            shape[
                "fingerprints"
            ] += 1
            shape[
                "controls"
            ] += len(
                fp[2]
            )
            shape[
                "groups"
            ] += len(
                fp[3]
            )

            for group_row in fp[3]:
                shape[
                    "child_refs"
                ] += len(
                    group_row[7]
                )
                shape[
                    "direct_refs"
                ] += len(
                    group_row[8]
                )

            result[
                key
            ] = isolation_fingerprint_digest(
                fp
            )

    return (
        result,
        shape,
    )



def capture_session_identity_census():
    """
    Compact whole-session identity/order census.

    This intentionally records only primitive DME identities:
      shot pointer + animation-set pointer order within each shot.

    It does NOT traverse control groups or controls.
    """
    rows = []

    for shot in list(
            sfmApp.GetShots()):
        rows.append(
            (
                native_ptr(
                    shot
                ),
                tuple([
                    native_ptr(
                        aset
                    )
                    for aset
                    in shot.animationSets
                ]),
            )
        )

    return tuple(rows)



def semantic_target_fingerprint(
        shot,
        aset):
    rig_context = discover_rig_context(
        shot,
        aset,
    )

    snapshot = capture_snapshot_explicit(
        shot,
        aset,
        "PRODUCTION_SEMANTIC_FINGERPRINT",
        rig_context,
    )

    group_rows = []

    for path in sorted(
            snapshot[
                "groups"
            ].keys()):
        meta = snapshot[
            "groups"
        ][path]

        group_rows.append((
            to_unicode(path),
            meta.get(
                "parent_path"
            ),
            bool(
                meta.get(
                    "visible"
                )
            ),
            bool(
                meta.get(
                    "effective_visible"
                )
            ),
            meta.get(
                "selectable"
            ),
            meta.get(
                "snappable"
            ),
            tuple(
                meta.get(
                    "group_color",
                    []
                )
            ),
            tuple([
                to_unicode(x)
                for x in meta.get(
                    "child_names_in_order",
                    []
                )
            ]),
            tuple([
                to_unicode(x)
                for x in meta.get(
                    "direct_control_names_in_order",
                    []
                )
            ]),
        ))

    memberships = tuple(sorted([
        (
            to_unicode(
                control_name
            ),
            tuple([
                to_unicode(path)
                for path in paths
            ]),
        )
        for control_name, paths
        in snapshot[
            "memberships"
        ].items()
    ]))

    control_types = tuple([
        (
            to_unicode(
                control_name
            ),
            to_unicode(
                snapshot[
                    "control_types"
                ].get(
                    control_name,
                    u""
                )
            ),
        )
        for control_name
        in snapshot[
            "control_names_in_animation_set_order"
        ]
    ])

    return (
        snapshot[
            "rig_status"
        ],
        snapshot[
            "rig_name"
        ],
        tuple(
            snapshot[
                "control_names_in_animation_set_order"
            ]
        ),
        control_types,
        tuple(
            snapshot[
                "owned_control_names_in_animation_set_order"
            ]
        ),
        tuple(
            snapshot[
                "owned_control_name_set"
            ]
        ),
        tuple(
            snapshot[
                "hidden_groups"
            ]
        ),
        tuple(
            group_rows
        ),
        memberships,
        tuple(
            snapshot[
                "duplicate_sibling_groups"
            ]
        ),
        tuple(
            snapshot[
                "duplicate_direct_controls"
            ]
        ),
        tuple(sorted([
            (
                to_unicode(k),
                tuple(v),
            )
            for k, v in snapshot[
                "duplicate_memberships"
            ].items()
        ])),
    )


def semantic_fingerprint_diff(
        first,
        second):
    labels = [
        "rig_status",
        "rig_name",
        "control_order",
        "control_types",
        "owned_order",
        "owned_set",
        "hidden_groups",
        "groups",
        "memberships",
        "duplicate_siblings",
        "duplicate_direct_controls",
        "duplicate_memberships",
    ]

    diffs = []

    for index, label in enumerate(
            labels):
        if first[index] != second[index]:
            diffs.append(
                label
            )

    return diffs


def raw_handle_diff_summary(
        first,
        second):
    first_controls = first[2]
    second_controls = second[2]
    first_groups = first[3]
    second_groups = second[3]

    first_group_handles = set([
        row[0]
        for row in first_groups
    ])
    second_group_handles = set([
        row[0]
        for row in second_groups
    ])

    first_control_handles = set([
        row[0]
        for row in first_controls
    ])
    second_control_handles = set([
        row[0]
        for row in second_controls
    ])

    return {
        "aset_handle_equal":
            first[0] == second[0],
        "root_handle_equal":
            first[1] == second[1],
        "control_rows_equal":
            first_controls == second_controls,
        "control_handle_sets_equal":
            first_control_handles
            == second_control_handles,
        "group_count_first":
            len(first_groups),
        "group_count_second":
            len(second_groups),
        "group_handle_overlap":
            len(
                first_group_handles.intersection(
                    second_group_handles
                )
            ),
        "group_handles_first_only":
            len(
                first_group_handles.difference(
                    second_group_handles
                )
            ),
        "group_handles_second_only":
            len(
                second_group_handles.difference(
                    first_group_handles
                )
            ),
    }

def read_undo_ledger(dm):
    count = None
    desc = None

    try:
        count = long(
            dm.GetUndoItemCount()
        )
    except Exception:
        count = None

    try:
        desc = dm.GetUndoDesc()
    except Exception:
        desc = None

    return (
        count,
        desc,
    )


def get_loaded_ifm_module():
    kernel32 = ctypes.windll.kernel32

    get_module_handle = (
        kernel32.GetModuleHandleW
    )
    get_module_handle.argtypes = [
        ctypes.c_wchar_p
    ]
    get_module_handle.restype = (
        ctypes.c_void_p
    )

    base = get_module_handle(
        u"ifm.dll"
    )

    if not base:
        raise ProbeError(
            "ifm.dll is not loaded."
        )

    return (
        kernel32,
        int(base),
    )


def get_loaded_module_path(
    kernel32,
    module_base,
):
    get_module_filename = (
        kernel32.GetModuleFileNameW
    )
    get_module_filename.argtypes = [
        ctypes.c_void_p,
        ctypes.c_wchar_p,
        ctypes.c_uint,
    ]
    get_module_filename.restype = (
        ctypes.c_uint
    )

    buffer_size = 32768

    buf = ctypes.create_unicode_buffer(
        buffer_size
    )

    count = get_module_filename(
        ctypes.c_void_p(
            module_base
        ),
        buf,
        buffer_size,
    )

    if count == 0:
        raise ProbeError(
            "GetModuleFileNameW failed for ifm.dll."
        )

    if count >= buffer_size:
        raise ProbeError(
            "Loaded ifm.dll path exceeded buffer."
        )

    return os.path.abspath(
        buf.value
    )


def _find_existing_run(main_window):
    try:
        objects = main_window.findChildren(
            QtCore.QObject
        )
    except Exception:
        return None

    for obj in objects:
        try:
            object_name = unicode(
                obj.objectName()
            )
        except Exception:
            continue

        if object_name == RUN_LOCK_NAME:
            return obj

    return None



def _canonicalize_context_path(path):
    if path is None:
        return None

    path = to_unicode(path)

    replacements = {
        u"RigArms/LeftArm/Left_Fingers":
            u"RigArms/LeftArm/LeftFingers",
        u"RigArms/RightArm/Right_Fingers":
            u"RigArms/RightArm/RightFingers",
        u"RigLegs/LeftLeg/Left_Toes":
            u"RigLegs/LeftLeg/LeftToes",
        u"RigLegs/RightLeg/Right_Toes":
            u"RigLegs/RightLeg/RightToes",
    }

    return replacements.get(
        path,
        path,
    )


def _active_rig_counterpart_destination(
        master_destination,
        source_path,
        has_rigarms,
        has_riglegs):
    if master_destination is None:
        return None

    destination = to_unicode(
        master_destination
    )
    source_path = _canonicalize_context_path(
        source_path
    )

    # Explicit active-rig Master destinations are already authoritative.
    if (
        destination == u"RigBody"
        or destination.startswith(u"RigBody/")
        or destination == u"RigArms"
        or destination.startswith(u"RigArms/")
        or destination == u"RigLegs"
        or destination.startswith(u"RigLegs/")
        or destination == u"RigHelpers"
        or destination.startswith(u"RigHelpers/")
    ):
        result = _canonicalize_context_path(
            destination
        )
    else:
        result = destination

        # Ordinary anatomical Master paths gain their active-rig presentation
        # counterpart only when fresh PRE proves that active rig family exists.
        if (
            source_path is not None
            and (
                source_path == u"RigBody"
                or source_path.startswith(u"RigBody/")
            )
            and (
                destination == u"Body"
                or destination.startswith(u"Body/")
            )
        ):
            result = u"RigBody"

        elif (
            has_rigarms
            and source_path is not None
            and (
                source_path == u"RigArms"
                or source_path.startswith(u"RigArms/")
            )
            and (
                destination == u"Arms"
                or destination.startswith(u"Arms/")
            )
        ):
            result = (
                u"RigArms"
                + destination[len(u"Arms"):]
            )

        elif (
            has_riglegs
            and source_path is not None
            and (
                source_path == u"RigLegs"
                or source_path.startswith(u"RigLegs/")
            )
            and (
                destination == u"Legs"
                or destination.startswith(u"Legs/")
            )
        ):
            result = (
                u"RigLegs"
                + destination[len(u"Legs"):]
            )

        elif (
            has_riglegs
            and source_path is not None
            and (
                source_path == u"RigLegs"
                or source_path.startswith(u"RigLegs/")
            )
            and destination == u"Toes/LeftToes"
        ):
            result = u"RigLegs/LeftLeg/LeftToes"

        elif (
            has_riglegs
            and source_path is not None
            and (
                source_path == u"RigLegs"
                or source_path.startswith(u"RigLegs/")
            )
            and destination == u"Toes/RightToes"
        ):
            result = u"RigLegs/RightLeg/RightToes"

    result = _canonicalize_context_path(
        result
    )

    # If current Master gives only a broad active-rig root while fresh PRE
    # supplies a coherent more-specific path inside that same family, preserve
    # the runtime specificity.  This is refinement, not reclassification.
    if source_path is not None:
        if (
            result == u"RigArms"
            and source_path.startswith(u"RigArms/")
        ):
            result = source_path

        elif (
            result == u"RigLegs"
            and source_path.startswith(u"RigLegs/")
        ):
            result = source_path

        elif (
            result == u"RigBody"
            and source_path.startswith(u"RigBody/")
        ):
            result = source_path

    return result


def derive_generic_uniformity_plan(
        pre,
        post,
        master,
        plan):
    rig_source = plan["rig_source"]
    rig_rows = plan["rig_rows"]
    classified = plan["classified"]

    source_paths = set([
        to_unicode(path)
        for path in rig_source["groups"].keys()
    ])

    has_rigarms = any([
        path == u"RigArms"
        or path.startswith(u"RigArms/")
        for path in source_paths
    ])

    has_riglegs = any([
        path == u"RigLegs"
        or path.startswith(u"RigLegs/")
        for path in source_paths
    ])

    model_leaf_specs = []

    if has_rigarms:
        model_leaf_specs.extend([
            (
                u"Arms/LeftArm/LeftFingers",
                u"RigArms/LeftArm/LeftFingers",
            ),
            (
                u"Arms/LeftArm/LeftCarpals",
                u"RigArms/LeftArm/LeftCarpals",
            ),
            (
                u"Arms/RightArm/RightFingers",
                u"RigArms/RightArm/RightFingers",
            ),
            (
                u"Arms/RightArm/RightCarpals",
                u"RigArms/RightArm/RightCarpals",
            ),
        ])

    if has_riglegs:
        model_leaf_specs.extend([
            (
                u"Toes/LeftToes",
                u"RigLegs/LeftLeg/LeftToes",
            ),
            (
                u"Toes/RightToes",
                u"RigLegs/RightLeg/RightToes",
            ),
        ])

    model_translations = {}
    model_candidate_names = set()

    for source_path, target_path in model_leaf_specs:
        source_meta = post["groups"].get(
            source_path
        )

        if source_meta is None:
            continue

        names = []

        for control_name in source_meta[
                "direct_control_names_in_order"]:
            control_name = to_unicode(
                control_name
            )

            if control_name in post[
                    "owned_control_name_set"]:
                continue

            if to_unicode(
                    post["control_types"].get(
                        control_name,
                        u"",
                    )
                    ) != u"DmeTransformControl":
                continue

            names.append(
                control_name
            )
            model_candidate_names.add(
                control_name
            )

        if names:
            model_translations[
                target_path
            ] = names

    toe_source_controls = {
        "Left": [],
        "Right": [],
    }

    for side, source_path in (
            ("Left", u"Toes/LeftToes"),
            ("Right", u"Toes/RightToes")):
        source_meta = post["groups"].get(
            source_path
        )

        if source_meta is not None:
            toe_source_controls[side] = [
                to_unicode(control_name)
                for control_name in source_meta[
                    "direct_control_names_in_order"
                ]
            ]

    rig_destinations = {}
    rig_destination_sources = {}
    rig_toe_promotions = {}
    rig_candidate_names = set()
    underspecified = []
    pre_hidden_master_active_names = set([
        to_unicode(row["name"])
        for row in classified[
            "pre_hidden_master_active"
        ]
    ])

    for row in rig_rows:
        control_name = to_unicode(
            row["name"]
        )
        rig_candidate_names.add(
            control_name
        )

        source_path = _canonicalize_context_path(
            row.get("relative_path")
        )

        if source_path is None:
            raise ProbeError(
                "Generic planner received rig row without relative_path: %r."
                % control_name
            )

        lookup = master_lookup(
            master,
            control_name,
        )

        if lookup["known"]:
            target_path = _active_rig_counterpart_destination(
                lookup["destination"],
                source_path,
                has_rigarms,
                has_riglegs,
            )
            authority = u"MASTER_PLUS_ACTIVE_RIG_COUNTERPART"

            if control_name in pre_hidden_master_active_names:
                authority = (
                    u"PRE_HIDDEN_MASTER_ACTIVE"
                    u"+MASTER_DESTINATION"
                    u"+VISIBLE_SAME_DESTINATION_PEERS"
                )

            # Fresh PRE may present a rig-owned control directly at <ROOT>.
            # If current Master places that control in an ordinary anatomical
            # family that native POST hides while the corresponding supported
            # active-rig family exists, use the visible active-rig counterpart.
            if source_path == u"<ROOT>":
                master_destination = to_unicode(
                    lookup["destination"]
                )

                arms_meta = post["groups"].get(
                    u"Arms"
                )
                legs_meta = post["groups"].get(
                    u"Legs"
                )
                body_meta = post["groups"].get(
                    u"Body"
                )

                if (
                    has_rigarms
                    and master_destination.startswith(
                        u"Arms/"
                    )
                    and arms_meta is not None
                    and not bool(
                        arms_meta[
                            "effective_visible"
                        ]
                    )
                ):
                    target_path = (
                        u"RigArms"
                        + master_destination[
                            len(u"Arms"):
                        ]
                    )
                    authority = (
                        u"MASTER_PLUS_ACTIVE_RIG_COUNTERPART"
                        u"+ROOT_DIRECT_HIDDEN_ARMS"
                    )

                elif (
                    has_riglegs
                    and master_destination.startswith(
                        u"Legs/"
                    )
                    and legs_meta is not None
                    and not bool(
                        legs_meta[
                            "effective_visible"
                        ]
                    )
                ):
                    target_path = (
                        u"RigLegs"
                        + master_destination[
                            len(u"Legs"):
                        ]
                    )
                    authority = (
                        u"MASTER_PLUS_ACTIVE_RIG_COUNTERPART"
                        u"+ROOT_DIRECT_HIDDEN_LEGS"
                    )

                elif (
                    master_destination == u"Body"
                    and body_meta is not None
                    and not bool(
                        body_meta[
                            "effective_visible"
                        ]
                    )
                    and any([
                        path == u"RigBody"
                        or path.startswith(u"RigBody/")
                        for path in source_paths
                    ])
                ):
                    target_path = u"RigBody"
                    authority = (
                        u"MASTER_PLUS_ACTIVE_RIG_COUNTERPART"
                        u"+ROOT_DIRECT_HIDDEN_BODY"
                    )
        else:
            # Only classifier-authorized Master-unknown rig rows reach this
            # list. Their fresh PRE semantic path remains the authority.
            target_path = source_path
            authority = u"FRESH_PRE_MASTER_UNKNOWN"

        if target_path is None:
            raise ProbeError(
                "Generic planner could not resolve target for %r."
                % control_name
            )

        # Runtime Toe-constraint evidence may refine a side-leg destination
        # into the nested active Toe presentation.
        side = None

        if target_path == u"RigLegs/LeftLeg":
            side = "Left"

        elif target_path == u"RigLegs/RightLeg":
            side = "Right"

        if side is not None:
            reference_found = False

            for source_control_name in toe_source_controls[
                    side]:
                if (
                    control_name in source_control_name
                    and source_control_name != control_name
                ):
                    reference_found = True
                    break

            if reference_found:
                target_path = (
                    u"RigLegs/LeftLeg/LeftToes"
                    if side == "Left"
                    else u"RigLegs/RightLeg/RightToes"
                )
                rig_toe_promotions[
                    control_name
                ] = target_path
                authority = (
                    authority
                    + u"+TOE_CONSTRAINT_EVIDENCE"
                )

        target_path = _canonicalize_context_path(
            target_path
        )

        rig_destinations[
            control_name
        ] = target_path

        rig_destination_sources[
            control_name
        ] = authority

        # Broad roots are acceptable only when neither current Master nor
        # fresh PRE contains a coherent more-specific destination.
        if target_path in (
                u"RigArms",
                u"RigLegs"):
            lookup_destination = (
                to_unicode(lookup["destination"])
                if lookup["known"]
                else None
            )

            if (
                source_path.startswith(
                    target_path + u"/"
                )
                or (
                    lookup_destination is not None
                    and (
                        u"/Left" in lookup_destination
                        or u"/Right" in lookup_destination
                    )
                )
            ):
                underspecified.append((
                    control_name,
                    source_path,
                    lookup_destination,
                    target_path,
                ))

    overlap = sorted(
        model_candidate_names.intersection(
            rig_candidate_names
        )
    )

    if overlap:
        raise ProbeError(
            "Generic policy plan has model/rig candidate overlap: %r."
            % overlap[:20]
        )

    # Resolve every authorized Master-stranded row.  Some rows are model
    # anatomy translated into active RigArms/RigLegs leaves; others may belong
    # to an ordinary Master family whose animator-facing branch is hidden by
    # the active rig.  In that case, use the proven active counterpart rather
    # than treating the row as "unaccounted".
    translated_model_names = set()
    translated_model_target_by_name = {}

    for target_path, names in model_translations.items():
        for control_name in names:
            control_name = to_unicode(
                control_name
            )
            translated_model_names.add(
                control_name
            )
            translated_model_target_by_name[
                control_name
            ] = to_unicode(
                target_path
            )

    has_rigbody = any([
        path == u"RigBody"
        or path.startswith(u"RigBody/")
        for path in source_paths
    ])

    master_destinations = {}
    master_destination_sources = {}
    unaccounted_master_rows = []

    for row in plan["master_rows"]:
        control_name = to_unicode(
            row["name"]
        )

        if control_name in translated_model_target_by_name:
            master_destinations[
                control_name
            ] = translated_model_target_by_name[
                control_name
            ]
            master_destination_sources[
                control_name
            ] = u"MODEL_TRANSLATION"
            continue

        lookup = master_lookup(
            master,
            control_name,
        )

        if not lookup["known"]:
            unaccounted_master_rows.append(
                control_name
            )
            continue

        master_destination = _canonicalize_context_path(
            lookup["destination"]
        )

        if master_destination is None:
            unaccounted_master_rows.append(
                control_name
            )
            continue

        target_path = master_destination
        authority = u"MASTER_DESTINATION"

        # If the ordinary semantic family is hidden by the supported active
        # rig, route the stranded control into that visible active counterpart.
        if (
            master_destination == u"Body"
            and has_rigbody
        ):
            body_meta = post["groups"].get(
                u"Body"
            )

            if (
                body_meta is not None
                and not bool(
                    body_meta["effective_visible"]
                )
            ):
                target_path = u"RigBody"
                authority = (
                    u"MASTER_DESTINATION+HIDDEN_BODY_ACTIVE_RIGBODY"
                )

        elif (
            master_destination.startswith(u"Arms/")
            and has_rigarms
        ):
            arms_meta = post["groups"].get(
                u"Arms"
            )

            if (
                arms_meta is not None
                and not bool(
                    arms_meta["effective_visible"]
                )
            ):
                target_path = (
                    u"RigArms"
                    + master_destination[
                        len(u"Arms"):
                    ]
                )
                authority = (
                    u"MASTER_DESTINATION+HIDDEN_ARMS_ACTIVE_RIGARMS"
                )

        elif (
            master_destination.startswith(u"Legs/")
            and has_riglegs
        ):
            legs_meta = post["groups"].get(
                u"Legs"
            )

            if (
                legs_meta is not None
                and not bool(
                    legs_meta["effective_visible"]
                )
            ):
                target_path = (
                    u"RigLegs"
                    + master_destination[
                        len(u"Legs"):
                    ]
                )
                authority = (
                    u"MASTER_DESTINATION+HIDDEN_LEGS_ACTIVE_RIGLEGS"
                )

        elif (
            master_destination == u"Toes/LeftToes"
            and has_riglegs
        ):
            target_path = (
                u"RigLegs/LeftLeg/LeftToes"
            )
            authority = (
                u"MASTER_DESTINATION+ACTIVE_RIG_TOE_COUNTERPART"
            )

        elif (
            master_destination == u"Toes/RightToes"
            and has_riglegs
        ):
            target_path = (
                u"RigLegs/RightLeg/RightToes"
            )
            authority = (
                u"MASTER_DESTINATION+ACTIVE_RIG_TOE_COUNTERPART"
            )

        target_path = _canonicalize_context_path(
            target_path
        )

        if target_path is None:
            unaccounted_master_rows.append(
                control_name
            )
            continue

        master_destinations[
            control_name
        ] = target_path
        master_destination_sources[
            control_name
        ] = authority

    unaccounted_master_rows = sorted(
        unaccounted_master_rows
    )

    keep_native = sorted(set([
        to_unicode(row["name"])
        for category_name in (
            "master_normalizations",
            "weak_unknown_diagnostics",
            "ambiguous_losses",
            "unresolved_owned_drift")
        for row in classified[
            category_name
        ]
    ]))

    return {
        "has_rigarms": has_rigarms,
        "has_riglegs": has_riglegs,
        "model_translations": model_translations,
        "rig_destinations": rig_destinations,
        "rig_destination_sources": rig_destination_sources,
        "rig_toe_promotions": rig_toe_promotions,
        "underspecified": underspecified,
        "master_destinations": master_destinations,
        "master_destination_sources": master_destination_sources,
        "unaccounted_master_rows": unaccounted_master_rows,
        "keep_native": keep_native,
        "strong_unknown_count": len(
            classified[
                "master_unknown_unknown"
            ]
        ),
        "authorized_master_count": len(
            plan["master_rows"]
        ),
        "authorized_rig_count": len(
            plan["rig_rows"]
        ),
    }

def production_resolve_group_path(root, path):
    path = to_unicode(path)

    if path in (
            u"",
            u"<ROOT>"):
        return root

    current = root

    for part in path.split(u"/"):
        current = find_direct_child(
            current,
            part,
        )

        if current is None:
            return None

    return current


def production_master_metadata_path(
        target_path,
        master):
    target_path = to_unicode(
        target_path
    )

    if target_path in master[
            "group_metadata"]:
        return target_path

    if target_path.startswith(
            u"RigArms/"):
        candidate = (
            u"Arms/"
            + target_path[
                len(u"RigArms/"):
            ]
        )

        if candidate in master[
                "group_metadata"]:
            return candidate

    if target_path == u"RigArms":
        if u"RigArms" in master[
                "group_metadata"]:
            return u"RigArms"

        if u"Arms" in master[
                "group_metadata"]:
            return u"Arms"

    if target_path == u"RigLegs":
        if u"RigLegs" in master[
                "group_metadata"]:
            return u"RigLegs"

        if u"Legs" in master[
                "group_metadata"]:
            return u"Legs"

    if target_path in (
            u"RigLegs/LeftLeg/LeftToes",
            u"RigLegs/RightLeg/RightToes"):
        candidate = (
            u"Toes/LeftToes"
            if target_path.endswith(
                u"/LeftToes")
            else u"Toes/RightToes"
        )

        if candidate in master[
                "group_metadata"]:
            return candidate

    return None


def production_source_paths_for_target(
        target_path):
    target_path = to_unicode(
        target_path
    )

    result = [
        target_path
    ]

    if target_path == u"RigArms":
        result.append(
            u"Arms"
        )

    elif target_path.startswith(
            u"RigArms/"):
        result.append(
            u"Arms/"
            + target_path[
                len(u"RigArms/"):
            ]
        )

    if target_path == u"RigLegs":
        result.append(
            u"Legs"
        )

    elif target_path in (
            u"RigLegs/LeftLeg/LeftToes",
            u"RigLegs/RightLeg/RightToes"):
        result.append(
            u"Toes/LeftToes"
            if target_path.endswith(
                u"/LeftToes")
            else u"Toes/RightToes"
        )

    elif target_path.startswith(
            u"RigLegs/"):
        result.append(
            u"Legs/"
            + target_path[
                len(u"RigLegs/"):
            ]
        )

    if target_path == u"RigBody":
        result.append(
            u"Body"
        )

    # Stable de-duplication.
    deduped = []

    for item in result:
        item = to_unicode(
            item
        )

        if item not in deduped:
            deduped.append(
                item
            )

    return deduped


def production_source_meta_for_target(
        target_path,
        pre,
        post,
        rig_source):
    candidate_paths = (
        production_source_paths_for_target(
            target_path
        )
    )

    # Active-rig semantic PRE is strongest runtime presentation evidence.
    for snapshot in (
            rig_source,
            pre):
        groups = snapshot[
            "groups"
        ]

        for candidate in candidate_paths:
            meta = groups.get(
                candidate
            )

            if meta is not None:
                return meta

    # Fresh native POST is fallback metadata authority for fields the Master
    # does not explicitly encode.
    for candidate in candidate_paths:
        meta = post[
            "groups"
        ].get(
            candidate
        )

        if meta is not None:
            return meta

    return None


def production_raw_selectable(group):
    value = scalar(
        group,
        "selectable",
    )

    if value is None:
        return None

    return bool(
        value
    )


def production_apply_explicit_master_metadata(
        group,
        target_path,
        master):
    master_path = production_master_metadata_path(
        target_path,
        master,
    )

    if master_path is None:
        return None

    meta = master[
        "group_metadata"
    ].get(
        master_path
    )

    if meta is None:
        return None

    explicit_color = meta.get(
        "group_color_explicit"
    )
    explicit_selectable = meta.get(
        "selectable_explicit"
    )

    if explicit_color is not None:
        set_group_color(
            group,
            explicit_color,
        )

    if explicit_selectable is not None:
        set_selectable(
            group,
            bool(
                explicit_selectable
            ),
        )

    return master_path


def production_apply_active_group_policy(
        group,
        target_path,
        pre,
        post,
        rig_source,
        master,
        source_meta=None):
    if source_meta is None:
        source_meta = production_source_meta_for_target(
            target_path,
            pre,
            post,
            rig_source,
        )

    if source_meta is not None:
        set_visible(
            group,
            True,
        )
        set_selectable(
            group,
            source_meta.get(
                "selectable"
            ),
        )
        set_snappable(
            group,
            source_meta.get(
                "snappable"
            ),
        )
        set_group_color(
            group,
            source_meta.get(
                "group_color"
            ),
        )
    else:
        set_visible(
            group,
            True,
        )

    master_path = production_apply_explicit_master_metadata(
        group,
        target_path,
        master,
    )

    return {
        "source_meta_found": bool(
            source_meta is not None
        ),
        "master_path": master_path,
    }


def production_ensure_group_path(
        root,
        target_path,
        pre,
        post,
        rig_source,
        master,
        created_paths):
    target_path = to_unicode(
        target_path
    )

    parts = target_path.split(
        u"/"
    )

    current = root
    prefix = []

    for depth, part in enumerate(
            parts):
        prefix.append(
            part
        )
        path = u"/".join(
            prefix
        )

        existing = find_direct_child(
            current,
            part,
        )

        if existing is not None:
            group = existing
        else:
            technical_name = (
                u"__PRODUCTION_CTX_%02d__%s"
                % (
                    depth + 1,
                    u"__".join(prefix),
                )
            )

            if find_direct_child(
                    current,
                    technical_name
                    ) is not None:
                raise ProbeError(
                    "Production technical group collision at %r."
                    % technical_name
                )

            group = create_independent_group(
                root,
                current,
                technical_name,
            )

            source_meta = production_source_meta_for_target(
                path,
                pre,
                post,
                rig_source,
            )

            if source_meta is not None:
                apply_source_metadata(
                    group,
                    source_meta,
                )
            else:
                set_visible(
                    group,
                    True,
                )

            rename_group(
                group,
                part,
            )

            created_paths.append(
                path
            )

        production_apply_active_group_policy(
            group,
            path,
            pre,
            post,
            rig_source,
            master,
        )

        current = group

    return current


def production_reorder_children_by_master(
        parent,
        master,
        master_parent_path,
        force_unknown_last=False):
    current_children = list(
        children(parent)
    )
    current_names = [
        to_unicode(
            name(child)
        )
        for child in current_children
    ]

    if len(current_names) != len(
            set(current_names)):
        raise ProbeError(
            "PRODUCTION refuses duplicate sibling names under %r: %r."
            % (
                master_parent_path,
                current_names,
            )
        )

    master_order = [
        to_unicode(x)
        for x in master[
            "group_sibling_order"
        ].get(
            master_parent_path,
            [],
        )
    ]

    child_by_name = dict([
        (
            to_unicode(name(child)),
            child,
        )
        for child in current_children
    ])

    known = [
        child_name
        for child_name in master_order
        if child_name in child_by_name
    ]

    contextual = [
        child_name
        for child_name in current_names
        if child_name not in master_order
    ]

    if force_unknown_last:
        contextual_without_unknown = [
            child_name
            for child_name in contextual
            if child_name != u"Unknown"
        ]

        desired = (
            list(known)
            + contextual_without_unknown
        )

        if u"Unknown" in child_by_name:
            desired.append(
                u"Unknown"
            )
    else:
        desired = (
            list(known)
            + contextual
        )

    if desired == current_names:
        return desired

    if (
        len(desired) != len(current_names)
        or set(desired) != set(current_names)
    ):
        raise ProbeError(
            "Production child-order cohort mismatch under %r: current=%r desired=%r."
            % (
                master_parent_path,
                current_names,
                desired,
            )
        )

    remove_child = getattr(
        parent,
        "RemoveChild",
        None,
    )

    if (
        remove_child is None
        or not callable(
            remove_child
        )
    ):
        raise ProbeError(
            "PRODUCTION RemoveChild unavailable under %r."
            % master_parent_path
        )

    handles_before = dict([
        (
            child_name,
            handle(
                child_by_name[
                    child_name
                ]
            ),
        )
        for child_name in current_names
    ])

    for child in current_children:
        remove_child(
            child
        )

    for child_name in desired:
        parent.AddChild(
            child_by_name[
                child_name
            ]
        )

    final_names = [
        to_unicode(
            name(child)
        )
        for child in children(
            parent
        )
    ]

    if final_names != desired:
        raise ProbeError(
            "Production child-order normalization failed under %r: desired=%r actual=%r."
            % (
                master_parent_path,
                desired,
                final_names,
            )
        )

    for child_name in desired:
        final_child = find_direct_child(
            parent,
            child_name,
        )

        if (
            final_child is None
            or handle(final_child)
            != handles_before[
                child_name
            ]
        ):
            raise ProbeError(
                "Production child-order normalization changed identity for %r."
                % child_name
            )

    return desired


def production_reorder_contextual_tree(
        root,
        master):
    result = {}

    result[u"<ROOT>"] = (
        production_reorder_children_by_master(
            root,
            master,
            u"<ROOT>",
            True,
        )
    )

    specs = [
        (
            u"RigArms",
            u"RigArms",
        ),
        (
            u"RigArms/LeftArm",
            u"Arms/LeftArm",
        ),
        (
            u"RigArms/RightArm",
            u"Arms/RightArm",
        ),
        (
            u"RigLegs",
            u"RigLegs",
        ),
        (
            u"RigLegs/LeftLeg",
            u"RigLegs/LeftLeg",
        ),
        (
            u"RigLegs/RightLeg",
            u"RigLegs/RightLeg",
        ),
    ]

    for live_path, master_path in specs:
        parent = production_resolve_group_path(
            root,
            live_path,
        )

        if parent is None:
            continue

        result[
            live_path
        ] = production_reorder_children_by_master(
            parent,
            master,
            master_path,
            False,
        )

    return result


def production_claim_destination(
        desired,
        control_name,
        target_path,
        authority):
    control_name = to_unicode(
        control_name
    )
    target_path = to_unicode(
        target_path
    )
    authority = to_unicode(
        authority
    )

    existing = desired.get(
        control_name
    )

    if existing is not None:
        if existing[
                "target_path"
                ] != target_path:
            raise ProbeError(
                "PRODUCTION conflicting generic destinations for %r: %r vs %r."
                % (
                    control_name,
                    existing[
                        "target_path"
                    ],
                    target_path,
                )
            )

        if authority not in existing[
                "authorities"]:
            existing[
                "authorities"
            ].append(
                authority
            )

        return

    desired[
        control_name
    ] = {
        "target_path": target_path,
        "authorities": [
            authority
        ],
    }


def production_apply_exact_master_destination_total_order(
        by_target,
        master):
    """
    Deterministically order a final contextual direct-control cohort by current
    Master only when every member is Master-known and the member's exact Master
    destination is the same final target path.

    This deliberately does not apply to mixed known/unknown cohorts or to
    contextual translations whose runtime destination differs from Master.
    """
    authorities = {}

    for target_path in sorted(
            by_target.keys()):
        target_path = to_unicode(
            target_path
        )
        names = [
            to_unicode(x)
            for x in by_target[
                target_path
            ]
        ]

        if len(names) < 2:
            continue

        ranked = []
        eligible = True

        for control_name in names:
            lookup = master_lookup(
                master,
                control_name,
            )

            if not lookup["known"]:
                eligible = False
                break

            master_destination = (
                _canonicalize_context_path(
                    lookup[
                        "destination"
                    ]
                )
            )

            if master_destination != target_path:
                eligible = False
                break

            ranked.append((
                int(
                    lookup[
                        "global_index"
                    ]
                ),
                int(
                    lookup[
                        "local_index"
                    ]
                ),
                control_name,
            ))

        if not eligible:
            continue

        ranked.sort(
            key=lambda row: (
                row[0],
                row[1],
            )
        )

        ordered = [
            row[2]
            for row in ranked
        ]

        if (
            len(ordered) != len(names)
            or set(ordered) != set(names)
        ):
            raise ProbeError(
                "Production exact-Master destination-order cohort mismatch for %r: "
                "current=%r ordered=%r."
                % (
                    target_path,
                    names,
                    ordered,
                )
            )

        by_target[
            target_path
        ] = ordered

        authorities[
            target_path
        ] = {
            "authority": (
                "EXACT_MASTER_DESTINATION_TOTAL_ORDER"
            ),
            "order": tuple(
                ordered
            ),
        }

    return authorities


def production_generic_composer(
        root,
        pre,
        post,
        master,
        shot,
        aset,
        plan,
        uniformity_plan):
    rig_source = plan[
        "rig_source"
    ]

    before_rig = discover_rig_context(
        shot,
        aset,
    )

    before = capture_snapshot_explicit(
        shot,
        aset,
        "PRODUCTION_GENERIC_COMPOSER_PRE",
        before_rig,
    )

    live = live_control_map(
        aset
    )

    desired = {}

    model_candidate_names = set()

    for target_path, names in uniformity_plan[
            "model_translations"
            ].items():
        for control_name in names:
            control_name = to_unicode(
                control_name
            )
            model_candidate_names.add(
                control_name
            )
            production_claim_destination(
                desired,
                control_name,
                target_path,
                u"MODEL_TRANSLATION",
            )

    for control_name, target_path in uniformity_plan[
            "rig_destinations"
            ].items():
        authority = uniformity_plan[
            "rig_destination_sources"
        ].get(
            control_name,
            u"RIG_PLAN",
        )

        production_claim_destination(
            desired,
            control_name,
            target_path,
            authority,
        )

    for control_name, target_path in uniformity_plan[
            "master_destinations"
            ].items():
        authority = uniformity_plan[
            "master_destination_sources"
        ].get(
            control_name,
            u"MASTER_STRANDED_PLAN",
        )

        production_claim_destination(
            desired,
            control_name,
            target_path,
            authority,
        )

    keep_native = set([
        to_unicode(x)
        for x in uniformity_plan[
            "keep_native"
        ]
    ])

    forbidden_overlap = sorted(
        keep_native.intersection(
            set(
                desired.keys()
            )
        )
    )

    if forbidden_overlap:
        raise ProbeError(
            "PRODUCTION keep-native controls also received contextual destinations: %r."
            % forbidden_overlap
        )

    created_paths = []

    required_paths = sorted(
        set([
            row[
                "target_path"
            ]
            for row in desired.values()
        ]),
        key=lambda path: (
            len(
                to_unicode(
                    path
                ).split(u"/")
            ),
            to_unicode(
                path
            ),
        ),
    )

    nodes = {}

    for target_path in required_paths:
        nodes[
            target_path
        ] = production_ensure_group_path(
            root,
            target_path,
            pre,
            post,
            rig_source,
            master,
            created_paths,
        )

    # Build a deterministic active-presentation order:
    #   1. rig-owned controls in classifier/PRE order,
    #   2. non-model Master-stranded controls,
    #   3. canonical model transforms in native-POST/Master order.
    by_target = {}

    def append_target_name(
            target_path,
            control_name):
        target_path = to_unicode(
            target_path
        )
        control_name = to_unicode(
            control_name
        )

        by_target.setdefault(
            target_path,
            []
        )

        if control_name not in by_target[
                target_path]:
            by_target[
                target_path
            ].append(
                control_name
            )

    for row in plan[
            "rig_rows"]:
        control_name = to_unicode(
            row["name"]
        )
        destination = desired.get(
            control_name
        )

        if destination is not None:
            append_target_name(
                destination[
                    "target_path"
                ],
                control_name,
            )

    for row in plan[
            "master_rows"]:
        control_name = to_unicode(
            row["name"]
        )

        if control_name in model_candidate_names:
            continue

        destination = desired.get(
            control_name
        )

        if destination is not None:
            append_target_name(
                destination[
                    "target_path"
                ],
                control_name,
            )

    for target_path, names in uniformity_plan[
            "model_translations"
            ].items():
        for control_name in names:
            append_target_name(
                target_path,
                control_name,
            )

    # Defensive fallback for any destination introduced by future planner
    # extensions but not represented in the three ordering cohorts above.
    for control_name, destination in sorted(
            desired.items()):
        append_target_name(
            destination[
                "target_path"
            ],
            control_name,
        )

    destination_direct_order_authorities = (
        production_apply_exact_master_destination_total_order(
            by_target,
            master,
        )
    )

    moved_names = []
    already_correct_names = []

    for target_path in sorted(
            by_target.keys()):
        group = nodes.get(
            target_path
        )

        if group is None:
            group = production_resolve_group_path(
                root,
                target_path,
            )

        if group is None:
            raise ProbeError(
                "Production target group disappeared before control composition: %r."
                % target_path
            )

        for control_name in by_target[
                target_path]:
            control = live.get(
                control_name
            )

            if control is None:
                raise ProbeError(
                    "PRODUCTION live control disappeared: %r."
                    % control_name
                )

            current_post = one_membership(
                post,
                control_name,
            )

            if current_post == target_path:
                already_correct_names.append(
                    control_name
                )
                continue

            add_control_to_group(
                group,
                control,
            )

            moved_names.append(
                control_name
            )

    toe_targets = [
        path
        for path in required_paths
        if path in (
            u"RigLegs/LeftLeg/LeftToes",
            u"RigLegs/RightLeg/RightToes",
        )
    ]

    if toe_targets:
        canonical_toes = production_resolve_group_path(
            root,
            u"Toes",
        )

        if canonical_toes is None:
            raise ProbeError(
                "PRODUCTION Toe translation requires canonical Toes source."
            )

        set_visible(
            canonical_toes,
            False,
        )

    # Restore active-rig helper accessibility if that runtime family exists.
    helpers = production_resolve_group_path(
        root,
        u"RigHelpers",
    )

    helper_source = rig_source[
        "groups"
    ].get(
        u"RigHelpers"
    )

    if (
        helpers is not None
        and helper_source is not None
    ):
        set_visible(
            helpers,
            bool(
                helper_source.get(
                    "visible",
                    True,
                )
            ),
        )
        set_selectable(
            helpers,
            helper_source.get(
                "selectable"
            ),
        )
        set_snappable(
            helpers,
            helper_source.get(
                "snappable"
            ),
        )

        production_apply_explicit_master_metadata(
            helpers,
            u"RigHelpers",
            master,
        )

    order_result = production_reorder_contextual_tree(
        root,
        master,
    )

    after_rig = discover_rig_context(
        shot,
        aset,
    )

    after = capture_snapshot_explicit(
        shot,
        aset,
        "PRODUCTION_GENERIC_COMPOSER_POST",
        after_rig,
    )

    failures = []

    # Exact contextual memberships.
    for control_name, destination in desired.items():
        actual_path = one_membership(
            after,
            control_name,
        )
        expected_path = destination[
            "target_path"
        ]

        if actual_path != expected_path:
            failures.append((
                "destination",
                control_name,
                expected_path,
                actual_path,
            ))

    # Fail-closed controls stay exactly where native POST left them.
    for control_name in sorted(
            keep_native):
        if (
            post["memberships"].get(
                control_name
            )
            != after["memberships"].get(
                control_name
            )
        ):
            failures.append((
                "keep_native_changed",
                control_name,
                post["memberships"].get(
                    control_name
                ),
                after["memberships"].get(
                    control_name
                ),
            ))

    # All non-candidate memberships must remain native POST.
    candidate_names = set(
        desired.keys()
    )

    for control_name, post_paths in post[
            "memberships"
            ].items():
        control_name = to_unicode(
            control_name
        )

        if control_name in candidate_names:
            continue

        after_paths = after[
            "memberships"
        ].get(
            control_name
        )

        if list(post_paths) != list(
                after_paths):
            failures.append((
                "noncandidate_membership_changed",
                control_name,
                list(post_paths),
                list(after_paths),
            ))

    # Required active presentation groups must be genuinely visible.
    for target_path in required_paths:
        meta = after[
            "groups"
        ].get(
            target_path
        )

        if (
            meta is None
            or not bool(
                meta[
                    "effective_visible"
                ]
            )
        ):
            failures.append((
                "target_not_effectively_visible",
                target_path,
            ))

    # Explicit current-Master group metadata must win where available.
    for target_path in required_paths:
        master_path = production_master_metadata_path(
            target_path,
            master,
        )

        if master_path is None:
            continue

        master_meta = master[
            "group_metadata"
        ].get(
            master_path
        )
        final_meta = after[
            "groups"
        ].get(
            target_path
        )

        if (
            master_meta is None
            or final_meta is None
        ):
            continue

        explicit_color = master_meta.get(
            "group_color_explicit"
        )
        explicit_selectable = master_meta.get(
            "selectable_explicit"
        )

        if (
            explicit_color is not None
            and list(
                final_meta[
                    "group_color"
                ]
            ) != list(
                explicit_color
            )
        ):
            failures.append((
                "master_color",
                target_path,
                explicit_color,
                final_meta[
                    "group_color"
                ],
            ))

        if explicit_selectable is not None:
            final_group = (
                production_resolve_group_path(
                    root,
                    target_path,
                )
            )

            raw_selectable = (
                None
                if final_group is None
                else production_raw_selectable(
                    final_group
                )
            )

            if raw_selectable is None:
                failures.append((
                    "master_selectable_raw_unavailable",
                    target_path,
                    explicit_selectable,
                ))

            elif (
                bool(
                    raw_selectable
                )
                != bool(
                    explicit_selectable
                )
            ):
                failures.append((
                    "master_selectable_raw",
                    target_path,
                    explicit_selectable,
                    raw_selectable,
                ))

    # Canonical Toes becomes hidden/internal only when active Toe translation
    # actually exists.
    if toe_targets:
        toes_meta = after[
            "groups"
        ].get(
            u"Toes"
        )

        if (
            toes_meta is None
            or bool(
                toes_meta[
                    "effective_visible"
                ]
            )
        ):
            failures.append((
                "canonical_toes_not_hidden_internal",
            ))

    # Current Master governs every Master-known root sibling. Unknown remains
    # last; contextual-only roots keep relative order after Master-known roots.
    root_actual = [
        to_unicode(
            name(child)
        )
        for child in children(
            root
        )
    ]

    master_root = [
        to_unicode(x)
        for x in master[
            "group_sibling_order"
        ].get(
            u"<ROOT>",
            [],
        )
    ]

    actual_master_projection = [
        child_name
        for child_name in root_actual
        if child_name in master_root
    ]

    expected_master_projection = [
        child_name
        for child_name in master_root
        if child_name in root_actual
    ]

    if (
        actual_master_projection
        != expected_master_projection
    ):
        failures.append((
            "root_master_projection",
            expected_master_projection,
            actual_master_projection,
        ))

    if (
        u"Unknown" in root_actual
        and root_actual[-1] != u"Unknown"
    ):
        failures.append((
            "unknown_not_last",
            root_actual,
        ))

    # Master-established side order.
    for path in (
            u"RigArms",
            u"RigLegs"):
        meta = after[
            "groups"
        ].get(
            path
        )

        if meta is None:
            continue

        actual_children = list(
            meta[
                "child_names_in_order"
            ]
        )

        master_children = [
            to_unicode(x)
            for x in master[
                "group_sibling_order"
            ].get(
                path,
                [],
            )
            if to_unicode(x)
            in actual_children
        ]

        actual_known = [
            child_name
            for child_name in actual_children
            if child_name in master[
                "group_sibling_order"
            ].get(
                path,
                [],
            )
        ]

        if actual_known != master_children:
            failures.append((
                "side_child_order",
                path,
                master_children,
                actual_known,
            ))

    # Finger/Carpal order uses the ordinary anatomical Master counterpart.
    for live_path, master_path in (
            (
                u"RigArms/LeftArm",
                u"Arms/LeftArm",
            ),
            (
                u"RigArms/RightArm",
                u"Arms/RightArm",
            )):
        meta = after[
            "groups"
        ].get(
            live_path
        )

        if meta is None:
            continue

        actual_children = list(
            meta[
                "child_names_in_order"
            ]
        )
        master_children_full = [
            to_unicode(x)
            for x in master[
                "group_sibling_order"
            ].get(
                master_path,
                [],
            )
        ]
        expected = [
            child_name
            for child_name in master_children_full
            if child_name in actual_children
        ]
        actual_known = [
            child_name
            for child_name in actual_children
            if child_name in master_children_full
        ]

        if actual_known != expected:
            failures.append((
                "finger_carpal_child_order",
                live_path,
                expected,
                actual_known,
            ))

    # No temporary scaffolding/wrapper may remain in the animator-facing tree.
    for path in after[
            "groups"
            ].keys():
        parts = to_unicode(
            path
        ).split(
            u"/"
        )

        if any([
                part.startswith(
                    u"__PRODUCTION_CTX_")
                for part in parts]):
            failures.append((
                "technical_group_leaked",
                path,
            ))

    if (
        production_resolve_group_path(
            root,
            to_unicode(
                RIG_RECON_ROOT
            )
        ) is not None
        or production_resolve_group_path(
            root,
            to_unicode(
                MASTER_RECON_ROOT
            )
        ) is not None
    ):
        failures.append((
            "legacy_wrapper_present",
        ))

    if (
        post[
            "owned_control_name_set"
        ]
        != after[
            "owned_control_name_set"
        ]
    ):
        failures.append((
            "ownership_changed",
        ))

    if (
        post[
            "hidden_groups"
        ]
        != after[
            "hidden_groups"
        ]
    ):
        failures.append((
            "hiddenGroups_changed",
        ))

    if (
        post[
            "control_names_in_animation_set_order"
        ]
        != after[
            "control_names_in_animation_set_order"
        ]
    ):
        failures.append((
            "animation_set_control_order_changed",
        ))

    if (
        after[
            "duplicate_control_names"
        ]
        or after[
            "duplicate_sibling_groups"
        ]
        or after[
            "duplicate_direct_controls"
        ]
        or after[
            "duplicate_memberships"
        ]
    ):
        failures.append((
            "duplicate_invariant",
        ))

    if after[
            "rig_status"
            ] != "SUPPORTED_ACTIVE_RIG":
        failures.append((
            "active_rig_status_changed",
            after[
                "rig_status"
            ],
        ))

    if failures:
        raise ProbeError(
            "Production generic composer validation failed for %r: %r."
            % (
                (
                    to_unicode(
                        shot.GetName()
                    ),
                    to_unicode(
                        aset.GetName()
                    ),
                ),
                failures[:80],
            )
        )

    master_selectability_rows = []

    for target_path in required_paths:
        master_path = (
            production_master_metadata_path(
                target_path,
                master,
            )
        )

        if master_path is None:
            continue

        master_meta = master[
            "group_metadata"
        ].get(
            master_path
        )

        if master_meta is None:
            continue

        explicit_selectable = (
            master_meta.get(
                "selectable_explicit"
            )
        )

        if explicit_selectable is None:
            continue

        final_group = (
            production_resolve_group_path(
                root,
                target_path,
            )
        )

        if final_group is None:
            continue

        master_selectability_rows.append((
            target_path,
            bool(
                explicit_selectable
            ),
            production_raw_selectable(
                final_group
            ),
            is_selectable(
                final_group
            ),
        ))

    return {
        "master_selectability_rows": (
            master_selectability_rows
        ),
        "desired_count": len(
            desired
        ),
        "moved_count": len(
            moved_names
        ),
        "already_correct_count": len(
            already_correct_names
        ),
        "created_paths": list(
            created_paths
        ),
        "root_order": root_actual,
        "toe_translation": bool(
            toe_targets
        ),
        "order_result": order_result,
        "destination_direct_order_authorities": (
            destination_direct_order_authorities
        ),
    }


# -----------------------------------------------------------------------------
# PRE-REBUILD ELIGIBILITY GATE + SCOPE UI
# -----------------------------------------------------------------------------

GATE_LOW_BONE_CEILING = 30
GATE_MIN_SHARED_TRANSFORMS = 4
GATE_MIN_CHILD_COVERAGE = 0.20

GATE_SUPPORTED_MDL_VERSIONS = (44, 48, 49)
GATE_MIN_MDL_HEADER_BYTES = 164
GATE_FLAGS_OFFSET = 152
GATE_NUMBONES_OFFSET = 156
GATE_BONEINDEX_OFFSET = 160
GATE_STATIC_PROP_FLAG = 0x10

SCOPE_SELECTED = u"SELECTED_SHOTS"
SCOPE_ALL = u"ALL_SHOTS"


def _gate_get_model_name(game_model):
    for attr_name in (
        "modelName",
        "modelPath",
        "fileName",
        "filename",
        "model",
    ):
        value = scalar(game_model, attr_name)
        if value is None:
            continue

        text = to_unicode(value).strip()

        if text:
            return text

    return None


def _gate_list_content_dirs(game_dir):
    try:
        entries = os.listdir(game_dir)
    except Exception:
        return []

    out = []

    for entry in entries:
        path = os.path.join(game_dir, entry)

        try:
            if os.path.isdir(path):
                out.append(path)
        except Exception:
            continue

    out.sort(
        key=lambda value: os.path.normcase(value)
    )

    return out


def _gate_normalize_model_relative_path(model_name):
    if model_name is None:
        return None

    text = to_unicode(model_name).strip()

    if not text:
        return None

    text = (
        text.replace(u"/", os.sep)
        .replace(u"\\", os.sep)
    )

    while text.startswith(os.sep):
        text = text[1:]

    return text


def _gate_loose_candidates(content_dirs, model_name):
    if model_name is None:
        return []

    raw = to_unicode(model_name).strip()

    if not raw:
        return []

    if os.path.isabs(raw):
        try:
            if os.path.isfile(raw):
                return [os.path.normpath(raw)]
        except Exception:
            pass
        return []

    rel = _gate_normalize_model_relative_path(
        raw
    )

    if not rel:
        return []

    candidates = []

    for content_dir in content_dirs:
        candidate = os.path.normpath(
            os.path.join(
                content_dir,
                rel,
            )
        )

        try:
            if os.path.isfile(candidate):
                candidates.append(candidate)
        except Exception:
            continue

    seen = set()
    unique = []

    for candidate in candidates:
        key = os.path.normcase(
            os.path.abspath(candidate)
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(candidate)

    return unique


def _gate_read_mdl_header(path):
    result = {
        "status": u"UNREAD",
        "numbones": None,
        "is_static_prop": None,
    }

    try:
        f = open(path, "rb")

        try:
            data = f.read(
                GATE_MIN_MDL_HEADER_BYTES
            )
        finally:
            f.close()

        if len(data) < 8:
            result["status"] = u"HEADER_TOO_SHORT"
            return result

        if data[0:4] != "IDST":
            result["status"] = u"BAD_MAGIC"
            return result

        version = int(
            struct.unpack(
                "<i",
                data[4:8],
            )[0]
        )

        if (
            version
            not in GATE_SUPPORTED_MDL_VERSIONS
        ):
            result["status"] = u"UNSUPPORTED_VERSION"
            return result

        if (
            len(data)
            < GATE_MIN_MDL_HEADER_BYTES
        ):
            result[
                "status"
            ] = u"HEADER_TOO_SHORT_FOR_SUPPORTED_LAYOUT"
            return result

        declared_length = int(
            struct.unpack(
                "<i",
                data[76:80],
            )[0]
        )

        flags = int(
            struct.unpack(
                "<i",
                data[
                    GATE_FLAGS_OFFSET:
                    GATE_FLAGS_OFFSET + 4
                ],
            )[0]
        )

        numbones = int(
            struct.unpack(
                "<i",
                data[
                    GATE_NUMBONES_OFFSET:
                    GATE_NUMBONES_OFFSET + 4
                ],
            )[0]
        )

        boneindex = int(
            struct.unpack(
                "<i",
                data[
                    GATE_BONEINDEX_OFFSET:
                    GATE_BONEINDEX_OFFSET + 4
                ],
            )[0]
        )

        actual_length = int(
            os.path.getsize(path)
        )

        if (
            declared_length <= 0
            or numbones < 0
            or boneindex < 0
            or (
                numbones > 0
                and boneindex <= 0
            )
            or boneindex > actual_length
        ):
            result["status"] = u"HEADER_SANITY_FAIL"
            return result

        result["status"] = u"HEADER_OK"
        result["numbones"] = numbones
        result["is_static_prop"] = bool(
            flags
            & GATE_STATIC_PROP_FLAG
        )

        return result

    except Exception as exc:
        result["status"] = (
            u"READ_ERROR:%s"
            % to_unicode(
                repr(exc)
            )
        )
        return result


def _gate_consensus_header(
        candidates,
        cache):
    result = {
        "resolution": u"NO_LOOSE_MATCH",
        "status": u"NOT_READ",
        "numbones": None,
        "is_static_prop": None,
    }

    if not candidates:
        return result

    headers = []

    for candidate in candidates:
        key = os.path.normcase(
            os.path.abspath(candidate)
        )

        if key not in cache:
            cache[key] = (
                _gate_read_mdl_header(
                    candidate
                )
            )

        headers.append(
            cache[key]
        )

    if len(headers) == 1:
        header = headers[0]
        result["resolution"] = (
            u"UNIQUE_LOOSE_MATCH"
        )
        result["status"] = (
            header["status"]
        )

        if (
            header["status"]
            == u"HEADER_OK"
        ):
            result["numbones"] = (
                header["numbones"]
            )
            result["is_static_prop"] = (
                header["is_static_prop"]
            )

        return result

    if all(
        header["status"]
        == u"HEADER_OK"
        for header in headers
    ):
        bone_values = set([
            int(header["numbones"])
            for header in headers
        ])
        static_values = set([
            bool(
                header["is_static_prop"]
            )
            for header in headers
        ])

        if (
            len(bone_values) == 1
            and len(static_values) == 1
        ):
            result["resolution"] = (
                u"MULTIPLE_HEADER_CONSENSUS"
            )
            result["status"] = (
                u"HEADER_CONSENSUS_OK"
            )
            result["numbones"] = (
                list(bone_values)[0]
            )
            result["is_static_prop"] = (
                list(static_values)[0]
            )
            return result

    result["resolution"] = (
        u"MULTIPLE_AMBIGUOUS"
    )
    result["status"] = (
        u"NO_SAFE_CONSENSUS"
    )

    return result


def _gate_normalized_token(value):
    folded = ascii_fold(value)
    return u"".join([
        ch
        for ch in folded
        if (
            (u"a" <= ch <= u"z")
            or (u"0" <= ch <= u"9")
        )
    ])


def _gate_path_segments(path):
    if not path:
        return []

    return [
        _gate_normalized_token(segment)
        for segment in to_unicode(
            path
        ).split(u"/")
        if segment
    ]


def _gate_has_arm_segment(path):
    for segment in _gate_path_segments(
            path):
        if segment in (
            "arms",
            "rigarms",
            "leftarm",
            "rightarm",
            "rigleftarm",
            "rigrightarm",
        ):
            return True

        if (
            segment.endswith("leftarm")
            or segment.endswith("rightarm")
        ):
            return True

    return False


def _gate_has_leg_segment(path):
    for segment in _gate_path_segments(
            path):
        if segment in (
            "legs",
            "riglegs",
            "leftleg",
            "rightleg",
            "rigleftleg",
            "rigrightleg",
        ):
            return True

        if (
            segment.endswith("leftleg")
            or segment.endswith("rightleg")
        ):
            return True

    return False


def _gate_literal_head_neck_token(
        literal):
    folded = ascii_fold(literal)

    pieces = [
        piece
        for piece in re.split(
            r"[^a-z0-9]+",
            folded,
        )
        if piece
    ]

    compact = _gate_normalized_token(
        literal
    )

    for piece in pieces:
        if piece in (
            "head",
            "neck",
        ):
            return True

        if (
            piece.startswith("head")
            or piece.startswith("neck")
        ):
            return True

    return (
        "head" in compact
        or "neck" in compact
    )


def _gate_has_head_path_segment(
        path):
    for segment in _gate_path_segments(
            path):
        if (
            "head" in segment
            or "neck" in segment
        ):
            return True

    return False


def _gate_transform_controls(aset):
    return [
        control
        for control in arr(
            aset,
            "controls",
        )
        if typ(control)
        == u"DmeTransformControl"
    ]


def _gate_nonroot_transform_names(
        aset):
    out = set()
    root_fold = ascii_fold(
        "rootTransform"
    )

    for control in _gate_transform_controls(
            aset):
        folded = ascii_fold(
            name(control)
        )

        if folded == root_fold:
            continue

        out.add(folded)

    return out


def _gate_is_alh(
        aset,
        master):
    arm = False
    leg = False
    head = False

    for control in _gate_transform_controls(
            aset):
        literal = name(control)

        lookup = master_lookup(
            master,
            literal,
        )

        destination = lookup[
            "destination"
        ]

        if lookup["known"]:
            if _gate_has_arm_segment(
                    destination):
                arm = True

            if _gate_has_leg_segment(
                    destination):
                leg = True

            if _gate_has_head_path_segment(
                    destination):
                head = True

        if _gate_literal_head_neck_token(
                literal):
            head = True

    return (
        bool(
            arm
            and leg
            and head
        ),
        arm,
        leg,
        head,
    )


def _gate_resolve_override_parent(
        game_model):
    value = scalar(
        game_model,
        "overrideParent",
    )

    if value is None:
        return None

    try:
        if not native_ptr(value):
            return None
    except Exception:
        return None

    return value


def _gate_ratio(num, den):
    if den <= 0:
        return 0.0

    return (
        float(num)
        / float(den)
    )


class RebuildScopeDialog(
        QtGui.QDialog):

    CHOICE_NONE = 0
    CHOICE_SELECTED = 1
    CHOICE_ALL = 2
    CHOICE_CANCEL = 3

    def __init__(
            self,
            parent=None):
        QtGui.QDialog.__init__(
            self,
            parent
        )

        self.choice = (
            self.CHOICE_NONE
        )

        self.setWindowTitle(
            "Rebuild Control Groups"
        )
        self.setModal(
            True
        )

        layout = (
            QtGui.QVBoxLayout()
        )
        self.setLayout(
            layout
        )

        title = QtGui.QLabel(
            "Rebuild Control Groups"
        )
        title.setAlignment(
            QtCore.Qt.AlignCenter
        )

        layout.addWidget(
            title
        )

        selected_button = (
            QtGui.QPushButton(
                "Rebuild Selected Shot(s)"
            )
        )
        all_button = (
            QtGui.QPushButton(
                "Rebuild All Shots"
            )
        )
        cancel_button = (
            QtGui.QPushButton(
                "Cancel"
            )
        )

        layout.addWidget(
            selected_button
        )
        layout.addWidget(
            all_button
        )
        layout.addWidget(
            cancel_button
        )

        selected_button.clicked.connect(
            self.choose_selected
        )
        all_button.clicked.connect(
            self.choose_all
        )
        cancel_button.clicked.connect(
            self.choose_cancel
        )

        self.setMinimumWidth(
            280
        )

    def choose_selected(self):
        self.choice = (
            self.CHOICE_SELECTED
        )
        self.accept()

    def choose_all(self):
        self.choice = (
            self.CHOICE_ALL
        )
        self.accept()

    def choose_cancel(self):
        self.choice = (
            self.CHOICE_CANCEL
        )
        self.reject()

    def closeEvent(
            self,
            event):
        if (
            self.choice
            == self.CHOICE_NONE
        ):
            self.choice = (
                self.CHOICE_CANCEL
            )

        QtGui.QDialog.closeEvent(
            self,
            event
        )


def _scope_dialog_parent():
    try:
        active = (
            QtGui.QApplication.activeWindow()
        )
    except Exception:
        active = None

    try:
        if (
            active is not None
            and isinstance(
                active,
                QtGui.QWidget,
            )
        ):
            return active
    except Exception:
        pass

    return None


def _resolve_selected_scope(
        all_shots):
    selected = list(
        sfmClipEditor.GetSelectedShots()
    )

    if not selected:
        raise ProbeError(
            "Rebuild Selected Shot(s) requires at least one Clip Editor-selected shot; selected_count=0."
        )

    # Resolve each UI-selected shot independently against the canonical
    # sfmApp.GetShots() list. A selected shot must have exactly one canonical
    # match. This prevents silent widening/narrowing of the requested scope.
    resolved_ptrs = set()

    for selected_shot in selected:
        selected_handle = None
        selected_ptr = (
            native_ptr(
                selected_shot
            )
        )

        try:
            selected_handle = int(
                selected_shot.GetHandle()
            )
        except Exception:
            pass

        matches = []

        for shot in all_shots:
            matched = False

            try:
                shot_handle = int(
                    shot.GetHandle()
                )
            except Exception:
                shot_handle = None

            shot_ptr = native_ptr(
                shot
            )

            if (
                selected_handle is not None
                and shot_handle is not None
                and selected_handle
                == shot_handle
            ):
                matched = True

            if (
                selected_ptr is not None
                and shot_ptr is not None
                and selected_ptr
                == shot_ptr
            ):
                matched = True

            if matched:
                matches.append(
                    shot
                )

        unique_matches = {}

        for shot in matches:
            unique_matches[
                native_ptr(
                    shot
                )
            ] = shot

        if len(unique_matches) != 1:
            raise ProbeError(
                "Selected Clip Editor shot did not resolve uniquely to sfmApp.GetShots(); matches=%d."
                % len(unique_matches)
            )

        resolved_ptrs.add(
            list(
                unique_matches.keys()
            )[0]
        )

    # Return the deduplicated selection in canonical session/timeline order,
    # not pointer order and not arbitrary UI selection order.
    resolved = []

    for shot in all_shots:
        shot_ptr = native_ptr(
            shot
        )

        if shot_ptr in resolved_ptrs:
            resolved.append(
                shot
            )

    if len(resolved) != len(resolved_ptrs):
        raise ProbeError(
            "Resolved selected-shot scope accounting mismatch; selected_unique=%d resolved=%d."
            % (
                len(resolved_ptrs),
                len(resolved),
            )
        )

    return resolved


def _choose_scope():
    all_shots = list(
        sfmApp.GetShots()
    )

    if not all_shots:
        raise ProbeError(
            "No shots returned by sfmApp.GetShots()."
        )

    dialog = RebuildScopeDialog(
        _scope_dialog_parent()
    )

    dialog.exec_()

    if (
        dialog.choice
        == RebuildScopeDialog.CHOICE_CANCEL
    ):
        return None, None

    if (
        dialog.choice
        == RebuildScopeDialog.CHOICE_SELECTED
    ):
        return (
            SCOPE_SELECTED,
            _resolve_selected_scope(
                all_shots
            ),
        )

    if (
        dialog.choice
        == RebuildScopeDialog.CHOICE_ALL
    ):
        return (
            SCOPE_ALL,
            all_shots,
        )

    raise ProbeError(
        "Unexpected rebuild scope dialog result."
    )


def _show_scope_error(message):
    text = to_unicode(
        message
    )

    try:
        QtGui.QMessageBox.warning(
            _scope_dialog_parent(),
            "Rebuild Control Groups",
            text,
        )
        return
    except Exception:
        pass

    try:
        sys.stdout.write(
            "Rebuild Control Groups: %s\n"
            % text
        )
    except Exception:
        pass



class RebuildControlGroupsProductionRun(
        QtCore.QObject):

    def __init__(
            self,
            main_window,
            scope_mode,
            scope_shots):
        QtCore.QObject.__init__(
            self,
            main_window
        )

        self.scope_mode = (
            to_unicode(
                scope_mode
            )
        )
        self.scope_shots = list(
            scope_shots
        )

        self.setObjectName(
            RUN_LOCK_NAME
        )

        self.fp = None
        self.finished = False
        self.failure_message = None

        self.rebuild = None
        self.ifm_path = None
        self.master_path = None
        self.master_hash = None

        self.original_head = None
        self.original_shot_ptr = None
        self.restore_in_progress = False

        self.work = []
        self.work_index = 0
        self.current_target_index = 0

        # CONTEXTUALIZER target-level Qt callback accounting.
        self.target_callback_defer_schedules = 0
        self.target_resume_callbacks = 0
        self.target_resume_guard_passes = 0
        self.target_reresolve_passes = 0

        self.session_expected = {}
        self.session_identity_expected = ()

        # CONTEXTUALIZER layered-isolation accounting.
        self.layer_peer_checks = 0
        self.layer_peer_fingerprints = 0
        self.layer_identity_checks = 0
        self.layer_periodic_global_checks = 0
        self.layer_end_global_checks = 0

        # CONTEXTUALIZER diagnostic telemetry only.
        self.run_started_wall = None
        self.current_shot_started_wall = None
        self.telemetry_target_sequence = 0
        self.telemetry_native_attempts = 0
        self.telemetry_completed_targets = 0

        # CONTEXTUALIZER address-space / parser observation accounting.
        self.contextualizer_architecture = None
        self.contextualizer_vas_samples = 0
        self.contextualizer_vas_successes = 0
        self.contextualizer_vas_failures = 0

        # CONTEXTUALIZER immutable scoped Master index. Pure Python only; no DME refs.
        self.master_index = None
        self.master_index_scope_folds = set()
        self.master_index_builds = 0
        self.master_index_build_seconds = 0.0
        self.master_index_build_private_delta = None
        self.master_index_build_working_delta = None
        self.master_index_gate_opportunities = 0
        self.master_index_target_opportunities = 0
        self.master_index_gate_validations = 0
        self.master_index_target_validations = 0
        self.master_index_sha_checks = 0
        self.master_index_sha_seconds = 0.0

        self.contextualizer_global_capture_count = 0
        self.contextualizer_global_capture_max_private_delta = None

        self.total_shots_seen = 0
        self.total_shots_processed = 0
        self.total_sets_seen = 0
        self.total_model_backed = 0
        self.total_non_model_skips = 0
        self.total_root_skips = 0
        self.total_targets = 0
        self.total_duplicate_aset_skips = 0
        self.total_gate_static_skips = 0
        self.total_gate_follower_skips = 0
        self.total_gate_lowbone_skips = 0
        self.total_gate_failclosed_process = 0
        self.gate_skip_model_counts = {}
        self.gate_mdl_cache = {}
        self.gate_content_dirs = []
        self.total_native_rebuilt = 0
        self.total_supported_active_rig = 0
        self.total_unrigged = 0
        self.total_ambiguous_rig = 0
        self.total_reconciled = 0
        self.total_native_only = 0
        self.total_policy_fallback = 0
        self.production_supported_plan_pairs = set()
        self.production_policy_plan_passes = 0
        self.production_composer_pairs = set()
        self.production_composer_passes = 0
        self.production_terminal_results = {}
        self.production_inventory_pairs = set()
        self.production_final_semantic_capture_pairs = set()
        self.production_mixed_direct_by_target = {}
        self.production_destination_order_cohort_count = 0

        self.class_totals = {
            "pre_hidden_master_active": 0,
            "rig_losses": 0,
            "master_stranded": 0,
            "parent_collapses": 0,
            "master_normalizations": 0,
            "master_unknown_unknown": 0,
            "weak_unknown_diagnostics": 0,
            "ambiguous_losses": 0,
            "unresolved_owned_drift": 0,
        }


    def log(
            self,
            text=""):
        try:
            if isinstance(
                    text,
                    unicode):
                data = text.encode(
                    "utf-8",
                    "backslashreplace",
                )
            else:
                data = str(text)
        except Exception:
            data = repr(text)

        try:
            sys.stdout.write(
                data + "\n"
            )
        except Exception:
            pass

        if self.fp is not None:
            try:
                self.fp.write(
                    data + "\n"
                )
                self.fp.flush()
            except Exception:
                pass


    def section(
            self,
            title):
        self.log("")
        self.log(
            "=" * 108
        )
        self.log(
            title
        )
        self.log(
            "=" * 108
        )


    def release_run_lock(self):
        try:
            self.setParent(
                None
            )
        except Exception:
            pass

        try:
            self.deleteLater()
        except Exception:
            pass


    def get_game_model(
            self,
            aset):
        try:
            if not aset.HasAttribute(
                    "gameModel"):
                return None
        except Exception:
            return None

        try:
            game_model = aset.gameModel
        except Exception:
            return None

        if (
            game_model is None
            or not native_ptr(
                game_model
            )
        ):
            return None

        return game_model


    def get_root_group(
            self,
            aset):
        try:
            return (
                aset.GetRootControlGroup()
            )
        except Exception:
            return None


    def shot_times(
            self,
            shot):
        tf = shot.timeFrame

        start = (
            tf.GetStartTime().GetSeconds()
        )
        duration = (
            tf.GetDuration().GetSeconds()
        )

        if duration <= 0.0:
            raise ProbeError(
                "Shot has non-positive duration."
            )

        return (
            start,
            duration,
            start
            + duration / 2.0,
        )


    def prepare_native_callback(
            self,
            module_base):
        actual_hash = sha256_stream(
            self.ifm_path
        )

        self.log(
            "ifm.dll path=%r"
            % self.ifm_path
        )
        self.log(
            "ifm.dll SHA256=%s"
            % actual_hash
        )

        if (
            actual_hash.lower()
            != EXPECTED_SHA256.lower()
        ):
            raise ProbeError(
                "Unsupported ifm.dll SHA256."
            )

        callback_address = (
            module_base
            + REBUILD_RVA
        )

        actual_prologue = (
            ctypes.string_at(
                callback_address,
                len(
                    EXPECTED_PROLOGUE
                ),
            )
        )

        if (
            actual_prologue
            != EXPECTED_PROLOGUE
        ):
            raise ProbeError(
                "Native Rebuild callback prologue mismatch."
            )

        NativeRebuild = (
            ctypes.WINFUNCTYPE(
                None,
                ctypes.c_void_p,
            )
        )

        self.rebuild = (
            NativeRebuild(
                callback_address
            )
        )

        self.log(
            "callback=%s"
            % hex(
                callback_address
            )
        )
        self.log(
            "NATIVE_GUARDS = PASS"
        )


    def derive_paths(self):
        global MASTER_PATH

        kernel32, module_base = (
            get_loaded_ifm_module()
        )

        self.ifm_path = (
            get_loaded_module_path(
                kernel32,
                module_base,
            )
        )

        tools_dir = os.path.dirname(
            self.ifm_path
        )
        bin_dir = os.path.dirname(
            tools_dir
        )
        game_dir = os.path.dirname(
            bin_dir
        )

        if (
            os.path.normcase(
                os.path.basename(
                    tools_dir
                )
            )
            != os.path.normcase(
                "tools"
            )
        ):
            raise ProbeError(
                "Loaded ifm.dll is not under tools."
            )

        if (
            os.path.normcase(
                os.path.basename(
                    bin_dir
                )
            )
            != os.path.normcase(
                "bin"
            )
        ):
            raise ProbeError(
                "Loaded ifm.dll is not under game\\bin\\tools."
            )

        usermod_dir = os.path.join(
            game_dir,
            "usermod",
        )

        self.master_path = os.path.join(
            usermod_dir,
            "cfg",
            "sfm_defaultanimationgroups.txt",
        )

        if not os.path.isfile(
                self.master_path):
            raise ProbeError(
                "Live Master not found: %s"
                % self.master_path
            )

        MASTER_PATH = (
            self.master_path
        )

        self.master_hash = (
            sha256_stream(
                self.master_path
            )
        )


        self.prepare_native_callback(
            module_base
        )

        return (
            game_dir,
            usermod_dir,
        )


    def assert_master_stable(self):
        current_hash = (
            sha256_stream(
                self.master_path
            )
        )

        if (
            current_hash.lower()
            != self.master_hash.lower()
        ):
            raise ProbeError(
                "Live Master changed during the run."
            )


    def contextualizer_resource_checkpoint(
            self,
            label,
            include_vas=True):
        memory = (
            contextualizer_process_memory_sample()
        )

        vas = {
            "ok": False,
            "min_address": None,
            "max_address": None,
            "free": None,
            "reserve": None,
            "commit": None,
            "largest_free": None,
            "free_regions": None,
            "query_count": 0,
            "elapsed": 0.0,
            "error": None,
        }

        if include_vas:
            self.contextualizer_vas_samples += 1
            vas = (
                contextualizer_virtual_address_sample()
            )

            if vas["ok"]:
                self.contextualizer_vas_successes += 1
            else:
                self.contextualizer_vas_failures += 1

        self.log(
            "CONTEXTUALIZER_RESOURCE_CHECKPOINT label=%s run_elapsed=%.3f "
            "mem_ok=%r working_set=%r peak_working_set=%r pagefile=%r "
            "peak_pagefile=%r private=%r vas_requested=%r vas_ok=%r "
            "min_address=%r max_address=%r mem_free=%r mem_reserve=%r "
            "mem_commit=%r largest_free=%r free_regions=%r "
            "virtual_query_count=%r vas_elapsed=%.4f vas_error=%r"
            % (
                label,
                (
                    time.time()
                    - self.run_started_wall
                    if self.run_started_wall is not None
                    else 0.0
                ),
                memory[
                    "ok"
                ],
                memory[
                    "working_set"
                ],
                memory[
                    "peak_working_set"
                ],
                memory[
                    "pagefile"
                ],
                memory[
                    "peak_pagefile"
                ],
                memory[
                    "private"
                ],
                include_vas,
                vas[
                    "ok"
                ],
                vas[
                    "min_address"
                ],
                vas[
                    "max_address"
                ],
                vas[
                    "free"
                ],
                vas[
                    "reserve"
                ],
                vas[
                    "commit"
                ],
                vas[
                    "largest_free"
                ],
                vas[
                    "free_regions"
                ],
                vas[
                    "query_count"
                ],
                vas[
                    "elapsed"
                ],
                vas[
                    "error"
                ],
            )
        )


    def collect_scope_master_wanted_folds(
            self):
        """
        Collect exact ASCII-folded control-name vocabulary already present in
        the user-selected command scope. Pure strings only.
        """
        wanted = set()
        animation_sets_seen = 0
        controls_seen = 0

        for shot in self.scope_shots:
            for aset in shot.animationSets:
                animation_sets_seen += 1

                for control in arr(
                        aset,
                        "controls"):
                    controls_seen += 1
                    wanted.add(
                        ascii_fold(
                            name(
                                control
                            )
                        )
                    )

        self.log(
            "CONTEXTUALIZER_SCOPE_MASTER_VOCABULARY animation_sets=%d controls=%d unique_folds=%d"
            % (
                animation_sets_seen,
                controls_seen,
                len(
                    wanted
                ),
            )
        )

        return wanted


    def contextualizer_assert_master_stable_for_index_use(
            self,
            phase):
        started = time.time()
        current_hash = sha256_stream(
            self.master_path
        )
        elapsed = (
            time.time()
            - started
        )

        self.master_index_sha_checks += 1
        self.master_index_sha_seconds += elapsed

        if (
            current_hash.lower()
            != self.master_hash.lower()
        ):
            raise ProbeError(
                "Live Master changed before scoped-index %s use."
                % phase
            )


    def contextualizer_validate_master_index_subset(
            self,
            wanted_folds,
            phase):
        self.contextualizer_assert_master_stable_for_index_use(
            phase
        )

        missing = (
            set(
                wanted_folds
            )
            - self.master_index_scope_folds
        )

        if missing:
            raise ProbeError(
                "CONTEXTUALIZER scoped Master index does not cover runtime %s fold(s): %r."
                % (
                    phase,
                    sorted(
                        missing
                    )[:20],
                )
            )

        validate_master_subset_conflicts(
            self.master_index,
            wanted_folds,
        )

        if phase == "GATE":
            self.master_index_gate_validations += 1

        elif phase == "TARGET":
            self.master_index_target_validations += 1

        else:
            raise ProbeError(
                "CONTEXTUALIZER unknown Master-index validation phase: %r."
                % phase
            )


    def contextualizer_should_checkpoint_after_shot(
            self,
            completed_shots):
        total = len(
            self.work
        )

        if completed_shots == 1:
            return True

        if (
            completed_shots
            % CONTEXTUALIZER_PERIODIC_GLOBAL_SHOT_INTERVAL
        ) == 0:
            return True

        last_start = max(
            1,
            total
            - CONTEXTUALIZER_VAS_LAST_SHOTS,
        )

        return bool(
            completed_shots
            >= last_start
        )


    def _record_gate_skip(
            self,
            reason,
            model_name):
        key = (
            to_unicode(reason),
            to_unicode(
                model_name
                if model_name is not None
                else u"<UNRESOLVED_MODEL>"
            ),
        )

        self.gate_skip_model_counts[
            key
        ] = (
            self.gate_skip_model_counts.get(
                key,
                0,
            )
            + 1
        )


    def snapshot_work(self):
        records = []

        shots = list(
            self.scope_shots
        )

        self.total_shots_seen = len(
            shots
        )

        for shot in shots:
            try:
                (
                    start,
                    duration,
                    midpoint,
                ) = self.shot_times(
                    shot
                )
            except Exception as exc:
                self.log(
                    "SKIP SHOT timeframe error ptr=%r error=%r"
                    % (
                        native_ptr(
                            shot
                        ),
                        exc,
                    )
                )
                continue

            shot_ptr = native_ptr(
                shot
            )

            if not shot_ptr:
                continue

            shot_name = to_unicode(
                shot.GetName()
            )

            rows = []
            gm_index = {}
            seen_asets = set()

            for aset in shot.animationSets:
                self.total_sets_seen += 1

                if self.get_game_model(
                        aset) is None:
                    self.total_non_model_skips += 1
                    continue

                self.total_model_backed += 1

                aset_ptr = native_ptr(
                    aset
                )

                if not aset_ptr:
                    raise ProbeError(
                        "Model-backed animation set has no native pointer."
                    )

                if aset_ptr in seen_asets:
                    self.total_duplicate_aset_skips += 1
                    continue

                seen_asets.add(
                    aset_ptr
                )

                game_model = (
                    self.get_game_model(
                        aset
                    )
                )

                root = self.get_root_group(
                    aset
                )

                root_valid = bool(
                    root is not None
                    and native_ptr(
                        root
                    )
                )

                if not root_valid:
                    self.total_root_skips += 1

                model_name = (
                    _gate_get_model_name(
                        game_model
                    )
                )

                header = (
                    _gate_consensus_header(
                        _gate_loose_candidates(
                            self.gate_content_dirs,
                            model_name,
                        ),
                        self.gate_mdl_cache,
                    )
                )

                transform_names = (
                    _gate_nonroot_transform_names(
                        aset
                    )
                )

                override_parent = (
                    _gate_resolve_override_parent(
                        game_model
                    )
                )

                row = {
                    "aset": aset,
                    "aset_ptr": aset_ptr,
                    "aset_name": to_unicode(
                        aset.GetName()
                    ),
                    "game_model": game_model,
                    "game_model_ptr": native_ptr(
                        game_model
                    ),
                    "model_name": model_name,
                    "root_valid": root_valid,
                    "header": header,
                    "transform_names": transform_names,
                    "override_parent": override_parent,
                }

                rows.append(
                    row
                )

                gm_index.setdefault(
                    row["game_model_ptr"],
                    []
                ).append(
                    row
                )

            wanted_folds = set()

            for row in rows:
                for folded in row[
                        "transform_names"]:
                    wanted_folds.add(
                        folded
                    )

            gate_master = None

            if wanted_folds:
                try:
                    self.master_index_gate_opportunities += 1

                    self.contextualizer_validate_master_index_subset(
                        wanted_folds,
                        "GATE",
                    )

                    gate_master = self.master_index

                except Exception as exc:
                    self.log(
                        "ELIGIBILITY_GATE MASTER_INDEX_FAIL_CLOSED shot=%r error=%r"
                        % (
                            shot_name,
                            exc,
                        )
                    )

            targets = []

            for row in rows:
                if not row[
                        "root_valid"]:
                    continue

                model_name = row[
                    "model_name"
                ]
                header = row[
                    "header"
                ]

                if (
                    header[
                        "is_static_prop"
                    ]
                    is True
                ):
                    self.total_gate_static_skips += 1
                    self._record_gate_skip(
                        u"STATIC_PROP",
                        model_name,
                    )
                    continue

                follower = False
                overlap_count = 0
                child_coverage = 0.0
                host_model_name = None

                parent = row[
                    "override_parent"
                ]

                if (
                    parent is not None
                    and typ(parent)
                    == u"DmeGameModel"
                ):
                    parent_ptr = native_ptr(
                        parent
                    )

                    host_rows = [
                        candidate
                        for candidate
                        in gm_index.get(
                            parent_ptr,
                            [],
                        )
                        if candidate[
                            "game_model_ptr"
                        ]
                        != row[
                            "game_model_ptr"
                        ]
                    ]

                    if len(host_rows) == 1:
                        host = host_rows[0]
                        host_model_name = host[
                            "model_name"
                        ]

                        child_model_key = (
                            None
                            if model_name is None
                            else ascii_fold(
                                model_name
                            )
                        )
                        host_model_key = (
                            None
                            if host_model_name is None
                            else ascii_fold(
                                host_model_name
                            )
                        )

                        if (
                            child_model_key
                            and host_model_key
                            and child_model_key
                            != host_model_key
                        ):
                            overlap_count = len(
                                row[
                                    "transform_names"
                                ].intersection(
                                    host[
                                        "transform_names"
                                    ]
                                )
                            )

                            child_count = len(
                                row[
                                    "transform_names"
                                ]
                            )

                            child_coverage = (
                                _gate_ratio(
                                    overlap_count,
                                    child_count,
                                )
                            )

                            follower = bool(
                                overlap_count
                                >= GATE_MIN_SHARED_TRANSFORMS
                                and child_coverage
                                >= GATE_MIN_CHILD_COVERAGE
                            )

                if follower:
                    self.total_gate_follower_skips += 1
                    self._record_gate_skip(
                        u"DIRECT_SKELETAL_FOLLOWER",
                        model_name,
                    )
                    continue

                numbones = header[
                    "numbones"
                ]

                if (
                    numbones is not None
                    and numbones
                    <= GATE_LOW_BONE_CEILING
                ):
                    if gate_master is None:
                        self.total_gate_failclosed_process += 1
                    else:
                        try:
                            (
                                alh_pass,
                                arm,
                                leg,
                                head,
                            ) = _gate_is_alh(
                                row["aset"],
                                gate_master,
                            )
                        except Exception:
                            alh_pass = None

                        if alh_pass is False:
                            self.total_gate_lowbone_skips += 1
                            self._record_gate_skip(
                                u"LOW_BONE_NO_ALH",
                                model_name,
                            )
                            continue

                        if alh_pass is None:
                            self.total_gate_failclosed_process += 1

                elif numbones is None:
                    self.total_gate_failclosed_process += 1

                targets.append({
                    "anim_set": row[
                        "aset"
                    ],
                    "name": row[
                        "aset_name"
                    ],
                    "ptr": row[
                        "aset_ptr"
                    ],
                })

                self.total_targets += 1

            if targets:
                records.append({
                    "shot": shot,
                    "name": shot.GetName(),
                    "ptr": shot_ptr,
                    "start": start,
                    "duration": duration,
                    "midpoint": midpoint,
                    "targets": targets,
                })

        records.sort(
            key=lambda row: row[
                "start"
            ]
        )

        self.section(
            "PRE-REBUILD ELIGIBILITY GATE"
        )
        self.log(
            "scope_mode=%s scoped_shots=%d"
            % (
                self.scope_mode,
                self.total_shots_seen,
            )
        )
        self.log(
            "gate thresholds low_bone<=%d shared>=%d child_coverage>=%.3f"
            % (
                GATE_LOW_BONE_CEILING,
                GATE_MIN_SHARED_TRANSFORMS,
                GATE_MIN_CHILD_COVERAGE,
            )
        )
        self.log(
            "gate skips static=%d follower=%d lowbone_no_alh=%d failclosed_process=%d"
            % (
                self.total_gate_static_skips,
                self.total_gate_follower_skips,
                self.total_gate_lowbone_skips,
                self.total_gate_failclosed_process,
            )
        )

        for key in sorted(
                self.gate_skip_model_counts.keys()):
            self.log(
                "GATE_SKIP reason=%s count=%d model=%s"
                % (
                    key[0],
                    self.gate_skip_model_counts[
                        key
                    ],
                    key[1],
                )
            )

        return records


    def verify_whole_session_expected(
            self,
            label):
        """
        Exhaustively compare the entire current session with session_expected
        WITHOUT materializing a second whole-session fingerprint dictionary.

        The existing compact identity/order census first proves that the live
        shot/aset population and order still exactly match the accepted
        baseline. Then each current animation set is fingerprinted, compared,
        and released one at a time.

        session_expected retains the typed production SHA-256 digest baseline.
        isolation_fingerprint() itself is unchanged and is still constructed
        fresh before hashing.
        """
        before_memory = (
            contextualizer_process_memory_sample()
        )

        started = time.time()

        current_identity = (
            capture_session_identity_census()
        )

        if (
            current_identity
            != self.session_identity_expected
        ):
            raise ProbeError(
                "CONTEXTUALIZER %s whole-session compact identity/order census changed."
                % label
            )

        fingerprint_count = 0
        mismatches = []

        for shot in list(
                sfmApp.GetShots()):
            shot_ptr = (
                native_ptr(
                    shot
                )
            )

            for aset in shot.animationSets:
                aset_ptr = (
                    native_ptr(
                        aset
                    )
                )

                key = (
                    shot_ptr,
                    aset_ptr,
                )

                if key not in self.session_expected:
                    raise ProbeError(
                        "CONTEXTUALIZER %s live animation-set key absent from accepted "
                        "session baseline: %r."
                        % (
                            label,
                            key,
                        )
                    )

                current_fp = (
                    isolation_fingerprint(
                        aset
                    )
                )
                current_digest = (
                    isolation_fingerprint_digest(
                        current_fp
                    )
                )

                fingerprint_count += 1

                if (
                    current_digest
                    != self.session_expected[
                        key
                    ]
                ):
                    if len(
                            mismatches) < 20:
                        mismatches.append(
                            key
                        )

                # No whole-session expanded 'current' collection exists.
                # current_fp and current_digest are replaced on the next
                # iteration and become unreachable under normal refcounting.

        if (
            fingerprint_count
            != len(
                self.session_expected
            )
        ):
            raise ProbeError(
                "CONTEXTUALIZER %s streaming whole-session fingerprint count mismatch: "
                "current=%d expected=%d."
                % (
                    label,
                    fingerprint_count,
                    len(
                        self.session_expected
                    ),
                )
            )

        elapsed = (
            time.time()
            - started
        )

        after_memory = (
            contextualizer_process_memory_sample()
        )

        self.contextualizer_global_capture_count += 1

        private_delta = None

        if (
            before_memory[
                "ok"
            ]
            and after_memory[
                "ok"
            ]
        ):
            private_delta = (
                after_memory[
                    "private"
                ]
                - before_memory[
                    "private"
                ]
            )

            if (
                self.contextualizer_global_capture_max_private_delta
                is None
                or private_delta
                > self.contextualizer_global_capture_max_private_delta
            ):
                self.contextualizer_global_capture_max_private_delta = (
                    private_delta
                )

        self.log(
            "CONTEXTUALIZER_STREAMING_GLOBAL_DEEP_VERIFY label=%s fingerprints=%d "
            "elapsed_seconds=%.3f before_private=%r after_private=%r "
            "delta_private=%r before_working=%r after_working=%r"
            % (
                label,
                fingerprint_count,
                elapsed,
                before_memory[
                    "private"
                ],
                after_memory[
                    "private"
                ],
                private_delta,
                before_memory[
                    "working_set"
                ],
                after_memory[
                    "working_set"
                ],
            )
        )

        if mismatches:
            raise ProbeError(
                "CONTEXTUALIZER %s whole-session isolation failure: %r"
                % (
                    label,
                    mismatches,
                )
            )

        return elapsed


    def verify_session_isolation_periodic(
            self,
            completed_shots):
        self.section(
            "CONTEXTUALIZER PERIODIC WHOLE-SESSION DEEP ISOLATION"
        )

        self.contextualizer_resource_checkpoint(
            "BEFORE_PERIODIC_GLOBAL_%d"
            % completed_shots,
            True,
        )

        elapsed = (
            self.verify_whole_session_expected(
                "PERIODIC_AFTER_SHOT_%d"
                % completed_shots
            )
        )

        # verify_whole_session_expected() has returned here. CONTEXTUALIZER never
        # materialized a whole-session expanded 'current' dictionary.
        self.contextualizer_resource_checkpoint(
            "AFTER_PERIODIC_GLOBAL_%d"
            % completed_shots,
            True,
        )

        self.layer_periodic_global_checks += 1

        self.log(
            "CONTEXTUALIZER_PERIODIC_WHOLE_SESSION_ISOLATION = PASS completed_shots=%d elapsed_seconds=%.3f"
            % (
                completed_shots,
                elapsed,
            )
        )


    def verify_session_isolation_end(
            self):
        self.section(
            "CONTEXTUALIZER END-OF-RUN WHOLE-SESSION DEEP ISOLATION"
        )

        self.contextualizer_resource_checkpoint(
            "BEFORE_END_GLOBAL",
            True,
        )

        elapsed = (
            self.verify_whole_session_expected(
                "END_OF_RUN"
            )
        )

        self.contextualizer_resource_checkpoint(
            "AFTER_END_GLOBAL",
            True,
        )

        self.layer_end_global_checks += 1

        self.log(
            "CONTEXTUALIZER_END_OF_RUN_WHOLE_SESSION_ISOLATION = PASS elapsed_seconds=%.3f"
            % elapsed
        )


    def verify_session_identity_layer(
            self,
            completed_shots):
        started = time.time()

        current = (
            capture_session_identity_census()
        )

        elapsed = (
            time.time()
            - started
        )

        if current != self.session_identity_expected:
            raise ProbeError(
                "CONTEXTUALIZER compact whole-session identity/order census changed after shot %d."
                % completed_shots
            )

        self.layer_identity_checks += 1

        self.log(
            "CONTEXTUALIZER_COMPACT_SESSION_IDENTITY = PASS completed_shots=%d shots=%d elapsed_seconds=%.3f"
            % (
                completed_shots,
                len(current),
                elapsed,
            )
        )


    def verify_current_shot_peers(
            self,
            shot_record,
            processed_target):
        """
        Deeply verify every animation set in the active shot EXCEPT the
        processed target itself.

        No follower/overlap heuristic is used here. The peer boundary is the
        complete current shot.
        """
        shot = shot_record[
            "shot"
        ]

        shot_ptr = shot_record[
            "ptr"
        ]

        processed_ptr = processed_target[
            "ptr"
        ]

        at_head = (
            sfmApp.GetShotAtCurrentTime()
        )

        if (
            at_head is None
            or native_ptr(
                at_head
            )
            != shot_ptr
        ):
            raise ProbeError(
                "CONTEXTUALIZER peer verifier lost expected current-shot context."
            )

        started = time.time()
        peer_count = 0
        processed_present = False
        mismatches = []

        for aset in shot.animationSets:
            aset_ptr = (
                native_ptr(
                    aset
                )
            )

            key = (
                shot_ptr,
                aset_ptr,
            )

            if key not in self.session_expected:
                raise ProbeError(
                    "CONTEXTUALIZER current-shot peer key absent from startup session baseline: %r."
                    % (
                        key,
                    )
                )

            if aset_ptr == processed_ptr:
                processed_present = True
                continue

            peer_count += 1

            current_fp = (
                isolation_fingerprint(
                    aset
                )
            )
            current_digest = (
                isolation_fingerprint_digest(
                    current_fp
                )
            )

            if (
                current_digest
                != self.session_expected[
                    key
                ]
            ):
                mismatches.append(
                    (
                        to_unicode(
                            aset.GetName()
                        ),
                        key,
                    )
                )

        if not processed_present:
            raise ProbeError(
                "CONTEXTUALIZER processed target no longer present in current shot."
            )

        if mismatches:
            raise ProbeError(
                "CONTEXTUALIZER current-shot peer isolation failure after target %r: %r"
                % (
                    to_unicode(
                        processed_target[
                            "name"
                        ]
                    ),
                    mismatches[:20],
                )
            )

        elapsed = (
            time.time()
            - started
        )

        self.layer_peer_checks += 1
        self.layer_peer_fingerprints += (
            peer_count
        )

        self.log(
            "CONTEXTUALIZER_CURRENT_SHOT_PEER_ISOLATION = PASS shot=%r target=%r peers=%d elapsed_seconds=%.3f"
            % (
                to_unicode(
                    shot_record[
                        "name"
                    ]
                ),
                to_unicode(
                    processed_target[
                        "name"
                    ]
                ),
                peer_count,
                elapsed,
            )
        )



    def preflight_reconciliation_plan(
            self,
            pre,
            post,
            master,
            exact_pair):
        classified = classify_production(
            pre,
            post,
            master,
        )

        for key in self.class_totals.keys():
            self.class_totals[
                key
            ] += len(
                classified.get(
                    key,
                    [],
                )
            )

        rig_source = classified[
            "pre_source"
        ]

        rig_rows_unordered = []

        for row in (
            classified[
                "rig_losses"
            ]
            + classified[
                "parent_collapses"
            ]
            + classified[
                "master_unknown_unknown"
            ]
        ):
            rig_rows_unordered.append({
                "name": row[
                    "name"
                ],
                "relative_path": row[
                    "pre_path"
                ],
            })

        for row in classified[
                "pre_hidden_master_active"]:
            rig_rows_unordered.append({
                "name": row[
                    "name"
                ],
                "relative_path": row[
                    "master_destination"
                ],
            })

        master_rows_unordered = []

        for row in classified[
                "master_stranded"]:
            master_rows_unordered.append({
                "name": row[
                    "name"
                ],
                "relative_path": row[
                    "master_destination"
                ],
            })

        # Validate all ordering policy before any reconciliation mutation.
        try:
            (
                rig_rows,
                unused_rig_tree,
                rig_order_authority,
            ) = order_candidate_rows_by_policy(
                rig_rows_unordered,
                master,
                rig_source,
            )

            (
                master_rows,
                unused_master_tree,
                master_order_authority,
            ) = order_candidate_rows_by_policy(
                master_rows_unordered,
                master,
                post,
            )
            mixed_paths = sorted([
                to_unicode(path)
                for path, authority
                in rig_order_authority.items()
                if authority
                == "MIXED_MASTER_KNOWN_UNKNOWN_PRE_TOTAL_ORDER"
            ])

            if mixed_paths:
                self.production_mixed_direct_by_target[
                    exact_pair
                ] = tuple(mixed_paths)

            self.log(
                "PRODUCTION_MIXED_DIRECT_ORDER_PATHS target=%r paths=%r"
                % (
                    exact_pair,
                    mixed_paths,
                )
            )

        except Exception as exc:
            return {
                "status": "NATIVE_POST_FALLBACK",
                "reason": (
                    "Ordering policy unresolved before mutation: %s"
                    % str(exc)
                ),
                "classified": classified,
                "rig_rows": [],
                "master_rows": [],
                "rig_source": rig_source,
            }

        return {
            "status": "AUTHORIZED",
            "reason": None,
            "classified": classified,
            "rig_rows": rig_rows,
            "master_rows": master_rows,
            "rig_source": rig_source,
        }


    def validate_reconciliation(
            self,
            pre,
            post,
            after,
            classified,
            rig_rows,
            master_rows,
            rig_source,
            master,
            rig_build,
            master_build):
        candidate_names = set([
            to_unicode(
                row[
                    "name"
                ]
            )
            for row in (
                rig_rows
                + master_rows
            )
        ])

        candidate_failures = []

        for row in rig_rows:
            expected = (
                to_unicode(
                    RIG_RECON_ROOT
                )
                + u"/"
                + to_unicode(
                    row[
                        "relative_path"
                    ]
                )
            )

            actual = one_membership(
                after,
                row[
                    "name"
                ],
            )

            meta = (
                None
                if actual is None
                else after[
                    "groups"
                ].get(
                    actual
                )
            )

            if (
                actual != expected
                or meta is None
                or not bool(
                    meta[
                        "effective_visible"
                    ]
                )
            ):
                candidate_failures.append(
                    (
                        row[
                            "name"
                        ],
                        expected,
                        actual,
                    )
                )

        for row in master_rows:
            expected = (
                to_unicode(
                    MASTER_RECON_ROOT
                )
                + u"/"
                + to_unicode(
                    row[
                        "relative_path"
                    ]
                )
            )

            actual = one_membership(
                after,
                row[
                    "name"
                ],
            )

            meta = (
                None
                if actual is None
                else after[
                    "groups"
                ].get(
                    actual
                )
            )

            if (
                actual != expected
                or meta is None
                or not bool(
                    meta[
                        "effective_visible"
                    ]
                )
            ):
                candidate_failures.append(
                    (
                        row[
                            "name"
                        ],
                        expected,
                        actual,
                    )
                )

        non_candidate_changes = []

        for control_name in post[
            "control_names_in_animation_set_order"
        ]:
            control_name = to_unicode(
                control_name
            )

            if control_name in candidate_names:
                continue

            before = list(
                post[
                    "memberships"
                ].get(
                    control_name,
                    [],
                )
            )

            actual = list(
                after[
                    "memberships"
                ].get(
                    control_name,
                    [],
                )
            )

            if before != actual:
                non_candidate_changes.append(
                    (
                        control_name,
                        before,
                        actual,
                    )
                )

        ownership_unchanged = bool(
            after[
                "owned_control_name_set"
            ]
            == post[
                "owned_control_name_set"
            ]
        )

        hidden_unchanged = bool(
            after[
                "hidden_groups"
            ]
            == post[
                "hidden_groups"
            ]
        )

        duplicates_clean = bool(
            not after[
                "duplicate_control_names"
            ]
            and not after[
                "duplicate_sibling_groups"
            ]
            and not after[
                "duplicate_direct_controls"
            ]
            and not after[
                "duplicate_memberships"
            ]
        )

        presentation_failures = []

        for build, source, wrapper in (
            (
                rig_build,
                rig_source,
                RIG_RECON_ROOT,
            ),
            (
                master_build,
                post,
                MASTER_RECON_ROOT,
            ),
        ):
            if build is None:
                continue

            for created in build[
                "created"
            ]:
                source_path = to_unicode(
                    created[
                        "source_path"
                    ]
                )
                final_path = (
                    to_unicode(
                        wrapper
                    )
                    + u"/"
                    + source_path
                )

                source_meta = source[
                    "groups"
                ].get(
                    source_path
                )
                actual_meta = after[
                    "groups"
                ].get(
                    final_path
                )

                if (
                    source_meta is None
                    or actual_meta is None
                ):
                    presentation_failures.append(
                        final_path
                    )
                    continue

                if not (
                    list(
                        source_meta[
                            "group_color"
                        ]
                    )
                    == list(
                        actual_meta[
                            "group_color"
                        ]
                    )
                    and source_meta[
                        "selectable"
                    ]
                    == actual_meta[
                        "selectable"
                    ]
                    and source_meta[
                        "snappable"
                    ]
                    == actual_meta[
                        "snappable"
                    ]
                    and bool(
                        actual_meta[
                            "effective_visible"
                        ]
                    )
                ):
                    presentation_failures.append(
                        final_path
                    )

        rig_order = (
            policy_ordering_comparison_for_wrapper(
                rig_source,
                after,
                rig_rows,
                master,
                RIG_RECON_ROOT,
            )
            if rig_rows
            else {
                "pass": True,
            }
        )

        master_order = (
            policy_ordering_comparison_for_wrapper(
                post,
                after,
                master_rows,
                master,
                MASTER_RECON_ROOT,
            )
            if master_rows
            else {
                "pass": True,
            }
        )

        passed = bool(
            not candidate_failures
            and not non_candidate_changes
            and ownership_unchanged
            and hidden_unchanged
            and duplicates_clean
            and not presentation_failures
            and rig_order[
                "pass"
            ]
            and master_order[
                "pass"
            ]
        )

        self.log(
            "candidate placement failures=%d"
            % len(
                candidate_failures
            )
        )
        self.log(
            "non-candidate membership changes=%d"
            % len(
                non_candidate_changes
            )
        )
        self.log(
            "ownership unchanged=%r"
            % ownership_unchanged
        )
        self.log(
            "hiddenGroups unchanged=%r"
            % hidden_unchanged
        )
        self.log(
            "duplicate invariants clean=%r"
            % duplicates_clean
        )
        self.log(
            "presentation metadata failures=%d"
            % len(
                presentation_failures
            )
        )
        self.log(
            "rig ordering pass=%r"
            % rig_order[
                "pass"
            ]
        )
        self.log(
            "master ordering pass=%r"
            % master_order[
                "pass"
            ]
        )

        if not passed:
            raise ProbeError(
                "Post-reconciliation validation failed."
            )

        self.log(
            "TARGET_RECONCILIATION_VALIDATION = PASS"
        )


    def run_target_transaction(
            self,
            shot_record,
            target):
        target_started_wall = time.time()

        self.telemetry_target_sequence += 1
        telemetry_target_sequence = (
            self.telemetry_target_sequence
        )

        shot = shot_record[
            "shot"
        ]
        aset = target[
            "anim_set"
        ]
        exact_pair = (
            to_unicode(shot.GetName()),
            to_unicode(aset.GetName()),
        )
        terminal_status = None

        aset_ptr = native_ptr(
            aset
        )

        if (
            aset_ptr
            != target[
                "ptr"
            ]
        ):
            raise ProbeError(
                "Animation-set pointer changed since inventory."
            )

        if self.get_game_model(
                aset) is None:
            raise ProbeError(
                "Animation set lost model backing."
            )

        root = self.get_root_group(
            aset
        )

        if (
            root is None
            or not native_ptr(
                root
            )
        ):
            self.total_root_skips += 1
            raise ProbeError(
                "Inventoried model-backed target lost its root group at transaction time: %r."
                % (exact_pair,)
            )

        self.assert_master_stable()

        pre_capture_ok = True
        pre_capture_error = None
        pre = None
        pre_rig = None

        try:
            pre_rig = discover_rig_context(
                shot,
                aset,
            )
            pre = capture_snapshot_explicit(
                shot,
                aset,
                "PRE",
                pre_rig,
            )
        except Exception as exc:
            pre_capture_ok = False
            pre_capture_error = str(
                exc
            )

        if pre_capture_ok:
            self.log(
                "PRE rig status=%s controls=%d groups=%d owned=%d"
                % (
                    pre[
                        "rig_status"
                    ],
                    pre[
                        "control_count"
                    ],
                    pre[
                        "group_count"
                    ],
                    len(
                        pre[
                            "owned_control_name_set"
                        ]
                    ),
                )
            )
        else:
            self.log(
                "PRE semantic capture unsupported; native-only fallback: %s"
                % pre_capture_error
            )
        if pre_capture_ok:
            self.log(
                "PRODUCTION_PRE_CAPTURE_GATE = PASS target=%r signature=%r"
                % (
                    exact_pair,
                    (
                        pre["control_count"],
                        pre["group_count"],
                        len(pre["owned_control_name_set"]),
                    ),
                )
            )

        dm = getattr(
            vs,
            "g_pDataModel",
            None
        )

        if dm is None:
            raise ProbeError(
                "vs.g_pDataModel unavailable."
            )

        if (
            not hasattr(
                dm,
                "IsUndoEnabled",
            )
            or not hasattr(
                dm,
                "SetUndoEnabled",
            )
        ):
            raise ProbeError(
                "Required undo controls unavailable."
            )

        undo_prior = bool(
            dm.IsUndoEnabled()
        )

        undo_count_before, undo_desc_before = (
            read_undo_ledger(
                dm
            )
        )

        self.log(
            "UNDO_ENABLED_BEFORE=%r count=%r desc=%r"
            % (
                undo_prior,
                undo_count_before,
                undo_desc_before,
            )
        )

        undo_restored = False

        try:
            dm.SetUndoEnabled(
                False
            )

            if bool(
                    dm.IsUndoEnabled()):
                raise ProbeError(
                    "Could not disable undo."
                )

            self.log(
                "TARGET_UNDO_DISABLE_GATE = PASS"
            )

            self.telemetry_native_attempts += 1
            native_attempt = (
                self.telemetry_native_attempts
            )

            pre_native_memory = (
                contextualizer_process_memory_sample()
            )

            self.log(
                "CONTEXTUALIZER_TELEMETRY phase=PRE_NATIVE target_seq=%d native_attempt=%d "
                "shot=%r target=%r run_elapsed=%.3f target_elapsed=%.3f "
                "mem_ok=%r working_set=%r peak_working_set=%r pagefile=%r "
                "peak_pagefile=%r private=%r"
                % (
                    telemetry_target_sequence,
                    native_attempt,
                    to_unicode(
                        shot.GetName()
                    ),
                    to_unicode(
                        aset.GetName()
                    ),
                    (
                        time.time()
                        - self.run_started_wall
                        if self.run_started_wall is not None
                        else 0.0
                    ),
                    (
                        time.time()
                        - target_started_wall
                    ),
                    pre_native_memory[
                        "ok"
                    ],
                    pre_native_memory[
                        "working_set"
                    ],
                    pre_native_memory[
                        "peak_working_set"
                    ],
                    pre_native_memory[
                        "pagefile"
                    ],
                    pre_native_memory[
                        "peak_pagefile"
                    ],
                    pre_native_memory[
                        "private"
                    ],
                )
            )

            self.rebuild(
                ctypes.c_void_p(
                    aset_ptr
                )
            )

            self.total_native_rebuilt += 1

            self.log(
                "NATIVE_REBUILD_RETURNED = PASS"
            )

            if not pre_capture_ok:
                self.total_native_only += 1
                raise NativePostFallback(
                    "NATIVE_POST_ONLY_PRE_CAPTURE_UNSUPPORTED"
                )

            post_rig = discover_rig_context(
                shot,
                aset,
            )

            post = capture_snapshot_explicit(
                shot,
                aset,
                "NATIVE_POST",
                post_rig,
            )

            if (
                pre[
                    "control_names_in_animation_set_order"
                ]
                != post[
                    "control_names_in_animation_set_order"
                ]
            ):
                raise ProbeError(
                    "Animation-set control order changed across native Rebuild."
                )

            if (
                pre[
                    "rig_status"
                ]
                != "SUPPORTED_ACTIVE_RIG"
            ):
                if pre[
                        "rig_status"
                        ] == "UNRIGGED":
                    self.total_unrigged += 1
                else:
                    self.total_ambiguous_rig += 1

                self.total_native_only += 1
                raise NativePostFallback(
                    "NATIVE_POST_ONLY_%s"
                    % pre[
                        "rig_status"
                    ]
                )

            self.total_supported_active_rig += 1

            if (
                post[
                    "rig_status"
                ]
                != "SUPPORTED_ACTIVE_RIG"
                or post[
                    "rig_handle"
                ]
                != pre[
                    "rig_handle"
                ]
            ):
                raise ProbeError(
                    "Supported active rig identity changed across native Rebuild."
                )

            if (
                post[
                    "owned_control_name_set"
                ]
                != pre[
                    "owned_control_name_set"
                ]
            ):
                raise ProbeError(
                    "Rig-owned control-name set changed across native Rebuild."
                )

            if (
                post[
                    "hidden_groups"
                ]
                != pre[
                    "hidden_groups"
                ]
            ):
                raise ProbeError(
                    "hiddenGroups changed across native Rebuild."
                )

            if (
                post[
                    "duplicate_control_names"
                ]
                or post[
                    "duplicate_sibling_groups"
                ]
                or post[
                    "duplicate_direct_controls"
                ]
                or post[
                    "duplicate_memberships"
                ]
            ):
                self.total_native_only += 1
                self.total_policy_fallback += 1
                raise NativePostFallback(
                    "NATIVE_POST_ONLY_DUPLICATE_SEMANTICS"
                )

            wanted_folds = set([
                ascii_fold(
                    control_name
                )
                for control_name
                in post[
                    "control_names_in_animation_set_order"
                ]
            ])

            self.master_index_target_opportunities += 1

            self.contextualizer_validate_master_index_subset(
                wanted_folds,
                "TARGET",
            )

            master = self.master_index

            plan = self.preflight_reconciliation_plan(
                pre,
                post,
                master,
                exact_pair,
            )

            classified = plan[
                "classified"
            ]

            self.log(
                "CLASS_COUNTS pre_hidden_master_active=%d rig_losses=%d master_stranded=%d "
                "parent_collapses=%d master_normalizations=%d "
                "strong_unknown=%d weak_unknown=%d ambiguous_losses=%d "
                "unresolved=%d"
                % (
                    len(
                        classified[
                            "pre_hidden_master_active"
                        ]
                    ),
                    len(
                        classified[
                            "rig_losses"
                        ]
                    ),
                    len(
                        classified[
                            "master_stranded"
                        ]
                    ),
                    len(
                        classified[
                            "parent_collapses"
                        ]
                    ),
                    len(
                        classified[
                            "master_normalizations"
                        ]
                    ),
                    len(
                        classified[
                            "master_unknown_unknown"
                        ]
                    ),
                    len(
                        classified[
                            "weak_unknown_diagnostics"
                        ]
                    ),
                    len(
                        classified[
                            "ambiguous_losses"
                        ]
                    ),
                    len(
                        classified[
                            "unresolved_owned_drift"
                        ]
                    ),
                )
            )

            if (
                plan[
                    "status"
                ]
                != "AUTHORIZED"
            ):
                self.total_native_only += 1
                self.total_policy_fallback += 1

                self.log(
                    "fallback reason=%s"
                    % plan[
                        "reason"
                    ]
                )

                raise NativePostFallback(
                    "NATIVE_POST_POLICY_FALLBACK"
                )

            rig_rows = plan[
                "rig_rows"
            ]
            master_rows = plan[
                "master_rows"
            ]

            # A supported active rig still enters the generic presentation
            # planner even when classifier repair rows are empty. Model-side
            # Finger/Carpal/Toe translation, helper accessibility, metadata,
            # and current-Master ordering are presentation policy independent
            # of whether rig-owned drift was detected.
            if (
                not rig_rows
                and not master_rows
            ):
                self.log(
                    "PRODUCTION_CLASSIFIER_REPAIR_ROWS = ZERO; GENERIC_PRESENTATION_PLANNER_STILL_REQUIRED"
                )

            # Native Rebuild should remove prior contextual scaffolding.
            root = self.get_root_group(
                aset
            )

            if (
                find_direct_child(
                    root,
                    RIG_RECON_ROOT,
                )
                is not None
                or find_direct_child(
                    root,
                    MASTER_RECON_ROOT,
                )
                is not None
            ):
                self.total_native_only += 1
                self.total_policy_fallback += 1
                raise NativePostFallback(
                    "NATIVE_POST_WRAPPER_SURVIVED"
                )

            live_controls = (
                live_control_map(
                    aset
                )
            )
            actual_signature = (
                len(classified["pre_hidden_master_active"]),
                len(classified["rig_losses"]),
                len(classified["master_stranded"]),
                len(classified["parent_collapses"]),
                len(classified["master_normalizations"]),
                len(classified["master_unknown_unknown"]),
                len(classified["weak_unknown_diagnostics"]),
                len(classified["ambiguous_losses"]),
                len(classified["unresolved_owned_drift"]),
            )

            self.log(
                "PRODUCTION_CLASS_SIGNATURE target=%r signature=%r"
                % (exact_pair, actual_signature)
            )

            if plan.get("status") != "AUTHORIZED":
                raise ProbeError(
                    "Production requires authorized plan for %r; status=%r reason=%r."
                    % (
                        exact_pair,
                        plan.get("status"),
                        plan.get("reason"),
                    )
                )

            uniformity_plan = derive_generic_uniformity_plan(
                pre,
                post,
                master,
                plan,
            )

            self.log(
                "PRODUCTION_GENERIC_POLICY has_RigArms=%r has_RigLegs=%r "
                "authorized_rig=%d authorized_master=%d strong_unknown=%d"
                % (
                    uniformity_plan["has_rigarms"],
                    uniformity_plan["has_riglegs"],
                    uniformity_plan["authorized_rig_count"],
                    uniformity_plan["authorized_master_count"],
                    uniformity_plan["strong_unknown_count"],
                )
            )
            self.log(
                "PRODUCTION_GENERIC_MODEL_TRANSLATIONS=%r"
                % [
                    (
                        path,
                        len(names),
                        list(names),
                    )
                    for path, names
                    in sorted(
                        uniformity_plan["model_translations"].items()
                    )
                ]
            )
            self.log(
                "PRODUCTION_GENERIC_RIG_DESTINATIONS=%r"
                % sorted(
                    uniformity_plan["rig_destinations"].items()
                )
            )
            self.log(
                "PRODUCTION_GENERIC_RIG_DESTINATION_AUTHORITIES=%r"
                % sorted(
                    uniformity_plan[
                        "rig_destination_sources"
                    ].items()
                )
            )
            self.log(
                "PRODUCTION_GENERIC_UNDERSPECIFIED_DESTINATIONS=%r"
                % uniformity_plan[
                    "underspecified"
                ]
            )
            self.log(
                "PRODUCTION_GENERIC_MASTER_STRANDED_DESTINATIONS=%r"
                % sorted(
                    uniformity_plan[
                        "master_destinations"
                    ].items()
                )
            )
            self.log(
                "PRODUCTION_GENERIC_MASTER_STRANDED_AUTHORITIES=%r"
                % sorted(
                    uniformity_plan[
                        "master_destination_sources"
                    ].items()
                )
            )
            self.log(
                "PRODUCTION_GENERIC_UNACCOUNTED_MASTER_ROWS=%r"
                % uniformity_plan[
                    "unaccounted_master_rows"
                ]
            )
            self.log(
                "PRODUCTION_GENERIC_RIG_TOE_PROMOTIONS=%r"
                % sorted(
                    uniformity_plan["rig_toe_promotions"].items()
                )
            )
            for (
                    promoted_name,
                    promoted_path
                    ) in uniformity_plan[
                        "rig_toe_promotions"
                        ].items():
                if promoted_path not in (
                        u"RigLegs/LeftLeg/LeftToes",
                        u"RigLegs/RightLeg/RightToes"):
                    raise ProbeError(
                        "PRODUCTION invalid generic Toe promotion: %r -> %r."
                        % (
                            promoted_name,
                            promoted_path,
                        )
                    )
            self.log(
                "PRODUCTION_GENERIC_KEEP_NATIVE=%r"
                % uniformity_plan["keep_native"]
            )

            if uniformity_plan[
                    "underspecified"
                    ]:
                raise ProbeError(
                    "Production generic planner left side-resolvable rig controls at broad roots: %r."
                    % uniformity_plan[
                        "underspecified"
                    ][:30]
                )

            if uniformity_plan[
                    "unaccounted_master_rows"
                    ]:
                raise ProbeError(
                    "Production generic planner could not resolve authorized Master-stranded rows: %r."
                    % uniformity_plan[
                        "unaccounted_master_rows"
                    ][:30]
                )
            self.production_supported_plan_pairs.add(
                exact_pair
            )
            self.production_policy_plan_passes += 1

            self.log(
                "PRODUCTION_GENERIC_POLICY_PLAN_FOR_TARGET = PASS"
            )

            composer_result = production_generic_composer(
                root,
                pre,
                post,
                master,
                shot,
                aset,
                plan,
                uniformity_plan,
            )

            self.log(
                "PRODUCTION_GENERIC_COMPOSER_RESULT target=%r desired=%d moved=%d "
                "already_correct=%d created_paths=%r toe_translation=%r"
                % (
                    exact_pair,
                    composer_result[
                        "desired_count"
                    ],
                    composer_result[
                        "moved_count"
                    ],
                    composer_result[
                        "already_correct_count"
                    ],
                    composer_result[
                        "created_paths"
                    ],
                    composer_result[
                        "toe_translation"
                    ],
                )
            )
            self.log(
                "PRODUCTION_GENERIC_COMPOSER_ROOT_ORDER target=%r order=%r"
                % (
                    exact_pair,
                    composer_result[
                        "root_order"
                    ],
                )
            )

            destination_order_rows = composer_result[
                "destination_direct_order_authorities"
            ]
            self.production_destination_order_cohort_count += len(
                destination_order_rows
            )
            self.log(
                "PRODUCTION_DESTINATION_DIRECT_ORDER_AUTHORITIES target=%r rows=%r"
                % (
                    exact_pair,
                    destination_order_rows,
                )
            )

            self.production_composer_pairs.add(
                exact_pair
            )
            self.production_composer_passes += 1
            self.total_reconciled += 1

            self.log(
                "MASTER_SELECTABLE_RAW_VS_API=%r"
                % composer_result.get(
                    "master_selectability_rows",
                    [],
                )
            )
            self.log(
                "RAW_MASTER_SELECTABILITY_VALIDATION_FOR_TARGET = PASS"
            )
            self.log(
                "PRODUCTION_GENERIC_COMPOSER_FOR_TARGET = PASS"
            )

            raise ContextualCompositionSuccess(
                "RECONCILED"
            )

        except ContextualCompositionSuccess as result:
            terminal_status = str(
                result
            )
            self.log(
                "TARGET_CONTEXTUAL_RESULT = %s"
                % terminal_status
            )

        except NativePostFallback as fallback:
            terminal_status = str(
                fallback
            )
            self.log(
                "TARGET_CONTEXTUAL_RESULT = %s"
                % terminal_status
            )

        finally:
            try:
                dm.SetUndoEnabled(
                    undo_prior
                )

                undo_restored = bool(
                    dm.IsUndoEnabled()
                    == undo_prior
                )
            except Exception:
                undo_restored = False

            self.log(
                "TARGET_UNDO_RESTORE_GATE = %s"
                % (
                    "PASS"
                    if undo_restored
                    else "FAIL"
                )
            )

            if not undo_restored:
                raise ProbeError(
                    "Undo-enabled state failed to restore."
                )

            undo_count_after, undo_desc_after = (
                read_undo_ledger(
                    dm
                )
            )

            if (
                undo_count_before is not None
                and undo_count_after is not None
            ):
                undo_delta = (
                    undo_count_after
                    - undo_count_before
                )
            else:
                undo_delta = None

            ledger_pass = bool(
                undo_delta == 0
                and undo_desc_after
                == undo_desc_before
            )

            self.log(
                "TARGET_UNDO_ITEM_DELTA=%r"
                % undo_delta
            )
            self.log(
                "TARGET_ZERO_UNDO_LEDGER_DELTA = %s"
                % (
                    "PASS"
                    if ledger_pass
                    else "FAIL"
                )
            )

            if not ledger_pass:
                raise ProbeError(
                    "Target transaction changed the existing undo ledger."
                )

        if terminal_status is None:
            raise ProbeError(
                "Production target did not reach an authorized terminal state: %r."
                % (exact_pair,)
            )
        if exact_pair in self.production_terminal_results:
            raise ProbeError(
                "Production target reached terminal accounting twice: %r."
                % (exact_pair,)
            )

        self.production_terminal_results[
            exact_pair
        ] = terminal_status

        self.log(
            "PRODUCTION_TARGET_TERMINAL_STATE = PASS target=%r state=%s"
            % (
                exact_pair,
                terminal_status,
            )
        )

        self.assert_master_stable()

        self.log(
            "TARGET_TRANSACTION_COMPLETE_WITH_UNDO_RESTORED = PASS"
        )

        key = (
            shot_record[
                "ptr"
            ],
            target[
                "ptr"
            ],
        )

        # CONTEXTUALIZER layered isolation:
        # capture the processed target directly, then deeply verify every
        # other animation set in the current shot against the production digest expected state.
        target_fingerprint = (
            isolation_fingerprint(
                aset
            )
        )

        if not target_fingerprint:
            raise ProbeError(
                "Processed target direct isolation fingerprint unavailable."
            )

        # CONTEXTUALIZER retention ablation:
        # execute the exact same fresh terminal semantic capture, but do not
        # retain its rich nested payload after successful construction.
        #
        # The prior rich dictionary values had no downstream consumer; final
        # accounting consumed only one successful capture per terminal target.
        semantic_now = semantic_target_fingerprint(
            shot,
            aset,
        )

        if semantic_now is None:
            raise ProbeError(
                "Fresh terminal semantic fingerprint capture returned None."
            )

        self.production_final_semantic_capture_pairs.add(
            exact_pair
        )

        self.log(
            "PRODUCTION_FINAL_SEMANTIC_FINGERPRINT_CAPTURE = PASS "
            "target=%r retained_payload=False"
            % (exact_pair,)
        )

        # Drop the local payload immediately after the successful capture is
        # evidenced. This is the sole CONTEXTUALIZER resource ablation.
        del semantic_now

        target_digest = (
            isolation_fingerprint_digest(
                target_fingerprint
            )
        )

        self.session_expected[
            key
        ] = target_digest

        self.log(
            "CONTEXTUALIZER_DIRECT_TARGET_ISOLATION_FINGERPRINT = PASS "
            "target=%r retained_expected=digest32"
            % (exact_pair,)
        )

        self.verify_current_shot_peers(
            shot_record,
            target,
        )

        self.telemetry_completed_targets += 1

        end_memory = (
            contextualizer_process_memory_sample()
        )

        self.log(
            "CONTEXTUALIZER_TELEMETRY phase=TARGET_END target_seq=%d native_attempt=%d "
            "shot=%r target=%r run_elapsed=%.3f target_elapsed=%.3f "
            "completed_targets=%d mem_ok=%r working_set=%r "
            "peak_working_set=%r pagefile=%r peak_pagefile=%r private=%r"
            % (
                telemetry_target_sequence,
                self.telemetry_native_attempts,
                to_unicode(
                    shot.GetName()
                ),
                to_unicode(
                    aset.GetName()
                ),
                (
                    time.time()
                    - self.run_started_wall
                    if self.run_started_wall is not None
                    else 0.0
                ),
                (
                    time.time()
                    - target_started_wall
                ),
                self.telemetry_completed_targets,
                end_memory[
                    "ok"
                ],
                end_memory[
                    "working_set"
                ],
                end_memory[
                    "peak_working_set"
                ],
                end_memory[
                    "pagefile"
                ],
                end_memory[
                    "peak_pagefile"
                ],
                end_memory[
                    "private"
                ],
            )
        )


    def contextualizer_assert_run_lock_present(self):
        try:
            main_window = self.parent()
        except Exception:
            main_window = None

        if main_window is None:
            raise ProbeError(
                "CONTEXTUALIZER target resume lost production run-lock parent."
            )

        try:
            object_name = to_unicode(
                self.objectName()
            )
        except Exception:
            object_name = u""

        if object_name != to_unicode(
                RUN_LOCK_NAME):
            raise ProbeError(
                "CONTEXTUALIZER target resume run-lock object name changed."
            )

        if _find_existing_run(
                main_window
        ) is None:
            raise ProbeError(
                "CONTEXTUALIZER target resume could not rediscover the production run lock."
            )


    def contextualizer_resolve_resume_target(
            self,
            record,
            target):
        self.contextualizer_assert_run_lock_present()
        self.assert_master_stable()

        at_head = (
            sfmApp.GetShotAtCurrentTime()
        )

        if (
            at_head is None
            or native_ptr(
                at_head
            )
            != record[
                "ptr"
            ]
        ):
            raise ProbeError(
                "CONTEXTUALIZER target resume lost expected shot context."
            )

        if self.current_target_index > 0:
            previous = record[
                "targets"
            ][
                self.current_target_index
                - 1
            ]

            previous_pair = (
                to_unicode(
                    record[
                        "name"
                    ]
                ),
                to_unicode(
                    previous[
                        "name"
                    ]
                ),
            )

            if previous_pair not in self.production_terminal_results:
                raise ProbeError(
                    "CONTEXTUALIZER target resume previous target is not terminal: %r."
                    % (previous_pair,)
                )

        matches = []

        for aset in at_head.animationSets:
            try:
                aset_ptr = native_ptr(
                    aset
                )
            except Exception:
                continue

            if aset_ptr != target[
                    "ptr"]:
                continue

            try:
                aset_name = to_unicode(
                    aset.GetName()
                )
            except Exception:
                aset_name = u""

            if aset_name != to_unicode(
                    target["name"]):
                continue

            matches.append(
                aset
            )

        if len(matches) != 1:
            raise ProbeError(
                "CONTEXTUALIZER next target failed unique resume re-resolution: "
                "shot=%r target=%r matches=%d."
                % (
                    to_unicode(
                        record["name"]
                    ),
                    to_unicode(
                        target["name"]
                    ),
                    len(matches),
                )
            )

        fresh_record = dict(
            record
        )
        fresh_record[
            "shot"
        ] = at_head

        fresh_target = dict(
            target
        )
        fresh_target[
            "anim_set"
        ] = matches[0]

        self.target_resume_guard_passes += 1
        self.target_reresolve_passes += 1

        self.log(
            "PRODUCTION_TARGET_RESUME_GUARDS = PASS shot=%r target=%r "
            "target_index=%d/%d"
            % (
                to_unicode(
                    record["name"]
                ),
                to_unicode(
                    target["name"]
                ),
                self.current_target_index + 1,
                len(
                    record[
                        "targets"
                    ]
                ),
            )
        )

        return (
            fresh_record,
            fresh_target,
        )


    def contextualizer_finish_current_shot(self):
        record = self.work[
            self.work_index
        ]

        if self.current_target_index != len(
                record["targets"]):
            raise ProbeError(
                "CONTEXTUALIZER shot completion reached before all eligible targets were terminal."
            )

        self.log(
            "SHOT_COMPLETE = PASS"
        )

        self.log(
            "CONTEXTUALIZER_SHOT_ELAPSED shot=%r elapsed_seconds=%.3f"
            % (
                to_unicode(
                    record["name"]
                ),
                (
                    time.time()
                    - self.current_shot_started_wall
                    if self.current_shot_started_wall is not None
                    else 0.0
                ),
            )
        )

        self.work_index += 1
        completed_shots = self.work_index

        self.verify_session_identity_layer(
            completed_shots
        )

        if (
            completed_shots
            < len(
                self.work
            )
            and (
                completed_shots
                % CONTEXTUALIZER_PERIODIC_GLOBAL_SHOT_INTERVAL
            ) == 0
        ):
            self.verify_session_isolation_periodic(
                completed_shots
            )

        if self.contextualizer_should_checkpoint_after_shot(
                completed_shots):
            self.contextualizer_resource_checkpoint(
                "AFTER_SHOT_%d"
                % completed_shots,
                True,
            )

        self.current_target_index = 0
        self.activate_next_shot()


    def process_current_target(self):
        if self.finished:
            return

        try:
            record = self.work[
                self.work_index
            ]

            if (
                self.current_target_index
                >= len(
                    record[
                        "targets"
                    ]
                )
            ):
                self.contextualizer_finish_current_shot()
                return

            target = record[
                "targets"
            ][
                self.current_target_index
            ]

            if self.current_target_index > 0:
                self.target_resume_callbacks += 1

            (
                fresh_record,
                fresh_target,
            ) = self.contextualizer_resolve_resume_target(
                record,
                target,
            )

            self.section(
                "TARGET %d/%d IN %s: %s"
                % (
                    self.current_target_index + 1,
                    len(
                        record[
                            "targets"
                        ]
                    ),
                    record[
                        "name"
                    ],
                    target[
                        "name"
                    ],
                )
            )

            self.run_target_transaction(
                fresh_record,
                fresh_target,
            )

            self.current_target_index += 1

            if (
                self.current_target_index
                < len(
                    record[
                        "targets"
                    ]
                )
            ):
                next_target = record[
                    "targets"
                ][
                    self.current_target_index
                ]

                self.target_callback_defer_schedules += 1

                self.log(
                    "PRODUCTION_TARGET_CALLBACK_DEFER_SCHEDULED = PASS "
                    "completed_target_index=%d/%d next_target=%r delay_ms=%d"
                    % (
                        self.current_target_index,
                        len(
                            record[
                                "targets"
                            ]
                        ),
                        to_unicode(
                            next_target[
                                "name"
                            ]
                        ),
                        CONTEXTUALIZER_TARGET_CALLBACK_DEFER_MS,
                    )
                )

                QtCore.QTimer.singleShot(
                    CONTEXTUALIZER_TARGET_CALLBACK_DEFER_MS,
                    self.process_current_target,
                )
                return

            self.contextualizer_finish_current_shot()

        except Exception as exc:
            self.log(
                traceback.format_exc()
            )
            self.abort(
                "Exception during CONTEXTUALIZER target-level Qt callback transaction: %r"
                % exc
            )


    def activate_next_shot(self):
        if self.finished:
            return

        if self.work_index >= len(self.work):
            try:
                self.verify_session_isolation_end()
            except Exception as exc:
                self.abort(
                    "CONTEXTUALIZER layered end-of-run whole-session isolation failed: %r"
                    % exc
                )
                return

            self.request_restore_and_finish()
            return

        record = self.work[
            self.work_index
        ]

        self.current_shot_started_wall = (
            time.time()
        )

        self.section(
            "ACTIVATE SHOT %d/%d: %s"
            % (
                self.work_index + 1,
                len(self.work),
                record["name"],
            )
        )

        self.log(
            "shot ptr=%r midpoint=%r targets=%d"
            % (
                record["ptr"],
                record["midpoint"],
                len(record["targets"]),
            )
        )

        try:
            sfmApp.SetHeadTimeInSeconds(
                record["midpoint"]
            )
        except Exception as exc:
            self.abort(
                "Could not move playhead into %s: %r"
                % (record["name"], exc)
            )
            return

        at_head = sfmApp.GetShotAtCurrentTime()

        if (
            at_head is None
            or native_ptr(at_head) != record["ptr"]
        ):
            self.abort(
                "Playhead did not enter expected shot."
            )
            return

        self.log(
            "SHOT_ACTIVATION_IMMEDIATE_GATE = PASS"
        )
        self.log(
            "Returning to SFM before target transactions."
        )

        QtCore.QTimer.singleShot(
            DEFER_MS,
            self.process_current_shot,
        )


    def process_current_shot(self):
        if self.finished:
            return

        try:
            record = self.work[
                self.work_index
            ]

            at_head = (
                sfmApp.GetShotAtCurrentTime()
            )

            if (
                at_head is None
                or native_ptr(
                    at_head
                )
                != record[
                    "ptr"
                ]
            ):
                raise ProbeError(
                    "Deferred callback lost expected shot context."
                )

            self.log(
                "DEFERRED_SHOT_CONTEXT_GATE = PASS"
            )

            self.total_shots_processed += 1
            self.current_target_index = 0

            # The first target runs in this already-deferred shot callback.
            # Any later target in this same shot starts only after a normal
            # return to the Qt event loop.
            self.process_current_target()

        except Exception as exc:
            self.log(
                traceback.format_exc()
            )
            self.abort(
                "Exception during deferred production-candidate shot entry: %r"
                % exc
            )


    def abort(
            self,
            message):
        if self.finished:
            return

        if self.failure_message is None:
            self.failure_message = (
                message
            )

        self.log(
            "ABORT: %s"
            % message
        )

        self.request_restore_and_finish()


    def request_restore_and_finish(self):
        if (
            self.finished
            or self.restore_in_progress
        ):
            return

        self.restore_in_progress = True

        self.section(
            "RESTORING ORIGINAL PLAYHEAD"
        )

        try:
            sfmApp.SetHeadTimeInSeconds(
                self.original_head
            )
            self.log(
                "requested original head=%r"
                % self.original_head
            )
        except Exception as exc:
            self.failure_message = (
                (
                    self.failure_message
                    + "; "
                )
                if self.failure_message
                else ""
            ) + (
                "playhead restore request failed: %r"
                % exc
            )

            self.final_report(
                False
            )
            return

        QtCore.QTimer.singleShot(
            DEFER_MS,
            self.finish_after_restore,
        )


    def finish_after_restore(self):
        if self.finished:
            return

        try:
            actual_head = float(
                sfmApp.GetHeadTimeInSeconds()
            )
        except Exception:
            actual_head = None

        try:
            actual_shot = (
                sfmApp.GetShotAtCurrentTime()
            )
        except Exception:
            actual_shot = None

        restore_pass = bool(
            actual_head is not None
            and abs(
                actual_head
                - float(
                    self.original_head
                )
            ) < 0.0001
            and actual_shot
            is not None
            and native_ptr(
                actual_shot
            )
            == self.original_shot_ptr
        )

        self.log(
            "restored head=%r shot=%r"
            % (
                actual_head,
                (
                    None
                    if actual_shot is None
                    else actual_shot.GetName()
                ),
            )
        )
        self.log(
            "ORIGINAL_PLAYHEAD_RESTORE = %s"
            % (
                "PASS"
                if restore_pass
                else "FAIL"
            )
        )

        if not restore_pass:
            if self.failure_message is None:
                self.failure_message = (
                    "Original playhead restoration failed."
                )

        self.final_report(
            self.failure_message is None
        )


    def final_report(
            self,
            success):
        if self.finished:
            return

        self.finished = True

        # Astra second-correction-gate F3 (re-opening the first
        # correction's teardown): the prior version released the lease
        # here but left `self.master_index` (the command's OWN reference
        # to the exact same payload dict the lease/view holds) untouched
        # -- the lease accounting then claimed "no live owner" while this
        # object (which can genuinely outlive final_report, e.g. still
        # reachable via Qt/other references) still held a live reference
        # to the payload. Fixed by following the REAL command-teardown
        # order Astra specified: (1) this IS the point of last use of
        # self.master_index (nothing after final_report reads it -- the
        # whole rebuild/reconciliation pipeline runs strictly BEFORE this
        # method, per the file's own architecture); (2) drop the
        # command-held payload reference FIRST; (3) THEN release the
        # consumer lease exactly once (guarded by the same `if self.
        # finished: return` this method already starts with, so this
        # whole block cannot execute twice); (4) the lease's own `.view`
        # reference dies naturally once `self._master_index_lease = None`
        # drops the last reference to the lease object itself -- no
        # separate explicit clear needed. Defensive getattr: the lease
        # may not exist if the command aborted before the master_index
        # build ever ran. A release failure is logged, never silently
        # swallowed, and never discards the fact that this was the only
        # cleanup handle (the lease reference is still dropped either way
        # in the `finally`, so a failed release cannot be retried nor
        # mistaken for a live lease on any subsequent inspection)."""
        self.master_index = None
        _lease = getattr(self, "_master_index_lease", None)
        if _lease is not None:
            try:
                _broker = _b2c_authority_runtime.get_broker()
                _broker.release_view_lease(_lease)
            except Exception as _lease_exc:
                self.log(
                    "R3-B2C-B correction: master_index lease release failed non-fatally: %r"
                    % (_lease_exc,)
                )
            finally:
                self._master_index_lease = None

        try:
            self.section(
                "FINAL RESULT"
            )

            self.contextualizer_resource_checkpoint(
                "FINAL_REPORT_ENTRY",
                True,
            )

            self.log(
                "shots seen=%d processed=%d"
                % (
                    self.total_shots_seen,
                    self.total_shots_processed,
                )
            )
            self.log(
                "animation sets seen=%d model-backed=%d targets=%d"
                % (
                    self.total_sets_seen,
                    self.total_model_backed,
                    self.total_targets,
                )
            )
            self.log(
                "native rebuilt=%d reconciled=%d native-only=%d policy-fallback=%d"
                % (
                    self.total_native_rebuilt,
                    self.total_reconciled,
                    self.total_native_only,
                    self.total_policy_fallback,
                )
            )
            self.log(
                "supported-active-rig=%d unrigged=%d ambiguous/stale-rig=%d"
                % (
                    self.total_supported_active_rig,
                    self.total_unrigged,
                    self.total_ambiguous_rig,
                )
            )

            for key in sorted(self.class_totals.keys()):
                self.log(
                    "CLASS_TOTAL %s=%d"
                    % (key, self.class_totals[key])
                )

            if self.failure_message is not None:
                self.log(
                    "failure=%s"
                    % self.failure_message
                )

            terminal_pass = bool(
                set(self.production_terminal_results.keys())
                == self.production_inventory_pairs
                and len(self.production_terminal_results)
                == self.total_targets
                and len(self.production_final_semantic_capture_pairs)
                == self.total_targets
            )

            session_digest_accounting_pass = bool(
                len(
                    self.session_expected
                ) > 0
                and all([
                    isinstance(
                        value,
                        str,
                    )
                    and len(
                        value
                    ) == 32
                    for value
                    in self.session_expected.values()
                ])
            )

            self.log(
                "CONTEXTUALIZER_SESSION_EXPECTED_DIGEST_ACCOUNTING values=%d "
                "digest_bytes_each=32 result=%s"
                % (
                    len(
                        self.session_expected
                    ),
                    (
                        "PASS"
                        if session_digest_accounting_pass
                        else "FAIL"
                    ),
                )
            )

            final_semantic_capture_accounting_pass = bool(
                len(
                    self.production_final_semantic_capture_pairs
                )
                == self.total_targets
                and self.production_final_semantic_capture_pairs
                == set(
                    self.production_terminal_results.keys()
                )
            )

            self.log(
                "CONTEXTUALIZER_TERMINAL_SEMANTIC_CAPTURE_ACCOUNTING captures=%d "
                "terminal_targets=%d retained_rich_payloads=0"
                % (
                    len(
                        self.production_final_semantic_capture_pairs
                    ),
                    len(
                        self.production_terminal_results
                    ),
                )
            )

            self.log(
                "CONTEXTUALIZER_TERMINAL_SEMANTIC_CAPTURE_ACCOUNTING = %s"
                % (
                    "PASS"
                    if final_semantic_capture_accounting_pass
                    else "FAIL"
                )
            )

            dynamic_accounting_pass = bool(
                self.total_native_rebuilt == self.total_targets
                and (self.total_reconciled + self.total_native_only)
                == self.total_targets
                and self.total_policy_fallback <= self.total_native_only
            )

            eligibility_accounting_pass = bool(
                self.total_model_backed
                == (
                    self.total_root_skips
                    + self.total_duplicate_aset_skips
                    + self.total_gate_static_skips
                    + self.total_gate_follower_skips
                    + self.total_gate_lowbone_skips
                    + self.total_targets
                )
            )

            self.log(
                "ELIGIBILITY_ACCOUNTING model_backed=%d root_skips=%d duplicate_aset_skips=%d "
                "static_skips=%d follower_skips=%d lowbone_skips=%d processed_targets=%d"
                % (
                    self.total_model_backed,
                    self.total_root_skips,
                    self.total_duplicate_aset_skips,
                    self.total_gate_static_skips,
                    self.total_gate_follower_skips,
                    self.total_gate_lowbone_skips,
                    self.total_targets,
                )
            )

            final_memory = (
                contextualizer_process_memory_sample()
            )

            self.log(
                "CONTEXTUALIZER_TELEMETRY_SUMMARY native_attempts=%d completed_targets=%d "
                "run_elapsed=%.3f mem_ok=%r working_set=%r peak_working_set=%r "
                "pagefile=%r peak_pagefile=%r private=%r"
                % (
                    self.telemetry_native_attempts,
                    self.telemetry_completed_targets,
                    (
                        time.time()
                        - self.run_started_wall
                        if self.run_started_wall is not None
                        else 0.0
                    ),
                    final_memory["ok"],
                    final_memory["working_set"],
                    final_memory["peak_working_set"],
                    final_memory["pagefile"],
                    final_memory["peak_pagefile"],
                    final_memory["private"],
                )
            )

            expected_periodic_checks = (
                max(
                    0,
                    (
                        self.total_shots_processed
                        - 1
                    )
                    // CONTEXTUALIZER_PERIODIC_GLOBAL_SHOT_INTERVAL
                )
            )

            layered_isolation_accounting_pass = bool(
                self.layer_peer_checks
                == self.total_targets
                and self.layer_identity_checks
                == self.total_shots_processed
                and self.layer_periodic_global_checks
                == expected_periodic_checks
                and self.layer_end_global_checks
                == 1
            )

            self.log(
                "PRODUCTION_TARGET_CALLBACK_COUNTS schedules=%d resume_callbacks=%d "
                "resume_guard_passes=%d target_reresolve_passes=%d"
                % (
                    self.target_callback_defer_schedules,
                    self.target_resume_callbacks,
                    self.target_resume_guard_passes,
                    self.target_reresolve_passes,
                )
            )

            self.log(
                "CONTEXTUALIZER_LAYERED_ISOLATION_COUNTS peer_checks=%d peer_fingerprints=%d "
                "identity_checks=%d periodic_global_checks=%d expected_periodic=%d "
                "end_global_checks=%d"
                % (
                    self.layer_peer_checks,
                    self.layer_peer_fingerprints,
                    self.layer_identity_checks,
                    self.layer_periodic_global_checks,
                    expected_periodic_checks,
                    self.layer_end_global_checks,
                )
            )

            self.log(
                "CONTEXTUALIZER_SCOPED_MASTER_INDEX_COUNTS builds=%d scope_folds=%d "
                "gate_opportunities=%d gate_validations=%d "
                "target_opportunities=%d target_validations=%d sha_checks=%d "
                "build_seconds=%.3f sha_seconds=%.3f build_private_delta=%r "
                "build_working_delta=%r"
                % (
                    self.master_index_builds,
                    len(
                        self.master_index_scope_folds
                    ),
                    self.master_index_gate_opportunities,
                    self.master_index_gate_validations,
                    self.master_index_target_opportunities,
                    self.master_index_target_validations,
                    self.master_index_sha_checks,
                    self.master_index_build_seconds,
                    self.master_index_sha_seconds,
                    self.master_index_build_private_delta,
                    self.master_index_build_working_delta,
                )
            )

            self.log(
                "CONTEXTUALIZER_ADDRESS_SPACE_TELEMETRY_SUMMARY vas_samples=%d "
                "vas_successes=%d vas_failures=%d global_capture_count=%d "
                "global_capture_max_private_delta=%r"
                % (
                    self.contextualizer_vas_samples,
                    self.contextualizer_vas_successes,
                    self.contextualizer_vas_failures,
                    self.contextualizer_global_capture_count,
                    self.contextualizer_global_capture_max_private_delta,
                )
            )

            expected_same_shot_defers = max(
                0,
                self.total_targets
                - self.total_shots_processed,
            )

            target_callback_accounting_pass = bool(
                self.target_callback_defer_schedules
                == expected_same_shot_defers
                and self.target_resume_callbacks
                == self.target_callback_defer_schedules
                and self.target_resume_guard_passes
                == self.total_targets
                and self.target_reresolve_passes
                == self.total_targets
            )

            contextualizer_telemetry_accounting_pass = bool(
                self.contextualizer_architecture is not None
                and self.contextualizer_architecture[
                    "ok"
                ]
                and self.contextualizer_vas_samples > 0
                and self.contextualizer_vas_successes
                == self.contextualizer_vas_samples
            )

            contextualizer_master_index_accounting_pass = bool(
                self.master_index_builds
                == 1
                and self.master_index is not None
                and self.master_index_gate_validations
                == self.master_index_gate_opportunities
                and self.master_index_target_validations
                == self.master_index_target_opportunities
                and self.master_index_sha_checks
                == (
                    1
                    + self.master_index_gate_validations
                    + self.master_index_target_validations
                )
            )

            self.log(
                "PRODUCTION_TARGET_CALLBACK_ACCOUNTING expected_same_shot_defers=%d "
                "schedules=%d resumes=%d guards=%d reresolves=%d targets=%d "
                "result=%s"
                % (
                    expected_same_shot_defers,
                    self.target_callback_defer_schedules,
                    self.target_resume_callbacks,
                    self.target_resume_guard_passes,
                    self.target_reresolve_passes,
                    self.total_targets,
                    (
                        "PASS"
                        if target_callback_accounting_pass
                        else "FAIL"
                    ),
                )
            )

            self.log(
                "CONTEXTUALIZER_TELEMETRY_ACCOUNTING = %s"
                % (
                    "PASS"
                    if contextualizer_telemetry_accounting_pass
                    else "FAIL"
                )
            )

            self.log(
                "CONTEXTUALIZER_SCOPED_MASTER_INDEX_ACCOUNTING = %s"
                % (
                    "PASS"
                    if contextualizer_master_index_accounting_pass
                    else "FAIL"
                )
            )

            self.log(
                "CONTEXTUALIZER_MASTER_INDEX_OPPORTUNITY_ACCOUNTING gate=%d/%d "
                "target=%d/%d sha=%d expected_sha=%d result=%s"
                % (
                    self.master_index_gate_validations,
                    self.master_index_gate_opportunities,
                    self.master_index_target_validations,
                    self.master_index_target_opportunities,
                    self.master_index_sha_checks,
                    (
                        1
                        + self.master_index_gate_validations
                        + self.master_index_target_validations
                    ),
                    (
                        "PASS"
                        if contextualizer_master_index_accounting_pass
                        else "FAIL"
                    ),
                )
            )

            composer_accounting_pass = bool(
                self.production_policy_plan_passes
                == self.production_composer_passes
                and self.production_composer_passes
                == self.total_reconciled
                and len(self.production_composer_pairs)
                == self.total_reconciled
                and self.production_supported_plan_pairs
                == self.production_composer_pairs
            )

            self.log(
                "PRODUCTION_TERMINAL_RESULTS=%r"
                % sorted(self.production_terminal_results.items())
            )
            self.log(
                "PRODUCTION_GENERIC_POLICY_PLAN_PASS_COUNT=%d"
                % self.production_policy_plan_passes
            )
            self.log(
                "PRODUCTION_GENERIC_COMPOSER_PASS_COUNT=%d"
                % self.production_composer_passes
            )
            self.log(
                "PRODUCTION_MIXED_DIRECT_BY_TARGET=%r"
                % sorted(self.production_mixed_direct_by_target.items())
            )
            self.log(
                "PRODUCTION_DESTINATION_DIRECT_ORDER_COHORT_COUNT=%d"
                % self.production_destination_order_cohort_count
            )

            checks = [
                (
                    "PRODUCTION_ALL_INVENTORIED_TARGETS_TERMINAL",
                    terminal_pass,
                ),
                (
                    "PRODUCTION_DYNAMIC_ACCOUNTING",
                    dynamic_accounting_pass,
                ),
                (
                    "PRODUCTION_ELIGIBILITY_ACCOUNTING",
                    eligibility_accounting_pass,
                ),
                (
                    "PRODUCTION_COMPOSER_ACCOUNTING",
                    composer_accounting_pass,
                ),
                (
                    "CONTEXTUALIZER_LAYERED_ISOLATION_ACCOUNTING",
                    layered_isolation_accounting_pass,
                ),
                (
                    "PRODUCTION_TARGET_CALLBACK_ACCOUNTING",
                    target_callback_accounting_pass,
                ),
                (
                    "CONTEXTUALIZER_TELEMETRY_ACCOUNTING",
                    contextualizer_telemetry_accounting_pass,
                ),
                (
                    "CONTEXTUALIZER_SCOPED_MASTER_INDEX_ACCOUNTING",
                    contextualizer_master_index_accounting_pass,
                ),
                (
                    "CONTEXTUALIZER_TERMINAL_SEMANTIC_CAPTURE_ACCOUNTING",
                    final_semantic_capture_accounting_pass,
                ),
                (
                    "CONTEXTUALIZER_SESSION_EXPECTED_DIGEST_ACCOUNTING",
                    session_digest_accounting_pass,
                ),
            ]

            for marker, passed in checks:
                self.log(
                    "%s = %s"
                    % (
                        marker,
                        "PASS" if passed else "FAIL",
                    )
                )

            success = bool(
                success
                and self.failure_message is None
                and terminal_pass
                and dynamic_accounting_pass
                and eligibility_accounting_pass
                and composer_accounting_pass
                and layered_isolation_accounting_pass
                and target_callback_accounting_pass
                and contextualizer_telemetry_accounting_pass
                and contextualizer_master_index_accounting_pass
                and final_semantic_capture_accounting_pass
                and session_digest_accounting_pass
            )

            self.log(
                "PRODUCTION_REBUILD_CONTROL_GROUPS = %s"
                % ("PASS" if success else "FAIL")
            )

            self.log(
                "PRODUCTION_CONTEXTUALIZER = %s"
                % ("PASS" if success else "FAIL")
            )

            if success:
                self.log(
                    "PASS means the production candidate completed the requested shot scope, every eligible target reached a terminal state, responsive Qt callback resumption remained guarded, and all semantic, isolation, undo, Master-index, eligibility, playhead, and accounting guarantees passed."
                )

        finally:
            try:
                if self.fp is not None:
                    self.fp.flush()
                    self.fp.close()
            except Exception:
                pass

            self.fp = None
            self.release_run_lock()


    def start(self):
        try:
            if not sfmApp.HasDocument():
                raise ProbeError(
                    "No SFM document is open."
                )

            self.fp = open(
                OUTPUT_PATH,
                "w"
            )

            self.run_started_wall = (
                time.time()
            )

            self.section(
                "SFM REBUILD CONTROL GROUPS - PRODUCTION CANDIDATE"
            )
            self.log(
                "PRODUCTION_REVISION = %s"
                % PRODUCTION_REVISION
            )
            self.log(
                "MUTATION STATUS: MUTATING PRODUCTION CANDIDATE"
            )
            self.log(
                "ROOT-DIRECT FIX: SYNTHETIC <ROOT> EXCLUDED FROM CHILD TREE; MASTER-KNOWN ROOT-DIRECT RIG CONTROLS MAY USE PROVEN HIDDEN-FAMILY ACTIVE-RIG COUNTERPART"
            )
            self.log(
                "MIXED DIRECT-ORDER POLICY: WHEN ONE CONTEXTUAL DIRECT-CONTROL COHORT MIXES MASTER-KNOWN AND MASTER-UNKNOWN CONTROLS, CURRENT MASTER CANNOT EXPRESS A COMPLETE TOTAL ORDER; PRESERVE THE FRESH PRE TOTAL DIRECT-CONTROL ORDER FOR THAT COHORT"
            )
            self.log(
                "PRODUCTION MODE: USER-SELECTED SCOPE; PRE-REBUILD ELIGIBILITY GATE; FROZEN NATIVE/CONTEXTUAL PIPELINE UNCHANGED FOR ELIGIBLE TARGETS"
            )
            self.log(
                "MASTER SELECTABILITY VALIDATION: EXPLICIT Master selectable READS STORED DmeControlGroup selectable ATTRIBUTE; IsSelectable() REMAINS DIAGNOSTIC"
            )
            self.log(
                "CONTEXTUALIZER LAYERED ISOLATION: ELIGIBLE TARGET MUTATION SEMANTICS ARE UNCHANGED"
            )
            self.log(
                "CONTEXTUALIZER LAYER 1: DIRECT PROCESSED-TARGET FINGERPRINT + DEEP CHECK OF ALL OTHER CURRENT-SHOT ANIMATION SETS AFTER EVERY TARGET"
            )
            self.log(
                "CONTEXTUALIZER LAYER 2: COMPACT WHOLE-SESSION SHOT/ANIMATION-SET IDENTITY CENSUS AFTER EVERY COMPLETED SHOT"
            )
            self.log(
                "CONTEXTUALIZER LAYER 3: EXHAUSTIVE WHOLE-SESSION DEEP VERIFICATION EVERY 12 NON-FINAL SHOTS + AT SUCCESSFUL END"
            )
            self.log(
                "CONTEXTUALIZER PEER POLICY: FOLLOWER/OVERLAP HEURISTICS DO NOT DEFINE ISOLATION PEERS"
            )
            self.log(
                "PRODUCTION RESPONSIVENESS: ONE ELIGIBLE TARGET PER QT CALLBACK; RETURN TO QT BETWEEN SUCCESSFUL SAME-SHOT TARGETS; SHOT-LEVEL 100ms DEFER RETAINED"
            )
            self.log(
                "CONTEXTUALIZER RESOURCE POLICY: COMPACT DIGEST BASELINE, TERMINAL-SEMANTIC "
                "NON-RETENTION, AND STREAMING GLOBAL VERIFIER RETAINED; ONE "
                "PERFORMANCE CHANGE ONLY - ONE IMMUTABLE SCOPED MASTER INDEX "
                "REPLACES REPEATED MASTER PARSING"
            )
            self.log(
                "CONTEXTUALIZER_MASTER_INDEX_POLICY = PURE-PYTHON STATIC MASTER DATA ONLY; "
                "PER-USE SHA256 STABILITY; PER-BOUNDARY SUBSET+CONFLICT VALIDATION"
            )
            self.log(
                "CONTEXTUALIZER_RUNTIME_DME_CACHE_POLICY = NONE"
            )
            self.log(
                "CONTEXTUALIZER_DIRECT_DME_TO_HASH_STREAMING = NO"
            )
            self.log(
                "CONTEXTUALIZER VIRTUALQUERY POLICY: LOW-CADENCE ONLY; NEVER CALLED PER TARGET OR IMMEDIATELY BEFORE NATIVE REBUILD"
            )
            self.log(
                "scope_mode=%s scope_shots=%d"
                % (
                    self.scope_mode,
                    len(self.scope_shots),
                )
            )
            self.log(
                "CONTEXTUALIZER_SCOPE_SHOT_NAMES = %r"
                % [
                    to_unicode(
                        shot.GetName()
                    )
                    for shot in self.scope_shots
                ]
            )
            self.log(
                "MASTER METADATA PARSER: PROVEN ENRICHED PARSER WITH group_metadata = ENABLED"
            )
            self.log(
                "BASE ARCHITECTURE: SFM Rebuild Control Groups Contextualizer"
            )
            self.log(
                "UNDO POLICY: entire per-target transaction is non-undoable"
            )

            self.contextualizer_architecture = (
                contextualizer_process_architecture_sample()
            )

            self.log(
                "CONTEXTUALIZER_PROCESS_ARCHITECTURE ok=%r pointer_bits=%r exe=%r "
                "machine=%r characteristics=%r large_address_aware=%r "
                "image_file_32bit_machine=%r error=%r"
                % (
                    self.contextualizer_architecture[
                        "ok"
                    ],
                    self.contextualizer_architecture[
                        "pointer_bits"
                    ],
                    self.contextualizer_architecture[
                        "exe_path"
                    ],
                    self.contextualizer_architecture[
                        "machine"
                    ],
                    self.contextualizer_architecture[
                        "characteristics"
                    ],
                    self.contextualizer_architecture[
                        "large_address_aware"
                    ],
                    self.contextualizer_architecture[
                        "image_file_32bit_machine"
                    ],
                    self.contextualizer_architecture[
                        "error"
                    ],
                )
            )

            self.contextualizer_resource_checkpoint(
                "CP0_COMMAND_START",
                True,
            )

            (
                game_dir,
                usermod_dir,
            ) = self.derive_paths()

            self.gate_content_dirs = (
                _gate_list_content_dirs(
                    game_dir
                )
            )

            self.log(
                "eligibility content directories=%d"
                % len(
                    self.gate_content_dirs
                )
            )

            self.log(
                "game directory=%r"
                % game_dir
            )
            self.log(
                "usermod directory=%r"
                % usermod_dir
            )
            self.log(
                "live Master=%r"
                % self.master_path
            )
            self.log(
                "live Master SHA256=%s"
                % self.master_hash
            )

            self.section(
                "CONTEXTUALIZER BUILD ONE SCOPED CANONICAL MASTER INDEX"
            )

            self.master_index_scope_folds = (
                self.collect_scope_master_wanted_folds()
            )

            if not self.master_index_scope_folds:
                raise ProbeError(
                    "CONTEXTUALIZER selected scope has no control-name vocabulary for Master indexing."
                )

            self.contextualizer_assert_master_stable_for_index_use(
                "BUILD"
            )

            before_index_memory = (
                contextualizer_process_memory_sample()
            )

            index_started = time.time()

            # R3-B2C-B: migrated from parse_targeted_master(...) to the
            # qualified shared-authority compatibility adapter. shipped_root
            # is a PROVISIONAL path (see acquire_master_index_via_qualified_
            # authority's own docstring) -- real-production shipped-sidecar
            # deployment location is not yet finalized by any prior B2 stage.
            #
            # Astra F3 correction: the function now also returns an explicit
            # ViewLease alongside the payload dict -- held here for the
            # remainder of this command's lifetime and released
            # deterministically (never GC-timing-dependent) at every real
            # exit path: normal completion, the run-lock/probe-error abort
            # paths, and the outer exception handler, so a later, unrelated
            # acquisition evicting this generation from the broker's cache
            # under memory pressure can never silently undercount memory
            # this command is still actively using.
            #
            # Astra second-correction-gate F4: expected_generation pins
            # this acquisition to self.master_hash -- the SAME live-Master
            # SHA-256 this command captured once, at command start, in
            # derive_paths(). Never accept a view of some OTHER generation
            # while this command remains pinned to master_hash.
            self.master_index, self._master_index_lease = (
                acquire_master_index_via_qualified_authority(
                    self.master_path,
                    self.master_index_scope_folds,
                    shipped_root=os.path.join(
                        usermod_dir, "scripts", "sfm", "gate_r2_formal_deploy",
                    ),
                    expected_generation=self.master_hash,
                )
            )

            self.master_index_build_seconds = (
                time.time()
                - index_started
            )
            self.master_index_builds = 1

            after_index_memory = (
                contextualizer_process_memory_sample()
            )

            if (
                before_index_memory["ok"]
                and after_index_memory["ok"]
            ):
                self.master_index_build_private_delta = (
                    after_index_memory[
                        "private"
                    ]
                    - before_index_memory[
                        "private"
                    ]
                )

                self.master_index_build_working_delta = (
                    after_index_memory[
                        "working_set"
                    ]
                    - before_index_memory[
                        "working_set"
                    ]
                )

            self.log(
                "CONTEXTUALIZER_SCOPED_MASTER_INDEX_BUILD = PASS unique_scope_folds=%d "
                "matched_folds=%d exact_literals=%d groups=%d mapping_count=%d "
                "destination_count=%d build_seconds=%.3f private_delta=%r "
                "working_set_delta=%r"
                % (
                    len(
                        self.master_index_scope_folds
                    ),
                    len(
                        self.master_index[
                            "folded"
                        ]
                    ),
                    len(
                        self.master_index[
                            "exact_literals"
                        ]
                    ),
                    len(
                        self.master_index[
                            "group_metadata"
                        ]
                    ),
                    self.master_index[
                        "mapping_count"
                    ],
                    self.master_index[
                        "destination_count"
                    ],
                    self.master_index_build_seconds,
                    self.master_index_build_private_delta,
                    self.master_index_build_working_delta,
                )
            )

            self.log(
                "CONTEXTUALIZER_MASTER_INDEX_CONFLICT_POLICY = ORIGINAL PER-GATE-SHOT "
                "AND PER-TARGET WANTED_FOLDS BOUNDARIES"
            )
            self.log(
                "CONTEXTUALIZER_MASTER_INDEX_RUNTIME_STATE_CACHE = NONE"
            )

            self.contextualizer_resource_checkpoint(
                "CP_INDEX_READY",
                True,
            )

            self.original_head = float(
                sfmApp.GetHeadTimeInSeconds()
            )

            original_shot = (
                sfmApp.GetShotAtCurrentTime()
            )

            if original_shot is None:
                raise ProbeError(
                    "Original playhead does not resolve to a shot."
                )

            self.original_shot_ptr = (
                native_ptr(
                    original_shot
                )
            )

            self.log(
                "original head=%r shot=%r ptr=%r"
                % (
                    self.original_head,
                    original_shot.GetName(),
                    self.original_shot_ptr,
                )
            )

            self.section(
                "BUILDING SCOPED MODEL TARGET INVENTORY"
            )

            self.contextualizer_resource_checkpoint(
                "CP1_BEFORE_INVENTORY_GATE",
                True,
            )

            self.work = (
                self.snapshot_work()
            )

            self.contextualizer_resource_checkpoint(
                "CP2_AFTER_INVENTORY_GATE",
                True,
            )

            self.log(
                "target-containing shots=%d animation-sets-seen=%d "
                "model-backed=%d eligible-model-targets=%d non-model=%d root-skips=%d"
                % (
                    len(self.work),
                    self.total_sets_seen,
                    self.total_model_backed,
                    self.total_targets,
                    self.total_non_model_skips,
                    self.total_root_skips,
                )
            )

            actual_pairs = set()

            for shot_record in self.work:
                shot_name = to_unicode(
                    shot_record["name"]
                )

                for target in shot_record["targets"]:
                    pair = (
                        shot_name,
                        to_unicode(target["name"]),
                    )

                    if pair in actual_pairs:
                        raise ProbeError(
                            "PRODUCTION duplicate shot/animation-set target pair: %r."
                            % (pair,)
                        )

                    actual_pairs.add(pair)

            if len(actual_pairs) != self.total_targets:
                raise ProbeError(
                    "Production dynamic inventory mismatch: targets=%d unique_pairs=%d."
                    % (
                        self.total_targets,
                        len(actual_pairs),
                    )
                )

            self.production_inventory_pairs = set(
                actual_pairs
            )

            self.log(
                "PRODUCTION_DYNAMIC_TARGET_INVENTORY = PASS"
            )

            self.section(
                "CONTEXTUALIZER COMPACT DIGEST WHOLE-SESSION ISOLATION BASELINE"
            )

            self.contextualizer_resource_checkpoint(
                "CP3_BEFORE_SESSION_BASELINE",
                True,
            )

            baseline_started = time.time()

            (
                self.session_expected,
                baseline_shape,
            ) = capture_session_fingerprint_digests()

            baseline_elapsed = (
                time.time()
                - baseline_started
            )

            self.contextualizer_resource_checkpoint(
                "CP4_AFTER_SESSION_DIGEST_BASELINE",
                True,
            )

            bad_digest_values = [
                key
                for (
                    key,
                    value) in self.session_expected.items()
                if (
                    not isinstance(
                        value,
                        str,
                    )
                    or len(
                        value
                    ) != 32
                )
            ]

            if bad_digest_values:
                raise ProbeError(
                    "CONTEXTUALIZER session_expected contains non-32-byte digest values: %r."
                    % (
                        bad_digest_values[
                            :20
                        ],
                    )
                )

            self.log(
                "CONTEXTUALIZER_SESSION_BASELINE_SHAPE fingerprints=%d controls=%d "
                "groups=%d child_refs=%d direct_refs=%d elapsed_seconds=%.3f"
                % (
                    baseline_shape[
                        "fingerprints"
                    ],
                    baseline_shape[
                        "controls"
                    ],
                    baseline_shape[
                        "groups"
                    ],
                    baseline_shape[
                        "child_refs"
                    ],
                    baseline_shape[
                        "direct_refs"
                    ],
                    baseline_elapsed,
                )
            )

            self.log(
                "CONTEXTUALIZER_SESSION_EXPECTED_DIGEST_BASELINE values=%d "
                "digest_bytes_each=32 raw_digest_payload_bytes=%d"
                % (
                    len(
                        self.session_expected
                    ),
                    (
                        len(
                            self.session_expected
                        )
                        * 32
                    ),
                )
            )

            self.log(
                "animation-set fingerprint digests captured=%d"
                % len(
                    self.session_expected
                )
            )
            self.log(
                "WHOLE_SESSION_ISOLATION_BASELINE = PASS"
            )
            self.log(
                "ISOLATION_FINGERPRINT_INCLUDES_GROUPCOLOR = PASS"
            )

            self.session_identity_expected = (
                capture_session_identity_census()
            )

            self.log(
                "CONTEXTUALIZER_COMPACT_SESSION_IDENTITY_BASELINE = PASS shots=%d"
                % len(
                    self.session_identity_expected
                )
            )

            if not self.work:
                current_identity = (
                    capture_session_identity_census()
                )
                if (
                    current_identity
                    != self.session_identity_expected
                ):
                    raise ProbeError(
                        "CONTEXTUALIZER compact identity changed in no-work scope."
                    )
                self.verify_session_isolation_end()
                self.request_restore_and_finish()
                return

            self.log(
                "Starting proven deferred playhead traversal."
            )

            self.activate_next_shot()

        except Exception as exc:
            try:
                self.log(
                    traceback.format_exc()
                )
            except Exception:
                pass

            if self.original_head is None:
                self.failure_message = (
                    "Startup failure: %r"
                    % exc
                )
                self.final_report(
                    False
                )
            else:
                self.abort(
                    "Startup failure: %r"
                    % exc
                )


def StartRebuildControlGroups():
    main_window = (
        sfmApp.GetMainWindow()
    )

    if main_window is None:
        try:
            sys.stdout.write(
                "Rebuild Control Groups: SFM main window unavailable.\n"
            )
        except Exception:
            pass
        return

    if (
        _find_existing_run(
            main_window
        )
        is not None
    ):
        try:
            sys.stdout.write(
                "Rebuild Control Groups is already running.\n"
            )
        except Exception:
            pass
        return

    try:
        (
            scope_mode,
            scope_shots,
        ) = _choose_scope()
    except Exception as exc:
        _show_scope_error(
            "Could not resolve rebuild scope: %s"
            % to_unicode(
                exc
            )
        )
        return

    if scope_mode is None:
        return

    run = (
        RebuildControlGroupsProductionRun(
            main_window,
            scope_mode,
            scope_shots,
        )
    )
    run.start()


StartRebuildControlGroups()
