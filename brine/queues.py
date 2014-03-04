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
Queue subclasses supporting automatic brining or barreling of
values as they are passed along.

These facilitate the sending of callable code between processes for
parallel execution.

It can conceivably be used to send callable code between machines as
well (eg: via a network socket). Utmost care must be taken to ensure
the transport medium is used securely, to prevent an intruder from
executing arbitrary code on the host.

:author: Christopher O'Brien  <obriencj@gmail.com>
:license: LGPL v.3
"""


from abc import ABCMeta
from brine import brine, unbrine
from .barrel import Barrel
from multiprocessing.queues import Queue, JoinableQueue, SimpleQueue


__all__ = (
    "BrinedQueueMix",
    "BrinedQueue", "BrinedJoinableQueue", "BrinedSimpleQueue",
    "BarreledQueueMix",
    "BarreledQueue", "BarreledJoinableQueue", "BarreledSimpleQueue",
)


class BrinedQueueMix(object):
    """
    Mixin that overrides the `put`, `get` methods to automatically
    `brine`, `unbrine` the passed value.
    """

    __metaclass__ = ABCMeta


    def put(self, value, **opts):
        value = brine(value)
        super(BrinedQueueMix, self).put(value, **opts)


    def get(self, **opts):
        value = super(BrinedQueueMix, self).get(**opts)
        return unbrine(value)


class BrinedQueue(BrinedQueueMix, Queue):
    """
    A `Queue` that takes the additional step of calling `brine` on its
    `put` argumens, and `unbrine` on its `get` results.
    """

    pass


class BrinedJoinableQueue(BrinedQueueMix, JoinableQueue):
    """
    A `JoinableQueue` that takes the additional step of calling
    `brine` on its `put` argumens, and `unbrine` on its `get` results.
    """

    pass


class BrinedSimpleQueue(SimpleQueue):
    """
    A `SimpleQueue` that takes the additional step of calling `brine`
    on its `put` argumens, and `unbrine` on its `get` results.
    """

    def _make_methods(self):
        # SimpleQueue doesn't have get/put methods, it has fields by
        # those names that just happen to be functions or bound
        # methods which write to its underlying pipe. As such, we
        # won't attempt to override them. Instead we'll replace the
        # values with wrappers.

        super(BrinedSimpleQueue, self)._make_methods()

        _put = self.put
        def put(value):
            _put(brine(value))
        self.put = put

        _get = self.get
        def get():
            return unbrine(_get())
        self.get = get


class BarreledQueueMix(object):
    """
    Mixin that overrides the `put`, `get` methods to automatically
    pack into or unpack from a `Barrel`
    """

    __metaclass__ = ABCMeta


    def put(self, value, **opts):
        bar = Barrel()
        bar[0] = value
        super(BarreledQueueMix, self).put(bar, **opts)


    def get(self, **opts):
        bar = super(BarreledQueueMix, self).get(**opts)
        return bar[0]


class BarreledQueue(BarreledQueueMix, Queue):
    """
    A `Queue` that takes the additional step of packing its `put`
    argument into a `Barrel` and unpacking its `get` results from a
    `Barrel`
    """

    pass


class BarreledJoinableQueue(BarreledQueueMix, JoinableQueue):
    """
    A `JoinableQueue` that takes the additional step of packing its
    `put` argument into a `Barrel` and unpacking its `get` results
    from a `Barrel`
    """

    pass


class BarreledSimpleQueue(SimpleQueue):
    """
    A `SimpleQueue` that packs data into a `Barrel` before sending
    with the `put` method, and unpacks data from a `Barrel` before
    returning from the `get` method.
    """

    def _make_methods(self):
        # SimpleQueue doesn't have get/put methods, it has fields by
        # those names that just happen to be functions or bound
        # methods which write to its underlying pipe. As such, we
        # won't attempt to override them. Instead we'll replace the
        # values with wrappers.

        super(BarreledSimpleQueue, self)._make_methods()

        _get = self.get
        def get():
            bar = _get()
            return bar[0]
        self.get = get

        _put = self.put
        def put(value):
            bar = Barrel()
            bar[0] = value
            _put(bar)
        self.put = put


#
# The end.
