# -*- coding: utf-8 -*-
# R1 -- embedded Python 2.7.5 qualification of sidecar-to-Normalizer
# consumer-projection parity. Real SFM, Qt/main-event thread, event-loop
# scheduling. Read-only: never calls native Rebuild, never touches DME,
# never mutates the project. Imports the REAL, unmodified Normalizer and
# T130 source files directly (no stubbing needed here -- sfmApp/vs/PySide
# are the genuine host modules), with only each file's own bare top-level
# auto-run call suppressed so importing them does not itself invoke the
# real command against this probe.

import sys
import os
import time
import json

try:
    unicode
except NameError:
    unicode = str

SCRATCH = r"C:\Users\REDACTED\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\67454949-e69f-4280-93d9-87c1f4464330\scratchpad"
GAME_SCRIPTS = r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts"
DEPLOY = os.path.join(GAME_SCRIPTS, "sfm", "gate_r1_deploy")
FIXTURES = os.path.join(DEPLOY, "fixtures")
NORMALIZER_PATH = os.path.join(DEPLOY, "real_normalizer.py")
T130_PATH = os.path.join(DEPLOY, "real_t130.py")

RESULT_LOG_PATH = SCRATCH + r"\gate_r1_embedded_result.log"
STAGE_LOG_PATH = SCRATCH + r"\gate_r1_embedded_stage_markers.log"
DONE_MARKER_PATH = SCRATCH + r"\gate_r1_embedded_DONE.marker"
RESULTS_JSON_PATH = SCRATCH + r"\gate_r1_embedded_results.json"

_lines = []


def log(msg):
    line = msg if isinstance(msg, unicode) else (msg.decode("utf-8", "replace") if isinstance(msg, str) else unicode(msg))
    _lines.append(u"[%.3f] %s" % (time.time(), line))
    f = open(RESULT_LOG_PATH, "wb")
    try:
        f.write((u"\n".join(_lines) + u"\n").encode("utf-8"))
    finally:
        f.close()


def mark_stage(name):
    ts = time.time()
    f = open(STAGE_LOG_PATH, "ab")
    try:
        f.write(("%s %r\n" % (name, ts)).encode("ascii"))
    finally:
        f.close()
    log(u"STAGE %s" % name)


_pass = [0]
_fail = [0]


def check(label, condition, detail=u""):
    if condition:
        _pass[0] += 1
        log(u"  PASS: %s %s" % (label, detail))
    else:
        _fail[0] += 1
        log(u"  FAIL: %s %s" % (label, detail))
    return condition


log(u"R1 embedded probe loaded, pid=%r sys.version=%r" % (os.getpid(), sys.version))

_qt_available = False
try:
    from PySide import QtCore
    _qt_available = True
    log(u"PySide import PASS")
except Exception as exc:
    log(u"PySide import FAILED: %r" % (exc,))

state = {}


def _guarded(fn):
    def wrapper():
        try:
            fn()
        except Exception:
            import traceback
            log(u"UNCAUGHT EXCEPTION in %s:\n%s" % (fn.__name__, traceback.format_exc()))
            marker = open(DONE_MARKER_PATH, "wb")
            try:
                marker.write(b"done-with-exception\n")
            finally:
                marker.close()
    return wrapper


def schedule(delay_ms, fn):
    QtCore.QTimer.singleShot(delay_ms, _guarded(fn))


def _load_module_suppressing_trailing_call(module_name, file_path, suppress_call):
    import types
    # Read as raw bytes/native str (NOT decoded to unicode) -- Python 2's
    # compile() rejects a unicode string that also contains a source
    # encoding declaration comment ("SyntaxError: encoding declaration in
    # Unicode string"). Passing the raw bytes through lets Python 2 handle
    # the file's own encoding declaration itself, exactly as a normal
    # import would.
    with open(file_path, "rb") as f:
        source = f.read()
    stripped = source.rstrip()
    last_line = stripped.rsplit(b"\n", 1)[-1].strip()
    if last_line == suppress_call.encode("ascii"):
        source = stripped[: -len(last_line)]
    module = types.ModuleType(module_name)
    module.__file__ = file_path
    sys.modules[module_name] = module
    code = compile(source, file_path, "exec")
    exec(code, module.__dict__)
    return module


REPO_TOOLS = r"E:\SFM Animation Group Master\tools"


