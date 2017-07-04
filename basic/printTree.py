#!/usr/bin/env python

print "enter the height:"
height = input()
space = height - 1
i = 1
while i <= 2*height:
   print space*" " + i*"*"
   i = i+2
   space = space - 1

truck = height/3
j = 0
while j<truck:
   print (height-1)*" " + "*"
   j = j+ 1
   
   
C:\Users\wqu\code>python tree.py
enter the height:
3
  *
 ***
*****
  *

C:\Users\wqu\code>python tree.py
enter the height:
8
       *
      ***
     *****
    *******
   *********
  ***********
 *************
***************
       *
       *
