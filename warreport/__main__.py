import asyncio
import logging

import os

import warreport
from warreport import battle_monitor, battle_reporting

logger = logging.getLogger("warreport")


def main():
    logger.info("Starting main loop.")
    logger.debug("Debug logging enabled.")
    loop = asyncio.get_event_loop()
    gathered_future = asyncio.gather(
        battle_monitor.grab_new_battles(loop),
        battle_monitor.process_battles(loop),
        battle_reporting.process_and_requeue_reports(loop),
        loop=loop,
    )
    try:
        loop.run_until_complete(gathered_future)
    except KeyboardInterrupt:
        logger.info("Caught KeyboardInterrupt: Ending main loop.")
        gathered_future.cancel()
        loop.run_forever()
        gathered_future.exception()
    except Exception:
        logger.exception("Caught exception: Ending main loop.")
        loop.close()
        os._exit(1)
    finally:
        loop.close()
    logger.info("Ended successfully.")
    # OS exit here in order to forcefully kill off any outstanding threaded blocking redis requests.
    os._exit(0)


if __name__ == '__main__':
    main()
