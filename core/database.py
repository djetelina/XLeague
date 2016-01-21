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
from helpers import abs_db_path

database = sqlite3.connect(abs_db_path(s.db_path), timeout=1)
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
    get_player_query = """
    SELECT
      1
    FROM players
    WHERE Name = ?
    COLLATE NOCASE
    """

    db.execute(get_player_query, (player, ))
    playerstats = dict(db.fetchone())
    return playerstats


def rating_change(name, ladder, rating, factor, streak, gwon, glost, mplayed, mwon, mlost):
    """
    Updates rating of a player

    :param name:        Name of the player
    :param ladder:      String with ladder type
    :param rating:      Float with rating
    :param factor:      Float with public rating factor
    :param streak:      Int with new streak
    :param gwon:        Int with new games won
    :param glost:       Int with new games lost
    :param mplayed:     Int with new matches played
    :param mwon:        Int with new matches won
    :param mlost:       Int with new matches lost
    """
    if ladder == "limited":
        update_player_query = """
        UPDATE players
        SET
          LHiddenRating = ?,
          LPub_Factor = ?,
          LStreak = ?,
          LGamesPlayed = LGamesPlayed + 1,
          LGamesWon = LGamesWon + ?,
          LGamesLost = LGamesLost + ?,
          LMatchesPlayed = LMatchesPlayed + ?,
          LMatchesWon = LMatchesWon + ?,
          LMatchesLost = LMatchesLost + ?
        WHERE Name = ?
        COLLATE NOCASE
        """
    elif ladder == "constructed":
        update_player_query = """
        UPDATE players
        SET
          CHiddenRating = ?,
          CPub_Factor = ?,
          CStreak = ?,
          CGamesPlayed = CGamesPlayed + 1,
          CGamesWon = CGamesWon + ?,
          CGamesLost = CGamesLost+ ?,
          CMatchesPlayed = CMatchesPlayed + ?,
          CMatchesWon = CMatchesWon + ?,
          CMatchesLost = CMatchesLost + ?
        WHERE Name = ?
        COLLATE NOCASE
        """
    else:
        print "Unknown ladder error in rating change"
        return

    db.execute(update_player_query, (rating, factor, streak, gwon, glost, mplayed, mwon, mlost, name))
    database.commit()


def vouchplayer(vouched):
    """
    Call to vouch player - creates new entry in the database

    :param vouched:     Name of a player to be added
    """

    insert_player_query = """
    INSERT INTO players (
      Name,
      Created
    )
    VALUES (
      ?,
      date('now')
    )"""

    db.execute(insert_player_query, vouched)
    database.commit()


def player_exists(name):
    """
    Returns True if a player for the name exists

    :param name:        Player name
    :return:            True/False
    """
    player_exists_query = """
    SELECT
      1
    FROM players
    WHERE name=?
    COLLATE NOCASE
    """

    db.execute(player_exists_query, (name, ))
    player = db.fetchone()
    exists = player is not None
    return exists


def vouch_request_exists(name):
    """
    Returns True if a voucher for the name exists

    :param name:       Player name
    """
    vouche_request_exists_query = """
    SELECT
      1
    FROM vouchrequests
    WHERE name=?
    COLLATE NOCASE
    """

    db.execute(vouche_request_exists_query, (name, ))
    vouche_request = db.fetchone()
    exists = vouche_request is not None
    return exists


def insert_vouch_request(name, about):
    """
    Inserts a vouch

    :param name:       Player name
    :param about:      About the player
    """
    insert_vouch_request_query = """
    INSERT INTO vouch_requests
    VALUES (
      ?,
      ?
    )
    """

    db.execute(insert_vouch_request_query, (name, about))
    database.commit()


def delete_vouch_request(name):
    """
    Deletes a vouch

    :param name:       Player name
    """
    delete_vouch_request_query = """
    DELETE FROM vouch_requests
    WHERE name=?
    COLLATE NOCASE
    """

    db.execute(delete_vouch_request_query, (name, ))
    database.commit()


def confirm_vouch_req(name):
    """
    Confirms vouch request

    :param name:        Player name
    :return:            String with reply
    """
    if vouch_request_exists(name):
        vouchplayer(name)
        delete_vouch_request(name)
        reply = "{} vouched.".format(name)
    else:
        reply = "Couldn't vouch {}.".format(name)
    return reply


def deny_vouch_req(name):
    """
    Denies vouch request

    :param name:        Player name
    :return:            String with reply
    """
    if vouch_request_exists(name):
        delete_vouch_request(name)
        reply = "Vouch request by {} denied.".format(name)
    else:
        reply = "Couldn't find {} in vouch requests.".format(name)
    return reply


