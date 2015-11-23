#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, defer
from twisted.web.client import getPage

import time, sys, json, numbers, datetime, sqlite3, os, string, random

joined = 0
players = []

playdb = sqlite3.connect((os.path.join(os.path.dirname(__file__), "players.db")))
pdb = playdb.cursor()

gamedb = sqlite3.connect((os.path.join(os.path.dirname(__file__), "games.db")))
gdb = gamedb.cursor()

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
			gdb.execute("SELECT * FROM games WHERE Running = 'Yes'")
			canjoin2 = gdb.fetchone()
			if canjoin2 is not None:
				if canjoin == 0 and player not in canjoin2:	
					joined = joined + 1
					players.append(player)
					if joined == 1:
						msg = "7 to go. Type .join to join.\nPlayers: " + ", ".join(map(str,players))
					elif joined == 2:
						msg = "6 to go. Type .join to join.\nPlayers: " + ", ".join(map(str,players))
					elif joined == 3:
						msg = "5 to go. Type .join to join.\nPlayers: " + ", ".join(map(str,players))
					elif joined == 4:
						msg = "4 to go. Type .join to join.\nPlayers: " + ", ".join(map(str,players))
					elif joined == 5:
						msg = "3 to go. Type .join to join.\nPlayers: " + ", ".join(map(str,players))
					elif joined == 6:
						msg = "2 to go. Type .join to join.\nPlayers: " + ", ".join(map(str,players))
					elif joined == 7:
						msg = "1 to go. Type .join to join.\nPlayers: " + ", ".join(map(str,players))
					elif joined == 8:
						joined = 0
						startdraft(self)
				else:
					msg = "You are already queued or in a draft."
			else: 
				if canjoin == 0:	
					joined = joined + 1
					players.append(player)
					if joined == 1:
						msg = "7 to go. Type .join to join.\nPlayers: " + ", ".join(map(str,players))
					elif joined == 2:
						msg = "6 to go. Type .join to join.\nPlayers: " + ", ".join(map(str,players))
					elif joined == 3:
						msg = "5 to go. Type .join to join.\nPlayers: " + ", ".join(map(str,players))
					elif joined == 4:
						msg = "4 to go. Type .join to join.\nPlayers: " + ", ".join(map(str,players))
					elif joined == 5:
						msg = "3 to go. Type .join to join.\nPlayers: " + ", ".join(map(str,players))
					elif joined == 6:
						msg = "2 to go. Type .join to join.\nPlayers: " + ", ".join(map(str,players))
					elif joined == 7:
						msg = "1 to go. Type .join to join.\nPlayers: " + ", ".join(map(str,players))
					elif joined == 8:
						joined = 0
						startdraft(self)
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

		if msg.startswith(".result"):
			result = msg.split()
			gdb.execute("SELECT * from games WHERE Running = 'Yes'")
			inprogress = gdb.fetchone()
			if inprogress is not None:
				if result[1] == user or result[2] == user and user in inprogress:
					ID = inprogress[0]
					DraftPlayed = inprogress[10] + 1
					Player1 = result[1]
					ScoreP1 = int(result[2])
					Player2 = result[4]
					ScoreP2 = int(result[3])
					pdb.execute("SELECT * FROM players WHERE Name = '%s'" % Player1)
					P1 = pdb.fetchone()
					pdb.execute("SELECT * FROM players WHERE Name = '%s'" % Player2)
					P2 = pdb.fetchone()
					WinsP1 = ScoreP1 + P1[4]
					WinsP2 = ScoreP2 + P2[4]
					LossP1 = ScoreP2 + P1[5]
					LossP2 = ScoreP1 + P2[5]
					NewPlayedP1 = ScoreP1 + ScoreP2 + P1[3]
					NewPlayedP2 = ScoreP1 + ScoreP2 + P2[3]
					if P1[3] <= 20:
						K1 = 20
					elif P1[3] > 20 and P1[3] < 40:
						K1 = 15
					elif P1[3] >= 40:
						K1 = 10
					if P2[3] <= 20:
						K2 = 20
					elif P2[3] > 20 and P2[3] <40:
						K2 = 15
					elif P2[3] >= 40:
						K2 = 10
					E1 = (1.0 / (1.0 + pow(10, ((P2[2] - P1[2]) / 400))))
					E2 = 1 - E1
					if ScoreP1 > ScoreP2:
						NewRatingP1 = int((P1[2] + K1 * (1 - E1)))
						NewRatingP2 = int((P2[2] + K2 * (0 - E2)))
						ChangeP1 = abs(P1[2] - NewRatingP1)
						ChangeP2 = abs(P2[2] - NewRatingP2)

						#Converting ratings to Strings for msg
						NewRatingP1 = str(NewRatingP1)
						NewRatingP2 = str(NewRatingP2)
						ChangeP1 = str(ChangeP1)
						ChangeP2 = str(ChangeP2)
						msg = "New Ratings: %s %s (+%s) %s %s (-%s)"%(P1[1], NewRatingP1, ChangeP1, P2[1], NewRatingP2, ChangeP2)
					elif ScoreP2 > ScoreP1:
						NewRatingP1 = int((P1[2] + K1 * (0 - E1)))
						NewRatingP2 = int((P2[2] + K2 * (1 - E2)))
						ChangeP1 = abs(P1[2] - NewRatingP1)
						ChangeP2 = abs(P2[2] - NewRatingP2)

						#Converting ratings to Strings for msg
						NewRatingP1 = str(NewRatingP1)
						NewRatingP2 = str(NewRatingP2)
						ChangeP1 = str(ChangeP1)
						ChangeP2 = str(ChangeP2)
						msg = "New Ratings: %s %s (+%s) %s %s (-%s)"%(P2[1], NewRatingP2, ChangeP2, P1[1], NewRatingP1, ChangeP1)
					else:
						msg = "Something horrible happened, results invalid."
					#And back to INT
					NewRatingP1 = int(NewRatingP1)
					NewRatingP2 = int(NewRatingP2)
					pdb.execute("UPDATE players SET ELO = %i, Played = %i, W = %i, L = %i WHERE Name = '%s'" % (NewRatingP1, NewPlayedP1, WinsP1, LossP1, P1[1]))
					pdb.execute("UPDATE players SET ELO = %i, Played = %i, W = %i, L = %i WHERE Name = '%s'" % (NewRatingP2, NewPlayedP2, WinsP2, LossP2, P2[1]))
					if DraftPlayed == 7:
						gdb.execute("UPDATE games SET GamesPlayed = %i, Running = 'No' WHERE ID = %i" % (DraftPlayed, ID))
						ID = str(ID)
						msg += "\nDraft #%s finished." % (ID)
					else:
						gdb.execute("UPDATE games SET GamesPlayed = %i WHERE ID = %i" % (DraftPlayed, ID))
					playdb.commit()
					gamedb.commit()

				else:
					msg = "ERROR: You can't report results for other players or you are not in a running game."
			else:
				msg = "You are not in a running game."
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
			msg = "Currently in draft. Type .join to join.\n Players: " + ", ".join(map(str,players))
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

def startdraft(self):
	global players
	gdb.execute("SELECT MAX(ID) AS max_id FROM games")
	gamestats = gdb.fetchone()
	ID = gamestats[0]
	NEWID = int(ID) + 1
	draft = [NEWID]
	msg = "Draft #%i is starting." % (NEWID)
	self.msg(channel, msg)
	password = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(7))
	for getplayer in players:
		pdb.execute("SELECT * FROM players WHERE Name = '%s'" % getplayer)
		playerstats = pdb.fetchone()
		player = playerstats[1]
		draft.append(player)
		msg = "Your draft has started. Password: %s" % (password)
		player = player.encode('UTF-8', 'replace')
		self.msg(player, msg)
	draft.append("Yes")
	draft.append(0)
	gdb.execute("INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", draft)
	gamedb.commit()
	players = []

if __name__ == '__main__':
	f = XLeagueBotFactory()
	reactor.connectTCP("irc.gamesurge.net", 6667, f)
	reactor.run()