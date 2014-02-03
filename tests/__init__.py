# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, see
# <http://www.gnu.org/licenses/>.


"""

Some unittests for brine

author: Christopher O'Brien  <obriencj@gmail.com>

"""


from brine import function_unnew, code_unnew
from brine import brine, unbrine
from cStringIO import StringIO
from pickle import Pickler, Unpickler

import new
import unittest


def pickle_unpickle(value):
    buffer = StringIO()
    Pickler(buffer).dump(value)
    buffer = StringIO(buffer.getvalue())
    return Unpickler(buffer).load()


class Obj(object):
    # This is just a sample class we can use for bound method pickling
    # tests
    def __init__(self, value):
        self.value = value
    def get_value(self):
        return self.value
    def set_value(self, value):
        self.value = value


def make_pair(value):
    shared = [value]
    def get_value():
        return shared[0]
    def set_value(value):
        shared[0] = value
    return get_value, set_value


def make_adder(by_i=0):
    return lambda x=0: x+by_i


class TestUnnew(unittest.TestCase):

    def test_adder_duplication(self):
        func_a = make_adder(8)
        func_b = new.function(*function_unnew(func_a))

        self.assertEqual(func_a(), func_b())
        self.assertEqual(func_a(5), func_b(5))


    def test_adder_code_duplication(self):
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


class TestBrine(unittest.TestCase):

    def test_brine_function(self):

        # this is the function we'll be duplicating.
        func_a = make_adder(8)

        # run it through pickle/unpickle to duplicate it
        func_b = unbrine(pickle_unpickle(brine(func_a)))

        self.assertEqual(func_a(), func_b())
        self.assertEqual(func_a(5), func_b(5))


    def test_brine_function_dict(self):
        func_a = make_adder(8)
        func_b = make_adder(9)

        assert(func_a() == 8)
        assert(func_b() == 9)

        l = { "func_a": func_a, "func_b": func_b }
        l = unbrine(pickle_unpickle(brine(l)))
        func_a2 = l["func_a"]
        func_b2 = l["func_b"]

        assert(func_a(5) == func_a2(5))
        assert(func_b(5) == func_b2(5))


    def test_brine_function_list(self):
        func_a = make_adder(8)
        func_b = make_adder(9)

        assert(func_a() == 8)
        assert(func_b() == 9)

        l = [func_a, func_b]
        l = unbrine(pickle_unpickle(brine(l)))

        assert(type(l) == list)
        func_a2, func_b2 = l

        assert(func_a(5) == func_a2(5))
        assert(func_b(5) == func_b2(5))


    def test_brine_function_tuple(self):
        func_a = make_adder(8)
        func_b = make_adder(9)

        assert(func_a() == 8)
        assert(func_b() == 9)

        l = (func_a, func_b)
        l = unbrine(pickle_unpickle(brine(l)))

        assert(type(l) == tuple)
        func_a2, func_b2 = l

        assert(func_a(5) == func_a2(5))
        assert(func_b(5) == func_b2(5))


    def test_brine_pair_list(self):
        getter, setter = make_pair("Hello World")

        # show that they work as expected
        assert(getter() == "Hello World")
        setter("Tacos")
        assert(getter() == "Tacos")

        # now pickle/unpickle to create duplicates of the original
        # bound methods
        tmp = [getter, setter]
        tmp = unbrine(pickle_unpickle(brine(tmp)))
        bgetter, bsetter = tmp

        # show that these duplicates successfully pickled the
        assert(bgetter() == "Tacos")
        bsetter("Hello World")
        assert(bgetter() == "Hello World")

        assert(getter() == "Tacos")


    def test_brine_method_list(self):
        o = Obj("Hello World")

        # snag bound methods from our object
        getter = o.get_value
        setter = o.set_value

        # show that they work as expected
        assert(getter() == "Hello World")
        setter("Tacos")
        assert(getter() == "Tacos")

        # now pickle/unpickle to create duplicates of the original
        # bound methods
        tmp = [getter, setter]
        tmp = unbrine(pickle_unpickle(brine(tmp)))
        bgetter, bsetter = tmp

        # show that these duplicates successfully pickled the
        assert(bgetter() == "Tacos")
        bsetter("Hello World")
        assert(bgetter() == "Hello World")

        assert(getter() == "Tacos")


#
# The end.
