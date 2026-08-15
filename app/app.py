import os
import time

import pyodbc
import socket
from dotenv import load_dotenv
from flask import Flask, render_template_string, jsonify
from azure.identity import ManagedIdentityCredential
load_dotenv()

app = Flask(__name__)

SQL_COPT_SS_ACCESS_TOKEN = 1256
SQL_SCOPE = "https://database.windows.net/.default"

STATUS_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>Azure Cloud Infrastructure</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 0 20px;
        }

        h1 {
            margin-bottom: 10px;
        }

        .box {
            border: 1px solid #ddd;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th,
        td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }

        .ok {
            color: green;
            font-weight: bold;
        }

        .bad {
            color: red;
            font-weight: bold;
        }

        code {
            background: #f4f4f4;
            padding: 2px 5px;
            border-radius: 4px;
        }
    </style>
</head>

<body>

    <h1>Sam Speed Cloud Infra</h1>

    <div class="box">
        <h2>Application Status</h2>

        <table>
            <tr>
                <th>Component</th>
                <th>Status</th>
                <th>Details</th>
            </tr>

            <tr>
                <td>Flask application</td>
                <td class="ok">Running</td>
                <td>Application is responding</td>
            </tr>

            <tr>
                <td>Azure SQL</td>
                <td>
                    {% if db.ok %}
                        <span class="ok">Connected</span>
                    {% else %}
                        <span class="bad">Not connected</span>
                    {% endif %}
                </td>
                <td>{{ db.detail }}</td>
            </tr>
        </table>
    </div>

    <div class="box">
        <h2>Configuration</h2>

        <p>
            SQL Server configured:
            {% if sql_configured %}
                <span class="ok">Yes</span>
            {% else %}
                <span class="bad">No</span>
            {% endif %}
        </p>

        <p>
            Database configured:
            {% if db_configured %}
                <span class="ok">Yes</span>
            {% else %}
                <span class="bad">No</span>
            {% endif %}
        </p>
    </div>

    <div class="box">
        <h2>Last Check</h2>
        <p>{{ time }}</p>
    </div>

</body>
</html>
"""

def check_database():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")

    if not server or not database:
        return False, "DB_SERVER or DB_NAME is not configured"

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER=tcp:{server},1433;"
        f"DATABASE={database};"
        "Authentication=ActiveDirectoryMsi;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=10;"
    )

    connection = None
    cursor = None

    try:
        connection = pyodbc.connect(connection_string)

        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

        if result and result[0] == 1:
            return True, "Azure SQL connection successful"

        return False, "Unexpected SQL result"

    except Exception as error:
        return False, f"Database connection failed: {error}"

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


@app.route("/identity-test")
def identity_test():
    try:
        credential = ManagedIdentityCredential()
        token = credential.get_token(
            "https://database.windows.net/.default"
        )

        return {
            "status": "token acquired",
            "expires_on": token.expires_on,
            "website_site_name": os.getenv("WEBSITE_SITE_NAME"),
        }

    except Exception as error:
        return {
            "status": "token acquisition failed",
            "error": str(error),
        }, 500

import socket

@app.route("/network-test")
def network_test():
    try:
        ip = socket.gethostbyname("speedserver.database.windows.net")

        return {
            "hostname": "speedserver.database.windows.net",
            "resolved_ip": ip,
            "expected_private_ip": "10.0.1.4",
            "private_path": ip == "10.0.1.4"
        }

    except Exception as error:
        return {
            "error": str(error)
        }, 500




@app.route("/users")
def users():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER=tcp:{server},1433;"
        f"DATABASE={database};"
        "Authentication=ActiveDirectoryMsi;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=10;"
    )

    connection = None
    cursor = None

    try:
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, name, email, created_at FROM Users ORDER BY id"
        )

        rows = cursor.fetchall()

        users = [
            {
                "id": row.id,
                "name": row.name,
                "email": row.email,
                "created_at": row.created_at.isoformat()
                if row.created_at
                else None,
            }
            for row in rows
        ]

        return jsonify(users)

    except Exception as error:
        return jsonify({
            "error": str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()



if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True,
    )
