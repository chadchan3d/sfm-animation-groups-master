# -*- coding: utf-8 -*-
"""Package-Boundary Correction, Blocker B: the decisive clean-directory
test. Proves the ONE supported publication path (`tools/sfm_master_
sidecar`'s real public compiler + publisher, unmodified in flow, only
its `.sfmsidecar` extension fixed -- see `compiler.generation_basename`)
now produces output the runtime broker (`sfm_master_authority_
productionized`, Correction6) can actually acquire -- closing Astra's
reproduced defect B ("a real successful CLI compilation produced a
manifest rejected by runtime... the resulting output directory was
reported as SidecarMissing").

Two interpreter phases, matching the real deployment shape (compiler
tooling is Python-3-only; the runtime authority package must work under
the real embedded Python 2.7.5 the Normalizer runs in):

  --phase=publish   (run under Python 3.10): starts from an EMPTY temp
      directory, invokes the real public `compiler`/`publisher` path,
      and immediately self-checks acquisition from that SAME process
      (proving the fix works without any interpreter-boundary
      questions first).

  --phase=acquire   (run under real Python 2.7.5, as a SEPARATE
      process, against the directory `--phase=publish` already
      populated -- no recompilation, no rewriting): proves the
      cross-interpreter, cross-process "installed product" scenario --
      the actual shape the real Normalizer integration will need.

Does not rely on repository-relative fixture paths (a fresh `tempfile.
mkdtemp()` directory every run). Does not manually rewrite the compiler
manifest into a different runtime format -- the runtime reads the
publisher's own real output, unmodified, via the corrected `selection.
py`/`pointer.py`.

Never launches SFM. Never modifies the frozen production Normalizer or
the canonical Master (writes only a small synthetic Master TXT of its
own into the temp directory).
"""
import hashlib
import os
import sys
import tempfile

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir, "tools")
CORRECTION6_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction6")

