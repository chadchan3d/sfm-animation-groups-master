# -*- coding: utf-8 -*-
"""The bounded worker entry point: one request in, exactly one JSON result out.

  python -m sfm_character_tools_updater.worker status           --installation CFG --result OUT
  python -m sfm_character_tools_updater.worker prepare-rebuild  --installation CFG --result OUT
  python -m sfm_character_tools_updater.worker prepare-import   --installation CFG --result OUT --source TXT
  python -m sfm_character_tools_updater.worker prepare-official --installation CFG --result OUT --package DIR
                                                                [--allow-older]
  python -m sfm_character_tools_updater.worker install          --installation CFG --result OUT
                                                                --prepared ID --confirm-sha SHA
                                                                [--accept-replacement]
  python -m sfm_character_tools_updater.worker recover          --installation CFG --result OUT
                                                                [--policy resume|rollback]

prepare-* commands map to the three primary actions (Rebuild My Data, Use Another TXT, Get
Official Data). They write only updater-private staging and may run while SFM is open. `install`
installs one prepared candidate through the one protected backend; it refuses while SFM is
running or its state is unknown. `--confirm-sha` is the destination TXT identity shown by the
preparation (consent is bound to it); `--accept-replacement` is required when the preparation
reports `consent_required`.

CFG is the installation's `usermod\\cfg` directory. The result file is created new (an
existing file is never overwritten); the last stdout line is `RESULT <outcome>`.

This is the backend's own entry point (R2 C5), not an alternate publisher.
"""
import argparse
import json
import sys
import traceback

from . import VERSION, backend, recovery
from .layout import Layout, resolve_installation
from .messages import MESSAGES, Stop

COMMANDS = ("status", "prepare-rebuild", "prepare-import", "prepare-official", "install", "recover")


def build_parser(commands=COMMANDS):
    p = argparse.ArgumentParser(prog="sfm_character_tools_updater.worker", allow_abbrev=False)
    p.add_argument("command", choices=commands)
    p.add_argument("--installation", required=True)
    p.add_argument("--result", required=True)
    p.add_argument("--prepared")
    p.add_argument("--confirm-sha")
    p.add_argument("--policy", default="resume", choices=("resume", "rollback"))
    p.add_argument("--source")
    p.add_argument("--package")
    p.add_argument("--allow-older", action="store_true")
    p.add_argument("--accept-replacement", action="store_true")
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
        return backend.prepare_rebuild(layout)
    if args.command == "prepare-import":
        if not args.source:
            raise Stop("REFUSED", "NOTHING", reason="prepare-import requires --source")
        return backend.prepare_import(layout, args.source)
    if args.command == "prepare-official":
        if not args.package:
            raise Stop("REFUSED", "NOTHING", reason="prepare-official requires --package")
        return backend.prepare_official(layout, args.package, args.allow_older)
    if args.command == "install":
        if not args.prepared or not args.confirm_sha:
            raise Stop("REFUSED", "NOTHING", reason="install requires --prepared and --confirm-sha")
        return backend.install(layout, args.prepared, args.confirm_sha, args.accept_replacement)
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
