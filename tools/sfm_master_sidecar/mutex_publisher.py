# -*- coding: utf-8 -*-
"""R3-B2E external rebuild/publication transaction.

Wraps the already-existing, already-tested compile/validate pipeline
(`compiler.py`, `manifest.py`) with the pieces R3-B2E specifically
requires that did not exist before this task:

  - a real Windows `Global\\` named mutex (`win_named_mutex.py`) instead
    of the existing `publisher.py`'s file-lock-only serialization;
  - preservation of the previous validated manifest as a recoverable
    `.bak` before it is overwritten;
  - an explicit additional validation gate through the FINAL R3-A2B
    validator/provider contract (bounded read + admission cap), on top
    of the existing production-reader self-validation;
  - `WAIT_ABANDONED` reconciliation (validate primary, validate backup,
    validate referenced artifacts, before any new commit);
  - ambiguous-replace-outcome reconciliation (never assumes "nothing
    changed" without checking actual disk state);
  - named fault-injection hooks matching the full R3-B2E crash-injection
    point list.

Reuses, unmodified: `compiler.capture_source_snapshot`,
`compiler.parse_and_compile`, `compiler.self_validate_from_path`,
`manifest.build_manifest_dict`/`serialize_manifest`/`parse_manifest_bytes`.
Python 3 only.
"""
import binascii
import hashlib
import json
import os
import sys
import types
import uuid
from pathlib import Path

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from . import compiler  # noqa: E402
from . import manifest as manifest_module  # noqa: E402
from . import win_named_mutex  # noqa: E402

MANIFEST_BASENAME = "manifest.json"
BACKUP_MANIFEST_BASENAME = "manifest.json.bak"
MANIFEST_SCHEMA_VERSION = 1

# The FINAL exported R3-A2B validator/provider contract -- verified by
# exact SHA-256 before use, exactly as `sfm_master_authority.sidecar_contract`
# already does on the reader side (R3-B2A). Kept as a literal constant here,
# not imported from the B2A package, since this external Python 3 utility
# is deliberately independent of the embedded-runtime broker package.
_FINAL_R3A2B_VALIDATOR_PATH = (
    r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_packed_validator_r3a2b.py"
)
_FINAL_R3A2B_PROVIDER_PATH = (
    r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_packed_provider_r3a2b.py"
)
_FINAL_R3A2B_VALIDATOR_SHA256 = "74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f"
_FINAL_R3A2B_PROVIDER_SHA256 = "d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677"
_GATE_R2_DEPLOY_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm\gate_r2_formal_deploy"
)

_r3a2b_validator_module = None
_r3a2b_provider_module = None


class MutexPublicationError(Exception):
    """Base class for every exception this module raises."""


class FinalGateValidationError(MutexPublicationError):
    """The FINAL R3-A2B validator/provider contract rejected the
    compiled artifact (in addition to, and after, the existing
    production-reader self-validation, which already passed)."""


class SourceMutatedDuringPublicationError(MutexPublicationError):
    """The live source path's bytes no longer match the captured
    snapshot's hash by the time the critical activation section ran."""


class GenerationCollisionError(MutexPublicationError):
    """Different bytes were found under the same immutable generation
    basename -- never overwritten."""


class CommitOutcomeUncertainError(MutexPublicationError):
    """The pointer-replace step reported an ambiguous result; disk state
    was reconciled and neither a clean 'committed' nor a clean
    'not-committed' classification could be established."""


class AbandonedStateUnrecoverableError(MutexPublicationError):
    """WAIT_ABANDONED was observed and BOTH the primary and backup
    manifests failed independent validation (missing, corrupt, or
    referencing a missing/mismatched artifact). R3-B2E Section 5 requires
    this to be an explicit failure, never a silent fresh commit over an
    unrecoverable prior state -- something deeper may be wrong with this
    generated-root/slot (filesystem corruption, wrong directory, a
    misbehaving concurrent process outside this protocol) and it is safer
    to stop for investigation than to paper over it with a new commit."""


