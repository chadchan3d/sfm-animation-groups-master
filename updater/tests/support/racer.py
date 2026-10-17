# -*- coding: utf-8 -*-
"""TEST-ONLY adversarial actor (ported from U0A racer.py c74c32ad...): one action per process,
result as one JSON line on stdout. The replace/move/delete calls an ordinary editor or tool
would make live here, not in the product's Win32 module.

  racer.py inplace PATH            open existing (GENERIC_WRITE, share R|W|D), overwrite start
  racer.py inplace_py PATH         Python open(PATH, 'r+b') overwrite (ordinary editor style)
  racer.py replacefile PATH        write PATH.~edit (CREATE_NEW), ReplaceFileW(PATH, tmp)
  racer.py movereplace PATH        write PATH.~edit, MoveFileExW(tmp, PATH, REPLACE_EXISTING)
  racer.py delete PATH             DeleteFileW
  racer.py rename PATH DEST        MoveFileExW(PATH, DEST, 0)
  racer.py create PATH             CreateFileW CREATE_NEW + write occupant bytes
  racer.py lock PATH               C4 lock open; hold until stdin line (prints ACQUIRED/REFUSED)
"""
import ctypes
import hashlib
import json
import os
import sys
from ctypes import wintypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sfm_character_tools_updater import w32  # noqa: E402

w32.TRACE_ENABLED[0] = True
k32 = w32.k32
k32.MoveFileExW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
k32.MoveFileExW.restype = wintypes.BOOL
k32.ReplaceFileW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR,
                             wintypes.DWORD, wintypes.LPVOID, wintypes.LPVOID]
k32.ReplaceFileW.restype = wintypes.BOOL
k32.DeleteFileW.argtypes = [wintypes.LPCWSTR]
k32.DeleteFileW.restype = wintypes.BOOL
MOVEFILE_REPLACE_EXISTING = 1

EDIT = b"USER EDIT FROM RACER %d\n" % os.getpid()


def move_file_ex(src, dst, flags):
    ok = k32.MoveFileExW(src, dst, flags)
    return bool(ok), ctypes.get_last_error()


def replace_file(target, replacement):
    ok = k32.ReplaceFileW(target, replacement, None, 0, None, None)
    return bool(ok), ctypes.get_last_error()


def delete_file(path):
    ok = k32.DeleteFileW(path)
    return bool(ok), ctypes.get_last_error()


def result_sha(path):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    except OSError:
        return None


def out(**kw):
    kw["pid"] = os.getpid()
    sys.stdout.write(json.dumps(kw, sort_keys=True) + "\n")
    sys.stdout.flush()


def main(a):
    act = a[0]
    if act == "inplace":
        h, err = w32.create_file(a[1], w32.GENERIC_WRITE, 7, w32.OPEN_EXISTING)
        if h is None:
            return out(action=act, ok=False, error=w32.ename(err))
        ok, err = w32.write_all(h, EDIT)
        w32.flush(h)
        w32.close(h)
        return out(action=act, ok=ok, error=None if ok else w32.ename(err),
                   result_sha256=result_sha(a[1]) if ok else None)
    if act == "inplace_py":
        try:
            with open(a[1], "r+b") as f:
                f.write(EDIT)
            return out(action=act, ok=True, result_sha256=result_sha(a[1]))
        except OSError as e:
            return out(action=act, ok=False, error="%s winerror=%s" % (type(e).__name__,
                                                                     getattr(e, "winerror", None)))
    if act in ("replacefile", "movereplace"):
        tmp = a[1] + ".~edit%d" % os.getpid()
        ok, err = w32.write_new_file(tmp, EDIT)
        if not ok:
            return out(action=act, ok=False, stage="temp", error=w32.ename(err))
        if act == "replacefile":
            ok, err = replace_file(a[1], tmp)
        else:
            ok, err = move_file_ex(tmp, a[1], MOVEFILE_REPLACE_EXISTING)
        leftover = os.path.exists(tmp)
        return out(action=act, ok=ok, error=None if ok else w32.ename(err), temp_left=leftover,
                   temp=os.path.basename(tmp), result_sha256=result_sha(a[1]) if ok else None)
    if act == "delete":
        ok, err = delete_file(a[1])
        return out(action=act, ok=ok, error=None if ok else w32.ename(err))
    if act == "rename":
        ok, err = move_file_ex(a[1], a[2], 0)
        return out(action=act, ok=ok, error=None if ok else w32.ename(err))
    if act == "create":
        ok, err = w32.write_new_file(a[1], b"UNEXPECTED OCCUPANT %d\n" % os.getpid())
        return out(action=act, ok=ok, error=None if ok else w32.ename(err))
    if act == "lock":
        h, err = w32.create_file(a[1], w32.GENERIC_READ | w32.GENERIC_WRITE, 0, w32.OPEN_ALWAYS,
                                 inherit=False)
        if h is None:
            return out(action=act, ok=False, state="REFUSED", error=w32.ename(err))
        out(action=act, ok=True, state="ACQUIRED", inheritable=w32.handle_inheritable(h),
            file_id=w32.file_id(h), created=(w32.TRACE[-1].get("last_error_after_success")
                                              != "ERROR_ALREADY_EXISTS(183)"))
        sys.stdin.readline()
        w32.close(h)
        return
    raise SystemExit("unknown action " + act)


if __name__ == "__main__":
    main(sys.argv[1:])
