import asyncio
import logging

import os

from warreport import battle_monitor, battle_reporting

logger = logging.getLogger("warreport")


def main():
    logger.info("Starting main loop.")
    logger.debug("Debug logging enabled.")
    loop = asyncio.get_event_loop()
    gathered_future = asyncio.gather(
        battle_monitor.grab_new_battles(loop),
        battle_monitor.process_battles(loop),
        battle_reporting.report_battles(loop),
        loop=loop,
    )
    try:
        loop.run_until_complete(gathered_future)
    except KeyboardInterrupt:
        logger.info("Caught KeyboardInterrupt: Ending main loop.")
        gathered_future.cancel()
        loop.run_forever()
        gathered_future.exception()
    finally:
        loop.close()
    logger.info("Ended successfully.")
    # TODO: this is basically so I don't have to Ctrl+C twice to exit. I don't know what holds up the process, and it
    # would definitely be a good idea to find out!
    os._exit(0)


if __name__ == '__main__':
    main()
