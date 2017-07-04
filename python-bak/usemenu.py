#!/usr/bin/env python
from menu import menu

reload(menu)
def a():
	return "a!"

def b():
	return "b!"

#Advanced version
#result = menu({'a':a, 'b':b})

# Basic version
result = menu(['a', 'b'])

# When I do this, the user is asked to enter a, b, or q

# If it's q, we get None back
# if it's a, we get a back
# if it's b, we get b back

# if the user types someting else, we give an error message
# and aks them to try again

 
