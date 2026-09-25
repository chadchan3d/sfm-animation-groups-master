# -*- coding: utf-8 -*-
"""
Checkpoint G (Later/Different Vocabulary) -- real-SFM qualification of the
narrow G proposition:

  Within one SFM process and one unchanged canonical Master generation,
  after a successful Normalizer command has acquired a projection for
  command vocabulary V1, a later legitimate Normalizer command whose
  vocabulary V2 differs from V1 and contains at least one fold absent
  from V1 must acquire/materialize authority covering V2 under that same
  generation. The earlier V1 projection must never be silently treated
  as authoritative for V2.

This is explicitly NOT generation replacement (roadmap item I). This
checkpoint never edits the Master, never republishes the sidecar, never
tests mid-command generation drift.

**Prepared 2026-09-25. NOT yet run against real SFM.**

**CORRECTION ROUND 2 (2026-09-25, independent review of the first
prepared package)** -- five blockers fixed before any real-SFM run:
  1. verify_run_log_content() previously accepted FINAL_REPORT_ENTRY as
     equivalent to an explicit production PASS. FINAL_REPORT_ENTRY is
     logged unconditionally by final_report() BEFORE the PASS/FAIL
     decision is even computed (Rebuild_Control_Groups_Normalizer.py
     lines ~13292-13775) -- it is a completion marker, not success
     evidence. Corrected to require FINAL_REPORT_ENTRY AND an explicit
     "PRODUCTION_REBUILD_CONTROL_GROUPS = PASS" line, and to fail
     outright on an explicit "= FAIL" line.
  2. Snapshot 01's HARD_GATES_PASSED previously only gated vocabulary/
     cache-key conditions. Now mechanically gates every governing
     condition (identities, guard state, provider/lease counters,
     fixture identity, project size, vocabulary, cache-key cleanliness)
     via one exhaustive gate_checks list -- any single failure produces
     INCONCLUSIVE_BEFORE_EXECUTION with the exact failed-check names.
  3. Snapshot 02 previously always classified RECORDED unconditionally.
     Now mechanically evaluates the V1 stage against 20+ hard checks and
     classifies V1_STAGE_PASSED or FAIL with exact failed-check names.
     INSTRUCTIONS.md now says: do not run command 2 unless Snapshot 02
     reports V1_STAGE_PASSED.
  4. Snapshot 03 previously always classified RECORDED unconditionally.
     Now mechanically evaluates the full G proposition and classifies
     G_PASS or FAIL with exact failed-check names, exposed directly in
     the final rollup (mechanical_final_verdict /
     mechanical_final_failed_checks) rather than requiring a reviewer to
     reconstruct the verdict from three separate files by hand.
  5. The V2-only Known witness previously stopped at the coverage index
     (status == Known). Now additionally inspects the view's ACTUAL
     view.payload["folded"][folded_key] rows against that same fold's
     coverage destination/occurrences, and separately requires the
     view's entire payload["folded"].keys() to exactly equal the set of
     requested folds whose coverage status is Known (never fewer, never
     more), and requires the run log's own logged matched_folds field to
     equal both the view's own known_count and its own
     payload_folded_key_count -- proving the witness (and the whole
     projection) is really materialized, not merely reported covered.

This is a pure READ-ONLY OBSERVER. It never invokes the Normalizer,
never invokes native Rebuild, never mutates the scene, never changes
shot selection, never acquires an authority projection itself, never
opens a provider, and never saves the project. The operator invokes the
real, ordinary "Rebuild Control Groups" command manually, between this
script's own three invocations.

Architecture facts this design relies on (independently verified by
direct source inspection against the accepted package,
tests/sidecar/qualification/candidate_b2c_correction6/
sfm_master_authority_productionized/, confirmed byte-identical to the
live-deployed copy at ChadChan3D/sfm_master_authority_productionized/,
before writing this script):
  - production's own acquire_master_index_via_qualified_authority()
    requests consumer kind "normalizer_compat" with
    expected_generation=self.master_hash (Rebuild_Control_Groups_
    Normalizer.py lines ~10059-10134).
  - broker.acquire_or_reuse_views()'s own cache-key formula (broker.py
    line ~498): (h0.sha256, None, frozenset(folded_keys), consumer_kind)
    -- reproduced here verbatim as a constant formula, never imported
    from production, so this checkpoint can independently construct the
    exact V1/V2 cache keys and query the broker's cache directly.
  - runtime.get_broker() returns the SAME broker object on every call
    once READY in a process (runtime.py docstring) -- calling it merely
    constructs/returns the resident Broker object; it never opens a
    sidecar or touches the Master (runtime.py module docstring). Safe
    for a read-only observer to call.
  - the authority package (sfm_master_authority_productionized/*) has
    ZERO SFM-only import dependencies (confirmed: no `import sfmApp`,
    `import sfmClipEditor`, or `import vs` anywhere in the package) --
    unlike production itself, it can be imported directly, both offline
    and in real SFM, with no line-range-extraction workaround needed.
  - DetachedView.cache_key() / is_stale() / coverage.covered_keys() /
    coverage.lookup(folded_key) -> CoverageResult(status, destination,
    occurrences) with status in {"Known", "MasterUnknown", "Uncovered"}
    (views.py). view.payload["folded"][folded_key] is only ever
    populated for Known folds (normalizer_compat_adapter.py's own
    builder never inserts a MasterUnknown/Uncovered fold into
    payload["folded"] -- confirmed by direct source inspection).
  - broker.provider_counters() / view_cache_entry_count() /
    outstanding_lease_count() / unreleased_lease_count() /
    recent_diagnostics() / cached_view(cache_key) are all read-only.
  - production's own log line (~14152-14165):
    "CONTEXTUALIZER_SCOPED_MASTER_INDEX_BUILD = PASS
    unique_scope_folds=%d matched_folds=%d ..." where matched_folds ==
    len(self.master_index["folded"]) -- the same field name this
    checkpoint independently cross-checks against the view's own
    known_count/payload_folded_key_count.
  - final_report() (lines ~13292-13775) logs "FINAL_REPORT_ENTRY"
    unconditionally near the START of finalization, THEN computes
    success, THEN logs "PRODUCTION_REBUILD_CONTROL_GROUPS = PASS" or
    "= FAIL" -- FINAL_REPORT_ENTRY alone never implies PASS.

V1/V2 vocabulary is derived INDEPENDENTLY here -- this script never
calls production's own collect_scope_master_wanted_folds(). It uses
fresh, self-contained reimplementations of the same neutral, stated
rule (ASCII-fold every control name in every animation set of the named
shot), not extracted from or shared with production's own code, so the
witness is a genuine independent check, not a restatement of the same
implementation.

Fixture identity is verified using the SAME technique
checkpoint_f2_r1's own already-qualified script uses (sfmApp.
GetDocumentRoot().GetFileId() -> vs.g_pDataModel.GetFileName(file_id) ->
os.path.basename()), never assumed from shot names alone, plus the
established 15-shot project size for this exact fixture (F3-Guard's own
real-SFM-confirmed "scope_mode=ALL_SHOTS scope_shots=15").

Evidence-file discipline matches this project's established convention
(real_sfm_qualification/checkpoint_process_attempt_guard/): every
snapshot/run is written to a NEW, uniquely-numbered, IMMUTABLE file;
write_evidence_*_once() refuses (raises) rather than silently
overwriting an existing path; only a small, explicitly non-evidentiary
continuation-state pointer file and the freely-overwritten final rollup
are ever replaced.
"""
import hashlib
import json
import os
import sys
import time

