#!/usr/bin/python

def normalize(name):
	name = name[0].upper() + name[1:].lower()
	return name

if __name__ == '__main__':
	name = ['tom', 'LISA', 'baTT']
	name = map(normalize, name)
	print(name)