def _sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _ensure_final_r3a2b_loaded():
    global _r3a2b_validator_module, _r3a2b_provider_module
    if _r3a2b_validator_module is not None and _r3a2b_provider_module is not None:
        return
    actual_v = _sha256_of_file(_FINAL_R3A2B_VALIDATOR_PATH)
    if actual_v != _FINAL_R3A2B_VALIDATOR_SHA256:
        raise FinalGateValidationError(
            "FINAL R3-A2B validator SHA-256 mismatch: expected %s, found %s"
            % (_FINAL_R3A2B_VALIDATOR_SHA256, actual_v)
        )
    actual_p = _sha256_of_file(_FINAL_R3A2B_PROVIDER_PATH)
    if actual_p != _FINAL_R3A2B_PROVIDER_SHA256:
        raise FinalGateValidationError(
            "FINAL R3-A2B provider SHA-256 mismatch: expected %s, found %s"
            % (_FINAL_R3A2B_PROVIDER_SHA256, actual_p)
        )
    if _GATE_R2_DEPLOY_DIR not in sys.path:
        sys.path.insert(0, _GATE_R2_DEPLOY_DIR)

    def _load(path, mod_name):
        with open(path, "rb") as f:
            src = f.read()
        mod = types.ModuleType(mod_name)
        mod.__file__ = path
        sys.modules[mod_name] = mod
        exec(compile(src, path, "exec"), mod.__dict__)
        return mod

    _r3a2b_validator_module = _load(_FINAL_R3A2B_VALIDATOR_PATH, "sfm_b2e_final_r3a2b_validator")
    sys.modules["candidate_packed_validator_r3a2b"] = _r3a2b_validator_module
    _r3a2b_provider_module = _load(_FINAL_R3A2B_PROVIDER_PATH, "sfm_b2e_final_r3a2b_provider")


def validate_with_final_r3a2b_contract(artifact_path, expected_source_sha256):
    """The R3-B2E-required ADDITIONAL gate: open, fully validate (bounded
    read + Section 20 A-J structural validation + admission cap), and
    immediately close via the FINAL exported R3-A2B contract. Raises
    `FinalGateValidationError` on any rejection. This runs in ADDITION to
    (never instead of) the existing `compiler.self_validate_from_path`
    production-reader semantic-parity check."""
    _ensure_final_r3a2b_loaded()
    try:
        provider = _r3a2b_provider_module.BoundedProvider.open_path(
            str(artifact_path), expected_source_sha256,
        )
    except _r3a2b_provider_module.SourceMismatchError as exc:
        raise FinalGateValidationError("FINAL R3-A2B gate: source mismatch: %s" % (exc,))
    except _r3a2b_provider_module.AuthorityUnavailable as exc:
        raise FinalGateValidationError("FINAL R3-A2B gate rejected the artifact: %s" % (exc,))
    provider.close()


def _unlink_quiet(path):
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass


def _publish_or_reuse_generation(tmp_gen_path, final_gen_path, blob):
    if final_gen_path.exists():
        existing = final_gen_path.read_bytes()
        if existing != blob:
            raise GenerationCollisionError(
                "generation basename %r already exists with DIFFERENT content -- refusing to "
                "overwrite (existing %d bytes vs new %d bytes)"
                % (final_gen_path.name, len(existing), len(blob))
            )
        _unlink_quiet(tmp_gen_path)
        return True
    os.replace(str(tmp_gen_path), str(final_gen_path))
    return False


def _try_validate_existing_manifest(manifest_path, output_dir):
    """Best-effort: parse an existing manifest and confirm its referenced
    artifact actually exists and matches its recorded SHA. Returns the
    parsed ManifestData on success, or None (never raises) -- used only
    for defensive reconciliation/backup decisions, never as a publish
    blocker by itself."""
    try:
        if not manifest_path.exists():
            return None
        data = manifest_module.parse_manifest_bytes(manifest_path.read_bytes())
        gen_path = manifest_module.resolve_generation_path(output_dir, data)
        if not os.path.isfile(gen_path):
            return None
        if _sha256_of_file(gen_path) != data.sidecar_sha256:
            return None
        return data
    except Exception:
        return None


def _reconcile_after_abandoned(output_dir):
    """WAIT_ABANDONED handling (ASTRA_CORRECTED.md Section 12 /
    R3-B2E Section 8): validate primary pointer, validate backup
    pointer, validate referenced artifacts -- classify, never blindly
    trust, before any new commit proceeds. Returns a small dict
    describing what was found; never raises on its own (a corrupt
    primary/backup here is exactly what this function exists to detect,
    not a reason to crash before the NEW publish attempt gets to try)."""
    output_dir = Path(output_dir)
    primary_path = output_dir / MANIFEST_BASENAME
    backup_path = output_dir / BACKUP_MANIFEST_BASENAME
    primary_ok = _try_validate_existing_manifest(primary_path, output_dir) is not None
    backup_ok = _try_validate_existing_manifest(backup_path, output_dir) is not None
    return {
        "primary_valid": primary_ok,
        "backup_valid": backup_ok,
        "primary_exists": primary_path.exists(),
        "backup_exists": backup_path.exists(),
    }


