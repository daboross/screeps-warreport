screeps-warreport
=================

Screeps WarReport is a small, incomplete app which tracks all recent battles in [screeps.com](https://screeps.com), and
includes various data from room history.

WarReport is built as an independent python 3.4 app, using asyncio for threading and redis as a backend database cache.
All stored data is stored in redis, for completely transparent restarts. Even with downtime, this application should
ideally still report all battles found since it's first run.

Note that this application is still very much in an alpha stage, and behavior and role is still in flux!

Any and all contributions welcome!

To run, simply install the requirement dependencies with `pip`, and run `python -m warreport` in the project directory!

For configuration of a different redis database, or other options, copy `config.default.json` to `config.json` and
modify.
