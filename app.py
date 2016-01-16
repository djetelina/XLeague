#!/usr/bin/env python
"""
Copyright (c) 2016 iScrE4m@gmail.com

To use the code, you must contact the author directly and ask permission.

This is being slowly split into smaller files, the main logic will be edited
after everything is done
"""

from __future__ import division

import json
import os
import random
import re
import string
import sys
import time
from collections import deque

import cyclone.httpclient
import cyclone.web
from twisted.internet import reactor, protocol, defer
from twisted.internet.defer import Deferred
from twisted.web.client import getPage
from twisted.words.protocols import irc

import core.rating as ELO
import core.database as db
import settings as s

InQueue = len(QueuedPlayers)
GameOpen = 0
GameType = ""
NeededToStart = 8
QueuedPlayers = []
PodGames = {2: 1, 4: 6, 8: 12}
runninggames = []


class Application(cyclone.web.Application):
    def __init__(self, botfactory):
        handlers = [
            (r"/", MainHandler),
            (r"/reqvouch", requestvouch),
            (r"/requests", requestjson),
            (r"/players", playersjson),
            (r"/games", gamesjson),
            (r"/variables", variablesjson),
            (r"/player/(.+)", playerjson),
            (r"/game/(.+)", gamejson),
        ]

        settings = dict(xheaders=False,
                        static_path="./static",
                        template_path="./templates", )

        self.botfactory = botfactory

        cyclone.web.Application.__init__(self, handlers, **settings)


class MainHandler(cyclone.web.RequestHandler):
    def get(self):
        self.render("api_docs.html")


