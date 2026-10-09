# -*- coding: utf-8 -*-
"""K -- offline evidence reader (qualification-only; never deployed).

Reads one K attempt folder (live, or a redacted repository copy) and derives the
mechanical facts the K adjudicator needs. It never decides PASS by itself; every
check is paired with the operator observations named in the K runbook
(cpm/qualification/K_INTEGRATED_PRODUCT_WORKFLOW_QUALIFICATION_DESIGN.md).

Build-agnostic helpers (CPM log grammar, scene-snapshot diff, preset readback,
library footprint, SHA256SUMS) are reused unchanged from the item-8 reader
(real_sfm_qualification/cpm_item8_post_cleanup/item8_evidence_reader.py). K adds:
pinned K identities and schemas, the production Normalizer log grammar,
per-consumer broker-view decomposition, consumer-boundary checks and the
design's section 5.4 resource rules.

Python 2.7 and 3.x. Read-only: it writes nothing.

  k_evidence_reader.py summary <attempt-dir> [--log <cpm-log>] [--normalizer-log <log> ...]
  k_evidence_reader.py normalizer <normalizer-log>
  k_evidence_reader.py views <attempt-dir> <seq>
  k_evidence_reader.py resources <attempt-dir> <seq> [<seq> ...]
  k_evidence_reader.py verify-sums <attempt-dir>
"""
from __future__ import print_function

import hashlib
import io
import json
import os
import re
import sys

_THIS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS, os.pardir, "cpm_item8_post_cleanup"))
import item8_evidence_reader as base  # noqa: E402

CANDIDATE_APP_SHA256 = "4e35f29242351317f2f961c27e19d66fcd3355cff964b081431fc2fff1f5b9d7"
LAUNCHER_SHA256 = base.LAUNCHER_SHA256
NORMALIZER_SHA256 = "1f4ec5a26605aa90380eb0532fec3915d2cc24a3a20473ed70d57198bd995db7"
G1_MASTER = base.G1_MASTER
G2_MASTER = base.G2_MASTER
PROBE_SCHEMA = "cpm-k-probe-record-v1"
SNAPSHOT_SCHEMA = "cpm-k-scene-snapshot-v1"
CPM_KIND = "cpm_compat_v1"
NORMALIZER_KIND = "normalizer_compat"
MB = 1000 * 1000
# Design section 5.4.
STOP_MIN_AVAIL_VIRTUAL = 600 * MB
STOP_MAX_PRIVATE = 3600 * MB
FAIL_PRIVATE_DELTA = 10 * MB
FAIL_COUNTER_STEP = 10
NORMALIZER_BUDGET = 4

# Reused unchanged (format-agnostic).
parse_log = base.parse_log
events_of = base.events_of
load_json = base.load_json
idle_check = base.idle_check
historical_check = base.historical_check
census_check = base.census_check
same_process_module = base.same_process_module
scope_generation = base.scope_generation
snapshot_diff = base.snapshot_diff
snapshot_value = base.snapshot_value
undo_state = base.undo_state
preset_value = base.preset_value
load_library_inventory = base.load_library_inventory
classify_library_diff = base.classify_library_diff
verify_sha256sums = base.verify_sha256sums

try:
    _TEXT = unicode  # noqa: F821
    _INTEGER = (int, long)  # noqa: F821  (Python 2: values above 2**31, e.g. private bytes, are long)
except NameError:
    _TEXT = str
    _INTEGER = (int,)


def _is_int(value):
    return isinstance(value, _INTEGER) and not isinstance(value, bool)


def load_probe_records(attempt_dir):
    """probe.jsonl with the K schema: append-only, seq 1..n contiguous."""
    raw = base._read_bytes(os.path.join(attempt_dir, "probe.jsonl"))
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
    raw = base._read_bytes(os.path.join(attempt_dir, *meta["file"].split("/")))
    if hashlib.sha256(raw).hexdigest() != meta["sha256"]:
        raise ValueError("scene snapshot %s does not match its probe-recorded SHA-256" % meta["file"])
    snap = base._json_bytes(raw)
    if snap.get("schema") != SNAPSHOT_SCHEMA or snap.get("seq") != record.get("seq"):
        raise ValueError("scene snapshot %s schema/seq mismatch" % meta["file"])
    return snap


