def func():
	global x
	print "x is", x
	x = 1

if __name__ == '__main__':
	x=10
	func()
	print "x is %d" % x