def makejudge(name):
    """
    Promotes player to a judge

    :param name:       Name of a player to be promoted
    """
    make_judge_query = """
    UPDATE players
    SET
      Judge = 1
    WHERE Name = ?
    COLLATE NOCASE
    """

    db.execute(make_judge_query, (name, ))
    database.commit()


"""
Dealing with games
"""


def getrunning():
    """
    Call to retrieve running games

    :return:            List with all the games
    """
    running_games_query = """
    SELECT
      *
    FROM games
    WHERE Running = 'Yes'
    """

    db.execute(running_games_query)
    running = db.fetchall()
    return running


def gamenewplayed(played, id):
    """
    Updates number of games played within an ID

    :param played:      New number of games played
    :param id:          ID of a game to be edited
    """
    update_games_played_query = """
    UPDATE games
    SET
      GamesPlayed = ?
    WHERE ID = ?
    """

    db.execute(update_games_played_query, (played, id))
    database.commit()


def closegame(id):
    """
    Sets game's state as not running

    :param id:          ID of a game to be edited
    """
    close_game_query = """
    UPDATE games
    SET
      Running = 'No'
    WHERE ID = ?
    """

    db.execute(close_game_query, (id, ))
    database.commit()


def getgameid(id):
    """
    Call to get game info by ID

    :param id:          ID of a game to be retrieved
    :return:            List with game info
    """
    get_game_query = """
    SELECT
      *
    FROM games
    WHERE ID = ?
    """

    db.execute(get_game_query, (id, ))
    id = db.fetchone()
    return id


def getgamenewid():
    """
    Call to get ID for new games

    :return:            Integer with ID
    """
    max_game_id_query = """
    SELECT
      MAX(ID) AS max_id
    FROM games
    """

    db.execute(max_game_id_query)
    game = db.fetchone()
    newid = int(game[0]) + 1
    return newid


def creategame(pod):
    """
    Creates new game

    :param pod:         List with: ID, "Yes", Games played,
                                   Pod size, GameType, Players 1-8
    """
    create_game_query = """
    INSERT INTO games
    VALUES (
      ?,
      ?,
      ?,
      ?,
      ?,
      ?,
      ?,
      ?,
      ?,
      ?,
      ?,
      ?,
      ?
    )"""

    db.execute(create_game_query, pod)
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
    ranked_players_query = """
    SELECT
      *,
      (
       SELECT
         COUNT(*)
       FROM players b
       WHERE b.ELO >= a.ELO
         AND Played > 0
      ) AS Rank
    FROM players a
    WHERE Played > 0
    ORDER BY ELO DESC
    """

    read = sql.read_sql(ranked_players_query, database)
    read = read.to_dict(orient='records')
    results = {"players": read}
    return results


def jsongames():
    """
    Creates dictionary with all games and their information

    :return:            Dictionary with all games and all their information
    """
    games_query = """
    SELECT
      *
    FROM games
    """

    rows = db.execute(games_query).fetchall()
    results = {"games": [dict(ix) for ix in rows]}
    return json.dumps(results)


def jsonplayer(player):
    """
    Creates dictionary with info about player specified by name

    :param player:      Name of a player to check
    :return:            Dictionary with player and it's information
    """
    ranked_player_query = """
    SELECT
      *,
      (
       SELECT
         COUNT(*)
       FROM players b
       WHERE b.ELO >= a.ELO
         AND Played > 0
      ) AS Rank
    FROM players a
    WHERE Name = ?
    COLLATE NOCASE
    """

    db.execute(ranked_player_query, (player, ))
    playerstats = {"player": [dict(db.fetchone())]}
    return playerstats


def jsongame(id):
    """
    Creates dictionary with an info about game specified by ID

    :param id:          ID of a game to check
    :return:            Dictionary with game and it's information
    """
    game_query = """
    SELECT
      *
    FROM games
    WHERE ID = ?
    COLLATE NOCASE
    """

    db.execute(game_query, (int(id), ))
    gamestats = {"game": [dict(db.fetchone())]}
    return gamestats


def jsonrequests():
    """
    Creates dictionary with all vouch requests

    :return:            Dictionary with all vouch requests
    """
    vouchers_query = """
    SELECT
      *
    FROM vouchrequests
    """

    rows = db.execute(vouchers_query).fetchall()
    result = {"vouchrequests": [dict(ix) for ix in rows]}
    return result


def vouchrequest(name, about):
    """
    Request a vouch

    :param name:        Name of a player for which to request vouch
    :param about:       About player
    :return:            String with reply
    """
    if vouch_request_exists(name):
        reply = "Tried to send vouch request, but you already requested vouch."
    elif player_exists(name):
        reply = "Tried to send vouch request, but you are already vouched."
    else:
        insert_vouch_request(name, about)
        reply = """Congratulations {}! Vouch request sent,
                   we will process it as soon as possible!""".format(name)
    return reply
