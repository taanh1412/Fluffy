from flask import Flask, request, jsonify
from flask_cors import CORS
from core.client import Client
import asyncio

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
client = Client()

async def run_async(coroutine):
    loop = asyncio.get_event_loop()
    return await coroutine

@app.route('/api/upload', methods=['POST'])
async def upload_file():
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file provided"}), 400
    file_data = file.read()
    file_name = file.filename
    file_hash = await run_async(client.upload(file_data, file_name, user_id))
    return jsonify({"file_hash": file_hash, "file_name": file_name}), 201

@app.route('/api/download/<file_hash>', methods=['GET'])
async def download_file(file_hash):
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    result = await run_async(client.download(file_hash, user_id))
    if result:
        data, file_name = result
        return jsonify({"file_hash": file_hash, "file_name": file_name, "data": data.decode('utf-8', errors='ignore')}), 200
    return jsonify({"error": "File not found"}), 404

@app.route('/api/search', methods=['GET'])
async def search_file():
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    query = request.args.get('query', '')
    results = await run_async(client.search(query, user_id))
    return jsonify([{"file_hash": r[0], "file_name": r[1]} for r in results]), 200

@app.route('/api/list', methods=['GET'])
async def list_files():
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    files = await run_async(client.list(user_id))
    return jsonify([{"file_hash": f[0], "file_name": f[1]} for f in files]), 200

@app.route('/api/delete/<file_hash>', methods=['DELETE'])
async def delete_file(file_hash):
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    success = await run_async(client.delete(file_hash, user_id))
    return jsonify({"success": success}), 200 if success else 404

@app.route('/api/update/<file_hash>', methods=['PUT'])
async def update_file(file_hash):
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file provided"}), 400
    new_data = file.read()
    success = await run_async(client.update(file_hash, new_data, user_id))
    return jsonify({"success": success}), 200 if success else 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)