def identity_check(record):
    """Exact K CPM build and launcher, private module, isolation."""
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


# ---------------------------------------------------------------------------
# Broker views per consumer (probe broker_detail)
# ---------------------------------------------------------------------------
def views_by_consumer(record):
    """{consumer_kind: {generation_sha: {"views": n, "live_leases": n, "stale": n}}}; None if unobserved."""
    detail = record.get("broker_detail") or {}
    views = detail.get("views")
    if not detail.get("broker_constructed") or not isinstance(views, list):
        return None
    out = {}
    for v in views:
        kind = out.setdefault(v.get("consumer_kind"), {})
        gen = kind.setdefault(v.get("master_sha256"), {"views": 0, "live_leases": 0, "stale": 0})
        gen["views"] += 1
        gen["live_leases"] += int(v.get("live_leases") or 0)
        gen["stale"] += 1 if v.get("stale") else 0
    return out


def k_idle_check(record):
    """Item-8 idle rules plus: no broker view holds a live lease."""
    base_result = idle_check(record)
    problems, unobserved = list(base_result["problems"]), list(base_result["unobserved"])
    per = views_by_consumer(record)
    if per is None:
        if (record.get("broker_detail") or {}).get("broker_constructed"):
            unobserved.append("broker views")
    else:
        for kind, gens in per.items():
            for gen, facts in gens.items():
                if facts["live_leases"]:
                    problems.append("%s view %s holds %d live lease(s)" % (kind, (gen or "")[:12], facts["live_leases"]))
    return {"idle": not problems and not unobserved, "problems": problems, "unobserved": unobserved}


def broker_id(record):
    return (record.get("broker_before") or {}).get("broker_id")


def consumer_boundary(before, after, consumer, generation):
    """Facts across one consumer action (two probe records): same broker, the
    consumer has a view for the generation afterwards, the other consumer's
    views did not disappear, idle afterwards."""
    other = NORMALIZER_KIND if consumer == CPM_KIND else CPM_KIND
    vb, va = views_by_consumer(before) or {}, views_by_consumer(after) or {}
    same_broker = broker_id(before) is not None and broker_id(before) == broker_id(after)
    if not (before.get("broker_before") or {}).get("broker_constructed"):
        same_broker = broker_id(after) is not None      # the action constructed the broker
    lost = sorted(g for g in (vb.get(other) or {}) if g not in (va.get(other) or {}))
    return {"same_broker": same_broker,
            "consumer_has_generation_view": generation in (va.get(consumer) or {}),
            "other_consumer_views_lost": lost,
            "idle_after": k_idle_check(after)["idle"],
            "ok": same_broker and generation in (va.get(consumer) or {}) and not lost and k_idle_check(after)["idle"]}


def diagnostics_events(record):
    tail = (record.get("broker_detail") or {}).get("diagnostics_tail")
    return [e.get("event") for e in tail] if isinstance(tail, list) else None


# ---------------------------------------------------------------------------
# Production Normalizer log (sfm_rebuild_control_groups.txt; rewritten per run)
# ---------------------------------------------------------------------------
_N_SCOPE = re.compile(r"^scope_mode=(?P<mode>\S+) scope_shots=(?P<count>\d+)\s*$")
_N_SHOT_NAMES = re.compile(r"^CONTEXTUALIZER_SCOPE_SHOT_NAMES = \[(?P<names>.*)\]\s*$")
_N_MASTER_SHA = re.compile(r"^live Master SHA256=(?P<sha>[0-9a-fA-F]{64})\s*$")
_N_RESULT = re.compile(r"^(?P<key>[A-Z][A-Z0-9_]+) = (?P<value>PASS|FAIL)\b")
_N_MEM = re.compile(r"\bmem_ok=(?P<ok>True|False)\b")
_N_TERMINAL = re.compile(r"^PRODUCTION_TERMINAL_RESULTS=(?P<rows>.*)$")
_N_REVISION = re.compile(r"^PRODUCTION_REVISION = (?P<rev>\S+)\s*$")


