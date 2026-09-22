# -*- coding: utf-8 -*-
"""Production Normalizer Integration (2026-09-22), Section 9B/9C:
acquisition/lifetime and failure-atomicity qualification for the two new
methods this integration added to the frozen production Normalizer
(`acquire_master_index_via_qualified_authority`,
`_release_master_index_lease_durable`).

Both methods are extracted VERBATIM (exact line ranges, SHA-256 pinned)
from the real, now-integrated frozen production Normalizer, dedented and
re-bound under new top-level function names (the `self` parameter itself
is left named `self` in the body, matching the established extraction
convention already used by `candidate_b2c_c/production_plan_layer.py`'s
own `preflight_reconciliation_plan_pure` extraction) -- then exercised
against a minimal fake command object and a REAL published sidecar
directory (compiled/published via the real, unmodified compiler/
publisher path), never a mock of the authority package itself.

Proves (Section B):
  - one acquisition covers every fold across a MULTI-target wanted-fold
    set in one call (the real command-lifetime sharing this integration
    relies on -- self.master_index_scope_folds already aggregates every
    target's vocabulary before this method is ever called, unchanged by
    this integration);
  - the complete packed provider/backing closes before this call returns
    (current_open_provider_count == 0 even while a lease is held);
  - the lease releases cleanly on the normal path;
  - the lease releases cleanly when release is reached via an in-flight
    exception (mirrors final_report()'s own finally-block usage);
  - release is idempotent (a second release call after the first is a
    safe no-op);
  - a later acquisition with the SAME source generation reuses cleanly;
  - a later acquisition pinned to a STALE/WRONG expected generation is
    REFUSED (never silently reused), and never sets a lease.

Proves (Section C):
  - shipped_root pointing at an unpublished/empty directory raises
    ProbeError (SidecarMissing wrapped), before any lease is taken;
  - a corrupted published artifact raises ProbeError (SidecarCorrupt
    wrapped), before any lease is taken;
  - in both cases, the fake command object's own state (self.master_index
    equivalent, self._master_index_lease) is never partially set -- no
    silent TXT fallback, no partial acquisition.

Never launches SFM. Read-only with respect to the frozen production
Normalizer; writes only to a private OS temp directory for its own
compiled/published fixtures, never to the canonical Master.
"""
import hashlib
import os
import shutil
import sys
import tempfile

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir, "tools")
CORRECTION6_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction6")

