"""Run the whole app on your laptop with fake AWS (moto). No account, no deploy, no Bedrock.

    pip install -r requirements-dev.txt
    python scripts/local_demo.py            # http://localhost:8000

Uses a storm replay over Bellandur so the map has red spots, and a stand-in verifier
that always answers "tyre-hub, confident" (the real agent needs Bedrock).
Good for frontend work; everything judges see must come from the deployed stack.
"""

import json
import os
import sys
from datetime import timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
os.environ.setdefault("ADMIN_TOKEN", "local-admin-token-123")
os.environ.setdefault("TELEGRAM_SECRET", "local-secret-12345678")
os.environ.update({"AWS_ACCESS_KEY_ID": "x", "AWS_SECRET_ACCESS_KEY": "x", "AWS_DEFAULT_REGION": "ap-south-1"})

from moto import mock_aws  # noqa: E402

mock = mock_aws()
mock.start()

from tests.conftest import create_fake_aws  # noqa: E402  same tables as the tests
from neeru import store, verifier  # noqa: E402
from handlers import api  # noqa: E402

create_fake_aws()
store.put_settings({"storm_replay": {
    "lat": 12.926, "lon": 77.681, "peak_mm_hr": 35, "radius_km": 6,
    "until": (store.now_utc() + timedelta(days=1)).isoformat(),
}})


def stand_in_verify(image_bytes, image_format, lat, lon, hotspot, lang="en"):
    return {
        "is_waterlogging": True, "depth": "tyre_hub", "confidence": 0.85, "is_valid_photo": True,
        "reason": "Local demo verdict (no Bedrock).",
        "rider_advice": "Local demo: avoid on a two-wheeler." if lang == "en" else "ಸ್ಥಳೀಯ ಡೆಮೊ: ದ್ವಿಚಕ್ರ ವಾಹನದಲ್ಲಿ ತಪ್ಪಿಸಿ.",
        "tools_used": ["get_rainfall_here", "nearby_reports", "submit_verdict"],
        "verified": True,
    }


verifier.verify = stand_in_verify
api.handler({"routeKey": "POST /admin/refresh", "headers": {"x-admin-token": os.environ["ADMIN_TOKEN"]}}, None)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "web"), **kwargs)

    def _api(self, method):
        path = urlparse(self.path).path[len("/api"):]
        route, params = f"{method} {path}", None
        if method == "GET" and path.startswith("/hotspots/"):
            route, params = "GET /hotspots/{id}", {"id": path.split("/")[2]}
        length = int(self.headers.get("Content-Length") or 0)
        event = {
            "routeKey": route,
            "headers": {k.lower(): v for k, v in self.headers.items()},
            "body": self.rfile.read(length).decode() if length else None,
            "pathParameters": params,
        }
        response = api.handler(event, None)
        self.send_response(response["statusCode"])
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response["body"].encode())

    def do_GET(self):
        if self.path.startswith("/api/"):
            return self._api("GET")
        if self.path.startswith("/config.js"):
            body = b'window.NEERU_API = "/api"; window.NEERU_BOT = "";\n'
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript")
            self.end_headers()
            return self.wfile.write(body)
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            return self._api("POST")
        self.send_error(404)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"Neeru local demo on http://localhost:{port}  (admin token: {os.environ['ADMIN_TOKEN']})")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