from PySide import QtCore

# ----------------------------------------------------------------------
# Governing identities this checkpoint is pinned against.
# ----------------------------------------------------------------------
EXPECTED_PRODUCTION_SHA256 = (
    "1f4ec5a26605aa90380eb0532fec3915d2cc24a3a20473ed70d57198bd995db7"
)
EXPECTED_CANONICAL_MASTER_SHA256 = (
    "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
)
EXPECTED_RUNTIME_API_VERSION = u"1.0.0-b2a"
EXPECTED_RUNTIME_BUILD_ID = u"package-boundary-corrected-2026-09-22"

PRODUCTION_INSTALLED_PATH = (
    "E:\\SteamLibrary\\steamapps\\common\\SourceFilmmaker\\game\\usermod"
    "\\scripts\\sfm\\mainmenu\\ChadChan3D\\Rebuild_Control_Groups_Normalizer.py"
)
# Same game_root-relative derivation the project's other real-SFM
# checkpoints already use (checkpoint_f2_r1, checkpoint_a) for an
# independent, read-only re-hash of the live canonical Master -- never
# opened for write, never parsed beyond a byte-for-byte SHA-256.
CANONICAL_MASTER_INSTALLED_PATH = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)),
    "usermod", "cfg", "sfm_defaultanimationgroups.txt",
)

# Exact source line ranges (1-indexed, inclusive) for the small handful
# of pure-Python/Qt definitions this checkpoint needs from production's
# own process-lifetime guard, verified against the pinned SHA-256 above
# via grep/Read immediately before writing this script -- identical to,
# and independently re-verified from, the ranges
# checkpoint_process_attempt_guard's own script uses (unaffected by the
# F-closeout copy-only edit, which only touched lines ~9420+, entirely
# after every range below).
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
V1_SHOT_NAME = u"shot3"
V2_SHOT_NAME = u"shot9"

# Fixture identity gate (BLOCKER 2) -- reuses checkpoint_f2_r1's own
# already-qualified technique/constants rather than inventing a new one.
EXPECTED_FIXTURE_FILENAME = u"F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx"
FORBIDDEN_ORIGINAL_FIXTURE_FILENAME = u"testscripts.dmx"
EXPECTED_PROJECT_SHOT_COUNT = 15

EVIDENCE_DIR = "C:\\Users\\Public\\Documents\\"
CONTINUATION_STATE_PATH = EVIDENCE_DIR + "sfm_checkpoint_g_continuation_state.json"
FINAL_RESULT_PATH = EVIDENCE_DIR + "sfm_checkpoint_g_final_result.json"
FINAL_SUMMARY_PATH = EVIDENCE_DIR + "sfm_checkpoint_g_final_summary.txt"

SNAPSHOT_SCHEDULE = [
    (u"baseline", u"UNUSED"),
    (u"after_v1", u"SELECTED_USED"),
    (u"after_v2", u"SELECTED_USED"),
]
RUN_LOG_LABELS = [
    u"v1_shot3",
    u"v2_shot9",
]


class CheckpointGError(Exception):
    pass


