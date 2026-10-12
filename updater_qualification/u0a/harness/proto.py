# -*- coding: utf-8 -*-
"""U0A experimental activation/recovery prototype (Astra Updater Blueprint R2, C2-C12).

DISPOSABLE EXPERIMENT ONLY. This is not the production updater, has no GUI,
no network/release client and no signing. It operates only on a synthetic
installation tree (a fake `usermod\\cfg`) created under the U0A test root.

Usage (one process per operation, so the controller can kill it at a barrier):
  proto.py activate <cfg> <result.json> --kind rebuild|replace [--source FILE]
           --confirm-sha SHA [--stop-at B1,B2] [--inject KEY=VALUE]
  proto.py recover  <cfg> <result.json> [--policy resume|rollback] [--stop-at ...]

At a stop barrier the process prints `BARRIER <name>` and blocks reading one
line from stdin (`go`). The controller may instead terminate it there.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid

import w32

SCHEMA = "u0a-tx-1"
MASTER_NAME = "sfm_defaultanimationgroups.txt"
SIDECAR_RE = re.compile(r"^sfm_master_v1_[0-9a-f]{64}\.sfmsidecar$")
TXID_RE = re.compile(r"^[0-9a-f]{32}$")
FIXED_NAMES = {"manifest.json", "master.txt"}
TERMINAL = {"COMPLETE", "ROLLED_BACK", "ABANDONED"}

MESSAGES = {
    "NOTHING": "Nothing was installed.",
    "INSTALLED": "Installation complete.",
    "RECOVERED": "Installation recovered.",
    "RESTORED": "Your previous files were restored.",
    "TXT_CHANGED": "Your TXT changed after the interruption. Choose which version to keep.",
    "MISSING": "Automatic recovery is unavailable; required files are missing.",
    "FOLDER_CHANGED": "The data folder changed. No files were overwritten.",
    "UNKNOWN_SCHEMA": "Use a compatible updater to recover this installation.",
    "NOOP": "Already installed; nothing changed.",
}


class Stop(Exception):
    def __init__(self, outcome, message_key, **details):
        Exception.__init__(self, outcome)
        self.outcome = outcome
        self.message_key = message_key
        self.details = details


# ---------------------------------------------------------------- layout
def resolve_installation(cfg):
    """C1: aliases may reach the same physical installation; operate on the resolved target."""
    h, err = w32.open_dir(os.path.abspath(cfg), share=7)
    if h is None:
        raise Stop("REFUSED", "NOTHING", reason="installation directory unavailable", error=w32.ename(err))
    try:
        fp = w32.final_path(h)
    finally:
        w32.close(h)
    if fp.startswith("\\\\?\\UNC\\"):
        raise Stop("REFUSED", "NOTHING", reason="network installation path is outside the support boundary")
    return fp[4:] if fp.startswith("\\\\?\\") else fp


class Layout(object):
    """Every path is derived from fixed rules; nothing is taken from a journal."""

    def __init__(self, cfg):
        self.cfg = os.path.abspath(cfg)
        self.master = os.path.join(self.cfg, MASTER_NAME)
        self.auth = os.path.join(self.cfg, "sfm_shared_authority")
        self.upd = os.path.join(self.cfg, "sfm_character_tools_updater")
        self.lock = os.path.join(self.upd, "installation.lock")
        self.txroot = os.path.join(self.upd, "transactions")

    def reparse_in_slots(self):
        """C1: no symlink/reparse point inside the managed Master/authority/transaction slots."""
        bad = []
        paths = [self.master, self.auth, self.upd, self.txroot]
        for root in (self.auth, self.txroot):
            if os.path.isdir(root):
                for dp, dn, fn in os.walk(root):
                    paths += [os.path.join(dp, n) for n in dn + fn]
        for p in paths:
            a = w32.attrs(p)
            if a != w32.INVALID_FILE_ATTRIBUTES and a & w32.FILE_ATTRIBUTE_REPARSE_POINT:
                bad.append(os.path.relpath(p, self.cfg))
        return bad

    def txdir(self, txid):
        if not TXID_RE.match(txid):
            raise Stop("CONFLICT", "FOLDER_CHANGED", reason="invalid transaction id", txid=txid)
        return os.path.join(self.txroot, txid)

    def slot(self, txid, kind, name):
        if kind == "master":
            return self.master
        if name not in FIXED_NAMES and not SIDECAR_RE.match(name):
            raise Stop("CONFLICT", "FOLDER_CHANGED", reason="invalid slot name", name=name)
        if kind == "auth":
            if name == "master.txt":
                raise Stop("CONFLICT", "FOLDER_CHANGED", reason="invalid auth slot", name=name)
            return os.path.join(self.auth, name)
        if kind in ("candidate", "snapshot", "retired"):
            return os.path.join(self.txdir(txid), kind, name)
        raise Stop("CONFLICT", "FOLDER_CHANGED", reason="invalid slot kind", kind=kind)


# ---------------------------------------------------------------- barriers
STOPS = set()
PASSED = []


def barrier(name):
    PASSED.append(name)
    if name in STOPS:
        sys.stdout.write("BARRIER %s\n" % name)
        sys.stdout.flush()
        line = sys.stdin.readline().strip()
        PASSED.append("resumed:%s:%s" % (name, line))


# ---------------------------------------------------------------- synthetic compiler
def sha(data):
    return hashlib.sha256(data).hexdigest()


def compile_synthetic(txt):
    src = sha(txt)
    body = ("SFMSIDECAR-SYNTHETIC-U0A\nformat=v1\nsource_sha256=%s\n" % src).encode("ascii")
    body += hashlib.sha512(txt).digest() * 64
    name = "sfm_master_v1_%s.sfmsidecar" % sha(body)
    manifest = json.dumps({"schema": 1, "format": "v1", "source_sha256": src,
                           "artifact": name, "artifact_sha256": sha(body)},
                          sort_keys=True, indent=2).encode("ascii") + b"\n"
    return name, body, manifest


def validate_candidate(txt, name, body, manifest):
    src = sha(txt)
    m = json.loads(manifest.decode("ascii"))
    ok = (SIDECAR_RE.match(name) and m["artifact"] == name and m["artifact_sha256"] == sha(body)
          and m["source_sha256"] == src and name == "sfm_master_v1_%s.sfmsidecar" % sha(body)
          and ("source_sha256=%s\n" % src).encode("ascii") in body)
    if not ok:
        raise Stop("REFUSED", "NOTHING", reason="candidate failed validation")


# ---------------------------------------------------------------- journal
def _line(seq, rec):
    body = json.dumps({"seq": seq, "rec": rec}, sort_keys=True, separators=(",", ":"))
    return ("%s\t%s\n" % (body, sha(body.encode("utf-8")))).encode("utf-8")


def parse_journal(data):
    """Returns (records, torn_tail_bytes or None). Raises Stop on malformed content."""
    recs = []
    lines = data.split(b"\n")
    tail = lines.pop()  # bytes after the final newline
    pending_torn = None
    for raw in lines:
        try:
            text = raw.decode("utf-8")
            body, digest = text.rsplit("\t", 1)
            if sha(body.encode("utf-8")) != digest:
                raise ValueError("checksum")
            obj = json.loads(body)
            seq, rec = obj["seq"], obj["rec"]
        except Exception:
            if pending_torn is None:
                pending_torn = sha(raw)
                continue
            raise Stop("CONFLICT", "UNKNOWN_SCHEMA", reason="malformed journal record")
        if pending_torn is not None:
            if rec.get("t") != "TORN_TAIL" or rec.get("sha") != pending_torn:
                raise Stop("CONFLICT", "UNKNOWN_SCHEMA", reason="malformed journal record")
            pending_torn = None
        if seq != len(recs):
            raise Stop("CONFLICT", "UNKNOWN_SCHEMA", reason="journal sequence gap")
        recs.append(rec)
    if pending_torn is not None:
        raise Stop("CONFLICT", "UNKNOWN_SCHEMA", reason="malformed journal record")
    if recs and (recs[0].get("t") != "INTENT" or recs[0].get("schema") != SCHEMA):
        raise Stop("CONFLICT", "UNKNOWN_SCHEMA", reason="unknown journal schema")
    return recs, (tail if tail else None)


class Journal(object):
    """Held open for the transaction's lifetime: write access, READ sharing only.
    A second process therefore cannot write it while the owner lives."""

    def __init__(self, path, create):
        disp = w32.CREATE_NEW if create else w32.OPEN_EXISTING
        self.h, err = w32.create_file(path, w32.GENERIC_READ | w32.GENERIC_WRITE,
                                      w32.FILE_SHARE_READ, disp)
        if self.h is None:
            raise Stop("REFUSED", "NOTHING", reason="journal unavailable", error=w32.ename(err),
                       journal_busy=(err == 32))
        data, _ = w32.read_all_handle(self.h)
        self.records, torn = parse_journal(data or b"")
        if torn is not None:
            # Preserve the torn bytes as their own line, then acknowledge them.
            w32.seek_end(self.h)
            self._write(b"\n")
            self.seq = len(self.records)
            self.append({"t": "TORN_TAIL", "sha": sha(torn)})
        self.seq = len(self.records)

    def _write(self, data):
        w32.seek_end(self.h)
        ok, err = w32.write_all(self.h, data)
        if ok:
            ok, err = w32.flush(self.h)
        if not ok:
            raise Stop("CONFLICT", "FOLDER_CHANGED", reason="journal write failed",
                       error=w32.ename(err))

    def append(self, rec):
        rec = json.loads(json.dumps(rec))
        if rec.get("t") == "CONFLICT" and self.records and self.records[-1] == rec:
            return  # the same unresolved conflict re-observed: keep recovery idempotent
        self._write(_line(self.seq, rec))
        self.records.append(rec)
        self.seq += 1

    def close(self):
        if self.h is not None:
            w32.close(self.h)
            self.h = None


# ---------------------------------------------------------------- observation
def observe_path(path):
    """Path-based reader with full sharing (never conflicts with nothing but an exclusive owner)."""
    a = w32.attrs(path)
    if a == w32.INVALID_FILE_ATTRIBUTES:
        return None
    if a & w32.FILE_ATTRIBUTE_REPARSE_POINT:
        return {"reparse": True}
    ident = w32.path_identity(path)
    if ident is None:
        return {"unreadable": True}
    return {"sha256": ident["sha256"], "file_id": ident["file_id"], "links": ident["info"]["links"]}


def auth_inventory(layout):
    return sorted(os.listdir(layout.auth))


def acquire_lock(layout):
    """C4: CreateFileW(GENERIC_READ|GENERIC_WRITE, share 0, OPEN_ALWAYS), non-inheritable."""
    h, err = w32.create_file(layout.lock, w32.GENERIC_READ | w32.GENERIC_WRITE, 0,
                             w32.OPEN_ALWAYS, inherit=False)
    if h is None:
        raise Stop("REFUSED", "NOTHING", reason="installation lock not acquired",
                   error=w32.ename(err))
    return h


def sfm_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq sfm.exe", "/NH"],
                             capture_output=True, text=True, timeout=30).stdout
    except Exception as e:  # advisory only
        return "unknown: %s" % e
    return "sfm.exe" in out.lower()


# ---------------------------------------------------------------- plan
def make_plan(intent):
    """Deterministic move list derived from the intent's hashes and validated names."""
    old, new, kind = intent["old"], intent["new"], intent["kind"]
    moves = []
    for s in old["sidecars"]:
        moves.append({"role": "S0", "src": ("auth", s["name"]), "dst": ("retired", s["name"]),
                      "sha256": s["sha256"]})
    if old["manifest"] is not None:
        moves.append({"role": "P0", "src": ("auth", "manifest.json"),
                      "dst": ("retired", "manifest.json"), "sha256": old["manifest"]["sha256"]})
    if kind == "replace":
        moves.append({"role": "M0", "src": ("master", ""), "dst": ("retired", "master.txt"),
                      "sha256": old["master"]["sha256"]})
        moves.append({"role": "M1", "src": ("candidate", "master.txt"), "dst": ("master", ""),
                      "sha256": new["master_sha256"]})
    moves.append({"role": "S1", "src": ("candidate", new["sidecar"]),
                  "dst": ("auth", new["sidecar"]), "sha256": new["sidecar_sha256"]})
    moves.append({"role": "P1", "src": ("candidate", "manifest.json"),
                  "dst": ("auth", "manifest.json"), "sha256": new["manifest_sha256"]})
    for i, m in enumerate(moves):
        m["i"] = i
    return moves


