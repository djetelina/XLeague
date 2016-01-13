#!/usr/bin/env python
"""
Copyright (c) 2016 iScrE4m@gmail.com

To use the code, you must contact the author directly and ask permission.

This is not going to be used, not as an object anyway, more at line 67
"""

import string
import random
from . import database as db

running_games= []

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
        self.waiting_results= []
        self.create_game()
        full_queue.QueuedPlayers = []

    def create_game(self):
        """
        Original function -  startpod in app.py

        Problems:   Requires instance of bot protocol to send passwords to users
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
            BOTINSTANCE.msg(player, msg)
        while len(database_entry) < 13:  # TODO This has to be edited based on new database structure
            database_entry.append("None")
        db.creategame(database_entry)
        reply = "Game {} - {} is starting".format(id, self.GameType)
        running_games.append(self)
        return reply

    def report_result(self, auth, args):
        match_score_auth, match_score_opponent = args[0], args[1]
        opponent = args[2]
        if any(d['auth'] == auth for d in self.waiting_results):
            previous_opponent = (d['opponent'] for d in self.waiting_results where )
            # Fuck it, I should be using database for running games, not objects
            # TODO create running_games database
            reply = "You already have a result waiting for confirmation from "

        return reply
