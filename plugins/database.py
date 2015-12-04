#!/usr/bin/env python

import os
import sqlite3

script_dir = os.path.dirname(__file__)
rel_path = "database/main.db"
database = sqlite3.connect(os.path.join(script_dir, rel_path), timeout=1)
database.row_factory = sqlite3.Row
db = database.cursor()


def getplayer(player):
    db.execute("SELECT * FROM players WHERE Name = ? COLLATE NOCASE", (player,))
    playerstats = dict(db.fetchone())
    return playerstats


def ratingchange(name, elo, played, w, l):
    db.execute("UPDATE players SET ELO = ?, Played = ?, W = ?, L = ? WHERE Name = ? COLLATE NOCASE",
               (elo, played, w, l, name))
    database.commit()


def vouchplayer(vouched):
    db.execute("SELECT MAX(ID) AS max_id FROM players")
    player = db.fetchone()
    id = player[0]
    newid = id + 1
    db.execute("INSERT INTO players VALUES (?, ?, 0, 1500, 0, 0, 0)", (newid, vouched))
    database.commit()


def makejudge(judge):
    db.execute("UPDATE players SET Judge = 1 WHERE Name = ? COLLATE NOCASE", (judge,))
    database.commit()


def getrunning():
    db.execute("SELECT * FROM games WHERE Running = 'Yes'")
    running = db.fetchall()
    return running


def gamenewplayed(played, id):
    db.execute("UPDATE games SET GamesPlayed = ? WHERE ID = ?", (played, id))
    database.commit()


def closegame(id):
    db.execute("UPDATE games SET Running = 'No' WHERE ID = ?", (id,))
    database.commit()


def getgameid(id):
    db.execute("SELECT * FROM games WHERE ID = ?", (id,))
    id = db.fetchone()
    return id


def getgamenewid():
    db.execute("SELECT MAX(ID) AS max_id FROM games")
    game = db.fetchone()
    newid = int(game[0]) + 1
    return newid


def creategame(pod):
    db.execute("INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", pod)
    database.commit()


if __name__ == '__main__':
    getrunning()
