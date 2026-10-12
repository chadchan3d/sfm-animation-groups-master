# -*- coding: utf-8 -*-
"""U0A controller: runs U0A-1..6 against disposable synthetic installations.

  python run_u0a.py <TEST_ROOT> <EVIDENCE_DIR>

TEST_ROOT must be a new or empty directory on a local fixed NTFS volume, outside
any SFM installation and outside the repository. Every case gets its own fake
`usermod\\cfg` tree under TEST_ROOT\\cases. Nothing else is written, except one
cross-volume rename attempt whose target must not come into existence (U0A-1g).
"""
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import proto  # noqa: E402
import w32  # noqa: E402

PY = sys.executable
ROOT = os.path.abspath(sys.argv[1])
EVID = os.path.abspath(sys.argv[2])
CASES = os.path.join(ROOT, "cases")
RESULTS = []
USER = os.environ.get("USERNAME", "")

# Read-only fingerprints of production locations that U0A must not touch. Supplied at run time
# (U0A_PROD_WATCH = ';'-separated files/directories) so no workstation path is stored here.
PROD_FILES = [x for x in os.environ.get("U0A_PROD_WATCH", "").split(";") if x]


def fingerprint():
    out = {}
    for p in PROD_FILES:
        if os.path.isdir(p):
            for n in sorted(os.listdir(p)):
                q = os.path.join(p, n)
                if os.path.isfile(q):
                    out[q] = hashlib.sha256(open(q, "rb").read()).hexdigest()
        elif os.path.isfile(p):
            out[p] = hashlib.sha256(open(p, "rb").read()).hexdigest()
        else:
            out[p] = None
    return out


# ---------------------------------------------------------------- isolation
def isolation_check():
    rp = os.path.realpath(ROOT)
    low = rp.lower()
    repo = os.path.realpath(os.path.join(HERE, "..", "..", "..")).lower()
    drive = os.path.splitdrive(rp)[0] + "\\"
    fs = ctypes.create_unicode_buffer(64)
    ctypes.windll.kernel32.GetVolumeInformationW(drive, None, 0, None, None, None, fs, 64)
    dtype = ctypes.windll.kernel32.GetDriveTypeW(drive)
    reparse = []
    cur = rp
    while True:
        a = w32.attrs(cur)
        if a != w32.INVALID_FILE_ATTRIBUTES and a & w32.FILE_ATTRIBUTE_REPARSE_POINT:
            reparse.append(cur)
        nxt = os.path.dirname(cur)
        if nxt == cur:
            break
        cur = nxt
    sfm_running = proto.sfm_running()
    chk = {
        "test_root_realpath_equals_given": os.path.normcase(rp) == os.path.normcase(ROOT),
        "filesystem": fs.value, "drive_type_fixed": dtype == 3,
        "outside_repository": not low.startswith(repo),
        "outside_sfm": "steamlibrary" not in low and "sourcefilmmaker" not in low,
        "no_reparse_points_on_path": not reparse,
        "root_empty_or_new": (not os.path.exists(ROOT)) or os.listdir(ROOT) == [],
        "sfm_running": sfm_running,
    }
    chk["PASS"] = (chk["test_root_realpath_equals_given"] and fs.value == "NTFS" and chk["drive_type_fixed"]
                   and chk["outside_repository"] and chk["outside_sfm"] and chk["no_reparse_points_on_path"]
                   and chk["root_empty_or_new"])
    return chk


# ---------------------------------------------------------------- fixtures
TXT_A = b'"groupFile"\r\n{\r\n\t"RigBody"\r\n\t{\r\n\t\t"control"\t\t"spine_1"\r\n\t}\r\n}\r\n'
TXT_B = TXT_A.replace(b"spine_1", b"spine_1\"\r\n\t\t\"control\"\t\t\"spine_2")
TXT_C = TXT_A.replace(b"spine_1", b"neck_1")
TXT_OLD = TXT_A.replace(b"spine_1", b"hips")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def make_case(name, master=TXT_B, compiled_from=TXT_A, with_manifest=True, extra_sidecars=(),
              extra_auth=()):
    """Installed state: Master + one active sidecar (compiled from `compiled_from`) + manifest."""
    cfg = os.path.join(CASES, name, "usermod", "cfg")
    os.makedirs(os.path.join(cfg, "sfm_shared_authority"))
    os.makedirs(os.path.join(cfg, "sfm_character_tools_updater", "transactions"))
    open(os.path.join(cfg, proto.MASTER_NAME), "wb").write(master)
    open(os.path.join(cfg, "unrelated_other.cfg"), "wb").write(b"// unrelated cfg file\n")
    n, body, man = proto.compile_synthetic(compiled_from)
    open(os.path.join(cfg, "sfm_shared_authority", n), "wb").write(body)
    for src in extra_sidecars:
        n2, b2, _ = proto.compile_synthetic(src)
        open(os.path.join(cfg, "sfm_shared_authority", n2), "wb").write(b2)
    if with_manifest:
        open(os.path.join(cfg, "sfm_shared_authority", "manifest.json"), "wb").write(man)
    for e in extra_auth:
        open(os.path.join(cfg, "sfm_shared_authority", e), "wb").write(b"publisher lock leftover\n")
    return cfg


def inventory(cfg):
    out = {}
    for dp, dn, fn in os.walk(cfg):
        for f in fn:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, cfg).replace("\\", "/")
            try:
                ident = w32.path_identity(p)
                out[rel] = {"sha256": ident["sha256"] if ident else None,
                            "file_id": ident["file_id"] if ident else None}
            except Exception as e:
                out[rel] = {"error": str(e)}
    return out


def data_view(inv):
    """Inventory without the lock file and journals (expected bookkeeping writes)."""
    return {k: v for k, v in inv.items()
            if k != "sfm_character_tools_updater/installation.lock" and not k.endswith("/journal")}


def shas(inv):
    """Content set used for loss checks (journal and lock bookkeeping excluded)."""
    return {v.get("sha256") for v in data_view(inv).values()}


def independent_verify(cfg, expect_master):
    """Recomputes the intended final set from scratch; ignores journal and result text."""
    master = open(os.path.join(cfg, proto.MASTER_NAME), "rb").read()
    n, body, man = proto.compile_synthetic(master)
    auth = os.path.join(cfg, "sfm_shared_authority")
    names = sorted(os.listdir(auth))
    ok = (sha(master) == sha(expect_master) and names == sorted([n, "manifest.json"])
          and sha(open(os.path.join(auth, n), "rb").read()) == sha(body)
          and sha(open(os.path.join(auth, "manifest.json"), "rb").read()) == sha(man))
    return {"ok": ok, "master_sha256": sha(master), "authority": names, "expected_sidecar": n}


def state_equals(cfg, inv_ref, keys_prefix=("sfm_defaultanimationgroups.txt", "sfm_shared_authority/")):
    inv = inventory(cfg)
    a = {k: v["sha256"] for k, v in inv.items() if k.startswith(keys_prefix)}
    b = {k: v["sha256"] for k, v in inv_ref.items() if k.startswith(keys_prefix)}
    return a == b


# ---------------------------------------------------------------- processes
class Stepper(object):
    def __init__(self, args, tag):
        self.out = os.path.join(EVID, "runs", tag + ".json")
        self.p = subprocess.Popen([PY, os.path.join(HERE, "proto.py")] + [args[0], args[1], self.out]
                                  + args[2:], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, cwd=HERE)
        self.tag = tag

    def wait_event(self):
        line = self.p.stdout.readline().strip()
        return line

    def go(self):
        self.p.stdin.write("go\n")
        self.p.stdin.flush()

    def kill(self):
        self.p.kill()  # TerminateProcess
        self.p.wait()
        return self.p.returncode

    def finish(self):
        rest, err = self.p.communicate(timeout=120)
        res = json.load(open(self.out, encoding="utf-8")) if os.path.exists(self.out) else None
        if self.p.returncode != 0:
            raise RuntimeError("proto exited %s: %s" % (self.p.returncode, err[-2000:]))
        return res


