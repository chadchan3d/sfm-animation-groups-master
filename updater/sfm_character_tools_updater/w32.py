# -*- coding: utf-8 -*-
"""Win32 file primitives for the protected installation backend (Python 3, ctypes).

Ported from the U0A/P1 qualification module (w32.py c7c21a5f...). The R2 C6 primitive set
only: CREATE_NEW writes with checked completion and flush, share-0 protection, handle-based
FileRenameInfo with ReplaceIfExists=FALSE, directory identity handles. Replace-existing,
delete and path-based move calls are deliberately absent.

When TRACE_ENABLED[0] is set (by the test entry point only) every call is recorded in TRACE
as (op, args, ok, last_error), so evidence shows the exact access masks, sharing modes,
dispositions and results used.
"""
import ctypes
import hashlib
import struct
from ctypes import wintypes

k32 = ctypes.WinDLL("kernel32", use_last_error=True)

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
DELETE = 0x00010000
FILE_READ_ATTRIBUTES = 0x0080
FILE_SHARE_READ = 1
FILE_SHARE_WRITE = 2
FILE_SHARE_DELETE = 4
CREATE_NEW = 1
OPEN_EXISTING = 3
OPEN_ALWAYS = 4
FILE_ATTRIBUTE_NORMAL = 0x80
FILE_ATTRIBUTE_DIRECTORY = 0x10
FILE_ATTRIBUTE_REPARSE_POINT = 0x400
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF

FileStandardInfo = 1
FileRenameInfo = 3
FileIdInfo = 18

ERRORS = {
    0: "ERROR_SUCCESS", 2: "ERROR_FILE_NOT_FOUND", 3: "ERROR_PATH_NOT_FOUND",
    5: "ERROR_ACCESS_DENIED", 6: "ERROR_INVALID_HANDLE", 32: "ERROR_SHARING_VIOLATION",
    33: "ERROR_LOCK_VIOLATION", 80: "ERROR_FILE_EXISTS", 87: "ERROR_INVALID_PARAMETER",
    112: "ERROR_DISK_FULL", 123: "ERROR_INVALID_NAME", 183: "ERROR_ALREADY_EXISTS",
    1175: "ERROR_UNABLE_TO_REMOVE_REPLACED", 1176: "ERROR_UNABLE_TO_MOVE_REPLACEMENT",
    1177: "ERROR_UNABLE_TO_MOVE_REPLACEMENT_2",
}


def ename(code):
    return "%s(%d)" % (ERRORS.get(code, "WIN32_ERROR"), code)


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("nLength", wintypes.DWORD), ("lpSecurityDescriptor", wintypes.LPVOID),
                ("bInheritHandle", wintypes.BOOL)]


k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                            ctypes.POINTER(SECURITY_ATTRIBUTES), wintypes.DWORD,
                            wintypes.DWORD, wintypes.HANDLE]
k32.CreateFileW.restype = wintypes.HANDLE
k32.CloseHandle.argtypes = [wintypes.HANDLE]
k32.CloseHandle.restype = wintypes.BOOL
k32.ReadFile.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
                         ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
k32.ReadFile.restype = wintypes.BOOL
k32.WriteFile.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.DWORD,
                          ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
k32.WriteFile.restype = wintypes.BOOL
k32.FlushFileBuffers.argtypes = [wintypes.HANDLE]
k32.FlushFileBuffers.restype = wintypes.BOOL
k32.SetFilePointerEx.argtypes = [wintypes.HANDLE, ctypes.c_longlong,
                                 ctypes.POINTER(ctypes.c_longlong), wintypes.DWORD]
k32.SetFilePointerEx.restype = wintypes.BOOL
k32.SetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID,
                                           wintypes.DWORD]
k32.SetFileInformationByHandle.restype = wintypes.BOOL
k32.GetFileInformationByHandleEx.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID,
                                             wintypes.DWORD]
k32.GetFileInformationByHandleEx.restype = wintypes.BOOL
k32.GetFinalPathNameByHandleW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD,
                                          wintypes.DWORD]
