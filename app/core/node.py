import pika
import asyncio

class Node:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.storage = {}
        self.channel = None

    def setup_rabbitmq(self, channel, is_replica: bool):
        self.channel = channel
        queue_name = f"node_{self.node_id}_{'replica' if is_replica else 'primary'}"
        self.channel.queue_declare(queue=queue_name)
        self.channel.basic_consume(queue=queue_name, on_message_callback=self.on_message, auto_ack=True)

    def on_message(self, ch, method, properties, body):
        print(f"Node {self.node_id} received message: {body}")
        # Implement message handling logic here (e.g., store file, retrieve file)

    async def store(self, file_hash: str, file_data: bytes, user_id: str, file_name: str):
        self.storage[file_hash] = (file_data, user_id, file_name)

    async def retrieve(self, file_hash: str):
        return self.storage.get(file_hash)

    async def delete(self, file_hash: str):
        if file_hash in self.storage:
            del self.storage[file_hash]
            return True
        return False