def run_proto(args, tag, stops=(), actions=None, kill_at=None):
    """Runs proto with optional barriers. actions: {barrier: callable}. kill_at: barrier name."""
    stop_list = list(stops) + ([kill_at] if kill_at else [])
    if stop_list:
        args = args + ["--stop-at", ",".join(stop_list)]
    s = Stepper(args, tag)
    events = []
    while True:
        ev = s.wait_event()
        if not ev:
            break
        events.append(ev)
        if ev.startswith("BARRIER "):
            b = ev.split(" ", 1)[1]
            if actions and b in actions:
                events.append({"action_at": b, "result": actions[b]()})
            if b == kill_at:
                code = s.kill()
                return {"killed_at": b, "exit_code": code, "events": events,
                        "termination": "TerminateProcess (Popen.kill)"}
            s.go()
        elif ev.startswith("RESULT"):
            break
    res = s.finish()
    return {"result": res, "events": events}


def racer(*args):
    p = subprocess.run([PY, os.path.join(HERE, "racer.py")] + list(args), capture_output=True,
                       text=True, cwd=HERE, timeout=60)
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        return {"raw_stdout": p.stdout, "stderr": p.stderr[-1000:], "rc": p.returncode}


class Holder(object):
    """Long-lived racer (hold/lock) in its own process."""

    def __init__(self, *args):
        self.p = subprocess.Popen([PY, os.path.join(HERE, "racer.py")] + list(args),
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, cwd=HERE)
        self.first = json.loads(self.p.stdout.readline())

    def release(self):
        try:
            self.p.stdin.write("x\n")
            self.p.stdin.flush()
        except OSError:
            pass
        self.p.wait(timeout=30)

    def kill(self):
        self.p.kill()
        self.p.wait()
        return self.p.returncode


def activate_args(cfg, kind="rebuild", source=None, confirm=None):
    a = ["activate", cfg, "--kind", kind,
         "--confirm-sha", confirm or sha(open(os.path.join(cfg, proto.MASTER_NAME), "rb").read())]
    if source:
        a += ["--source", source]
    # U0A uses synthetic installations only; the advisory SFM-process check is recorded, not
    # enforced, so a running (unrelated) SFM does not abort synthetic runs. 6o tests the refusal.
    a += ["--inject", "sfm_policy_record_only=1"]
    return a


def record(test, name, verdict, **ev):
    ev.update(test=test, case=name, verdict=verdict)
    RESULTS.append(ev)
    print("%-8s %-58s %s" % (test, name[:58], verdict))
    sys.stdout.flush()


def outcome_of(run):
    if "result" in run and run["result"]:
        return run["result"].get("outcome")
    return None


# ================================================================= U0A-1
def u0a_1():
    d = os.path.join(CASES, "u0a1")
    os.makedirs(os.path.join(d, "sub"))
    a = os.path.join(d, "a.txt")
    b = os.path.join(d, "sub", "b.txt")
    w32.TRACE[:] = []
    w32.write_new_file(a, b"protected payload\n")
    before = w32.path_identity(a)
    h, err = w32.create_file(a, w32.GENERIC_READ | w32.DELETE, 0, w32.OPEN_EXISTING)
    inh = w32.handle_inheritable(h)
    comp = {
        "other_read_full_share": racer("hold", a, "7", "r"),
        "other_inplace_write": racer("inplace", a),
        "other_delete": racer("delete", a),
        "other_rename": racer("rename", a, a + ".moved"),
        "other_replacefile": racer("replacefile", a),
        "other_movereplace": racer("movereplace", a),
    }
    refused = all(not v.get("ok") and "SHARING_VIOLATION" in str(v.get("error"))
                  for k, v in comp.items() if k not in ("other_replacefile", "other_movereplace"))
    repl_refused = all(not comp[k].get("ok") for k in ("other_replacefile", "other_movereplace"))
    id_before = w32.file_id(h)
    ok, err = w32.rename_by_handle(h, b, False)
    fp = w32.final_path(h)
    sh, _ = w32.sha_handle(h)
    id_after = w32.file_id(h)
    reopen_held = w32.create_file(b, w32.GENERIC_READ, 7, w32.OPEN_EXISTING)
    w32.close(h)
    after = w32.path_identity(b)
    trace1 = list(w32.TRACE)
    passed = (ok and refused and repl_refused and not inh and sh == before["sha256"] and id_before == id_after
              and after["sha256"] == before["sha256"] and after["file_id"] == before["file_id"]
              and reopen_held[0] is None and reopen_held[1] == 32 and not os.path.exists(a))
    for k in ("other_replacefile", "other_movereplace"):
        t = comp[k].get("temp")
        if t and os.path.exists(os.path.join(d, t)):
            comp[k]["temp_preserved_by_racer"] = True
    record("U0A-1", "1a/1b exclusive GENERIC_READ|DELETE share 0; rename by held handle; reopen+hash",
           "PASS" if passed else "FAIL", before=before, after=after, competitors=comp,
           rename_ok=ok, rename_error=w32.ename(err) if not ok else None, final_path_by_handle=fp,
           hash_via_held_handle=sh, file_id_before=id_before, file_id_after=id_after,
           reopen_while_held_error=w32.ename(reopen_held[1]), handle_inheritable=inh, trace=trace1)

    # 1c destination exists: no clobber
    w32.TRACE[:] = []
    c = os.path.join(d, "c.txt")
    w32.write_new_file(c, b"occupant\n")
    occ = w32.path_identity(c)
    h, _ = w32.create_file(b, w32.GENERIC_READ | w32.DELETE, 0, w32.OPEN_EXISTING)
    ok, err = w32.rename_by_handle(h, c, False)
    fp = w32.final_path(h)
    w32.close(h)
    passed = (not ok and err == 183 and w32.path_identity(c) == occ
              and w32.path_identity(b)["sha256"] == before["sha256"])
    record("U0A-1", "1c ReplaceIfExists=FALSE onto existing destination", "PASS" if passed else "FAIL",
           error=w32.ename(err), source_still_at=fp, occupant_before=occ,
           occupant_after=w32.path_identity(c), source_after=w32.path_identity(b), trace=list(w32.TRACE))

    # 1d rename without DELETE access is refused (DELETE is required for the own-handle move)
    w32.TRACE[:] = []
    h, _ = w32.create_file(b, w32.GENERIC_READ, 0, w32.OPEN_EXISTING)
    ok, err = w32.rename_by_handle(h, os.path.join(d, "d.txt"), False)
    w32.close(h)
    record("U0A-1", "1d own-handle rename without DELETE access", "PASS" if (not ok and err == 5) else "FAIL",
           error=w32.ename(err), note="confirms GENERIC_READ|DELETE is needed for a file that moves",
           trace=list(w32.TRACE))

    # 1e retained protection GENERIC_READ share 0
    w32.TRACE[:] = []
    h, _ = w32.create_file(b, w32.GENERIC_READ, 0, w32.OPEN_EXISTING)
    comp = {"read": racer("hold", b, "7", "r"), "write": racer("inplace", b), "delete": racer("delete", b),
            "rename": racer("rename", b, b + ".x"), "replacefile": racer("replacefile", b),
            "movereplace": racer("movereplace", b)}
    w32.close(h)
    passed = all(not v.get("ok") for v in comp.values()) and w32.path_identity(b)["sha256"] == before["sha256"]
    record("U0A-1", "1e retained-file protection GENERIC_READ share 0", "PASS" if passed else "FAIL",
           competitors=comp, trace=list(w32.TRACE))

    # 1f a directory occupant at the destination name also refuses
    w32.TRACE[:] = []
    os.mkdir(os.path.join(d, "dirocc"))
    h, _ = w32.create_file(b, w32.GENERIC_READ | w32.DELETE, 0, w32.OPEN_EXISTING)
    ok, err = w32.rename_by_handle(h, os.path.join(d, "dirocc"), False)
    w32.close(h)
    record("U0A-1", "1f destination occupied by a directory", "PASS" if not ok else "FAIL",
           error=w32.ename(err), dir_still_present=os.path.isdir(os.path.join(d, "dirocc")),
           trace=list(w32.TRACE))

    # 1g cross-volume move is refused (no copy fallback exists in the primitive)
    w32.TRACE[:] = []
    other = ("E:" if os.path.splitdrive(ROOT)[0].upper() == "C:" else "C:") + "\\u0a_crossvolume_probe_target.tmp"
    existed = os.path.exists(other)
    h, _ = w32.create_file(b, w32.GENERIC_READ | w32.DELETE, 0, w32.OPEN_EXISTING)
    ok, err = w32.rename_by_handle(h, other, False)
    w32.close(h)
    created = os.path.exists(other) and not existed
    if created:
        os.remove(other)
    record("U0A-1", "1g cross-volume own-handle rename", "PASS" if (not ok and not created) else "FAIL",
           error=w32.ename(err), target="<other volume root>\\u0a_crossvolume_probe_target.tmp",
           target_created=created, source_intact=w32.path_identity(b)["sha256"] == before["sha256"],
           trace=list(w32.TRACE))


