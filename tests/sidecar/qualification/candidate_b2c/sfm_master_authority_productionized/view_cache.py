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
        pinned ownership prevents safe admission."""
        cache_key = view.cache_key()
        needed = view.estimated_bytes

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
        self._entries.pop(cache_key, None)
        try:
            self._insertion_order.remove(cache_key)
        except ValueError:
            pass
        self._ledger.release(memory_accounting.CATEGORY_RETAINED_VIEWS, cache_key)

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
