"""Load data/hotspots.json into the hotspots table. Safe to re-run: it keeps learned thresholds.

Usage: python scripts/seed_hotspots.py [--reset-thresholds]
"""

import json
import sys
from decimal import Decimal
from pathlib import Path

import boto3

from stack import outputs

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    reset = "--reset-thresholds" in sys.argv
    table = boto3.resource("dynamodb", region_name="ap-south-1").Table(outputs()["HotspotsTableName"])
    spots = json.loads((ROOT / "data" / "hotspots.json").read_text(), parse_float=Decimal)

    for spot in spots:
        existing = table.get_item(Key={"id": spot["id"]}).get("Item")
        if existing and not reset:
            # keep the threshold citizens have already calibrated, and the current risk
            spot = {**existing, **{k: v for k, v in spot.items() if k != "threshold_mm"}}
        table.put_item(Item=spot)
        print(f"seeded {spot['id']}")
    print(f"{len(spots)} hotspots ready. Next: POST /admin/refresh to compute risk now.")


if __name__ == "__main__":
    main()
