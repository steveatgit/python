class Scoop():
	def __init__(self, flavor):
		self.flavor = flavor

# modify the Bowl class so it contains a max
# of 3 scoops
# (assuming you use add_scoops)

class Bowl():
	max_scoops = 3
	def __init__(self):
		self.scoops = []
	def add_scoops(self, *args):
		self.scoops += args[:self.max_scoops
								  - len(self.scoops)]
	def flavors(self):
		return [one_scoop.flavor
			     for one_scoop in self.scoops]

# BigBowl contains a max of 5 scoops

class BigBowl(Bowl):
	max_scoops = 5

s1 = Scoop('chocolate')
s2 = Scoop('vanilla')
s3 = Scoop('green tea')
s4 = Scoop('bread')
s5 = Scoop('coffee')
s6 = Scoop('cheese')


for one_scoop in [s1, s2, s3]:
	print one_scoop.flavor

b = Bowl()
b.add_scoops(s1, s2)
b.add_scoops(s3)
b.add_scoops(s4, s5)
print b.flavors()

bb = BigBowl()
bb.add_scoops(s1, s2)
bb.add_scoops(s3, s4)
bb.add_scoops(s5, s6)
print bb.flavors()