def parse_normalizer_log(text):
    out = {"scope_mode": None, "scope_shots": None, "shot_names": None, "live_master_sha256": [], "results": {},
           "mem_ok_true": 0, "mem_ok_false": 0, "terminal_results": None, "revision": None, "cpm_lines": 0}
    for line in text.splitlines():
        m = _N_SCOPE.match(line)
        if m and out["scope_mode"] is None:
            out["scope_mode"], out["scope_shots"] = m.group("mode"), int(m.group("count"))
        m = _N_SHOT_NAMES.match(line)
        if m:
            out["shot_names"] = re.findall(r"u?'([^']*)'", m.group("names"))
        m = _N_MASTER_SHA.match(line)
        if m:
            out["live_master_sha256"].append(m.group("sha").lower())
        m = _N_RESULT.match(line)
        if m:
            out["results"].setdefault(m.group("key"), []).append(m.group("value"))
        for m in _N_MEM.finditer(line):
            out["mem_ok_true" if m.group("ok") == "True" else "mem_ok_false"] += 1
        m = _N_TERMINAL.match(line)
        if m:
            out["terminal_results"] = re.findall(r"u?'([^']*)'\), '([A-Z_]+)'", m.group("rows"))
        m = _N_REVISION.match(line)
        if m:
            out["revision"] = m.group("rev")
        if re.search(r"\bPROD_[A-Z_]+[ =]", line) and not line.startswith("PRODUCTION"):
            out["cpm_lines"] += 1
    return out


def normalizer_run_check(parsed, shots, generation):
    """One Selected-Shot(s) run: exact scope, PASS/PASS, pinned generation, memory, no CPM lines."""
    res = parsed["results"]
    checks = {
        "selected_scope": parsed["scope_mode"] == "SELECTED_SHOTS" and parsed["scope_shots"] == len(shots),
        "shot_names": parsed["shot_names"] == list(shots),
        "rebuild_pass": res.get("PRODUCTION_REBUILD_CONTROL_GROUPS") == ["PASS"],
        "contextualizer_pass": res.get("PRODUCTION_CONTEXTUALIZER") == ["PASS"],
        "generation_pinned": bool(parsed["live_master_sha256"]) and set(parsed["live_master_sha256"]) == set([generation]),
        "mem_ok_all_true": parsed["mem_ok_true"] > 0 and parsed["mem_ok_false"] == 0,
        "no_fail_results": not [k for k, v in res.items() if "FAIL" in v],
        "no_cpm_lines": parsed["cpm_lines"] == 0,
    }
    return {"ok": all(checks.values()), "checks": checks}


