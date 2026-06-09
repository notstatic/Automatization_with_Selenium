"""Pure helpers for parsing scraped values and the fallback buy rule."""

from . import config


def parse_amount(text):
    """Parse an in-game money/stock string like '$ 1,234' or '12,345,678' to int."""
    cleaned = text.replace("$", "").replace(",", "").strip()
    if not cleaned.lstrip("-").isdigit() or not cleaned.lstrip("-"):
        raise ValueError(f"cannot parse amount from {text!r}")
    return int(cleaned)


def should_buy(price, remaining, price_threshold, min_stock=config.MIN_STOCK):
    """Original threshold rule, used when no price schedule is available."""
    return price <= price_threshold or remaining <= min_stock
