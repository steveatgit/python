class Person():
	print 'A'
	def __init__(self, name):
		print 'B'
		self.name = name
		Person.population += 1
Person.population = 0
print 'C'
print "Before, population = {}".format(Person.population)
p1 = Person('name1')
p2 = Person('name2')
print "After, population = {}".format(Person.population)
print 'D'

