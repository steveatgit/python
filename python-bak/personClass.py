class Person:
	Count = 0
	def __init__(self, name, age):
		Person.Count += 1
		self.name = name
		self.age = age

p = Person("peter", 25)
p1 = Person("Tom", 10)

print Person.Count
print p.name
print p.age
