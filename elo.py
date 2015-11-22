import math

NameP1="iScrE4m"
RatingP1=1500
PlayedP1=0
WP1=0
LP1=0

NameP2="Arthur"
RatingP2=1500
PlayedP2=0
WP2=0
LP2=0

K1=0
K2=0

RatingA=0
RatingB=0
	

def match():
	if PlayedP1 == 0:
		K1 = 20
	elif PlayedP1 > 20:
		K1 = 15
	elif PlayedP1 > 40:
		K1 = 10
	else:
		print "Error setting K1\n"
	if PlayedP2 == 0:
		K2 = 20
	elif PlayedP2 > 20:
		K2 = 15
	elif PlayedP2 > 40:
		K2 = 10
	else:
		print "Error setting K2\n"
	E1 = (1.0 / (1.0 + pow(10, ((RatingP2 - RatingP1) / 400))))
	print E1
	E2 = 1 - E1
	print E2
	winner = raw_input("Who won?\n")
	if winner == "1":
		print RatingP1
		print K1
		print E1
		RatingA = (RatingP1 + K1 * (1 - E1))
		print RatingA
		RatingB = (RatingP2 + K2 * (0 - E2))
		print RatingB
	elif winner == "2":
		RatingA = (RatingP1 + K1 * (0 - E1))
		RatingB = (RatingP2 + K2 * (1 - E2))
	else:
		print "Enter 1 or 2\n"
		match()

if __name__ == '__main__':
	match()