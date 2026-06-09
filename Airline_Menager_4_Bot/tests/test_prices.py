from datetime import datetime, timezone

import pytest

from am4bot import config
from am4bot.prices import BuyDecision, PriceSchedule, TICKS_PER_DAY, decide_buy

NOW = datetime(2026, 6, 9, 12, 10, tzinfo=timezone.utc)  # tick index 24 (12:00)


def make_schedule(fuel=1000, co2=150, overrides=None):
    """Uniform schedule; overrides maps (day, tick_index) -> fuel price."""
    days = {
        day: [
            {"time": f"{i // 2:02d}:{(i % 2) * 30:02d}:00.000Z", "fuel": fuel, "co2": co2}
            for i in range(TICKS_PER_DAY)
        ]
        for day in range(1, 32)
    }
    for (day, idx), price in (overrides or {}).items():
        days[day][idx]["fuel"] = price
    return PriceSchedule(days)


class TestPriceSchedule:
    def test_vendored_schedule_loads_and_has_sane_shape(self):
        schedule = PriceSchedule.load()
        assert sorted(schedule.days) == list(range(1, 32))
        for ticks in schedule.days.values():
            assert len(ticks) == TICKS_PER_DAY
            for tick in ticks:
                assert 0 < tick["fuel"] <= 10_000
                assert 0 < tick["co2"] <= 1_000

    def test_current_tick_floors_to_half_hour(self):
        schedule = make_schedule(overrides={(9, 24): 777})
        tick = schedule.current_tick(NOW)
        assert tick.time == datetime(2026, 6, 9, 12, 0, tzinfo=timezone.utc)
        assert tick.fuel == 777

    def test_ticks_ahead_crosses_midnight_and_month(self):
        # 23:45 UTC on Jan 31: the second tick ahead is Feb 1 (day key 1).
        schedule = make_schedule(overrides={(1, 0): 444})
        now = datetime(2026, 1, 31, 23, 45, tzinfo=timezone.utc)
        ahead = schedule.ticks_ahead(now, hours=1)
        assert [t.time.day for t in ahead] == [1, 1]
        assert ahead[0].fuel == 444

    def test_load_rejects_malformed_schedule(self, tmp_path):
        bad = tmp_path / "schedule.json"
        bad.write_text('{"1": []}')
        with pytest.raises(ValueError):
            PriceSchedule.load(bad)


class TestDecideBuy:
    def test_critical_stock_buys_at_any_price(self):
        decision = decide_buy("fuel", 2500, 100_000, NOW, make_schedule(), 320)
        assert decision.buy
        assert "critical" in decision.reason

    def test_bargain_price_buys_with_full_stock(self):
        decision = decide_buy("fuel", 320, 5_000_000, NOW, make_schedule(), 320)
        assert decision.buy
        assert "bargain" in decision.reason

    def test_sufficient_stock_waits(self):
        decision = decide_buy("fuel", 1000, 5_000_000, NOW, make_schedule(), 320)
        assert not decision.buy

    def test_lookahead_waits_when_cheaper_tick_coming(self):
        # Low stock, current tick costs 1000, but two cheaper ticks arrive within 6h.
        schedule = make_schedule(overrides={(9, 28): 400, (9, 30): 450})
        decision = decide_buy("fuel", 1000, 900_000, NOW, schedule, 320)
        assert not decision.buy
        assert "$400" in decision.reason

    def test_lookahead_buys_when_current_is_cheapest(self):
        # Low stock and the current tick beats everything in the window.
        schedule = make_schedule(overrides={(9, 24): 500})
        decision = decide_buy("fuel", 500, 900_000, NOW, schedule, 320)
        assert decision.buy

    def test_schedule_mismatch_falls_back_to_buying_on_low_stock(self):
        # Scraped price wildly different from scheduled 1000: ignore schedule.
        decision = decide_buy("fuel", 2000, 900_000, NOW, make_schedule(), 320)
        assert decision.buy
        assert "mismatch" in decision.reason

    def test_no_schedule_buys_on_low_stock(self):
        decision = decide_buy("fuel", 2000, 900_000, NOW, None, 320)
        assert decision.buy

    def test_co2_uses_co2_prices(self):
        schedule = make_schedule(co2=150)
        decision = decide_buy("co2", 150, 900_000, NOW, schedule, config.CO2_HARD_THRESHOLD)
        # Uniform CO2 schedule: current tick ties the whole window, so buy.
        assert decision.buy
