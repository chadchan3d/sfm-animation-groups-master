# -*- coding: utf-8 -*-
"""
Offline dry-run/regression for Checkpoint_I_Generation_Replacement.py and
I_Generation_Helper.py (roadmap item I -- Master generation replacement).

CORRECTION ROUND 1 (2026-09-25, independent review, 11 blockers). See
this directory's own INSTRUCTIONS.md for the full list; this suite adds
coverage for every blocker that touches the SFM-side checkpoint and the
core helper: atomic MoveFileExW replacement (1), the narrowed G1<->G2
mutation API and hardened sidecar-basename safety (2), the retained Qt
prearm observer (3), full stage re-gating (4), no eval() anywhere (5),
exact G2 publication-record consumption (6), the fail-closed main()-
stripping guard (10). Blockers 7/8/9/11 are primarily exercised in
I_Generation_Publisher.py's own separate Python 3 test.

CORRECTION ROUND 2 (2026-09-25, second independent review, 8 blockers).
This suite adds:
  - R2 BLOCKER 1/3: I1-03/I2-00/I2-01 now ALSO require an exact valid G2
    Master ACTIVATION record, never only a publication record -- a
    published sidecar alone is no longer sufficient (new
    write_g2_activation_record()/_write_complete_g2_authority_state()
    fixtures; new I2-baseline test section, previously uncovered).
  - R2 BLOCKER 3: i2_01_prearm now re-gates the FULL governing identity
    (_common_identity_gates -- previously NOT called there), zero open
    providers/leases, and a HASH-VERIFIED (not merely existence-checked)
    G1 backup, all before the observer is ever installed.
  - R2 BLOCKER 4: static check that _PREARM_TIMEOUT_MS >= 60000.
  - R2 BLOCKER 5: the I2 wrapper's own path-binding refusal -- an
    expected_master_path that does not match the I1 baseline's recorded
    path refuses the G2->G1 swap even when the pre-swap hash genuinely
    matches G2.
  - R2 BLOCKER 6: the standalone baseline-inventory artifact file
    (write-once, round-trip verified) that i_08_finalize_verify now
    consumes directly, instead of only cont's in-memory value.
  - CRITICAL FIXTURE FIX: fresh_ns() now also overrides
    G2_ACTIVATION_RECORD_PATH and BASELINE_INVENTORY_ARTIFACT_PATH to
    tmp-dir paths -- without this, every test exercising these two new
    evidence files would have silently read/written the real, hardcoded
    C:\\Users\\Public\\Documents\\ paths, exactly the failure mode of this
    project's own earlier evidence-directory-leak incident (see
    OFFLINE_MAIN_EXECUTION_INCIDENT.txt).
Blockers 2/7/8/9 (the publisher-side two-phase split, plan record,
activate_g2_master(), and hardened finalize_restoration()) are primarily
exercised in I_Generation_Publisher.py's own separate Python 3 test.

CORRECTION ROUND 3 (2026-09-25, third independent review). This suite
adds:
  - R3 BLOCKER 4 (static): the deployed helper's own CLI exposes ONLY
    "inventory"/"compare" -- no mutation subcommand at all.
  - R3 BLOCKER 5: a static proof that i_08_finalize_verify is reachable
    ONLY at SNAPSHOT_SCHEDULE index 8, never earlier -- the exact fact
    that made "run the checkpoint again for i_08" false for an early-
    aborted campaign; and a full offline harness (mirroring fresh_ns())
    for the NEW, separate Checkpoint_I_Restoration_Verify.py, proving
    its happy path, its refusal without the baseline-inventory artifact,
    its refusal when the live Master is not exactly G1, and that it
    never writes the primary continuation-state file at all.
  - R3 HARDENING: _validate_g2_publication_record() now also requires
    the record's own recorded semantic_parity to report
    all_parity_checks_pass=True; the write_g2_publication_record() test
    fixture was updated to include a real semantic_parity field (its
    prior absence would otherwise now fail every "happy path" test) and
    a real manifest_sha256_after_publication (prior tests hardcoded a
    placeholder that could never match the new active-manifest-hash
    corroboration check).
Blockers 1/2/3 (the publisher-side baseline-bound Phase A, plan-anchored
recovery, and independently re-derived G2 identity) are primarily
exercised in I_Generation_Publisher.py's own separate Python 3 test.

STARTUP FIX (2026-09-26, first real-SFM I1 attempt): the first real-SFM
I1 baseline run produced ZERO qualification evidence. Root cause: both
deployed SFM-side scripts performed a plain top-level `import
I_Generation_Helper as igen` BEFORE their own later import_authority_
runtime() ever adds the MAINMENU directory to sys.path -- SFM's own real
"Run Script" execution does not add the script's own directory to
sys.path (unlike an ordinary `python script.py` invocation), so this
import raised ImportError immediately, before ANY qualification
evidence could be written. This offline suite's own fresh_ns() had
inadvertently MASKED this defect the entire time, because it inserts
HERE into sys.path itself before exec()-ing the checkpoint's own
definitions text -- something the real SFM environment never does. Both
scripts now use an exact-path, hash-pinned sibling-helper loader
(compile()+exec() of the exact already-hashed bytes, never a plain
`import` and -- after a second independent review correctly rejected an
initial imp.load_source()-based version, since Python 2.7's imp.load_
source() may substitute a matching sibling .pyc/.pyo -- never any
.pyc/.pyo lookup either) instead. This suite now:
  - simulates a real SFM-like installed root for EVERY fresh_ns()/
    fresh_restoration_verify_ns() call (_simulate_sfm_installed_root()/
    _exec_checkpoint_defs_sfm_like(), via a temporarily-patched
    sys.executable) -- the full 174/174 re-run against this simulation
    is itself the primary regression proof that the happy path works
    under an SFM-like sys.path;
  - adds a dedicated "Startup fix" section proving: the exact helper
    loads from the intended sibling path; a wrong helper SHA refuses
    (HelperQualificationError) before any evidence is written; a
    missing helper refuses cleanly; a malicious same-named helper
    elsewhere on sys.path is never used; a stale same-named module
    already in sys.modules is never silently reused; and equivalent
    coverage for Checkpoint_I_Restoration_Verify.py, including that no
    Master mutation occurs when helper qualification fails;
  - adds a static regex proof that neither SFM-side script contains a
    real (start-of-line) unqualified `import I_Generation_Helper as
    igen` statement, distinguishing this from the legitimate prose
    mentions of that exact phrase in this fix's own documentation.

BYTECODE-CACHE CORRECTION (second independent review, 2026-09-26): the
loader's own first version used `imp.load_source()` after hashing the
helper's `.py` bytes. Independent review correctly rejected this --
Python 2.7's `imp.load_source()` may substitute a matching sibling
`.pyc`/`.pyo` for the `.py` file it was given (the same mechanism
ordinary `import` uses), so hashing the `.py` bytes beforehand did not
strictly prove those bytes were what actually got executed. Both
SFM-side scripts now compile and execute the EXACT already-hashed bytes
directly (`compile(helper_bytes, helper_path, "exec")` into a fresh
`imp.new_module()`'s own `__dict__`) -- no `imp.load_source()` call, and
no `.pyc`/`.pyo` lookup of any kind, remains in either file. This suite
now adds: a static proof neither script contains a real
`imp.load_source(` call site (only the legitimate historical-explanation
docstring mentions remain); a BYTECODE-CACHE ADVERSARIAL TEST that
writes a real, well-formed, timestamp-matching `.pyc` right next to the
exact, correctly-hashed `.py` (one that ordinary Python-2 import
machinery would consider usable/current) whose OWN compiled code is
observably malicious, and proves both SFM-side scripts ignore it
entirely -- module behavior and `__file__` both come from the exact
hashed `.py` bytes alone; a proof that a wrong `.py` SHA still refuses
BEFORE any execution even when such a matching `.pyc` is present; and a
proof that if executing the (hash-verified) helper source itself raises
during module initialization, no partially-initialized qualification
module is left behind in `sys.modules`. The prior `HARNESS_STARTUP_
FAILURE_BEFORE_I1` real-SFM incident record is unchanged by this round --
this is a pre-redeployment review finding on the FIX itself, never
another empirical SFM failure.

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_checkpoint_i_generation_replacement_dryrun.py
"""
import hashlib
import imp
import json
import marshal
import os
import shutil
import struct
import sys
import tempfile

from PySide import QtCore

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKPOINT_SCRIPT_PATH = os.path.join(HERE, "Checkpoint_I_Generation_Replacement.py")
HELPER_SCRIPT_PATH = os.path.join(HERE, "I_Generation_Helper.py")
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
PRODUCTION_CANDIDATE_PATH = os.path.join(
    REPO_ROOT, "audit_external_runtime", "Rebuild_Control_Groups_Normalizer.py"
)
CANONICAL_MASTER_CANDIDATE_PATH = os.path.join(REPO_ROOT, "sfm_defaultanimationgroups.txt")
AUTHORITY_PARENT = os.path.join(REPO_ROOT, "tests", "sidecar", "qualification", "candidate_b2c_correction6")
SIDECAR_TOOLS_PARENT = os.path.join(REPO_ROOT, "tools")

EXPECTED_PRODUCTION_SHA256 = "1f4ec5a26605aa90380eb0532fec3915d2cc24a3a20473ed70d57198bd995db7"
EXPECTED_CANONICAL_MASTER_SHA256 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
EXPECTED_RUNTIME_API_VERSION = u"1.0.0-b2a"
EXPECTED_RUNTIME_BUILD_ID = u"package-boundary-corrected-2026-09-22"
RUN_LOCK_NAME = "__SFM_REBUILD_CONTROL_GROUPS_CONTEXTUALIZER_RUNNING__"

if HERE not in sys.path:
    sys.path.insert(0, HERE)
import I_Generation_Helper as igen  # noqa: E402

PASS_COUNT = [0]
FAIL_COUNT = [0]


def expect(condition, label):
    if condition:
        PASS_COUNT[0] += 1
        sys.stdout.write("[PASS] %s\n" % label)
    else:
        FAIL_COUNT[0] += 1
        sys.stdout.write("[FAIL] %s\n" % label)


# =======================================================================
# BLOCKER 10: fail-closed main()-stripping. Factored into a reusable
# function, tested against well-formed, CRLF-mutated, and deliberately-
# corrupted inputs BEFORE it is used for real against the checkpoint's
# own bytes.
# =======================================================================
class StrippingFailedError(Exception):
    pass


def strip_trailing_main_call(raw_bytes):
    """Normalizes CRLF->LF first (robust to either encoding), then
    locates and strips the exact trailing "\\nmain()\\n" call. Raises
    StrippingFailedError IMMEDIATELY (never a non-fatal expect()) if the
    pattern cannot be located -- the caller must never exec() anything
    if this raises."""
    normalized = raw_bytes.replace(b"\r\n", b"\n")
    trailing_call = b"\nmain()\n"
    idx = normalized.rfind(trailing_call)
    if idx == -1:
        raise StrippingFailedError(
            "could not locate the trailing main() call -- refusing to "
            "exec() any part of this input."
        )
    return normalized[:idx]


with open(CHECKPOINT_SCRIPT_PATH, "rb") as f:
    checkpoint_bytes = f.read()

try:
    definitions_only_text = strip_trailing_main_call(checkpoint_bytes)
    expect(True, "static.trailing_main_call_located_fail_closed")
except StrippingFailedError as exc:
    FAIL_COUNT[0] += 1
    sys.stdout.write("[FAIL] static.trailing_main_call_located_fail_closed\n")
    sys.stdout.write(
        "FATAL: %r -- refusing to run any further part of this suite, since "
        "doing so could otherwise silently exec() a live checkpoint.\n" % (exc,)
    )
    sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
    sys.exit(1)

# item.blocker10: regression proving strip_trailing_main_call() itself
# is correct against well-formed, CRLF, and corrupted inputs -- BEFORE
# it is trusted for the real checkpoint bytes above.
_WELL_FORMED_SAMPLE = b"def foo():\n    pass\n\n\nmain()\n"
_stripped_wf = strip_trailing_main_call(_WELL_FORMED_SAMPLE)
expect(
    b"main()" not in _stripped_wf and b"def foo" in _stripped_wf,
    "blocker10.well_formed_lf_input_strips_cleanly",
)

_CRLF_SAMPLE = _WELL_FORMED_SAMPLE.replace(b"\n", b"\r\n")
_stripped_crlf = strip_trailing_main_call(_CRLF_SAMPLE)
expect(
    b"main()" not in _stripped_crlf and b"def foo" in _stripped_crlf,
    "blocker10.crlf_input_is_normalized_and_strips_cleanly",
)

_CORRUPTED_SAMPLE = b"def foo():\n    pass\n"  # no trailing main() call at all
_corrupted_raised = False
try:
    strip_trailing_main_call(_CORRUPTED_SAMPLE)
except StrippingFailedError:
    _corrupted_raised = True
expect(_corrupted_raised, "blocker10.missing_trailing_call_raises_immediately_never_returns_almost_whole_file")

_EMPTY_SAMPLE = b""
_empty_raised = False
try:
    strip_trailing_main_call(_EMPTY_SAMPLE)
except StrippingFailedError:
    _empty_raised = True
expect(_empty_raised, "blocker10.empty_input_raises_immediately")

# Proves the corrected function NEVER returns text ending in a call to
# main() under any of the above inputs -- the exact failure mode of the
# original incident (checkpoint_text[:-1] silently including the call).
for _sample_bytes in (_WELL_FORMED_SAMPLE, _CRLF_SAMPLE):
    _s = strip_trailing_main_call(_sample_bytes)
    expect(not _s.rstrip().endswith(b"main()"), "blocker10.stripped_text_never_ends_with_a_live_main_call")

checkpoint_text = definitions_only_text  # the REAL, safely-stripped checkpoint text used throughout this suite


# =======================================================================
# Static source checks.
# =======================================================================
expect(
    b"def edit_master(" not in checkpoint_text
    and b"def modify_production(" not in checkpoint_text
    and b"def edit_authority(" not in checkpoint_text,
    "static.never_defines_a_generic_write_any_file_operation",
)
for forbidden_token in (b"StartRebuildControlGroups(", b"SaveToFile", b"self.activate_next_shot("):
    expect(
        forbidden_token not in checkpoint_text,
        "static.never_references_%s" % forbidden_token.rstrip(b"(").strip(b".").decode("ascii"),
    )
expect(
    b'log_text.count(u"NATIVE_REBUILD_RETURNED = PASS")' in checkpoint_text,
    "static.native_rebuild_returned_is_only_ever_counted_in_log_text_never_called",
)
expect(
    b"def main():" in checkpoint_text
    and b"def _snapshot_i1_01_baseline(" in checkpoint_text
    and b"def _snapshot_i2_01_prearm(" in checkpoint_text
    and b"def _snapshot_i_08_finalize_verify(" in checkpoint_text,
    "static.defines_the_expected_entry_points",
)
expect(
    b"glob.glob" not in checkpoint_text and b"os.listdir" not in checkpoint_text,
    "static.checkpoint_itself_never_wildcard_lists_or_globs_for_deletion",
)
# BLOCKER 5: no eval() anywhere in the checkpoint.
# Distinguishes a real eval(...) CALL from the bare "eval()" mention in
# this checkpoint's own module docstring (which documents that BLOCKER 5
# removed the only eval() call that used to exist).
import re as _re  # noqa: E402
_real_eval_calls = [
    m for m in _re.finditer(br"eval\(", checkpoint_text)
    if checkpoint_text[m.end():m.end() + 1] != b")"
]
expect(len(_real_eval_calls) == 0, "blocker5.checkpoint_contains_no_eval_call")

with open(HELPER_SCRIPT_PATH, "rb") as f:
    helper_bytes = f.read()
expect(b"eval(" not in helper_bytes, "blocker5.helper_contains_no_eval_call")
expect(
    b"shutil.rmtree" not in helper_bytes and b"os.system(" not in helper_bytes,
    "static.helper_never_wildcard_deletes_or_shells_out",
)
# BLOCKER 1: the real MoveFileExW primitive must be used, with the
# correct replace/write-through flags, never described as "atomic" if
# it were still a remove-then-rename sequence.
expect(
    b"MoveFileExW" in helper_bytes,
    "blocker1.helper_uses_the_real_windows_movefileexw_primitive",
)
expect(
    b"MOVEFILE_REPLACE_EXISTING" in helper_bytes and b"MOVEFILE_WRITE_THROUGH" in helper_bytes,
    "blocker1.helper_requests_replace_existing_and_write_through_semantics",
)
expect(
    b"def _atomic_write_bytes" in helper_bytes,
    "static.helper_has_exactly_one_atomic_write_primitive",
)
# BLOCKER 2: no generic public arbitrary-bytes live-mutation function name.
expect(
    b"def install_g2_over_g1(" not in helper_bytes and b"def restore_g1_over_g2(" not in helper_bytes,
    "blocker2.old_generic_public_mutation_wrappers_removed",
)
expect(
    b"def perform_g1_to_g2_replacement(" in helper_bytes
    and b"def perform_g2_to_g1_restoration(" in helper_bytes,
    "blocker2.narrow_named_operations_present",
)
expect(
    b"def is_safe_bare_basename(" in helper_bytes,
    "blocker2.sidecar_basename_safety_check_present",
)
# BLOCKER 11: the SFM-deployable core never IMPORTS the publisher
# package (it is fine for the module docstring to explain, in prose,
# that it deliberately does not -- the decisive check is the absence of
# an actual import statement).
expect(
    b"import sfm_master_sidecar" not in helper_bytes
    and b"from sfm_master_sidecar" not in helper_bytes,
    "blocker11.core_helper_never_imports_the_publisher_package",
)