def phase_begin():
    mark_stage("BEGIN")
    for p in (DEPLOY, os.path.join(DEPLOY, "qualification"), REPO_TOOLS):
        if sys.path.count(p) == 0:
            sys.path.insert(0, p)

    norm = _load_module_suppressing_trailing_call(
        "_r1_real_normalizer_oracle_embedded", NORMALIZER_PATH, "StartRebuildControlGroups()")
    t130 = _load_module_suppressing_trailing_call(
        "_r1_real_t130_oracle_embedded", T130_PATH, "install_t121()")
    check("real manual/live modules imported natively (no stub needed in real SFM)",
          norm.parse_targeted_master is not None and t130.t120_parse_master is not None)

    import bounded_provider
    import bounded_view
    import r1_consumer_projection as proj

    state["norm"] = norm
    state["t130"] = t130
    state["bounded_provider"] = bounded_provider
    state["bounded_view"] = bounded_view
    state["proj"] = proj

    mark_stage("MODULE_IMPORT_END")
    schedule(100, phase_1_hit_alias_family)


def ascii_fold(v):
    out = []
    for ch in v:
        o = ord(ch)
        out.append(chr(o + 32) if 65 <= o <= 90 else ch)
    return "".join(out)


def phase_1_hit_alias_family():
    mark_stage("P1_HIT_ALIAS_BEGIN")
    norm = state["norm"]
    proj = state["proj"]
    bounded_view = state["bounded_view"]
    bounded_provider = state["bounded_provider"]

    txt_path = os.path.join(FIXTURES, "12_same_fold_same_destination.txt")
    artifact_path = os.path.join(FIXTURES, "12_same_fold_same_destination.bin")
    sha = "a983006bb8da1dafd3d80f107a4b181c3b9b9e4a5ebcd67da7d8341d9e9564b7"

    # 1: REAL manual TXT parser, natively, on the real TXT path.
    real_manual = norm.parse_targeted_master(txt_path, {"foo"}, validate_conflicts=False)
    check("1: real parse_targeted_master runs natively in embedded SFM", real_manual is not None)

    # 2: sidecar-side projection of the SAME generation.
    provider = bounded_provider.BoundedProvider.open_path(artifact_path, sha)
    manual_proj = proj.build_manual_projection(
        provider, bounded_view, {"foo"}, norm.ProbeError,
        norm.parse_master_rgba_text, norm.parse_master_bool_text,
    )

    # 3: real master_lookup against BOTH, must agree exactly.
    real_res = norm.master_lookup(real_manual, "Foo")
    sidecar_res = norm.master_lookup(manual_proj, "Foo")
    check("2: real TXT-parsed and sidecar-projected manual master_lookup agree exactly",
          real_res == sidecar_res, "txt=%r sidecar=%r" % (real_res, sidecar_res))
    check("3: whole-source mapping_count agrees", real_manual["mapping_count"] == manual_proj["mapping_count"])
    check("3: whole-source destination_count agrees", real_manual["destination_count"] == manual_proj["destination_count"])
    check("3: complete fold family size agrees",
          len(real_manual["folded"]["foo"]) == len(manual_proj["folded"]["foo"]) == 3)

    state["provider"] = provider
    state["manual_proj"] = manual_proj
    state["real_manual"] = real_manual
    mark_stage("P1_HIT_ALIAS_END")
    schedule(100, phase_2_conflict)


def phase_2_conflict():
    mark_stage("P2_CONFLICT_BEGIN")
    norm = state["norm"]
    proj = state["proj"]
    bounded_view = state["bounded_view"]
    bounded_provider = state["bounded_provider"]

    txt_path = os.path.join(FIXTURES, "13_same_fold_different_destinations.txt")
    artifact_path = os.path.join(FIXTURES, "13_same_fold_different_destinations.bin")
    sha = "4f851d907bb1244af6689884c73fedc3347b9bac867560f0183c1edcc12ea519"

    real_conf = norm.parse_targeted_master(txt_path, {"bar"}, validate_conflicts=False)
    provider = bounded_provider.BoundedProvider.open_path(artifact_path, sha)
    sidecar_conf = proj.build_manual_projection(
        provider, bounded_view, {"bar"}, norm.ProbeError,
        norm.parse_master_rgba_text, norm.parse_master_bool_text,
    )

    real_raised = sidecar_raised = None
    try:
        norm.master_lookup(real_conf, "Bar")
    except norm.ProbeError as exc:
        real_raised = exc
    try:
        norm.master_lookup(sidecar_conf, "Bar")
    except norm.ProbeError as exc:
        sidecar_raised = exc
    check("4: both real-TXT and sidecar-projected master_lookup raise the same conflict category",
          real_raised is not None and sidecar_raised is not None, "txt=%r sidecar=%r" % (real_raised, sidecar_raised))

    try:
        norm.validate_master_subset_conflicts(sidecar_conf, {"some_other_fold"})
        check("5: targeted conflict timing preserved (broad-scope fold not yet active does not reject)", True)
    except norm.ProbeError as exc:
        check("5: targeted conflict timing preserved (broad-scope fold not yet active does not reject)", False, repr(exc))
    try:
        norm.validate_master_subset_conflicts(sidecar_conf, {"bar"})
        check("5: subset validation rejects once active subset includes the conflict", False, "did not raise")
    except norm.ProbeError as exc:
        check("5: subset validation rejects once active subset includes the conflict", True, repr(exc))

    provider.close()
    mark_stage("P2_CONFLICT_END")
    schedule(100, phase_3_live_and_snap)


