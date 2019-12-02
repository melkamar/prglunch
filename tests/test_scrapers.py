from prglunch.scrapers import scrapers_list, OliveScraper, RebelWingsScraper, PotrefenaHusaScraper


def test_scrapers_count():
    assert len(scrapers_list) > 0


class TestOliveScraper:
    def test_fetch_menu(self):
        s = OliveScraper()
        meals = s.fetch_menu()
        print(meals)


class TestRebelWingsScraper:
    def test_fetch_menu(self):
        s = RebelWingsScraper()
        meals = s.fetch_menu()
        print(meals)


class TestPotrefenaHusaScraper:
    def test_fetch_menu(self):
        s = PotrefenaHusaScraper()
        meals = s.fetch_menu()
        print(meals)
