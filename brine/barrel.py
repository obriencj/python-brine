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
Provides a way to Brine a number of interrelated functions, using a
Barrel

author: Christopher O'Brien  <obriencj@gmail.com>
license: LGPL v.3
"""


from brine import BrineObject, BrineFunction, BrineMethod
from brine import brine, unbrine
from brine._cellwork import cell_get_value, cell_set_value, cell_from_value
from functools import partial
from itertools import imap
from types import BuiltinFunctionType, FunctionType, MethodType


__all__ = [ "Barrel", "BarrelFunction", "BarrelMethod" ]


class BarrelFunction(BrineFunction):

    """
    A brined function in a barrel. This function may be recursive, or
    may reference other functions. Use the BrineBarrel's add_function
    and get_function methods rather than instanciating this class
    directly.
    """

    def __init__(self, barrel, function):
        self._barrel = barrel
        super(BarrelFunction, self).__init__(function=function)


    def __getstate__(self):
        return (self._barrel, ) + super(BarrelFunction, self).__getstate__()


    def __setstate__(self, state):
        self._barrel = state[0]
        super(BarrelFunction, self).__setstate__(state[1:])


    def _brine_cell(self, cell):
        val = cell_get_value(cell)
        bval = self._barrel._brine(val)
        return cell_from_value(bval)


    def _unbrine_cell(self, with_globals, cell):
        val = cell_get_value(cell)
        ubval = self._barrel._unbrine(val)
        cell_set_value(cell, ubval)


    def _function_unnew(self, function):
        self._barrel._putcache(function, self)

        ufunc = super(BarrelFunction, self)._function_unnew(function)
        if ufunc[4] is not None:
            ufunc[4] = tuple(imap(self._brine_cell, ufunc[4]))
        return ufunc


    def _code_unnew(self, code):
        uncode = super(BarrelFunction, self)._code_unnew(code)
        uncode[5] = tuple(imap(self._barrel._brine, uncode[5]))
        return uncode


    def _code_new(self, with_globals, ucode):
        ucode[5] = tuple(imap(self._barrel._unbrine, ucode[5]))
        return super(BarrelFunction, self)._code_new(with_globals, ucode)


    def _function_new(self, with_globals, ufunc):
        func = super(BarrelFunction, self)._function_new(with_globals, ufunc)

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


class BarrelMethod(BrineMethod):

    """
    A brined bound method in a barrel.
    """

    def __init__(self, barrel, boundmethod):
        self._barrel = barrel
        super(BarrelMethod, self).__init__(boundmethod)


class Barrel(object):

    """
    A dict-like mapping supporting automatic brining of contained
    values
    """

    # TODO: this tries to do brining at the wrong time (at __setitem__
    # rather than __getdata__), I need to fix that.  However, the
    # __getitem__ still needs to be unbrining point, since we want to
    # give the option to set globals before we unbrine anything.

    # TODO: bring in some of the renaming features from the old
    # NameBarrel version of this class.

    def __init__(self):
        self._cache = dict()
        self._vidcache = dict()
        self._brined = dict()
        self._glbls = globals()


    #  == dict API ==

    def __setitem__(self, key, val):
        val = self._brine(val)
        self._brined[key] = self._brine(val)


    def __getitem__(self, key):
        if self._brined.has_key(key):
            val = self._brined.get(key)
            return self._unbrine(val)
        else:
            raise KeyError(key)


    def __delitem__(self, key):
        del self._brined[key]


    def __iter__(self):
        return self._brined.iterkeys()


    def get(self, key, default_val=None):
        if self._brined.has_key(key):
            val = self._brined.get(key)
            return self._unbrine(val)
        else:
            return default_val


    def iteritems(self):
        brined = self._brined
        return ((k,self._unbrine(v)) for k,v in brined.iteritems())


    def items(self):
        return list(self.iteritems())


    def iterkeys(self):
        return self._brined.iterkeys()


    def keys(self):
        return list(self.iterkeys())


    def itervalues(self):
        return imap(self._unbrine, self._brined.itervalues())


    def values(self):
        return list(self.itervalues())


    def update(self, from_dict):
        for key, val in from_dict.items():
            self[key] = val


    def clear(self):
        self._cache.clear()
        self._brined.clear()
        self._glbls = globals()


    # == pickle API ==

    def __getstate__(self):
        return (self._brined, )


    def __setstate__(self, data):
        self._cache = dict()
        self._vidcache = dict()

        brined = data[0]
        self._brined = brined

        self._glbls = globals()


    # == Barrel API ==

    def use_globals(self, glbls=None):

        """
        optionally provide a different set of globals when rebuilding
        functions from their brined bits
        """

        self._glbls = globals() if glbls is None else glbls


    def reset(self):

        """
        Clears the internal caching, meaning any future sets or gets from
        this Barrel will cause full brining or unbrining rather than
        returning an already computed value.

        If you retrieved a value from this barrel and want to load a
        new copy (possibly with different globals), calling reset() is
        a way to achieve such.
        """

        self._cache.clear()
        self._vidcache.clear()


    def _putcache(self, key, value):
        self._cache[id(key)] = value
        self._vidcache[id(key)] = key


    def _getcache(self, key):
        return self._cache.get(id(key))


    def _unbrine(self, value):
        if isinstance(value, BrineObject):
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
        if isinstance(value, BuiltinFunctionType):
            # don't touch builtins
            pass

        elif isinstance(value, MethodType):
            ret = self._getcache(value)
            if not ret:
                ret = BarrelMethod(self, value)
                self._putcache(value, ret)
            value = ret

        elif isinstance(value, FunctionType):
            ret = self._getcache(value)
            if not ret:
                ret = BarrelFunction(self, value)
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
