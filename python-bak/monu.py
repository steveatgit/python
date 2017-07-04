#!/usr/bin/env python

def menu(options):
	while True:
		input = raw_input("Enter the menu: ")
#		input = raw_input("enter an option (%s): "% '/'.join(options.keys()))
		if input in options:
#			if input == 'a':
#				__main__.a()
#			elif input == 'b'
#				__main__.b()
			return options[input]()
		elif input == 'q':
			return None
		else:
			print "Error enter, please enter again: "