def expected_states(intent, moves):
    """E_k for k = 0..n: slot -> sha (None = vacant) after the first k moves."""
    state = {}
    for m in moves:
        state.setdefault(tuple(m["src"]), None)
        state.setdefault(tuple(m["dst"]), None)
    # Build E_0: a slot's initial content is the sha of the first move that reads from it,
    # unless an earlier move writes it first.
    e0 = dict(state)
    touched = set()
    for m in moves:
        s, d = tuple(m["src"]), tuple(m["dst"])
        if s not in touched:
            e0[s] = m["sha256"]
        touched.add(s)
        touched.add(d)
    if intent["kind"] == "rebuild":
        e0[("master", "")] = intent["old"]["master"]["sha256"]
    states = [dict(e0)]
    cur = dict(e0)
    for m in moves:
        cur = dict(cur)
        cur[tuple(m["src"])] = None
        cur[tuple(m["dst"])] = m["sha256"]
        states.append(cur)
    return states


def observe_slots(layout, txid, slots):
    obs = {}
    for s in slots:
        o = observe_path(layout.slot(txid, s[0], s[1]))
        obs[s] = o
    return obs


def match_state(obs, states):
    """Returns list of k whose expected state matches observation exactly (by sha256)."""
    hits = []
    for k, st in enumerate(states):
        good = True
        for slot, want in st.items():
            o = obs.get(slot)
            have = None if o is None else o.get("sha256", "!unusable")
            if have != want:
                good = False
                break
        if good:
            hits.append(k)
    return hits