# ---------------------------------------------------------------------------
# Resources (design section 5.4)
# ---------------------------------------------------------------------------
def resource_stop(record, normalizer_parsed=None):
    """STOP before the next Normalizer command when any threshold is crossed."""
    res = record.get("resources") or {}
    reasons, unobserved = [], []
    if not res.get("observed"):
        unobserved.append("resources")
    else:
        avail, private = res.get("avail_virtual"), res.get("private_usage")
        if not _is_int(avail):
            unobserved.append("avail_virtual")
        elif avail < STOP_MIN_AVAIL_VIRTUAL:
            reasons.append("free VAS %d MB < 600 MB" % (avail // MB))
        if not _is_int(private):
            unobserved.append("private_usage")
        elif private > STOP_MAX_PRIVATE:
            reasons.append("private bytes %d MB > 3600 MB" % (private // MB))
    if normalizer_parsed is not None and normalizer_parsed.get("mem_ok_false"):
        reasons.append("Normalizer mem_ok=False x%d" % normalizer_parsed["mem_ok_false"])
    return {"stop": bool(reasons) or bool(unobserved), "reasons": reasons, "unobserved": unobserved}


def cpm_accumulation(closed_records):
    """Equivalent closed-CPM states with no Normalizer command between them, in
    order. FAIL if private bytes grow > 10 MB between any pair, or if handles,
    GDI or USER grow by > 10 in the same direction on two consecutive steps."""
    keys = ("handles", "gdi_objects", "user_objects")
    steps, problems = [], []
    for a, b in zip(closed_records, closed_records[1:]):
        ra, rb = a.get("resources") or {}, b.get("resources") or {}
        step = {"from": a.get("seq"), "to": b.get("seq")}
        for k in ("private_usage",) + keys:
            if _is_int(ra.get(k)) and _is_int(rb.get(k)):
                step[k] = rb[k] - ra[k]
            else:
                step[k] = None
                problems.append("%s unobserved between %s and %s" % (k, a.get("seq"), b.get("seq")))
        if _is_int(step["private_usage"]) and step["private_usage"] > FAIL_PRIVATE_DELTA:
            problems.append("private +%d bytes between %s and %s" % (step["private_usage"], a.get("seq"), b.get("seq")))
        steps.append(step)
    for k in keys:
        for s1, s2 in zip(steps, steps[1:]):
            if _is_int(s1[k]) and _is_int(s2[k]) and s1[k] > FAIL_COUNTER_STEP and s2[k] > FAIL_COUNTER_STEP:
                problems.append("%s grew > %d twice (%s->%s, %s->%s)" % (k, FAIL_COUNTER_STEP, s1["from"], s1["to"],
                                                                        s2["from"], s2["to"]))
    return {"ok": not problems, "steps": steps, "problems": problems}


def summary(attempt_dir, log_text=None, normalizer_texts=None):
    records = load_probe_records(attempt_dir)
    rows = []
    for rec in records:
        res = rec.get("resources") or {}
        rows.append({"seq": rec["seq"], "wall_time": rec.get("wall_time"), "pid": rec.get("pid"),
                     "identity": identity_check(rec)["ok"], "idle": k_idle_check(rec),
                     "historical": historical_check(rec)["inactive"], "broker_id": broker_id(rec),
                     "views": views_by_consumer(rec), "scope_generation": scope_generation(rec),
                     "normalizer_names_in_main": (rec.get("host") or {}).get("normalizer_names_in_main"),
                     "private_mb": (res.get("private_usage") or 0) // MB if _is_int(res.get("private_usage")) else None,
                     "avail_virtual_mb": res.get("avail_virtual") // MB if _is_int(res.get("avail_virtual")) else None,
                     "errors": sorted(rec.get("errors") or {})})
    out = {"attempt": os.path.basename(os.path.normpath(attempt_dir)), "probes": rows,
           "pids": sorted(set(r.get("pid") for r in records)),
           "brokers": sorted(set(b for b in (broker_id(r) for r in records) if b))}
    if log_text is not None:
        parsed = parse_log(log_text)
        counts = {}
        for e in parsed["events"]:
            counts[e["tag"]] = counts.get(e["tag"], 0) + 1
        out["log_event_counts"] = counts
        out["log_historical_or_removed"] = parsed["historical_or_removed"]
    if normalizer_texts:
        out["normalizer_runs"] = [parse_normalizer_log(t) for t in normalizer_texts]
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, args = argv[1], argv[2:]

    def read(path):
        return io.open(path, encoding="utf-8", errors="replace").read()
    if cmd == "summary":
        log = read(args[args.index("--log") + 1]) if "--log" in args else None
        nlogs = [read(args[i + 1]) for i, a in enumerate(args) if a == "--normalizer-log"]
        result = summary(args[0], log, nlogs)
    elif cmd == "normalizer":
        result = parse_normalizer_log(read(args[0]))
    elif cmd == "views":
        records = dict((r["seq"], r) for r in load_probe_records(args[0]))
        result = views_by_consumer(records[int(args[1])])
    elif cmd == "resources":
        records = dict((r["seq"], r) for r in load_probe_records(args[0]))
        chosen = [records[int(s)] for s in args[1:]]
        result = {"stop": [resource_stop(r) for r in chosen], "accumulation": cpm_accumulation(chosen)}
    elif cmd == "verify-sums":
        result = verify_sha256sums(args[0])
    else:
        print(__doc__)
        return 2
    print(json.dumps(result, indent=1, sort_keys=True, default=_TEXT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