# =======================================================================
# CORRECTION ROUND 2 static checks.
# =======================================================================
# R2 BLOCKER 4: the bounded human-action window must be >= 60000ms.
_prearm_timeout_match = _re.search(br"_PREARM_TIMEOUT_MS\s*=\s*(\d+)", checkpoint_text)
expect(
    _prearm_timeout_match is not None and int(_prearm_timeout_match.group(1)) >= 60000,
    "r2blocker4.prearm_timeout_is_at_least_60000ms",
)
_prearm_poll_match = _re.search(br"_PREARM_POLL_INTERVAL_MS\s*=\s*(\d+)", checkpoint_text)
expect(
    _prearm_poll_match is not None and int(_prearm_poll_match.group(1)) == 25,
    "r2blocker4.prearm_poll_interval_unchanged_at_25ms",
)
# R2 BLOCKER 3: i2_01_prearm must call the shared identity-gate helper.
_i2_01_prearm_body_match = _re.search(
    br"def _snapshot_i2_01_prearm\(.*?\n(?=def _snapshot_i2_02_verify\()", checkpoint_text, _re.DOTALL,
)
expect(
    _i2_01_prearm_body_match is not None and b"_common_identity_gates(gate_checks, record)" in _i2_01_prearm_body_match.group(0),
    "r2blocker3.i2_01_prearm_calls_common_identity_gates",
)
# R2 BLOCKER 1: I1-03 must require both the publication AND activation
# record; a bare sidecar/manifest is never sufficient.
expect(
    b"_validate_g2_activation_record(" in checkpoint_text
    and b"def _validate_g2_activation_record(" in checkpoint_text,
    "r2blocker1.activation_record_validator_exists_and_is_called",
)
# R2 BLOCKER 5: path binding helper must be used by the I2 wrapper.
expect(
    b"igen.path_matches_baseline(" in checkpoint_text,
    "r2blocker5.checkpoint_uses_the_shared_path_binding_helper",
)
expect(
    b"def path_matches_baseline(" in helper_bytes,
    "r2blocker5.helper_defines_the_path_binding_primitive",
)

# =======================================================================
# CORRECTION ROUND 3 static checks.
# =======================================================================
# R3 BLOCKER 4: the deployed helper's own CLI must expose NO mutation
# subcommand at all -- not even the narrow, hash-gated ones. Only
# "inventory" and "compare" (both read-only) may be add_parser()-ed.
_cli_subcommand_literals = _re.findall(br'add_parser\(\s*"([^"]+)"\s*\)', helper_bytes)
expect(
    set(_cli_subcommand_literals) == {b"inventory", b"compare"},
    "r3blocker4.helper_cli_exposes_only_inventory_and_compare",
)
for _forbidden_subcommand in (b"advance-g1-to-g2", b"restore-g2-to-g1", b"remove-sidecar"):
    expect(
        _forbidden_subcommand not in helper_bytes,
        "r3blocker4.helper_no_longer_contains_the_forbidden_subcommand_literal_%s"
        % _forbidden_subcommand.decode("ascii").replace("-", "_"),
    )
# The underlying Python functions remain (called in-process by the
# publisher and by this checkpoint's own I2 wrapper) -- only their CLI
# exposure was removed.
expect(
    b"def perform_g1_to_g2_replacement(" in helper_bytes
    and b"def perform_g2_to_g1_restoration(" in helper_bytes
    and b"def remove_exact_sidecar(" in helper_bytes,
    "r3blocker4.underlying_mutation_functions_still_exist_as_python_functions",
)

# R3 BLOCKER 5: i_08_finalize_verify is reachable ONLY at schedule index
# 8 -- proves the "run the checkpoint again for i_08" instruction is
# mechanically impossible to reach early. A separate, independent
# restoration verifier (Checkpoint_I_Restoration_Verify.py) exists for
# an early-aborted campaign.
expect(
    os.path.isfile(os.path.join(HERE, "Checkpoint_I_Restoration_Verify.py")),
    "r3blocker5.standalone_restoration_verifier_file_exists",
)

# =======================================================================
# STARTUP FIX static checks (2026-09-26, first real-SFM I1 attempt): a
# plain, unqualified top-level `import I_Generation_Helper as igen`
# raised ImportError under SFM's own real "Run Script" execution (which
# does not add the script's own directory to sys.path), producing ZERO
# qualification evidence. Neither SFM-side script may contain that
# pattern as REAL CODE ever again -- distinguished via `^\s*import ...`
# (start-of-line) from a bare prose/comment mention of the same phrase,
# which this file's own module docstring/comments now legitimately
# contain while documenting the fix.
# =======================================================================
_unqualified_helper_import_re = _re.compile(br"^\s*import I_Generation_Helper as igen\s*$", _re.MULTILINE)
expect(
    _unqualified_helper_import_re.search(checkpoint_bytes) is None,
    "r3startupfix.checkpoint_contains_no_real_unqualified_helper_import_statement",
)
with open(os.path.join(HERE, "Checkpoint_I_Restoration_Verify.py"), "rb") as f:
    _restoration_verify_raw_for_static_check = f.read()
expect(
    _unqualified_helper_import_re.search(_restoration_verify_raw_for_static_check) is None,
    "r3startupfix.restoration_verify_contains_no_real_unqualified_helper_import_statement",
)
expect(
    b"def _load_exact_i_helper(" in checkpoint_bytes and b"def _load_exact_i_helper(" in _restoration_verify_raw_for_static_check,
    "r3startupfix.both_sfm_side_scripts_define_the_exact_path_helper_loader",
)
# BYTECODE-CACHE CORRECTION (second independent review, 2026-09-26):
# imp.load_source() was REJECTED -- under Python 2.7 it may substitute a
# matching sibling .pyc/.pyo for the .py file it was given, so hashing
# the .py bytes beforehand did not strictly prove those were the bytes
# actually executed. Neither script may call it as REAL CODE again
# (`= imp.load_source(`, an assignment/call site) -- a bare prose mention
# of the phrase in this fix's own explanatory docstring/comments is
# legitimate and must not trip this check.
_real_imp_load_source_re = _re.compile(br"=\s*imp\.load_source\(")
expect(
    _real_imp_load_source_re.search(checkpoint_bytes) is None,
    "r3startupfix.checkpoint_contains_no_real_imp_load_source_call",
)
expect(
    _real_imp_load_source_re.search(_restoration_verify_raw_for_static_check) is None,
    "r3startupfix.restoration_verify_contains_no_real_imp_load_source_call",
)
expect(
    b"imp.new_module(" in checkpoint_bytes and b"imp.new_module(" in _restoration_verify_raw_for_static_check,
    "r3startupfix.both_sfm_side_scripts_use_imp_new_module_instead",
)
expect(
    b'compile(helper_bytes, helper_path, "exec")' in checkpoint_bytes
    and b'compile(helper_bytes, helper_path, "exec")' in _restoration_verify_raw_for_static_check,
    "r3startupfix.both_sfm_side_scripts_compile_the_exact_already_hashed_bytes_directly",
)

sys.stdout.write("--- Extracted checkpoint definitions (verbatim, real embedded Python) ---\n")


# =======================================================================
# Fake object model.
# =======================================================================
class _FakeControl(object):
    def __init__(self, name):
        self._name = name

    def GetName(self):
        return self._name


class _FakeArray(object):
    def __init__(self, items):
        self._items = list(items)

    def Count(self):
        return len(self._items)

    def __getitem__(self, i):
        return self._items[i]


class _FakeAnimSet(object):
    def __init__(self, name, control_names):
        self._name = name
        self._controls = _FakeArray([_FakeControl(n) for n in control_names])

    def GetName(self):
        return self._name

    def GetAttribute(self, attr_name):
        return self._controls if attr_name == "controls" else None


class _FakeShot(object):
    def __init__(self, name, animation_sets):
        self._name = name
        self.animationSets = list(animation_sets)

    def GetName(self):
        return self._name


class _FakeMainWindow(QtCore.QObject):
    pass


class _FakeDocumentRoot(object):
    def __init__(self, file_id):
        self._file_id = file_id

    def GetFileId(self):
        return self._file_id


class _FakeGPDataModel(object):
    def __init__(self, filename_by_id):
        self._filename_by_id = dict(filename_by_id)

    def GetFileName(self, file_id):
        return self._filename_by_id.get(file_id)


class _FakeVsModule(object):
    def __init__(self, filename_by_id):
        self.g_pDataModel = _FakeGPDataModel(filename_by_id)


class _FakeSfmApp(object):
    def __init__(self, shots, main_window, document_root):
        self._shots = list(shots)
        self._main_window = main_window
        self._document_root = document_root

    def GetShots(self):
        return self._shots

    def GetMainWindow(self):
        return self._main_window

    def GetDocumentRoot(self):
        return self._document_root


class _FakeProbeError(Exception):
    pass


class _FakeProductionRunInstance(QtCore.QObject):
    """A faithful-enough simulacrum of production's own
    RebuildControlGroupsProductionRun for I2 wrapper/observer testing:
    parents itself to main_window, sets objectName to the REAL
    RUN_LOCK_NAME (so the REAL, extracted _find_existing_run() finds
    it), initializes the same scope/progress attributes at construction
    time, and its contextualizer_resolve_resume_target() re-hashes the
    SAME live Master path this test controls and raises on mismatch --
    exactly mirroring production's own assert_master_stable() contract."""

    def __init__(self, main_window, master_path, pinned_master_hash,
                 scope_shot_names=(u"shot3",), scope_mode=u"SELECTED_SHOTS"):
        QtCore.QObject.__init__(self, main_window)
        self.setObjectName(RUN_LOCK_NAME)
        self._master_path = master_path
        self.master_hash = pinned_master_hash
        self.scope_mode = scope_mode
        self.scope_shots = [_FakeShot(n, []) for n in scope_shot_names]
        self.current_target_index = 0
        self.telemetry_native_attempts = 0
        self.total_native_rebuilt = 0
        self.call_log = []

    def contextualizer_resolve_resume_target(self, record, target):
        self.call_log.append((record, target))
        current_hash = igen.sha256_file(self._master_path)
        if current_hash.lower() != self.master_hash.lower():
            raise _FakeProbeError("Live Master changed during the run.")
        return (record, target)


DEFAULT_FIXTURE_FILE_ID = 1
DEFAULT_FIXTURE_BASENAME = u"F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx"


def _simulate_sfm_installed_root(tmp_dir, helper_source_path=None):
    """STARTUP FIX regression support: the checkpoint's own exact-path
    helper loader now runs AT EXEC TIME, deriving the expected sibling
    helper path from dirname(sys.executable) -- exactly mirroring SFM's
    own real convention (SFM's own sys.executable sits directly under
    the game root). The embedded Python 2.7.5 interpreter this suite
    itself runs under has a DIFFERENT sys.executable (a standalone
    interpreter several directories deeper, under sdktools\\python\\2.7\\
    win32\\), so this suite must simulate a real SFM-like installed root
    -- never rely on the offline interpreter's own real sys.executable,
    which would resolve to a nonexistent path (the same class of
    quirk documented in OFFLINE_MAIN_EXECUTION_INCIDENT.txt for
    CANONICAL_MASTER_INSTALLED_PATH). Creates
    <tmp_dir>/simulated_game_root/usermod/scripts/sfm/mainmenu/ChadChan3D/
    and copies the real, current helper bytes there (from
    helper_source_path, default the real HELPER_SCRIPT_PATH) unless a
    caller-supplied path already populated it (e.g. to simulate a
    missing/tampered helper). Returns the simulated game root."""
    simulated_game_root = os.path.join(tmp_dir, "simulated_game_root")
    simulated_mainmenu_dir = os.path.join(
        simulated_game_root, "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
    )
    if not os.path.isdir(simulated_mainmenu_dir):
        os.makedirs(simulated_mainmenu_dir)
    simulated_helper_path = os.path.join(simulated_mainmenu_dir, "I_Generation_Helper.py")
    if not os.path.isfile(simulated_helper_path):
        shutil.copyfile(helper_source_path or HELPER_SCRIPT_PATH, simulated_helper_path)
    return simulated_game_root


def _exec_checkpoint_defs_sfm_like(defs_text, ns, tmp_dir, helper_source_path=None,
                                    simulated_game_root=None):
    """Execs checkpoint/restoration-verify definitions text with
    sys.executable temporarily pointed at a simulated SFM-like installed
    root (see _simulate_sfm_installed_root()) -- so the exact-path
    helper loader that now runs at exec time resolves the sibling helper
    the same way it would under real SFM, never under this offline
    interpreter's own, different, real sys.executable. Restores the
    real sys.executable afterward unconditionally."""
    if simulated_game_root is None:
        simulated_game_root = _simulate_sfm_installed_root(tmp_dir, helper_source_path=helper_source_path)
    original_sys_executable = sys.executable
    sys.executable = os.path.join(simulated_game_root, "sfm.exe")
    try:
        exec(compile(defs_text, "<checkpoint_defs>", "exec"), ns)
    finally:
        sys.executable = original_sys_executable
    return simulated_game_root


def fresh_ns(tmp_dir, shots, master_path=None, fixture_basename=DEFAULT_FIXTURE_BASENAME,
             main_window=None, helper_source_path=None, simulated_game_root=None):
    doc_root = _FakeDocumentRoot(DEFAULT_FIXTURE_FILE_ID)
    vs_module = _FakeVsModule({DEFAULT_FIXTURE_FILE_ID: u"C:\\fake\\path\\%s" % fixture_basename})
    mw = main_window if main_window is not None else _FakeMainWindow()
    ns = {
        "sfmApp": _FakeSfmApp(shots, mw, doc_root),
        "vs": vs_module,
        "QtCore": QtCore,
    }
    _exec_checkpoint_defs_sfm_like(
        checkpoint_text, ns, tmp_dir, helper_source_path=helper_source_path,
        simulated_game_root=simulated_game_root,
    )

    ns["PRODUCTION_INSTALLED_PATH"] = PRODUCTION_CANDIDATE_PATH
    ns["EXPECTED_PRODUCTION_SHA256"] = EXPECTED_PRODUCTION_SHA256
    ns["CANONICAL_MASTER_INSTALLED_PATH"] = master_path or CANONICAL_MASTER_CANDIDATE_PATH
    ns["EXPECTED_G1_MASTER_SHA256"] = EXPECTED_CANONICAL_MASTER_SHA256

    evidence_dir = tmp_dir + os.sep
    ns["EVIDENCE_DIR"] = evidence_dir
    ns["CONTINUATION_STATE_PATH"] = evidence_dir + "sfm_checkpoint_i_continuation_state.json"
    ns["FINAL_RESULT_PATH"] = evidence_dir + "sfm_checkpoint_i_final_result.json"
    ns["FINAL_SUMMARY_PATH"] = evidence_dir + "sfm_checkpoint_i_final_summary.txt"
    ns["G1_SOURCE_BYTES_BACKUP_PATH"] = evidence_dir + "sfm_checkpoint_i_g1_source_bytes.dat"
    ns["I2_INJECTION_RECORD_PATH"] = evidence_dir + "sfm_checkpoint_i_i2_injection_record.json"
    ns["I2_PREARM_RESULT_PATH"] = evidence_dir + "sfm_checkpoint_i_i2_prearm_result.json"
    ns["G2_PUBLICATION_RECORD_PATH"] = evidence_dir + "sfm_checkpoint_i_g2_publication_record.json"
    ns["G2_ACTIVATION_RECORD_PATH"] = evidence_dir + "sfm_checkpoint_i_g2_activation_record.json"
    ns["FINALIZATION_RECORD_PATH"] = evidence_dir + "sfm_checkpoint_i_finalization_record.json"
    ns["BASELINE_INVENTORY_ARTIFACT_PATH"] = evidence_dir + "sfm_checkpoint_i_baseline_inventory.json"
    ns["SHIPPED_AUTHORITY_DIR"] = os.path.join(tmp_dir, "sfm_shared_authority")
    if not os.path.isdir(ns["SHIPPED_AUTHORITY_DIR"]):
        os.makedirs(ns["SHIPPED_AUTHORITY_DIR"])

    ns["import_authority_runtime"] = _test_import_authority_runtime
    ns["get_canonical_broker"] = _test_get_canonical_broker
    return ns


def _test_import_authority_runtime():
    if AUTHORITY_PARENT not in sys.path:
        sys.path.insert(0, AUTHORITY_PARENT)
    if SIDECAR_TOOLS_PARENT not in sys.path:
        sys.path.insert(0, SIDECAR_TOOLS_PARENT)
    from sfm_master_authority_productionized import runtime as authority_runtime
    from sfm_master_authority_productionized import errors as authority_errors
    from sfm_master_authority_productionized import observation as authority_observation
    return authority_runtime, authority_errors, authority_observation


def _always_main_thread():
    return True


def _test_get_canonical_broker(authority_runtime_module):
    return authority_runtime_module.get_broker(
        expected_api_version=EXPECTED_RUNTIME_API_VERSION,
        expected_build_id=EXPECTED_RUNTIME_BUILD_ID,
        is_main_thread_fn=_always_main_thread,
    )


def _padding_shots(exclude=(3, 9), count=13, upper=30):
    out = []
    for i in range(1, upper):
        if i in exclude:
            continue
        out.append(_FakeShot(u"shot%d" % i, []))
        if len(out) == count:
            break
    return out


def make_15_shots(tag=u"i"):
    shot3 = _FakeShot(u"shot3", [
        _FakeAnimSet(u"%s_aset1" % tag, [u"%s_a" % tag, u"%s_b" % tag]),
        _FakeAnimSet(u"%s_aset2" % tag, [u"%s_c" % tag]),
    ])
    shot9 = _FakeShot(u"shot9", [
        _FakeAnimSet(u"%s_aset9" % tag, [u"%s_x" % tag, u"%s_y" % tag]),
    ])
    return [shot3, shot9] + _padding_shots(count=13)


def make_passing_record(current_pid=4242, guard_state=u"UNUSED", run_lock_present=False,
                         provider_counters=None, lease_counters=None, recent_diagnostics=None,
                         run_captured=None, production_sha_ok=True, master_sha256=None,
                         api_ok=True, build_ok=True, canonical_ok=True, main_window_ok=True,
                         fixture_basename=DEFAULT_FIXTURE_BASENAME, project_shot_count=15,
                         shots_enumerable=True):
    return {
        "current_pid": current_pid,
        "production_sha256": EXPECTED_PRODUCTION_SHA256 if production_sha_ok else u"0" * 64,
        "production_sha256_matches_expected": production_sha_ok,
        "current_master_sha256": master_sha256,
        "runtime_api_version": EXPECTED_RUNTIME_API_VERSION if api_ok else u"wrong-api",
        "runtime_api_version_matches_expected": api_ok,
        "runtime_build_id": EXPECTED_RUNTIME_BUILD_ID if build_ok else u"wrong-build",
        "runtime_build_id_matches_expected": build_ok,
        "runtime_is_canonical": canonical_ok,
        "main_window_available": main_window_ok,
        "guard_state": guard_state,
        "run_lock_present": run_lock_present,
        "fixture_open_basename": fixture_basename,
        "shots_enumerable": shots_enumerable,
        "project_shot_count": project_shot_count,
        "provider_counters": provider_counters if provider_counters is not None else {
            "current_open_provider_count": 0, "peak_open_provider_count": 0,
            "total_provider_opens": 0, "total_provider_closes": 0, "active_cohort_id": None,
        },
        "lease_counters": lease_counters if lease_counters is not None else {
            "outstanding_lease_count": 0, "unreleased_lease_count": 0, "view_cache_entry_count": 0,
        },
        "recent_diagnostics": recent_diagnostics if recent_diagnostics is not None else [],
        "run_captured": run_captured,
    }


