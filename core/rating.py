#!/usr/bin/env python
"""
Copyright (c) 2016 iScrE4m@gmail.com

To use the code, you must contact the author directly and ask permission.
"""

from __future__ import division
from . import database as db

Klow = 10
Kmid = 15
Khigh = 20


def decide_k(player):
    """
    Decides K factor of a player

    :param player:      Dictionary with player info
    :return:            K factor

    More dynamic k factor code
    (currently testing what feels the most fair to our users)

    played = player['Played']
    if played <= 20:
        k = Khigh
    elif played < 40:
        k = Kmid
    elif played >= 40:
        k = Klow
    """
    k = 32
    return k


def decide_e(player1, player2):
    """
    Decides E in ELO formula

    :param player1:     Dictionary with player 1 info
    :param player2:     Dictionary with player 2 info
    :return:
    """
    e = (1.0 / (1.0 + pow(10, (player2['ELO'] - player1['ELO']) / 400)))
    return e


def newelo(winner, loser):
    """
    Calculates new rating for a player, must be called twice for each player

    :param winner:      Dictionary with Winner's info
    :param loser:       Dictionary with Loser's info
    :return:            Integer with final rating
    """
    winner_k = decide_k(winner)
    loser_k = decide_k(loser)
    winner_e = decide_e(winner, loser)
    loser_e = 1 - winner_e
    result = {
        'W': int(winner['ELO'] + winner_k * (1 - winner_e)),
        'L': int(loser['ELO'] + loser_k * (0 - loser_e))
    }
    return result


def match_confirmed(dic):
    player_1 = db.getplayer(dic['auth'])
    p1_score = int(dic['auth_score'])
    player_2 = db.getplayer(dic['opponent'])
    p2_score = int(dic['opponent_score'])
    if p1_score > p2_score:
        result = newelo(player_1, player_2)
        # TODO Need to regain focus before continuing
        reply = result
    elif p2_score > p1_score:
        result = newelo(player_2, player_1)
        reply = result
    else:
        reply = "Couldn't determine winner, try again"
    return reply
