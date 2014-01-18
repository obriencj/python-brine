"""

Unit tests for brine.barrel

author: Christopher O'Brien  <obriencj@gmail.com>
license: LGPLv3

"""


from brine import function_unnew
from brine.barrel import BrineBarrel
from pickle import Pickler, Unpickler
from cStringIO import StringIO

import unittest


def make_incrementor(start=0, by=5):
    def incrementor():
        i = incrementor.i
        incrementor.i += by
        return i
    incrementor.i = start
    return incrementor


def make_recursive_adder(by_i=0):
    def add_i(x, rem=by_i):
        if rem > 0:
            return 1+add_i(x, rem-1)
        else:
            return x
    return add_i


def create_pair(default_val=None):
    shared = [default_val]
    def getter():
        return shared[0]
    def setter(val):
        shared[0] = val
    return getter, setter


class TestBarrel(unittest.TestCase):

    def test_anon_inner(self):

        fives = make_incrementor(0, 5)

        assert(callable(fives))
        assert(fives() == 0)
        assert(fives() == 5)
        assert(fives() == 10)

        ba = BrineBarrel()
        ba.add_function(fives, "fives")

        buf = StringIO()

        pi = Pickler(buf)
        pi.dump(ba)

        up = Unpickler(StringIO(buf.getvalue()))
        new_ba = up.load()
        new_fives = new_ba.get_function("fives", locals())

        assert(callable(new_fives))
        assert(new_fives() == 15)
        assert(new_fives() == 20)
        assert(new_fives() == 25)

        #assert(function_unnew(fives) == function_unnew(new_fives))


    def test_anon_recursive_inner(self):

        add_8 = make_recursive_adder(8)

        assert(callable(add_8))
        assert(add_8(10) == 18)

        ba = BrineBarrel()
        ba.add_function(add_8, "add_8")

        buf = StringIO()

        pi = Pickler(buf)
        pi.dump(ba)

        up = Unpickler(StringIO(buf.getvalue()))
        new_ba = up.load()
        new_ba.rename_function("add_8", "new_add_8")
        new_add_8 = new_ba.get_function("new_add_8", locals())

        assert(callable(new_add_8))
        assert(new_add_8(10) == 18)

        #assert(function_unnew(add_8) == function_unnew(new_add_8))


    def test_shared_cell(self):

        getter, setter = create_pair(8)
        assert(getter() == 8)

        setter(9)
        assert(getter() == 9)

        ba = BrineBarrel()
        ba.add_function(getter, "getter")
        ba.add_function(setter, "setter")

        buf = StringIO()

        pi = Pickler(buf)
        pi.dump(ba)

        up = Unpickler(StringIO(buf.getvalue()))
        new_ba = up.load()
        
        new_getter = new_ba.get_function("getter", locals())
        new_setter = new_ba.get_function("setter", locals())

        # check the initial value of the new pair
        assert(new_getter() == 9)

        # change the new pair and check that it did indeed change
        new_setter(10)
        assert(new_getter() == 10)

        # the old pair isn't effected by the new pair
        assert(getter() == 9)
        setter(7)
        assert(getter() == 7)

        # and show that we haven't effected our new pair
        assert(new_getter() == 10)
    

#
# The end.
