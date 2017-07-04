#!/usr/bin/env python

class Person(object):
	population = 0
	def __init__(self,
				 given_name = 'no given name',
				 family_name = 'no family name'):
		self.given_name = given_name
		self.family_name = family_name
		self._secret = 'shh'
		self.__very_secret = 'shh!'
		self.population += 1

	def get_given_name(self):
		return self.given_name

	def set_given_name(self, new_name):
		self.given_name = new_name

	def fullname(self):
		return "%s %s" % (self.given_name, self.family_name)
	
	def current_population(self):
		return self.population

	def __del__(self):
		self.population -= 1
		print "I'm dead!"

class Employee(Person):
	def __init__(self, given_name, family_name, id_number):
		Person.__init__(self, given_name, family_name)
		self.id_number = id_number

