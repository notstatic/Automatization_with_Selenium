"""Future price schedule and the buying decision built on it.

AM4 fuel/CO2 prices follow a fixed repeating schedule keyed by UTC
day-of-month (1-31) with 48 half-hour ticks per day. The vendored
``data/price_schedule.json`` was extracted from the am4-helper.web.app
JS bundle (see scripts/update_schedule.py to refresh it).
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import config

logger = logging.getLogger(__name__)

SCHEDULE_PATH = Path(__file__).parent / "data" / "price_schedule.json"
TICKS_PER_DAY = 48


@dataclass
class Tick:
    time: datetime
    fuel: int
    co2: int


@dataclass
class BuyDecision:
    buy: bool
    reason: str


class PriceSchedule:
    def __init__(self, days):
        """days: dict mapping day-of-month (int 1-31) to a list of 48 tick dicts."""
        self.days = days

    @classmethod
    def load(cls, path=SCHEDULE_PATH):
        with open(path) as f:
            raw = json.load(f)
        days = {int(day): ticks for day, ticks in raw.items()}
        if sorted(days) != list(range(1, 32)):
            raise ValueError("price schedule must contain day keys 1..31")
        for day, ticks in days.items():
            if len(ticks) != TICKS_PER_DAY:
                raise ValueError(f"day {day}: expected {TICKS_PER_DAY} ticks, got {len(ticks)}")
        return cls(days)

    def _tick_at(self, when):
        when = when.astimezone(timezone.utc)
        floored = when.replace(minute=(when.minute // 30) * 30, second=0, microsecond=0)
        entry = self.days[floored.day][floored.hour * 2 + floored.minute // 30]
        return Tick(time=floored, fuel=int(entry["fuel"]), co2=int(entry["co2"]))

    def current_tick(self, now_utc):
        """Scheduled prices for the half-hour tick containing now_utc."""
        return self._tick_at(now_utc)

    def ticks_ahead(self, now_utc, hours):
        """The next hours*2 ticks after the current one, crossing day boundaries."""
        start = self._tick_at(now_utc).time
        return [self._tick_at(start + timedelta(minutes=30 * i)) for i in range(1, hours * 2 + 1)]


def decide_buy(resource, current_price, remaining, now_utc, schedule, hard_threshold,
               min_stock=config.MIN_STOCK, critical_stock=config.CRITICAL_STOCK):
    """Decide whether to buy `resource` ('fuel' or 'co2') now.

    Rules, in order: buy on critically low stock at any price; buy any
    absolute bargain; with comfortable stock do nothing; with low stock use
    the schedule to buy only when the current tick is among the cheapest of
    the next LOOKAHEAD_HOURS hours. If the scraped price disagrees with the
    schedule (game devs changed the table), fall back to the threshold rule.
    """
    if remaining <= critical_stock:
        return BuyDecision(True, f"stock critical ({remaining:,})")
    if current_price <= hard_threshold:
        return BuyDecision(True, f"bargain price ${current_price}")
    if remaining > min_stock:
        return BuyDecision(False, f"stock sufficient ({remaining:,})")

    if schedule is None:
        return BuyDecision(True, "stock low, no schedule for look-ahead")

    scheduled_price = getattr(schedule.current_tick(now_utc), resource)
    if abs(current_price - scheduled_price) > scheduled_price * config.SCHEDULE_MISMATCH_TOLERANCE:
        logger.warning(
            "%s: scraped price $%s deviates from scheduled $%s; ignoring schedule",
            resource, current_price, scheduled_price,
        )
        return BuyDecision(True, "stock low, schedule mismatch fallback")

    future = [getattr(t, resource) for t in schedule.ticks_ahead(now_utc, config.LOOKAHEAD_HOURS)]
    cutoff = sorted(future + [current_price])[config.LOOKAHEAD_TOP_N - 1]
    if current_price <= cutoff:
        return BuyDecision(
            True,
            f"stock low and ${current_price} is among the {config.LOOKAHEAD_TOP_N} "
            f"cheapest ticks of the next {config.LOOKAHEAD_HOURS}h",
        )
    return BuyDecision(
        False,
        f"stock low but cheaper tick within {config.LOOKAHEAD_HOURS}h (min ${min(future)})",
    )
