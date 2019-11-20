from prglunch.scrapers import scrapers_list, OliveScraper

def test_scrapers_count():
    assert len(scrapers_list) > 0


class TestOliveScraper:
    def test_fetch_menu(self):
        s = OliveScraper()
        meals = s.fetch_menu()
        print(meals)
