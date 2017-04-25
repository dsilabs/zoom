

class MyObj(object):

    def __str__(self):
        return '__str__'

    def __repr__(self):
        return '__repr__'


obj = MyObj()

print('This is a {} response'.format(obj))
