# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint A: Bootstrap / Installed-
Authority Smoke Test.

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: NON-MUTATING -- zero scene mutation, zero native
Rebuild, zero save. This script does not touch vs.g_pDataModel, does
not create/modify/delete any group or control, and does not save
anything.

Purpose:
  Prove, from a REAL running SFM process, that the production-
  integrated qualified shared-authority package resolves, imports, and
  can acquire one small Normalizer-compatible detached projection of the
  REAL canonical Master TXT -- using ONLY the same sys.executable-
  derived discovery mechanism the accepted, integrated production
  Normalizer itself uses (commit
  68f1188e7dcb3fdd34d384396bf5d7a14acf7d25).

  Every step below is wrapped so a failure is recorded as a FAIL line,
  never an unhandled exception that would only show a raw traceback.

Output:
  A single text report is written to:
    C:\\Users\\Public\\Documents\\sfm_checkpoint_a_bootstrap_smoke.txt
  A short summary is also printed to SFM's own console/output.

Do not save the SFM project after running this script. Do not modify
this file to "fix" a failure -- report the exact result instead.
"""
import ctypes
import hashlib
import os
import sys
import time
import traceback

OUTPUT_PATH = (
    "C:\\Users\\Public\\Documents\\"
    "sfm_checkpoint_a_bootstrap_smoke.txt"
)

EXPECTED_API_VERSION = "1.0.0-b2a"
EXPECTED_BUILD_ID = "package-boundary-corrected-2026-09-22"
EXPECTED_CANONICAL_MASTER_SHA256 = (
    "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, bool(condition), detail))


def _safe_repr(value):
    try:
        return repr(value)
    except Exception:
        return "<unrepr-able>"


lines = []
lines.append("SFM CHECKPOINT A -- BOOTSTRAP / INSTALLED-AUTHORITY SMOKE TEST")
lines.append("started_at=%r" % time.strftime("%Y-%m-%d %H:%M:%S"))
lines.append("python_version=%r" % sys.version)
lines.append("")

broker = None
lease = None

try:
    game_root = os.path.dirname(os.path.abspath(sys.executable))
    lines.append("sys.executable=%r" % sys.executable)
    lines.append("derived_game_root=%r" % game_root)
    check("game_root.derived_without_exception", True)

    mainmenu_dir = os.path.join(
        game_root, "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
    )
    lines.append("expected_mainmenu_dir=%r" % mainmenu_dir)
    check("mainmenu_dir.exists_on_disk", os.path.isdir(mainmenu_dir), mainmenu_dir)

    authority_root = os.path.join(mainmenu_dir, "sfm_master_authority_productionized")
    sidecar_root = os.path.join(mainmenu_dir, "sfm_master_sidecar")
    check("authority_package_dir.exists_on_disk", os.path.isdir(authority_root), authority_root)
    check("sidecar_package_dir.exists_on_disk", os.path.isdir(sidecar_root), sidecar_root)

    if mainmenu_dir not in sys.path:
        sys.path.insert(0, mainmenu_dir)

    from sfm_master_authority_productionized import runtime as authority_runtime
    from sfm_master_authority_productionized import errors as authority_errors
    from sfm_master_authority_productionized import normalizer_compat_adapter as authority_compat_adapter
    check("import.sfm_master_authority_productionized_runtime", True)

    actual_origin_dir = authority_runtime.get_actual_origin_dir()
    lines.append("authority_runtime_origin_dir=%r" % actual_origin_dir)
    check(
        "authority_runtime.origin_matches_installed_package_dir",
        os.path.normcase(os.path.normpath(actual_origin_dir))
        == os.path.normcase(os.path.normpath(authority_root)),
        actual_origin_dir,
    )

    check(
        "authority_runtime.api_version_matches_expected",
        authority_runtime.RUNTIME_API_VERSION == EXPECTED_API_VERSION,
        authority_runtime.RUNTIME_API_VERSION,
    )
    check(
        "authority_runtime.build_id_matches_expected",
        authority_runtime.RUNTIME_BUILD_ID == EXPECTED_BUILD_ID,
        authority_runtime.RUNTIME_BUILD_ID,
    )
    check("authority_runtime.is_canonical", authority_runtime.is_canonical())

    lines.append("RUNTIME_API_VERSION=%r" % authority_runtime.RUNTIME_API_VERSION)
    lines.append("RUNTIME_BUILD_ID=%r" % authority_runtime.RUNTIME_BUILD_ID)

    master_path = os.path.join(game_root, "usermod", "cfg", "sfm_defaultanimationgroups.txt")
    check("master_path.exists_on_disk", os.path.isfile(master_path), master_path)

    master_file = open(master_path, "rb")
    try:
        master_bytes = master_file.read()
    finally:
        master_file.close()
    master_sha = hashlib.sha256(master_bytes).hexdigest()
    lines.append("live_master_path=%r" % master_path)
    lines.append("live_master_sha256=%s" % master_sha)
    check(
        "master_sha256.matches_expected_canonical",
        master_sha == EXPECTED_CANONICAL_MASTER_SHA256,
        master_sha,
    )

    is_main_thread_fn = None
    try:
        from PySide import QtCore
        is_main_thread_fn = lambda: (
            QtCore.QThread.currentThread()
            is QtCore.QCoreApplication.instance().thread()
        )
    except Exception:
        is_main_thread_fn = None

    broker = authority_runtime.get_broker(
        expected_api_version=EXPECTED_API_VERSION,
        expected_build_id=EXPECTED_BUILD_ID,
        is_main_thread_fn=is_main_thread_fn,
    )
    check("broker.constructed", broker is not None)
    lines.append("broker_state=%r" % authority_runtime.get_state())

    shipped_root = os.path.join(game_root, "usermod", "cfg", "sfm_shared_authority")
    lines.append("shipped_root=%r" % shipped_root)
    check("shipped_root.exists_on_disk", os.path.isdir(shipped_root), shipped_root)

    wanted_folds = frozenset()
    request_specs = {
        "checkpoint_a_smoke": (
            wanted_folds,
            authority_compat_adapter.build_targeted_master_compatible_projection(wanted_folds),
        ),
    }

    detached = broker.acquire_or_reuse_views(
        master_path, request_specs, shipped_root=shipped_root, expected_generation=master_sha,
    )
    check("acquisition.detached_view_returned", "checkpoint_a_smoke" in detached)
    view = detached.get("checkpoint_a_smoke")

    if view is not None:
        payload = view.payload
        check(
            "projection.has_expected_keys",
            set(payload.keys()) == set([
                "mapping_count", "destination_count", "folded",
                "exact_literals", "group_sibling_order", "group_metadata",
            ]),
            sorted(payload.keys()),
        )
        lines.append("projection_mapping_count=%r" % payload.get("mapping_count"))
        lines.append("projection_destination_count=%r" % payload.get("destination_count"))
        lines.append("projection_group_count=%r" % len(payload.get("group_metadata", {})))

        check(
            "projection.semantic_generation_matches_live_master_sha",
            view.semantic_generation.master_sha256 == master_sha,
            view.semantic_generation.master_sha256,
        )

        after_counters = broker.provider_counters()
        check(
            "provider.closed_before_return",
            after_counters.get("current_open_provider_count") == 0,
            after_counters,
        )

        lease = broker.lease_view(view)
        check("lease.acquired", lease is not None)

        broker.release_view_lease(lease)
        lease = None
        check("lease.released_cleanly", True)

        final_counters = broker.provider_counters()
        check(
            "provider.zero_open_after_release",
            final_counters.get("current_open_provider_count") == 0,
            final_counters,
        )

except Exception as exc:
    lines.append("EXCEPTION: %s" % _safe_repr(exc))
    lines.append(traceback.format_exc())
    check("checkpoint_a.completed_without_unhandled_exception", False, exc)
else:
    check("checkpoint_a.completed_without_unhandled_exception", True)

finally:
    if lease is not None:
        try:
            broker.release_view_lease(lease)
        except Exception:
            pass

lines.append("")
lines.append("--- CHECKS ---")
all_pass = True
for name, ok, detail in RESULTS:
    status = "PASS" if ok else "FAIL"
    if not ok:
        all_pass = False
    if detail is None:
        lines.append("[%s] %s" % (status, name))
    else:
        lines.append("[%s] %s -- %s" % (status, name, _safe_repr(detail)))

lines.append("")
lines.append(
    "RESULT: %d/%d %s"
    % (
        sum(1 for _, ok, _ in RESULTS if ok),
        len(RESULTS),
        "ALL PASS" if all_pass else "SOME FAILED",
    )
)
lines.append("finished_at=%r" % time.strftime("%Y-%m-%d %H:%M:%S"))

report_text = "\n".join(lines) + "\n"

write_ok = True
try:
    out_file = open(OUTPUT_PATH, "wb")
    try:
        out_file.write(report_text.encode("ascii", "replace"))
    finally:
        out_file.close()
except Exception:
    write_ok = False

try:
    sys.stdout.write(report_text)
    sys.stdout.write(
        "\nCheckpoint A report written to: %s (write_ok=%r)\n" % (OUTPUT_PATH, write_ok)
    )
except Exception:
    pass
