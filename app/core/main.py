from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
from supernode import SuperNode
import asyncio

app = Flask(__name__)

# Configure CORS to allow requests from the frontend origin
CORS(app, resources={r"/api/*": {
    "origins": "http://localhost:8000",
    "allow_headers": ["Content-Type", "X-Auth-Token"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
}})

supernode = SuperNode()

@app.route('/api/register', methods=['POST'])
async def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    token = await supernode.register_user(username, password)
    if token:
        return jsonify({"token": token, "user_id": username})
    return jsonify({"error": "Registration failed: User already exists"}), 400

@app.route('/api/login', methods=['POST'])
async def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    token = await supernode.login_user(username, password)
    if token:
        return jsonify({"token": token, "user_id": username})
    return jsonify({"error": "Login failed: Invalid credentials"}), 401

@app.route('/api/upload', methods=['POST'])
async def upload_file():
    token = request.headers.get("X-Auth-Token") or request.form.get("token")
    if not token or not supernode.validate_token(token):
        return jsonify({"error": "Authentication required"}), 401
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    file_data = file.read()
    user_id = supernode.get_user_id_from_token(token)
    file_hash = await supernode.upload_file(file_data, file.filename, user_id)
    return jsonify({"file_hash": file_hash})

@app.route('/api/download/<file_hash>', methods=['GET'])
async def download_file(file_hash):
    token = request.headers.get("X-Auth-Token")
    if not token or not supernode.validate_token(token):
        return jsonify({"error": "Authentication required"}), 401
    user_id = supernode.get_user_id_from_token(token)
    result = await supernode.download_file(file_hash, user_id)
    if result:
        return jsonify({"data": result[1], "file_hash": file_hash})
    return jsonify({"error": "File not found or unauthorized"}), 404

@app.route('/api/search', methods=['GET'])
async def search_file():
    token = request.headers.get("X-Auth-Token")
    if not token or not supernode.validate_token(token):
        return jsonify({"error": "Authentication required"}), 401
    query = request.args.get("query", "")
    user_id = supernode.get_user_id_from_token(token)
    results = await supernode.search_file(query, user_id)
    return jsonify(results)

@app.route('/api/list', methods=['GET'])
async def list_files():
    token = request.headers.get("X-Auth-Token")
    if not token or not supernode.validate_token(token):
        return jsonify({"error": "Authentication required"}), 401
    user_id = supernode.get_user_id_from_token(token)
    files = await supernode.list_files(user_id)
    return jsonify(files)

@app.route('/api/delete/<file_hash>', methods=['DELETE'])
async def delete_file(file_hash):
    token = request.headers.get("X-Auth-Token")
    if not token or not supernode.validate_token(token):
        return jsonify({"error": "Authentication required"}), 401
    user_id = supernode.get_user_id_from_token(token)
    success = await supernode.delete_file(file_hash, user_id)
    return jsonify({"success": success})

@app.route('/api/update/<file_hash>', methods=['PUT'])
async def update_file(file_hash):
    token = request.headers.get("X-Auth-Token") or request.form.get("token")
    if not token or not supernode.validate_token(token):
        return jsonify({"error": "Authentication required"}), 401
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    file_data = file.read()
    user_id = supernode.get_user_id_from_token(token)
    success = await supernode.update_file(file_hash, file_data, user_id)
    return jsonify({"success": success})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)