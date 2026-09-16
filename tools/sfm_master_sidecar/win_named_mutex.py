# -*- coding: utf-8 -*-
"""Real Windows named-mutex publisher serialization -- R3-B2E,
ASTRA_CORRECTED.md Section 12 (`Global\\` mutex, SID + canonical Master
slot namespace, bounded wait, explicit outcome categories, no silent
fallback to a weaker `Local\\` mutex).

Python 3 only (external rebuild utility, per the R3-B2E prompt's own
"B2E's Windows publication utility itself may be Python 3" allowance).
Never used by any runtime reader -- B2A/B2B never import this module.

Verified for real on this host (2026-09-15): `Global\\` mutex creation,
WaitForSingleObject, and ReleaseMutex all work end to end (this host's
interactive session has the privilege needed to create Global-namespace
kernel objects).

`WAIT_ABANDONED` ITSELF IS EMPIRICALLY QUALIFIED (R3-B2E1, 2026-09-15):
an initial cross-process crash simulation (child acquires, then
`os._exit()`s without releasing; a SEPARATE, later process then opens the
same name) did NOT reproduce `WAIT_ABANDONED` -- root-caused, not merely
observed: when the crashing process holds the ONLY open handle to the
mutex, Windows destroys the kernel object outright the instant that
process terminates (handle refcount reaches zero), so a later
`CreateMutexW` with the identical name simply creates a brand-new,
non-abandoned object -- there is no longer an object left to observe an
"abandoned" transition on. This is correct, documented Win32 kernel-
object lifetime behavior, not a defect in the acquire/wait logic below.
Once a THIRD party holds its own open handle to the mutex across the
crash (exactly the situation that arises naturally whenever two real
publishers contend for the same slot, e.g. one already waiting when the
other dies), `WAIT_ABANDONED` reproduces deterministically and the
`OUTCOME_ACQUIRED_ABANDONED` path below was exercised for real (not
mocked) via both `os._exit()` and `TerminateProcess()` death methods.
See the R3-B2E1 qualification report for the low-level probe and full
evidence.
"""
import ctypes
import time
from ctypes import wintypes

_kernel32 = ctypes.windll.kernel32
_advapi32 = ctypes.windll.advapi32

_kernel32.GetCurrentProcess.restype = wintypes.HANDLE
_kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.CreateMutexW.restype = wintypes.HANDLE
_kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_kernel32.WaitForSingleObject.restype = wintypes.DWORD
_kernel32.ReleaseMutex.argtypes = [wintypes.HANDLE]
_kernel32.ReleaseMutex.restype = wintypes.BOOL
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_kernel32.LocalFree.argtypes = [wintypes.LPVOID]

_advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
_advapi32.OpenProcessToken.restype = wintypes.BOOL
_advapi32.GetTokenInformation.argtypes = [
    wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
]
_advapi32.GetTokenInformation.restype = wintypes.BOOL
_advapi32.ConvertSidToStringSidW.argtypes = [wintypes.LPVOID, ctypes.POINTER(ctypes.c_wchar_p)]
_advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL

_TOKEN_QUERY = 0x0008
_TOKEN_USER = 1
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

WAIT_OBJECT_0 = 0x00000000
WAIT_ABANDONED = 0x00000080
WAIT_TIMEOUT = 0x00000102
WAIT_FAILED = 0xFFFFFFFF

OUTCOME_ACQUIRED = "acquired"
OUTCOME_ACQUIRED_ABANDONED = "acquired_abandoned"
OUTCOME_TIMEOUT = "timeout"
OUTCOME_ACCESS_OR_CONFIG_FAILURE = "access_or_config_failure"


class MutexError(Exception):
    """Base class for every exception this module raises."""


class MutexTimeoutError(MutexError):
    pass


class MutexAccessError(MutexError):
    """Mutex creation/acquisition failed for a reason other than timeout
    (access denied, DACL/config problem, or Global namespace unavailable).
    Never silently downgraded to a weaker `Local\\` mutex -- the caller
    must handle this explicitly (ASTRA_CORRECTED.md Section 12)."""


