# -*- coding: utf-8 -*-
"""TEST-ONLY: runs the SHIPPING worker unchanged (no test seam is set) under a Python audit hook
that records every name lookup and socket connection attempt. Never shipped.

  net_audit.py NETLOG <worker arguments...>

NETLOG is created new and receives a JSON list of [event, detail] entries.
"""
import json
import os
import runpy
import sys

UPDATER = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVENTS = []


def hook(event, args):
    if event == "socket.getaddrinfo":
        EVENTS.append([event, "%s:%s" % (args[0], args[1])])
    elif event == "socket.connect":
        EVENTS.append([event, repr(args[1])])


def main():
    log_path, rest = sys.argv[1], sys.argv[2:]
    sys.path.insert(0, UPDATER)
    sys.addaudithook(hook)
    sys.argv = ["sfm_character_tools_updater.worker"] + rest
    try:
        runpy.run_module("sfm_character_tools_updater.worker", run_name="__main__", alter_sys=True)
    except SystemExit as e:
        code = e.code
    else:
        code = 0
    with open(log_path, "x", encoding="utf-8") as f:
        json.dump(EVENTS, f)
    sys.exit(code)


if __name__ == "__main__":
    main()