class requestvouch(cyclone.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(requestvouch, self).__init__(application, request, **kwargs)
        self.botfactory = application.botfactory

    def msg(self, channel, msg):
        bot = self.botfactory.getProtocolByName("XLeagueBot")  # TODO fuj
        sendmsg(bot, channel, msg)

    def post(self):
        self.add_header("Access-Control-Allow-Origin", "*")
        name = self.get_argument("name")
        about = self.get_argument("about")
        done = db.vouchrequest(name, about)
        self.write(done)
        self.finish()
        msg = "New vouch request by {}".format(name)
        self.msg(s.channel, msg)  # TODO fuj


class requestjson(cyclone.web.RequestHandler):
    def get(self):
        self.add_header("Access-Control-Allow-Origin", "*")
        self.add_header("Content-type", "application/json")
        result = db.jsonrequests()
        self.write(result)


class playersjson(cyclone.web.RequestHandler):
    def get(self):
        self.add_header("Access-Control-Allow-Origin", "*")
        self.add_header("Content-type", "application/json")
        result = db.jsonplayers()
        self.write(result)


class gamesjson(cyclone.web.RequestHandler):
    def get(self):
        self.add_header("Content-type", "application/json")
        self.add_header("Access-Control-Allow-Origin", "*")
        result = db.jsongames()
        self.write(result)


class variablesjson(cyclone.web.RequestHandler):
    def get(self):
        self.add_header("Content-type", "application/json")
        self.add_header("Access-Control-Allow-Origin", "*")
        global QueuedPlayers
        global NeededToStart
        global GameType
        global GameOpen
        global runninggames
        result = {"variables": [{"InQueue": len(QueuedPlayers),
                                 "QueuedPlayers": ", ".join(QueuedPlayers),
                                 "NeededToStart": NeededToStart,
                                 "GameType": GameType,
                                 "GameOpen": GameOpen,
                                 "RunningGames": ", ".join(runninggames)}]}
        towrite = json.dumps(result)
        self.write(towrite)


class playerjson(cyclone.web.RequestHandler):
    def get(self, player):
        self.add_header("Content-type", "application/json")
        self.add_header("Access-Control-Allow-Origin", "*")
        result = db.jsonplayer(player)
        self.write(result)


class gamejson(cyclone.web.RequestHandler):
    def get(self, number):
        self.add_header("Content-type", "application/json")
        self.add_header("Access-Control-Allow-Origin", "*")
        result = db.jsongame(number)
        self.write(result)


class NoAccount(Exception):
    "No account found."


class XLeagueBot(irc.IRCClient):
    nickname = s.nickname

    def __init__(self):
        self._whoisQueue = deque()

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.factory.registerProtocol(self)

    def connectionLost(self, reason):
        self.factory.unregisterProtocol(self)
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        self.join(self.factory.channel)

    def joined(self, channel):
        status = "Joined {}".format(channel)
        log(status)
        auth(self)

    def noticed(self, user, channel, msg):
        status = "Notice from {}: {}".format(user, msg)
        log(status)

    def msg(self, user, message, length=None):
        irc.IRCClient.msg(self, user, message, length)

    @defer.inlineCallbacks
    def privmsg(self, user, channel, msg):
        global QueuedPlayers
        global NeededToStart
        global GameType
        global PodGames
        global GameOpen
        global runninggames

        user = user.split('!', 1)[0]
        status = "{} in {}: {}".format(user, channel, msg)
        log(status)

        if channel == self.nickname:
            ignore = ['ChanServ', 'AuthServ', 'iScrE4m']
            if user == 'iScrE4m':
                command = msg.split()
                channel = command[0]
                msg = " ".join(command[1:])
                sendmsg(self, channel, msg)
            elif user not in ignore:
                msg = "Please use {} for commands.".format(s.channel)
                channel = user
                sendmsg(self, channel, msg)

        if msg.startswith(".join"):
            authed = yield self.deferredwhois(user)
            player = db.getplayer(authed)
            games = db.getrunning()
            if player is not None:
                if player['Name'] not in QueuedPlayers and player[
                        'Name'] not in games and GameOpen == 1:
                    addtoqueue(authed)
                    if len(QueuedPlayers) == NeededToStart:
                        msg = startpod(self)
                    else:
                        players_left = NeededToStart - len(QueuedPlayers)
                        msg = "{} to start {}. Type .join to join".format(
                            players_left, GameType)

                elif GameOpen == 0:
                    msg = "No games open. Ask a Judge to open a game for you."
                else:
                    msg = "You are already in a queue"
            else:
                msg = "You are not vouched"
            sendmsg(self, channel, msg)

        if msg.startswith(".leave"):
            authed = yield self.deferredwhois(user)
            if authed in QueuedPlayers:
                removefromqueue(authed)
                msg = "{} left the queue".format(authed)
            else:
                msg = "You can't leave if you didn't join, silly"
            sendmsg(self, channel, msg)

        if msg.startswith(".players"):
            if GameOpen == 1:
                players = ", ".join(map(str, QueuedPlayers))
                msg = "{} out of {} in queue for {}: {}".format(
                    len(QueuedPlayers), NeededToStart, GameType, players)
            else:
                msg = "No games open. Ask a Judge to open a game for you."
            sendmsg(self, channel, msg)

        if msg.startswith(".player "):
            player = msg.split()
            player = player[1]
            try:
                stats = db.getplayer(player)
                try:
                    wlr = str(int(stats['W'] / stats['Played'] * 100)) + "%"
                except ZeroDivisionError:
                    wlr = "N/A"
                msg = "\n".join([
                    "Stats for {} - Rating: {} - Games Played: {}",
                    " - Wins: {} - Losses: {} - WLR: {}"
                ]).format(stats['Name'], stats['ELO'], stats['Played'],
                          stats['W'], stats['L'], wlr)
            except TypeError:
                msg = "No player named '{}' found".format(player)
            sendmsg(self, channel, msg)

        if msg.startswith(".card"):
            card = msg.split(" ", 1)[1]
            fetchcarddatabyname(self, channel, card)

        if msg.startswith(".games"):
            running = db.getrunning()
            if not running:
                msg = "No games are in progress."
            else:
                games = " | ".join(["#{}".format(str(row[0])) for row in
                                    running])
                msg = "Games in progress | {}".format(games)
            sendmsg(self, channel, msg)

        if msg.startswith(".info"):
            id = msg.split()
            id = int(id[1])
            game = db.getgameid(id)
            if game is not None:
                players = ", ".join([game['Player {}'.format(ix)]
                                     for ix in range(1, 9)])
                msg = "\n".join([
                    "Game #{} - Running: {} - Type: {}",
                    " - Pod size: {} - Games Played: {} - Players: {}"
                ]).join(game['ID'], game['Running'], game['GameType'],
                        game['Pod'], game['GamesPlayed'], players)
                msg = msg.replace(", None", "")
            else:
                msg = "There is no game with ID {}".format(id)
            sendmsg(self, channel, msg)

        if msg.startswith(".help"):
            channel = user
            authed = yield self.deferredwhois(user)
            msg = "\n".join([
                "My commands:", ".join ~~~ Joins queue for an open game",
                ".leave ~~~ Leaves Queue you were in",
                ".players ~~~ Lists players queued for an open game",
                ".player <nick> ~~~ Gets stats of player",
                ".games ~~~ Lists IDs of running games",
                ".info <GameID> ~~~ Gets info about game",
                ".card <CardName> ~~~ Gets details of a card"
            ])
            judge = db.getplayer(authed)
            if judge['Judge'] == 1:
                msg += "\n".join([
                    "", "===== JUDGE COMMANDS =====",
                    ".confirm_vouch_req <nick> ~~~ Vouches player (or .deny_vouch_req)",
                    ".open <GameType> <Players> ~~~ Opens a draft/sealed for" +
                    " number of players",
                    ".close <GameID> ~~~ Closes game (Used for games in" +
                    " database, NOT for queues)",
                    ".result <GameID> <Winner> <WinnerScore> <LoserScore>" +
                    " <Loser> ~~~ Reports a result for GameID.",
                    ".updateleader ~~~ Updates leaderboard on the website"
                ])
            sendmsg(self, channel, msg)

        # Judge commands

        if msg.startswith(".confirm_vouch_req"):
            authed = yield self.deferredwhois(user)
            judge = db.getplayer(authed)
            if judge['Judge'] == 1:
                vouched = msg.split()
                vouched = vouched[1]
                msg = db.confirm_vouch_req(vouched)
            else:
                msg = "You don't have sufficient permissions to vouch anybody"
            sendmsg(self, channel, msg)

        if msg.startswith(".deny_vouch_req"):
            authed = yield self.deferredwhois(user)
            judge = db.getplayer(authed)
            if judge['Judge'] == 1:
                vouched = msg.split()
                vouched = vouched[1]
                msg = db.deny_vouch_req(vouched)
            else:
                msg = " ".join([
                    "You don't have sufficient permissions",
                    "to deny a vouch requests"
                ])
            sendmsg(self, channel, msg)

        if msg.startswith(".open"):
            authed = yield self.deferredwhois(user)
            judge = db.getplayer(authed)
            if judge['Judge'] == 1:
                msg = msg.split()
                GameOpen = 1
                GameType = msg[1]
                NeededToStart = int(msg[2])
                QueuedPlayers = []
                msg = ("{} for {} players is now open." +
                       " Type .join to join").format(GameType, NeededToStart)
            else:
                msg = "You don't have sufficient permissions to open new game."
            sendmsg(self, channel, msg)

        if msg.startswith(".close"):
            authed = yield self.deferredwhois(user)
            judge = db.getplayer(authed)
            if judge['Judge'] == 1:
                msg = msg.split()
                id = int(msg[1])
                db.closegame(id)
                runninggames.remove(str(id))
                msg = "Game closed."
            else:
                msg = "You don't have sufficient permissions to clos games."
            sendmsg(self, channel, msg)

        if msg.startswith(".result"):
            authed = yield self.deferredwhois(user)
            judge = db.getplayer(authed)
            if judge['Judge'] == 1:
                result = msg.split()
                id = int(result[1])

                winner = result[2]
                winnerdict = db.getplayer(winner)
                playedw = winnerdict['Played'] + 1
                ww = winnerdict['W'] + 1
                lw = winnerdict['L']

                loser = result[5]
                loserdict = db.getplayer(loser)
                playedl = loserdict['Played'] + 1
                wl = loserdict['W']
                ll = loserdict['L'] + 1

                winnerelo = ELO.newelo("W", winnerdict, loserdict)
                loserelo = ELO.newelo("L", winnerdict, loserdict)
                changewinner = winnerelo - winnerdict['ELO']
                changeloser = loserelo - loserdict['ELO']

                msg = "New Ratings: {} {} [+{}] {} {} [{}]".format(
                    winner, winnerelo, changewinner, loser, loserelo,
                    changeloser)

                db.rating_change(winner, winnerelo, playedw, ww, lw)
                db.rating_change(loser, loserelo, playedl, wl, ll)

                game = db.getgameid(id)
                played = game['GamesPlayed'] + 1
                db.gamenewplayed(played, id)
                if played == PodGames[game['Pod']]:
                    db.closegame(id)
                    runninggames.remove(str(id))
                    msg += "\nGame #{} ended.".format(id)
            else:
                msg = " ".join([
                    "You don't have sufficient permissions to report results.",
                    "Ask a judge to report them for you."
                ])
            sendmsg(self, channel, msg)

        # Admin commands

        if msg.startswith(".promote"):
            authed = yield self.deferredwhois(user)
            admins = ['iScrE4m']
            if authed in admins:
                judge = msg.split()
                judge = judge[1]
                db.makejudge(judge)
                giveop(self, judge)
                msg = "{} is now Judge".format(judge)
            else:
                msg = "Only admin can promote players."
            sendmsg(self, channel, msg)

    def userLeft(self, user, channel):
        global QueuedPlayers
        user = user.split('!', 1)[0]
        if user in QueuedPlayers:
            removefromqueue(user)

    def clientmsg(self, channel, message):
        reactor.callFromThread(self.msg, channel, message)

    def irc_330(self, prefix, params):
        self._currentActiveNick = params[2]

    def irc_RPL_ENDOFWHOIS(self, prefix, params):
        deferredToFire, who = self._whoisQueue.popleft()
        currentActiveNick = self._currentActiveNick
        self._currentActiveNick = None

        if currentActiveNick is None:
            deferredToFire.errback(NoAccount(who))
        else:
            deferredToFire.callback(currentActiveNick)

    def deferredwhois(self, nick):
        result = Deferred()
        self._whoisQueue.append((result, nick))
        self.whois(nick)
        return result


class XLeagueBotFactory(protocol.ClientFactory):
    protocol = XLeagueBot

    def __init__(self):
        self.channel = s.channel
        self.protocols = {}

    def getProtocolByName(self, name):
        return self.protocols.get(name)

    def registerProtocol(self, protocol):
        self.protocols[protocol.nickname] = protocol

    def unregisterProtocol(self, protocol):
        del self.protocols[protocol.nickname]

    def clientConnectionLost(self, connector, reason):
        connector.connect()

    # noinspection PyUnresolvedReferences
    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


def errorhandler(error):
    log(str(error))


def auth(self):
    msg = "auth {} {}".format(s.auth_name, s.auth_pw)
    self.msg('AuthServ@Services.GameSurge.net', msg)


def giveop(self, user):
    msg = "addop {} {}".format(s.channel, user)
    self.msg('ChanServ', msg)


def log(status):
    timestamp = time.strftime("%H:%M:%S", time.localtime(time.time()))
    status = "[{}] ".format(timestamp + status)
    # Adds timestamp, prints and logs current status
    status = status.encode('utf-8', errors='replace')
    print status


def sendmsg(protocol, channel, msg):
    status = "Sending message to {}: {}".format(channel, msg)
    msg = msg.encode('UTF-8', 'replace')
    protocol.msg(channel, msg)
    log(status)


def addtoqueue(player):
    QueuedPlayers.append(player)


def removefromqueue(player):
    QueuedPlayers.remove(player)


# TODO port to separate file
def startpod(self):
    global GameOpen
    global GameType
    global QueuedPlayers
    global runninggames
    id = db.getgamenewid()
    # Creating list for new database entry
    # with new ID, is running and 0 games played, Pod, Type
    pod = [id, "Yes", 0, NeededToStart, GameType]
    # Generating password to send to players
    password = ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(7))
    # Send each player the password and add him to database
    for queued in QueuedPlayers:
        pod.append(queued)
        msg = "Your {} has started. Password: '{}'".format(GameType, password)
        queued = queued.encode('UTF-8', 'replace')
        sendmsg(self, queued, msg)
    # If pod has fewer than 8 people,
    # this will make sure we give enough data to the database
    while len(pod) < 13:
        pod.append("None")
    db.creategame(pod)
    runninggames.append(str(id))
    msg = "Game #{} - {} is starting".format(id, GameType)
    # Close queuing
    GameOpen = 0
    GameType = 0
    QueuedPlayers = []
    return msg