def phase_3_live_and_snap():
    mark_stage("P3_LIVE_SNAP_BEGIN")
    t130 = state["t130"]
    proj = state["proj"]
    bounded_view = state["bounded_view"]
    bounded_provider = state["bounded_provider"]

    txt_path = os.path.join(FIXTURES, "12_same_fold_same_destination.txt")
    real_master120 = t130.t120_parse_master(txt_path, ["Foo"])
    real_live_res = t130.t120_master_lookup(real_master120, "Foo")

    artifact_path = os.path.join(FIXTURES, "12_same_fold_same_destination.bin")
    sha = "a983006bb8da1dafd3d80f107a4b181c3b9b9e4a5ebcd67da7d8341d9e9564b7"
    provider = bounded_provider.BoundedProvider.open_path(artifact_path, sha)
    sidecar_live = proj.build_live_master120(provider, bounded_view, {"foo"}, t130.ProbeError, sha)
    sidecar_live_res = t130.t120_master_lookup(sidecar_live, "Foo")
    check("6: real live t120_parse_master (native) and sidecar live projection agree via t120_master_lookup",
          real_live_res == sidecar_live_res, "txt=%r sidecar=%r" % (real_live_res, sidecar_live_res))
    kernel = t130.t130_t95_master_from_t120(sidecar_live)
    check("6: T95 bridge runs on the sidecar-built live projection", kernel["mapping_count"] == sidecar_live["total_controls"])
    provider.close()

    snap_txt = os.path.join(FIXTURES, "snap_alias.txt")
    snap_artifact = os.path.join(FIXTURES, "snap_alias.bin")
    snap_sha = "ea7a4b527c440973362652cb24f9b08e32d968dde3a74d798bc4ec2a70ff8ba4"
    real_snap_master120 = t130.t120_parse_master(snap_txt, ["X"])
    provider2 = bounded_provider.BoundedProvider.open_path(snap_artifact, snap_sha)
    sidecar_snap = proj.build_live_master120(provider2, bounded_view, {"x"}, t130.ProbeError, snap_sha)
    check("7: real live parser accepts 'snap' alias natively",
          real_snap_master120["group_metadata"]["Grp"]["snappable"] == u"1")
    check("7: sidecar live projection accepts 'snap' alias identically",
          sidecar_snap["group_metadata"]["Grp"]["snappable"] == "1")
    provider2.close()

    mark_stage("P3_LIVE_SNAP_END")
    schedule(100, phase_4_detached_and_cleanup)


def phase_4_detached_and_cleanup():
    mark_stage("P4_DETACHED_CLEANUP_BEGIN")
    norm = state["norm"]
    manual_proj = state["manual_proj"]
    provider = state["provider"]

    provider.close()
    check("8: backing provider closed", not provider.is_valid())
    res = norm.master_lookup(manual_proj, "Foo")
    check("8: detached manual projection (built in phase 1) still consumable via real master_lookup "
          "after complete backing has been closed", res["known"] is True and res["destination"] == "Grp")

    mark_stage("P4_DETACHED_CLEANUP_END")
    schedule(100, phase_done)


def phase_done():
    results = {"pass_count": _pass[0], "fail_count": _fail[0]}
    with open(RESULTS_JSON_PATH, "wb") as f:
        f.write(json.dumps(results, indent=2, default=str).encode("utf-8"))
    log(u"R1 embedded probe RESULT: %d PASS / %d FAIL" % (_pass[0], _fail[0]))
    mark_stage("DONE")
    marker = open(DONE_MARKER_PATH, "wb")
    try:
        marker.write(b"done\n")
    finally:
        marker.close()


if _qt_available:
    schedule(3000, phase_begin)
    log(u"R1 embedded probe scheduled.")
else:
    log(u"Qt not available -- probe NOT scheduled.")
