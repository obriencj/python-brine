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
Unit tests for brine.queues

:author: Christopher O'Brien  <obriencj@gmail.com>
:license: LGPL v.3
"""


from abc import ABCMeta, abstractmethod
from brine.queues import *
from functools import partial
from multiprocessing import Process
from pickle import Pickler, Unpickler

from unittest import TestCase

from . import make_adder, make_pair, pickle_unpickle, Obj
from .barrel import make_incrementor, make_recursive_adder


def mp_helper(tasks, results):
    try:
        for work, args, kwds in iter(tasks.get, False):
            try:
                result = (True, work(*args, **kwds))
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                result = (False, type(exc), exc, None)
            results.put(result)

    except KeyboardInterrupt:
        return

    except Exception:
        raise


class MultiprocessHarness(object):
    """
    A setUp/tearDown harness that will provide a multiprocessing queue
    for us to test against.
    """

    def __init__(self, *args, **kwds):
        super(MultiprocessHarness, self).__init__(*args, **kwds)
        self.tasks = None
        self.results = None
        self.process = None


    @abstractmethod
    def create_queue(self):
        pass


    def remote(self, work, *args, **kwds):
        assert(self.tasks is not None)
        assert(self.results is not None)
        assert(self.process is not None)

        self.tasks.put((work, args, kwds))
        success, result = self.results.get()
        if success:
            return result
        else:
            raise result[0], result[1]


    def setUp(self):
        assert(self.tasks is None)
        assert(self.results is None)
        assert(self.process is None)

        self.tasks = self.create_queue()
        self.results = self.create_queue()

        process = Process(target=mp_helper, args=(self.tasks, self.results))
        process.daemon = False
        process.start()
        self.process = process


    def tearDown(self):
        self.tasks.put(False)

        self.process.terminate()
        self.process.join()
        self.process = None

        if hasattr(self.tasks, "close"):
            self.tasks.close()
        self.tasks = None

        if hasattr(self.results, "close"):
            self.results.close()
        self.results = None


class CommonTests(object):


    def test_anon_8(self):
        anon_8 = (lambda: 8)
        col = self.remote(anon_8)
        self.assertEqual(col, 8)


    def test_anon_x(self):
        anon_x = (lambda x: x)
        col = self.remote(anon_x, 8)
        self.assertEqual(col, 8)


    def test_adder(self):
        add_8 = make_adder(8)
        col = self.remote(add_8, 1)
        self.assertEqual(col, 9)


    def test_make_adder(self):
        # send function across the wire, and receive new function back
        add_8 = self.remote(make_adder, 8)
        self.assertEqual(add_8(2), 10)


    def test_partial_adder(self):
        add_8 = self.remote(partial(make_adder, 8))
        self.assertEqual(add_8(2), 10)



class TestBrinedQueue(MultiprocessHarness, CommonTests, TestCase):

    def create_queue(self):
        return BrinedQueue()


class TestBrinedJoinableQueue(TestBrinedQueue):

    def create_queue(self):
        return BrinedJoinableQueue()


class TestBrinedSimpleQueue(TestBrinedQueue):

    def create_queue(self):
        return BrinedSimpleQueue()


class TestBarreledQueue(MultiprocessHarness, CommonTests, TestCase):

    def create_queue(self):
        return BarreledQueue()


class TestBarreledJoinableQueue(TestBarreledQueue):

    def create_queue(self):
        return BarreledJoinableQueue()


class TestBarreledSimpleQueue(TestBarreledQueue):

    def create_queue(self):
        return BarreledSimpleQueue()


#
# The end.
