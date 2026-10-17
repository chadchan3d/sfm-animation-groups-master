# -*- coding: utf-8 -*-
"""TEST-ONLY: acts as the legacy publisher's lock step, using the unchanged
tools/sfm_master_sidecar/publisher.py `_ExclusiveFileLock` (open "a+b" + msvcrt byte lock).
Ported from P1 legacy_pub.py aaa6eef8...

  legacy_pub.py hold <publisher.lock>   acquire, print HELD, wait for one stdin line, release
  legacy_pub.py try  <publisher.lock>   acquire with 1 s timeout, release; print JSON result
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(REPO, "tools"))
from sfm_master_sidecar import publisher  # noqa: E402


def main(op, path):
    lk = publisher._ExclusiveFileLock(path)
    try:
        lk.acquire(timeout=1.0 if op == "try" else 30.0)
    except Exception as e:
        print(json.dumps({"op": op, "acquired": False, "error": "%s: %s" % (type(e).__name__, e)}))
        sys.stdout.flush()
        return
    if op == "hold":
        print("HELD")
        sys.stdout.flush()
        sys.stdin.readline()
    lk.release()
    print(json.dumps({"op": op, "acquired": True, "size_after": os.path.getsize(path)}))
    sys.stdout.flush()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
