import asyncio
from supernode import SuperNode

class Client:
    def __init__(self):
        self.supernode = SuperNode()

    async def upload(self, file_data, file_name, user_id):
        return await self.supernode.upload_file(file_data, file_name, user_id)

    async def download(self, file_hash, user_id):
        return await self.supernode.download_file(file_hash, user_id)

    async def search(self, query, user_id):
        return await self.supernode.search_file(query, user_id)

    async def list(self, user_id):
        return await self.supernode.list_files(user_id)

    async def delete(self, file_hash, user_id):
        return await self.supernode.delete_file(file_hash, user_id)

    async def update(self, file_hash, new_file_data, user_id):
        return await self.supernode.update_file(file_hash, new_file_data, user_id)

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