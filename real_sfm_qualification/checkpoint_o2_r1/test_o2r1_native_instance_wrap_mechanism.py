# -*- coding: utf-8 -*-
"""
Offline sanity check for Checkpoint O2-R1's corrected native-Rebuild
instrumentation approach.

O2's own class-level patch on `RebuildControlGroupsProductionRun.
prepare_native_callback` observed ZERO native calls because -- confirmed
by direct source reading this session -- exec()-ing the production
file's bytes does not merely DEFINE classes/functions: its own top-level
code SYNCHRONOUSLY constructs the run instance and performs one-time
command-level setup (including the real `self.rebuild` assignment)
BEFORE exec() itself returns control to the diagnostic script. A
class-level patch installed AFTER exec() returns is therefore installed
too late -- the one-and-only call to `prepare_native_callback` already
happened.

This test proves, using a SYNTHETIC source string shaped like that exact
pattern (a class whose __init__ sets a callable attribute, with
module-level top-level code that constructs an instance and calls a
setup method IMMEDIATELY, all inside the same exec()'d blob -- not the
real production source, which is already covered by the real-SFM run
and by direct source citation elsewhere), that O2-R1's fix works:

  1. A class-level patch installed AFTER exec() returns is indeed too
     late (reproducing O2's own bug for confirmation).
  2. Locating the already-constructed instance immediately after exec()
     returns (here: via a known namespace key, standing in for O2-R1's
     real main_window.findChildren()+objectName() lookup) and wrapping
     that INSTANCE's own attribute directly DOES correctly intercept
     later calls -- because a plain instance-attribute reassignment
     takes precedence over the class's own attribute by ordinary Python
     attribute-lookup rules.
"""
import sys

SYNTHETIC_SOURCE = """
class NativeCallable(object):
    def __call__(self, aset_ptr):
        return ("NATIVE_REBUILD_RESULT", aset_ptr)

class RunLike(object):
    def __init__(self):
        self.rebuild = None
        self.prepare_native_callback()

    def prepare_native_callback(self):
        # Mirrors production's own prepare_native_callback: this is the
        # ONE place self.rebuild is ever assigned.
        self.rebuild = NativeCallable()

# Mirrors production's own module-level, unconditional
# StartRebuildControlGroups() call: constructing the instance and
# running its one-time setup happens SYNCHRONOUSLY, as part of
# executing this source, before exec() ever returns.
run_instance = RunLike()

def run_target_transaction_like(instance, aset_ptr):
    # Mirrors the REAL per-target call site (line 11464 in production):
    # this is called later, from the Qt-deferred per-target loop -- in
    # this synthetic test, simply called after exec() returns.
    return instance.rebuild(aset_ptr)
"""

PASS_COUNT = [0]
FAIL_COUNT = [0]


def expect(condition, label, detail=None):
    if condition:
        PASS_COUNT[0] += 1
        sys.stdout.write("[PASS] %s%s\n" % (label, ("" if detail is None else " -- %r" % (detail,))))
    else:
        FAIL_COUNT[0] += 1
        sys.stdout.write("[FAIL] %s%s\n" % (label, ("" if detail is None else " -- %r" % (detail,))))


sys.stdout.write("--- Reproducing O2's own bug: class-level patch installed AFTER exec() is too late ---\n")

ns_broken = {}
exec(compile(SYNTHETIC_SOURCE, "<synthetic_o2_style>", "exec"), ns_broken)

# By this point (exec() already returned), the real assignment already
# happened -- confirm the instance's own self.rebuild is already the
# REAL (unwrapped) callable.
expect(
    type(ns_broken["run_instance"].rebuild).__name__ == "NativeCallable",
    "sanity.self_rebuild_is_already_set_by_the_time_exec_returns",
)

# Now install a CLASS-level patch on prepare_native_callback (O2's own
# original approach) -- too late, since it already ran once and will
# never run again for this instance.
RunLikeClass = ns_broken["RunLike"]
original_prepare = RunLikeClass.prepare_native_callback
class_patch_calls = []


def wrapped_prepare(self, *a, **kw):
    class_patch_calls.append(1)
    return original_prepare(self, *a, **kw)


RunLikeClass.prepare_native_callback = wrapped_prepare

# Call the per-target seam the same way production's own Qt-deferred
# loop eventually would.
result_broken = ns_broken["run_target_transaction_like"](ns_broken["run_instance"], 0xDEAD)

expect(class_patch_calls == [], "bug_reproduced.class_level_patch_on_prepare_native_callback_never_fires_again")
expect(
    result_broken == ("NATIVE_REBUILD_RESULT", 0xDEAD),
    "bug_reproduced.native_call_still_succeeds_but_via_the_UNWRAPPED_original_callable",
)


sys.stdout.write("\n--- O2-R1's fix: wrap the INSTANCE's own attribute immediately after exec() ---\n")

ns_fixed = {}
exec(compile(SYNTHETIC_SOURCE, "<synthetic_o2r1_style>", "exec"), ns_fixed)

# O2-R1's real script locates the instance via main_window.findChildren()
# + objectName()==RUN_LOCK_NAME; this synthetic test stands in for that
# lookup with a direct namespace-key fetch (the LOOKUP MECHANISM differs,
# but the decisive property under test -- instance-attribute patching
# after synchronous construction -- is identical).
located_instance = ns_fixed["run_instance"]
expect(located_instance is not None, "fix.instance_located_immediately_after_exec_returns")

instance_patch_calls = []
original_rebuild_fixed = located_instance.rebuild


def observed_rebuild(aset_ptr):
    instance_patch_calls.append(aset_ptr)
    return original_rebuild_fixed(aset_ptr)


located_instance.rebuild = observed_rebuild

result_fixed = ns_fixed["run_target_transaction_like"](located_instance, 0xBEEF)

expect(instance_patch_calls == [0xBEEF], "fix.instance_level_wrap_correctly_intercepts_the_later_call")
expect(
    result_fixed == ("NATIVE_REBUILD_RESULT", 0xBEEF),
    "fix.original_native_callable_still_invoked_with_the_same_argument_same_return_value",
)

# Confirm the instance-level attribute takes precedence over whatever
# the CLASS itself still says (mirrors "self.rebuild" always being an
# instance attribute, never shadowed by any class-level definition).
expect(
    located_instance.__dict__.get("rebuild") is observed_rebuild,
    "fix.wrapped_callable_lives_on_the_instance_dict_not_the_class",
)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
