screeps-warreport
=================

Screeps WarReport is a small standalone server application which tracks all recent battles in
[screeps.com](https://screeps.com), and includes various data from room history.

WarReport is built as an independent python 3.4 app, using asyncio for threading and redis as a backend database cache.
It's a design goal of WarReport to store all needed data in redis, so that if the application is shut down for any small
period of time, it will be able to immediately resume service and process any backlog which has accumulated when it's
put back online.

Any and all contributions welcome!

To run, simply install the required depeendencies with `pip install -r requirements.txt`, and then run 
`python -m warreport` in the project directory!

To stop, simply kill the process with Ctrl+C. This isn't too gracefully handled right now, but since no needed data is
stored in process memory and race conditions are avoided as much as possible, killing the application should have little
to no affect on the service.

To add custom configurations, copy `config.default.json` to `config.json` and edit.