def describe_divergence(obs, states):
    """Mismatching slots against the nearest expected state (fewest mismatches)."""
    best = None
    for k, st in enumerate(states):
        mm = []
        for slot, want in st.items():
            o = obs.get(slot)
            have = None if o is None else o.get("sha256", "!unusable")
            if have != want:
                mm.append({"slot": "/".join(slot), "observed": have, "expected": want, "nearest_k": k})
        if best is None or len(mm) < len(best):
            best = mm
    return best


def allowed_auth_names(intent):
    names = {s["name"] for s in intent["old"]["sidecars"]}
    names.add(intent["new"]["sidecar"])
    names.add("manifest.json")
    return names


# ---------------------------------------------------------------- move executor
def norm_final(p):
    if p is None:
        return None
    if p.startswith("\\\\?\\"):
        p = p[4:]
    return os.path.normcase(os.path.abspath(p))


def execute(layout, txid, moves, handles, journal, direction, start_k, prefix):
    """Forward: performs moves start_k..n-1. Rollback: undoes moves start_k-1..0.
    Every move: journal BEGIN -> no-clobber handle rename -> journal DONE.
    Returns (k_reached, failure or None)."""
    order = range(start_k, len(moves)) if direction == "forward" else range(start_k - 1, -1, -1)
    k = start_k
    for i in order:
        m = moves[i]
        src, dst = (m["src"], m["dst"]) if direction == "forward" else (m["dst"], m["src"])
        dest = layout.slot(txid, dst[0], dst[1])
        journal.append({"t": "BEGIN", "dir": direction, "i": i, "role": m["role"]})
        barrier("%s_begin_%s_%d" % (prefix, direction, i))
        ok, err = w32.rename_by_handle(handles[i], dest, replace_if_exists=False)
        barrier("%s_moved_%s_%d" % (prefix, direction, i))
        if not ok:
            journal.append({"t": "FAILED", "dir": direction, "i": i, "error": w32.ename(err)})
            return k, {"i": i, "role": m["role"], "dest": dest, "error": w32.ename(err)}
        if norm_final(w32.final_path(handles[i])) != norm_final(dest):
            journal.append({"t": "FAILED", "dir": direction, "i": i, "error": "final path mismatch"})
            return k, {"i": i, "role": m["role"], "error": "final path mismatch"}
        journal.append({"t": "DONE", "dir": direction, "i": i, "role": m["role"]})
        barrier("%s_done_%s_%d" % (prefix, direction, i))
        k = i + 1 if direction == "forward" else i
    return k, None


