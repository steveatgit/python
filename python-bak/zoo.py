#!/usr/bin/env python

class Animal(object):
	def __init__(self, name, color, leg_number):
		self.name = name
		self.color = color
		self.leg_number = leg_number
	def __repr__(self):
		return "%s %s (%s legs)" % (self.name, self.color, self.leg_number)

class Cage(object):
	animals = []
	def __init__(self, cage_ID):
		self.cage_ID = cage_ID
	def add_animals(self, *animals):
		self.animals += animals
	def __repr__(self):
		output =  "\nCage ID %s\n" % self.cage_ID
		output += '\n'.join(['\t' + str(animal)
							for animal in self.animals])
#		for animal in self.animals:
#			output += "\t%s\n" %s animal
		return output
	def animals_of_color(self, color):
		return '\n'.join([str(animal) for animal in self.animals
						 if animal.color == color])
	def animals_with_legs(self, leg_number):
		return '\n'.join([str(animal) for animal in self.animals
						  if animal.leg_number = number_leg])	
	def number_of_leg(self):
		return sum([animal.number_of_legs
					for animal in self.animals])
class Zoo(object):
	cages = []
    def add_cages(self, *cages):
		self.cages += cages
#	def __repr__(self):
#		return '\n'.join([str(animal) for animal in])	
	def animals_of_color(self, color):
		return  '\n'.join([cage.animals_of_color(color)
						   for cage
						   in self.cages])
	def animals_of_with_legs(leg_number):
		return '\n'.join([cage.animals_with_legs(leg_number)
						  for cage
						  in self.cages])
	def animal_of_legs():
		return '\n'.join([cage.animals_of_legs()
						  for cage
						  in self.cages])

if __name__ == '__main__':
	sheep1 = Animal('sheep', 'white', 4)
	sheep2 = Animal('sheep', 'black', 4)
	wolf = Animal('wolf', 'black', 4)
	snake = Animal('snake', 'brown', 0)

	c1 = Cage(1)
	c1.add_animals(sheep1, sheep2)
	print c1

	c2 = Cage(2)
	c2.add_animals(wolf, snake)
	print c2

	z = Zoo()
	z.add_cages(c1, c2)

	print '-' * 60
	print z.animals_of_color('black')
	
	print '-' * 60
	print z.animals_with_legs(4)
	
	print '-' * 60
	print z.number_of_legs()

#	print z #print all animals, all cages
 
