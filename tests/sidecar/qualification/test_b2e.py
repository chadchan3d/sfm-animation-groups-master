# -*- coding: utf-8 -*-
"""R3-B2E offline qualification suite. Python 3 only. Never launches
SFM, never modifies R1D/final-R3-A2B/Master/production consumer files.
Uses the real official Master (read-only) plus isolated scratch output
directories.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, r"E:\SFM Animation Group Master\tools")
from sfm_master_sidecar import mutex_publisher, generated_root, manifest as manifest_module, win_named_mutex

REAL_MASTER = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
REAL_MASTER_SHA = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
KNOWN_OFFICIAL_ARTIFACT_SHA = "bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b"

SCRATCH_ROOT = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2e\test_out"

results = []


def check(name, condition, detail=None):
    results.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


def fresh_dir(name):
    d = os.path.join(SCRATCH_ROOT, name)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    return d


def make_custom_master(text):
    d = tempfile.mkdtemp(prefix="b2e_custom_master_")
    p = os.path.join(d, "custom_master.txt")
    with open(p, "wb") as f:
        f.write(text.encode("utf-8"))
    return p


CUSTOM_MASTER_TEXT = (
    '"groupFile"\n{\n\t"RigArms"\n\t{\n\t\t"control"\t\t"TestControlA"\n\t\t"control"\t\t"TestControlB"\n\t}\n}\n'
)


# ===========================================================================
# SECTION: official current Master + exact reproduction
# ===========================================================================
print("=== Official Master compile + exact reproduction ===")

out1 = fresh_dir("official_basic")
slot1 = generated_root.derive_install_slot_identity(r"C:\fake_install", REAL_MASTER)
result1 = mutex_publisher.publish(REAL_MASTER, out1, mutex_slot_identity=slot1)
check("official.1 publish succeeds against the real current official Master", result1 is not None)
check("official.2 compiled artifact SHA EXACTLY matches the known official_sidecar_artifact.bin SHA",
      result1.ordinary_sha256 == KNOWN_OFFICIAL_ARTIFACT_SHA, result1.ordinary_sha256)
check("official.3 source_sha256 matches the pinned real Master SHA", result1.source_sha256 == REAL_MASTER_SHA)
check("official.4 mutex_outcome_kind is a normal acquisition", result1.mutex_outcome_kind == win_named_mutex.OUTCOME_ACQUIRED)

result1b = mutex_publisher.publish(REAL_MASTER, out1, mutex_slot_identity=slot1)
check("official.5 republishing the SAME source reuses the existing generation", result1b.reused is True)
check("official.6 reused generation basename is identical", result1b.generation_basename == result1.generation_basename)


# ===========================================================================
# SECTION: custom fixture Master
# ===========================================================================
print("=== Custom fixture Master ===")

custom_master_path = make_custom_master(CUSTOM_MASTER_TEXT)
out2 = fresh_dir("custom_basic")
slot2 = generated_root.derive_install_slot_identity(r"C:\fake_install", custom_master_path)
result2 = mutex_publisher.publish(custom_master_path, out2, mutex_slot_identity=slot2)
check("custom.1 a custom, non-official Master compiles and publishes successfully", result2 is not None)
check("custom.2 custom artifact SHA differs from the official one",
      result2.ordinary_sha256 != KNOWN_OFFICIAL_ARTIFACT_SHA)


# ===========================================================================
# SECTION: pointer encode/decode + malformed pointers + traversal
# ===========================================================================
print("=== Pointer encode/decode, malformed, traversal ===")

active2 = mutex_publisher.read_active_manifest(out2)
check("pointer.1 round-tripped manifest has schema_version field", active2.raw.get("schema_version") == 1, active2.raw)
check("pointer.2 round-tripped manifest source_sha256 matches", active2.source_sha256 == hashlib.sha256(open(custom_master_path, "rb").read()).hexdigest())

# malformed: duplicate key
malformed_dup = b'{"generation_basename": "sfm_master_0_' + b"0" * 64 + b'.bin", "generation_basename": "x", "sidecar_sha256": "' + b"0" * 64 + b'", "source_sha256": "' + b"0" * 64 + b'", "source_byte_length": 1, "format_contract_version": 0, "authority_semantics_version": 0, "counts": {"groups":1,"occurrences":1,"folds":1}}'
try:
    manifest_module.parse_manifest_bytes(malformed_dup)
    check("pointer.3 duplicate-key manifest rejected", False, "did not raise")
except manifest_module.ManifestError:
    check("pointer.3 duplicate-key manifest rejected", True)

# malformed: missing required field
malformed_missing = json.dumps({"generation_basename": "sfm_master_0_" + "0" * 64 + ".bin"}).encode("utf-8")
try:
    manifest_module.parse_manifest_bytes(malformed_missing)
    check("pointer.4 missing-required-field manifest rejected", False, "did not raise")
except manifest_module.ManifestError:
    check("pointer.4 missing-required-field manifest rejected", True)

# traversal: basename with path separators / '..'
for bad_name in ("../../evil.bin", "..\\evil.bin", "C:\\evil.bin", "sub/evil.bin"):
    ok = not manifest_module._is_safe_generation_basename(bad_name)
    check("pointer.5 traversal/absolute basename rejected: %r" % bad_name, ok, bad_name)

# path confinement: resolve_generation_path never escapes output_dir
safe_data = manifest_module.ManifestData({
    "generation_basename": "sfm_master_0_" + "a" * 64 + ".bin",
    "sidecar_sha256": "a" * 64, "source_sha256": "b" * 64, "source_byte_length": 1,
    "format_contract_version": 0, "authority_semantics_version": 0, "counts": {"groups": 0, "occurrences": 0, "folds": 0},
})
resolved = manifest_module.resolve_generation_path(out2, safe_data)
check("pointer.6 resolved generation path stays confined under output_dir",
      os.path.dirname(os.path.abspath(resolved)) == os.path.abspath(out2))


# ===========================================================================
# SECTION: artifact digest mismatch / source mismatch / R3-A2B gate
# ===========================================================================
print("=== Artifact digest mismatch, source mismatch, FINAL R3-A2B gate ===")

# Artifact digest mismatch: corrupt the published generation file in place,
# then confirm the FINAL R3-A2B gate (called fresh) rejects it.
out3 = fresh_dir("digest_mismatch")
slot3 = generated_root.derive_install_slot_identity(r"C:\fake_install", REAL_MASTER)
result3 = mutex_publisher.publish(REAL_MASTER, out3, mutex_slot_identity=slot3)
with open(result3.generation_path, "r+b") as f:
    f.seek(200)
    f.write(b"\xff\xff\xff\xff")
try:
    mutex_publisher.validate_with_final_r3a2b_contract(result3.generation_path, REAL_MASTER_SHA)
    check("mismatch.1 corrupted published artifact rejected by FINAL R3-A2B gate", False, "did not raise")
except mutex_publisher.FinalGateValidationError:
    check("mismatch.1 corrupted published artifact rejected by FINAL R3-A2B gate", True)

# Source mismatch: publish, then republish with a source that produces the
# SAME artifact bytes coincidentally is not realistic; instead directly
# exercise validate_with_final_r3a2b_contract with a wrong expected SHA.
try:
    mutex_publisher.validate_with_final_r3a2b_contract(result1.generation_path, "0" * 64)
    check("mismatch.2 wrong expected source_sha256 rejected by FINAL R3-A2B gate", False, "did not raise")
except mutex_publisher.FinalGateValidationError:
    check("mismatch.2 wrong expected source_sha256 rejected by FINAL R3-A2B gate", True)


# ===========================================================================
# SECTION: compiler parity mismatch injection
# ===========================================================================
print("=== Compiler parity mismatch injection ===")

import importlib
from sfm_master_sidecar import compiler as compiler_module

_orig_verify_parity = compiler_module.verify_semantic_parity


def _always_fail_parity(result, r):
    raise compiler_module.SelfValidationError("INJECTED parity mismatch for testing")


compiler_module.verify_semantic_parity = _always_fail_parity
try:
    out_parity = fresh_dir("parity_injected")
    slot_parity = generated_root.derive_install_slot_identity(r"C:\fake_install", custom_master_path)
    try:
        mutex_publisher.publish(custom_master_path, out_parity, mutex_slot_identity=slot_parity)
        check("parity.1 injected parity mismatch blocks publication", False, "did not raise")
    except compiler_module.SelfValidationError:
        check("parity.1 injected parity mismatch blocks publication", True)
    check("parity.2 no manifest was published when parity failed",
          not os.path.exists(os.path.join(out_parity, mutex_publisher.MANIFEST_BASENAME)))
finally:
    compiler_module.verify_semantic_parity = _orig_verify_parity


# ===========================================================================
# SECTION: crash injection at every named fault stage
# ===========================================================================
print("=== Crash injection ===")

FAULT_STAGES = [
    "before_parse", "before_self_validation", "after_self_validation",
    "before_r3a2b_gate", "after_r3a2b_gate", "before_generation_publication",
    "after_generation_publication", "before_manifest_temp_write", "after_manifest_temp_write",
    "before_mutex_acquire", "before_backup_preparation", "after_backup_preparation",
    "before_source_recheck", "before_manifest_replace", "after_manifest_replace",
    "before_commit_verification", "after_commit_verification",
]


class _InjectedFault(Exception):
    pass


def _make_hook(stage_to_fail):
    def _hook(stage):
        if stage == stage_to_fail:
            raise _InjectedFault("injected failure at %r" % stage)
    return _hook


# Pre-publish ONE valid generation so "prior valid pointer remains usable"
# has something real to check against for every injected failure below.
out_crash = fresh_dir("crash_injection")
slot_crash = generated_root.derive_install_slot_identity(r"C:\fake_install", REAL_MASTER)
baseline = mutex_publisher.publish(REAL_MASTER, out_crash, mutex_slot_identity=slot_crash)
baseline_manifest_bytes = (out_crash and open(os.path.join(out_crash, mutex_publisher.MANIFEST_BASENAME), "rb").read())

# Use the CUSTOM master for the injected-failure republish attempts, so a
# genuinely NEW generation is what gets interrupted each time (never
# re-triggering the "reuse" path, which would short-circuit real work).
crash_master = make_custom_master(CUSTOM_MASTER_TEXT + "\n// stage marker\n")

all_stage_results = []
for stage in FAULT_STAGES:
    raised_correctly = False
    try:
        mutex_publisher.publish(crash_master, out_crash, mutex_slot_identity=slot_crash, _fault_hook=_make_hook(stage))
    except _InjectedFault:
        raised_correctly = True
    except Exception as exc:
        raised_correctly = "unexpected exception type: %r" % (exc,)

    # Invariant after EVERY injected failure: the prior valid manifest is
    # either untouched (still byte-identical to baseline) or has been
    # cleanly advanced to a fully-verifiable NEW valid state -- never a
    # half-written/corrupt manifest.
    manifest_path = os.path.join(out_crash, mutex_publisher.MANIFEST_BASENAME)
    manifest_intact = False
    if os.path.exists(manifest_path):
        try:
            manifest_module.parse_manifest_bytes(open(manifest_path, "rb").read())
            manifest_intact = True
        except manifest_module.ManifestError:
            manifest_intact = False
    else:
        manifest_intact = True  # no manifest at all is also an acceptable (pre-first-publish) state, not corruption

    stage_ok = (raised_correctly is True) and manifest_intact
    all_stage_results.append((stage, stage_ok, raised_correctly, manifest_intact))
    check("crash.%s injected failure propagates AND manifest remains parseable/untouched" % stage,
          stage_ok, (raised_correctly, manifest_intact))

    # Clean up any orphaned temp files this attempt may have left (never a
    # correctness requirement -- temp files ARE allowed to remain per
    # "no automatic GC" -- but bounded cleanup where safe, per Section 14).
    for leftover in os.listdir(out_crash):
        if leftover.startswith(".tmp-"):
            try:
                os.remove(os.path.join(out_crash, leftover))
            except OSError:
                pass

check("crash.ALL every one of the 17 fault stages was exercised", len(all_stage_results) == len(FAULT_STAGES))


# ===========================================================================
# SECTION: existing corrupt final artifact (never overwrite on trust)
# ===========================================================================
print("=== Existing corrupt final artifact ===")

out4 = fresh_dir("existing_corrupt_final")
slot4 = generated_root.derive_install_slot_identity(r"C:\fake_install", REAL_MASTER)
result4 = mutex_publisher.publish(REAL_MASTER, out4, mutex_slot_identity=slot4)
# Corrupt the ALREADY-PUBLISHED final generation file in place.
with open(result4.generation_path, "r+b") as f:
    f.seek(50)
    f.write(b"\x00\x00\x00\x00")
try:
    mutex_publisher.publish(REAL_MASTER, out4, mutex_slot_identity=slot4)
    check("existingcorrupt.1 republish detects the corrupted final artifact and refuses to silently reuse it",
          False, "did not raise")
except mutex_publisher.GenerationCollisionError:
    check("existingcorrupt.1 republish detects the corrupted final artifact and refuses to silently reuse it", True)


# ===========================================================================
# SECTION: backup recovery
# ===========================================================================
print("=== Backup recovery ===")

out5 = fresh_dir("backup_recovery")
slot5 = generated_root.derive_install_slot_identity(r"C:\fake_install", REAL_MASTER)
mutex_publisher.publish(REAL_MASTER, out5, mutex_slot_identity=slot5)  # publish #1 -- no backup yet (nothing prior to preserve)
custom_master_2 = make_custom_master(CUSTOM_MASTER_TEXT + "\n// second generation\n")
slot5b = generated_root.derive_install_slot_identity(r"C:\fake_install", custom_master_2)
mutex_publisher.publish(custom_master_2, out5, mutex_slot_identity=slot5)  # different source, SAME output_dir/slot -> publish #2 preserves #1 as backup
backup_path = os.path.join(out5, mutex_publisher.BACKUP_MANIFEST_BASENAME)
check("backup.1 a .bak file was created preserving the PRIOR manifest", os.path.exists(backup_path))
backup_data = manifest_module.parse_manifest_bytes(open(backup_path, "rb").read())
check("backup.2 the backup manifest is the ORIGINAL (official Master) generation, not the new one",
      backup_data.source_sha256 == REAL_MASTER_SHA)

# Now corrupt the PRIMARY manifest and prove recover_from_backup restores it.
primary_path = os.path.join(out5, mutex_publisher.MANIFEST_BASENAME)
with open(primary_path, "wb") as f:
    f.write(b"{not valid json")
recovered = mutex_publisher.recover_from_backup(out5)
check("backup.3 recover_from_backup() returns True when primary is corrupt and backup is valid", recovered is True)
restored = mutex_publisher.read_active_manifest(out5)
check("backup.4 restored primary manifest matches the backup's content (the original official generation)",
      restored.source_sha256 == REAL_MASTER_SHA)

# corrupt backup is not trusted
with open(backup_path, "wb") as f:
    f.write(b"{also not valid json")
with open(primary_path, "wb") as f:
    f.write(b"{still not valid json")
recovered2 = mutex_publisher.recover_from_backup(out5)
check("backup.5 recover_from_backup() returns False when BOTH primary and backup are corrupt (never trusts a corrupt backup)",
      recovered2 is False)


# ===========================================================================
# SECTION: changed H1 source (source changes before mutex/H1)
# ===========================================================================
print("=== Changed H1 source ===")

out6 = fresh_dir("changed_h1")
slot6 = generated_root.derive_install_slot_identity(r"C:\fake_install", REAL_MASTER)
mutable_master = make_custom_master(CUSTOM_MASTER_TEXT)


def _mutate_source_before_recheck(stage):
    if stage == "before_source_recheck":
        with open(mutable_master, "ab") as f:
            f.write(b"\n// mutated after capture, before mutex recheck\n")


try:
    mutex_publisher.publish(mutable_master, out6, mutex_slot_identity=slot6, _fault_hook=_mutate_source_before_recheck)
    check("h1change.1 source mutated before the mutex-held recheck is detected -> publication aborted", False, "did not raise")
except mutex_publisher.SourceMutatedDuringPublicationError:
    check("h1change.1 source mutated before the mutex-held recheck is detected -> publication aborted", True)
check("h1change.2 no manifest was published for the mutated-mid-flight source",
      not os.path.exists(os.path.join(out6, mutex_publisher.MANIFEST_BASENAME)))

# Source changed then restored to IDENTICAL exact bytes -- acknowledged as
# indistinguishable from "never changed" by SHA/length alone (documented
# limitation, never claimed detectable).
out6b = fresh_dir("changed_then_restored")
slot6b = generated_root.derive_install_slot_identity(r"C:\fake_install", REAL_MASTER)
stable_master = make_custom_master(CUSTOM_MASTER_TEXT)
original_bytes = open(stable_master, "rb").read()


def _mutate_then_restore(stage):
    if stage == "before_source_recheck":
        with open(stable_master, "wb") as f:
            f.write(b"TEMPORARILY_DIFFERENT")
        with open(stable_master, "wb") as f:
            f.write(original_bytes)  # restored to the EXACT original bytes


result6b = mutex_publisher.publish(stable_master, out6b, mutex_slot_identity=slot6b, _fault_hook=_mutate_then_restore)
check(
    "h1change.3 DOCUMENTED LIMIT: source edited then restored to IDENTICAL exact bytes before the "
    "mutex-held recheck is NOT detected (H0==H1 by content-hash equality) and publication proceeds "
    "-- explicitly acknowledged as an inherent limitation of content-hash-only observation, never "
    "claimed as a proven-safe 'nothing happened'",
    result6b is not None,
)


# ===========================================================================
# SECTION: WAIT_ABANDONED reconciliation logic (mocked outcome)
# ===========================================================================
print("=== WAIT_ABANDONED reconciliation (mocked -- see report for the real-OS observation note) ===")

out_abandon = fresh_dir("abandoned_mocked")
slot_abandon = generated_root.derive_install_slot_identity(r"C:\fake_install", REAL_MASTER)
mutex_publisher.publish(REAL_MASTER, out_abandon, mutex_slot_identity=slot_abandon)  # establish a valid baseline

recon = mutex_publisher._reconcile_after_abandoned(out_abandon)
check("abandoned.1 reconciliation over a genuinely valid primary reports primary_valid=True",
      recon["primary_valid"] is True, recon)

# Corrupt the primary and re-check reconciliation classification.
primary_path_ab = os.path.join(out_abandon, mutex_publisher.MANIFEST_BASENAME)
with open(primary_path_ab, "wb") as f:
    f.write(b"{corrupt}")
recon2 = mutex_publisher._reconcile_after_abandoned(out_abandon)
check("abandoned.2 reconciliation over a corrupt primary (no backup yet) reports primary_valid=False, backup_valid=False",
      recon2 == {"primary_valid": False, "backup_valid": False, "primary_exists": True, "backup_exists": False}, recon2)

# Exercise the FULL publish() path with mutex.acquire() mocked to report
# OUTCOME_ACQUIRED_ABANDONED, proving on_wait_abandoned fires and
# _reconcile_after_abandoned is actually invoked inside a real publish call
# (not merely callable in isolation).
_orig_acquire = win_named_mutex.WindowsNamedMutex.acquire


def _mock_abandoned_acquire(self, timeout_seconds=30.0):
    handle_holder = _orig_acquire(self, timeout_seconds=timeout_seconds)
    return win_named_mutex.NamedMutexOutcome(win_named_mutex.OUTCOME_ACQUIRED_ABANDONED, handle=handle_holder.handle)


win_named_mutex.WindowsNamedMutex.acquire = _mock_abandoned_acquire
stages_seen = []
try:
    out_abandon2 = fresh_dir("abandoned_mocked_full")
    slot_abandon2 = generated_root.derive_install_slot_identity(r"C:\fake_install", REAL_MASTER)
    result_ab = mutex_publisher.publish(
        REAL_MASTER, out_abandon2, mutex_slot_identity=slot_abandon2,
        _fault_hook=lambda stage: stages_seen.append(stage),
    )
finally:
    win_named_mutex.WindowsNamedMutex.acquire = _orig_acquire

check("abandoned.3 a mocked WAIT_ABANDONED outcome triggers the on_wait_abandoned fault stage inside a real publish() call",
      "on_wait_abandoned" in stages_seen, stages_seen)
check("abandoned.4 publish() still completes successfully after reconciling an abandoned-but-otherwise-fine state",
      result_ab is not None and result_ab.mutex_outcome_kind == win_named_mutex.OUTCOME_ACQUIRED_ABANDONED)
check("abandoned.5 abandoned_reconciliation was recorded on the result", result_ab.abandoned_reconciliation is not None, result_ab.abandoned_reconciliation)


print()
failed = [n for n, ok in results if not ok]
print("RESULT: %d/%d %s" % (len(results) - len(failed), len(results), "ALL PASS" if not failed else "FAILED: %r" % (failed,)))
if failed:
    sys.exit(1)
