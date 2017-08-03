#http://www.cnblogs.com/superxuezhazha/p/5746922.html
class Person(object):
    def __init__(self, name, gender):
        self.name = name
        self.gender = gender

class Student(Person):
    def __init__(self, name, gender, score):
        super(Student, self).__init__(name, gender)
        self.score = score
    def __repr__(self): #convert class instance to string 
        return '(Student: %s, %s, %s)' % (self.name, self.gender, self.score)
    #__repr__ = __str__

s = Student('Bob', 'mail', 88)
print s  #(Student: Bob, mail, 88)
