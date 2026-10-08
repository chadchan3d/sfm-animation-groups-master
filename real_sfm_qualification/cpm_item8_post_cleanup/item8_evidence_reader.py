# -*- coding: utf-8 -*-
"""CPM item 8 -- offline evidence reader (qualification-only; never deployed).

Reads one item-8 attempt folder (live, or its redacted repository copy) and
derives the mechanical facts the adjudicator needs. It never decides PASS by
itself: product "verified" flags are not oracles, and every check here is
paired with operator observations and preselected values (ITEM8_RUNBOOK.md).

Python 2.7 and 3.x. Read-only: it writes nothing.

  item8_evidence_reader.py summary <attempt-dir> [--log <cpm-log-excerpt>]
  item8_evidence_reader.py snapshot-diff <attempt-dir> <seq-a> <seq-b> [<animset>]
  item8_evidence_reader.py library-diff <before.txt> <after.txt> --allow <rule> [...]
  item8_evidence_reader.py readback <preset.json> <literal>
  item8_evidence_reader.py verify-sums <attempt-dir>
"""
from __future__ import print_function

import hashlib
import io
import json
import os
import re
import sys

CANDIDATE_APP_SHA256 = "bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5"
LAUNCHER_SHA256 = "996ca483d625d37feb8d8f38a8d13db16f999d4189d98434db9c284a0a458c51"
G1_MASTER = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
G2_MASTER = "54413b6ca618f73733b6624e1d2411a6cfb00a24489330ccbfc153760f3486e7"
PROBE_SCHEMA = "cpm-item8-probe-record-v1"
SNAPSHOT_SCHEMA = "cpm-item8-scene-snapshot-v1"
EPS = 1.0e-5
HISTORICAL_COUNTERS = ("_SEMANTIC_PROVIDER_OPEN_COUNT", "_SEMANTIC_PROVIDER_REUSE_COUNT",
                       "_SEMANTIC_PROVIDER_INVALIDATION_COUNT", "_SEMANTIC_PROVIDER_PRODUCTION_PARSE_COUNT",
                       "_SEMANTIC_PROVIDER_GENERATION")

try:
    _TEXT = unicode  # noqa: F821
except NameError:
    _TEXT = str

