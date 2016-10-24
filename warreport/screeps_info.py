import logging

import requests
from collections import Counter

from . import data_caching

USERNAME_URL_FORMAT = "https://screeps.com/api/user/find?id={user_id}"
HISTORY_URL_FORMAT = "https://screeps.com/room-history/{room}/{tick}.json"

logger = logging.getLogger("warreport")


class ScreepsError(Exception):
    def __init__(self, data):
        self.message = "Screeps API Error: {}".format(data)

    def __str__(self):
        return self.message


def username_from_id(user_id):
    cached = data_caching.get_username(user_id)
    if cached is not None:
        return cached
    call_result = requests.get(USERNAME_URL_FORMAT.format(user_id=user_id))
    if call_result.ok:
        name = call_result.json().get('user', {}).get('username', None)
        if name is None:
            raise ScreepsError("{} (at api/user/find?id={})".format(call_result.content, user_id))
        data_caching.set_username(user_id, name)
        return name
    else:
        raise ScreepsError("{} (at api/user/find?id={})".format(call_result.content, user_id))


def get_battledata(room_name, center_tick):
    center_tick = int(center_tick)
    if center_tick % 60 < 20:
        # start_tick is 60-79 earlier
        start_tick = center_tick - center_tick % 60 - 60
        # end_tick is 161-180 after
    else:
        # start_tick is 20-59 earlier
        start_tick = center_tick - center_tick % 60
        # end_tick is 181-220 after
    end_tick = start_tick + 240

    cached_player_counts = data_caching.get_player_counts(room_name, start_tick)
    if cached_player_counts is not None:
        return {"player_counts": cached_player_counts}
    if data_caching.get_battledata_not_yet_avail(room_name, start_tick):
        return None

    creeps_found = set()
    player_to_bodycounts = Counter()
    for tick_to_call in range(start_tick, end_tick, 20):
        result = requests.get(HISTORY_URL_FORMAT.format(room=room_name, tick=tick_to_call))
        if result.status_code == 404:
            data_caching.set_battledata_not_yet_avail(room_name, start_tick)
            return None
        elif result.status_code != 200:
            logger.warning("Non-404 error accessing battle data! Error: {} ({}), url: {}"
                            .format(result.content, result.status_code, result.url))
            data_caching.set_battledata_not_yet_avail(room_name, start_tick)
            return None
        json_root = result.json()
        for tick_data in json_root['ticks'].values():
            for creep_id, obj_data in tick_data.items():
                # type is only set for new creeps, but we don't really care about updates to old creeps yet because
                # we're just counting raw bodyparts.
                if not obj_data:
                    continue
                if obj_data.get('type') == 'creep' and creep_id not in creeps_found:
                    creeps_found.add(creep_id)
                    owner = obj_data['user']
                    player_to_bodycounts[owner] += len(obj_data['body'])  # super boring atm
    try:
        player_counts = {username_from_id(user_id): count for user_id, count in player_to_bodycounts.items()}
    except ScreepsError as e:
        logger.warning("Couldn't find username(s)! Error: {}, player_counts: {}".format(e, player_to_bodycounts))
        data_caching.set_battledata_not_yet_avail(room_name, start_tick)
        return None
    data_caching.set_player_counts(room_name, start_tick, player_counts)
    return {"player_counts": player_counts}
