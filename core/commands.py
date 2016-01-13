#!/usr/bin/env python
"""
Copyright (c) 2016 iScrE4m@gmail.com

To use the code, you must contact the author directly and ask permission.
"""

from . import database as db
from . import games


def handle(auth, queues, msg):
    """
    Command handler

    :param auth:            AUTH of a player sending command
    :param queues:          Dictionary with queue instances
    :param msg:             Message received
    :return:                String with reply
    """

    command = msg[1:].split()
    name = command[0]
    args = command[1:]
    total_queued = []
    for instance in queues.itervalues():
        total_queued.append(instance.QueuedPlayers)
    player = db.getplayer(auth)
    """
    command                 List from message stripped of the command character
    name                    Name of the command entered by user
    args                    Arguments of the command
    total_queued            List of all players currently queued in any queue
    player                  Dictionary with player information
    """

    if player['Vouched'] == 1:
        if name == "join":
            return join(auth, total_queued, queues, args)
        elif name == "leave":
            return leave(auth, queues)

    # Command not recognized
    else:
        return "The command doesn't exist or you don't have enough permissions"


def join(auth, total_queued, queues, args):
    """
    Join a queue

    IRC usage: '.join QueueName'

    :param auth:            Auth of the player
    :param total_queued:    List of all players currently queued in any queue
    :param queues:          Dictionary with queue instances
    :param args:            Name of queue to join - also queue_to_join
    :return:                String with reply
    """
    queue_name = args[0]
    if queue_name not in queues:  # searching in keys
        reply = "\n".join([
            "Enter a valid queue name",
            " (Draft, Sealed2, Sealed4, Sealed, Standard)"
        ])
    elif auth is not None:
        games = db.getrunning()
        if auth not in total_queued and auth not in games:
            queue_to_join = queues[queue_name]
            queue_to_join.add(auth)
            if queue_to_join.check() is True:
                # TODO Figure out how to deal with starting a pod
                reply = ""
            else:
                to_start = queue_to_join.to_start()
                reply = "\n".join([
                    "{} joined the {} queue. {} players to start",
                    " - type .join {} to join"
                ]).format(auth, args[0], to_start, args[0])
        else:
            reply = "You are already in a queue or in a game"
    else:
        reply = "You can't join a game if you aren't vouched"

    return reply


def leave(auth, queues):
    """
    Leaves the queue player is currently in

    IRC usage: '.leave'

    :param auth:        Auth of the player
    :param queues:      Dictionary with queue instances
    :return:            String with reply
    """
    for key, instance in queues.iteritems():
        if auth in instance.QueuedPlayers:
            instance.remove(auth)
            reply = "{} left the {} queue".format(auth, key)
            break
    else:
        reply = "You are not in any queue"
    return reply


def result(auth, player, args):
    for game in games.running_games:
        if auth in game.players:
            reply = game.report_result(auth, args)
            return reply
    else:
        reply = "You are not in any running game"
    return reply
