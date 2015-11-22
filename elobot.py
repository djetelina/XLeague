#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, defer
from twisted.web.client import getPage

import time, sys, json, numbers, datetime, sqlite3, os

joined = 0
players = []

playdb = sqlite3.connect((os.path.join(os.path.dirname(__file__), "players.db")))
pdb = playdb.cursor()

class XLeagueBot(irc.IRCClient):
	
	nickname = "XLeagueBot"
	password = ""
	
	def connectionMade(self):
		irc.IRCClient.connectionMade(self)

	def connectionLost(self, reason):
		irc.IRCClient.connectionLost(self, reason)

	# callbacks for events

	def signedOn(self):
		self.join(self.factory.channel)

	def joined(self, channel):
		print "joined %s" %channel

	def privmsg(self, user, channel, msg):
		global joined
		global players
		global pdb
		user = user.split('!', 1)[0]

		if channel == self.nickname:
			msg = "Please use #XLeague for commands."
			self.msg(user, msg)
			return

		if msg.startswith(".join"):
			pdb.execute("SELECT * FROM players WHERE Name = '%s'" % user)
			playerstats = pdb.fetchone()
			player = playerstats[1]
			canjoin = players.count(player)
			if canjoin == 0:	
				joined = joined + 1
				players.append(player)
				if joined == 1:
					msg = "7 to go. Type .join to join.\n Players: " + ",".join(map(str,players))
				elif joined == 2:
					msg = "6 to go. Type .join to join.\n Players: " + ",".join(map(str,players))
				elif joined == 3:
					msg = "5 to go. Type .join to join.\n Players: " + ",".join(map(str,players))
				elif joined == 4:
					msg = "4 to go. Type .join to join.\n Players: " + ",".join(map(str,players))
				elif joined == 5:
					msg = "3 to go. Type .join to join.\n Players: " + ",".join(map(str,players))
				elif joined == 6:
					msg = "2 to go. Type .join to join.\n Players: " + ",".join(map(str,players))
				elif joined == 7:
					msg = "1 to go. Type .join to join.\n Players: " + ",".join(map(str,players))
				elif joined == 8:
					msg = "Draft is Starting."
					joined = 0
					startdraft()
			else:
				msg = "You are already queued."
			self.msg(channel, msg)

		if msg.startswith(".leave"):
			pdb.execute("SELECT * FROM players WHERE Name = '%s'" % user)
			playerstats = pdb.fetchone()
			player = playerstats[1]
			canleave = players.count(player)
			if canleave == 1:
				players.remove(player)
				joined = joined - 1
				msg = "%s left."%(player)
			else:
				msg = "I could not find you in draft."
			msg = msg.encode('UTF-8', 'replace')
			self.msg(channel, msg)

		if msg.startswith(".player"):
			player = msg[8:]
			player = player.strip()
			try:
				pdb.execute("SELECT * FROM players WHERE Name = '%s'" % player)
				playerstats = pdb.fetchone()
				try:
					WLR = str(playerstats[4] / playerstats[5] * 100) + "%"
				except ZeroDivisionError:
					WLR = "N/A"
				msg = "Stats for " + playerstats[1] + " -" + " Rating: " + str(playerstats[2]) + " - Games Played: " + str(playerstats[3]) + " - Wins: " + str(playerstats[4]) + " - Losses: " + str(playerstats[5]) + " - Win Percentage: " + WLR
			except TypeError:
				msg = "No player named '%s' found"%(player)
			msg = msg.encode('UTF-8', 'replace')
			self.msg(channel, msg)


		if msg.startswith(".players"):
			msg = "Currently in draft. Type .join to join.\n Players: " + ",".join(map(str,players))
			self.msg(channel, msg)


class XLeagueBotFactory(protocol.ClientFactory):

	protocol = XLeagueBot

	def __init__(self):
		self.channel = "#XLeague"

	def clientConnectionLost(self, connector, reason):
		connector.connect()

	def clientConnectionFailed(self, connector, reason):
		print "connection failed:", reason
		reactor.stop()

def startdraft():
	print "Draft would start now."

if __name__ == '__main__':
	f = XLeagueBotFactory()
	reactor.connectTCP("irc.gamesurge.net", 6667, f)
	reactor.run()