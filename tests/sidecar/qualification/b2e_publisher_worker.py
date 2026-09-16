# -*- coding: utf-8 -*-
"""Real subprocess worker for R3-B2E concurrent-publisher tests. Invoked
as: python publisher_worker.py <source_path> <output_dir> <slot_identity>
[--hold-seconds N] [--result-path P]. Writes a small JSON result file
describing what happened (never relies on stdout, which a crashing
process might not flush)."""
import json
import sys

sys.path.insert(0, r"E:\SFM Animation Group Master\tools")
from sfm_master_sidecar import mutex_publisher


def main():
    args = sys.argv[1:]
    source_path = args[0]
    output_dir = args[1]
    slot_identity = args[2]
    hold_seconds = 0.0
    result_path = None
    crash_after_acquire = False
    i = 3
    while i < len(args):
        if args[i] == "--hold-seconds":
            hold_seconds = float(args[i + 1])
            i += 2
        elif args[i] == "--result-path":
            result_path = args[i + 1]
            i += 2
        elif args[i] == "--crash-after-acquire":
            crash_after_acquire = True
            i += 1
        else:
            i += 1

    outcome = {"ok": False}
    hook_state = {}

    def _hook(stage):
        if stage == "before_manifest_replace" and hold_seconds > 0:
            import time
            time.sleep(hold_seconds)
        if stage == "before_manifest_replace" and crash_after_acquire:
            import os
            if result_path:
                with open(result_path, "w") as f:
                    json.dump({"ok": False, "crashed_while_holding_mutex": True}, f)
            os._exit(7)

    try:
        result = mutex_publisher.publish(
            source_path, output_dir, mutex_slot_identity=slot_identity, _fault_hook=_hook,
        )
        outcome = {
            "ok": True,
            "generation_basename": result.generation_basename,
            "reused": result.reused,
            "ordinary_sha256": result.ordinary_sha256,
            "mutex_outcome_kind": result.mutex_outcome_kind,
        }
    except Exception as exc:
        outcome = {"ok": False, "exception_type": type(exc).__name__, "exception_str": str(exc)}

    if result_path:
        with open(result_path, "w") as f:
            json.dump(outcome, f)
    print(json.dumps(outcome))


if __name__ == "__main__":
    main()
