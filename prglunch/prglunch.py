from prglunch.model import *
from prglunch.scrapers import *
import logging
from prglunch import slack
import argparse

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("chardet").setLevel(logging.WARNING)

#
# Edit this list to configure which restaurants (and in which order) to report
#
SCRAPERS = [
    MahiniScraper(),
    ZauVegetarianScraper(),
    KozlovnaScraper(),
    PintaScraper(),
    ZlataKovadlinaScraper(),
    UHoliseScraper(),
    PetPenezScraper()
]


def get_restaurants() -> List[Restaurant]:
    return [sc.get_restaurant() for sc in SCRAPERS]


def restaurant_to_slack_poll(restaurant: Restaurant) -> str:
    meals = "\n".join(f'- {m.name} *({m.price},-)*' for m in restaurant.menu)
    return f'*{restaurant.name}*\n{meals}\n\n'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--slack-token')
    parser.add_argument('--slack-channel')
    return parser.parse_args()


def main():
    args = parse_args()

    restaurants = get_restaurants()

    poll_options = [restaurant_to_slack_poll(r) for r in restaurants]
    slack.post_poll(poll_options, args.slack_token, args.slack_channel)


if __name__ == '__main__':
    main()
