import os
import socket
import sqlite3
import urllib.parse
from flask import Flask, render_template_string

app = Flask(__name__)

STATUS_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Application status</title>
    <style>
      body { font-family: Arial, sans-serif; padding: 24px }
      .ok { color: #0a0 }
      .bad { color: #a00 }
      .box { border: 1px solid #ddd; padding: 12px; margin: 8px 0; border-radius: 6px }
      table { border-collapse: collapse }
      td, th { padding: 6px 12px; border-bottom: 1px solid #eee }
    </style>
  </head>
  <body>
    <h1>Application status</h1>
    <div class="box">
      <strong>Website reachable:</strong>
      <span class="ok">Yes</span>
      <div>Time: {{ time }}</div>
    </div>

    <div class="box">
      <h2>Application</h2>
      <table>
        <tr><th>Component</th><th>Status</th><th>Details</th></tr>
        <tr><td>App process</td><td><span class="ok">Running</span></td><td>Flask app responding</td></tr>
        <tr><td>Database</td>
            <td>{% if db.ok %}<span class="ok">Connected</span>{% else %}<span class="bad">Not connected</span>{% endif %}</td>
            <td>{{ db.detail }}</td>
        </tr>
      </table>
    </div>

    <div class="box">
      <h2>Raw info</h2>
      <pre>{{ raw }}</pre>
    </div>
  </body>
</html>
"""


def check_sqlite(db_url, timeout=2):
    try:
        # sqlite URL can be sqlite:///absolute/path or sqlite:///:memory:
        if db_url.startswith("sqlite:///"):
            path = db_url.replace("sqlite://", "")
        elif db_url.startswith("sqlite://"):
            path = db_url.replace("sqlite://", "")
        else:
            path = db_url
        conn = sqlite3.connect(path, timeout=timeout)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        conn.close()
        return True, "sqlite OK"
    except Exception as e:
        return False, f"sqlite error: {e}"


def try_db_connection(db_url):
    """
    Attempt to connect to a database described by DB URL. Supported schemes: sqlite, postgresql, mysql.
    For Postgres/MySQL will try to use psycopg2 / pymysql if installed; otherwise falls back to TCP reachability test.
    Returns (ok: bool, detail: str)
    """
    if not db_url:
        return False, "DATABASE_URL not set"

    parsed = urllib.parse.urlparse(db_url)
    scheme = (parsed.scheme or "").lower()

    # sqlite
    if scheme.startswith("sqlite"):
        return check_sqlite(db_url)

    host = parsed.hostname
    port = parsed.port
    username = parsed.username
    password = parsed.password
    dbname = parsed.path[1:] if parsed.path and parsed.path.startswith("/") else parsed.path

    # Postgres
    if scheme in ("postgres", "postgresql"):
        try:
            import psycopg2
            dsn = db_url
            conn = psycopg2.connect(dsn, connect_timeout=3)
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            cur.close()
            conn.close()
            return True, "postgres OK (psycopg2)"
        except Exception as e:
            # fallback to TCP check
            if host and port:
                sock_ok = tcp_check(host, port)
                return False, f"psycopg2 error: {e}; TCP reachable: {sock_ok}"
            return False, f"psycopg2 error: {e}"

    # MySQL
    if scheme in ("mysql", "mysql+pymysql"):
        try:
            import pymysql
            conn = pymysql.connect(host=host, port=port or 3306, user=username, password=password, db=dbname, connect_timeout=3)
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            cur.close()
            conn.close()
            return True, "mysql OK (pymysql)"
        except Exception as e:
            if host and (port or 3306):
                sock_ok = tcp_check(host, port or 3306)
                return False, f"pymysql error: {e}; TCP reachable: {sock_ok}"
            return False, f"pymysql error: {e}"

    # Generic: try TCP reachability if host/port available
    if host and port:
        sock_ok = tcp_check(host, port)
        return (sock_ok, f"tcp reachable: {sock_ok}")

    return False, f"Unsupported DB scheme: {scheme}"


def tcp_check(host, port, timeout=3):
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except Exception:
        return False


@app.route("/")
def home():
    # Provide a friendly status page that shows whether the app is up and whether a DB is reachable
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("DB_URL")
    ok, detail = try_db_connection(db_url)

    raw = {
        'DATABASE_URL': bool(db_url),
        'parsed_db_url': db_url,
    }

    return render_template_string(STATUS_TEMPLATE, time=__import__('time').ctime(), db={"ok": ok, "detail": detail}, raw=raw)

if __name__ == "__main__":
    # Bind to all interfaces so external checks can reach it if run in a container/VM.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)