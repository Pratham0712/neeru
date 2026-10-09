"""Write web/config.js with the deployed API URL and zip web/ for Amplify Hosting (manual deploy).

Usage: TELEGRAM_BOT_USERNAME=neeru_blr_bot python scripts/build_web.py   ->  dist/neeru-web.zip
"""

import os
import zipfile
from pathlib import Path

from stack import outputs

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    api_url = outputs()["ApiUrl"]
    bot = os.environ.get("TELEGRAM_BOT_USERNAME", "").lstrip("@")
    (ROOT / "web" / "config.js").write_text(
        f'window.NEERU_API = "{api_url}";\nwindow.NEERU_BOT = "{bot}";\n'
    )

    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    archive = dist / "neeru-web.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in (ROOT / "web").rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(ROOT / "web"))
    print(f"API: {api_url}\nUpload {archive} in Amplify console -> Deploy without Git")


if __name__ == "__main__":
    main()