# ================================================================= U0A-2 source races
def race_case(tag, kind, phase, action, target_role):
    cfg = make_case(tag, master=TXT_B if kind == "rebuild" else TXT_A, compiled_from=TXT_A)
    src = None
    if kind == "replace":
        src = os.path.join(CASES, tag, "import_source.txt")
        open(src, "wb").write(TXT_C)
    inv0 = inventory(cfg)
    auth = os.path.join(cfg, "sfm_shared_authority")
    target = {"master": os.path.join(cfg, proto.MASTER_NAME),
              "sidecar": os.path.join(auth, [n for n in os.listdir(auth) if n.endswith(".sfmsidecar")][0])
              }[target_role]

    def act():
        if action == "rename":
            return racer("rename", target, target + ".renamed")
        return racer(action, target)

    barrier = {"before_preview": None, "after_preview": "previewed", "before_protection": "snapshots_written",
               "during_protection": "protected", "during_moves": "moves_done", "after_release": "released"}[phase]
    pre = None
    if phase == "before_preview":
        pre = act()
    run = run_proto(activate_args(cfg, kind, src, confirm=sha(open(os.path.join(cfg, proto.MASTER_NAME), "rb").read())
                                  if phase != "before_preview" else sha(TXT_B if kind == "rebuild" else TXT_A)),
                    tag, stops=[barrier] if barrier else [], actions={barrier: act} if barrier else None)
    res = run["result"]
    racer_res = pre if pre else [e for e in run["events"] if isinstance(e, dict)][0]["result"]
    inv1 = inventory(cfg)
    edit_sha = racer_res.get("result_sha256") if racer_res.get("ok") else None
    edit_present = (edit_sha is None) or edit_sha in shas(inv1)
    target_rel = os.path.relpath(target, cfg).replace("\\", "/")
    target_sha0 = inv0[target_rel]["sha256"]
    lost = set(shas(inv0) - shas(inv1) - {None})
    if racer_res.get("ok") and action in ("delete", "rename", "inplace", "inplace_py", "replacefile",
                                          "movereplace"):
        # the racer's own successful change of its target is the user's action, not a loss
        lost.discard(target_sha0)
    lost = sorted(lost)
    outcome = res["outcome"]
    if phase == "during_protection":
        # The racer must be refused. If its refused attempt left debris (an editor temp file) in the
        # authority directory, the inventory recheck must stop the activation before any move.
        debris = sorted(k for k in inv1 if k.startswith("sfm_shared_authority/") and ".~edit" in k)
        passed = (not racer_res.get("ok")) and not lost and (
            outcome == "COMPLETE" or (outcome == "ABANDONED" and debris and
                                      (res.get("details") or {}).get("mismatch") == ["authority inventory"]))
    elif phase == "after_release":
        passed = outcome == "COMPLETE" and racer_res.get("ok") and edit_present and not lost
    else:
        # before protection: the racer wins; the updater must refuse without moving anything
        auth0 = {k: v["sha256"] for k, v in inv0.items() if k.startswith("sfm_shared_authority/") and k != target_rel}
        auth1 = {k: v["sha256"] for k, v in inv1.items() if k.startswith("sfm_shared_authority/") and k != target_rel
                 and not k.endswith(".renamed")}
        passed = (outcome in ("REFUSED", "ABANDONED") and racer_res.get("ok") and edit_present
                  and auth0 == auth1 and not lost)
    record("U0A-2", "%s %s %s on %s" % (kind, phase, action, target_role), "PASS" if passed else "FAIL",
           racer=racer_res, outcome=outcome, message=res.get("message"), details=res.get("details"),
           inventory_before=inv0, inventory_after=inv1, lost_original_sha256=lost, run=tag)


def u0a_2():
    n = 0
    for kind in ("rebuild", "replace"):
        for phase in ("before_preview", "after_preview", "before_protection", "during_protection",
                      "after_release"):
            for action in ("inplace", "inplace_py", "replacefile", "movereplace", "delete", "rename"):
                n += 1
                race_case("u0a2_%02d_%s_%s_%s" % (n, kind, phase, action), kind, phase, action, "master")
    for phase in ("before_protection", "during_protection"):
        for action in ("inplace", "replacefile", "delete", "rename"):
            n += 1
            race_case("u0a2_%02d_sidecar_%s_%s" % (n, phase, action), "rebuild", phase, action, "sidecar")
    # Replace: master path is vacant between moving M0 out and M1 in. A file created there
    # must be preserved and the transaction must not overwrite it.
    dest_collisions(prefix="u0a2_dest")


def dest_collisions(prefix):
    for kind in ("rebuild", "replace"):
        cfg0 = make_case("%s_plan_%s" % (prefix, kind), master=TXT_B if kind == "rebuild" else TXT_A)
        src = os.path.join(CASES, "%s_plan_%s" % (prefix, kind), "import.txt")
        open(src, "wb").write(TXT_C)
        dry = run_proto(activate_args(cfg0, kind, src if kind == "replace" else None), "%s_plan_%s" % (prefix, kind))
        plan = dry["result"]["plan"]
        for mv in plan:
            tag = "%s_%s_move%d_%s" % (prefix, kind, mv["i"], mv["role"])
            cfg = make_case(tag, master=TXT_B if kind == "rebuild" else TXT_A)
            src = os.path.join(CASES, tag, "import.txt")
            open(src, "wb").write(TXT_C)
            inv0 = inventory(cfg)
            box = {}

            def occupy(mv=mv, cfg=cfg, box=box):
                lay = proto.Layout(cfg)
                txid = os.listdir(lay.txroot)[0]
                kindd, name = mv["dst"].split("/", 1)
                p = lay.slot(txid, kindd, name)
                box["path"] = os.path.relpath(p, cfg)
                return racer("create", p)
            run = run_proto(activate_args(cfg, kind, src if kind == "replace" else None), tag,
                            stops=["act_begin_forward_%d" % mv["i"]],
                            actions={"act_begin_forward_%d" % mv["i"]: occupy})
            res = run["result"]
            inv1 = inventory(cfg)
            occ = [v for k, v in inv1.items() if k.replace("/", "\\") == box["path"]]
            occ_ok = bool(occ) and occ[0]["sha256"] and b"UNEXPECTED" in open(os.path.join(cfg, box["path"]), "rb").read()
            lost = sorted(shas(inv0) - shas(inv1) - {None})
            fwd = res.get("forward_failure") or (res.get("details") or {})
            passed = (res["outcome"] in ("ROLLED_BACK", "CONFLICT") and occ_ok and not lost
                      and res["outcome"] != "COMPLETE")
            if res["outcome"] == "ROLLED_BACK":
                passed = passed and state_equals(cfg, inv0)
            record("U0A-2", "%s destination occupied before move %d (%s)" % (kind, mv["i"], mv["role"]),
                   "PASS" if passed else "FAIL", outcome=res["outcome"], message=res.get("message"),
                   forward_failure=res.get("forward_failure"), details=res.get("details"),
                   occupant=box.get("path"), occupant_preserved=occ_ok, lost_original_sha256=lost,
                   inventory_before=inv0, inventory_after=inv1, run=tag)
            # A follow-up recovery must not overwrite the occupant either.
            if res["outcome"] == "CONFLICT":
                rec = run_proto(["recover", cfg], tag + "_recover")
                inv2 = inventory(cfg)
                ok2 = (b"UNEXPECTED" in open(os.path.join(cfg, box["path"]), "rb").read()
                       and not (shas(inv0) - shas(inv2) - {None}))
                record("U0A-2", "%s occupied move %d: recovery afterwards" % (kind, mv["i"]),
                       "PASS" if ok2 else "FAIL",
                       recovery=rec["result"]["transactions"], inventory_after=inv2, run=tag + "_recover")


