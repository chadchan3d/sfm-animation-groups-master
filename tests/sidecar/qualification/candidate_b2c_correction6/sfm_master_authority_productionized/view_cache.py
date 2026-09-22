# -*- coding: utf-8 -*-
"""Detached-view cache + admission/eviction policy -- ASTRA_CORRECTED.md
Sections 5/8/9/10, R3-B2B Sections 8-9.

Cache key includes semantic generation, projection contract, coverage
identity, and consumer/projection kind -- never reused merely because
Master SHA matches if projection semantics/coverage differ
(ASTRA_CORRECTED.md Section 9).
"""
from . import errors
from . import memory_accounting


class ViewCache(object):
    def __init__(self, ledger):
        self._ledger = ledger
        self._entries = {}          # cache_key -> DetachedView
        self._insertion_order = []  # cache_key list, oldest first
        # Astra F3 correction: views evicted from the cache while a
        # consumer lease is STILL live are moved here instead of having
        # their ledger charge released immediately -- the charge is
        # DEFERRED, keyed by the view's own identity, until the last
        # lease against it is released (see release_lease() below).
        # Under the corrected architecture this should never actually
        # be populated in normal operation (eviction already skips any
        # leased view, see _evict_one), but it exists as defense in
        # depth against any OTHER removal path (e.g. a future explicit
        # cache-clear) that might remove a still-leased view.
        self._leased_orphans = {}   # id(view) -> (view, cache_key)

    def get(self, cache_key):
        """Never hands out a view whose authorization was revoked --
        callers must re-acquire rather than trust a stale cache hit."""
        view = self._entries.get(cache_key)
        if view is not None and view.is_stale():
            return None
        return view

    def admit(self, view):
        """Before publishing: calculate the conservative logical charge,
        consider already-retained views, evict unpinned reusable/stale
        views under pressure, and only then admit -- or refuse if active
        pinned ownership prevents safe admission.

        Astra F3 correction ("same-key pinned replacement defect"): a
        same-key admission (a fresh cohort re-publishing the identical
        generation/coverage/consumer_kind) used to silently OVERWRITE
        `self._entries[cache_key]` and the ledger's own charge entry
        directly -- if the OLD view at that key still had live consumer
        leases, its accounting was clobbered rather than preserved, an
        undercount identical in kind to the eviction-while-leased defect.
        Any pre-existing entry at this exact key is now retired through
        the SAME `_remove()` path eviction uses (deferring its ledger
        release if it is still leased -- explicit old+new overlap
        accounting, not silent replacement) before the new view is
        admitted under that key."""
        cache_key = view.cache_key()
        needed = view.estimated_bytes

        # Astra SECOND correction gate F3/F4 ("second-view failure" /
        # no-partial-effects requirement, found while building Test 4):
        # if `needed` ALONE already exceeds the gate, no amount of
        # evicting OTHER, unrelated cache entries could ever make this
        # fit -- evicting them anyway would needlessly destroy perfectly
        # good, still-useful cache state for a request that was doomed
        # from the start. Refuse immediately, before touching anything
        # (including this view's own same-key predecessor, if any).
        if needed > memory_accounting.RETAINED_PROMOTION_GATE_BYTES:
            raise errors.ViewAdmissionRefused(
                "admitting a %d-byte view ALONE exceeds the retained promotion gate (%d bytes) "
                "-- no eviction of anything else could ever make this fit; refusing without "
                "touching any existing cache state." % (needed, memory_accounting.RETAINED_PROMOTION_GATE_BYTES)
            )

        if cache_key in self._entries:
            self._remove(cache_key)

        while self._ledger.would_exceed_retained_gate(needed) and self._evict_one():
            pass
        if self._ledger.would_exceed_retained_gate(needed):
            raise errors.ViewAdmissionRefused(
                "admitting a %d-byte view would exceed the retained promotion gate "
                "(%d bytes) and no further unpinned view could be evicted."
                % (needed, memory_accounting.RETAINED_PROMOTION_GATE_BYTES)
            )

        self._entries[cache_key] = view
        self._insertion_order.append(cache_key)
        self._ledger.charge(memory_accounting.CATEGORY_RETAINED_VIEWS, cache_key, needed)
        return view

    def admit_batch(self, views):
        """Astra SECOND correction gate F3/F4: the ONLY sanctioned way to
        publish MORE THAN ONE view from a single acquisition. Fixes a
        real, reproduced bug in the per-view `admit()` loop the first
        correction still used at the Broker level: admitting view A then
        view B (two SEPARATE `admit()` calls) let B's own eviction pass
        evict A -- moments after A had JUST been charged/inserted in the
        SAME batch -- while the CALLER still returned both A and B to
        its own caller. The ledger then reflected only B's charge while
        the caller-visible result still included A, and a lease taken on
        the now-evicted A never restored any charge.

        Fix: compute the TOTAL bytes needed for the WHOLE batch UP
        FRONT, evict (existing, unrelated, already-cached entries only --
        never a member of THIS batch, since none of them are in
        `self._entries` yet) until the total fits or nothing more can be
        evicted, and ONLY THEN charge+insert EVERY view in the batch
        together. If the whole batch cannot be made to fit, NOTHING is
        published -- no partial admission, no partial charge, the
        pre-existing visible cache state is left completely untouched
        (since nothing was written to `self._entries`/the ledger before
        this point, there is nothing to roll back). No view in `views`
        is ever gettable/leaseable while uncharged, because charging and
        insertion happen together, after the fits-check has already
        succeeded for the batch as a whole."""
        if not views:
            return []

        total_needed = sum(v.estimated_bytes for v in views)

        # Astra SECOND correction gate F3/F4 (found while building Test 4
        # -- Section 13's "second-view failure" case): if the batch's OWN
        # total already exceeds the gate, no amount of evicting OTHER,
        # unrelated cache entries could ever make it fit -- doing so
        # anyway would needlessly destroy perfectly good, still-useful
        # cache state for a request that was doomed from the start,
        # violating this method's own "pre-existing visible cache state
        # is left completely untouched" promise on failure. Refuse
        # immediately, before evicting or retiring anything.
        if total_needed > memory_accounting.RETAINED_PROMOTION_GATE_BYTES:
            raise errors.ViewAdmissionRefused(
                "admitting a %d-byte batch of %d view(s) ALONE exceeds the retained promotion "
                "gate (%d bytes) -- no eviction of anything else could ever make this fit; "
                "refusing without touching any existing cache state."
                % (total_needed, len(views), memory_accounting.RETAINED_PROMOTION_GATE_BYTES)
            )

        while self._ledger.would_exceed_retained_gate(total_needed) and self._evict_one():
            pass
        if self._ledger.would_exceed_retained_gate(total_needed):
            raise errors.ViewAdmissionRefused(
                "admitting a %d-byte batch of %d view(s) would exceed the retained promotion "
                "gate (%d bytes) and no further unpinned view could be evicted."
                % (total_needed, len(views), memory_accounting.RETAINED_PROMOTION_GATE_BYTES)
            )

        # Retire any pre-existing same-key entries FIRST (same
        # old+new-overlap-preserving path `admit()` already established),
        # entirely before charging/inserting the new batch, so a
        # same-key collision WITHIN the batch's own retirement step can
        # never interleave with the batch's own charge/insert step below.
        for view in views:
            cache_key = view.cache_key()
            if cache_key in self._entries:
                self._remove(cache_key)

        for view in views:
            cache_key = view.cache_key()
            self._entries[cache_key] = view
            self._insertion_order.append(cache_key)
            self._ledger.charge(memory_accounting.CATEGORY_RETAINED_VIEWS, cache_key, view.estimated_bytes)

        return views

    def _evict_one(self):
        """Eviction order: (1) unpinned stale views (already invalidated,
        cheapest to drop -- their payload is diagnostic-only at this
        point); (2) unpinned redundant covered views, oldest first. A
        view still `pinned` (actively borrowed by a consumer fixture) is
        never evicted."""
        for cache_key in list(self._insertion_order):
            view = self._entries.get(cache_key)
            if view is None:
                self._insertion_order.remove(cache_key)
                continue
            if not view.pinned and view.is_stale():
                self._remove(cache_key)
                return True
        for cache_key in list(self._insertion_order):
            view = self._entries.get(cache_key)
            if view is not None and not view.pinned:
                self._remove(cache_key)
                return True
        return False  # every remaining entry is pinned -- cannot evict further

    def _remove(self, cache_key):
        view = self._entries.pop(cache_key, None)
        try:
            self._insertion_order.remove(cache_key)
        except ValueError:
            pass
        if view is not None and view.has_live_leases():
            # Astra F3 (found while building Test 3's same-key-
            # replacement case): the ledger's own charge dict is keyed
            # by `entry_id`, and `cache_key` IS that entry_id -- if the
            # deferred charge were simply left registered under the
            # SAME cache_key, a later same-key admission (the exact
            # "same-key pinned replacement" scenario) would silently
            # OVERWRITE it via its own `ledger.charge(category,
            # cache_key, ...)` call, reproducing the identical collision
            # one level down. The orphan's charge is therefore RE-KEYED
            # here to a distinct, private entry_id (never colliding with
            # any real cache_key) before the original cache_key entry is
            # released -- explicit old+new overlap accounting, not a
            # silent clobber at either layer.
            orphan_entry_id = ("leased_orphan", id(view))
            self._ledger.charge(memory_accounting.CATEGORY_RETAINED_VIEWS, orphan_entry_id, view.estimated_bytes)
            self._ledger.release(memory_accounting.CATEGORY_RETAINED_VIEWS, cache_key)
            self._leased_orphans[id(view)] = (view, orphan_entry_id)
            return
        self._ledger.release(memory_accounting.CATEGORY_RETAINED_VIEWS, cache_key)

    def acquire_lease(self, view):
        """Astra F3: the ONLY sanctioned way a real consumer takes
        explicit, trackable ownership of a view independent of the
        cache's own membership -- returns a views.ViewLease token the
        caller must eventually pass to release_lease() (deterministically,
        on command completion/cancellation/failure/dialog-close, never
        relying on garbage-collection timing).

        Astra SECOND correction gate F3/F4 ("lease attempt on an evicted
        returned view"): a caller may still hold a plain Python reference
        to a view returned by an EARLIER acquisition, after a LATER,
        unrelated acquisition's eviction pressure has since dropped it
        from the cache. Since `DetachedView.acquire_lease()` itself has
        no notion of cache membership, honoring such a call unconditionally
        would create a live lease with ZERO backing ledger charge (the
        charge was already released at eviction, since the view had no
        live lease at that moment -- otherwise it would have become a
        leased orphan instead, see `_remove()`). Refuse unless `view` is
        still tracked in SOME accounted state: either still the live
        entry at its own cache_key, or already a leased orphan (which by
        definition already has >=1 live lease and a preserved, re-keyed
        charge -- gaining a further lease on it is exactly the normal
        multi-consumer-sharing case, not this defect)."""
        cache_key = view.cache_key()
        currently_cached = self._entries.get(cache_key) is view
        is_leased_orphan = id(view) in self._leased_orphans
        if not currently_cached and not is_leased_orphan:
            raise errors.EvictedViewLeaseRefused(
                "cannot lease this view: it is no longer tracked by the cache in any accounted "
                "state (evicted with zero live leases, so its retained-bytes charge was already "
                "released) -- re-acquire a fresh view instead of leasing a stale reference"
            )
        return view.acquire_lease()

    def release_lease(self, lease):
        """Releases a lease acquired via acquire_lease(). If the view was
        evicted from the cache while this lease (or another) was still
        live, releasing the LAST outstanding lease now finalizes the
        deferred ledger release (see _remove above) -- the charge
        release only happens once ALL accounted owners -- cache
        membership AND every consumer lease -- have released."""
        view = lease.view
        view.release_lease(lease)
        if not view.has_live_leases():
            orphan = self._leased_orphans.pop(id(view), None)
            if orphan is not None:
                _, cache_key = orphan
                self._ledger.release(memory_accounting.CATEGORY_RETAINED_VIEWS, cache_key)

    def outstanding_lease_count(self):
        """Diagnostic: total live leases across every view this cache
        currently knows about (cached or orphaned-but-leased) -- used by
        Test 3 to prove deterministic release on command completion/
        cancellation/failure leaves nothing outstanding."""
        total = 0
        for view in self._entries.values():
            total += view.live_lease_count()
        for view, _cache_key in self._leased_orphans.values():
            total += view.live_lease_count()
        return total

    def invalidate_generation(self, master_sha256):
        """Marks stale (via each view's shared LiveAuthorizationToken)
        every view belonging to a now-superseded generation -- BOTH
        currently-cached entries AND leased orphans (Package-Boundary
        Correction, 2026-09-21: Astra-reproduced defect A, "leased
        orphan views escape generation invalidation"). Does NOT evict/
        free/release anything; ownership/accounting for an orphan is
        completely untouched by this call (its `_leased_orphans` entry
        and re-keyed ledger charge remain exactly as `_remove()` left
        them, releasable only via `release_lease()` once its last lease
        is released) -- only its AUTHORIZATION is revoked, so `is_stale()`/
        `require_valid()` correctly reject it as a currently-authorized
        view/token from this point on, per corrected-B1's 'does not
        pretend bytes are freed until references release'.

        Root cause (reproduced, not assumed): this method previously
        iterated `self._entries.values()` only. A view displaced into
        `self._leased_orphans` by `_remove()` (Section: 'admit'/
        '_evict_one') keeps its OWN `authorization` token unless that
        exact token object is also visited here -- a leased view of a
        just-superseded generation, evicted moments before this call,
        would otherwise remain indistinguishable from a currently
        authorized view forever (its token is never invalidated by any
        other code path)."""
        seen_token_ids = set()
        for view in self._entries.values():
            if view.semantic_generation.master_sha256 == master_sha256:
                token = view.authorization
                if id(token) not in seen_token_ids:
                    token.invalidate()
                    seen_token_ids.add(id(token))
        for view, _entry_id in self._leased_orphans.values():
            if view.semantic_generation.master_sha256 == master_sha256:
                token = view.authorization
                if id(token) not in seen_token_ids:
                    token.invalidate()
                    seen_token_ids.add(id(token))

    def entry_count(self):
        return len(self._entries)

    def all_views(self):
        return list(self._entries.values())
