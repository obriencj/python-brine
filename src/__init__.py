"""

Provides a simple way to pickle/unpickle function objects.

So, to truly pickle a function we need to be able to duplicate its
code. By default, pickle will simply store the function's name, and
then attempt to associate that with a function when unpickling. In
order to mark a function for actual storage, use the brine_function
function to create a BrinedFunction, which may then be pickled. Later,
after unpickling the BrinedFunction, call unbrine_function to get a
new copy of the original function

See the brine.barrel module in order to pickle recursive functions,
multiple functions, or functions with closures

author: Christopher O'Brien  <siege@preoccupied.net>

$Revision: 1.3 $ $Date: 2007/11/02 18:52:27 $

"""



# CellType, cell_get_value, cell_from_value, cell_set_value
from brine.cellwork import *
    


def brine_function(func):

    ''' wraps a function so that it may be pickled '''
    
    return BrinedFunction(function=func)



def unbrine_function(bfunc, globals):

    ''' unwraps a function that had been pickled '''
    
    return bfunc.get_function(globals)
    


def code_unnew(code):

    """ returns the necessary arguments for use in new.code to create
    an identical but separate code block """
    
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

    """ returns the necessary arguments for use in new.function to
    create an identical but separate function """
    
    return [ func.func_code,
             func.func_globals,
             func.func_name,
             func.func_defaults,
             func.func_closure ]




# A function object needs to be brined before it can be pickled, and
# unbrined after it's unpickled. We need to do this because pickle has
# #some default behavior for pickling types.FunctionType which we do
# not #want to break. Therefore, we will simply wrap any Function
# instances #in BrinedFunction before pickling, and unwap them after
# unpickling



class BrinedFunction(object):

    """ wraps a function so that it may be pickled. For the most part
    you'll want to use brine_function and unbrine_function instead of
    instantiating or accessing this class directly """


    def __init__(self, function=None):
        self.uncode = ()
        self.unfunc = ()
        self.fdict = {}

        if function:
            self.set_function(function)
    

    def __getstate__(self):
        # used to pickle
        return self.uncode, self.unfunc, self.fdict
    
    
    def __setstate__(self, state):
        # used to unpickle
        self.uncode, self.unfunc, self.fdict = state


    def set_uncode(self, uncode):
        # the expanded data to create a code object
        self.uncode = list(uncode)


    def set_unfunc(self, unfunc):
        # the expanded data to create a function object
        self.unfunc = list(unfunc)


    def set_fdict(self, fdict):
        # the __dict__ for the function object
        self.fdict = dict(fdict)


    def set_function(self, function):

        """ set the function to be pickled by this instance """
        
        self.set_code(function.func_code)

        unfunc = function_unnew(function)
        unfunc[0] = None
        unfunc[1] = {}
        self.set_unfunc(unfunc)

        self.set_fdict(function.__dict__)


    def set_code(self, code):

        """ set the function's code to be pickled by this instance """
        
        self.set_uncode(code_unnew(code))


    def get_function(self, globals):

        """ create a copy of the original function """
        
        import new

        # compose the function
        ufunc = self.unfunc[:]
        ufunc[0] = self.get_code()
        ufunc[1] = globals
        func = new.function(*ufunc)

        # setup any of the function's members
        func.__dict__.update(self.fdict)
        
        return func


    def get_code(self):

        """ create a copy of the code from the original function """
        
        import new
        return new.code(*self.uncode)


    def get_function_name(self):

        """ the internal name for the wrapped function """
        
        return self.unfunc[2]


    def rename(self, name, recurse=True):
        
        """ attempts to rename the function data. If recurse is True,
        then any references in the function to its own name (provided
        it's not a shadowed variable reference), will be changed to
        reflect the new name. This makes it possible to rename
        recursive functions. """

        orig = self.get_name()
        
        self.unfunc[2] = name
        self.uncode[9] = name

        if recurse:
            self.rename_references(orig, name)


    def rename_references(self, old_name, new_name):

        """ change any references to old_name to instead reference
        new_name. This does not change function parameter names. """

        uncode = self.uncode
        
        # nested defs or lambdas will need to have their references
        # tweaked too. They should already be BrinedFunctions by this
        # point
        consts = uncode[5]
        for c in consts:
            if isinstance(c, BrinedFunction):
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
                raise Exception("renaming references of %r to %r"
                                " creates conflicts" % (old_name, new_name))
            
            def swap(n):
                if n == old_name:
                    return new_name
                else:
                    return n
            
            uncode[6] = tuple([swap(n) for n in names])
            uncode[12] = tuple([swap(n) for n in freevars])
            uncode[13] = tuple([swap(n) for n in cellvars])



# let's give the pickle module knowledge of how to load and dump Cell
# and Code objects


def pickle_cell(cell):
    return unpickle_cell, (cell_get_value(cell), )


def unpickle_cell(cell_val):
    return cell_from_value(cell_val)


def reg_cell_pickler():

    """ Called automatically when the module is loaded, this function
    will ensure that the CellType has pickle/unpickle functions
    registered with copy_reg """
    
    import copy_reg
    copy_reg.pickle(CellType, pickle_cell, unpickle_cell)


# register when the module is loaded
reg_cell_pickler()



def pickle_code(code):
    return unpickle_code, tuple(code_unnew(code))


def unpickle_code(*ncode):
    import new
    return new.code(*ncode)


def reg_code_pickler():
    import copy_reg, types
    copy_reg.pickle(types.CodeType, pickle_code, unpickle_code)


# register when the module is loaded
reg_code_pickler()



#
# The end.
