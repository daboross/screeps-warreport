import asyncio

from warreport import battle_monitor


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(
        battle_monitor.grab_new_battles(loop),
        battle_monitor.process_battles(loop),
    ))

if __name__ == '__main__':
    main()
