# -*- coding: utf-8 -*-
"""
Offline, real-Python-2.7.5 empirical test supporting the F1-1 static
object-lifetime/reachability audit.

This test does NOT execute the real production Normalizer (that requires the
real SFM/Qt environment and is out of scope for an offline test). It proves,
using a small SYNTHETIC stand-in, the GENERAL mechanism the audit relies on:

  Claim: F1's own harness pattern --
      prod_ns = {}
      exec(compile(production_source, "<production>", "exec"), prod_ns)
      ... use prod_ns ...
      # loop repeats: prod_ns = {} (reassignment, NOT explicit del + gc.collect())
  -- reassigns the name `prod_ns` each iteration, which frees any ACYCLIC
  garbage immediately via CPython refcounting, but does NOT guarantee
  collection of REFERENCE CYCLES (e.g. an instance whose bound method is
  stored as its own attribute, a very common shape for callback/handler
  objects) unless the cyclic garbage collector actually runs before the
  next iteration begins.

  F1's own script (Checkpoint_F1_Repeated_Warm_Use_Stability.py) calls
  gc.collect() exactly ONCE, in its finalize section, AFTER all 4 commands
  complete -- never between commands. Production's own source
  (Rebuild_Control_Groups_Normalizer.py, module docstring) explicitly
  states "no gc.collect()" is used internally, by design. So nothing
  collects such cycles between F1's own 4 commands except CPython's
  automatic generation-threshold-triggered collection, which is not
  guaranteed to fire before the next command's own allocations begin.

This test measures, empirically, under the real embedded Python 2.7.5:
  (a) with automatic gc DISABLED and no manual collect() between iterations,
      cyclic garbage from repeated exec() calls accumulates (uncollected
      objects are still alive, reachable only via gc's own tracked-object
      list, not via any name in this script) until a collect() is finally
      called;
  (b) a single subsequent gc.collect() reclaims objects proportional to the
      NUMBER OF ITERATIONS that ran without collection, not just the last
      one -- demonstrating accumulation, not per-iteration cleanup;
  (c) calling gc.collect() after EVERY iteration (the F1-R1 fix) instead
      reclaims each iteration's cycle immediately, so nothing accumulates.

This supports, but does not by itself prove, that this exact mechanism
explains the real F1-1 SFM crash -- it demonstrates the mechanism exists and
is real under the actual interpreter F1 runs under. Whether it materially
contributed to the crash (vs. production/SFM's own per-command retention)
is exactly the question the F1-R1 diagnostic is designed to help attribute.
"""

import gc


CYCLE_SOURCE = (
    "class _Node(object):\n"
    "    def __init__(self):\n"
    "        self.payload = list(range(200))\n"
    "        self.callback = self.method\n"
    "    def method(self):\n"
    "        return self.payload\n"
    "_instance = _Node()\n"
)


def make_one_cycle_via_exec():
    ns = {}
    exec(compile(CYCLE_SOURCE, "<f1_audit_cycle_test>", "exec"), ns)
    return ns


def count_tracked_node_garbage():
    n = 0
    for obj in gc.get_objects():
        if type(obj).__name__ == "_Node":
            n += 1
    return n


def run_case_no_interim_collection(iterations):
    gc.disable()
    try:
        gc.collect()
        baseline = count_tracked_node_garbage()

        for _ in range(iterations):
            ns = make_one_cycle_via_exec()
            del ns

        before_final_collect = count_tracked_node_garbage()
        reclaimed = gc.collect()
        after_final_collect = count_tracked_node_garbage()

        return {
            "baseline_nodes": baseline,
            "nodes_alive_before_any_collect": before_final_collect - baseline,
            "objects_reclaimed_by_single_final_collect": reclaimed,
            "nodes_alive_after_final_collect": after_final_collect - baseline,
        }
    finally:
        gc.enable()


def run_case_collect_every_iteration(iterations):
    gc.disable()
    try:
        gc.collect()
        baseline = count_tracked_node_garbage()

        max_nodes_alive_at_any_point = 0
        for _ in range(iterations):
            ns = make_one_cycle_via_exec()
            del ns
            gc.collect()
            alive = count_tracked_node_garbage() - baseline
            if alive > max_nodes_alive_at_any_point:
                max_nodes_alive_at_any_point = alive

        return {
            "baseline_nodes": baseline,
            "max_nodes_alive_at_any_point_during_run": max_nodes_alive_at_any_point,
            "nodes_alive_after_run": count_tracked_node_garbage() - baseline,
        }
    finally:
        gc.enable()


def main():
    import sys

    print("Python version: %s" % (sys.version,))

    iterations = 4  # mirrors F1's own 4-command loop

    print("")
    print("Case A: no gc.collect() between iterations (F1-1's actual pattern)")
    result_a = run_case_no_interim_collection(iterations)
    for k in sorted(result_a):
        print("  %s = %r" % (k, result_a[k]))

    accumulation_proved = (
        result_a["nodes_alive_before_any_collect"] >= iterations
        and result_a["objects_reclaimed_by_single_final_collect"] >= iterations
        and result_a["nodes_alive_after_final_collect"] == 0
    )
    print("  ACCUMULATION_PROVED = %r" % (accumulation_proved,))

    print("")
    print(
        "Case B: gc.collect() after every iteration (the F1-R1 fix)"
    )
    result_b = run_case_collect_every_iteration(iterations)
    for k in sorted(result_b):
        print("  %s = %r" % (k, result_b[k]))

    no_accumulation_proved = (
        result_b["max_nodes_alive_at_any_point_during_run"] <= 1
        and result_b["nodes_alive_after_run"] == 0
    )
    print("  NO_ACCUMULATION_PROVED = %r" % (no_accumulation_proved,))

    print("")
    overall = accumulation_proved and no_accumulation_proved
    print("OVERALL_TEST_PASS = %r" % (overall,))
    return 0 if overall else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
