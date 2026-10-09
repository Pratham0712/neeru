"""Test setup: fake AWS (moto), seeded hotspots, and no real network calls."""

import json
import os
from decimal import Decimal
from pathlib import Path

os.environ.update({
    "AWS_DEFAULT_REGION": "ap-south-1",
    "AWS_REGION": "ap-south-1",
    "AWS_ACCESS_KEY_ID": "testing",
    "AWS_SECRET_ACCESS_KEY": "testing",
    "TELEGRAM_BOT_TOKEN": "test-token",
    "TELEGRAM_SECRET": "test-secret-1234567890",
    "ADMIN_TOKEN": "admin-token-1234567890",
    "ALERTS_TOPIC_ARN": "",
})

import boto3  # noqa: E402
import pytest  # noqa: E402
from moto import mock_aws  # noqa: E402

from neeru import alerts, config, engine, store, telegram  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 100


def create_fake_aws() -> None:
    """Create the tables and bucket from template.yaml and seed hotspots. Call inside mock_aws()."""
    ddb = boto3.client("dynamodb", region_name="ap-south-1")
    ddb.create_table(
        TableName=config.HOTSPOTS_TABLE, BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
    )
    ddb.create_table(
        TableName=config.REPORTS_TABLE, BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[{"AttributeName": "hotspot_id", "AttributeType": "S"},
                              {"AttributeName": "sk", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "hotspot_id", "KeyType": "HASH"},
                   {"AttributeName": "sk", "KeyType": "RANGE"}],
    )
    ddb.create_table(
        TableName=config.SUBS_TABLE, BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[{"AttributeName": "hotspot_id", "AttributeType": "S"},
                              {"AttributeName": "chat_id", "AttributeType": "N"}],
        KeySchema=[{"AttributeName": "hotspot_id", "KeyType": "HASH"},
                   {"AttributeName": "chat_id", "KeyType": "RANGE"}],
        GlobalSecondaryIndexes=[{
            "IndexName": "by-chat",
            "KeySchema": [{"AttributeName": "chat_id", "KeyType": "HASH"},
                          {"AttributeName": "hotspot_id", "KeyType": "RANGE"}],
            "Projection": {"ProjectionType": "ALL"},
        }],
    )
    ddb.create_table(
        TableName=config.SESSIONS_TABLE, BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[{"AttributeName": "chat_id", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "chat_id", "KeyType": "HASH"}],
    )
    boto3.client("s3", region_name="ap-south-1").create_bucket(
        Bucket=config.PHOTOS_BUCKET, CreateBucketConfiguration={"LocationConstraint": "ap-south-1"}
    )
    store.reset_clients()
    engine.reset_clients()

    table = boto3.resource("dynamodb", region_name="ap-south-1").Table(config.HOTSPOTS_TABLE)
    for spot in json.loads((ROOT / "data" / "hotspots.json").read_text(encoding="utf-8"), parse_float=Decimal):
        table.put_item(Item=spot)


@pytest.fixture
def aws():
    with mock_aws():
        create_fake_aws()
        yield
        store.reset_clients()
        engine.reset_clients()


@pytest.fixture
def sent(monkeypatch):
    """Capture Telegram messages instead of sending them."""
    messages = []

    def fake_send(chat_id, text, reply_markup=None):
        messages.append({"chat_id": chat_id, "text": text, "reply_markup": reply_markup})
        return {"ok": True}

    monkeypatch.setattr(telegram, "send_message", fake_send)
    monkeypatch.setattr(alerts.telegram, "send_message", fake_send)
    monkeypatch.setattr(telegram, "answer_callback", lambda *a, **k: {"ok": True})
    return messages
