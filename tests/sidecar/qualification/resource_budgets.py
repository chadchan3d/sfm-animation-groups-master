# -*- coding: utf-8 -*-
"""GATE C0.7 -- QUALIFICATION-ONLY explicit resource budgets. NOT production
code, NOT a binary-format change. Defines the budgets that must exist
before "bounded" is a defensible claim (Astra Round 2 / Gate C0 finding:
selective access alone does not make an architecture bounded if any single
request can still force an unbounded amount of work or retained memory).

These are PROVISIONAL C0 QUALIFICATION LIMITS, not public format limits or
production SLAs -- chosen conservatively from what has actually been
measured in this project (idle S2 steady ~22.77 MiB, largest real fold
family = 7, synthetic adversarial family = 500, largest tested consumer
view = 21,989 occurrence rows), not derived from any external requirement.
A future gate may raise, lower, or formalize them; C0 requires only that
SOME explicit, enforced values exist and that violating one produces an
explicit failure -- never a truncation, and never a `MasterUnknown`.
"""

# Provisional, qualification-only. See module docstring.
BUDGET_ARTIFACT_BYTES_BEFORE_ACQUISITION = 64 * 1024 * 1024   # 64 MiB
BUDGET_STRING_CACHE_ESTIMATED_BYTES = 4 * 1024 * 1024         # 4 MiB
BUDGET_ONE_FAMILY_RESULT_OCCURRENCE_ROWS = 5000               # rows
BUDGET_ONE_CONSUMER_SNAPSHOT_OCCURRENCE_ROWS = 50000          # rows
BUDGET_TOTAL_PINNED_VIEWS_ESTIMATED_BYTES = 20 * 1024 * 1024  # 20 MiB


class ResourceBudgetExceeded(Exception):
    """Raised when a qualification-only budget would be exceeded. Distinct
    from `MasterUnknown` (an authoritative "not present" answer): a budget
    refusal means the answer IS known but this qualification candidate
    declines to materialize/publish it at this size -- it must never be
    silently reinterpreted as "the fold is absent." Distinct from
    `AuthorityUnavailable`: the provider itself is fine; only this one
    request's result size is refused. Never partially satisfied -- no
    truncated family, no partial view is ever returned alongside this
    exception."""


def check_artifact_bytes_before_acquisition(byte_length):
    if byte_length > BUDGET_ARTIFACT_BYTES_BEFORE_ACQUISITION:
        raise ResourceBudgetExceeded(
            "artifact is %d bytes, exceeding the qualification budget of %d bytes "
            "for whole-file acquisition -- refused before reading, never truncated." % (
                byte_length, BUDGET_ARTIFACT_BYTES_BEFORE_ACQUISITION,
            )
        )


def check_string_cache_budget(provider):
    est = provider.string_cache_estimated_bytes()
    if est > BUDGET_STRING_CACHE_ESTIMATED_BYTES:
        raise ResourceBudgetExceeded(
            "string cache estimated at %d bytes, exceeding the qualification budget of %d bytes. "
            "Eviction may remove REUSABLE cache state only -- it must never transform an "
            "uncovered/not-yet-decoded fact into MasterUnknown." % (
                est, BUDGET_STRING_CACHE_ESTIMATED_BYTES,
            )
        )


def check_family_result_budget(occurrence_count, fold_key):
    if occurrence_count > BUDGET_ONE_FAMILY_RESULT_OCCURRENCE_ROWS:
        raise ResourceBudgetExceeded(
            "fold %r resolves to a family of %d occurrence rows, exceeding the qualification "
            "budget of %d rows for a single family result. Refused whole -- never truncated, "
            "and never reported as MasterUnknown (the family is known, just too large to "
            "publish under this budget)." % (
                fold_key, occurrence_count, BUDGET_ONE_FAMILY_RESULT_OCCURRENCE_ROWS,
            )
        )


def check_consumer_snapshot_budget(view):
    total_rows = sum(len(rows) for rows in view["folded"].values())
    if total_rows > BUDGET_ONE_CONSUMER_SNAPSHOT_OCCURRENCE_ROWS:
        raise ResourceBudgetExceeded(
            "requested view would retain %d total occurrence rows across %d folds, exceeding "
            "the qualification budget of %d rows for one consumer snapshot. Refused whole -- "
            "never a partially-published view." % (
                total_rows, len(view["folded"]), BUDGET_ONE_CONSUMER_SNAPSHOT_OCCURRENCE_ROWS,
            )
        )


def build_view_bounded_with_budget(provider, wanted_folds, probe_error_cls, bounded_view_module):
    """Wraps `bounded_view.build_view_bounded` with the family-result and
    consumer-snapshot budgets. Semantics for an IN-BUDGET request are
    completely unchanged (same function, same return value) -- the budget
    check only ever ADDS an explicit refusal path for an OUT-OF-BUDGET
    request; it never alters an in-budget result."""
    # Per-fold family budget: probe each wanted fold's family size via a
    # single bounded lookup (the same cost `build_view_bounded` would pay
    # anyway) BEFORE committing to building/retaining the full view, so a
    # single oversized family is caught before any partial materialization.
    for fold_key in wanted_folds:
        result = provider.lookup_fold(fold_key.encode("utf-8"))
        if result.__class__.__name__ != "MasterUnknown":
            occs = result.occurrences()
            check_family_result_budget(len(occs), fold_key)

    view = bounded_view_module.build_view_bounded(provider, wanted_folds, probe_error_cls)
    check_consumer_snapshot_budget(view)
    check_string_cache_budget(provider)
    return view