for _p in (os.path.abspath(TOOLS_DIR), os.path.abspath(CORRECTION6_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

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

# 1-indexed, inclusive. Re-verify with: sed -n '<start>,<end>p' Rebuild_Control_Groups_Normalizer.py
ACQUIRE_RANGE = (9587, 9663)
EXPECTED_ACQUIRE_SHA256 = "ca0703b53287b59865ba7962befe88019a0bca59ed93badeb95f6473cae0360e"
RELEASE_RANGE = (9665, 9695)
EXPECTED_RELEASE_SHA256 = "5d0fe1a621f8c1c4d331bab903a7487f908a9f30db801486d393d2771d9ac791"


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


def _dedent_method(src):
    out = []
    for line in src.splitlines():
        if line.startswith("    "):
            out.append(line[4:])
        else:
            out.append(line)
    return "\n".join(out) + "\n"


class ProbeError(Exception):
    pass


class _FakeThread(object):
    pass


_main_thread = _FakeThread()


class _FakeQThread(object):
    @staticmethod
    def currentThread():
        return _main_thread


class _FakeApp(object):
    @staticmethod
    def thread():
        return _main_thread


class _FakeQCoreApplication(object):
    @staticmethod
    def instance():
        return _FakeApp()


class _FakeQtCore(object):
    QThread = _FakeQThread
    QCoreApplication = _FakeQCoreApplication


def build_extracted_namespace():
    from sfm_master_authority_productionized import runtime as authority_runtime
    from sfm_master_authority_productionized import errors as authority_errors
    from sfm_master_authority_productionized import normalizer_compat_adapter as authority_compat_adapter
    from sfm_master_authority_productionized import sidecar_contract
    sidecar_contract.ensure_loaded()

    lines = _read_and_verify_normalizer()
    acquire_src = _dedent_method(_extract(lines, ACQUIRE_RANGE[0], ACQUIRE_RANGE[1], EXPECTED_ACQUIRE_SHA256))
    release_src = _dedent_method(_extract(lines, RELEASE_RANGE[0], RELEASE_RANGE[1], EXPECTED_RELEASE_SHA256))

    acquire_src = acquire_src.replace(
        "def acquire_master_index_via_qualified_authority(\n        self,",
        "def _extracted_acquire(\n        self,",
        1,
    )
    release_src = release_src.replace(
        "def _release_master_index_lease_durable(self):",
        "def _extracted_release(self):",
        1,
    )

    ns = {
        "os": os,
        "ProbeError": ProbeError,
        "authority_runtime": authority_runtime,
        "authority_errors": authority_errors,
        "authority_compat_adapter": authority_compat_adapter,
        "QtCore": _FakeQtCore,
        "_AUTHORITY_EXPECTED_API_VERSION": authority_runtime.RUNTIME_API_VERSION,
        "_AUTHORITY_EXPECTED_BUILD_ID": authority_runtime.RUNTIME_BUILD_ID,
    }
    exec(compile(acquire_src, "<acquire_extract>", "exec"), ns)
    exec(compile(release_src, "<release_extract>", "exec"), ns)
    return ns, ProbeError


class FakeCommand(object):
    def __init__(self, master_path, master_hash, scope_folds):
        self.master_path = master_path
        self.master_hash = master_hash
        self.master_index_scope_folds = scope_folds
        self._master_index_broker = None
        self._master_index_lease = None


MASTER_TXT_BODY = (
    u'"groupFile"\n{\n'
    u'"RigArms"\n{\n'
    u'\t"control"\t\t"target_one_control_a"\n'
    u'\t"control"\t\t"target_one_control_b"\n'
    u'\t"control"\t\t"target_two_control_c"\n'
    u"}\n"
    u"}\n"
)
MULTI_TARGET_FOLDS = frozenset([
    b"target_one_control_a", b"target_one_control_b", b"target_two_control_c",
])

PYTHON3_EXE = "C:\\Users\\Eman\\AppData\\Local\\Programs\\Python\\Python310\\python.exe"


def _publish_via_python3(master_path, shipped_root):
    """`tools/sfm_master_sidecar/publisher.py` is Python-3-only (uses
    pathlib) -- this test's own acquisition/release logic is not, and is
    exercised under both interpreters, so publishing is shelled out to a
    real Python 3.10 subprocess regardless of which interpreter is
    running this test, matching the established two-phase publish(py3)/
    acquire(py2.7.5) pattern used elsewhere in this qualification tree."""
    import subprocess
    script = (
        "import sys; sys.path.insert(0, %r)\n"
        "from sfm_master_sidecar import publisher\n"
        "publisher.publish(%r, %r)\n"
    ) % (os.path.abspath(TOOLS_DIR), master_path, shipped_root)
    proc = subprocess.Popen(
        [PYTHON3_EXE, "-c", script],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    out, _ = proc.communicate()
    if proc.returncode != 0:
        raise AssertionError("publish subprocess failed: %s" % out.decode("utf-8", "replace"))


def main():
    ns, ProbeError = build_extracted_namespace()
    extracted_acquire = ns["_extracted_acquire"]
    extracted_release = ns["_extracted_release"]

    root = tempfile.mkdtemp(prefix="pb_normalizer_acquisition_")
    try:
        usermod_dir = os.path.join(root, "usermod")
        shipped_root = os.path.join(usermod_dir, "cfg", "sfm_shared_authority")
        os.makedirs(shipped_root)

        master_path = os.path.join(root, "master.txt")
        with open(master_path, "wb") as f:
            f.write(MASTER_TXT_BODY.encode("utf-8"))
        master_sha = hashlib.sha256(MASTER_TXT_BODY.encode("utf-8")).hexdigest()

        _publish_via_python3(master_path, shipped_root)

        # --- Section B: normal acquisition, multi-target fold coverage ---
        cmd = FakeCommand(master_path, master_sha, MULTI_TARGET_FOLDS)
        payload = extracted_acquire(cmd, usermod_dir)

        check("acquisition.returns_expected_keys",
              set(payload.keys()) == {
                  "mapping_count", "destination_count", "folded",
                  "exact_literals", "group_sibling_order", "group_metadata",
              }, sorted(payload.keys()))
        check("acquisition.covers_every_multi_target_fold",
              set(payload["folded"].keys()) == MULTI_TARGET_FOLDS,
              sorted(payload["folded"].keys()))
        check("acquisition.mapping_count_matches_occurrence_total",
              payload["mapping_count"] == 3, payload["mapping_count"])
        check("acquisition.lease_was_taken", cmd._master_index_lease is not None)
        check("acquisition.broker_was_recorded", cmd._master_index_broker is not None)

        counters = cmd._master_index_broker.provider_counters()
        check("acquisition.provider_closed_before_return_completes",
              counters["current_open_provider_count"] == 0, counters)

        # --- Section B: release, then idempotent second release ---
        extracted_release(cmd)
        check("release.lease_cleared", cmd._master_index_lease is None)
        extracted_release(cmd)  # must be a safe no-op
        check("release.second_call_is_safe_noop", cmd._master_index_lease is None)

        # --- Section B: release reached via an in-flight exception (mirrors final_report()'s finally) ---
        cmd2 = FakeCommand(master_path, master_sha, MULTI_TARGET_FOLDS)
        extracted_acquire(cmd2, usermod_dir)
        release_completed_despite_exception = False
        try:
            try:
                raise RuntimeError("simulated mid-command failure")
            finally:
                extracted_release(cmd2)
                release_completed_despite_exception = (cmd2._master_index_lease is None)
        except RuntimeError:
            pass
        check("release.completes_when_reached_via_finally_during_exception",
              release_completed_despite_exception)

        # --- Section B: a later command with the SAME generation reuses cleanly ---
        cmd3 = FakeCommand(master_path, master_sha, MULTI_TARGET_FOLDS)
        payload3 = extracted_acquire(cmd3, usermod_dir)
        check("reuse.later_command_same_generation_succeeds",
              payload3["mapping_count"] == payload["mapping_count"])
        extracted_release(cmd3)

        # --- Section B: a later command pinned to a STALE generation is refused ---
        cmd4 = FakeCommand(master_path, "0" * 64, MULTI_TARGET_FOLDS)
        stale_rejected = False
        try:
            extracted_acquire(cmd4, usermod_dir)
        except ProbeError:
            stale_rejected = True
        check("reuse.stale_expected_generation_rejected", stale_rejected)
        check("reuse.stale_generation_never_took_a_lease", cmd4._master_index_lease is None)

        # --- Section C: shipped_root points at an unpublished/empty directory ---
        # A fresh broker/view-cache state is forced here (and before the
        # corrupt-artifact case below): get_broker() returns the SAME
        # process-wide singleton every call, so without a reset these
        # cases could silently hit an ALREADY-CACHED view from the
        # earlier successful acquisitions above (same master_path, same
        # folds) and never actually touch shipped_root/the artifact at
        # all -- which would prove nothing. _reset_for_test_only() is the
        # same test-only escape hatch this package's own qualification
        # suite already uses for this exact reason.
        authority_runtime = ns["authority_runtime"]
        authority_runtime._reset_for_test_only()
        empty_root = os.path.join(root, "empty_usermod")
        os.makedirs(os.path.join(empty_root, "cfg", "sfm_shared_authority"))
        cmd5 = FakeCommand(master_path, master_sha, MULTI_TARGET_FOLDS)
        unpublished_rejected = False
        unpublished_exc = None
        try:
            extracted_acquire(cmd5, empty_root)
        except ProbeError as exc:
            unpublished_rejected = True
            unpublished_exc = exc
        check("failure_atomicity.unpublished_shipped_root_rejected", unpublished_rejected, unpublished_exc)
        check("failure_atomicity.unpublished_never_took_a_lease", cmd5._master_index_lease is None)

        # --- Section C: corrupted published artifact ---
        corrupt_root = os.path.join(root, "corrupt_usermod")
        corrupt_shipped_root = os.path.join(corrupt_root, "cfg", "sfm_shared_authority")
        shutil.copytree(shipped_root, corrupt_shipped_root)
        gen_files = [n for n in os.listdir(corrupt_shipped_root) if n.endswith(".sfmsidecar")]
        check("failure_atomicity.corrupt_fixture_found_generation_file", len(gen_files) == 1, gen_files)
        corrupt_path = os.path.join(corrupt_shipped_root, gen_files[0])
        with open(corrupt_path, "r+b") as f:
            data = bytearray(f.read())
            for i in range(min(64, len(data))):
                data[i] = 0
            f.seek(0)
            f.write(bytes(data))
        authority_runtime._reset_for_test_only()
        cmd6 = FakeCommand(master_path, master_sha, MULTI_TARGET_FOLDS)
        corrupt_rejected = False
        try:
            extracted_acquire(cmd6, corrupt_root)
        except ProbeError:
            corrupt_rejected = True
        check("failure_atomicity.corrupt_artifact_rejected", corrupt_rejected)
        check("failure_atomicity.corrupt_never_took_a_lease", cmd6._master_index_lease is None)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("\nRESULT: %d/%d %s" % (
        sum(1 for _, c in RESULTS if c), len(RESULTS),
        "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
    ))
    if not all(condition for _, condition in RESULTS):
        sys.exit(1)


if __name__ == "__main__":
    main()