# ---------------------------------------------------------------------------
# Current (item-7 candidate) retained event formats. Every pattern below is
# checked against the candidate's own log_line format strings by
# test_cpm_item8_probe.py. Timestamps: the CPM log prefixes "[HH:MM:SS.ffffff] ".
# ---------------------------------------------------------------------------
_STAMP = r"^\[(?P<time>\d\d:\d\d:\d\d(?:\.\d+)?)\] "
CURRENT_EVENTS = [
    ("G18AN_RUN", r"G18AN_RUN run_id=(?P<run_id>\S+) pid=(?P<pid>\d+) parity_oracle=(?P<parity_oracle>\S+)"),
    ("PROD_R15_MODULE", r"PROD_R15_MODULE name=(?P<name>\S+) loader=(?P<loader>\S+) state=(?P<state>\S+) "
                        r"build_sha256=(?P<build_sha256>\S+) file=(?P<file>.+)"),
    ("PROD_R15_WINDOW_REUSED", r"PROD_R15_WINDOW_REUSED run_id=(?P<run_id>\S+)"),
    ("PROD_WINDOW_SHOWN", r"PROD_WINDOW_SHOWN=True initial_index=(?P<initial_index>-?\d+)"),
    ("PROD_CLOSE_REQUEST", r"PROD_CLOSE_REQUEST operation=(?P<operation>\S+) fit_active=(?P<fit_active>\S+) "
                           r"fit_stage_running=(?P<fit_stage_running>\S+)"),
    ("PROD_CLOSE_FINALIZED", r"PROD_CLOSE_FINALIZED=True"),
    ("PROD_PROVIDER_HEALTH", r"PROD_PROVIDER_HEALTH status=(?P<status>\S+) reason=(?P<reason>\S+)(?P<rest>.*)"),
    ("PROD_MODEL_SWITCH_STAGE", r"PROD_MODEL_SWITCH_STAGE stage='(?P<stage>[^']+)'(?P<rest>.*)"),
    ("PROD_CPM_OPERATION_AUTHORIZED", r"PROD_CPM_OPERATION_AUTHORIZED operation=(?P<operation>u?'[^']*') "
                                      r"sha256=(?P<sha256>[0-9a-f]{64}) kind=(?P<kind>\S+) membership=(?P<membership>.+)"),
    ("PROD_CPM_OPERATION_AUTHORIZATION_REFUSED", r"PROD_CPM_OPERATION_AUTHORIZATION_REFUSED "
                                                 r"operation=(?P<operation>u?'[^']*') reason=(?P<reason>\S+)"),
    ("PROD_CPM_STALE_GENERATION_REBUILD_SCHEDULED",
     r"PROD_CPM_STALE_GENERATION_REBUILD_SCHEDULED identity=(?P<identity>.+)"),
    ("PROD_CPM_STALE_GENERATION_REBUILD", r"PROD_CPM_STALE_GENERATION_REBUILD identity=(?P<identity>.+)"),
    ("PROD_OPERATION_BEGIN", r"PROD_OPERATION_BEGIN id=(?P<id>\d+) kind=(?P<kind>u?'[^']*') context=(?P<context>.+)"),
    ("PROD_OPERATION_END", r"PROD_OPERATION_END id=(?P<id>\d+) kind=(?P<kind>u?'[^']*') phase=(?P<phase>\S+) "
                           r"native_commit=(?P<native_commit>\S+) durable_commit=(?P<durable_commit>\S+)"),
    ("PROD_APPLY", r"PROD_APPLY outcome='(?P<outcome>[^']+)'(?P<rest>.*)"),
    ("PROD_SAVE", r"PROD_SAVE=PASS model=(?P<model>\S+) kind=(?P<kind>\S+) name=(?P<name>u?'[^']*') "
                  r"controls=(?P<controls>\d+)(?P<rest>.*)"),
    ("PROD_UPDATE", r"PROD_UPDATE=PASS model=(?P<model>\S+) kind=(?P<kind>\S+) preset=(?P<preset>u?'[^']*') "
                    r"controls=(?P<controls>\d+)(?P<rest>.*)"),
    ("PROD_CPM_FIT_STAGE_OPEN", r"PROD_CPM_FIT_STAGE_OPEN index=(?P<index>\d+) gfit=(?P<gfit>[0-9a-f]{64}) "
                                r"literals=(?P<literals>\d+)"),
    ("PROD_CPM_FIT_STAGE_RELEASED", r"PROD_CPM_FIT_STAGE_RELEASED index=(?P<index>\d+) ok=(?P<ok>\S+)"),
    ("CLOTHING_FIT_STAGE", r"CLOTHING_FIT_STAGE=(?P<status>PASS|SKIP) generation=(?P<generation>\d+) "
                           r"index=(?P<index>\d+)(?P<rest>.*)"),
    ("CLOTHING_FIT_RESULT", r"CLOTHING_FIT_RESULT generation=(?P<generation>\d+) selected=(?P<selected>\d+) "
                            r"changed=(?P<changed>\d+) already_matched=(?P<already_matched>\d+) "
                            r"partial=(?P<partial>\d+) partial_changed=(?P<partial_changed>\d+) "
                            r"partial_already_matched=(?P<partial_already_matched>\d+) skipped=(?P<skipped>\d+) "
                            r"failed=(?P<failed>\d+) unattempted=(?P<unattempted>\d+) "
                            r"committed_order=(?P<committed_order>.+?) reusable=True pure_source_baseline=True"),
    ("PROD_RESOURCE", r"PROD_RESOURCE label=(?P<label>u?'[^']*') working_set_mb=(?P<working_set_mb>\S+) "
                      r"private_commit_mb=(?P<private_commit_mb>\S+)(?P<rest>.*)"),
]
_COMPILED = [(tag, re.compile(_STAMP + pattern + r"\s*$")) for tag, pattern in CURRENT_EVENTS]
# Removed by item 7 or superseded; their presence means the log is not the candidate's.
REMOVED_OR_HISTORICAL = [
    ("CLOTHING_FIT_RESULT=PASS (historical pre-item-7 format)", re.compile(r"CLOTHING_FIT_RESULT=PASS ")),
    ("PROD_PERF (removed by item 7)", re.compile(r"\] PROD_PERF ")),
    ("ASTRA_PERF (removed by item 7)", re.compile(r"\] ASTRA_PERF ")),
    ("PROD_ACTION_TIMING (removed by item 7)", re.compile(r"\] PROD_ACTION_TIMING ")),
    ("PROD_MODELS candidate dump (removed by item 7)", re.compile(r"\] PROD_MODELS .*candidates=")),
    ("G18AN_PROVIDER_FORCE_MODE (removed by item 7)", re.compile(r"\] G18AN_PROVIDER_FORCE_MODE")),
]


