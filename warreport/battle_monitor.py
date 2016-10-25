import asyncio
import logging

from functools import partial

from warreport import redis_conn as redis, screeps_api, data_caching, screeps_info, sighandler

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
        if sighandler.has_exited():
            return
        if last_grabbed_tick is not None:
            battles = yield from loop.run_in_executor(None, partial(screeps_api.battles, sinceTick=last_grabbed_tick))
        else:
            battles = yield from loop.run_in_executor(None, partial(screeps_api.battles, interval=2000))
        if battles and battles.get('ok'):
            last_grabbed_tick = battles.get('time')
            if len(battles['rooms']):
                yield from asyncio.gather(
                    loop.run_in_executor(None, partial(redis.set, _LAST_CHECKED_TICK_KEY, last_grabbed_tick,
                                                       ex=_LAST_CHECKED_EXPIRE_SECONDS)),
                    loop.run_in_executor(None, partial(data_caching.add_battles_to_processing_queue,
                                                       ((obj['_id'], obj['lastPvpTime'])
                                                        for obj in battles['rooms']))),
                    loop=loop
                )
        yield from sighandler.sleep(60)


@asyncio.coroutine
def process_battles(loop):
    """
    :type loop: asyncio.events.AbstractEventLoop
    """
    while True:
        room_name, hostilities_tick = yield from loop.run_in_executor(None, data_caching.get_next_battle_to_process)
        battle_info = None
        while battle_info is None:
            battle_info = yield from sighandler.wait_for_this_or_exited(loop.run_in_executor(
                None, partial(screeps_info.get_battle_data, room_name, hostilities_tick)))
            if sighandler.has_exited():
                return
            if battle_info is None:
                latest_tick = yield from loop.run_in_executor(None, redis.get, _LAST_CHECKED_TICK_KEY)
                if latest_tick is not None and int(latest_tick) - int(hostilities_tick) \
                        > _SEND_TO_BACK_OF_QUEUE_IF_OLDER_THAN_TICKS:
                    logger.debug("Battle in {} at {} is {} ticks old - sending to back of queue.".format(
                        room_name, hostilities_tick, int(latest_tick) - int(hostilities_tick)))
                    yield from loop.run_in_executor(None, data_caching.add_battle_to_processing_queue, room_name,
                                                    hostilities_tick)
                    yield from loop.run_in_executor(None, data_caching.finished_processing_battle, room_name,
                                                    hostilities_tick, None)
                    # Don't sleep quite as long, but we still don't want to be constantly checking if the only battles
                    # in our queue are old battles.
                    # It is still OK to sleep this short though, since each individual room's "unavailable" status is
                    # cached for one minute.
                    yield from sighandler.sleep(5)
                    break
                # Cache expires in 60 seconds.
                exited = yield from sighandler.sleep(90)
                if exited:
                    break

        if battle_info is None:
            continue  # We've chosen to skip this one

        yield from loop.run_in_executor(None, data_caching.finished_processing_battle, room_name, hostilities_tick,
                                        battle_info)