def _preserve_backup_if_valid(output_dir):
    """Preserve the current PRIMARY manifest as `.bak` before it is
    overwritten -- only if it is itself a previously-validated pointer
    (ASTRA_CORRECTED.md Section 13: 'backup pointer: prior validated
    pointer only'). A corrupt/missing primary is simply not backed up
    (there is nothing valid to preserve)."""
    output_dir = Path(output_dir)
    primary_path = output_dir / MANIFEST_BASENAME
    if _try_validate_existing_manifest(primary_path, output_dir) is None:
        return False
    backup_path = output_dir / BACKUP_MANIFEST_BASENAME
    tmp_backup = output_dir / (".tmp-backup-%s.json" % uuid.uuid4().hex)
    with open(tmp_backup, "wb") as dst, open(primary_path, "rb") as src:
        dst.write(src.read())
        dst.flush()
        os.fsync(dst.fileno())
    os.replace(str(tmp_backup), str(backup_path))
    return True


def recover_from_backup(output_dir):
    """Explicit backup-recovery entry point: if the primary manifest is
    missing/corrupt but the backup independently passes full admission,
    restores it as the new primary. Applies the SAME full validation
    rules on recovery as on any other candidate -- never a shortcut path.
    Returns True if recovery occurred, False if the backup was itself
    invalid/absent (never silently trusted)."""
    output_dir = Path(output_dir)
    primary_path = output_dir / MANIFEST_BASENAME
    backup_path = output_dir / BACKUP_MANIFEST_BASENAME
    if _try_validate_existing_manifest(primary_path, output_dir) is not None:
        return False  # primary is already fine -- nothing to recover
    if _try_validate_existing_manifest(backup_path, output_dir) is None:
        return False  # backup is not trustworthy either
    tmp = output_dir / (".tmp-recover-%s.json" % uuid.uuid4().hex)
    with open(tmp, "wb") as dst, open(backup_path, "rb") as src:
        dst.write(src.read())
        dst.flush()
        os.fsync(dst.fileno())
    os.replace(str(tmp), str(primary_path))
    return True


def _verify_committed_manifest(output_dir, expected_manifest_bytes):
    """Re-read the just-committed primary manifest independently from
    disk and confirm it matches what was intended, and that its
    referenced artifact is present/correct -- the required commit
    verification step."""
    manifest_path = output_dir / MANIFEST_BASENAME
    on_disk = manifest_path.read_bytes()
    if on_disk != expected_manifest_bytes:
        raise CommitOutcomeUncertainError(
            "committed manifest bytes do not match what was intended to be written -- disk "
            "state does not match the expected commit"
        )
    data = manifest_module.parse_manifest_bytes(on_disk)
    gen_path = manifest_module.resolve_generation_path(output_dir, data)
    if not os.path.isfile(gen_path):
        raise CommitOutcomeUncertainError("committed manifest references a generation file that does not exist")
    if _sha256_of_file(gen_path) != data.sidecar_sha256:
        raise CommitOutcomeUncertainError("committed manifest's referenced generation file digest does not match")


class PublishResult(object):
    __slots__ = (
        "generation_basename", "generation_path", "manifest_path", "reused",
        "ordinary_sha256", "source_sha256", "mutex_outcome_kind", "abandoned_reconciliation",
    )

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


