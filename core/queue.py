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


class Draft:
    def __init__(self):
        self.GameType = "Draft"
        self.leaderboard = "limited"
        self.NeededToStart = 8
        self.QueuedPlayers = []

    def add(self, player):
        self.QueuedPlayers.append(player)

    def remove(self, player):
        self.QueuedPlayers.remove(player)

    def check(self):
        if len(self.QueuedPlayers) == self.NeededToStart:
            return True
        else:
            return False


class Sealed2:
    def __init__(self):
        self.GameType = "Sealed duel"
        self.leaderboard = "limited"
        self.NeededToStart = 2
        self.QueuedPlayers = []

    def add(self, player):
        self.QueuedPlayers.append(player)

    def remove(self, player):
        self.QueuedPlayers.remove(player)

    def check(self):
        if len(self.QueuedPlayers) == self.NeededToStart:
            return True
        else:
            return False


class Sealed4:
    def __init__(self):
        self.GameType = "Sealed 4 players"
        self.leaderboard = "limited"
        self.NeededToStart = 4
        self.QueuedPlayers = []

    def add(self, player):
        self.QueuedPlayers.append(player)

    def remove(self, player):
        self.QueuedPlayers.remove(player)

    def check(self):
        if len(self.QueuedPlayers) == self.NeededToStart:
            return True
        else:
            return False


class Sealed:
    def __init__(self):
        self.GameType = "Sealed Classic"
        self.leaderboard = "limited"
        self.NeededToStart = 8
        self.QueuedPlayers = []

    def add(self, player):
        self.QueuedPlayers.append(player)

    def remove(self, player):
        self.QueuedPlayers.remove(player)

    def check(self):
        if len(self.QueuedPlayers) == self.NeededToStart:
            return True
        else:
            return False


class Standard:
    def __init__(self):
        self.GameType = "Standard"
        self.leaderboard = "constructed"
        self.NeededToStart = 2
        self.QueuedPlayers = []

    def add(self, player):
        self.QueuedPlayers.append(player)

    def remove(self, player):
        self.QueuedPlayers.remove(player)

    def check(self):
        if len(self.QueuedPlayers) == self.NeededToStart:
            return True
        else:
            return False
