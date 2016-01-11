#!/usr/bin/env python

"""
Copyright (c) 2016 iScrE4m@gmail.com

To use the code, you must contact the author directly and ask permission.
"""


def start_queues():
    """
    Creates instances of all queues

    :return:            Dictionary with queue instances
    """
    return {"Draft": Draft, "Sealed": Sealed, "Sealed2": Sealed2,"Sealed4": Sealed4,"Standard": Standard}


class Game(object):
    def __init__(self, game_type, leaderboard, needed_to_start):
        self.GameType = game_type
        self.leaderboard = leaderboard
        self.NeededToStart = needed_to_start
        self.QueuedPlayers = []
        # the list shouldn't be in the argument above because of list's mutable behavior:
        # https://gist.github.com/Janiczek/83f0a063f3a9dbadc0b2

    def add(self, player):
        self.QueuedPlayers.append(player)

    def remove(self, player):
        self.QueuedPlayers.remove(player)

    def check(self):
        if len(self.QueuedPlayers) == self.NeededToStart:
            return True
        else:
            return False

class Draft(Game):
    def __init__(self, game_type="Draft", leaderboard="limited", needed_to_start=8):
        super(Draft, self).__init__(game_type, leaderboard, needed_to_start)

class Sealed2(Game):
    def __init__(self, game_type="Sealed duel", leaderboard="limited", needed_to_start=2):
        super(Sealed2, self).__init__(game_type, leaderboard, needed_to_start)

class Sealed4(Game):
    def __init__(self, game_type="Sealed 4 players", leaderboard="limited", needed_to_start=4):
        super(Sealed4, self).__init__(game_type, leaderboard, needed_to_start)

class Sealed(Game):
    def __init__(self, game_type="Sealed Classic", leaderboard="limited", needed_to_start=8):
        super(Sealed, self).__init__(game_type, leaderboard, needed_to_start)

class Standard(Game):
    def __init__(self, game_type="Standard", leaderboard="constructed", needed_to_start=2):
        super(Standard, self).__init__(game_type, leaderboard, needed_to_start)
