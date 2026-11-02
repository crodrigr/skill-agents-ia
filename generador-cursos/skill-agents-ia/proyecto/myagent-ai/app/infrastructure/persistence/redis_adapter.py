from redis.asyncio import Redis


class RedisCache:
    """Caché con tiempo de vida (TTL). Si no hay REDIS_URL, no se usa."""

    def __init__(self, url: str) -> None:
        self._redis = Redis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        return await self._redis.get(key)

    async def set(self, key: str, value: str, ttl: int = 60) -> None:
        await self._redis.set(key, value, ex=ttl)

    async def close(self) -> None:
        await self._redis.aclose()
