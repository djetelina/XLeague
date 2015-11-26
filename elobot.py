#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, defer
from twisted.web.client import getPage
import pandas.io.sql as sql
from wordpress_xmlrpc import Client, WordPressPage
from wordpress_xmlrpc.methods import posts

import time, sys, json, numbers, datetime, sqlite3, os, string, random, csv

joined = 0
players = []

vouchers = ["iScrE4m"]

playdb = sqlite3.connect((os.path.join(os.path.dirname(__file__), "players.db")), timeout=1)
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
		with open(os.path.join(os.path.dirname(__file__), "auth.txt")) as f:
			auth = f.read().split(',')
			msg = "auth %s %s" % (auth[0], auth[1])
			self.msg('AuthServ@Services.GameSurge.net', msg)

	def noticed(self, user, channel, msg):
		print "Notice from %s: %s" % (user, msg)

	def privmsg(self, user, channel, msg):
		global joined
		global players
		global pdb
		global vouchers
		user = user.split('!', 1)[0]

		print "%s in %s: %s" % (user, channel, msg)

		if channel == self.nickname:
			msg = "Please use #XLeague for commands."
			self.msg(user, msg)
			return

		if msg.startswith(".join"):
			pdb.execute("SELECT * FROM players WHERE Name = '%s'" % user)
			playerstats = pdb.fetchone()
			player = playerstats[1]
			# check if player isn't already queued
			canjoin = players.count(player)
			gdb.execute("SELECT * FROM games WHERE Running = 'Yes'")
			canjoin2 = gdb.fetchall()
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
				joined = joined -1
				players.remove(player)
				msg = "%s left."%(player)
			else:
				msg = "I could not find you in draft."
			msg = msg.encode('UTF-8', 'replace')
			self.msg(channel, msg)

		if msg.startswith(".result"):
			result = msg.split()
			# Let's select games that are running
			gdb.execute("SELECT * from games WHERE Running = 'Yes'")
			inprogress = gdb.fetchall()
			# If there are games running
			if inprogress is not None:
				# If user is reporting matches that he's playing in, let him through
				if result[1] == user or result[2] == user and user in inprogress:
					# Define ID of the game, so we know which to edit
					ID = inprogress[0]
					# Add 1 to number of games played (reported) for game database
					DraftPlayed = inprogress[10] + 1
					# Define who are our players and what score they reported
					Player1 = result[1]
					ScoreP1 = int(result[2])
					Player2 = result[4]
					ScoreP2 = int(result[3])
					# Find and define players
					pdb.execute("SELECT * FROM players WHERE Name = '%s'" % Player1)
					P1 = pdb.fetchone()
					pdb.execute("SELECT * FROM players WHERE Name = '%s'" % Player2)
					P2 = pdb.fetchone()
					# Add new scores to current wins and losses and games played in database
					WinsP1 = ScoreP1 + P1[4]
					WinsP2 = ScoreP2 + P2[4]
					LossP1 = ScoreP2 + P1[5]
					LossP2 = ScoreP1 + P2[5]
					NewPlayedP1 = ScoreP1 + ScoreP2 + P1[3]
					NewPlayedP2 = ScoreP1 + ScoreP2 + P2[3]
					# Decide which K rating to assign with based on Games Played
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
					# Calculate expectations for ELO
					E1 = (1.0 / (1.0 + pow(10, ((P2[2] - P1[2]) / 400))))
					E2 = 1 - E1
					# If The first score is higher, Player 1 won
					if ScoreP1 > ScoreP2:
						# Calculate new ratings from ELO formula
						NewRatingP1 = int((P1[2] + K1 * (1 - E1)))
						NewRatingP2 = int((P2[2] + K2 * (0 - E2)))
						# Calculate absolute value of rating change
						ChangeP1 = abs(P1[2] - NewRatingP1)
						ChangeP2 = abs(P2[2] - NewRatingP2)
						#Converting ratings to Strings for msg
						NewRatingP1 = str(NewRatingP1)
						NewRatingP2 = str(NewRatingP2)
						ChangeP1 = str(ChangeP1)
						ChangeP2 = str(ChangeP2)
						# Report to channel new ratings
						msg = "New Ratings: %s %s (+%s) %s %s (-%s)"%(P1[1], NewRatingP1, ChangeP1, P2[1], NewRatingP2, ChangeP2)
					elif ScoreP2 > ScoreP1:
						# Calculate new ratings from ELO formula
						NewRatingP1 = int((P1[2] + K1 * (0 - E1)))
						NewRatingP2 = int((P2[2] + K2 * (1 - E2)))
						# Calculate absolute value of rating change
						ChangeP1 = abs(P1[2] - NewRatingP1)
						ChangeP2 = abs(P2[2] - NewRatingP2)
						#Converting ratings to Strings for msg
						NewRatingP1 = str(NewRatingP1)
						NewRatingP2 = str(NewRatingP2)
						ChangeP1 = str(ChangeP1)
						ChangeP2 = str(ChangeP2)
						# Report to channel new ratings
						msg = "New Ratings: %s %s (+%s) %s %s (-%s)"%(P2[1], NewRatingP2, ChangeP2, P1[1], NewRatingP1, ChangeP1)
					else:
						msg = "Something horrible happened, results invalid."
					# Conver rating back to integer for database
					NewRatingP1 = int(NewRatingP1)
					NewRatingP2 = int(NewRatingP2)
					# Update new player scores and stats
					pdb.execute("UPDATE players SET ELO = %i, Played = %i, W = %i, L = %i WHERE Name = '%s'" % (NewRatingP1, NewPlayedP1, WinsP1, LossP1, P1[1]))
					pdb.execute("UPDATE players SET ELO = %i, Played = %i, W = %i, L = %i WHERE Name = '%s'" % (NewRatingP2, NewPlayedP2, WinsP2, LossP2, P2[1]))
					# If all games are finished (7 for 8 player Single Elim), close the game
					if DraftPlayed == 7:
						gdb.execute("UPDATE games SET GamesPlayed = %i, Running = 'No' WHERE ID = %i" % (DraftPlayed, ID))
						ID = str(ID)
						msg += "\nDraft #%s finished." % (ID)
					# Otherwise, just increase number of games already played
					else:
						gdb.execute("UPDATE games SET GamesPlayed = %i WHERE ID = %i" % (DraftPlayed, ID))
					playdb.commit()
					gamedb.commit()

				else:
					msg = "ERROR: You can't report results for other players or you are not in a running game."
			else:
				msg = "You are not in a running game."
			# Encode msg to UTF, twisted doesn't handle Unicode
			msg = msg.encode('UTF-8', 'replace')
			self.msg(channel, msg)

		if msg.startswith(".player "):
			player = msg[8:]
			player = player.strip()
			try:
				pdb.execute("SELECT * FROM players WHERE Name = '%s'" % player)
				playerstats = pdb.fetchone()
				try:
					WLR = str(int(playerstats[4] / playerstats[3] * 100)) + "%"
				except ZeroDivisionError:
					WLR = "N/A"
				msg = "Stats for " + playerstats[1] + " -" + " Rating: " + str(playerstats[2]) + " - Games Played: " + str(playerstats[3]) + " - Wins: " + str(playerstats[4]) + " - Losses: " + str(playerstats[5]) + " - Win Percentage: " + WLR
			except TypeError:
				msg = "No player named '%s' found"%(player)
			msg = msg.encode('UTF-8', 'replace')
			self.msg(channel, msg)

		if msg.startswith(".players"):
			msg = "Players in queue: " + ", ".join(map(str,players))
			self.msg(channel, msg)

		if msg.startswith(".vouch"):
			if user in vouchers:
				vouched = msg.split()	
				pdb.execute("SELECT MAX(ID) AS max_id FROM players")
				playerstats = pdb.fetchone()
				ID = playerstats[0]
				NEWID = int(ID) + 1
				vouched = vouched[1]
				pdb.execute("INSERT INTO players VALUES (?, ?, 1500, 0, 0, 0)", (NEWID, vouched))
				playdb.commit()
				msg = "Succesfully vouched %s" % (vouched)
			else:
				msg = "You don't have sufficient permissions to vouch anybody."
			self.msg(channel, msg)

		if msg.startswith(".postdb"):
			if user in vouchers:
				postdb(self)
				msg = "Posting database."
			else:
				msg = "You can't do that."
			self.msg(channel, msg)

	def userLeft(self, user, channel):
		global players
		user = user.split('!', 1)[0]
		if user in players:
			players = players.remove(user)

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

