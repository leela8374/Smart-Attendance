"""
scripts/setup_dynamo.py
Creates all four DynamoDB tables if they don't already exist.
Run once on your EC2 instance:
    python scripts/setup_dynamo.py
"""

import boto3
import os
import time

REGION = os.environ.get("AWS_REGION", "us-east-1")

dynamo = boto3.client("dynamodb", region_name=REGION)

TABLES = [
    {
        "TableName": os.environ.get("DYNAMO_USERS_TABLE", "sas_users"),
        "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "user_id", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": os.environ.get("DYNAMO_COURSES_TABLE", "sas_courses"),
        "KeySchema": [{"AttributeName": "course_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "course_id", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": os.environ.get("DYNAMO_ATTENDANCE_TABLE", "sas_attendance"),
        "KeySchema": [{"AttributeName": "record_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "record_id", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": os.environ.get("DYNAMO_ENROLLMENT_TABLE", "sas_enrollment"),
        "KeySchema": [{"AttributeName": "enrollment_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "enrollment_id", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
    },
]


def create_tables():
    existing = {t["TableName"] for t in dynamo.list_tables()["TableNames"]}
    for spec in TABLES:
        name = spec["TableName"]
        if name in existing:
            print(f"  ✅ Already exists: {name}")
            continue
        dynamo.create_table(**spec)
        print(f"  🔨 Creating: {name} …", end=" ", flush=True)
        waiter = dynamo.get_waiter("table_exists")
        waiter.wait(TableName=name)
        print("done.")
    print("\nAll DynamoDB tables are ready.")


if __name__ == "__main__":
    create_tables()