def parse_log(text):
    """Classify CPM log lines. Returns {"events": [...], "historical_or_removed": [...]}.
    Only CURRENT_EVENTS are events; historical/removed formats are reported, never
    counted (a historical Fit result is not a current Fit result)."""
    events, flagged = [], []
    for number, line in enumerate(text.splitlines(), 1):
        for label, regex in REMOVED_OR_HISTORICAL:
            if regex.search(line):
                flagged.append({"line": number, "label": label, "text": line})
        for tag, regex in _COMPILED:
            m = regex.match(line)
            if m:
                fields = m.groupdict()
                events.append({"line": number, "tag": tag, "time": fields.pop("time"), "fields": fields})
                break
    return {"events": events, "historical_or_removed": flagged}


def events_of(parsed, tag):
    return [e for e in parsed["events"] if e["tag"] == tag]


# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------
def _read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def _json_bytes(raw):
    if raw[:3] == b"\xef\xbb\xbf":
        raw = raw[3:]
    return json.loads(raw.decode("utf-8"))


def load_json(path):
    return _json_bytes(_read_bytes(path))


def load_probe_records(attempt_dir):
    """probe.jsonl: append-only, one record per line, seq 1..n contiguous."""
    raw = _read_bytes(os.path.join(attempt_dir, "probe.jsonl"))
    if raw and not raw.endswith(b"\n"):
        raise ValueError("probe.jsonl does not end with a newline")
    records = [json.loads(line.decode("utf-8")) for line in raw.splitlines() if line.strip()]
    for i, rec in enumerate(records, 1):
        if rec.get("schema") != PROBE_SCHEMA:
            raise ValueError("record %d has schema %r" % (i, rec.get("schema")))
        if rec.get("seq") != i:
            raise ValueError("probe seq not contiguous at line %d (seq=%r)" % (i, rec.get("seq")))
    return records


def load_snapshot(attempt_dir, record):
    meta = record.get("scene_snapshot") or {}
    if not meta.get("observed"):
        raise ValueError("probe seq %s has no scene snapshot: %s" % (record.get("seq"), meta.get("error")))
    raw = _read_bytes(os.path.join(attempt_dir, *meta["file"].split("/")))
    if hashlib.sha256(raw).hexdigest() != meta["sha256"]:
        raise ValueError("scene snapshot %s does not match its probe-recorded SHA-256" % meta["file"])
    snap = _json_bytes(raw)
    if snap.get("schema") != SNAPSHOT_SCHEMA or snap.get("seq") != record.get("seq"):
        raise ValueError("scene snapshot %s schema/seq mismatch" % meta["file"])
    return snap


# ---------------------------------------------------------------------------
# Probe-record checks (mechanical; "insufficient observability" is never PASS)
# ---------------------------------------------------------------------------
def _int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def idle_check(record):
    """Idle authority ownership at a completed/closed checkpoint."""
    problems, unobserved = [], []
    b = record.get("broker_before") or {}
    if not b.get("observed"):
        unobserved.append("broker state")
    elif not b.get("runtime_loaded") or not b.get("broker_constructed"):
        unobserved.append("canonical broker not constructed")
    else:
        for key in ("outstanding_leases", "unreleased_lease_registry"):
            if not _int(b.get(key)):
                unobserved.append(key)
            elif b[key] != 0:
                problems.append("%s=%s" % (key, b[key]))
        pc = b.get("provider_counters")
        if not isinstance(pc, dict) or not _int(pc.get("current_open_provider_count")):
            unobserved.append("current_open_provider_count")
        elif pc["current_open_provider_count"] != 0:
            problems.append("open_providers=%s" % pc["current_open_provider_count"])
    w = record.get("window") or {}
    if not w.get("observed"):
        unobserved.append("window")
    elif w.get("slot_occupied") and w.get("owned_by_private_module"):
        if w.get("operation") is not None:
            problems.append("operation active: %r" % (w.get("operation"),))
        for key in ("fit_active", "fit_stage_running", "modal_deferred_fit_stage_pending", "busy"):
            if w.get(key) not in (False, None):
                problems.append("%s=%r" % (key, w.get(key)))
    acq = record.get("acquisition_by_probe") or {}
    if not acq.get("determinable"):
        unobserved.append("probe acquisition delta")
    elif acq.get("probe_caused_acquisition"):
        problems.append("probe caused acquisition: %r" % (acq.get("changed") or acq.get("reason"),))
    return {"idle": not problems and not unobserved, "problems": problems, "unobserved": unobserved}


