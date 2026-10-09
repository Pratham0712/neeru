"""All runtime configuration comes from environment variables set by template.yaml."""

import os

AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")

HOTSPOTS_TABLE = os.environ.get("HOTSPOTS_TABLE", "neeru-hotspots")
REPORTS_TABLE = os.environ.get("REPORTS_TABLE", "neeru-reports")
SUBS_TABLE = os.environ.get("SUBS_TABLE", "neeru-subscriptions")
SESSIONS_TABLE = os.environ.get("SESSIONS_TABLE", "neeru-sessions")
PHOTOS_BUCKET = os.environ.get("PHOTOS_BUCKET", "neeru-photos")
ALERTS_TOPIC_ARN = os.environ.get("ALERTS_TOPIC_ARN", "")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_SECRET = os.environ.get("TELEGRAM_SECRET", "")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

# Bedrock model used by the verifier agent. Must be a vision-capable model or
# inference profile available in your region (check Bedrock console -> Inference profiles).
MODEL_ID = os.environ.get("MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", AWS_REGION)

# A report this far (km) from every known hotspot creates a new citizen-reported spot.
NEW_SPOT_RADIUS_KM = float(os.environ.get("NEW_SPOT_RADIUS_KM", "0.8"))
# How long a verified report keeps influencing a hotspot's risk.
REPORT_WINDOW_HOURS = float(os.environ.get("REPORT_WINDOW_HOURS", "2"))
# Do not re-send a red alert for the same hotspot within this many minutes.
ALERT_COOLDOWN_MIN = int(os.environ.get("ALERT_COOLDOWN_MIN", "60"))
