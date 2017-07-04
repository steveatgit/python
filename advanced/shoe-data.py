# Turn shoe-data.txt into a list of dict
# 
# print [
# {'brand': 'Adidas',
#  'color': 'orange',
#  'size': '43'},
# ...
# ]

#!/usr/bin/env python

shoes = [ ]
filename = 'exercise-files/shoe-data.txt'

def line_to_list(fp):
	for line in fp.readlines():
		brand, color, size = line.strip().split('\t')
		shoe_dic = {'brand': brand, 'color': color, 'size': size}
		shoes.append(shoe_dic)

with open(filename) as fp:
	line_to_list(fp)

# sort the shoes in order of brand
# (alphabetical order by brand)

def sort_by_brand(shoe):
	return shoe['brand']
def sort_by_brand_and_size(shoe):
	return shoe['brand'], shoe['size']

shoes.sort(key=sort_by_brand_and_size)

print '\n'.join([str(shoe) for shoe in shoes])
