# -*- coding: utf-8 -*-
"""Independent-audit targeted correction -- BLOCKER B fixture builder.

Builds two REAL, genuinely compiled and self-validated Master+sidecar
pairs (Master A + sidecar A source-bound to A; Master B + sidecar B
source-bound to B), placed in the SAME shipped root, so a decisive
generation-binding test can prove: command pinned to A, current Master
is B, valid sidecar B IS available in the shipped root -- and the
acquisition must still reject specifically on generation mismatch, never
falling back to SidecarMissing (which would be true only if B's sidecar
did not exist).

Astra Narrow Issue E: every path here is derived from this file's own
on-disk location (`__file__`), never a hardcoded machine root -- this
script (and the fixtures it produces) work identically from any checkout
location, a fresh clone, or an extracted archive root. Python 3 only
(uses the production compiler/writer/reader pipeline, itself Python-3-
only).
"""
import hashlib
import json
import os
import shutil
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
# tests/sidecar/qualification/<this file> -> repo root is 3 levels up.
REPO_ROOT = os.path.normpath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
FIXROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction3", "fixtures_ab")

if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from sfm_master_sidecar import compiler  # noqa: E402

if os.path.isdir(FIXROOT):
    shutil.rmtree(FIXROOT)
os.makedirs(FIXROOT)

MANIFEST = {}


def build_and_validate(name, master_text):
    data = ('"groupFile"\n{\n' + master_text + '\n}\n').encode("utf-8")
    snapshot = compiler.SourceSnapshot(path="<synthetic:%s>" % name, data=data)
    outcome = compiler.parse_and_compile(snapshot)
    compiler.self_validate_from_bytes(outcome)

    master_path = os.path.join(FIXROOT, "%s_master.txt" % name)
    artifact_path = os.path.join(FIXROOT, "%s.sfmsidecar" % name)
    with open(master_path, "wb") as f:
        f.write(data)
    with open(artifact_path, "wb") as f:
        f.write(outcome.blob)

    master_sha = hashlib.sha256(data).hexdigest()
    artifact_sha = hashlib.sha256(outcome.blob).hexdigest()
    MANIFEST[name] = {
        "master_path": master_path, "artifact_path": artifact_path,
        "master_sha256": master_sha, "artifact_sha256": artifact_sha,
        "artifact_bytes": len(outcome.blob), "occurrence_count": len(outcome.result.occurrences),
    }
    print("[built] %-16s master_sha=%s artifact_sha=%s bytes=%d" % (
        name, master_sha[:16], artifact_sha[:16], len(outcome.blob)))
    return outcome


build_and_validate("generation_a", '\t"control"\t\t"left"\n\t"control"\t\t"right"\n\t"control"\t\t"GenerationAOnlyControl"')
build_and_validate("generation_b", '\t"control"\t\t"left"\n\t"control"\t\t"right"\n\t"control"\t\t"GenerationBOnlyControl"')

# Both artifacts placed in ONE shared shipped root -- BOTH remain
# discoverable simultaneously regardless of which Master content is
# currently live, which is exactly what a decisive A-vs-B generation
# test requires (Blocker B: "valid sidecar B, source-bound to B" must
# actually be present, not merely absent-and-defaulting-to-SidecarMissing).
SHARED_SHIPPED_ROOT = os.path.join(FIXROOT, "shipped_both")
os.makedirs(SHARED_SHIPPED_ROOT)
for name in ("generation_a", "generation_b"):
    shutil.copy(MANIFEST[name]["artifact_path"], os.path.join(SHARED_SHIPPED_ROOT, name + ".sfmsidecar"))
MANIFEST["shared_shipped_root"] = SHARED_SHIPPED_ROOT

with open(os.path.join(FIXROOT, "manifest.json"), "w") as f:
    json.dump(MANIFEST, f, indent=2, sort_keys=True)

print("\nFixture root:", FIXROOT)
print("Shared shipped root (both A and B artifacts always present):", SHARED_SHIPPED_ROOT)
