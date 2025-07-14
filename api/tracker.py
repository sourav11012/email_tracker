from flask import Flask, send_file, request
import sqlite3
import pathlib
import os
import tempfile
from slack_sdk.webhook import WebhookClient
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

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

GRACE_SEC = 5

@app.route("/t/<open_id>.png")
def track(open_id):
    email = request.args.get("e", "unknown")
    ua    = request.headers.get("User-Agent", "")

    now = datetime.now(timezone.utc)

    # Fetch earliest timestamp for this open_id
    with get_db() as db:
        row = db.execute(
            "SELECT MIN(ts) AS first_ts FROM opens WHERE open_id = ?",
            (open_id,)
        ).fetchone()
        first_ts = None if row["first_ts"] is None else datetime.fromisoformat(row["first_ts"])

    # Log this hit (always)
    log_open(open_id, email, ua)

    # Decide whether to notify
    should_notify = False
    if first_ts is not None:
        # Not the very first hit
        if now - first_ts > timedelta(seconds=GRACE_SEC):
            should_notify = True
    # else: first_hit ⇒ no notify

    if should_notify and slack:
        try:
            slack.send(text=f"📬 {email} opened (id={open_id})")
        except Exception as e:
            print("Slack error:", e)

    return send_file(IMAGE_PATH, mimetype="image/png")

@app.route("/health")
def health():
    return "ok", 200


