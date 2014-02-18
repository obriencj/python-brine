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
Brine provides a way to wrap function objects so that they may be
pickled.

To truly pickle a function we need to be able to duplicate its code
and its closures. By default, `pickle` will simply store the
function's name, and then attempt to associate that with a function
when unpickling. This of course fails when the function is a lambda or
not otherwise defined at the top level.

In order to mark a function, method, or partial for storage, use the
`brine` function to create a wrapper. Later, after pickling and
unpickling the wrapper, call `unbrine` to get a new copy of the
original function.

Loading this module has the side effect of registering a pickle
handler for the `CellType` type. This should be of low impact, as the
only place this type is used is within function instances, and it
typically unexposed.

:author: Christopher O'Brien  <obriencj@gmail.com>
:license: LGPL v.3
"""


from abc import ABCMeta, abstractmethod
from functools import partial
from types import BuiltinFunctionType, BuiltinMethodType
from types import FunctionType, MethodType
from ._cellwork import CellType, cell_get_value, cell_from_value

import copy_reg
import new


__all__ = [ "brine", "unbrine",
            "BrinedObject",
            "BrinedFunction", "BrinedMethod", "BrinedPartial",
            "code_unnew", "code_new",
            "function_unnew", "function_new" ]


def brine(value):

    """
    Wrap an object so that it may be pickled. Behavior by type of
    `value` is as follows:

    * `builtin_function_or_method` is unchanged
    * `partial` is wrapped as a `BrinePartial`
    * `instancemethod` is wrapped as a `BrineMethod`
    * `function` is wrapped as a `BrineFunction`
    * `list` and `tuple` are duplicated and contents are brined
    * `dict` is duplicated and its values are brined
    * all other types are returned unchanged

    This function provides neither caching nor preservation of
    uniqueness -- if the same function is in a list multiple times,
    each will be wrapped individually and as a result will be
    duplicated when unbrined.

    In cases where uniqueness needs to be preserved, use a `Barrel`
    instead.

    Parameters
    ----------
    value : `object`
      object to be brined for pickling

    Returns
    -------
    wrapped : `object`
      as defined by the `value` parameter
    """

    if isinstance(value, (BuiltinFunctionType, BuiltinMethodType)):
        return value
    elif isinstance(value, partial):
        return BrinedPartial(value)
    elif isinstance(value, MethodType):
        return BrinedMethod(value)
    elif isinstance(value, FunctionType):
        return BrinedFunction(value)
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
    Unwrap a `value` previously wrapped with the `brine`
    function. Behavior by type of `value` is as follows:

    * `BrinePartial` unwraps to a `partial`
    * `BrineMethod` unwraps to a `instancemethod`
    * `BrineFunction` unwraps to a `function`
    * `list` and `tuple` are duplicated and contents unbrined
    * `dict` is duplicated and its values are unbrined

    Parameters
    ----------
    value : `object`
      value to be unbrined

    with_globals : `dict` or `None`
      globals dictionary to use when recreating functions. `None` is
      the same as `globals()`

    Returns
    -------
    unwrapped : `object`
      as defined by the type of `value`
    """

    glbls = globals() if with_globals is None else with_globals

    if isinstance(value, BrinedObject):
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
    The necessary arguments for use in :func:`code_new` to create an
    identical but distinct :data:`~types.CodeType` instance.

    :param code: code object for inspection
    :type code: :data:`~types.CodeType`
    :return: :class:`list` of member values of `code`
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


def code_new(argcount, nlocals, stacksize, flags, code, consts,
             names, varnames, filename, name, firstlineno, lnotab,
             freevars, cellvars):

    """
    Create a new code object. Identical to :func:`new.code`

    :return: new :data:`~types.CodeType` instance
    """

    return new.code(argcount, nlocals, stacksize, flags, code,
                    consts, names, varnames, filename, name,
                    firstlineno, lnotab, freevars, cellvars)


def function_unnew(func):

    """
    The necessary arguments for use in :func:`function_new` to create
    an identical but distinct :data:`~types.FunctionType` instance.

    :param func: function object for inspection
    :type func: :data:`~types.FunctionType`
    :return: :class:`list` of member values of `func`
    """

    return [ func.func_code,
             func.func_globals,
             func.func_name,
             func.func_defaults,
             func.func_closure ]