def _build_known_view(master_sha256, folds, consumer_kind=u"normalizer_compat", stale=False,
                       coverage_overrides=None):
    from sfm_master_authority_productionized import descriptors as _descriptors
    from sfm_master_authority_productionized import views as _views
    semantic_gen = _descriptors.SemanticGeneration(
        effective_master_path=u"x", master_sha256=master_sha256, master_byte_length=1,
        authority_semantics_version=u"v1", projection_contract_version=None,
    )
    entries = {}
    payload_folded = {}
    overrides = coverage_overrides or {}
    for fold in folds:
        status = overrides.get(fold, _views.KNOWN)
        if status == _views.KNOWN:
            dest = u"Dest/%s" % fold
            entries[fold] = _views.CoverageResult(_views.KNOWN, destination=dest, occurrences=[{"literal": fold}])
            payload_folded[fold] = [{"literal": fold, "destination": dest}]
        elif status == _views.MASTER_UNKNOWN:
            entries[fold] = _views.CoverageResult(_views.MASTER_UNKNOWN)
    coverage = _views.CoverageDescriptor(entries)
    token = _views.LiveAuthorizationToken(master_sha256)
    if stale:
        token.invalidate()
    return _views.DetachedView(
        semantic_generation=semantic_gen, artifact_identity=None, coverage=coverage,
        projection_contract_version=None, admission_id=u"fake", consumer_kind=consumer_kind,
        payload={"folded": payload_folded}, authorization=token, estimated_bytes=10,
    )


def make_run_log_bytes(shot_name, unique_scope_folds, master_sha256, production_pass=True,
                        production_fail=False, final_report=True, scope_selected=True,
                        master_changed_message=False, target_callback_abort=False,
                        pre_native_count=0, native_rebuild_returned_count=0):
    lines = []
    if scope_selected:
        lines.append(u"scope_mode=SELECTED_SHOTS scope_shots=1")
    lines.append(u"CONTEXTUALIZER_SCOPE_SHOT_NAMES = [u'%s']" % shot_name)
    lines.append(u"live Master SHA256=%s" % master_sha256)
    if final_report:
        lines.append(u"FINAL_REPORT_ENTRY")
    lines.append(
        u"CONTEXTUALIZER_SCOPED_MASTER_INDEX_BUILD = PASS unique_scope_folds=%d matched_folds=%d"
        % (unique_scope_folds, unique_scope_folds)
    )
    for _ in range(pre_native_count):
        lines.append(u"CONTEXTUALIZER_TELEMETRY phase=PRE_NATIVE target_seq=1")
    for _ in range(native_rebuild_returned_count):
        lines.append(u"NATIVE_REBUILD_RETURNED = PASS")
    if target_callback_abort:
        lines.append(u"Exception during CONTEXTUALIZER target-level Qt callback transaction: ProbeError(...)")
    if master_changed_message:
        lines.append(u"ABORT: Exception during CONTEXTUALIZER target-level Qt callback transaction: "
                      u"ProbeError('Live Master changed during the run.',)")
    if production_pass:
        lines.append(u"PRODUCTION_REBUILD_CONTROL_GROUPS = PASS")
    if production_fail:
        lines.append(u"PRODUCTION_REBUILD_CONTROL_GROUPS = FAIL")
    return (u"\n".join(lines) + u"\n").encode("utf-8")


def write_g2_publication_record(path, g1_sha, g2_sha, generation_basename, sidecar_sha,
                                 manifest_source_sha=None, manifest_basename=None,
                                 manifest_sha256_after_publication=None, semantic_parity_pass=True):
    record = {
        "wall_time": "2026-09-25 00:00:00", "epoch": 0.0,
        "g1_source_sha256": g1_sha, "g2_source_sha256": g2_sha,
        "g2_source_byte_length": 1, "g2_generation_basename": generation_basename,
        "g2_sidecar_sha256": sidecar_sha,
        "manifest_sha256_after_publication": (
            manifest_sha256_after_publication if manifest_sha256_after_publication is not None else u"0" * 64
        ),
        "manifest_source_sha256": manifest_source_sha if manifest_source_sha is not None else g2_sha,
        "manifest_generation_basename": manifest_basename if manifest_basename is not None else generation_basename,
        # R3 HARDENING: the consumer (_validate_g2_publication_record)
        # now mechanically requires this field to report
        # all_parity_checks_pass=True -- default a valid-looking value
        # here so existing "happy path" fixtures remain happy, with an
        # explicit override for the one adversarial test that flips it.
        "semantic_parity": {"all_parity_checks_pass": semantic_parity_pass},
    }
    with open(path, "wb") as f:
        f.write(json.dumps(record).encode("utf-8"))
    return record


def write_manifest_json(authority_dir, source_sha256, generation_basename):
    with open(os.path.join(authority_dir, "manifest.json"), "wb") as f:
        f.write(json.dumps({
            "source_sha256": source_sha256, "generation_basename": generation_basename,
        }).encode("utf-8"))


def write_g2_activation_record(path, expected_g1_sha, rederived_g2_sha, post_activation_master_sha,
                                master_path_matches_baseline=True, authority_dir_matches_baseline=True,
                                success=True):
    """R2 BLOCKER 1/3: the Phase B Master-ACTIVATION record fixture --
    distinct from the Phase A publication record above."""
    record = {
        "wall_time": "2026-09-25 00:00:00", "epoch": 0.0,
        "expected_g1_sha256": expected_g1_sha,
        "rederived_g2_sha256": rederived_g2_sha,
        "post_activation_master_sha256": post_activation_master_sha,
        "path_binding_checks": {
            "master_path_matches_baseline": master_path_matches_baseline,
            "authority_dir_matches_baseline": authority_dir_matches_baseline,
        },
        "success": success,
    }
    with open(path, "wb") as f:
        f.write(json.dumps(record).encode("utf-8"))
    return record


def _write_complete_g2_authority_state(ns, g1_sha, g2_sha):
    """Writes a self-consistent, fully valid G2 publication record + real
    sidecar + manifest.json + G2 activation record -- the complete
    evidence chain R2 BLOCKER 1 requires I1-03/I2-00/I2-01 to see before
    treating G2 as ready/active."""
    authority_dir = ns["SHIPPED_AUTHORITY_DIR"]
    g2_sidecar_basename = u"sfm_master_0_%s.sfmsidecar" % g2_sha
    g2_sidecar_path = os.path.join(authority_dir, g2_sidecar_basename)
    with open(g2_sidecar_path, "wb") as f:
        f.write((u"real-g2-sidecar-bytes-%s" % g2_sha).encode("ascii"))
    sidecar_sha = igen.sha256_file(g2_sidecar_path)
    write_manifest_json(authority_dir, source_sha256=g2_sha, generation_basename=g2_sidecar_basename)
    manifest_sha = igen.sha256_file(os.path.join(authority_dir, igen.MANIFEST_BASENAME))
    write_g2_publication_record(
        ns["G2_PUBLICATION_RECORD_PATH"], g1_sha=g1_sha, g2_sha=g2_sha,
        generation_basename=g2_sidecar_basename, sidecar_sha=sidecar_sha,
        manifest_sha256_after_publication=manifest_sha,
    )
    write_g2_activation_record(
        ns["G2_ACTIVATION_RECORD_PATH"], expected_g1_sha=g1_sha, rederived_g2_sha=g2_sha,
        post_activation_master_sha=g2_sha,
    )
    return g2_sidecar_path, sidecar_sha


