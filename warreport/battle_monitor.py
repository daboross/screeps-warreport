import asyncio
import logging

from functools import partial

from warreport import redis_conn as redis, screeps_info, queuing
from warreport.screeps_info import ScreepsError

_LAST_CHECKED_TICK_KEY = "screeps:warreport:last-checked-tick"
_LAST_CHECKED_EXPIRE_SECONDS = 30 * 60
_SEND_TO_BACK_OF_QUEUE_IF_OLDER_THAN_TICKS = 1000

logger = logging.getLogger("warreport")


@asyncio.coroutine
def grab_new_battles(loop):
    """
    :type loop: asyncio.events.AbstractEventLoop
    """
    last_grabbed_tick = yield from loop.run_in_executor(None, redis.get, _LAST_CHECKED_TICK_KEY)
    while True:
        try:
            if last_grabbed_tick is not None:
                battles = yield from loop.run_in_executor(None, partial(screeps_info.grab_battles_uncached,
                                                                        since_tick=last_grabbed_tick))
            else:
                battles = yield from loop.run_in_executor(None, partial(screeps_info.grab_battles_uncached,
                                                                        interval=2000))
        except ScreepsError as e:
            logging.warning("Error accessing battles API: {}".format(e))
        else:
            last_grabbed_tick = battles.get('time')
            if len(battles['rooms']):
                yield from asyncio.gather(
                    loop.run_in_executor(None, partial(redis.set, _LAST_CHECKED_TICK_KEY, last_grabbed_tick,
                                                       ex=_LAST_CHECKED_EXPIRE_SECONDS)),
                    loop.run_in_executor(None, queuing.push_battles_for_processing,
                                         ((obj['_id'], obj['lastPvpTime']) for obj in battles['rooms'])),
                    loop=loop
                )
        yield from asyncio.sleep(60, loop=loop)


@asyncio.coroutine
def process_battles(loop):
    """
    :type loop: asyncio.events.AbstractEventLoop
    """
    while True:
        room_name, hostilities_tick, database_key = yield from loop.run_in_executor(
            None, queuing.get_next_battle_to_process)

        battle_info = yield from loop.run_in_executor(None, partial(screeps_info.get_battle_data,
                                                                    room_name, hostilities_tick))

        if battle_info is None:
            # If we continue without sending queuing a finished battle, the battle will simply be sent to the back of
            # the processing queue. This way, we'll keep checking to see if we have any history parts available every 90
            # seconds, and if we have multiple battles which aren't in order, we'll still get to all of them in good
            # time.
            yield from asyncio.sleep(90, loop=loop)
            continue

        yield from loop.run_in_executor(None, queuing.submit_processed_battle, database_key, battle_info)
