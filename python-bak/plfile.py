#! /usr/bin/env python

def plword(word):
	if word[0] in 'aeiou':
		return word + 'way'
	else:
		return word[1:] + word[0] + 'ay'

filename = ''

print ' '.join([plword(word) for word in open(filename).read().split(':')])
