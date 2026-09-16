# -*- coding: utf-8 -*-
"""R3-B2C-B plumbing: deterministically stages the B2C-A candidate
authority package (authored/reviewed at sfm_master_authority_
productionized/) into a correctly-named sibling directory,
sfm_master_authority/, so it can be imported as `sfm_master_authority`
-- required by runtime.py's own canonical-module-name self-check
(`__name__ == "sfm_master_authority.runtime"`), which a differently
named directory can never satisfy.

This replaces the earlier B2C-A session-scratchpad staging copy with an
in-repo, reviewable, reproducible one. The SOURCE of truth for the
candidate authority code remains sfm_master_authority_productionized/
(never edited by this script); this script only ever copies FROM there
TO sfm_master_authority/, and only .py files (never .pyc/__pycache__).
Never touches the frozen production deploy package.

Run with either interpreter; takes no arguments; safe to re-run (each
run fully refreshes the staged copy from the current productionized
source).
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(HERE, "sfm_master_authority_productionized")
DEST_DIR = os.path.join(HERE, "sfm_master_authority")


def stage():
    if not os.path.isdir(SOURCE_DIR):
        raise RuntimeError("source directory missing: %r" % SOURCE_DIR)
    if not os.path.isdir(DEST_DIR):
        os.makedirs(DEST_DIR)

    copied = []
    for name in sorted(os.listdir(SOURCE_DIR)):
        if not name.endswith(".py"):
            continue
        src = os.path.join(SOURCE_DIR, name)
        dst = os.path.join(DEST_DIR, name)
        shutil.copyfile(src, dst)
        copied.append(name)

    # Remove any stale destination .py file that no longer exists in the
    # source, so DEST_DIR never silently retains an obsolete module.
    removed = []
    for name in sorted(os.listdir(DEST_DIR)):
        if name.endswith(".py") and name not in copied:
            os.remove(os.path.join(DEST_DIR, name))
            removed.append(name)

    pycache = os.path.join(DEST_DIR, "__pycache__")
    if os.path.isdir(pycache):
        shutil.rmtree(pycache)

    return copied, removed


if __name__ == "__main__":
    copied, removed = stage()
    print("Staged %d files into %s" % (len(copied), DEST_DIR))
    for name in copied:
        print("  %s" % name)
    if removed:
        print("Removed %d stale file(s):" % len(removed))
        for name in removed:
            print("  %s" % name)
