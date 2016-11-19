"""
One major data format used here is a map of "battle data". The following defines all available forms:


{
    # The latest tick checked, so when starting check the next section after this
    # Included: in still-processing data
    # Added: after first successfully history collection
    # Updated: whenever we find a newer history
    'max_tick_checked': 1232230,

    # The first tick to check when starting (and do a back check from here if found, as this will be the first history
    # retrieved).
    # Included: in data which hasn't successfully collected any history
    # Added: when room is first submitted to processing queue.
    'tick_to_check': 1222222,

    # A list of players involved, and how many creeps have been counted so far.
    # Included: in all data.
    # Added: empty object added after first history collection.
    # Updated: during every history collection
    'player_creep_counts': {
        'name1': {
            # 10 type a creeps
            'creep_type_a': 10,
            # 20 type b creeps
            'creep_type_b': 20,
            # ...
        },
        'name2': {
            # ...
        },
        # ...
    },

    # A list of creep IDs which we have already added to the creeps map
    # Included: in non-finished data
    # Added: empty list after first history collection.
    'creeps_found': [
        '582f8e657a1fc8bf5cd28be5',
        '582f8116e8c62a5d2e464ad2',
        # ...
    ],

    # The room's owner / reserver, or null if unowned and unreserved.
    # Included: in all data.
    # Added: after first successful history collection.
    owner: 'screepsuser',

    # The room's rcl, or 0 if reserved or completely unowned.
    # Included: in all data.
    # Added: after first successful history collection.
    rcl: 3,

    # The earliest tick we've found hostilities for.
    # Included: in all data.
    # Added: after first successful history collection.
    'earliest_hostilities_detected': 12232322,

    # If true, this is a confirmed continuation of the last reported battle in this room.
    # Included: in all data.
    # Added: after first successful history collection (given that after first successful history collection, we
    #     backtrace history until either we've reached the last reported tick for the room, or there are no hostilities,
    #     or we reach the end of history).
    'earliest_hostilities_collided': false,

    # This is the latest hostile action we've found.
    # Included: in all data
    # Added: after first successful history collection
    # Updated: every history gathering
    'latest_hostilities_detected': 12232323,

    # This is `latest_hostilties_detected - earliest_hostilities_detected`
    # Included: in final data
    # Added: when data collection is complete
    'duration': 23,

    # If we're still finding hostilities at this tick, just report the battle now and assume we'll re-add it to the
    # reporting queue.
    # Included: in data which isn't complete
    # Added: when room is first submitted to processing queue.
    'stop_checking_at': 1224222,

    # If true, data collection stopped because we reached a tick limit, and hostilities were still happening during the
    # last history segment we retrieved.
    # Included: in complete data
    # Added: when data collection is complete
    'battle_still_ongoing': false,


    # A list of players involved, and what their alliances are. Players without alliances are still listed, but with
    # null values.
    # Included: in complete data
    # Added: when data collection is complete
    'alliances': {
        'name1': 'north-eastern nation',
        'name2': 'HEYA town',
        'name3': null,
    },

    # The room the hostilities occurred in - only added for reporting (otherwise it's already stored as the key which
    # is used to retrieve this data).
    # Included: in complete data
    # Added: when data collection is complete
    'room': 'E15N53',
}

The following are smaller defined formats in which the battle info may appear:

No data processed yet, just freshly found:


{
    # The first tick to check when starting (and do a back check from here if found, as this will be the first history
    # retrieved).
    'tick_to_check': 1222222,

    # If we're still finding hostilities at this tick, just report the battle now and assume we'll re-add it to the
    # reporting queue.
    'stop_checking_at': 1224222,
}

Initial starting history segment found, and past history segments searched, but still missing some future history:

{
    # The latest tick checked, so when starting check the next section after this
    'max_tick_checked': 1232230,

    # A list of players involved, and how many creeps have been counted so far.
    'player_creep_counts': {
        'name1': {
            # 10 type a creeps
            'creep_type_a': 10,
            # 20 type b creeps
            'creep_type_b': 20,
            # ...
        },
        'name2': {
            # ...
        },
        # ...
    },

    # A list of creep IDs which we have already added to the creeps map
    'creeps_found': [
        '582f8e657a1fc8bf5cd28be5',
        '582f8116e8c62a5d2e464ad2',
        # ...
    ]

    # The room's owner / reserver, or null if unowned and unreserved.
    owner: 'screepsuser',

    # The room's rcl, or 0 if reserved or completely unowned.
    rcl: 3,

    # The earliest tick we've found hostilities for.
    'earliest_hostilities_detected': 12232322,

    # If true, this is a confirmed continuation of the last reported battle in this room.
    'earliest_hostilities_collided': false

    # This is the latest hostile action we've found.
    'latest_hostilities_detected': 12232323,

    # If we're still finding hostilities at this tick, just report the battle now and assume we'll re-add it to the
    # reporting queue.
    'stop_checking_at': 1224222,
}

Completed data in the reporting queue(s):

{
    # The room the hostilities occurred in - only added for reporting (otherwise it's already stored as the key which
    # is used to retrieve this data).
    'room': 'E15N53',

    # A list of players involved, and how many creeps have been counted so far.
    'player_creep_counts': {
        'name1': {
            # 10 type a creeps
            'creep_type_a': 10,
            # 20 type b creeps
            'creep_type_b': 20,
            # ...
        },
        'name2': {
            # ...
        },
        # ...
    },

    # A list of players involved, and what their alliances are. Players without alliances are still listed, but with
    # null values.
    'alliances': {
        'name1': 'north-eastern nation',
        'name2': 'HEYA town',
        'name3': null,
    },

    # The room's owner / reserver, or null if unowned and unreserved.
    owner: 'screepsuser',

    # The room's rcl, or 0 if reserved or completely unowned.
    rcl: 3,

    # The earliest tick we've found hostilities for.
    'earliest_hostilities_detected': 12232322,

    # If true, this is a confirmed continuation of the last reported battle in this room.
    'earliest_hostilities_collided': false,

    # This is the latest hostile action we've found.
    'latest_hostilities_detected': 12232323,

    # If true, data collection stopped because we reached a tick limit, and hostilities were still happening during the
    # last history segment we retrieved.
    'battle_still_ongoing': false,

    # This is `latest_hostilties_detected - earliest_hostilities_detected`
    duration: 23,
}
"""

