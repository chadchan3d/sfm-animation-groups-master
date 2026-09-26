# -*- coding: utf-8 -*-
"""
Checkpoint I -- Restoration Verify (standalone recovery-verification tool)

R3 BLOCKER 5 (2026-09-25, third independent review): the primary
Checkpoint_I_Generation_Replacement.py's own i_08_finalize_verify
snapshot is only naturally reachable via its fixed SNAPSHOT_SCHEDULE,
after snapshots 1-7 have already run in sequence. For an EARLY-ABORTED
I1/I2 campaign (e.g. I1 failed at i1_02, or i1_03 never passed), i_08 is
never naturally reached, and the round 1/round 2 instruction to "run the
checkpoint again for i_08 after finalizing" was therefore FALSE for that
case -- the continuation state would still be sitting wherever the abort
left it, not at i_08.

This is a SEPARATE, read-only, one-shot verification tool for exactly
that situation. After the external finalizer (I_Generation_Publisher.py
finalize) has been run, restart SFM fresh and run THIS script instead of
the primary checkpoint when the campaign aborted before I1_PASS +
I2_FAIL_CLOSED_PASS. It:
  - independently verifies production identity (SHA-256 of the live
    installed Normalizer) and runtime identity (API version, build ID,
    canonical status) -- the same technique the primary checkpoint uses;
  - verifies the live canonical Master is EXACTLY the pinned canonical
    G1;
  - verifies SFM itself is actually reachable (a real main window);
  - reads the STANDALONE baseline-inventory artifact the primary
    checkpoint's own i1_01 snapshot wrote (R2 BLOCKER 6) -- never
    requires the primary continuation state or any nested Snapshot-01
    JSON extraction;
  - independently captures the CURRENT live-state inventory (Master +
    manifest + every shipped sidecar) and requires EXACT equality
    against that baseline;
  - optionally corroborates the external finalizer's own finalization
    record, if present (never REQUIRED -- this script's own independent
    inventory comparison is the authoritative check, exactly like the
    primary checkpoint's own i_08 snapshot);
  - writes its OWN immutable evidence file. Running this script NEVER
    reads, advances, or writes sfm_checkpoint_i_continuation_state.json
    or any other primary-checkpoint evidence file -- it is completely
    independent of SNAPSHOT_SCHEDULE/next_snapshot_index.

For a campaign that reached I1_PASS + I2_FAIL_CLOSED_PASS, use the
PRIMARY checkpoint's own scheduled i_08_finalize_verify snapshot instead
-- only that snapshot can set final_i_verdict=I_PASS in
sfm_checkpoint_i_final_result.json. This script never writes to that
file and never claims I_PASS; its own classification is exactly
RESTORATION_CONFIRMED or RESTORATION_NOT_CONFIRMED, describing recovery
only, never the overall I campaign's own verdict.

If I1 aborted BEFORE any G2 authority/Master mutation ever occurred
(i.e. before Phase A's prepare-publish-g2 was ever run), no restoration
command and no run of this script are necessary at all -- the live
Master was never touched, so there is nothing to restore or verify.

Run under SFM's own "Run Script" mechanism, exactly like the primary
checkpoint -- never imported as a library (this file, like every other
real-SFM checkpoint script in this project, ends with an unconditional
module-level main() call).
"""
import hashlib
import imp
import json
import os
import sys
import time

# ----------------------------------------------------------------------
# STARTUP FIX (2026-09-26, first real-SFM I1 attempt): see the identical,
# fully-commented fix in Checkpoint_I_Generation_Replacement.py for the
# full root-cause account -- a plain top-level `import I_Generation_
# Helper as igen` raised ImportError under SFM's own "Run Script"
# execution (which does NOT add the script's own directory to sys.path),
# producing zero qualification evidence. This is the identical
# exact-path, hash-pinned sibling-helper loader, applied here too. No
# reference to `igen` occurs anywhere above this point in the file.
# ----------------------------------------------------------------------
EXPECTED_I_HELPER_SHA256 = (
    "1d08b0282b0904f2993fc0aa0a98f73b5260291c7f3700ca9f946e3f447fbad7"
)


class HelperQualificationError(Exception):
    pass


def _mainmenu_dir_for_helper_loading():
    game_root = os.path.dirname(os.path.abspath(sys.executable))
    return os.path.join(game_root, "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D")


