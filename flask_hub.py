"""
Flask Hub Server - Coordinates between Web App, LLM, and Grasshopper

Architecture:
- Web app sends prompts here
- Flask calls LLM to get parameter updates
- Flask POSTs params to GH's HTTP Listener
- GH processes, then POSTs geometry back here
- Web app polls for results

Run: python flask_hub.py

Configuration via .env file or environment variables:
- LLM_HOST_URL: LLM API endpoint (default: http://localhost:11434/v1/chat/completions for Ollama)
- LLM_MODEL: Model name (default: llama3.2:1b)
- OPENAI_API_KEY: API key (optional for local LLMs like Ollama)
- GH_URL: Grasshopper HTTP Listener URL (default: http://localhost:3000/update)
- PORT: Server port (default: 5001)
"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import json
import urllib.request
import uuid
import threading
import time
import os
import tempfile
import re
import ast
import traceback
import whisper

# Load .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded .env file")
except ImportError:
    print("python-dotenv not installed, using environment variables only")
    print("Install with: pip install python-dotenv")

app = Flask(__name__)

# Initialize Socket.IO with CORS support
# Use threading mode (simpler, no eventlet dependency)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
ASYNC_MODE = 'threading'

# Track connected WebSocket clients
connected_clients = set()

# Track connected Grasshopper clients (separate from web clients)
gh_clients = set()

# Enable CORS manually (works even without flask-cors package)


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Handle preflight OPTIONS requests


@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return jsonify({'status': 'ok'}), 200


# Store pending/completed requests
results = {}
results_lock = threading.Lock()

# Configuration
GH_URL = os.environ.get("GH_URL", "http://localhost:3000/update")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
DEFAULT_MODEL = os.environ.get("LLM_MODEL", "llama3.2:1b")
DEFAULT_HOST_URL = os.environ.get(
    "LLM_HOST_URL", "http://localhost:11434/v1/chat/completions")

# Cleanup old results after 5 minutes
RESULT_TTL_SECONDS = 300


def cleanup_old_results():
    """Remove results older than TTL"""
    while True:
        time.sleep(60)
        current_time = time.time()
        with results_lock:
            expired = [
                rid for rid, data in results.items()
                if current_time - data.get("timestamp", 0) > RESULT_TTL_SECONDS
            ]
            for rid in expired:
                del results[rid]


# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_results, daemon=True)
cleanup_thread.start()

# Load Whisper model (lazy loading to avoid startup delay)
whisper_model = None
WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL", "base")


def get_whisper_model():
    """Lazy load whisper model"""
    global whisper_model
    if whisper_model is None:
        print(f"[WHISPER] Loading model: {WHISPER_MODEL_SIZE}")
        whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
        print(f"[WHISPER] Model loaded successfully")
    return whisper_model


def call_llm(prompt, params_json, api_key=None, model=None, host_url=None):
    """
    Call OpenAI-compatible API to get parameter updates.

    Works with:
    - OpenAI API (https://api.openai.com/v1/chat/completions)
    - Ollama (http://localhost:11434/v1/chat/completions)
    - Any OpenAI-compatible API
    """
    url = host_url or DEFAULT_HOST_URL
    api_key = api_key or OPENAI_API_KEY
    model = model or DEFAULT_MODEL

    system_prompt = f"""You control a parametric 3D model in Grasshopper. Adjust parameters based on user requests.

AVAILABLE PARAMETERS (current values and valid ranges):
{params_json}

INTERPRETATION GUIDELINES:
- "slightly/a bit" = ~10-20% change from current value
- "more/increase/decrease" = ~25-50% change from current value
- "much/significantly/double/half" = ~50-100% change from current value
- "maximize/minimize" = set to max/min bound
- Always stay within min/max bounds
- Round to 1 decimal place

EXAMPLES:
User: "make it taller" -> {{"height": 7.5}}
User: "wider but shorter" -> {{"width": 8.0, "height": 3.0}}
User: "maximize the width" -> {{"width": 10.0}}
User: "reset to defaults" -> {{"width": 5.0, "height": 5.0}}
User: "what time is it?" -> {{}}

RESPONSE FORMAT:
- Output ONLY a valid JSON object mapping parameter names to new numeric values
- Include only parameters you want to change
- ONLY use parameters from the AVAILABLE PARAMETERS list
- ONLY include parameters that based on your interpretation need to change
- Use an empty object {{}} if the request is unrelated or no changes apply
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3  # Lower temperature for more consistent outputs
    }

    # Add JSON response format for OpenAI API (improves reliability)
    # Skip for Ollama (localhost) as support varies by model
    if "openai.com" in url or "api.openai" in url:
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Content-Type": "application/json",
    }

    # Only add Authorization header if api_key is provided (not needed for Ollama)
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers=headers, method="POST")

    print(f"Calling LLM: {url} with model {model}")

    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    return result["choices"][0]["message"]["content"]


