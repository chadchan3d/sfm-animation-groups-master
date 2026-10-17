# -*- coding: utf-8 -*-
"""TEST-ONLY read-only fingerprints (ported from P1/C1 p1common.live_fingerprint and
footprint_snapshot.py). Nothing here writes to the SFM installation: files are read with
plain shared reads, never locked exclusively.

  fingerprint.py live <game_dir> <p0_inventory.json> <out.json>
      Master + every authority file (SHA-256), the authority and cfg listings, the P0-inventoried
      usermod\\scripts closure, gameinfo.txt; compared with the P1 pins.
  fingerprint.py footprint <out.json> <dir> [<dir> ...]
      Top-level listing (name, type, mtime, size) of each directory.
"""
import datetime
import hashlib
import json
import os
import sys

LIVE_PINS = {
    "sfm_defaultanimationgroups.txt": "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93",
    "manifest.json": "d810d6486305a098d4855eea15f6feea3dc7fe7f7aaf97a08415fcac8e7701d6",
    "publisher.lock": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "sfm_master_0_bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b.sfmsidecar":
        "bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b",
}


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def stamp(t):
    return datetime.datetime.utcfromtimestamp(t).isoformat() + "Z"


def live(game, inventory):
    cfg = os.path.join(game, "usermod", "cfg")
    auth = os.path.join(cfg, "sfm_shared_authority")
    inv = json.load(open(inventory, encoding="utf-8"))
    fp = {"utc": datetime.datetime.utcnow().isoformat() + "Z", "authority": {}, "closure_mismatches": [],
          "closure_count": 0}
    fp["authority"]["sfm_defaultanimationgroups.txt"] = sha_file(os.path.join(cfg, "sfm_defaultanimationgroups.txt"))
    fp["authority_listing"] = sorted(os.listdir(auth))
    for n in fp["authority_listing"]:
        fp["authority"][n] = sha_file(os.path.join(auth, n))
    base = os.path.join(game, "usermod", "scripts")
    for row in inv["scripts_closure_snapshot_2026-10-13T00Z"]:
        p = os.path.join(base, row["relpath_under_usermod_scripts"].replace("/", "\\"))
        fp["closure_count"] += 1
        try:
            h = sha_file(p)
        except OSError:
            h = None
        if h != row["sha256"]:
            fp["closure_mismatches"].append(row["relpath_under_usermod_scripts"])
    fp["gameinfo"] = sha_file(os.path.join(game, "usermod", "gameinfo.txt"))
    fp["cfg_listing"] = sorted(os.listdir(cfg))
    fp["updater_directory_present"] = os.path.exists(os.path.join(cfg, "sfm_character_tools_updater"))
    fp["authority_matches_pins"] = (fp["authority"] == LIVE_PINS)
    fp["gameinfo_matches_p0"] = fp["gameinfo"] == inv["gameinfo"]["sha256"]
    fp["ok"] = fp["authority_matches_pins"] and fp["gameinfo_matches_p0"] and not fp["closure_mismatches"] \
        and not fp["updater_directory_present"]
    return fp


def listing(d):
    out = []
    try:
        names = sorted(os.listdir(d))
    except OSError as e:
        return {"error": str(e)}
    for n in names:
        p = os.path.join(d, n)
        try:
            st = os.lstat(p)
            out.append({"name": n, "dir": os.path.isdir(p), "mtime": stamp(st.st_mtime), "size": st.st_size})
        except OSError as e:
            out.append({"name": n, "error": str(e)})
    return out


def main(argv):
    if argv[0] == "live":
        res, out = live(argv[1], argv[2]), argv[3]
    elif argv[0] == "footprint":
        out = argv[1]
        res = {"utc": datetime.datetime.utcnow().isoformat() + "Z", "dirs": {d: listing(d) for d in argv[2:]}}
    else:
        raise SystemExit("unknown mode")
    with open(out, "x", encoding="utf-8") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    print(argv[0], "ok=%s" % res.get("ok"))


if __name__ == "__main__":
    main(sys.argv[1:])