def verify_final(layout, txid, intent, moves, states, k, handles, master_handle):
    """Through held handles (bytes + location) and an independent directory listing."""
    problems = []
    for m in moves:
        h = handles.get(m["i"])
        s, _ = w32.sha_handle(h)
        if s != m["sha256"]:
            problems.append({"role": m["role"], "problem": "hash via handle", "sha": s})
        loc = m["dst"] if k == len(moves) else m["src"]
        want = layout.slot(txid, loc[0], loc[1])
        if norm_final(w32.final_path(h)) != norm_final(want):
            problems.append({"role": m["role"], "problem": "location", "have": w32.final_path(h)})
    if master_handle is not None:
        s, _ = w32.sha_handle(master_handle)
        if s != intent["old"]["master"]["sha256"]:
            problems.append({"role": "M(retained)", "problem": "hash via handle", "sha": s})
    names = auth_inventory(layout)
    st = states[k]
    want_names = sorted(n for (kind, n), v in st.items() if kind == "auth" and v is not None)
    if names != want_names:
        problems.append({"problem": "authority inventory", "have": names, "want": want_names})
    return problems


# ---------------------------------------------------------------- activation
def activate(layout, kind, source, confirm_sha, inject):
    res = {"operation": "activate", "kind": kind}
    lock = None
    held = []
    journal = None
    txid = None
    try:
        # C7.1-2: compile and validate the candidate (path-based readers; before protection)
        try:
            if kind == "rebuild":
                txt = open(layout.master, "rb").read()
            else:
                txt = open(source, "rb").read()  # captured immutable copy of the import
        except OSError as e:
            raise Stop("REFUSED", "MISSING", reason="source unreadable",
                       error="%s winerror=%s" % (type(e).__name__, getattr(e, "winerror", None)))
        name, body, manifest = compile_synthetic(txt)
        validate_candidate(txt, name, body, manifest)
        res["candidate"] = {"master_sha256": sha(txt), "sidecar": name,
                            "sidecar_sha256": sha(body), "manifest_sha256": sha(manifest)}
        # Preview of the active state (path readers)
        m0 = observe_path(layout.master)
        if m0 is None or "sha256" not in m0:
            raise Stop("REFUSED", "MISSING", reason="active master missing or unusable", observed=m0)
        if m0["links"] != 1:
            raise Stop("REFUSED", "FOLDER_CHANGED", reason="master has hard links", links=m0["links"])
        inv = auth_inventory(layout)
        sidecars, manifest_old, unknown = [], None, []
        for n in inv:
            p = os.path.join(layout.auth, n)
            o = observe_path(p)
            if SIDECAR_RE.match(n) and o and "sha256" in o and o["links"] == 1:
                sidecars.append({"name": n, "sha256": o["sha256"], "file_id": o["file_id"]})
            elif n == "manifest.json" and o and "sha256" in o and o["links"] == 1:
                manifest_old = {"sha256": o["sha256"], "file_id": o["file_id"]}
            else:
                unknown.append(n)
        if unknown:
            raise Stop("REFUSED", "FOLDER_CHANGED", reason="unfamiliar authority content",
                       unfamiliar=unknown)
        dir_ids = {"cfg": w32.path_identity(layout.cfg, True)["file_id"],
                   "auth": w32.path_identity(layout.auth, True)["file_id"]}
        res["preview"] = {"master": m0, "sidecars": sidecars, "manifest": manifest_old,
                          "inventory": inv, "dirs": dir_ids}
        if kind == "rebuild" and confirm_sha != sha(txt):
            raise Stop("REFUSED", "NOTHING", reason="rebuild source changed since confirmation")
        if confirm_sha != m0["sha256"]:
            raise Stop("REFUSED", "NOTHING", reason="destination generation changed; re-present decision",
                       observed=m0["sha256"], confirmed=confirm_sha)
        noop = (sha(txt) == m0["sha256"] and len(sidecars) == 1 and sidecars[0]["name"] == name
                and manifest_old is not None and manifest_old["sha256"] == sha(manifest))
        barrier("previewed")
        if noop:
            lock = acquire_lock(layout)
            for p, want in ((layout.master, m0["sha256"]),
                            (os.path.join(layout.auth, name), sha(body)),
                            (os.path.join(layout.auth, "manifest.json"), sha(manifest))):
                h, err = w32.create_file(p, w32.GENERIC_READ, 0, w32.OPEN_EXISTING)
                if h is None:
                    raise Stop("REFUSED", "NOTHING", reason="no-op verification open failed",
                               path=p, error=w32.ename(err))
                held.append(h)
                s, _ = w32.sha_handle(h)
                if s != want:
                    raise Stop("REFUSED", "NOTHING", reason="no-op verification hash mismatch")
            if auth_inventory(layout) != sorted([name, "manifest.json"]):
                raise Stop("REFUSED", "NOTHING", reason="no-op inventory changed")
            res.update(outcome="NOOP", message=MESSAGES["NOOP"])
            return res

        # C7.3: transaction directory, intent, journal, candidates (outside the active directory)
        txid = uuid.uuid4().hex
        res["txid"] = txid
        td = layout.txdir(txid)
        for d in (td, os.path.join(td, "candidate"), os.path.join(td, "snapshot"),
                  os.path.join(td, "retired")):
            os.mkdir(d)
        intent = {"schema": SCHEMA, "txid": txid, "kind": kind,
                  "old": {"master": {"sha256": m0["sha256"], "file_id": m0["file_id"]},
                          "sidecars": sidecars, "manifest": manifest_old},
                  "new": {"master_sha256": sha(txt), "sidecar": name, "sidecar_sha256": sha(body),
                          "manifest_sha256": sha(manifest)},
                  "dirs": dir_ids}
        ok, err = w32.write_new_file(os.path.join(td, "intent.json"),
                                     json.dumps(intent, sort_keys=True, indent=1).encode("utf-8"))
        if not ok:
            raise Stop("ABANDONED", "NOTHING", reason="intent write failed", error=w32.ename(err))
        journal = Journal(os.path.join(td, "journal"), create=True)
        journal.append({"t": "INTENT", "schema": SCHEMA, "txid": txid})
        cands = [("master.txt", txt)] if kind == "replace" else []
        cands += [(name, body), ("manifest.json", manifest)]
        for n, data in cands:
            ok, err = w32.write_new_file(layout.slot(txid, "candidate", n), data,
                                         inject_error=inject.get("candidate_write_error"))
            if not ok:
                journal.append({"t": "ABANDONED", "reason": "candidate write failed",
                                "error": w32.ename(err)})
                raise Stop("ABANDONED", "NOTHING", reason="candidate write failed",
                           error=w32.ename(err))
        barrier("candidates_written")
        # C7.4: verified snapshot copies of the pre-operation files
        snaps = [("master.txt", layout.master, m0["sha256"])]
        snaps += [(s["name"], os.path.join(layout.auth, s["name"]), s["sha256"]) for s in sidecars]
        if manifest_old:
            snaps.append(("manifest.json", os.path.join(layout.auth, "manifest.json"),
                          manifest_old["sha256"]))
        for n, p, want in snaps:
            try:
                data = open(p, "rb").read()
            except OSError as e:
                journal.append({"t": "ABANDONED", "reason": "source unreadable during snapshot"})
                raise Stop("ABANDONED", "NOTHING", reason="source unreadable during snapshot",
                           error="%s winerror=%s" % (type(e).__name__, getattr(e, "winerror", None)))
            if sha(data) != want:
                journal.append({"t": "ABANDONED", "reason": "source changed during snapshot"})
                raise Stop("ABANDONED", "NOTHING", reason="source changed during snapshot", path=p)
            ok, err = w32.write_new_file(layout.slot(txid, "snapshot", n), data)
            if not ok:
                journal.append({"t": "ABANDONED", "reason": "snapshot write failed",
                                "error": w32.ename(err)})
                raise Stop("ABANDONED", "NOTHING", reason="snapshot write failed", error=w32.ename(err))
        barrier("snapshots_written")
        # C7.5 confirmation was supplied (confirm_sha) and bound to M0 above.
        # C7.6: installation lock; other transactions; advisory SFM check
        try:
            lock = acquire_lock(layout)
        except Stop as e:
            journal.append({"t": "ABANDONED", "reason": e.details.get("reason"),
                            "error": e.details.get("error")})
            raise Stop("ABANDONED", "NOTHING", **e.details)
        barrier("locked")
        for other in sorted(os.listdir(layout.txroot)):
            if other == txid:
                continue
            if not TXID_RE.match(other):
                journal.append({"t": "ABANDONED", "reason": "unfamiliar transaction entry"})
                raise Stop("ABANDONED", "FOLDER_CHANGED", reason="unfamiliar transaction entry",
                           entry=other)
            st = transaction_status(layout, other)
            if st not in TERMINAL:
                journal.append({"t": "ABANDONED", "reason": "other transaction needs reconciliation",
                                "other": other, "other_status": st})
                raise Stop("ABANDONED", "NOTHING", reason="another transaction must be reconciled first",
                           other=other, other_status=st)
        jdata, _ = w32.read_all_handle(journal.h)
        if parse_journal(jdata)[0][-1].get("t") != "INTENT":
            raise Stop("CONFLICT", "FOLDER_CHANGED", reason="own journal changed by another process")
        res["sfm_running_advisory"] = sfm_running()
        if res["sfm_running_advisory"] is True and inject.get("sfm_policy_record_only") != 1:
            journal.append({"t": "ABANDONED", "reason": "SFM running"})
            raise Stop("ABANDONED", "NOTHING", reason="SFM is running")
        # C7.7: protected handles
        moves = make_plan(intent)
        states = expected_states(intent, moves)
        handles = {}
        master_handle = None

        def protect(path, access):
            h, err = w32.create_file(path, access, 0, w32.OPEN_EXISTING)
            if h is None:
                journal.append({"t": "ABANDONED", "reason": "protection failed", "path_role": path_role(layout, path),
                                "error": w32.ename(err)})
                raise Stop("ABANDONED", "NOTHING", reason="protection failed", path=path,
                           error=w32.ename(err))
            held.append(h)
            return h

        if kind == "rebuild":
            master_handle = protect(layout.master, w32.GENERIC_READ)
        for m in moves:
            p = layout.slot(txid, m["src"][0], m["src"][1])
            handles[m["i"]] = protect(p, w32.GENERIC_READ | w32.DELETE)
        dir_pins = {}
        for key, p in (("cfg", layout.cfg), ("auth", layout.auth),
                       ("candidate", os.path.join(td, "candidate")),
                       ("retired", os.path.join(td, "retired"))):
            h, err = w32.open_dir(p)
            if h is None:
                journal.append({"t": "ABANDONED", "reason": "directory pin failed", "error": w32.ename(err)})
                raise Stop("ABANDONED", "NOTHING", reason="directory pin failed", dir=key,
                           error=w32.ename(err))
            held.append(h)
            dir_pins[key] = w32.file_id(h)
        barrier("protected")
        # C7.8: revalidate bytes and physical identities through the held handles
        mism = []
        if master_handle is not None:
            s, _ = w32.sha_handle(master_handle)
            if s != m0["sha256"] or w32.file_id(master_handle) != m0["file_id"]:
                mism.append("master")
        for m in moves:
            h = handles[m["i"]]
            s, _ = w32.sha_handle(h)
            info = w32.std_info(h)
            if s != m["sha256"] or info["links"] != 1:
                mism.append(m["role"])
            if m["role"] == "M0" and w32.file_id(h) != m0["file_id"]:
                mism.append("M0 identity")
            if m["role"] == "S0":
                want = [x for x in sidecars if x["name"] == m["src"][1]][0]["file_id"]
                if w32.file_id(h) != want:
                    mism.append("S0 identity")
            if m["role"] == "P0" and w32.file_id(h) != manifest_old["file_id"]:
                mism.append("P0 identity")
        if dir_pins["cfg"] != dir_ids["cfg"] or dir_pins["auth"] != dir_ids["auth"]:
            mism.append("directory identity")
        # C7.9: recheck the active-directory inventory
        if auth_inventory(layout) != inv:
            mism.append("authority inventory")
        if mism:
            journal.append({"t": "ABANDONED", "reason": "revalidation failed", "mismatch": mism})
            raise Stop("ABANDONED", "NOTHING", reason="revalidation through handles failed",
                       mismatch=mism)
        journal.append({"t": "PROTECTED"})
        journal.append({"t": "DIR", "dir": "forward"})
        res["plan"] = [{"i": m["i"], "role": m["role"], "src": "/".join(m["src"]),
                        "dst": "/".join(m["dst"])} for m in moves]
        k, failure = execute(layout, txid, moves, handles, journal, "forward", 0, "act")
        if failure:
            res["forward_failure"] = failure
            journal.append({"t": "DIR", "dir": "rollback", "reason": "forward move failed"})
            k, rfail = execute(layout, txid, moves, handles, journal, "rollback", k, "actrb")
            if rfail or k != 0:
                journal.append({"t": "CONFLICT", "reason": "rollback incomplete"})
                raise Stop("CONFLICT", "FOLDER_CHANGED", reason="rollback incomplete",
                           rollback_failure=rfail, k=k)
            problems = verify_final(layout, txid, intent, moves, states, 0, handles, master_handle)
            if problems:
                journal.append({"t": "CONFLICT", "reason": "post-rollback verification failed"})
                raise Stop("CONFLICT", "FOLDER_CHANGED", reason="post-rollback verification failed",
                           problems=problems)
            journal.append({"t": "ROLLED_BACK"})
            res.update(outcome="ROLLED_BACK", message=MESSAGES["NOTHING"])
            return res
        barrier("moves_done")
        problems = verify_final(layout, txid, intent, moves, states, len(moves), handles, master_handle)
        if problems:
            journal.append({"t": "CONFLICT", "reason": "final verification failed", "problems": problems})
            raise Stop("CONFLICT", "FOLDER_CHANGED", reason="final verification failed",
                       problems=problems)
        journal.append({"t": "VERIFIED"})
        journal.append({"t": "COMPLETE"})
        barrier("complete")
        res.update(outcome="COMPLETE", message=MESSAGES["INSTALLED"])
        return res
    except Stop as e:
        res.update(outcome=e.outcome, message=MESSAGES[e.message_key], details=e.details)
        return res
    finally:
        for h in held:
            w32.close(h)
        if journal is not None:
            journal.close()
        if lock is not None:
            w32.close(lock)
        barrier("released")


