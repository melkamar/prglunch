from prglunch.prglunch import SCRAPERS
from prglunch.scrapers import *
import pytest


class TestMahiniScraper:
    def test_fetch_menu(self):
        assert True


class TestKozlovnaScraper:
    def test_fetch_menu(self):
        assert True


@pytest.mark.parametrize('scraper', SCRAPERS, ids=[s.__class__.__name__ for s in SCRAPERS])
def test_sanity_all_scrapers(scraper):
    """Check that all scrapers return at least something."""
    assert len(scraper.fetch_menu()) > 0


class TestKovadlinaScraper:
    def test_fetch_menu(self):
        s = ZlataKovadlinaScraper()
        meals = s.fetch_menu()
        print(meals)


class TestUHoliseScraper:
    def test_fetch_menu(self):
        s = UHoliseScraper()
        meals = s.fetch_menu()
        print(meals)


class TestPetPenezScraper:
    def test_fetch_menu(self):
        s = PetPenezScraper()
        meals = s.fetch_menu()
        print(meals)
        assert len(meals) > 0

class TestBentoCafeScraper:
    def test_fetch_menu(self):
        s = BentoCafeScraper()
        meals = s.fetch_menu()
        print(meals)
        assert len(meals) > 0
