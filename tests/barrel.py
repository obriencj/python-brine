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
Unit tests for brine.barrel

:author: Christopher O'Brien  <obriencj@gmail.com>
:license: LGPL v.3
"""


from brine.barrel import Barrel
from cStringIO import StringIO
from functools import partial
from pickle import Pickler, Unpickler

import unittest


from . import make_adder, make_pair, pickle_unpickle, Obj


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


class TestBarrel(unittest.TestCase):

    def test_anon_inner(self):

        fives = make_incrementor(0, 5)

        self.assertTrue(callable(fives))
        self.assertEqual(fives(), 0)
        self.assertEqual(fives(), 5)
        self.assertEqual(fives(), 10)

        ba = Barrel()
        ba["fives"] = fives

        new_ba = pickle_unpickle(ba)

        new_fives = new_ba["fives"]

        self.assertTrue(callable(new_fives))
        self.assertEqual(new_fives(), 15)
        self.assertEqual(new_fives(), 20)
        self.assertEqual(new_fives(), 25)


    def test_anon_recursive_inner(self):

        add_8 = make_recursive_adder(8)

        self.assertTrue(callable(add_8))
        self.assertEqual(add_8(10), 18)

        ba = Barrel()
        ba["add_8"] = add_8

        new_ba = pickle_unpickle(ba)

        new_add_8 = new_ba["add_8"]

        self.assertTrue(callable(new_add_8))
        self.assertEqual(new_add_8(10), 18)


    def test_shared_cell(self):

        getter, setter = make_pair(8)
        self.assertEqual(getter(), 8)

        setter(9)
        self.assertEqual(getter(), 9)

        ba = Barrel()
        ba["getter"] = getter
        ba["setter"] = setter

        new_ba = pickle_unpickle(ba)

        new_getter = new_ba["getter"]
        new_setter = new_ba["setter"]

        # check the initial value of the new pair
        self.assertEqual(new_getter(), 9)

        # change the new pair and check that it did indeed change
        new_setter(10)
        self.assertEqual(new_getter(), 10)

        # the old pair isn't effected by the new pair
        self.assertEqual(getter(), 9)
        setter(7)
        self.assertEqual(getter(), 7)

        # and show that we haven't effected our new pair
        self.assertEqual(new_getter(), 10)


    def test_contained_shared(self):
        # test that pickling maintains uniqueness and that
        # multiple versions of the same pairs/cells come
        # out as the same pairs and cells

        getter_a, setter_a = make_pair("A")
        getter_b, setter_b = make_pair("B")
        getter_c, setter_c = make_pair("C")

        self.assertEqual(getter_a(), "A")
        self.assertEqual(getter_b(), "B")
        self.assertEqual(getter_c(), "C")

        ba = Barrel()
        ba["pair_a"] = (getter_a, setter_a)
        ba["pair_b"] = (getter_b, setter_b)
        ba["pair_c"] = (getter_c, setter_c)
        ba["pairs"] = { "a": [getter_a, setter_a],
                        "b": [getter_b, setter_b],
                        "c": [getter_c, setter_c] }

        new_ba = pickle_unpickle(ba)

        getter_na1, setter_na1 = new_ba["pair_a"]
        getter_nb1, setter_nb1 = new_ba["pair_b"]
        getter_nc1, setter_nc1 = new_ba["pair_c"]

        newpairs = new_ba["pairs"]
        getter_na2, setter_na2 = newpairs['a']
        getter_nb2, setter_nb2 = newpairs['b']
        getter_nc2, setter_nc2 = newpairs['c']

        self.assertEqual(getter_na1(), "A")
        self.assertEqual(getter_nb1(), "B")
        self.assertEqual(getter_nc1(), "C")
        self.assertEqual(getter_na2(), "A")
        self.assertEqual(getter_nb2(), "B")
        self.assertEqual(getter_nc2(), "C")

        setter_na1("_A")
        setter_nb1("_B")
        setter_nc1("_C")
        self.assertEqual(getter_na1(), "_A")
        self.assertEqual(getter_nb1(), "_B")
        self.assertEqual(getter_nc1(), "_C")
        self.assertEqual(getter_na2(), "_A")
        self.assertEqual(getter_nb2(), "_B")
        self.assertEqual(getter_nc2(), "_C")

        setter_na2("A_")
        setter_nb2("B_")
        setter_nc2("C_")
        self.assertEqual(getter_na1(), "A_")
        self.assertEqual(getter_nb1(), "B_")
        self.assertEqual(getter_nc1(), "C_")
        self.assertEqual(getter_na2(), "A_")
        self.assertEqual(getter_nb2(), "B_")
        self.assertEqual(getter_nc2(), "C_")


    def test_barrel_method_list(self):
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
        ba = Barrel()
        ba["getter"] = getter
        ba["setter"] = setter

        # stuff the same ones in again, to ensure that we get the
        # exact same ones back out and not duplicates
        ba["gs"] = [getter, setter]

        new_ba = pickle_unpickle(ba)

        ngetter1 = new_ba["getter"]
        nsetter1 = new_ba["setter"]
        ngetter2 = new_ba["gs"][0]
        nsetter2 = new_ba["gs"][1]

        # no duplication, same members
        self.assertEqual(ngetter1, ngetter2)
        self.assertEqual(nsetter1, nsetter2)

        # same self class
        self.assertEqual(type(ngetter1.im_self), type(getter.im_self))
        self.assertEqual(type(nsetter1.im_self), type(setter.im_self))

        # show that these duplicates successfully pickled
        self.assertEqual(ngetter1(), "Tacos")
        nsetter1("Hello World")
        self.assertEqual(ngetter1(), "Hello World")

        # show we're not connected to the original
        self.assertEqual(getter(), "Tacos")


    def test_barrel_dict(self):

        # just testing the barrel dictionary accessors

        ba = Barrel()
        ba["Hello"] = "World"
        self.assertEqual(ba.keys(), ["Hello"])
        self.assertEqual(ba.values(), ["World"])
        self.assertEqual(ba.items(), [("Hello", "World")])

        del ba["Hello"]
        self.assertEqual(ba.keys(), [])
        self.assertEqual(ba.values(), [])

        # the managed interface for assertRaises isn't added until
        # Python 2.7, and we try to support 2.6
        self.assertRaises(KeyError, lambda: ba["Hello"])

        ba.clear()
        self.assertEqual(list(iter(ba)), [])

        ba["A"] = 100
        self.assertEqual(ba.get("A", None), 100)
        self.assertEqual(ba.get("B", None), None)

        data = {"A": 101, "B": 102, "Hello": "World"}
        ba.update(data)

        self.assertEqual(ba["A"], 101)
        self.assertEqual(ba["B"], 102)
        self.assertEqual(ba["Hello"], "World")

        d = {}
        d.update(ba)

        self.assertEqual(d, data)


    def test_barrel_brine_other(self):

        data_built = ( map, zip, globals )
        data_types = ( type, tuple, int )
        data_stuff = (501, 5.01, "Hello", set([1, 3, 5, 7]))

        ba = Barrel()
        ba["data_built"] = data_built
        ba["data_types"] = data_types
        ba["data_stuff"] = data_stuff

        new_ba = pickle_unpickle(ba)

        ndata_built = new_ba["data_built"]
        ndata_types = new_ba["data_types"]
        ndata_stuff = new_ba["data_stuff"]

        self.assertEqual(data_built, ndata_built)
        self.assertEqual(data_types, ndata_types)
        self.assertEqual(data_stuff, ndata_stuff)


    def test_barrel_reset_no_globals(self):
        add_8 = lambda x: x+8
        add_8_all = lambda l: map(add_8, l)

        self.assertEqual(add_8(100), 108)
        res = add_8_all([1, 2, 3, 4])
        self.assertEqual(res, [9, 10, 11, 12])

        ba = Barrel()
        ba["add_8"] = add_8
        ba["add_8_all"] = add_8_all

        # duplicate the barrel via pickle/unpickle
        new_ba = pickle_unpickle(ba)

        # tell the barrel that all unbrining should use an empty dict
        # as globals
        new_ba.use_globals({})

        # this works fine since it references no globals
        new_add_8 = new_ba["add_8"]
        self.assertEqual(new_add_8, new_ba["add_8"])
        self.assertEqual(new_add_8(100), 108)

        new_add_8_all = new_ba["add_8_all"]

        # however with no globals, the 'map' builtin won't be found,
        # and so trying to call add_8_all will raise a NameError Note,
        # the 'with' support on assertRaises isn't added until 2.7 and
        # we try to support 2.6
        foo = lambda: new_add_8_all([1, 2, 3, 4])
        self.assertRaises(NameError, foo)

        new_ba.reset()
        new_ba.use_globals()

        newer_add_8 = new_ba["add_8"]
        self.assertNotEqual(new_add_8, newer_add_8)
        self.assertEqual(newer_add_8(100), 108)

        newer_add_8_all = new_ba["add_8_all"]
        self.assertNotEqual(new_add_8_all, newer_add_8_all)
        res = newer_add_8_all([1, 2, 3, 4])
        self.assertEqual(res, [9, 10, 11, 12])


    def test_barrel_partial_function(self):
        add_x_y = lambda x, y: (x + y)
        add_8 = partial(add_x_y, 8)

        self.assertEqual(type(add_8), partial)
        self.assertEqual(add_8(10), 18)

        ba = Barrel()
        ba["add_8"] = add_8

        new_ba = pickle_unpickle(ba)
        new_add_8 = new_ba["add_8"]

        self.assertNotEqual(add_8, new_add_8)
        self.assertEqual(type(new_add_8), partial)
        self.assertEqual(add_8(11), 19)


    def test_barrel_partial_method(self):
        o = Obj("Hungry")

        self.assertEqual(o.get_value(), "Hungry")

        getter = o.get_value
        give_cake = partial(o.set_value, "Cake")
        give_taco = partial(o.set_value, "Taco")

        give_cake()
        self.assertEqual(getter(), "Cake")
        give_taco()
        self.assertEqual(getter(), "Taco")

        ba = Barrel()
        ba["getter"] = getter
        ba["cake"] = give_cake
        ba["taco"] = give_taco

        new_ba = pickle_unpickle(ba)
        ngetter = new_ba["getter"]
        ngive_cake = new_ba["cake"]
        ngive_taco = new_ba["taco"]

        self.assertEqual(ngetter(), "Taco")
        ngive_cake()
        self.assertEqual(ngetter(), "Cake")

        # check that they're not interfering with one-another
        self.assertNotEqual(ngetter(), getter())

        ngive_taco()
        self.assertEqual(ngetter(), "Taco")


    def test_barrel_cache_reset(self):
        # check behavior of dict API from a freshly reset barrel

        ba = Barrel()
        ba["tacos"] = "tacos"
        self.assertEqual(ba["tacos"], "tacos")

        ba.reset()
        new_ba = pickle_unpickle(ba)

        new_ba["cake"] = "no thanks"
        new_ba.reset()
        self.assertEqual(new_ba.get("cake"), None)

        new_ba.reset()
        new_ba.update({"cake": "no thanks"})
        self.assertEqual(new_ba["cake"], "no thanks")
        new_ba.reset()
        self.assertEqual(new_ba.get("cake"), None)

        new_ba.reset()
        lval = new_ba.get("tacos")
        new_ba.reset()
        rval = new_ba["tacos"]
        self.assertEqual(lval, rval)

        new_ba.reset()
        lval = new_ba.items()
        new_ba.reset()
        rval = list(new_ba.iteritems())
        self.assertEqual(lval, rval)

        new_ba.reset()
        lval = new_ba.keys()
        new_ba.reset()
        rval = list(new_ba.iterkeys())
        self.assertEqual(lval, rval)

        new_ba.reset()
        lval = list(iter(new_ba))
        new_ba.reset()
        rval = list(new_ba.iterkeys())
        self.assertEqual(lval, rval)

        new_ba.reset()
        lval = new_ba.values()
        new_ba.reset()
        rval = list(new_ba.itervalues())
        self.assertEqual(lval, rval)


    def test_barrel_uniqueness(self):
        add_8 = make_adder(8)
        add_9 = make_adder(9)

        ba = Barrel(add_8=add_8, add_9=add_9, a8=add_8, a9=add_9)

        self.assertEqual(ba["add_8"], ba["a8"])
        self.assertEqual(ba["add_9"], ba["a9"])

        new_ba = pickle_unpickle(ba)

        self.assertEqual(new_ba["add_8"], new_ba["a8"])
        self.assertEqual(new_ba["add_9"], new_ba["a9"])

        self.assertNotEqual(new_ba["add_8"], new_ba["a9"])
        self.assertNotEqual(new_ba["add_9"], new_ba["a8"])


#
# The end.
