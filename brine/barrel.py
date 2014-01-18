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


from brine import BrineFunction, brine, unbrine
from brine._cellwork import cell_get_value, cell_set_value, cell_from_value
from types import BuiltinFunctionType, FunctionType, MethodType

import new


__all__ = [ "BarrelFunction", "BarrelMethod", "Barrel",
            "RenameException" ]


class RenameException(Exception):
    """ Raised by Barrel.rename_function """
    pass


class BarrelFunction(BrineFunction):

    """ A brined function in a barrel. This function may be recursive,
    or may reference other functions. Use the BrineBarrel's
    add_function and get_function methods rather than instanciating
    this class directly. """


    def __init__(self, function=None, barrel=None):
        self.barrel = barrel
        super(BarrelFunction, self).__init__(function=function)


    def __getstate__(self):
        return self.barrel, self._uncode, self._unfunc, self._fdict


    def __setstate__(self, state):
        self.barrel, self._uncode, self._unfunc, self._fdict = state


    def brine_var(self, obj):
        if isinstance(obj, FunctionType):
            return self.barrel.brine_function(obj)
        else:
            return obj


    def unbrine_var(self, obj, with_globals):
        if isinstance(obj, BrineFunction):
            return self.barrel.unbrine_function(obj, with_globals)
        else:
            return obj


    def brine_cell(self, cell):
        val = cell_get_value(cell)
        bval = self.brine_var(val)

        # if we bothered to brine it, create a new cell for the brined
        # value
        if not bval is val:
            cell = cell_from_value(bval)

        return cell


    def unbrine_cell(self, cell, globals):
        val = cell_get_value(cell)
        ubval = self.unbrine_var(val, globals)

        # if we bothered to unbrine it, update the cell to the
        # unbrined value.
        if not ubval is val:
            cell_set_value(cell, ubval)

        return cell


    def set_code(self, code):
        super(BarrelFunction, self).set_code(code)

        # brine the code's constants
        uncode = self._uncode
        if uncode[5]:
            uncode[5] = tuple(self.brine_var(c) for c in uncode[5])


    def set_function(self, function):
        # make sure the barrel only attempts to brine this function
        # once, so put our entry into the cache before attempting to
        # brine our internals
        self.barrel._cache[function] = self

        super(BarrelFunction, self).set_function(function)

        # brine the function's closure
        unfunc = self._unfunc
        if unfunc[4]:
            unfunc[4] = tuple(self.brine_cell(c) for c in unfunc[4])


    def get_code(self):
        ucode = self._uncode[:]

        # unbrine anything constants before generating the code instance
        if ucode[5]:
            ucode[5] = tuple(self.unbrine_var(c, globals) for c in ucode[5])

        return new.code(*ucode)


    def get_function(self, globals):

        ufunc = self._unfunc[:]
        ufunc[0] = self.get_code()
        ufunc[1] = globals

        func = new.function(*ufunc)

        func.__dict__.update(self._fdict)

        # make sure the barrel only attempts to unbrine this function
        # once, so put our entry into the func_inst map before
        # attempting to unbrine our internals
        self.barrel._cache[self] = func

        # this is the necessary second-pass, which will go through the
        # newly generated function and will unbrine any cells. We need
        # to do this in a second pass because it's possible that one
        # of the cells will want to be the same function that we've
        # just unbrined

        if ufunc[4]:
            ufunc[4] = [self.unbrine_cell(c, globals) for c in ufunc[4]]
            ufunc[4] = tuple(ufunc[4])

        return func


class BarrelMethod(BarrelFunction):

    """ A brined bound method in a barrel. """


    def __init__(self, function=None):
        super(BarrelMethod, self).__init__(function=function)
        self.im_self = None


    def set_function(self, meth):
        super(BarrelMethod, self).set_function(meth.im_func)
        self.im_self = meth.im_self


    def get_function(self, with_globals):
        func = super(BarrelMethod, self).get_function(with_globals)
        inst = self.im_self
        return MethodType(func, inst, inst.__class__)


    def __getstate__(self):
        return (self.im_self,) + super(BarrelMethod, self).__getstate__()


    def __setstate__(self, state):
        self.im_self = state[0]
        super(BarrelMethod, self).__setstate__(state[1:])


class Barrel(object):

    """ a barrel full of brined functions. Use a BrineBarrel when you
    need to brine more than one function, or one or more recursive
    functions """


    def __init__(self):
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

            self._cache[func] = bfunc
        return bfunc


    def unbrine_function(self, bfunc, with_globals):
        func = self._cache.get(bfunc, None)
        if not func:
            func = bfunc.get_function(with_globals)
            self._cache[bfunc] = func
        return func


    def rename_function(self, original_name, new_name, recurse=True):

        """ Changes the name of a function inside the barrel. If recurse
        is true, then all references to that function by name in any of
        the functions in this barrel will be replaced.  Raises a
        RenameException if that name is already being referenced by
        one of the functions in the barrel. """

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

        """ returns an unbrined function, referenced by name """

        return self.functions.get(name).get_function(globals)


    def add_function(self, func, as_name=None):

        """ takes a function, brines it, and adds it to this barrel
        by its current name, or by an alias """

        bfunc = self.brine_function(func)
        self.add_brined(bfunc, as_name=as_name)


def barrel_from_globals(from_globals):

    """ automatically create a barrel filled with the functions found
    in the specified globals """

    barrel = BrineBarrel()

    for k,v in from_globals.items():
        if isinstance(v, FunctionType) and \
           not isinstance(v, BuiltinFunctionType):

            barrel.add_function(v, as_name=k)

    return barrel


def deploy_barrel(barrel, into_globals):

    """ unbrines all the functions in the barrel and places them into
    the given globals """

    prep = dict(barrel.functions)
    for k,v in prep.items():
        prep[k] = v.get_function(globals)
    into_globals.update(prep)


#
# The end.