def function_new(code, with_globals, name, defaults, closure):

    """
    Creates a new function. Identical to :func:`new.function`

    :param code: code object for the function to execute when called
    :type code: :data:`~types.CodeType`
    :param with_globals:
    :type with_globals: :class:`dict` often the result of :func:`globals`
    :param name: name for the function
    :type name: :class:`str`
    :param defaults: defaults for the function
    :param closure: captured :class:`CellType` cells defining the closure
    :type closure: :class:`tuple`
    :return: new :data:`~types.FunctionType` instance
    """

    return new.function(code, with_globals, name, defaults, closure)


class BrinedObject(object): # pragma: no cover

    """
    Abstract base class for brine wrappers. Defines the interface
    required for brine.

    * When instantiated, should accept a `value` to wrap
    * The `get` method should return a new copy of the wrapped `value`
    * Must define the `__getstate__` and `__setstate__` methods for
      `pickle` support.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, value):
        """
        Wrap `value` so that it may be pickled.

        Parameters
        ----------
        value : `object`
            the instance needing to be wrapped for pickling
        """
        pass

    @abstractmethod
    def __getstate__(self):
        """
        Special method used by a `pickle.Pickler` to serialize an instance
        of this class.

        Returns
        -------
        data : `tuple`
            information to provide to the pickle API. Should be the
            same as what is expected in the `__setstate__` method
        """
        pass

    @abstractmethod
    def __setstate__(self, data):
        """
        Special method used by a `pickle.Unpickler` to deserialize an
        instance of this class. Should accept the same data returned
        by the `__getstate__` method

        Parameters
        ----------
        data : `tuple`
            information provided by the pickle API to instantiate a
            new copy
        """
        pass

    @abstractmethod
    def get(self, with_globals):
        """
        Recreate a copy of the initial brined value

        Parameters
        ----------
        with_globals : `globals()` or `dict`-like
            The global namespace to be used when recreating the
            value.

        Returns
        -------
        value : `object`
            A copy of the `value` originally passed to `__init__`
        """
        pass


# A function object needs to be brined before it can be pickled, and
# unbrined after it's unpickled. We need to do this because pickle has
# some default behavior for pickling types.FunctionType which we do
# not want to break. Therefore, we will simply wrap any Function
# instances in BrinedFunction before pickling, and unwap them after
# unpickling


class BrinedFunction(BrinedObject):

    """
    Wraps a function so that it may be pickled. For the most part
    you'll want to use the brine and unbrine functions from this
    module rather than instantiating or accessing this class directly
    """

    def __init__(self, function):
        self._unfunc = self._function_unnew(function)
        self._fdict = dict(function.__dict__)


    def __getstate__(self):
        return self._unfunc, self._fdict


    def __setstate__(self, state):
        self._unfunc, self._fdict = state


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


    def get(self, with_globals):

        # compose the function
        func = self._function_new(with_globals, list(self._unfunc))

        # setup any of the function's members
        func.__dict__.update(self._fdict)

        return func


    def _function_new(self, with_globals, ufunc):
        ufunc[0] = self._code_new(with_globals, list(ufunc[0]))
        ufunc[1] = with_globals
        return function_new(*ufunc)


    def _code_new(self, with_globals, uncode):
        return code_new(*uncode)


class BrinedMethod(BrinedObject):

    """
    Wraps a bound method so that it can be pickled. By default pickle
    refuses to operate on bound instance method object. This wrapper
    will still require that the object instance supports pickling,
    which in turn requires that the class be defined at the top level.
    As with the `BrineFunction` class, it is better to use the `brine`
    and `unbrine` functions from this module rather than to create an
    instance of this class directly.
    """

    def __init__(self, boundmethod):
        self._im_self = boundmethod.im_self
        self._funcname = boundmethod.im_func.__name__


    def __getstate__(self):
        return (self._im_self, self._funcname)


    def __setstate__(self, state):
        self._im_self = state[0]
        self._funcname = state[1]


    def get(self, with_globals):
        return getattr(self._im_self, self._funcname)


class BrinedPartial(BrinedObject):

    """
    Wrap a :class:`functools.partial` instance that references a
    function or method that is otherwise unsupported by pickle.
    """

    def __init__(self, part):
        self._func = brine(part.func)
        self._args = brine(part.args or None)
        self._keywords = brine(part.keywords or None)


    def get(self, with_globals):

        func = unbrine(self._func, with_globals)
        args = unbrine(self._args or tuple(), with_globals)
        kwds = unbrine(self._keywords or dict(), with_globals)
        return partial(func, *args, **kwds)


    def __getstate__(self):
        return (self._func, self._args, self._keywords)


    def __setstate__(self, data):
        self._func, self._args, self._keywords = data


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
