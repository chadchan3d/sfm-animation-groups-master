# -*- coding: utf-8 -*-
"""
Checkpoint I (Master Generation Replacement) -- real-SFM qualification of
roadmap item I, specifically and ONLY:

    generation replacement -- the Master TXT changing BETWEEN commands
    (I1), and the invariant that one ACTIVE command may never straddle
    two generations (I2).

Governing invariant under test:
    One command = one Master generation. A later command may adopt a
    later generation; an active command may not.

This is explicitly NOT another later-vocabulary test (that is G, PASS/
CLOSED). I1 deliberately uses the SAME shot (shot9) for both commands so
vocabulary is never a variable -- only the Master generation changes.

**Prepared 2026-09-25. CORRECTION ROUND 1 applied 2026-09-25 (independent
review, 11 blockers). NOT yet run against real SFM.**

CORRECTION ROUND 1 summary (full detail in INSTRUCTIONS.md and the
review bundle's own CHANGE_INVENTORY.txt):
  - BLOCKER 1 (atomic Master replacement) and BLOCKER 2 (narrowed live-
    mutation surface) are fixed in I_Generation_Helper.py, imported here
    unchanged -- this file's own I2 wrapper now calls the new, narrow
    igen.perform_g2_to_g1_restoration() instead of the old generic
    restore_g1_over_g2().
  - BLOCKER 3: I2 arming is no longer a synchronous, humanly-impossible
    "invoke checkpoint again before target 1" step. It is now a
    retained, bounded, ~25ms-interval Qt timer/observer
    (_I2PrearmObserver) installed BEFORE the operator ever starts the
    command (snapshot i2_01_prearm), which detects the newly-created
    production run instance, mechanically validates it is exactly the
    expected run (master_hash==G2, scope==Selected shot3 alone, zero
    targets completed, zero native attempts so far, wrapper not already
    installed), installs the SAME one-shot contextualizer_resolve_
    resume_target wrapper this project's own review already accepted,
    and persists immutable arming evidence BEFORE the operator ever
    touches the UI. Snapshot i2_02_verify now REQUIRES that persisted
    evidence (never reasoning) to prove the wrapper was installed before
    target 1.
  - BLOCKER 4: every consequential stage (i1_02, i1_03, i1_04, i2_00,
    i2_02) now re-gates identities/guard/run-lock/live-Master-generation
    directly, never relying on "baseline passed earlier" for a mutable
    fact.
  - BLOCKER 5: no eval() anywhere. The G1 cache key is reconstructed
    directly from its own stored components (G1 sha, shot9 fold set,
    consumer kind), never from a repr() string.
  - BLOCKER 6: i1_03's "G2 ready" gate now consumes and mechanically
    verifies the EXACT immutable G2 publication record the external,
    repo-side I_Generation_Publisher.py writes (generation basename,
    exact sidecar SHA, exact manifest SHA, manifest fields) -- "any
    sfm_master_*.sfmsidecar exists" is never sufficient authority
    readiness again.
  - BLOCKER 8: the final rollup's own final_i_verdict is now
    I_RUNTIME_PASS_RESTORATION_REQUIRED immediately after I1+I2 succeed,
    and only becomes I_PASS after a NEW, final, read-only snapshot
    (i_08_finalize_verify) independently confirms the external
    finalizer's own restoration record reports exact_match=True against
    the pre-I baseline inventory.

**CORRECTION ROUND 2 applied 2026-09-25 (second independent review, 8
blockers). NOT yet run against real SFM.** Full detail in INSTRUCTIONS.md
and the round-2 review bundle's own CHANGE_INVENTORY.txt; summary:
  - R2 BLOCKER 1: round 1's own I_Generation_Publisher.py never actually
    switched the live Master (INSTRUCTIONS.md's claim that publish-g2
    did so was simply wrong). The publisher is now an explicit TWO-PHASE
    design -- Phase A (construct + plan + publish G2 AUTHORITY, never
    touches the live Master) and Phase B (activate_g2_master(), the ONLY
    function that ever calls perform_g1_to_g2_replacement()). I1-03 now
    requires BOTH an exact valid G2 publication record AND an exact
    valid G2 Master ACTIVATION record (_validate_g2_activation_record(),
    new).
  - R2 BLOCKER 2: the operator/caller can no longer supply a manually
    prepared --g2-source file for real qualification use; Phase A's
    construct_and_write_g2_source() constructs G2 bytes itself, from
    exact canonical G1 bytes.
  - R2 BLOCKER 3: _snapshot_i2_01_prearm() now calls
    _common_identity_gates() (round 1 did not) plus every itemized I2
    precondition -- both evidence-chain records, zero open providers/
    leases, and a HASH-VERIFIED (not merely existence-checked) G1
    backup -- before the observer is ever installed.
  - R2 BLOCKER 4: _PREARM_TIMEOUT_MS raised from round 1's humanly-tight
    5000ms to 60000ms; poll cadence (25ms) unchanged.
  - R2 BLOCKER 5: every live-mutation/finalization operation now binds
    its Master/authority paths to the exact paths the I1 baseline
    inventory recorded (igen.path_matches_baseline()) before trusting
    them for anything -- an arbitrary/wrong path is never sufficient
    authorization by itself. Applied in I_Generation_Publisher.py's
    activate_g2_master()/finalize_restoration() and in this checkpoint's
    own I2 wrapper (_install_i2_wrapper()).
  - R2 BLOCKER 6: the I1 baseline inventory is now ALSO written as its
    own standalone, immutable, write-once artifact
    (sfm_checkpoint_i_baseline_inventory.json), consumed directly by
    i_08_finalize_verify -- never only embedded in Snapshot 01 or this
    process's own in-memory continuation state.
  - R2 BLOCKER 7: I_Generation_Publisher.py's write_g2_plan_record()
    writes an immutable PLAN record, computed entirely from the
    already-accepted read-only check_only() operation, BEFORE the first
    live authority mutation -- so a failure during publication never
    leaves recovery dependent on a record that had not yet been created.
  - R2 BLOCKER 8: finalize_restoration() now independently RE-VERIFIES
    the publication record (re-derived G1+LF hash, safe basename, exact
    on-disk sidecar SHA, recorded semantic parity) immediately before it
    is ever allowed to authorize a sidecar deletion -- a tampered or
    wrong record can no longer authorize deletion merely because the
    file exists.

**CORRECTION ROUND 3 applied 2026-09-25 (third independent review, 5
blockers + 1 hardening). NOT yet run against real SFM.** Full detail in
INSTRUCTIONS.md; summary of what touches THIS file:
  - R3 BLOCKER 1 (I_Generation_Publisher.py): Phase A publication is
    itself a live mutation (writes a sidecar, replaces manifest.json) --
    now also baseline-path-bound before publish_generation() ever runs.
  - R3 BLOCKER 2/3 (I_Generation_Publisher.py): finalize_restoration()
    can now recover using the G2 plan record alone (never REQUIRES the
    publication record), and independently re-derives G2 identity as
    G1+LF rather than trusting publication_record's own claimed hash.
  - R3 BLOCKER 4 (I_Generation_Helper.py): its own CLI no longer exposes
    any mutation subcommand at all -- I_Generation_Publisher.py's
    activate_g2_master() is now literally the only external G1->G2
    activation surface.
  - R3 BLOCKER 5 (NEW FILE, Checkpoint_I_Restoration_Verify.py): a
    separate, read-only, one-shot recovery-verification tool for an
    EARLY-ABORTED I1/I2 campaign that never naturally reaches this
    file's own scheduled i_08_finalize_verify snapshot. Never advances
    or depends on this file's own SNAPSHOT_SCHEDULE/continuation state.
  - R3 HARDENING (this file): _validate_g2_publication_record() now also
    mechanically requires the record's own recorded semantic_parity to
    report all_parity_checks_pass=True (never merely assumed), and
    corroborates the active manifest's current on-disk SHA-256 against
    the record's own manifest_sha256_after_publication.

This checkpoint has THREE distinct roles (not a pure read-only observer
like Checkpoint_G_Later_Vocabulary.py -- I2's prearm/injection steps are
deliberate, narrowly-targeted instruments, called out as such):

  I1 (snapshots i1_01..i1_04): a pure READ-ONLY OBSERVER. It never
  invokes the Normalizer, never invokes native Rebuild, never mutates
  the scene, never opens a provider, never saves. The G1<->G2 Master
  swap and sidecar publish/finalize between commands is performed by a
  SEPARATE, external, ordinary Python 3 invocation of the repo-side-only
  I_Generation_Publisher.py, outside SFM, while SFM sits idle -- never
  by this script.

  I2 prearm (i2_00, i2_01): i2_00 is a pure read-only baseline. i2_01
  ("prearm") is a narrowly-scoped, one-shot INSTALLER: it arms a
  retained Qt timer/observer (never blocks, never busy-waits) that will,
  asynchronously and entirely in the background, locate the live
  command instance the MOMENT it appears and mechanically validate it
  before wrapping exactly one of its bound methods.

  I2 verify (i2_02) and the final restoration check (i_08) are again
  pure read-only observers, run only after the relevant real-world
  action (the command finishing; the external restoration) has already
  happened.

Architecture facts this design relies on (independently verified by
direct source inspection against the pinned production candidate,
Rebuild_Control_Groups_Normalizer.py, SHA-256
1f4ec5a26605aa90380eb0532fec3915d2cc24a3a20473ed70d57198bd995db7):
  - self.master_hash is set ONCE, inside derive_paths() (called
    synchronously from start(), lines ~9878-9886, ~13949), well before
    start() eventually reaches activate_next_shot() and returns control
    to Qt -- so by the time ANY Qt timer could possibly fire, master_hash
    is already set.
  - DEFER_MS = 100 (line 136) is the delay used to schedule the FIRST
    shot's own deferred entry callback from start()/activate_next_shot();
    CONTEXTUALIZER_TARGET_CALLBACK_DEFER_MS = 0 (line 137) is the delay
    used to schedule every LATER target's resume callback. start() itself
    runs entirely synchronously (no Qt yield) and is substantially longer
    than one ~25ms observer poll interval, so a retained observer polling
    every ~25ms, started BEFORE the operator invokes the command, is
    already overdue (has already had multiple poll opportunities) by the
    time control first returns to Qt and the 100ms first-target timer
    even begins counting down -- giving a realistic, non-racing
    opportunity to arm before target 1, independently PROVEN per real run
    via the observer's own persisted evidence (see BLOCKER 3 above), never
    claimed from timing reasoning alone.
  - RebuildControlGroupsProductionRun.__init__ (lines ~9464-9520)
    initializes self.current_target_index = 0, self.telemetry_native_
    attempts = 0, self.total_native_rebuilt = 0, self.scope_mode,
    self.scope_shots, self.requested_scope_class, ALL synchronously at
    construction time, and self.setObjectName(RUN_LOCK_NAME) -- so a
    newly-detected instance's exact scope/progress can be validated
    immediately, before any target has run.
  - contextualizer_resolve_resume_target(self, record, target) calls
    self.assert_master_stable() as its first action, and is called
    exactly once per target (including target 1) from
    process_current_target() (lines ~12722-12727, ~12922-12957) -- never
    skipped, never batched.
  - process_current_target()'s own try/except (lines ~12926-13034)
    catches any exception raised inside it and calls self.abort(
    "Exception during CONTEXTUALIZER target-level Qt callback
    transaction: %r" % exc), eventually reaching final_report(False) --
    production itself detects and fails closed; this checkpoint only
    observes the resulting log.
  - the per-target native-Rebuild window logs "...phase=PRE_NATIVE..."
    then "NATIVE_REBUILD_RETURNED = PASS" (lines ~11882-11937) -- each
    exactly once per target that reaches it.
  - the live Master SHA-256 is logged once per command: "live Master
    SHA256=%s" % self.master_hash (line ~13978).
  - the broker's own invalidate_generation() (view_cache.py) marks stale
    every cached view of a superseded generation without evicting it; a
    stale view becomes unreachable via broker.cached_view() once a newer
    generation is acquired.
  - the official sidecar compiler/publisher (tools/sfm_master_sidecar/
    publisher.py, Python 3 only, imported ONLY from the repo-side-only
    I_Generation_Publisher.py -- never from this file) is the same real,
    accepted code used to publish the live G1 generation originally.

Fixture identity, guard-state extraction, and evidence-file discipline
all reuse the SAME exact line-range-extraction and write_evidence_*_once
patterns already qualified in Checkpoint_G_Later_Vocabulary.py.
"""
import hashlib
import imp
import json
import os
import sys
import time

