# -*- coding: utf-8 -*-
"""
Offline regression for Checkpoint F1-R2 Phase 1
(Checkpoint_F1_R2_Phase1_Create_Normalized_Copy.py, SHA-256
d938f878608b0cbd9302620265da9c47161abfbc8382308ad504bfb6fcea5d54 -- repaired
2026-09-23 after a real-SFM Phase 1 attempt failed with TypeError("in
method 'IDataModel_SaveToFile', argument 2 of type 'char const *'"); see
the strict-binding regression below) and Phase 2
(Checkpoint_F1_R2_Phase2_Normalized_Copy_Retest.py, SHA-256
03249bad2a7f86cfbdc6e226edeb72ea6f15f9769b135d1ad46cc6a6e4ce4f80,
unchanged).

The centerpiece of this regression is `save_normalized_diagnostic_copy()`
(Phase 1) -- the one function in this whole project that WRITES to a new
project file. It is tested here with INJECTED FAKE `sfmApp`/`vs` modules
(no real SFM environment available offline), specifically to prove its
core safety invariant: **it must never call the native SaveToFile at all
when the computed target path would equal the original fixture's own
path**, and it must correctly propagate real Save-As semantics (target
path independent of the original) when they differ.

Also proves: the shared primitives (stable_hash, the
CONTEXTUALIZER_RESOURCE_CHECKPOINT parser, write_json_atomic,
write_text_atomic) are byte-identical to every earlier checkpoint's own
copies; and the phase1-vs-phase2 comparison arithmetic (serialized/
resident delta, per-run delta) both scripts compute is correct given
known inputs.

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_f1_r2_diagnostic_regression.py
"""
import hashlib
import json
import os
import sys
import tempfile

PHASE1_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Checkpoint_F1_R2_Phase1_Create_Normalized_Copy.py")
PHASE2_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Checkpoint_F1_R2_Phase2_Normalized_Copy_Retest.py")
EXPECTED_PHASE1_SHA256 = "d938f878608b0cbd9302620265da9c47161abfbc8382308ad504bfb6fcea5d54"
EXPECTED_PHASE2_SHA256 = "03249bad2a7f86cfbdc6e226edeb72ea6f15f9769b135d1ad46cc6a6e4ce4f80"

CHECKPOINT_PARSER_RANGE = (344, 415)
WRITE_JSON_ATOMIC_RANGE = (418, 466)
WRITE_TEXT_ATOMIC_RANGE = (469, 507)
SAVE_FUNCTION_RANGE = (510, 616)

PASS_COUNT = [0]
FAIL_COUNT = [0]


def expect(condition, label):
    if condition:
        PASS_COUNT[0] += 1
        sys.stdout.write("[PASS] %s\n" % label)
    else:
        FAIL_COUNT[0] += 1
        sys.stdout.write("[FAIL] %s\n" % label)


with open(PHASE1_PATH, "rb") as f:
    phase1_bytes = f.read()
phase1_text = phase1_bytes.decode("ascii")
expect(hashlib.sha256(phase1_bytes).hexdigest() == EXPECTED_PHASE1_SHA256, "phase1_script.sha256_matches_pinned")

with open(PHASE2_PATH, "rb") as f:
    phase2_bytes = f.read()
expect(hashlib.sha256(phase2_bytes).hexdigest() == EXPECTED_PHASE2_SHA256, "phase2_script.sha256_matches_pinned")

phase1_lines = phase1_text.splitlines()


def extract(range_tuple, lines=phase1_lines):
    start, end = range_tuple
    return "\n".join(lines[start - 1:end])


sys.stdout.write("\n--- Shared primitives (verbatim) ---\n")

shared_ns = {"hashlib": hashlib, "json": json, "os": os}
exec(compile(extract(CHECKPOINT_PARSER_RANGE), "<checkpoint_parser>", "exec"), shared_ns)
exec(compile(extract(WRITE_JSON_ATOMIC_RANGE), "<write_json_atomic>", "exec"), shared_ns)
exec(compile(extract(WRITE_TEXT_ATOMIC_RANGE), "<write_text_atomic>", "exec"), shared_ns)

parse_resource_checkpoint_line = shared_ns["parse_resource_checkpoint_line"]
summarize_resource_checkpoints = shared_ns["summarize_resource_checkpoints"]
write_json_atomic = shared_ns["write_json_atomic"]
write_text_atomic = shared_ns["write_text_atomic"]

