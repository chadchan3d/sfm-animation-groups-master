# -*- coding: utf-8 -*-
"""Production Normalizer Integration (2026-09-22), Section 6/9: functional
qualification for `native_master_protect_acquire`/`native_master_protect_
release`, extracted VERBATIM (exact line range, SHA-256 pinned, the same
range already proven to exec cleanly by test_normalizer_integration_
bootstrap.py) from the real, now-integrated frozen production Normalizer.

Proves, against a REAL file on disk (never the canonical Master):
  - acquire() returns a real, usable handle while the file remains
    readable by a second, independent handle (FILE_SHARE_READ preserved);
  - a concurrent WRITE-mode open from a second handle is DENIED while the
    protect handle is held (the actual protection this mechanism exists
    to provide);
  - release() frees the handle -- a subsequent write-mode open succeeds
    again;
  - acquire() against a nonexistent path returns None rather than raising
    (never aborts the run merely because protection could not be
    acquired -- purely additive to the existing SHA-256 stability
    checks, per this function's own docstring).

Windows-only (uses ctypes/kernel32 CreateFileW directly, matching the
extracted code itself). Never launches SFM. Read-only with respect to
the frozen production Normalizer and the canonical Master.
"""
import ctypes
import hashlib
import os
import sys
import tempfile

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

FROZEN_NORMALIZER_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py"
)
EXPECTED_FROZEN_NORMALIZER_SHA256 = (
    "f69a57436d46252fb78d9ae2a2155d7206e07869c74ac5f4d28f6676f5ef2cf0"
)

# Same range as test_normalizer_integration_bootstrap.py's BOOTSTRAP_BLOCK_RANGE
# (the native_master_protect_* functions live at the tail of that same block).
BLOCK_RANGE = (176, 352)
EXPECTED_BLOCK_SHA256 = "d6a96f5ee175669edcfecf9eb3744574eaee22fe9480c3102e77e33aca1c5cc6"

_GENERIC_WRITE = 0x40000000
_FILE_SHARE_READ = 0x00000001
_OPEN_EXISTING = 3
_FILE_ATTRIBUTE_NORMAL = 0x00000080
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


def _try_open_for_write(path):
    """Independent, minimal probe (deliberately NOT reusing the extracted
    function itself) -- opens `path` for GENERIC_WRITE with only
    FILE_SHARE_READ allowed on ITS OWN side, matching how a real editor/
    writer would attempt to open the Master TXT. Returns True if the open
    succeeded (and immediately closes it), False if CreateFileW failed."""
    kernel32 = ctypes.windll.kernel32
    create_file_w = kernel32.CreateFileW
    create_file_w.argtypes = [
        ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
        ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
    ]
    create_file_w.restype = ctypes.c_void_p
    handle = create_file_w(
        path, _GENERIC_WRITE, _FILE_SHARE_READ, None,
        _OPEN_EXISTING, _FILE_ATTRIBUTE_NORMAL, None,
    )
    if handle is None or handle == _INVALID_HANDLE_VALUE:
        return False
    kernel32.CloseHandle(handle)
    return True


