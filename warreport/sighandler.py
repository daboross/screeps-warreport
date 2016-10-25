import asyncio
import logging

import signal
from asyncio.tasks import FIRST_COMPLETED

_exit_future = None
_loop = None
logger = logging.getLogger("warreport")


def exited_future():
    return _exit_future


@asyncio.coroutine
def sleep(time):
    """
    Sleeps for a given number of ticks, or until the program has exited.
    """
    try:
        asyncio.wait_for(asyncio.shield(exited_future()), time, loop=_loop)
    except TimeoutError:
        return False
    else:
        return True


@asyncio.coroutine
def wait_for_this_or_exited(coroutine):
    done, not_done = yield from asyncio.wait([asyncio.shield(exited_future()), coroutine],
                                             loop=_loop, return_when=FIRST_COMPLETED)
    for coro in done:
        if coro == coroutine:
            return coro.result()


def has_exited():
    return _exit_future.done()


def trigger_exit():
    if not _exit_future.done():
        logger.debug("Exiting!")
        _exit_future.set_result(True)
    else:
        logger.debug("Exit future already set.")


def trigger_exit_threadsafe():
    logger.debug("ThreadSafe exit triggering now")
    _loop.call_soon_threadsafe(trigger_exit)


def setup(loop):
    """
    :type loop: asyncio.events.AbstractEventLoop
    """
    global _exit_future, _loop
    _loop = loop
    _exit_future = asyncio.futures.Future(loop=loop)

    loop.add_signal_handler(signal.SIGINT, trigger_exit_threadsafe)
    loop.add_signal_handler(signal.SIGTERM, trigger_exit_threadsafe)
