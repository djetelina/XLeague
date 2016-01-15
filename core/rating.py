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
    k = 12
    return k


def decide_e(player1, player2):
    """
    Decides E in ELO formula

    :param player1:     Integer with ELO of player 1
    :param player2:     Integer with ELO of player 2
    :return:            Integer with E
    """
    e = (1.0 / (1.0 + pow(10, (player2 - player1) / 400)))
    return e


def rating_diff(old, new):
    """
    Returns difference between old and new rating

    :param old:         Int with old rating
    :param new:         Int with new rating
    :return:            Int with rating difference
    """
    result = new - old
    return result


def newelo(winner, loser, ladder):
    """
    Calculates new rating for a player, must be called twice for each player

    :param winner:      Dictionary with Winner's info
    :param loser:       Dictionary with Loser's info
    :param ladder:      String with ladder type (limited/constructed)
    :return:            Dictionary with new rating information
    """
    winner_k = decide_k(winner)
    loser_k = decide_k(loser)
    if ladder == 'constructed':
        winner_elo = winner['Rating_H_C']
        loser_elo = loser['Rating_H_C']
    elif ladder == 'limited':
        winner_elo = winner['Rating_H_L']
        loser_elo = loser['Rating_H_L']
    else:
        return "Error: Invalid ladder type"
    winner_e = decide_e(winner_elo, loser_elo)
    loser_e = 1 - winner_e
    w_newelo = int(winner_elo + winner_k * (1 - winner_e))
    l_newelo = int(loser_elo + loser_k * (0 - loser_e))
    result = {
        'W': str(w_newelo),
        'W_difference': str(rating_diff(winner_elo, w_newelo)),
        'L': str(l_newelo),
        'L_difference': str(rating_diff(loser_elo, l_newelo))
    }
    return result


def match_confirmed(dic):
    # Fuck I forgot about implementing hidden rating, we will fight again later!
    """
    Call this when you have confirmed result of a match

    :param dic:     Dictionary with player names and scores
                        'auth'              : String with name of Player 1
                        'opponent'          : String with name of Player 2
                        'auth_score'        : String with score of player 1
                        'opponent_score'    : String with score of player 2
                        'ladder_type'       : String with ladder_type
    :return:        String with names, new ratings and rating changes
    """
    # Get player info from DB
    player_1 = db.getplayer(dic['auth'])
    player_2 = db.getplayer(dic['opponent'])
    # Get score of players
    p1_score = int(dic['auth_score'])
    p2_score = int(dic['opponent_score'])
    if p1_score > p2_score:
        result = newelo(player_1, player_2, dic['ladder_type'])
    elif p2_score > p1_score:
        result = newelo(player_2, player_1, dic['ladder_type'])
    else:
        reply = "Couldn't determine winner, try again"
        return reply
    w_newelo = result['W']
    l_newelo = result['L']
    w_diff = result['W_difference']
    l_diff = result['L_difference']
    reply = "New ratings: {}: {} [{}], {}: {} [{}]".format(dic['auth'], w_newelo,
                                                           w_diff, dic['opponent'],
                                                           l_newelo, l_diff
                                                           )
    return reply