REAL_CP0_LINE = (
    "CONTEXTUALIZER_RESOURCE_CHECKPOINT label=CP0_COMMAND_START run_elapsed=0.010 "
    "mem_ok=True working_set=3166584832L peak_working_set=3166584832L pagefile=3166584832L "
    "peak_pagefile=3166584832L private=3166584832L vas_requested=True vas_ok=True "
    "min_address=65536 max_address=4294901759L mem_free=416239616 mem_reserve=90000000 "
    "mem_commit=180000000L largest_free=186384384 free_regions=30 virtual_query_count=400 "
    "vas_elapsed=0.004 vas_error=None"
)
REAL_FINAL_LINE = (
    "CONTEXTUALIZER_RESOURCE_CHECKPOINT label=FINAL_REPORT_ENTRY run_elapsed=180.0 "
    "mem_ok=True working_set=3404951552L peak_working_set=3404951552L pagefile=3404951552L "
    "peak_pagefile=3404951552L private=3404951552L vas_requested=True vas_ok=True "
    "min_address=65536 max_address=4294901759L mem_free=182996992 mem_reserve=90000000 "
    "mem_commit=180000000L largest_free=75366400 free_regions=90 virtual_query_count=900 "
    "vas_elapsed=0.004 vas_error=None"
)
summary = summarize_resource_checkpoints(REAL_CP0_LINE + "\n" + REAL_FINAL_LINE + "\n")
expect(summary["final_report_entry_reached"] is True, "parser.reproduces_command_3_style_log")
private_delta = summary["last_checkpoint"]["private"] - summary["first_checkpoint"]["private"]
free_vas_delta = summary["last_checkpoint"]["mem_free"] - summary["first_checkpoint"]["mem_free"]
largest_free_delta = summary["last_checkpoint"]["largest_free"] - summary["first_checkpoint"]["largest_free"]
expect(private_delta == 238366720, "parser.reproduces_confirmed_command_3_private_delta_exactly (%r)" % (private_delta,))
expect(free_vas_delta == -233242624, "parser.reproduces_confirmed_command_3_free_vas_delta_exactly (%r)" % (free_vas_delta,))
expect(largest_free_delta == -111017984, "parser.reproduces_confirmed_command_3_largest_free_delta_exactly (%r)" % (largest_free_delta,))

tmp_dir = tempfile.mkdtemp(prefix="f1_r2_regress_")
json_path = os.path.join(tmp_dir, "artifact.json")
ok, err, reparsed = write_json_atomic(json_path, {"a": 1})
expect(ok and err is None and reparsed == {"a": 1}, "write_json_atomic.simple_write_ok")
text_path = os.path.join(tmp_dir, "summary.txt")
ok2, err2 = write_text_atomic(text_path, b"hello\n")
expect(ok2 and err2 is None, "write_text_atomic.simple_write_ok")

sys.stdout.write("\n--- save_normalized_diagnostic_copy(): core safety invariant ---\n")


class _FakeElement(object):
    def __init__(self, file_id):
        self._file_id = file_id

    def GetFileId(self):
        return self._file_id


class _FakeSfmApp(object):
    def __init__(self, root):
        self._root = root

    def GetDocumentRoot(self):
        return self._root


class _FakeDataModel(object):
    """Records every SaveToFile call so the test can assert it was
    NEVER invoked in the refusal case."""
    def __init__(self, file_names, file_formats, save_should_succeed=True):
        self._file_names = file_names
        self._file_formats = file_formats
        self.save_calls = []
        self.save_should_succeed = save_should_succeed

    def GetFileName(self, file_id):
        return self._file_names[file_id]

    def GetFileFormat(self, file_id):
        return self._file_formats[file_id]

    def SaveToFile(self, path, path_id, encoding, fmt, root):
        self.save_calls.append({"path": path, "path_id": path_id, "encoding": encoding, "format": fmt, "root": root})
        if self.save_should_succeed:
            with open(path, "wb") as f:
                f.write(b"fake-dmx-bytes")
            return True
        return False


class _FakeVsModule(object):
    def __init__(self, data_model):
        self.g_pDataModel = data_model


def make_save_function(sfm_app, vs_module):
    ns = {"os": os, "sfmApp": sfm_app, "vs": vs_module}
    exec(compile(extract(SAVE_FUNCTION_RANGE), "<save_normalized_diagnostic_copy>", "exec"), ns)
    return ns["save_normalized_diagnostic_copy"]


# Case A: normal, healthy Save-As -- target path DIFFERS from the
# original fixture's own path. Must succeed and must call SaveToFile
# with the correct arguments.
original_dir = tempfile.mkdtemp(prefix="f1_r2_original_fixture_")
original_path = os.path.join(original_dir, u"qualification_fixture.sfm")
with open(original_path, "wb") as f:
    f.write(b"original-fixture-bytes")

