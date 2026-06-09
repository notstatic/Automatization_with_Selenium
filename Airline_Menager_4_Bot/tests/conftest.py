from unittest.mock import MagicMock

import pytest
from selenium.common.exceptions import NoSuchElementException


class FakeElement:
    def __init__(self, text=""):
        self.text = text
        self.click = MagicMock()
        self.send_keys = MagicMock()

    def is_displayed(self):
        return True

    def is_enabled(self):
        return True


class FakeDriver:
    """Driver double: find_element serves canned elements keyed by locator."""

    def __init__(self):
        self.elements = {}
        self.missing = set()
        self.get = MagicMock()

    def set_text(self, locator, text):
        self.elements[tuple(locator)] = FakeElement(text)

    def element(self, locator):
        """The element for a locator, or None if it was never touched."""
        return self.elements.get(tuple(locator))

    def clicked(self, locator):
        el = self.element(locator)
        return el is not None and el.click.called

    def find_element(self, by, value):
        if (by, value) in self.missing:
            raise NoSuchElementException(value)
        return self.elements.setdefault((by, value), FakeElement())


@pytest.fixture
def fake_driver():
    return FakeDriver()
