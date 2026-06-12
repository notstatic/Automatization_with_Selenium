import pytest

from am4bot.parsing import parse_amount, should_buy


class TestParseAmount:
    @pytest.mark.parametrize("text,expected", [
        ("$ 1,234", 1234),
        ("1,234,567", 1234567),
        ("300", 300),
        ("  $ 42  ", 42),
        ("-5", -5),
    ])
    def test_valid(self, text, expected):
        assert parse_amount(text) == expected

    @pytest.mark.parametrize("text", ["", "  ", "$", "N/A", "12.5", "1,234 lbs"])
    def test_invalid_raises(self, text):
        with pytest.raises(ValueError):
            parse_amount(text)


class TestShouldBuy:
    def test_buys_at_threshold(self):
        assert should_buy(320, 5_000_000, price_threshold=320)

    def test_skips_just_above_threshold(self):
        assert not should_buy(321, 5_000_000, price_threshold=320)

    def test_buys_at_min_stock(self):
        assert should_buy(2500, 1_000_000, price_threshold=320, min_stock=1_000_000)

    def test_skips_just_above_min_stock(self):
        assert not should_buy(2500, 1_000_001, price_threshold=320, min_stock=1_000_000)
