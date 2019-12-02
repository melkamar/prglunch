import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup

from prglunch.model import MenuItem, Restaurant

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

__all__ = ['scrapers_list']

# This list will contain all scrapers registered by @scraper
scrapers_list = []


def scraper(cls):
    """
    Decorator to register a scraper class. All scraper classes that should be used must be
    decorated using this.

    The decorator just instantiates the class and stores it in the scrapers_list.

    :param cls: The decorated class
    :return:
    """
    scrapers_list.append(cls())

    def wrapped_class():
        return cls()

    return wrapped_class


class BaseScraper(ABC):
    """
    Interface for concrete scrapers.

    A scraper is responsible for fetching and parsing a restaurant menu.
    """
    REGEX_PRICE_PATTERN = r'(?:(\d+)\s*[Kk][Čč])|(?:(\d+)\s*,[-–])'

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

    @staticmethod
    def get_current_weekday() -> int:
        return datetime.now().weekday()


@scraper
class OliveScraper(BaseScraper):
    def fetch_menu(self) -> List[MenuItem]:
        result = []

        # True if the iteration is inside the day we want the menu for. If this is False then we
        # are not adding menu items to the result set
        inside_wanted_day = False

        soup = self.get_soup_of_menu()
        meal_wrappers_tags = soup.select('div#detail_content_block tr')
        for meal_wrapper in meal_wrappers_tags:
            day_of_week_word = DAYS_OF_WEEK[self.get_current_weekday()]
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


@scraper
class RebelWingsScraper(BaseScraper):
    def fetch_menu(self) -> List[MenuItem]:
        result = []

        soup = self.get_soup_of_menu()
        meal_wrappers_tags = soup.select('div.foodlist')

        for meal_wrappers_tag in meal_wrappers_tags:
            header_tag = meal_wrappers_tag.select_one('h2')
            if header_tag is None:
                continue

            header_text = header_tag.text.lower()
            if self._should_skip_header(header_text):
                continue

            day_of_week = self._get_day_of_week_from_header(header_text)
            if self.get_current_weekday() != day_of_week:
                continue

            # Now we are in the tag of the current day - process that

            food_tags = meal_wrappers_tag.select('div.foodname')
            price_tags = meal_wrappers_tag.select('div.foodprice')

            for food_tag, price_tag in zip(food_tags, price_tags):
                food_name = food_tag.text.strip()
                food_price = self.parse_price_kc(price_tag.text)
                result.append(MenuItem(food_name, food_price))

        return result

    @staticmethod
    def _get_day_of_week_from_header(header_text: str) -> int:
        match = re.search(r'^([^/]+)', header_text)
        if not match:
            return -1

        day_name = match.group(1).strip().lower()
        return DAYS_OF_WEEK.index(day_name)

    @staticmethod
    def _should_skip_header(header_text):
        for blacklisted_text in [
            'acqua comunale',
            'hit týdne'
        ]:
            if blacklisted_text in header_text:
                return True

        return False

    @property
    def name(self) -> str:
        return 'Rebel Wings'

    @property
    def menu_url(self) -> str:
        return 'http://www.rebelwings.cz/#weeklymenu'


@scraper
class PotrefenaHusaScraper(BaseScraper):
    def fetch_menu(self) -> List[MenuItem]:
        result = []

        soup = self.get_soup_of_menu()
        meals_div = soup.select_one('div.denninabidka')

        meal_names_tags = meals_div.select('h4')
        meal_prices_tags = meals_div.select('span.price')
        meal_details_tags = meals_div.select('p')

        for meal_name_tag, meal_price_tag, meal_details_tag in zip(meal_names_tags,
                                                                   meal_prices_tags,
                                                                   meal_details_tags):
            meal_full_name = '{} {}'.format(meal_name_tag.text.replace('\xa0', ' ').strip(),
                                            meal_details_tag.text.replace('\xa0', ' ').strip())

            meal_price = self.parse_price_kc(meal_price_tag.text.strip())

            result.append(MenuItem(meal_full_name, meal_price))

        return result

    @property
    def name(self) -> str:
        return 'Potrefená Husa'

    @property
    def menu_url(self) -> str:
        return 'https://www.potrefena-husa.eu/'
