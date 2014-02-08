# Overview of python-brine

[![Build Status](https://travis-ci.org/obriencj/python-brine.png?branch=master)](https://travis-ci.org/obriencj/python-brine)
[![Coverage Status](https://coveralls.io/repos/obriencj/python-brine/badge.png?branch=master)](https://coveralls.io/r/obriencj/python-brine?branch=master)

Brine is a [Python] module that adds support for the "true" pickling
of functions. The default behavior of the [pickle] library is to
reference functions by name alone. This presents a significant problem
when the function you wish to pickle is either anonymous or not
defined at the top level.

Brine provides a way to pickle the actual underlying code of a
function, including any captured cells, and then restore them again.

Brine also provides Barrel, which is a dictionary-like interface for
brining multiple functions. It allows shared resources to be pickled
while referring to each other (eg: mutually recursive inner
functions).

I've set the version to 0.9.0 and will not be promising any API
stability until 1.0.0 is reached. That said, I do not believe it is
too terribly far off. Until such time as I set the API in stone, avoid
depending on this module for anything serious.

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


## Unit testing

I've setup [travis-ci] and [coveralls.io] for this project, so tests
are run automatically, and coverage is computed then. However, if
you'd like to run the tests manually, simply invoke them via

```bash
python setup.py test
```

You may check code coverage by use of [coverage.py], invoked as

```bash
# generates coverage data in .coverage
coverage run --source=brine setup.py test

# creates an html report from the above in htmlcov/index.html
coverage html
```

[travis-ci]: https://travis-ci.org
[coveralls.io]: https://coveralls.io
[coverage.py]: http://nedbatchelder.com/code/coverage/


## TODO

The following tasks need to be taken care of before we reach the point
of tagging a 1.0.0 release and subsequently publishing to [PyPI].

* Change the timing on brining the contents of a `brine.Barrel`. As is
  currently implemented objects are brined at the time of being added
  to the barrel (by being associated with a key). This causes problems
  for mutable types, as it's conceivable that they could change post
  brining, and then the barrel contents would actually be out-of-date.
  Instead I should consider only brining as part of the `__getdata__`
  call to the barrel.
* Should we allow users to extend BrineObject, in the same manner that
  pickle can be (somewhat) extended today? TBD.


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
