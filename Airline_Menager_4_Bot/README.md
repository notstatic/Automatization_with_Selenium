# AM4-Bot

Bot for the [Airline Manager 4](https://www.airline4.net/) simulator. It logs in,
buys fuel and CO2 quota at good prices, starts marketing campaigns and departs
landed planes in a loop.

## Price-aware buying

AM4 fuel/CO2 prices follow a fixed repeating schedule: UTC day-of-month (1-31)
with 48 half-hour ticks per day. The schedule is vendored in
`am4bot/data/price_schedule.json` (extracted from the
[am4-helper](https://am4-helper.web.app/tabs/prices) app bundle) and the bot
uses it to look ahead:

- stock critically low → buy immediately at any price
- absolute bargain (fuel ≤ $320, CO2 ≤ $80) → buy
- stock comfortable → do nothing
- stock low → buy only when the current tick is among the cheapest of the
  next 6 hours; otherwise wait for the cheaper tick

If the scraped in-game price disagrees with the schedule (the game devs changed
the table), the bot falls back to the simple threshold rule. Refresh the
vendored schedule with:

```
python scripts/update_schedule.py
```

## Setup

Requires Python 3.10+ and Chrome (Selenium Manager downloads the matching
chromedriver automatically).

```
pip install -r requirements.txt
export AM4_USERNAME='your_username'
export AM4_PASSWORD='your_password'
```

## Run

From this directory:

```
python -m am4bot.main
```

Stop with Ctrl-C.

## Tests

```
python -m pytest tests -v
```

The tests use a fake Selenium driver — no browser or account needed.
