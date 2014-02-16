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
Unit tests for brine

:author: Christopher O'Brien  <obriencj@gmail.com>
:license: LGPL v.3
"""


from brine import brine, unbrine
from brine import code_unnew, code_new
from brine import function_unnew, function_new
from cStringIO import StringIO
from functools import partial
from pickle import Pickler, Unpickler

import unittest


class Obj(object):
    # This is just a sample class we can use for bound method pickling
    # tests
    def __init__(self, value):
        self.value = value
    def get_value(self):
        return self.value
    def set_value(self, value):
        self.value = value


def pickle_unpickle(value):
    buffer = StringIO()
    Pickler(buffer).dump(value)
    buffer = StringIO(buffer.getvalue())
    return Unpickler(buffer).load()


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
        func_b = function_new(*function_unnew(func_a))

        self.assertEqual(func_a(), func_b())
        self.assertEqual(func_a(5), func_b(5))


    def test_adder_code_duplication(self):
        func_a = make_adder(8)

        # get the guts of the function and its code
        unfunc = function_unnew(func_a)
        uncode = code_unnew(unfunc[0])

        # make a new code from the guts of the original code
        unfunc[0] = code_new(*uncode)

        # make a new function with the new code
        func_b = function_new(*unfunc)

        self.assertEqual(func_a(), func_b())
        self.assertEqual(func_a(5), func_b(5))


class TestBrine(unittest.TestCase):

    def test_brine_other(self):
        # test that brine doesn't break normal pickling of non-function
        # types (builtins, types, simple values)

        data_built = ( map, zip, globals )
        data_types = ( type, tuple, int )
        data_stuff = (501, 5.01, "Hello", set([1, 3, 5, 7]))
        data = [data_built, data_types, data_stuff]

        # duplicate is all via brine/pickle/unpickle/unbrine
        ndata = unbrine(pickle_unpickle(brine(data)))
        ndata_built = ndata[0]
        ndata_types = ndata[1]
        ndata_stuff = ndata[2]

        self.assertEqual(data_built, ndata_built)
        self.assertEqual(data_types, ndata_types)
        self.assertEqual(data_stuff, ndata_stuff)


    def test_brine_function(self):
        # this is the function we'll be duplicating.
        func_a = make_adder(8)

        # run it through pickle/unpickle to duplicate it
        func_b = unbrine(pickle_unpickle(brine(func_a)))

        self.assertEqual(func_a(), func_b())
        self.assertEqual(func_a(5), func_b(5))


    def test_brine_function_dict(self):
        # test brinind of a function embedded in a dict

        func_a = make_adder(8)
        func_b = make_adder(9)

        self.assertEqual(func_a(), 8)
        self.assertEqual(func_b(), 9)

        l = { "func_a": func_a, "func_b": func_b }
        l = unbrine(pickle_unpickle(brine(l)))
        func_a2 = l["func_a"]
        func_b2 = l["func_b"]

        self.assertEqual(func_a(5), func_a2(5))
        self.assertEqual(func_b(5), func_b2(5))


    def test_brine_function_list(self):
        # test brining of a function embedded in a list

        func_a = make_adder(8)
        func_b = make_adder(9)

        self.assertEqual(func_a(), 8)
        self.assertEqual(func_b(), 9)

        l = [func_a, func_b]
        l = unbrine(pickle_unpickle(brine(l)))

        self.assertEqual(type(l), list)
        func_a2, func_b2 = l

        self.assertEqual(func_a(5), func_a2(5))
        self.assertEqual(func_b(5), func_b2(5))


    def test_brine_function_tuple(self):
        # test brining of a function embedded in a tuple

        func_a = make_adder(8)
        func_b = make_adder(9)

        self.assertEqual(func_a(), 8)
        self.assertEqual(func_b(), 9)

        l = (func_a, func_b)
        l = unbrine(pickle_unpickle(brine(l)))

        self.assertEqual(type(l), tuple)
        func_a2, func_b2 = l

        self.assertEqual(func_a(5), func_a2(5))
        self.assertEqual(func_b(5), func_b2(5))


    def test_brine_pair_list(self):
        # test that a pair of function sharing a clusure come out
        # sharing the same dup'd closure

        getter, setter = make_pair("Hello World")

        # show that they work as expected
        self.assertEqual(getter(), "Hello World")
        setter("Tacos")
        self.assertEqual(getter(), "Tacos")

        # now pickle/unpickle to create duplicates of the original
        # functions
        tmp = [getter, setter]
        tmp = unbrine(pickle_unpickle(brine(tmp)))
        bgetter, bsetter = tmp

        # show that these duplicates successfully pickled the
        self.assertEqual(bgetter(), "Tacos")
        bsetter("Hello World")
        self.assertEqual(bgetter(), "Hello World")

        self.assertEqual(getter(), "Tacos")


    def test_brine_method_list(self):
        o = Obj("Hello World")

        # snag bound methods from our object
        getter = o.get_value
        setter = o.set_value

        # show that they work as expected
        self.assertEqual(getter(), "Hello World")
        setter("Tacos")
        self.assertEqual(getter(), "Tacos")

        # now pickle/unpickle to create duplicates of the original
        # bound methods
        tmp = [getter, setter]
        tmp = unbrine(pickle_unpickle(brine(tmp)))
        bgetter, bsetter = tmp

        # show that these duplicates successfully pickled the
        self.assertEqual(bgetter(), "Tacos")
        bsetter("Hello World")
        self.assertEqual(bgetter(), "Hello World")

        self.assertEqual(getter(), "Tacos")


    def test_brine_partial_function(self):
        # test that brining a partial of a function works

        add_x_y = lambda x, y: (x + y)
        add_8 = partial(add_x_y, 8)

        self.assertEqual(type(add_8), partial)
        self.assertEqual(add_8(10), 18)

        new_add_8 = unbrine(pickle_unpickle(brine(add_8)))

        self.assertNotEqual(add_8, new_add_8)
        self.assertEqual(type(new_add_8), partial)
        self.assertEqual(add_8(11), 19)


    def test_brine_partial_method(self):
        # test that brining of a partial of a method works

        o = Obj("Hungry")

        self.assertEqual(o.get_value(), "Hungry")

        getter = o.get_value
        give_cake = partial(o.set_value, "Cake")
        give_taco = partial(o.set_value, "Taco")

        give_cake()
        self.assertEqual(getter(), "Cake")
        give_taco()
        self.assertEqual(getter(), "Taco")

        tmp = [getter, give_cake, give_taco]
        tmp = unbrine(pickle_unpickle(brine(tmp)))
        ngetter, ngive_cake, ngive_taco = tmp

        self.assertEqual(ngetter(), "Taco")
        ngive_cake()
        self.assertEqual(ngetter(), "Cake")

        # check that they're not interfering with one-another
        self.assertNotEqual(ngetter(), getter())

        ngive_taco()
        self.assertEqual(ngetter(), "Taco")


#
# The end.
