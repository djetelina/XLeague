#!/usr/bin/env python
"""
Copyright (c) 2016 iScrE4m@gmail.com

To use the code, you must contact the author directly and ask permission.
"""

from __future__ import division

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


def newelo(whose, winner, loser):
    """
    Calculates new rating for a player, must be called twice for each player

    :param whose:       'W' or 'L' to know if we are calculating
                        rating for winner or loser
    :param winner:      Dictionary with Winner's info
    :param loser:       Dictionary with Loser's info
    :return:            Integer with final rating
    """
    result = []
    winnerk = decide_k(winner)
    loserk = decide_k(loser)
    winnere = decide_e(winner, loser)
    losere = 1 - winnere
    if whose == "W":
        result = int((winner['ELO'] + winnerk * (1 - winnere)))
    elif whose == "L":
        result = int((loser['ELO'] + loserk * (0 - losere)))
    return result