def historical_check(record):
    """Historical provider telemetry at its inactive baseline (None, all zero)."""
    m = record.get("module") or {}
    if not m.get("present"):
        return {"inactive": None, "reason": "private module not loaded"}
    h = m.get("historical") or {}
    problems, unobserved = [], []
    if h.get("semantic_provider_is_none") is not True:
        problems.append("_SEMANTIC_PROVIDER is not None")
    for name in HISTORICAL_COUNTERS:
        value = h.get(name)
        if not _int(value):
            unobserved.append(name)
        elif value != 0:
            problems.append("%s=%s" % (name, value))
    return {"inactive": not problems and not unobserved, "problems": problems, "unobserved": unobserved}


def identity_check(record):
    """Exact candidate, private module, isolation (Phase A criteria)."""
    ident, m, w = record.get("identity") or {}, record.get("module") or {}, record.get("window") or {}
    host = record.get("host") or {}
    checks = {
        "python_2_7_5": record.get("python") == "2.7.5",
        "installed_impl_is_candidate": ident.get("installed_impl_sha256") == CANDIDATE_APP_SHA256,
        "installed_launcher_pinned": ident.get("installed_launcher_sha256") == LAUNCHER_SHA256,
        "no_cpm_names_in_main": host.get("cpm_names_in_main") == [],
    }
    if m.get("present"):
        checks.update({
            "module_build_is_candidate": m.get("build_sha256") == CANDIDATE_APP_SHA256,
            "module_file_is_impl_path": m.get("file_is_impl_path") is True,
            "module_private_loader": m.get("loader_is_private_loader") is True,
            "module_ready": m.get("state") == "ready",
            "module_dict_not_main": m.get("module_dict_is_main_dict") is False,
            "no_other_cpm_modules": m.get("other_modules_defining_cpm") == [],
        })
    if w.get("slot_occupied"):
        checks.update({
            "window_owned_by_private_module": w.get("owned_by_private_module") is True,
            "window_globals_private": w.get("function_globals_is_private_module") is True,
            "window_alive": w.get("alive") is True,
        })
    return {"ok": all(checks.values()), "checks": checks}


def census_check(record, windows, watchers):
    c = record.get("census") or {}
    if not c.get("observed"):
        return {"ok": False, "unobserved": True}
    ok = (c.get("prodwindow_toplevel_total") == windows and c.get("prodwindow_toplevel_owned") == windows
          and c.get("active_watchers") == watchers)
    return {"ok": ok, "census": c}


def same_process_module(a, b):
    """Stable private module/class/run identity across two probe records."""
    ma, mb = a.get("module") or {}, b.get("module") or {}
    keys = ("id", "prodwindow_class_id", "startprodtool_id", "run_id", "build_sha256")
    return {"same": a.get("pid") == b.get("pid") and all(ma.get(k) == mb.get(k) for k in keys) and bool(ma.get("id")),
            "differs": [k for k in keys if ma.get(k) != mb.get(k)] + ([] if a.get("pid") == b.get("pid") else ["pid"])}


def scope_generation(record):
    w = record.get("window") or {}
    return (w.get("scope") or {}).get("provider_sha256")


