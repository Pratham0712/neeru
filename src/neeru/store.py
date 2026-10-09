"""DynamoDB access. Every other module talks to the database only through this file.

Tables (all pay-per-request):
  hotspots       pk id                      -- one item per spot, plus id "_config" for settings
  reports        pk hotspot_id, sk sk       -- sk = "<iso time>#<report id>", newest last
  subscriptions  pk hotspot_id, sk chat_id  -- GSI "by-chat" on chat_id for /stop
  sessions       pk chat_id                 -- bot state (language, pending photo); TTL on expires_at
                                               also holds "update#<id>" items to de-duplicate Telegram retries
"""

import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from . import config

_ddb = None
CONFIG_ID = "_config"


def _table(name: str):
    global _ddb
    if _ddb is None:
        _ddb = boto3.resource("dynamodb", region_name=config.AWS_REGION)
    return _ddb.Table(name)


def reset_clients():
    """Used by tests after moto starts."""
    global _ddb
    _ddb = None


def to_ddb(value):
    """DynamoDB does not accept floats; store them as Decimal."""
    if isinstance(value, float):
        return Decimal(str(round(value, 6)))
    if isinstance(value, dict):
        return {k: to_ddb(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [to_ddb(v) for v in value]
    return value


def from_ddb(value):
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, dict):
        return {k: from_ddb(v) for k, v in value.items()}
    if isinstance(value, list):
        return [from_ddb(v) for v in value]
    return value


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ---------- hotspots ----------

def list_hotspots() -> list[dict]:
    table = _table(config.HOTSPOTS_TABLE)
    items, kwargs = [], {}
    while True:
        page = table.scan(**kwargs)
        items.extend(page["Items"])
        if "LastEvaluatedKey" not in page:
            break
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]
    return [from_ddb(i) for i in items if i["id"] != CONFIG_ID]


def get_hotspot(hotspot_id: str) -> dict | None:
    item = _table(config.HOTSPOTS_TABLE).get_item(Key={"id": hotspot_id}).get("Item")
    return from_ddb(item) if item else None


def put_hotspot(hotspot: dict) -> None:
    _table(config.HOTSPOTS_TABLE).put_item(Item=to_ddb(hotspot))


def update_hotspot(hotspot_id: str, fields: dict) -> None:
    names = {f"#{k}": k for k in fields}
    values = {f":{k}": to_ddb(v) for k, v in fields.items()}
    _table(config.HOTSPOTS_TABLE).update_item(
        Key={"id": hotspot_id},
        UpdateExpression="SET " + ", ".join(f"#{k} = :{k}" for k in fields),
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


def get_settings() -> dict:
    item = _table(config.HOTSPOTS_TABLE).get_item(Key={"id": CONFIG_ID}).get("Item")
    return from_ddb(item) if item else {"id": CONFIG_ID}


def put_settings(settings: dict) -> None:
    settings = {**settings, "id": CONFIG_ID}
    _table(config.HOTSPOTS_TABLE).put_item(Item=to_ddb(settings))


def active_storm_replay() -> dict | None:
    replay = get_settings().get("storm_replay")
    if not replay:
        return None
    if datetime.fromisoformat(replay["until"]) < now_utc():
        return None
    return replay


# ---------- reports ----------

def put_report(report: dict) -> None:
    item = {**report, "sk": f"{report['created_at']}#{report['report_id']}"}
    _table(config.REPORTS_TABLE).put_item(Item=to_ddb(item))


def recent_reports(hotspot_id: str, hours: float) -> list[dict]:
    since = (now_utc() - timedelta(hours=hours)).isoformat()
    page = _table(config.REPORTS_TABLE).query(
        KeyConditionExpression=Key("hotspot_id").eq(hotspot_id) & Key("sk").gte(since),
        ScanIndexForward=False,
    )
    return [from_ddb(i) for i in page["Items"]]


# ---------- subscriptions ----------

def subscribe(hotspot_id: str, chat_id: int, lang: str) -> None:
    _table(config.SUBS_TABLE).put_item(
        Item={"hotspot_id": hotspot_id, "chat_id": int(chat_id), "lang": lang, "created_at": now_utc().isoformat()}
    )


def subscribers(hotspot_id: str) -> list[dict]:
    page = _table(config.SUBS_TABLE).query(KeyConditionExpression=Key("hotspot_id").eq(hotspot_id))
    return [from_ddb(i) for i in page["Items"]]


def subscriptions_for_chat(chat_id: int) -> list[dict]:
    page = _table(config.SUBS_TABLE).query(
        IndexName="by-chat", KeyConditionExpression=Key("chat_id").eq(int(chat_id))
    )
    return [from_ddb(i) for i in page["Items"]]


def unsubscribe_all(chat_id: int) -> int:
    subs = subscriptions_for_chat(chat_id)
    table = _table(config.SUBS_TABLE)
    for sub in subs:
        table.delete_item(Key={"hotspot_id": sub["hotspot_id"], "chat_id": int(chat_id)})
    return len(subs)


# ---------- bot sessions ----------

def get_session(chat_id: int) -> dict:
    item = _table(config.SESSIONS_TABLE).get_item(Key={"chat_id": str(chat_id)}).get("Item")
    return from_ddb(item) if item else {"chat_id": str(chat_id), "lang": "en"}


def put_session(session: dict) -> None:
    session = {**session, "chat_id": str(session["chat_id"]), "expires_at": int(time.time()) + 30 * 86400}
    _table(config.SESSIONS_TABLE).put_item(Item=to_ddb(session))


def claim_update(update_id: int) -> bool:
    """True the first time we see a Telegram update_id, False on retries."""
    try:
        _table(config.SESSIONS_TABLE).put_item(
            Item={"chat_id": f"update#{update_id}", "expires_at": int(time.time()) + 86400},
            ConditionExpression="attribute_not_exists(chat_id)",
        )
        return True
    except ClientError as err:
        if err.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise
