#!/usr/bin/env python

import os
import json
import sqlite3

import pandas.io.sql as sql

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


def jsonplayers():
    read = sql.read_sql("SELECT *, (SELECT COUNT(*) from players b where b.ELO >= a.ELO and Played > 0) as Rank FROM players a WHERE Played > 0 ORDER BY ELO DESC", database)
    ## read.index += 1
    read = read.to_dict(orient='records')
    ## read = {str(k):v for k, v in read.items()}
    results = {"players":read}
    ## rows = db.execute("SELECT * FROM players").fetchall()
    ## results = {"players":[dict (ix) for ix in rows]}
    return json.dumps( results ) 


def jsongames():
    rows = db.execute("SELECT * FROM games").fetchall()
    results = {"games":[dict (ix) for ix in rows]}
    return json.dumps( results ) 

def jsonplayer(player):
    db.execute("SELECT *, (SELECT COUNT(*) from players b where b.ELO >= a.ELO and Played > 0) as Rank FROM players a WHERE Name = ? COLLATE NOCASE", (player,))
    playerstats = {"player":[dict(db.fetchone())]}
    return playerstats

def jsongame(id):
    db.execute("SELECT * FROM games WHERE ID = ? COLLATE NOCASE", (int(id),))
    gamestats = {"game":[dict(db.fetchone())]}
    return gamestats

def jsonrequests():
    rows = db.execute("SELECT * FROM vouchrequests").fetchall()
    result = {"vouchrequests":[dict (ix) for ix in rows]}
    return json.dumps ( result )

def vouchrequest(name, about):
    request = db.execute("SELECT 1 FROM vouchrequests WHERE name=?", (name, ))
    didrequest = request.fetchone()
    vouched = db.execute("SELECT 1 FROM players WHERE name=?", (name, ))
    isvouched = request.fetchone()
    if didrequest is not None:
        done = "Tried to send vouch request, but you already requested vouch."
    elif isvouched is not None:
        done = "Tried to send vouchrequest, but you are already vouched."
    else:
        db.execute("INSERT INTO vouchrequests VALUES (?, ?)", (name, about))
        database.commit()
        done = "Congratulations %s! Vouch request sent, we will process it as soon as possible!" % name
    return done

def confirmvouch(name):
    db.execute("SELECT 1 from vouchrequests WHERE name=?", (name, ))
    player = db.fetchone()
    if player is not None:
        vouchplayer(name)
        db.execute("DELETE FROM vouchrequests WHERE name=?", (name, ))
        result = "%s vouched." % name
        database.commit()
    else:
        result = "Couldn't vouch %s." % name
    return result

def denyvouch(name):
    db.execute("SELECT 1 from vouchrequests WHERE name=?", (name, ))
    player = db.fetchone()
    if player is not None:
        db.execute("DELETE FROM vouchrequests WHERE name=?", (name, ))
        result = "Vouch request by %s denied." % name
        database.commit()
    else:
        result = "Couldn't find %s in vouch requests." % name
    return result

if __name__ == '__main__':
    print jsonplayer("iScrE4m")