def publish(source_path, output_dir, mutex_slot_identity, official_policy=False,
            mutex_timeout_seconds=30.0, skip_final_r3a2b_gate=False, _fault_hook=None):
    """The full R3-B2E publication transaction. `_fault_hook(stage)` is a
    narrow TEST-ONLY hook (never part of the public contract, always
    `None` in real use) called at each named point below; if it raises,
    that exception propagates as a simulated failure at exactly that
    point, with the same cleanup guarantees real failures get.

    Named fault-injection stages (R3-B2E Section 14):
    before_parse, before_self_validation, after_self_validation,
    before_r3a2b_gate, after_r3a2b_gate, before_generation_publication,
    after_generation_publication, before_manifest_temp_write,
    after_manifest_temp_write, before_mutex_acquire, on_wait_abandoned,
    before_backup_preparation, after_backup_preparation,
    before_source_recheck, before_manifest_replace, after_manifest_replace,
    before_commit_verification, after_commit_verification.
    """

    def fire(stage):
        if _fault_hook is not None:
            _fault_hook(stage)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fire("before_parse")
    snapshot = compiler.capture_source_snapshot(source_path)
    outcome = compiler.parse_and_compile(snapshot, official_policy=official_policy)

    tmp_gen_path = output_dir / (".tmp-gen-%s.bin" % uuid.uuid4().hex)
    with open(tmp_gen_path, "wb") as f:
        f.write(outcome.blob)
        f.flush()
        os.fsync(f.fileno())

    try:
        fire("before_self_validation")
        compiler.self_validate_from_path(outcome, tmp_gen_path)
        fire("after_self_validation")

        if not skip_final_r3a2b_gate:
            fire("before_r3a2b_gate")
            validate_with_final_r3a2b_contract(tmp_gen_path, outcome.result.source_sha256)
            fire("after_r3a2b_gate")
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
    manifest_dict["schema_version"] = MANIFEST_SCHEMA_VERSION
    manifest_dict["projection_semantics_version"] = None  # not yet defined by the current header format -- honest None
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
    mutex_name = win_named_mutex.build_mutex_name(mutex_slot_identity)
    mtx = win_named_mutex.WindowsNamedMutex(mutex_name)

    fire("before_mutex_acquire")
    mutex_outcome = mtx.acquire(timeout_seconds=mutex_timeout_seconds)
    abandoned_reconciliation = None
    try:
        if mutex_outcome.kind == win_named_mutex.OUTCOME_ACQUIRED_ABANDONED:
            fire("on_wait_abandoned")
            abandoned_reconciliation = _reconcile_after_abandoned(output_dir)
            _some_prior_state_exists = (
                abandoned_reconciliation["primary_exists"] or abandoned_reconciliation["backup_exists"]
            )
            _both_unusable = (
                not abandoned_reconciliation["primary_valid"] and not abandoned_reconciliation["backup_valid"]
            )
            if _some_prior_state_exists and _both_unusable:
                # Evidence of PRIOR publication state exists (a manifest
                # and/or backup file is actually present) but NONE of it is
                # trustworthy -- distinct from a legitimate first-ever
                # publish (nothing on disk yet, nothing to lose). Refuse
                # rather than silently paper over an unrecoverable prior
                # state with a fresh commit.
                _unlink_quiet(tmp_manifest_path)
                raise AbandonedStateUnrecoverableError(
                    "WAIT_ABANDONED observed and BOTH primary and backup manifests under %r "
                    "failed independent validation (primary_exists=%r backup_exists=%r) -- refusing "
                    "to commit a new pointer over an unrecoverable prior state; the freshly-compiled "
                    "generation for this publish attempt remains on disk as a harmless orphan (no "
                    "automatic GC)." % (
                        str(output_dir), abandoned_reconciliation["primary_exists"],
                        abandoned_reconciliation["backup_exists"],
                    )
                )

        fire("before_backup_preparation")
        _preserve_backup_if_valid(output_dir)
        fire("after_backup_preparation")

        fire("before_source_recheck")
        live_bytes = Path(source_path).read_bytes()
        live_sha = hashlib.sha256(live_bytes).hexdigest()
        if live_sha != snapshot.sha256_hex:
            _unlink_quiet(tmp_manifest_path)
            raise SourceMutatedDuringPublicationError(
                "source at %r changed between capture (%s) and activation (%s) -- activation "
                "aborted; the prior valid pointer remains untouched; the compiled generation "
                "for the captured snapshot may remain as a harmless orphan"
                % (str(source_path), snapshot.sha256_hex, live_sha)
            )

        fire("before_manifest_replace")
        try:
            os.replace(str(tmp_manifest_path), str(final_manifest_path))
        except Exception as exc:
            # Ambiguous-failure reconciliation: never assume "nothing
            # changed" -- inspect actual disk state and classify.
            on_disk_now = final_manifest_path.read_bytes() if final_manifest_path.exists() else None
            if on_disk_now == manifest_bytes:
                pass  # actually committed despite the reported error -- proceed as committed
            elif on_disk_now is None or on_disk_now != manifest_bytes:
                _unlink_quiet(tmp_manifest_path)
                raise CommitOutcomeUncertainError(
                    "pointer replacement raised %r; disk state does not clearly show the intended "
                    "content -- classified NOT-COMMITTED/UNCERTAIN, never silently reported as "
                    "success" % (exc,)
                )
        fire("after_manifest_replace")

        fire("before_commit_verification")
        _verify_committed_manifest(output_dir, manifest_bytes)
        fire("after_commit_verification")
    except Exception:
        _unlink_quiet(tmp_manifest_path)
        raise
    finally:
        mtx.release()

    return PublishResult(
        generation_basename=final_basename,
        generation_path=final_gen_path,
        manifest_path=final_manifest_path,
        reused=reused,
        ordinary_sha256=outcome.ordinary_sha256,
        source_sha256=snapshot.sha256_hex,
        mutex_outcome_kind=mutex_outcome.kind,
        abandoned_reconciliation=abandoned_reconciliation,
    )


def read_active_manifest(output_dir):
    path = Path(output_dir) / MANIFEST_BASENAME
    if not path.exists():
        return None
    return manifest_module.parse_manifest_bytes(path.read_bytes())
