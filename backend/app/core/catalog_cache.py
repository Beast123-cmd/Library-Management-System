"""Short-lived process cache for catalogue reads.

Catalogue results are public to authenticated library members, while stock can
change during circulation. A small TTL protects the database during concurrent
searches without presenting stale availability for long.
"""

from time import monotonic
from typing import Any, Hashable


class CatalogCache:
    def __init__(self, max_entries: int = 512) -> None:
        self._entries: dict[Hashable, tuple[float, Any]] = {}
        self._max_entries = max_entries

    def get(self, key: Hashable) -> Any | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at <= monotonic():
            self._entries.pop(key, None)
            return None
        return value

    def set(self, key: Hashable, value: Any, ttl_seconds: int) -> None:
        if key not in self._entries and len(self._entries) >= self._max_entries:
            oldest_key = min(self._entries, key=lambda entry: self._entries[entry][0])
            self._entries.pop(oldest_key, None)
        self._entries[key] = (monotonic() + ttl_seconds, value)

    def invalidate(self) -> None:
        self._entries.clear()


catalog_cache = CatalogCache()
