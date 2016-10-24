import logging

import requests
from collections import Counter
from collections import defaultdict

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
            raise ScreepsError("{} ({}, at {})".format(call_result.text, call_result.status_code, call_result.url))
        data_caching.set_username(user_id, name)
        return name
    else:
        raise ScreepsError("{} ({}, at {})".format(call_result.text, call_result.status_code,
                                                   call_result.url))


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

    cached_battle_data = data_caching.get_battle_data(room_name, start_tick)
    if cached_battle_data is not None:
        return cached_battle_data
    if data_caching.get_battledata_not_yet_avail(room_name, start_tick):
        return None

    first_hostilities_tick = None

    creeps_found = set()
    player_to_bodycounts = defaultdict(Counter)
    for tick_to_call in range(start_tick, end_tick, 20):
        result = requests.get(HISTORY_URL_FORMAT.format(room=room_name, tick=tick_to_call))
        if result.status_code == 404:
            logger.debug("Checked data for room {} tick {}: not generated yet (404).".format(room_name, tick_to_call))
            data_caching.set_battledata_not_yet_avail(room_name, start_tick)
            return None
        elif result.status_code != 200:
            logger.warning("Non-404 error accessing battle data! Error: {} ({}), url: {}"
                           .format(result.text, result.status_code, result.url))
            data_caching.set_battledata_not_yet_avail(room_name, start_tick)
            return None
        json_root = result.json()
        for tick, tick_data in json_root['ticks'].items():
            for creep_id, obj_data in tick_data.items():
                # type is only set for new creeps, but we don't really care about updates to old creeps yet because
                # we're just counting raw bodyparts.
                if not obj_data:
                    continue
                if obj_data.get('type') == 'creep' and creep_id not in creeps_found:
                    creeps_found.add(creep_id)
                    owner = obj_data['user']
                    # I've seen user_id 2 and 3 both somewhere, not sure what it represents but I think it's either
                    # source keepers or invaders. I'm assuming there's a '1' too, since '2' exists... Anyways, can't
                    # hurt to add an exception here, since neither one is a valid regular user ID.
                    # NOTE: user_id 2 is confirmed to be invader. I don't know what user_id 3 is.
                    if owner.isdigit() and int(owner) < 10:
                        continue
                    counter = player_to_bodycounts[owner]
                    for part in obj_data['body']:
                        counter[part['type']] += 1
                action_log = obj_data.get('action_log')
                if action_log and (action_log.get('attack') or action_log.get('rangedAttack') or action_log.get('heal')
                                   or action_log.get('rangedMassAttack')):
                    if first_hostilities_tick is None or tick < first_hostilities_tick:
                        first_hostilities_tick = tick

    try:
        player_counts = {username_from_id(user_id): data for user_id, data in player_to_bodycounts.items()}
    except ScreepsError as e:
        logger.warning("Couldn't find username(s)! Error: {}, player_counts: {}".format(e, player_to_bodycounts))
        data_caching.set_battledata_not_yet_avail(room_name, start_tick)
        return None
    battle_data = {
        "room": room_name,
        "hostilities_tick": first_hostilities_tick or center_tick,
        "player_counts": player_counts,
    }
    data_caching.set_battle_data(room_name, start_tick, battle_data)
    return battle_data
