from __future__ import annotations

from loguru import logger


class _NoopMemory:
    async def remember(self, content: str, user_id: str, **kwargs) -> str | None:
        return None

    async def recall(self, query: str, user_id: str, top_k: int = 5) -> list:
        return []

    async def close(self) -> None:
        pass


class HeadroomSessionMemory:
    def __init__(self) -> None:
        self._memory = _NoopMemory()
        self._available = False

    async def ensure_ready(self) -> bool:
        if self._available:
            return True
        try:
            from headroom import Memory as HMemory

            self._memory = HMemory()
            # ponytail: calls private _ensure_initialized — no public init method available
            await self._memory._ensure_initialized()
            self._available = True
            logger.info("Headroom memory initialized")
            return True
        except Exception as exc:
            logger.debug("Headroom memory not available: {}", exc)
            return False

    async def remember(self, content: str, user_id: str, **kwargs) -> str | None:
        if not self._available:
            return None
        return await self._memory.save(content, user_id=user_id, **kwargs)

    async def recall(self, query: str, user_id: str, top_k: int = 5) -> list:
        if not self._available:
            return []
        return await self._memory.search(query, user_id=user_id, top_k=top_k)

    async def close(self) -> None:
        await self._memory.close()

    @property
    def available(self) -> bool:
        return self._available
