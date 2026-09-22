# -*- coding: utf-8 -*-
"""Production Normalizer Integration (2026-09-22, corrected same day per
independent audit), Section 6/9: functional qualification for
`native_master_protect_acquire`/`native_master_protect_release` AND the
fail-closed call-site gate in `run_target_transaction()` that now REQUIRES
a real protect handle before proceeding toward native Rebuild.

Correction context: the independent audit found the original checkpoint
left protection fail-OPEN -- `native_master_protect_acquire(...) -> None`
did not abort the command. The fix, verified here, is at the CALL SITE,
not the primitive: `native_master_protect_acquire()` itself still never
raises (it returns a real handle or `None`), but the call site
immediately raises `ProbeError` on `None`, before `self.assert_master_
stable()` or native Rebuild ever run.

Both the primitive pair and the fail-closed call-site snippet are
extracted VERBATIM (exact line ranges, SHA-256 pinned) from the real,
now-corrected frozen production Normalizer.

Proves, against REAL files on disk (never the canonical Master):
  - acquire() returns a real, usable handle while the file remains
    readable by a second, independent handle (FILE_SHARE_READ preserved);
  - a concurrent WRITE-mode open from a second handle is DENIED while the
    protect handle is held (the actual protection this mechanism exists
    to provide);
  - release() frees the handle -- a subsequent write-mode open succeeds
    again;
  - acquire() against a nonexistent path returns None (primitive-level
    fact, unchanged);
  - acquire() against a path an ALREADY-OPEN, fully-exclusive writer
    holds (the race-relevant failure mode named by the audit) also
    returns None;
  - THE GATE: when acquire() would return None (either failure mode
    above), the extracted call-site snippet raises ProbeError and NEVER
    reaches `self.assert_master_stable()` -- i.e. never proceeds toward
    the protected native-mutation window without a real handle;
  - THE GATE, positive case: when acquire() succeeds, the snippet does
    NOT raise, and DOES reach `self.assert_master_stable()`.

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
    "88805dbbcebf8c813a97b5346194ff546ecd2a0ef7c6ab47192734b41e1fa2ef"
)

# 1-indexed, inclusive. Re-verify with: sed -n '<start>,<end>p' Rebuild_Control_Groups_Normalizer.py
# The bootstrap block (same range test_normalizer_integration_bootstrap.py
# uses -- the native_master_protect_* functions live at its tail).
BLOCK_RANGE = (176, 361)
EXPECTED_BLOCK_SHA256 = "7be3dae59f0c536fccf11fac0ab9eccd665a4359895c2b7bf4cee4c0714571cd"

# The fail-closed gate snippet inside run_target_transaction(): acquires
# the handle, raises ProbeError on None, otherwise calls
# self.assert_master_stable(). Method-body indentation (8 spaces).
GATE_RANGE = (11271, 11285)
EXPECTED_GATE_SHA256 = "ad923039edb1e5fa46de9c79fe977f8c20058d178cca91b829fee8a5a7f64ab3"

_GENERIC_WRITE = 0x40000000
_GENERIC_READ = 0x80000000
_FILE_SHARE_READ = 0x00000001
_OPEN_EXISTING = 3
_FILE_ATTRIBUTE_NORMAL = 0x00000080
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

_create_file_w = ctypes.windll.kernel32.CreateFileW
_create_file_w.argtypes = [
    ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
    ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
]
_create_file_w.restype = ctypes.c_void_p


def _try_open_for_write(path):
    """Independent, minimal probe (deliberately NOT reusing the extracted
    function itself) -- opens `path` for GENERIC_WRITE with only
    FILE_SHARE_READ allowed on ITS OWN side, matching how a real editor/
    writer would attempt to open the Master TXT. Returns True if the open
    succeeded (and immediately closes it), False if CreateFileW failed."""
    handle = _create_file_w(
        path, _GENERIC_WRITE, _FILE_SHARE_READ, None,
        _OPEN_EXISTING, _FILE_ATTRIBUTE_NORMAL, None,
    )
    if handle is None or handle == _INVALID_HANDLE_VALUE:
        return False
    ctypes.windll.kernel32.CloseHandle(handle)
    return True


def _open_fully_exclusive(path):
    """Opens `path` with dwShareMode=0 -- no sharing at all, simulating
    an already-open conflicting writer/editor. Any subsequent
    CreateFileW call against this path (even a pure FILE_SHARE_READ-only
    read attempt) fails with a sharing violation while this handle is
    held -- this is the race-relevant conflict the audit named."""
    handle = _create_file_w(
        path, _GENERIC_READ | _GENERIC_WRITE, 0, None,
        _OPEN_EXISTING, _FILE_ATTRIBUTE_NORMAL, None,
    )
    if handle is None or handle == _INVALID_HANDLE_VALUE:
        return None
    return handle


class ProbeError(Exception):
    pass


class FakeSelf(object):
    def __init__(self, master_path):
        self.master_path = master_path
        self.assert_master_stable_calls = 0

    def assert_master_stable(self):
        self.assert_master_stable_calls += 1


def _read_and_verify_normalizer():
    with open(FROZEN_NORMALIZER_PATH, "rb") as f:
        data = f.read()
    actual = hashlib.sha256(data).hexdigest()
    if actual != EXPECTED_FROZEN_NORMALIZER_SHA256:
        raise AssertionError(
            "frozen Normalizer SHA-256 mismatch: expected %s, got %s"
            % (EXPECTED_FROZEN_NORMALIZER_SHA256, actual)
        )
    return data.decode("ascii").splitlines()


def _extract(lines, start, end, expected_sha256):
    block = "\n".join(lines[start - 1:end]) + "\n"
    actual = hashlib.sha256(block.encode("ascii")).hexdigest()
    if actual != expected_sha256:
        raise AssertionError(
            "extracted block SHA-256 mismatch: expected %s, got %s -- line range (%d, %d) may be stale"
            % (expected_sha256, actual, start, end)
        )
    return block


def main():
    import shutil

    lines = _read_and_verify_normalizer()
    check("source.frozen_normalizer_sha256_pinned", True)

    block = _extract(lines, BLOCK_RANGE[0], BLOCK_RANGE[1], EXPECTED_BLOCK_SHA256)
    check("source.block_sha256_pinned", True)

    gate_snippet = _extract(lines, GATE_RANGE[0], GATE_RANGE[1], EXPECTED_GATE_SHA256)
    check("source.gate_sha256_pinned", True)

    ns = {"os": os, "sys": sys, "ctypes": ctypes}
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

    # The gate snippet is dedented (8 -> 0) and wrapped in a synthetic
    # top-level function taking `self` -- the snippet's own body text is
    # untouched, matching this project's established method-extraction
    # convention (production_plan_layer.py's preflight_reconciliation_
    # plan_pure). It needs native_master_protect_acquire and ProbeError
    # as free names, exactly as the real file provides them at module
    # scope.
    # The snippet is already indented 8 spaces (method-body level in the
    # real file) -- that is already valid, consistent indentation for a
    # function body, so it is used AS-IS under a new `def` wrapper rather
    # than dedented (dedenting to 0 would leave the body unindented,
    # which is a SyntaxError under a def).
    gate_ns = {"native_master_protect_acquire": acquire_fn, "ProbeError": ProbeError}
    gate_src = "def _extracted_protect_gate(self):\n" + gate_snippet
    exec(compile(gate_src, "<protect_gate_extract>", "exec"), gate_ns)
    protect_gate = gate_ns["_extracted_protect_gate"]

    test_root = tempfile.mkdtemp(prefix="pb_normalizer_native_protect_target_")
    try:
        target_path = os.path.join(test_root, "fake_master.txt")
        with open(target_path, "wb") as f:
            f.write(b"placeholder Master-like content\n")

        # --- Primitive-level facts (native_master_protect_acquire itself) ---
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

        try:
            release_fn(None)
            release_fn(handle)
            check("release.never_raises_on_none_or_double_release", True)
        except Exception as exc:
            check("release.never_raises_on_none_or_double_release", False, exc)

        # --- Sharing-conflict case (the race-relevant failure mode) ---
        conflicting_writer_path = os.path.join(test_root, "conflict_master.txt")
        with open(conflicting_writer_path, "wb") as f:
            f.write(b"placeholder Master-like content\n")
        conflicting_handle = _open_fully_exclusive(conflicting_writer_path)
        check("sharing_conflict.simulated_writer_opened_exclusively",
              conflicting_handle is not None and conflicting_handle != _INVALID_HANDLE_VALUE)
        check("sharing_conflict.acquire_returns_none_while_writer_holds_exclusive",
              acquire_fn(conflicting_writer_path) is None)
        ctypes.windll.kernel32.CloseHandle(conflicting_handle)
        reacquired_handle = acquire_fn(conflicting_writer_path)
        check("sharing_conflict.acquire_succeeds_once_writer_releases", reacquired_handle is not None)
        release_fn(reacquired_handle)  # must not leak -- would otherwise block the next exclusive open below

        # --- THE GATE: fail-closed call-site behavior ---
        fake_ok = FakeSelf(target_path)
        try:
            protect_gate(fake_ok)
            check("gate.positive_case_does_not_raise", True)
        except ProbeError as exc:
            check("gate.positive_case_does_not_raise", False, exc)
        check("gate.positive_case_reaches_assert_master_stable", fake_ok.assert_master_stable_calls == 1)

        fake_missing = FakeSelf(os.path.join(test_root, "does_not_exist.txt"))
        gate_raised_for_missing = False
        try:
            protect_gate(fake_missing)
        except ProbeError:
            gate_raised_for_missing = True
        check("gate.nonexistent_path_raises_probeerror", gate_raised_for_missing)
        check("gate.nonexistent_path_never_reaches_assert_master_stable",
              fake_missing.assert_master_stable_calls == 0)

        conflicting_handle2 = _open_fully_exclusive(conflicting_writer_path)
        check("sharing_conflict.second_simulated_writer_opened_exclusively",
              conflicting_handle2 is not None and conflicting_handle2 != _INVALID_HANDLE_VALUE,
              conflicting_handle2)
        fake_conflict = FakeSelf(conflicting_writer_path)
        gate_raised_for_conflict = False
        try:
            protect_gate(fake_conflict)
        except ProbeError:
            gate_raised_for_conflict = True
        check("gate.sharing_conflict_raises_probeerror", gate_raised_for_conflict)
        check("gate.sharing_conflict_never_reaches_assert_master_stable",
              fake_conflict.assert_master_stable_calls == 0)
        ctypes.windll.kernel32.CloseHandle(conflicting_handle2)
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
