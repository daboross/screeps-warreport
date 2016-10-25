import json
import logging.config

import os
import redis

SLACK_URL = None
redis_conn = None


def _setup_logging(logging_config):
    logging_dir = os.path.join(os.path.abspath(os.path.curdir), logging_config.get('directory', 'logs'))

    if not os.path.exists(logging_dir):
        os.makedirs(logging_dir)

    dict_config = {
        "version": 1,
        "formatters": {
            "brief": {
                "format": "[%(asctime)s][%(levelname)s] %(message)s",
                "datefmt": "%H:%M:%S"
            },
            "full": {
                "format": "[%(asctime)s][%(levelname)s] %(message)s",
                "datefmt": "%Y-%m-%d][%H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "brief",
                "level": "INFO",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "full",
                "level": "INFO",
                "filename": os.path.join(logging_dir, "app.log")
            }
        },
        "loggers": {
            "warreport": {
                "level": "DEBUG",
                "handlers": ["console", "file"]
            }
        }
    }

    if logging_config.get("console_debug", False):
        dict_config["handlers"]["console"]["level"] = "DEBUG"

    if logging_config.get("file_debug", False):
        dict_config["handlers"]["debug_file"] = {
            "class": "logging.FileHandler",
            "formatter": "full",
            "level": "DEBUG",
            "filename": os.path.join(logging_dir, "debug.log")
        }
        dict_config["loggers"]["warreport"]["handlers"].append("debug_file")

    logging.config.dictConfig(dict_config)


def _set_database(database_config):
    global redis_conn
    host = database_config.get('host', 'localhost')
    port = database_config.get('port', 6379)
    database = database_config.get('database', 0)

    redis_conn = redis.StrictRedis(host=host, port=port, db=database)
    logging.getLogger("warreport").info("Database connected successfully.")


# TODO: maybe we want to be more OOP and have specific instances of the application instead of one per python instance?
def _setup():
    default_database_config = {
        "host": "localhost",
        "port": 6379,
        "database": 0,
        "prefix": "screeps:warreport:"
    }
    default_logging_config = {
        "directory": "logs",
        "console_debug": False,
        "file_debug": False,
    }
    if os.path.exists(os.path.abspath("config.json")):
        with open(os.path.abspath("config.json")) as config_file:
            json_conf = json.load(config_file)
        database_config = json_conf.get("database", default_database_config)
        logging_config = json_conf.get("logging", default_logging_config)
    else:
        json_conf = {}
        database_config = default_database_config
        logging_config = default_logging_config

    _setup_logging(logging_config)
    _set_database(database_config)

    global SLACK_URL
    SLACK_URL = json_conf.get('slack_url', None)
    # This can stand in as a good default that we should NOT try and use.
    if SLACK_URL == "https://hooks.slack.com/services/XXX/YYY/ZZZ":
        SLACK_URL = None


_setup()

from . import data_caching, screeps_info, battle_monitor, battle_reporting
