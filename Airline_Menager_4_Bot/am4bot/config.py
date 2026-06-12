"""Thresholds, purchase amounts, scheduling parameters and page selectors."""

import os

from selenium.webdriver.common.by import By

WEBSITE_URL = "https://www.airline4.net/"

# Buying thresholds
FUEL_HARD_THRESHOLD = 320       # $/1000 lbs: always buy at or below this price
CO2_HARD_THRESHOLD = 80         # $/1000 quotas: always buy at or below this price
MIN_STOCK = 1_000_000           # below this, start looking for a good tick to refill
CRITICAL_STOCK = 300_000        # below this, buy immediately regardless of price
FUEL_BUY_AMOUNT = 9_000_000
CO2_BUY_AMOUNT = 8_000_000

# Look-ahead algorithm (see am4bot.prices)
LOOKAHEAD_HOURS = 6             # how far into the price schedule to look
LOOKAHEAD_TOP_N = 2             # buy if the current tick is among the N cheapest in the window
SCHEDULE_MISMATCH_TOLERANCE = 0.10  # scraped vs scheduled price deviation that disables look-ahead

# Main loop
LOOP_SLEEP_SECONDS = 60


def get_credentials():
    """Read AM4 credentials from the environment."""
    try:
        return os.environ["AM4_USERNAME"], os.environ["AM4_PASSWORD"]
    except KeyError as exc:
        raise SystemExit(
            f"Missing environment variable {exc}. "
            "Set AM4_USERNAME and AM4_PASSWORD before running the bot."
        ) from None


class Selectors:
    """All page locators in one place; the game UI shifting only breaks this file."""

    # Login
    LOGIN_OPEN = (By.XPATH, "/html/body/div[3]/div[1]/div[5]/button[1]")
    LOGIN_EMAIL = (By.ID, "lEmail")
    LOGIN_PASSWORD = (By.ID, "lPass")
    LOGIN_SUBMIT = (By.ID, "btnLogin")
    FLIGHT_INFO_CLOSE = (By.XPATH, '//*[@id="flightInfo"]/div[4]/span')

    # Fuel / CO2 panel
    FUEL_OPEN = (By.XPATH, "/html/body/div[7]/div/div[3]/div[3]")
    FUEL_PRICE = (By.XPATH, '//*[@id="fuelMain"]/div/div[1]/span[2]/b')
    FUEL_BUY = (By.XPATH, '//*[@id="fuelMain"]/div/div[7]/div/button[2]')
    CO2_TAB = (By.XPATH, "/html/body/div[5]/div/div/div[3]/div[1]/button[2]")
    CO2_PRICE = (By.XPATH, '//*[@id="co2Main"]/div/div[2]/span[2]/b')
    CO2_BUY = (By.XPATH, '//*[@id="co2Main"]/div/div[8]/div/button[2]')
    HOLDING = (By.ID, "holding")
    AMOUNT_INPUT = (By.ID, "amountInput")
    POPUP_CLOSE = (By.XPATH, '//*[@id="popup"]/div/div/div[1]/div/span')

    # Marketing campaigns
    FINANCE_OPEN = (By.XPATH, "/html/body/div[7]/div/div[3]/div[5]")
    MARKETING_TAB = (By.XPATH, "/html/body/div[5]/div/div/div[3]/div[1]/button[2]")
    NEW_CAMPAIGN = (By.XPATH, "/html/body/div[5]/div/div/div[3]/div[2]/div/div[1]/div[2]/button")
    ECO_CAMPAIGN_ROW = (By.XPATH, '//*[@id="campaign-1"]/table/tbody/tr[2]')
    ECO_CAMPAIGN_START = (By.XPATH, '//*[@id="marketingStart"]/table/tbody/tr/td[3]/button')
    REPUTATION_CAMPAIGN_ROW = (By.XPATH, '//*[@id="campaign-1"]/table/tbody/tr[1]')
    DURATION_SELECT = (By.ID, "dSelector")
    DURATION_24H = (By.XPATH, '//*[@id="dSelector"]/option[6]')
    REPUTATION_START = (By.ID, "c4Btn")

    # Departures
    STATUS_OPEN = (By.XPATH, "/html/body/div[7]/div/div[3]/div[1]")
    LANDED_TAB = (By.XPATH, "/html/body/div[7]/div/div[2]/div[6]/div[5]/div/div/div/button[2]")
    DEPART_ALL = (By.XPATH, '//*[@id="listDepartAll"]/div/button')