from warreport.key_constants import USERNAME_CACHE_EXPIRE, USERNAME_CACHE_KEY, BATTLE_DATA_KEY, BATTLE_DATA_EXPIRE, \
    ALLIANCES_FETCHED_KEY, ALLIANCES_FETCHED_EXPIRE, ALLIANCE_CACHE_KEY, ALLIANCE_CACHE_EXPIRE

try:
    import rapidjson as json
except ImportError:
    import json

from warreport import redis_conn as cache_connection

__all__ = ["get_username", "set_username", "set_ongoing_data", "get_ongoing_data", "is_alliance_data_recent",
           "update_alliance_data", "get_cached_alliance"]


def get_username(user_id):
    key = USERNAME_CACHE_KEY.format(user_id)
    raw = cache_connection.get(key)
    if raw is None:
        return None
    else:
        return raw.decode()


def set_username(user_id, username):
    key = USERNAME_CACHE_KEY.format(user_id)
    cache_connection.set(key, username, ex=USERNAME_CACHE_EXPIRE)


# Just a note:
# With the following data methods, we assume a few things:
# 1. If tick 220 history is available, and tick 200 history is not available, tick 200 history will _never_ be
#    available.
# TODO: add more assumptions here.


def set_ongoing_data(room_name, data_map):
    """
    Sets the "currently process" data for a given room name.

    This stores the data map into redis as JSON.

    :param room_name: The room
    :param data_map: The data map, in the "battle data" format described in module docs.
    """
    key = BATTLE_DATA_KEY.format(room_name)
    cache_connection.set(key, json.dumps(data_map), ex=BATTLE_DATA_EXPIRE)


def get_ongoing_data(room_name):
    """
    Gets the "currently processing" data for a given room name, set with set_ongoing_data.
    :return: the data
    :rtype: dict[str, int | list[str] | dict[str, dict[str, str]]]
    """
    key = BATTLE_DATA_KEY.format(room_name)
    return json.loads(cache_connection.get(key).decode())


def is_alliance_data_recent():
    return cache_connection.exists(ALLIANCES_FETCHED_KEY)


def update_alliance_data(user_alliance_tuple_list):
    pipe = cache_connection.pipeline()
    pipe.set(ALLIANCES_FETCHED_KEY, 1, ex=ALLIANCES_FETCHED_EXPIRE)
    for user, alliance in user_alliance_tuple_list:
        pipe.set(ALLIANCE_CACHE_KEY.format(user), alliance, ex=ALLIANCE_CACHE_EXPIRE)
    pipe.execute()


def get_cached_alliance(username):
    """
    Note: be sure to check if is_alliance_data_recent() before using this, or you could get incorrect/old results.
    """
    key = ALLIANCE_CACHE_KEY.format(username)
    raw = cache_connection.get(key)
    if raw is None:
        return None
    else:
        return raw.decode()
