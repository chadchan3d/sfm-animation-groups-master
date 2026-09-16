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
        relying on garbage-collection timing)."""
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
        every cached view belonging to a now-superseded generation.
        Does NOT evict/free them immediately -- their payload may still
        be referenced/read for diagnosis; eviction happens lazily on the
        next admission pressure, per corrected-B1's 'does not pretend
        bytes are freed until references release'."""
        seen_token_ids = set()
        for view in self._entries.values():
            if view.semantic_generation.master_sha256 == master_sha256:
                token = view.authorization
                if id(token) not in seen_token_ids:
                    token.invalidate()
                    seen_token_ids.add(id(token))

    def entry_count(self):
        return len(self._entries)

    def all_views(self):
        return list(self._entries.values())
