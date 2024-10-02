"""
Flask Hub Server - Coordinates between Web App, LLM, and Grasshopper
"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import json
import urllib.request
import os
import uuid

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

connected_clients = set()
gh_clients = set()
results = {}

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

DEFAULT_MODEL = os.environ.get("LLM_MODEL", "llama3.2:1b")
DEFAULT_HOST_URL = os.environ.get("LLM_HOST_URL", "http://localhost:11434/v1/chat/completions")


def call_llm(prompt, params_json):
    system_prompt = f"""You control a parametric 3D model.

AVAILABLE PARAMETERS:
{params_json}

Return ONLY a JSON object with parameter names and new values.
"""
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
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
    params = app.config.get("CURRENT_PARAMS", [])
    emit('params_init', {'params': params})


@socketio.on('disconnect')
def handle_disconnect():
    connected_clients.discard(request.sid)
    gh_clients.discard(request.sid)


@socketio.on('params_update')
def handle_params_update(data):
    params = data.get('params', {})
    for client_sid in gh_clients:
        socketio.emit('params_to_gh', {'params': params}, to=client_sid)
    emit('params_ack', {'status': 'sent'})


@socketio.on('gh_connect')
def handle_gh_connect(data=None):
    gh_clients.add(request.sid)
    emit('gh_connect_ack', {'status': 'connected'})


@socketio.on('gh_params_register')
def handle_gh_params_register(data):
    params = data.get('params', [])
    app.config["CURRENT_PARAMS"] = params
    web_clients = connected_clients - gh_clients
    for client_sid in web_clients:
        socketio.emit('params_sync', {'params': params}, to=client_sid)


@socketio.on('gh_geometry')
def handle_gh_geometry(data):
    """GH sends computed geometry."""
    request_id = data.get('request_id')
    geometry = data.get('geometry')

    # Push to web clients
    web_clients = connected_clients - gh_clients
    for client_sid in web_clients:
        socketio.emit('geometry_result', {
            'request_id': request_id,
            'geometry': geometry
        }, to=client_sid)


@app.route("/geometry_callback", methods=["POST"])
def geometry_callback():
    """HTTP fallback for geometry from GH."""
    body = request.json
    request_id = body.get("request_id")
    geometry = body.get("geometry")

    if connected_clients:
        socketio.emit('geometry_result', {
            'request_id': request_id,
            'geometry': geometry
        })

    return jsonify({"status": "ok"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/chat", methods=["POST"])
def chat():
    body = request.json
    prompt = body.get("prompt")
    params = body.get("params", [])

    if not prompt:
        return jsonify({"error": "No prompt"}), 400

    request_id = str(uuid.uuid4())

    try:
        llm_response = call_llm(prompt, json.dumps(params))
        param_updates = json.loads(llm_response)

        # Send to GH
        for client_sid in gh_clients:
            socketio.emit('params_to_gh', {
                'request_id': request_id,
                'params': param_updates
            }, to=client_sid)

        return jsonify({"request_id": request_id, "params": param_updates})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"Flask Hub on port {port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