def _load_exact_i_helper():
    """Exact-path, hash-pinned sibling-helper loader -- see the module-
    level STARTUP FIX note above. Refuses (raises HelperQualificationError,
    no partial load) if the exact expected file is missing, or if its
    current on-disk bytes do not hash to EXACTLY EXPECTED_I_HELPER_SHA256.

    STARTUP FIX CORRECTION (second independent review, 2026-09-26): the
    first version of this loader used imp.load_source(name, helper_path)
    after hashing helper_path's own bytes. Under Python 2.7,
    imp.load_source() may substitute a matching sibling .pyc/.pyo for
    the .py file it was given (the same mechanism ordinary `import`
    uses) -- so hashing the .py bytes beforehand did NOT strictly prove
    those bytes were what actually got executed; a crafted/coincidental
    .pyc sitting next to the exact, correctly-hashed .py could have
    silently run instead. This version never calls imp.load_source() and
    never triggers any .pyc/.pyo lookup at all: it compiles and executes
    the EXACT already-hashed `helper_bytes` directly via compile() +
    exec() into a fresh module object's own __dict__."""
    helper_path = os.path.join(_mainmenu_dir_for_helper_loading(), "I_Generation_Helper.py")
    if not os.path.isfile(helper_path):
        raise HelperQualificationError(
            "Expected sibling helper not found at %r -- refusing to "
            "proceed." % (helper_path,)
        )
    fp = open(helper_path, "rb")
    try:
        helper_bytes = fp.read()
    finally:
        fp.close()
    actual_sha256 = hashlib.sha256(helper_bytes).hexdigest()
    if actual_sha256.lower() != EXPECTED_I_HELPER_SHA256.lower():
        raise HelperQualificationError(
            "Sibling helper at %r hashes to %r, not the exact approved "
            "%r -- refusing to load." % (helper_path, actual_sha256, EXPECTED_I_HELPER_SHA256)
        )

    # Compile the EXACT already-hashed bytes -- never a fresh read of the
    # file, never any .pyc/.pyo lookup of any kind.
    code = compile(helper_bytes, helper_path, "exec")

    qualified_module_name = "_sfm_i_generation_helper_qualified"
    # A stale prior load under this SAME qualification-specific name must
    # never be silently reused either -- always execute fresh from the
    # exact, just-hashed bytes.
    if qualified_module_name in sys.modules:
        del sys.modules[qualified_module_name]

    module = imp.new_module(qualified_module_name)
    module.__file__ = helper_path
    module.__package__ = None
    # Registered in sys.modules BEFORE exec, matching ordinary import
    # semantics, so a failure partway through execution can be cleanly
    # rolled back (no partially-initialized module left behind) --
    # module.__name__ is the synthetic qualified_module_name, never
    # "__main__", so I_Generation_Helper.py's own
    # `if __name__ == "__main__":` CLI guard cannot fire.
    sys.modules[qualified_module_name] = module
    try:
        exec(code, module.__dict__)
    except Exception:
        if sys.modules.get(qualified_module_name) is module:
            del sys.modules[qualified_module_name]
        raise

    loaded_file = os.path.normcase(os.path.abspath(getattr(module, "__file__", "") or ""))
    if loaded_file != os.path.normcase(os.path.abspath(helper_path)):
        raise HelperQualificationError(
            "Loaded helper module's own __file__ %r does not resolve to "
            "the intended path %r -- refusing to use it."
            % (loaded_file, helper_path)
        )
    return module


igen = _load_exact_i_helper()

EXPECTED_PRODUCTION_SHA256 = (
    "1f4ec5a26605aa90380eb0532fec3915d2cc24a3a20473ed70d57198bd995db7"
)
EXPECTED_G1_MASTER_SHA256 = igen.EXPECTED_CANONICAL_G1_MASTER_SHA256
EXPECTED_RUNTIME_API_VERSION = u"1.0.0-b2a"
EXPECTED_RUNTIME_BUILD_ID = u"package-boundary-corrected-2026-09-22"

