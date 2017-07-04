#!/usr/bin/python

def triangles(N):
	L1 = [1,1]
	L0 = [1]
 	L = []
	i = 2
	for i in range(2, N):
		L.append(1)
		j = 1
		for j in range(N-1):
			L.append(L1[j-1] + L1[j])
		L.append(1)
		L0 = L1
		L1 = L

	for l in L1:
		print(l)

if __name__ == '__main__':
	triangles(5)
