from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DB_PATH = "zowe_capability_catalog.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 🔹 Catalog list API
@app.route("/api/catalog", methods=["GET"])
def get_catalog():
    family = request.args.get("family")

    conn = get_db_connection()
    
    if family:
        rows = conn.execute(
            "SELECT * FROM zowe_capability WHERE command_family = ?",
            (family,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM zowe_capability").fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])

# 🔹 Capability detail API
@app.route("/api/capability", methods=["GET"])
def get_capability_detail():
    command = request.args.get("command")

    if not command:
        return jsonify({"error": "command parameter required"}), 400

    conn = get_db_connection()

    capability = conn.execute(
        "SELECT * FROM zowe_capability WHERE zowe_command = ?",
        (command,)
    ).fetchone()

    if capability is None:
        conn.close()
        return jsonify({"error": "Capability not found"}), 404

    preconditions = conn.execute(
        """
        SELECT precondition
        FROM zowe_capability_precondition
        WHERE capability_id = ?
        """,
        (capability["id"],)
    ).fetchall()

    conn.close()

    return jsonify({
        "capability": dict(capability),
        "preconditions": [p["precondition"] for p in preconditions]
    })

if __name__ == "__main__":
    app.run(debug=True)