PRODUCTION_INSTALLED_PATH = (
    "E:\\SteamLibrary\\steamapps\\common\\SourceFilmmaker\\game\\usermod"
    "\\scripts\\sfm\\mainmenu\\ChadChan3D\\Rebuild_Control_Groups_Normalizer.py"
)
CANONICAL_MASTER_INSTALLED_PATH = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)),
    "usermod", "cfg", "sfm_defaultanimationgroups.txt",
)
SHIPPED_AUTHORITY_DIR = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)),
    "usermod", "cfg", "sfm_shared_authority",
)

EVIDENCE_DIR = "C:\\Users\\Public\\Documents\\"
BASELINE_INVENTORY_ARTIFACT_PATH = EVIDENCE_DIR + "sfm_checkpoint_i_baseline_inventory.json"
FINALIZATION_RECORD_PATH = EVIDENCE_DIR + "sfm_checkpoint_i_finalization_record.json"
RESTORATION_VERIFY_RESULT_PATH = EVIDENCE_DIR + "sfm_checkpoint_i_restoration_verify_result.json"


class RestorationVerifyError(Exception):
    pass


# ----------------------------------------------------------------------
# Atomic-write primitive for this script's own evidence file -- verbatim
# pattern reused from the primary checkpoint. Never overwrites.
# ----------------------------------------------------------------------
def write_evidence_json_once(path, obj):
    if os.path.exists(path):
        raise RestorationVerifyError(
            "Refusing to overwrite existing evidence file: %r" % (path,)
        )
    tmp_path = path + ".tmp"
    text = json.dumps(obj, indent=2, sort_keys=True)
    fp = open(tmp_path, "wb")
    try:
        fp.write(text.encode("utf-8"))
        fp.flush()
        os.fsync(fp.fileno())
    finally:
        fp.close()
    fp2 = open(tmp_path, "rb")
    try:
        reparsed = json.loads(fp2.read().decode("utf-8"))
    finally:
        fp2.close()
    try:
        os.rename(tmp_path, path)
    except Exception as exc:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise RestorationVerifyError(
            "Refusing to overwrite existing evidence file (rename failed, "
            "target likely already exists): %r (%r)" % (path, exc)
        )
    return reparsed


def _gate(gate_checks, name, passed, detail=None):
    gate_checks.append({"name": name, "passed": bool(passed), "detail": detail})


def _locate_mainmenu_dir():
    # Single source of truth: the exact-path helper loader above already
    # derives this same directory before igen is ever bound.
    return _mainmenu_dir_for_helper_loading()


def import_authority_runtime():
    mainmenu_dir = _locate_mainmenu_dir()
    if mainmenu_dir not in sys.path:
        sys.path.insert(0, mainmenu_dir)
    from sfm_master_authority_productionized import runtime as authority_runtime
    return authority_runtime


def get_canonical_broker(authority_runtime):
    from PySide import QtCore
    return authority_runtime.get_broker(
        expected_api_version=EXPECTED_RUNTIME_API_VERSION,
        expected_build_id=EXPECTED_RUNTIME_BUILD_ID,
        is_main_thread_fn=lambda: (
            QtCore.QThread.currentThread()
            is QtCore.QCoreApplication.instance().thread()
        ),
    )


