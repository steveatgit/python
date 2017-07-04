import cPickle

nameList = ["peter", "Tom", "Brian"]
f = file("data.data", "w")
cPickle.dump(nameList, f)
f.close()

del nameList

f = file("data.data")
newNameList = cPickle.load(f)
f.close()

print newNameList

