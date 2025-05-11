import os
import pika
import requests
from node import Node

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
CORE_SERVICE_URL = os.getenv("CORE_SERVICE_URL", "http://core:5001")
NODE_AUTH_TOKEN = os.getenv("NODE_AUTH_TOKEN", "secure_node_token_123")

node = Node(node_id="node_1")  # Unique node ID for this instance

connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()

def register_node():
    try:
        response = requests.post(
            f"{CORE_SERVICE_URL}/register_node",
            json={"node_id": node.node_id},
            headers={"X-Node-Auth-Token": NODE_AUTH_TOKEN}
        )
        if response.status_code == 200:
            print(f"Node {node.node_id} registered successfully")
            is_replica = response.json().get("is_replica", False)
            return is_replica
        else:
            print(f"Failed to register node: {response.json().get('error')}")
            exit(1)
    except Exception as e:
        print(f"Error registering node: {str(e)}")
        exit(1)

is_replica = register_node()
node.setup_rabbitmq(channel, is_replica)
print(f"Node {node.node_id} (Replica: {is_replica}) started, listening for messages...")
channel.start_consuming()