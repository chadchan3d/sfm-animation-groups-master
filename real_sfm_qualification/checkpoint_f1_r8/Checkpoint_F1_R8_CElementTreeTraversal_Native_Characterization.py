# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint F1-R8: CElementTreeTraversal
Native Semantic Characterization.

RUN TYPE: MAIN MENU SCRIPT
PURPOSE: This is a CHARACTERIZATION checkpoint, not an optimization
benchmark. F1-R7's static audit (F1_R7_LOWER_LEVEL_TRAVERSAL_AUDIT.md)
classified the real, installed, native `CElementTreeTraversal` class as a
MEASUREMENT_CANDIDATE, blocked from EXACT_CANDIDATE status by two
questions that could not be resolved from any binding stub, header, or
source evidence present in this SFM install:

  A. pAttrName semantics -- does CElementTreeTraversal(root, pAttrName)
     follow only the one named attribute, or can it be made to follow
     every element-reference attribute (matching legacy reachable()'s own
     whole-attribute-list walk)?
  B. visitation semantics -- does it deduplicate shared/DAG-reachable
     elements across the WHOLE traversal (matching legacy's permanent
     handle-keyed `seen` set), or only detect cycles along the CURRENT
     traversal path (the two-state NOT_VISITED/VISITING signature)?

This checkpoint resolves ONLY those two questions, empirically, against a
small, deliberately-constructed, DETACHED native DME graph -- never the
qualification fixture's own real scene graph, and never anything attached
to the open session, a shot, an animation set, or the production scene
hierarchy. It does NOT measure command-scale resource savings. It does
NOT modify production. It does NOT build the F1-R7 optimization prototype
-- that remains gated behind this checkpoint's own result.

MUTATION STATUS: creates and destroys a handful of small, detached,
never-attached, never-saved DME elements under a dedicated scratch file
ID (see "Detached graph technique" below). Never touches the open
document's own root, any shot, any animation set, or any control. Never
calls SaveToFile. Every created element is explicitly destroyed and the
scratch file ID is explicitly removed before this script finishes,
regardless of outcome.

Detached graph technique: `vs.g_pDataModel.FindOrCreateFileId(name)`
registers a brand-new, purely in-memory file-ID namespace tag (no disk
I/O -- confirmed by its own signature, `FindOrCreateFileId(char const *
pFilename) -> DmFileId_t`, which never touches disk unless SaveToFile is
later called against that ID, which this script never does).
`vs.CreateElement(elemType, elemName, fileid)` (confirmed real via a
first-party SFM script, `platform/scripts/sfm/dag/exact/count1/
create_lights.py`, which calls this exact function) creates elements
tagged with that scratch file ID. Nothing in this script ever assigns a
scratch element as the value of any attribute belonging to an element
outside the scratch graph, so nothing here becomes reachable from the
open document's own root.