def path_role(layout, path):
    return os.path.relpath(path, layout.cfg)


def transaction_status(layout, txid):
    p = os.path.join(layout.txdir(txid), "journal")
    h, err = w32.create_file(p, w32.GENERIC_READ | w32.GENERIC_WRITE, w32.FILE_SHARE_READ,
                             w32.OPEN_EXISTING)
    if h is None:
        return "BUSY" if err == 32 else "UNREADABLE:%s" % w32.ename(err)
    try:
        data, _ = w32.read_all_handle(h)
    finally:
        w32.close(h)
    try:
        recs, torn = parse_journal(data or b"")
    except Stop:
        return "MALFORMED"
    if not recs:
        return "EMPTY"
    return recs[-1].get("t")


# ---------------------------------------------------------------- recovery
def recover(layout, policy):
    res = {"operation": "recover", "policy": policy, "transactions": []}
    lock = acquire_lock(layout)
    try:
        for txid in sorted(os.listdir(layout.txroot)):
            res["transactions"].append(recover_one(layout, txid, policy))
        outs = [t["outcome"] for t in res["transactions"]]
        res["outcome"] = "NOTHING_TO_RECOVER" if not outs else (
            "CONFLICT" if "CONFLICT" in outs else ("REFUSED" if "REFUSED" in outs else "OK"))
        return res
    finally:
        w32.close(lock)
        barrier("released")


