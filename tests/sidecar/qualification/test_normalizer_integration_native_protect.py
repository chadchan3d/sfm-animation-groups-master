# -*- coding: utf-8 -*-
"""Production Normalizer Integration (2026-09-22, corrected a second time
per independent re-audit), Section 6/9: protection-LIFETIME qualification
for `native_master_protect_acquire`/`native_master_protect_release` and
their call site in `run_target_transaction()`.

Correction context: the first fail-closed correction closed the "acquire
returns None but the run continues anyway" defect. The independent
re-audit then found a NARROWER remaining defect: a *successfully*
acquired handle could still leak, because it was acquired several
potentially-raising statements (most importantly `self.assert_master_
stable()` itself) BEFORE the try/finally that owned its release. If any
of those statements raised, execution never reached the `finally` that
calls `native_master_protect_release()`.

The fix moves acquisition to immediately before the existing transaction
`try:`, and moves `self.assert_master_stable()` to be the FIRST statement
INSIDE that `try:` -- so every potentially-raising operation between a
successful acquire and the handle's release now runs strictly inside the
one `try/finally` that owns it. `None` still correctly raises BEFORE the
`try:` (no real handle exists yet to release in that case).

This file proves the correction two ways:

1. **AST/structural proof** (the audit's own preferred approach, since
   the real `try:` body is ~1000 lines including native Rebuild and
   dozens of dependencies this offline harness cannot execute): the
   ENTIRE `run_target_transaction()` method is extracted verbatim
   (exact line range, SHA-256 pinned) and parsed with Python's `ast`
   module. It asserts, directly against the real production AST, that:
     - the acquire assignment is immediately followed by the None-check
       `if`, which is immediately followed by the `try:` (no other
       statement -- and therefore no other chance to raise -- sits
       between a successful acquire and the try that owns its release);
     - the `try:`'s FIRST body statement is `self.assert_master_stable()`
       (the protected hash is the first protected operation, before
       Undo is disabled and before native Rebuild);
     - the `try:`'s `finally:` clause's FIRST statement releases the
       handle via `native_master_protect_release(...)`, itself wrapped
       in its own inner try/except (so a release failure cannot skip
       the rest of the real finally's other cleanup, unchanged from
       before).

2. **Functional, runnable proof**, using the REAL, verbatim-extracted
   `native_master_protect_acquire`/`native_master_protect_release`
   primitives (unchanged since the first correction -- their own
   extracted bodies hash identically) inside a small, explicitly-labeled
   SYNTHETIC skeleton that mirrors EXACTLY the structure the AST proof
   above establishes (acquire -> None-check -> try: assert_master_
   stable() ... finally: release()) -- never a hand-invented shape. This
   proves, against real Windows handles:
     - acquisition failure still raises ProbeError and never reaches the
       protected hash/native path;
     - successful acquisition + a non-raising protected hash proceeds
       normally, and the handle is still released afterward;
     - successful acquisition + `assert_master_stable()` RAISING still
       releases the handle (the exact defect this correction closes);
     - after that forced failure, an independent write-mode open of the
       SAME test file succeeds, proving the Windows handle was actually
       closed, not merely that Python's `finally` ran;
     - the sharing-conflict fail-closed behavior (an already-open,
       fully-exclusive simulated writer) remains intact.

Windows-only (uses ctypes/kernel32 CreateFileW directly). Never launches
SFM. Read-only with respect to the frozen production Normalizer and the
canonical Master.
"""
import ast
import ctypes
import hashlib
import os
import sys
import tempfile
import textwrap

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
    "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"
)

# 1-indexed, inclusive. Re-verify with: sed -n '<start>,<end>p' Rebuild_Control_Groups_Normalizer.py
# The bootstrap block (native_master_protect_acquire/release primitives).
BLOCK_RANGE = (176, 361)
EXPECTED_BLOCK_SHA256 = "7be3dae59f0c536fccf11fac0ab9eccd665a4359895c2b7bf4cee4c0714571cd"

# The acquire + fail-closed None-check, at its NEW location (immediately
# before the transaction try:, per this correction).
ACQUIRE_GATE_RANGE = (11374, 11386)
EXPECTED_ACQUIRE_GATE_SHA256 = "c344979dc47c3ce661a667336007a1315f553855027ba06e93a16d37ced1159e"