Design:
  1. exec()s the pinned, SHA-256-verified production bytes into a fresh
     namespace -- exactly as every earlier checkpoint does -- solely to
     extract legacy's own `reachable`/`handle`/`name`/`to_unicode`/
     `scalar`/`typ` helpers VERBATIM (never reimplemented), used here as
     the "legacy control" this checkpoint compares native traversal
     against. Locates the already-constructed run instance and sets
     instance.finished = True immediately, before ever pumping the Qt
     event loop -- identical technique to every earlier checkpoint. This
     checkpoint never reads instance.work for its own core (detached-
     graph) characterization; it is read only for the OPTIONAL,
     gated, real-scene sanity check at the very end.
  2. Resolves `vs.CreateElement`, `vs.AT_ELEMENT`, `vs.AT_ELEMENT_ARRAY`,
     and `vs.CElementTreeTraversal` (falling back to the `vs.datamodel`
     submodule directly if not re-exported at the `vs` package level).
     If any required symbol cannot be resolved, or a minimal detached-
     element creation probe fails, this checkpoint reports
     `detached_graph_available: False` and an overall classification of
     `INCONCLUSIVE`, and stops the native-characterization work there --
     it does not invent an alternative method.
  3. Builds three small, detached native DME graphs (see the three
     `build_graph_*` functions below) under one dedicated scratch file
     ID, using only confirmed-real APIs: `AddAttribute(name, type)` (a
     real `CDmElement` method) plus `SetValue()`/`SetCount()`/`append()`
     (real `CDmAttribute` methods, confirmed via this SDK's own internal
     `_swig_setattr` implementation, which calls them the same way).
  4. Runs legacy's own extracted `reachable()` over each graph's root,
     recording the exact ordered/unique handle sequence, duplicate
     count, and termination/exception behavior.
  5. Runs `CElementTreeTraversal` over each graph's root for every
     legitimately-justified tested `pAttrName` value (see
     TESTED_ATTR_NAMES_GRAPH1 below for the exact justification of each
     one -- no invented wildcard strings), under a strict bounded
     watchdog (MAX_TRAVERSAL_STEPS) so a pathological native traversal
     cannot hang SFM. Records BOTH `GetElement()` (queried before each
     `Next()` call) and `Next()`'s own return value at every step, since
     the binding stub alone does not disambiguate which one represents
     "the newly visited node" -- this checkpoint records raw empirical
     behavior rather than assuming an interpretation.
  6. Computes a decisive single-call coverage check for the multi-
     attribute graph (does any ONE tested pAttrName's traversal alone
     reach legacy's full unique-handle set?) and a mechanical dedup
     classification for the DAG/cycle graphs (GLOBAL_DEDUP_EQUIVALENT /
     PATH_ONLY_DEDUP / NO_SAFE_DEDUP / OTHER / INCONCLUSIVE).
  7. Computes the final mechanical disposition (EXACT_CANDIDATE_SUPPORTED
     / SEMANTICALLY_INSUFFICIENT / INCONCLUSIVE) exactly per the accepted
     F1-R8 instruction: EXACT_CANDIDATE_SUPPORTED requires BOTH complete
     single-call forward-reachable coverage AND global dedup equivalence.
  8. ONLY if the final disposition is EXACT_CANDIDATE_SUPPORTED, runs one
     additional, small, strictly read-only sanity comparison against the
     ALREADY-OPEN real qualification fixture's own first shot's scene --
     never 62 targets, never native Rebuild, never the production
     contextual pipeline.
  9. Destroys every created scratch element and removes the scratch file
     ID before finishing, regardless of outcome.
 10. No save. No native Rebuild. No shot activation beyond what step 1's
     own exec() of production unavoidably performs (its own one-time
     setup, immediately neutralized, never advanced).

Do NOT run this against the original testscripts.dmx fixture -- this
script structurally refuses to proceed if the currently open document's
own filename does not match the expected normalized-copy filename.
"""
import gc
import hashlib
import json
import os
import sys
import time
import traceback

from PySide import QtCore

try:
    import vs.datamodel as _vs_datamodel_submodule
except Exception:
    _vs_datamodel_submodule = None

# ---------------------------------------------------------------------------
# Pinned identities.
# ---------------------------------------------------------------------------

EXPECTED_PRODUCTION_NORMALIZER_SHA256 = (
    "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"
)
EXPECTED_CANONICAL_MASTER_SHA256 = (
    "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
)
EXPECTED_NORMALIZED_COPY_FILENAME = u"F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx"
FORBIDDEN_ORIGINAL_FIXTURE_FILENAME = u"testscripts.dmx"

MAX_TRAVERSAL_STEPS = 2000  # bounded watchdog; generous relative to <10-node synthetic graphs
SCRATCH_FILEID_NAME = "f1_r8_detached_scratch_graph"
SCRATCH_ELEMENT_TYPE = "DmElement"  # the base/generic DME element type

JSON_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r8_result.json"
SUMMARY_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r8_result_summary.txt"
NATIVE_TRAVERSAL_LOG_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r8_native_traversal_log.txt"

PRODUCTION_NORMALIZER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)),
    "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
    "Rebuild_Control_Groups_Normalizer.py",
)
CANONICAL_MASTER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)),
    "usermod", "cfg", "sfm_defaultanimationgroups.txt",
)


class CheckpointF1R8Error(Exception):
    pass


ANOMALIES = []


def anomaly(message):
    ANOMALIES.append(message)
    try:
        sys.stdout.write("ANOMALY: %s\n" % message)
    except Exception:
        pass


TRAVERSAL_LOG_LINES = []


def log_line(message):
    TRAVERSAL_LOG_LINES.append(message)
    try:
        sys.stdout.write("%s\n" % message)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Shared helpers (verbatim, same copies every earlier checkpoint uses).
# ---------------------------------------------------------------------------

def b_to_unicode(value):
    if isinstance(value, unicode):
        return value
    try:
        return value.decode("utf-8")
    except Exception:
        try:
            return value.decode("latin-1")
        except Exception:
            return unicode(value)


def write_json_atomic(final_path, data_obj):
    tmp_path = final_path + ".tmp"

    def _cleanup_tmp():
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

    try:
        f = open(tmp_path, "wb")
        try:
            json.dump(data_obj, f)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
        finally:
            f.close()
    except Exception as exc:
        _cleanup_tmp()
        return False, "json.dump()/write to temp file (%r) failed: %r" % (tmp_path, exc), None
    try:
        temp_size = os.path.getsize(tmp_path)
    except Exception as exc:
        _cleanup_tmp()
        return False, "could not stat temp file (%r): %r" % (tmp_path, exc), None
    if temp_size <= 0:
        _cleanup_tmp()
        return False, "temp file is zero bytes after write (size=%r)" % (temp_size,), None
    try:
        with open(tmp_path, "rb") as f:
            reparsed_obj = json.load(f)
    except Exception as exc:
        _cleanup_tmp()
        return False, "temp file reopen/reparse verification failed: %r" % (exc,), None
    try:
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(tmp_path, final_path)
    except Exception as exc:
        return False, "promoting temp file to final path failed: %r" % (exc,), None
    return True, None, reparsed_obj


def write_text_atomic(final_path, text_bytes):
    tmp_path = final_path + ".tmp"

    def _cleanup_tmp():
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

    try:
        f = open(tmp_path, "wb")
        try:
            f.write(text_bytes)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
        finally:
            f.close()
    except Exception as exc:
        _cleanup_tmp()
        return False, "temp file write (%r) failed: %r" % (tmp_path, exc)
    try:
        temp_size = os.path.getsize(tmp_path)
    except Exception as exc:
        _cleanup_tmp()
        return False, "could not stat temp file (%r): %r" % (tmp_path, exc)
    if temp_size <= 0:
        _cleanup_tmp()
        return False, "temp file is zero bytes after write (size=%r)" % (temp_size,)
    try:
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(tmp_path, final_path)
    except Exception as exc:
        return False, "promoting temp file to final path failed: %r" % (exc,)
    return True, None


def resolve_datamodel_symbol(name):
    """Resolve a datamodel symbol, preferring the `vs` package re-export
    (confirmed real for e.g. `vs.CreateElement`) and falling back to the
    `vs.datamodel` submodule directly."""
    try:
        if hasattr(vs, name):
            return getattr(vs, name)
    except Exception:
        pass
    if _vs_datamodel_submodule is not None:
        try:
            if hasattr(_vs_datamodel_submodule, name):
                return getattr(_vs_datamodel_submodule, name)
        except Exception:
            pass
    return None


# ---------------------------------------------------------------------------
# Detached graph construction (never attached to the open session).
# ---------------------------------------------------------------------------

def create_scratch_node(create_element_fn, fileid, elem_name):
    # F1-R8-R1 repair: elem_name MUST be a plain Python 2 `str`, never
    # `unicode`. The installed SWIG overload set for the module-level
    # `CreateElement` free function includes
    # `CreateElement<CDmElement>(char const*, char const*, DmFileId_t)`
    # (confirmed via the real, working first-party call
    # `vs.CreateElement("DmeProjectedLight", lightName, parent.GetFileId())`
    # in `platform/scripts/sfm/dag/exact/count1/create_lights.py`, where
    # every literal passed as the object-name argument is a plain `str`,
    # e.g. "keyLight" -- never `u"keyLight"`). Passing `unicode` for this
    # parameter does not match any registered overload's typemap and
    # raises `NotImplementedError: Wrong number or type of arguments for
    # overloaded function 'CreateElement'` -- the exact class of bug
    # already diagnosed and fixed once in this project for SaveToFile's
    # own `pFileName` parameter (F1-R2). Every caller of this function
    # passes a plain `str` literal (never `u"..."`); this assertion exists
    # so a future edit cannot silently reintroduce a `unicode` literal.
    assert isinstance(elem_name, str), "elem_name must be a plain Python 2 str, not unicode: %r" % (elem_name,)
    return create_element_fn(SCRATCH_ELEMENT_TYPE, elem_name, fileid)


def link_scalar(at_element_const, parent, attr_name, child):
    attr = parent.AddAttribute(attr_name, at_element_const)
    attr.SetValue(child)
    return attr


def link_array(at_element_array_const, parent, attr_name, children):
    attr = parent.AddAttribute(attr_name, at_element_array_const)
    attr.SetCount(0)
    for c in children:
        attr.append(c)
    return attr


def build_graph_multiattr(create_element_fn, at_element_const, at_element_array_const, fileid):
    """
    ROOT --attr_A--> A --attr_A--> C
    ROOT --attr_B--> B --attr_B--> D
    A    --attr_list (array)--> [E, F]

    Purpose: does CElementTreeTraversal(root, pAttrName) follow only the
    one named attribute, or can it be made to follow every element-
    reference attribute regardless of name? attr_A is deliberately reused
    at two different nesting levels (ROOT and A) to test whether pAttrName
    scoping, if it exists, is attribute-NAME-based globally (would still
    reach C via A's own attr_A) rather than positional/depth-based.
    attr_list is a genuine AT_ELEMENT_ARRAY attribute, included so this
    graph also answers "are array-typed reference attributes followed at
    all" for at least one tested pAttrName value.
    """
    root = create_scratch_node(create_element_fn, fileid, "F1R8_MA_ROOT")
    a = create_scratch_node(create_element_fn, fileid, "F1R8_MA_A")
    b = create_scratch_node(create_element_fn, fileid, "F1R8_MA_B")
    c = create_scratch_node(create_element_fn, fileid, "F1R8_MA_C")
    d = create_scratch_node(create_element_fn, fileid, "F1R8_MA_D")
    e = create_scratch_node(create_element_fn, fileid, "F1R8_MA_E")
    f = create_scratch_node(create_element_fn, fileid, "F1R8_MA_F")

    link_scalar(at_element_const, root, "attr_A", a)
    link_scalar(at_element_const, root, "attr_B", b)
    link_scalar(at_element_const, a, "attr_A", c)
    link_scalar(at_element_const, b, "attr_B", d)
    link_array(at_element_array_const, a, "attr_list", [e, f])

    return {"root": root, "a": a, "b": b, "c": c, "d": d, "e": e, "f": f}


def build_graph_dag(create_element_fn, at_element_array_const, fileid):
    """
    ROOT --ref--> [A, B]
    A    --ref--> [C]
    B    --ref--> [C]   (C is shared -- reachable via two distinct paths)

    Purpose: is a shared/DAG-reachable element emitted once globally
    (matching legacy's handle-keyed `seen` dedup) or once per incoming
    path (or some other way)?
    """
    root = create_scratch_node(create_element_fn, fileid, "F1R8_DAG_ROOT")
    a = create_scratch_node(create_element_fn, fileid, "F1R8_DAG_A")
    b = create_scratch_node(create_element_fn, fileid, "F1R8_DAG_B")
    c = create_scratch_node(create_element_fn, fileid, "F1R8_DAG_C")

    link_array(at_element_array_const, root, "ref", [a, b])
    link_array(at_element_array_const, a, "ref", [c])
    link_array(at_element_array_const, b, "ref", [c])

    return {"root": root, "a": a, "b": b, "c": c}


def build_graph_cycle(create_element_fn, at_element_array_const, fileid):
    """
    ROOT --ref--> [A]
    A    --ref--> [B]
    B    --ref--> [ROOT]   (cycle back to root)

    Purpose: does traversal terminate? Are already-visited nodes emitted
    again? Does cycle handling match legacy's global-handle dedup?
    """
    root = create_scratch_node(create_element_fn, fileid, "F1R8_CYC_ROOT")
    a = create_scratch_node(create_element_fn, fileid, "F1R8_CYC_A")
    b = create_scratch_node(create_element_fn, fileid, "F1R8_CYC_B")

    link_array(at_element_array_const, root, "ref", [a])
    link_array(at_element_array_const, a, "ref", [b])
    link_array(at_element_array_const, b, "ref", [root])

    return {"root": root, "a": a, "b": b}


# Every tested pAttrName value and its explicit justification. No invented
# wildcard strings.
#
# A Python-None (NULL const char*) probe is DELIBERATELY EXCLUDED here.
# Passing None to a SWIG `char const *` parameter is commonly mapped to a
# NULL pointer, but nothing in the installed binding stub, any header, or
# any other evidence in this SFM install establishes that
# CElementTreeTraversal's own C++ implementation SAFELY handles a NULL
# pAttrName (as opposed to, for example, dereferencing it unconditionally
# and crashing the process). Passing "" is a genuine, safe, non-NULL
# C-string value (an empty but valid pointer), which is not the same
# safety question. NULL and "" are NOT assumed equivalent anywhere in this
# checkpoint. NULL pAttrName semantics are recorded as UNKNOWN
# (`report["null_pattrname_probe"]`) rather than tested, unless the
# remaining named/empty-string probes fail to establish complete-forward-
# traversal and global-dedup semantics AND a NULL probe is separately
# judged actually necessary to qualify the API -- that would require its
# own explicit safety review before being added back, not silent
# reintroduction.
TESTED_ATTR_NAMES_GRAPH1 = [
    ("attr_A", "attr_A", "the real, present scalar reference attribute name used at two different nesting levels (ROOT and A)"),
    ("attr_B", "attr_B", "the real, present scalar reference attribute name used at ROOT and B"),
    ("attr_list", "attr_list", "the real, present AT_ELEMENT_ARRAY reference attribute name on A"),
    ("empty_string", "", "the natural 'absence of a name' probe -- a legitimate, safe, non-NULL C-string value, not an invented sentinel"),
]
TESTED_ATTR_NAMES_DAG_AND_CYCLE = [
    ("ref", "ref", "the real, present AT_ELEMENT_ARRAY reference attribute name used at every node in this graph"),
]

NULL_PATTRNAME_PROBE_STATUS = (
    "NOT_TESTED_UNKNOWN -- no installed binding/source evidence establishes that "
    "CElementTreeTraversal safely accepts a NULL pAttrName; not assumed equivalent "
    "to the empty-string probe; would require its own explicit safety review "
    "before being tested."
)


# ---------------------------------------------------------------------------
# Legacy control and native traversal runners.
# ---------------------------------------------------------------------------

def run_legacy_reachable(reachable_fn, handle_fn, root_obj, label):
    t0 = time.time()
    try:
        out = list(reachable_fn(root_obj))
    except Exception as exc:
        return {
            "label": label, "exception": repr(exc), "elapsed_seconds": time.time() - t0,
            "sequence_handles": None, "sequence_length": None, "unique_handles": None,
            "unique_count": None, "duplicate_count": None,
        }
    elapsed = time.time() - t0
    handles = []
    for o in out:
        try:
            handles.append(handle_fn(o))
        except Exception:
            pass
    unique = sorted(set(handles))
    return {
        "label": label,
        "exception": None,
        "elapsed_seconds": elapsed,
        "sequence_handles": handles,
        "sequence_length": len(handles),
        "unique_handles": unique,
        "unique_count": len(unique),
        "duplicate_count": len(handles) - len(unique),
    }


def run_native_traversal(traversal_cls, handle_fn, name_fn, root_obj, attr_name_arg, label, max_steps=MAX_TRAVERSAL_STEPS):
    result = {
        "label": label,
        "tested_attr_name_repr": repr(attr_name_arg),
        "constructor_accepted": None,
        "construct_exception": None,
        "steps": [],
        "watchdog_triggered": False,
        "terminated_cleanly": False,
        "loop_exception": None,
        "elapsed_seconds": None,
    }
    t0 = time.time()
    try:
        trav = traversal_cls(root_obj, attr_name_arg)
    except Exception as exc:
        result["constructor_accepted"] = False
        result["construct_exception"] = repr(exc)
        result["elapsed_seconds"] = time.time() - t0
        log_line("[%s] constructor REJECTED attr_name=%r: %r" % (label, attr_name_arg, exc))
        return result

    result["constructor_accepted"] = True
    log_line("[%s] constructor accepted attr_name=%r" % (label, attr_name_arg))

    step_count = 0
    while True:
        try:
            valid = trav.IsValid()
        except Exception as exc:
            result["loop_exception"] = "IsValid() raised: %r" % (exc,)
            break
        if not valid:
            result["terminated_cleanly"] = True
            break

        step_count += 1
        if step_count > max_steps:
            result["watchdog_triggered"] = True
            log_line("[%s] WATCHDOG TRIGGERED at step %d (attr_name=%r)" % (label, step_count, attr_name_arg))
            break

        get_elem, get_exc = None, None
        try:
            get_elem = trav.GetElement()
        except Exception as exc:
            get_exc = repr(exc)

        depth = None
        try:
            depth = trav.CurrentDepth()
        except Exception:
            pass

        get_handle, get_name = None, None
        if get_elem is not None:
            try:
                get_handle = handle_fn(get_elem)
            except Exception:
                pass
            try:
                get_name = name_fn(get_elem)
            except Exception:
                pass

        next_elem, next_exc = None, None
        try:
            next_elem = trav.Next()
        except Exception as exc:
            next_exc = repr(exc)

        next_handle, next_name = None, None
        if next_elem is not None:
            try:
                next_handle = handle_fn(next_elem)
            except Exception:
                pass
            try:
                next_name = name_fn(next_elem)
            except Exception:
                pass

        step_record = {
            "step_index": step_count,
            "current_depth": depth,
            "get_element_handle": get_handle,
            "get_element_name": get_name,
            "get_element_exception": get_exc,
            "next_return_handle": next_handle,
            "next_return_name": next_name,
            "next_return_exception": next_exc,
        }
        result["steps"].append(step_record)
        log_line("[%s] step=%d depth=%r get=%r/%r next=%r/%r" % (
            label, step_count, depth, get_handle, get_name, next_handle, next_name,
        ))

        if next_exc is not None:
            result["loop_exception"] = "Next() raised: %s" % next_exc
            break

    result["elapsed_seconds"] = time.time() - t0

    get_handles = [s["get_element_handle"] for s in result["steps"] if s["get_element_handle"] is not None]
    next_handles = [s["next_return_handle"] for s in result["steps"] if s["next_return_handle"] is not None]
    result["get_element_sequence"] = get_handles
    result["get_element_unique_count"] = len(set(get_handles))
    result["get_element_duplicate_count"] = len(get_handles) - len(set(get_handles))
    result["next_return_sequence"] = next_handles
    result["next_return_unique_count"] = len(set(next_handles))
    result["next_return_duplicate_count"] = len(next_handles) - len(set(next_handles))
    result["get_element_matches_next_return_same_index"] = (get_handles == next_handles)
    result["get_element_matches_next_return_shifted_by_one"] = (get_handles[1:] == next_handles[:-1]) if (len(get_handles) > 1 and len(next_handles) > 1) else None
    return result


def classify_dag_cycle_dedup(dag_native, cycle_native):
    if dag_native is None or cycle_native is None:
        return "INCONCLUSIVE"
    if dag_native.get("constructor_accepted") is not True or cycle_native.get("constructor_accepted") is not True:
        return "INCONCLUSIVE"
    if cycle_native.get("watchdog_triggered"):
        return "NO_SAFE_DEDUP"

    dag_seq = dag_native.get("get_element_sequence") or []
    cycle_seq = cycle_native.get("get_element_sequence") or []
    if len(dag_seq) == 0 or len(cycle_seq) == 0:
        return "INCONCLUSIVE"

    dag_has_duplicates = len(dag_seq) > len(set(dag_seq))
    cycle_has_duplicates = len(cycle_seq) > len(set(cycle_seq))
    cycle_terminated = cycle_native.get("terminated_cleanly") is True

    if (not dag_has_duplicates) and cycle_terminated and (not cycle_has_duplicates):
        return "GLOBAL_DEDUP_EQUIVALENT"
    if dag_has_duplicates and cycle_terminated:
        return "PATH_ONLY_DEDUP"
    if not cycle_terminated:
        return "NO_SAFE_DEDUP"
    return "OTHER"


def graph1_single_call_coverage_ok(graph1_legacy, graph1_native_probes):
    """Decisive question: can ANY ONE tested pAttrName's single traversal
    alone reach legacy's full unique-handle set? (Not the union across
    multiple calls -- a single invocation, per the accepted instruction's
    own decisive-question framing.)"""
    if graph1_legacy is None or graph1_legacy.get("unique_handles") is None:
        return None, None
    legacy_set = set(graph1_legacy["unique_handles"])
    matching_probe_labels = []
    for probe in graph1_native_probes:
        if probe.get("constructor_accepted") is not True:
            continue
        probe_set = set(probe.get("get_element_sequence") or [])
        if probe_set == legacy_set and len(legacy_set) > 0:
            matching_probe_labels.append(probe["tested_attr_name_repr"])
    return (len(matching_probe_labels) > 0), matching_probe_labels


def compute_final_classification(detached_graph_available, coverage_ok, dedup_classification):
    if not detached_graph_available:
        return "INCONCLUSIVE"
    if coverage_ok is None or dedup_classification in ("INCONCLUSIVE",):
        return "INCONCLUSIVE"
    if coverage_ok and dedup_classification == "GLOBAL_DEDUP_EQUIVALENT":
        return "EXACT_CANDIDATE_SUPPORTED"
    return "SEMANTICALLY_INSUFFICIENT"


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------

report = {
    "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "python_version": sys.version,
    "checks": [],
    "anomalies": ANOMALIES,
    "provenance": {},
    "graph_definitions": {
        "multiattr": "ROOT --attr_A--> A --attr_A--> C ; ROOT --attr_B--> B --attr_B--> D ; A --attr_list(array)--> [E, F]",
        "dag": "ROOT --ref(array)--> [A, B] ; A --ref(array)--> [C] ; B --ref(array)--> [C] (shared C)",
        "cycle": "ROOT --ref(array)--> [A] ; A --ref(array)--> [B] ; B --ref(array)--> [ROOT] (cycle)",
    },
    "tested_attr_names": {
        "multiattr": [{"label": lbl, "value_repr": repr(val), "justification": just} for (lbl, val, just) in TESTED_ATTR_NAMES_GRAPH1],
        "dag_and_cycle": [{"label": lbl, "value_repr": repr(val), "justification": just} for (lbl, val, just) in TESTED_ATTR_NAMES_DAG_AND_CYCLE],
    },
    "null_pattrname_probe_status": NULL_PATTRNAME_PROBE_STATUS,
    "detached_graph_available": None,
    "detached_graph_unavailable_reason": None,
    "legacy_control": {},
    "native_probes": {"multiattr": [], "dag": [], "cycle": []},
    "graph1_coverage": {},
    "dag_cycle_dedup_classification": None,
    "final_classification": None,
    "real_scene_sanity_check": {"attempted": False, "reason_not_attempted": None},
    "in_progress": True,
}


def check(name, condition, detail=None):
    report["checks"].append({"name": name, "pass": bool(condition), "detail": repr(detail) if detail is not None else None})
    try:
        sys.stdout.write("[%s] %s%s\n" % ("PASS" if condition else "FAIL", name, ("" if detail is None else " -- %r" % (detail,))))
    except Exception:
        pass


def write_rolling_evidence():
    ok, err, _r = write_json_atomic(JSON_OUTPUT_PATH, report)
    if not ok:
        anomaly("Rolling evidence write failed (run continues): %s" % (err,))
    return ok


main_window = None
instance = None
scratch_fileid = None
created_handles = []

try:
    with open(PRODUCTION_NORMALIZER_PATH, "rb") as f:
        production_bytes = f.read()
    production_sha = hashlib.sha256(production_bytes).hexdigest()
    check("production_normalizer.sha256_matches_accepted_integration", production_sha == EXPECTED_PRODUCTION_NORMALIZER_SHA256, production_sha)

    with open(CANONICAL_MASTER_PATH, "rb") as f:
        master_bytes = f.read()
    master_sha = hashlib.sha256(master_bytes).hexdigest()
    check("canonical_master.sha256_unchanged", master_sha == EXPECTED_CANONICAL_MASTER_SHA256, master_sha)

    if not (production_sha == EXPECTED_PRODUCTION_NORMALIZER_SHA256 and master_sha == EXPECTED_CANONICAL_MASTER_SHA256):
        raise CheckpointF1R8Error("Pre-flight SHA-256 check failed -- refusing to proceed.")
    report["provenance"]["production_normalizer_sha256"] = production_sha
    report["provenance"]["canonical_master_sha256"] = master_sha

    if not bool(sfmApp.HasDocument()):
        raise CheckpointF1R8Error("No SFM document is open.")

    root_for_filename = sfmApp.GetDocumentRoot()
    if root_for_filename is None:
        raise CheckpointF1R8Error("sfmApp.GetDocumentRoot() returned None.")
    open_file_id = root_for_filename.GetFileId()
    open_path = vs.g_pDataModel.GetFileName(open_file_id)
    open_basename = os.path.basename(b_to_unicode(open_path)) if open_path else u""

    check("fixture.refuses_original_fixture_filename", open_basename.lower() != FORBIDDEN_ORIGINAL_FIXTURE_FILENAME.lower(), open_basename)
    check("fixture.matches_expected_normalized_copy_filename", open_basename.lower() == EXPECTED_NORMALIZED_COPY_FILENAME.lower(), open_basename)
    if open_basename.lower() == FORBIDDEN_ORIGINAL_FIXTURE_FILENAME.lower():
        raise CheckpointF1R8Error("REFUSING TO RUN against the original disposable qualification fixture (%r)." % (open_basename,))
    if open_basename.lower() != EXPECTED_NORMALIZED_COPY_FILENAME.lower():
        raise CheckpointF1R8Error("Open document (%r) does not match the expected normalized-copy filename (%r)." % (open_basename, EXPECTED_NORMALIZED_COPY_FILENAME))

    fixture_gate_passed = all(c["pass"] for c in report["checks"])
    if not fixture_gate_passed:
        raise CheckpointF1R8Error("Starting-state fixture gate failed -- aborting before any production invocation.")

    main_window = sfmApp.GetMainWindow()
    check("f1r8.main_window_available", main_window is not None)
    write_rolling_evidence()

    prod_ns = {}
    try:
        exec(compile(production_bytes, "<installed_production_normalizer_f1r8>", "exec"), prod_ns)
    except Exception as exc:
        anomaly("Production Normalizer execution raised: %r" % (exc,))
        anomaly(traceback.format_exc())

    legacy_reachable = prod_ns.get("reachable")
    legacy_handle = prod_ns.get("handle")
    legacy_name = prod_ns.get("name")
    legacy_to_unicode = prod_ns.get("to_unicode")
    legacy_scalar = prod_ns.get("scalar")
    legacy_typ = prod_ns.get("typ")

    for required_name, required_value in (
        ("reachable", legacy_reachable), ("handle", legacy_handle), ("name", legacy_name),
        ("to_unicode", legacy_to_unicode), ("scalar", legacy_scalar), ("typ", legacy_typ),
    ):
        if required_value is None:
            raise CheckpointF1R8Error("Required production name not found in exec'd namespace: %s" % required_name)

    run_lock_name = prod_ns.get("RUN_LOCK_NAME")
    if run_lock_name is None:
        raise CheckpointF1R8Error("RUN_LOCK_NAME not found in exec'd namespace.")

    for child in main_window.findChildren(QtCore.QObject):
        try:
            if b_to_unicode(child.objectName()) == run_lock_name:
                instance = child
                break
        except Exception:
            continue

    check("f1r8.run_instance_located", instance is not None)
    if instance is None:
        raise CheckpointF1R8Error("Could not locate the already-constructed run instance immediately after exec().")

    instance.finished = True
    check("f1r8.real_instance_neutralized", bool(instance.finished))
    write_rolling_evidence()

    # -----------------------------------------------------------------
    # Resolve the detached-graph construction APIs. If any required
    # symbol is missing, or a minimal creation probe fails, report
    # detached_graph_available=False and stop the native-characterization
    # work -- do not invent an alternative method.
    # -----------------------------------------------------------------
    create_element_fn = resolve_datamodel_symbol("CreateElement")
    at_element_const = resolve_datamodel_symbol("AT_ELEMENT")
    at_element_array_const = resolve_datamodel_symbol("AT_ELEMENT_ARRAY")
    traversal_cls = resolve_datamodel_symbol("CElementTreeTraversal")

    check("f1r8.resolved_CreateElement", callable(create_element_fn))
    check("f1r8.resolved_AT_ELEMENT", at_element_const is not None)
    check("f1r8.resolved_AT_ELEMENT_ARRAY", at_element_array_const is not None)
    check("f1r8.resolved_CElementTreeTraversal", traversal_cls is not None)

    detached_graph_available = False
    unavailable_reason = None

    if not (callable(create_element_fn) and at_element_const is not None and at_element_array_const is not None and traversal_cls is not None):
        unavailable_reason = "One or more required datamodel symbols (CreateElement/AT_ELEMENT/AT_ELEMENT_ARRAY/CElementTreeTraversal) could not be resolved from either `vs` or `vs.datamodel`."
    else:
        try:
            scratch_fileid = vs.g_pDataModel.FindOrCreateFileId(SCRATCH_FILEID_NAME)
            # Plain str, not unicode -- see create_scratch_node()'s own F1-R8-R1 comment.
            probe_node = create_element_fn(SCRATCH_ELEMENT_TYPE, "F1R8_PROBE_NODE", scratch_fileid)
            if probe_node is None:
                unavailable_reason = "vs.CreateElement('DmElement', ..., scratch_fileid) returned None on the minimal probe."
            else:
                probe_handle = probe_node.GetHandle()
                created_handles.append(probe_handle)
                probe_attr = probe_node.AddAttribute("probe_scalar", at_element_const)
                probe_attr.SetValue(probe_node)  # self-reference, immediately discarded -- only proves AddAttribute/SetValue work
                detached_graph_available = True
        except Exception as exc:
            unavailable_reason = "Minimal detached-element creation probe raised: %r" % (exc,)

    report["detached_graph_available"] = detached_graph_available
    report["detached_graph_unavailable_reason"] = unavailable_reason
    check("f1r8.detached_graph_available", detached_graph_available, unavailable_reason)
    write_rolling_evidence()

    graph1_legacy = None
    graph1_native_probes = []
    dag_legacy = None
    dag_native = None
    cycle_legacy = None
    cycle_native = None
    coverage_ok = None
    coverage_matching_probes = None
    dedup_classification = "INCONCLUSIVE"

    if detached_graph_available:
        # --- Graph 1: multi-attribute forward references ---
        nodes1 = build_graph_multiattr(create_element_fn, at_element_const, at_element_array_const, scratch_fileid)
        for n in nodes1.values():
            created_handles.append(n.GetHandle())

        graph1_legacy = run_legacy_reachable(legacy_reachable, legacy_handle, nodes1["root"], "multiattr_legacy")
        report["legacy_control"]["multiattr"] = graph1_legacy
        log_line("=== GRAPH 1 (multiattr) LEGACY: %r ===" % (graph1_legacy,))

        for (lbl, val, just) in TESTED_ATTR_NAMES_GRAPH1:
            probe = run_native_traversal(traversal_cls, legacy_handle, legacy_name, nodes1["root"], val, "multiattr_native_%s" % lbl)
            graph1_native_probes.append(probe)
        report["native_probes"]["multiattr"] = graph1_native_probes
        write_rolling_evidence()

        coverage_ok, coverage_matching_probes = graph1_single_call_coverage_ok(graph1_legacy, graph1_native_probes)
        report["graph1_coverage"] = {
            "single_call_coverage_ok": coverage_ok,
            "matching_probe_attr_names": coverage_matching_probes,
            "legacy_unique_count": graph1_legacy.get("unique_count"),
        }
        check("f1r8.graph1_single_call_coverage_evaluated", coverage_ok is not None, coverage_ok)

        # --- Graph 2: shared-reference DAG ---
        nodes2 = build_graph_dag(create_element_fn, at_element_array_const, scratch_fileid)
        for n in nodes2.values():
            created_handles.append(n.GetHandle())

        dag_legacy = run_legacy_reachable(legacy_reachable, legacy_handle, nodes2["root"], "dag_legacy")
        report["legacy_control"]["dag"] = dag_legacy
        log_line("=== GRAPH 2 (dag) LEGACY: %r ===" % (dag_legacy,))

        for (lbl, val, just) in TESTED_ATTR_NAMES_DAG_AND_CYCLE:
            dag_native = run_native_traversal(traversal_cls, legacy_handle, legacy_name, nodes2["root"], val, "dag_native_%s" % lbl)
        report["native_probes"]["dag"] = [dag_native] if dag_native is not None else []
        write_rolling_evidence()

        # --- Graph 3: cycle ---
        nodes3 = build_graph_cycle(create_element_fn, at_element_array_const, scratch_fileid)
        for n in nodes3.values():
            created_handles.append(n.GetHandle())

        cycle_legacy = run_legacy_reachable(legacy_reachable, legacy_handle, nodes3["root"], "cycle_legacy")
        report["legacy_control"]["cycle"] = cycle_legacy
        log_line("=== GRAPH 3 (cycle) LEGACY: %r ===" % (cycle_legacy,))

        for (lbl, val, just) in TESTED_ATTR_NAMES_DAG_AND_CYCLE:
            cycle_native = run_native_traversal(traversal_cls, legacy_handle, legacy_name, nodes3["root"], val, "cycle_native_%s" % lbl)
        report["native_probes"]["cycle"] = [cycle_native] if cycle_native is not None else []
        write_rolling_evidence()

        dedup_classification = classify_dag_cycle_dedup(dag_native, cycle_native)
        report["dag_cycle_dedup_classification"] = dedup_classification
        check("f1r8.dag_cycle_dedup_classified", dedup_classification is not None, dedup_classification)

    final_classification = compute_final_classification(detached_graph_available, coverage_ok, dedup_classification)
    report["final_classification"] = final_classification
    check("f1r8.final_classification_computed", final_classification is not None, final_classification)
    write_rolling_evidence()

    # -----------------------------------------------------------------
    # Optional real-scene read-only sanity check -- ONLY if the detached
    # graph already established EXACT_CANDIDATE_SUPPORTED.
    # -----------------------------------------------------------------
    if final_classification == "EXACT_CANDIDATE_SUPPORTED":
        report["real_scene_sanity_check"]["attempted"] = True
        try:
            work = instance.work
            if not work:
                raise CheckpointF1R8Error("instance.work is empty; cannot run the real-scene sanity check.")
            first_shot = work[0]["shot"]
            scene = legacy_scalar(first_shot, "scene")
            winning_attr_name = coverage_matching_probes[0] if coverage_matching_probes else None
            winning_attr_value = None
            for (lbl, val, just) in TESTED_ATTR_NAMES_GRAPH1:
                if repr(val) == winning_attr_name:
                    winning_attr_value = val
                    break

            scene_legacy = run_legacy_reachable(legacy_reachable, legacy_handle, scene, "real_scene_legacy")
            scene_native = run_native_traversal(traversal_cls, legacy_handle, legacy_name, scene, winning_attr_value, "real_scene_native")

            legacy_set = set(scene_legacy.get("unique_handles") or [])
            native_set = set(scene_native.get("get_element_sequence") or [])
            report["real_scene_sanity_check"].update({
                "legacy": scene_legacy,
                "native": scene_native,
                "unique_handle_sets_equal": (legacy_set == native_set),
                "legacy_unique_count": len(legacy_set),
                "native_unique_count": len(native_set),
            })
            check("f1r8.real_scene_sanity_check_ran", True)
        except Exception as exc:
            report["real_scene_sanity_check"]["reason_not_attempted"] = "Attempted but raised: %r" % (exc,)
            anomaly("Real-scene sanity check raised: %r" % (exc,))
    else:
        report["real_scene_sanity_check"]["reason_not_attempted"] = (
            "final_classification=%r -- real-scene sanity check is gated behind EXACT_CANDIDATE_SUPPORTED only." % (final_classification,)
        )

    check("neutralization.real_pipeline_never_advanced", getattr(instance, "total_shots_processed", 0) == 0, getattr(instance, "total_shots_processed", None))

except CheckpointF1R8Error as gate_exc:
    anomaly("GATE FAILURE (orderly abort): %s" % gate_exc)
    report["gate_failure"] = True
except Exception as top_exc:
    anomaly("UNHANDLED TOP-LEVEL EXCEPTION: %s" % repr(top_exc))
    anomaly(traceback.format_exc())
    report["gate_failure"] = False
finally:
    # Destroy every created scratch element and remove the scratch file ID,
    # regardless of outcome.
    destroyed_count = 0
    destroy_errors = []
    for h in created_handles:
        try:
            vs.g_pDataModel.DestroyElement(h)
            destroyed_count += 1
        except Exception as exc:
            destroy_errors.append(repr(exc))
    if scratch_fileid is not None:
        try:
            vs.g_pDataModel.RemoveFileId(scratch_fileid)
        except Exception as exc:
            destroy_errors.append("RemoveFileId: %r" % (exc,))
    report["scratch_cleanup"] = {
        "created_count": len(created_handles),
        "destroyed_count": destroyed_count,
        "destroy_errors": destroy_errors,
    }
    if destroy_errors:
        anomaly("Scratch cleanup had errors: %r" % (destroy_errors,))

# ---------------------------------------------------------------------------
# Finalize / write output.
# ---------------------------------------------------------------------------

report["in_progress"] = False
report["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

all_checks_passed = all(c["pass"] for c in report["checks"]) if report["checks"] else False
completed_without_exception = not any(a.startswith("UNHANDLED TOP-LEVEL EXCEPTION") for a in ANOMALIES)
report["overall_pass"] = bool(all_checks_passed and completed_without_exception and not report.get("gate_failure"))

json_write_ok, json_write_error, _r = write_json_atomic(JSON_OUTPUT_PATH, report)
if not json_write_ok:
    anomaly("Final JSON write failed: %s" % json_write_error)

summary_lines = []
summary_lines.append("SFM CHECKPOINT F1-R8 -- CELEMENTTREETRAVERSAL NATIVE SEMANTIC CHARACTERIZATION")
summary_lines.append("started_at=%s  finished_at=%s" % (report["started_at"], report["finished_at"]))
if report.get("gate_failure"):
    summary_lines.append("*** GATE FAILURE ***")
summary_lines.append("")
summary_lines.append("--- CHECKS ---")
for c in report["checks"]:
    summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
summary_lines.append("")
summary_lines.append("null_pattrname_probe_status=%r" % (report.get("null_pattrname_probe_status"),))
summary_lines.append("detached_graph_available=%r  reason=%r" % (report.get("detached_graph_available"), report.get("detached_graph_unavailable_reason")))
summary_lines.append("graph1_coverage=%r" % (report.get("graph1_coverage"),))
summary_lines.append("dag_cycle_dedup_classification=%r" % (report.get("dag_cycle_dedup_classification"),))
summary_lines.append("FINAL_CLASSIFICATION=%r" % (report.get("final_classification"),))
summary_lines.append("real_scene_sanity_check=%r" % (report.get("real_scene_sanity_check"),))
summary_lines.append("scratch_cleanup=%r" % (report.get("scratch_cleanup"),))
summary_lines.append("")
summary_lines.append("OVERALL_PASS=%r" % report["overall_pass"])
summary_lines.append("")
summary_lines.append("--- ANOMALIES (%d) ---" % len(ANOMALIES))
for a in ANOMALIES:
    summary_lines.append("- %s" % a)
if not ANOMALIES:
    summary_lines.append("(none)")
summary_lines.append("")
summary_lines.append("json_output_path=%s (write_ok=%r)" % (JSON_OUTPUT_PATH, json_write_ok))

summary_text = u"\n".join(summary_lines) + u"\n"
summary_write_ok, summary_write_error = write_text_atomic(SUMMARY_OUTPUT_PATH, summary_text.encode("ascii", "replace"))

traversal_log_text = u"\n".join(TRAVERSAL_LOG_LINES) + u"\n"
traversal_log_write_ok, traversal_log_write_error = write_text_atomic(NATIVE_TRAVERSAL_LOG_PATH, traversal_log_text.encode("ascii", "replace"))

try:
    sys.stdout.write(summary_text.encode("ascii", "replace"))
    sys.stdout.write(
        "\nCheckpoint F1-R8 reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r)\n  %s (write_ok=%r)\n"
        % (JSON_OUTPUT_PATH, json_write_ok, SUMMARY_OUTPUT_PATH, summary_write_ok, NATIVE_TRAVERSAL_LOG_PATH, traversal_log_write_ok)
    )
    sys.stdout.write("\nThis checkpoint never mutated the open document. DO NOT SAVE anyway, per standing discipline. Restart SFM afterward.\n")
except Exception:
    pass
