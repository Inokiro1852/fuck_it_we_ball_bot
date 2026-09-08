import asyncio
from collections import OrderedDict
from typing import Any


class DuelManager:
    def __init__(self, destruction_time: int = 3600, max_finished_cache: int = 10000):
        self.__duels: dict[str, dict | str] = {}
        self.__finished_duels: OrderedDict[str, None] = OrderedDict()
        self.__locks: dict[str, asyncio.Lock] = {}
        self.__cleanup_tasks: dict[str, asyncio.Task] = {}
        self.__meta_lock = asyncio.Lock()
        self.__destruction_time: int = destruction_time
        self.__max_finished_cache: int = max_finished_cache

    async def get_lock(self, inline_id: str) -> asyncio.Lock:
        async with self.__meta_lock:
            if inline_id not in self.__locks:
                self.__locks[inline_id] = asyncio.Lock()
            return self.__locks[inline_id]

    async def create_duel(self, inline_id: str, tables: Any) -> dict | None:
        if await self.is_finished(inline_id):
            return None
        duel = self.__duels.get(inline_id)
        if not isinstance(duel, dict):
            duel = {'players': [], 'tables': tables}
            self.__duels[inline_id] = duel
        return duel

    async def get_duel(self, inline_id: str) -> dict | None:
        if await self.is_finished(inline_id):
            return None
        duel = self.__duels.get(inline_id)
        return duel if isinstance(duel, dict) else None

    async def is_finished(self, inline_id: str) -> bool:
        return (
            inline_id in self.__finished_duels
            or self.__duels.get(inline_id) == 'finished'
        )

    async def mark_finished(self, inline_id: str) -> None:
        self.__finished_duels[inline_id] = None
        if len(self.__finished_duels) > self.__max_finished_cache:
            self.__finished_duels.popitem(last=False)

        self.__duels[inline_id] = 'finished'
        self.__schedule_cleanup(inline_id, delay=self.__destruction_time)

    async def schedule_terminate_duel(self, inline_id: str) -> None:
        self.__schedule_cleanup(inline_id, delay=self.__destruction_time)

    def __schedule_cleanup(self, inline_id: str, delay: int) -> None:
        if existing_task := self.__cleanup_tasks.get(inline_id):
            existing_task.cancel()

        task = asyncio.create_task(self.__cleanup_after(inline_id, delay))
        self.__cleanup_tasks[inline_id] = task
        task.add_done_callback(lambda _: self.__cleanup_tasks.pop(inline_id, None))

    async def __cleanup_after(self, inline_id: str, delay: int) -> None:
        try:
            await asyncio.sleep(delay)
            self.__duels.pop(inline_id, None)
            async with self.__meta_lock:
                lock = self.__locks.get(inline_id)
                if lock and not lock.locked():
                    self.__locks.pop(inline_id, None)
        except asyncio.CancelledError:
            pass
