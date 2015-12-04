#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import json
import os
import random
import re
import string
import sys
import time
from twisted.internet import reactor, protocol
from twisted.web.client import getPage
from twisted.words.protocols import irc
from twisted.internet.threads import deferToThread
import plugins.ELO as ELO
import plugins.database as db
import plugins.wordpress as wordpress

reload(sys)
# noinspection PyUnresolvedReferences
sys.setdefaultencoding('utf-8')

InQueue = 0
GameOpen = 0
GameType = ""
NeededToStart = 8
QueuedPlayers = []
PodGames = {2: 1, 4: 6, 8: 12}


# IRC functions
def clientinput(XLeagueBot):
    while True:
        msg = raw_input()
        XLeagueBot.clientmsg("#xleague", msg)

# noinspection PyClassHasNoInit,PyClassHasNoInit,PyAbstractClass
class XLeagueBot(irc.IRCClient):
    nickname = "XLeagueBot"

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        deferToThread(clientinput, self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        self.join(self.factory.channel)

    def joined(self, channel):
        status = "Joined %s" % channel
        log(status)
        auth(self)

    def noticed(self, user, channel, msg):
        status = "Notice from %s: %s" % (user, msg)
        log(status)

    def privmsg(self, user, channel, msg):
        global InQueue
        global QueuedPlayers
        global NeededToStart
        global GameType
        global PodGames
        global GameOpen

        user = user.split('!', 1)[0]
        status = "%s in %s: %s" % (user, channel, msg)
        log(status)

        if channel == self.nickname:
            ignore = ['ChanServ']
            if channel not in ignore:
                msg = "Please use #XLeague for commands."
                channel = user
                sendmsg(self, channel, msg)

        if msg.startswith(".join"):
            player = db.getplayer(user)
            games = db.getrunning()
            if player is not None:
                if player['Name'] not in QueuedPlayers and player['Name'] not in games and GameOpen == 1:
                    addtoqueue(user)
                    if InQueue == NeededToStart:
                        msg = startpod(self)
                    else:
                        msg = str(NeededToStart - InQueue) + " to start %s. Type .join to join" % GameType

                elif GameOpen == 0:
                    msg = "No games open. Ask a Judge to open a game for you."
                else:
                    msg = "You are already in a queue"
            else:
                msg = "You are not vouched"
            sendmsg(self, channel, msg)

        if msg.startswith(".leave"):
            if user in QueuedPlayers:
                removefromqueue(user)
                msg = "%s left the queue" % user
            else:
                msg = "You can't leave if you didn't join, silly"
            sendmsg(self, channel, msg)

        if msg.startswith(".players"):
            if GameOpen == 1:
                msg = "%i out of %i in queue for %s: " % (InQueue, NeededToStart, GameType) + ", ".join(
                    map(str, QueuedPlayers))
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
                msg = "Stats for %s - Rating: %i - Games Played: %i - Wins: %i - Losses: %i - WLR: %s" % (
                    stats['Name'], stats['ELO'], stats['Played'], stats['W'], stats['L'], wlr)
            except TypeError:
                msg = "No player named '%s' found" % player
            sendmsg(self, channel, msg)

        if msg.startswith(".card"):
            card = msg.split(" ", 1)[1]
            fetchcarddatabyname(self, channel, card)

        if msg.startswith(".games"):
            running = db.getrunning()
            if not running:
                msg = "No games are in progress."
            else:
                msg = "Games in progress "
                for row in running:
                    msg += "| #%s " % str(row[0])
            sendmsg(self, channel, msg)

        if msg.startswith(".info"):
            id = msg.split()
            id = int(id[1])
            game = db.getgameid(id)
            if game is not None:
                # noinspection PyPep8
                msg = "Game #%i - Running: %s - Type: %s - Pod size: %i - Games Played: %i - Players: %s, %s, %s, %s, %s, %s, %s, %s" % (
                    game['ID'], game['Running'], game['GameType'], game['Pod'], game['GamesPlayed'], game['Player 1'],
                    game['Player 2'], game['Player 3'], game['Player 4'], game['Player 5'], game['Player 6'],
                    game['Player 7'], game['Player 8'])
                msg = msg.replace(", None", "")
            else:
                msg = "There is no game with ID %i" % id
            sendmsg(self, channel, msg)

        if msg.startswith(".help"):
            channel = user
            msg = "My commands:\n"
            msg += ".join ~~~ Joins queue for an open game\n"
            msg += ".leave ~~~ Leaves Queue you were in\n"
            msg += ".players ~~~ Lists players queued for an open game\n"
            msg += ".player <nick> ~~~ Gets stats of player\n"
            msg += ".games ~~~ Lists IDs of running games\n"
            msg += ".info <GameID> ~~~ Gets info about game\n"
            msg += ".card <CardName> ~~~ Gets details of a card\n"
            judge = db.getplayer(user)
            if judge['Judge'] == 1:
                msg += "===== JUDGE COMMANDS =====\n"
                msg += ".vouch <nick> ~~~ Vouches player\n"
                msg += ".open <GameType> <Players> ~~~ Opens a draft/sealed for number of players\n"
                msg += ".close <GameID> ~~~ Closes game (Used for games in database, NOT for queues)\n"
                msg += ".result <GameID> <Winner> <WinnerScore> <LoserScore> <Loser> ~~~ Reports a result for GameID.\n"
                msg += ".updateleader ~~~ Updates leaderboard on the website"
            sendmsg(self, channel, msg)

        # Judge commands

        if msg.startswith(".vouch"):
            judge = db.getplayer(user)
            if judge['Judge'] == 1:
                vouched = msg.split()
                vouched = vouched[1]
                db.vouchplayer(vouched)
                msg = "Succesfully vouched %s" % vouched
            else:
                msg = "You don't have sufficient permissions to vouch anybody"
            sendmsg(self, channel, msg)

        if msg.startswith(".open"):
            judge = db.getplayer(user)
            if judge['Judge'] == 1:
                msg = msg.split()
                GameOpen = 1
                GameType = msg[1]
                NeededToStart = int(msg[2])
                InQueue = 0
                QueuedPlayers = []
                msg = "%s for %i players is now open. Type .join to join" % (GameType, NeededToStart)
            else:
                msg = "You don't have sufficient permissions to open new game."
            sendmsg(self, channel, msg)

        if msg.startswith(".close"):
            judge = db.getplayer(user)
            if judge['Judge'] == 1:
                msg = msg.split()
                id = int(msg[1])
                db.closegame(id)
                msg = "Game closed."
            else:
                msg = "You don't have sufficient permissions to clos games."
            sendmsg(self, channel, msg)

        if msg.startswith(".result"):
            judge = db.getplayer(user)
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

                msg = "New Ratings: %s %i [+%i] %s %i [%i]" % (
                    winner, winnerelo, changewinner, loser, loserelo, changeloser)

                db.ratingchange(winner, winnerelo, playedw, ww, lw)
                db.ratingchange(loser, loserelo, playedl, wl, ll)

                game = db.getgameid(id)
                played = game['GamesPlayed'] + 1
                db.gamenewplayed(played, id)
                if played == PodGames[game['Pod']]:
                    db.closegame(id)
                    msg += "\nGame #%i ended." % id
            else:
                msg = "You don't have sufficient permissions to report results. Ask a judge to report them for you."
            sendmsg(self, channel, msg)

        if msg.startswith(".updateleader"):
            judge = db.getplayer(user)
            if judge['Judge'] == 1:
                wordpress.updateleader()
                msg = "Leaderboard updated"
            else:
                msg = "You don't have sufficient permissions to update leaderboard"
            sendmsg(self, channel, msg)

        # Admin commands

        if msg.startswith(".promote"):
            admins = ['iScrE4m']
            if user in admins:
                judge = msg.split()
                judge = judge[1]
                db.makejudge(judge)
                giveop(self, judge)
                msg = "%s is now Judge" % judge
            else:
                msg = "Only admin can promote players."
            sendmsg(self, channel, msg)

    def userLeft(self, user, channel):
        global QueuedPlayers
        global InQueue
        user = user.split('!', 1)[0]
        if user in QueuedPlayers:
            removefromqueue(user)

    def clientmsg(self, channel, message):
        reactor.callFromThread(self.msg, channel, message)
        status = "XLeagueBot in %s: %s" % (channel, message)


class XLeagueBotFactory(protocol.ClientFactory):
    protocol = XLeagueBot

    def __init__(self):
        self.channel = "#XLeague"

    def clientConnectionLost(self, connector, reason):
        connector.connect()

    # noinspection PyUnresolvedReferences
    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


# Called functions
def errorhandler(error):
    log(str(error))


def auth(self):
    with open(os.path.join(os.path.dirname(__file__), "auth.txt")) as authfile:
        logininfo = authfile.read().split(',')
        msg = "auth %s %s" % (logininfo[0], logininfo[1])
        self.msg('AuthServ@Services.GameSurge.net', msg)


def giveop(self, user):
    msg = "addop #xLeague %s" % user
    self.msg('ChanServ', msg)


def log(status):
    timestamp = time.strftime("%H:%M:%S", time.localtime(time.time()))
    status = "[%s] " % timestamp + status
    # Adds timestamp, prints and logs current status
    status = status.encode('utf-8', errors='replace')
    print status
    with open(os.path.join(os.path.dirname(__file__), "log.txt"), 'a') as f:
        f.write("%s\n" % status)


def sendmsg(self, channel, msg):
    status = "Sending message to %s: %s" % (channel, msg)
    msg = msg.encode('UTF-8', 'replace')
    self.msg(channel, msg)
    log(status)


def addtoqueue(player):
    global InQueue
    InQueue += 1
    QueuedPlayers.append(player)


def removefromqueue(player):
    global InQueue
    InQueue -= 1
    QueuedPlayers.remove(player)


def startpod(self):
    global InQueue
    global GameOpen
    global GameType
    global QueuedPlayers
    id = db.getgamenewid()
    # Creating list for new database entry with new ID, is running and 0 games played, Pod, Type
    pod = [id, "Yes", 0, NeededToStart, GameType]
    # Generating password to send to players
    password = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(7))
    # Send each player the password and add him to database
    for queued in QueuedPlayers:
        pod.append(queued)
        msg = "Your %s has started. Password: '%s'" % (GameType, password)
        queued = queued.encode('UTF-8', 'replace')
        sendmsg(self, queued, msg)
    # If pod has fewer than 8 people, this will make sure we give enough data to the database
    while len(pod) < 13:
        pod.append("None")
    db.creategame(pod)
    msg = "Game #%i - %s is starting" % (id, GameType)
    # Close queuing
    InQueue = 0
    GameOpen = 0
    GameType = 0
    QueuedPlayers = []
    return msg


# .card deferred processing - I hate deferred. So much.

def stripcurlybraces(s):
    return re.sub("[{}]", "", s)


def fetchcarddatabyname(self, channel, name):
    apiurl = "http://api.deckbrew.com/mtg/cards/" + re.sub("[\'\",]", "", re.sub(" ", "-", name.lower()))
    card = getPage(apiurl)
    card.addCallback(cardcallback(self, channel))
    card.addErrback(errorhandler)


# Returning a function with only one input allows us to get more variables from callback
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
    msg = name + " [" + supertypes + types + subtypes + "] " + cost + "\n" + text + power
    sendmsg(self, channel, msg)


if __name__ == '__main__':
    f = XLeagueBotFactory()
    try:
        log("Connecting")
        # noinspection PyUnresolvedReferences
        reactor.connectTCP("irc.gamesurge.net", 6667, f)
        # noinspection PyUnresolvedReferences
        reactor.run()
    except Exception as e:
        print("Error connecting: " + str(e))
        log(str(e))
