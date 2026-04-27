"""
AWS Service Connectors
- DynamoDB
- SNS (email alerts)
"""

import boto3
import logging
from flask import current_app

logger = logging.getLogger(__name__)

# ─── Singleton clients (module-level, reused across requests) ───────────────

_dynamodb = None
_sns      = None


def get_dynamodb():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource(
            "dynamodb",
            region_name=current_app.config["AWS_REGION"],
        )
    return _dynamodb


def get_sns():
    global _sns
    if _sns is None:
        _sns = boto3.client(
            "sns",
            region_name=current_app.config["AWS_REGION"],
        )
    return _sns


# ─── Helper: table accessor ──────────────────────────────────────────────────

def table(name_key: str):
    """
    Returns a DynamoDB Table resource.
    name_key: config key e.g. 'DYNAMO_USERS_TABLE'
    """
    dynamodb = get_dynamodb()
    table_name = current_app.config[name_key]
    return dynamodb.Table(table_name)
