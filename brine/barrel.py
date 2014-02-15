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
Provides a way to wrap multiple interrelated functions, while
preserving uniqueness.

:author: Christopher O'Brien  <obriencj@gmail.com>
:license: LGPL v.3
"""


from abc import ABCMeta
from brine import BrinedObject, BrinedFunction, BrinedMethod, BrinedPartial
from brine import brine, unbrine
from brine._cellwork import cell_get_value, cell_set_value, cell_from_value
from functools import partial
from itertools import imap
from types import BuiltinFunctionType, FunctionType, MethodType


__all__ = [ "Barrel" ]


class BarreledObject(BrinedObject):

    __metaclass__ = ABCMeta


    def __init__(self, barrel, value):
        self._barrel = barrel
        super(BarreledObject, self).__init__(value)


    def brine_related(self, value):
        return self._barrel._brine(value)


    def unbrine_related(self, brined_value):
        return self._barrel._unbrine(brined_value)


class BarreledFunction(BarreledObject, BrinedFunction):

    """
    A brined function in a barrel. This function may be recursive, or
    may reference other functions. Use the BrineBarrel's add_function
    and get_function methods rather than instanciating this class
    directly.
    """


    def __getstate__(self):
        return (self._barrel, ) + super(BarreledFunction, self).__getstate__()


    def __setstate__(self, state):
        self._barrel = state[0]
        super(BarreledFunction, self).__setstate__(state[1:])


    def _brine_cell(self, cell):
        val = cell_get_value(cell)
        bval = self.brine_related(val)
        return cell_from_value(bval)


    def _unbrine_cell(self, with_globals, cell):
        val = cell_get_value(cell)
        ubval = self.unbrine_related(val)
        cell_set_value(cell, ubval)


    def _function_unnew(self, function):
        self._barrel._putcache(function, self)

        ufunc = super(BarreledFunction, self)._function_unnew(function)
        if ufunc[4] is not None:
            ufunc[4] = tuple(imap(self._brine_cell, ufunc[4]))
        return ufunc


    def _code_unnew(self, code):
        uncode = super(BarreledFunction, self)._code_unnew(code)
        uncode[5] = tuple(imap(self.brine_related, uncode[5]))
        return uncode


    def _code_new(self, with_globals, ucode):
        ucode[5] = tuple(imap(self.unbrine_related, ucode[5]))
        return super(BarreledFunction, self)._code_new(with_globals, ucode)


    def _function_new(self, with_globals, ufunc):
        func = super(BarreledFunction, self)._function_new(with_globals, ufunc)

        # make sure the barrel only attempts to unbrine this function
        # once, so put our entry into the cache before attempting to
        # unbrine our cells in-place
        self._barrel._putcache(self, func)

        # this is the necessary second-pass, which will go through the
        # newly generated function and will unbrine any cells. We need
        # to do this in a second pass because it's possible that one
        # of the cells will want to be the same function that we've
        # just unbrined
        if ufunc[4] is not None:
            ub = partial(self._unbrine_cell, with_globals)
            ufunc[4] = tuple(imap(ub, ufunc[4]))

        return func


class BarreledMethod(BarreledObject, BrinedMethod):

    """
    A brined bound method in a barrel.
    """

    pass


class BarreledPartial(BarreledObject, BrinedPartial):

    """
    A brined partial in a barrel.
    """

    def set(self, part):
        brine = self._barrel._brine
        self.func = brine(part.func)
        self.args = brine(part.args or None)
        self.keywords = brine(part.keywords or None)


    def get(self, with_globals):
        unbrine = self._barrel._unbrine
        func = unbrine(self.func)
        args = unbrine(self.args or tuple())
        kwds = unbrine(self.keywords or dict())
        return partial(func, *args, **kwds)


    def __getstate__(self):
        return (self._barrel, ) + super(BarreledPartial, self).__getstate__()


    def __setstate__(self, data):
        self._barrel = data[0]
        super(BarreledPartial, self).__setstate__(data[1:])


class Barrel(object):

    """
    A dict-like mapping supporting automatic brining of contained
    values when pickled.
    """

    def __init__(self, **values):

        """
        Create an empty Barrel. Optionally initializes it with the mapping
        from the `values` parameter.
        """

        self._brined = None
        self._unbrined = dict(values)
        self._glbls = globals()
        self._cache = None


    # == dict API ==

    def __setitem__(self, key, val):
        if self._unbrined is None:
            self._unbrine_all()
        self._unbrined[key] = val


    def __getitem__(self, key):
        if self._unbrined is None:
            self._unbrine_all()
        return self._unbrined[key]


    def __delitem__(self, key):
        if self._unbrined is not None:
            del self._unbrined[key]


    def __iter__(self):
        if self._unbrined is None:
            self._unbrine_all()
        return iter(self._unbrined)


    def get(self, key, default_value=None):

        """
        An unbrined copy of the value assodicated with `key` if `key` is
        in this Barrel, else `default_value`.
        """

        if self._unbrined is None:
            self._unbrine_all()
        return self._unbrined.get(key, default_value)


    def iteritems(self):
        if self._unbrined is None:
            self._unbrine_all()
        return self._unbrined.iteritems()


    def items(self):
        if self._unbrined is None:
            self._unbrine_all()
        return self._unbrined.items()


    def iterkeys(self):
        if self._unbrined is None:
            self._unbrine_all()
        return self._unbrined.iterkeys()


    def keys(self):
        if self._unbrined is None:
            self._unbrine_all()
        return self._unbrined.keys()


    def itervalues(self):
        if self._unbrined is None:
            self._unbrine_all()
        return self._unbrined.itervalues()


    def values(self):
        if self._unbrined is None:
            self._unbrine_all()
        return self._unbrined.values()


    def update(self, from_dict):
        """
        Update the contents of this Barrel from the keys and values in
        `from_dict`
        """

        if self._unbrined is None:
            self._unbrine_all()
        return self._unbrined.update(from_dict)


    def clear(self):
        """
        Remove all key and value pairs in this Barrel, and clear the
        cache.
        """

        self._brined = None
        self._unbrined = dict()


    # == pickle API ==

    def __getstate__(self):
        if self._unbrined is None:
            return self._brined or dict()
        else:
            if self._brined is None:
                self._brine_all()
            return self._brined


    def __setstate__(self, data):
        self._brined = data
        self._unbrined = None
        self._glbls = globals()
        self._cache = None


    # == Barrel API ==

    def use_globals(self, glbls=None):
        """
        Provide a different set of globals when rebuilding functions from
        their brined wrappers.
        """

        self._glbls = globals() if glbls is None else glbls


    def reset(self):
        """
        Clears the internal cache. Any future sets or gets from this
        Barrel will cause full brining or unbrining rather than
        returning an already computed value.

        If you retrieved a value from this barrel and want to load a
        new copy (possibly with different globals), calling reset() is
        a way to achieve such.
        """

        if self._brined is None:
            self._brine_all()
        self._unbrined = None


    def _brine_all(self):
        oldcache = self._cache
        self._cache = dict()
        self._brined = self._brine(self._unbrined)
        self._cache = oldcache


    def _unbrine_all(self):
        oldcache = self._cache
        self._cache = dict()
        self._unbrined = self._unbrine(self._brined)
        self._cache = oldcache


    def _putcache(self, original, brined):
        self._cache[id(original)] = brined


    def _getcache(self, original):
        return self._cache.get(id(original))


    def _unbrine(self, value):
        assert(self._cache is not None)

        if isinstance(value, BrinedObject):
            ret = self._getcache(value)
            if not ret:
                ret = value.get(self._glbls)
                self._putcache(value, ret)
            value = ret

        elif isinstance(value, (tuple, list)):
            ret = self._getcache(value)
            if ret is None:
                vt = type(value)
                ret = vt(imap(self._unbrine, iter(value)))
                self._putcache(value, ret)
            value = ret

        elif isinstance(value, dict):
            ret = self._getcache(value)
            if ret is None:
                ret = dict(self._unbrine(value.items()))
                self._putcache(value, ret)
            value = ret

        return value


    def _brine(self, value):
        assert(self._cache is not None)

        if isinstance(value, BuiltinFunctionType):
            # don't touch builtins
            pass

        elif isinstance(value, partial):
            ret = self._getcache(value)
            if not ret:
                ret = BarreledPartial(self, value)
                self._putcache(value, ret)
            value = ret

        elif isinstance(value, MethodType):
            ret = self._getcache(value)
            if not ret:
                ret = BarreledMethod(self, value)
                self._putcache(value, ret)
            value = ret

        elif isinstance(value, FunctionType):
            ret = self._getcache(value)
            if not ret:
                ret = BarreledFunction(self, value)
                self._putcache(value, ret)
            value = ret

        elif isinstance(value, (tuple,list)):
            ret = self._getcache(value)
            if ret is None:
                vt = type(value)
                ret = vt(imap(self._brine, iter(value)))
                self._putcache(value, ret)
            value = ret

        elif isinstance(value, dict):
            ret = self._getcache(value)
            if ret is None:
                ret = dict(self._brine(value.items()))
                self._putcache(value, ret)
            value = ret

        return value


#
# The end.
