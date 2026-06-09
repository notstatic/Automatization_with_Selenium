from datetime import datetime, timezone

from am4bot import config
from am4bot.bot import AM4Bot
from am4bot.config import Selectors

NOW = datetime(2026, 6, 9, 12, 0, tzinfo=timezone.utc)


def make_bot(driver):
    # No schedule: decisions follow the threshold fallback rules.
    return AM4Bot(driver, schedule=None, wait_timeout=0)


class TestCheckFuel:
    def test_buys_at_bargain_price(self, fake_driver):
        fake_driver.set_text(Selectors.FUEL_PRICE, "$ 300")
        fake_driver.set_text(Selectors.HOLDING, "5,000,000")
        make_bot(fake_driver).check_fuel(NOW)
        amount = fake_driver.element(Selectors.AMOUNT_INPUT)
        amount.send_keys.assert_called_once_with(str(config.FUEL_BUY_AMOUNT))
        assert fake_driver.clicked(Selectors.FUEL_BUY)
        assert fake_driver.clicked(Selectors.POPUP_CLOSE)

    def test_skips_when_expensive_and_stocked(self, fake_driver):
        fake_driver.set_text(Selectors.FUEL_PRICE, "$ 2,400")
        fake_driver.set_text(Selectors.HOLDING, "5,000,000")
        make_bot(fake_driver).check_fuel(NOW)
        assert not fake_driver.clicked(Selectors.FUEL_BUY)
        assert fake_driver.element(Selectors.AMOUNT_INPUT) is None
        assert fake_driver.clicked(Selectors.POPUP_CLOSE)

    def test_unparseable_price_does_not_buy_and_closes_panel(self, fake_driver):
        fake_driver.set_text(Selectors.FUEL_PRICE, "N/A")
        make_bot(fake_driver).check_fuel(NOW)
        assert not fake_driver.clicked(Selectors.FUEL_BUY)
        assert fake_driver.clicked(Selectors.POPUP_CLOSE)


class TestCheckCO2:
    def test_buys_on_low_stock(self, fake_driver):
        fake_driver.set_text(Selectors.CO2_PRICE, "$ 150")
        fake_driver.set_text(Selectors.HOLDING, "900,000")
        make_bot(fake_driver).check_co2(NOW)
        assert fake_driver.clicked(Selectors.CO2_TAB)
        amount = fake_driver.element(Selectors.AMOUNT_INPUT)
        amount.send_keys.assert_called_once_with(str(config.CO2_BUY_AMOUNT))
        assert fake_driver.clicked(Selectors.CO2_BUY)

    def test_skips_when_expensive_and_stocked(self, fake_driver):
        fake_driver.set_text(Selectors.CO2_PRICE, "$ 190")
        fake_driver.set_text(Selectors.HOLDING, "5,000,000")
        make_bot(fake_driver).check_co2(NOW)
        assert not fake_driver.clicked(Selectors.CO2_BUY)


class TestLogin:
    def test_enters_credentials_and_submits(self, fake_driver):
        make_bot(fake_driver).login("user@example.com", "hunter2")
        fake_driver.get.assert_called_once_with(config.WEBSITE_URL)
        fake_driver.element(Selectors.LOGIN_EMAIL).send_keys.assert_called_once_with("user@example.com")
        fake_driver.element(Selectors.LOGIN_PASSWORD).send_keys.assert_called_once_with("hunter2")
        assert fake_driver.clicked(Selectors.LOGIN_SUBMIT)


class TestDepartAll:
    def test_departs_when_button_present(self, fake_driver):
        make_bot(fake_driver).depart_all()
        assert fake_driver.clicked(Selectors.DEPART_ALL)

    def test_missing_depart_button_does_not_crash(self, fake_driver):
        fake_driver.missing.add(Selectors.DEPART_ALL)
        make_bot(fake_driver).depart_all()
        assert fake_driver.clicked(Selectors.FLIGHT_INFO_CLOSE)


class TestCampaigns:
    def test_eco_campaign_clicks_through(self, fake_driver):
        make_bot(fake_driver).start_eco_campaign()
        assert fake_driver.clicked(Selectors.ECO_CAMPAIGN_ROW)
        assert fake_driver.clicked(Selectors.ECO_CAMPAIGN_START)
        assert fake_driver.clicked(Selectors.POPUP_CLOSE)

    def test_unavailable_campaign_still_closes_panel(self, fake_driver):
        fake_driver.missing.add(Selectors.NEW_CAMPAIGN)
        make_bot(fake_driver).start_reputation_campaign()
        assert not fake_driver.clicked(Selectors.REPUTATION_START)
        assert fake_driver.clicked(Selectors.POPUP_CLOSE)
