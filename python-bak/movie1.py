#!/usr/bin/env python

movies = [
	['Captain Philips', 133, 'Paul greengrass'],
	['Gravity', 90, 'Alfono Cuaron'],
	['American Hustle', 138, 'DavidO. Russell']
]

look_for = raw_input("Enter a movie title to find: ")

for movie in movies:
	if look_for in movie[0]:
		print "Found your movie, '%s'," % movie[0]
		break
	else:
		print "Did not find any matches."