k32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
k32.GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
k32.GetFileAttributesW.restype = wintypes.DWORD
k32.GetHandleInformation.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
k32.GetHandleInformation.restype = wintypes.BOOL

TRACE = []
TRACE_ENABLED = [False]


def _rec(op, args, ok, err, **extra):
    if not TRACE_ENABLED[0]:
        return None
    r = {"op": op, "args": args, "ok": bool(ok), "error": ename(err) if not ok else None}
    r.update(extra)
    TRACE.append(r)
    return r


def trace_event(kind, **detail):
    """Ordinal decision marker in the same trace as every Win32 call."""
    if not TRACE_ENABLED[0]:
        return
    rec = {"op": "EVENT", "event": kind}
    rec.update(detail)
    TRACE.append(rec)


def mask_text(access):
    parts = []
    for v, n in ((GENERIC_READ, "GENERIC_READ"), (GENERIC_WRITE, "GENERIC_WRITE"),
                 (DELETE, "DELETE"), (FILE_READ_ATTRIBUTES, "FILE_READ_ATTRIBUTES")):
        if access & v:
            parts.append(n)
    return "|".join(parts) or "0"


def share_text(share):
    parts = [n for v, n in ((1, "READ"), (2, "WRITE"), (4, "DELETE")) if share & v]
    return "|".join(parts) or "0"


DISPO = {1: "CREATE_NEW", 2: "CREATE_ALWAYS", 3: "OPEN_EXISTING", 4: "OPEN_ALWAYS"}


def create_file(path, access, share, disposition, flags=FILE_ATTRIBUTE_NORMAL, inherit=False):
    """Returns (handle or None, last_error)."""
    sa = SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), None, bool(inherit))
    h = k32.CreateFileW(path, access, share, ctypes.byref(sa), disposition, flags, None)
    err = ctypes.get_last_error()
    ok = h != INVALID_HANDLE_VALUE and h is not None
    _rec("CreateFileW", {"path": path, "access": mask_text(access), "share": share_text(share),
                         "disposition": DISPO.get(disposition, disposition),
                         "flags": hex(flags), "inheritable": bool(inherit)}, ok, err,
         last_error_after_success=ename(err) if ok else None)
    return (h if ok else None), err


def close(h):
    ok = k32.CloseHandle(h)
    err = ctypes.get_last_error()
    _rec("CloseHandle", {}, ok, err)
    return ok


def handle_inheritable(h):
    f = wintypes.DWORD()
    k32.GetHandleInformation(h, ctypes.byref(f))
    return bool(f.value & 1)


def write_all(h, data):
    done = wintypes.DWORD()
    buf = ctypes.create_string_buffer(data, len(data))
    ok = k32.WriteFile(h, buf, len(data), ctypes.byref(done), None)
    err = ctypes.get_last_error()
    ok = bool(ok) and done.value == len(data)
    _rec("WriteFile", {"bytes": len(data)}, ok, err, written=done.value)
    return ok, err


def flush(h):
    ok = k32.FlushFileBuffers(h)
    err = ctypes.get_last_error()
    _rec("FlushFileBuffers", {}, ok, err)
    return bool(ok), err


def seek0(h):
    newp = ctypes.c_longlong()
    return bool(k32.SetFilePointerEx(h, 0, ctypes.byref(newp), 0))


def seek_end(h):
    newp = ctypes.c_longlong()
    return bool(k32.SetFilePointerEx(h, 0, ctypes.byref(newp), 2))


def read_all_handle(h):
    """Reads the whole file through an already-open handle (from offset 0)."""
    if not seek0(h):
        return None, ctypes.get_last_error()
    out = []
    buf = ctypes.create_string_buffer(1 << 16)
    while True:
        n = wintypes.DWORD()
        ok = k32.ReadFile(h, buf, len(buf), ctypes.byref(n), None)
        if not ok:
            return None, ctypes.get_last_error()
        if n.value == 0:
            break
        out.append(buf.raw[:n.value])
    return b"".join(out), 0


