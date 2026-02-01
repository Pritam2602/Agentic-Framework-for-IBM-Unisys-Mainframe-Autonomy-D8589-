from flask import Flask, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DB_PATH = "zowe_capability_catalog.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/api/catalog", methods=["GET"])
def get_catalog():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM zowe_capability_catalog").fetchall()
    conn.close()

    catalog = [dict(row) for row in rows]
    return jsonify(catalog)

if __name__ == "__main__":
    app.run(debug=True)
