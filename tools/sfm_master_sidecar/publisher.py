# -*- coding: utf-8 -*-
"""Immutable generation publication transaction + OS-backed exclusive
publisher lock. Python 3 only.

An "output namespace" is one directory containing:
  - immutable generation files: `sfm_master_<fmt>_<64-hex-sidecar-sha256>.sfmsidecar`
    (Package-Boundary Correction, 2026-09-21: extension changed from
    `.bin` -- see `compiler.generation_basename()`'s own docstring for
    why)
  - one active manifest: `manifest.json`
  - `publisher.lock` -- an OS-backed exclusive lock file (never a
    lockfile-EXISTENCE convention; see `_ExclusiveFileLock` below)

Publication transaction (final spec Section 34, Phase B2E Part 13):
capture source snapshot -> parse -> compile -> write a unique temp
generation file to the destination filesystem -> reader self-validation
(from the bytes ACTUALLY ON DISK) -> semantic parity -> compute the final
immutable generation identity -> publish-or-reuse that immutable generation
-> prepare a temp manifest -> acquire the publisher lock for ONLY the
critical activation section -> re-read/hash the LIVE source path -> compare
to the captured hash -> abort activation on any mismatch -> atomically
replace the active manifest -> release the lock.

The manifest means only "generation G was compiled from source hash X" --
never a claim of TXT+manifest atomicity against arbitrary external editors
(final spec Section 34's own explicit non-claim, Phase B2E Part 14).
"""

import hashlib
import os
import sys
import time
import uuid
from pathlib import Path

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from . import compiler  # noqa: E402
from . import format as fmt  # noqa: E402
from . import manifest as manifest_module  # noqa: E402

MANIFEST_BASENAME = "manifest.json"
LOCK_BASENAME = "publisher.lock"


class PublicationError(Exception):
    """Base class for every exception this module raises."""


class GenerationCollisionError(PublicationError):
    """Different bytes were found under the SAME immutable generation
    basename -- never overwritten. Given the basename IS the content's own
    SHA-256, this indicates either filesystem corruption or (astronomically
    unlikely) a hash collision; either way, publication refuses to proceed."""


class SourceMutatedDuringPublicationError(PublicationError):
    """The live source path's bytes no longer match the captured snapshot's
    hash by the time the critical activation section ran -- the prior
    active manifest is left untouched; an orphan immutable generation for
    the (now-stale) captured snapshot may remain, which is harmless."""


class LockTimeoutError(PublicationError):
    """Could not acquire the publisher lock within the requested timeout."""


# ---------------------------------------------------------------------------
# OS-backed exclusive lock. Never a bare "does a file exist" convention --
# an actual OS exclusive-lock primitive, released by the OS itself if the
# holding process dies (crash-safe by construction, final spec Section 35).
# ---------------------------------------------------------------------------

if sys.platform == "win32":
    import msvcrt

    class _ExclusiveFileLock(object):
        def __init__(self, path):
            self._path = path
            self._fh = None

        def acquire(self, timeout=30.0, poll_interval=0.05):
            self._fh = open(self._path, "a+b")
            deadline = time.time() + timeout
            while True:
                try:
                    self._fh.seek(0)
                    msvcrt.locking(self._fh.fileno(), msvcrt.LK_NBLCK, 1)
                    return
                except OSError:
                    if time.time() >= deadline:
                        self._fh.close()
                        self._fh = None
                        raise LockTimeoutError("could not acquire publisher lock within %.1fs" % timeout)
                    time.sleep(poll_interval)

        def release(self):
            if self._fh is None:
                return
            try:
                self._fh.seek(0)
                try:
                    msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass  # already unlocked (e.g. by process death elsewhere)
            finally:
                self._fh.close()
                self._fh = None

else:
    import fcntl

    class _ExclusiveFileLock(object):
        def __init__(self, path):
            self._path = path
            self._fh = None

        def acquire(self, timeout=30.0, poll_interval=0.05):
            self._fh = open(self._path, "a+b")
            deadline = time.time() + timeout
            while True:
                try:
                    fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return
                except OSError:
                    if time.time() >= deadline:
                        self._fh.close()
                        self._fh = None
                        raise LockTimeoutError("could not acquire publisher lock within %.1fs" % timeout)
                    time.sleep(poll_interval)

        def release(self):
            if self._fh is None:
                return
            try:
                fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
            finally:
                self._fh.close()
                self._fh = None


class PublisherLock(object):
    """Context manager wrapping `_ExclusiveFileLock` for one output
    namespace's `publisher.lock` file."""

    def __init__(self, output_dir, timeout=30.0):
        self._lock = _ExclusiveFileLock(str(Path(output_dir) / LOCK_BASENAME))
        self._timeout = timeout

    def __enter__(self):
        self._lock.acquire(timeout=self._timeout)
        return self

    def __exit__(self, exc_type, exc, tb):
        self._lock.release()
        return False


# ---------------------------------------------------------------------------
# Results.
# ---------------------------------------------------------------------------


class CheckOnlyResult(object):
    __slots__ = ("snapshot", "outcome")

    def __init__(self, snapshot, outcome):
        self.snapshot = snapshot
        self.outcome = outcome


