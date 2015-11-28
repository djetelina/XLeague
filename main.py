#!/usr/bin/env python

from __future__ import division

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, defer
from twisted.web.client import getPage

import plugins.database as db
import plugins.ELO as elo
import plugins.wordpress as wordpress

import time, os, string, random, json


InQueue = 0
GameOpen = 0
GameType = ""
NeededToStart = 8
QueuedPlayers = []
PodGames = {2:1, 4:6, 8:12}

# IRC functions

class XLeagueBot(irc.IRCClient):

	nickname = "XLeagueBot"

	def connectionMade(self):
		irc.IRCClient.connectionMade(self)

	def connectionLost(self, reason):
		irc.IRCClient.connectionLost(self, reason)

	def signedOn(self):
		self.join(self.factory.channel)

	def joined(self, channel):
		status = "Joined %s" % (channel)
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
				SendMsg(self, channel, msg)

		if msg.startswith(".join"):
			player = db.getPlayer(user)
			games = db.getRunning()
			if player is not None:
				if player['Name'] not in QueuedPlayers and player['Name'] not in games and GameOpen == 1:
					AddToQueue(user)
					if InQueue == NeededToStart:
						msg = StartPod(self)
					else:
						msg = str(NeededToStart - InQueue) + " to start %s. Type .join to join" % GameType
					
				elif GameOpen == 0:
					msg = "No games open. Ask a Judge to open a game for you."
				else:
					msg = "You are already in a queue"
			else:
				msg = "You are not vouched"
			SendMsg(self, channel, msg)

		if msg.startswith(".leave"):
			if user in QueuedPlayers:
				RemoveFromQueue(user)
				msg = "%s left the queue" % user
			else:
				msg = "You can't leave if you didn't join, silly"
			SendMsg(self, channel, msg)

		if msg.startswith(".players"):
			if GameOpen ==1:
				msg = "%i out of %i in queue for %s: " % (InQueue, NeededToStart, GameType) + ", ".join(map(str,QueuedPlayers))
			else:
				msg = "No games open. Ask a Judge to open a game for you."
			SendMsg(self, channel, msg)

		if msg.startswith(".player "):
			player = msg.split()
			player = player[1]
			try:
				stats = db.getPlayer(player)
				try:
					WLR = str(int(stats['W'] / stats['Played'] * 100)) + "%"
				except ZeroDivisionError:
					WLR = "N/A"
				msg = "Stats for %s - Rating: %i - Games Played: %i - Wins: %i - Losses: %i - WLR: %s" % (stats['Name'], stats['ELO'], stats['Played'], stats['W'], stats['L'], WLR)
			except TypeError:
				msg = "No player named '%s' found" % player
			SendMsg(self, channel, msg)
		
		if msg.startswith(".card"):
			card = msg.split(" ",1)[1]
			fetchCardDataByName(self, channel, card)

		if msg.startswith(".help"):
			channel = user
			msg = "My commands:\n"
			msg += ".join ~~~ Joins queue for an open game\n"
			msg += ".leave ~~~ Leaves Queue you were in\n"
			msg += ".players ~~~ Lists players queued for an open game\n"
			msg += ".player <nick> ~~~ Gets stats of player\n"
			msg += ".card <CardName> ~~~ Gets details of a card\n"
			judge = db.getPlayer(user)
			if judge['Judge'] == 1:
				msg += "===== JUDGE COMMANDS ====="
				msg += ".vouch <nick> ~~~ Vouches player\n"
				msg += ".open <GameType> <Players> ~~~ Opens a draft/sealed for number of players\n"
				msg += ".close <GameID> ~~~ Closes game\n"
				msg += ".result <GameID> <Winner> <WinnerScore> <LoserScore> <Loser> ~~~ Reports a result for GameID.\n"
				msg += ".updateleader ~~~ Updates leaderboard on the website\n"
			SendMsg(self, channel, msg)

		# Judge commands

		if msg.startswith(".vouch"):
			judge = db.getPlayer(user)
			if judge['Judge'] == 1:
				vouched = msg.split()
				vouched = vouched[1]
				db.vouchPlayer(vouched)
				msg = "Succesfully vouched %s" % (vouched)
			else:
				msg = "You don't have sufficient permissions to vouch anybody"
			SendMsg(self, channel, msg)

		if msg.startswith(".open"):
			judge = db.getPlayer(user)
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
			SendMsg(self, channel, msg)

		if msg.startswith(".close"):
			judge = db.getPlayer(user)
			if judge['Judge'] == 1:
				msg = msg.split()
				ID = int(msg[1])
				db.closeGame(ID)
				msg = "Game closed."
			else:
				msg = "You don't have sufficient permissions to clos games."
			SendMsg(self, channel, msg)

		if msg.startswith(".result"):
			judge = db.getPlayer(user)
			if judge['Judge'] == 1:
				result = msg.split()
				ID = int(result[1])

				Winner = result[2]
				Winnerdict = db.getPlayer(Winner)
				PlayedW = Winnerdict['Played'] + 1
				WW = Winnerdict['W'] + 1
				LW = Winnerdict['L']

				Loser = result[5]
				Loserdict = db.getPlayer(Loser)
				PlayedL = Loserdict['Played'] + 1
				WL = Loserdict['W']
				LL = Loserdict['L'] + 1

				WinnerELO = elo.NewELO("W", Winnerdict, Loserdict)
				LoserELO = elo.NewELO("L", Winnerdict, Loserdict)
				ChangeWinner = WinnerELO - Winnerdict['ELO']
				ChangeLoser = LoserELO - Loserdict['ELO']

				msg = "New Ratings: %s %i [+%i] %s %i [%i]" % (Winner, WinnerELO, ChangeWinner, Loser, LoserELO, ChangeLoser)
				
				db.ratingChange(Winner, WinnerELO, PlayedW, WW, LW)
				db.ratingChange(Loser, LoserELO, PlayedL, WL, LL)

				game = db.getGameID(ID)
				Played = game['GamesPlayed'] + 1
				db.GameNewPlayed(Played, ID)
				if Played == PodGames[game['Pod']]:
					db.closeGame(ID)
			else:
				msg = "You don't have sufficient permissions to report results. Ask a judge to report them for you."
			SendMsg(self, channel, msg)

		if msg.startswith(".updateleader"):
			judge = db.getPlayer(user)
			if judge['Judge'] == 1:
				wordpress.updateLeader()
				msg = "Leaderboard updated"
			else:
				msg = "You don't have sufficient permissions to update leaderboard"
			SendMsg(self, channel, msg)
		
		# Admin commands

		if msg.startswith(".promote"):
			admins = ['iScrE4m']
			if user in admins:
				judge = msg.split()
				judge = judge[1]
				db.makeJudge(judge)
				giveOp(self, judge)
				msg = "%s is now Judge" % (judge)
			else:
				msg = "Only admin can promote players."
			SendMsg(self, channel, msg)

	def userLeft(self, user, channel):
		global QueuedPlayers
		global InQueue
		user = user.split('!', 1)[0]
		if user in QueuedPlayers:
			RemoveFromQueue(user)

