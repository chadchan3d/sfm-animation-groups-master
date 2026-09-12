# -*- coding: utf-8 -*-
"""GATE B -- QUALIFICATION-ONLY "T2": strongest reasonable shared-TXT
session-cache alternative. Test-only. Never imported by production code,
never modifies `Rebuild_Control_Groups_Normalizer.py`.

Wraps the REAL, unmodified oracle functions (`parse_targeted_master`,
`validate_master_subset_conflicts` from `gate_a2_normalizer_oracle_extract`)
with a session object that tracks, for ONE Master generation identity:

    covered_folds   -- every fold ever requested in this generation (whether
                        it turned out present or genuinely absent)
    view            -- the last full `parse_targeted_master` result, scoped
                        to the UNION of every fold ever requested
    proven_absent   -- the subset of covered_folds with no entry in
                        view["folded"] -- a generation-bound negative cache

Rules (Gate B Part 3, verbatim):
  A. requested subset of covered_folds -> reuse `view`, NO TXT scan.
  B. requested folds include anything new -> coalesce (covered | wanted),
     ONE complete TXT scan over the union, extend coverage.
  C. a previously-proven-absent fold requested again -> already inside
     covered_folds from its first request, so rule A's "no scan" already
     covers it; no separate negative-cache path is needed to satisfy this.
  D. `invalidate()` (an explicit, EXTERNAL generation-change signal --
     nothing in this module detects a generation change on its own) drops
     covered_folds/view/proven_absent unconditionally.

This is the STRONGEST fair reasonable shared-TXT counterfactual: it never
rescans for a subset of already-covered vocabulary, and a covered scope's
repeat request costs nothing beyond re-returning the retained view. It is
NOT made artificially inefficient to flatter S1.
"""

import time


class SharedTxtSession(object):
    def __init__(self, master_path, parse_targeted_master, generation_id):
        self.master_path = master_path
        self._parse_targeted_master = parse_targeted_master
        self.generation_id = generation_id
        self.covered_folds = set()
        self.view = None
        self.proven_absent = set()

    def acquire(self, wanted_folds):
        """Returns (view, scanned, scan_time_s). `scanned` is False exactly
        when rule A applies (no TXT touch at all -- not even a re-open)."""
        wanted_folds = set(wanted_folds)
        new_folds = wanted_folds - self.covered_folds
        if self.view is not None and not new_folds:
            return self.view, False, 0.0

        union_folds = self.covered_folds | wanted_folds
        t0 = time.time()
        view = self._parse_targeted_master(self.master_path, union_folds, validate_conflicts=False)
        t1 = time.time()

        self.covered_folds = union_folds
        self.view = view
        self.proven_absent = set(f for f in union_folds if f not in view["folded"])
        return view, True, (t1 - t0)

    def is_covered(self, wanted_folds):
        return set(wanted_folds).issubset(self.covered_folds)

    def is_proven_absent(self, folded_key):
        return folded_key in self.proven_absent

    def invalidate(self, new_generation_id):
        """Rule D: explicit, external generation-change signal. No production
        lifecycle code is implied or exercised here -- this is a qualification
        model of the invalidation EFFECT only."""
        self.generation_id = new_generation_id
        self.covered_folds = set()
        self.view = None
        self.proven_absent = set()
