import asyncio
from core.node import Node
from typing import List, Dict, Optional

class Leader:
    def __init__(self, leader_id: str):
        self.leader_id = leader_id
        self.nodes: List[Node] = []
        self.term = 0
        self.is_leader = False
        self.log: List[tuple] = []
        self.commit_index = 0

    async def add_node(self, node: Node) -> None:
        self.nodes.append(node)
        await node.task_queue.put(("join", node.node_id))

    async def replicate(self, file_hash: str, file_data: bytes) -> None:
        if self.is_leader:
            entry = (self.term, "replicate", file_hash, file_data)
            self.log.append(entry)
            tasks = [node.store(file_hash, file_data) for node in self.nodes]
            await asyncio.gather(*tasks)

    async def request_vote(self, candidate_id: str) -> bool:
        self.term += 1
        self.is_leader = candidate_id == self.leader_id
        return self.is_leader

    async def append_entries(self) -> None:
        if self.is_leader:
            for node in self.nodes:
                if node.is_alive:
                    await node.task_queue.put(("sync", self.log[-1]))
            self.commit_index = len(self.log) - 1