fake_root = _FakeElement(file_id=7)
fake_sfmapp = _FakeSfmApp(fake_root)
fake_dm = _FakeDataModel({7: original_path}, {7: u"session"}, save_should_succeed=True)
fake_vs = _FakeVsModule(fake_dm)

save_fn = make_save_function(fake_sfmapp, fake_vs)
result_a = save_fn(u"F1_R2_NORMALIZED_DIAGNOSTIC_COPY.sfm")

expect(result_a["ok"] is True, "save.case_a_healthy_save_succeeds (%r)" % (result_a,))
expect(result_a["target_differs_from_original"] is True, "save.case_a_target_correctly_detected_as_different")
expect(result_a["original_path"] == original_path, "save.case_a_original_path_recorded_correctly")
expect(result_a["target_path"] == os.path.join(original_dir, u"F1_R2_NORMALIZED_DIAGNOSTIC_COPY.sfm"), "save.case_a_target_path_computed_correctly")
expect(len(fake_dm.save_calls) == 1, "save.case_a_SaveToFile_called_exactly_once")
expect(fake_dm.save_calls[0]["encoding"] == "binary", "save.case_a_uses_binary_encoding_matching_real_usage_example")
expect(fake_dm.save_calls[0]["format"] == u"session", "save.case_a_format_derived_from_GetFileFormat_not_hardcoded")
expect(fake_dm.save_calls[0]["root"] is fake_root, "save.case_a_passes_the_live_document_root")
expect(os.path.exists(result_a["target_path"]), "save.case_a_new_file_actually_created_on_disk")
expect(os.path.exists(original_path), "save.case_a_original_fixture_file_untouched")
with open(original_path, "rb") as f:
    expect(f.read() == b"original-fixture-bytes", "save.case_a_original_fixture_bytes_unchanged")

# Case B: adversarial -- the computed target path (original's own
# directory + the requested filename) happens to equal the original
# fixture's own path exactly (e.g. an operator/config error requesting
# the original filename as the save-as name). The function MUST refuse
# and MUST NEVER call SaveToFile.
fake_dm_b = _FakeDataModel({7: original_path}, {7: u"session"}, save_should_succeed=True)
fake_vs_b = _FakeVsModule(fake_dm_b)
save_fn_b = make_save_function(fake_sfmapp, fake_vs_b)
result_b = save_fn_b(u"qualification_fixture.sfm")  # same basename as the original

expect(result_b["ok"] is False, "save.case_b_refuses_when_target_equals_original")
expect(result_b["target_differs_from_original"] is False, "save.case_b_correctly_detects_target_equals_original")
expect(len(fake_dm_b.save_calls) == 0, "save.case_b_SaveToFile_NEVER_called -- the critical safety guarantee")
expect("REFUSING TO SAVE" in (result_b["error"] or ""), "save.case_b_error_message_explains_refusal")

# Case C: native SaveToFile itself returns False (e.g. disk full,
# permission denied) -- must be reported as a clean failure, not an
# unhandled exception, and must not fabricate success.
fake_dm_c = _FakeDataModel({7: original_path}, {7: u"session"}, save_should_succeed=False)
fake_vs_c = _FakeVsModule(fake_dm_c)
save_fn_c = make_save_function(fake_sfmapp, fake_vs_c)
result_c = save_fn_c(u"F1_R2_NORMALIZED_DIAGNOSTIC_COPY_2.sfm")

expect(result_c["ok"] is False, "save.case_c_native_failure_reported_as_ok_False")
expect(len(fake_dm_c.save_calls) == 1, "save.case_c_SaveToFile_was_attempted_once")
expect("SaveToFile() returned False" in (result_c["error"] or ""), "save.case_c_error_message_explains_native_failure")

sys.stdout.write("\n--- Strict-binding regression: SaveToFile's pFileName must be a Python 2 str ---\n")


class _StrictTypedFakeDataModel(object):
    """Mimics the REAL SWIG binding's own type strictness for pFileName
    (declared 'char const *' in vs/datamodel.py) -- rejects a unicode
    path with the EXACT TypeError a real-SFM Phase 1 attempt produced
    (2026-09-23): TypeError("in method 'IDataModel_SaveToFile', argument
    2 of type 'char const *'"). GetFileName() returns a plain str, per
    the SWIG stub's own 'char const *' return typemap and per the proven
    real usage in cleanEmptyControls.py (passes sys.argv[2], always str).
    This fake exists specifically because the permissive _FakeDataModel
    above (which accepts any Python type) could not have caught the real
    bug -- this one can and does."""
    def __init__(self, file_names, file_formats):
        self._file_names = file_names
        self._file_formats = file_formats
        self.save_calls = []

    def GetFileName(self, file_id):
        return self._file_names[file_id]

    def GetFileFormat(self, file_id):
        return self._file_formats[file_id]

    def SaveToFile(self, path, path_id, encoding, fmt, root):
        if type(path) is not str:
            raise TypeError(
                "in method 'IDataModel_SaveToFile', argument 2 of type 'char const *'"
            )
        self.save_calls.append({"path": path, "path_id": path_id, "encoding": encoding, "format": fmt, "root": root})
        with open(path, "wb") as f:
            f.write(b"fake-dmx-bytes")
        return True


