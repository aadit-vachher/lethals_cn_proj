from flask import Flask, jsonify, make_response
import socket

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "message": "Backend A is running",
        "server": socket.gethostname()
    })

@app.route("/api/status")
def status():
    response = make_response(jsonify({
        "status": "ok",
        "backend": "A",
        "server": socket.gethostname()
    }))

    response.headers["X-Backend"] = "A"
    response.headers["Cache-Control"] = "public, max-age=60"

    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001)