def main():
    with open(FROZEN_NORMALIZER_PATH, "rb") as f:
        data = f.read()
    actual = hashlib.sha256(data).hexdigest()
    check("source.frozen_normalizer_sha256_pinned", actual == EXPECTED_FROZEN_NORMALIZER_SHA256, actual)

    text = data.decode("ascii")
    lines = text.splitlines()
    start, end = BLOCK_RANGE
    block = "\n".join(lines[start - 1:end]) + "\n"
    block_sha = hashlib.sha256(block.encode("ascii")).hexdigest()
    check("source.block_sha256_pinned", block_sha == EXPECTED_BLOCK_SHA256, block_sha)

    ns = {"os": os, "sys": sys, "ctypes": ctypes}
    # sys.executable/sys.path aren't exercised by the protect functions
    # themselves, but the block as a whole still needs a real package to
    # import successfully -- reuse the same fake layout as the bootstrap
    # test rather than duplicating that machinery here would be cleaner,
    # but this file's own scope is narrowly the two protect functions, so
    # a minimal stub for the parts of the block THEY don't depend on is
    # simpler and keeps this file self-contained; the FULL block (including
    # the authority bootstrap/import portion) is already proven to exec
    # cleanly by test_normalizer_integration_bootstrap.py against a real
    # package layout -- re-proving that here would be redundant.
    import shutil
    fake_root = tempfile.mkdtemp(prefix="pb_normalizer_native_protect_")
    try:
        game_dir = os.path.join(fake_root, "game")
        mainmenu_dir = os.path.join(game_dir, "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D")
        os.makedirs(mainmenu_dir)
        fake_exe = os.path.join(game_dir, "sfm.exe")
        with open(fake_exe, "wb") as f:
            f.write(b"not a real executable\n")

        _this_dir = os.path.dirname(os.path.abspath(__file__))
        shutil.copytree(
            os.path.join(_this_dir, "candidate_b2c_correction6", "sfm_master_authority_productionized"),
            os.path.join(mainmenu_dir, "sfm_master_authority_productionized"),
            ignore=shutil.ignore_patterns("*.pyc", "__pycache__"),
        )
        shutil.copytree(
            r"E:\SFM Animation Group Master\tools\sfm_master_sidecar",
            os.path.join(mainmenu_dir, "sfm_master_sidecar"),
            ignore=shutil.ignore_patterns("*.pyc", "__pycache__"),
        )

        sys.executable = fake_exe
        if mainmenu_dir not in sys.path:
            sys.path.insert(0, mainmenu_dir)

        try:
            exec(compile(block, "<native_protect_block_extract>", "exec"), ns)
            check("block.execs_without_exception", True)
        except Exception as exc:
            check("block.execs_without_exception", False, exc)
            ns = None
    finally:
        shutil.rmtree(fake_root, ignore_errors=True)

    if ns is None:
        print("\nRESULT: %d/%d SOME FAILED (block did not exec)" % (
            sum(1 for _, c in RESULTS if c), len(RESULTS)))
        sys.exit(1)

    acquire_fn = ns["native_master_protect_acquire"]
    release_fn = ns["native_master_protect_release"]

    test_root = tempfile.mkdtemp(prefix="pb_normalizer_native_protect_target_")
    try:
        target_path = os.path.join(test_root, "fake_master.txt")
        with open(target_path, "wb") as f:
            f.write(b"placeholder Master-like content\n")

        check("negative.acquire_on_nonexistent_path_returns_none",
              acquire_fn(os.path.join(test_root, "does_not_exist.txt")) is None)

        handle = acquire_fn(target_path)
        check("acquire.returns_a_real_handle", handle is not None and handle != _INVALID_HANDLE_VALUE, handle)

        with open(target_path, "rb") as f:
            readable_while_held = f.read() == b"placeholder Master-like content\n"
        check("acquire.readers_remain_unaffected_while_held", readable_while_held)

        write_denied_while_held = not _try_open_for_write(target_path)
        check("acquire.write_open_denied_while_held", write_denied_while_held)

        release_fn(handle)

        write_allowed_after_release = _try_open_for_write(target_path)
        check("release.write_open_allowed_after_release", write_allowed_after_release)

        # release() must never raise, including on a None handle or a
        # double-release of an already-closed handle.
        try:
            release_fn(None)
            release_fn(handle)
            check("release.never_raises_on_none_or_double_release", True)
        except Exception as exc:
            check("release.never_raises_on_none_or_double_release", False, exc)
    finally:
        shutil.rmtree(test_root, ignore_errors=True)

    print("\nRESULT: %d/%d %s" % (
        sum(1 for _, c in RESULTS if c), len(RESULTS),
        "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
    ))
    if not all(condition for _, condition in RESULTS):
        sys.exit(1)


if __name__ == "__main__":
    main()