def recover_one(layout, txid, policy):
    r = {"txid": txid}
    held = []
    journal = None
    try:
        td = layout.txdir(txid)
        try:
            intent = json.loads(open(os.path.join(td, "intent.json"), "rb").read().decode("utf-8"))
        except Exception as e:
            raise Stop("CONFLICT", "UNKNOWN_SCHEMA", reason="intent unreadable", error=str(e))
        if intent.get("schema") != SCHEMA or intent.get("txid") != txid:
            raise Stop("CONFLICT", "UNKNOWN_SCHEMA", reason="unknown transaction schema")
        jpath = os.path.join(td, "journal")
        if w32.attrs(jpath) == w32.INVALID_FILE_ATTRIBUTES:
            # Interrupted between intent and journal creation: nothing can have moved.
            moves = make_plan(intent)
            states = expected_states(intent, moves)
            obs = observe_slots(layout, txid, sorted(states[0].keys()))
            if match_state(obs, states) != [0]:
                raise Stop("CONFLICT", "FOLDER_CHANGED", reason="journal missing and state not original")
            journal = Journal(jpath, create=True)
            journal.append({"t": "INTENT", "schema": SCHEMA, "txid": txid, "by": "recovery"})
            journal.append({"t": "ABANDONED", "reason": "journal missing; original state verified"})
            r.update(outcome="ABANDONED", message=MESSAGES["NOTHING"])
            return r
        journal = Journal(jpath, create=False)
        recs = journal.records
        types = [x.get("t") for x in recs]
        moves = make_plan(intent)
        states = expected_states(intent, moves)
        slots = sorted(states[0].keys())
        obs = observe_slots(layout, txid, slots)
        hits = match_state(obs, states)
        r["observed_k"] = hits
        r["journal_tail"] = types[-4:]
        dirs = [x["dir"] for x in recs if x.get("t") == "DIR"]
        names = set(auth_inventory(layout))
        extra = sorted(names - allowed_auth_names(intent))
        last = types[-1] if types else None
        if last in TERMINAL:
            # Terminal: verify only, never mutate (journal text is not trusted alone).
            want_k = {"COMPLETE": len(moves), "ROLLED_BACK": 0}.get(last)
            if last == "ABANDONED" and "PROTECTED" not in types:
                want_k = 0
            r["terminal"] = last
            r["verified"] = (want_k is not None and want_k in hits and not extra)
            r.update(outcome="TERMINAL", message="Transaction already %s; verified=%s; no files changed."
                     % (last, r["verified"]))
            return r
        if extra:
            journal.append({"t": "CONFLICT", "reason": "unfamiliar authority content", "names": extra})
            raise Stop("CONFLICT", "FOLDER_CHANGED", reason="unfamiliar authority content", names=extra)
        if len(hits) != 1:
            div = describe_divergence(obs, states)
            key = "FOLDER_CHANGED"
            master_slot = [d for d in div if d["slot"] == "master/"]
            if master_slot and master_slot[0]["observed"] is not None:
                key = "TXT_CHANGED"
            elif any(d["observed"] is None for d in div):
                key = "MISSING"
            journal.append({"t": "CONFLICT", "reason": "disk state matches no recorded transition",
                            "divergence": div})
            raise Stop("CONFLICT", key, reason="disk state matches no recorded transition",
                       divergence=div)
        k = hits[0]
        # Journal/disk consistency: the disk may be at most one move ahead of the last DONE.
        done_fwd = [x["i"] for x in recs if x.get("t") == "DONE" and x.get("dir") == "forward"]
        done_rb = [x["i"] for x in recs if x.get("t") == "DONE" and x.get("dir") == "rollback"]
        protected = "PROTECTED" in types
        if not protected:
            if k != 0:
                journal.append({"t": "CONFLICT", "reason": "files moved without protection record"})
                raise Stop("CONFLICT", "FOLDER_CHANGED", reason="files moved without protection record")
            journal.append({"t": "ABANDONED", "reason": "recovered before protection"})
            r.update(outcome="ABANDONED", message=MESSAGES["NOTHING"])
            return r
        direction = dirs[-1] if dirs else "forward"
        # Replay the journal: DONE records give the last certain k; an unmatched BEGIN
        # means the disk may legitimately be one move further (rename done, DONE not written).
        jk, pending = 0, None
        for x in recs:
            if x.get("t") == "BEGIN":
                pending = (x["dir"], x["i"])
            elif x.get("t") == "DONE":
                jk = x["i"] + 1 if x["dir"] == "forward" else x["i"]
                pending = None
            elif x.get("t") == "RECONCILED":
                # an earlier recovery verified this exact disk state before acting
                jk = x["k"]
                pending = None
        allowed = {jk}
        if pending is not None:
            allowed.add(pending[1] + 1 if pending[0] == "forward" else pending[1])
        consistent = k in allowed
        r["journal_allowed_k"] = sorted(allowed)
        r["journal_k"] = jk
        if not consistent:
            journal.append({"t": "CONFLICT", "reason": "journal and disk disagree", "disk_k": k})
            raise Stop("CONFLICT", "FOLDER_CHANGED", reason="journal and disk disagree", disk_k=k,
                       journal_k=jk)
        if direction == "forward" and policy == "rollback":
            direction = "rollback"
        # Protect every file that will still move, plus the retained master (rebuild).
        master_handle = None
        if intent["kind"] == "rebuild":
            h, err = w32.create_file(layout.master, w32.GENERIC_READ, 0, w32.OPEN_EXISTING)
            if h is None:
                raise Stop("REFUSED", "NOTHING", reason="cannot protect master", error=w32.ename(err))
            held.append(h)
            master_handle = h
        handles = {}
        for m in moves:
            loc = m["dst"] if m["i"] < k else m["src"]
            p = layout.slot(txid, loc[0], loc[1])
            h, err = w32.create_file(p, w32.GENERIC_READ | w32.DELETE, 0, w32.OPEN_EXISTING)
            if h is None:
                raise Stop("REFUSED", "NOTHING", reason="cannot protect file", role=m["role"],
                           error=w32.ename(err))
            held.append(h)
            s, _ = w32.sha_handle(h)
            if s != m["sha256"] or w32.std_info(h)["links"] != 1:
                journal.append({"t": "CONFLICT", "reason": "file changed before protection", "role": m["role"]})
                raise Stop("CONFLICT", "FOLDER_CHANGED", reason="file changed before protection",
                           role=m["role"])
            handles[m["i"]] = h
        if master_handle is not None:
            s, _ = w32.sha_handle(master_handle)
            if s != intent["old"]["master"]["sha256"]:
                journal.append({"t": "CONFLICT", "reason": "master changed"})
                raise Stop("CONFLICT", "TXT_CHANGED", reason="master changed")
        if sorted(set(auth_inventory(layout)) - allowed_auth_names(intent)):
            journal.append({"t": "CONFLICT", "reason": "unfamiliar authority content"})
            raise Stop("CONFLICT", "FOLDER_CHANGED", reason="unfamiliar authority content")
        barrier("rec_protected")
        journal.append({"t": "RECONCILED", "k": k, "dir": direction})
        if not dirs or dirs[-1] != direction:
            journal.append({"t": "DIR", "dir": direction, "reason": "recovery policy=%s" % policy})
        kk, failure = execute(layout, txid, moves, handles, journal, direction, k, "rec")
        if failure:
            journal.append({"t": "CONFLICT", "reason": "recovery move failed", "failure": failure})
            raise Stop("CONFLICT", "FOLDER_CHANGED", reason="recovery move failed", failure=failure)
        final_k = len(moves) if direction == "forward" else 0
        problems = verify_final(layout, txid, intent, moves, states, final_k, handles, master_handle)
        if problems:
            journal.append({"t": "CONFLICT", "reason": "recovery verification failed", "problems": problems})
            raise Stop("CONFLICT", "FOLDER_CHANGED", reason="recovery verification failed",
                       problems=problems)
        if direction == "forward":
            journal.append({"t": "VERIFIED"})
            journal.append({"t": "COMPLETE", "by": "recovery"})
            r.update(outcome="COMPLETE", message=MESSAGES["RECOVERED"], from_k=k)
        else:
            journal.append({"t": "ROLLED_BACK", "by": "recovery"})
            r.update(outcome="ROLLED_BACK", message=MESSAGES["RESTORED"], from_k=k)
        return r
    except Stop as e:
        r.update(outcome=e.outcome, message=MESSAGES[e.message_key], details=e.details)
        return r
    finally:
        for h in held:
            w32.close(h)
        if journal is not None:
            journal.close()


