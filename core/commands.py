#!/usr/bin/env python

"""
Copyright (c) 2016 iScrE4m@gmail.com

To use the code, you must contact the author directly and ask permission.
"""

from . import database as db


def handle(auth, queues, channel, msg):
    """
    Command handler

    :param auth:            AUTH of a player sending command
    :param queues:          List of queues objects
    :param channel:         Channel, where command was received
    :param msg:             Message received
    :return:                Command to execute
                                To prevent sending protocol instance and to not act if invalid command was entered
    """

    command = msg[1:].split()
    name = command[0]
    args = command[1:]
    total_queued = []
    for instance in queues:
        total_queued.append(instance.QueuedPlayers)
    """
    command                 List from message stripped of command character
    name                    Name of the command entered by user
    args                    Arguments of the command
    total_queued            List of all the players currently queued in any queue
    """

    if name == "join":
        reply = join(auth, total_queued, queues, args)
        return lambda: self.msg(reply, channel)
    elif name == "":
        return

    # Command not recognized
    else:
        return lambda: None


def join(auth, total_queued, queues, args):
    """
    Join a queue

    IRC usage: '.join QueueName'

    :param auth:            Auth of the player
    :param total_queued:    List of all the players currently queued in any queue
    :param queues:          List with instances of queues
    :param args:            Name of queue to join - also queue_key
    :return:                String with reply
    """
    queue_key = args[0]
    games = db.getrunning()
    if auth is not None:
        if auth['Name'] not in total_queued and auth['Name'] not in games:
            queue_key.add(auth['Name'])
            if queue_key.check() is True:
                # TODO Figure out how to deal with starting a pod
                reply = ""
            else:
                to_start = str(queue_key.NeededToStart - queue_key.QueuedPlayers)
                reply = "%s joined a queue. %s players to start %s. Type .join to join" % (auth['Name'], to_start, queue_key.GameType)
        else:
            reply = "You are already in a queue or in a game"
    elif queue_key in queues:
        reply = "Enter a valid queue name (Draft, Sealed2, Sealed4, Sealed, Standard)"
    else:
        reply = "You can't join a game, if you aren't vouched"

    return reply
