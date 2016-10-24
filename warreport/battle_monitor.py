import asyncio
import logging

import requests

from warreport import redis_conn as redis, screeps_api, data_caching, screeps_info, SLACK_URL

_LAST_CHECKED_TICK_KEY = "screeps:warreport:last-checked-tick"
_LAST_CHECKED_EXPIRE_SECONDS = 30 * 60
_SEND_TO_BACK_OF_QUEUE_IF_OLDER_THAN_TICKS = 2000

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
        if battles and battles.get('ok'):
            last_grabbed_tick = battles.get('time')
            if len(battles['rooms']):
                yield from asyncio.gather(
                    loop.run_in_executor(None, lambda: redis.set(_LAST_CHECKED_TICK_KEY, last_grabbed_tick,
                                                                 ex=_LAST_CHECKED_EXPIRE_SECONDS)),
                    loop.run_in_executor(None, lambda: data_caching.add_battles_to_queue((
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
                latest_tick = yield from loop.run_in_executor(None, redis.get, _LAST_CHECKED_TICK_KEY)
                if latest_tick is not None and int(latest_tick) - int(hostilities_tick) \
                        > _SEND_TO_BACK_OF_QUEUE_IF_OLDER_THAN_TICKS:
                    logger.debug("Battle in {} at {} is {} ticks old - sending to back of queue.".format(
                        room_name, hostilities_tick, int(latest_tick) - int(hostilities_tick)))
                    yield from loop.run_in_executor(None, data_caching.add_battle_to_queue, room_name, hostilities_tick)
                    yield from loop.run_in_executor(None, data_caching.finished_battle, room_name, hostilities_tick)
                    # Don't sleep quite as long, but we still don't want to be constantly checking if the only battles
                    # in our queue are old battles.
                    # It is still OK to sleep this short though, since each individual room's "unavailable" status is
                    # cached for one minute.
                    yield from asyncio.sleep(5, loop=loop)
                    break
                # Cache expires in 60 seconds.
                yield from asyncio.sleep(90, loop=loop)

        if battle_info is None:
            continue  # We've chosen to skip this one

        assert isinstance(battle_info, dict)

        if should_report(battle_info):
            # TODO: get first hostility tick as part of battle data!
            text = format_message_slack(battle_info)
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
                                 .format(slack_response.text, slack_response.status_code, payload))
                    continue  # < don't mark as finished
        else:
            logger.debug("Skipping battle in {} at {} ({}).".format(room_name, hostilities_tick,
                                                                    describe_battle(battle_info)))

        yield from loop.run_in_executor(None, data_caching.finished_battle, room_name, hostilities_tick)


def should_report(battle_info):
    return len(battle_info['player_counts']) >= 2


def format_message_slack(battle_info):
    room_name = battle_info['room']

    return "Battle in <https://screeps.com/a/#!/history/{}?t={}|{}>: {}".format(
        room_name, int(battle_info['hostilities_tick']) - 5, room_name,
        describe_battle(battle_info))


def describe_battle(battle_info):
    items_list = sorted(battle_info['player_counts'].items(), key=lambda t: sum(t[1].values()))
    return " vs. ".join("{} ({})".format(
        name, ", ".join("{}{}".format(count, type[0].upper())
                        for type, count in sorted(parts.items(), key=lambda t: t[1]))
    ) for name, parts in items_list)
