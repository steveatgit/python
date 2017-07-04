try:
	print 1/0
except ZeroDivisionError, e:
	print e
except:
	print "error or exception occured"
