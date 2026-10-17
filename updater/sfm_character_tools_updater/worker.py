# -*- coding: utf-8 -*-
"""The bounded worker entry point: one request in, exactly one JSON result out.

  python -m sfm_character_tools_updater.worker status          --installation CFG --result OUT
  python -m sfm_character_tools_updater.worker prepare-rebuild --installation CFG --result OUT
  python -m sfm_character_tools_updater.worker install         --installation CFG --result OUT
                                                               --prepared ID --confirm-sha SHA
  python -m sfm_character_tools_updater.worker recover         --installation CFG --result OUT
                                                               [--policy resume|rollback]

CFG is the installation's `usermod\\cfg` directory. The result file is created new (an
existing file is never overwritten); the last stdout line is `RESULT <outcome>`.

This is the backend's own entry point (R2 C5), not an alternate publisher. The replacement
route (Use Another TXT, Get Official Data) is not exposed in L-1.
"""
import argparse
import json
import sys
import traceback

from . import VERSION, backend, recovery
from .layout import Layout, resolve_installation
from .messages import MESSAGES, Stop

COMMANDS = ("status", "prepare-rebuild", "install", "recover")


def build_parser(commands=COMMANDS):
    p = argparse.ArgumentParser(prog="sfm_character_tools_updater.worker", allow_abbrev=False)
    p.add_argument("command", choices=commands)
    p.add_argument("--installation", required=True)
    p.add_argument("--result", required=True)
    p.add_argument("--prepared")
    p.add_argument("--confirm-sha")
    p.add_argument("--policy", default="resume", choices=("resume", "rollback"))
    return p


def dispatch(args, extra=None):
    real = resolve_installation(args.installation)
    layout = Layout(real)
    bad = layout.reparse_in_slots()
    if bad:
        raise Stop("REFUSED", "FOLDER_CHANGED", reason="reparse point inside managed slots", paths=bad)
    if extra and args.command in extra:
        return extra[args.command](layout, args)
    if args.command == "status":
        return backend.status(layout)
    if args.command == "prepare-rebuild":
        return backend.prepare(layout, "rebuild")
    if args.command == "install":
        if not args.prepared or not args.confirm_sha:
            raise Stop("REFUSED", "NOTHING", reason="install requires --prepared and --confirm-sha")
        return backend.install(layout, args.prepared, args.confirm_sha)
    if args.command == "recover":
        return recovery.recover(layout, args.policy)
    raise Stop("REFUSED", "NOTHING", reason="unknown command")


def run(args, extra=None):
    try:
        res = dispatch(args, extra)
    except Stop as e:
        res = {"operation": args.command, "outcome": e.outcome, "message": MESSAGES[e.message_key],
               "details": e.details}
    except Exception:
        res = {"operation": args.command, "outcome": "ERROR", "message": MESSAGES["ERROR"],
               "details": {"traceback": traceback.format_exc()}}
    res["updater_version"] = VERSION
    return res


def write_result(path, res):
    with open(path, "x", encoding="utf-8") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    sys.stdout.write("RESULT %s\n" % res.get("outcome"))
    sys.stdout.flush()


def main(argv=None):
    args = build_parser().parse_args(argv)
    write_result(args.result, run(args))


if __name__ == "__main__":
    main()
