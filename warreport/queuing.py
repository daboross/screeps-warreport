import json

from warreport import DATABASE_PREFIX, redis_conn

_VERSION = "0.1"
PROCESSING_QUEUE = DATABASE_PREFIX + _VERSION + ":processing_queue"

REPORTING_QUEUE = DATABASE_PREFIX + _VERSION + ":reporting_queue"


def push_battles_for_processing(battles_array):
    """
    Pushes a number of battles into the processing queue.
    :param battles_array: A list of (room_name, hostilities_tick) tuples
    """
    redis_conn.lpush(PROCESSING_QUEUE, *("{}:{}".format(room_name, start_tick)
                                         for room_name, start_tick in battles_array))


def get_next_battle_to_process():
    """
    Gets a single battle to process. This method returns the battle's room, the last known hostilities tick, and a
    database key for use when re-submitting processed data.
    :return: A tuple of (room_name, start_tick, database_key)
    """
    # TODO: This implementation currently allows for the possibility of processing the same data twice when we have at
    # least two clients, and a queue shorter than the number of clients. On one hand, this should be changed. On the
    # other, we really only support one client at a time, and this allows us to not require a separate
    # "currently_processing" queue to monitor.
    raw_battle = redis_conn.brpoplpush(PROCESSING_QUEUE, PROCESSING_QUEUE)
    room_name, start_tick = raw_battle.decode().split(':')
    return room_name, start_tick, raw_battle


def submit_processed_battle(database_key, battle_info_dict):
    """
    Submit a processed battle via a database_key and battle_info_dict.
    :param database_key: The database_key corresponding to the battle processed (retrieved from
                         get_next_battle_to_process())
    :param battle_info_dict: The processed data.
    """
    pipe = redis_conn.pipeline()
    pipe.lrem(PROCESSING_QUEUE, -1, database_key)
    pipe.lpush(REPORTING_QUEUE, json.dumps(battle_info_dict))
    pipe.execute()


def get_next_battle_to_report():
    """
    Gets a single battle to report. This method returns the processed information dict, and a database_key for use when
    marking as completed.

    TODO: describe in detail the battle_info_dict format here.

    :return: A tuple of (battle_info_dict, database_key)
    """
    # TODO: This implementation currently allows for the possibility of processing the same data twice when we have at
    # least two clients, and a queue shorter than the number of clients. On one hand, this should be changed. On the
    # other, we really only support one client at a time, and this allows us to not require a separate
    # "currently_processing" queue to monitor.
    raw_battle_info = redis_conn.brpoplpush(REPORTING_QUEUE, REPORTING_QUEUE)
    battle_info = json.loads(raw_battle_info.decode())
    return battle_info, raw_battle_info


def mark_battle_reported(database_key):
    """
    Marks a battle from the reporting queue as reported, given a database_key retrieved from get_next_battle_to_report.

    If this method isn't called, get_next_battle_to_report will start returning already-reported battles once it has
    returned each battle once.
    :param database_key: The database_key returned from get_next_battle_to_report corresponding to the battle
                         successfully reported.
    """
    redis_conn.lrem(REPORTING_QUEUE, -1, database_key)
