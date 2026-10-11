"""
CTF Box - "InternalOps" web application
-----------------------------------------------------------------
Intentionally vulnerable Flask app for a pentesting-module CTF box.

Vuln chain implemented here:
  1. JWT algorithm-confusion / "alg:none" acceptance bug in verify_token()
     -> lets an attacker forge a token with role=admin, no valid signature.
  2. Authenticated (but unauthenticated-in-practice, thanks to bug #1)
     admin endpoint that pickle.loads()'s attacker-controlled, base64-encoded
     data -> remote code execution inside the container.

This code is deliberately insecure. Do not deploy it anywhere but an
isolated lab VM/container built for this assignment.
-----------------------------------------------------------------
"""

import base64
import pickle
import time

import jwt
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Secret used to *sign* real tokens. The bug is not that this leaks -
# the bug is that the verifier also accepts alg=none, so this secret
# is never actually needed by the attacker.
SECRET_KEY = "sup3r_internal_ops_signing_key_2024"

# Toy "user database"
USERS = {
    "operator": {"password": "L3tM31nPlz!", "role": "user"},
}


def issue_token(username, role):
    payload = {"sub": username, "role": role, "iat": int(time.time())}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def verify_token(token):
    """
    VULNERABLE: the algorithms allow-list includes 'none', and PyJWT
    (depending on version/config) will accept an unsigned token when
    'none' is permitted. A real HS256 token is never required.
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256", "none"],
            options={"verify_signature": True},
        )
        return payload
    except Exception:
        return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    user = USERS.get(username)
    if not user or user["password"] != password:
        return jsonify({"error": "invalid credentials"}), 401

    token = issue_token(username, user["role"])
    return jsonify({"token": token})


@app.route("/api/profile", methods=["GET"])
def profile():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "missing bearer token"}), 401

    payload = verify_token(auth.split(" ", 1)[1])
    if not payload:
        return jsonify({"error": "invalid token"}), 401

    return jsonify({"user": payload.get("sub"), "role": payload.get("role")})


@app.route("/admin/debug", methods=["POST"])
def admin_debug():
    """
    Internal diagnostics endpoint. Meant only for role=admin.
    Accepts a base64-encoded, pickled 'diagnostic report' object and
    unpickles it to print a summary. This is the RCE sink.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "missing bearer token"}), 401

    payload = verify_token(auth.split(" ", 1)[1])
    if not payload or payload.get("role") != "admin":
        return jsonify({"error": "admin role required"}), 403

    data = request.get_json(force=True, silent=True) or {}
    blob = data.get("report")
    if not blob:
        return jsonify({"error": "missing 'report' field"}), 400

    try:
        raw = base64.b64decode(blob)
        report = pickle.loads(raw)  # <-- insecure deserialization
        return jsonify({"status": "ok", "summary": str(report)})
    except Exception as e:
        return jsonify({"error": f"failed to process report: {e}"}), 500


if __name__ == "__main__":
    # Bound to all interfaces inside the container; the host only
    # publishes this on a non-standard port (see docker-compose.yml)
    app.run(host="0.0.0.0", port=5000)