from PySide import QtCore

# ----------------------------------------------------------------------
# STARTUP FIX (2026-09-26, first real-SFM I1 attempt): the deployed
# checkpoint's own plain top-level `import I_Generation_Helper as igen`
# raised ImportError before any qualification evidence could ever be
# written -- SFM's own "Run Script" execution does NOT add the script's
# own directory to sys.path (unlike an ordinary `python script.py`
# invocation), so the sibling helper module was simply not importable by
# name at that point. This is a harness startup failure, never an I1
# result: zero evidence files were produced (not even snapshot 1), the
# canonical Master remained G1, and the authority namespace was never
# touched. The offline test suite's own fresh_ns() had inadvertently
# masked this defect the whole time, because it inserts this directory
# into sys.path itself before exec()-ing the checkpoint's own
# definitions text -- something the real SFM environment never does.
#
# Fix: an EXACT-PATH, HASH-PINNED sibling-helper loader. Never a plain
# `import` -- that could otherwise silently resolve a same-named module
# already sitting in sys.modules or found via some other sys.path entry.
# Derives the exact expected sibling helper path from the same
# installed-SFM-root logic already used elsewhere in this file, requires
# that exact file to exist, SHA-256's its actual on-disk bytes BEFORE
# loading, requires the exact approved EXPECTED_I_HELPER_SHA256, then
# COMPILES AND EXECUTES THOSE EXACT ALREADY-HASHED BYTES DIRECTLY (never
# imp.load_source() -- a second independent review correctly rejected an
# earlier version of this loader that used it, since Python 2.7's
# imp.load_source() may substitute a matching sibling .pyc/.pyo for the
# .py file it was given, which would have meant the hash check proved
# the .py bytes on disk without strictly proving those were the bytes
# actually executed), and verifies the loaded module's own __file__
# resolves to the intended path before ever binding it as `igen`. No
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

# ----------------------------------------------------------------------
# Governing identities this checkpoint is pinned against.
# ----------------------------------------------------------------------
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

# Exact source line ranges (1-indexed, inclusive), pinned against the
# SHA-256 above -- identical to, and independently re-verified from, the
# ranges Checkpoint_G_Later_Vocabulary.py's own script uses.
RUN_LOCK_NAME_RANGE = (158, 160)
CONSTANTS_MARKER_NAMES_RANGE = (196, 212)
OUTPUT_PATH_RANGE = (214, 217)
MARKER_ERROR_CLASS_RANGE = (847, 857)
TO_UNICODE_RANGE = (899, 909)
FIND_EXISTING_RUN_RANGE = (5654, 5673)
FIND_NAMED_MARKER_RANGE = (5676, 5718)
PROCESS_STATE_CONSTANTS_RANGE = (5775, 5780)
READ_PROCESS_SCOPE_STATE_RANGE = (5783, 5825)

CONSUMER_KIND = u"normalizer_compat"
I1_SHOT_NAME = u"shot9"
I2_SHOT_NAME = u"shot3"
EXPECTED_I2_TARGET_COUNT = 2

EXPECTED_FIXTURE_FILENAME = u"F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx"
FORBIDDEN_ORIGINAL_FIXTURE_FILENAME = u"testscripts.dmx"
EXPECTED_PROJECT_SHOT_COUNT = 15

_PREARM_POLL_INTERVAL_MS = 25
# CORRECTION ROUND 2, R2 BLOCKER 4: round 1's 5000ms bounded window
# required the operator to navigate the SFM menu and scope dialog within
# five seconds. Increased to a realistic 60s bounded human-action
# window; poll cadence is unchanged. The qualification evidence still
# proves the wrapper armed strictly before target 1 -- the longer
# waiting window does not weaken that proof, it only bounds how long the
# observer is willing to wait for the operator to act.
_PREARM_TIMEOUT_MS = 60000

EVIDENCE_DIR = "C:\\Users\\Public\\Documents\\"
CONTINUATION_STATE_PATH = EVIDENCE_DIR + "sfm_checkpoint_i_continuation_state.json"
FINAL_RESULT_PATH = EVIDENCE_DIR + "sfm_checkpoint_i_final_result.json"
FINAL_SUMMARY_PATH = EVIDENCE_DIR + "sfm_checkpoint_i_final_summary.txt"
G1_SOURCE_BYTES_BACKUP_PATH = EVIDENCE_DIR + "sfm_checkpoint_i_g1_source_bytes.dat"
I2_INJECTION_RECORD_PATH = EVIDENCE_DIR + "sfm_checkpoint_i_i2_injection_record.json"
I2_PREARM_RESULT_PATH = EVIDENCE_DIR + "sfm_checkpoint_i_i2_prearm_result.json"
G2_PUBLICATION_RECORD_PATH = EVIDENCE_DIR + "sfm_checkpoint_i_g2_publication_record.json"
# R2 BLOCKER 1/3: the separate, explicit Phase B Master-ACTIVATION
# record (distinct from the Phase A publication record above) --
# proves the live Master was actually switched to G2 through the
# corrected atomic path, never merely that a sidecar/publication record
# exists.
G2_ACTIVATION_RECORD_PATH = EVIDENCE_DIR + "sfm_checkpoint_i_g2_activation_record.json"
FINALIZATION_RECORD_PATH = EVIDENCE_DIR + "sfm_checkpoint_i_finalization_record.json"
# R2 BLOCKER 6: the I1 baseline inventory as its OWN standalone,
# immutable, write-once evidence artifact -- so recovery/finalization
# never requires the operator to manually extract nested JSON from
# Snapshot 01.
BASELINE_INVENTORY_ARTIFACT_PATH = EVIDENCE_DIR + "sfm_checkpoint_i_baseline_inventory.json"

SNAPSHOT_SCHEDULE = [
    (u"i1_01_baseline_g1", u"UNUSED"),
    (u"i1_02_after_g1_command", u"SELECTED_USED"),
    (u"i1_03_g2_ready", u"SELECTED_USED"),
    (u"i1_04_after_g2_command", u"SELECTED_USED"),
    (u"i2_00_baseline_g2", u"UNUSED"),
    (u"i2_01_prearm", u"UNUSED"),
    (u"i2_02_verify", u"SELECTED_USED"),
    (u"i_08_finalize_verify", u"UNUSED"),
]
RUN_LOG_LABELS = [
    u"i1_g1_shot9",
    u"i1_g2_shot9",
    u"i2_g2_shot3",
]

_RETAINED_PREARM_OBSERVER = None  # module-level keepalive, belt-and-suspenders


class CheckpointIError(Exception):
    pass


# ----------------------------------------------------------------------
# Atomic-write primitives for THIS checkpoint's own evidence files --
# verbatim pattern reused from Checkpoint_G_Later_Vocabulary.py. (These
# are NOT the live-Master mutation primitives -- those now live
# exclusively in I_Generation_Helper.py, corrected per BLOCKER 1.)
# ----------------------------------------------------------------------
def write_json_rollup(path, obj):
    tmp_path = path + ".tmp"
    try:
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
        if os.path.exists(path):
            os.remove(path)
        os.rename(tmp_path, path)
        return True, None, reparsed
    except Exception as exc:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        return False, u"%r" % (exc,), None


def write_text_rollup(path, text_bytes):
    tmp_path = path + ".tmp"
    try:
        fp = open(tmp_path, "wb")
        try:
            fp.write(text_bytes)
            fp.flush()
            os.fsync(fp.fileno())
        finally:
            fp.close()
        if os.path.exists(path):
            os.remove(path)
        os.rename(tmp_path, path)
        return True, None
    except Exception as exc:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        return False, u"%r" % (exc,)


