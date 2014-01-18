"""

Provides a way to Brine a number of interrelated functions, using a Barrel

author: Christopher O'Brien  <siege@preoccupied.net>

$Revision: 1.4 $ $Date: 2007/11/02 18:52:27 $

"""


import brine
import types


class BarreledFunction(brine.BrinedFunction):

    """ A brined function in a barrel. This function may be recursive,
    or may reference other functions. Use the BrineBarrel's
    add_function and get_function methods rather than instanciating
    this class directly. """


    def __init__(self, function=None, barrel=None):
        self.barrel = barrel
        brine.BrinedFunction.__init__(self, function=function)


    def __getstate__(self):
        return self.barrel, self.uncode, self.unfunc, self.fdict


    def __setstate__(self, state):
        self.barrel, self.uncode, self.unfunc, self.fdict = state


    def brine_var(self, obj):
        if isinstance(obj, types.FunctionType):
            return self.barrel.brine_function(obj)
        else:
            return obj


    def unbrine_var(self, obj, globals):
        if isinstance(obj, brine.BrinedFunction):
            return self.barrel.unbrine_function(obj, globals)
        else:
            return obj


    def brine_cell(self, cell):
        val = brine.cell_get_value(cell)
        bval = self.brine_var(val)

        # if we bothered to brine it, create a new cell for the brined
        # value
        if not bval is val:
            cell = brine.cell_from_value(bval)

        return cell


    def unbrine_cell(self, cell, globals):
        val = brine.cell_get_value(cell)
        ubval = self.unbrine_var(val, globals)

        # if we bothered to unbrine it, update the cell to the
        # unbrined value.
        if not ubval is val:
            brine.cell_set_value(cell, ubval)

        return cell


    def set_code(self, code):
        brine.BrinedFunction.set_code(self, code)

        # brine the code's constants
        uncode = self.uncode
        if uncode[5]:
            uncode[5] = tuple([self.brine_var(c) for c in uncode[5]])


    def set_function(self, function):
        # make sure the barrel only attempts to brine this function
        # once, so put our entry into the func_inst map before
        # attempting to brine our internals
        self.barrel.func_inst[function] = self

        brine.BrinedFunction.set_function(self, function)

        # brine the function's closure
        unfunc = self.unfunc
        if unfunc[4]:
            unfunc[4] = tuple([self.brine_cell(c) for c in unfunc[4]])


    def get_code(self):
        import new

        ucode = self.uncode[:]

        # unbrine anything constants before generating the code instance
        if ucode[5]:
            ucode[5] = [self.unbrine_var(c, globals) for c in ucode[5]]
            ucode[5] = tuple(ucode[5])

        return new.code(*ucode)


    def get_function(self, globals):
        import new

        ufunc = self.unfunc[:]
        ufunc[0] = self.get_code()
        ufunc[1] = globals

        func = new.function(*ufunc)

        func.__dict__.update(self.fdict)

        # make sure the barrel only attempts to unbrine this function
        # once, so put our entry into the func_inst map before
        # attempting to unbrine our internals
        self.barrel.func_inst[self] = func

        # this is the necessary second-pass, which will go through the
        # newly generated function and will unbrine any cells. We need
        # to do this in a second pass because it's possible that one
        # of the cells will want to be the same function that we've
        # just unbrined

        if ufunc[4]:
            ufunc[4] = [self.unbrine_cell(c, globals) for c in ufunc[4]]
            ufunc[4] = tuple(ufunc[4])

        return func


class BarreledMethod(BarreledFunction):

    """ A brined bound method in a barrel. """


    def __init__(self, function=None):
        self.im_self = None
        BarreledFunction.__init__(self, function=function)


    def set_function(self, meth):
        BarreledFunction.set_function(self, meth.im_func)
        self.im_self = meth.im_self


    def get_function(self, globals):
        func = BarreledFunction.get_function(self, globals)
        inst = self.im_self
        return types.MethodType(func, inst, inst.__class__)


    def __getstate__(self):
        return (self.im_self,) + BarreledFunction.__getstate__(self)


    def __setstate__(self, state):
        self.im_self = state[0]
        BarreledFunction.__setstate__(self, state[1:])


class BrineBarrel(object):

    """ a barrel full of brined functions. Use a BrineBarrel when you
    need to brine more than one function, or one or more recursive
    functions """


    def __init__(self):
        self.functions = {}

        # only used for preventing recursion and duplicates in pickling
        # or unpickling. Never actually stored.
        self.func_inst = {}


    def __getstate__(self):
        return (self.functions, )


    def __setstate__(self, state):
        (self.functions, ) = state
        self.func_inst = {}


    def brine_function(self, func):
        bfunc = self.func_inst.get(func)
        if not bfunc:
            if isinstance(func, types.MethodType):
                bfunc = BarreledMethod(function=func, barrel=self)

            elif isinstance(func, types.FunctionType):
                bfunc = BarreledFunction(function=func, barrel=self)

            self.func_inst[func] = bfunc
        return bfunc


    def unbrine_function(self, bfunc, globals):
        func = self.func_inst.get(bfunc)
        if not func:
            func = bfunc.get_function(globals)
            self.func_inst[bfunc] = func
        return func


    def rename_function(self, original_name, new_name, recurse=True):

        """ changes the name of a function in the barrel. If recurse
        is true, then all references to that function by name will be
        in any of the functions in this barrel will be replaced.
        Raises an error if that name is already being referenced by
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
        if isinstance(v, types.FunctionType) and \
           not isinstance(v, types.BuiltinFunctionType):

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
