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

Provides a way to Brine a number of interrelated functions, using a Barrel

author: Christopher O'Brien  <obriencj@gmail.com>
license: LGPL v.3

"""


from brine import BrineObject, BrineFunction, BrineMethod
from brine import brine, unbrine
from brine._cellwork import cell_get_value, cell_set_value, cell_from_value
from functools import partial
from itertools import imap
from types import BuiltinFunctionType, FunctionType, MethodType

import new


__all__ = [ "Barrel", "BarrelFunction", "BarrelMethod" ]


class RenameException(Exception):
    """
    Raised by NameBarrel.rename_function
    """
    pass


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
        ubval = self._barrel._unbrine(with_globals, val)
        cell_set_value(cell, ubval)


    def _function_unnew(self, function):
        self._barrel._putcache(function, self)

        ufunc = super(BarrelFunction, self)._function_unnew(function)
        ufunc[4] = tuple(imap(self._brine_cell, ufunc[4]))
        return ufunc


    def _code_unnew(self, code):
        uncode = super(BarrelFunction, self)._code_unnew(code)
        uncode[5] = tuple(imap(self._barrel._brine, uncode[5]))
        return uncode


    def _code_new(self, with_globals, ucode):

        ub = partial(self._barrel._unbrine, with_globals)
        ucode[5] = tuple(imap(ub, ucode[5]))

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
        ub = partial(self._unbrine_cell, with_globals)
        ufunc[4] = tuple(imap(ub, ufunc[4]))

        return func


class BarrelMethod(BrineMethod):

    """
    A brined bound method in a barrel.
    """

    def __init__(self, barrel, boundmethod):
        self._barrel = barrel
        super(self, BarrelMethod).__init__(boundmethod)


class Barrel(object):

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
        self._with_globals = globals()


    def __setitem__(self, key, val):
        val = self._brine(val)
        self._brined[key] = self._brine(val)


    def __getitem__(self, key):
        if self._brined.has_key(key):
            val = self._brined.get(key)
            return self._unbrine(self._glbls, val)
        else:
            raise KeyError(key)


    def _putcache(self, key, value):
        self._cache[id(key)] = value
        self._vidcache[id(key)] = key


    def _getcache(self, key):
        return self._cache.get(id(key))


    def get(self, key, default_val=None):
        if self._brined.has_key(key):
            val = self._brined.get(key)
            return self._unbrine(self._glbls, val)
        else:
            return default_val


    def __iter__(self):
        return self._brined.iterkeys()


    def iteritems(self):
        glbls = self._glbls
        brined = self._brined
        return ((k,self._unbrine(glbls, v)) for k,v in brined.iteritems())


    def items(self):
        return list(self.iteritems())


    def iterkeys(self):
        return self._brined.iterkeys()


    def keys(self):
        return list(self.iterkeys())


    def itervalues(self):
        act = partial(self._unbrine, self._glbls)
        return imap(act, self._brined.itervalues())


    def values(self):
        return list(self.itervalues())


    def __getstate__(self):
        return (self._brined, )


    def __setstate__(self, data):
        self._cache = dict()
        self._vidcache = dict()

        brined = data[0]
        self._brined = brined

        self._glbls = globals()


    def clear(self):
        self._cache.clear()
        self._brined.clear()
        self._glbls = globals()


    def use_globals(self, glbls=None):
        self._glbls = globals() if glbls is None else glbls


    def _unbrine(self, with_globals, value):
        if isinstance(value, BrineObject):
            ret = self._getcache(value)
            if not ret:
                ret = value.get(with_globals)
                self._putcache(value, ret)
            value = ret

        elif isinstance(value, (tuple, list)):
            ret = self._getcache(value)
            if ret is None:
                vt = type(value)
                ub = partial(self._unbrine, with_globals)
                ret = vt(imap(ub, iter(value)))
                self._putcache(value, ret)
            value = ret

        elif isinstance(value, dict):
            ret = self._getcache(value)
            if ret is None:
                ret = dict(self._unbrine(with_globals, value.items()))
                self._putcache(value, ret)
            value = ret

        return value


    def _brine(self, value):
        if isinstance(value, MethodType):
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


class NameBarrel(object):

    """
    A collection of brined functions. Use a Barrel when you need to
    brine more than one function, or one or more recursive functions,
    or functions which share closures, etc.
    """


    def __init__(self):
        # Do not use.
        assert(False)

        self.functions = dict()

        # only used for preventing recursion and duplicates in pickling
        # or unpickling. Never actually stored.
        self._cache = dict()


    def __getstate__(self):
        return (self.functions, )


    def __setstate__(self, state):
        (self.functions, ) = state
        self._cache = dict()


    def brine_function(self, func):
        bfunc = self._cache.get(func, None)
        if not bfunc:
            if isinstance(func, MethodType):
                bfunc = BarrelMethod(function=func, barrel=self)

            elif isinstance(func, FunctionType):
                bfunc = BarrelFunction(function=func, barrel=self)

            else:
                raise TypeError("Excepected MethodType or FunctionType,"
                                " got %r" % type(func))

            self._cache[func] = bfunc
        return bfunc


    def unbrine_function(self, bfunc, with_globals):
        func = self._cache.get(bfunc, None)
        if not func:
            func = bfunc.get_function(with_globals)
            self._cache[bfunc] = func
        return func


    def rename_function(self, original_name, new_name, recurse=True):

        """
        Changes the name of a function inside the barrel. If recurse is
        true, then all references to that function by name in any of
        the functions in this barrel will be replaced.  Raises a
        RenameException if that name is already being referenced by
        one of the functions in the barrel.
        """

        fun = self.functions.get(original_name)
        if not fun:
            return

        self.remove_brined(original_name, and_aliases=False)

        fun.rename(new_name, recurse)

        if recurse:
            for f in self.functions.itervalues():
                f.rename_references(original_name, new_name)

        self.functions[new_name] = fun


    def remove_brined(self, name, and_aliases=False):
        funcmap = self.functions

        func = funcmap.get(name)
        if not func:
            return

        del funcmap[name]
        if and_aliases:
            for k,v in funcmap.items():
                if v is func:
                    del funcmap[k]


    def add_brined(self, brinedfunc, as_name=None):
        if not as_name:
            as_name = brinedfunc.get_function_name()
        self.functions[as_name] = brinedfunc


    def get_function(self, name, globals):

        """
        returns an unbrined function, referenced by name
        """

        return self.functions.get(name).get_function(globals)


    def add_function(self, func, as_name=None):

        """
        takes a function, brines it, and adds it to this barrel by its
        current name, or by an alias
        """

        bfunc = self.brine_function(func)
        self.add_brined(bfunc, as_name=as_name)


#
# The end.