# ================================================================= U0A-3 lock
def u0a_3():
    d = make_case("u0a3")
    lay = proto.Layout(d)
    A = Holder("lock", lay.lock)
    B = racer("lock", lay.lock)
    record("U0A-3", "3a two competing processes", "PASS" if A.first["state"] == "ACQUIRED" and B.get("state") == "REFUSED" else "FAIL",
           holder=A.first, competitor=B)
    code = A.kill()
    exists = os.path.exists(lay.lock)
    C = Holder("lock", lay.lock)
    record("U0A-3", "3b holder terminated while holding; reacquisition",
           "PASS" if C.first["state"] == "ACQUIRED" and exists and not C.first["created"] else "FAIL",
           killed_exit_code=code, lock_file_exists_after_kill=exists, reacquirer=C.first)
    # activation refuses while the lock is held
    inv0 = inventory(d)
    run = run_proto(activate_args(d), "u0a3_activate_while_locked")
    inv1 = inventory(d)
    record("U0A-3", "3c activation while another process owns the lock",
           "PASS" if run["result"]["outcome"] == "ABANDONED" and state_equals(d, inv0) else "FAIL",
           outcome=run["result"]["outcome"], details=run["result"].get("details"))
    # lock directory cannot be renamed while the lock is held
    r = racer("dirrename", lay.upd, lay.upd + "_renamed")
    record("U0A-3", "3d rename of the lock's directory while held", "PASS" if not r.get("ok") else "FAIL",
           racer=r)
    C.release()
    # stale lock file (existence) does not imply ownership
    D = Holder("lock", lay.lock)
    record("U0A-3", "3e pre-existing lock file without a live owner",
           "PASS" if D.first["state"] == "ACQUIRED" and not D.first["created"] and not D.first["inheritable"] else "FAIL",
           acquirer=D.first)
    # aliases to the same physical installation
    aliases = {}
    junction = os.path.join(CASES, "u0a3_junction_alias")
    subprocess.run(["cmd", "/c", "mklink", "/J", junction, os.path.join(CASES, "u0a3")], capture_output=True)
    aliases["junction"] = os.path.join(junction, "usermod", "cfg", "sfm_character_tools_updater", "installation.lock")
    aliases["case_variant"] = lay.lock.upper()
    aliases["extended_prefix"] = "\\\\?\\" + lay.lock
    aliases["dot_segments"] = os.path.join(lay.upd, "transactions", "..", "installation.lock")
    sbuf = ctypes.create_unicode_buffer(1024)
    ctypes.windll.kernel32.GetShortPathNameW(lay.lock, sbuf, 1024)
    if sbuf.value and sbuf.value.lower() != lay.lock.lower():
        aliases["short_8dot3"] = sbuf.value
    hl = os.path.join(lay.upd, "installation_hardlink.lock")
    try:
        os.link(lay.lock, hl)
        aliases["hard_link"] = hl
    except OSError as e:
        aliases["hard_link_error"] = str(e)
    letter = None
    for L in "QRSTUVWXYZ":
        if not os.path.exists(L + ":\\"):
            letter = L
            break
    if letter:
        sp = subprocess.run(["subst", letter + ":", os.path.join(CASES, "u0a3")], capture_output=True, text=True)
        if sp.returncode == 0:
            aliases["subst_drive"] = letter + ":\\usermod\\cfg\\sfm_character_tools_updater\\installation.lock"
    unc = "\\\\localhost\\" + lay.lock[0] + "$" + lay.lock[2:]
    aliases["unc_admin_share"] = unc
    ares = {}
    for k, p in aliases.items():
        if k.endswith("_error"):
            continue
        r = racer("lock", p)
        ares[k] = r
    passed = all((not r.get("ok")) for r in ares.values())
    sharing = {k: r.get("error") for k, r in ares.items()}
    D.release()
    # every alias resolves to the same physical file
    ids = {}
    for k, p in aliases.items():
        if k.endswith("_error"):
            continue
        ident = w32.path_identity(p)
        ids[k] = ident["file_id"] if ident else None
    ids["canonical"] = w32.path_identity(lay.lock)["file_id"]
    if letter and "subst_drive" in aliases:
        subprocess.run(["subst", letter + ":", "/d"], capture_output=True)
    if "hard_link" in aliases:
        os.remove(hl)
    record("U0A-3", "3f aliases to the same physical lock while held", "PASS" if passed else "FAIL",
           aliases={k: redact_alias(v) for k, v in aliases.items()}, competitor_errors=sharing,
           physical_identity=ids)
    # access denied: lock file denies write for this user
    d2 = make_case("u0a3_denied")
    l2 = proto.Layout(d2)
    open(l2.lock, "wb").close()
    icacls(l2.lock, "/deny", "%s:(W)" % USER)
    before = sorted(os.listdir(l2.upd))
    r = racer("lock", l2.lock)
    after = sorted(os.listdir(l2.upd))
    icacls(l2.lock, "/remove:d", USER)
    record("U0A-3", "3g lock file denies write access", "PASS" if (not r.get("ok") and "ACCESS_DENIED" in str(r.get("error")) and before == after) else "FAIL",
           competitor=r, updater_dir_before=before, updater_dir_after=after,
           note="no per-user substitute lock is created")
    os.remove(l2.lock)
    icacls(l2.upd, "/deny", "%s:(WD)" % USER)
    r = racer("lock", l2.lock)
    after = sorted(os.listdir(l2.upd))
    icacls(l2.upd, "/remove:d", USER)
    record("U0A-3", "3h lock directory denies file creation (no lock file yet)",
           "PASS" if (not r.get("ok") and "ACCESS_DENIED" in str(r.get("error")) and "installation.lock" not in after) else "FAIL",
           competitor=r, updater_dir_after=after)
    record("U0A-3", "3i cross-user contention", "NOT RUN",
           reason="no second interactive account credentials and no elevation in this session; "
                  "the share-mode lock is a kernel file-object property and is not SID-named, "
                  "but cross-user evidence is deferred (U0B/L)")


def redact_alias(p):
    return p.replace(ROOT, "<U0A_ROOT>")


def icacls(path, *args):
    """icacls cannot address paths beyond MAX_PATH; reach the item through a temporary subst
    drive mapped to its parent directory (same physical file)."""
    letter = None
    for L in "PONMLKJIH":
        if not os.path.exists(L + ":\\"):
            letter = L
            break
    sp = subprocess.run(["subst", letter + ":", os.path.dirname(path)], capture_output=True, text=True)
    if sp.returncode != 0:
        raise RuntimeError("subst failed: %s" % sp.stdout)
    try:
        r = subprocess.run(["icacls", letter + ":\\" + os.path.basename(path)] + list(args),
                           capture_output=True, text=True)
    finally:
        subprocess.run(["subst", letter + ":", "/d"], capture_output=True)
    if "Successfully processed 1 files" not in r.stdout:
        raise RuntimeError("icacls failed on %s: %s %s" % (redact_alias(path), r.stdout, r.stderr))
    return r


