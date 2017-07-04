#given name, family name, email, phone

# a - add new person
# l - list all people
# q - quit
# f - find people (search through names + email)
# w - write info to disk
# r - read info from disk

# blog.lerner.co.il (reduce fun)

#!/usr/bin/env python

people = []
filename = '/tmp/people'

def write_data():
	
while True:
	user_choice = raw_input("enter you choice:")

	if user_choice == 'q':
		break
	elif user_choice == 'a'
		given_name
		people.append(new_person)
		
		#DRY -- don't repeat youself
		new_person = {}
		for field in 
	elif user_choice == 'w':
		f = open(filename)
		for person in people:
			print("%s\t")
		f.close()
	elif user_choice == 'r':
		f = open(filename)	
		people = []	
		for line in f:
			given_name, family_name, email, phone_number = line.split()

			new_person = {'given_name':given_name,
						  'family_name':}
	elif user_choice = 	'f':

