#!/usr/bin/env python
"""
Copyright (c) 2016 iScrE4m@gmail.com

To use the code, you must contact the author directly and ask permission.
"""

import string
import random
from . import database as db
from . import rating
from ..import settings as s

running_games = []


class RunningGame:
    """
    Actions to take:

    * Create game from pod
    * Record result
        * Keep track of opponents already matched together
        * Only record once both players verify results
        * Judge can force result record
    * Close game
    """

    def __init__(self, full_queue):
        self.GameType = full_queue.GameType
        self.leaderboard = full_queue.leaderboard
        self.players = full_queue.QueuedPlayers
        self.matches_played = []
        self.waiting_results = []
        self.create_game()
        full_queue.QueuedPlayers = []

    def create_game(self):
        """
        Original function -  startpod in app.py

        Problems:   Requires instance of bot protocol to send passwords to users
                    and for a reply message (__init_ can't return)
                    which means sending the instance to command handler too
                    (something I wanted to avoid, but I guess it's just adding
                    too much work)
        """
        new_id = db.getgamenewid()
        database_entry = [new_id, ]  # TODO This has to be filled based on new database structure
        password = ''.join(
                random.SystemRandom().choice(string.ascii_uppercase + string.digits)
                for _ in range(7))
        for player in self.players:
            database_entry.append(player)
            msg = "{} you were in queue for has started. Password: '{}'".format(self.GameType, password)
            BOTINSTANCE.msg(player, msg)  # TODO send bot instance
        while len(database_entry) < 13:  # TODO This has to be edited based on new database structure
            database_entry.append("None")
        db.creategame(database_entry)
        reply = "Game {} - {} is starting".format(id, self.GameType)
        running_games.append(self)
        BOTINSTANCE.msg(s.channel, reply)  # TODO send bot instance

    def report_result(self, auth, args):
        """
        Handles reports of results

        :param auth:    String with name of player sending result
        :param args:    Arguments of his command
        :return:        String with reply
        """
        # Iterate over results waiting for confirmation
        for d in self.waiting_results:
            # Check if player only didn't submit another result
            if auth == d['auth']:
                previous_opponent = d['opponent']
                reply = "You already have a result waiting for confirmation from {}".format(previous_opponent)
                break
            # Check if message is confirmation
            elif auth == d['opponent']:
                reply = self.confirm_result(auth, args)
                break
        # Queue result as waiting for confirmation
        else:
            match_score_auth, match_score_opponent = args[0], args[1]
            opponent = args[2]
            waiting_result = {
                'auth': auth,
                'opponent': opponent,
                'auth_score': match_score_auth,
                'opponent_score': match_score_opponent
            }
            self.waiting_results.append(waiting_result)
            reply = "Result submitted, waiting for {} to confirm".format(opponent)
        return reply

    def confirm_result(self, auth, args):
        """
        Handles result waiting for confirmation

        :param auth:    String with name of player confirming result
        :param args:    Arguments of his command
        :return:        String with reply
        """
        for d in self.waiting_results:
            if d['opponent'] == auth:
                wanted_dictionary = d
                self.waiting_results.remove(d)
                break
        else:
            reply = "Unexpected error when confirming result"
            return reply
        match_score_auth, match_score_opponent = args[0], args[1]
        opponent = args[2]
        compared_dictionary = {
            'auth': opponent,
            'opponent': auth,
            'auth_score': match_score_opponent,
            'opponent_score': match_score_auth
        }
        if compared_dictionary == wanted_dictionary:
            reply = rating.match_confirmed(wanted_dictionary)
        else:
            reply = "Your reported results didn't match. Try again"
        return reply
