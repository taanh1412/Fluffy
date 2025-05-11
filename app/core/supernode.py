import asyncio
import hashlib
import sqlite3
import os
import uuid
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import pika
import redis.asyncio as redis
from leader import Leader
import time

class SuperNode:
    def __init__(self):
        self.rabbitmq_connection = None
        self.primary = None
        self.replica = None
        self.redis_client = None
        self.db_path = os.getenv("DB_PATH", "/data/supernode.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.user_files: Dict[str, Set[str]] = {}
        self._initialize_services()
        self._initialize_db()

    def _initialize_services(self):
        max_retries = 5
        retry_delay = 5
        for attempt in range(max_retries):
            try:
                rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
                self.rabbitmq_connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=rabbitmq_host)
                )
                self.primary = Leader("Primary_Leader", self.rabbitmq_connection)
                self.replica = Leader("Replica_Leader", self.rabbitmq_connection)
                self.primary.is_leader = True
                print("Connected to RabbitMQ successfully")
                break
            except pika.exceptions.AMQPConnectionError as e:
                if attempt < max_retries - 1:
                    print(f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise Exception(f"Max retries reached. Failed to connect to RabbitMQ: {e}")
        for attempt in range(max_retries):
            try:
                redis_host = os.getenv("REDIS_HOST", "redis")
                self.redis_client = redis.Redis(host=redis_host, port=6379, decode_responses=False)
                asyncio.run(self.redis_client.ping())
                print("Connected to Redis successfully")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Failed to connect to Redis (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise Exception(f"Max retries reached. Failed to connect to Redis: {e}")

    def _get_db_connection(self):
        """Create a new SQLite connection for the current thread."""
        conn = sqlite3.connect(self.db_path)
        return conn

    def _initialize_db(self):
        """Initialize the database schema."""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS users
                   (user_id TEXT PRIMARY KEY, password_hash TEXT, token TEXT)"""
            )
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS search_index
                   (file_name TEXT, file_hash TEXT, PRIMARY KEY (file_name, file_hash))"""
            )
            conn.commit()

    async def register_user(self, username: str, password: str) -> Optional[str]:
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            token = str(uuid.uuid4())
            try:
                cursor.execute(
                    "INSERT INTO users (user_id, password_hash, token) VALUES (?, ?, ?)",
                    (username, password_hash, token)
                )
                conn.commit()
                return token
            except sqlite3.IntegrityError:
                return None

    async def login_user(self, username: str, password: str) -> Optional[str]:
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute(
                "SELECT token FROM users WHERE user_id = ? AND password_hash = ?",
                (username, password_hash)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    async def add_node(self, node, is_replica: bool = False) -> None:
        leader = self.replica if is_replica else self.primary
        print(f"Adding node {node.node_id} to {'replica' if is_replica else 'primary'} leader")
        await leader.add_node(node)

    async def upload_file(self, file_data: bytes, file_name: str, user_id: str) -> str:
        if user_id not in self.user_files:
            self.user_files[user_id] = set()
        file_hash = hashlib.md5(file_data + user_id.encode() + file_name.encode() + str(datetime.now()).encode()).hexdigest()
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO search_index (file_name, file_hash) VALUES (?, ?)", (file_name, file_hash))
            conn.commit()
        self.user_files[user_id].add(file_hash)
        await self.redis_client.set(file_hash, file_data)
        tasks = [
            self.primary.replicate(file_hash, file_data, user_id, file_name, "store"),
            self.replica.replicate(file_hash, file_data, user_id, file_name, "store")
        ]
        await asyncio.gather(*tasks)
        await self.primary.append_entries()
        await self.replica.append_entries()
        return file_hash

    async def download_file(self, file_hash: str, user_id: str) -> Optional[Tuple[bytes, str]]:
        if file_hash not in self.user_files.get(user_id, set()):
            return None
        cached_data = await self.redis_client.get(file_hash)
        if cached_data:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT file_name FROM search_index WHERE file_hash = ?", (file_hash,))
                file_name = cursor.fetchone()[0]
            return cached_data, file_name
        for leader in [self.primary, self.replica]:
            for node in leader.nodes:
                data = await node.retrieve(file_hash)
                if data:
                    await self.redis_client.set(file_hash, data[0])
                    return data[0], data[2]
        return None

    async def search_file(self, query: str, user_id: str) -> List[Tuple[str, str]]:
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_name, file_hash FROM search_index WHERE file_name LIKE ?", (f"%{query}%",))
            results = [(row[1], row[0]) for row in cursor.fetchall() if row[1] in self.user_files.get(user_id, set())]
        return results

    async def list_files(self, user_id: str) -> List[Tuple[str, str]]:
        results = []
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            for file_hash in self.user_files.get(user_id, set()):
                cursor.execute("SELECT file_name FROM search_index WHERE file_hash = ?", (file_hash,))
                row = cursor.fetchone()
                if row:
                    results.append((file_hash, row[0]))
        return results

    async def delete_file(self, file_hash: str, user_id: str) -> bool:
        if file_hash not in self.user_files.get(user_id, set()):
            return False
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM search_index WHERE file_hash = ?", (file_hash,))
            conn.commit()
        self.user_files[user_id].remove(file_hash)
        await self.redis_client.delete(file_hash)
        tasks = [
            self.primary.replicate(file_hash, b"", user_id, "", "delete"),
            self.replica.replicate(file_hash, b"", user_id, "", "delete")
        ]
        await asyncio.gather(*tasks)
        await self.primary.append_entries()
        await self.replica.append_entries()
        return True

    async def update_file(self, file_hash: str, new_file_data: bytes, user_id: str) -> bool:
        if file_hash not in self.user_files.get(user_id, set()):
            return False
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_name FROM search_index WHERE file_hash = ?", (file_hash,))
            file_name = cursor.fetchone()[0]
        await self.delete_file(file_hash, user_id)
        new_hash = await self.upload_file(new_file_data, file_name, user_id)
        return new_hash != file_hash

    async def failover(self):
        if not self.primary.is_leader:
            await self.replica.request_vote(self.replica.leader_id)
            self.primary, self.replica = self.replica, self.primary