#!/usr/bin/env python
"""
Copyright (c) 2016 iScrE4m@gmail.com

To use the code, you must contact the author directly and ask permission.

FIRST DRAFT of games handling
"""

import string
from . import database as db


class RunningGame:

    def __init__(self, fullqueue):
        self.GameType = fullqueue.GameType
        self.leaderboard = fullqueue.leaderboard
        self.players = fullqueue.QueuedPlayers
        self.create_game()
        fullqueue.QueuedPlayers = []

    def create_game(self):
        """
        Original function

        Problems:   Requires instance of bot protocol to send passwords to users
                    which means sending the instance to command handler too
                    (something I wanted to avoid, but I guess it's just adding
                    too much work)

        def startpod(self):
            global GameOpen
            global GameType
            global QueuedPlayers
            global runninggames
            id = db.getgamenewid()
            # Creating list for new database entry
            # with new ID, is running and 0 games played, Pod, Type
            pod = [id, "Yes", 0, NeededToStart, GameType]
            # Generating password to send to players
            password = ''.join(
                random.SystemRandom().choice(string.ascii_uppercase + string.digits)
                for _ in range(7))
            # Send each player the password and add him to database
            for queued in QueuedPlayers:
                pod.append(queued)
                msg = "Your {} has started. Password: '{}'".format(GameType, password)
                queued = queued.encode('UTF-8', 'replace')
                sendmsg(self, queued, msg)
            # If pod has fewer than 8 people,
            # this will make sure we give enough data to the database
            while len(pod) < 13:
                pod.append("None")
            db.creategame(pod)
            runninggames.append(str(id))
            msg = "Game #{} - {} is starting".format(id, GameType)
            # Close queuing
            GameOpen = 0
            GameType = 0
            QueuedPlayers = []
            return msg
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
        return reply

    def close_game(self):
        """
        I'm thinking way too much in copying way, not properly abusing object capabilities.
        I just wanted to commit outline of what join function should be calling

        // iScrE4m
        """
