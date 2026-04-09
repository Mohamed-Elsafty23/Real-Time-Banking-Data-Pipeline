"""
Stream Debezium CDC topics into MinIO as partitioned Parquet objects.

Topic names follow Debezium's {prefix}.{schema}.{table} convention; the prefix
matches kafka-debezium/generate_and_post_connector.py (core_banking_oltp).
"""
import boto3
from kafka import KafkaConsumer
import json
import pandas as pd
from datetime import datetime
import os
from pathlib import Path

from dotenv import load_dotenv

# -----------------------------
# Load secrets from consumer/.env (works regardless of cwd)
# -----------------------------
_cons = Path(__file__).resolve().parent
load_dotenv(_cons / ".env")
load_dotenv(_cons.parent / ".env")

CDC_TOPICS = (
    "core_banking_oltp.public.customers",
    "core_banking_oltp.public.accounts",
    "core_banking_oltp.public.transactions",
)

# Kafka consumer settings
consumer = KafkaConsumer(
    *CDC_TOPICS,
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP"),
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id=os.getenv("KAFKA_GROUP"),
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# MinIO client
s3 = boto3.client(
    's3',
    endpoint_url=os.getenv("MINIO_ENDPOINT"),
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY")
)

bucket = os.getenv("MINIO_BUCKET")

# Create bucket if not exists
if bucket not in [b['Name'] for b in s3.list_buckets()['Buckets']]:
    s3.create_bucket(Bucket=bucket)

# Consume and write function
def write_to_minio(table_name, records):
    if not records:
        return
    df = pd.DataFrame(records)
    date_str = datetime.now().strftime('%Y-%m-%d')
    file_path = f'{table_name}_{date_str}.parquet'
    df.to_parquet(file_path, engine='fastparquet', index=False)
    s3_key = f'{table_name}/date={date_str}/{table_name}_{datetime.now().strftime("%H%M%S%f")}.parquet'
    s3.upload_file(file_path, bucket, s3_key)
    os.remove(file_path)
    print(f"Uploaded {len(records)} rows to s3://{bucket}/{s3_key}")

# Batch consume
batch_size = 50
buffer = {t: [] for t in CDC_TOPICS}

print("Kafka consumer started; waiting for CDC events...")

for message in consumer:
    topic = message.topic
    event = message.value
    payload = event.get("payload", {})
    record = payload.get("after")  # Only take the actual row

    if record:
        buffer[topic].append(record)
        print(f"[{topic}] -> {record}")  # Debugging

    if len(buffer[topic]) >= batch_size:
        write_to_minio(topic.split('.')[-1], buffer[topic])
        buffer[topic] = []
