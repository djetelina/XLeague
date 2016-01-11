#!/usr/bin/env python

"""
Copyright (c) 2016 iScrE4m@gmail.com

To use the code, you must contact the author directly and ask permission.

Database will be restructured
"""

import json
import sqlite3

import pandas.io.sql as sql

from .. import settings as s

database = sqlite3.connect(s.db_path, timeout=1)
database.row_factory = sqlite3.Row
db = database.cursor()

"""
Dealing with players
"""


def getplayer(player):
    """
    Call to retrieve player information

    :param player:      Name of a player (their GameSurge auth)
    :return:            Dictionary with player information
    """
    db.execute("SELECT * FROM players WHERE Name = ? COLLATE NOCASE", (player,))
    playerstats = dict(db.fetchone())
    return playerstats


def ratingchange(name, elo, played, w, l):
    """
    Changes rating of a player

    :param name:        Name of a player to edit
    :param elo:         New rating
    :param played:      New number of games played
    :param w:           New number of games won
    :param l:           New number of games lost
    """
    db.execute("UPDATE players SET ELO = ?, Played = ?, W = ?, L = ? WHERE Name = ? COLLATE NOCASE",
               (elo, played, w, l, name))
    database.commit()


def vouchplayer(vouched):
    """
    Call to vouch player - creates new entry in the database

    :param vouched:     Name of a player to be added
    """
    db.execute("SELECT MAX(ID) AS max_id FROM players")
    player = db.fetchone()
    id = player[0]
    newid = id + 1
    db.execute("INSERT INTO players VALUES (?, ?, 0, 1500, 0, 0, 0)", (newid, vouched))
    database.commit()


def confirmvouch(name):
    """
    Confirms vouch request

    :param name:        Player name
    :return:            String with reply
    """
    db.execute("SELECT 1 FROM vouchrequests WHERE name=? COLLATE NOCASE", (name,))
    player = db.fetchone()
    if player is not None:
        vouchplayer(name)
        db.execute("DELETE FROM vouchrequests WHERE name=? COLLATE NOCASE", (name,))
        reply = "%s vouched." % name
        database.commit()
    else:
        reply = "Couldn't vouch %s." % name
    return reply


def denyvouch(name):
    """
    Denies vouch request

    :param name:        Player name
    :return:            String with reply
    """
    db.execute("SELECT 1 FROM vouchrequests WHERE name=? COLLATE NOCASE", (name,))
    player = db.fetchone()
    if player is not None:
        db.execute("DELETE FROM vouchrequests WHERE name=? COLLATE NOCASE", (name,))
        reply = "Vouch request by %s denied." % name
        database.commit()
    else:
        reply = "Couldn't find %s in vouch requests." % name
    return reply


def makejudge(judge):
    """
    Promotes player to a judge

    :param judge:       Name of a player to be promoted
    """
    db.execute("UPDATE players SET Judge = 1 WHERE Name = ? COLLATE NOCASE", (judge,))
    database.commit()


"""
Dealing with games
"""


def getrunning():
    """
    Call to retrieve running games

    :return:            List with all the games
    """
    db.execute("SELECT * FROM games WHERE Running = 'Yes'")
    running = db.fetchall()
    return running


def gamenewplayed(played, id):
    """
    Updates number of games played within an ID

    :param played:      New number of games played
    :param id:          ID of a game to be edited
    """
    db.execute("UPDATE games SET GamesPlayed = ? WHERE ID = ?", (played, id))
    database.commit()


def closegame(id):
    """
    Sets game's state as not running

    :param id:          ID of a game to be edited
    """
    db.execute("UPDATE games SET Running = 'No' WHERE ID = ?", (id,))
    database.commit()


def getgameid(id):
    """
    Call to get game info by ID

    :param id:          ID of a game to be retrieved
    :return:            List with game info
    """
    db.execute("SELECT * FROM games WHERE ID = ?", (id,))
    id = db.fetchone()
    return id


def getgamenewid():
    """
    Call to get ID for new games

    :return:            Integer with ID
    """
    db.execute("SELECT MAX(ID) AS max_id FROM games")
    game = db.fetchone()
    newid = int(game[0]) + 1
    return newid


def creategame(pod):
    """
    Creates new game

    :param pod:         List with: ID, "Yes", Games played, Pod size, GameType, Players 1-8)
    """
    db.execute("INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", pod)
    database.commit()


"""
API calls

Q: Why do they all have json in their names, when they return dictionaries?
A: Cyclone prints out dictionaries as json
"""


def jsonplayers():
    """
    Creates dictionary with all players and their information

    :return:            Dictionary with all players and all their information
    """
    read = sql.read_sql(
            "SELECT *, (SELECT COUNT(*) FROM players b WHERE b.ELO >= a.ELO AND Played > 0) AS Rank FROM players a WHERE Played > 0 ORDER BY ELO DESC",
            database)
    read = read.to_dict(orient='records')
    results = {"players": read}
    return results


def jsongames():
    """
    Creates dictionary with all games and their information

    :return:            Dictionary with all games and all their information
    """
    rows = db.execute("SELECT * FROM games").fetchall()
    results = {"games": [dict(ix) for ix in rows]}
    return json.dumps(results)


def jsonplayer(player):
    """
    Creates dictionary with info about player specified by name

    :param player:      Name of a player to check
    :return:            Dictionary with player and it's information
    """
    db.execute(
            "SELECT *, (SELECT COUNT(*) FROM players b WHERE b.ELO >= a.ELO AND Played > 0) AS Rank FROM players a WHERE Name = ? COLLATE NOCASE",
            (player,))
    playerstats = {"player": [dict(db.fetchone())]}
    return playerstats


def jsongame(id):
    """
    Creates dictionary with an info about game specified by ID

    :param id:          ID of a game to check
    :return:            Dictionary with game and it's information
    """
    db.execute("SELECT * FROM games WHERE ID = ? COLLATE NOCASE", (int(id),))
    gamestats = {"game": [dict(db.fetchone())]}
    return gamestats


def jsonrequests():
    """
    Creates dictionary with all vouch requests

    :return:            Dictionary with all vouch requests
    """
    rows = db.execute("SELECT * FROM vouchrequests").fetchall()
    result = {"vouchrequests": [dict(ix) for ix in rows]}
    return result


def vouchrequest(name, about):
    """
    Request a vouch

    :param name:        Name of a player for which to request vouch
    :param about:       About player
    :return:            String with reply
    """
    request = db.execute("SELECT 1 FROM vouchrequests WHERE name=? COLLATE NOCASE", (name,))
    didrequest = request.fetchone()
    vouched = db.execute("SELECT 1 FROM players WHERE name=? COLLATE NOCASE", (name,))
    isvouched = vouched.fetchone()
    if didrequest is not None:
        reply = "Tried to send vouch request, but you already requested vouch."
    elif isvouched is not None:
        reply = "Tried to send vouchrequest, but you are already vouched."
    else:
        db.execute("INSERT INTO vouchrequests VALUES (?, ?)", (name, about))
        database.commit()
        reply = "Congratulations %s! Vouch request sent, we will process it as soon as possible!" % name
    return reply
