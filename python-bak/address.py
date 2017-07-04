# given name, family name, email, phone

# a - add new person
# l - list all people
# q - quit
# f - find people (search through names + email)
# w - write info to disk
# r - read info from disk

# blog.lerner.co.il (reduce fun)

#!/usr/bin/env python
addresses = [
	['yue', 'gong', 'ygong@vmware.com', 1333],
	['yang', 'liu', 'yangl@vmware.com', 1222],
]

params = ['a','l', 'q', 'f', 'w', 'r']
param = raw_input("the param is: ")

if param in params[0]:
	for 

if param in params[1]:
	for address in addresses:
		print address[0], address[1], address[2], address[3]
  
