import logging
import re
from abc import ABC, abstractmethod
from typing import List

import requests
from bs4 import BeautifulSoup

from prglunch.model import MenuItem, Restaurant

__all__ = ['BaseScraper', 'MahiniScraper', 'ZauVegetarianScraper', 'KozlovnaScraper',
           'PintaScraper', 'ZlataKovadlinaScraper', 'UHoliseScraper', 'PetPenezScraper']

log = logging.getLogger(__name__)


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


class MahiniScraper(BaseScraper):
    REGEX_PREFIX_PATTERN = r'(VEGE -)|(VÝDEJ \d* -)'

    @property
    def menu_url(self):
        return 'https://www.manihi.cz/menu/'

    def fetch_menu(self) -> List[MenuItem]:
        soup = BeautifulSoup(self.get_menu_page(), 'html.parser')
        candidates = soup.select('div.content.cf.wnd-no-cols div.text-content p strong')
        meal_names = [c.text for c in candidates if c.text.find('Kč') != -1]

        meals = []
        for meal_name in meal_names:
            price = BaseScraper.parse_price_kc(meal_name)

            name_without_price = meal_name.replace('\n', ' ')
            name_without_price = re.sub(BaseScraper.REGEX_PRICE_PATTERN, '', name_without_price)
            name_without_price = re.sub(MahiniScraper.REGEX_PREFIX_PATTERN, '', name_without_price)
            name_without_price = name_without_price.strip()
            meals.append(MenuItem(name_without_price, price))

        return meals

    @property
    def name(self) -> str:
        return "Mahini"


class ZauVegetarianScraper(BaseScraper):
    def fetch_menu(self) -> List[MenuItem]:
        return [
            MenuItem("Samoobslužný bufet (100g)", 29)
        ]

    @property
    def name(self) -> str:
        return "ZAU Vegetariánská restaurace (asijský bufet)"

    @property
    def menu_url(self) -> str:
        return ""


class KozlovnaScraper(BaseScraper):
    def fetch_menu(self) -> List[MenuItem]:
        soup = BeautifulSoup(self.get_menu_page(), 'html.parser')
        meals = []
        candidates = soup.select('table.dailyMenuTable tr')
        for candidate in candidates:
            meal_name_tags = candidate.select('td.td-popis span.td-jidlo-obsah')
            if not meal_name_tags:
                continue
            assert len(meal_name_tags) == 1, f'Expected to find a single meal name, ' \
                f'but found {meal_name_tags}'
            meal_name = meal_name_tags[0].text.replace('\n', ' ').strip()

            if KozlovnaScraper._exclude_item(meal_name):
                continue

            meal_price_tags = candidate.select('td.td-cena')
            meal_price = -1
            if meal_price_tags:
                assert len(meal_price_tags) == 1, f'Expected to find a single meal price, ' \
                    f'but found {meal_name_tags}'
                match = re.search(r'\s*(\d*).*', meal_price_tags[0].text)
                if match:
                    meal_price = int(match.group(1))
            meals.append(MenuItem(meal_name, meal_price))

        return meals

    @staticmethod
    def _exclude_item(name: str) -> bool:
        """
        We want to exclude some items (coffee, lemonades). If this function returns True, the item is to be discarded.
        """
        if name.lower().startswith('espresso'):
            return True

        if name.lower().startswith('u nás vyroben'):
            return True

        return False

    @property
    def name(self) -> str:
        return 'Holešovická Kozlovna'

    @property
    def menu_url(self) -> str:
        return 'http://www.holesovickakozlovna.cz/#pn'


class PintaScraper(BaseScraper):
    def fetch_menu(self) -> List[MenuItem]:
        soup = BeautifulSoup(self.get_menu_page(override_encoding=True), 'html.parser')
        meals = []
        candidates = soup.select('table tr')
        for candidate in candidates:
            tds = candidate.select('td')

            # Only condsider rows with 3 tds
            if len(tds) != 3:
                continue

            meal_name = tds[1].text
            meal_price = BaseScraper.parse_price_kc(tds[2].text)
            meals.append(MenuItem(meal_name, meal_price))

        return meals

    @property
    def name(self) -> str:
        return "Pinta"

    @property
    def menu_url(self) -> str:
        return 'http://www.pinta-restaurace.cz/denni_menu.php'


class ZlataKovadlinaScraper(BaseScraper):
    @property
    def name(self) -> str:
        return 'Zlatá kovadlina'

    @property
    def menu_url(self) -> str:
        return 'http://zlatakovadlina.cz/'

    def fetch_menu(self) -> List[MenuItem]:
        soup = BeautifulSoup(self.get_menu_page(override_encoding=True), 'html.parser')
        meals = []
        candidates = soup.select('div.wpb_wrapper table.rwd-table tr')
        for candidate in candidates:
            tds = candidate.select('td')

            # Only condsider rows with 3 tds
            if len(tds) != 9:
                continue

            if not tds[3].text.strip():  # Skip items with no price text
                continue

            meal_name = tds[2].text
            meal_price = BaseScraper.parse_price_kc(tds[3].text)
            meals.append(MenuItem(meal_name, meal_price))

        return meals


class UHoliseScraper(BaseScraper):
    def fetch_menu(self) -> List[MenuItem]:
        soup = BeautifulSoup(self.get_menu_page(override_encoding=True), 'html.parser')
        meals = []
        candidates = soup.select('div.lcMenuWrapper div.lc_block_wrapper')
        for candidate in candidates:
            column_texts = [child.select('span')[0] for child in list(candidate.children)[1:]]
            meal_name, meal_price = map(lambda x: x.text.capitalize(), column_texts)

            # Skip drinks (0,2 l - Limonáda)
            if meal_name.startswith('0,'):
                continue

            meals.append(MenuItem(meal_name, BaseScraper.parse_price_kc(meal_price)))

        return meals

    @property
    def name(self) -> str:
        return "U Holiše"

    @property
    def menu_url(self) -> str:
        return "https://www.restauraceuholise.cz/menu/denni-menu"


class PetPenezScraper(BaseScraper):
    def fetch_menu(self) -> List[MenuItem]:
        soup = BeautifulSoup(self.get_menu_page(override_encoding=True), 'html.parser')
        meals = []
        tables = soup.select('div.content table')

        # Daily menu
        table = tables[0]
        rows = table.select('tr')
        for row in rows:
            cells = row.select('td')
            name = cells[1].text
            price = self.parse_price_kc(cells[2].text)

            meals.append(MenuItem(name, price))

        # Weekly menu
        table = tables[1]
        rows = table.select('tr')
        for row in rows:
            cells = row.select('td')
            name = cells[1].text
            price = self.parse_price_kc(cells[2].text)
            if price < 60:  # Skip low-priced items (drinks etc.)
                continue

            meals.append(MenuItem(name, price))

        return meals

    @property
    def name(self) -> str:
        return 'Pět Peněz'

    @property
    def menu_url(self) -> str:
        return 'http://www.restauracepetpenez.cz/'