# ----------------------------------------------------------------------
# Atomic-write primitives -- verbatim pattern reused from
# checkpoint_process_attempt_guard/Checkpoint_Process_Attempt_Guard_
# Qualification.py (the established, already-qualified project pattern).
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
        raise CheckpointGError(
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
        raise CheckpointGError(
            "Refusing to overwrite existing evidence file (rename "
            "failed, target likely already exists): %r (%r)" % (path, exc)
        )
    return reparsed


def write_evidence_text_once(path, text_bytes):
    if os.path.exists(path):
        raise CheckpointGError(
            "Refusing to overwrite existing evidence file: %r" % (path,)
        )
    tmp_path = path + ".tmp"
    fp = open(tmp_path, "wb")
    try:
        fp.write(text_bytes)
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
        raise CheckpointGError(
            "Refusing to overwrite existing evidence file (rename "
            "failed, target likely already exists): %r (%r)" % (path, exc)
        )


def read_continuation_state():
    if not os.path.exists(CONTINUATION_STATE_PATH):
        return {
            "next_snapshot_index": 1,
            "next_run_index": 1,
            "last_known_log_sha256": None,
            "captured_snapshots": [],
            "captured_runs": [],
            "witness": None,
            "baseline_pid": None,
            "baseline_master_sha256": None,
            "baseline_provider_counters": None,
            "baseline_diagnostics": None,
            "v1_stage_provider_counters": None,
            "v1_stage_diagnostics": None,
        }
    fp = open(CONTINUATION_STATE_PATH, "rb")
    try:
        raw = fp.read()
    finally:
        fp.close()
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise CheckpointGError(
            "continuation-state file is present but could not be "
            "parsed: %r -- refusing to guess." % (exc,)
        )
    for required_key in (
        "next_snapshot_index", "next_run_index", "last_known_log_sha256",
        "captured_snapshots", "captured_runs", "witness",
        "baseline_pid", "baseline_master_sha256",
        "baseline_provider_counters", "baseline_diagnostics",
        "v1_stage_provider_counters", "v1_stage_diagnostics",
    ):
        if required_key not in parsed:
            raise CheckpointGError(
                "continuation-state file is present but missing expected "
                "key %r -- refusing to guess." % (required_key,)
            )
    return parsed


# ----------------------------------------------------------------------
# Production guard-state extraction (verbatim technique reused from
# checkpoint_process_attempt_guard) -- production itself has SFM-only
# import dependencies, so only these small, pure definitions are
# extracted by exact line range, never a whole-file exec().
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
            raise CheckpointGError(
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


def verify_run_log_content(raw_bytes, expected_shot_name, expected_unique_scope_folds):
    """Read-only, purely textual verification of one preserved production
    log against the independently-derived witness -- never re-derives the
    vocabulary itself, only checks the log's own self-reported facts
    against what this checkpoint already computed independently at
    baseline. Never raises; returns a structured result dict so callers
    (main() and the offline test alike) can inspect every individual
    check.

    BLOCKER 1 correction: FINAL_REPORT_ENTRY is captured as its own
    field but is NEVER sufficient for all_checks_pass by itself --
    final_report() logs it unconditionally, before success is even
    computed (Rebuild_Control_Groups_Normalizer.py lines ~13292-13775).
    An explicit "PRODUCTION_REBUILD_CONTROL_GROUPS = PASS" line is
    independently required, and an explicit "= FAIL" line forces
    all_checks_pass False even if every other check passed."""
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

    unique_scope_folds_matches = (
        logged_unique_scope_folds is not None
        and logged_unique_scope_folds == expected_unique_scope_folds
    )

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
        "all_checks_pass": (
            scope_selected_present
            and exact_single_shot_present
            and final_report_entry_present
            and production_pass_present
            and (not production_fail_present)
            and unique_scope_folds_matches
        ),
    }


# ----------------------------------------------------------------------
# Independent vocabulary derivation -- fresh, self-contained
# reimplementations of the neutral rule production's own
# collect_scope_master_wanted_folds() uses, written here from scratch,
# never extracted from or delegating to production's own code, so this
# is a genuine independent witness rather than a restatement of the
# same implementation under test.
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
    """Returns (folds_set, provenance_dict, animation_sets_seen,
    controls_seen). provenance_dict maps folded_key -> list of
    {"literal", "animation_set"} dicts sufficient to identify which
    actual shot/animation-set/control produced each fold."""
    folds = set()
    provenance = {}
    animation_sets_seen = 0
    controls_seen = 0
    for aset in shot.animationSets:
        animation_sets_seen += 1
        aset_name = _independent_object_name(aset)
        for control in _independent_control_array(aset):
            controls_seen += 1
            literal = _independent_object_name(control)
            folded = _independent_ascii_fold(literal)
            folds.add(folded)
            provenance.setdefault(folded, [])
            provenance[folded].append({
                "literal": literal,
                "animation_set": aset_name,
            })
    return folds, provenance, animation_sets_seen, controls_seen


def resolve_unique_shot(all_shots, shot_name):
    matches = []
    for shot in all_shots:
        if _independent_object_name(shot) == shot_name:
            matches.append(shot)
    return matches


def cache_key_for(master_sha256, folds, consumer_kind):
    # Reproduces broker.acquire_or_reuse_views()'s own documented cache-
    # key formula verbatim, as a constant formula independently
    # implemented here -- never imported from production or the
    # authority package's own internals -- so this checkpoint can query
    # the broker's cache directly without performing any acquisition
    # itself.
    return (master_sha256, None, frozenset(folds), consumer_kind)


# ----------------------------------------------------------------------
# Diagnostic-delta helper (DIAGNOSTIC DELTAS correction) -- mechanically
# identifies the recent_diagnostics() entries added since a prior
# snapshot's own persisted list, tolerating the broker's bounded
# _MAX_DIAGNOSTICS eviction of the oldest head entries but never
# tolerating reordering. Used instead of a loose/cumulative search.
# ----------------------------------------------------------------------
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
# Authority package import. Zero SFM-only dependencies (verified by
# direct source inspection before writing this script) -- safe to
# import directly, both offline and in real SFM.
# ----------------------------------------------------------------------
def _locate_mainmenu_dir():
    # Deliberately duplicates production's own
    # _authority_locate_mainmenu_dir() formula rather than importing or
    # calling it -- this checkpoint does not exec/import production at
    # all beyond the small guard-state line-range extraction above.
    game_root = os.path.dirname(os.path.abspath(sys.executable))
    return os.path.join(
        game_root, "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
    )


def import_authority_runtime():
    mainmenu_dir = _locate_mainmenu_dir()
    if mainmenu_dir not in sys.path:
        sys.path.insert(0, mainmenu_dir)
    from sfm_master_authority_productionized import runtime as authority_runtime
    from sfm_master_authority_productionized import errors as authority_errors
    from sfm_master_authority_productionized import observation as authority_observation
    return authority_runtime, authority_errors, authority_observation


def get_canonical_broker(authority_runtime):
    # Read-only per this package's own module docstring: constructs/
    # returns the resident Broker object only -- never opens a sidecar,
    # never touches the Master, never acquires a provider.
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
    per_fold = {}
    known_count = 0
    master_unknown_count = 0
    uncovered_count = 0
    for fold in sorted(requested_folds):
        result = view.coverage.lookup(fold)
        per_fold[fold] = {
            "status": result.status,
            "destination": result.destination,
            "occurrences": result.occurrences,
        }
        if result.status == u"Known":
            known_count += 1
        elif result.status == u"MasterUnknown":
            master_unknown_count += 1
        else:
            uncovered_count += 1

    payload_folded_keys = None
    try:
        payload_folded_keys = sorted(view.payload.get("folded", {}).keys())
    except Exception:
        payload_folded_keys = None

    known_folds_sorted = sorted(
        fold for fold, entry in per_fold.items() if entry["status"] == u"Known"
    )
    payload_keys_match_known_folds = (
        payload_folded_keys is not None
        and payload_folded_keys == known_folds_sorted
    )
    payload_folded_key_count_matches_known_count = (
        payload_folded_keys is not None
        and len(payload_folded_keys) == known_count
    )

    return {
        "present": True,
        "is_stale": view.is_stale(),
        "consumer_kind": view.consumer_kind,
        "semantic_generation_master_sha256": view.semantic_generation.master_sha256,
        "covered_keys_sorted": sorted(covered),
        "covered_keys_equals_requested": (covered == frozenset(requested_folds)),
        "per_requested_fold": per_fold,
        "known_count": known_count,
        "master_unknown_count": master_unknown_count,
        "uncovered_count": uncovered_count,
        "known_folds_sorted": known_folds_sorted,
        "payload_folded_key_count": (
            len(payload_folded_keys) if payload_folded_keys is not None else None
        ),
        "payload_folded_keys_sorted": payload_folded_keys,
        "payload_keys_match_known_folds": payload_keys_match_known_folds,
        "payload_folded_key_count_matches_known_count": (
            payload_folded_key_count_matches_known_count
        ),
    }


def inspect_witness_payload_row(view, folded_key):
    """Direct, read-only inspection of one fold's ACTUAL
    view.payload["folded"][folded_key] rows against that SAME fold's own
    coverage result (BLOCKER 5) -- proves a Known witness is really
    materialized in the payload, not merely reported Known by the
    coverage index alone. A Known-coverage fold missing from the payload
    (present_in_payload False) is reported, not silently treated as a
    valid witness."""
    coverage_result = view.coverage.lookup(folded_key)
    try:
        payload_rows = view.payload.get("folded", {}).get(folded_key)
    except Exception:
        payload_rows = None

    present_in_payload = payload_rows is not None
    occurrences = coverage_result.occurrences
    row_count_matches_occurrences = (
        present_in_payload
        and occurrences is not None
        and len(payload_rows) == len(occurrences)
    )

    destinations_consistent = False
    row_destinations_sorted = None
    if present_in_payload:
        if isinstance(coverage_result.destination, list):
            expected_destinations = set(coverage_result.destination)
        elif coverage_result.destination is not None:
            expected_destinations = set([coverage_result.destination])
        else:
            expected_destinations = set()
        row_destinations = set(row.get("destination") for row in payload_rows)
        row_destinations_sorted = sorted(row_destinations)
        destinations_consistent = (
            len(row_destinations) > 0
            and row_destinations.issubset(expected_destinations)
        )

    return {
        "coverage_status": coverage_result.status,
        "coverage_destination": coverage_result.destination,
        "coverage_occurrences": occurrences,
        "present_in_payload": present_in_payload,
        "payload_row_count": (len(payload_rows) if present_in_payload else None),
        "payload_row_destinations_sorted": row_destinations_sorted,
        "row_count_matches_occurrences": row_count_matches_occurrences,
        "destinations_consistent_with_coverage": destinations_consistent,
        "internally_consistent": (
            coverage_result.status == u"Known"
            and present_in_payload
            and row_count_matches_occurrences
            and destinations_consistent
        ),
    }


def find_v2_only_known_witness(view_inspection, v2_only_folds):
    if not view_inspection.get("present"):
        return None
    per_fold = view_inspection.get("per_requested_fold", {})
    for fold in sorted(v2_only_folds):
        entry = per_fold.get(fold)
        if entry is not None and entry.get("status") == u"Known":
            return {"folded_key": fold, "coverage": entry}
    return None


def main():
    cont = read_continuation_state()
    snapshot_index = cont["next_snapshot_index"]
    if snapshot_index - 1 < len(SNAPSHOT_SCHEDULE):
        operation_label, expected_state = SNAPSHOT_SCHEDULE[snapshot_index - 1]
    else:
        operation_label, expected_state = u"unscheduled_extra_snapshot", None

    record = {
        "wall_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "epoch": time.time(),
        "current_pid": os.getpid(),
        "snapshot_index": snapshot_index,
        "operation": operation_label,
        "expected_state": expected_state,
    }

    # --- Identities ---
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
            canonical_master_sha256 = hashlib.sha256(_mf.read()).hexdigest()
        record["canonical_master_sha256"] = canonical_master_sha256
        record["canonical_master_sha256_matches_expected"] = (
            canonical_master_sha256 == EXPECTED_CANONICAL_MASTER_SHA256
        )
    except Exception as exc:
        record["canonical_master_sha256"] = None
        record["canonical_master_sha256_matches_expected"] = False
        record["canonical_master_read_error"] = u"%r" % (exc,)

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

    # --- Authority runtime/broker (read-only) ---
    authority_runtime = None
    authority_errors = None
    authority_observation = None
    broker = None
    try:
        authority_runtime, authority_errors, authority_observation = import_authority_runtime()
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
            raise CheckpointGError(
                "Detected a production-log change beyond the fixed "
                "%d-entry run-evidence schedule (run_index=%d)."
                % (len(RUN_LOG_LABELS), run_index)
            )
        run_label = RUN_LOG_LABELS[run_index - 1]
        run_filename = "sfm_checkpoint_g_run_%02d_%s.txt" % (run_index, run_label)
        run_path = EVIDENCE_DIR + run_filename
        write_evidence_text_once(run_path, log_fp["raw_bytes"])

        witness_for_verify = cont.get("witness") or {}
        expected_shot_for_run = V1_SHOT_NAME if run_index == 1 else V2_SHOT_NAME
        expected_count_for_run = (
            len(witness_for_verify.get("v1_folds_sorted", []))
            if run_index == 1
            else len(witness_for_verify.get("v2_folds_sorted", []))
        )
        log_verification = verify_run_log_content(
            log_fp["raw_bytes"], expected_shot_for_run, expected_count_for_run
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
        "exists": log_fp["exists"], "size_bytes": log_fp["size_bytes"],
        "sha256": log_fp["sha256"],
    }
    record["run_captured"] = run_capture_record

    # --- Snapshot-specific logic ---
    if snapshot_index == 1:
        result = _snapshot_01_baseline(record, broker, authority_observation)
        record.update(result)
        # Persist the independently-derived witness (and, only on a
        # genuine pass, the baseline facts snapshots 02/03 need for
        # their own mechanical stage gates) into continuation state so
        # later, separate invocations can read them back.
        cont["witness"] = record.get("witness")
        if record.get("classification") == u"HARD_GATES_PASSED":
            cont["baseline_pid"] = record["current_pid"]
            cont["baseline_master_sha256"] = record.get("baseline_master_sha256_observed")
            cont["baseline_provider_counters"] = record.get("provider_counters")
            cont["baseline_diagnostics"] = record.get("recent_diagnostics")
    elif snapshot_index == 2:
        result = _snapshot_02_after_v1(record, cont, broker, authority_observation)
        record.update(result)
        if record.get("classification") == u"V1_STAGE_PASSED":
            cont["v1_stage_provider_counters"] = record.get("provider_counters")
            cont["v1_stage_diagnostics"] = record.get("recent_diagnostics")
    elif snapshot_index == 3:
        result = _snapshot_03_after_v2(record, cont, broker, authority_observation)
        record.update(result)

    # --- Write immutable snapshot evidence ---
    snapshot_json_filename = "sfm_checkpoint_g_snapshot_%02d_%s.json" % (snapshot_index, operation_label)
    snapshot_txt_filename = "sfm_checkpoint_g_snapshot_%02d_%s.txt" % (snapshot_index, operation_label)
    write_evidence_json_once(EVIDENCE_DIR + snapshot_json_filename, record)

    txt_lines = [
        u"CHECKPOINT G -- SNAPSHOT #%02d (%s)" % (snapshot_index, operation_label),
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
        raise CheckpointGError("Failed to persist continuation-state: %s" % err)

    # BLOCKER 4: expose the mechanical final verdict and failed-check
    # list directly in the rollup, rather than requiring a reviewer to
    # reconstruct it by hand from three separate snapshot files.
    last_snapshot_entry = cont["captured_snapshots"][-1] if cont["captured_snapshots"] else None
    ok2, err2, _r2 = write_json_rollup(FINAL_RESULT_PATH, {
        "captured_snapshots": cont["captured_snapshots"],
        "captured_runs": cont["captured_runs"],
        "witness": cont.get("witness"),
        "mechanical_final_verdict": (
            last_snapshot_entry["classification"] if last_snapshot_entry else None
        ),
        "mechanical_final_failed_checks": (
            last_snapshot_entry.get("failed_gates") if last_snapshot_entry else None
        ),
    })
    if not ok2:
        raise CheckpointGError("Failed to write final-result rollup: %s" % err2)

    summary_text = u"\n".join(txt_lines) + u"\n"
    write_text_rollup(FINAL_SUMMARY_PATH, summary_text.encode("utf-8"))

    try:
        sys.stdout.write(summary_text)
    except Exception:
        pass


def _snapshot_01_baseline(record, broker, authority_observation):
    """BLOCKER 2: mechanically gates EVERY governing baseline condition
    -- identities, guard/run-lock state, provider/lease counters,
    fixture identity, project size, vocabulary hard gates, and cache-key
    cleanliness -- via one exhaustive gate_checks list. Any single
    failure produces INCONCLUSIVE_BEFORE_EXECUTION (never FAIL) with the
    exact failed-check names, and the operator must not run command 1."""
    out = {}
    gate_checks = []

    def gate(name, passed, detail=None):
        gate_checks.append({"name": name, "passed": bool(passed), "detail": detail})

    gate(
        "identity.production_sha256_matches_expected",
        record.get("production_sha256_matches_expected") is True,
        record.get("production_sha256"),
    )
    gate(
        "identity.canonical_master_sha256_matches_expected",
        record.get("canonical_master_sha256_matches_expected") is True,
        record.get("canonical_master_sha256"),
    )
    gate(
        "identity.runtime_api_version_matches_expected",
        record.get("runtime_api_version_matches_expected") is True,
        record.get("runtime_api_version"),
    )
    gate(
        "identity.runtime_build_id_matches_expected",
        record.get("runtime_build_id_matches_expected") is True,
        record.get("runtime_build_id"),
    )
    gate(
        "identity.runtime_is_canonical",
        record.get("runtime_is_canonical") is True,
        record.get("runtime_is_canonical"),
    )
    gate(
        "state.main_window_available",
        record.get("main_window_available") is True,
        record.get("main_window_available"),
    )
    gate(
        "state.guard_state_is_unused",
        record.get("guard_state") == u"UNUSED",
        record.get("guard_state"),
    )
    gate(
        "state.run_lock_absent",
        record.get("run_lock_present") is False,
        record.get("run_lock_present"),
    )

    provider_counters = record.get("provider_counters") or {}
    gate(
        "provider.current_open_provider_count_is_zero",
        provider_counters.get("current_open_provider_count") == 0,
        provider_counters.get("current_open_provider_count"),
    )
    gate(
        "provider.total_opens_equals_total_closes",
        provider_counters.get("total_provider_opens") == provider_counters.get("total_provider_closes"),
        (provider_counters.get("total_provider_opens"), provider_counters.get("total_provider_closes")),
    )

    lease_counters = record.get("lease_counters") or {}
    gate(
        "lease.outstanding_lease_count_is_zero",
        lease_counters.get("outstanding_lease_count") == 0,
        lease_counters.get("outstanding_lease_count"),
    )
    gate(
        "lease.unreleased_lease_count_is_zero",
        lease_counters.get("unreleased_lease_count") == 0,
        lease_counters.get("unreleased_lease_count"),
    )

    # Fixture identity -- reused technique from checkpoint_f2_r1's own
    # already-qualified fixture gate (GetDocumentRoot/GetFileId/
    # g_pDataModel.GetFileName), never assumed from shot names alone.
    open_basename = u""
    try:
        root_for_filename = sfmApp.GetDocumentRoot()
        open_file_id = root_for_filename.GetFileId()
        open_path = vs.g_pDataModel.GetFileName(open_file_id)
        open_basename = os.path.basename(_independent_to_unicode(open_path)) if open_path else u""
    except Exception as exc:
        out["fixture_identity_error"] = u"%r" % (exc,)
    out["fixture_open_basename"] = open_basename
    gate(
        "fixture.matches_expected_normalized_copy",
        open_basename.lower() == EXPECTED_FIXTURE_FILENAME.lower(),
        open_basename,
    )
    gate(
        "fixture.is_not_forbidden_original",
        open_basename.lower() != FORBIDDEN_ORIGINAL_FIXTURE_FILENAME.lower(),
        open_basename,
    )

    try:
        all_shots = list(sfmApp.GetShots())
    except Exception as exc:
        all_shots = []
        gate("fixture.shots_enumerable", False, u"%r" % (exc,))
    else:
        gate("fixture.shots_enumerable", True, None)

    out["project_shot_count"] = len(all_shots)
    gate(
        "fixture.project_shot_count_matches_established_size",
        len(all_shots) == EXPECTED_PROJECT_SHOT_COUNT,
        len(all_shots),
    )

    v1_matches = resolve_unique_shot(all_shots, V1_SHOT_NAME)
    v2_matches = resolve_unique_shot(all_shots, V2_SHOT_NAME)
    out["v1_match_count"] = len(v1_matches)
    out["v2_match_count"] = len(v2_matches)
    gate("vocabulary.v1_shot_resolves_uniquely", len(v1_matches) == 1, len(v1_matches))
    gate("vocabulary.v2_shot_resolves_uniquely", len(v2_matches) == 1, len(v2_matches))

    v1_folds, v1_provenance = frozenset(), {}
    v2_folds, v2_provenance = frozenset(), {}
    if len(v1_matches) == 1:
        v1_folds, v1_provenance, v1_asets, v1_controls = derive_shot_vocabulary(v1_matches[0])
        out["v1_animation_sets_seen"] = v1_asets
        out["v1_controls_seen"] = v1_controls
    if len(v2_matches) == 1:
        v2_folds, v2_provenance, v2_asets, v2_controls = derive_shot_vocabulary(v2_matches[0])
        out["v2_animation_sets_seen"] = v2_asets
        out["v2_controls_seen"] = v2_controls

    v2_only = v2_folds - v1_folds
    out["v1_folds_sorted"] = sorted(v1_folds)
    out["v2_folds_sorted"] = sorted(v2_folds)
    out["v2_only_folds_sorted"] = sorted(v2_only)
    out["v1_count"] = len(v1_folds)
    out["v2_count"] = len(v2_folds)
    out["v2_only_count"] = len(v2_only)
    out["v1_hash"] = hashlib.sha256(u"\n".join(sorted(v1_folds)).encode("utf-8")).hexdigest()
    out["v2_hash"] = hashlib.sha256(u"\n".join(sorted(v2_folds)).encode("utf-8")).hexdigest()

    gate("vocabulary.v1_nonempty", len(v1_folds) > 0, len(v1_folds))
    gate("vocabulary.v2_nonempty", len(v2_folds) > 0, len(v2_folds))
    gate("vocabulary.v1_not_equal_v2", v1_folds != v2_folds, None)
    gate("vocabulary.v2_only_nonempty", len(v2_only) > 0, len(v2_only))

    # Clean-start cache-key gate -- uses the SAME cheap, read-only H0
    # observation the broker itself uses internally (observation.
    # observe_master(), no provider open -- confirmed by direct source
    # inspection of broker.py's own acquire_or_reuse_views()).
    h0_sha256 = None
    v1_key_present = None
    v2_key_present = None
    if broker is not None and authority_observation is not None:
        try:
            h0 = authority_observation.observe_master(CANONICAL_MASTER_INSTALLED_PATH)
            h0_sha256 = h0.sha256
            out["baseline_master_sha256_observed"] = h0_sha256
            out["baseline_view_cache_entry_count"] = broker.view_cache_entry_count()
            v1_key = cache_key_for(h0_sha256, v1_folds, CONSUMER_KIND)
            v2_key = cache_key_for(h0_sha256, v2_folds, CONSUMER_KIND)
            v1_key_present = broker.cached_view(v1_key) is not None
            v2_key_present = broker.cached_view(v2_key) is not None
            out["baseline_v1_cache_key_present"] = v1_key_present
            out["baseline_v2_cache_key_present"] = v2_key_present
        except Exception as exc:
            out["baseline_cache_key_gate_error"] = u"%r" % (exc,)

    gate(
        "authority.broker_and_observation_available",
        broker is not None and authority_observation is not None,
        None,
    )
    gate(
        "authority.observed_master_hash_matches_governing_master_sha256",
        h0_sha256 is not None and h0_sha256 == EXPECTED_CANONICAL_MASTER_SHA256,
        h0_sha256,
    )
    gate("cache.v1_cache_key_absent_at_baseline", v1_key_present is False, v1_key_present)
    gate("cache.v2_cache_key_absent_at_baseline", v2_key_present is False, v2_key_present)

    out["gate_checks"] = gate_checks
    failed = [g["name"] for g in gate_checks if not g["passed"]]
    out["failed_gates"] = failed

    if failed:
        out["classification"] = u"INCONCLUSIVE_BEFORE_EXECUTION"
        out["gate_failure"] = (
            u"%d baseline gate(s) failed -- operator must NOT run "
            u"command 1: %s" % (len(failed), u", ".join(failed))
        )
        return out

    out["witness"] = {
        "v1_shot_name": V1_SHOT_NAME, "v2_shot_name": V2_SHOT_NAME,
        "v1_folds_sorted": out["v1_folds_sorted"],
        "v2_folds_sorted": out["v2_folds_sorted"],
        "v2_only_folds_sorted": out["v2_only_folds_sorted"],
        "v1_provenance": v1_provenance, "v2_provenance": v2_provenance,
    }
    out["classification"] = u"HARD_GATES_PASSED"
    return out


def _snapshot_02_after_v1(record, cont, broker, authority_observation):
    """BLOCKER 3: mechanically evaluates the V1 stage against every
    required condition (continuity, identities, guard state, Master
    generation, run-01 verification, provider/lease/diagnostic deltas,
    V1 view freshness/coverage/payload consistency, V2 cache key still
    absent). Classifies V1_STAGE_PASSED or FAIL with exact failed-check
    names -- never an unconditional RECORDED. The operator must NOT run
    command 2 unless this reports V1_STAGE_PASSED."""
    out = {}
    gate_checks = []

    def gate(name, passed, detail=None):
        gate_checks.append({"name": name, "passed": bool(passed), "detail": detail})

    witness = cont.get("witness")
    if witness is None:
        out["classification"] = u"FAIL"
        out["gate_failure"] = u"no baseline witness recorded -- baseline hard gates did not pass"
        out["failed_gates"] = [u"continuity.baseline_witness_present"]
        return out

    baseline_pid = cont.get("baseline_pid")
    baseline_master_sha256 = cont.get("baseline_master_sha256")
    baseline_provider_counters = cont.get("baseline_provider_counters") or {}
    baseline_diagnostics = cont.get("baseline_diagnostics") or []

    gate(
        "continuity.same_pid_as_baseline",
        record.get("current_pid") == baseline_pid,
        (record.get("current_pid"), baseline_pid),
    )
    gate("identity.production_sha256_matches_expected", record.get("production_sha256_matches_expected") is True, None)
    gate("identity.canonical_master_sha256_matches_expected", record.get("canonical_master_sha256_matches_expected") is True, None)
    gate("identity.runtime_api_version_matches_expected", record.get("runtime_api_version_matches_expected") is True, None)
    gate("identity.runtime_build_id_matches_expected", record.get("runtime_build_id_matches_expected") is True, None)
    gate("identity.runtime_is_canonical", record.get("runtime_is_canonical") is True, None)
    gate("state.guard_state_is_selected_used", record.get("guard_state") == u"SELECTED_USED", record.get("guard_state"))
    gate("state.run_lock_absent", record.get("run_lock_present") is False, record.get("run_lock_present"))

    v1_folds = frozenset(witness["v1_folds_sorted"])
    v2_folds = frozenset(witness["v2_folds_sorted"])

    try:
        h0 = authority_observation.observe_master(CANONICAL_MASTER_INSTALLED_PATH)
        master_sha256_now = h0.sha256
    except Exception as exc:
        out["classification"] = u"FAIL"
        out["gate_failure"] = u"could not observe the Master for cache-key construction: %r" % (exc,)
        out["failed_gates"] = [u"generation.master_observable"]
        return out
    out["observed_master_sha256"] = master_sha256_now
    gate("generation.master_unchanged_from_baseline", master_sha256_now == baseline_master_sha256, (master_sha256_now, baseline_master_sha256))

    run_captured = record.get("run_captured")
    gate(
        "run.exactly_one_new_run01_log_captured",
        run_captured is not None and run_captured.get("step_ordinal") == 1,
        run_captured.get("step_ordinal") if run_captured else None,
    )
    log_verification = (run_captured or {}).get("log_verification") or {}
    gate("run.run01_verifier_all_checks_pass", bool(log_verification.get("all_checks_pass")), log_verification)
    gate("run.logged_unique_scope_folds_equals_v1_count", log_verification.get("unique_scope_folds_matches") is True, log_verification.get("logged_unique_scope_folds"))

    provider_counters_now = record.get("provider_counters") or {}
    opens_delta = (provider_counters_now.get("total_provider_opens") or 0) - (baseline_provider_counters.get("total_provider_opens") or 0)
    closes_delta = (provider_counters_now.get("total_provider_closes") or 0) - (baseline_provider_counters.get("total_provider_closes") or 0)
    out["provider_opens_delta_since_baseline"] = opens_delta
    out["provider_closes_delta_since_baseline"] = closes_delta
    gate("provider.exactly_one_open_since_baseline", opens_delta == 1, opens_delta)
    gate("provider.exactly_one_close_since_baseline", closes_delta == 1, closes_delta)
    gate("provider.current_open_provider_count_is_zero", provider_counters_now.get("current_open_provider_count") == 0, provider_counters_now.get("current_open_provider_count"))

    v1_cache_key = cache_key_for(master_sha256_now, v1_folds, CONSUMER_KIND)
    v2_cache_key = cache_key_for(master_sha256_now, v2_folds, CONSUMER_KIND)
    v1_inspection = inspect_cached_view(broker, v1_cache_key, v1_folds) if broker is not None else {"present": False}
    v2_inspection = inspect_cached_view(broker, v2_cache_key, v2_folds) if broker is not None else {"present": False}
    out["v1_cache_key_repr"] = repr(v1_cache_key)
    out["v2_cache_key_repr"] = repr(v2_cache_key)
    out["v1_view"] = v1_inspection
    out["v2_view_still_absent_check"] = v2_inspection

    gate("view.v1_cached_view_present", v1_inspection.get("present") is True, None)
    gate("view.v1_view_is_fresh", bool(v1_inspection.get("present")) and (not v1_inspection.get("is_stale")), v1_inspection.get("is_stale"))
    gate("view.v1_consumer_kind_is_normalizer_compat", v1_inspection.get("consumer_kind") == CONSUMER_KIND, v1_inspection.get("consumer_kind"))
    gate(
        "view.v1_semantic_generation_matches_governing_master",
        v1_inspection.get("semantic_generation_master_sha256") == EXPECTED_CANONICAL_MASTER_SHA256,
        v1_inspection.get("semantic_generation_master_sha256"),
    )
    gate("view.v1_covered_keys_equal_v1", v1_inspection.get("covered_keys_equals_requested") is True, None)
    gate("view.v1_zero_uncovered", v1_inspection.get("uncovered_count") == 0, v1_inspection.get("uncovered_count"))
    gate("view.v1_payload_known_keys_match_coverage_known_keys", v1_inspection.get("payload_keys_match_known_folds") is True, None)
    gate("view.v1_payload_key_count_matches_known_count", v1_inspection.get("payload_folded_key_count_matches_known_count") is True, None)
    gate("view.v2_cache_key_still_absent", v2_inspection.get("present") is False, v2_inspection.get("present"))

    lease_counters_now = record.get("lease_counters") or {}
    gate("lease.outstanding_zero", lease_counters_now.get("outstanding_lease_count") == 0, lease_counters_now.get("outstanding_lease_count"))
    gate("lease.unreleased_zero", lease_counters_now.get("unreleased_lease_count") == 0, lease_counters_now.get("unreleased_lease_count"))

    diagnostics_now = record.get("recent_diagnostics") or []
    delta, delta_clean = diagnostics_delta(baseline_diagnostics, diagnostics_now)
    delta_events = [e.get("event") for e in delta]
    out["diagnostics_delta_since_baseline_event_names"] = delta_events
    out["diagnostics_delta_continuity_established"] = delta_clean
    gate("diagnostics.delta_continuity_established", delta_clean, None)
    gate("diagnostics.delta_contains_cohort_acquired", u"cohort_acquired" in delta_events, delta_events)
    gate("diagnostics.delta_excludes_fully_reused_no_provider_open", u"fully_reused_no_provider_open" not in delta_events, delta_events)

    logged_matched_folds = log_verification.get("logged_matched_folds")
    matched_folds_consistency = (
        logged_matched_folds is not None
        and logged_matched_folds == v1_inspection.get("known_count") == v1_inspection.get("payload_folded_key_count")
    )
    out["matched_folds_consistency_check"] = {
        "logged_matched_folds": logged_matched_folds,
        "known_count": v1_inspection.get("known_count"),
        "payload_folded_key_count": v1_inspection.get("payload_folded_key_count"),
    }
    gate("consistency.logged_matched_folds_equals_known_count_equals_payload_count", matched_folds_consistency, out["matched_folds_consistency_check"])

    out["gate_checks"] = gate_checks
    failed = [g["name"] for g in gate_checks if not g["passed"]]
    out["failed_gates"] = failed
    if failed:
        out["classification"] = u"FAIL"
        out["gate_failure"] = (
            u"%d V1-stage check(s) failed -- operator must NOT run "
            u"command 2: %s" % (len(failed), u", ".join(failed))
        )
    else:
        out["classification"] = u"V1_STAGE_PASSED"
    return out


def _snapshot_03_after_v2(record, cont, broker, authority_observation):
    """BLOCKER 4/5: mechanically evaluates the full G proposition --
    continuity, identities, guard state, Master generation, run-02
    verification, provider/lease/diagnostic deltas, V2 view freshness/
    coverage/payload consistency, and a V2-only Known witness proven
    against its ACTUAL payload row (not merely the coverage index).
    Classifies G_PASS or FAIL with exact failed-check names -- never an
    unconditional RECORDED."""
    out = {}
    gate_checks = []

    def gate(name, passed, detail=None):
        gate_checks.append({"name": name, "passed": bool(passed), "detail": detail})

    witness = cont.get("witness")
    if witness is None:
        out["classification"] = u"FAIL"
        out["gate_failure"] = u"no baseline witness recorded"
        out["failed_gates"] = [u"continuity.baseline_witness_present"]
        return out

    baseline_pid = cont.get("baseline_pid")
    baseline_master_sha256 = cont.get("baseline_master_sha256")
    v1_stage_provider_counters = cont.get("v1_stage_provider_counters") or {}
    v1_stage_diagnostics = cont.get("v1_stage_diagnostics") or []

    gate(
        "continuity.same_pid_as_baseline_and_v1_stage",
        record.get("current_pid") == baseline_pid,
        (record.get("current_pid"), baseline_pid),
    )
    gate("identity.production_sha256_matches_expected", record.get("production_sha256_matches_expected") is True, None)
    gate("identity.canonical_master_sha256_matches_expected", record.get("canonical_master_sha256_matches_expected") is True, None)
    gate("identity.runtime_api_version_matches_expected", record.get("runtime_api_version_matches_expected") is True, None)
    gate("identity.runtime_build_id_matches_expected", record.get("runtime_build_id_matches_expected") is True, None)
    gate("identity.runtime_is_canonical", record.get("runtime_is_canonical") is True, None)
    gate("state.guard_state_remains_selected_used", record.get("guard_state") == u"SELECTED_USED", record.get("guard_state"))

    v2_folds = frozenset(witness["v2_folds_sorted"])
    v2_only_folds = frozenset(witness["v2_only_folds_sorted"])

    try:
        h0 = authority_observation.observe_master(CANONICAL_MASTER_INSTALLED_PATH)
        master_sha256_now = h0.sha256
    except Exception as exc:
        out["classification"] = u"FAIL"
        out["gate_failure"] = u"could not observe the Master for cache-key construction: %r" % (exc,)
        out["failed_gates"] = [u"generation.master_observable"]
        return out
    out["observed_master_sha256"] = master_sha256_now
    gate("generation.master_unchanged_from_baseline", master_sha256_now == baseline_master_sha256, (master_sha256_now, baseline_master_sha256))

    run_captured = record.get("run_captured")
    gate(
        "run.exactly_one_new_run02_log_captured",
        run_captured is not None and run_captured.get("step_ordinal") == 2,
        run_captured.get("step_ordinal") if run_captured else None,
    )
    log_verification = (run_captured or {}).get("log_verification") or {}
    gate("run.run02_verifier_all_checks_pass", bool(log_verification.get("all_checks_pass")), log_verification)
    gate("run.exact_single_selected_shot9", log_verification.get("exact_single_shot_present") is True, None)
    gate("run.logged_unique_scope_folds_equals_v2_count", log_verification.get("unique_scope_folds_matches") is True, log_verification.get("logged_unique_scope_folds"))

    provider_counters_now = record.get("provider_counters") or {}
    opens_delta = (provider_counters_now.get("total_provider_opens") or 0) - (v1_stage_provider_counters.get("total_provider_opens") or 0)
    closes_delta = (provider_counters_now.get("total_provider_closes") or 0) - (v1_stage_provider_counters.get("total_provider_closes") or 0)
    out["provider_opens_delta_since_v1_stage"] = opens_delta
    out["provider_closes_delta_since_v1_stage"] = closes_delta
    gate("provider.exactly_one_open_since_v1_stage", opens_delta == 1, opens_delta)
    gate("provider.exactly_one_close_since_v1_stage", closes_delta == 1, closes_delta)
    gate("provider.current_open_provider_count_is_zero", provider_counters_now.get("current_open_provider_count") == 0, provider_counters_now.get("current_open_provider_count"))

    v2_cache_key = cache_key_for(master_sha256_now, v2_folds, CONSUMER_KIND)
    v2_inspection = inspect_cached_view(broker, v2_cache_key, v2_folds) if broker is not None else {"present": False}
    out["v2_cache_key_repr"] = repr(v2_cache_key)
    out["v2_view"] = v2_inspection

    gate("view.v2_cached_view_present", v2_inspection.get("present") is True, None)
    gate("view.v2_view_is_fresh", bool(v2_inspection.get("present")) and (not v2_inspection.get("is_stale")), v2_inspection.get("is_stale"))
    gate("view.v2_consumer_kind_is_normalizer_compat", v2_inspection.get("consumer_kind") == CONSUMER_KIND, v2_inspection.get("consumer_kind"))
    gate(
        "view.v2_semantic_generation_matches_governing_master",
        v2_inspection.get("semantic_generation_master_sha256") == EXPECTED_CANONICAL_MASTER_SHA256,
        v2_inspection.get("semantic_generation_master_sha256"),
    )
    gate("view.v2_covered_keys_equal_v2", v2_inspection.get("covered_keys_equals_requested") is True, None)
    gate("view.v2_zero_uncovered", v2_inspection.get("uncovered_count") == 0, v2_inspection.get("uncovered_count"))
    gate("view.v2_payload_known_keys_match_coverage_known_keys", v2_inspection.get("payload_keys_match_known_folds") is True, None)
    gate("view.v2_payload_key_count_matches_known_count", v2_inspection.get("payload_folded_key_count_matches_known_count") is True, None)

    lease_counters_now = record.get("lease_counters") or {}
    gate("lease.outstanding_zero", lease_counters_now.get("outstanding_lease_count") == 0, lease_counters_now.get("outstanding_lease_count"))
    gate("lease.unreleased_zero", lease_counters_now.get("unreleased_lease_count") == 0, lease_counters_now.get("unreleased_lease_count"))

    diagnostics_now = record.get("recent_diagnostics") or []
    delta, delta_clean = diagnostics_delta(v1_stage_diagnostics, diagnostics_now)
    delta_events = [e.get("event") for e in delta]
    out["diagnostics_delta_since_v1_stage_event_names"] = delta_events
    out["diagnostics_delta_continuity_established"] = delta_clean
    gate("diagnostics.delta_continuity_established", delta_clean, None)
    gate("diagnostics.delta_contains_cohort_acquired", u"cohort_acquired" in delta_events, delta_events)
    gate("diagnostics.delta_excludes_fully_reused_no_provider_open", u"fully_reused_no_provider_open" not in delta_events, delta_events)

    logged_matched_folds = log_verification.get("logged_matched_folds")
    matched_folds_consistency = (
        logged_matched_folds is not None
        and logged_matched_folds == v2_inspection.get("known_count") == v2_inspection.get("payload_folded_key_count")
    )
    out["matched_folds_consistency_check"] = {
        "logged_matched_folds": logged_matched_folds,
        "known_count": v2_inspection.get("known_count"),
        "payload_folded_key_count": v2_inspection.get("payload_folded_key_count"),
    }
    gate("consistency.logged_matched_folds_equals_known_count_equals_payload_count", matched_folds_consistency, out["matched_folds_consistency_check"])

    # V2-only Known witness -- BLOCKER 5: proven against the view's
    # ACTUAL payload row, not merely the coverage index.
    witness_result = find_v2_only_known_witness(v2_inspection, v2_only_folds)
    out["v2_only_known_witness"] = witness_result
    witness_valid = False
    if witness_result is not None:
        v2_view_obj = broker.cached_view(v2_cache_key) if broker is not None else None
        if v2_view_obj is not None:
            payload_check = inspect_witness_payload_row(v2_view_obj, witness_result["folded_key"])
            out["v2_only_known_witness_payload_check"] = payload_check
            witness_valid = bool(payload_check.get("internally_consistent"))
        out["v2_only_known_witness_provenance"] = witness.get("v2_provenance", {}).get(witness_result["folded_key"])
    gate("witness.v2_only_known_witness_found_and_payload_consistent", witness_valid, witness_result)

    out["gate_checks"] = gate_checks
    failed = [g["name"] for g in gate_checks if not g["passed"]]
    out["failed_gates"] = failed
    if failed:
        out["classification"] = u"FAIL"
        out["gate_failure"] = u"%d final G check(s) failed: %s" % (len(failed), u", ".join(failed))
    else:
        out["classification"] = u"G_PASS"
    return out


main()
