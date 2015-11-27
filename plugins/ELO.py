#!/usr/bin/env python

from __future__ import division

Klow = 10
Kmid = 15
Khigh = 20

def decideK(player):
	played = player['Played']
	if played <=20:
		K = Khigh
	elif played < 40:
		K = Kmid
	elif played  >= 40:
		K = Klow
	return K

def decideE(player1, player2):
	E = (1.0 / (1.0 + pow(10, (player2['ELO'] - player1['ELO']) / 400)))
	return E

def NewELO(Whose, Winner,Loser):
	NewELO = []
	WinnerK = decideK(Winner)
	LoserK = decideK(Loser)
	WinnerE = decideE(Winner, Loser)
	LoserE = 1 - WinnerE
	if Whose == "W":
		NewELO = int((Winner['ELO'] + WinnerK * (1 - WinnerE)))
	elif Whose == "L":
		NewELO = int((Loser['ELO'] + LoserK * (0 - LoserE)))
	return NewELO

def main():
	return

if __name__ == '__main__':
	main()