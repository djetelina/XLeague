from __future__ import division
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, defer
from twisted.web.client import getPage

import time, sys, json, numbers, datetime

joined = 0
players = []

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
		user = user.split('!', 1)[0]

		if channel == self.nickname:
			msg = "Please use #XLeague for commands."
			self.msg(user, msg)
			return

		if msg.startswith(".join"):
			canjoin = players.count(user)
			if canjoin == 0:	
				joined = joined + 1
				players.append(user)
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
			canleave = players.count(user)
			if canleave == 1:
				players.remove(user)
				joined = joined - 1
				msg = "%s left."%(user)
			else:
				msg = "I could not find you in draft."
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