def write_evidence_json_once(path, obj):
    if os.path.exists(path):
        raise CheckpointIError(
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
        raise CheckpointIError(
            "Refusing to overwrite existing evidence file (rename "
            "failed, target likely already exists): %r (%r)" % (path, exc)
        )
    return reparsed


def write_evidence_bytes_once(path, raw_bytes):
    if os.path.exists(path):
        raise CheckpointIError(
            "Refusing to overwrite existing evidence file: %r" % (path,)
        )
    tmp_path = path + ".tmp"
    fp = open(tmp_path, "wb")
    try:
        fp.write(raw_bytes)
        fp.flush()
        os.fsync(fp.fileno())
    finally:
        fp.close()
    try:
        os.rename(tmp_path, path)
    except Exception as exc:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise CheckpointIError(
            "Refusing to overwrite existing evidence file (rename "
            "failed, target likely already exists): %r (%r)" % (path, exc)
        )


write_evidence_text_once = write_evidence_bytes_once


def read_continuation_state():
    if not os.path.exists(CONTINUATION_STATE_PATH):
        return {
            "next_snapshot_index": 1,
            "next_run_index": 1,
            "last_known_log_sha256": None,
            "captured_snapshots": [],
            "captured_runs": [],
            "i1_baseline_pid": None,
            "i1_baseline_master_sha256": None,
            "i1_expected_g2_sha256": None,
            "i1_shot9_folds_sorted": None,
            "i1_baseline_provider_counters": None,
            "i1_baseline_diagnostics": None,
            "i1_baseline_inventory": None,
            "i1_g1_stage_provider_counters": None,
            "i1_g1_stage_diagnostics": None,
            "i1_g2_ready_provider_counters": None,
            "i1_g2_ready_diagnostics": None,
            "i2_baseline_pid": None,
            "i2_baseline_provider_counters": None,
            "i2_baseline_diagnostics": None,
            "i2_prearmed": False,
        }
    fp = open(CONTINUATION_STATE_PATH, "rb")
    try:
        raw = fp.read()
    finally:
        fp.close()
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise CheckpointIError(
            "continuation-state file is present but could not be "
            "parsed: %r -- refusing to guess." % (exc,)
        )
    for required_key in (
        "next_snapshot_index", "next_run_index", "last_known_log_sha256",
        "captured_snapshots", "captured_runs",
        "i1_baseline_pid", "i1_baseline_master_sha256", "i1_expected_g2_sha256",
        "i1_shot9_folds_sorted", "i1_baseline_provider_counters", "i1_baseline_diagnostics",
        "i1_baseline_inventory",
        "i1_g1_stage_provider_counters", "i1_g1_stage_diagnostics",
        "i1_g2_ready_provider_counters", "i1_g2_ready_diagnostics",
        "i2_baseline_pid", "i2_baseline_provider_counters", "i2_baseline_diagnostics", "i2_prearmed",
    ):
        if required_key not in parsed:
            raise CheckpointIError(
                "continuation-state file is present but missing expected "
                "key %r -- refusing to guess." % (required_key,)
            )
    return parsed


# ----------------------------------------------------------------------
# Production guard-state extraction (verbatim technique reused from
# Checkpoint_G_Later_Vocabulary.py / checkpoint_process_attempt_guard).
# ----------------------------------------------------------------------
def _extract_lines(raw_bytes, range_tuple):
    start, end = range_tuple
    lines = raw_bytes.split("\n")
    return "\n".join(lines[start - 1:end])


def load_production_guard_definitions():
    fp = open(PRODUCTION_INSTALLED_PATH, "rb")
    try:
        raw_bytes = fp.read()
    finally:
        fp.close()

    sha256 = hashlib.sha256(raw_bytes).hexdigest()

    ns = {"QtCore": QtCore}
    for range_tuple in (
        RUN_LOCK_NAME_RANGE, CONSTANTS_MARKER_NAMES_RANGE, OUTPUT_PATH_RANGE,
        MARKER_ERROR_CLASS_RANGE, TO_UNICODE_RANGE, FIND_EXISTING_RUN_RANGE,
        FIND_NAMED_MARKER_RANGE, PROCESS_STATE_CONSTANTS_RANGE,
        READ_PROCESS_SCOPE_STATE_RANGE,
    ):
        exec(
            compile(
                _extract_lines(raw_bytes, range_tuple),
                "<production_guard_definitions_readonly>",
                "exec",
            ),
            ns,
        )

    for required_name in (
        "RUN_LOCK_NAME", "OUTPUT_PATH", "NormalizerProcessAttemptMarkerError",
        "_find_existing_run", "_find_named_process_marker",
        "_read_process_scope_state",
    ):
        if required_name not in ns:
            raise CheckpointIError(
                "Extraction did not produce the expected definition %r "
                "-- the pinned line ranges may be stale; refusing to "
                "proceed rather than guess." % (required_name,)
            )

    return ns, sha256


def contextualizer_log_fingerprint(output_path):
    if not os.path.exists(output_path):
        return {"exists": False, "size_bytes": None, "sha256": None, "raw_bytes": None}
    fp = open(output_path, "rb")
    try:
        raw = fp.read()
    finally:
        fp.close()
    return {
        "exists": True,
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "raw_bytes": raw,
    }


_UNIQUE_SCOPE_FOLDS_RE_PREFIX = u"unique_scope_folds="
_MATCHED_FOLDS_RE_PREFIX = u"matched_folds="
_LIVE_MASTER_SHA_LOG_PREFIX = u"live Master SHA256="


def _extract_int_field(log_text, prefix):
    idx = log_text.find(prefix)
    if idx == -1:
        return None
    start = idx + len(prefix)
    end = start
    while end < len(log_text) and log_text[end].isdigit():
        end += 1
    if end == start:
        return None
    try:
        return int(log_text[start:end])
    except Exception:
        return None


def _extract_hex_field(log_text, prefix, length=64):
    idx = log_text.find(prefix)
    if idx == -1:
        return None
    start = idx + len(prefix)
    candidate = log_text[start:start + length]
    if len(candidate) != length:
        return None
    for ch in candidate:
        if ch not in u"0123456789abcdef":
            return None
    return candidate


def verify_run_log_content(raw_bytes, expected_shot_name, expected_unique_scope_folds,
                            expect_production_pass=True):
    """Read-only, purely textual verification of one preserved production
    log. For I1 (expect_production_pass=True): requires FINAL_REPORT_
    ENTRY AND an explicit "PRODUCTION_REBUILD_CONTROL_GROUPS = PASS" line
    (never FINAL_REPORT_ENTRY alone). For I2 (expect_production_pass=
    False): requires FINAL_REPORT_ENTRY AND an explicit "= FAIL" line,
    PLUS production's own stability-check evidence (never a substitute/
    manual failure)."""
    try:
        log_text = raw_bytes.decode("utf-8", "replace")
    except Exception:
        log_text = u""

    scope_selected_present = u"scope_mode=SELECTED_SHOTS" in log_text
    expected_shot_marker = u"CONTEXTUALIZER_SCOPE_SHOT_NAMES = [u'%s']" % expected_shot_name
    exact_single_shot_present = expected_shot_marker in log_text
    final_report_entry_present = u"FINAL_REPORT_ENTRY" in log_text
    production_pass_present = u"PRODUCTION_REBUILD_CONTROL_GROUPS = PASS" in log_text
    production_fail_present = u"PRODUCTION_REBUILD_CONTROL_GROUPS = FAIL" in log_text

    logged_unique_scope_folds = _extract_int_field(log_text, _UNIQUE_SCOPE_FOLDS_RE_PREFIX)
    logged_matched_folds = _extract_int_field(log_text, _MATCHED_FOLDS_RE_PREFIX)
    logged_master_sha256 = _extract_hex_field(log_text, _LIVE_MASTER_SHA_LOG_PREFIX)

    unique_scope_folds_matches = (
        expected_unique_scope_folds is None
        or (
            logged_unique_scope_folds is not None
            and logged_unique_scope_folds == expected_unique_scope_folds
        )
    )

    pre_native_count = log_text.count(u"phase=PRE_NATIVE")
    native_rebuild_returned_count = log_text.count(u"NATIVE_REBUILD_RETURNED = PASS")
    master_changed_message_present = u"Live Master changed during the run." in log_text
    target_callback_abort_present = (
        u"Exception during CONTEXTUALIZER target-level Qt callback transaction" in log_text
    )

    base_checks = (
        scope_selected_present
        and exact_single_shot_present
        and final_report_entry_present
        and unique_scope_folds_matches
    )
    if expect_production_pass:
        all_checks_pass = base_checks and production_pass_present and (not production_fail_present)
    else:
        all_checks_pass = base_checks and production_fail_present and (not production_pass_present)

    return {
        "scope_selected_present": scope_selected_present,
        "exact_single_shot_present": exact_single_shot_present,
        "final_report_entry_present": final_report_entry_present,
        "production_pass_present": production_pass_present,
        "production_fail_present": production_fail_present,
        "logged_unique_scope_folds": logged_unique_scope_folds,
        "expected_unique_scope_folds": expected_unique_scope_folds,
        "unique_scope_folds_matches": unique_scope_folds_matches,
        "logged_matched_folds": logged_matched_folds,
        "logged_master_sha256": logged_master_sha256,
        "pre_native_count": pre_native_count,
        "native_rebuild_returned_count": native_rebuild_returned_count,
        "master_changed_message_present": master_changed_message_present,
        "target_callback_abort_present": target_callback_abort_present,
        "all_checks_pass": all_checks_pass,
    }


# ----------------------------------------------------------------------
# Independent vocabulary derivation -- fresh, self-contained
# reimplementation, never extracted from or delegating to production's
# own code (same technique as Checkpoint_G_Later_Vocabulary.py).
# ----------------------------------------------------------------------
def _independent_to_unicode(value):
    if isinstance(value, unicode):
        return value
    try:
        return value.decode("utf-8")
    except Exception:
        try:
            return value.decode("latin-1")
        except Exception:
            return unicode(value)


def _independent_ascii_fold(value):
    s = _independent_to_unicode(value)
    out = []
    for ch in s:
        o = ord(ch)
        if 65 <= o <= 90:
            out.append(unichr(o + 32))
        else:
            out.append(ch)
    return u"".join(out)


def _independent_object_name(obj):
    try:
        return _independent_to_unicode(obj.GetName())
    except Exception:
        return u"<UNNAMED>"


def _independent_control_array(aset):
    try:
        attr_obj = aset.GetAttribute("controls")
    except Exception:
        return []
    if attr_obj is None:
        return []
    try:
        count = int(attr_obj.Count())
    except Exception:
        try:
            count = len(attr_obj)
        except Exception:
            return []
    out = []
    for i in xrange(count):
        try:
            out.append(attr_obj[i])
        except Exception:
            try:
                out.append(attr_obj.GetValue(i))
            except Exception:
                continue
    return out


def derive_shot_vocabulary(shot):
    folds = set()
    animation_sets_seen = 0
    controls_seen = 0
    for aset in shot.animationSets:
        animation_sets_seen += 1
        for control in _independent_control_array(aset):
            controls_seen += 1
            folds.add(_independent_ascii_fold(_independent_object_name(control)))
    return folds, animation_sets_seen, controls_seen


def resolve_unique_shot(all_shots, shot_name):
    return [s for s in all_shots if _independent_object_name(s) == shot_name]


def cache_key_for(master_sha256, folds, consumer_kind):
    return (master_sha256, None, frozenset(folds), consumer_kind)


def diagnostics_delta(old_list, new_list):
    if not old_list:
        return list(new_list), True
    old_len = len(old_list)
    if len(new_list) >= old_len and new_list[:old_len] == old_list:
        return list(new_list[old_len:]), True
    for k in range(old_len, 0, -1):
        if len(new_list) >= k and new_list[:k] == old_list[old_len - k:]:
            return list(new_list[k:]), True
    return list(new_list), False


# ----------------------------------------------------------------------
# Authority package import (same technique as Checkpoint_G_Later_Vocabulary.py).
# ----------------------------------------------------------------------
def _locate_mainmenu_dir():
    # Single source of truth: the exact-path helper loader above already
    # derives this same directory before igen is ever bound.
    return _mainmenu_dir_for_helper_loading()


def import_authority_runtime():
    mainmenu_dir = _locate_mainmenu_dir()
    if mainmenu_dir not in sys.path:
        sys.path.insert(0, mainmenu_dir)
    from sfm_master_authority_productionized import runtime as authority_runtime
    from sfm_master_authority_productionized import errors as authority_errors
    from sfm_master_authority_productionized import observation as authority_observation
    return authority_runtime, authority_errors, authority_observation


def get_canonical_broker(authority_runtime):
    return authority_runtime.get_broker(
        expected_api_version=EXPECTED_RUNTIME_API_VERSION,
        expected_build_id=EXPECTED_RUNTIME_BUILD_ID,
        is_main_thread_fn=lambda: (
            QtCore.QThread.currentThread()
            is QtCore.QCoreApplication.instance().thread()
        ),
    )


def capture_provider_counters(broker):
    return dict(broker.provider_counters())


def capture_lease_counters(broker):
    return {
        "outstanding_lease_count": broker.outstanding_lease_count(),
        "unreleased_lease_count": broker.unreleased_lease_count(),
        "view_cache_entry_count": broker.view_cache_entry_count(),
    }


def inspect_cached_view(broker, cache_key, requested_folds):
    view = broker.cached_view(cache_key)
    if view is None:
        return {"present": False}
    covered = view.coverage.covered_keys()
    known_count = 0
    uncovered_count = 0
    for fold in requested_folds:
        result = view.coverage.lookup(fold)
        if result.status == u"Known":
            known_count += 1
        elif result.status != u"MasterUnknown":
            uncovered_count += 1
    return {
        "present": True,
        "is_stale": view.is_stale(),
        "consumer_kind": view.consumer_kind,
        "semantic_generation_master_sha256": view.semantic_generation.master_sha256,
        "covered_keys_equals_requested": (covered == frozenset(requested_folds)),
        "known_count": known_count,
        "uncovered_count": uncovered_count,
    }


def _identity_and_state_record():
    """Shared identity/state capture used by every snapshot handler --
    factored out once rather than duplicated per-handler."""
    record = {}
    try:
        prod_ns, production_sha256 = load_production_guard_definitions()
        record["production_sha256"] = production_sha256
        record["production_sha256_matches_expected"] = (
            production_sha256 == EXPECTED_PRODUCTION_SHA256
        )
    except Exception as exc:
        prod_ns = None
        record["production_sha256"] = None
        record["production_sha256_matches_expected"] = False
        record["production_load_error"] = u"%r" % (exc,)

    try:
        with open(CANONICAL_MASTER_INSTALLED_PATH, "rb") as _mf:
            current_master_sha256 = hashlib.sha256(_mf.read()).hexdigest()
        record["current_master_sha256"] = current_master_sha256
    except Exception as exc:
        record["current_master_sha256"] = None
        record["current_master_read_error"] = u"%r" % (exc,)

    try:
        main_window = sfmApp.GetMainWindow()
    except Exception as exc:
        main_window = None
        record["main_window_error"] = u"%r" % (exc,)
    record["main_window_available"] = main_window is not None

    if prod_ns is not None and main_window is not None:
        try:
            record["guard_state"] = prod_ns["_read_process_scope_state"](main_window)
            record["guard_state_error"] = None
        except prod_ns["NormalizerProcessAttemptMarkerError"] as exc:
            record["guard_state"] = None
            record["guard_state_error"] = u"%r" % (exc,)
        try:
            found_run_lock = prod_ns["_find_existing_run"](main_window)
            record["run_lock_present"] = found_run_lock is not None
        except Exception as exc:
            record["run_lock_present"] = None
            record["run_lock_error"] = u"%r" % (exc,)
        output_path = prod_ns.get("OUTPUT_PATH")
    else:
        record["guard_state"] = None
        record["run_lock_present"] = None
        output_path = "C:\\Users\\Public\\Documents\\sfm_rebuild_control_groups.txt"

    authority_runtime = None
    authority_observation = None
    broker = None
    try:
        authority_runtime, _e, authority_observation = import_authority_runtime()
        record["runtime_api_version"] = authority_runtime.RUNTIME_API_VERSION
        record["runtime_api_version_matches_expected"] = (
            authority_runtime.RUNTIME_API_VERSION == EXPECTED_RUNTIME_API_VERSION
        )
        record["runtime_build_id"] = getattr(authority_runtime, "RUNTIME_BUILD_ID", None)
        record["runtime_build_id_matches_expected"] = (
            record["runtime_build_id"] == EXPECTED_RUNTIME_BUILD_ID
        )
        record["runtime_is_canonical"] = authority_runtime.is_canonical()
        broker = get_canonical_broker(authority_runtime)
        record["provider_counters"] = capture_provider_counters(broker)
        record["lease_counters"] = capture_lease_counters(broker)
        record["recent_diagnostics"] = broker.recent_diagnostics()
    except Exception as exc:
        record["authority_import_or_broker_error"] = u"%r" % (exc,)

    try:
        all_shots = list(sfmApp.GetShots())
    except Exception as exc:
        all_shots = []
        record["shots_enumerable"] = False
        record["shots_enumerable_error"] = u"%r" % (exc,)
    else:
        record["shots_enumerable"] = True
    record["project_shot_count"] = len(all_shots)

    open_basename = u""
    try:
        root_for_filename = sfmApp.GetDocumentRoot()
        open_file_id = root_for_filename.GetFileId()
        open_path = vs.g_pDataModel.GetFileName(open_file_id)
        open_basename = os.path.basename(_independent_to_unicode(open_path)) if open_path else u""
    except Exception as exc:
        record["fixture_identity_error"] = u"%r" % (exc,)
    record["fixture_open_basename"] = open_basename

    return record, prod_ns, main_window, authority_observation, broker, output_path, all_shots


def _gate(gate_checks, name, passed, detail=None):
    gate_checks.append({"name": name, "passed": bool(passed), "detail": detail})


def _common_identity_gates(gate_checks, record):
    _gate(gate_checks, "identity.production_sha256_matches_expected",
          record.get("production_sha256_matches_expected") is True, record.get("production_sha256"))
    _gate(gate_checks, "identity.runtime_api_version_matches_expected",
          record.get("runtime_api_version_matches_expected") is True, record.get("runtime_api_version"))
    _gate(gate_checks, "identity.runtime_build_id_matches_expected",
          record.get("runtime_build_id_matches_expected") is True, record.get("runtime_build_id"))
    _gate(gate_checks, "identity.runtime_is_canonical",
          record.get("runtime_is_canonical") is True, record.get("runtime_is_canonical"))
    _gate(gate_checks, "state.main_window_available",
          record.get("main_window_available") is True, None)
    _gate(gate_checks, "fixture.matches_expected_normalized_copy",
          record.get("fixture_open_basename", u"").lower() == EXPECTED_FIXTURE_FILENAME.lower(),
          record.get("fixture_open_basename"))
    _gate(gate_checks, "fixture.is_not_forbidden_original",
          record.get("fixture_open_basename", u"").lower() != FORBIDDEN_ORIGINAL_FIXTURE_FILENAME.lower(),
          record.get("fixture_open_basename"))
    _gate(gate_checks, "fixture.shots_enumerable", record.get("shots_enumerable") is True, None)
    _gate(gate_checks, "fixture.project_shot_count_matches_established_size",
          record.get("project_shot_count") == EXPECTED_PROJECT_SHOT_COUNT, record.get("project_shot_count"))


def main():
    cont = read_continuation_state()
    snapshot_index = cont["next_snapshot_index"]
    if snapshot_index - 1 < len(SNAPSHOT_SCHEDULE):
        operation_label, expected_state = SNAPSHOT_SCHEDULE[snapshot_index - 1]
    else:
        operation_label, expected_state = u"unscheduled_extra_snapshot", None

    (record, prod_ns, main_window, authority_observation, broker, output_path,
     all_shots) = _identity_and_state_record()
    record["wall_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    record["epoch"] = time.time()
    record["current_pid"] = os.getpid()
    record["snapshot_index"] = snapshot_index
    record["operation"] = operation_label
    record["expected_state"] = expected_state

    # --- Production log fingerprint / run-evidence capture ---
    log_fp = contextualizer_log_fingerprint(output_path)
    current_log_sha256 = log_fp["sha256"] if log_fp["exists"] else None
    run_capture_record = None
    baseline_seeded = False

    if snapshot_index == 1:
        cont["last_known_log_sha256"] = current_log_sha256
        baseline_seeded = True
    elif log_fp["exists"] and log_fp["sha256"] != cont["last_known_log_sha256"]:
        run_index = cont["next_run_index"]
        if run_index > len(RUN_LOG_LABELS):
            raise CheckpointIError(
                "Detected a production-log change beyond the fixed "
                "%d-entry run-evidence schedule (run_index=%d)."
                % (len(RUN_LOG_LABELS), run_index)
            )
        run_label = RUN_LOG_LABELS[run_index - 1]
        run_filename = "sfm_checkpoint_i_run_%02d_%s.txt" % (run_index, run_label)
        run_path = EVIDENCE_DIR + run_filename
        write_evidence_text_once(run_path, log_fp["raw_bytes"])

        expected_shot_for_run = I1_SHOT_NAME if run_index in (1, 2) else I2_SHOT_NAME
        expected_count_for_run = (
            len(cont.get("i1_shot9_folds_sorted") or []) if run_index in (1, 2) else None
        )
        expect_pass = run_index in (1, 2)
        log_verification = verify_run_log_content(
            log_fp["raw_bytes"], expected_shot_for_run, expected_count_for_run,
            expect_production_pass=expect_pass,
        )

        run_capture_record = {
            "filename": run_filename, "sha256": log_fp["sha256"],
            "size_bytes": log_fp["size_bytes"], "step_ordinal": run_index,
            "label": run_label, "pid": record["current_pid"],
            "wall_time": record["wall_time"],
            "captured_at_snapshot_index": snapshot_index,
            "log_verification": log_verification,
        }
        cont["captured_runs"].append(run_capture_record)
        cont["next_run_index"] = run_index + 1
        cont["last_known_log_sha256"] = log_fp["sha256"]

    record["baseline_seeded"] = baseline_seeded
    record["production_log_fingerprint"] = {
        "exists": log_fp["exists"], "size_bytes": log_fp["size_bytes"], "sha256": log_fp["sha256"],
    }
    record["run_captured"] = run_capture_record

    # --- Snapshot-specific logic ---
    handlers = {
        u"i1_01_baseline_g1": _snapshot_i1_01_baseline,
        u"i1_02_after_g1_command": _snapshot_i1_02_after_g1,
        u"i1_03_g2_ready": _snapshot_i1_03_g2_ready,
        u"i1_04_after_g2_command": _snapshot_i1_04_after_g2,
        u"i2_00_baseline_g2": _snapshot_i2_00_baseline,
        u"i2_01_prearm": _snapshot_i2_01_prearm,
        u"i2_02_verify": _snapshot_i2_02_verify,
        u"i_08_finalize_verify": _snapshot_i_08_finalize_verify,
    }
    handler = handlers.get(operation_label)
    if handler is not None:
        result = handler(record, cont, broker, authority_observation, all_shots, main_window, prod_ns)
        record.update(result)

    # --- Write immutable snapshot evidence ---
    snapshot_json_filename = "sfm_checkpoint_i_snapshot_%02d_%s.json" % (snapshot_index, operation_label)
    snapshot_txt_filename = "sfm_checkpoint_i_snapshot_%02d_%s.txt" % (snapshot_index, operation_label)
    write_evidence_json_once(EVIDENCE_DIR + snapshot_json_filename, record)

    txt_lines = [
        u"CHECKPOINT I -- SNAPSHOT #%02d (%s)" % (snapshot_index, operation_label),
        u"wall_time = %s" % record["wall_time"],
        u"current_pid = %s" % record["current_pid"],
        u"production_sha256_matches_expected = %s" % record.get("production_sha256_matches_expected"),
        u"guard_state = %s (expected %s)" % (record.get("guard_state"), expected_state),
        u"classification = %s" % record.get("classification"),
        u"gate_failure = %s" % record.get("gate_failure"),
        u"failed_gates = %s" % (record.get("failed_gates"),),
    ]
    write_evidence_text_once(
        EVIDENCE_DIR + snapshot_txt_filename,
        (u"\n".join(txt_lines) + u"\n").encode("utf-8"),
    )

    cont["captured_snapshots"].append({
        "filename": snapshot_json_filename, "step_ordinal": snapshot_index,
        "pid": record["current_pid"], "wall_time": record["wall_time"],
        "operation": operation_label, "expected_state": expected_state,
        "observed_guard_state": record.get("guard_state"),
        "classification": record.get("classification"),
        "failed_gates": record.get("failed_gates"),
    })
    cont["next_snapshot_index"] = snapshot_index + 1

    ok, err, _r = write_json_rollup(CONTINUATION_STATE_PATH, cont)
    if not ok:
        raise CheckpointIError("Failed to persist continuation-state: %s" % err)

    last_snapshot_entry = cont["captured_snapshots"][-1] if cont["captured_snapshots"] else None
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
        if finalize_verdict == u"RESTORATION_CONFIRMED":
            final_i_verdict = u"I_PASS"
        else:
            # BLOCKER 8: restoration is mandatory before I_PASS/I CLOSED.
            final_i_verdict = u"I_RUNTIME_PASS_RESTORATION_REQUIRED"
    elif i1_verdict is not None or i2_verdict is not None:
        final_i_verdict = u"I_INCOMPLETE_OR_FAILED"

    ok2, err2, _r2 = write_json_rollup(FINAL_RESULT_PATH, {
        "captured_snapshots": cont["captured_snapshots"],
        "captured_runs": cont["captured_runs"],
        "mechanical_last_snapshot_verdict": (
            last_snapshot_entry["classification"] if last_snapshot_entry else None
        ),
        "mechanical_last_snapshot_failed_checks": (
            last_snapshot_entry.get("failed_gates") if last_snapshot_entry else None
        ),
        "i1_verdict": i1_verdict,
        "i2_verdict": i2_verdict,
        "finalize_verdict": finalize_verdict,
        "final_i_verdict": final_i_verdict,
    })
    if not ok2:
        raise CheckpointIError("Failed to write final-result rollup: %s" % err2)

    summary_text = u"\n".join(txt_lines) + u"\n"
    write_text_rollup(FINAL_SUMMARY_PATH, summary_text.encode("utf-8"))

    try:
        sys.stdout.write(summary_text)
    except Exception:
        pass


# ----------------------------------------------------------------------
# I1 handlers.
# ----------------------------------------------------------------------
def _snapshot_i1_01_baseline(record, cont, broker, authority_observation, all_shots, main_window, prod_ns):
    gate_checks = []
    _common_identity_gates(gate_checks, record)
    _gate(gate_checks, "identity.g1_master_sha256_matches_expected",
          record.get("current_master_sha256") == EXPECTED_G1_MASTER_SHA256, record.get("current_master_sha256"))
    _gate(gate_checks, "state.guard_state_is_unused", record.get("guard_state") == u"UNUSED", record.get("guard_state"))
    _gate(gate_checks, "state.run_lock_absent", record.get("run_lock_present") is False, record.get("run_lock_present"))

    provider_counters = record.get("provider_counters") or {}
    _gate(gate_checks, "provider.current_open_provider_count_is_zero",
          provider_counters.get("current_open_provider_count") == 0, provider_counters.get("current_open_provider_count"))
    lease_counters = record.get("lease_counters") or {}
    _gate(gate_checks, "lease.outstanding_lease_count_is_zero",
          lease_counters.get("outstanding_lease_count") == 0, lease_counters.get("outstanding_lease_count"))
    _gate(gate_checks, "lease.unreleased_lease_count_is_zero",
          lease_counters.get("unreleased_lease_count") == 0, lease_counters.get("unreleased_lease_count"))

    i1_matches = resolve_unique_shot(all_shots, I1_SHOT_NAME)
    _gate(gate_checks, "vocabulary.shot9_resolves_uniquely", len(i1_matches) == 1, len(i1_matches))

    shot9_folds = frozenset()
    if len(i1_matches) == 1:
        shot9_folds, _asets, _controls = derive_shot_vocabulary(i1_matches[0])
    _gate(gate_checks, "vocabulary.shot9_nonempty", len(shot9_folds) > 0, len(shot9_folds))

    g1_bytes = None
    g2_bytes_sha256 = None
    g1_cache_present = None
    g2_cache_present = None
    inventory = None
    if broker is not None and authority_observation is not None and len(shot9_folds) > 0:
        try:
            with open(CANONICAL_MASTER_INSTALLED_PATH, "rb") as _mf:
                g1_bytes = _mf.read()
            g2_bytes = igen.construct_g2_bytes(g1_bytes)
            g2_bytes_sha256 = hashlib.sha256(g2_bytes).hexdigest()

            h0 = authority_observation.observe_master(CANONICAL_MASTER_INSTALLED_PATH)
            g1_key = cache_key_for(h0.sha256, shot9_folds, CONSUMER_KIND)
            g2_key = cache_key_for(g2_bytes_sha256, shot9_folds, CONSUMER_KIND)
            g1_cache_present = broker.cached_view(g1_key) is not None
            g2_cache_present = broker.cached_view(g2_key) is not None
        except Exception as exc:
            record["cache_key_gate_error"] = u"%r" % (exc,)
    _gate(gate_checks, "cache.g1_shot9_cache_key_absent_at_baseline", g1_cache_present is False, g1_cache_present)
    _gate(gate_checks, "cache.g2_shot9_cache_key_absent_at_baseline", g2_cache_present is False, g2_cache_present)

    try:
        inventory = igen.capture_live_state_inventory(CANONICAL_MASTER_INSTALLED_PATH, SHIPPED_AUTHORITY_DIR)
        inventory_valid = inventory.get("master_sha256") == EXPECTED_G1_MASTER_SHA256
    except Exception as exc:
        inventory = None
        inventory_valid = False
        record["inventory_capture_error"] = u"%r" % (exc,)
    _gate(gate_checks, "helper.baseline_live_state_inventory_valid", inventory_valid, None)

    record["shot9_folds_sorted"] = sorted(shot9_folds)
    record["shot9_count"] = len(shot9_folds)
    record["expected_g2_master_sha256"] = g2_bytes_sha256
    record["baseline_live_state_inventory"] = inventory
    failed = [g["name"] for g in gate_checks if not g["passed"]]
    out = {"gate_checks": gate_checks, "failed_gates": failed}

    if failed:
        out["classification"] = u"INCONCLUSIVE_BEFORE_EXECUTION"
        out["gate_failure"] = u"%d baseline gate(s) failed: %s" % (len(failed), u", ".join(failed))
        return out

    if g1_bytes is not None:
        write_evidence_bytes_once(G1_SOURCE_BYTES_BACKUP_PATH, g1_bytes)

    # R2 BLOCKER 6: the baseline inventory is ALSO written as its own
    # standalone, immutable, write-once artifact -- never only embedded
    # in this snapshot/continuation-state JSON. write_evidence_json_once
    # already re-reads/reparses the file it just wrote; independently
    # re-verify here that the reparsed content is byte-for-byte the same
    # dict this snapshot itself embeds, rather than merely assuming it
    # by construction.
    baseline_inventory_artifact_path = None
    if inventory is not None:
        reparsed_inventory = write_evidence_json_once(BASELINE_INVENTORY_ARTIFACT_PATH, inventory)
        if reparsed_inventory != inventory:
            raise CheckpointIError(
                "Baseline inventory artifact round-trip mismatch: the "
                "file written to %r does not reparse to the exact same "
                "inventory this snapshot embeds." % (BASELINE_INVENTORY_ARTIFACT_PATH,)
            )
        baseline_inventory_artifact_path = BASELINE_INVENTORY_ARTIFACT_PATH
    record["baseline_inventory_artifact_path"] = baseline_inventory_artifact_path
    record["baseline_inventory_artifact_matches_embedded"] = (baseline_inventory_artifact_path is not None)

    cont["i1_baseline_pid"] = record["current_pid"]
    cont["i1_baseline_master_sha256"] = record.get("current_master_sha256")
    cont["i1_expected_g2_sha256"] = g2_bytes_sha256
    cont["i1_shot9_folds_sorted"] = sorted(shot9_folds)
    cont["i1_baseline_provider_counters"] = record.get("provider_counters")
    cont["i1_baseline_diagnostics"] = record.get("recent_diagnostics")
    cont["i1_baseline_inventory"] = inventory
    cont["i1_baseline_inventory_artifact_path"] = baseline_inventory_artifact_path
    out["classification"] = u"I1_BASELINE_PASSED"
    return out


def _snapshot_i1_02_after_g1(record, cont, broker, authority_observation, all_shots, main_window, prod_ns):
    gate_checks = []
    baseline_pid = cont.get("i1_baseline_pid")
    _common_identity_gates(gate_checks, record)
    _gate(gate_checks, "continuity.same_pid_as_baseline", record.get("current_pid") == baseline_pid,
          (record.get("current_pid"), baseline_pid))
    _gate(gate_checks, "state.guard_state_is_selected_used", record.get("guard_state") == u"SELECTED_USED",
          record.get("guard_state"))
    _gate(gate_checks, "state.run_lock_absent", record.get("run_lock_present") is False, record.get("run_lock_present"))
    _gate(gate_checks, "generation.live_master_still_exactly_g1",
          record.get("current_master_sha256") == cont.get("i1_baseline_master_sha256"),
          record.get("current_master_sha256"))

    run_captured = record.get("run_captured")
    _gate(gate_checks, "run.exactly_one_new_run01_log_captured",
          run_captured is not None and run_captured.get("step_ordinal") == 1,
          run_captured.get("step_ordinal") if run_captured else None)
    log_verification = (run_captured or {}).get("log_verification") or {}
    _gate(gate_checks, "run.run01_verifier_all_checks_pass", bool(log_verification.get("all_checks_pass")), log_verification)

    shot9_folds = frozenset(cont.get("i1_shot9_folds_sorted") or [])
    g1_sha = cont.get("i1_baseline_master_sha256")
    g1_inspection = {"present": False}
    if broker is not None and g1_sha is not None:
        g1_key = cache_key_for(g1_sha, shot9_folds, CONSUMER_KIND)
        g1_inspection = inspect_cached_view(broker, g1_key, shot9_folds)
    _gate(gate_checks, "view.g1_view_present", g1_inspection.get("present") is True, None)
    _gate(gate_checks, "view.g1_view_generation_matches_g1",
          g1_inspection.get("semantic_generation_master_sha256") == g1_sha, g1_inspection.get("semantic_generation_master_sha256"))
    _gate(gate_checks, "view.g1_covered_keys_equal_shot9", g1_inspection.get("covered_keys_equals_requested") is True, None)

    baseline_provider_counters = cont.get("i1_baseline_provider_counters") or {}
    provider_counters_now = record.get("provider_counters") or {}
    opens_delta = (provider_counters_now.get("total_provider_opens") or 0) - (baseline_provider_counters.get("total_provider_opens") or 0)
    closes_delta = (provider_counters_now.get("total_provider_closes") or 0) - (baseline_provider_counters.get("total_provider_closes") or 0)
    _gate(gate_checks, "provider.exactly_one_open_since_baseline", opens_delta == 1, opens_delta)
    _gate(gate_checks, "provider.exactly_one_close_since_baseline", closes_delta == 1, closes_delta)

    baseline_diag = cont.get("i1_baseline_diagnostics") or []
    diagnostics_now = record.get("recent_diagnostics") or []
    delta, delta_clean = diagnostics_delta(baseline_diag, diagnostics_now)
    delta_events = [e.get("event") for e in delta]
    _gate(gate_checks, "diagnostics.delta_continuity_established", delta_clean, None)
    _gate(gate_checks, "diagnostics.delta_contains_cohort_acquired", u"cohort_acquired" in delta_events, delta_events)

    lease_counters_now = record.get("lease_counters") or {}
    _gate(gate_checks, "lease.outstanding_zero", lease_counters_now.get("outstanding_lease_count") == 0, None)
    _gate(gate_checks, "lease.unreleased_zero", lease_counters_now.get("unreleased_lease_count") == 0, None)
    _gate(gate_checks, "provider.current_open_provider_count_is_zero",
          provider_counters_now.get("current_open_provider_count") == 0, provider_counters_now.get("current_open_provider_count"))

    failed = [g["name"] for g in gate_checks if not g["passed"]]
    out = {"gate_checks": gate_checks, "failed_gates": failed}
    if failed:
        out["classification"] = u"FAIL"
        out["gate_failure"] = u"%d I1-G1-stage check(s) failed: %s" % (len(failed), u", ".join(failed))
        return out
    cont["i1_g1_stage_provider_counters"] = record.get("provider_counters")
    cont["i1_g1_stage_diagnostics"] = record.get("recent_diagnostics")
    out["classification"] = u"I1_G1_STAGE_PASSED"
    return out


def _validate_g2_publication_record(record_out, authority_dir, expected_g1_sha, expected_g2_sha):
    """BLOCKER 6: mechanically consumes and verifies the EXACT immutable
    G2 publication record the external, repo-side I_Generation_
    Publisher.py writes -- never "any sidecar exists". R3 HARDENING:
    also mechanically requires the record's own recorded semantic_parity
    to report all_parity_checks_pass=True, rather than merely assuming
    Phase A's own producer-side check succeeded, and corroborates the
    active manifest's current on-disk SHA-256 against the record's own
    manifest_sha256_after_publication."""
    checks = {}
    publication_record = igen.read_publication_record_plain(G2_PUBLICATION_RECORD_PATH)
    checks["publication_record_present"] = publication_record is not None
    if publication_record is None:
        return checks, None

    checks["record_g1_source_sha256_matches"] = (
        publication_record.get("g1_source_sha256") == expected_g1_sha
    )
    checks["record_g2_source_sha256_matches"] = (
        publication_record.get("g2_source_sha256") == expected_g2_sha
    )
    parity = publication_record.get("semantic_parity") or {}
    checks["record_semantic_parity_is_pass"] = parity.get("all_parity_checks_pass") is True
    basename = publication_record.get("g2_generation_basename")
    checks["generation_basename_is_safe"] = bool(basename) and igen.is_safe_bare_basename(basename)

    sidecar_sha_on_disk = None
    sidecar_exists = False
    if checks["generation_basename_is_safe"]:
        sidecar_path = os.path.join(authority_dir, basename)
        sidecar_exists = os.path.isfile(sidecar_path)
        if sidecar_exists:
            try:
                sidecar_sha_on_disk = igen.sha256_file(sidecar_path)
            except Exception:
                sidecar_sha_on_disk = None
    checks["exact_named_sidecar_exists"] = sidecar_exists
    checks["exact_named_sidecar_sha_matches_record"] = (
        sidecar_sha_on_disk is not None
        and sidecar_sha_on_disk == publication_record.get("g2_sidecar_sha256")
    )

    active_manifest_source_sha = igen.read_manifest_source_sha256_plain(authority_dir)
    active_manifest_basename = igen.read_manifest_field_plain(authority_dir, "generation_basename")
    checks["active_manifest_source_sha_equals_g2"] = (active_manifest_source_sha == expected_g2_sha)
    checks["active_manifest_generation_basename_matches_record"] = (
        active_manifest_basename == basename
    )

    manifest_path = os.path.join(authority_dir, igen.MANIFEST_BASENAME)
    current_manifest_sha = None
    if os.path.isfile(manifest_path):
        try:
            current_manifest_sha = igen.sha256_file(manifest_path)
        except Exception:
            current_manifest_sha = None
    checks["active_manifest_current_sha_equals_recorded_manifest_sha"] = (
        current_manifest_sha is not None
        and current_manifest_sha == publication_record.get("manifest_sha256_after_publication")
    )
    return checks, publication_record


def _validate_g2_activation_record(expected_g1_sha, expected_g2_sha):
    """R2 BLOCKER 1/3: mechanically consumes and verifies the EXACT
    immutable G2 Master ACTIVATION record the external, repo-side
    I_Generation_Publisher.py's activate_g2_master() writes -- proves
    the live Master was actually switched to G2 through the corrected,
    hash-gated, atomic (MoveFileExW) path, never merely that a
    sidecar/publication record exists (which round 1's own I1-03 gate
    incorrectly treated as sufficient)."""
    checks = {}
    activation_record = igen.read_finalization_record_plain(G2_ACTIVATION_RECORD_PATH)
    checks["activation_record_present"] = activation_record is not None
    if activation_record is None:
        return checks, None

    checks["activation_success"] = activation_record.get("success") is True
    checks["activation_expected_g1_matches"] = (
        activation_record.get("expected_g1_sha256") == expected_g1_sha
    )
    checks["activation_rederived_g2_matches_expected"] = (
        activation_record.get("rederived_g2_sha256") == expected_g2_sha
    )
    checks["activation_post_master_equals_expected_g2"] = (
        activation_record.get("post_activation_master_sha256") == expected_g2_sha
    )
    binding = activation_record.get("path_binding_checks") or {}
    checks["activation_master_path_matched_baseline"] = binding.get("master_path_matches_baseline") is True
    checks["activation_authority_dir_matched_baseline"] = binding.get("authority_dir_matches_baseline") is True
    return checks, activation_record


def _snapshot_i1_03_g2_ready(record, cont, broker, authority_observation, all_shots, main_window, prod_ns):
    gate_checks = []
    baseline_pid = cont.get("i1_baseline_pid")
    _common_identity_gates(gate_checks, record)
    _gate(gate_checks, "continuity.same_pid_as_baseline", record.get("current_pid") == baseline_pid,
          (record.get("current_pid"), baseline_pid))
    _gate(gate_checks, "state.guard_state_is_selected_used", record.get("guard_state") == u"SELECTED_USED",
          record.get("guard_state"))
    _gate(gate_checks, "state.run_lock_absent", record.get("run_lock_present") is False, record.get("run_lock_present"))

    expected_g1_sha = cont.get("i1_baseline_master_sha256")
    expected_g2_sha = cont.get("i1_expected_g2_sha256")
    _gate(gate_checks, "generation.live_master_equals_expected_g2",
          record.get("current_master_sha256") == expected_g2_sha,
          (record.get("current_master_sha256"), expected_g2_sha))

    pub_checks, publication_record = _validate_g2_publication_record(
        record, SHIPPED_AUTHORITY_DIR, expected_g1_sha, expected_g2_sha,
    )
    for name, passed in pub_checks.items():
        _gate(gate_checks, "authority.%s" % name, passed, None)
    record["g2_publication_record"] = publication_record

    # R2 BLOCKER 1/3: I1-03 must require BOTH an exact valid G2
    # publication record AND an exact valid G2 Master ACTIVATION record
    # -- a published sidecar alone never proves the live Master was
    # actually switched.
    act_checks, activation_record = _validate_g2_activation_record(expected_g1_sha, expected_g2_sha)
    for name, passed in act_checks.items():
        _gate(gate_checks, "activation.%s" % name, passed, None)
    record["g2_activation_record"] = activation_record

    shot9_folds = frozenset(cont.get("i1_shot9_folds_sorted") or [])
    g2_inspection = {"present": False}
    if broker is not None and expected_g2_sha is not None:
        g2_key = cache_key_for(expected_g2_sha, shot9_folds, CONSUMER_KIND)
        g2_inspection = inspect_cached_view(broker, g2_key, shot9_folds)
    _gate(gate_checks, "cache.g2_view_not_yet_cached", g2_inspection.get("present") is False, g2_inspection.get("present"))

    g1_still_observable = None
    if broker is not None and expected_g1_sha is not None:
        g1_key = cache_key_for(expected_g1_sha, shot9_folds, CONSUMER_KIND)
        g1_inspection = inspect_cached_view(broker, g1_key, shot9_folds)
        g1_still_observable = g1_inspection.get("present") is True
    _gate(gate_checks, "cache.g1_view_still_present_as_previous_generation_state", g1_still_observable is True, g1_still_observable)

    provider_counters = record.get("provider_counters") or {}
    lease_counters = record.get("lease_counters") or {}
    _gate(gate_checks, "provider.current_open_provider_count_is_zero",
          provider_counters.get("current_open_provider_count") == 0, None)
    _gate(gate_checks, "lease.outstanding_zero", lease_counters.get("outstanding_lease_count") == 0, None)
    _gate(gate_checks, "lease.unreleased_zero", lease_counters.get("unreleased_lease_count") == 0, None)

    failed = [g["name"] for g in gate_checks if not g["passed"]]
    out = {"gate_checks": gate_checks, "failed_gates": failed}
    if failed:
        out["classification"] = u"INCONCLUSIVE_BEFORE_EXECUTION"
        out["gate_failure"] = (
            u"%d G2-ready check(s) failed -- operator must NOT run command "
            u"B: %s" % (len(failed), u", ".join(failed))
        )
        return out
    cont["i1_g2_ready_provider_counters"] = record.get("provider_counters")
    cont["i1_g2_ready_diagnostics"] = record.get("recent_diagnostics")
    out["classification"] = u"I1_G2_READY"
    return out


def _snapshot_i1_04_after_g2(record, cont, broker, authority_observation, all_shots, main_window, prod_ns):
    gate_checks = []
    baseline_pid = cont.get("i1_baseline_pid")
    _common_identity_gates(gate_checks, record)
    _gate(gate_checks, "continuity.same_pid_as_baseline", record.get("current_pid") == baseline_pid,
          (record.get("current_pid"), baseline_pid))
    _gate(gate_checks, "state.guard_state_is_selected_used", record.get("guard_state") == u"SELECTED_USED",
          record.get("guard_state"))
    _gate(gate_checks, "state.run_lock_absent", record.get("run_lock_present") is False, record.get("run_lock_present"))

    expected_g2_sha = cont.get("i1_expected_g2_sha256")
    _gate(gate_checks, "generation.live_master_still_exactly_g2",
          record.get("current_master_sha256") == expected_g2_sha, record.get("current_master_sha256"))

    run_captured = record.get("run_captured")
    _gate(gate_checks, "run.exactly_one_new_run02_log_captured",
          run_captured is not None and run_captured.get("step_ordinal") == 2,
          run_captured.get("step_ordinal") if run_captured else None)
    log_verification = (run_captured or {}).get("log_verification") or {}
    _gate(gate_checks, "run.run02_verifier_all_checks_pass", bool(log_verification.get("all_checks_pass")), log_verification)
    _gate(gate_checks, "run.logged_master_sha256_equals_g2",
          log_verification.get("logged_master_sha256") == expected_g2_sha, log_verification.get("logged_master_sha256"))

    shot9_folds = frozenset(cont.get("i1_shot9_folds_sorted") or [])
    g2_inspection = {"present": False}
    if broker is not None and expected_g2_sha is not None:
        g2_key = cache_key_for(expected_g2_sha, shot9_folds, CONSUMER_KIND)
        g2_inspection = inspect_cached_view(broker, g2_key, shot9_folds)
    _gate(gate_checks, "view.g2_view_present", g2_inspection.get("present") is True, None)
    _gate(gate_checks, "view.g2_view_is_fresh", bool(g2_inspection.get("present")) and (not g2_inspection.get("is_stale")), None)
    _gate(gate_checks, "view.g2_view_generation_matches_g2",
          g2_inspection.get("semantic_generation_master_sha256") == expected_g2_sha, None)
    _gate(gate_checks, "view.g2_covered_keys_equal_shot9", g2_inspection.get("covered_keys_equals_requested") is True, None)
    _gate(gate_checks, "view.g2_zero_uncovered", g2_inspection.get("uncovered_count") == 0, g2_inspection.get("uncovered_count"))

    g1_sha = cont.get("i1_baseline_master_sha256")
    g1_no_longer_usable = None
    if broker is not None and g1_sha is not None:
        g1_key = cache_key_for(g1_sha, shot9_folds, CONSUMER_KIND)
        g1_no_longer_usable = broker.cached_view(g1_key) is None
    _gate(gate_checks, "view.g1_view_no_longer_a_usable_cache_hit", g1_no_longer_usable is True, g1_no_longer_usable)

    ready_provider_counters = cont.get("i1_g2_ready_provider_counters") or {}
    provider_counters_now = record.get("provider_counters") or {}
    opens_delta = (provider_counters_now.get("total_provider_opens") or 0) - (ready_provider_counters.get("total_provider_opens") or 0)
    closes_delta = (provider_counters_now.get("total_provider_closes") or 0) - (ready_provider_counters.get("total_provider_closes") or 0)
    _gate(gate_checks, "provider.exactly_one_open_since_g2_ready", opens_delta == 1, opens_delta)
    _gate(gate_checks, "provider.exactly_one_close_since_g2_ready", closes_delta == 1, closes_delta)
    _gate(gate_checks, "provider.current_open_provider_count_is_zero",
          provider_counters_now.get("current_open_provider_count") == 0, None)

    ready_diag = cont.get("i1_g2_ready_diagnostics") or []
    diagnostics_now = record.get("recent_diagnostics") or []
    delta, delta_clean = diagnostics_delta(ready_diag, diagnostics_now)
    delta_events = [e.get("event") for e in delta]
    _gate(gate_checks, "diagnostics.delta_continuity_established", delta_clean, None)
    _gate(gate_checks, "diagnostics.delta_contains_fresh_cohort_acquired", u"cohort_acquired" in delta_events, delta_events)
    _gate(gate_checks, "diagnostics.delta_excludes_fully_reused_no_provider_open",
          u"fully_reused_no_provider_open" not in delta_events, delta_events)

    lease_counters_now = record.get("lease_counters") or {}
    _gate(gate_checks, "lease.outstanding_zero", lease_counters_now.get("outstanding_lease_count") == 0, None)
    _gate(gate_checks, "lease.unreleased_zero", lease_counters_now.get("unreleased_lease_count") == 0, None)

    failed = [g["name"] for g in gate_checks if not g["passed"]]
    out = {"gate_checks": gate_checks, "failed_gates": failed}
    if failed:
        out["classification"] = u"FAIL"
        out["gate_failure"] = u"%d I1-G2-stage check(s) failed: %s" % (len(failed), u", ".join(failed))
    else:
        out["classification"] = u"I1_PASS"
    return out


# ----------------------------------------------------------------------
# I2 handlers.
# ----------------------------------------------------------------------
def _snapshot_i2_00_baseline(record, cont, broker, authority_observation, all_shots, main_window, prod_ns):
    gate_checks = []
    _common_identity_gates(gate_checks, record)
    expected_g1_sha = cont.get("i1_baseline_master_sha256")
    expected_g2_sha = cont.get("i1_expected_g2_sha256")
    _gate(gate_checks, "identity.live_master_equals_g2",
          record.get("current_master_sha256") == expected_g2_sha,
          (record.get("current_master_sha256"), expected_g2_sha))
    _gate(gate_checks, "state.guard_state_is_unused", record.get("guard_state") == u"UNUSED", record.get("guard_state"))
    _gate(gate_checks, "state.run_lock_absent", record.get("run_lock_present") is False, record.get("run_lock_present"))

    pub_checks, publication_record = _validate_g2_publication_record(
        record, SHIPPED_AUTHORITY_DIR, expected_g1_sha, expected_g2_sha,
    )
    for name, passed in pub_checks.items():
        _gate(gate_checks, "authority.%s" % name, passed, None)
    record["g2_publication_record"] = publication_record

    act_checks, activation_record = _validate_g2_activation_record(expected_g1_sha, expected_g2_sha)
    for name, passed in act_checks.items():
        _gate(gate_checks, "activation.%s" % name, passed, None)
    record["g2_activation_record"] = activation_record

    provider_counters = record.get("provider_counters") or {}
    lease_counters = record.get("lease_counters") or {}
    _gate(gate_checks, "provider.current_open_provider_count_is_zero",
          provider_counters.get("current_open_provider_count") == 0, None)
    _gate(gate_checks, "lease.outstanding_zero", lease_counters.get("outstanding_lease_count") == 0, None)
    _gate(gate_checks, "lease.unreleased_zero", lease_counters.get("unreleased_lease_count") == 0, None)

    i2_matches = resolve_unique_shot(all_shots, I2_SHOT_NAME)
    _gate(gate_checks, "vocabulary.shot3_resolves_uniquely", len(i2_matches) == 1, len(i2_matches))
    animation_sets_seen = None
    if len(i2_matches) == 1:
        _folds, animation_sets_seen, _controls = derive_shot_vocabulary(i2_matches[0])
    _gate(gate_checks, "fixture.shot3_has_at_least_two_animation_sets",
          animation_sets_seen is not None and animation_sets_seen >= EXPECTED_I2_TARGET_COUNT, animation_sets_seen)

    failed = [g["name"] for g in gate_checks if not g["passed"]]
    out = {"gate_checks": gate_checks, "failed_gates": failed}
    if failed:
        out["classification"] = u"INCONCLUSIVE_BEFORE_EXECUTION"
        out["gate_failure"] = u"%d I2-baseline check(s) failed: %s" % (len(failed), u", ".join(failed))
        return out
    cont["i2_baseline_pid"] = record["current_pid"]
    cont["i2_baseline_provider_counters"] = record.get("provider_counters")
    cont["i2_baseline_diagnostics"] = record.get("recent_diagnostics")
    out["classification"] = u"I2_BASELINE_PASSED"
    return out


def _validate_expected_i2_instance(instance, expected_g2_sha, expected_shot_name):
    """BLOCKER 3: mechanical pre-wrap validation that the detected run
    instance is EXACTLY the expected run, before any wrapping occurs."""
    checks = {}
    checks["wrapper_not_already_installed"] = not bool(getattr(instance, "_checkpoint_i_wrapper_installed", False))
    checks["master_hash_matches_g2"] = (getattr(instance, "master_hash", None) == expected_g2_sha)

    try:
        scope_shots = list(getattr(instance, "scope_shots", []))
    except Exception:
        scope_shots = []
    shot_names = []
    for s in scope_shots:
        try:
            shot_names.append(_independent_object_name(s))
        except Exception:
            shot_names.append(u"<error>")

    checks["scope_is_exactly_one_shot"] = (len(scope_shots) == 1)
    checks["scope_shot_matches_expected"] = (shot_names == [expected_shot_name])
    checks["scope_mode_is_selected"] = (getattr(instance, "scope_mode", None) == u"SELECTED_SHOTS")
    checks["no_target_completed_yet"] = (getattr(instance, "current_target_index", None) == 0)
    checks["zero_native_attempts_so_far"] = (getattr(instance, "telemetry_native_attempts", None) == 0)
    checks["zero_native_rebuilt_so_far"] = (getattr(instance, "total_native_rebuilt", None) == 0)

    valid = all(checks.values())
    return {"valid": valid, "checks": checks, "observed_shot_names": shot_names}


def _install_i2_wrapper(instance, expected_g2_sha, expected_master_path):
    """Wraps EXACTLY ONE bound method, contextualizer_resolve_resume_
    target, with a counting closure. Call 1 (target 1) passes through
    untouched. Call 2 (target 2) performs the ONE sanctioned, hash-gated
    G2->G1 restore (igen.perform_g2_to_g1_restoration -- BLOCKER 2) and
    then calls the ORIGINAL, UNMODIFIED production method -- production's
    own self.assert_master_stable() is what detects the change. This
    closure never raises the expected exception itself.

    R2 BLOCKER 5: before performing the swap, binds the live Master path
    to the exact path the I1 baseline inventory recorded
    (expected_master_path) -- an arbitrary/unexpected path is never
    sufficient authorization by itself, even though
    CANONICAL_MASTER_INSTALLED_PATH is itself a fixed, process-derived
    constant; this is a cheap, mechanical, defense-in-depth check against
    that constant ever silently diverging from what I1 actually
    observed."""
    original_method = instance.contextualizer_resolve_resume_target
    injection_state = {"call_count": 0}

    def _wrapper(work_record, target):
        injection_state["call_count"] += 1
        call_index = injection_state["call_count"]
        if call_index == 2:
            evidence = {
                "call_index": call_index,
                "wall_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "epoch": time.time(),
                "pid": os.getpid(),
            }
            master_path_matches_baseline = igen.path_matches_baseline(
                CANONICAL_MASTER_INSTALLED_PATH, expected_master_path,
            )
            evidence["master_path_matches_baseline"] = master_path_matches_baseline
            try:
                pre_sha = hashlib.sha256(open(CANONICAL_MASTER_INSTALLED_PATH, "rb").read()).hexdigest()
            except Exception as exc:
                pre_sha = None
                evidence["pre_swap_hash_error"] = u"%r" % (exc,)
            evidence["pre_swap_master_sha256"] = pre_sha
            evidence["pre_swap_matches_expected_g2"] = (pre_sha == expected_g2_sha)
            if not master_path_matches_baseline:
                evidence["swap_performed"] = False
                evidence["swap_skipped_reason"] = (
                    u"live Master path does not match the I1 baseline "
                    u"inventory's recorded Master path -- refusing to write."
                )
            elif evidence["pre_swap_matches_expected_g2"]:
                try:
                    with open(G1_SOURCE_BYTES_BACKUP_PATH, "rb") as _gf:
                        g1_bytes = _gf.read()
                    op_record = igen.perform_g2_to_g1_restoration(
                        CANONICAL_MASTER_INSTALLED_PATH, g1_bytes, expected_g2_sha,
                    )
                    evidence["swap_performed"] = True
                    evidence["swap_operation_record"] = op_record
                except Exception as exc:
                    evidence["swap_performed"] = False
                    evidence["swap_error"] = u"%r" % (exc,)
            else:
                evidence["swap_performed"] = False
                evidence["swap_skipped_reason"] = u"pre-swap hash did not match expected G2 -- refusing to write."
            try:
                write_evidence_json_once(I2_INJECTION_RECORD_PATH, evidence)
            except Exception:
                pass
        return original_method(work_record, target)

    instance.contextualizer_resolve_resume_target = _wrapper
    instance._checkpoint_i_wrapper_installed = True


class _I2PrearmObserver(QtCore.QObject):
    """BLOCKER 3: a retained, bounded Qt timer/observer, parented
    durably to main_window, that polls (never blocks) at
    _PREARM_POLL_INTERVAL_MS for the newly-created production run
    instance, mechanically validates it, installs the wrapper, and stops
    itself -- installed BEFORE the operator ever starts the command."""

    def __init__(self, main_window, prod_ns, expected_g2_sha, expected_shot_name, evidence_path,
                 expected_master_path):
        QtCore.QObject.__init__(self, main_window)
        self._main_window = main_window
        self._prod_ns = prod_ns
        self._expected_g2_sha = expected_g2_sha
        self._expected_shot_name = expected_shot_name
        self._evidence_path = evidence_path
        self._expected_master_path = expected_master_path
        self._elapsed_ms = 0
        self._resolved = False
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(False)
        self._timer.timeout.connect(self._poll)

    def start(self):
        self._timer.start(_PREARM_POLL_INTERVAL_MS)

    def _poll(self):
        if self._resolved:
            return
        self._elapsed_ms += _PREARM_POLL_INTERVAL_MS
        try:
            instance = self._prod_ns["_find_existing_run"](self._main_window)
        except Exception:
            instance = None

        if instance is not None:
            validation = _validate_expected_i2_instance(instance, self._expected_g2_sha, self._expected_shot_name)
            if validation["valid"]:
                _install_i2_wrapper(instance, self._expected_g2_sha, self._expected_master_path)
                self._finish({"outcome": u"ARMED", "elapsed_ms": self._elapsed_ms, "validation": validation})
            else:
                self._finish({"outcome": u"UNEXPECTED_RUN", "elapsed_ms": self._elapsed_ms, "validation": validation})
            return

        if self._elapsed_ms >= _PREARM_TIMEOUT_MS:
            self._finish({"outcome": u"TIMEOUT", "elapsed_ms": self._elapsed_ms})

    def _finish(self, result):
        self._resolved = True
        result["wall_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        result["pid"] = os.getpid()
        try:
            write_evidence_json_once(self._evidence_path, result)
        except Exception:
            pass
        self._timer.stop()


def _snapshot_i2_01_prearm(record, cont, broker, authority_observation, all_shots, main_window, prod_ns):
    """BLOCKER 3 (round 1) + R2 BLOCKER 3 (this correction round):
    installs the retained prearm observer BEFORE the operator ever
    starts the command -- never a synchronous "arm after start()" step.
    Returns immediately; arming resolves asynchronously, verified later
    at i2_02 via the observer's own persisted evidence.

    R2 BLOCKER 3: round 1 did NOT call _common_identity_gates() here --
    a wrong production/runtime/fixture identity could have gone
    undetected right up until the observer was installed. This snapshot
    now mechanically re-gates the FULL governing identity (production
    SHA, runtime API/build/canonical, main window, fixture identity,
    shot enumerability/count) plus every I2-specific precondition,
    including the two evidence-chain records (G2 publication AND G2
    Master activation -- R2 BLOCKER 1), zero open providers/leases, and
    a HASH-VERIFIED (not merely existence-checked) G1 backup, before the
    observer is ever installed. Any failure: INCONCLUSIVE_BEFORE_
    EXECUTION, observer NOT installed."""
    gate_checks = []
    _common_identity_gates(gate_checks, record)
    _gate(gate_checks, "continuity.same_pid_as_i2_baseline",
          record.get("current_pid") == cont.get("i2_baseline_pid"),
          (record.get("current_pid"), cont.get("i2_baseline_pid")))
    _gate(gate_checks, "state.guard_state_is_unused", record.get("guard_state") == u"UNUSED", record.get("guard_state"))
    _gate(gate_checks, "state.run_lock_absent", record.get("run_lock_present") is False, record.get("run_lock_present"))

    expected_g1_sha = cont.get("i1_baseline_master_sha256")
    expected_g2_sha = cont.get("i1_expected_g2_sha256")
    _gate(gate_checks, "identity.live_master_equals_g2", record.get("current_master_sha256") == expected_g2_sha,
          record.get("current_master_sha256"))

    pub_checks, publication_record = _validate_g2_publication_record(
        record, SHIPPED_AUTHORITY_DIR, expected_g1_sha, expected_g2_sha,
    )
    for name, passed in pub_checks.items():
        _gate(gate_checks, "authority.%s" % name, passed, None)
    record["g2_publication_record"] = publication_record

    act_checks, activation_record = _validate_g2_activation_record(expected_g1_sha, expected_g2_sha)
    for name, passed in act_checks.items():
        _gate(gate_checks, "activation.%s" % name, passed, None)
    record["g2_activation_record"] = activation_record

    provider_counters = record.get("provider_counters") or {}
    lease_counters = record.get("lease_counters") or {}
    _gate(gate_checks, "provider.current_open_provider_count_is_zero",
          provider_counters.get("current_open_provider_count") == 0, provider_counters.get("current_open_provider_count"))
    _gate(gate_checks, "lease.outstanding_lease_count_is_zero",
          lease_counters.get("outstanding_lease_count") == 0, lease_counters.get("outstanding_lease_count"))
    _gate(gate_checks, "lease.unreleased_lease_count_is_zero",
          lease_counters.get("unreleased_lease_count") == 0, lease_counters.get("unreleased_lease_count"))

    baseline_inventory = cont.get("i1_baseline_inventory") or {}
    expected_master_path = baseline_inventory.get("master_path")
    _gate(gate_checks, "injection.baseline_master_path_known", bool(expected_master_path), expected_master_path)

    g1_backup_hash_ok = False
    g1_backup_actual_sha = None
    if os.path.exists(G1_SOURCE_BYTES_BACKUP_PATH):
        try:
            with open(G1_SOURCE_BYTES_BACKUP_PATH, "rb") as _gbf:
                g1_backup_actual_sha = hashlib.sha256(_gbf.read()).hexdigest()
            g1_backup_hash_ok = (g1_backup_actual_sha == EXPECTED_G1_MASTER_SHA256)
        except Exception as exc:
            record["g1_backup_hash_error"] = u"%r" % (exc,)
    _gate(gate_checks, "injection.g1_source_bytes_backup_hashes_to_canonical_g1",
          g1_backup_hash_ok, g1_backup_actual_sha)

    _gate(gate_checks, "injection.prod_ns_available", prod_ns is not None, None)
    _gate(gate_checks, "injection.main_window_available", main_window is not None, None)
    _gate(gate_checks, "injection.not_already_prearmed", cont.get("i2_prearmed") is not True, cont.get("i2_prearmed"))

    failed = [g["name"] for g in gate_checks if not g["passed"]]
    out = {"gate_checks": gate_checks, "failed_gates": failed}
    if failed:
        out["classification"] = u"INCONCLUSIVE_BEFORE_EXECUTION"
        out["gate_failure"] = u"%d prearm pre-condition(s) failed -- observer NOT installed: %s" % (
            len(failed), u", ".join(failed)
        )
        return out

    global _RETAINED_PREARM_OBSERVER
    observer = _I2PrearmObserver(
        main_window, prod_ns, expected_g2_sha, I2_SHOT_NAME, I2_PREARM_RESULT_PATH, expected_master_path,
    )
    observer.start()
    _RETAINED_PREARM_OBSERVER = observer
    try:
        main_window._checkpoint_i_prearm_observer_keepalive = observer
    except Exception:
        pass

    cont["i2_prearmed"] = True
    out["classification"] = u"PREARM_INSTALLED"
    out["prearm_note"] = (
        u"Observer running asynchronously in the background (poll interval "
        u"%dms, timeout %dms). Invoke Rebuild Control Groups -> Selected "
        u"Shot(s) -> shot3 now. Run this checkpoint again AFTER the "
        u"command finishes to verify arming evidence." % (_PREARM_POLL_INTERVAL_MS, _PREARM_TIMEOUT_MS)
    )
    return out


def _snapshot_i2_02_verify(record, cont, broker, authority_observation, all_shots, main_window, prod_ns):
    gate_checks = []
    _common_identity_gates(gate_checks, record)
    _gate(gate_checks, "continuity.same_pid_as_i2_baseline",
          record.get("current_pid") == cont.get("i2_baseline_pid"),
          (record.get("current_pid"), cont.get("i2_baseline_pid")))
    _gate(gate_checks, "state.guard_state_remains_selected_used",
          record.get("guard_state") == u"SELECTED_USED", record.get("guard_state"))
    _gate(gate_checks, "state.run_lock_absent", record.get("run_lock_present") is False, record.get("run_lock_present"))

    expected_g1_sha = cont.get("i1_baseline_master_sha256")
    _gate(gate_checks, "generation.live_master_now_exactly_canonical_g1",
          record.get("current_master_sha256") == expected_g1_sha, record.get("current_master_sha256"))

    # BLOCKER 3: prove the wrapper was installed before target 1 from
    # PERSISTED evidence, never from timing reasoning alone.
    prearm_result = igen.read_finalization_record_plain(I2_PREARM_RESULT_PATH)
    _gate(gate_checks, "prearm.result_present", prearm_result is not None, None)
    _gate(gate_checks, "prearm.outcome_armed",
          prearm_result is not None and prearm_result.get("outcome") == u"ARMED",
          prearm_result.get("outcome") if prearm_result else None)
    validation = (prearm_result or {}).get("validation") or {}
    pre_checks = validation.get("checks") or {}
    _gate(gate_checks, "prearm.armed_before_any_target_completed", pre_checks.get("no_target_completed_yet") is True, None)
    _gate(gate_checks, "prearm.armed_with_zero_native_attempts", pre_checks.get("zero_native_attempts_so_far") is True, None)
    _gate(gate_checks, "prearm.armed_with_zero_native_rebuilt", pre_checks.get("zero_native_rebuilt_so_far") is True, None)
    _gate(gate_checks, "prearm.armed_correct_shot_scope", pre_checks.get("scope_shot_matches_expected") is True, None)
    _gate(gate_checks, "prearm.armed_correct_master_hash", pre_checks.get("master_hash_matches_g2") is True, None)
    record["prearm_result"] = prearm_result

    run_captured = record.get("run_captured")
    _gate(gate_checks, "run.exactly_one_new_run03_log_captured",
          run_captured is not None and run_captured.get("step_ordinal") == 3,
          run_captured.get("step_ordinal") if run_captured else None)
    log_verification = (run_captured or {}).get("log_verification") or {}

    _gate(gate_checks, "run.final_report_entry_present", log_verification.get("final_report_entry_present") is True, None)
    _gate(gate_checks, "run.explicit_production_fail", log_verification.get("production_fail_present") is True, None)
    _gate(gate_checks, "run.no_explicit_production_pass", log_verification.get("production_pass_present") is False, None)
    _gate(gate_checks, "run.master_changed_message_present",
          log_verification.get("master_changed_message_present") is True, None)
    _gate(gate_checks, "run.target_callback_abort_present",
          log_verification.get("target_callback_abort_present") is True, None)
    _gate(gate_checks, "run.exactly_one_pre_native", log_verification.get("pre_native_count") == 1,
          log_verification.get("pre_native_count"))
    _gate(gate_checks, "run.exactly_one_native_rebuild_returned",
          log_verification.get("native_rebuild_returned_count") == 1,
          log_verification.get("native_rebuild_returned_count"))
    _gate(gate_checks, "run.logged_master_sha256_equals_g2",
          log_verification.get("logged_master_sha256") == cont.get("i1_expected_g2_sha256"),
          log_verification.get("logged_master_sha256"))

    injection_evidence = igen.read_finalization_record_plain(I2_INJECTION_RECORD_PATH)
    _gate(gate_checks, "injection.evidence_present", injection_evidence is not None, None)
    _gate(gate_checks, "injection.occurred_exactly_at_call_index_two",
          injection_evidence is not None and injection_evidence.get("call_index") == 2, None)
    _gate(gate_checks, "injection.pre_swap_matched_expected_g2",
          injection_evidence is not None and injection_evidence.get("pre_swap_matches_expected_g2") is True, None)
    _gate(gate_checks, "injection.swap_performed",
          injection_evidence is not None and injection_evidence.get("swap_performed") is True, None)
    swap_op = (injection_evidence or {}).get("swap_operation_record") or {}
    _gate(gate_checks, "injection.swap_post_hash_equals_g1",
          swap_op.get("post_operation_master_sha256") == expected_g1_sha,
          swap_op.get("post_operation_master_sha256"))
    record["injection_evidence"] = injection_evidence

    diagnostics_now = record.get("recent_diagnostics") or []
    baseline_diag = cont.get("i2_baseline_diagnostics") or []
    delta, delta_clean = diagnostics_delta(baseline_diag, diagnostics_now)
    delta_events = [e.get("event") for e in delta]
    cohort_acquired_count = delta_events.count(u"cohort_acquired")
    _gate(gate_checks, "diagnostics.delta_continuity_established", delta_clean, None)
    _gate(gate_checks, "diagnostics.exactly_one_cohort_acquired_no_post_swap_reacquisition",
          cohort_acquired_count == 1, cohort_acquired_count)

    provider_counters_now = record.get("provider_counters") or {}
    lease_counters_now = record.get("lease_counters") or {}
    _gate(gate_checks, "provider.current_open_provider_count_is_zero",
          provider_counters_now.get("current_open_provider_count") == 0, provider_counters_now.get("current_open_provider_count"))
    _gate(gate_checks, "lease.outstanding_zero", lease_counters_now.get("outstanding_lease_count") == 0, None)
    _gate(gate_checks, "lease.unreleased_zero", lease_counters_now.get("unreleased_lease_count") == 0, None)

    failed = [g["name"] for g in gate_checks if not g["passed"]]
    out = {"gate_checks": gate_checks, "failed_gates": failed}
    if failed:
        out["classification"] = u"FAIL"
        out["gate_failure"] = u"%d I2 verification check(s) failed: %s" % (len(failed), u", ".join(failed))
    else:
        out["classification"] = u"I2_FAIL_CLOSED_PASS"
    return out


# ----------------------------------------------------------------------
# BLOCKER 8/9: final restoration-verification snapshot. Read-only. Run
# AFTER SFM has been reopened following the external finalizer.
# ----------------------------------------------------------------------
def _snapshot_i_08_finalize_verify(record, cont, broker, authority_observation, all_shots, main_window, prod_ns):
    gate_checks = []
    _common_identity_gates(gate_checks, record)
    expected_g1_sha = cont.get("i1_baseline_master_sha256") or EXPECTED_G1_MASTER_SHA256
    _gate(gate_checks, "generation.live_master_is_exactly_canonical_g1",
          record.get("current_master_sha256") == expected_g1_sha, record.get("current_master_sha256"))
    _gate(gate_checks, "state.guard_state_is_unused", record.get("guard_state") == u"UNUSED", record.get("guard_state"))

    finalization_record = igen.read_finalization_record_plain(FINALIZATION_RECORD_PATH)
    _gate(gate_checks, "finalization.record_present", finalization_record is not None, None)
    _gate(gate_checks, "finalization.exact_match_true",
          finalization_record is not None and finalization_record.get("exact_match") is True,
          finalization_record.get("exact_match") if finalization_record else None)
    record["finalization_record"] = finalization_record

    # R2 BLOCKER 6: consume the standalone, checkpoint-generated baseline
    # inventory ARTIFACT FILE directly -- never the operator manually
    # extracting nested JSON from Snapshot 01, and never only this
    # process's own in-memory continuation state.
    baseline_inventory = igen.read_finalization_record_plain(BASELINE_INVENTORY_ARTIFACT_PATH)
    _gate(gate_checks, "finalization.baseline_inventory_artifact_present", baseline_inventory is not None, None)
    live_inventory = None
    comparison_here = None
    if baseline_inventory is not None:
        try:
            live_inventory = igen.capture_live_state_inventory(CANONICAL_MASTER_INSTALLED_PATH, SHIPPED_AUTHORITY_DIR)
            comparison_here = igen.compare_inventories(baseline_inventory, live_inventory)
        except Exception as exc:
            record["independent_inventory_error"] = u"%r" % (exc,)
    _gate(gate_checks, "finalization.independent_reverification_exact_match",
          comparison_here is not None and comparison_here.get("exact_match") is True,
          comparison_here.get("exact_match") if comparison_here else None)
    record["independent_live_inventory"] = live_inventory
    record["independent_comparison_to_baseline"] = comparison_here

    failed = [g["name"] for g in gate_checks if not g["passed"]]
    out = {"gate_checks": gate_checks, "failed_gates": failed}
    if failed:
        out["classification"] = u"RESTORATION_NOT_CONFIRMED"
        out["gate_failure"] = u"%d finalization check(s) failed: %s" % (len(failed), u", ".join(failed))
    else:
        out["classification"] = u"RESTORATION_CONFIRMED"
    return out


main()
