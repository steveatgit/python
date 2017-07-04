import os
import cPickle
import sys

class Contacts:
	def __init__(self, name, phone, mail):
		self.name = name
		self.phone = phone
		self.mail = mail

	def update(self, name, phone, mail):
		self.name = name
		self.phone = phone
		self.mail = mail

	def display(self):
		print "name is %s, phone is %s, mail is %s" % (self.name, self.phone, self.mail)

mydata = os.getcwd() + os.sep + "contact.data"

while True:
	print "----------------------------------------"
	operation = raw_input("please input your operation add/delete/modify/search/all/exit:")
	if operation == "exit":
		sys.exit()
	
	if os.path.exists(mydata):
		if os.path.getsize(mydata) == 0:
			contacts = {}
		else:
			f = file(mydata)
			contacts = cPickle.load(f)
			f.close
	else:
		contacts = {}

	if operation == "add":
		while True:
			name = raw_input("input name(if exit back to choose operation):")
			if name == "exit":
				break
			if name in contacts:
				print "name has already existed, input a new name:"
				continue
			else:
				phone = raw_input("input phone:")
				mail = raw_input("input mail:")
				contacts[name] = Contacts(name, phone, mail)
				f = file(mydata, "w")
				cPickle.dump(contacts, f)
				f.close()
				print "add successfully"
				break
	elif operation == "delete":
		name = raw_input("input name you want to delete:")
		if name in contacts:
			del contacts[name]
			f = file(mydata)
			cPickle.dump(contacts, f)
			f.close()
			print "delete successfully"
		else:
			print "there is not the name in the contacts"
	elif operation == "modify":
		name = raw_input("input name you want to modify:")
		if name in contacts:
			phone = raw_input("input phone:")
			mail = raw_input("input mail:")
			contacts[name].update(name, phone, mail)
			f = file(mydata, "w")
			cPickle.dump(contacts, f)
			f.close()
		else:
			print "there is not the name in the contacts"
	elif operation == "search":
		name = raw_input("input name you want to search:")
		if name in contacts:
			contacts[name].display()
		else:
			print "there is no person named %s", name
	elif operation == "all":
		for name, contact in contacts.items():
			contact.display()
	else:
		print "unknown person"	
