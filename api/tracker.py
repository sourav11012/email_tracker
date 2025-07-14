from flask import Flask, send_file, request
import sqlite3
import pathlib
import os
import tempfile
from slack_sdk.webhook import WebhookClient
from dotenv import load_dotenv

load_dotenv()

TMP_DIR = pathlib.Path(tempfile.gettempdir())
DATABASE = TMP_DIR / "opens.db"
IMAGE_PATH = pathlib.Path(__file__).parent.parent / "images" / "qr.jpeg"
SLACK_URL = os.getenv("SLACK_URL")

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

with get_db() as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS opens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            open_id TEXT,
            email TEXT,
            ua TEXT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()

slack = WebhookClient(SLACK_URL) if SLACK_URL else None

def log_open(open_id, email, ua):
    with get_db() as db:
        db.execute(
            "INSERT INTO opens(open_id,email,ua) VALUES (?,?,?)",
            (open_id, email, ua)
        )
        db.commit()
    if slack:
        try:
            slack.send(text=f"📬 {email} opened (id={open_id})")
        except Exception as e:
            print("Slack error:", e)

@app.route("/t/<open_id>.jpeg")
def track(open_id):
    email = request.args.get("e", "unknown")
    ua = request.headers.get("User-Agent", "")
    log_open(open_id, email, ua)
    return send_file(IMAGE_PATH, mimetype="image/jpeg")

@app.route("/health")
def health():
    return "ok", 200


