import os
dirname = '/etc/'

problems = {}

for file_index, one_filename in enumerate(os.listdir(dirname)):
   try:
      for line_index, one_line in enumerate(open(dirname + one_filename)):
         print "[{}][{}] {}".format(file_index,
                                    line_index,
                                    one_line.rstrip())
   except IOError as e:
      problems[one_filename] = str(e)

for key, value in problems.items():
   print "{:23}: {}".format(key, value)

