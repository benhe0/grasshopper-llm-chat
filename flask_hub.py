"""
Flask Hub Server - Coordinates between Web App and Grasshopper
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/chat", methods=["POST"])
def chat():
    # TODO: implement LLM call
    body = request.json
    prompt = body.get("prompt", "")
    return jsonify({"status": "not implemented", "prompt": prompt})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
