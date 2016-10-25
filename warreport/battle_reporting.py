import asyncio
import logging

import requests
from functools import partial

from warreport import data_caching, SLACK_URL
from warreport.constants import civilian, scout

logger = logging.getLogger("warreport")


@asyncio.coroutine
def report_battles(loop):
    """
    :type loop: asyncio.events.AbstractEventLoop
    """
    while True:
        battle_info = yield from loop.run_in_executor(None, data_caching.get_next_reportable_battle_info)
        assert isinstance(battle_info, dict)
        if should_report(battle_info):
            # TODO: get first hostility tick as part of battle data!
            text = format_message(battle_info)
            if SLACK_URL is None:
                logger.info(text)
            else:
                payload = {
                    "text": text,
                }
                slack_response = yield from loop.run_in_executor(None, partial(requests.post, SLACK_URL, json=payload))
                assert isinstance(slack_response, requests.Response)
                if slack_response.status_code != 200:
                    logger.error("Couldn't post to slack! {} ({}, for payload {})"
                                 .format(slack_response.text, slack_response.status_code, payload))
                    yield from asyncio.sleep(60, loop=loop)  # Try again in 30 seconds.
                    continue  # < don't mark as finished
        else:
            logger.debug("Skipping battle in {} at {} ({}).".format(battle_info['room'],
                                                                    battle_info['hostilities_tick'],
                                                                    describe_battle(battle_info)))
        yield from loop.run_in_executor(None, data_caching.finished_reporting_battle, battle_info)


def should_report(battle_info):
    # Don't report a single player dismantling their own things
    if len(battle_info['player_counts']) < 2:
        return False
    # Don't report a single civilian or scout walking into someone's owned room and being shot down
    if not any(any(role != civilian and role != scout for role in creeps.keys())
               for player, creeps in battle_info['player_counts'].items() if battle_info.get('owner') != player):
        return False
    return True


def format_message(battle_info):
    room_name = battle_info['room']

    return "Battle in <https://screeps.com/a/#!/history/{}?t={}|{}>{}: {}".format(
        room_name, int(battle_info['hostilities_tick']) - 5, room_name,
        describe_room(battle_info), describe_battle(battle_info))


def describe_room(battle_info):
    if 'owner' in battle_info:
        if 'rcl' in battle_info:
            return ' ({}, {})'.format(battle_info['owner'], battle_info['rcl'])
        else:
            return ' ({})'.format(battle_info['owner'])
    else:
        return ''


def describe_battle(battle_info):
    # Sort by a tuple of (not the owner, username) so that the owner of a room always comes first.
    items_list = sorted(battle_info['player_counts'].items(),
                        key=lambda t: (t[0] != battle_info.get('owner'), t[0]))
    return " vs. ".join("{} ({})".format(
        name,
        ", ".join("{} {}{}".format(count, type, 's' if count > 1 else '')
                  for type, count in sorted(parts.items(), key=lambda t: t[0])),
    ) for name, parts in items_list)
