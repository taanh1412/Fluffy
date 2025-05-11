import asyncio
from typing import Dict, Optional

class Node:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.data: Dict[str, bytes] = {}
        self.task_queue = asyncio.Queue()
        self.is_alive = True

    async def store(self, file_hash: str, file_data: bytes) -> None:
        if self.is_alive:
            self.data[file_hash] = file_data
            await self.task_queue.put(("store", file_hash, file_data))

    async def retrieve(self, file_hash: str) -> Optional[bytes]:
        return self.data.get(file_hash) if self.is_alive else None

    async def steal_work(self, other_nodes: list) -> None:
        if self.is_alive and self.task_queue.empty():
            for node in other_nodes:
                if not node.task_queue.empty():
                    task = await node.task_queue.get()
                    await self.task_queue.put(task)
                    break