def postdb(self):
	global playdb
	# read SQL with panda
	read = sql.read_sql("SELECT Name, ELO, Played, W, L FROM players ORDER BY ELO DESC", playdb)
	csvpath = (os.path.join(os.path.dirname(__file__), "temp.csv"))
	# convert and save to csv with pandah
	read.to_csv(csvpath)
	# get wordpress login information
	with open(os.path.join(os.path.dirname(__file__), "wp.txt")) as f:
		wplogin = f.read().split(',')
	# open csv and save it to string
	with open(csvpath, 'rb') as f:
		csvfile = csv.reader(f)
		table = ""
		for row in csvfile:
			table += "%s\n"%(str(row))
	# get rid of unwanted characters
	table = table.translate(None, '\'[]')
	timestamp = time.strftime("%d.%m.%Y at %H:%M:%S", time.localtime(time.time()))
	# define content of new page, syntax for wordpress title, our string in the middle and Timestamp at the end
	content = "[table]" + str(table) + "[/table] \n Last update: %s" % (timestamp)
	# Login to wordpress
	wp = Client("http://xleague.djetelina.cz/xmlrpc.php", "%s"%(wplogin[0]), "%s"%(wplogin[1]))
	# Define what are we editing
	page = WordPressPage()
	page.title = "Leaderboard"
	page.id = 139
	page.content = content
	page.post_status = "publish"
	# Edit desired page
	wp.call(posts.EditPost(page.id, page))
	playdb.commit()


if __name__ == '__main__':
	f = XLeagueBotFactory()
	reactor.connectTCP("irc.gamesurge.net", 6667, f)
	reactor.run()