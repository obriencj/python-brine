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


import new
from brine import function_unnew, code_unnew
from brine import brine, unbrine

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
        pi.dump(brine(func_a))

        # unpickle func_b
        up = Unpickler(StringIO(buf.getvalue()))
        func_b = unbrine(up.load(), locals())

        self.assertEqual(func_a(), func_b())
        self.assertEqual(func_a(5), func_b(5))


#
# The end.
