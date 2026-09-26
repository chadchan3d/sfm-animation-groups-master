# -*- coding: utf-8 -*-
"""
Python-3-only smoke/regression test for I_Generation_Publisher.py --
the repo-side-only publisher/finalizer for roadmap item I.

CORRECTION ROUND 1 (2026-09-25, independent review): renamed from
test_i_generation_helper_publisher_py3.py (which tested functions that
have since moved out of I_Generation_Helper.py per BLOCKER 11) and
substantially expanded to cover BLOCKER 6 (exact G2 publication
record), BLOCKER 7 (semantic-parity counts + digest), BLOCKER 8/9
(mandatory restoration/finalization, usable even if I2 never began),
and BLOCKER 11 (explicit, validated repo-root discovery -- never a
relative-path guess).

CORRECTION ROUND 2 (2026-09-25, second independent review): the
publisher is now a two-phase design (R2 BLOCKER 1). This suite adds:
  - R2 BLOCKER 2: construct_and_write_g2_source() builds G2 itself, from
    exact canonical G1 bytes -- never a manually-supplied file.
  - R2 BLOCKER 7: write_g2_plan_record() writes an immutable plan record
    BEFORE any authority-directory write exists; publish_g2_with_record()
    re-derives everything fresh rather than trusting the plan blindly.
  - R2 BLOCKER 1 Phase B: activate_g2_master() -- the ONLY function that
    ever calls perform_g1_to_g2_replacement() -- documented G2 activation
    actually changes the live Master to G2; publication alone explicitly
    does NOT claim Master activation; activation is never attempted
    without a valid publication record.
  - R2 BLOCKER 5: path-binding adversarial tests (wrong Master path / wrong
    authority directory refuse before any write) for both
    activate_g2_master() and finalize_restoration().
  - R2 BLOCKER 8: a tampered publication record cannot authorize G2
    sidecar deletion during finalize_restoration().
  - Full-lifecycle recoverability: publication succeeds but activation
    fails remains fully recoverable via finalize_restoration(); no live
    Master mutation ever occurs without prior recoverable G2 identity
    evidence.

CORRECTION ROUND 3 (2026-09-25, third independent review): this suite
adds:
  - R3 BLOCKER 1: write_g2_plan_record() now also requires the I1
    baseline inventory and records baseline_master_path/
    baseline_authority_dir into the plan itself; publish_g2_with_record()
    refuses a wrong output_dir BEFORE publish_generation() ever runs,
    creating/modifying nothing there.
  - R3 BLOCKER 2: finalize_restoration() now takes an explicit
    plan_record parameter and can recover using ONLY the plan record
    (publication_record=None) -- covering both "the publication-record
    write itself failed" and "the publication record is simply absent
    after a partial Phase-A mutation."
  - R3 BLOCKER 3: finalize_restoration() independently re-derives G2
    identity as G1+LF rather than trusting publication_record's own
    claimed g2_source_sha256 -- a tampered publication record cannot
    prevent Master restoration, and (when plan+publication agree on the
    sidecar's own identity) does not by itself block authority cleanup
    either. When the two records DISAGREE on that identity, cleanup is
    refused outright (fail closed, never a guess).

Kept in its OWN file, separate from test_checkpoint_i_generation_
replacement_dryrun.py, because that suite's main body execs Checkpoint_
I_Generation_Replacement.py's own source text (Python-2-only builtins
throughout, matching SFM's embedded Python 2.7.5 runtime) and can never
itself run under Python 3. This file exercises the real,
accepted publisher under a REAL Python 3 interpreter.

Run under an ordinary Python 3 interpreter (never inside SFM):
  python test_i_generation_publisher_py3.py
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
CANONICAL_MASTER_CANDIDATE_PATH = os.path.join(REPO_ROOT, "sfm_defaultanimationgroups.txt")
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import I_Generation_Helper as igen  # noqa: E402
import I_Generation_Publisher as igpub  # noqa: E402

PASS_COUNT = [0]
FAIL_COUNT = [0]


def expect(condition, label):
    if condition:
        PASS_COUNT[0] += 1
        sys.stdout.write("[PASS] %s\n" % label)
    else:
        FAIL_COUNT[0] += 1
        sys.stdout.write("[FAIL] %s\n" % label)


expect(sys.version_info[0] >= 3, "sanity.running_under_python_3")

with open(CANONICAL_MASTER_CANDIDATE_PATH, "rb") as _f:
    _CANON_G1_BYTES = _f.read()
_CANON_G1_SHA = hashlib.sha256(_CANON_G1_BYTES).hexdigest()


def _setup_g1_source(tmp_dir):
    """Writes an on-disk copy of the real canonical G1 bytes, under an
    expected_g1_sha256 the tests can pin to (using the real canonical
    hash as `expected`, since g1_bytes ARE the real canonical bytes)."""
    g1_source_path = os.path.join(tmp_dir, "g1_source.txt")
    with open(g1_source_path, "wb") as f:
        f.write(_CANON_G1_BYTES)
    return g1_source_path, _CANON_G1_SHA


def _fake_baseline_inventory(master_path, authority_dir, master_sha256):
    """A minimal baseline-inventory dict for standalone plan-record tests
    that do not need a full igen.capture_live_state_inventory() (no real
    Master/authority files exist yet at this point in those tests) --
    only the three fields write_g2_plan_record()/path-binding checks
    actually read."""
    return {"master_path": master_path, "authority_dir": authority_dir, "master_sha256": master_sha256}


# =======================================================================
# BLOCKER 11 (round 1): explicit, validated repo root -- never a
# relative-path guess. Refuses cleanly against a wrong/fake root, and
# never even attempts an import in that case.
# =======================================================================
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    fake_root = os.path.join(tmp_dir, "not_a_real_repo")
    os.makedirs(fake_root)
    raised = False
    try:
        igpub.validate_repo_root(fake_root)
    except igpub.GenerationPublisherError:
        raised = True
    expect(raised, "blocker11.validate_repo_root_refuses_a_root_without_the_real_publisher_package")

    real_root_ok = igpub.validate_repo_root(REPO_ROOT)
    expect(real_root_ok == REPO_ROOT, "blocker11.validate_repo_root_accepts_the_real_repo_root")

    raised2 = False
    try:
        igpub.check_only_source(fake_root, CANONICAL_MASTER_CANDIDATE_PATH)
    except igpub.GenerationPublisherError:
        raised2 = True
    expect(raised2, "blocker11.check_only_source_refuses_a_wrong_repo_root_before_importing_anything")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# BLOCKER 7 (round 1): semantic counts + a stronger deterministic
# semantic digest, proving G1 and G2 are semantically identical despite
# different SHA.
# =======================================================================
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    g1_source_path, g1_sha = _setup_g1_source(tmp_dir)
    g2_bytes = igen.construct_g2_bytes(_CANON_G1_BYTES)
    g2_sha = hashlib.sha256(g2_bytes).hexdigest()
    g2_source_path = os.path.join(tmp_dir, "g2_source.txt")
    with open(g2_source_path, "wb") as f:
        f.write(g2_bytes)

    check_g1 = igpub.check_only_source(REPO_ROOT, g1_source_path)
    check_g2 = igpub.check_only_source(REPO_ROOT, g2_source_path)

    expect(check_g1["source_sha256"] == g1_sha, "sanity.check_only_g1_reports_correct_source_sha256")
    expect(check_g2["source_sha256"] == g2_sha, "sanity.check_only_g2_reports_correct_source_sha256")
    expect(check_g1["source_sha256"] != check_g2["source_sha256"], "blocker7.g1_and_g2_have_different_sha256")
    expect("counts" in check_g1 and "counts" in check_g2, "blocker7.check_only_source_returns_semantic_counts")
    expect("semantic_digest" in check_g1 and "semantic_digest" in check_g2, "blocker7.check_only_source_returns_a_semantic_digest")
    expect("ordinary_sha256" in check_g1 and "ordinary_sha256" in check_g2, "blocker7.check_only_source_returns_ordinary_sha256")

    parity = igpub.compare_semantic_parity(check_g1, check_g2)
    expect(parity["groups_equal"] is True, "blocker7.g1_g2_group_counts_equal")
    expect(parity["occurrences_equal"] is True, "blocker7.g1_g2_occurrence_counts_equal")
    expect(parity["folds_equal"] is True, "blocker7.g1_g2_fold_family_counts_equal")
    expect(parity["semantic_digest_equal"] is True, "blocker7.g1_g2_semantic_digest_equal")
    expect(parity["source_sha256_differs"] is True, "blocker7.g1_g2_source_sha256_still_differs")
    expect(parity["all_parity_checks_pass"] is True, "blocker7.overall_semantic_parity_confirmed")

    different_source_path = os.path.join(tmp_dir, "different_source.txt")
    with open(different_source_path, "wb") as f:
        f.write(_CANON_G1_BYTES.replace(b'"control"', b'"controlx"', 1) if b'"control"' in _CANON_G1_BYTES else _CANON_G1_BYTES + b"\n\n")
    try:
        check_different = igpub.check_only_source(REPO_ROOT, different_source_path)
        parity_negative = igpub.compare_semantic_parity(check_g1, check_different)
        expect(
            parity_negative["all_parity_checks_pass"] is False,
            "blocker7.a_genuinely_different_source_does_not_show_false_parity",
        )
    except Exception:
        expect(True, "blocker7.a_genuinely_different_source_does_not_show_false_parity")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# R2 BLOCKER 2: construct_and_write_g2_source() -- the repo-side
# preparation operation builds G2 ITSELF, from exact canonical G1 bytes.
# No manually-supplied G2 file is ever accepted for real qualification
# use again.
# =======================================================================
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    g1_source_path, g1_sha = _setup_g1_source(tmp_dir)
    g2_source_out = os.path.join(tmp_dir, "generated_g2.txt")

    facts = igpub.construct_and_write_g2_source(g1_source_path, g2_source_out, expected_g1_sha256=g1_sha)
    expect(os.path.isfile(g2_source_out), "r2blocker2.g2_source_file_actually_written")
    with open(g2_source_out, "rb") as f:
        written_g2_bytes = f.read()
    expect(
        igen.g2_bytes_are_exact_g1_plus_one_lf(_CANON_G1_BYTES, written_g2_bytes),
        "r2blocker2.generated_g2_is_exactly_g1_plus_one_lf",
    )
    expect(facts["g2_source_sha256"] == hashlib.sha256(written_g2_bytes).hexdigest(),
           "r2blocker2.returned_facts_report_correct_g2_sha256")
    expect(facts["g1_source_sha256"] == g1_sha, "r2blocker2.returned_facts_report_correct_g1_sha256")

    # No manual byte editing possible: the function refuses a G1 source
    # that does not match the expected hash, BEFORE writing anything.
    tampered_g1_path = os.path.join(tmp_dir, "tampered_g1.txt")
    with open(tampered_g1_path, "wb") as f:
        f.write(_CANON_G1_BYTES + b"X")
    raised = False
    try:
        igpub.construct_and_write_g2_source(tampered_g1_path, os.path.join(tmp_dir, "never_written.txt"), expected_g1_sha256=g1_sha)
    except igpub.GenerationPublisherError:
        raised = True
    expect(raised, "r2blocker2.refuses_a_g1_source_not_matching_expected_hash")
    expect(not os.path.exists(os.path.join(tmp_dir, "never_written.txt")),
           "r2blocker2.no_file_written_when_g1_hash_check_fails")

    # Refuses to overwrite an existing G2 source file (write-once).
    raised2 = False
    try:
        igpub.construct_and_write_g2_source(g1_source_path, g2_source_out, expected_g1_sha256=g1_sha)
    except igpub.GenerationPublisherError:
        raised2 = True
    expect(raised2, "r2blocker2.refuses_to_overwrite_an_existing_g2_source_file")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# R2/R3 BLOCKER 7/1: write_g2_plan_record() -- an immutable plan record
# written BEFORE any live authority mutation, now ALSO requiring the I1
# baseline inventory and recording its own baseline Master/authority
# paths into the plan (R3 BLOCKER 1). Every field independently
# derivable from check_only() alone, including the exact expected
# sidecar SHA-256 and generation basename -- provably correct once
# publication actually happens.
# =======================================================================
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    g1_source_path, g1_sha = _setup_g1_source(tmp_dir)
    g2_source_out = os.path.join(tmp_dir, "generated_g2.txt")
    igpub.construct_and_write_g2_source(g1_source_path, g2_source_out, expected_g1_sha256=g1_sha)

    plan_out = os.path.join(tmp_dir, "plan_record.json")
    authority_dir_not_yet_created = os.path.join(tmp_dir, "authority")
    fake_master_path = os.path.join(tmp_dir, "master.txt")
    baseline_inventory = _fake_baseline_inventory(fake_master_path, authority_dir_not_yet_created, g1_sha)

    plan = igpub.write_g2_plan_record(REPO_ROOT, g1_source_path, g2_source_out, plan_out, baseline_inventory,
                                       expected_g1_sha256=g1_sha)

    expect(not os.path.isdir(authority_dir_not_yet_created),
           "r2blocker7.plan_record_written_before_any_authority_directory_exists")
    for required_field in (
        "g1_source_path", "g1_source_sha256", "g2_source_path", "expected_g2_source_sha256",
        "expected_g2_source_byte_length", "expected_semantic_parity", "expected_sidecar_ordinary_sha256",
        "expected_generation_basename", "baseline_master_path", "baseline_authority_dir",
        "check_only_g1_result", "check_only_g2_result",
    ):
        expect(required_field in plan, "r2blocker7.plan_record_contains_%s" % required_field)
    expect(plan["expected_semantic_parity"]["all_parity_checks_pass"] is True,
           "r2blocker7.plan_record_records_confirmed_semantic_parity")
    expect(plan["baseline_master_path"] == fake_master_path,
           "r3blocker1.plan_record_records_baseline_master_path")
    expect(plan["baseline_authority_dir"] == authority_dir_not_yet_created,
           "r3blocker1.plan_record_records_baseline_authority_dir")
    expect(os.path.isfile(plan_out), "r2blocker7.plan_record_file_actually_written")

    # R3 BLOCKER 1: refuses to plan against a baseline whose own recorded
    # master_sha256 is not the expected canonical G1 -- never plan
    # against an untrusted baseline.
    bad_baseline = _fake_baseline_inventory(fake_master_path, authority_dir_not_yet_created, "0" * 64)
    raised0 = False
    try:
        igpub.write_g2_plan_record(REPO_ROOT, g1_source_path, g2_source_out, os.path.join(tmp_dir, "plan_badbaseline.json"),
                                    bad_baseline, expected_g1_sha256=g1_sha)
    except igpub.GenerationPublisherError:
        raised0 = True
    expect(raised0, "r3blocker1.write_g2_plan_record_refuses_a_baseline_not_matching_canonical_g1")

    # NOW actually publish, and confirm the plan's pre-derived facts were
    # exactly right (never a guess) -- the real published basename/
    # sidecar-sha match what the plan predicted before any write.
    output_dir = authority_dir_not_yet_created
    record_out = os.path.join(tmp_dir, "publication_record.json")
    record = igpub.publish_g2_with_record(REPO_ROOT, plan_out, output_dir, record_out, expected_g1_sha256=g1_sha)
    expect(record["g2_generation_basename"] == plan["expected_generation_basename"],
           "r2blocker7.plan_predicted_generation_basename_matches_real_publish")
    expect(record["g2_sidecar_sha256"] == plan["expected_sidecar_ordinary_sha256"],
           "r2blocker7.plan_predicted_sidecar_sha256_matches_real_publish")

    # Refuses to plan a G2 that is not exactly G1+LF.
    tampered_g2_path = os.path.join(tmp_dir, "tampered_g2.txt")
    with open(tampered_g2_path, "wb") as f:
        f.write(_CANON_G1_BYTES + b"\n\n")
    raised = False
    try:
        igpub.write_g2_plan_record(REPO_ROOT, g1_source_path, tampered_g2_path, os.path.join(tmp_dir, "plan2.json"),
                                    baseline_inventory, expected_g1_sha256=g1_sha)
    except igpub.GenerationPublisherError:
        raised = True
    expect(raised, "r2blocker7.refuses_to_plan_a_g2_source_not_exactly_g1_plus_one_lf")

    # publish_g2_with_record() re-derives everything fresh: if the G2
    # source drifts AFTER the plan was written, publication must refuse.
    plan_out_drift = os.path.join(tmp_dir, "plan_drift.json")
    g2_source_drift = os.path.join(tmp_dir, "g2_source_drift.txt")
    drift_authority_dir = os.path.join(tmp_dir, "authority_drift")
    drift_baseline = _fake_baseline_inventory(fake_master_path, drift_authority_dir, g1_sha)
    igpub.construct_and_write_g2_source(g1_source_path, g2_source_drift, expected_g1_sha256=g1_sha)
    igpub.write_g2_plan_record(REPO_ROOT, g1_source_path, g2_source_drift, plan_out_drift, drift_baseline, expected_g1_sha256=g1_sha)
    with open(g2_source_drift, "ab") as f:
        f.write(b"drifted")
    raised2 = False
    try:
        igpub.publish_g2_with_record(REPO_ROOT, plan_out_drift, drift_authority_dir,
                                      os.path.join(tmp_dir, "record_drift.json"), expected_g1_sha256=g1_sha)
    except igpub.GenerationPublisherError:
        raised2 = True
    expect(raised2, "r2blocker7.publish_refuses_when_g2_source_has_drifted_since_planning")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# R3 BLOCKER 1: Phase A publication is ITSELF a live mutation (it writes
# a sidecar and replaces manifest.json). A wrong output_dir must STOP
# before publish_generation() is ever permitted to run, creating or
# modifying nothing there, and leaving the real, plan-recorded baseline
# authority namespace untouched.
# =======================================================================
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    g1_source_path, g1_sha = _setup_g1_source(tmp_dir)
    g2_source_out = os.path.join(tmp_dir, "g2_source.txt")
    igpub.construct_and_write_g2_source(g1_source_path, g2_source_out, expected_g1_sha256=g1_sha)

    real_authority_dir = os.path.join(tmp_dir, "real_authority")
    fake_master_path = os.path.join(tmp_dir, "master.txt")
    baseline_inventory = _fake_baseline_inventory(fake_master_path, real_authority_dir, g1_sha)

    plan_out = os.path.join(tmp_dir, "plan.json")
    igpub.write_g2_plan_record(REPO_ROOT, g1_source_path, g2_source_out, plan_out, baseline_inventory,
                                expected_g1_sha256=g1_sha)

    wrong_output_dir = os.path.join(tmp_dir, "wrong_authority")
    record_out = os.path.join(tmp_dir, "record.json")
    raised = False
    try:
        igpub.publish_g2_with_record(REPO_ROOT, plan_out, wrong_output_dir, record_out, expected_g1_sha256=g1_sha)
    except igpub.GenerationPublisherError:
        raised = True
    expect(raised, "r3blocker1.publish_g2_with_record_refuses_a_wrong_output_dir")
    expect(not os.path.exists(wrong_output_dir),
           "r3blocker1.wrong_output_dir_has_nothing_created_or_modified_in_it")
    expect(not os.path.exists(real_authority_dir),
           "r3blocker1.the_real_plan_recorded_authority_namespace_is_untouched")
    expect(not os.path.exists(record_out),
           "r3blocker1.no_publication_record_written_when_output_dir_is_refused")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# BLOCKER 6 (round 1), updated for R2/R3: publish_g2_with_record() --
# the full immutable publication record with every required field, now
# consuming a baseline-bound plan record instead of raw source paths.
# =======================================================================
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    g1_source_path, g1_sha = _setup_g1_source(tmp_dir)
    g2_source_path = os.path.join(tmp_dir, "g2_source.txt")
    igpub.construct_and_write_g2_source(g1_source_path, g2_source_path, expected_g1_sha256=g1_sha)
    output_dir = os.path.join(tmp_dir, "authority")
    fake_master_path = os.path.join(tmp_dir, "master.txt")
    baseline_inventory = _fake_baseline_inventory(fake_master_path, output_dir, g1_sha)
    plan_out = os.path.join(tmp_dir, "plan_record.json")
    igpub.write_g2_plan_record(REPO_ROOT, g1_source_path, g2_source_path, plan_out, baseline_inventory,
                                expected_g1_sha256=g1_sha)

    record_out = os.path.join(tmp_dir, "publication_record.json")
    record = igpub.publish_g2_with_record(REPO_ROOT, plan_out, output_dir, record_out, expected_g1_sha256=g1_sha)

    g2_sha = hashlib.sha256(igen._read_bytes(g2_source_path)).hexdigest()
    for required_field in (
        "g1_source_sha256", "g2_source_sha256", "g2_source_byte_length", "g2_generation_basename",
        "g2_sidecar_sha256", "manifest_sha256_after_publication", "manifest_source_sha256",
        "manifest_generation_basename", "publish_result", "check_only_g1_result", "check_only_g2_result",
        "semantic_parity", "plan_record_path", "plan_record_sha256",
    ):
        expect(required_field in record, "blocker6.publication_record_contains_%s" % required_field)

    expect(record["g1_source_sha256"] == g1_sha, "blocker6.record_g1_source_sha256_correct")
    expect(record["g2_source_sha256"] == g2_sha, "blocker6.record_g2_source_sha256_correct")
    expect(record["manifest_source_sha256"] == g2_sha, "blocker6.record_manifest_source_sha256_equals_g2")
    expect(
        record["manifest_generation_basename"] == record["g2_generation_basename"],
        "blocker6.record_manifest_basename_matches_generation_basename",
    )
    sidecar_path = os.path.join(output_dir, record["g2_generation_basename"])
    expect(
        os.path.isfile(sidecar_path) and igen.sha256_file(sidecar_path) == record["g2_sidecar_sha256"],
        "blocker6.record_sidecar_sha256_matches_the_real_file_on_disk",
    )
    expect(
        igen.read_manifest_source_sha256_plain(output_dir) == g2_sha,
        "blocker6.dual_compatible_plain_reader_confirms_active_manifest_points_to_g2",
    )

    raised = False
    try:
        igpub.publish_g2_with_record(REPO_ROOT, plan_out, output_dir, record_out, expected_g1_sha256=g1_sha)
    except igpub.GenerationPublisherError:
        raised = True
    expect(raised, "blocker6.publish_g2_with_record_refuses_to_overwrite_an_existing_publication_record")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# prepare_and_publish_g2() -- Phase A end-to-end convenience wrapper.
# Documents that publication alone does NOT claim Master activation --
# no master_path argument exists on this function at all.
# =======================================================================
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    g1_source_path, g1_sha = _setup_g1_source(tmp_dir)
    g2_source_out = os.path.join(tmp_dir, "g2_source.txt")
    plan_out = os.path.join(tmp_dir, "plan.json")
    output_dir = os.path.join(tmp_dir, "authority")
    record_out = os.path.join(tmp_dir, "publication_record.json")
    fake_master_path = os.path.join(tmp_dir, "master.txt")
    baseline_inventory = _fake_baseline_inventory(fake_master_path, output_dir, g1_sha)

    result = igpub.prepare_and_publish_g2(REPO_ROOT, g1_source_path, g2_source_out, plan_out, output_dir, record_out,
                                           baseline_inventory, expected_g1_sha256=g1_sha)
    expect("g2_source_facts" in result and "plan_record_path" in result and "publication_record" in result,
           "phaseA.prepare_and_publish_g2_returns_all_three_stages")
    import inspect as _inspect
    expect("master" not in _inspect.signature(igpub.prepare_and_publish_g2).parameters
           and "master_path" not in _inspect.signature(igpub.prepare_and_publish_g2).parameters,
           "r2blocker1.prepare_and_publish_g2_has_no_master_path_parameter_at_all")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)


def _full_phase_a_setup(tmp_dir):
    """Shared fixture: real canonical G1 on disk as the 'live Master',
    a completed real baseline inventory, and a completed Phase A (plan +
    publication record, baseline-bound per R3 BLOCKER 1) -- Master still
    exactly G1 throughout, since Phase A never touches it. Returns the
    parsed plan record too, since finalize_restoration() now consumes it
    directly (R3 BLOCKER 2)."""
    g1_source_path, g1_sha = _setup_g1_source(tmp_dir)
    master_path = os.path.join(tmp_dir, "master.txt")
    with open(master_path, "wb") as f:
        f.write(_CANON_G1_BYTES)
    authority_dir = os.path.join(tmp_dir, "authority")
    igpub.publish_generation(REPO_ROOT, g1_source_path, authority_dir)
    baseline_inventory = igen.capture_live_state_inventory(master_path, authority_dir)

    g2_source_out = os.path.join(tmp_dir, "g2_source.txt")
    plan_out = os.path.join(tmp_dir, "plan.json")
    record_out = os.path.join(tmp_dir, "publication_record.json")
    phase_a_result = igpub.prepare_and_publish_g2(
        REPO_ROOT, g1_source_path, g2_source_out, plan_out, authority_dir, record_out, baseline_inventory,
        expected_g1_sha256=g1_sha,
    )
    with open(plan_out, "rb") as f:
        plan_record = json.loads(f.read().decode("utf-8"))
    return {
        "g1_source_path": g1_source_path, "g1_sha": g1_sha, "master_path": master_path,
        "authority_dir": authority_dir, "baseline_inventory": baseline_inventory,
        "plan_record": plan_record, "plan_record_path": plan_out,
        "publication_record": phase_a_result["publication_record"],
    }


# =======================================================================
# R2 BLOCKER 1, Phase B: activate_g2_master() -- the ONLY function that
# ever calls perform_g1_to_g2_replacement(). Documented G2 activation
# ACTUALLY changes the live Master to G2.
# =======================================================================
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    ctx = _full_phase_a_setup(tmp_dir)
    expect(igen.sha256_file(ctx["master_path"]) == ctx["g1_sha"],
           "phaseB.master_still_exactly_g1_after_phase_a_publication_alone")

    activation_out = os.path.join(tmp_dir, "activation_record.json")
    activation = igpub.activate_g2_master(
        ctx["master_path"], ctx["authority_dir"], ctx["baseline_inventory"], ctx["publication_record"],
        activation_out, expected_g1_sha256=ctx["g1_sha"],
    )
    expect(activation["success"] is True, "phaseB.activate_g2_master_reports_success")
    expect(
        igen.sha256_file(ctx["master_path"]) == ctx["publication_record"]["g2_source_sha256"],
        "phaseB.documented_g2_activation_actually_changes_live_master_to_g2",
    )
    expect(activation["path_binding_checks"]["master_path_matches_baseline"] is True,
           "phaseB.activation_record_confirms_master_path_binding")
    expect(activation["path_binding_checks"]["authority_dir_matches_baseline"] is True,
           "phaseB.activation_record_confirms_authority_dir_binding")
    expect(os.path.isfile(activation_out), "phaseB.activation_record_file_actually_written")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# Activation is never attempted without a valid publication record.
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    g1_source_path, g1_sha = _setup_g1_source(tmp_dir)
    master_path = os.path.join(tmp_dir, "master.txt")
    with open(master_path, "wb") as f:
        f.write(_CANON_G1_BYTES)
    authority_dir = os.path.join(tmp_dir, "authority")
    igpub.publish_generation(REPO_ROOT, g1_source_path, authority_dir)
    baseline_inventory = igen.capture_live_state_inventory(master_path, authority_dir)

    raised = False
    try:
        igpub.activate_g2_master(master_path, authority_dir, baseline_inventory, None,
                                  os.path.join(tmp_dir, "never.json"), expected_g1_sha256=g1_sha)
    except igpub.GenerationPublisherError:
        raised = True
    expect(raised, "r2blocker7.activation_refused_with_no_publication_record_at_all")
    expect(igen.sha256_file(master_path) == g1_sha,
           "r2blocker7.master_untouched_when_activation_refused_for_missing_publication")
    expect(not os.path.exists(os.path.join(tmp_dir, "never.json")),
           "r2blocker7.no_activation_record_written_when_activation_refused")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# R2 BLOCKER 5: path-binding adversarial tests for activate_g2_master().
# =======================================================================
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    ctx = _full_phase_a_setup(tmp_dir)

    wrong_master_path = os.path.join(tmp_dir, "some_other_master.txt")
    with open(wrong_master_path, "wb") as f:
        f.write(_CANON_G1_BYTES)
    raised = False
    try:
        igpub.activate_g2_master(wrong_master_path, ctx["authority_dir"], ctx["baseline_inventory"],
                                  ctx["publication_record"], os.path.join(tmp_dir, "never1.json"),
                                  expected_g1_sha256=ctx["g1_sha"])
    except igpub.GenerationPublisherError:
        raised = True
    expect(raised, "r2blocker5.activate_g2_master_refuses_a_master_path_not_matching_baseline")
    expect(igen.sha256_file(wrong_master_path) == ctx["g1_sha"],
           "r2blocker5.wrong_master_path_file_itself_untouched")
    expect(igen.sha256_file(ctx["master_path"]) == ctx["g1_sha"],
           "r2blocker5.real_baseline_master_untouched_when_wrong_path_supplied")

    wrong_authority_dir = os.path.join(tmp_dir, "some_other_authority")
    os.makedirs(wrong_authority_dir)
    raised2 = False
    try:
        igpub.activate_g2_master(ctx["master_path"], wrong_authority_dir, ctx["baseline_inventory"],
                                  ctx["publication_record"], os.path.join(tmp_dir, "never2.json"),
                                  expected_g1_sha256=ctx["g1_sha"])
    except igpub.GenerationPublisherError:
        raised2 = True
    expect(raised2, "r2blocker5.activate_g2_master_refuses_an_authority_dir_not_matching_baseline")
    expect(igen.sha256_file(ctx["master_path"]) == ctx["g1_sha"],
           "r2blocker5.master_untouched_when_wrong_authority_dir_supplied")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# R2 BLOCKER 7 full-lifecycle recoverability: publication succeeds but
# activation fails remains fully recoverable via finalize_restoration().
# =======================================================================
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    ctx = _full_phase_a_setup(tmp_dir)

    # Simulate activation failing (wrong authority dir -- a realistic
    # operator mistake) -- Master remains untouched, G1.
    wrong_authority_dir = os.path.join(tmp_dir, "wrong_authority")
    os.makedirs(wrong_authority_dir)
    raised = False
    try:
        igpub.activate_g2_master(ctx["master_path"], wrong_authority_dir, ctx["baseline_inventory"],
                                  ctx["publication_record"], os.path.join(tmp_dir, "failed_activation.json"),
                                  expected_g1_sha256=ctx["g1_sha"])
    except igpub.GenerationPublisherError:
        raised = True
    expect(raised, "recoverability.simulated_activation_failure_raises")
    expect(igen.sha256_file(ctx["master_path"]) == ctx["g1_sha"],
           "recoverability.master_remains_g1_after_activation_failure")

    finalize_out = os.path.join(tmp_dir, "finalization_record.json")
    result = igpub.finalize_restoration(
        REPO_ROOT, ctx["master_path"], ctx["authority_dir"], ctx["g1_source_path"], ctx["plan_record"],
        ctx["publication_record"], ctx["baseline_inventory"], finalize_out, expected_g1_sha256=ctx["g1_sha"],
    )
    expect(result["master_restore_performed"] is False,
           "recoverability.finalize_takes_already_g1_branch_after_activation_failure")
    expect(result["exact_match"] is True,
           "recoverability.finalize_returns_exact_baseline_after_publication_succeeded_but_activation_failed")
    expect(result["g2_sidecar_removed"] is True,
           "recoverability.finalize_still_cleans_up_the_orphaned_g2_sidecar")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# BLOCKER 8/9 (round 1), now via the real two-phase flow: mandatory
# closure, safe current-Master handling, usable even if I2 never began.
# =======================================================================
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    ctx = _full_phase_a_setup(tmp_dir)
    activation_out = os.path.join(tmp_dir, "activation_record.json")
    igpub.activate_g2_master(ctx["master_path"], ctx["authority_dir"], ctx["baseline_inventory"],
                              ctx["publication_record"], activation_out, expected_g1_sha256=ctx["g1_sha"])
    expect(igen.sha256_file(ctx["master_path"]) == ctx["publication_record"]["g2_source_sha256"],
           "sanity.master_is_exactly_g2_after_real_activation")

    finalize_out = os.path.join(tmp_dir, "finalization_record.json")
    result = igpub.finalize_restoration(
        REPO_ROOT, ctx["master_path"], ctx["authority_dir"], ctx["g1_source_path"], ctx["plan_record"],
        ctx["publication_record"], ctx["baseline_inventory"], finalize_out, expected_g1_sha256=ctx["g1_sha"],
    )
    expect(result["master_restore_performed"] is True, "blocker8.finalize_restoration_restores_from_g2")
    expect(igen.sha256_file(ctx["master_path"]) == ctx["g1_sha"], "blocker8.live_master_is_exactly_g1_after_finalize")
    expect(result["g2_sidecar_removed"] is True, "blocker9.finalize_restoration_removes_the_test_created_g2_sidecar")
    expect(
        not os.path.isfile(os.path.join(ctx["authority_dir"], ctx["publication_record"]["g2_generation_basename"])),
        "blocker9.g2_sidecar_file_is_actually_gone_from_disk",
    )
    expect(
        igen.read_manifest_source_sha256_plain(ctx["authority_dir"]) == ctx["g1_sha"],
        "blocker8.active_manifest_points_back_to_g1_after_finalize",
    )
    expect(result["exact_match"] is True, "blocker8.final_inventory_exactly_matches_the_pre_i_baseline")

    finalize_out2 = os.path.join(tmp_dir, "finalization_record2.json")
    result2 = igpub.finalize_restoration(
        REPO_ROOT, ctx["master_path"], ctx["authority_dir"], ctx["g1_source_path"], ctx["plan_record"],
        ctx["publication_record"], ctx["baseline_inventory"], finalize_out2, expected_g1_sha256=ctx["g1_sha"],
    )
    expect(result2["master_restore_performed"] is False, "blocker9.finalize_restoration_does_not_rewrite_an_already_g1_master")
    expect(result2["exact_match"] is True, "blocker9.finalize_restoration_usable_even_if_i2_never_began_or_already_restored")

    with open(ctx["master_path"], "wb") as f:
        f.write(b"completely unrelated bytes")
    finalize_out3 = os.path.join(tmp_dir, "finalization_record3.json")
    raised = False
    try:
        igpub.finalize_restoration(
            REPO_ROOT, ctx["master_path"], ctx["authority_dir"], ctx["g1_source_path"], ctx["plan_record"],
            ctx["publication_record"], ctx["baseline_inventory"], finalize_out3, expected_g1_sha256=ctx["g1_sha"],
        )
    except igpub.GenerationPublisherError:
        raised = True
    expect(raised, "blocker8.finalize_restoration_stops_on_an_unexpected_live_master_state")
    expect(
        igen.sha256_file(ctx["master_path"]) == hashlib.sha256(b"completely unrelated bytes").hexdigest(),
        "blocker8.unexpected_state_leaves_the_live_master_completely_untouched",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# R2 BLOCKER 5: path-binding adversarial tests for finalize_restoration().
# =======================================================================
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    ctx = _full_phase_a_setup(tmp_dir)

    wrong_master_path = os.path.join(tmp_dir, "some_other_master.txt")
    with open(wrong_master_path, "wb") as f:
        f.write(_CANON_G1_BYTES)
    raised = False
    try:
        igpub.finalize_restoration(
            REPO_ROOT, wrong_master_path, ctx["authority_dir"], ctx["g1_source_path"], ctx["plan_record"],
            ctx["publication_record"], ctx["baseline_inventory"], os.path.join(tmp_dir, "never1.json"),
            expected_g1_sha256=ctx["g1_sha"],
        )
    except igpub.GenerationPublisherError:
        raised = True
    expect(raised, "r2blocker5.finalize_restoration_refuses_a_master_path_not_matching_baseline")
    expect(igen.sha256_file(wrong_master_path) == ctx["g1_sha"], "r2blocker5.wrong_master_path_file_untouched_by_finalize")
    expect(igen.sha256_file(ctx["master_path"]) == ctx["g1_sha"], "r2blocker5.real_master_untouched_by_finalize_wrong_path_attempt")

    wrong_authority_dir = os.path.join(tmp_dir, "some_other_authority")
    os.makedirs(wrong_authority_dir)
    raised2 = False
    try:
        igpub.finalize_restoration(
            REPO_ROOT, ctx["master_path"], wrong_authority_dir, ctx["g1_source_path"], ctx["plan_record"],
            ctx["publication_record"], ctx["baseline_inventory"], os.path.join(tmp_dir, "never2.json"),
            expected_g1_sha256=ctx["g1_sha"],
        )
    except igpub.GenerationPublisherError:
        raised2 = True
    expect(raised2, "r2blocker5.finalize_restoration_refuses_an_authority_dir_not_matching_baseline")
    expect(igen.sha256_file(ctx["master_path"]) == ctx["g1_sha"], "r2blocker5.master_untouched_by_finalize_wrong_authority_attempt")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# R2 BLOCKER 8: a tampered publication record cannot authorize G2
# sidecar deletion during finalize_restoration(). Master restoration
# itself is independent of this check and must still succeed. plan_record
# is intentionally None here -- these tests exercise the publication-
# record-alone revalidation path in isolation.
# =======================================================================
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    ctx = _full_phase_a_setup(tmp_dir)
    activation_out = os.path.join(tmp_dir, "activation_record.json")
    igpub.activate_g2_master(ctx["master_path"], ctx["authority_dir"], ctx["baseline_inventory"],
                              ctx["publication_record"], activation_out, expected_g1_sha256=ctx["g1_sha"])

    tampered_record = dict(ctx["publication_record"])
    tampered_record["g2_sidecar_sha256"] = "0" * 64  # does not match the real on-disk sidecar

    finalize_out = os.path.join(tmp_dir, "finalization_record.json")
    result = igpub.finalize_restoration(
        REPO_ROOT, ctx["master_path"], ctx["authority_dir"], ctx["g1_source_path"], None, tampered_record,
        ctx["baseline_inventory"], finalize_out, expected_g1_sha256=ctx["g1_sha"],
    )
    expect(result["master_restore_performed"] is True,
           "r2blocker8.master_restoration_still_succeeds_despite_tampered_record")
    expect(igen.sha256_file(ctx["master_path"]) == ctx["g1_sha"],
           "r2blocker8.live_master_is_exactly_g1_despite_tampered_record")
    expect(result["sidecar_removal_plan"]["checks"]["publication_record_revalidation"]["all_checks_pass"] is False,
           "r2blocker8.tampered_record_fails_independent_revalidation")
    expect(result["g2_sidecar_removed"] is False,
           "r2blocker8.tampered_record_does_not_authorize_sidecar_deletion")
    real_sidecar_path = os.path.join(ctx["authority_dir"], ctx["publication_record"]["g2_generation_basename"])
    expect(os.path.isfile(real_sidecar_path),
           "r2blocker8.real_sidecar_file_still_present_on_disk_after_tampered_finalize")
    expect(igen.sha256_file(real_sidecar_path) == ctx["publication_record"]["g2_sidecar_sha256"],
           "r2blocker8.real_sidecar_file_content_unchanged_after_tampered_finalize")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# A second, different tamper: recorded semantic parity flipped to False
# must also refuse deletion (a fresh tmp_dir/context, since the block
# above already consumed and cleaned up its own).
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    ctx = _full_phase_a_setup(tmp_dir)
    activation_out = os.path.join(tmp_dir, "activation_record.json")
    igpub.activate_g2_master(ctx["master_path"], ctx["authority_dir"], ctx["baseline_inventory"],
                              ctx["publication_record"], activation_out, expected_g1_sha256=ctx["g1_sha"])

    tampered_record2 = dict(ctx["publication_record"])
    tampered_parity = dict(tampered_record2["semantic_parity"])
    tampered_parity["all_parity_checks_pass"] = False
    tampered_record2["semantic_parity"] = tampered_parity

    finalize_out = os.path.join(tmp_dir, "finalization_record.json")
    result = igpub.finalize_restoration(
        REPO_ROOT, ctx["master_path"], ctx["authority_dir"], ctx["g1_source_path"], None, tampered_record2,
        ctx["baseline_inventory"], finalize_out, expected_g1_sha256=ctx["g1_sha"],
    )
    expect(result["g2_sidecar_removed"] is False,
           "r2blocker8.tampered_semantic_parity_flag_does_not_authorize_sidecar_deletion")
    real_sidecar_path = os.path.join(ctx["authority_dir"], ctx["publication_record"]["g2_generation_basename"])
    expect(os.path.isfile(real_sidecar_path),
           "r2blocker8.real_sidecar_file_still_present_after_tampered_semantic_parity_finalize")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# R3 BLOCKER 2: recovery using the plan record ALONE (publication_record
# is None) -- covering both "the publication-record write itself failed"
# and "the publication record is simply absent after a partial Phase-A
# mutation." No live Master activation occurs in either case (Master
# stays exactly G1 throughout, matching the blocker's own test spec).
# =======================================================================
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    g1_source_path, g1_sha = _setup_g1_source(tmp_dir)
    master_path = os.path.join(tmp_dir, "master.txt")
    with open(master_path, "wb") as f:
        f.write(_CANON_G1_BYTES)
    authority_dir = os.path.join(tmp_dir, "authority")
    igpub.publish_generation(REPO_ROOT, g1_source_path, authority_dir)
    baseline_inventory = igen.capture_live_state_inventory(master_path, authority_dir)

    g2_source_out = os.path.join(tmp_dir, "g2_source.txt")
    plan_out = os.path.join(tmp_dir, "plan.json")
    igpub.construct_and_write_g2_source(g1_source_path, g2_source_out, expected_g1_sha256=g1_sha)
    igpub.write_g2_plan_record(REPO_ROOT, g1_source_path, g2_source_out, plan_out, baseline_inventory,
                                expected_g1_sha256=g1_sha)

    record_out = os.path.join(tmp_dir, "publication_record.json")
    orig_write_record_once = igpub._write_record_once

    def _boom(path, rec):
        if path == record_out:
            raise IOError("simulated disk failure writing the publication record")
        return orig_write_record_once(path, rec)

    igpub._write_record_once = _boom
    try:
        raised = False
        try:
            igpub.publish_g2_with_record(REPO_ROOT, plan_out, authority_dir, record_out, expected_g1_sha256=g1_sha)
        except Exception:
            raised = True
        expect(raised, "r3blocker2.simulated_publication_record_write_failure_raises")
    finally:
        igpub._write_record_once = orig_write_record_once

    expect(not os.path.exists(record_out),
           "r3blocker2.no_publication_record_file_exists_after_the_simulated_write_failure")
    with open(plan_out, "rb") as f:
        plan_record = json.loads(f.read().decode("utf-8"))
    expected_sidecar_path = os.path.join(authority_dir, plan_record["expected_generation_basename"])
    expect(os.path.isfile(expected_sidecar_path),
           "r3blocker2.the_real_g2_sidecar_was_actually_published_despite_the_record_write_failure")
    expect(igen.sha256_file(master_path) == g1_sha, "r3blocker2.no_live_master_activation_occurred")

    finalize_out = os.path.join(tmp_dir, "finalization_record.json")
    result = igpub.finalize_restoration(
        REPO_ROOT, master_path, authority_dir, g1_source_path, plan_record, None,
        baseline_inventory, finalize_out, expected_g1_sha256=g1_sha,
    )
    expect(result["master_restore_performed"] is False, "r3blocker2.finalize_takes_the_already_g1_branch")
    expect(result["exact_match"] is True, "r3blocker2.recovery_using_baseline_g1_and_plan_returns_exact_baseline")
    expect(result["g2_sidecar_removed"] is True, "r3blocker2.exact_g2_orphan_is_removed_via_the_plan_record_alone")
    expect(result["sidecar_removal_plan"]["source"] == "plan_record",
           "r3blocker2.removal_was_authorized_via_the_plan_record_path")
    expect(not os.path.isfile(expected_sidecar_path), "r3blocker2.orphan_sidecar_file_actually_gone_from_disk")
    expect(igen.read_manifest_source_sha256_plain(authority_dir) == g1_sha,
           "r3blocker2.manifest_returns_exactly_to_baseline")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    g1_source_path, g1_sha = _setup_g1_source(tmp_dir)
    master_path = os.path.join(tmp_dir, "master.txt")
    with open(master_path, "wb") as f:
        f.write(_CANON_G1_BYTES)
    authority_dir = os.path.join(tmp_dir, "authority")
    igpub.publish_generation(REPO_ROOT, g1_source_path, authority_dir)
    baseline_inventory = igen.capture_live_state_inventory(master_path, authority_dir)

    g2_source_out = os.path.join(tmp_dir, "g2_source.txt")
    plan_out = os.path.join(tmp_dir, "plan.json")
    igpub.construct_and_write_g2_source(g1_source_path, g2_source_out, expected_g1_sha256=g1_sha)
    plan_record = igpub.write_g2_plan_record(REPO_ROOT, g1_source_path, g2_source_out, plan_out, baseline_inventory,
                                              expected_g1_sha256=g1_sha)

    # The authority mutation happens WITHOUT ever going through
    # publish_g2_with_record()'s own record-writing code path at all
    # (e.g. the operator's shell was killed between publish and the
    # record write) -- publish_generation() is the exact same real,
    # accepted call publish_g2_with_record() itself makes.
    igpub.publish_generation(REPO_ROOT, g2_source_out, authority_dir)
    never_written_record_path = os.path.join(tmp_dir, "publication_record.json")
    expect(not os.path.exists(never_written_record_path), "r3blocker2.publication_record_genuinely_absent")

    finalize_out = os.path.join(tmp_dir, "finalization_record.json")
    result = igpub.finalize_restoration(
        REPO_ROOT, master_path, authority_dir, g1_source_path, plan_record, None,
        baseline_inventory, finalize_out, expected_g1_sha256=g1_sha,
    )
    expect(result["exact_match"] is True,
           "r3blocker2.exact_recovery_when_publication_record_was_never_written_at_all")
    expect(result["g2_sidecar_removed"] is True,
           "r3blocker2.orphan_g2_sidecar_removed_via_plan_when_publication_record_absent")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# R3 BLOCKER 3: Master restoration must not trust the publication
# record for G2 identity. A tampered g2_source_sha256 must not prevent
# safe G2->G1 restoration, and -- since the tamper does not touch the
# sidecar's own basename/SHA fields, so plan+publication still agree on
# identity -- authority cleanup remains possible through the
# independently verified plan.
# =======================================================================
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    ctx = _full_phase_a_setup(tmp_dir)
    activation_out = os.path.join(tmp_dir, "activation_record.json")
    igpub.activate_g2_master(ctx["master_path"], ctx["authority_dir"], ctx["baseline_inventory"],
                              ctx["publication_record"], activation_out, expected_g1_sha256=ctx["g1_sha"])
    expect(igen.sha256_file(ctx["master_path"]) == ctx["publication_record"]["g2_source_sha256"],
           "sanity.master_is_exactly_g2_before_the_tamper_test")

    tampered_record = dict(ctx["publication_record"])
    tampered_record["g2_source_sha256"] = "0" * 64  # tamper ONLY the field R3 BLOCKER 3 forbids trusting

    finalize_out = os.path.join(tmp_dir, "finalization_record.json")
    result = igpub.finalize_restoration(
        REPO_ROOT, ctx["master_path"], ctx["authority_dir"], ctx["g1_source_path"], ctx["plan_record"],
        tampered_record, ctx["baseline_inventory"], finalize_out, expected_g1_sha256=ctx["g1_sha"],
    )
    expect(result["master_restore_performed"] is True,
           "r3blocker3.master_restoration_succeeds_despite_a_tampered_publication_record_g2_source_sha256")
    expect(igen.sha256_file(ctx["master_path"]) == ctx["g1_sha"],
           "r3blocker3.live_master_is_exactly_g1_after_finalize")
    expect(result["g2_identity_corroboration"]["publication_g2_sha_matches_derived"] is False,
           "r3blocker3.corroboration_correctly_flags_the_tampered_publication_g2_sha")
    expect(result["g2_identity_corroboration"]["plan_g2_sha_matches_derived"] is True,
           "r3blocker3.corroboration_confirms_the_untampered_plan_g2_sha")
    expect(result["g2_sidecar_removed"] is True,
           "r3blocker3.authority_cleanup_still_possible_through_the_independently_verified_plan")
    expect(result["sidecar_removal_plan"]["source"] == "publication_and_plan",
           "r3blocker3.removal_source_correctly_reflects_both_records_agreeing_on_identity")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# =======================================================================
# R3 BLOCKER 3 (interaction): plan/publication disagreement on the
# sidecar's own identity fails closed for destructive cleanup -- never a
# guess. Master restoration itself is unaffected.
# =======================================================================
tmp_dir = tempfile.mkdtemp(prefix="i_generation_publisher_py3_")
try:
    ctx = _full_phase_a_setup(tmp_dir)
    activation_out = os.path.join(tmp_dir, "activation_record.json")
    igpub.activate_g2_master(ctx["master_path"], ctx["authority_dir"], ctx["baseline_inventory"],
                              ctx["publication_record"], activation_out, expected_g1_sha256=ctx["g1_sha"])

    disagreeing_plan = dict(ctx["plan_record"])
    disagreeing_plan["expected_generation_basename"] = "sfm_master_0_totally_different_basename.sfmsidecar"

    finalize_out = os.path.join(tmp_dir, "finalization_record.json")
    result = igpub.finalize_restoration(
        REPO_ROOT, ctx["master_path"], ctx["authority_dir"], ctx["g1_source_path"], disagreeing_plan,
        ctx["publication_record"], ctx["baseline_inventory"], finalize_out, expected_g1_sha256=ctx["g1_sha"],
    )
    expect(result["master_restore_performed"] is True,
           "r3blocker3.master_restoration_unaffected_by_a_plan_publication_disagreement")
    expect(result["g2_sidecar_removed"] is False,
           "r3blocker3.plan_publication_disagreement_fails_closed_for_destructive_cleanup")
    real_sidecar_path = os.path.join(ctx["authority_dir"], ctx["publication_record"]["g2_generation_basename"])
    expect(os.path.isfile(real_sidecar_path),
           "r3blocker3.real_sidecar_file_still_present_after_a_disagreement_refusal")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
if FAIL_COUNT[0]:
    sys.exit(1)
