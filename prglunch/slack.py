import logging
from typing import *

import requests

log = logging.getLogger(__name__)
API_URL = 'https://slack.com/api/chat.command'
# TOKEN = 'xoxp-3990455078-426475007523-450294814544-7463ab2e63fe0011eb7664caeba3d1ff'
# CHANNEL = 'CD8TL598B'
COMMAND = '/poll'


def post_poll(options: List[str], slack_token: str, slack_channel: str):
    if not slack_token or not slack_channel:
        log.error('You need to provide --slack-token and --slack-channel '
                  'to send the menu to slack.')
        return

    log.debug(f'Posting poll with options: {options}')
    options_str = '\n'.join(f'"{o}"' for o in (raw.replace('"', '\'') for raw in options))
    poll_text = f'''"Kam na oběd?" {options_str}'''

    log.debug(f'Slack-formatted message: {poll_text}')

    params = {
        'data': API_URL,
        'token': slack_token,
        'channel': slack_channel,
        'command': COMMAND,
        'text': poll_text
    }
    print(params)
    # requests.post(API_URL, params=params)
