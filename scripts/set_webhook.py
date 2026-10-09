"""Point your Telegram bot at the deployed API and register its commands.

Usage: TELEGRAM_BOT_TOKEN=... TELEGRAM_SECRET=... python scripts/set_webhook.py
(use the same values you gave `sam deploy`)
"""

import json
import os
import urllib.request

from stack import outputs


def call(token: str, method: str, payload: dict) -> dict:
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    secret = os.environ["TELEGRAM_SECRET"]
    url = outputs()["TelegramWebhookUrl"]

    print(call(token, "setWebhook", {
        "url": url,
        "secret_token": secret,
        "allowed_updates": ["message", "callback_query"],
        "drop_pending_updates": True,
    }))
    print(call(token, "setMyCommands", {"commands": [
        {"command": "start", "description": "Start / choose language"},
        {"command": "lang", "description": "Change language"},
        {"command": "stop", "description": "Stop all alerts"},
    ]}))
    print(call(token, "getWebhookInfo", {}))


if __name__ == "__main__":
    main()
