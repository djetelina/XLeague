#!/usr/bin/env python
"""
Copyright (c) 2016 iScrE4m@gmail.com

To use the code, you must contact the author directly and ask permission.
"""

import cyclone.httpclient
import cyclone.web

from .. import settings as s
from . import database as db


class MainHandler(cyclone.web.RequestHandler):
    def get(self):
        self.render("api_docs.html")


class RequestVouch(cyclone.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(RequestVouch, self).__init__(application, request, **kwargs)
        self.bot_factory = application.botfactory

    def msg(self, channel, msg):
        bot = self.bot_factory.getProtocolByName("XLeagueBot")  # TODO fuj
        bot.msg(channel, msg)

    def post(self):
        self.add_header("Access-Control-Allow-Origin", "*")
        name = self.get_argument("name")
        about = self.get_argument("about")
        done = db.vouchrequest(name, about)
        self.write(done)
        self.finish()
        msg = "New vouch request by {}".format(name)
        self.msg(s.channel, msg)


class VouchRequestsJson(cyclone.web.RequestHandler):
    def get(self):
        self.add_header("Access-Control-Allow-Origin", "*")
        self.add_header("Content-type", "application/json")
        result = db.jsonrequests()
        self.write(result)


class PlayersJson(cyclone.web.RequestHandler):
    def get(self):
        self.add_header("Access-Control-Allow-Origin", "*")
        self.add_header("Content-type", "application/json")
        result = db.jsonplayers()
        self.write(result)


class GamesJson(cyclone.web.RequestHandler):
    def get(self):
        self.add_header("Content-type", "application/json")
        self.add_header("Access-Control-Allow-Origin", "*")
        result = db.jsongames()
        self.write(result)


class VariablesJson(cyclone.web.RequestHandler):
        # TODO Adjust variables from queues (probably send dictionary with queues)
    def get(self):
        self.add_header("Content-type", "application/json")
        self.add_header("Access-Control-Allow-Origin", "*")


class PlayerJson(cyclone.web.RequestHandler):
    """
    On GET renders json of single player from argument after /
    """
    def get(self, player):
        self.add_header("Content-type", "application/json")
        self.add_header("Access-Control-Allow-Origin", "*")
        result = db.jsonplayer(player)
        if result is not None:
            self.write(result)
        else:
            self.write("No player named {} found".format(player))


class GameJson(cyclone.web.RequestHandler):
    """
    On GET renders json of single game from arguments after /
    """
    def get(self, number):
        self.add_header("Content-type", "application/json")
        self.add_header("Access-Control-Allow-Origin", "*")
        result = db.jsongame(number)
        if result is not None:
            self.write(result)
        else:
            self.write("No game with ID {} found".format(number))
