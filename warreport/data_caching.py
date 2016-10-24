from warreport import redis_conn as cache_connection

__all__ = ["get_username", "set_username", "get_player_counts", "set_player_counts", "get_battledata_not_yet_avail",
           "set_battledata_not_yet_avail"]

USERNAME_KEY = "screeps:warreport:username:{}"
USERNAME_EXPIRE = 60 * 60 * 5

PLAYER_COUNTS_KEY = "screeps:warreport:battledata:{}:{}"
PLAYER_COUNTS_EXPIRE = 60 * 60 * 24 * 3

NO_BATTLE_DATA_KEY = "screeps:warreport:battledata-not-avail:{}:{}"
NO_BATTLE_DATA_EXPIRE = 60

QUEUED_BATTLES_KEY = "screeps:warreport:unreported_battles"
CURRENTLY_PROCESSING_KEY = "screeps:warreport:current_battle"


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


def get_player_counts(room_name, start_tick):
    key = PLAYER_COUNTS_KEY.format(room_name, start_tick)
    # hgetall will return an empty dict for a hash which doesn't exist - we bypass this by adding a '_checked' field.
    raw = cache_connection.hgetall(key)
    if len(raw):
        return {k.decode(): v.decode() for k, v in raw.items() if k != '__$checked'}


def set_player_counts(room_name, start_tick, data_dict):
    if not len(data_dict):
        data_dict = {'__$checked': 1}  # redis doesn't allow empty hashes.
    key = PLAYER_COUNTS_KEY.format(room_name, start_tick)
    pipe = cache_connection.pipeline()
    pipe.hmset(key, data_dict)
    pipe.expire(key, PLAYER_COUNTS_EXPIRE)
    pipe.execute()


def get_battledata_not_yet_avail(room_name, start_tick):
    key = NO_BATTLE_DATA_KEY.format(room_name, start_tick)
    return cache_connection.get(key)


def set_battledata_not_yet_avail(room_name, start_tick):
    key = NO_BATTLE_DATA_KEY.format(room_name, start_tick)
    cache_connection.set(key, 1, ex=NO_BATTLE_DATA_EXPIRE)


def add_battle_to_queue(room_name, start_tick):
    cache_connection.rpush(QUEUED_BATTLES_KEY, "{}:{}".format(room_name, start_tick))


def add_battles_to_queue(battles_array):
    cache_connection.rpush(QUEUED_BATTLES_KEY, *("{}:{}".format(room_name, start_tick)
                                                 for room_name, start_tick in battles_array))


def get_next_battle_blocking():
    # TODO: this really does assume that we're only doing one at a time, and may produce duplicate messages if we have
    # multiple instances running!
    current = cache_connection.get(CURRENTLY_PROCESSING_KEY)
    if current:
        return current.decode().split(':')
    # blpop returns a (key, popped_value) tuple
    battle = cache_connection.blpop(QUEUED_BATTLES_KEY)[1]
    cache_connection.set(CURRENTLY_PROCESSING_KEY, battle)
    return battle.decode().split(':')


def finished_battle(room_name, start_tick):
    current = cache_connection.get(CURRENTLY_PROCESSING_KEY)
    if current.decode() == '{}:{}'.format(room_name, start_tick):
        cache_connection.delete(CURRENTLY_PROCESSING_KEY)
