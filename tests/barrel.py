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

author: Christopher O'Brien  <obriencj@gmail.com>
license: LGPLv3

"""


from brine import function_unnew
from brine.barrel import Barrel
from pickle import Pickler, Unpickler
from cStringIO import StringIO

import unittest


from . import make_adder, make_pair


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


def pickle_unpickle(value):
    """
    pickle value, then unpickle it and return the unpickled copy
    """

    buf = StringIO()
    pi = Pickler(buf)
    pi.dump(value)

    buf = StringIO(buf.getvalue())
    up = Unpickler(buf)
    return up.load()


class TestBarrel(unittest.TestCase):

    def test_anon_inner(self):

        fives = make_incrementor(0, 5)

        assert(callable(fives))
        assert(fives() == 0)
        assert(fives() == 5)
        assert(fives() == 10)

        ba = Barrel()
        ba["fives"] = fives

        new_ba = pickle_unpickle(ba)

        new_fives = new_ba["fives"]

        assert(callable(new_fives))
        assert(new_fives() == 15)
        assert(new_fives() == 20)
        assert(new_fives() == 25)


    def test_anon_recursive_inner(self):

        add_8 = make_recursive_adder(8)

        assert(callable(add_8))
        assert(add_8(10) == 18)

        ba = Barrel()
        ba["add_8"] = add_8

        new_ba = pickle_unpickle(ba)

        new_add_8 = new_ba["add_8"]

        assert(callable(new_add_8))
        assert(new_add_8(10) == 18)


    def test_shared_cell(self):

        getter, setter = make_pair(8)
        assert(getter() == 8)

        setter(9)
        assert(getter() == 9)

        ba = Barrel()
        ba["getter"] = getter
        ba["setter"] = setter

        new_ba = pickle_unpickle(ba)

        new_getter = new_ba["getter"]
        new_setter = new_ba["setter"]

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


    def test_contained_shared(self):
        # test that pickling maintains uniqueness and that
        # multiple versions of the same pairs/cells come
        # out as the same pairs and cells

        getter_a, setter_a = make_pair("A")
        getter_b, setter_b = make_pair("B")
        getter_c, setter_c = make_pair("C")

        assert(getter_a() == "A")
        assert(getter_b() == "B")
        assert(getter_c() == "C")

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

        assert(getter_na1() == "A")
        assert(getter_nb1() == "B")
        assert(getter_nc1() == "C")
        assert(getter_na2() == "A")
        assert(getter_nb2() == "B")
        assert(getter_nc2() == "C")

        setter_na1("_A")
        setter_nb1("_B")
        setter_nc1("_C")
        assert(getter_na1() == "_A")
        assert(getter_nb1() == "_B")
        assert(getter_nc1() == "_C")
        assert(getter_na2() == "_A")
        assert(getter_nb2() == "_B")
        assert(getter_nc2() == "_C")

        setter_na2("A_")
        setter_nb2("B_")
        setter_nc2("C_")
        assert(getter_na1() == "A_")
        assert(getter_nb1() == "B_")
        assert(getter_nc1() == "C_")
        assert(getter_na2() == "A_")
        assert(getter_nb2() == "B_")
        assert(getter_nc2() == "C_")


#
# The end.
