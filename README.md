# Overview of python-brine

Brine is a [Python] module that adds support for the "true" pickling
of functions. The default behavior of the [pickle] library is to
reference functions by name alone. This presents a significant problem
when the function you wish to pickle is either anonymous or not
defined at the top level.

Brine provides a way to pickle the actual underlying code of a
function, including any captured cells, and then restore them again.

Brine also provides Barrel, which allows shared resources to be
pickled while referring to each other (eg: two inner functions sharing
the same cell).

I've set the version to 0.9.0 and will not be promising any API
stability until 1.0.0 is reached. That said, I do not believe it is
too terribly far off. I have a few bits and pieces I want to test and
re-evaluate (considering changing barrel to use arbitrary keys rather
than a name). Until such time as I set the API in stone, this is just
for mucking about.

* [python-brine on GitHub][github]
* python-brine not on PyPI until version 1.0.0

[python]: http://python.org "Python"

[pickle]: http://docs.python.org/2.7/library/pickle.html
"pickle - Python object serialization"

[github]: https://github.com/obriencj/python-brine/
"python-brine on GitHub"


## Requirements

* [Python] 2.6 or later (no support for Python 3, the underlying
  function fields differ a bit)


## Install

This module uses setuptools, so simply run

```bash
python setup.py install
```


## Usage

Before we begin, let's contrive a function to preform the
pickle/unpickle dance, so we don't have to write that over and over
again throughout these examples:

```python
from pickle import Pickler, Unpickler
from cStringIO import StringIO

def pickle_unpickle(value):
    buffer = StringIO()
    Pickler(buffer).dump(value)
	buffer = StringIO(buffer.getvalue())
    return Unpickler(buffer).load()
```

### Anonymous or inner functions

Pickle normally refuses to serialize a function that is not defined in
the top level. The `BrineFunction` class wraps a function in a manner
that supports pickling, and will actually put the code and cells into
the serialization stream.

We can use `brine.brine` to wrap a FunctionType instance, and
`brine.unbrine` to unwrap it again.

```python
from brine import brine, unbrine

# create a function that wouldn't normally be supported via pickle
myfun = lambda x: ("Why hello there, %s" % str(x))
myfun("Godzilla") # ==> "Why hello there, Godzilla"

# if we tried this without the brine/unbrine wrapping, we'd get a
# pickle.PicklingError raised all up in our biz
myfun_redux = unbrine(pickle_unpickle(brine(myfun)))

# this is now a copy of the original
myfun_redux("Mothra") # ==> "Why hello there, Mothra"
```

How about something with a captured value (a closure)?

```python
def make_myfun(who):
    return lambda: ("Why hello there, %s" % who)

myfun = make_myfun("Orion")
myfun() # ==> "Why hello there, Orion"

myfun_redux = unbrine(pickle_unpickle(brine(myfun)))
myfun_redux() # ==> "Why hello there, Orion"
```

### Bound instance methods

Pickle normally refuses to serialize bound instance methods. This is
somewhat odd, because it can be done by name. The `BrineMethod` class
can be used to wrap a bound instance method. Note that because a bound
method needs to be associated with a object instance, that instance
will also need to support pickling (and hence, likely need to be
defined at the top level).

BrineMethod is name-based; it doesn't try to pickle underlying class
code.

```python
# setup a simple class for us to work over
class Obj(object):
    def __init__(self, value=None):
	    self.value = value
	def get_value(self):
	    return self.value
	def set_value(self, value):
	    self.value = value

inst = Obj("Tacos")
getter = inst.get_value
setter = inst.set_value

setter("Carrots")
getter() # ==> "Carrots"

# a little dance to brine and unbrine both bound methods
tmp = (getter, setter)
tmp = unbrine(pickle_unpickle(brine(tmp)))
n_getter, n_setter = tmp

n_getter() # ==> "Carrots"
n_setter("Sandwich")
n_getter() # ==> "Sandwich"

# the original is unaffected
getter() # ==> "Carrots"
```


## Unit tests

I tried for 100% code coverage from tests, and at the time of this
writing I've achieved it. That said, my test cases are pretty ugly and
commingled. You can run the tests via

```bash
python setup.py test
```

I've determined code coverage by use of [coverage.py], invoked as

```bash
# generates coverage data in .coverage
coverage run --source=brine/,tests/ ./setup.py test

# creates an html report from the above in htmlcov/index.html
coverage html
```

[coverage.py]: http://nedbatchelder.com/code/coverage/


## Contact

Christopher O'Brien <obriencj@gmail.com>


## License

This library is free software; you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation; either version 3 of the
License, or (at your option) any later version.

This library is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, see
<http://www.gnu.org/licenses/>.