class PublishResult(object):
    __slots__ = (
        "generation_basename", "generation_path", "manifest_path", "reused",
        "ordinary_sha256", "source_sha256",
    )

    def __init__(self, generation_basename, generation_path, manifest_path, reused, ordinary_sha256, source_sha256):
        self.generation_basename = generation_basename
        self.generation_path = generation_path
        self.manifest_path = manifest_path
        self.reused = reused
        self.ordinary_sha256 = ordinary_sha256
        self.source_sha256 = source_sha256


def check_only(source_path, official_policy=False):
    """Part 6: establishes parse success, profile eligibility, deterministic
    compilation, reader structural validation, source binding, and semantic
    parity -- WITHOUT touching any output namespace, publishing a
    generation, or modifying the manifest. No disk writes at all."""
    snapshot = compiler.capture_source_snapshot(source_path)
    outcome = compiler.parse_and_compile(snapshot, official_policy=official_policy)
    compiler.self_validate_from_bytes(outcome)
    return CheckOnlyResult(snapshot, outcome)


def publish(
    source_path,
    output_dir,
    official_policy=False,
    lock_timeout=30.0,
    _fault_hook=None,
):
    """The full publication transaction. `_fault_hook(stage)` is a narrow,
    TEST-ONLY internal hook (Phase B2E Part 27) -- called at named points;
    if it raises, that exception propagates as a simulated failure at
    exactly that point. Never part of the public contract; always `None` in
    real use."""

    def fire(stage):
        if _fault_hook is not None:
            _fault_hook(stage)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fire("before_parse")
    snapshot = compiler.capture_source_snapshot(source_path)
    outcome = compiler.parse_and_compile(snapshot, official_policy=official_policy)

    tmp_gen_path = output_dir / (".tmp-gen-%s.sfmsidecar" % uuid.uuid4().hex)
    with open(tmp_gen_path, "wb") as f:
        f.write(outcome.blob)
        f.flush()
        os.fsync(f.fileno())

    try:
        fire("before_self_validation")
        compiler.self_validate_from_path(outcome, tmp_gen_path)
        fire("after_self_validation")
    except Exception:
        _unlink_quiet(tmp_gen_path)
        raise

    final_basename = compiler.generation_basename(outcome.ordinary_sha256)
    final_gen_path = output_dir / final_basename

    try:
        fire("before_generation_publication")
        reused = _publish_or_reuse_generation(tmp_gen_path, final_gen_path, outcome.blob)
        fire("after_generation_publication")
    except Exception:
        _unlink_quiet(tmp_gen_path)
        raise

    manifest_dict = manifest_module.build_manifest_dict(outcome, final_basename)
    manifest_bytes = manifest_module.serialize_manifest(manifest_dict)

    tmp_manifest_path = output_dir / (".tmp-manifest-%s.json" % uuid.uuid4().hex)
    try:
        fire("before_manifest_temp_write")
        with open(tmp_manifest_path, "wb") as f:
            f.write(manifest_bytes)
            f.flush()
            os.fsync(f.fileno())
        fire("after_manifest_temp_write")
    except Exception:
        _unlink_quiet(tmp_manifest_path)
        raise

    final_manifest_path = output_dir / MANIFEST_BASENAME
    lock = PublisherLock(output_dir, timeout=lock_timeout)
    try:
        with lock:
            # Critical section: only the live-source recheck + manifest
            # activation are serialized -- everything expensive (parse,
            # compile, validation) already happened outside the lock.
            fire("before_source_recheck")
            live_bytes = Path(source_path).read_bytes()
            live_sha = hashlib.sha256(live_bytes).hexdigest()
            if live_sha != snapshot.sha256_hex:
                _unlink_quiet(tmp_manifest_path)
                raise SourceMutatedDuringPublicationError(
                    "source at %r changed between capture (%s) and activation (%s) -- "
                    "activation aborted; the compiled generation for the captured snapshot "
                    "may remain as a harmless orphan" % (str(source_path), snapshot.sha256_hex, live_sha)
                )
            fire("before_manifest_replace")
            os.replace(str(tmp_manifest_path), str(final_manifest_path))
    except Exception:
        _unlink_quiet(tmp_manifest_path)
        raise

    return PublishResult(
        generation_basename=final_basename,
        generation_path=final_gen_path,
        manifest_path=final_manifest_path,
        reused=reused,
        ordinary_sha256=outcome.ordinary_sha256,
        source_sha256=snapshot.sha256_hex,
    )


def _publish_or_reuse_generation(tmp_gen_path, final_gen_path, blob):
    """Returns True if an existing, byte-identical generation was reused
    (temp file discarded); False if the temp file was atomically promoted
    to the final immutable name. Raises `GenerationCollisionError` if
    different bytes are ever found under the same immutable name -- never
    overwritten."""
    if final_gen_path.exists():
        existing = final_gen_path.read_bytes()
        if existing != blob:
            raise GenerationCollisionError(
                "generation basename %r already exists with DIFFERENT content -- refusing to overwrite "
                "(existing %d bytes vs new %d bytes)" % (final_gen_path.name, len(existing), len(blob))
            )
        _unlink_quiet(tmp_gen_path)
        return True
    os.replace(str(tmp_gen_path), str(final_gen_path))
    return False


def _unlink_quiet(path):
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass


def read_active_manifest(output_dir):
    """Reads and hardened-parses the active manifest, if any. Returns
    `None` if no manifest file exists (never an error -- an output
    namespace with no publications yet is a normal state)."""
    path = Path(output_dir) / MANIFEST_BASENAME
    if not path.exists():
        return None
    return manifest_module.parse_manifest_bytes(path.read_bytes())
