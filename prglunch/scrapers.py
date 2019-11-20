import logging
import re
from abc import ABC, abstractmethod
from typing import List
import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from prglunch.model import MenuItem, Restaurant

__all__ = ['OliveScraper']

log = logging.getLogger(__name__)

DAYS_OF_WEEK = [
    'pondělí',
    'úterý',
    'středa',
    'čtvrtek',
    'pátek',
    'sobota',
    'neděle',
]


class BaseScraper(ABC):
    """
    Interface for concrete scrapers.

    A scraper is responsible for fetching and parsing a restaurant menu.
    """
    REGEX_PRICE_PATTERN = r'(?:(\d+)\s*[Kk][Čč])|(?:(\d+)\s*,-)'

    def get_restaurant(self):
        return Restaurant(self.name, self.fetch_menu())

    @abstractmethod
    def fetch_menu(self) -> List[MenuItem]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def menu_url(self) -> str:
        pass

    def get_menu_page(self, override_encoding=False) -> str:
        response = requests.get(self.menu_url)
        response.raise_for_status()

        if override_encoding:
            response.encoding = response.apparent_encoding
        return response.text.replace('\xa0', ' ')

    @staticmethod
    def parse_price_kc(price_kc_text: str) -> int:
        m = re.search(BaseScraper.REGEX_PRICE_PATTERN, price_kc_text)
        if m:
            try:  # Return the first non-None captured group value
                return int(next(x for x in m.groups() if x))
            except StopIteration:
                pass  # Fall to the return below

        return -1

    def get_soup_of_menu(self) -> BeautifulSoup:
        """Get the BeautifulSoup object populated with the downloaded HTML menu"""
        return BeautifulSoup(self.get_menu_page(), 'html.parser')


class OliveScraper(BaseScraper):
    def fetch_menu(self) -> List[MenuItem]:
        result = []

        # True if the iteration is inside the day we want the menu for. If this is False then we
        # are not adding menu items to the result set
        inside_wanted_day = False

        soup = self.get_soup_of_menu()
        meal_wrappers_tags = soup.select('div#detail_content_block tr')
        for meal_wrapper in meal_wrappers_tags:
            day_of_week_word = DAYS_OF_WEEK[datetime.now().weekday()]
            if meal_wrapper.text.strip().lower() == day_of_week_word:
                inside_wanted_day = True
                continue

            if not inside_wanted_day:
                continue

            if meal_wrapper.text.strip().lower() in DAYS_OF_WEEK:
                # We are already inside a day of week we are looking for and just got a header for
                # another day of week -> we are done
                break

            # e.g. "Polévka: **Kulajda s houbami / Dill sour soup"
            full_meal_name = meal_wrapper.select_one('th').text

            match = re.search(r'\*\*([^/]+)', full_meal_name)
            if match:
                meal_name = match.group(1).strip()
            else:
                meal_name = 'N/A'

            # Ignore certain meals
            if meal_name in [
                'Denní nabídka jídel z Hummus a Gyros baru!'
            ]:
                continue

            full_meal_price = meal_wrapper.select_one('td').text
            price_match = re.search(self.REGEX_PRICE_PATTERN, full_meal_price)
            if price_match:
                meal_price = price_match.group(1)
            else:
                meal_price = -1

            result.append(MenuItem(meal_name, meal_price))

        return result

    @property
    def name(self) -> str:
        return 'Olive'

    @property
    def menu_url(self) -> str:
        return 'http://www.olivefood.cz/olive-florentinum/10/'