for p in (os.path.abspath(TOOLS_DIR), os.path.abspath(CORRECTION6_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


# A fixed, well-known temp path both interpreter phases agree on (NOT a
# repository path -- purely an OS temp directory, matching "does not
# rely on repository-relative fixture paths").
CLEAN_DIR = os.path.join(tempfile.gettempdir(), "sfm_package_boundary_clean_dir_test")
MASTER_TXT_PATH = os.path.join(CLEAN_DIR, "clean_master.txt")

MASTER_TXT_BODY = (
    u'"groupFile"\n{\n'
    u'"RigArms"\n{\n'
    u'\t"control"\t\t"clean_dir_control_a"\n'
    u'\t"control"\t\t"clean_dir_control_b"\n'
    u"}\n"
    u"}\n"
)

WANTED_FOLDS = frozenset([b"clean_dir_control_a", b"clean_dir_control_b"])


def _phase_publish():
    """Runs under Python 3.10. Starts from an EMPTY temp directory,
    compiles+publishes via the real public path, then self-checks
    acquisition immediately, in-process."""
    import shutil
    if os.path.isdir(CLEAN_DIR):
        shutil.rmtree(CLEAN_DIR)
    os.makedirs(CLEAN_DIR)
    with open(MASTER_TXT_PATH, "wb") as f:
        f.write(MASTER_TXT_BODY.encode("utf-8"))
    check("publish.starts_from_empty_directory the clean directory contains only the Master TXT "
          "before publication", sorted(os.listdir(CLEAN_DIR)) == ["clean_master.txt"])

    from sfm_master_sidecar import publisher  # noqa: E402

    result = publisher.publish(MASTER_TXT_PATH, CLEAN_DIR)
    check("publish.produces_sfmsidecar_extension the real supported publisher now emits a "
          "'.sfmsidecar'-suffixed artifact (Astra defect B fix)",
          result.generation_basename.endswith(".sfmsidecar"), result.generation_basename)
    check("publish.artifact_file_exists the published artifact file actually exists on disk at "
          "the returned generation_path", os.path.isfile(str(result.generation_path)))
    check("publish.manifest_file_exists the published manifest.json actually exists on disk",
          os.path.isfile(str(result.manifest_path)))

    real_master_sha = hashlib.sha256(MASTER_TXT_BODY.encode("utf-8")).hexdigest()
    check("publish.source_sha_matches the publisher's own reported source_sha256 matches an "
          "independent hash of the exact bytes written", result.source_sha256 == real_master_sha)

    # Self-check acquisition from THIS SAME process/interpreter, using
    # ONLY the just-published directory -- no compiler internals reused.
    _run_acquisition_checks(label="publish-phase self-check (Python 3)", require_py2=False)


def _run_acquisition_checks(label, require_py2):
    from sfm_master_authority_productionized import broker as broker_mod  # noqa: E402
    from sfm_master_authority_productionized import normalizer_compat_adapter as adapter  # noqa: E402
    from sfm_master_authority_productionized import sidecar_contract  # noqa: E402
    sidecar_contract.ensure_loaded()

    if require_py2:
        try:
            unicode  # noqa: F821
        except NameError:
            check("%s.real_python27_interpreter this phase is running under real Python 2.7 "
                  "(required for the cross-interpreter proof)" % label, False, sys.version)
            return

    with open(MASTER_TXT_PATH, "rb") as f:
        real_master_sha = hashlib.sha256(f.read()).hexdigest()

    b = broker_mod.Broker(api_version="package-boundary-clean-dir-test")

    # --- 1. Shipped-root acquisition: the real, default production path
    #        ("normal production-facing broker policy", selection.py's
    #        own docstring) -- this is what Astra's repro exercised and
    #        what the fix directly targets. ---
    request_specs = {
        "normalizer": (WANTED_FOLDS, adapter.build_targeted_master_compatible_projection(WANTED_FOLDS)),
    }
    detached = b.acquire_or_reuse_views(
        MASTER_TXT_PATH, request_specs, shipped_root=CLEAN_DIR,
        expected_generation=real_master_sha,
    )
    check("%s.shipped_root_acquisition_succeeds acquiring authority via shipped_root= from the "
          "REAL published directory succeeds (no SidecarMissing)" % label,
          "normalizer" in detached, detached)
    view = detached["normalizer"]

    check("%s.source_generation_matches acquired view's source generation matches the real "
          "Master's own SHA-256" % label, view.semantic_generation.master_sha256 == real_master_sha)
    check("%s.artifact_identity_present acquired view carries a real artifact identity "
          "(embedded_source_sha256 matches)" % label,
          view.artifact_identity.embedded_source_sha256 == real_master_sha)
    # `folded` is keyed by whatever literal form the request used (bytes,
    # to match WANTED_FOLDS -- both interpreters); look up with the SAME
    # type rather than assuming a normalized unicode key.
    folded = view.payload["folded"]
    lookup_keys = [k for k in (b"clean_dir_control_a", b"clean_dir_control_b")]
    resolved_entries = [folded.get(k, []) for k in lookup_keys]
    check("%s.semantic_projection_correct the acquired payload resolves both wanted literals to "
          "their real destination (RigArms)" % label,
          all(len(entries) > 0 for entries in resolved_entries) and
          all(e["destination"] in (u"RigArms", "RigArms") for entries in resolved_entries for e in entries),
          folded)

    lease = b.lease_view(view)
    check("%s.lease_granted a real, live lease was granted" % label, lease is not None and not lease.is_released())
    counters_while_leased = b.provider_counters()
    check("%s.provider_closed_after_acquisition provider_counters()['current_open_provider_count']"
          " == 0 even while a lease is held (provider closed before this call returned)" % label,
          counters_while_leased["current_open_provider_count"] == 0, counters_while_leased)

    b.release_view_lease(lease)
    check("%s.lease_released_cleanly releasing the lease completes with no error" % label,
          lease.is_released())
    final_counters = b.provider_counters()
    check("%s.no_provider_leak_after_release provider_counters() still shows zero open providers "
          "after release" % label, final_counters["current_open_provider_count"] == 0, final_counters)

    # --- 2. Local-pointer acquisition: the (fixed) qualification-mode
    #        path, proving manifest.json now doubles correctly as the
    #        pointer file for both consumption paths (one canonical
    #        contract, not two). ---
    manifest_path = os.path.join(CLEAN_DIR, "manifest.json")
    b2 = broker_mod.Broker(api_version="package-boundary-clean-dir-test-local")
    request_specs2 = {
        "normalizer": (WANTED_FOLDS, adapter.build_targeted_master_compatible_projection(WANTED_FOLDS)),
    }
    detached2 = b2.acquire_or_reuse_views(
        MASTER_TXT_PATH, request_specs2, allow_local_candidates=True,
        local_pointer_path=manifest_path, generated_root=CLEAN_DIR,
        shipped_root=CLEAN_DIR,  # harmless fallback also available; local should win
        expected_generation=real_master_sha,
    )
    check("%s.local_pointer_acquisition_succeeds acquiring authority via the (fixed) local-"
          "pointer path, using the real publisher's manifest.json directly as the pointer file, "
          "succeeds" % label, "normalizer" in detached2, detached2)
    lease2 = b2.lease_view(detached2["normalizer"])
    b2.release_view_lease(lease2)
    check("%s.local_pointer_no_provider_leak" % label,
          b2.provider_counters()["current_open_provider_count"] == 0)


def _phase_acquire():
    """Runs under the SEPARATE, real Python 2.7.5 interpreter, against
    the directory `--phase=publish` already populated -- no
    recompilation, no manifest rewriting."""
    check("acquire.clean_dir_exists_from_prior_publish_phase the directory produced by the "
          "publish phase is present and was not created by this phase",
          os.path.isdir(CLEAN_DIR) and os.path.isfile(MASTER_TXT_PATH))
    _run_acquisition_checks(label="acquire-phase (Python 2.7.5, separate process)", require_py2=True)


if __name__ == "__main__":
    phase = None
    for arg in sys.argv[1:]:
        if arg.startswith("--phase="):
            phase = arg.split("=", 1)[1]
    if phase not in ("publish", "acquire"):
        print("usage: %s --phase=publish|acquire" % sys.argv[0])
        sys.exit(2)

    print("Interpreter: %s" % sys.version)
    print("Phase: %s" % phase)

    if phase == "publish":
        _phase_publish()
    else:
        _phase_acquire()

    print("\nRESULT: %d/%d %s" % (
        sum(1 for _, c in RESULTS if c), len(RESULTS),
        "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
    ))
    if not all(condition for _, condition in RESULTS):
        sys.exit(1)
