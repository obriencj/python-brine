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
`brine` function to create a BrineFunction, which may then be pickled.
Later, after unpickling the BrineFunction, call `unbrine` to get a new
copy of the original function

See the brine.barrel module in order to pickle recursive functions,
mutually recursive functions, and the like.

author: Christopher O'Brien  <obriencj@gmail.com>
licelse: LGPL v.3
"""


from abc import ABCMeta, abstractmethod
from types import BuiltinFunctionType, FunctionType, MethodType
from ._cellwork import CellType, cell_get_value, cell_from_value

import copy_reg
import new


__all__ = [ "BrineObject", "BrineFunction", "BrineMethod",
            "brine", "unbrine",
            "code_unnew", "function_unnew", ]


def brine(value):

    """
    Wraps a value so that it may be pickled. Funcions are wrapped in a
    BrineFunction; methods are wrapped in a BrineMethod; lists and
    tuples have their items brined; dictionaries have their values
    (but not keys) brined. Builtin functions and all other types are
    returned unchanged.

    Note that there is no de-duplication or caching -- ie: if the same
    function is in a list multiple times, each will be wrapped
    individually and as a result will be duplicated when unbrined. For
    complex situations like this, use a Barrel from the brine.barrel
    module.
    """

    if isinstance(value, BuiltinFunctionType):
        return value
    elif isinstance(value, MethodType):
        return BrineMethod(value)
    elif isinstance(value, FunctionType):
        return BrineFunction(value)
    elif isinstance(value, (list, tuple)):
        # create a duplicate of the collection with brined internals
        ty = type(value)
        return ty(brine(i) for i in iter(value))
    elif isinstance(value, dict):
        items = value.items()
        return dict((key,brine(val)) for key,val in items)
    else:
        return value


def unbrine(value, with_globals=None):

    """
    Unwraps a value that had been pickled via the brine function
    """

    glbls = globals() if with_globals is None else with_globals

    if isinstance(value, BrineObject):
        return value.get(glbls)
    elif isinstance(value, (list, tuple)):
        ty = type(value)
        return ty(unbrine(i, glbls) for i in iter(value))
    elif isinstance(value, dict):
        items = value.items()
        return dict((key,unbrine(val, glbls)) for key,val in items)
    else:
        return value


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


class BrineObject(object): # pragma: no cover

    __metaclass__ = ABCMeta

    @abstractmethod
    def __getstate__(self):
        pass

    @abstractmethod
    def __setstate__(self, data):
        pass

    @abstractmethod
    def get(self, with_globals=None):
        pass


# A function object needs to be brined before it can be pickled, and
# unbrined after it's unpickled. We need to do this because pickle has
# #some default behavior for pickling types.FunctionType which we do
# not want to break. Therefore, we will simply wrap any Function
# instances in BrinedFunction before pickling, and unwap them after
# unpickling


class BrineFunction(BrineObject):

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

        glbls = globals() if with_globals is None else with_globals

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


class BrineMethod(BrineObject):

    """
    Wraps a bound method so that it can be pickled. By default pickle
    refuses to operate on bound instance method object. This wrapper
    will still require that the object instance supports pickling,
    which in turn requires that the class be defined at the top level.
    """

    def __init__(self, boundmethod=None):
        self._im_self = None
        self._funcname = None
        if boundmethod is not None:
            self.set(boundmethod)


    def set(self, method):
        self._im_self = method.im_self
        self._funcname = method.im_func.__name__


    def get(self, with_globals):
        return getattr(self._im_self, self._funcname)


    def __getstate__(self):
        return (self._im_self, self._funcname)


    def __setstate__(self, state):
        self._im_self = state[0]
        self._funcname = state[1]


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


#
# The end.