# The entire run_target_transaction() method -- for AST structural
# analysis only, never exec'd (it references shot/aset/dm/native
# Rebuild/etc. this offline harness cannot provide).
METHOD_RANGE = (11198, 12224)
EXPECTED_METHOD_SHA256 = "6a2151959890230a822af1596abf4333eeb5882783ef4e6ea690df8f6db4777d"

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
    FILE_SHARE_READ allowed on ITS OWN side. Returns True if the open
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
    an already-open conflicting writer/editor."""
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
    def __init__(self, master_path, stability_raises=False):
        self.master_path = master_path
        self._stability_raises = stability_raises
        self.assert_master_stable_calls = 0

    def assert_master_stable(self):
        self.assert_master_stable_calls += 1
        if self._stability_raises:
            raise RuntimeError("simulated Master instability during native Rebuild window")


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


# ---------------------------------------------------------------------------
# 1. AST/structural proof.
# ---------------------------------------------------------------------------

def _is_call_to(node, name):
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == name
    )


def _is_self_method_call(node, method_name):
    if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)):
        return False
    func = node.value.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == method_name
        and isinstance(func.value, ast.Name)
        and func.value.id == "self"
    )


def _is_assign_from_call(node, target_name, call_name):
    return (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == target_name
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == call_name
    )


def _try_shape(node):
    """Normalizes try-statement shape across Python 2/3 AST differences.
    Python 3 has one unified `ast.Try` (body/handlers/orelse/finalbody).
    Python 2 splits this into `ast.TryFinally` (body/finalbody) and
    `ast.TryExcept` (body/handlers/orelse, no finalbody). A single
    try/except/finally (our OUTER try, which has both `except
    ContextualCompositionSuccess`/`except NativePostFallback` AND a
    `finally`) is represented in Python 2 as a `TryFinally` whose own
    `body` is a list containing exactly one nested `TryExcept` -- that
    nested node's `body` is unwrapped here to get the real first
    statements (e.g. `self.assert_master_stable()`), not the wrapper
    list. Returns (body, finalbody) if `node` is try-like, else None;
    `finalbody` is `[]` for a plain try/except with no finally."""
    try_type = getattr(ast, "Try", None)
    if try_type is not None and isinstance(node, try_type):
        return node.body, node.finalbody
    try_finally_type = getattr(ast, "TryFinally", None)
    try_except_type = getattr(ast, "TryExcept", None)
    if try_finally_type is not None and isinstance(node, try_finally_type):
        body = node.body
        if len(body) == 1 and try_except_type is not None and isinstance(body[0], try_except_type):
            body = body[0].body
        return body, node.finalbody
    if try_except_type is not None and isinstance(node, try_except_type):
        return node.body, []
    return None


def run_ast_structural_proof(method_source):
    tree = ast.parse(textwrap.dedent(method_source))
    func_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "run_target_transaction"]
    check("ast.method_found", len(func_defs) == 1, len(func_defs))
    if len(func_defs) != 1:
        return
    body = func_defs[0].body

    acquire_idx = None
    for i, stmt in enumerate(body):
        if _is_assign_from_call(stmt, "native_master_protect_handle", "native_master_protect_acquire"):
            acquire_idx = i
            break
    check("ast.acquire_assignment_found", acquire_idx is not None)
    if acquire_idx is None:
        return

    none_check = body[acquire_idx + 1] if acquire_idx + 1 < len(body) else None
    is_none_check_if = (
        isinstance(none_check, ast.If)
        and isinstance(none_check.test, ast.Compare)
        and isinstance(none_check.test.left, ast.Name)
        and none_check.test.left.id == "native_master_protect_handle"
    )
    check("ast.none_check_immediately_follows_acquire", is_none_check_if)

    try_node = body[acquire_idx + 2] if acquire_idx + 2 < len(body) else None
    outer_shape = _try_shape(try_node) if try_node is not None else None
    check("ast.try_immediately_follows_none_check_no_gap", outer_shape is not None)
    if outer_shape is None:
        return
    outer_body, outer_finalbody = outer_shape

    first_try_stmt = outer_body[0] if outer_body else None
    check("ast.first_statement_in_try_is_assert_master_stable",
          _is_self_method_call(first_try_stmt, "assert_master_stable"))

    check("ast.try_has_finally", len(outer_finalbody) > 0)
    if not outer_finalbody:
        return

    inner_shape = _try_shape(outer_finalbody[0])
    check("ast.finally_first_statement_is_inner_try", inner_shape is not None)
    if inner_shape is not None:
        inner_body, _inner_finalbody = inner_shape
        release_call_found = bool(inner_body) and _is_call_to(inner_body[0], "native_master_protect_release")
        check("ast.finally_inner_try_releases_handle_first", release_call_found)


# ---------------------------------------------------------------------------
# 2. Functional proof, via a synthetic skeleton mirroring the AST-proven shape.
# ---------------------------------------------------------------------------

_SKELETON_SOURCE = """
def _skeleton(self):
    native_master_protect_handle = native_master_protect_acquire(self.master_path)
    if native_master_protect_handle is None:
        raise ProbeError("required native Master protection handle unavailable")
    try:
        self.assert_master_stable()
    finally:
        try:
            native_master_protect_release(native_master_protect_handle)
        except Exception:
            pass