# ---------------------------------------------------------------- CLI
def main(argv):
    op, cfg, out = argv[0], argv[1], argv[2]
    opts = {}
    rest = argv[3:]
    while rest:
        k = rest.pop(0)
        opts.setdefault(k, []).append(rest.pop(0))
    STOPS.update(x for v in opts.get("--stop-at", []) for x in v.split(",") if x)
    inject = {}
    for kv in opts.get("--inject", []):
        k, v = kv.split("=", 1)
        inject[k] = int(v)
    try:
        layout = Layout(resolve_installation(cfg))
        bad = layout.reparse_in_slots()
        if bad:
            raise Stop("REFUSED", "FOLDER_CHANGED", reason="reparse point inside managed slots",
                       paths=bad)
        if op == "activate":
            res = activate(layout, opts["--kind"][0], (opts.get("--source") or [None])[0],
                           opts["--confirm-sha"][0], inject)
        elif op == "recover":
            res = recover(layout, (opts.get("--policy") or ["resume"])[0])
        else:
            raise SystemExit("unknown op")
    except Stop as e:
        res = {"operation": op, "outcome": e.outcome, "message": MESSAGES[e.message_key],
               "details": e.details}
    except Exception:
        import traceback
        res = {"operation": op, "outcome": "ERROR", "message": "Unexpected error; state preserved, not reported as success.",
               "details": {"traceback": traceback.format_exc()}}
    res["barriers"] = PASSED
    res["trace"] = w32.TRACE
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    sys.stdout.write("RESULT %s\n" % res.get("outcome"))
    sys.stdout.flush()


if __name__ == "__main__":
    main(sys.argv[1:])
