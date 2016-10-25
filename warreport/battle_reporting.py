import asyncio
import logging

import requests
from functools import partial

from warreport import SLACK_URL, queuing
from warreport.constants import civilian, scout

logger = logging.getLogger("warreport")


@asyncio.coroutine
def report_battles(loop):
    """
    :type loop: asyncio.events.AbstractEventLoop
    """
    while True:
        battle_info, database_key = yield from loop.run_in_executor(None, queuing.get_next_battle_to_report)
        assert isinstance(battle_info, dict)
        if should_report(battle_info):
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
                    # When we can't post, let's just go and try the next battle. If we don't tell queuing that we've
                    # finished the battle, it will just go to the end of the queue, and we'll try to report it again
                    # once we've reported everything else.
                    yield from asyncio.sleep(60, loop=loop)
                    continue  # < don't mark as finished
            logger.debug("Reported battle {}:{}!".format(battle_info['room'], battle_info['hostilities_tick']))
        else:
            logger.debug("Skipping battle {}:{} ({}).".format(battle_info['room'],
                                                              battle_info['hostilities_tick'],
                                                              describe_battle(battle_info)))
        yield from loop.run_in_executor(None, queuing.mark_battle_reported, database_key)


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

    return "<https://screeps.com/a/#!/history/{}?t={}|{}{}>: {} tick battle{}: {}".format(
        room_name, int(battle_info['hostilities_tick']) - 5, room_name,
        describe_rcl(battle_info), describe_duration(battle_info),
        describe_defender(battle_info), describe_battle(battle_info))


def describe_rcl(battle_info):
    if 'rcl' in battle_info:
        return " (RCL {})".format(battle_info['rcl'])
    else:
        return ""


def describe_duration(battle_info):
    if 'duration' in battle_info:
        return "{0:03d}".format(battle_info['duration'])
    else:
        return "???"


def describe_defender(battle_info):
    if 'owner' in battle_info:
        return ", {} defending".format(battle_info['owner'])
    else:
        return ""


def describe_battle(battle_info):
    # Sort by a tuple of (not the owner, username) so that the owner of a room always comes first.
    items_list = sorted(battle_info['player_counts'].items(),
                        key=lambda t: (t[0] != battle_info.get('owner'), t[0]))
    return " vs. ".join("{}'s {}".format(name, describe_player_creep_list(parts)) for name, parts in items_list)


def describe_player_creep_list(creeps):
    creeps = sorted(creeps.items(), key=lambda t: t[0])
    if len(creeps) >= 2:
        last_role, last_count = creeps[-1]
        return "{} and {}".format(
            ", ".join(describe_creep(role, count) for role, count in creeps[:-1]),
            describe_creep(last_role, last_count)
        )
    else:
        return ", ".join(describe_creep(role, count) for role, count in creeps)


def describe_creep(role, count):
    if count > 1:
        return "{} {}s".format(count, role)
    else:
        return "{} {}".format(count, role)
