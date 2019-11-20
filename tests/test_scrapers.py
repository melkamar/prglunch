from prglunch.prglunch import SCRAPERS
from prglunch.scrapers import *
import pytest


@pytest.mark.parametrize('scraper', SCRAPERS, ids=[s.__class__.__name__ for s in SCRAPERS])
def test_sanity_all_scrapers(scraper):
    """Check that all scrapers return at least something."""
    assert len(scraper.fetch_menu()) > 0


class TestOliveScraper:
    def test_fetch_menu(self):
        s = OliveScraper()
        meals = s.fetch_menu()
        print(meals)
