import asyncio
import logging

import requests

from warreport import redis_conn as redis, screeps_api, data_caching, screeps_info, SLACK_URL

_LAST_CHECKED_TICK_KEY = "screeps:warreport:last-checked-tick"

logger = logging.getLogger("warreport")


@asyncio.coroutine
def grab_new_battles(loop):
    """
    :type loop: asyncio.events.AbstractEventLoop
    """
    last_grabbed_tick = yield from loop.run_in_executor(None, redis.get, _LAST_CHECKED_TICK_KEY)
    while True:
        if last_grabbed_tick is not None:
            battles = yield from loop.run_in_executor(None, lambda: screeps_api.battles(sinceTick=last_grabbed_tick))
        else:
            battles = yield from loop.run_in_executor(None, lambda: screeps_api.battles(interval=2000))
        if battles.get('ok'):
            last_grabbed_tick = battles.get('time')
            if len(battles['rooms']):
                yield from asyncio.gather(
                    loop.run_in_executor(None,
                                         lambda: redis.set(_LAST_CHECKED_TICK_KEY, last_grabbed_tick, ex=30 * 60)),
                    loop.run_in_executor(None,
                                         lambda: data_caching.add_battles_to_queue((
                                             (obj['_id'], obj['lastPvpTime']) for obj in battles['rooms']))),
                    loop=loop
                )
        yield from asyncio.sleep(5 * 60, loop=loop)


@asyncio.coroutine
def process_battles(loop):
    while True:
        room_name, hostilities_tick = yield from loop.run_in_executor(None, data_caching.get_next_battle_blocking)
        battle_info = None
        while battle_info is None:
            battle_info = yield from loop.run_in_executor(
                None, lambda: screeps_info.get_battledata(room_name, hostilities_tick))
            if battle_info is None:
                yield from asyncio.sleep(2 * 60, loop=loop)

        assert isinstance(battle_info, dict)

        if should_report(battle_info):
            # TODO: get first hostility tick as part of battle data!
            text = "Battle in <https://screeps.com/a/#!/history/{}?t={}|{}>: {}" \
                .format(room_name, hostilities_tick - 10, room_name,
                        " vs. ".join("{} ({} total parts)".format(name, parts)
                                     for name, parts in battle_info['player_counts'].items()))
            if SLACK_URL is None:
                logger.info(text)
            else:
                # TODO: another queue of messages in redis for posting to slack, so we can keep processing more data and
                # post to slack at the same time
                payload = {
                    "text": text,
                }
                slack_response = yield from loop.run_in_executor(None, lambda: requests.post(SLACK_URL, json=payload))
                assert isinstance(slack_response, requests.Response)
                if slack_response.status_code != 200:
                    logger.error("Couldn't post to slack! {} ({}, for payload {})"
                                 .format(slack_response.content, slack_response.status_code, payload))
                    continue  # < don't mark as finished
        else:
            logger.debug("Skipping battle in {} at {} ({})."
                         .format(room_name, hostilities_tick,
                                 " vs. ".join("{} ({} total parts)".format(name, parts)
                                              for name, parts in battle_info['player_counts'].items())))
        yield from loop.run_in_executor(None, data_caching.finished_battle, room_name, hostilities_tick)


def should_report(battle_info):
    return len(battle_info['player_counts']) >= 2
