# -*- coding: utf-8 -*-
"""Windows handle-backed EXISTING-file identity comparison.

ASTRA_CORRECTED.md Section 3 explicitly rejects `os.path.realpath()` +
lowercasing as proof of Windows file identity (it does not resolve
junctions/hardlinks to a canonical form, and NTFS case-insensitivity is a
red herring, not proof of physical-file identity). This module instead
opens each candidate path (must already exist) with a fully-sharing,
read-only handle and compares the OS's own on-disk file identity: volume
serial number + file index (the closest Win32 equivalent of a POSIX
(st_dev, st_ino) pair). Two different path strings that resolve to the
SAME (volume_serial, file_index_high, file_index_low) tuple are proven to
be the same file, independent of junctions/hardlinks/8.3 short names.

Python 2.7 / 3 compatible (ctypes/wintypes behave identically in both).
Every handle opened here is closed in a `finally` block -- no exceptions.

This module is NOT used to resolve/discover output paths that do not yet
exist -- that is a distinct string/component-validation problem, handled
separately (see `pointer.py`'s path-confinement checks).
"""
import ctypes
from ctypes import wintypes

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x00000080

INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

_kernel32 = ctypes.windll.kernel32

_CreateFileW = _kernel32.CreateFileW
_CreateFileW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
    wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
]
_CreateFileW.restype = wintypes.HANDLE


class BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", wintypes.DWORD),
        ("ftCreationTime", wintypes.FILETIME),
        ("ftLastAccessTime", wintypes.FILETIME),
        ("ftLastWriteTime", wintypes.FILETIME),
        ("dwVolumeSerialNumber", wintypes.DWORD),
        ("nFileSizeHigh", wintypes.DWORD),
        ("nFileSizeLow", wintypes.DWORD),
        ("nNumberOfLinks", wintypes.DWORD),
        ("nFileIndexHigh", wintypes.DWORD),
        ("nFileIndexLow", wintypes.DWORD),
    ]


_GetFileInformationByHandle = _kernel32.GetFileInformationByHandle
_GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(BY_HANDLE_FILE_INFORMATION)]
_GetFileInformationByHandle.restype = wintypes.BOOL

_CloseHandle = _kernel32.CloseHandle
_CloseHandle.argtypes = [wintypes.HANDLE]
_CloseHandle.restype = wintypes.BOOL


class FileIdentityUnavailable(Exception):
    pass


class FileIdentity(object):
    __slots__ = ("volume_serial", "file_index_high", "file_index_low", "final_path")

    def __init__(self, volume_serial, file_index_high, file_index_low, final_path):
        self.volume_serial = volume_serial
        self.file_index_high = file_index_high
        self.file_index_low = file_index_low
        self.final_path = final_path

    def same_file_as(self, other):
        if other is None:
            return False
        return (
            self.volume_serial == other.volume_serial
            and self.file_index_high == other.file_index_high
            and self.file_index_low == other.file_index_low
        )

    def __repr__(self):
        return "FileIdentity(volume=%r, index=(%r,%r), final_path=%r)" % (
            self.volume_serial, self.file_index_high, self.file_index_low, self.final_path,
        )


def get_existing_file_identity(path):
    """Open `path` (must already exist) read-only, sharing everything
    (never blocks a concurrent editor/SFM), and return its genuine
    Windows on-disk identity. Raises FileIdentityUnavailable if the file
    cannot be opened or its info cannot be queried. Always closes the
    handle it opens."""
    handle = _CreateFileW(
        path, GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None,
    )
    if handle is None or handle == INVALID_HANDLE_VALUE:
        raise FileIdentityUnavailable(
            "CreateFileW failed for %r (GetLastError=%d)" % (path, ctypes.GetLastError())
        )
    try:
        info = BY_HANDLE_FILE_INFORMATION()
        ok = _GetFileInformationByHandle(handle, ctypes.byref(info))
        if not ok:
            raise FileIdentityUnavailable(
                "GetFileInformationByHandle failed for %r (GetLastError=%d)" % (path, ctypes.GetLastError())
            )
        final_path = _try_get_final_path(handle)
        return FileIdentity(info.dwVolumeSerialNumber, info.nFileIndexHigh, info.nFileIndexLow, final_path)
    finally:
        _CloseHandle(handle)


def _try_get_final_path(handle):
    """Best-effort GetFinalPathNameByHandleW -- optional corroborating
    evidence only. The volume+file-index pair above is the real identity
    proof; this call's absence or failure never invalidates an otherwise-
    successful identity result."""
    try:
        get_final_path = _kernel32.GetFinalPathNameByHandleW
    except AttributeError:
        return None
    try:
        get_final_path.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
        get_final_path.restype = wintypes.DWORD
        buf = ctypes.create_unicode_buffer(32768)
        n = get_final_path(handle, buf, len(buf), 0)
        if n == 0 or n >= len(buf):
            return None
        return buf.value
    except Exception:
        return None
