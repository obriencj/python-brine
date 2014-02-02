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
Provides a simple way to pickle/unpickle function objects.

To truly pickle a function we need to be able to duplicate its code
and its closures. By default, pickle will simply store the function's
name, and then attempt to associate that with a function when
unpickling. In order to mark a function for actual storage, use the
`brine` function to create a BrineFunction, which may then be
pickled. Later, after unpickling the BrineFunction, call `unbrine` to
get a new copy of the original function

See the brine.barrel module in order to pickle recursive functions,
multiple functions, or functions with closures.

author: Christopher O'Brien  <obriencj@gmail.com>
licelse: LGPL v.3
"""


# CellType, cell_get_value, cell_from_value, cell_set_value
from brine._cellwork import *
from types import BuiltinFunctionType, FunctionType, MethodType, CodeType

import copy_reg
import new


__all__ = [ "BrineFunction", "BrineMethod",
            "brine", "unbrine",
            "code_unnew", "function_unnew", ]


def brine(func):

    """
    wraps a function so that it may be pickled
    """

    if isinstance(func, BuiltinFunctionType):
        return func
    elif isinstance(func, MethodType):
        return BrineMethod(function=func)
    elif isinstance(func, FunctionType):
        return BrineFunction(function=func)
    else:
        return func


def unbrine(bfunc, with_globals=None):

    """
    unwraps a function that had been pickled
    """

    glbls = globals() if with_globals is None else with_globals
    if isinstance(bfunc, BrineFunction):
        return bfunc.get(with_globals)
    else:
        return bfunc


def code_unnew(code):

    """
    returns the necessary arguments for use in new.code to create an
    identical but separate code block
    """

    return [ code.co_argcount,
             code.co_nlocals,
             code.co_stacksize,
             code.co_flags,
             code.co_code,
             code.co_consts,
             code.co_names,
             code.co_varnames,
             code.co_filename,
             code.co_name,
             code.co_firstlineno,
             code.co_lnotab,
             code.co_freevars,
             code.co_cellvars ]


def function_unnew(func):

    """
    returns the necessary arguments for use in new.function to create
    an identical but separate function
    """

    return [ func.func_code,
             func.func_globals,
             func.func_name,
             func.func_defaults,
             func.func_closure ]


# A function object needs to be brined before it can be pickled, and
# unbrined after it's unpickled. We need to do this because pickle has
# #some default behavior for pickling types.FunctionType which we do
# not want to break. Therefore, we will simply wrap any Function
# instances in BrinedFunction before pickling, and unwap them after
# unpickling


class BrineFunction(object):

    """
    wraps a function so that it may be pickled. For the most part
    you'll want to use brine_function and unbrine_function instead of
    instantiating or accessing this class directly
    """

    def __init__(self, function=None):
        self._unfunc = ()
        self._fdict = {}

        if function:
            self.set(function)


    def __getstate__(self):
        # used to pickle
        return self._unfunc, self._fdict


    def __setstate__(self, state):
        # used to unpickle
        self._unfunc, self._fdict = state


    def set(self, function):

        """
        set the function to be pickled by this instance
        """

        self._unfunc = self._function_unnew(function)
        self._fdict = dict(function.__dict__)


    def _function_unnew(self, function):
        unfunc = function_unnew(function)
        unfunc[0] = self._code_unnew(unfunc[0])
        unfunc[1] = dict() # func_globals
        return unfunc


    def _code_unnew(self, code):

        """
        can be overridden to process the unnew data
        """

        return code_unnew(code)


    def get(self, with_globals=None):

        """
        create a copy of the original function
        """

        glbls = with_globals or globals()

        # compose the function
        func = self._function_new(glbls, list(self._unfunc))

        # setup any of the function's members
        func.__dict__.update(self._fdict)

        return func


    def _function_new(self, with_globals, ufunc):
        ufunc[0] = self._code_new(with_globals, list(ufunc[0]))
        ufunc[1] = with_globals
        return new.function(*ufunc)


    def _code_new(self, with_globals, uncode):
        return new.code(*uncode)


    def get_function_name(self):

        """
        the internal name for the wrapped function
        """

        return self._unfunc[2]


    def rename(self, name, recurse=True):

        """
        attempts to rename the function data. If recurse is True, then any
        references in the function to its own name (provided it's not
        a shadowed variable reference), will be changed to reflect the
        new name. This makes it possible to rename recursive
        functions.
        """

        orig = self.get_function_name()

        self._unfunc[2] = name
        self._uncode[9] = name

        if recurse:
            self.rename_references(orig, name)


    def rename_references(self, old_name, new_name):

        """
        change any references to old_name to instead reference
        new_name. This does not change function parameter names.
        """

        uncode = self._unfunc[0]

        # nested defs or lambdas will need to have their references
        # tweaked too. They should already be BrinedFunctions by this
        # point
        consts = uncode[5]
        for c in consts:
            if isinstance(c, BrineFunction):
                c.rename_references(old_name, new_name)

        names = uncode[6]
        varnames = uncode[7]
        freevars = uncode[12]
        cellvars = uncode[13]

        # if it's in either of these, then it's being shadowed (is
        # that correct with cellvars?) so we won't rename any deeper
        if not (old_name in varnames or old_name in cellvars):

            # make sure we're not creating a conflict with this rename
            if new_name in varnames or new_name in cellvars:
                errm = "conflict renaming %r to %r" % (old_name, new_name)
                raise RenameException(errm)

            swap = lambda n: new_name if n == old_name else n

            uncode[6] = tuple(swap(n) for n in names)
            uncode[12] = tuple(swap(n) for n in freevars)
            uncode[13] = tuple(swap(n) for n in cellvars)


class BrineMethod(BrineFunction):

    """
    Wraps a bound method so that it can be pickled.
    """

    def __init__(self, function=None):
        self.im_self = None
        super(BrineMethod, self).__init__(function=function)


    def set(self, method):
        super(BrineMethod, self).set(method.im_func)
        self.im_self = method.im_self


    def get(self, with_globals):
        func = super(BrineMethod, self).get(with_globals)
        inst = self.im_self
        return MethodType(func, inst, inst.__class__)


    def __getstate__(self):
        return (self.im_self,) + super(BrineMethod, self).__getstate__()


    def __setstate__(self, state):
        self.im_self = state[0]
        super(BrineMethod, self).__setstate__(state[1:])


# let's give the pickle module knowledge of how to load and dump Cell
# and Code objects


def _pickle_cell(cell):
    return _unpickle_cell, (cell_get_value(cell), )


def _unpickle_cell(cell_val):
    return cell_from_value(cell_val)


def reg_cell_pickler():

    """
    Called automatically when the module is loaded, this function will
    ensure that the CellType has pickle/unpickle functions registered
    with copy_reg
    """

    copy_reg.pickle(CellType, _pickle_cell, _unpickle_cell)


# register when the module is loaded
reg_cell_pickler()


def _pickle_code(code):
    return _unpickle_code, tuple(code_unnew(code))


def _unpickle_code(*ncode):
    return new.code(*ncode)


def reg_code_pickler():
    copy_reg.pickle(CodeType, _pickle_code, _unpickle_code)


# register when the module is loaded
reg_code_pickler()


#
# The end.