class XLeagueBotFactory(protocol.ClientFactory):

	protocol = XLeagueBot

	def __init__(self):
		self.channel = "#XLeague"

	def clientConnectionLost(self, connector, reason):
		connector.connect()

	def clientConnectionFailed(self, connector, reason):
		print "connection failed:", reason
		reactor.stop()

# Called functions

def errorHandler(error):
    print "An error has occurred: <%s>" % str(error)

def auth(self):
	with open(os.path.join(os.path.dirname(__file__), "auth.txt")) as f:
		auth = f.read().split(',')
		msg = "auth %s %s" % (auth[0], auth[1])
		self.msg('AuthServ@Services.GameSurge.net', msg)

def giveOp(self, user):
	msg = "addop #xLeague %s" % user
	self.msg('ChanServ', msg)

def log(status):
	timestamp = time.strftime("%H:%M:%S", time.localtime(time.time()))
	status = "[%s] "%timestamp + status
	# Adds timestamp, prints and logs current status
	print status
	with open(os.path.join(os.path.dirname(__file__), "log.txt"), 'a') as f:
		f.write("%s\n" % status)

def SendMsg(self, channel, msg):
	status = "Sending message to %s: %s" % (channel, msg)
	msg = msg.encode('UTF-8', 'replace')
	self.msg(channel, msg)
	log (status)

def AddToQueue(player):
	global InQueue
	InQueue = InQueue + 1
	QueuedPlayers.append(player)

def RemoveFromQueue(player):
	global InQueue
	InQueue = InQueue - 1
	QueuedPlayers.remove(player)

def StartPod(self):
	global InQueue
	global GameOpen
	global GameType
	global QueuedPlayers
	ID = db.getGameNewID()
	# Creating list for new database entry with new ID, is running and 0 games played, Pod, Type
	Pod = [ID, "Yes", 0, NeededToStart, GameType]
	# Generating password to send to players
	password = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(7))
	# Send each player the password and add him to database
	print QueuedPlayers
	for queued in QueuedPlayers:
		print queued
		Pod.append(queued)
		msg = "Your %s has started. Password: '%s'" % (GameType, password)
		queued = queued.encode('UTF-8', 'replace')
		SendMsg(self, queued, msg)
	# If pod has fewer than 8 people, this will make sure we give enough data to the database
	while len(Pod) < 13:
		Pod.append("None")
	db.CreateGame(Pod)
	msg = "Game #%i - %s is starting" % (ID, GameType)
	# Close queuing
	InQueue = 0
	GameOpen = 0
	GameType = 0
	QueuedPlayers = []
	return msg

# .card deferred processing - I hate deferred. So much.

def stripCurlyBraces(s):
	return str.replace(str.replace(s, "{", ""), "}", "")

def fetchCardDataByName(self, channel, name):
	apiurl = "http://api.deckbrew.com/mtg/cards/" + str.replace(str.replace(str.replace(name.lower(), " ", "-"), ",", ""), "'", "")
	card = getPage(apiurl)
	card.addCallback(cardCallback(self, channel))
	card.addErrback(errorHandler)

# Returning a function with only one input allows us to get more variables from callback which we need to succesfully send a msg after the fetching is done

def cardCallback(self, channel):
	def callprocess(data):
		tocall = cardprocess(self, channel, data)
	return callprocess

def cardprocess(self, channel, data):
	c = json.loads(data)
	name = c["name"].encode("utf-8")
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
		cost = "(" + stripCurlyBraces(c["cost"].encode("utf-8")) + ") "
	else:
		cost = ""
	text = str.replace(stripCurlyBraces(c["text"].encode("utf-8")), "\n", " ")
	if "power" in c:
		power = " [" + c["power"] + "/" + c["toughness"] + "]"
	else:
		power = ""
	msg = name + " [" + supertypes + types + subtypes + "] " + cost + "\n" + text + power
	SendMsg(self, channel, msg)


if __name__ == '__main__':
	f = XLeagueBotFactory()
	try:
		reactor.connectTCP("irc.gamesurge.net", 6667, f)
		reactor.run()
	except Exception as e:
		print("Error connecting: " + str(e))

