"""Alerts when a hotspot turns red (and an all-clear when it recovers).

Riders get a Telegram message in their language. Ward engineers / ops get the
same event on an SNS topic (subscribe an email or SMS to it in the console).
"""

import json
import logging
from datetime import datetime, timedelta

import boto3

from . import config, i18n, store, telegram

log = logging.getLogger(__name__)
_sns = None


def _sns_client():
    global _sns
    if _sns is None:
        _sns = boto3.client("sns", region_name=config.AWS_REGION)
    return _sns


def why_text(risk: dict, lang: str) -> str:
    parts = []
    if risk.get("report_depth"):
        parts.append(i18n.t("why_report", lang, depth=i18n.depth(risk["report_depth"], lang)))
    if risk.get("next_mm", 0) >= 1:
        parts.append(i18n.t("why_rain", lang, mm=round(risk["next_mm"])))
    return "\n".join(parts)


def on_level_change(hotspot: dict, old_level: str, risk: dict, replay: bool = False) -> int:
    """Send alerts for a level change. Returns the number of Telegram messages sent."""
    new_level = risk["level"]
    if new_level == old_level:
        return 0

    if new_level == "red":
        last = hotspot.get("last_alert_at")
        if last and datetime.fromisoformat(last) > store.now_utc() - timedelta(minutes=config.ALERT_COOLDOWN_MIN):
            return 0
        store.update_hotspot(hotspot["id"], {"last_alert_at": store.now_utc().isoformat()})
        _publish_ops(hotspot, risk, replay)
        key = "alert_red"
    elif old_level == "red" and new_level == "green":
        key = "alert_clear"
    else:
        return 0

    sent = 0
    for sub in store.subscribers(hotspot["id"]):
        lang = sub.get("lang", "en")
        text = i18n.t(key, lang, name=i18n.place_name(hotspot, lang), why=why_text(risk, lang))
        if replay:
            text += "\n" + i18n.t("replay_note", lang)
        if telegram.send_message(sub["chat_id"], text).get("ok"):
            sent += 1
    return sent


def _publish_ops(hotspot: dict, risk: dict, replay: bool) -> None:
    if not config.ALERTS_TOPIC_ARN:
        return
    prefix = "[STORM REPLAY DEMO] " if replay else ""
    try:
        _sns_client().publish(
            TopicArn=config.ALERTS_TOPIC_ARN,
            Subject=f"{prefix}Neeru: {hotspot['name']} is RED"[:99],
            Message=json.dumps(
                {
                    "hotspot": hotspot["name"],
                    "lat": hotspot["lat"],
                    "lon": hotspot["lon"],
                    "score": risk["score"],
                    "drivers": risk["drivers"],
                    "replay": replay,
                },
                indent=2,
            ),
        )
    except Exception:
        log.exception("SNS publish failed")
