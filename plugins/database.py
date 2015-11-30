#!/usr/bin/env python

import sqlite3, os

script_dir = os.path.dirname(__file__)
rel_path = "database/main.db"
database = sqlite3.connect(os.path.join(script_dir, rel_path), timeout=1)
database.row_factory = sqlite3.Row
db  = database.cursor()

def getPlayer(player):
	db.execute("SELECT * FROM players WHERE Name = '%s' COLLATE NOCASE" % player)
	playerstats = dict(db.fetchone())
	return playerstats

def ratingChange(Name, ELO, Played, W, L):
	db.execute("UPDATE players SET ELO = %i, Played = %i, W = %i, L = %i WHERE Name = '%s' COLLATE NOCASE" % (ELO, Played, W, L, Name))
	database.commit()

def vouchPlayer(vouched):
	db.execute("SELECT MAX(ID) as max_id from players")
	player = db.fetchone()
	ID = player[0]
	NewID = ID + 1
	db.execute("INSERT INTO players VALUES (?, ?, 0, 1500, 0, 0, 0)", (NewID, vouched))
	database.commit()

def makeJudge(judge):
	db.execute("UPDATE players SET Judge = 1 WHERE Name = '%s' COLLATE NOCASE" % (judge)) 
	database.commit()

def getRunning():
	db.execute("SELECT * FROM games WHERE Running = 'Yes'")
	running = db.fetchall()
	return running

def GameNewPlayed(Played, ID):
	db.execute("UPDATE games set GamesPlayed = %i WHERE ID = %i" % (Played, ID))
	database.commit()

def closeGame(ID):
	db.execute("UPDATE games set Running = 'No' WHERE ID = %i" % ID)
	database.commit()

def getGameID(ID):
	db.execute("SELECT * FROM games WHERE ID = %i" % ID)
	ID = db.fetchone()
	return ID

def getGameNewID():
	db.execute("SELECT MAX(ID) AS max_id FROM games")
	game = db.fetchone()
	NewID = int(game[0]) + 1
	return NewID

def CreateGame(Pod):
	db.execute("INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", Pod)
	database.commit()

if __name__ == '__main__':
    getRunning()