"""AM4Bot: drives the airline4.net UI through an injected Selenium driver."""

import logging
from datetime import datetime, timezone

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from . import config, parsing, prices
from .config import Selectors

logger = logging.getLogger(__name__)

RECOVERABLE = (NoSuchElementException, TimeoutException, ElementClickInterceptedException)


class AM4Bot:
    def __init__(self, driver, schedule=None, wait_timeout=10):
        self.driver = driver
        self.schedule = schedule
        self.wait = WebDriverWait(driver, wait_timeout)

    def _click(self, locator):
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def _type(self, locator, text):
        self.wait.until(EC.visibility_of_element_located(locator)).send_keys(text)

    def _text(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator)).text

    def _close_popup(self):
        try:
            self._click(Selectors.POPUP_CLOSE)
        except RECOVERABLE:
            logger.debug("no popup to close")

    def login(self, username, password):
        self.driver.get(config.WEBSITE_URL)
        self._click(Selectors.LOGIN_OPEN)
        self._type(Selectors.LOGIN_EMAIL, username)
        self._type(Selectors.LOGIN_PASSWORD, password)
        self._click(Selectors.LOGIN_SUBMIT)
        try:
            self._click(Selectors.FLIGHT_INFO_CLOSE)
        except RECOVERABLE:
            logger.info("no departure popup to close after login")

    def check_fuel(self, now_utc=None):
        self._check_resource(
            resource="fuel",
            open_locators=[Selectors.FUEL_OPEN],
            price_locator=Selectors.FUEL_PRICE,
            buy_locator=Selectors.FUEL_BUY,
            hard_threshold=config.FUEL_HARD_THRESHOLD,
            buy_amount=config.FUEL_BUY_AMOUNT,
            now_utc=now_utc,
        )

    def check_co2(self, now_utc=None):
        self._check_resource(
            resource="co2",
            open_locators=[Selectors.FUEL_OPEN, Selectors.CO2_TAB],
            price_locator=Selectors.CO2_PRICE,
            buy_locator=Selectors.CO2_BUY,
            hard_threshold=config.CO2_HARD_THRESHOLD,
            buy_amount=config.CO2_BUY_AMOUNT,
            now_utc=now_utc,
        )

    def _check_resource(self, resource, open_locators, price_locator, buy_locator,
                        hard_threshold, buy_amount, now_utc=None):
        now_utc = now_utc or datetime.now(timezone.utc)
        try:
            for locator in open_locators:
                self._click(locator)
            price = parsing.parse_amount(self._text(price_locator))
            remaining = parsing.parse_amount(self._text(Selectors.HOLDING))
            decision = prices.decide_buy(
                resource, price, remaining, now_utc, self.schedule, hard_threshold,
            )
            logger.info(
                "%s: price=$%s remaining=%s -> %s (%s)",
                resource, price, remaining, "BUY" if decision.buy else "wait", decision.reason,
            )
            if decision.buy:
                self._type(Selectors.AMOUNT_INPUT, str(buy_amount))
                self._click(buy_locator)
                after = parsing.parse_amount(self._text(Selectors.HOLDING))
                if after > remaining:
                    logger.info(
                        "%s purchased at $%s (stock %s -> %s)", resource, price, remaining, after,
                    )
                else:
                    logger.warning("%s purchase had no effect, probably not enough money", resource)
        except RECOVERABLE as exc:
            logger.warning("check_%s failed: %s", resource, exc.__class__.__name__)
        except ValueError as exc:
            logger.error("check_%s: %s", resource, exc)
        finally:
            self._close_popup()

    def start_eco_campaign(self):
        self._start_campaign("Eco Friendly", [
            Selectors.ECO_CAMPAIGN_ROW,
            Selectors.ECO_CAMPAIGN_START,
        ])

    def start_reputation_campaign(self):
        self._start_campaign("Increase Reputation", [
            Selectors.REPUTATION_CAMPAIGN_ROW,
            Selectors.DURATION_SELECT,
            Selectors.DURATION_24H,
            Selectors.REPUTATION_START,
        ])

    def _start_campaign(self, name, steps):
        try:
            self._click(Selectors.FINANCE_OPEN)
            self._click(Selectors.MARKETING_TAB)
            self._click(Selectors.NEW_CAMPAIGN)
            for locator in steps:
                self._click(locator)
            logger.info("started campaign: %s", name)
        except RECOVERABLE as exc:
            logger.info("campaign %s not started (%s)", name, exc.__class__.__name__)
        finally:
            self._close_popup()

    def depart_all(self):
        try:
            self._click(Selectors.STATUS_OPEN)
            self._click(Selectors.LANDED_TAB)
            self._click(Selectors.DEPART_ALL)
            logger.info("departed all waiting planes")
        except RECOVERABLE as exc:
            logger.info("nothing to depart (%s)", exc.__class__.__name__)
        finally:
            try:
                self._click(Selectors.FLIGHT_INFO_CLOSE)
            except RECOVERABLE:
                logger.debug("no flight info panel to close")
