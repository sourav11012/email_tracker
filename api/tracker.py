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
IMAGE_PATH = pathlib.Path(__file__).parent.parent / "images" / "sign.png"
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


@app.route("/t/<open_id>.png")
def track(open_id):
    """Log every request, but Slack-ping only from the 2nd hit onward."""
    email = request.args.get("e", "unknown")
    ua    = request.headers.get("User-Agent", "")

    # --- check if we've seen this open_id before
    with get_db() as db:
        seen_before = db.execute(
            "SELECT 1 FROM opens WHERE open_id = ? LIMIT 1", (open_id,)
        ).fetchone()

    # --- always log the hit
    log_open(open_id, email, ua)

    # --- only notify Slack if it's NOT the first time
    if seen_before and slack:
        try:
            slack.send(text=f"📬 {email} opened again (id={open_id})")
        except Exception as e:
            print("Slack error:", e)

    return send_file(IMAGE_PATH, mimetype="image/png")

@app.route("/health")
def health():
    return "ok", 200


