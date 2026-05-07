import time
import threading
from typing import Callable, TypeVar, Generic

T = TypeVar("T")


class _CacheEntry(Generic[T]):
    def __init__(self, value: T, ttl: float):
        self.value = value
        self.expires_at = time.monotonic() + ttl


class SimpleCache(Generic[T]):
    """Caché en memoria con tiempo de expiración (TTL)."""

    def __init__(self, ttl_seconds: float = 300):
        self._store: dict[str, _CacheEntry[T]] = {}
        self._ttl = ttl_seconds
        self._lock = threading.Lock()

    def get(self, key: str) -> T | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.monotonic() > entry.expires_at:
                del self._store[key]
                return None
            return entry.value

    def set(self, key: str, value: T) -> None:
        with self._lock:
            self._store[key] = _CacheEntry(value, self._ttl)

    def get_or_set(self, key: str, factory: Callable[[], T]) -> T:
        value = self.get(key)
        if value is not None:
            return value
        new_value = factory()
        self.set(key, new_value)
        return new_value


# Instancia global para categorías, con TTL de 5 minutos
categoria_cache = SimpleCache(list)(ttl_seconds=300)