def sha_handle(h):
    data, err = read_all_handle(h)
    if data is None:
        _rec("ReadFile(hash via handle)", {}, False, err)
        return None, err
    s = hashlib.sha256(data).hexdigest()
    _rec("ReadFile(hash via handle)", {}, True, 0, sha256=s, size=len(data))
    return s, 0


def file_id(h):
    buf = ctypes.create_string_buffer(24)
    ok = k32.GetFileInformationByHandleEx(h, FileIdInfo, buf, 24)
    if not ok:
        return None
    vol, = struct.unpack_from("<Q", buf.raw, 0)
    return "%016x:%s" % (vol, buf.raw[8:24][::-1].hex())


def std_info(h):
    buf = ctypes.create_string_buffer(24)
    ok = k32.GetFileInformationByHandleEx(h, FileStandardInfo, buf, 24)
    if not ok:
        return None
    alloc, eof, links, delete_pending, is_dir = struct.unpack_from("<qqIBB", buf.raw, 0)
    return {"size": eof, "links": links, "delete_pending": bool(delete_pending),
            "directory": bool(is_dir)}


def final_path(h):
    buf = ctypes.create_unicode_buffer(1024)
    n = k32.GetFinalPathNameByHandleW(h, buf, 1024, 0)
    return buf.value if n else None


def rename_by_handle(h, dest, replace_if_exists=False):
    """SetFileInformationByHandle(FileRenameInfo). x64 FILE_RENAME_INFO layout:
    union{BOOLEAN ReplaceIfExists; DWORD Flags} @0, HANDLE RootDirectory @8,
    DWORD FileNameLength @16, WCHAR FileName[] @20."""
    name = dest.encode("utf-16-le")
    size = 20 + len(name) + 2
    buf = ctypes.create_string_buffer(size)
    struct.pack_into("<B", buf, 0, 1 if replace_if_exists else 0)
    struct.pack_into("<Q", buf, 8, 0)
    struct.pack_into("<I", buf, 16, len(name))
    ctypes.memmove(ctypes.addressof(buf) + 20, name, len(name))
    ok = k32.SetFileInformationByHandle(h, FileRenameInfo, buf, size)
    err = ctypes.get_last_error()
    _rec("SetFileInformationByHandle(FileRenameInfo)",
         {"dest": dest, "ReplaceIfExists": bool(replace_if_exists), "RootDirectory": None},
         ok, err)
    return bool(ok), err


def attrs(path):
    return k32.GetFileAttributesW(path)


def open_dir(path, share=FILE_SHARE_READ | FILE_SHARE_WRITE):
    """Directory identity/pin handle; by default denies DELETE sharing so the
    directory itself cannot be renamed or deleted while held."""
    return create_file(path, FILE_READ_ATTRIBUTES, share, OPEN_EXISTING,
                       FILE_FLAG_BACKUP_SEMANTICS)


def path_identity(path, directory=False):
    """Opens with full sharing just to read identity/hash (path-based preview reader)."""
    flags = FILE_FLAG_BACKUP_SEMANTICS if directory else FILE_ATTRIBUTE_NORMAL
    access = FILE_READ_ATTRIBUTES if directory else GENERIC_READ
    h, err = create_file(path, access, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                         OPEN_EXISTING, flags)
    if h is None:
        return None
    try:
        out = {"file_id": file_id(h), "info": std_info(h)}
        if not directory:
            out["sha256"], _ = sha_handle(h)
        return out
    finally:
        close(h)


def write_new_file(path, data, inject_error=None):
    """CREATE_NEW, checked write, flush, then verification through the same handle."""
    h, err = create_file(path, GENERIC_READ | GENERIC_WRITE, 0, CREATE_NEW)
    if h is None:
        return False, err
    try:
        if inject_error:
            _rec("WriteFile(INJECTED FAULT)", {"bytes": len(data)}, False, inject_error)
            return False, inject_error
        ok, err = write_all(h, data)
        if not ok:
            return False, err
        ok, err = flush(h)
        if not ok:
            return False, err
        s, err = sha_handle(h)
        if s != hashlib.sha256(data).hexdigest():
            return False, err or -1
        return True, 0
    finally:
        close(h)
