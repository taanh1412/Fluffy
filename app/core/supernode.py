import asyncio
import hashlib
import platform
from typing import Dict, Optional, List
from core.leader import Leader
from core.node import Node
from collections import OrderedDict

class SuperNode:
    def __init__(self):
        self.primary = Leader("Primary_Leader")
        self.replica = Leader("Replica_Leader")
        self.data_store: Dict[str, bytes] = {}
        self.cache = OrderedDict()
        self.search_index = {}  # Simple in-memory index
        self.CACHE_SIZE = 100

    async def add_node(self, node: Node, is_replica: bool = False) -> None:
        leader = self.replica if is_replica else self.primary
        await leader.add_node(node)

    async def distribute_and_replicate(self, file_data: bytes, file_name: str) -> str:
        file_hash = hashlib.md5(file_data).hexdigest()
        self.data_store[file_hash] = file_data
        self.search_index[file_name] = file_hash

        # Cache optimization
        if len(self.cache) >= self.CACHE_SIZE:
            self.cache.popitem(last=False)
        self.cache[file_hash] = file_data

        # Replicate to primary and replica
        tasks = [
            self.primary.replicate(file_hash, file_data),
            self.replica.replicate(file_hash, file_data)
        ]
        await asyncio.gather(*tasks)
        await self.primary.append_entries()
        await self.replica.append_entries()
        return file_hash

    async def retrieve_file(self, file_hash: str) -> Optional[bytes]:
        if file_hash in self.cache:
            return self.cache[file_hash]
        for leader in [self.primary, self.replica]:
            for node in leader.nodes:
                data = await node.retrieve(file_hash)
                if data:
                    self.cache[file_hash] = data
                    return data
        return b"File not found"

    async def search_file(self, query: str) -> List[str]:
        return [hash for name, hash in self.search_index.items() if query in name]

    async def failover(self):
        if not self.primary.is_leader:
            await self.replica.request_vote(self.replica.leader_id)
            self.primary, self.replica = self.replica, self.primary

async def main():
    supernode = SuperNode()
    nodes = [Node(f"Node_{i}") for i in range(3)]
    for node, is_rep in zip(nodes, [False, True, False]):
        await supernode.add_node(node, is_rep)

    # Simulate client requests
    file_data = b"Sample file content"
    file_hash = await supernode.distribute_and_replicate(file_data, "sample.txt")
    retrieved_data = await supernode.retrieve_file(file_hash)
    print(f"Retrieved data: {retrieved_data}")
    search_results = await supernode.search_file("sample")
    print(f"Search results: {search_results}")

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())