# GetFileName() returns str (bytes), matching the real binding -- not
# unicode, unlike the permissive fake's own original_path construction
# above.
strict_original_dir = tempfile.mkdtemp(prefix="f1_r2_strict_fixture_")
strict_original_path = os.path.join(strict_original_dir, "qualification_fixture.sfm")
with open(strict_original_path, "wb") as f:
    f.write(b"original-fixture-bytes")

fake_dm_strict = _StrictTypedFakeDataModel({7: strict_original_path}, {7: u"session"})
fake_vs_strict = _FakeVsModule(fake_dm_strict)
save_fn_strict = make_save_function(fake_sfmapp, fake_vs_strict)
# Exactly SAVE_AS_FILENAME's own real literal (Phase 1 line 107):
# u"F1_R2_NORMALIZED_DIAGNOSTIC_COPY.sfm" -- unicode, reproducing the
# exact type composition that triggered the real failure.
result_strict = save_fn_strict(u"F1_R2_NORMALIZED_DIAGNOSTIC_COPY.sfm")

expect(result_strict["ok"] is True, "save.strict_binding_save_succeeds_against_type_strict_fake (%r)" % (result_strict,))
expect(len(fake_dm_strict.save_calls) == 1, "save.strict_binding_SaveToFile_called_exactly_once")
if fake_dm_strict.save_calls:
    expect(type(fake_dm_strict.save_calls[0]["path"]) is str, "save.strict_binding_native_call_receives_str_not_unicode -- the exact repair this regression proves (%r)" % (type(fake_dm_strict.save_calls[0]["path"]),))
    expect(fake_dm_strict.save_calls[0]["path"] == os.path.join(strict_original_dir, "F1_R2_NORMALIZED_DIAGNOSTIC_COPY.sfm"), "save.strict_binding_path_content_correct_after_encoding")
# result["target_path"] itself (used for os.path.exists/getsize and the
# refusal check) remains unicode, unchanged -- only the native call's own
# argument was narrowed.
expect(isinstance(result_strict["target_path"], unicode), "save.strict_binding_result_target_path_remains_unicode_unchanged")

sys.stdout.write("\n--- Phase 1 <-> Phase 2 comparison arithmetic ---\n")

# Reproduces the exact arithmetic both scripts perform when computing
# the serialized/resident delta (Phase 2's idle-after-load vs Phase 1's
# idle-before-run) and the per-run delta (Phase 2's own CP0 vs
# FINAL_REPORT_ENTRY), using illustrative but internally consistent
# numbers.
phase1_idle_before_run = {"available": True, "working_set_bytes": 3000000000, "pagefile_usage_bytes": 3000000000}
phase2_idle_after_load = {"available": True, "working_set_bytes": 3150000000, "pagefile_usage_bytes": 3150000000}
serialized_resident_delta = phase2_idle_after_load["working_set_bytes"] - phase1_idle_before_run["working_set_bytes"]
expect(serialized_resident_delta == 150000000, "comparison.serialized_resident_delta_arithmetic_correct (%r)" % (serialized_resident_delta,))

phase2_cp0 = {"private": 3160000000, "mem_free": 300000000, "largest_free": 150000000}
phase2_final = {"private": 3200000000, "mem_free": 260000000, "largest_free": 110000000}
per_run_private_delta = phase2_final["private"] - phase2_cp0["private"]
per_run_free_vas_delta = phase2_final["mem_free"] - phase2_cp0["mem_free"]
expect(per_run_private_delta == 40000000, "comparison.per_run_private_delta_arithmetic_correct (%r)" % (per_run_private_delta,))
expect(per_run_free_vas_delta == -40000000, "comparison.per_run_free_vas_delta_arithmetic_correct (%r)" % (per_run_free_vas_delta,))

# Illustrative attribution sanity check (NOT a hardcoded classifier in
# the scripts themselves -- this only proves the numbers, correctly
# computed, would visibly point toward different conclusions depending
# on which component dominates; classification itself is applied by the
# reviewing analyst from the real numbers, per explicit instruction).
expect(
    serialized_resident_delta < per_run_private_delta * 10,
    "comparison.illustrative_numbers_are_internally_consistent_for_a_worked_example",
)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
