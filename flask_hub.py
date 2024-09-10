"""
Flask Hub Server - Coordinates between Web App, LLM, and Grasshopper
"""

from flask import Flask, request, jsonify
import json
import urllib.request
import os

app = Flask(__name__)

# Enable CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# Configuration
DEFAULT_MODEL = os.environ.get("LLM_MODEL", "llama3.2:1b")
DEFAULT_HOST_URL = os.environ.get("LLM_HOST_URL", "http://localhost:11434/v1/chat/completions")


def call_llm(prompt, params_json):
    """Call LLM API to get parameter updates."""
    system_prompt = f"""You control a parametric 3D model. Adjust parameters based on user requests.

AVAILABLE PARAMETERS:
{params_json}

Return ONLY a JSON object with parameter names and new values.
Example: {{"width": 8.0, "height": 3.0}}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    payload = {
        "model": DEFAULT_MODEL,
        "messages": messages,
        "temperature": 0.3
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        DEFAULT_HOST_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    return result["choices"][0]["message"]["content"]


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/chat", methods=["POST"])
def chat():
    body = request.json
    prompt = body.get("prompt")
    params = body.get("params", [])

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    try:
        params_json = json.dumps(params, indent=2)
        llm_response = call_llm(prompt, params_json)
        param_updates = json.loads(llm_response)

        return jsonify({
            "status": "ok",
            "params": param_updates
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"Starting Flask Hub on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
