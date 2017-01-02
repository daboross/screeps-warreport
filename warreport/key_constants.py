from warreport import DATABASE_PREFIX

_VERSION = "0.2"
PROCESSING_QUEUE = DATABASE_PREFIX + _VERSION + ":processing_queue"
PROCESSING_QUEUE_SET = DATABASE_PREFIX + _VERSION + ":processing_set"

REPORTING_QUEUE = DATABASE_PREFIX + _VERSION + ":reporting_queue"

USERNAME_CACHE_KEY = DATABASE_PREFIX + "cache:username:{}"
USERNAME_CACHE_EXPIRE = 60 * 60 * 5

ALLIANCE_CACHE_KEY = DATABASE_PREFIX + "cache:alliance:{}"
ALLIANCE_CACHE_EXPIRE = 60 * 60 * 5

ALLIANCES_FETCHED_KEY = DATABASE_PREFIX + "fetched-alliance-cache"
ALLIANCES_FETCHED_EXPIRE = 60 * 60 * 4

BATTLE_DATA_KEY = DATABASE_PREFIX + "ongoing-data:{}"
# if it's still in here for 3 days, something has gone wrong and we can just get rid of it.
BATTLE_DATA_EXPIRE = 60 * 60 * 24 * 3

ROOM_LAST_BATTLE_END_TICK_KEY = DATABASE_PREFIX + "last-finished-battle:{}"
ROOM_LAST_BATTLE_END_TICK_EXPIRE = 60 * 60 * 24 * 10

_LAST_CHECKED_TICK_KEY = DATABASE_PREFIX + "last-checked-tick"
_LAST_CHECKED_TICK_EXPIRE_SECONDS = 60 * 60

"""
NOTE: This max ticks is max _history ticks successfully retrieved after starting_.
"""
KEEP_IN_QUEUE_FOR_MAX_TICKS = 120

"""
This is the hard deadline where no more history collection will be attempted (if the current tick is this many ticks
after the last known hostilities (or the first hostilities if no history has been found), give up.)
"""
KEEP_IN_QUEUE_FOR_MAX_TICKS_UNSUCCESSFUL = 2000
