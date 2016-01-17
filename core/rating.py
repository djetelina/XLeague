#!/usr/bin/env python
"""
Copyright (c) 2016 iScrE4m@gmail.com

To use the code, you must contact the author directly and ask permission.
"""

from __future__ import division
from . import database as db


class RatingChange:
    """
    TODO
    Non code logic:
    - For each match, change hidden rating
    - Adjust overall rating change to streak (breakpoints)
    - Send public rating (HiddenRating*PubFactor)
    - Write new data to database (rating, game, match, streak, factor)
    """

    def __init__(self, data):
        """
        Create this object when you have confirmed results
        then call .process

        :param data:     Dictionary with player names and scores
                            'auth'              : String with name of Player 1
                            'opponent'          : String with name of Player 2
                            'auth_score'        : String with score of player 1
                            'opponent_score'    : String with score of player 2
                            'ladder_type'       : String with ladder_type
        """
        self.player_1_db = db.getplayer(data['auth'])
        self.player_2_db = db.getplayer(data['opponent'])
        self.p1_score = data['auth_score']
        self.p2_score = data['opponent_score']
        if data['ladder_type'] == "constructed":
            self.player_1 = {
                'rating_start': self.player_1_db['CHiddenRating'],
                'rating_final': self.player_1_db['CHiddenRating'],
                'streak': self.player_1_db['CStreak'],
                'factor': self.player_1_db['CPub_Factor']
            }
            self.player_2 = {
                'rating_start': self.player_2_db['CHiddenRating'],
                'rating_final': self.player_2_db['CHiddenRating'],
                'streak': self.player_2_db['CStreak'],
                'factor': self.player_2_db['CPub_Factor']
            }
        elif data['ladder_type'] == "limited":
            self.player_1 = {
                'rating_start': self.player_1_db['LHiddenRating'],
                'rating_final': self.player_1_db['LHiddenRating'],
                'streak': self.player_1_db['LStreak'],
                'factor': self.player_1_db['LPub_Factor']
            }
            self.player_2 = {
                'rating_start': self.player_2_db['LHiddenRating'],
                'rating_final': self.player_2_db['LHiddenRating'],
                'streak': self.player_2_db['LStreak'],
                'factor': self.player_2_db['LPub_Factor']
            }
        self.player_1.update({
            'k': decide_k(self.player_1_db),
            'game_increase': 1,
            'gw_increase': 0,
            'gl_increase': 0,
            'match_increase': self.p1_score + self.p2_score,
            'mw_increase': self.p1_score,
            'ml_increase': self.p2_score
        })
        self.player_2.update({
            'k': decide_k(self.player_2_db),
            'game_increase': 1,
            'gw_increase': 0,
            'gl_increase': 0,
            'match_increase': self.p1_score + self.p2_score,
            'mw_increase': self.p2_score,
            'ml_increase': self.p1_score
        })
        self.winner = 0
        self.decide_winner()

    def decide_winner(self):
        if self.p1_score > self.p2_score:
            self.winner = 1
            self.player_1['gw_increase'] = 1
            self.player_2['gl_increase'] = 1
        elif self.p1_score < self.p2_score:
            self.winner = 2
            self.player_2['gw_increase'] = 1
            self.player_1['gl_increase'] = 1
        else:
            self.winner = 0

    def process(self):
        while self.p1_score > 0:
            self.p1_score -= 1
            self.elo(1)
        while self.p2_score > 0:
            self.p2_score -= 1
            self.elo(2)
        if self.winner == 1:
            self.player_1['streak'] += 1
            self.player_2['streak'] = 0
            if self.player_1['factor'] < 1:
                self.player_1['factor'] += 0.1
        elif self.winner == 2:
            self.player_2['streak'] += 1
            self.player_1['streak'] = 0
            if self.player_2['factor'] < 1:
                self.player_2['factor'] += 0.1
        # TODO streak processing
        p1_public = int(self.player_1['rating_final'] * self.player_1['factor'])
        p2_public = int(self.player_2['rating_final'] * self.player_2['factor'])
        p1_diff = rating_diff(self.player_1['rating_start'], self.player_1['rating_final'])
        p2_diff = rating_diff(self.player_2['rating_start'], self.player_2['rating_final'])
        reply = "New ratings: {}: {} [{}], {}: {} [{}]".format(self.player_1_db['Name'],
                                                               p1_public, p1_diff,
                                                               self.player_2_db['Name'],
                                                               p2_public, p2_diff)
        return reply

    def elo(self, winner):
        p1_e = decide_e(self.player_1['rating_final'], self.player_2['rating_final'])
        p2_e = 1 - p1_e
        if winner == 1:
            self.player_1['rating_final'] = (
                self.player_1['rating_final'] + self.player_1['k'] * (1 - p1_e)
            )
            self.player_2['rating_final'] = (
                self.player_2['rating_final'] + self.player_2['k'] * (0 - p2_e)
            )
        elif winner == 2:
            self.player_1['rating_final'] = (
                self.player_1['rating_final'] + self.player_1['k'] * (0 - p1_e)
            )
            self.player_2['rating_final'] = (
                self.player_2['rating_final'] + self.player_2['k'] * (1 - p2_e)
            )


def decide_k(player):
    """
    Decides K factor of a player

    :param player:      Dictionary with player info
    :return:            K factor

    More dynamic k factor code
    (currently testing what feels the most fair to our users)
    Klow = 10
    Kmid = 15
    Khigh = 20
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
    result = int(new - old)
    return result