def parse_llm_response(response):
    """Extract JSON from LLM response, handling code blocks"""
    text = response.strip()

    # Handle markdown code blocks
    if "```" in text:
        # Find content between code blocks
        parts = text.split("```")
        for part in parts[1::2]:  # Every other part (inside code blocks)
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            try:
                return json.loads(part)
            except json.JSONDecodeError:
                continue

    # Try direct JSON parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in text
        match = re.search(r'\{[^{}]*\}', text)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Could not parse LLM response as JSON: {text}")


def send_to_grasshopper(request_id, params):
    """Send parameter updates to GH via WebSocket (preferred) or HTTP fallback"""

    # Prefer WebSocket if GH clients are connected
    if gh_clients:
        for client_sid in gh_clients:
            socketio.emit('params_to_gh', {
                'request_id': request_id,
                'params': params
            }, to=client_sid)
        print(
            f"[GH] Sent params via WebSocket to {len(gh_clients)} GH client(s)")
        return "sent_via_websocket"

    # Fallback to HTTP if no WebSocket GH clients
    data = json.dumps({
        "request_id": request_id,
        "params": params
    }).encode("utf-8")

    req = urllib.request.Request(
        GH_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        raise ConnectionError(f"Failed to send to Grasshopper: {e}")


@app.route("/chat", methods=["POST"])
def chat():
    """
    Receive prompt from web app, process via LLM, forward params to GH.

    Request body:
    {
        "prompt": "make it wider",
        "params": [{"name": "width", "value": 5, "min": 0, "max": 10}, ...],
        "api_key": "sk-...",  // optional if env var set
        "model": "gpt-4o"     // optional
    }

    Response:
    {
        "request_id": "uuid",
        "status": "processing",
        "params": {"width": 8.0}  // params sent to GH
    }
    """
    body = request.json
    prompt = body.get("prompt")
    params = body.get("params", [])
    api_key = body.get("api_key")
    model = body.get("model")

    print(f"\n{'='*50}")
    print(f"[CHAT] Received prompt: {prompt}")
    print(f"[CHAT] Params from web app: {json.dumps(params, indent=2)}")

    if not prompt:
        print("[CHAT] ERROR: No prompt provided")
        return jsonify({"error": "No prompt provided"}), 400

    # Format params for LLM
    params_json = json.dumps(params, indent=2)

    request_id = str(uuid.uuid4())
    print(f"[CHAT] Request ID: {request_id}")

    with results_lock:
        results[request_id] = {
            "status": "processing",
            "timestamp": time.time()
        }

    try:
        # Call LLM to get parameter updates
        print(f"[CHAT] Calling LLM...")
        llm_response = call_llm(prompt, params_json, api_key, model)
        print(f"[CHAT] LLM raw response: {llm_response}")

        param_updates = parse_llm_response(llm_response)
        print(f"[CHAT] Parsed param updates: {param_updates}")

        with results_lock:
            results[request_id]["llm_response"] = llm_response
            results[request_id]["params"] = param_updates

        # Handle case where LLM returns empty object (no changes apply)
        if not param_updates:
            print(f"[CHAT] No parameter changes needed for this request")
            with results_lock:
                results[request_id]["status"] = "complete"
                results[request_id]["message"] = "No parameter changes applicable"
            print(
                f"[CHAT] Returning to web app - request_id: {request_id}, no changes")
            print(f"{'='*50}\n")
            return jsonify({
                "request_id": request_id,
                "status": "complete",
                "params": {},
                "message": "No parameter changes applicable to this request"
            })

        # Forward to Grasshopper
        print(f"[CHAT] Sending to Grasshopper: {GH_URL}")
        gh_response = send_to_grasshopper(request_id, param_updates)
        print(f"[CHAT] GH response: {gh_response}")

        print(
            f"[CHAT] Returning to web app - request_id: {request_id}, params: {param_updates}")
        print(f"{'='*50}\n")

        return jsonify({
            "request_id": request_id,
            "status": "processing",
            "params": param_updates
        })

    except Exception as e:
        print(f"[CHAT] ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()

        with results_lock:
            results[request_id] = {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
        return jsonify({
            "request_id": request_id,
            "status": "error",
            "error": str(e)
        }), 500


@app.route("/geometry_callback", methods=["POST"])
def geometry_callback():
    """
    Receive computed geometry and current params from Grasshopper.

    Request body:
    {
        "request_id": "uuid",
        "geometry": [{mesh data}, ...],
        "params": [{"name": "width", "value": 5, ...}, ...]  // optional - current param values
    }
    """
    body = request.json
    request_id = body.get("request_id")
    geometry = body.get("geometry")
    params = body.get("params")

    print(f"\n{'='*50}")
    print(f"[GEOMETRY] Received callback for request_id: {request_id}")
    print(
        f"[GEOMETRY] Geometry meshes count: {len(geometry) if geometry else 0}")

    if not request_id:
        print("[GEOMETRY] ERROR: No request_id provided")
        return jsonify({"error": "No request_id provided"}), 400

    # Update current params if provided (for two-way sync)
    if params:
        print(
            f"[GEOMETRY] Raw params type: {type(params)}, length: {len(params) if hasattr(params, '__len__') else 'N/A'}")

        # If params is a string, try to parse it as JSON or Python literal
        if isinstance(params, str):
            try:
                params = json.loads(params)
                print(f"[GEOMETRY] Parsed params string as JSON")
            except json.JSONDecodeError:
                # Try Python literal (single quotes instead of double)
                try:
                    params = ast.literal_eval(params)
                    print(f"[GEOMETRY] Parsed params string as Python literal")
                except:
                    print(f"[GEOMETRY] WARNING: Could not parse params string")
                    print(f"[GEOMETRY] First 100 chars: {params[:100]}")
                    params = None

        if isinstance(params, list) and len(params) > 0:
            print(
                f"[GEOMETRY] First item type: {type(params[0])}, value: {params[0]}")

        # Validate params format - should be list of dicts with 'name' and 'value'
        if isinstance(params, list) and len(params) > 0:
            if isinstance(params[0], dict) and 'name' in params[0]:
                app.config["CURRENT_PARAMS"] = params
                print(f"[GEOMETRY] Updated {len(params)} parameters from GH")
                for p in params:
                    print(f"  - {p.get('name')}: {p.get('value')}")
            else:
                print(
                    f"[GEOMETRY] WARNING: params format not recognized, skipping update")
                params = None  # Don't use invalid params for WebSocket
        elif params is not None:
            print(f"[GEOMETRY] WARNING: params is not a list or is empty")
            params = None

    with results_lock:
        if request_id in results:
            results[request_id]["status"] = "complete"
            results[request_id]["geometry"] = geometry
            results[request_id]["completed_at"] = time.time()
            print(f"[GEOMETRY] Updated existing result - status: complete")
        else:
            # Create new entry if request_id not found (edge case)
            results[request_id] = {
                "status": "complete",
                "geometry": geometry,
                "timestamp": time.time(),
                "completed_at": time.time()
            }
            print(f"[GEOMETRY] Created new result entry - status: complete")

    # Cache geometry for new client connections
    if geometry:
        app.config["CURRENT_GEOMETRY"] = geometry

    # Push to all connected WebSocket clients
    if connected_clients:
        socketio.emit('geometry_result', {
            'request_id': request_id,
            'geometry': geometry,
            'status': 'complete'
        })
        print(
            f"[GEOMETRY] Pushed geometry to {len(connected_clients)} WebSocket clients")

        # Also emit params_sync if params changed (for GH slider changes)
        if params:
            socketio.emit('params_sync', {
                'params': params,
                'source': 'grasshopper'
            })
            print(f"[GEOMETRY] Pushed params_sync to WebSocket clients")

    print(f"{'='*50}\n")
    return jsonify({"status": "ok"})


@app.route("/result/<request_id>", methods=["GET"])
def get_result(request_id):
    """
    Poll for result status and data.

    Response statuses:
    - "processing": LLM/GH still working
    - "complete": Geometry ready in response
    - "error": Something failed
    - "not_found": Unknown request_id
    """
    with results_lock:
        result = results.get(request_id)
        if result is None:
            print(f"[POLL] Request {request_id[:8]}... not found")
            return jsonify({"status": "not_found"}), 404
        print(
            f"[POLL] Request {request_id[:8]}... status: {result.get('status')}")
        return jsonify(result)


@app.route("/transcribe", methods=["POST"])
def transcribe():
    """
    Transcribe audio using local Whisper model.

    Request: multipart/form-data with 'audio' file field
    Response: {"text": "transcribed text", "language": "en"}
    """
    print(f"\n{'='*50}")
    print(f"[TRANSCRIBE] Received audio transcription request")

    if 'audio' not in request.files:
        print("[TRANSCRIBE] ERROR: No audio file provided")
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']

    if audio_file.filename == '':
        print("[TRANSCRIBE] ERROR: Empty filename")
        return jsonify({"error": "Empty filename"}), 400

    try:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            audio_file.save(tmp.name)
            tmp_path = tmp.name
            print(f"[TRANSCRIBE] Saved audio to: {tmp_path}")

        # Load model and transcribe
        model = get_whisper_model()
        print(f"[TRANSCRIBE] Transcribing...")
        result = model.transcribe(tmp_path)

        # Clean up temp file
        os.unlink(tmp_path)

        text = result["text"].strip()
        language = result.get("language", "unknown")

        print(f"[TRANSCRIBE] Result: '{text}' (language: {language})")
        print(f"{'='*50}\n")

        return jsonify({
            "text": text,
            "language": language
        })

    except Exception as e:
        print(f"[TRANSCRIBE] ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "gh_url": GH_URL,
        "pending_requests": len([r for r in results.values() if r.get("status") == "processing"])
    })


@app.route("/params", methods=["POST"])
def register_params():
    """
    GH posts current params here (on startup or when sliders change).
    This syncs params to web clients via WebSocket.
    """
    body = request.json
    params = body.get("params", [])

    app.config["CURRENT_PARAMS"] = params

    print(f"\n{'='*50}")
    print(f"[PARAMS] Registered {len(params)} parameters from GH:")
    for p in params:
        print(
            f"  - {p.get('name')}: {p.get('value')} (range: {p.get('min')} - {p.get('max')})")

    # Push to WebSocket clients if any are connected
    if connected_clients:
        socketio.emit('params_sync', {
            'params': params,
            'source': 'grasshopper'
        })
        print(
            f"[PARAMS] Pushed params_sync to {len(connected_clients)} WebSocket clients")

    print(f"{'='*50}\n")
    return jsonify({"status": "ok", "count": len(params)})


@app.route("/params", methods=["GET"])
def get_params():
    """Get currently registered params (if GH has sent them)"""
    params = app.config.get("CURRENT_PARAMS", [])
    print(f"[PARAMS] Web app fetched {len(params)} parameters")
    return jsonify({"params": params})


@app.route("/update", methods=["POST"])
def update_params():
    """
    Direct parameter update from webapp to GH (no LLM involved).

    Request body:
    {
        "params": {"width": 5.0, "height": 3.2}
    }
    """
    body = request.json
    params = body.get("params", {})

    print(f"\n{'='*50}")
    print(f"[UPDATE] Direct param update from webapp")
    print(f"[UPDATE] Params: {params}")

    if not params:
        return jsonify({"error": "No params provided"}), 400

    request_id = str(uuid.uuid4())

    # Store for polling
    with results_lock:
        results[request_id] = {
            "status": "processing",
            "timestamp": time.time()
        }

    try:
        # Forward to Grasshopper
        send_to_grasshopper(request_id, params)
        print(f"[UPDATE] Sent to GH, request_id: {request_id}")
        print(f"{'='*50}\n")

        return jsonify({
            "request_id": request_id,
            "status": "processing",
            "params": params
        })
    except Exception as e:
        print(f"[UPDATE] ERROR: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# WEBSOCKET EVENT HANDLERS
# ============================================================

@socketio.on('connect')
def handle_connect():
    """Client connected via WebSocket"""
    connected_clients.add(request.sid)
    print(
        f"[SOCKET] Client connected: {request.sid} (total: {len(connected_clients)})")

    # Send current params to newly connected client
    params = app.config.get("CURRENT_PARAMS", [])
    emit('params_init', {'params': params})

    # Send cached geometry if available (for web clients reconnecting)
    cached_geometry = app.config.get("CURRENT_GEOMETRY")
    if cached_geometry:
        emit('geometry_result', {
            'request_id': 'cached',
            'geometry': cached_geometry,
            'status': 'complete'
        })
        print(
            f"[SOCKET] Sent cached geometry ({len(cached_geometry)} meshes) to new client")


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    connected_clients.discard(request.sid)
    was_gh = request.sid in gh_clients
    gh_clients.discard(request.sid)
    client_type = "GH" if was_gh else "Web"
    print(f"[SOCKET] {client_type} client disconnected: {request.sid} (web: {len(connected_clients - gh_clients)}, gh: {len(gh_clients)})")


@socketio.on('params_update')
def handle_params_update(data):
    """
    Receive param updates from webapp, forward to GH and broadcast to other clients.

    Expected data: { "params": {"width": 5.0, "height": 3.2} }
    """
    params = data.get('params', {})
    sender_sid = request.sid
    print(f"[SOCKET] Received params_update from {sender_sid}: {params}")

    if not params:
        emit('error', {'message': 'No params provided'})
        return

    request_id = str(uuid.uuid4())

    # Store for tracking
    with results_lock:
        results[request_id] = {
            "status": "processing",
            "timestamp": time.time(),
            "source": "websocket"
        }

    try:
        send_to_grasshopper(request_id, params)
        emit('params_ack', {
            'request_id': request_id,
            'params': params,
            'status': 'sent_to_gh'
        })

        # Broadcast slider change to all OTHER web clients
        other_web_clients = (connected_clients - gh_clients) - {sender_sid}
        for client_sid in other_web_clients:
            socketio.emit('params_broadcast', {
                'params': params,
                'source': 'other_client'
            }, to=client_sid)
        if other_web_clients:
            print(
                f"[SOCKET] Broadcast params to {len(other_web_clients)} other clients")

        print(f"[SOCKET] Params sent to GH, request_id: {request_id}")
    except Exception as e:
        print(f"[SOCKET] Error sending to GH: {e}")
        emit('error', {'message': str(e), 'request_id': request_id})


@socketio.on('chat_request')
def handle_chat_request(data):
    """
    Handle chat/LLM requests via WebSocket and broadcast to all clients.

    Expected data: {
        "prompt": "make it wider",
        "params": [{"name": "width", "value": 5, "min": 0, "max": 10}, ...],
        "username": "John"  // optional
    }
    """
    prompt = data.get('prompt')
    params = data.get('params', [])
    api_key = data.get('api_key')
    model = data.get('model')
    username = data.get('username', 'User')
    sender_sid = request.sid

    print(
        f"[SOCKET] Received chat_request from {sender_sid} ({username}): {prompt}")

    if not prompt:
        emit('error', {'message': 'No prompt provided'})
        return

    request_id = str(uuid.uuid4())
    web_clients = connected_clients - gh_clients

    # Broadcast user message to ALL web clients (including sender)
    for client_sid in web_clients:
        socketio.emit('chat_message', {
            'request_id': request_id,
            'type': 'user',
            'content': prompt,
            'username': username,
            'from_self': client_sid == sender_sid
        }, to=client_sid)

    # Notify all clients that LLM is processing
    for client_sid in web_clients:
        socketio.emit('chat_processing', {
            'request_id': request_id,
            'status': 'calling_llm'
        }, to=client_sid)

    try:
        params_json = json.dumps(params, indent=2)
        llm_response = call_llm(prompt, params_json, api_key, model)
        param_updates = parse_llm_response(llm_response)

        print(f"[SOCKET] LLM returned params: {param_updates}")

        # Handle case where LLM returns empty object (no changes apply)
        if not param_updates:
            print(f"[SOCKET] No parameter changes needed for this request")
            for client_sid in web_clients:
                socketio.emit('chat_llm_response', {
                    'request_id': request_id,
                    'type': 'assistant',
                    'params': {},
                    'status': 'complete',
                    'message': 'No parameter changes applicable to this request'
                }, to=client_sid)
            return

        # Broadcast LLM response to ALL web clients
        for client_sid in web_clients:
            socketio.emit('chat_llm_response', {
                'request_id': request_id,
                'type': 'assistant',
                'params': param_updates,
                'status': 'sending_to_gh'
            }, to=client_sid)

        send_to_grasshopper(request_id, param_updates)

        with results_lock:
            results[request_id] = {
                "status": "processing",
                "params": param_updates,
                "timestamp": time.time()
            }

    except Exception as e:
        print(f"[SOCKET] Chat error: {e}")
        # Broadcast error to all clients
        for client_sid in web_clients:
            socketio.emit('error', {
                'message': str(e),
                'request_id': request_id
            }, to=client_sid)


# ============================================================
# GRASSHOPPER WEBSOCKET EVENT HANDLERS
# ============================================================

@socketio.on('gh_connect')
def handle_gh_connect(data=None):
    """Grasshopper client connected and identified itself."""
    gh_clients.add(request.sid)
    print(
        f"[GH-SOCKET] Grasshopper connected: {request.sid} (total GH clients: {len(gh_clients)})")

    # Send current params to newly connected GH client
    params = app.config.get("CURRENT_PARAMS", [])
    emit('params_init', {'params': params})
    emit('gh_connect_ack', {'status': 'connected', 'client_id': request.sid})


@socketio.on('gh_params_register')
def handle_gh_params_register(data):
    """
    Grasshopper registers its available parameters.

    Expected data: { "params": [{"name": "width", "value": 5, "min": 0, "max": 10}, ...] }
    """
    params = data.get('params', [])

    print(f"\n{'='*50}")
    print(
        f"[GH-SOCKET] Received params registration: {len(params)} parameters")
    for p in params:
        print(
            f"  - {p.get('name')}: {p.get('value')} (range: {p.get('min')} - {p.get('max')})")

    # Store params
    app.config["CURRENT_PARAMS"] = params

    # Push to web clients
    web_clients = connected_clients - gh_clients
    if web_clients:
        for client_sid in web_clients:
            socketio.emit('params_sync', {
                'params': params,
                'source': 'grasshopper'
            }, to=client_sid)
        print(
            f"[GH-SOCKET] Pushed params_sync to {len(web_clients)} web clients")

    emit('params_ack', {'status': 'registered', 'count': len(params)})
    print(f"{'='*50}\n")


@socketio.on('gh_geometry')
def handle_gh_geometry(data):
    """
    Grasshopper sends computed geometry.

    Expected data: {
        "request_id": "uuid",
        "geometry": [{mesh data}, ...],
        "params": [{"name": "width", "value": 5, ...}, ...]  // optional
    }
    """
    request_id = data.get('request_id')
    geometry = data.get('geometry')
    params = data.get('params')

    print(f"\n{'='*50}")
    print(f"[GH-SOCKET] Received geometry for request_id: {request_id}")
    print(
        f"[GH-SOCKET] Geometry meshes count: {len(geometry) if geometry else 0}")

    if not request_id:
        emit('error', {'message': 'No request_id provided'})
        return

    # Update current params if provided
    if params and isinstance(params, list) and len(params) > 0:
        if isinstance(params[0], dict) and 'name' in params[0]:
            app.config["CURRENT_PARAMS"] = params
            print(f"[GH-SOCKET] Updated {len(params)} parameters from GH")

    # Store result
    with results_lock:
        if request_id in results:
            results[request_id]["status"] = "complete"
            results[request_id]["geometry"] = geometry
            results[request_id]["completed_at"] = time.time()
        else:
            results[request_id] = {
                "status": "complete",
                "geometry": geometry,
                "timestamp": time.time(),
                "completed_at": time.time()
            }

    # Cache geometry for new client connections
    if geometry:
        app.config["CURRENT_GEOMETRY"] = geometry

    # Push geometry to web clients only (not back to GH)
    web_clients = connected_clients - gh_clients
    if web_clients:
        for client_sid in web_clients:
            socketio.emit('geometry_result', {
                'request_id': request_id,
                'geometry': geometry,
                'status': 'complete'
            }, to=client_sid)
        print(f"[GH-SOCKET] Pushed geometry to {len(web_clients)} web clients")

        # Also emit params_sync if params changed
        if params:
            for client_sid in web_clients:
                socketio.emit('params_sync', {
                    'params': params,
                    'source': 'grasshopper'
                }, to=client_sid)
            print(f"[GH-SOCKET] Pushed params_sync to web clients")

    emit('geometry_ack', {'status': 'received',
         'mesh_count': len(geometry) if geometry else 0})
    print(f"{'='*50}\n")


if __name__ == "__main__":
    # Changed to 5001 to avoid macOS AirPlay conflict
    port = int(os.environ.get("PORT", 5001))

    print("=" * 50)
    print("Flask Hub Server (WebSocket Enabled)")
    print("=" * 50)
    print(f"Server:    http://127.0.0.1:{port}")
    print(f"WebSocket: ws://127.0.0.1:{port}")
    print(f"Async:     {ASYNC_MODE}")
    print(f"LLM Host:  {DEFAULT_HOST_URL}")
    print(f"LLM Model: {DEFAULT_MODEL}")
    print(
        f"API Key:   {'Set' if OPENAI_API_KEY else 'Not needed (local LLM)'}")
    print(f"GH URL:    {GH_URL}")
    print("=" * 50)
    print("\nHTTP Endpoints:")
    print("  POST /chat          - Send prompt, get request_id")
    print("  GET  /result/<id>   - Poll for geometry result")
    print("  POST /geometry_callback - GH posts geometry (HTTP fallback)")
    print("  POST /transcribe    - Transcribe audio with Whisper")
    print("  GET  /health        - Health check")
    print("\nWebSocket Events (Web App):")
    print("  params_update       - Client sends param changes")
    print("  params_broadcast    - Server broadcasts param changes to other clients")
    print("  chat_request        - Client sends chat/LLM request")
    print("  chat_message        - Server broadcasts chat messages to all clients")
    print("  chat_llm_response   - Server broadcasts LLM response to all clients")
    print("  params_sync         - Server pushes param changes from GH")
    print("  geometry_result     - Server pushes geometry to all clients")
    print("\nWebSocket Events (Grasshopper):")
    print("  gh_connect          - GH identifies itself")
    print("  gh_params_register  - GH registers available params")
    print("  gh_geometry         - GH sends computed geometry")
    print("  params_to_gh        - Server pushes param updates to GH")
    print(f"\nWhisper Model: {WHISPER_MODEL_SIZE}")
    print("=" * 50)

    # Use socketio.run instead of app.run for WebSocket support
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
