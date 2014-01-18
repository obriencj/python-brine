
"""

Some unittests for brine

author: Christopher O'Brien  <siege@preoccupied.net>

"""



import new
from brine import function_unnew, code_unnew
from brine import brine_function, unbrine_function

import unittest




def make_adder(by_i=0):
    return lambda x=0: x+by_i



class TestAdderDuplication(unittest.TestCase):
    
    def testAdderDuplication(self):
        func_a = make_adder(8)
        func_b = new.function(*function_unnew(func_a))

        self.assertEqual(func_a(), func_b())
        self.assertEqual(func_a(5), func_b(5))


    def testAdderCodeDuplication(self):
        func_a = make_adder(8)
        
        # get the guts of the function and its code
        unfunc = function_unnew(func_a)
        uncode = code_unnew(unfunc[0])
        
        # make a new code from the guts of the original code
        unfunc[0] = new.code(*uncode)
        
        # make a new function with the new code
        func_b = new.function(*unfunc)

        self.assertEqual(func_a(), func_b())
        self.assertEqual(func_a(5), func_b(5))


        
class TestAdderPickling(unittest.TestCase):
    def testPickling(self):

        from cStringIO import StringIO
        from pickle import Pickler, Unpickler
        
        # this is the function we'll be duplicating.
        func_a = make_adder(8)
        
        buf = StringIO()
        
        # pickle func_a
        pi = Pickler(buf)
        pi.dump(brine_function(func_a))
        
        # unpickle func_b
        up = Unpickler(StringIO(buf.getvalue()))
        func_b = unbrine_function(up.load(), locals())
        
        self.assertEqual(func_a(), func_b())
        self.assertEqual(func_a(5), func_b(5))



def suite():
    loader = unittest.TestLoader()

    tests = [
        loader.loadTestsFromTestCase(TestAdderDuplication),
        loader.loadTestsFromTestCase(TestAdderPickling) ]

    return unittest.TestSuite(tests)



def main():
    runner = unittest.TextTestRunner()
    runner.run(suite())



if __name__ == '__main__':
    main()



#
# The end.
