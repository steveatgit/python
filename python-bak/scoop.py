#!/usr/bin/env python

# s = Scoop('chocolate')
# print s.flavor  #should print "chocolate"

class Scoop(object):
	def __init__(self, flavor):
		self.flavor = flavor

class Cone(object):
	max_scoops = 3
	def __init__(self):
		self.scoops = []
	def add_scoops(self, *scoops):
#		for scoop in scoops:
#			self.scoops.append(scoop)
		self.scoops.extend(scoops) 
#		self.scoops += scoops
		self.scoops = self.scoops[:self.max_scoops]
	def print_scoops(self):
		for scoop in self.scoops:
			print " %s " % scoop.flavor
	def scoops_string(self):
		print '\n'.join([scoop.flavor for scoop in self.scoops])

class BigCone(Cone):
	max_scoops = 5

if __name__ == '__main__':
	s1 = Scoop('chocolate')
#	print s1.flavor
	s2 = Scoop('vanilla')
	s3 = Scoop('coffee')
	s4 = Scoop('cherry')
	s5 = Scoop('apple')
	s6 = Scoop('peach')
	
	c = Cone()
	c.add_scoops(s1)
	c.add_scoops(s2, s3)
	c.add_scoops(s4)	
	
	c.print_scoops() #print out the three flavors
	
	print '\n'

	bc = BigCone()  # can take up to 5 scoops
	bc.add_scoops(s1,s2,s3,s4,s5,s6)
	bc.print_scoops()

