from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import requests
import logging

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:8000"}})
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

CORE_SERVICE_URL = "http://core:5001"

def authenticate_token(token):
    if not token:
        return None
    try:
        response = requests.get(f"{CORE_SERVICE_URL}/verify_token", headers={"X-Auth-Token": token})
        if response.status_code == 200:
            return response.json().get("user_id")
        return None
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        return None

@app.route("/api/<path:path>", methods=["OPTIONS"])
def handle_options(path):
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "http://localhost:8000")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, X-Auth-Token")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    return response, 200

@app.route("/api/register", methods=["POST"])
def register():
    try:
        logger.debug(f"Received headers: {request.headers}")
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 415
        response = requests.post(f"{CORE_SERVICE_URL}/register", json=data)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@app.route("/api/login", methods=["POST"])
def login():
    try:
        logger.debug(f"Received headers: {request.headers}")
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 415
        response = requests.post(f"{CORE_SERVICE_URL}/login", json=data)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

@app.route("/api/upload", methods=["POST"])
def upload_file():
    try:
        token = request.headers.get("X-Auth-Token")
        user_id = authenticate_token(token)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file provided"}), 400
        files = {"file": (file.filename, file.read())}
        headers = {"X-Auth-Token": token, "X-User-ID": user_id}
        response = requests.post(f"{CORE_SERVICE_URL}/upload", files=files, headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@app.route("/api/download/<file_hash>", methods=["GET"])
def download_file(file_hash):
    try:
        token = request.headers.get("X-Auth-Token")
        user_id = authenticate_token(token)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        headers = {"X-Auth-Token": token, "X-User-ID": user_id}
        response = requests.get(f"{CORE_SERVICE_URL}/download/{file_hash}", headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

@app.route("/api/search", methods=["GET"])
def search_file():
    try:
        token = request.headers.get("X-Auth-Token")
        user_id = authenticate_token(token)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        query = request.args.get("query", "")
        headers = {"X-Auth-Token": token, "X-User-ID": user_id}
        response = requests.get(f"{CORE_SERVICE_URL}/search?query={query}", headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({"error": f"Search failed: {str(e)}"}), 500

@app.route("/api/list", methods=["GET"])
def list_files():
    try:
        token = request.headers.get("X-Auth-Token")
        user_id = authenticate_token(token)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        headers = {"X-Auth-Token": token, "X-User-ID": user_id}
        response = requests.get(f"{CORE_SERVICE_URL}/list", headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"List error: {str(e)}")
        return jsonify({"error": f"List failed: {str(e)}"}), 500

@app.route("/api/delete/<file_hash>", methods=["DELETE"])
def delete_file(file_hash):
    try:
        token = request.headers.get("X-Auth-Token")
        user_id = authenticate_token(token)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        headers = {"X-Auth-Token": token, "X-User-ID": user_id}
        response = requests.delete(f"{CORE_SERVICE_URL}/delete/{file_hash}", headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        return jsonify({"error": f"Delete failed: {str(e)}"}), 500

@app.route("/api/update/<file_hash>", methods=["PUT"])
def update_file(file_hash):
    try:
        token = request.headers.get("X-Auth-Token")
        user_id = authenticate_token(token)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file provided"}), 400
        files = {"file": (file.filename, file.read())}
        headers = {"X-Auth-Token": token, "X-User-ID": user_id}
        response = requests.put(f"{CORE_SERVICE_URL}/update/{file_hash}", files=files, headers=headers)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Update error: {str(e)}")
        return jsonify({"error": f"Update failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)