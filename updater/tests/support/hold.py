# -*- coding: utf-8 -*-
"""TEST-ONLY: hold one file open with an exact access mask / share mode until one stdin line
(ported from P1 hold.py 382f453a...).

  hold.py PATH ACCESS SHARE     ACCESS: r | rd (GENERIC_READ|DELETE) ; SHARE: integer
Prints one JSON line ({"held": true, ...} or the error), then waits.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sfm_character_tools_updater import w32  # noqa: E402


def main(path, access, share):
    acc = {"r": w32.GENERIC_READ, "rd": w32.GENERIC_READ | w32.DELETE}[access]
    h, err = w32.create_file(path, acc, int(share), w32.OPEN_EXISTING)
    if h is None:
        print(json.dumps({"held": False, "error": w32.ename(err)}))
        sys.stdout.flush()
        return
    print(json.dumps({"held": True, "access": access, "share": int(share)}))
    sys.stdout.flush()
    sys.stdin.readline()
    w32.close(h)


if __name__ == "__main__":
    main(*sys.argv[1:4])
