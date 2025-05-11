import pika
import asyncio
from node import Node

class Leader:
    def __init__(self, leader_id: str, connection):
        self.leader_id = leader_id
        self.connection = connection
        self.channel = connection.channel()
        self.nodes: list[Node] = []
        self.is_leader = False

    async def add_node(self, node: Node) -> None:
        self.nodes.append(node)
        print(f"Node {node.node_id} added to leader {self.leader_id}")

    async def replicate(self, file_hash: str, file_data: bytes, user_id: str, file_name: str, action: str) -> None:
        for node in self.nodes:
            await node.store(file_hash, file_data, user_id, file_name) if action == "store" else await node.delete(file_hash)

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