"""


def main():
    lines = _read_and_verify_normalizer()
    check("source.frozen_normalizer_sha256_pinned", True)

    block = _extract(lines, BLOCK_RANGE[0], BLOCK_RANGE[1], EXPECTED_BLOCK_SHA256)
    check("source.block_sha256_pinned", True)

    method_source = _extract(lines, METHOD_RANGE[0], METHOD_RANGE[1], EXPECTED_METHOD_SHA256)
    check("source.method_sha256_pinned", True)

    _extract(lines, ACQUIRE_GATE_RANGE[0], ACQUIRE_GATE_RANGE[1], EXPECTED_ACQUIRE_GATE_SHA256)
    check("source.acquire_gate_sha256_pinned", True)

    run_ast_structural_proof(method_source)

    ns = {"os": os, "sys": sys, "ctypes": ctypes}
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

    skeleton_ns = {
        "native_master_protect_acquire": acquire_fn,
        "native_master_protect_release": release_fn,
        "ProbeError": ProbeError,
    }
    exec(compile(_SKELETON_SOURCE, "<synthetic_skeleton_mirroring_ast_proven_shape>", "exec"), skeleton_ns)
    skeleton = skeleton_ns["_skeleton"]

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
        check("release.write_open_allowed_after_release", _try_open_for_write(target_path))

        # --- Sharing-conflict case (the race-relevant failure mode) ---
        conflict_path = os.path.join(test_root, "conflict_master.txt")
        with open(conflict_path, "wb") as f:
            f.write(b"placeholder Master-like content\n")
        conflicting_handle = _open_fully_exclusive(conflict_path)
        check("sharing_conflict.simulated_writer_opened_exclusively",
              conflicting_handle is not None and conflicting_handle != _INVALID_HANDLE_VALUE)
        check("sharing_conflict.acquire_returns_none_while_writer_holds_exclusive",
              acquire_fn(conflict_path) is None)
        ctypes.windll.kernel32.CloseHandle(conflicting_handle)
        reacquired = acquire_fn(conflict_path)
        check("sharing_conflict.acquire_succeeds_once_writer_releases", reacquired is not None)
        release_fn(reacquired)

        # --- Functional lifecycle proof, via the AST-proven-shape skeleton ---

        # 2a. Acquisition failure -> ProbeError, never reaches protected hash.
        fake_missing = FakeSelf(os.path.join(test_root, "does_not_exist.txt"))
        raised = False
        try:
            skeleton(fake_missing)
        except ProbeError:
            raised = True
        check("lifecycle.missing_path_raises_probeerror", raised)
        check("lifecycle.missing_path_never_reaches_protected_hash",
              fake_missing.assert_master_stable_calls == 0)

        # 2b. Successful acquisition + successful protected hash -> proceeds
        #     normally, handle released afterward.
        fake_ok = FakeSelf(target_path, stability_raises=False)
        skeleton(fake_ok)  # must not raise
        check("lifecycle.success_path_reaches_protected_hash", fake_ok.assert_master_stable_calls == 1)
        check("lifecycle.success_path_releases_handle", _try_open_for_write(target_path))

        # 2c. THE DEFECT THIS CORRECTION CLOSES: successful acquisition +
        #     assert_master_stable() RAISING must still release the handle.
        target_path_2 = os.path.join(test_root, "fake_master_2.txt")
        with open(target_path_2, "wb") as f:
            f.write(b"placeholder Master-like content\n")
        fake_raises = FakeSelf(target_path_2, stability_raises=True)
        stability_raised = False
        try:
            skeleton(fake_raises)
        except RuntimeError:
            stability_raised = True
        check("lifecycle.stability_check_actually_raised", stability_raised)
        check("lifecycle.handle_released_even_though_stability_check_raised",
              _try_open_for_write(target_path_2))
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
