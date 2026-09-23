# -*- coding: utf-8 -*-
"""
Offline sanity check: does reassigning a module-level function name (or a
class method) INSIDE an exec()'d namespace dict, AFTER exec() but BEFORE
the function is ever called, actually affect subsequent calls made from
OTHER functions/methods defined in that SAME exec()'d source -- exactly
the technique Checkpoint O2's real-SFM diagnostic relies on to
observationally instrument discover_rig_context/capture_tree/
capture_snapshot_explicit/run_target_transaction/prepare_native_callback
without ever editing the production file.

This uses a SYNTHETIC source string shaped like the real pattern (a
module-level helper function called by an unqualified name from inside a
class method, all defined in one exec()'d blob), not the real production
source -- proving the general CPython name-resolution mechanism, not
re-deriving anything already confirmed by direct source reading of the
real file (see the O2 script's own docstring for those citations).
"""
import sys

SYNTHETIC_SOURCE = """
def helper(x):
    return ("ORIGINAL", x)

class Worker(object):
    def do_work(self, x):
        return helper(x)
"""

ns = {}
exec(compile(SYNTHETIC_SOURCE, "<synthetic>", "exec"), ns)

PASS_COUNT = [0]
FAIL_COUNT = [0]


def expect(condition, label, detail=None):
    if condition:
        PASS_COUNT[0] += 1
        sys.stdout.write("[PASS] %s%s\n" % (label, ("" if detail is None else " -- %r" % (detail,))))
    else:
        FAIL_COUNT[0] += 1
        sys.stdout.write("[FAIL] %s%s\n" % (label, ("" if detail is None else " -- %r" % (detail,))))


worker = ns["Worker"]()
before_patch = worker.do_work(5)
expect(before_patch == ("ORIGINAL", 5), "before_patch_calls_original_helper", before_patch)

original_helper = ns["helper"]
calls = []


def wrapped_helper(x):
    calls.append(x)
    result = original_helper(x)
    return ("WRAPPED",) + result


ns["helper"] = wrapped_helper

after_patch = worker.do_work(7)
expect(after_patch == ("WRAPPED", "ORIGINAL", 7), "after_patch_worker_uses_wrapped_helper_via_shared_globals", after_patch)
expect(calls == [7], "wrapper_recorded_exactly_the_one_call", calls)

# Also confirm class-METHOD patching (the run_target_transaction /
# prepare_native_callback pattern) works identically.
SYNTHETIC_SOURCE_2 = """
class Runner(object):
    def transact(self, x):
        return ("METHOD_ORIGINAL", x)
"""
ns2 = {}
exec(compile(SYNTHETIC_SOURCE_2, "<synthetic2>", "exec"), ns2)
RunnerClass = ns2["Runner"]
original_method = RunnerClass.transact
method_calls = []


def wrapped_method(self, x):
    method_calls.append(x)
    return ("METHOD_WRAPPED",) + original_method(self, x)


RunnerClass.transact = wrapped_method
runner_instance = RunnerClass()
method_result = runner_instance.transact(9)
expect(method_result == ("METHOD_WRAPPED", "METHOD_ORIGINAL", 9), "class_method_patch_works_identically", method_result)
expect(method_calls == [9], "method_wrapper_recorded_exactly_the_one_call", method_calls)

# Confirm patching happens PER-EXEC (i.e. re-exec'ing the same source into
# a FRESH namespace dict gives a fresh, unpatched copy) -- this is what
# lets O2 re-install its wrappers cleanly on command 2 without any
# leftover state from command 1's own patched namespace.
ns_fresh = {}
exec(compile(SYNTHETIC_SOURCE, "<synthetic_fresh>", "exec"), ns_fresh)
fresh_worker = ns_fresh["Worker"]()
fresh_result = fresh_worker.do_work(3)
expect(fresh_result == ("ORIGINAL", 3), "fresh_reexec_is_unpatched_independent_of_prior_command", fresh_result)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