def get_current_user_sid_string():
    """Real SID string for the current process token's user, via
    OpenProcessToken + GetTokenInformation(TokenUser) +
    ConvertSidToStringSidW. Verified for real on this host: returns e.g.
    'S-1-5-21-...-1001'. Raises MutexAccessError on any failure."""
    h_token = wintypes.HANDLE()
    proc = _kernel32.GetCurrentProcess()
    if not _advapi32.OpenProcessToken(proc, _TOKEN_QUERY, ctypes.byref(h_token)):
        raise MutexAccessError("OpenProcessToken failed (GetLastError=%d)" % ctypes.GetLastError())
    try:
        size = wintypes.DWORD(0)
        _advapi32.GetTokenInformation(h_token, _TOKEN_USER, None, 0, ctypes.byref(size))
        buf = ctypes.create_string_buffer(size.value)
        if not _advapi32.GetTokenInformation(h_token, _TOKEN_USER, buf, size, ctypes.byref(size)):
            raise MutexAccessError("GetTokenInformation failed (GetLastError=%d)" % ctypes.GetLastError())
        sid_ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_void_p))[0]
        str_sid_ptr = ctypes.c_wchar_p()
        if not _advapi32.ConvertSidToStringSidW(sid_ptr, ctypes.byref(str_sid_ptr)):
            raise MutexAccessError("ConvertSidToStringSidW failed (GetLastError=%d)" % ctypes.GetLastError())
        try:
            return str_sid_ptr.value
        finally:
            _kernel32.LocalFree(str_sid_ptr)
    finally:
        _kernel32.CloseHandle(h_token)


def build_mutex_name(master_slot_identity, sid_string=None):
    """`Global\\SFM_CGN_R3_PublisherLock_<SID>_<slot-hash>` -- namespace
    includes the current user's SID (so different users never contend
    unnecessarily and DACL scoping is meaningful) plus a caller-supplied
    canonical Master-slot/pointer identity (opaque short token, e.g. an
    install-root+Master-path hash -- see `generated_root.py`)."""
    if sid_string is None:
        sid_string = get_current_user_sid_string()
    safe_slot = "".join(c if (c.isalnum() or c == "-") else "_" for c in master_slot_identity)
    return r"Global\SFM_CGN_R3_PublisherLock_%s_%s" % (sid_string, safe_slot)


class NamedMutexOutcome(object):
    __slots__ = ("kind", "handle", "detail")

    def __init__(self, kind, handle=None, detail=None):
        self.kind = kind
        self.handle = handle
        self.detail = detail


class WindowsNamedMutex(object):
    """Real Win32 `Global\\` named mutex. Never falls back to a `Local\\`
    mutex silently -- if Global-namespace creation fails, `acquire()`
    raises `MutexAccessError` and the caller must decide (per corrected
    B1: a documented single-session limitation, or refuse to publish)."""

    def __init__(self, name):
        self.name = name
        self._handle = None

    def acquire(self, timeout_seconds=30.0):
        """Returns a `NamedMutexOutcome` with `kind` one of
        `OUTCOME_ACQUIRED`, `OUTCOME_ACQUIRED_ABANDONED` (caller now owns
        the mutex but must treat protected state as potentially
        inconsistent), or raises `MutexTimeoutError`/`MutexAccessError`."""
        handle = _kernel32.CreateMutexW(None, False, self.name)
        if handle is None or handle == _INVALID_HANDLE_VALUE:
            raise MutexAccessError(
                "CreateMutexW failed for %r (GetLastError=%d) -- refusing to fall back to a "
                "weaker Local mutex" % (self.name, ctypes.GetLastError())
            )
        self._handle = handle

        timeout_ms = max(0, int(timeout_seconds * 1000))
        result = _kernel32.WaitForSingleObject(handle, timeout_ms)

        if result == WAIT_OBJECT_0:
            return NamedMutexOutcome(OUTCOME_ACQUIRED, handle=handle)
        if result == WAIT_ABANDONED:
            return NamedMutexOutcome(OUTCOME_ACQUIRED_ABANDONED, handle=handle)
        if result == WAIT_TIMEOUT:
            _kernel32.CloseHandle(handle)
            self._handle = None
            raise MutexTimeoutError(
                "could not acquire named mutex %r within %.1fs" % (self.name, timeout_seconds)
            )
        # WAIT_FAILED or any other unexpected result.
        err = ctypes.GetLastError()
        _kernel32.CloseHandle(handle)
        self._handle = None
        raise MutexAccessError(
            "WaitForSingleObject on %r returned unexpected result %r (GetLastError=%d)"
            % (self.name, result, err)
        )

    def release(self):
        if self._handle is None:
            return
        try:
            _kernel32.ReleaseMutex(self._handle)
        finally:
            _kernel32.CloseHandle(self._handle)
            self._handle = None

    def __enter__(self):
        outcome = self.acquire()
        self._last_outcome = outcome
        return outcome

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False
