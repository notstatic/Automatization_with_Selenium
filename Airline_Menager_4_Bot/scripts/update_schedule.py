"""Re-extract the AM4 price schedule from the am4-helper.web.app JS bundle.

The site embeds the full schedule (UTC day-of-month 1-31 x 48 half-hour
ticks) as a JSON.parse('...') literal inside a lazily loaded webpack chunk.
Run this script when the game's price table changes; it rewrites
am4bot/data/price_schedule.json.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

SITE = "https://am4-helper.web.app"
OUT = Path(__file__).resolve().parent.parent / "am4bot" / "data" / "price_schedule.json"
TICKS_PER_DAY = 48


def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8")


def validate(data):
    if sorted(map(int, data)) != list(range(1, 32)):
        raise ValueError("expected day keys 1..31")
    for day, ticks in data.items():
        if len(ticks) != TICKS_PER_DAY:
            raise ValueError(f"day {day}: expected {TICKS_PER_DAY} ticks, got {len(ticks)}")
        for tick in ticks:
            int(tick["fuel"])
            int(tick["co2"])
            str(tick["time"])


def main():
    index = fetch(f"{SITE}/tabs/prices")
    runtime_name = re.search(r'src="(runtime\.[0-9a-f]+\.js)"', index).group(1)
    runtime = fetch(f"{SITE}/{runtime_name}")
    for num, chunk_hash in re.findall(r'(\d+):"([0-9a-f]{12,20})"', runtime):
        src = fetch(f"{SITE}/{num}.{chunk_hash}.js")
        blob = re.search(r"JSON\.parse\('(\{.*?\})'\)", src, re.S)
        if not blob or '"fuel"' not in blob.group(1):
            continue
        data = json.loads(blob.group(1).replace("\\\\", "\\"))
        validate(data)
        OUT.write_text(json.dumps(data) + "\n")
        print(f"wrote {OUT} ({len(data)} days x {TICKS_PER_DAY} ticks)")
        return
    sys.exit("price schedule blob not found in any chunk")


if __name__ == "__main__":
    main()