def main():
    gate_checks = []
    record = {
        "wall_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "epoch": time.time(),
        "current_pid": os.getpid(),
    }

    try:
        with open(PRODUCTION_INSTALLED_PATH, "rb") as fp:
            production_sha256 = hashlib.sha256(fp.read()).hexdigest()
    except Exception as exc:
        production_sha256 = None
        record["production_load_error"] = u"%r" % (exc,)
    record["production_sha256"] = production_sha256
    _gate(gate_checks, "identity.production_sha256_matches_expected",
          production_sha256 == EXPECTED_PRODUCTION_SHA256, production_sha256)

    try:
        with open(CANONICAL_MASTER_INSTALLED_PATH, "rb") as mf:
            current_master_sha256 = hashlib.sha256(mf.read()).hexdigest()
    except Exception as exc:
        current_master_sha256 = None
        record["current_master_read_error"] = u"%r" % (exc,)
    record["current_master_sha256"] = current_master_sha256
    _gate(gate_checks, "generation.live_master_is_exactly_canonical_g1",
          current_master_sha256 == EXPECTED_G1_MASTER_SHA256, current_master_sha256)

    try:
        main_window = sfmApp.GetMainWindow()  # noqa: F821 -- injected by SFM's own Run Script mechanism
    except Exception as exc:
        main_window = None
        record["main_window_error"] = u"%r" % (exc,)
    record["main_window_available"] = main_window is not None
    _gate(gate_checks, "state.main_window_available", main_window is not None, None)

    try:
        authority_runtime = import_authority_runtime()
        record["runtime_api_version"] = authority_runtime.RUNTIME_API_VERSION
        record["runtime_api_version_matches_expected"] = (
            authority_runtime.RUNTIME_API_VERSION == EXPECTED_RUNTIME_API_VERSION
        )
        record["runtime_build_id"] = getattr(authority_runtime, "RUNTIME_BUILD_ID", None)
        record["runtime_build_id_matches_expected"] = (
            record["runtime_build_id"] == EXPECTED_RUNTIME_BUILD_ID
        )
        record["runtime_is_canonical"] = authority_runtime.is_canonical()
        get_canonical_broker(authority_runtime)  # only to prove it is reachable/canonical
    except Exception as exc:
        record["runtime_api_version_matches_expected"] = False
        record["runtime_build_id_matches_expected"] = False
        record["runtime_is_canonical"] = False
        record["authority_import_or_broker_error"] = u"%r" % (exc,)
    _gate(gate_checks, "identity.runtime_api_version_matches_expected",
          record.get("runtime_api_version_matches_expected") is True, record.get("runtime_api_version"))
    _gate(gate_checks, "identity.runtime_build_id_matches_expected",
          record.get("runtime_build_id_matches_expected") is True, record.get("runtime_build_id"))
    _gate(gate_checks, "identity.runtime_is_canonical",
          record.get("runtime_is_canonical") is True, record.get("runtime_is_canonical"))

    baseline_inventory = igen.read_finalization_record_plain(BASELINE_INVENTORY_ARTIFACT_PATH)
    _gate(gate_checks, "restoration_verify.baseline_inventory_artifact_present",
          baseline_inventory is not None, None)
    record["baseline_inventory_artifact_path"] = BASELINE_INVENTORY_ARTIFACT_PATH
    record["baseline_inventory"] = baseline_inventory

    live_inventory = None
    comparison = None
    if baseline_inventory is not None:
        try:
            live_inventory = igen.capture_live_state_inventory(
                CANONICAL_MASTER_INSTALLED_PATH, SHIPPED_AUTHORITY_DIR,
            )
            comparison = igen.compare_inventories(baseline_inventory, live_inventory)
        except Exception as exc:
            record["independent_inventory_error"] = u"%r" % (exc,)
    _gate(gate_checks, "restoration_verify.independent_reverification_exact_match",
          comparison is not None and comparison.get("exact_match") is True,
          comparison.get("exact_match") if comparison else None)
    record["live_inventory"] = live_inventory
    record["comparison_to_baseline"] = comparison

    # Corroboration only -- never required. The independent inventory
    # comparison above is the authoritative check, exactly like the
    # primary checkpoint's own i_08 snapshot.
    finalization_record = igen.read_finalization_record_plain(FINALIZATION_RECORD_PATH)
    record["finalization_record_present"] = finalization_record is not None
    record["finalization_record_exact_match"] = (
        finalization_record.get("exact_match") if finalization_record else None
    )

    failed = [g["name"] for g in gate_checks if not g["passed"]]
    record["gate_checks"] = gate_checks
    record["failed_gates"] = failed
    if failed:
        record["classification"] = u"RESTORATION_NOT_CONFIRMED"
        record["gate_failure"] = u"%d restoration-verify check(s) failed: %s" % (
            len(failed), u", ".join(failed)
        )
    else:
        record["classification"] = u"RESTORATION_CONFIRMED"

    write_evidence_json_once(RESTORATION_VERIFY_RESULT_PATH, record)

    summary_lines = [
        u"CHECKPOINT I -- RESTORATION VERIFY (standalone, independent of the primary schedule)",
        u"wall_time = %s" % record["wall_time"],
        u"current_pid = %s" % record["current_pid"],
        u"classification = %s" % record["classification"],
        u"failed_gates = %s" % (record.get("failed_gates"),),
    ]
    summary_text = u"\n".join(summary_lines) + u"\n"
    try:
        sys.stdout.write(summary_text)
    except Exception:
        pass


main()