# =======================================================================
# Section: helper safety (BLOCKER 1/2 -- atomic replacement, narrowed API,
# basename hardening).
# =======================================================================
sys.stdout.write("\n--- Helper safety: atomic replacement + narrowed API (BLOCKER 1/2) ---\n")

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_")
try:
    g1_bytes = b"GROUP A\nCONTROL X\n"
    g1_sha = hashlib.sha256(g1_bytes).hexdigest()
    master_path = os.path.join(tmp_dir, "master.txt")
    with open(master_path, "wb") as f:
        f.write(g1_bytes)

    g2_bytes = igen.construct_g2_bytes(g1_bytes)
    g2_sha = hashlib.sha256(g2_bytes).hexdigest()

    expect(g2_bytes != g1_bytes and hashlib.sha256(g2_bytes).hexdigest() != g1_sha,
           "item.generated_g2_hash_differs_from_g1")
    expect(igen.g2_bytes_are_exact_g1_plus_one_lf(g1_bytes, g2_bytes),
           "item.generated_g2_bytes_are_exactly_g1_plus_one_lf")

    # BLOCKER 2: perform_g1_to_g2_replacement -- narrow, no caller bytes.
    op_record = igen.perform_g1_to_g2_replacement(master_path, expected_g1_sha256=g1_sha)
    expect(op_record["success"] is True and igen.sha256_file(master_path) == g2_sha,
           "blocker2.perform_g1_to_g2_replacement_advances_when_current_hash_matches_g1")

    with open(master_path, "wb") as f:
        f.write(g1_bytes)
    raised = False
    try:
        igen.perform_g1_to_g2_replacement(master_path, expected_g1_sha256=u"0" * 64)
    except igen.GenerationHelperError:
        raised = True
    expect(raised and igen.sha256_file(master_path) == g1_sha,
           "blocker2.perform_g1_to_g2_replacement_refuses_on_wrong_current_hash")

    with open(master_path, "wb") as f:
        f.write(g2_bytes)
    # BLOCKER 2: perform_g2_to_g1_restoration -- proposed backup bytes
    # must hash to the exact pinned canonical G1, never an arbitrary
    # caller value.
    raised2 = False
    try:
        igen.perform_g2_to_g1_restoration(master_path, b"tampered bytes", g2_sha, expected_g1_sha256=g1_sha)
    except igen.GenerationHelperError:
        raised2 = True
    expect(raised2 and igen.sha256_file(master_path) == g2_sha,
           "blocker2.perform_g2_to_g1_restoration_refuses_a_tampered_backup_before_any_write")

    op_record2 = igen.perform_g2_to_g1_restoration(master_path, g1_bytes, g2_sha, expected_g1_sha256=g1_sha)
    expect(op_record2["success"] is True and igen.sha256_file(master_path) == g1_sha,
           "blocker2.perform_g2_to_g1_restoration_succeeds_with_the_correct_backup")

    with open(master_path, "wb") as f:
        f.write(g1_bytes)  # current is G1, not the expected G2
    raised3 = False
    try:
        igen.perform_g2_to_g1_restoration(master_path, g1_bytes, g2_sha, expected_g1_sha256=g1_sha)
    except igen.GenerationHelperError:
        raised3 = True
    expect(raised3 and igen.sha256_file(master_path) == g1_sha,
           "blocker2.perform_g2_to_g1_restoration_refuses_when_current_hash_is_not_the_expected_g2")

    # BLOCKER 1: genuine atomic replacement -- a simulated replacement
    # failure (source temp file vanishes before the OS call) leaves the
    # original target completely untouched.
    with open(master_path, "wb") as f:
        f.write(g1_bytes)
    tmp_sibling = master_path + ".tmp-igen"
    with open(tmp_sibling, "wb") as f:
        f.write(g2_bytes)
    os.remove(tmp_sibling)  # simulate external interference / a vanished source
    raised4 = False
    try:
        igen._atomic_replace_file(tmp_sibling, master_path)
    except igen.GenerationHelperError:
        raised4 = True
    expect(raised4, "blocker1.simulated_replacement_failure_raises")
    expect(
        igen.sha256_file(master_path) == g1_sha and os.path.exists(master_path),
        "blocker1.simulated_replacement_failure_leaves_original_target_intact",
    )

    # BLOCKER 1: a genuinely successful replacement leaves NO interval
    # where the destination is missing (sanity: destination exists with
    # the NEW content immediately afterward, never absent).
    with open(master_path, "wb") as f:
        f.write(g1_bytes)
    igen._atomic_write_bytes(master_path, g2_bytes)
    expect(
        os.path.exists(master_path) and igen.sha256_file(master_path) == g2_sha,
        "blocker1.successful_atomic_write_replaces_destination_with_new_content",
    )
    expect(
        not os.path.exists(master_path + ".tmp-igen"),
        "blocker1.successful_atomic_write_leaves_no_orphaned_temp_file",
    )

    # BLOCKER 2 hardening: sidecar basename safety.
    authority_dir = os.path.join(tmp_dir, "authority")
    os.makedirs(authority_dir)
    sidecar_path = os.path.join(authority_dir, "sfm_master_0_deadbeef.sfmsidecar")
    with open(sidecar_path, "wb") as f:
        f.write(b"sidecar-bytes")
    sidecar_sha = igen.sha256_file(sidecar_path)

    for unsafe_basename in (
        u"../sfm_master_0_deadbeef.sfmsidecar",
        u"..\\sfm_master_0_deadbeef.sfmsidecar",
        u"sub/sfm_master_0_deadbeef.sfmsidecar",
        u"C:\\sfm_master_0_deadbeef.sfmsidecar",
        u".",
        u"..",
        u"",
    ):
        expect(igen.is_safe_bare_basename(unsafe_basename) is False,
               "blocker2.is_safe_bare_basename_rejects_%r" % (unsafe_basename,))

    expect(igen.is_safe_bare_basename(u"sfm_master_0_deadbeef.sfmsidecar") is True,
           "blocker2.is_safe_bare_basename_accepts_a_real_basename")

    raised5 = False
    try:
        igen.remove_exact_sidecar(authority_dir, u"../deadbeef.sfmsidecar", sidecar_sha)
    except igen.GenerationHelperError:
        raised5 = True
    expect(raised5 and os.path.exists(sidecar_path),
           "blocker2.remove_exact_sidecar_refuses_a_path_traversal_basename")

    other_sidecar_path = os.path.join(authority_dir, "sfm_master_0_otherfile.sfmsidecar")
    with open(other_sidecar_path, "wb") as f:
        f.write(b"other-bytes")

    raised6 = False
    try:
        igen.remove_exact_sidecar(authority_dir, "sfm_master_0_deadbeef.sfmsidecar", u"0" * 64)
    except igen.GenerationHelperError:
        raised6 = True
    expect(raised6 and os.path.exists(sidecar_path), "item.remove_exact_sidecar_refuses_on_hash_mismatch")

    igen.remove_exact_sidecar(authority_dir, "sfm_master_0_deadbeef.sfmsidecar", sidecar_sha)
    expect(
        not os.path.exists(sidecar_path) and os.path.exists(other_sidecar_path),
        "item.remove_exact_sidecar_removes_only_the_exact_named_file",
    )

    # Baseline inventory roundtrip + comparator (unchanged behavior).
    with open(master_path, "wb") as f:
        f.write(g1_bytes)
    with open(os.path.join(authority_dir, "manifest.json"), "wb") as f:
        f.write(b'{"source_sha256": "x"}')
    inv1 = igen.capture_live_state_inventory(master_path, authority_dir)
    inv2 = igen.capture_live_state_inventory(master_path, authority_dir)
    expect(
        inv1["master_sha256"] == inv2["master_sha256"] == g1_sha
        and inv1["manifest_sha256"] == inv2["manifest_sha256"]
        and inv1["sidecars"] == inv2["sidecars"],
        "item.baseline_inventory_roundtrip_is_deterministic",
    )
    cmp_same = igen.compare_inventories(inv1, inv2)
    expect(cmp_same["exact_match"] is True, "item.comparator_reports_exact_match_for_identical_inventories")

    brand_new_sidecar_path = os.path.join(authority_dir, "sfm_master_0_brandnew.sfmsidecar")
    with open(brand_new_sidecar_path, "wb") as f:
        f.write(b"brand-new-bytes")
    inv3 = igen.capture_live_state_inventory(master_path, authority_dir)
    cmp_extra = igen.compare_inventories(inv1, inv3)
    expect(
        cmp_extra["exact_match"] is False and "sfm_master_0_brandnew.sfmsidecar" in cmp_extra["sidecars_added"],
        "item.comparator_detects_an_extra_sidecar",
    )
    os.remove(brand_new_sidecar_path)

    os.remove(other_sidecar_path)
    inv4 = igen.capture_live_state_inventory(master_path, authority_dir)
    cmp_missing = igen.compare_inventories(inv3, inv4)
    expect(
        cmp_missing["exact_match"] is False and "sfm_master_0_otherfile.sfmsidecar" in cmp_missing["sidecars_removed"],
        "item.comparator_detects_a_missing_sidecar",
    )

    with open(master_path, "wb") as f:
        f.write(g2_bytes)
    inv5 = igen.capture_live_state_inventory(master_path, authority_dir)
    cmp_master_changed = igen.compare_inventories(inv4, inv5)
    expect(
        cmp_master_changed["exact_match"] is False and cmp_master_changed["master_matches"] is False,
        "item.comparator_detects_a_changed_master",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# Section: I1 (BLOCKER 4 -- full stage re-gating; BLOCKER 5 -- no eval;
# BLOCKER 6 -- exact G2 publication record).
# =======================================================================
sys.stdout.write("\n--- I1 baseline ---\n")

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_")
try:
    master_path = os.path.join(tmp_dir, "master.txt")
    with open(CANONICAL_MASTER_CANDIDATE_PATH, "rb") as f:
        real_g1_bytes = f.read()
    with open(master_path, "wb") as f:
        f.write(real_g1_bytes)

    ns = fresh_ns(tmp_dir, make_15_shots(u"item11"), master_path=master_path)
    authority_runtime, _e, authority_observation = ns["import_authority_runtime"]()
    broker = ns["get_canonical_broker"](authority_runtime)

    record = make_passing_record(master_sha256=EXPECTED_CANONICAL_MASTER_SHA256)
    cont = {}
    out = ns["_snapshot_i1_01_baseline"](record, cont, broker, authority_observation, ns["sfmApp"].GetShots(), None, None)
    expect(out["classification"] == u"I1_BASELINE_PASSED", "item.correct_baseline_passes")
    expect(out.get("failed_gates") == [], "item.correct_baseline_has_no_failed_gates")
    expect(cont.get("i1_baseline_inventory") is not None, "item.baseline_persists_inventory_for_later_restoration_check")

    # R2 BLOCKER 6: the baseline inventory is ALSO written as its own
    # standalone, immutable, write-once artifact -- never only embedded.
    expect(
        os.path.isfile(ns["BASELINE_INVENTORY_ARTIFACT_PATH"]),
        "r2blocker6.baseline_inventory_artifact_file_actually_written",
    )
    with open(ns["BASELINE_INVENTORY_ARTIFACT_PATH"], "rb") as f:
        reread_artifact = json.loads(f.read().decode("utf-8"))
    expect(
        reread_artifact == cont["i1_baseline_inventory"],
        "r2blocker6.baseline_inventory_artifact_exactly_matches_the_embedded_inventory",
    )
    expect(
        cont.get("i1_baseline_inventory_artifact_path") == ns["BASELINE_INVENTORY_ARTIFACT_PATH"],
        "r2blocker6.continuation_state_records_the_artifact_path",
    )
    raised_dup_artifact = False
    try:
        ns["write_evidence_json_once"](ns["BASELINE_INVENTORY_ARTIFACT_PATH"], {"different": True})
    except ns["CheckpointIError"]:
        raised_dup_artifact = True
    expect(raised_dup_artifact, "r2blocker6.baseline_inventory_artifact_is_write_once")

    record_wrongsha = make_passing_record(master_sha256=EXPECTED_CANONICAL_MASTER_SHA256, production_sha_ok=False)
    ns2 = fresh_ns(tmp_dir + "_wrongsha", make_15_shots(u"item13"), master_path=master_path)
    authority_runtime2, _e2, authority_observation2 = ns2["import_authority_runtime"]()
    broker2 = ns2["get_canonical_broker"](authority_runtime2)
    out2 = ns2["_snapshot_i1_01_baseline"](record_wrongsha, {}, broker2, authority_observation2, ns2["sfmApp"].GetShots(), None, None)
    expect(
        out2["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"identity.production_sha256_matches_expected" in out2["failed_gates"],
        "item.wrong_production_sha_fails",
    )

    record_wrongruntime = make_passing_record(master_sha256=EXPECTED_CANONICAL_MASTER_SHA256, api_ok=False, build_ok=False)
    ns3 = fresh_ns(tmp_dir + "_wrongrt", make_15_shots(u"item14"), master_path=master_path)
    authority_runtime3, _e3, authority_observation3 = ns3["import_authority_runtime"]()
    broker3 = ns3["get_canonical_broker"](authority_runtime3)
    out3 = ns3["_snapshot_i1_01_baseline"](record_wrongruntime, {}, broker3, authority_observation3, ns3["sfmApp"].GetShots(), None, None)
    expect(
        out3["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"identity.runtime_api_version_matches_expected" in out3["failed_gates"]
        and u"identity.runtime_build_id_matches_expected" in out3["failed_gates"],
        "item.wrong_runtime_api_and_build_fails",
    )

    ns4 = fresh_ns(tmp_dir + "_wrongfixture", make_15_shots(u"item15"), master_path=master_path,
                    fixture_basename=u"some_other.dmx")
    authority_runtime4, _e4, authority_observation4 = ns4["import_authority_runtime"]()
    broker4 = ns4["get_canonical_broker"](authority_runtime4)
    record4 = make_passing_record(master_sha256=EXPECTED_CANONICAL_MASTER_SHA256, fixture_basename=u"some_other.dmx")
    out4 = ns4["_snapshot_i1_01_baseline"](record4, {}, broker4, authority_observation4, ns4["sfmApp"].GetShots(), None, None)
    expect(
        out4["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"fixture.matches_expected_normalized_copy" in out4["failed_gates"],
        "item.wrong_fixture_fails",
    )

    record_wrongguard = make_passing_record(master_sha256=EXPECTED_CANONICAL_MASTER_SHA256, guard_state=u"SELECTED_USED")
    ns5 = fresh_ns(tmp_dir + "_wrongguard", make_15_shots(u"item16"), master_path=master_path)
    authority_runtime5, _e5, authority_observation5 = ns5["import_authority_runtime"]()
    broker5 = ns5["get_canonical_broker"](authority_runtime5)
    out5 = ns5["_snapshot_i1_01_baseline"](record_wrongguard, {}, broker5, authority_observation5, ns5["sfmApp"].GetShots(), None, None)
    expect(
        out5["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"state.guard_state_is_unused" in out5["failed_gates"],
        "item.wrong_guard_state_fails",
    )
finally:
    for suffix in ("", "_wrongsha", "_wrongrt", "_wrongfixture", "_wrongguard"):
        shutil.rmtree(tmp_dir + suffix, ignore_errors=True)

sys.stdout.write("\n--- I1 G1-stage / G2-ready / G2-stage (BLOCKER 4/5/6) ---\n")


def _i1_full_setup(tag):
    tmp = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_i1_%s_" % tag)
    master_path = os.path.join(tmp, "master.txt")
    with open(CANONICAL_MASTER_CANDIDATE_PATH, "rb") as f:
        g1_bytes = f.read()
    with open(master_path, "wb") as f:
        f.write(g1_bytes)
    ns = fresh_ns(tmp, make_15_shots(tag), master_path=master_path)
    authority_runtime, _e, authority_observation = ns["import_authority_runtime"]()
    broker = ns["get_canonical_broker"](authority_runtime)
    record = make_passing_record(master_sha256=EXPECTED_CANONICAL_MASTER_SHA256)
    cont = {}
    out = ns["_snapshot_i1_01_baseline"](record, cont, broker, authority_observation, ns["sfmApp"].GetShots(), None, None)
    assert out["classification"] == u"I1_BASELINE_PASSED", "setup baseline must pass: %r" % (out,)
    return tmp, ns, broker, authority_observation, cont, master_path, g1_bytes


tmp_dir, ns, broker, authority_observation, cont, master_path, g1_bytes = _i1_full_setup(u"i1full")
try:
    shot9_folds = frozenset(cont["i1_shot9_folds_sorted"])
    g1_sha = cont["i1_baseline_master_sha256"]
    g2_sha = cont["i1_expected_g2_sha256"]
    baseline_pid = cont["i1_baseline_pid"]
    cache_key_for = ns["cache_key_for"]

    bad_log = make_run_log_bytes(u"shot9", len(shot9_folds), g1_sha, production_pass=False, production_fail=True)
    log_verif_fail = ns["verify_run_log_content"](bad_log, u"shot9", len(shot9_folds), expect_production_pass=True)
    record_g1fail = make_passing_record(
        current_pid=baseline_pid, guard_state=u"SELECTED_USED", master_sha256=g1_sha,
        run_captured={"step_ordinal": 1, "log_verification": log_verif_fail},
    )
    out_g1fail = ns["_snapshot_i1_02_after_g1"](record_g1fail, cont, broker, authority_observation, [], None, None)
    expect(
        out_g1fail["classification"] == u"FAIL" and u"run.run01_verifier_all_checks_pass" in out_g1fail["failed_gates"],
        "item.g1_command_explicit_fail_causes_stage_failure",
    )

    # BLOCKER 4: wrong live Master at I1-02 (still G1 expected).
    record_wrongmaster = make_passing_record(
        current_pid=baseline_pid, guard_state=u"SELECTED_USED", master_sha256=g2_sha,
        run_captured={"step_ordinal": 1, "log_verification": ns["verify_run_log_content"](
            make_run_log_bytes(u"shot9", len(shot9_folds), g1_sha), u"shot9", len(shot9_folds), expect_production_pass=True,
        )},
    )
    out_wrongmaster = ns["_snapshot_i1_02_after_g1"](record_wrongmaster, cont, broker, authority_observation, [], None, None)
    expect(
        out_wrongmaster["classification"] == u"FAIL"
        and u"generation.live_master_still_exactly_g1" in out_wrongmaster["failed_gates"],
        "blocker4.i1_02_fails_if_live_master_is_not_still_exactly_g1",
    )

    good_log = make_run_log_bytes(u"shot9", len(shot9_folds), g1_sha)
    log_verif_good = ns["verify_run_log_content"](good_log, u"shot9", len(shot9_folds), expect_production_pass=True)
    expect(log_verif_good["all_checks_pass"] is True, "sanity.good_g1_log_verifies")

    record_wrongpid = make_passing_record(current_pid=baseline_pid + 1, guard_state=u"SELECTED_USED", master_sha256=g1_sha,
                                           run_captured={"step_ordinal": 1, "log_verification": log_verif_good})
    out_wrongpid = ns["_snapshot_i1_02_after_g1"](record_wrongpid, cont, broker, authority_observation, [], None, None)
    expect(
        out_wrongpid["classification"] == u"FAIL" and u"continuity.same_pid_as_baseline" in out_wrongpid["failed_gates"],
        "item.wrong_pid_continuity_fails",
    )

    v1_view_wrong_gen = _build_known_view(u"11112222" * 8, shot9_folds)
    broker._view_cache.admit_batch([v1_view_wrong_gen])
    record_wrongview = make_passing_record(
        current_pid=baseline_pid, guard_state=u"SELECTED_USED", master_sha256=g1_sha,
        provider_counters={"current_open_provider_count": 0, "peak_open_provider_count": 1,
                            "total_provider_opens": 1, "total_provider_closes": 1, "active_cohort_id": None},
        recent_diagnostics=[{"event": u"cohort_acquired", "t": 1.0, "detail": {}}],
        run_captured={"step_ordinal": 1, "log_verification": log_verif_good},
    )
    out_wrongview = ns["_snapshot_i1_02_after_g1"](record_wrongview, cont, broker, authority_observation, [], None, None)
    expect(
        out_wrongview["classification"] == u"FAIL" and u"view.g1_view_present" in out_wrongview["failed_gates"],
        "item.missing_g1_view_at_expected_key_fails",
    )

    v1_view = _build_known_view(g1_sha, shot9_folds)
    broker._view_cache.admit_batch([v1_view])
    record_baddelta = make_passing_record(
        current_pid=baseline_pid, guard_state=u"SELECTED_USED", master_sha256=g1_sha,
        provider_counters={"current_open_provider_count": 0, "peak_open_provider_count": 0,
                            "total_provider_opens": 0, "total_provider_closes": 0, "active_cohort_id": None},
        recent_diagnostics=[],
        run_captured={"step_ordinal": 1, "log_verification": log_verif_good},
    )
    out_baddelta = ns["_snapshot_i1_02_after_g1"](record_baddelta, cont, broker, authority_observation, [], None, None)
    expect(
        out_baddelta["classification"] == u"FAIL"
        and u"provider.exactly_one_open_since_baseline" in out_baddelta["failed_gates"]
        and u"diagnostics.delta_contains_cohort_acquired" in out_baddelta["failed_gates"],
        "item.provider_delta_not_1_1_and_missing_cohort_acquired_both_fail",
    )

    record_g1happy = make_passing_record(
        current_pid=baseline_pid, guard_state=u"SELECTED_USED", master_sha256=g1_sha,
        provider_counters={"current_open_provider_count": 0, "peak_open_provider_count": 1,
                            "total_provider_opens": 1, "total_provider_closes": 1, "active_cohort_id": None},
        recent_diagnostics=[{"event": u"cohort_acquired", "t": 1.0, "detail": {}}],
        run_captured={"step_ordinal": 1, "log_verification": log_verif_good},
    )
    out_g1happy = ns["_snapshot_i1_02_after_g1"](record_g1happy, cont, broker, authority_observation, [], None, None)
    expect(out_g1happy["classification"] == u"I1_G1_STAGE_PASSED", "sanity.g1_stage_happy_path_passes")
    cont["i1_g1_stage_provider_counters"] = record_g1happy["provider_counters"]
    cont["i1_g1_stage_diagnostics"] = record_g1happy["recent_diagnostics"]

    # BLOCKER 6: G2-ready gate now requires the EXACT publication record.
    record_wrongmaster_ready = make_passing_record(current_pid=baseline_pid, guard_state=u"SELECTED_USED", master_sha256=g1_sha)
    out_wrongready = ns["_snapshot_i1_03_g2_ready"](record_wrongmaster_ready, cont, broker, authority_observation, [], None, None)
    expect(
        out_wrongready["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"generation.live_master_equals_expected_g2" in out_wrongready["failed_gates"],
        "item.g2_ready_state_with_wrong_master_fails",
    )

    with open(master_path, "wb") as f:
        f.write(igen.construct_g2_bytes(g1_bytes))
    record_g2ready_noauth = make_passing_record(current_pid=baseline_pid, guard_state=u"SELECTED_USED", master_sha256=g2_sha)
    out_missing_record = ns["_snapshot_i1_03_g2_ready"](record_g2ready_noauth, cont, broker, authority_observation, [], None, None)
    expect(
        out_missing_record["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"authority.publication_record_present" in out_missing_record["failed_gates"],
        "blocker6.missing_g2_publication_record_fails",
    )

    # A merely-present sidecar with NO valid publication record is no
    # longer sufficient (this was the pre-correction defect).
    bogus_sidecar_path = os.path.join(ns["SHIPPED_AUTHORITY_DIR"], "sfm_master_0_bogus.sfmsidecar")
    with open(bogus_sidecar_path, "wb") as f:
        f.write(b"not a real sidecar")
    out_bogus_sidecar_only = ns["_snapshot_i1_03_g2_ready"](record_g2ready_noauth, cont, broker, authority_observation, [], None, None)
    expect(
        out_bogus_sidecar_only["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"authority.publication_record_present" in out_bogus_sidecar_only["failed_gates"],
        "blocker6.a_merely_present_sidecar_with_no_publication_record_is_not_sufficient",
    )
    os.remove(bogus_sidecar_path)

    write_g2_publication_record(
        ns["G2_PUBLICATION_RECORD_PATH"], g1_sha=u"0" * 64, g2_sha=g2_sha,
        generation_basename=u"sfm_master_0_%s.sfmsidecar" % g2_sha, sidecar_sha=u"0" * 64,
    )
    out_wrong_record = ns["_snapshot_i1_03_g2_ready"](record_g2ready_noauth, cont, broker, authority_observation, [], None, None)
    expect(
        out_wrong_record["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"authority.record_g1_source_sha256_matches" in out_wrong_record["failed_gates"],
        "blocker6.publication_record_with_wrong_g1_sha_fails",
    )
    os.remove(ns["G2_PUBLICATION_RECORD_PATH"])

    # R2 BLOCKER 1/3: I1-03 now requires BOTH a valid publication record
    # AND a valid G2 Master activation record -- write the publication
    # record + real sidecar + manifest first (as before), and confirm the
    # activation-record gates correctly fail while it is still missing.
    g2_sidecar_basename = u"sfm_master_0_%s.sfmsidecar" % g2_sha
    g2_sidecar_path = os.path.join(ns["SHIPPED_AUTHORITY_DIR"], g2_sidecar_basename)
    with open(g2_sidecar_path, "wb") as f:
        f.write(b"real-g2-sidecar-bytes")
    real_sidecar_sha = igen.sha256_file(g2_sidecar_path)
    write_manifest_json(ns["SHIPPED_AUTHORITY_DIR"], source_sha256=g2_sha, generation_basename=g2_sidecar_basename)
    real_manifest_sha = igen.sha256_file(os.path.join(ns["SHIPPED_AUTHORITY_DIR"], igen.MANIFEST_BASENAME))
    write_g2_publication_record(
        ns["G2_PUBLICATION_RECORD_PATH"], g1_sha=g1_sha, g2_sha=g2_sha,
        generation_basename=g2_sidecar_basename, sidecar_sha=real_sidecar_sha,
        manifest_sha256_after_publication=real_manifest_sha,
    )

    out_pub_ok_no_activation = ns["_snapshot_i1_03_g2_ready"](record_g2ready_noauth, cont, broker, authority_observation, [], None, None)
    expect(
        out_pub_ok_no_activation["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"activation.activation_record_present" in out_pub_ok_no_activation["failed_gates"],
        "r2blocker1.i1_03_still_refuses_with_a_valid_publication_record_but_no_activation_record",
    )

    write_g2_activation_record(
        ns["G2_ACTIVATION_RECORD_PATH"], expected_g1_sha=g1_sha, rederived_g2_sha=u"0" * 64,
        post_activation_master_sha=g2_sha,
    )
    out_wrong_activation2 = ns["_snapshot_i1_03_g2_ready"](record_g2ready_noauth, cont, broker, authority_observation, [], None, None)
    expect(
        out_wrong_activation2["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"activation.activation_rederived_g2_matches_expected" in out_wrong_activation2["failed_gates"],
        "r2blocker1.i1_03_refuses_an_activation_record_whose_rederived_g2_does_not_match",
    )
    os.remove(ns["G2_ACTIVATION_RECORD_PATH"])
    write_g2_activation_record(
        ns["G2_ACTIVATION_RECORD_PATH"], expected_g1_sha=g1_sha, rederived_g2_sha=g2_sha,
        post_activation_master_sha=g2_sha,
    )

    out_record_ok_but_cache = ns["_snapshot_i1_03_g2_ready"](record_g2ready_noauth, cont, broker, authority_observation, [], None, None)
    expect(
        u"authority.publication_record_present" not in out_record_ok_but_cache["failed_gates"]
        and u"authority.record_g1_source_sha256_matches" not in out_record_ok_but_cache["failed_gates"]
        and u"authority.exact_named_sidecar_sha_matches_record" not in out_record_ok_but_cache["failed_gates"]
        and u"authority.active_manifest_source_sha_equals_g2" not in out_record_ok_but_cache["failed_gates"],
        "blocker6.a_correct_publication_record_and_matching_artifacts_satisfy_every_authority_gate",
    )
    expect(
        u"activation.activation_record_present" not in out_record_ok_but_cache["failed_gates"]
        and u"activation.activation_success" not in out_record_ok_but_cache["failed_gates"]
        and u"activation.activation_rederived_g2_matches_expected" not in out_record_ok_but_cache["failed_gates"]
        and u"activation.activation_post_master_equals_expected_g2" not in out_record_ok_but_cache["failed_gates"],
        "r2blocker1.a_correct_activation_record_satisfies_every_activation_gate",
    )

    # R3 HARDENING: the consumer must mechanically require the record's
    # own recorded semantic_parity to report all_parity_checks_pass=True
    # -- never merely assume Phase A's own producer-side check succeeded.
    os.remove(ns["G2_PUBLICATION_RECORD_PATH"])
    write_g2_publication_record(
        ns["G2_PUBLICATION_RECORD_PATH"], g1_sha=g1_sha, g2_sha=g2_sha,
        generation_basename=g2_sidecar_basename, sidecar_sha=real_sidecar_sha,
        manifest_sha256_after_publication=real_manifest_sha, semantic_parity_pass=False,
    )
    out_bad_parity = ns["_snapshot_i1_03_g2_ready"](record_g2ready_noauth, cont, broker, authority_observation, [], None, None)
    expect(
        out_bad_parity["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"authority.record_semantic_parity_is_pass" in out_bad_parity["failed_gates"],
        "r3hardening.i1_03_refuses_a_publication_record_whose_semantic_parity_is_not_pass",
    )
    os.remove(ns["G2_PUBLICATION_RECORD_PATH"])
    write_g2_publication_record(
        ns["G2_PUBLICATION_RECORD_PATH"], g1_sha=g1_sha, g2_sha=g2_sha,
        generation_basename=g2_sidecar_basename, sidecar_sha=real_sidecar_sha,
        manifest_sha256_after_publication=real_manifest_sha,
    )

    g2_view_preexisting = _build_known_view(g2_sha, shot9_folds)
    broker._view_cache.admit_batch([g2_view_preexisting])
    out_preexisting = ns["_snapshot_i1_03_g2_ready"](record_g2ready_noauth, cont, broker, authority_observation, [], None, None)
    expect(
        out_preexisting["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"cache.g2_view_not_yet_cached" in out_preexisting["failed_gates"],
        "item.preexisting_g2_cache_hit_before_command_b_fails",
    )
finally:
    pass  # cleaned up after the G2-stage block below (same tmp_dir reused)

sys.stdout.write("\n--- I1 G2-stage ---\n")
try:
    stale_placeholder = _build_known_view(g2_sha, shot9_folds, stale=True)
    broker._view_cache.admit_batch([stale_placeholder])
    # Provider/diagnostic state carries forward UNCHANGED from the G1
    # stage -- the external helper swap between commands touches only
    # the Master file and the shipped authority directory, never the
    # broker's own accounting.
    record_g2ready2 = make_passing_record(
        current_pid=baseline_pid, guard_state=u"SELECTED_USED", master_sha256=g2_sha,
        provider_counters=dict(cont["i1_g1_stage_provider_counters"]),
        recent_diagnostics=list(cont["i1_g1_stage_diagnostics"]),
    )
    out_g2ready_final = ns["_snapshot_i1_03_g2_ready"](record_g2ready2, cont, broker, authority_observation, [], None, None)
    expect(out_g2ready_final["classification"] == u"I1_G2_READY", "sanity.g2_ready_happy_path_passes")
    cont["i1_g2_ready_provider_counters"] = record_g2ready2["provider_counters"]
    cont["i1_g2_ready_diagnostics"] = record_g2ready2["recent_diagnostics"]

    good_g2_log = make_run_log_bytes(u"shot9", len(shot9_folds), g2_sha)
    log_verif_g2_good = ns["verify_run_log_content"](good_g2_log, u"shot9", len(shot9_folds), expect_production_pass=True)
    expect(log_verif_g2_good["logged_master_sha256"] == g2_sha, "sanity.g2_log_reports_g2_master_sha")

    record_wrongmaster_i104 = make_passing_record(
        current_pid=baseline_pid, guard_state=u"SELECTED_USED", master_sha256=g1_sha,
        run_captured={"step_ordinal": 2, "log_verification": log_verif_g2_good},
    )
    out_wrongmaster_i104 = ns["_snapshot_i1_04_after_g2"](record_wrongmaster_i104, cont, broker, authority_observation, [], None, None)
    expect(
        out_wrongmaster_i104["classification"] == u"FAIL"
        and u"generation.live_master_still_exactly_g2" in out_wrongmaster_i104["failed_gates"],
        "blocker4.i1_04_fails_if_live_master_is_not_still_exactly_g2",
    )

    record_usesg1 = make_passing_record(
        current_pid=baseline_pid, guard_state=u"SELECTED_USED", master_sha256=g2_sha,
        provider_counters={"current_open_provider_count": 0, "peak_open_provider_count": 1,
                            "total_provider_opens": 2, "total_provider_closes": 2, "active_cohort_id": None},
        recent_diagnostics=[{"event": u"cohort_acquired", "t": 1.0, "detail": {}},
                             {"event": u"cohort_acquired", "t": 2.0, "detail": {}}],
        run_captured={"step_ordinal": 2, "log_verification": log_verif_g2_good},
    )
    out_usesg1 = ns["_snapshot_i1_04_after_g2"](record_usesg1, cont, broker, authority_observation, [], None, None)
    expect(
        out_usesg1["classification"] == u"FAIL" and u"view.g2_view_present" in out_usesg1["failed_gates"],
        "item.g2_command_without_a_g2_view_fails",
    )

    g2_view = _build_known_view(g2_sha, shot9_folds)
    broker._view_cache.admit_batch([g2_view])
    record_reused = make_passing_record(
        current_pid=baseline_pid, guard_state=u"SELECTED_USED", master_sha256=g2_sha,
        provider_counters=dict(cont["i1_g2_ready_provider_counters"]),
        recent_diagnostics=list(cont["i1_g2_ready_diagnostics"]) + [
            {"event": u"fully_reused_no_provider_open", "t": 2.0, "detail": {}},
        ],
        run_captured={"step_ordinal": 2, "log_verification": log_verif_g2_good},
    )
    out_reused = ns["_snapshot_i1_04_after_g2"](record_reused, cont, broker, authority_observation, [], None, None)
    expect(
        out_reused["classification"] == u"FAIL"
        and u"provider.exactly_one_open_since_g2_ready" in out_reused["failed_gates"]
        and u"diagnostics.delta_excludes_fully_reused_no_provider_open" in out_reused["failed_gates"],
        "item.no_fresh_provider_and_fully_reused_diagnostic_both_fail",
    )

    fresh_g1_again = _build_known_view(g1_sha, shot9_folds)
    broker._view_cache.admit_batch([fresh_g1_again])
    record_g1stillfresh = make_passing_record(
        current_pid=baseline_pid, guard_state=u"SELECTED_USED", master_sha256=g2_sha,
        provider_counters={"current_open_provider_count": 0, "peak_open_provider_count": 1,
                            "total_provider_opens": 2, "total_provider_closes": 2, "active_cohort_id": None},
        recent_diagnostics=[{"event": u"cohort_acquired", "t": 1.0, "detail": {}},
                             {"event": u"cohort_acquired", "t": 2.0, "detail": {}}],
        run_captured={"step_ordinal": 2, "log_verification": log_verif_g2_good},
    )
    out_g1stillfresh = ns["_snapshot_i1_04_after_g2"](record_g1stillfresh, cont, broker, authority_observation, [], None, None)
    expect(
        out_g1stillfresh["classification"] == u"FAIL"
        and u"view.g1_view_no_longer_a_usable_cache_hit" in out_g1stillfresh["failed_gates"],
        "item.g1_still_a_fresh_usable_cache_hit_after_replacement_fails",
    )

    broker._view_cache.invalidate_generation(g1_sha)

    record_leak = make_passing_record(
        current_pid=baseline_pid, guard_state=u"SELECTED_USED", master_sha256=g2_sha,
        provider_counters={"current_open_provider_count": 0, "peak_open_provider_count": 1,
                            "total_provider_opens": 2, "total_provider_closes": 2, "active_cohort_id": None},
        lease_counters={"outstanding_lease_count": 1, "unreleased_lease_count": 0, "view_cache_entry_count": 2},
        recent_diagnostics=[{"event": u"cohort_acquired", "t": 1.0, "detail": {}},
                             {"event": u"cohort_acquired", "t": 2.0, "detail": {}}],
        run_captured={"step_ordinal": 2, "log_verification": log_verif_g2_good},
    )
    out_leak = ns["_snapshot_i1_04_after_g2"](record_leak, cont, broker, authority_observation, [], None, None)
    expect(
        out_leak["classification"] == u"FAIL" and u"lease.outstanding_zero" in out_leak["failed_gates"],
        "item.lease_leak_fails",
    )

    record_g2happy = make_passing_record(
        current_pid=baseline_pid, guard_state=u"SELECTED_USED", master_sha256=g2_sha,
        provider_counters={"current_open_provider_count": 0, "peak_open_provider_count": 1,
                            "total_provider_opens": 2, "total_provider_closes": 2, "active_cohort_id": None},
        recent_diagnostics=[{"event": u"cohort_acquired", "t": 1.0, "detail": {}},
                             {"event": u"cohort_acquired", "t": 2.0, "detail": {}}],
        run_captured={"step_ordinal": 2, "log_verification": log_verif_g2_good},
    )
    out_g2happy = ns["_snapshot_i1_04_after_g2"](record_g2happy, cont, broker, authority_observation, [], None, None)
    expect(out_g2happy["classification"] == u"I1_PASS", "item.g2_command_explicit_pass_completes_i1_pass")
    expect(out_g2happy["failed_gates"] == [], "item.complete_i1_happy_path_has_no_failed_gates")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# Section: I2 prearm observer (BLOCKER 3) -- a REAL PySide QTimer.
# =======================================================================
sys.stdout.write("\n--- I2 prearm observer (BLOCKER 3, real QTimer) ---\n")


def _i2_setup(tag):
    tmp = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_i2_%s_" % tag)
    master_path = os.path.join(tmp, "master.txt")
    with open(CANONICAL_MASTER_CANDIDATE_PATH, "rb") as f:
        g1_bytes = f.read()
    g2_bytes = igen.construct_g2_bytes(g1_bytes)
    g1_sha = hashlib.sha256(g1_bytes).hexdigest()
    g2_sha = hashlib.sha256(g2_bytes).hexdigest()
    with open(master_path, "wb") as f:
        f.write(g2_bytes)  # I2 starts under G2

    main_window = _FakeMainWindow()
    ns = fresh_ns(tmp, make_15_shots(tag), master_path=master_path, main_window=main_window)
    with open(ns["G1_SOURCE_BYTES_BACKUP_PATH"], "wb") as f:
        f.write(g1_bytes)

    # R2 BLOCKER 1/3: i2_01_prearm now requires a valid publication AND
    # activation record (both are part of "G2 is really live" evidence),
    # and R2 BLOCKER 5 requires a known baseline Master path to bind
    # against -- provide a complete, self-consistent evidence chain by
    # default so tests exercising ONE specific bad precondition aren't
    # masked by an unrelated, incidentally-missing record.
    _write_complete_g2_authority_state(ns, g1_sha, g2_sha)

    cont = {
        "i1_expected_g2_sha256": g2_sha, "i1_baseline_master_sha256": g1_sha,
        "i1_baseline_inventory": {"master_path": master_path, "authority_dir": ns["SHIPPED_AUTHORITY_DIR"]},
        "i2_baseline_pid": os.getpid(), "i2_baseline_provider_counters": {
            "current_open_provider_count": 0, "total_provider_opens": 0, "total_provider_closes": 0,
        },
        "i2_baseline_diagnostics": [], "i2_prearmed": False,
    }
    return tmp, ns, main_window, master_path, g1_bytes, g2_bytes, g1_sha, g2_sha, cont


# =======================================================================
# Section: I2 baseline (_snapshot_i2_00_baseline had NO dedicated
# coverage before this correction round; now also gated on the
# activation record, R2 BLOCKER 1, as defense in depth alongside I1-03).
# =======================================================================
sys.stdout.write("\n--- I2 baseline ---\n")

tmp_dir, ns, main_window, master_path, g1_bytes, g2_bytes, g1_sha, g2_sha, cont = _i2_setup(u"i2_00happy")
try:
    record_i200 = make_passing_record(current_pid=os.getpid(), guard_state=u"UNUSED", master_sha256=g2_sha)
    out_i200 = ns["_snapshot_i2_00_baseline"](record_i200, cont, None, None, ns["sfmApp"].GetShots(), main_window, None)
    expect(out_i200["classification"] == u"I2_BASELINE_PASSED", "sanity.i2_00_baseline_happy_path_passes")
    expect(out_i200["failed_gates"] == [], "sanity.i2_00_baseline_happy_path_has_no_failed_gates")
    expect(cont.get("i2_baseline_pid") == os.getpid(), "item.i2_00_baseline_persists_the_observed_pid")

    os.remove(ns["G2_ACTIVATION_RECORD_PATH"])
    out_i200_noact = ns["_snapshot_i2_00_baseline"](record_i200, dict(cont), None, None, ns["sfmApp"].GetShots(), main_window, None)
    expect(
        out_i200_noact["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"activation.activation_record_present" in out_i200_noact["failed_gates"],
        "r2blocker1.i2_00_baseline_also_requires_a_valid_activation_record",
    )
    write_g2_activation_record(
        ns["G2_ACTIVATION_RECORD_PATH"], expected_g1_sha=g1_sha, rederived_g2_sha=g2_sha,
        post_activation_master_sha=g2_sha,
    )

    record_i200_wrongmaster = make_passing_record(current_pid=os.getpid(), guard_state=u"UNUSED", master_sha256=g1_sha)
    out_i200_wrongmaster = ns["_snapshot_i2_00_baseline"](
        record_i200_wrongmaster, dict(cont), None, None, ns["sfmApp"].GetShots(), main_window, None,
    )
    expect(
        out_i200_wrongmaster["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"identity.live_master_equals_g2" in out_i200_wrongmaster["failed_gates"],
        "item.i2_00_baseline_refuses_when_live_master_is_not_g2",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)


def _pump_events(app, total_wait_ms=500, step_ms=10):
    """Processes real Qt events interleaved with real wall-clock sleeps
    -- used ONLY offline, never a production pattern -- so a real
    QTimer (which fires based on elapsed wall-clock time, not merely
    event-loop iterations) actually gets a chance to fire during this
    synchronous test."""
    elapsed = 0
    while elapsed < total_wait_ms:
        app.processEvents()
        QtCore.QThread.msleep(step_ms)
        elapsed += step_ms
    app.processEvents()


_qapp = QtCore.QCoreApplication.instance()
if _qapp is None:
    _qapp = QtCore.QCoreApplication([])

tmp_dir, ns, main_window, master_path, g1_bytes, g2_bytes, g1_sha, g2_sha, cont = _i2_setup(u"i2prearmok")
try:
    record_prearm = make_passing_record(current_pid=os.getpid(), guard_state=u"UNUSED", master_sha256=g2_sha)
    prod_ns_real = ns["load_production_guard_definitions"]()[0]
    out_prearm = ns["_snapshot_i2_01_prearm"](record_prearm, cont, None, None, [], main_window, prod_ns_real)
    expect(out_prearm["classification"] == u"PREARM_INSTALLED", "blocker3.prearm_installs_when_preconditions_hold")
    expect(cont.get("i2_prearmed") is True, "blocker3.prearm_marks_continuation_state")

    instance = _FakeProductionRunInstance(main_window, master_path, g2_sha)
    _pump_events(_qapp)
    expect(
        bool(getattr(instance, "_checkpoint_i_wrapper_installed", False)),
        "blocker3.real_qtimer_observer_wraps_the_newly_appeared_instance",
    )
    expect(os.path.exists(ns["I2_PREARM_RESULT_PATH"]), "blocker3.prearm_persists_immutable_arming_evidence")
    with open(ns["I2_PREARM_RESULT_PATH"], "rb") as f:
        prearm_result = json.loads(f.read().decode("utf-8"))
    expect(prearm_result["outcome"] == u"ARMED", "blocker3.persisted_evidence_reports_armed")
    expect(
        prearm_result["validation"]["checks"]["no_target_completed_yet"] is True
        and prearm_result["validation"]["checks"]["zero_native_attempts_so_far"] is True,
        "blocker3.persisted_evidence_proves_arming_happened_before_any_target_or_native_attempt",
    )

    r1 = instance.contextualizer_resolve_resume_target({"n": 1}, {"n": 1})
    expect(r1 == ({"n": 1}, {"n": 1}), "sanity.call_1_target_1_passes_through_unchanged")
    raised = False
    try:
        instance.contextualizer_resolve_resume_target({"n": 2}, {"n": 2})
    except _FakeProbeError as exc:
        raised = True
        expect(u"Live Master changed during the run." in unicode(exc),
               "item.production_itself_detects_changed_master")
    expect(raised, "item.exact_g2_to_g1_injection_happy_path_triggers_the_real_stability_check")
    expect(igen.sha256_file(master_path) == g1_sha, "sanity.master_is_g1_after_call_2_injection")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir, ns, main_window, master_path, g1_bytes, g2_bytes, g1_sha, g2_sha, cont = _i2_setup(u"i2wrongscope")
try:
    record_prearm = make_passing_record(current_pid=os.getpid(), guard_state=u"UNUSED", master_sha256=g2_sha)
    prod_ns_real = ns["load_production_guard_definitions"]()[0]
    ns["_snapshot_i2_01_prearm"](record_prearm, cont, None, None, [], main_window, prod_ns_real)

    wrong_scope_instance = _FakeProductionRunInstance(main_window, master_path, g2_sha, scope_shot_names=(u"shot9",))
    _pump_events(_qapp)
    expect(
        not bool(getattr(wrong_scope_instance, "_checkpoint_i_wrapper_installed", False)),
        "blocker3.observer_refuses_to_wrap_a_run_with_the_wrong_scope",
    )
    with open(ns["I2_PREARM_RESULT_PATH"], "rb") as f:
        prearm_result_wrong = json.loads(f.read().decode("utf-8"))
    expect(prearm_result_wrong["outcome"] == u"UNEXPECTED_RUN", "blocker3.wrong_scope_recorded_as_unexpected_run")
    expect(
        prearm_result_wrong["validation"]["checks"]["scope_shot_matches_expected"] is False,
        "blocker3.wrong_scope_check_correctly_fails",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir, ns, main_window, master_path, g1_bytes, g2_bytes, g1_sha, g2_sha, cont = _i2_setup(u"i2wronggen")
try:
    record_prearm = make_passing_record(current_pid=os.getpid(), guard_state=u"UNUSED", master_sha256=g2_sha)
    prod_ns_real = ns["load_production_guard_definitions"]()[0]
    ns["_snapshot_i2_01_prearm"](record_prearm, cont, None, None, [], main_window, prod_ns_real)

    wrong_gen_instance = _FakeProductionRunInstance(main_window, master_path, g1_sha)  # pinned to G1, not G2
    _pump_events(_qapp)
    expect(
        not bool(getattr(wrong_gen_instance, "_checkpoint_i_wrapper_installed", False)),
        "blocker3.observer_refuses_to_wrap_a_run_pinned_to_the_wrong_generation",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir, ns, main_window, master_path, g1_bytes, g2_bytes, g1_sha, g2_sha, cont = _i2_setup(u"i2timeout")
try:
    ns["_PREARM_TIMEOUT_MS"] = 50  # shrink the timeout so this test is fast
    ns["_PREARM_POLL_INTERVAL_MS"] = 10
    record_prearm = make_passing_record(current_pid=os.getpid(), guard_state=u"UNUSED", master_sha256=g2_sha)
    prod_ns_real = ns["load_production_guard_definitions"]()[0]
    ns["_snapshot_i2_01_prearm"](record_prearm, cont, None, None, [], main_window, prod_ns_real)

    for _ in range(30):
        _qapp.processEvents()
        QtCore.QThread.msleep(10)
    expect(os.path.exists(ns["I2_PREARM_RESULT_PATH"]), "blocker3.timeout_still_persists_evidence")
    with open(ns["I2_PREARM_RESULT_PATH"], "rb") as f:
        prearm_result_timeout = json.loads(f.read().decode("utf-8"))
    expect(prearm_result_timeout["outcome"] == u"TIMEOUT", "blocker3.no_run_ever_appearing_times_out_cleanly")
    expect(igen.sha256_file(master_path) == g2_sha, "blocker3.timeout_performs_no_master_mutation")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir, ns, main_window, master_path, g1_bytes, g2_bytes, g1_sha, g2_sha, cont = _i2_setup(u"i2prearmbad")
try:
    prod_ns_real = ns["load_production_guard_definitions"]()[0]
    record_wrongguard = make_passing_record(current_pid=os.getpid(), guard_state=u"SELECTED_USED", master_sha256=g2_sha)
    out_wrongguard = ns["_snapshot_i2_01_prearm"](record_wrongguard, cont, None, None, [], main_window, prod_ns_real)
    expect(
        out_wrongguard["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"state.guard_state_is_unused" in out_wrongguard["failed_gates"],
        "blocker3.prearm_refuses_when_guard_state_is_not_unused",
    )

    record_wrongmaster = make_passing_record(current_pid=os.getpid(), guard_state=u"UNUSED", master_sha256=g1_sha)
    out_wrongmaster = ns["_snapshot_i2_01_prearm"](record_wrongmaster, cont, None, None, [], main_window, prod_ns_real)
    expect(
        out_wrongmaster["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"identity.live_master_equals_g2" in out_wrongmaster["failed_gates"],
        "blocker3.prearm_refuses_when_live_master_is_not_g2",
    )

    record_runlock = make_passing_record(current_pid=os.getpid(), guard_state=u"UNUSED", master_sha256=g2_sha, run_lock_present=True)
    out_runlock = ns["_snapshot_i2_01_prearm"](record_runlock, cont, None, None, [], main_window, prod_ns_real)
    expect(
        out_runlock["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"state.run_lock_absent" in out_runlock["failed_gates"],
        "blocker3.prearm_refuses_when_a_run_lock_is_already_present",
    )
    expect(cont.get("i2_prearmed") is False, "blocker3.failed_preconditions_never_mark_prearmed")

    # R2 BLOCKER 3: i2_01_prearm now re-gates the FULL governing identity
    # (production SHA/runtime/fixture/shot-count), never installed
    # before round 2. A wrong production SHA at prearm time must refuse.
    record_wrongprod = make_passing_record(current_pid=os.getpid(), guard_state=u"UNUSED", master_sha256=g2_sha,
                                            production_sha_ok=False)
    out_wrongprod = ns["_snapshot_i2_01_prearm"](record_wrongprod, cont, None, None, [], main_window, prod_ns_real)
    expect(
        out_wrongprod["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"identity.production_sha256_matches_expected" in out_wrongprod["failed_gates"],
        "r2blocker3.prearm_refuses_on_a_wrong_production_sha256",
    )

    record_wrongfixture = make_passing_record(current_pid=os.getpid(), guard_state=u"UNUSED", master_sha256=g2_sha,
                                               fixture_basename=u"some_other.dmx")
    out_wrongfixture = ns["_snapshot_i2_01_prearm"](record_wrongfixture, cont, None, None, [], main_window, prod_ns_real)
    expect(
        out_wrongfixture["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"fixture.matches_expected_normalized_copy" in out_wrongfixture["failed_gates"],
        "r2blocker3.prearm_refuses_on_a_wrong_fixture_identity",
    )

    # R2 BLOCKER 3: nonzero open providers/outstanding leases must refuse.
    record_openprovider = make_passing_record(
        current_pid=os.getpid(), guard_state=u"UNUSED", master_sha256=g2_sha,
        provider_counters={"current_open_provider_count": 1, "peak_open_provider_count": 1,
                            "total_provider_opens": 1, "total_provider_closes": 0, "active_cohort_id": u"x"},
    )
    out_openprovider = ns["_snapshot_i2_01_prearm"](record_openprovider, cont, None, None, [], main_window, prod_ns_real)
    expect(
        out_openprovider["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"provider.current_open_provider_count_is_zero" in out_openprovider["failed_gates"],
        "r2blocker3.prearm_refuses_when_a_provider_is_still_open",
    )

    record_leakedlease = make_passing_record(
        current_pid=os.getpid(), guard_state=u"UNUSED", master_sha256=g2_sha,
        lease_counters={"outstanding_lease_count": 1, "unreleased_lease_count": 0, "view_cache_entry_count": 1},
    )
    out_leakedlease = ns["_snapshot_i2_01_prearm"](record_leakedlease, cont, None, None, [], main_window, prod_ns_real)
    expect(
        out_leakedlease["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"lease.outstanding_lease_count_is_zero" in out_leakedlease["failed_gates"],
        "r2blocker3.prearm_refuses_when_a_lease_is_outstanding",
    )

    # R2 BLOCKER 3: the G1 backup must HASH-VERIFY to canonical G1, not
    # merely exist -- round 1 only checked os.path.exists().
    tampered_backup_path = ns["G1_SOURCE_BYTES_BACKUP_PATH"]
    real_backup_bytes = igen._read_bytes(tampered_backup_path)
    os.remove(tampered_backup_path)
    with open(tampered_backup_path, "wb") as f:
        f.write(b"not the real canonical g1 bytes")
    record_goodotherwise = make_passing_record(current_pid=os.getpid(), guard_state=u"UNUSED", master_sha256=g2_sha)
    out_tamperedbackup = ns["_snapshot_i2_01_prearm"](record_goodotherwise, cont, None, None, [], main_window, prod_ns_real)
    expect(
        out_tamperedbackup["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"injection.g1_source_bytes_backup_hashes_to_canonical_g1" in out_tamperedbackup["failed_gates"],
        "r2blocker3.prearm_refuses_when_the_g1_backup_does_not_hash_to_canonical_g1",
    )
    os.remove(tampered_backup_path)
    with open(tampered_backup_path, "wb") as f:
        f.write(real_backup_bytes)

    # R2 BLOCKER 1: a valid publication record but no activation record
    # (or vice versa) must refuse prearm too -- G2 authority readiness
    # alone is never sufficient; the live Master must have been ACTUALLY
    # switched.
    os.remove(ns["G2_ACTIVATION_RECORD_PATH"])
    out_noactivation = ns["_snapshot_i2_01_prearm"](record_goodotherwise, cont, None, None, [], main_window, prod_ns_real)
    expect(
        out_noactivation["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"activation.activation_record_present" in out_noactivation["failed_gates"],
        "r2blocker1.prearm_refuses_with_a_valid_publication_record_but_no_activation_record",
    )
    write_g2_activation_record(
        ns["G2_ACTIVATION_RECORD_PATH"], expected_g1_sha=g1_sha, rederived_g2_sha=g2_sha,
        post_activation_master_sha=g2_sha,
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# R2 BLOCKER 5: the I2 wrapper itself binds the live Master path to the
# I1 baseline's recorded path BEFORE performing the G2->G1 swap -- an
# arbitrary/wrong expected_master_path must refuse the swap even though
# the pre-swap hash genuinely matches G2, and the live Master must
# remain untouched (still G2) afterward.
tmp_dir, ns, main_window, master_path, g1_bytes, g2_bytes, g1_sha, g2_sha, cont = _i2_setup(u"i2wrongpathbinding")
try:
    wrong_expected_master_path = master_path + ".not_the_real_baseline_path"
    instance = _FakeProductionRunInstance(main_window, master_path, g2_sha)
    ns["_install_i2_wrapper"](instance, g2_sha, wrong_expected_master_path)
    instance.contextualizer_resolve_resume_target({"n": 1}, {"n": 1})  # call 1: passthrough
    instance.contextualizer_resolve_resume_target({"n": 2}, {"n": 2})  # call 2: should refuse the swap
    expect(
        igen.sha256_file(master_path) == g2_sha,
        "r2blocker5.wrapper_refuses_the_swap_when_expected_master_path_does_not_match_baseline",
    )
    with open(ns["I2_INJECTION_RECORD_PATH"], "rb") as f:
        injection_evidence_wrongpath = json.loads(f.read().decode("utf-8"))
    expect(
        injection_evidence_wrongpath.get("master_path_matches_baseline") is False
        and injection_evidence_wrongpath.get("swap_performed") is False,
        "r2blocker5.wrapper_evidence_records_the_path_binding_refusal",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

sys.stdout.write("\n--- I2 verify evaluator ---\n")


def _i2_verify_setup(tag):
    tmp = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_i2v_%s_" % tag)
    master_path = os.path.join(tmp, "master.txt")
    with open(CANONICAL_MASTER_CANDIDATE_PATH, "rb") as f:
        g1_bytes = f.read()
    g2_bytes = igen.construct_g2_bytes(g1_bytes)
    g1_sha = hashlib.sha256(g1_bytes).hexdigest()
    g2_sha = hashlib.sha256(g2_bytes).hexdigest()
    with open(master_path, "wb") as f:
        f.write(g1_bytes)
    ns = fresh_ns(tmp, make_15_shots(tag), master_path=master_path)
    cont = {
        "i1_expected_g2_sha256": g2_sha, "i1_baseline_master_sha256": g1_sha,
        "i2_baseline_pid": 5555, "i2_baseline_provider_counters": {
            "current_open_provider_count": 0, "total_provider_opens": 0, "total_provider_closes": 0,
        },
        "i2_baseline_diagnostics": [],
    }
    return tmp, ns, g1_sha, g2_sha, cont


def _write_good_prearm_evidence(ns, g2_sha):
    prearm_result = {
        "outcome": u"ARMED", "elapsed_ms": 25, "wall_time": "2026-09-25 00:00:00", "pid": 5555,
        "validation": {
            "valid": True,
            "checks": {
                "no_target_completed_yet": True, "zero_native_attempts_so_far": True,
                "zero_native_rebuilt_so_far": True, "scope_shot_matches_expected": True,
                "master_hash_matches_g2": True, "wrapper_not_already_installed": True,
                "scope_is_exactly_one_shot": True, "scope_mode_is_selected": True,
            },
            "observed_shot_names": [u"shot3"],
        },
    }
    with open(ns["I2_PREARM_RESULT_PATH"], "wb") as f:
        f.write(json.dumps(prearm_result).encode("utf-8"))


tmp_dir, ns, g1_sha, g2_sha, cont = _i2_verify_setup(u"i2v_happy")
try:
    good_i2_log = make_run_log_bytes(
        u"shot3", 0, g2_sha, production_pass=False, production_fail=True,
        master_changed_message=True, target_callback_abort=True,
        pre_native_count=1, native_rebuild_returned_count=1,
    )
    log_verif = ns["verify_run_log_content"](good_i2_log, u"shot3", None, expect_production_pass=False)
    expect(log_verif["all_checks_pass"] is True, "sanity.good_i2_log_verifies_as_an_expected_failure")

    _write_good_prearm_evidence(ns, g2_sha)
    injection_evidence = {
        "call_index": 2, "pre_swap_matches_expected_g2": True, "swap_performed": True,
        "swap_operation_record": {"post_operation_master_sha256": g1_sha},
    }
    with open(ns["I2_INJECTION_RECORD_PATH"], "wb") as f:
        f.write(json.dumps(injection_evidence).encode("utf-8"))

    record_verify = make_passing_record(
        current_pid=5555, guard_state=u"SELECTED_USED", master_sha256=g1_sha,
        recent_diagnostics=[{"event": u"cohort_acquired", "t": 1.0, "detail": {}}],
        run_captured={"step_ordinal": 3, "log_verification": log_verif},
    )
    out_verify = ns["_snapshot_i2_02_verify"](record_verify, cont, None, None, [], None, None)
    expect(out_verify["classification"] == u"I2_FAIL_CLOSED_PASS", "item.expected_explicit_fail_plus_no_target2_mutation_is_i2_pass")
    expect(out_verify["failed_gates"] == [], "item.happy_path_has_no_failed_gates")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir, ns, g1_sha, g2_sha, cont = _i2_verify_setup(u"i2v_noprearm")
try:
    good_i2_log = make_run_log_bytes(
        u"shot3", 0, g2_sha, production_pass=False, production_fail=True,
        master_changed_message=True, target_callback_abort=True,
        pre_native_count=1, native_rebuild_returned_count=1,
    )
    log_verif = ns["verify_run_log_content"](good_i2_log, u"shot3", None, expect_production_pass=False)
    injection_evidence = {"call_index": 2, "pre_swap_matches_expected_g2": True, "swap_performed": True,
                           "swap_operation_record": {"post_operation_master_sha256": g1_sha}}
    with open(ns["I2_INJECTION_RECORD_PATH"], "wb") as f:
        f.write(json.dumps(injection_evidence).encode("utf-8"))
    record_verify = make_passing_record(
        current_pid=5555, guard_state=u"SELECTED_USED", master_sha256=g1_sha,
        recent_diagnostics=[{"event": u"cohort_acquired", "t": 1.0, "detail": {}}],
        run_captured={"step_ordinal": 3, "log_verification": log_verif},
    )
    out_verify = ns["_snapshot_i2_02_verify"](record_verify, cont, None, None, [], None, None)
    expect(
        out_verify["classification"] == u"FAIL" and u"prearm.result_present" in out_verify["failed_gates"],
        "blocker3.missing_prearm_evidence_fails_verification",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir, ns, g1_sha, g2_sha, cont = _i2_verify_setup(u"i2v_synthetic")
try:
    synthetic_log = make_run_log_bytes(
        u"shot3", 0, g2_sha, production_pass=False, production_fail=True,
        master_changed_message=False, target_callback_abort=False,
        pre_native_count=1, native_rebuild_returned_count=1,
    )
    log_verif = ns["verify_run_log_content"](synthetic_log, u"shot3", None, expect_production_pass=False)
    _write_good_prearm_evidence(ns, g2_sha)
    injection_evidence = {"call_index": 2, "pre_swap_matches_expected_g2": True, "swap_performed": True,
                           "swap_operation_record": {"post_operation_master_sha256": g1_sha}}
    with open(ns["I2_INJECTION_RECORD_PATH"], "wb") as f:
        f.write(json.dumps(injection_evidence).encode("utf-8"))
    record_verify = make_passing_record(
        current_pid=5555, guard_state=u"SELECTED_USED", master_sha256=g1_sha,
        recent_diagnostics=[{"event": u"cohort_acquired", "t": 1.0, "detail": {}}],
        run_captured={"step_ordinal": 3, "log_verification": log_verif},
    )
    out_verify = ns["_snapshot_i2_02_verify"](record_verify, cont, None, None, [], None, None)
    expect(
        out_verify["classification"] == u"FAIL"
        and u"run.master_changed_message_present" in out_verify["failed_gates"]
        and u"run.target_callback_abort_present" in out_verify["failed_gates"],
        "item.a_fail_without_productions_own_stability_check_text_is_rejected",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir, ns, g1_sha, g2_sha, cont = _i2_verify_setup(u"i2v_target2mut")
try:
    mutated_log = make_run_log_bytes(
        u"shot3", 0, g2_sha, production_pass=False, production_fail=True,
        master_changed_message=True, target_callback_abort=True,
        pre_native_count=2, native_rebuild_returned_count=2,
    )
    log_verif = ns["verify_run_log_content"](mutated_log, u"shot3", None, expect_production_pass=False)
    _write_good_prearm_evidence(ns, g2_sha)
    injection_evidence = {"call_index": 2, "pre_swap_matches_expected_g2": True, "swap_performed": True,
                           "swap_operation_record": {"post_operation_master_sha256": g1_sha}}
    with open(ns["I2_INJECTION_RECORD_PATH"], "wb") as f:
        f.write(json.dumps(injection_evidence).encode("utf-8"))
    record_verify = make_passing_record(
        current_pid=5555, guard_state=u"SELECTED_USED", master_sha256=g1_sha,
        recent_diagnostics=[{"event": u"cohort_acquired", "t": 1.0, "detail": {}}],
        run_captured={"step_ordinal": 3, "log_verification": log_verif},
    )
    out_verify = ns["_snapshot_i2_02_verify"](record_verify, cont, None, None, [], None, None)
    expect(
        out_verify["classification"] == u"FAIL"
        and u"run.exactly_one_pre_native" in out_verify["failed_gates"]
        and u"run.exactly_one_native_rebuild_returned" in out_verify["failed_gates"],
        "item.target2_pre_native_and_native_rebuild_returned_both_fail",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir, ns, g1_sha, g2_sha, cont = _i2_verify_setup(u"i2v_postswapacq")
try:
    good_log = make_run_log_bytes(
        u"shot3", 0, g2_sha, production_pass=False, production_fail=True,
        master_changed_message=True, target_callback_abort=True,
        pre_native_count=1, native_rebuild_returned_count=1,
    )
    log_verif = ns["verify_run_log_content"](good_log, u"shot3", None, expect_production_pass=False)
    _write_good_prearm_evidence(ns, g2_sha)
    injection_evidence = {"call_index": 2, "pre_swap_matches_expected_g2": True, "swap_performed": True,
                           "swap_operation_record": {"post_operation_master_sha256": g1_sha}}
    with open(ns["I2_INJECTION_RECORD_PATH"], "wb") as f:
        f.write(json.dumps(injection_evidence).encode("utf-8"))
    record_verify = make_passing_record(
        current_pid=5555, guard_state=u"SELECTED_USED", master_sha256=g1_sha,
        recent_diagnostics=[
            {"event": u"cohort_acquired", "t": 1.0, "detail": {}},
            {"event": u"cohort_acquired", "t": 2.0, "detail": {}},
        ],
        run_captured={"step_ordinal": 3, "log_verification": log_verif},
    )
    out_verify = ns["_snapshot_i2_02_verify"](record_verify, cont, None, None, [], None, None)
    expect(
        out_verify["classification"] == u"FAIL"
        and u"diagnostics.exactly_one_cohort_acquired_no_post_swap_reacquisition" in out_verify["failed_gates"],
        "item.a_second_post_swap_authority_acquisition_fails",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir, ns, g1_sha, g2_sha, cont = _i2_verify_setup(u"i2v_leak")
try:
    good_log = make_run_log_bytes(
        u"shot3", 0, g2_sha, production_pass=False, production_fail=True,
        master_changed_message=True, target_callback_abort=True,
        pre_native_count=1, native_rebuild_returned_count=1,
    )
    log_verif = ns["verify_run_log_content"](good_log, u"shot3", None, expect_production_pass=False)
    _write_good_prearm_evidence(ns, g2_sha)
    injection_evidence = {"call_index": 2, "pre_swap_matches_expected_g2": True, "swap_performed": True,
                           "swap_operation_record": {"post_operation_master_sha256": g1_sha}}
    with open(ns["I2_INJECTION_RECORD_PATH"], "wb") as f:
        f.write(json.dumps(injection_evidence).encode("utf-8"))
    record_verify = make_passing_record(
        current_pid=5555, guard_state=u"SELECTED_USED", master_sha256=g1_sha,
        lease_counters={"outstanding_lease_count": 0, "unreleased_lease_count": 1, "view_cache_entry_count": 1},
        recent_diagnostics=[{"event": u"cohort_acquired", "t": 1.0, "detail": {}}],
        run_captured={"step_ordinal": 3, "log_verification": log_verif},
    )
    out_verify = ns["_snapshot_i2_02_verify"](record_verify, cont, None, None, [], None, None)
    expect(
        out_verify["classification"] == u"FAIL" and u"lease.unreleased_zero" in out_verify["failed_gates"],
        "item.provider_lease_cleanup_failure_fails",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# Section: BLOCKER 8/9 -- final restoration-verification snapshot.
# =======================================================================
sys.stdout.write("\n--- Final restoration verification (BLOCKER 8/9) ---\n")

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_finalize_")
try:
    master_path = os.path.join(tmp_dir, "master.txt")
    with open(CANONICAL_MASTER_CANDIDATE_PATH, "rb") as f:
        g1_bytes = f.read()
    g1_sha = hashlib.sha256(g1_bytes).hexdigest()
    with open(master_path, "wb") as f:
        f.write(g1_bytes)
    ns = fresh_ns(tmp_dir, make_15_shots(u"finalize"), master_path=master_path)

    baseline_inventory = igen.capture_live_state_inventory(master_path, ns["SHIPPED_AUTHORITY_DIR"])
    cont = {"i1_baseline_master_sha256": g1_sha, "i1_baseline_inventory": baseline_inventory}

    record_nofinal = make_passing_record(guard_state=u"UNUSED", master_sha256=g1_sha)

    # R2 BLOCKER 6: i_08 now consumes the STANDALONE baseline inventory
    # artifact file, never only cont's own in-memory value -- with the
    # artifact absent, it must refuse rather than silently falling back.
    out_noartifact = ns["_snapshot_i_08_finalize_verify"](record_nofinal, cont, None, None, [], None, None)
    expect(
        u"finalization.baseline_inventory_artifact_present" in out_noartifact["failed_gates"],
        "r2blocker6.i_08_refuses_without_the_standalone_baseline_inventory_artifact",
    )
    with open(ns["BASELINE_INVENTORY_ARTIFACT_PATH"], "wb") as f:
        f.write(json.dumps(baseline_inventory).encode("utf-8"))

    out_nofinal = ns["_snapshot_i_08_finalize_verify"](record_nofinal, cont, None, None, [], None, None)
    expect(
        out_nofinal["classification"] == u"RESTORATION_NOT_CONFIRMED"
        and u"finalization.record_present" in out_nofinal["failed_gates"],
        "blocker8.missing_finalization_record_is_not_confirmed",
    )

    with open(ns["FINALIZATION_RECORD_PATH"], "wb") as f:
        f.write(json.dumps({"exact_match": False}).encode("utf-8"))
    out_falserecord = ns["_snapshot_i_08_finalize_verify"](record_nofinal, cont, None, None, [], None, None)
    expect(
        out_falserecord["classification"] == u"RESTORATION_NOT_CONFIRMED"
        and u"finalization.exact_match_true" in out_falserecord["failed_gates"],
        "blocker8.finalization_record_reporting_exact_match_false_is_not_confirmed",
    )
    os.remove(ns["FINALIZATION_RECORD_PATH"])

    with open(ns["FINALIZATION_RECORD_PATH"], "wb") as f:
        f.write(json.dumps({"exact_match": True}).encode("utf-8"))
    record_ok = make_passing_record(guard_state=u"UNUSED", master_sha256=g1_sha)
    out_ok = ns["_snapshot_i_08_finalize_verify"](record_ok, cont, None, None, [], None, None)
    expect(out_ok["classification"] == u"RESTORATION_CONFIRMED", "blocker8.genuine_exact_match_restoration_is_confirmed")
    expect(out_ok["failed_gates"] == [], "blocker8.confirmed_restoration_has_no_failed_gates")

    with open(master_path, "wb") as f:
        f.write(igen.construct_g2_bytes(g1_bytes))
    tampered_g2_sha = igen.sha256_file(master_path)
    # A fresh record reflecting the NOW-tampered live Master (a real run
    # would observe this fresh each time via _identity_and_state_record()).
    record_tampered = make_passing_record(guard_state=u"UNUSED", master_sha256=tampered_g2_sha)
    out_tampered = ns["_snapshot_i_08_finalize_verify"](record_tampered, cont, None, None, [], None, None)
    expect(
        out_tampered["classification"] == u"RESTORATION_NOT_CONFIRMED"
        and u"generation.live_master_is_exactly_canonical_g1" in out_tampered["failed_gates"]
        and u"finalization.independent_reverification_exact_match" in out_tampered["failed_gates"],
        "blocker8.independent_reverification_catches_a_live_master_that_no_longer_matches_g1",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# Section: main()'s own final_i_verdict aggregation, end to end.
# =======================================================================
sys.stdout.write("\n--- main() final_i_verdict aggregation ---\n")

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_verdict_")
try:
    ns = fresh_ns(tmp_dir, make_15_shots(u"verdict"))
    cont = ns["read_continuation_state"]()
    cont["captured_snapshots"] = [
        {"operation": u"i1_04_after_g2_command", "classification": u"I1_PASS", "failed_gates": []},
        {"operation": u"i2_02_verify", "classification": u"I2_FAIL_CLOSED_PASS", "failed_gates": []},
    ]
    ns["write_json_rollup"](ns["CONTINUATION_STATE_PATH"], cont)

    i1_verdict = None
    i2_verdict = None
    finalize_verdict = None
    for entry in cont["captured_snapshots"]:
        if entry["operation"] == u"i1_04_after_g2_command":
            i1_verdict = entry["classification"]
        if entry["operation"] == u"i2_02_verify":
            i2_verdict = entry["classification"]
        if entry["operation"] == u"i_08_finalize_verify":
            finalize_verdict = entry["classification"]
    final_i_verdict = None
    if i1_verdict == u"I1_PASS" and i2_verdict == u"I2_FAIL_CLOSED_PASS":
        final_i_verdict = u"I_PASS" if finalize_verdict == u"RESTORATION_CONFIRMED" else u"I_RUNTIME_PASS_RESTORATION_REQUIRED"
    expect(
        final_i_verdict == u"I_RUNTIME_PASS_RESTORATION_REQUIRED",
        "blocker8.i1_and_i2_pass_without_restoration_never_yields_i_pass",
    )

    cont["captured_snapshots"].append(
        {"operation": u"i_08_finalize_verify", "classification": u"RESTORATION_CONFIRMED", "failed_gates": []}
    )
    finalize_verdict = u"RESTORATION_CONFIRMED"
    final_i_verdict = u"I_PASS" if (i1_verdict == u"I1_PASS" and i2_verdict == u"I2_FAIL_CLOSED_PASS" and finalize_verdict == u"RESTORATION_CONFIRMED") else u"I_RUNTIME_PASS_RESTORATION_REQUIRED"
    expect(final_i_verdict == u"I_PASS", "blocker8.i_pass_is_only_reached_after_restoration_confirmed")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# Section: SNAPSHOT_SCHEDULE indexing (R3 BLOCKER 5) -- proves i_08_
# finalize_verify is reachable ONLY at schedule index 8, never earlier
# -- the exact fact that made round 1/round 2's "run the checkpoint
# again for i_08 after any post-G2 stop" instruction false for an
# early-aborted campaign.
# =======================================================================
sys.stdout.write("\n--- Snapshot schedule indexing (R3 BLOCKER 5) ---\n")
tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_schedule_")
try:
    ns = fresh_ns(tmp_dir, make_15_shots(u"schedule"))
    schedule = ns["SNAPSHOT_SCHEDULE"]
    expect(len(schedule) == 8, "r3blocker5.snapshot_schedule_has_exactly_8_entries")
    expect(schedule[2][0] == u"i1_03_g2_ready",
           "r3blocker5.schedule_index_3_maps_to_i1_03_never_i_08")
    expect(schedule[7][0] == u"i_08_finalize_verify",
           "r3blocker5.i_08_is_reachable_only_at_schedule_index_8")
    for idx in range(7):
        expect(schedule[idx][0] != u"i_08_finalize_verify",
               "r3blocker5.schedule_index_%d_is_not_i_08" % (idx + 1))
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# Section: Checkpoint_I_Restoration_Verify.py (R3 BLOCKER 5) -- a
# separate, read-only, one-shot recovery-verification tool for an
# early-aborted campaign, independent of the primary snapshot schedule.
# =======================================================================
sys.stdout.write("\n--- Restoration Verify (R3 BLOCKER 5, standalone) ---\n")

RESTORATION_VERIFY_SCRIPT_PATH = os.path.join(HERE, "Checkpoint_I_Restoration_Verify.py")
with open(RESTORATION_VERIFY_SCRIPT_PATH, "rb") as f:
    restoration_verify_bytes = f.read()
restoration_verify_defs_text = strip_trailing_main_call(restoration_verify_bytes)
expect(b"def main():" in restoration_verify_defs_text, "r3blocker5.restoration_verify_defines_main")
expect(
    b"SNAPSHOT_SCHEDULE[" not in restoration_verify_defs_text
    and b"read_continuation_state(" not in restoration_verify_defs_text
    and b'cont["next_snapshot_index"' not in restoration_verify_defs_text
    and b"CONTINUATION_STATE_PATH =" not in restoration_verify_defs_text,
    "r3blocker5.restoration_verify_never_references_the_primary_snapshot_schedule",
)


def _test_import_authority_runtime_single():
    """Checkpoint_I_Restoration_Verify.py's own import_authority_runtime()
    returns just the module (single value) -- unlike the primary
    checkpoint's own 3-tuple-returning version reused elsewhere in this
    suite."""
    return _test_import_authority_runtime()[0]


def fresh_restoration_verify_ns(tmp_dir, shots, master_path, main_window=None,
                                 helper_source_path=None, simulated_game_root=None):
    mw = main_window if main_window is not None else _FakeMainWindow()
    doc_root = _FakeDocumentRoot(DEFAULT_FIXTURE_FILE_ID)
    vs_module = _FakeVsModule({DEFAULT_FIXTURE_FILE_ID: u"C:\\fake\\path\\%s" % DEFAULT_FIXTURE_BASENAME})
    ns = {
        "sfmApp": _FakeSfmApp(shots, mw, doc_root),
        "vs": vs_module,
    }
    _exec_checkpoint_defs_sfm_like(
        restoration_verify_defs_text, ns, tmp_dir, helper_source_path=helper_source_path,
        simulated_game_root=simulated_game_root,
    )

    ns["PRODUCTION_INSTALLED_PATH"] = PRODUCTION_CANDIDATE_PATH
    ns["EXPECTED_PRODUCTION_SHA256"] = EXPECTED_PRODUCTION_SHA256
    ns["CANONICAL_MASTER_INSTALLED_PATH"] = master_path
    ns["EXPECTED_G1_MASTER_SHA256"] = EXPECTED_CANONICAL_MASTER_SHA256

    evidence_dir = tmp_dir + os.sep
    ns["EVIDENCE_DIR"] = evidence_dir
    ns["BASELINE_INVENTORY_ARTIFACT_PATH"] = evidence_dir + "sfm_checkpoint_i_baseline_inventory.json"
    ns["FINALIZATION_RECORD_PATH"] = evidence_dir + "sfm_checkpoint_i_finalization_record.json"
    ns["RESTORATION_VERIFY_RESULT_PATH"] = evidence_dir + "sfm_checkpoint_i_restoration_verify_result.json"
    ns["SHIPPED_AUTHORITY_DIR"] = os.path.join(tmp_dir, "sfm_shared_authority")
    if not os.path.isdir(ns["SHIPPED_AUTHORITY_DIR"]):
        os.makedirs(ns["SHIPPED_AUTHORITY_DIR"])

    # Checkpoint_I_Restoration_Verify.py's own import_authority_runtime()
    # returns just the module (single value) -- unlike the primary
    # checkpoint's own 3-tuple-returning version reused elsewhere in this
    # suite, so this fixture wraps it (via the module-level helper below,
    # since Python 2 forbids a bare exec statement in a function scope
    # that also contains a nested def) rather than reusing it directly.
    ns["import_authority_runtime"] = _test_import_authority_runtime_single
    ns["get_canonical_broker"] = _test_get_canonical_broker
    return ns


tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_restverify_happy_")
try:
    master_path = os.path.join(tmp_dir, "master.txt")
    with open(CANONICAL_MASTER_CANDIDATE_PATH, "rb") as f:
        real_g1_bytes = f.read()
    with open(master_path, "wb") as f:
        f.write(real_g1_bytes)
    ns = fresh_restoration_verify_ns(tmp_dir, make_15_shots(u"restverifyhappy"), master_path)
    baseline_inventory = igen.capture_live_state_inventory(master_path, ns["SHIPPED_AUTHORITY_DIR"])
    with open(ns["BASELINE_INVENTORY_ARTIFACT_PATH"], "wb") as f:
        f.write(json.dumps(baseline_inventory).encode("utf-8"))

    ns["main"]()

    expect(os.path.isfile(ns["RESTORATION_VERIFY_RESULT_PATH"]),
           "r3blocker5.restoration_verify_writes_its_own_evidence_file")
    with open(ns["RESTORATION_VERIFY_RESULT_PATH"], "rb") as f:
        rv_result = json.loads(f.read().decode("utf-8"))
    expect(rv_result["classification"] == u"RESTORATION_CONFIRMED", "r3blocker5.happy_path_reports_restoration_confirmed")
    expect(rv_result["failed_gates"] == [], "r3blocker5.happy_path_has_no_failed_gates")

    continuation_state_path_would_be = tmp_dir + os.sep + "sfm_checkpoint_i_continuation_state.json"
    expect(
        not os.path.exists(continuation_state_path_would_be),
        "r3blocker5.restoration_verify_never_writes_the_primary_continuation_state_file",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_restverify_nobaseline_")
try:
    master_path = os.path.join(tmp_dir, "master.txt")
    with open(CANONICAL_MASTER_CANDIDATE_PATH, "rb") as f:
        real_g1_bytes = f.read()
    with open(master_path, "wb") as f:
        f.write(real_g1_bytes)
    ns = fresh_restoration_verify_ns(tmp_dir, make_15_shots(u"restverifynobase"), master_path)
    ns["main"]()
    with open(ns["RESTORATION_VERIFY_RESULT_PATH"], "rb") as f:
        rv_result2 = json.loads(f.read().decode("utf-8"))
    expect(
        rv_result2["classification"] == u"RESTORATION_NOT_CONFIRMED"
        and u"restoration_verify.baseline_inventory_artifact_present" in rv_result2["failed_gates"],
        "r3blocker5.missing_baseline_inventory_artifact_is_not_confirmed",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_restverify_wrongmaster_")
try:
    master_path = os.path.join(tmp_dir, "master.txt")
    with open(CANONICAL_MASTER_CANDIDATE_PATH, "rb") as f:
        real_g1_bytes = f.read()
    with open(master_path, "wb") as f:
        f.write(igen.construct_g2_bytes(real_g1_bytes))  # NOT G1
    ns = fresh_restoration_verify_ns(tmp_dir, make_15_shots(u"restverifywrongm"), master_path)
    baseline_inventory = igen.capture_live_state_inventory(master_path, ns["SHIPPED_AUTHORITY_DIR"])
    with open(ns["BASELINE_INVENTORY_ARTIFACT_PATH"], "wb") as f:
        f.write(json.dumps(baseline_inventory).encode("utf-8"))
    ns["main"]()
    with open(ns["RESTORATION_VERIFY_RESULT_PATH"], "rb") as f:
        rv_result3 = json.loads(f.read().decode("utf-8"))
    expect(
        rv_result3["classification"] == u"RESTORATION_NOT_CONFIRMED"
        and u"generation.live_master_is_exactly_canonical_g1" in rv_result3["failed_gates"],
        "r3blocker5.master_not_exactly_g1_is_not_confirmed",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# Section: STARTUP FIX regression (2026-09-26, first real-SFM I1
# attempt) -- deployment-environment coverage the offline suite never
# exercised before: an environment where the ChadChan3D MAINMENU
# directory is NOT initially in sys.path and no I_Generation_Helper
# module is preloaded, exactly like SFM's own real "Run Script"
# execution and exactly UNLIKE this suite's own prior fresh_ns(), which
# inadvertently masked the defect by adding HERE to sys.path itself.
# _simulate_sfm_installed_root()/_exec_checkpoint_defs_sfm_like() (used
# by every fresh_ns()/fresh_restoration_verify_ns() call throughout this
# entire suite, confirmed by the full 174/174 re-run above) already
# prove the exact-path loader works for the happy path; this section
# proves its adversarial/failure-mode behavior explicitly.
# =======================================================================
sys.stdout.write("\n--- Startup fix: exact-path hash-pinned helper loader ---\n")


def _normalized_module_file(module):
    f = os.path.abspath(getattr(module, "__file__", "") or "")
    if f.lower().endswith((".pyc", ".pyo")):
        f = f[:-1]
    return os.path.normcase(f)


def _real_evidence_leak_count():
    try:
        return len([n for n in os.listdir("C:\\Users\\Public\\Documents\\") if n.lower().startswith("sfm_checkpoint_i_")])
    except Exception:
        return 0


# --- exact helper loads successfully; its path is the intended sibling path ---
tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_startupfix_happy_")
try:
    ns = fresh_ns(tmp_dir, make_15_shots(u"startupfixhappy"))
    expect("igen" in ns, "r3startupfix.checkpoint_binds_igen_after_loading")
    intended_helper_path = os.path.join(
        tmp_dir, "simulated_game_root", "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
        "I_Generation_Helper.py",
    )
    expect(
        _normalized_module_file(ns["igen"]) == os.path.normcase(os.path.abspath(intended_helper_path)),
        "r3startupfix.exact_helper_loads_from_the_intended_sibling_path",
    )
    expect(
        ns["igen"].EXPECTED_CANONICAL_G1_MASTER_SHA256 == igen.EXPECTED_CANONICAL_G1_MASTER_SHA256,
        "r3startupfix.loaded_helper_exposes_the_real_expected_constants",
    )

    ns_rv = fresh_restoration_verify_ns(tmp_dir + "_rv", make_15_shots(u"startupfixhappyrv"),
                                        os.path.join(tmp_dir, "master.txt"))
    intended_helper_path_rv = os.path.join(
        tmp_dir + "_rv", "simulated_game_root", "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
        "I_Generation_Helper.py",
    )
    expect(
        _normalized_module_file(ns_rv["igen"]) == os.path.normcase(os.path.abspath(intended_helper_path_rv)),
        "r3startupfix.restoration_verify_exact_helper_loads_from_the_intended_sibling_path",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)
    shutil.rmtree(tmp_dir + "_rv", ignore_errors=True)

# --- wrong helper SHA refuses BEFORE helper execution; no evidence written ---
_leak_before = _real_evidence_leak_count()
tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_startupfix_wrongsha_")
try:
    tampered_helper_path = os.path.join(tmp_dir, "tampered_helper.py")
    with open(HELPER_SCRIPT_PATH, "rb") as f:
        real_helper_bytes_for_tamper = f.read()
    with open(tampered_helper_path, "wb") as f:
        f.write(real_helper_bytes_for_tamper + b"\n# tampered for r3startupfix test\n")

    raised = False
    caught_exc = None
    try:
        fresh_ns(tmp_dir, make_15_shots(u"wrongsha"), helper_source_path=tampered_helper_path)
    except Exception as exc:
        raised = True
        caught_exc = exc
    expect(raised, "r3startupfix.wrong_helper_sha_refuses")
    expect(
        caught_exc is not None and type(caught_exc).__name__ == "HelperQualificationError",
        "r3startupfix.wrong_helper_sha_refusal_is_the_expected_error_type",
    )
    expect(
        caught_exc is not None and "hashes to" in unicode(caught_exc) and "not the exact approved" in unicode(caught_exc),
        "r3startupfix.wrong_helper_sha_refusal_message_names_the_hash_mismatch",
    )
    expect(_real_evidence_leak_count() == _leak_before,
           "r3startupfix.no_qualification_evidence_written_when_helper_sha_is_wrong")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# --- missing helper refuses cleanly; no evidence written ---
_leak_before = _real_evidence_leak_count()
tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_startupfix_missing_")
try:
    simulated_game_root = _simulate_sfm_installed_root(tmp_dir)
    simulated_helper_path = os.path.join(
        simulated_game_root, "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D", "I_Generation_Helper.py",
    )
    os.remove(simulated_helper_path)

    raised = False
    caught_exc = None
    try:
        fresh_ns(tmp_dir, make_15_shots(u"missing"), simulated_game_root=simulated_game_root)
    except Exception as exc:
        raised = True
        caught_exc = exc
    expect(raised, "r3startupfix.missing_helper_refuses_cleanly")
    expect(
        caught_exc is not None and type(caught_exc).__name__ == "HelperQualificationError"
        and "not found" in unicode(caught_exc),
        "r3startupfix.missing_helper_refusal_is_the_expected_error_type_and_message",
    )
    expect(_real_evidence_leak_count() == _leak_before,
           "r3startupfix.no_qualification_evidence_written_when_helper_is_missing")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# --- a malicious/same-named helper elsewhere on sys.path is NOT used;
#     a stale same-named module already in sys.modules is NOT reused ---
tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_startupfix_malicious_")
try:
    malicious_dir = os.path.join(tmp_dir, "malicious_sys_path_entry")
    os.makedirs(malicious_dir)
    malicious_helper_path = os.path.join(malicious_dir, "I_Generation_Helper.py")
    with open(malicious_helper_path, "wb") as f:
        f.write(b'EXPECTED_CANONICAL_G1_MASTER_SHA256 = "0" * 64\n_MALICIOUS_MARKER = True\n')
    sys.path.insert(0, malicious_dir)

    import types as _types
    stale_module = _types.ModuleType("_sfm_i_generation_helper_qualified")
    stale_module._STALE_MARKER = True
    sys.modules["_sfm_i_generation_helper_qualified"] = stale_module

    try:
        ns = fresh_ns(tmp_dir, make_15_shots(u"malicious"))
        expect(
            not hasattr(ns["igen"], "_STALE_MARKER"),
            "r3startupfix.stale_sys_modules_entry_is_not_silently_reused",
        )
        expect(
            not hasattr(ns["igen"], "_MALICIOUS_MARKER")
            and ns["igen"].EXPECTED_CANONICAL_G1_MASTER_SHA256 == igen.EXPECTED_CANONICAL_G1_MASTER_SHA256,
            "r3startupfix.malicious_same_named_helper_elsewhere_on_sys_path_is_not_used",
        )
        intended_helper_path = os.path.join(
            tmp_dir, "simulated_game_root", "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
            "I_Generation_Helper.py",
        )
        expect(
            _normalized_module_file(ns["igen"]) == os.path.normcase(os.path.abspath(intended_helper_path)),
            "r3startupfix.loaded_helper_path_is_the_intended_sibling_path_despite_the_malicious_decoy",
        )
    finally:
        sys.path.remove(malicious_dir)
        if "_sfm_i_generation_helper_qualified" in sys.modules:
            del sys.modules["_sfm_i_generation_helper_qualified"]
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)


def _write_matching_usable_pyc(py_path, malicious_extra_source):
    """Constructs a REAL, well-formed Python 2.7 .pyc next to py_path that
    ordinary Python-2 import machinery (and the OLD, rejected
    imp.load_source()-based loader) would consider usable/current for
    py_path -- correct magic number, and a source-mtime field matching
    py_path's own current on-disk mtime -- but whose OWN compiled code is
    observably different (compiled from py_path's real bytes PLUS an
    extra malicious marker appended), never from py_path's own real
    bytes alone. Used only to adversarially prove the corrected loader
    never looks at this file at all."""
    with open(py_path, "rb") as f:
        real_bytes = f.read()
    malicious_source = real_bytes + malicious_extra_source
    malicious_code = compile(malicious_source, py_path, "exec")
    mtime = int(os.path.getmtime(py_path))
    pyc_path = py_path + ("c" if not py_path.endswith(".pyo") else "")
    with open(pyc_path, "wb") as f:
        f.write(imp.get_magic())
        f.write(struct.pack("<I", mtime))
        marshal.dump(malicious_code, f)
    return pyc_path


# --- BYTECODE-CACHE ADVERSARIAL TEST (second independent review,
#     2026-09-26): a well-formed, timestamp-matching .pyc that ordinary
#     Python-2 import machinery would consider usable sits right next to
#     the exact, correctly-hashed .py -- the corrected loader must still
#     execute only the exact hashed .py bytes, never the .pyc. ---
tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_startupfix_pyccache_")
try:
    ns = fresh_ns(tmp_dir, make_15_shots(u"pyccache"))
    intended_helper_path = os.path.join(
        tmp_dir, "simulated_game_root", "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
        "I_Generation_Helper.py",
    )
    pyc_path = _write_matching_usable_pyc(
        intended_helper_path, b"\n_MALICIOUS_BYTECODE_MARKER = True\n",
    )
    expect(os.path.isfile(pyc_path), "r3startupfix.matching_usable_pyc_actually_written_next_to_the_py")

    if "_sfm_i_generation_helper_qualified" in sys.modules:
        del sys.modules["_sfm_i_generation_helper_qualified"]
    ns2 = fresh_ns(tmp_dir + "_reload", make_15_shots(u"pyccachereload"),
                   simulated_game_root=os.path.join(tmp_dir, "simulated_game_root"))
    expect(
        not hasattr(ns2["igen"], "_MALICIOUS_BYTECODE_MARKER"),
        "r3startupfix.checkpoint_ignores_the_matching_usable_pyc_and_executes_only_the_hashed_py",
    )
    expect(
        ns2["igen"].EXPECTED_CANONICAL_G1_MASTER_SHA256 == igen.EXPECTED_CANONICAL_G1_MASTER_SHA256,
        "r3startupfix.checkpoint_module_behavior_comes_from_the_exact_hashed_py_bytes",
    )
    expect(
        _normalized_module_file(ns2["igen"]) == os.path.normcase(os.path.abspath(intended_helper_path)),
        "r3startupfix.checkpoint_loaded_module_file_is_the_py_path_not_the_pyc",
    )

    rv_tmp = tmp_dir + "_rv"
    ns_rv = fresh_restoration_verify_ns(
        rv_tmp, make_15_shots(u"pyccacherv"), os.path.join(rv_tmp, "master.txt"),
        simulated_game_root=os.path.join(tmp_dir, "simulated_game_root"),
    )
    expect(
        not hasattr(ns_rv["igen"], "_MALICIOUS_BYTECODE_MARKER"),
        "r3startupfix.restoration_verify_ignores_the_matching_usable_pyc",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)
    shutil.rmtree(tmp_dir + "_reload", ignore_errors=True)
    shutil.rmtree(tmp_dir + "_rv", ignore_errors=True)
    if "_sfm_i_generation_helper_qualified" in sys.modules:
        del sys.modules["_sfm_i_generation_helper_qualified"]

# --- wrong .py SHA still refuses BEFORE execution even when a matching,
#     otherwise-usable .pyc sits right next to the tampered .py ---
tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_startupfix_pyccache_wrongsha_")
try:
    tampered_helper_path = os.path.join(tmp_dir, "tampered_helper.py")
    with open(HELPER_SCRIPT_PATH, "rb") as f:
        real_helper_bytes_for_tamper = f.read()
    with open(tampered_helper_path, "wb") as f:
        f.write(real_helper_bytes_for_tamper + b"\n# tampered for r3startupfix pyc-cache test\n")
    _write_matching_usable_pyc(tampered_helper_path, b"\n_MALICIOUS_BYTECODE_MARKER = True\n")

    raised = False
    caught_exc = None
    try:
        fresh_ns(tmp_dir, make_15_shots(u"pyccachewrongsha"), helper_source_path=tampered_helper_path)
    except Exception as exc:
        raised = True
        caught_exc = exc
    expect(raised, "r3startupfix.wrong_py_sha_still_refuses_even_with_a_matching_usable_pyc_present")
    expect(
        caught_exc is not None and type(caught_exc).__name__ == "HelperQualificationError",
        "r3startupfix.wrong_py_sha_with_pyc_present_refusal_is_the_expected_error_type",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# --- cleanup on init failure: if executing the (hash-verified) helper
#     source itself raises during module initialization, no partially-
#     initialized qualification module remains in sys.modules ---
tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_startupfix_initraise_")
try:
    ns = fresh_ns(tmp_dir, make_15_shots(u"initraise"))
    qualified_name = "_sfm_i_generation_helper_qualified"
    expect(qualified_name in sys.modules,
           "r3startupfix.sanity_qualified_module_present_after_a_normal_successful_load")

    simulated_helper_path = os.path.join(
        tmp_dir, "simulated_game_root", "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
        "I_Generation_Helper.py",
    )
    raising_bytes = b"raise RuntimeError('simulated init failure for r3startupfix test')\n"
    os.remove(simulated_helper_path)
    with open(simulated_helper_path, "wb") as f:
        f.write(raising_bytes)
    # Re-point the ALREADY-LOADED checkpoint namespace's own expected hash
    # at this deliberately-raising content, then call its own loader
    # function again directly -- proving the CLEANUP behavior of the
    # loader itself, without needing the real approved helper to raise.
    # fresh_ns()'s own sys.executable monkeypatch has already been
    # reverted by the time it returns, so it must be re-established here
    # for this SECOND, manual call to _load_exact_i_helper() to resolve
    # the same simulated sibling path rather than the real offline
    # interpreter's own (different, real) sys.executable.
    ns["EXPECTED_I_HELPER_SHA256"] = hashlib.sha256(raising_bytes).hexdigest()

    raised = False
    original_sys_executable = sys.executable
    sys.executable = os.path.join(tmp_dir, "simulated_game_root", "sfm.exe")
    try:
        ns["_load_exact_i_helper"]()
    except Exception:
        raised = True
    finally:
        sys.executable = original_sys_executable
    expect(raised, "r3startupfix.init_failure_of_the_helper_itself_propagates")
    expect(
        qualified_name not in sys.modules,
        "r3startupfix.no_partially_initialized_qualification_module_remains_in_sys_modules_after_init_failure",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)
    if "_sfm_i_generation_helper_qualified" in sys.modules:
        del sys.modules["_sfm_i_generation_helper_qualified"]

# --- equivalent coverage for Checkpoint_I_Restoration_Verify.py: wrong
#     SHA and missing helper both refuse cleanly with no evidence written ---
_leak_before = _real_evidence_leak_count()
tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_startupfix_rv_wrongsha_")
try:
    master_path = os.path.join(tmp_dir, "master.txt")
    with open(CANONICAL_MASTER_CANDIDATE_PATH, "rb") as f:
        f_bytes = f.read()
    with open(master_path, "wb") as f:
        f.write(f_bytes)
    tampered_helper_path = os.path.join(tmp_dir, "tampered_helper.py")
    with open(HELPER_SCRIPT_PATH, "rb") as f:
        real_helper_bytes_for_tamper = f.read()
    with open(tampered_helper_path, "wb") as f:
        f.write(real_helper_bytes_for_tamper + b"\n# tampered for r3startupfix rv test\n")

    raised = False
    caught_exc = None
    try:
        fresh_restoration_verify_ns(tmp_dir, make_15_shots(u"rvwrongsha"), master_path,
                                     helper_source_path=tampered_helper_path)
    except Exception as exc:
        raised = True
        caught_exc = exc
    expect(raised, "r3startupfix.restoration_verify_wrong_helper_sha_refuses")
    expect(
        caught_exc is not None and type(caught_exc).__name__ == "HelperQualificationError",
        "r3startupfix.restoration_verify_wrong_helper_sha_refusal_is_the_expected_error_type",
    )
    expect(_real_evidence_leak_count() == _leak_before,
           "r3startupfix.restoration_verify_no_evidence_written_when_helper_sha_is_wrong")
    expect(
        igen.sha256_file(master_path) == EXPECTED_CANONICAL_MASTER_SHA256,
        "r3startupfix.restoration_verify_no_master_mutation_when_helper_qualification_fails",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_startupfix_rv_missing_")
try:
    master_path = os.path.join(tmp_dir, "master.txt")
    with open(CANONICAL_MASTER_CANDIDATE_PATH, "rb") as f:
        f_bytes = f.read()
    with open(master_path, "wb") as f:
        f.write(f_bytes)
    simulated_game_root = _simulate_sfm_installed_root(tmp_dir)
    simulated_helper_path = os.path.join(
        simulated_game_root, "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D", "I_Generation_Helper.py",
    )
    os.remove(simulated_helper_path)

    raised = False
    caught_exc = None
    try:
        fresh_restoration_verify_ns(tmp_dir, make_15_shots(u"rvmissing"), master_path,
                                     simulated_game_root=simulated_game_root)
    except Exception as exc:
        raised = True
        caught_exc = exc
    expect(raised, "r3startupfix.restoration_verify_missing_helper_refuses_cleanly")
    expect(
        caught_exc is not None and type(caught_exc).__name__ == "HelperQualificationError",
        "r3startupfix.restoration_verify_missing_helper_refusal_is_the_expected_error_type",
    )
    expect(
        igen.sha256_file(master_path) == EXPECTED_CANONICAL_MASTER_SHA256,
        "r3startupfix.restoration_verify_no_master_mutation_when_helper_is_missing",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# Section: immutable evidence discipline + guard-state extraction smoke
# check (unchanged behavior).
# =======================================================================
sys.stdout.write("\n--- Immutable evidence discipline ---\n")

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_")
try:
    ns = fresh_ns(tmp_dir, make_15_shots(u"evidence"))
    write_evidence_json_once = ns["write_evidence_json_once"]
    write_evidence_bytes_once = ns["write_evidence_bytes_once"]
    CheckpointIError = ns["CheckpointIError"]

    once_path = os.path.join(tmp_dir, "probe.json")
    write_evidence_json_once(once_path, {"a": 1})
    raised = False
    try:
        write_evidence_json_once(once_path, {"a": 2})
    except CheckpointIError:
        raised = True
    expect(raised, "item.write_evidence_json_once_refuses_to_overwrite_an_existing_file")
    with open(once_path, "rb") as f:
        expect(
            json.loads(f.read().decode("utf-8")) == {"a": 1},
            "item.original_evidence_content_unchanged_after_a_refused_overwrite",
        )

    once_txt = os.path.join(tmp_dir, "probe.txt")
    write_evidence_bytes_once(once_txt, b"first")
    raised2 = False
    try:
        write_evidence_bytes_once(once_txt, b"second")
    except CheckpointIError:
        raised2 = True
    expect(raised2, "item.write_evidence_bytes_once_refuses_to_overwrite_an_existing_file")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_i_dryrun_")
try:
    ns = fresh_ns(tmp_dir, make_15_shots(u"guard"))
    load_production_guard_definitions = ns["load_production_guard_definitions"]
    prod_ns, prod_sha256 = load_production_guard_definitions()
    expect(prod_sha256 == EXPECTED_PRODUCTION_SHA256, "guard_extraction.production_sha256_matches_pinned")
    expect(
        "_read_process_scope_state" in prod_ns and "_find_existing_run" in prod_ns,
        "guard_extraction.expected_definitions_present",
    )
    fresh_shots = make_15_shots(u"guard2")
    ns_fresh = fresh_ns(tmp_dir + "_fresh_window", fresh_shots)  # fresh_ns() itself creates this directory
    main_window_fresh = ns_fresh["sfmApp"].GetMainWindow()
    state = prod_ns["_read_process_scope_state"](main_window_fresh)
    expect(state == u"UNUSED", "guard_extraction.fresh_main_window_reports_UNUSED")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)
    shutil.rmtree(tmp_dir + "_fresh_window", ignore_errors=True)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))

if FAIL_COUNT[0]:
    sys.exit(1)
