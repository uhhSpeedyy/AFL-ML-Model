import os
import struct

import pyodbc
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

SQL_COPT_SS_ACCESS_TOKEN = 1256
SQL_SCOPE = "https://database.windows.net/.default"


def check_database():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")

    if not server or not database:
        return False, "DB_SERVER or DB_NAME is not configured"

    try:
        credential = DefaultAzureCredential()

        token = credential.get_token(SQL_SCOPE).token

        token_bytes = token.encode("utf-16-le")
        token_struct = struct.pack(
            f"<I{len(token_bytes)}s",
            len(token_bytes),
            token_bytes,
        )

        connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER=tcp:{server},1433;"
            f"DATABASE={database};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=10;"
        )

        connection = pyodbc.connect(
            connection_string,
            attrs_before={
                SQL_COPT_SS_ACCESS_TOKEN: token_struct
            },
        )

        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        if result and result[0] == 1:
            return True, "Azure SQL connection successful"

        return False, "Unexpected SQL result"

    except Exception as error:
        return False, f"Database connection failed: {error}"