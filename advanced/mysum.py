# Define "mysum" which takes one paramter (a list, tuple, or set,
# 													  containing integers)
# and returns the sum of these integers.
# 
# Do ot se the built-in 'sum' function!

#!/usr/bin/env python

def mysum(box):
	sum = 0
	for num in box:
		sum += num
	print "the sum is {}".format(sum)

if __name__ == '__main__':
	#box = raw_input("please enter some data(list or tuple or set):")
	box = [10, 20, 30]
	mysum(box)
