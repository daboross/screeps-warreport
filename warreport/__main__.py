import asyncio
import logging

import os

from warreport import battle_monitor, battle_reporting, sighandler, redis_conn

logger = logging.getLogger("warreport")


def main():
    logger.info("Starting main loop.")
    logger.debug("Debug logging enabled.")
    loop = asyncio.get_event_loop()
    sighandler.setup(loop)
    loop.run_until_complete(asyncio.gather(
        battle_monitor.grab_new_battles(loop),
        battle_monitor.process_battles(loop),
        battle_reporting.report_battles(loop),
    ))
    redis_conn.connection_pool.disconnect()
    # We've finished - this is now needed to force exit all running redis handler threads
    # sys.exit() doesn't seem to work - this seems to be the best solution at the moment.
    os._exit(0)


if __name__ == '__main__':
    main()
