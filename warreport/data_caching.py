import json

from warreport import redis_conn as cache_connection, DATABASE_PREFIX

__all__ = ["get_username", "set_username", "get_battle_data", "set_battle_data", "get_battle_data_not_yet_avail",
           "set_battle_data_not_yet_avail"]

USERNAME_KEY = DATABASE_PREFIX + "cache:username:{}"
USERNAME_EXPIRE = 60 * 60 * 5

BATTLE_DATA_KEY = DATABASE_PREFIX + "cache:battle-data:{}:{}"
BATTLE_DATA_EXPIRE = 60 * 60 * 24 * 3

NO_BATTLE_DATA_KEY = DATABASE_PREFIX + "cache:battle-data-not-avail:{}:{}"
NO_BATTLE_DATA_EXPIRE = 60


def get_username(user_id):
    key = USERNAME_KEY.format(user_id)
    raw = cache_connection.get(key)
    if raw is None:
        return None
    else:
        return raw.decode()


def set_username(user_id, username):
    key = USERNAME_KEY.format(user_id)
    cache_connection.set(key, username, ex=USERNAME_EXPIRE)


def get_battle_data(room_name, start_tick):
    key = BATTLE_DATA_KEY.format(room_name, start_tick)
    # hgetall will return an empty dict for a hash which doesn't exist - we bypass this by adding a '_checked' field.
    raw = cache_connection.get(key)
    if raw:
        return json.loads(raw.decode())
    else:
        return None


def set_battle_data(room_name, start_tick, data_dict):
    key = BATTLE_DATA_KEY.format(room_name, start_tick)
    cache_connection.set(key, json.dumps(data_dict))


def get_battle_data_not_yet_avail(room_name, start_tick):
    key = NO_BATTLE_DATA_KEY.format(room_name, start_tick)
    return cache_connection.get(key)


def set_battle_data_not_yet_avail(room_name, start_tick):
    key = NO_BATTLE_DATA_KEY.format(room_name, start_tick)
    cache_connection.set(key, 1, ex=NO_BATTLE_DATA_EXPIRE)