# ---------------------------------------------------------------------------
# Scene snapshots
# ---------------------------------------------------------------------------
def _num(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _same_side(a, b):
    if set(a) != set(b):
        return False
    for key in a:
        x, y = a[key], b[key]
        if _num(x) and _num(y):
            if abs(float(x) - float(y)) > EPS:
                return False
        elif x != y:
            return False
    return True


def snapshot_diff(snap_a, snap_b, animset):
    """Literals whose recorded per-side values differ between two snapshots of one
    fixture animation set; missing sets are reported, never treated as equal."""
    sa = ((snap_a.get("scene") or {}).get("fixture_sets") or {}).get(animset)
    sb = ((snap_b.get("scene") or {}).get("fixture_sets") or {}).get(animset)
    if sa is None or sb is None:
        return {"comparable": False, "reason": "%s missing from %s" % (animset, "a" if sa is None else "b")}
    changed = []
    for literal in sorted(set(sa) | set(sb)):
        la, lb = sa.get(literal), sb.get(literal)
        if la is None or lb is None or set(la) != set(lb) or not all(_same_side(la[s], lb[s]) for s in la):
            changed.append(literal)
    return {"comparable": True, "changed": changed, "literal_count": len(sa)}


def snapshot_value(snap, animset, literal, side="mono", key="evaluated"):
    sets = (snap.get("scene") or {}).get("fixture_sets") or {}
    return ((sets.get(animset) or {}).get(literal) or {}).get(side, {}).get(key)


def undo_state(snap):
    return (snap.get("scene") or {}).get("undo")


# ---------------------------------------------------------------------------
# Preset readback and library inventories
# ---------------------------------------------------------------------------
def preset_value(record, literal):
    """A saved value as written by p02_saved_value_record: values["flex.<literal>"]."""
    entry = (record.get("values") or {}).get(u"flex." + literal)
    if entry is None:
        raise KeyError("preset has no flex.%s value" % literal)
    if entry.get("representation") == "MONO":
        return {"mono": float(entry["mono"])}
    if entry.get("representation") == "STEREO":
        return {"left": float(entry["left"]), "right": float(entry["right"])}
    raise ValueError("unknown representation %r" % (entry.get("representation"),))


def load_library_inventory(path):
    """Write-LibInventory output: '<relative path>\\t<sha256>' lines, ordinal-sorted, LF."""
    rows = {}
    raw = _read_bytes(path).decode("utf-8")
    for line in raw.split("\n"):
        if not line:
            continue
        rel, sha = line.rsplit("\t", 1)
        rows[rel] = sha
    return rows


# prod_unique_path: <folder>/<prod_safe_name(name)[:100]>--<preset_id[:12]>[-N].json, preset_id
# "preset-" + uuid4 hex; folders P03_BODY_FOLDER "Body Presets" / P03_EXPRESSION_FOLDER "Expressions".
_PRESET_FILE = re.compile(r"^(?P<folder>Body Presets|Expressions)/(?P<name>.+)--preset-[0-9a-f]{5}(?:-\d+)?\.json$")


def classify_library_diff(before, after, allow):
    """Classify a library change against an explicit allowed persistence footprint.

    allow: list of rules, each one of
      ("new-preset", folder, name)      exactly one added '<folder>/<name>--preset-<5hex>.json'
      ("changed", relative_path)        that existing file may change (or stay identical)
      ("optional", relative_path)       that file may be added or changed (or stay identical)
    Anything else added, removed or changed is a violation. A required new preset
    that is missing is a violation; an allowed file that is byte-identical is not.
    """
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(k for k in set(before) & set(after) if before[k] != after[k])
    accounted, violations, satisfied = set(), [], []
    for rule in allow:
        if rule[0] == "new-preset":
            folder, name = rule[1], rule[2]
            hits = []
            for k in added:
                m = _PRESET_FILE.match(k)
                if m and m.group("folder") == folder and m.group("name") == name:
                    hits.append(k)
            if len(hits) != 1:
                violations.append("expected exactly one new %s preset %r; found %r" % (folder, name, hits))
            else:
                satisfied.append(hits[0])
            accounted.update(hits)
        elif rule[0] == "changed":
            if rule[1] not in before:
                violations.append("allowed-changed file %r was not present before" % rule[1])
            accounted.add(rule[1])
        elif rule[0] == "optional":
            accounted.add(rule[1])
        else:
            raise ValueError("unknown rule %r" % (rule,))
    for k in added + changed:
        if k not in accounted:
            violations.append("unexpected %s: %s" % ("addition" if k in added else "change", k))
    for k in removed:
        violations.append("unexpected removal: %s" % k)
    return {"ok": not violations, "added": added, "removed": removed, "changed": changed,
            "violations": violations, "new_presets": satisfied}


# ---------------------------------------------------------------------------
# Attempt integrity
# ---------------------------------------------------------------------------
def verify_sha256sums(attempt_dir):
    """SHA256SUMS.txt: '<sha256>  <relative path>' for every other file in the attempt."""
    listed, problems = {}, []
    raw = _read_bytes(os.path.join(attempt_dir, "SHA256SUMS.txt")).decode("utf-8")
    for line in raw.split("\n"):
        if not line:
            continue
        sha, rel = line.split("  ", 1)
        listed[rel] = sha
    actual = set()
    for base, _dirs, files in os.walk(attempt_dir):
        for name in files:
            rel = os.path.relpath(os.path.join(base, name), attempt_dir).replace(os.sep, "/")
            if rel != "SHA256SUMS.txt":
                actual.add(rel)
    for rel in sorted(actual - set(listed)):
        problems.append("unlisted file: %s" % rel)
    for rel in sorted(set(listed) - actual):
        problems.append("listed file missing: %s" % rel)
    for rel in sorted(actual & set(listed)):
        if hashlib.sha256(_read_bytes(os.path.join(attempt_dir, *rel.split("/")))).hexdigest() != listed[rel]:
            problems.append("hash mismatch: %s" % rel)
    return {"ok": not problems, "files": len(listed), "problems": problems}


def summary(attempt_dir, log_text=None):
    records = load_probe_records(attempt_dir)
    rows = []
    for rec in records:
        rows.append({"seq": rec["seq"], "wall_time": rec.get("wall_time"), "pid": rec.get("pid"),
                     "identity": identity_check(rec)["ok"], "idle": idle_check(rec),
                     "historical": historical_check(rec)["inactive"],
                     "census": (rec.get("census") or {}).get("prodwindow_toplevel_total"),
                     "watchers": (rec.get("census") or {}).get("active_watchers"),
                     "scope_generation": scope_generation(rec), "errors": sorted(rec.get("errors") or {})})
    out = {"attempt": os.path.basename(os.path.normpath(attempt_dir)), "probes": rows,
           "pids": sorted(set(r.get("pid") for r in records))}
    if log_text is not None:
        parsed = parse_log(log_text)
        counts = {}
        for e in parsed["events"]:
            counts[e["tag"]] = counts.get(e["tag"], 0) + 1
        out["log_event_counts"] = counts
        out["log_historical_or_removed"] = parsed["historical_or_removed"]
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, args = argv[1], argv[2:]
    if cmd == "summary":
        log = None
        if "--log" in args:
            log = io.open(args[args.index("--log") + 1], encoding="utf-8", errors="replace").read()
        result = summary(args[0], log)
    elif cmd == "snapshot-diff":
        records = dict((r["seq"], r) for r in load_probe_records(args[0]))
        a, b = load_snapshot(args[0], records[int(args[1])]), load_snapshot(args[0], records[int(args[2])])
        names = [args[3]] if len(args) > 3 else sorted(set((a["scene"].get("fixture_sets") or {})) |
                                                       set((b["scene"].get("fixture_sets") or {})))
        result = dict((n, snapshot_diff(a, b, n)) for n in names)
        result["undo"] = {"a": undo_state(a), "b": undo_state(b)}
    elif cmd == "library-diff":
        rules = []
        for spec in args[args.index("--allow") + 1:] if "--allow" in args else []:
            parts = spec.split(":", 2)
            rules.append(tuple(parts))
        result = classify_library_diff(load_library_inventory(args[0]), load_library_inventory(args[1]), rules)
    elif cmd == "readback":
        result = preset_value(load_json(args[0]), args[1])
    elif cmd == "verify-sums":
        result = verify_sha256sums(args[0])
    else:
        print(__doc__)
        return 2
    print(json.dumps(result, indent=1, sort_keys=True, default=_TEXT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
