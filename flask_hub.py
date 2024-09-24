"""
Flask Hub Server - Coordinates between Web App, LLM, and Grasshopper
"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import json
import urllib.request
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

connected_clients = set()
gh_clients = set()

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

DEFAULT_MODEL = os.environ.get("LLM_MODEL", "llama3.2:1b")
DEFAULT_HOST_URL = os.environ.get("LLM_HOST_URL", "http://localhost:11434/v1/chat/completions")


def call_llm(prompt, params_json):
    system_prompt = f"""You control a parametric 3D model. Adjust parameters based on user requests.

AVAILABLE PARAMETERS:
{params_json}

Return ONLY a JSON object with parameter names and new values.
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    payload = {"model": DEFAULT_MODEL, "messages": messages, "temperature": 0.3}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(DEFAULT_HOST_URL, data=data,
                                  headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"]


@socketio.on('connect')
def handle_connect():
    connected_clients.add(request.sid)
    print(f"Client connected: {request.sid}")
    # Send current params to new client
    params = app.config.get("CURRENT_PARAMS", [])
    emit('params_init', {'params': params})


@socketio.on('disconnect')
def handle_disconnect():
    connected_clients.discard(request.sid)
    gh_clients.discard(request.sid)
    print(f"Client disconnected: {request.sid}")


@socketio.on('params_update')
def handle_params_update(data):
    """Receive param updates from webapp, forward to GH."""
    params = data.get('params', {})
    print(f"Received params_update: {params}")

    # Forward to GH clients
    for client_sid in gh_clients:
        socketio.emit('params_to_gh', {'params': params}, to=client_sid)

    emit('params_ack', {'status': 'sent'})


@socketio.on('gh_connect')
def handle_gh_connect(data=None):
    """Grasshopper client identifies itself."""
    gh_clients.add(request.sid)
    print(f"Grasshopper connected: {request.sid}")
    emit('gh_connect_ack', {'status': 'connected'})


@socketio.on('gh_params_register')
def handle_gh_params_register(data):
    """GH registers its parameters."""
    params = data.get('params', [])
    app.config["CURRENT_PARAMS"] = params
    print(f"GH registered {len(params)} parameters")

    # Push to web clients
    web_clients = connected_clients - gh_clients
    for client_sid in web_clients:
        socketio.emit('params_sync', {'params': params}, to=client_sid)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "clients": len(connected_clients)})


@app.route("/chat", methods=["POST"])
def chat():
    body = request.json
    prompt = body.get("prompt")
    params = body.get("params", [])

    if not prompt:
        return jsonify({"error": "No prompt"}), 400

    try:
        llm_response = call_llm(prompt, json.dumps(params))
        param_updates = json.loads(llm_response)
        return jsonify({"status": "ok", "params": param_updates})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"Starting Flask Hub on port {port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
