#!/usr/bin/env python

from __future__ import division

Klow = 10
Kmid = 15
Khigh = 20


# noinspection PyUnboundLocalVariable
def decidek(player):
    played = player['Played']
#    if played <= 20:
#        k = Khigh
#    elif played < 40:
#        k = Kmid
#    elif played >= 40:
#        k = Klow
    k = 32
    return k


def decidee(player1, player2):
    e = (1.0 / (1.0 + pow(10, (player2['ELO'] - player1['ELO']) / 400)))
    return e


def newelo(whose, winner, loser):
    newelo = []
    winnerk = decidek(winner)
    loserk = decidek(loser)
    winnere = decidee(winner, loser)
    losere = 1 - winnere
    if whose == "W":
        newelo = int((winner['ELO'] + winnerk * (1 - winnere)))
    elif whose == "L":
        newelo = int((loser['ELO'] + loserk * (0 - losere)))
    return newelo


def main():
    return


if __name__ == '__main__':
    main()
