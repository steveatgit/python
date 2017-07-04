# print all lines of all files in a directory
# 
# [0] [0] 1st line of the first file
# [0] [1] 2nd line of the first file
# [0] [2] 3rd line of the first file
# [0] [3] 4th line of the first file
# [1] [0] 1st line of the second file
# [1] [1] 2nd line of the second file
# [1] [2] 3rd line of the second file
# [1] [3] 4th line of the second file
# 
# If you encounter any errors/problems in
# reading a file, then go on
# 
# But when you're done printing all of he lines
# print the problems

import os

dirname = '/etc/'
file_index = 0
dic = {}
files = os.listdir(dirname)
for one_file in files:
	file_index += 1
	line_index = 0
	try:
		with open one_file as fp:
			for line in fp.readlines():
				line_index += 1
				dict1 = {'[file_index][line_index]': line}
				dic.update(dict1)
	except:
		print "can't open file {}".format(file)
			
			
print dic


