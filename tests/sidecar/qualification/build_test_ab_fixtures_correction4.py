# -*- coding: utf-8 -*-
"""Final targeted infrastructure correction -- BLOCKER 3.E fixture
builder (successor to build_test_ab_fixtures_correction3.py).

Builds the same two real, compiled, self-validated Master+sidecar pairs
(generation A, generation B, both in one shared shipped root) as the
Correction3 builder, but with two independent-re-audit fixes:

1. Writes pure-LF bytes (unchanged from Correction3 -- `\\n` only, never
   `\\r\\n`) AND relies on the repo's own `.gitattributes` rule
   (`tests/sidecar/qualification/candidate_b2c_correction*/fixtures_ab/
   *_master.txt text eol=lf`) so a future `git archive` of the commit
   containing these files reproduces these EXACT bytes -- without that
   attribute, `git archive`'s zip writer can mark a text-heuristic blob
   with a platform-text flag that some zip extractors then translate
   (LF -> CRLF) on extraction, which is exactly the archive/embedded-
   hash mismatch the independent re-audit reproduced for Correction3's
   own A/B fixtures.
2. The manifest (BLOCKER 3.E) now stores RELATIVE paths + semantic role
   + generation identity -- never an absolute execution path -- so a
   consumer resolves fixtures relative to the manifest's OWN directory,
   working correctly from any checkout location or extracted archive
   root.
"""
import hashlib
import json
import os
import shutil
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
FIXROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction4", "fixtures_ab")

if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from sfm_master_sidecar import compiler  # noqa: E402

if os.path.isdir(FIXROOT):
    shutil.rmtree(FIXROOT)
os.makedirs(FIXROOT)

MANIFEST = {}


def build_and_validate(name, master_text, generation_identity):
    data = ('"groupFile"\n{\n' + master_text + '\n}\n').encode("utf-8")
    assert b"\r" not in data, "fixture master text must be pure LF -- found a CR byte"
    snapshot = compiler.SourceSnapshot(path="<synthetic:%s>" % name, data=data)
    outcome = compiler.parse_and_compile(snapshot)
    compiler.self_validate_from_bytes(outcome)

    master_rel = "%s_master.txt" % name
    artifact_rel = "%s.sfmsidecar" % name
    with open(os.path.join(FIXROOT, master_rel), "wb") as f:
        f.write(data)
    with open(os.path.join(FIXROOT, artifact_rel), "wb") as f:
        f.write(outcome.blob)

    master_sha = hashlib.sha256(data).hexdigest()
    artifact_sha = hashlib.sha256(outcome.blob).hexdigest()
    MANIFEST[name] = {
        # BLOCKER 3.E: relative to THIS manifest's own directory (FIXROOT)
        # -- never an absolute path baked in at build time.
        "master_relative_path": master_rel,
        "artifact_relative_path": artifact_rel,
        "master_sha256": master_sha,
        "artifact_sha256": artifact_sha,
        "artifact_bytes": len(outcome.blob),
        "occurrence_count": len(outcome.result.occurrences),
        "semantic_role": name,
        "generation_identity": generation_identity,
    }
    print("[built] %-16s master_sha=%s artifact_sha=%s bytes=%d" % (
        name, master_sha[:16], artifact_sha[:16], len(outcome.blob)))
    return outcome


build_and_validate(
    "generation_a", '\t"control"\t\t"left"\n\t"control"\t\t"right"\n\t"control"\t\t"GenerationAOnlyControl"',
    generation_identity="A")
build_and_validate(
    "generation_b", '\t"control"\t\t"left"\n\t"control"\t\t"right"\n\t"control"\t\t"GenerationBOnlyControl"',
    generation_identity="B")

# Both artifacts placed in ONE shared shipped root -- BOTH remain
# discoverable simultaneously regardless of which Master content is
# currently live (Blocker B's own requirement, unchanged from Correction3).
SHARED_SHIPPED_ROOT_REL = "shipped_both"
os.makedirs(os.path.join(FIXROOT, SHARED_SHIPPED_ROOT_REL))
for name in ("generation_a", "generation_b"):
    shutil.copy(
        os.path.join(FIXROOT, MANIFEST[name]["artifact_relative_path"]),
        os.path.join(FIXROOT, SHARED_SHIPPED_ROOT_REL, name + ".sfmsidecar"),
    )
MANIFEST["shared_shipped_root_relative_path"] = SHARED_SHIPPED_ROOT_REL

with open(os.path.join(FIXROOT, "manifest.json"), "w") as f:
    json.dump(MANIFEST, f, indent=2, sort_keys=True)

print("\nFixture root:", FIXROOT)
print("Shared shipped root (relative):", SHARED_SHIPPED_ROOT_REL)