# ================================================================= U0A-4 activation
def u0a_4():
    # 4a rebuild: TXT unchanged (edited after the old sidecar was compiled)
    cfg = make_case("u0a4_rebuild", master=TXT_B, compiled_from=TXT_A)
    inv0 = inventory(cfg)
    run = run_proto(activate_args(cfg), "u0a4_rebuild")
    inv1 = inventory(cfg)
    iv = independent_verify(cfg, TXT_B)
    master_same = inv0[proto.MASTER_NAME] == inv1[proto.MASTER_NAME]
    lay = proto.Layout(cfg)
    txid = run["result"]["txid"]
    retired = sorted(os.listdir(os.path.join(lay.txdir(txid), "retired")))
    cand = sorted(os.listdir(os.path.join(lay.txdir(txid), "candidate")))
    lost = sorted(shas(inv0) - shas(inv1) - {None})
    rec = run_proto(["recover", cfg], "u0a4_rebuild_recover_after")
    inv2 = inventory(cfg)
    passed = (run["result"]["outcome"] == "COMPLETE" and iv["ok"] and master_same and not lost
              and cand == [] and len(retired) == 2 and inv2 == inv1
              and rec["result"]["transactions"][0]["outcome"] == "TERMINAL")
    record("U0A-4", "4a rebuild with TXT unchanged (bytes and file identity retained)",
           "PASS" if passed else "FAIL", outcome=run["result"]["outcome"], plan=run["result"]["plan"],
           independent=iv, master_bytes_and_identity_unchanged=master_same, retired=retired,
           candidate_left=cand, inventory_before=inv0, inventory_after=inv1,
           repeat_recovery=rec["result"]["transactions"], repeat_recovery_changed_nothing=inv2 == inv1,
           barriers=run["result"]["barriers"], trace=run["result"]["trace"])
    # 4b replacement TXT with matching authority
    cfg = make_case("u0a4_replace", master=TXT_A, compiled_from=TXT_A)
    src = os.path.join(CASES, "u0a4_replace", "import.txt")
    open(src, "wb").write(TXT_C)
    src_before = w32.path_identity(src)
    inv0 = inventory(cfg)
    run = run_proto(activate_args(cfg, "replace", src), "u0a4_replace")
    inv1 = inventory(cfg)
    iv = independent_verify(cfg, TXT_C)
    lost = sorted(shas(inv0) - shas(inv1) - {None})
    txid = run["result"]["txid"]
    retired = sorted(os.listdir(os.path.join(proto.Layout(cfg).txdir(txid), "retired")))
    src_after = w32.path_identity(src)
    passed = (run["result"]["outcome"] == "COMPLETE" and iv["ok"] and not lost and len(retired) == 3
              and src_after["sha256"] == src_before["sha256"])
    record("U0A-4", "4b replacement TXT with matching authority", "PASS" if passed else "FAIL",
           outcome=run["result"]["outcome"], plan=run["result"]["plan"], independent=iv, retired=retired,
           import_source_unmodified=src_after["sha256"] == src_before["sha256"],
           inventory_before=inv0, inventory_after=inv1, barriers=run["result"]["barriers"],
           trace=run["result"]["trace"])
    # 4c verified no-op
    cfg = make_case("u0a4_noop", master=TXT_A, compiled_from=TXT_A)
    inv0 = inventory(cfg)
    run = run_proto(activate_args(cfg), "u0a4_noop")
    inv1 = inventory(cfg)
    record("U0A-4", "4c already-installed candidate is a verified no-op",
           "PASS" if run["result"]["outcome"] == "NOOP" and data_view(inv0) == data_view(inv1) else "FAIL",
           outcome=run["result"]["outcome"], unchanged_except_lock_file=data_view(inv0) == data_view(inv1),
           lock_file_created=("sfm_character_tools_updater/installation.lock" in inv1
                              and "sfm_character_tools_updater/installation.lock" not in inv0))
    # 4d several historical sidecars and no manifest -> exactly one active artifact afterwards
    cfg = make_case("u0a4_multi", master=TXT_B, compiled_from=TXT_A, with_manifest=False,
                    extra_sidecars=(TXT_OLD,))
    inv0 = inventory(cfg)
    run = run_proto(activate_args(cfg), "u0a4_multi")
    iv = independent_verify(cfg, TXT_B)
    inv1 = inventory(cfg)
    record("U0A-4", "4d two historical sidecars, no manifest -> one active artifact",
           "PASS" if run["result"]["outcome"] == "COMPLETE" and iv["ok"] and not (shas(inv0) - shas(inv1) - {None}) else "FAIL",
           outcome=run["result"]["outcome"], plan=run["result"]["plan"], independent=iv,
           inventory_before=inv0, inventory_after=inv1)
    # 4e activation through an installation alias (junction) lands at the physical location
    cfg = make_case("u0a4_alias", master=TXT_B, compiled_from=TXT_A)
    j = os.path.join(CASES, "u0a4_alias_junction")
    subprocess.run(["cmd", "/c", "mklink", "/J", j, os.path.join(CASES, "u0a4_alias")], capture_output=True)
    acfg = os.path.join(j, "usermod", "cfg")
    run = run_proto(activate_args(acfg), "u0a4_alias")
    iv = independent_verify(cfg, TXT_B)
    record("U0A-4", "4e activation addressed through a junction alias of the installation",
           "PASS" if run["result"]["outcome"] == "COMPLETE" and iv["ok"] else "FAIL",
           outcome=run["result"]["outcome"], independent=iv,
           note="final paths reported by the held handles are the physical (junction-resolved) paths")


# ================================================================= U0A-5 interruption
def all_barriers(kind):
    tag = "u0a5_probe_%s" % kind
    cfg = make_case(tag, master=TXT_B if kind == "rebuild" else TXT_A)
    src = os.path.join(CASES, tag, "import.txt")
    open(src, "wb").write(TXT_C)
    run = run_proto(activate_args(cfg, kind, src if kind == "replace" else None), tag)
    return [b for b in run["result"]["barriers"] if not b.startswith("resumed:")], run["result"]["plan"]


def judge(cfg, inv0, all_shas, outcome, expect_master_new, expect_master_old):
    """Acceptable: verified new state, verified old state, or conflict with every byte-set preserved."""
    inv = inventory(cfg)
    lost = sorted(all_shas - shas(inv) - {None})
    if outcome == "COMPLETE":
        ok = independent_verify(cfg, expect_master_new)["ok"]
        return ok and not lost, "new", lost
    if outcome in ("ROLLED_BACK", "ABANDONED"):
        return state_equals(cfg, inv0) and not lost, "old", lost
    if outcome == "CONFLICT":
        return not lost, "conflict", lost
    return False, "unexpected:%s" % outcome, lost


