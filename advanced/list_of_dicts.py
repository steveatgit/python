#given name, family name, phone number, email
#
#list of dicts
#
#q - quit
#a - add a new person to the DB. Meaning: ask 4 questions
#    and add the answers to the data structure
#l - list all people, all information, int the DB
#f - ask the user for a search string, and  then print
#	 all records which have this string anywhere *in*
#	 the name (give or family) or email address
#w - write all of the records to a file on disk (tab-separated/CSV)
#    (erasing previous versions of the file)
#r - read all records from disk into memory, replacing the earlier version of the DB

#!/usr/bin/env python

peoples = [{'given_name': 'wqu', 'family_name': 'Yantai', 'phone_number': '123456', 'email': 'wqu@vmware.com'}]

command = raw_input("please enter the command: ")

if command not in 'qalfwr' or command == 'q':
	exit
if command == 'a':
	given_name = raw_input('please enter the given name: ')
	family_name = raw_input('please enter the family name: ')
	phone_number = raw_input('please enter the phone number: ')
	email = raw_input('please enter the email: ')
	new_people = {'given_name': given_name, 'family_name': family_name, 'phone_number': phone_number, 'email': email}
	peoples.append(new_people)
elif command == 'l':
	print peoples
elif command == 'f':
	search_string = raw_input("please enter the searth string: ")
	for people in peoples:
		if search_string in people['given_name'] or people['family_name'] or people['email']:
			print "{}\t{}\t{}\t{}".format(people['given_name'], people['family_name'], people['phone_number'], people['email']) 
elif command == 'w':
	f = open('/tmp/people', 'w')
	title = ['given_name', 'family_name', 'phone_number', 'email']
	f.write('\t'.join(title))
	for people in peoples:
		info_people = [people['given_name'], people['family_name'], people['phone_number'], people['email']]
		f.write('\n' + '\t'.join(info_people))
	f.close()
elif command == 'r':
	f = open('/tmp/people', 'r')
	for line in f:
		(given_name, family_name,
		 phone, email) = line.strip().split('\t')
	peoples.append({'given_name': given_name, 'family_name': family_name, 'phone_number': phone, 'email': email})
	for people in peoples:
		print "{}\t{}\t{}\t{}".format(people['given_name'], people['family_name'], people['phone_number'], people['email']) 
		


	
	



