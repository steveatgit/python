test = '''\
this is a test for file 
author: wqu 
date:   2015/3/29 
'''

f = file("test.log", "w")
f.write(test)
f.close()

f = file("test.log")

while True:
	line = f.readline()
	if len(line) == 0:
		break
	print line

f.close()
