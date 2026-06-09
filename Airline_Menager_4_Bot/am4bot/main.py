"""Entry point: create the driver, log in and run the bot loop."""

import logging
import time
from datetime import datetime, timezone

from selenium import webdriver

from . import config
from .bot import AM4Bot
from .prices import PriceSchedule

logger = logging.getLogger(__name__)


def create_driver():
    # Selenium Manager resolves chromedriver automatically.
    return webdriver.Chrome()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    username, password = config.get_credentials()

    try:
        schedule = PriceSchedule.load()
        logger.info("price schedule loaded (%d days)", len(schedule.days))
    except (OSError, ValueError, KeyError) as exc:
        schedule = None
        logger.warning("price schedule unavailable (%s); using threshold fallback", exc)

    driver = create_driver()
    bot = AM4Bot(driver, schedule=schedule)
    try:
        bot.login(username, password)
        last_tick = None
        while True:
            # Prices change on half-hour UTC boundaries; check once per tick.
            now = datetime.now(timezone.utc)
            tick = (now.day, now.hour, now.minute >= 30)
            if tick != last_tick:
                bot.check_fuel(now)
                bot.check_co2(now)
                last_tick = tick
            bot.start_eco_campaign()
            bot.start_reputation_campaign()
            bot.depart_all()
            time.sleep(config.LOOP_SLEEP_SECONDS)
    except KeyboardInterrupt:
        logger.info("stopping")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