# .card deferred processing - I hate deferred. So much.


def stripcurlybraces(s):
    return re.sub("[{}]", "", s)


def fetchcarddatabyname(self, channel, name):
    apiurl = "http://api.deckbrew.com/mtg/cards/" + re.sub(
        "[\'\",]", "", re.sub(" ", "-", name.lower()))
    card = getPage(apiurl)
    card.addCallback(cardcallback(self, channel))
    card.addErrback(errorhandler)

# Returning a function with only one input
# allows us to get more variables from callback
# which we need to succesfully send a msg after the fetching is done


def cardcallback(self, channel):
    def callprocess(data):
        cardprocess(self, channel, data)

    return callprocess


def cardprocess(self, channel, data):
    c = json.loads(data)
    name = c["name"]
    if "supertypes" in c:
        supertypes = " ".join(c["supertypes"]) + " - "
    else:
        supertypes = ""
    types = " ".join(c["types"])
    if "subtypes" in c:
        subtypes = " - " + " ".join(c["subtypes"])
    else:
        subtypes = ""
    if len(c["cost"]) > 0:
        cost = "(" + stripcurlybraces(c["cost"]) + ") "
    else:
        cost = ""
    text = re.sub("\n", " ", stripcurlybraces(c["text"]))
    if "power" in c:
        power = " [" + c["power"] + "/" + c["toughness"] + "]"
    else:
        power = ""
    msg = "{} [{}{}{}] {}\n{}{}".format(name, supertypes, types, subtypes,
                                        cost, text, power)
    sendmsg(self, channel, msg)


if __name__ == "__main__":
    reload(sys)
    # noinspection PyUnresolvedReferences
    sys.setdefaultencoding('utf-8')
    f = XLeagueBotFactory()
    port = int(os.getenv('OPENSHIFT_PYTHON_PORT', 8888))
    host = os.getenv('OPENSHIFT_PYTHON_IP', "0.0.0.0")
    app = Application(f)
    reactor.connectTCP(s.network, s.port, f)
    reactor.listenTCP(port, app, interface=host)
    reactor.run()
