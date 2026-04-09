import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# -----------------------------
# Load environment variables (script directory, not cwd)
# -----------------------------
_kd = Path(__file__).resolve().parent
load_dotenv(_kd / ".env")
load_dotenv(_kd.parent / ".env")

# -----------------------------
# Build connector JSON in memory
# -----------------------------
connector_config = {
    "name": "rtbanking-postgres-cdc",
    "config": {
        "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
        "database.hostname": os.getenv("POSTGRES_HOST"),
        "database.port": os.getenv("POSTGRES_PORT"),
        "database.user": os.getenv("POSTGRES_USER"),
        "database.password": os.getenv("POSTGRES_PASSWORD"),
        "database.dbname": os.getenv("POSTGRES_DB"),
        "topic.prefix": "core_banking_oltp",
        "table.include.list": "public.customers,public.accounts,public.transactions",
        "plugin.name": "pgoutput",
        "slot.name": "rtbanking_cdc_slot",
        "publication.autocreate.mode": "filtered",
        "tombstones.on.delete": "false",
        "decimal.handling.mode": "double",
    },
}

# -----------------------------
# Send request to Debezium Connect
# -----------------------------
connect_base = os.getenv("KAFKA_CONNECT_URL", "http://localhost:8083").rstrip("/")
url = f"{connect_base}/connectors"
headers = {"Content-Type": "application/json"}

response = requests.post(url, headers=headers, data=json.dumps(connector_config))

# -----------------------------
# Debug/Output
# -----------------------------
if response.status_code == 201:
    print("Connector created successfully.")
elif response.status_code == 409:
    print("Connector already exists (idempotent).")
else:
    print(f"Failed to create connector ({response.status_code}): {response.text}")