class SchoolMember:
	def __init__(self, name, age):
		self.name = name
		self.age = age
		print '''initialize the 
school member'''

	def tell(self):
		print "name is %s, age is %d" % (self.name, self.age)

class Teacher(SchoolMember):
	def __init__(self, name, age, salary):
		SchoolMember.__init__(self, name, age)
		self.salary = salary
		print "initialize the teacher clas"

	def tell(self):
		SchoolMember.tell(self)
		print "salary is %d" % self.salary

s1 = SchoolMember("peter", 25)
t1 = Teacher("Brian", 40, 10000)

members = [s1, t1]
for m in members:
	m.tell()
