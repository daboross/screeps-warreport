import asyncio
import logging

from warreport import battle_monitor

logger = logging.getLogger("warreport")


def main():
    logger.info("Starting main loop.")
    logger.debug("Debug logging enabled.")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(
        battle_monitor.grab_new_battles(loop),
        battle_monitor.process_battles(loop),
    ))


if __name__ == '__main__':
    main()
