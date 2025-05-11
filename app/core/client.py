import asyncio
from core.supernode import SuperNode

class Client:
    def __init__(self):
        self.supernode = SuperNode()

    async def upload_file(self, file_data: bytes, file_name: str) -> str:
        return await self.supernode.distribute_and_replicate(file_data, file_name)

    async def download_file(self, file_hash: str) -> bytes:
        return await self.supernode.retrieve_file(file_hash)

    async def search_files(self, query: str) -> list:
        return await self.supernode.search_file(query)

async def main():
    client = Client()
    file_data = b"Sample file content"
    file_hash = await client.upload_file(file_data, "sample.txt")
    data = await client.download_file(file_hash)
    print(f"Downloaded data: {data}")
    results = await client.search_files("sample")
    print(f"Search results: {results}")

if __name__ == "__main__":
        asyncio.run(main())