def u0a_5():
    for kind in ("rebuild", "replace"):
        barriers, plan = all_barriers(kind)
        kills = [b for b in barriers if b not in ("previewed",)]
        for policy in ("resume", "rollback"):
            for b in kills:
                kill_case(kind, b, policy)
        # interruption during recovery (forward resume and rollback), from a mid-transaction kill
        mid = "act_moved_forward_%d" % (len(plan) // 2)
        for policy in ("resume", "rollback"):
            rec_barriers = kill_case(kind, mid, policy, probe_recovery=True)
            for rb in rec_barriers:
                kill_case(kind, mid, policy, kill_recovery_at=rb)
        # post-crash user edit, missing component, journal/disk disagreement
        post_crash_cases(kind, plan)


def new_install(tag, kind):
    cfg = make_case(tag, master=TXT_B if kind == "rebuild" else TXT_A)
    src = os.path.join(CASES, tag, "import.txt")
    open(src, "wb").write(TXT_C)
    return cfg, src


def kill_case(kind, b, policy, probe_recovery=False, kill_recovery_at=None):
    tag = "u0a5_%s_%s_%s%s" % (kind, policy, b, ("_reckill_" + kill_recovery_at) if kill_recovery_at else
                                ("_probe" if probe_recovery else ""))
    cfg, src = new_install(tag, kind)
    inv0 = inventory(cfg)
    new_master = TXT_B if kind == "rebuild" else TXT_C
    cand = proto.compile_synthetic(new_master)
    all_shas = shas(inv0) | {sha(new_master), sha(cand[1]), sha(cand[2])}
    run = run_proto(activate_args(cfg, kind, src if kind == "replace" else None), tag, kill_at=b)
    killed = "killed_at" in run
    inv_k = inventory(cfg)
    rec_args = ["recover", cfg, "--policy", policy]
    extra = {}
    if kill_recovery_at:
        r1 = run_proto(rec_args, tag + "_rec1", kill_at=kill_recovery_at)
        extra["recovery_killed_at"] = r1.get("killed_at")
        extra["inventory_after_recovery_kill"] = inventory(cfg)
    rec = run_proto(rec_args, tag + "_rec")
    if probe_recovery:
        return [x for x in rec["result"]["barriers"] if x.startswith("rec_")]
    txs = rec["result"]["transactions"]
    outc = txs[0]["outcome"] if txs else "NONE"
    if outc == "TERMINAL":
        outc = txs[0]["terminal"]
    inv1 = inventory(cfg)
    ok, where, lost = judge(cfg, inv0, all_shas, outc, new_master, None)
    rec2 = run_proto(rec_args, tag + "_rec2")
    inv2 = inventory(cfg)
    idem = inv2 == inv1 and all(t["outcome"] in ("TERMINAL", "CONFLICT", "REFUSED") for t in rec2["result"]["transactions"])
    truthful = True
    if where == "conflict":
        truthful = "recovered" not in txs[0]["message"].lower() and "complete" not in txs[0]["message"].lower()
    passed = killed and ok and idem and truthful
    record("U0A-5", "%s kill@%s policy=%s%s" % (kind, b, policy,
                                               (" reckill@" + kill_recovery_at) if kill_recovery_at else ""),
           "PASS" if passed else "FAIL", killed=run.get("killed_at"), exit_code=run.get("exit_code"),
           inventory_after_kill=inv_k, recovery=txs, final_state=where, lost_sha256=lost,
           second_recovery=rec2["result"]["transactions"], second_recovery_changed_nothing=inv2 == inv1,
           run=tag, **extra)
    return None


def post_crash_cases(kind, plan):
    mid = "act_done_forward_%d" % (len(plan) // 2)
    # (a) user edits/creates the TXT after the crash, before recovery
    tag = "u0a5_%s_postcrash_txt_edit" % kind
    cfg, src = new_install(tag, kind)
    run_proto(activate_args(cfg, kind, src if kind == "replace" else None), tag, kill_at=mid)
    mp = os.path.join(cfg, proto.MASTER_NAME)
    inv_crash = inventory(cfg)
    if os.path.exists(mp):
        r = racer("inplace", mp)
    else:
        r = racer("create", mp)
    user_bytes = open(mp, "rb").read()
    inv_k = inventory(cfg)
    rec = run_proto(["recover", cfg], tag + "_rec")
    t = rec["result"]["transactions"][0]
    inv1 = inventory(cfg)
    kept = open(mp, "rb").read() == user_bytes
    lost = sorted(shas(inv_k) - shas(inv1) - {None})
    rec2 = run_proto(["recover", cfg], tag + "_rec2")
    passed = t["outcome"] == "CONFLICT" and kept and not lost and inventory(cfg) == inv1 and         data_view(inv1) == data_view(inv_k)
    record("U0A-5", "%s TXT changed after crash, before recovery" % kind, "PASS" if passed else "FAIL",
           racer=r, recovery=t, newer_bytes_retained=kept, lost_sha256=lost,
           second_recovery=rec2["result"]["transactions"])
    # (b) a required recovery component is missing (retired original removed)
    tag = "u0a5_%s_missing_retired" % kind
    cfg, src = new_install(tag, kind)
    run_proto(activate_args(cfg, kind, src if kind == "replace" else None), tag, kill_at=mid)
    lay = proto.Layout(cfg)
    txid = os.listdir(lay.txroot)[0]
    ret = os.path.join(lay.txdir(txid), "retired")
    victim = sorted(os.listdir(ret))[0]
    os.rename(os.path.join(ret, victim), os.path.join(CASES, tag, "removed_" + victim))
    inv_k = inventory(cfg)
    rec = run_proto(["recover", cfg, "--policy", "rollback"], tag + "_rec")
    t = rec["result"]["transactions"][0]
    inv1 = inventory(cfg)
    passed = (t["outcome"] == "CONFLICT" and "restored" not in t["message"].lower()
              and data_view(inv1) == data_view(inv_k) and t["message"] == proto.MESSAGES["MISSING"])
    record("U0A-5", "%s retired original missing; rollback requested" % kind, "PASS" if passed else "FAIL",
           removed=victim, recovery=t, data_unchanged=data_view(inv1) == data_view(inv_k))
    # (c) corrupted candidate (resume requested)
    tag = "u0a5_%s_corrupt_candidate" % kind
    cfg, src = new_install(tag, kind)
    early = "act_done_forward_0"
    run_proto(activate_args(cfg, kind, src if kind == "replace" else None), tag, kill_at=early)
    lay = proto.Layout(cfg)
    txid = os.listdir(lay.txroot)[0]
    cdir = os.path.join(lay.txdir(txid), "candidate")
    victim = [n for n in os.listdir(cdir) if n.endswith(".sfmsidecar")][0]
    with open(os.path.join(cdir, victim), "r+b") as f:
        f.write(b"CORRUPT")
    inv_k = inventory(cfg)
    rec = run_proto(["recover", cfg], tag + "_rec")
    t = rec["result"]["transactions"][0]
    inv1 = inventory(cfg)
    passed = t["outcome"] == "CONFLICT" and data_view(inv1) == data_view(inv_k)
    record("U0A-5", "%s candidate corrupted after crash; resume requested" % kind, "PASS" if passed else "FAIL",
           recovery=t, data_unchanged=data_view(inv1) == data_view(inv_k))
    # (d) journal claims more progress than the disk shows (no journal-only recovery)
    tag = "u0a5_%s_journal_ahead" % kind
    cfg, src = new_install(tag, kind)
    run_proto(activate_args(cfg, kind, src if kind == "replace" else None), tag, kill_at="act_done_forward_1")
    lay = proto.Layout(cfg)
    txid = os.listdir(lay.txroot)[0]
    plan_moves = proto.make_plan(json.load(open(os.path.join(lay.txdir(txid), "intent.json"))))
    m = plan_moves[1]
    a = lay.slot(txid, *m["dst"])
    b = lay.slot(txid, *m["src"])
    os.rename(a, b)  # the disk silently loses move 1 although the journal says DONE
    inv_k = inventory(cfg)
    rec = run_proto(["recover", cfg], tag + "_rec")
    t = rec["result"]["transactions"][0]
    inv1 = inventory(cfg)
    passed = t["outcome"] == "CONFLICT" and data_view(inv1) == data_view(inv_k)
    record("U0A-5", "%s journal records DONE for a move the disk does not show" % kind,
           "PASS" if passed else "FAIL", recovery=t, data_unchanged=data_view(inv1) == data_view(inv_k))
    # (e) interruption during the activation's own rollback (triggered by a destination occupant)
    tag = "u0a5_%s_activation_rollback_kill" % kind
    cfg, src = new_install(tag, kind)
    inv0 = inventory(cfg)
    last = [m["i"] for m in plan if m["role"] == "S1"][0]
    box = {}

    def occupy(cfg=cfg, box=box):
        lay = proto.Layout(cfg)
        txid = os.listdir(lay.txroot)[0]
        p = lay.slot(txid, *proto.make_plan(json.load(open(os.path.join(lay.txdir(txid), "intent.json"))))[last]["dst"])
        box["p"] = p
        return racer("create", p)
    run = run_proto(activate_args(cfg, kind, src if kind == "replace" else None), tag,
                    stops=["act_begin_forward_%d" % last], actions={"act_begin_forward_%d" % last: occupy},
                    kill_at="actrb_done_rollback_%d" % (last - 1))
    inv_k = inventory(cfg)
    rec = run_proto(["recover", cfg], tag + "_rec")
    t = rec["result"]["transactions"][0]
    inv1 = inventory(cfg)
    occ_ok = b"UNEXPECTED" in open(box["p"], "rb").read()
    # the occupant sits in the authority dir -> recovery must refuse (unfamiliar content), preserving all
    lost = sorted(shas(inv0) - shas(inv1) - {None})
    rec2 = run_proto(["recover", cfg], tag + "_rec2")
    passed = (run.get("killed_at") is not None and occ_ok and not lost and t["outcome"] in ("CONFLICT", "ROLLED_BACK")
              and inventory(cfg) == inv1)
    record("U0A-5", "%s activation rollback interrupted, then recovered twice" % kind, "PASS" if passed else "FAIL",
           killed_at=run.get("killed_at"), recovery=t, second_recovery=rec2["result"]["transactions"],
           occupant_preserved=occ_ok, lost_sha256=lost, inventory_after_kill=inv_k, inventory_after=inv1)
    # after the operator removes the occupant (preserved elsewhere), recovery completes the rollback
    os.rename(box["p"], os.path.join(CASES, tag, "operator_saved_occupant"))
    rec3 = run_proto(["recover", cfg], tag + "_rec3")
    t3 = rec3["result"]["transactions"][0]
    ok3 = t3["outcome"] in ("ROLLED_BACK", "TERMINAL") and state_equals(cfg, inv0)
    record("U0A-5", "%s ...after occupant set aside by operator: recovery finishes rollback" % kind,
           "PASS" if ok3 else ("PASS" if t3["outcome"] == "CONFLICT" and not (shas(inv0) - shas(inventory(cfg)) - {None}) else "FAIL"),
           recovery=t3, old_state_verified=state_equals(cfg, inv0))


# ================================================================= U0A-6 failure cases
def u0a_6():
    def simple(tag, kind="rebuild", stops=(), actions=None, inject=None, cfg=None, src=None, expect=("ABANDONED",),
               title=None, extra_check=None, actor_changes_active=False):
        if cfg is None:
            cfg, src = new_install(tag, kind)
        inv0 = inventory(cfg)
        args = activate_args(cfg, kind, src if kind == "replace" else None)
        if inject:
            args += ["--inject", inject]
        run = run_proto(args, tag, stops=stops, actions=actions)
        res = run["result"]
        inv1 = inventory(cfg)
        lost = sorted(shas(inv0) - shas(inv1) - {None})
        unchanged_active = state_equals(cfg, inv0)
        ok = res["outcome"] in expect and not lost
        if res["outcome"] in ("ABANDONED", "REFUSED", "ROLLED_BACK") and not actor_changes_active:
            ok = ok and unchanged_active
        if extra_check:
            ok = ok and extra_check(cfg, res)
        record("U0A-6", title or tag, "PASS" if ok else "FAIL", outcome=res["outcome"], message=res.get("message"),
               details=res.get("details"), forward_failure=res.get("forward_failure"),
               active_files_unchanged=unchanged_active, lost_sha256=lost,
               events=[e for e in run["events"] if isinstance(e, dict)], run=tag)
        return cfg, res

    # access denied: DELETE denied on the old sidecar -> protection fails before any move
    tag = "u0a6_deny_delete_sidecar"
    cfg, src = new_install(tag, "rebuild")
    auth = os.path.join(cfg, "sfm_shared_authority")
    sc = os.path.join(auth, [n for n in os.listdir(auth) if n.endswith(".sfmsidecar")][0])
    icacls(sc, "/deny", "%s:(DE)" % USER)
    icacls(auth, "/deny", "%s:(DC)" % USER)
    simple(tag, cfg=cfg, src=src, title="6a access denied: DELETE denied on old sidecar (file DE + dir DC)")
    icacls(auth, "/remove:d", USER)
    icacls(sc, "/remove:d", USER)
    # access denied mid-transaction: file creation denied in the authority directory
    tag = "u0a6_deny_add_file_auth"
    cfg, src = new_install(tag, "rebuild")
    auth = os.path.join(cfg, "sfm_shared_authority")
    icacls(auth, "/deny", "%s:(WD)" % USER)
    inv0 = inventory(cfg)
    c, res = simple(tag, cfg=cfg, src=src, expect=("CONFLICT", "ROLLED_BACK"),
                    title="6b access denied on rename into authority dir mid-transaction")
    icacls(auth, "/remove:d", USER)
    rec = run_proto(["recover", cfg], tag + "_rec_after_acl_restored")
    t = rec["result"]["transactions"][0]
    iv_old = state_equals(cfg, inv0)
    iv_new = independent_verify(cfg, TXT_B)["ok"]
    record("U0A-6", "6b ...after permission restored: recovery", "PASS" if (t["outcome"] in ("ROLLED_BACK", "COMPLETE", "TERMINAL") and (iv_old or iv_new)) else "FAIL",
           recovery=t, old_state=iv_old, new_state=iv_new)
    # sharing violation: Normalizer-style reader (GENERIC_READ, share READ) holds the Master
    tag = "u0a6_sharing_master_reader"
    cfg, src = new_install(tag, "rebuild")
    H = Holder("hold", os.path.join(cfg, proto.MASTER_NAME), "1", "r")
    simple(tag, cfg=cfg, src=src, title="6c sharing violation: Normalizer-style read handle on Master")
    H.release()
    tag = "u0a6_sharing_sidecar_fullshare_reader"
    cfg, src = new_install(tag, "rebuild")
    auth = os.path.join(cfg, "sfm_shared_authority")
    H = Holder("hold", os.path.join(auth, [n for n in os.listdir(auth) if n.endswith(".sfmsidecar")][0]), "7", "r")
    simple(tag, cfg=cfg, src=src, title="6d sharing violation: full-sharing reader on old sidecar")
    H.release()
    # missing source
    tag = "u0a6_missing_old_sidecar"
    cfg, src = new_install(tag, "rebuild")
    auth = os.path.join(cfg, "sfm_shared_authority")
    scp = os.path.join(auth, [n for n in os.listdir(auth) if n.endswith(".sfmsidecar")][0])
    simple(tag, cfg=cfg, src=src, stops=["snapshots_written"],
           actions={"snapshots_written": lambda: racer("rename", scp, os.path.join(CASES, tag, "moved_away.sfmsidecar"))},
           title="6e missing source: old sidecar moved away before protection",
           expect=("ABANDONED",), actor_changes_active=True)
    tag = "u0a6_missing_candidate"
    cfg, src = new_install(tag, "rebuild")

    def kill_cand(cfg=cfg, tag=tag):
        lay = proto.Layout(cfg)
        txid = os.listdir(lay.txroot)[0]
        cd = os.path.join(lay.txdir(txid), "candidate")
        n = [x for x in os.listdir(cd) if x.endswith(".sfmsidecar")][0]
        return racer("rename", os.path.join(cd, n), os.path.join(CASES, tag, "moved_away_candidate"))
    simple(tag, cfg=cfg, src=src, stops=["snapshots_written"], actions={"snapshots_written": kill_cand},
           title="6f missing source: candidate sidecar removed before protection")
    # write interruption / insufficient space (simulated)
    simple("u0a6_disk_full_simulated", inject="candidate_write_error=112",
           title="6g candidate write fails ERROR_DISK_FULL (SIMULATED injection)")
    # unexpected files
    tag = "u0a6_unfamiliar_publisher_lock"
    cfg = make_case(tag, master=TXT_B, extra_auth=("publisher.lock",))
    simple(tag, cfg=cfg, expect=("REFUSED",), title="6h unfamiliar pre-existing file in authority dir (publisher.lock)")
    tag = "u0a6_unexpected_sidecar_during_protection"
    cfg, src = new_install(tag, "rebuild")
    stranger = os.path.join(cfg, "sfm_shared_authority",
                            "sfm_master_v1_%s.sfmsidecar" % ("0" * 64))
    simple(tag, cfg=cfg, src=src, stops=["moves_done"], actions={"moves_done": lambda: racer("create", stranger)},
           expect=("CONFLICT",), title="6i unexpected sidecar created in authority dir during the transaction",
           extra_check=lambda c, r: os.path.exists(stranger))
    # malformed journal / unknown schema (after a mid-transaction kill)
    for variant in ("flip_byte_middle", "torn_tail", "unknown_intent_schema", "unknown_journal_schema",
                    "intent_traversal_name"):
        tag = "u0a6_journal_%s" % variant
        cfg, src = new_install(tag, "rebuild")
        run_proto(activate_args(cfg), tag, kill_at="act_done_forward_1")
        lay = proto.Layout(cfg)
        txid = os.listdir(lay.txroot)[0]
        jp = os.path.join(lay.txdir(txid), "journal")
        ip = os.path.join(lay.txdir(txid), "intent.json")
        data = open(jp, "rb").read()
        if variant == "flip_byte_middle":
            lines = data.split(b"\n")
            lines[2] = lines[2].replace(b'"t":"', b'"t":"X', 1)
            open(jp, "wb").write(b"\n".join(lines))
        elif variant == "torn_tail":
            open(jp, "wb").write(data[:-25])
        elif variant == "unknown_intent_schema":
            it = json.load(open(ip))
            it["schema"] = "u0a-tx-99"
            open(ip, "w").write(json.dumps(it))
        elif variant == "unknown_journal_schema":
            lines = data.split(b"\n")
            body = lines[0].split(b"\t")[0].replace(proto.SCHEMA.encode(), b"u0a-tx-99")
            lines[0] = body + b"\t" + sha(body).encode()
            open(jp, "wb").write(b"\n".join(lines))
        elif variant == "intent_traversal_name":
            it = json.load(open(ip))
            it["new"]["sidecar"] = "..\\..\\..\\escaped.txt"
            open(ip, "w").write(json.dumps(it))
        inv_k = inventory(cfg)
        rec = run_proto(["recover", cfg], tag + "_rec")
        t = rec["result"]["transactions"][0]
        inv1 = inventory(cfg)
        if variant == "torn_tail":
            ok = t["outcome"] in ("COMPLETE",) and independent_verify(cfg, TXT_B)["ok"]
        else:
            ok = t["outcome"] in ("CONFLICT", "REFUSED") and {k: v for k, v in inv1.items() if not k.endswith("journal")} == \
                {k: v for k, v in inv_k.items() if not k.endswith("journal")}
        record("U0A-6", "6j journal/intent %s -> recovery" % variant, "PASS" if ok else "FAIL",
               recovery=t, nonjournal_files_unchanged=ok)
    # identity mismatch: Master replaced by identical bytes (new file id) between preview and protection
    tag = "u0a6_identity_master_swapped_same_bytes"
    cfg, src = new_install(tag, "rebuild")
    mp = os.path.join(cfg, proto.MASTER_NAME)

    def swap(mp=mp):
        tmp = mp + ".swap"
        shutil.copyfile(mp, tmp)
        return _swap(mp, tmp)
    simple(tag, cfg=cfg, src=src, stops=["snapshots_written"], actions={"snapshots_written": swap},
           title="6k identity mismatch: Master replaced by identical bytes before protection")
    tag = "u0a6_identity_auth_dir_swapped"
    cfg, src = new_install(tag, "rebuild")
    auth = os.path.join(cfg, "sfm_shared_authority")

    def swapdir(auth=auth):
        os.rename(auth, auth + "_original")
        shutil.copytree(auth + "_original", auth)
        return {"swapped": True}
    cfgx, resx = simple(tag, cfg=cfg, src=src, stops=["snapshots_written"], actions={"snapshots_written": swapdir},
                        expect=("ABANDONED",), title="6l identity mismatch: authority directory swapped for a copy")
    tag = "u0a6_hardlinked_master"
    cfg, src = new_install(tag, "rebuild")
    os.link(os.path.join(cfg, proto.MASTER_NAME), os.path.join(CASES, tag, "hardlink_to_master.txt"))
    simple(tag, cfg=cfg, src=src, expect=("REFUSED",), title="6m hard-linked Master (alias) refused")
    # reparse alias inside the managed slot: authority directory replaced by a junction
    tag = "u0a6_junction_authority_dir"
    cfg, src = new_install(tag, "rebuild")
    auth = os.path.join(cfg, "sfm_shared_authority")
    real = os.path.join(CASES, tag, "elsewhere_authority")
    os.rename(auth, real)
    subprocess.run(["cmd", "/c", "mklink", "/J", auth, real], capture_output=True)
    inv0 = {n: sha(open(os.path.join(real, n), "rb").read()) for n in os.listdir(real)}
    run = run_proto(activate_args(cfg), tag)
    res = run["result"]
    inv1 = {n: sha(open(os.path.join(real, n), "rb").read()) for n in os.listdir(real)}
    record("U0A-6", "6n junction (reparse point) as the authority directory",
           "PASS" if res["outcome"] == "REFUSED" and inv0 == inv1 else "FAIL",
           outcome=res["outcome"], details=res.get("details"), target_dir_changed=inv0 != inv1)


def u0a_6_sfm():
    tag = "u0a6_sfm_running_refusal"
    cfg, src = new_install(tag, "rebuild")
    inv0 = inventory(cfg)
    args = activate_args(cfg)
    i = args.index("sfm_policy_record_only=1")
    del args[i - 1:i + 1]
    run = run_proto(args, tag)
    res = run["result"]
    if res.get("sfm_running_advisory") is True:
        ok = res["outcome"] == "ABANDONED" and state_equals(cfg, inv0)
        record("U0A-6", "6o advisory check: sfm.exe running -> activation refused", "PASS" if ok else "FAIL",
               outcome=res["outcome"], details=res.get("details"))
    else:
        record("U0A-6", "6o advisory check: sfm.exe running -> activation refused", "NOT RUN",
               reason="sfm.exe not running at test time", observed=res.get("sfm_running_advisory"))


def _swap(mp, tmp):
    ok, err = w32.move_file_ex(tmp, mp, w32.MOVEFILE_REPLACE_EXISTING)
    return {"ok": ok, "error": None if ok else w32.ename(err)}


# ================================================================= main
def main():
    iso = isolation_check()
    print("isolation", json.dumps(iso))
    if not iso["PASS"]:
        raise SystemExit("isolation check failed; nothing written")
    os.makedirs(CASES)
    os.makedirs(os.path.join(EVID, "runs"))
    fp0 = fingerprint()
    t0 = time.time()
    for fn in (u0a_1, u0a_2, u0a_3, u0a_4, u0a_5, u0a_6, u0a_6_sfm):
        try:
            fn()
        except Exception as e:  # a harness crash is recorded, never silently skipped
            import traceback
            record(fn.__name__.upper().replace("_", "-"), "HARNESS ERROR", "INCONCLUSIVE",
                   error=traceback.format_exc())
    fp1 = fingerprint()
    import winreg
    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem")
        long_paths = winreg.QueryValueEx(k, "LongPathsEnabled")[0]
    except OSError:
        long_paths = None
    maxlen = max(len(os.path.join(dp, f)) for dp, dn, fn in os.walk(ROOT) for f in fn)
    summary = {"isolation": iso, "production_fingerprint_unchanged": fp0 == fp1,
               "production_fingerprint_entries": len(fp0),
               "production_watch_locations": len(PROD_FILES), "elapsed_s": round(time.time() - t0, 1),
               "python": sys.version, "windows": list(sys.getwindowsversion()[:3]),
               "long_paths_enabled": long_paths, "max_test_path_length": maxlen,
               "test_root_length": len(ROOT),
               "counts": {}}
    for r in RESULTS:
        summary["counts"].setdefault(r["test"], {}).setdefault(r["verdict"], 0)
        summary["counts"][r["test"]][r["verdict"]] += 1
    json.dump({"summary": summary, "results": RESULTS}, open(os.path.join(EVID, "u0a_results.json"), "w"),
              indent=1, default=str)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
