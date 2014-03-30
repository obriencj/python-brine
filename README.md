# Overview of python-brine

[![Build Status](https://travis-ci.org/obriencj/python-brine.png?branch=master)](https://travis-ci.org/obriencj/python-brine)
[![Coverage Status](https://coveralls.io/repos/obriencj/python-brine/badge.png?branch=master)](https://coveralls.io/r/obriencj/python-brine?branch=master)

Brine is a [Python] module that adds support for the "true" pickling
of functions. The default behavior of the `pickle` [library][pickle]
is to reference functions by name alone. This presents a significant
problem when the function you wish to serialize is either a `lambda`
or not defined at the top level.

The `brine` [module][brine-module] provides a way to pickle the actual
underlying code of a function, including any closures, and then
restore them again.

For more advanced features, there is the `brine.barrel`
[module][barrel-module]. A barrel is a dictionary-like interface for
brining multiple functions.  Barrel's internal brining step is
recursive. This allows anonymous functions to work on closures
referring to other anonymous functions (eg: mutually recursive lambdas
and the like). It also preserves uniqueness, if you happen to add the
same function multiple times.

* [python-brine documentation][docs]
* [python-brine on GitHub][github]
* [python-brine on PyPI][pypi]

[python]: http://python.org "Python"

[pickle]: http://docs.python.org/2.7/library/pickle.html
"pickle - Python object serialization"

[brine-module]: http://obriencj.preoccupied.net/python-brine/brine/

[barrel-module]: http://obriencj.preoccupied.net/python-brine/barrel/

[docs]: http://obriencj.preoccupied.net/python-brine/

[github]: https://github.com/obriencj/python-brine/
"python-brine on GitHub"

[pypi]: https://pypi.python.org/pypi/brine


## Using brine

Before we begin with our examples, let's contrive a function to
preform the pickle/unpickle dance. We'll refer to this helper
throughout the remainder of the section.

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

We can use `brine.brine` to wrap a `FunctionType` instance, and
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

Here is something more complex -- two functions sharing a captured
value (a closure).

```python
def make_actor(line):
    who = ["nobody special"]
    def notice(monster):
        who[0] = str(monster)
    def alert():
        return line % who[0]
    return notice, alert

actor = make_actor("Look out, it's %s!")
notice, alert = actor

notice("Godzilla")
alert() # ==> "Look out, it's Godzilla!"

# duplicate our highly trained actor
actor_redux = unbrine(pickle_unpickle(brine(actor)))
notice_redux, alert_redux = actor_redux

# our copy of the actor functions come out sharing their own new
# closure cell
alert_redux() # ==> "Look out, it's Godzilla!"
notice_redux("Mothra")
alert_redux() # ==> "Look out, it's Mothra!"
```


### Bound instance methods

Pickle normally refuses to serialize bound instance methods. This is
somewhat odd, because it can be done by name. The `BrineMethod` class
can be used to wrap a bound instance or class method. Note that
because a bound method needs to be associated with an object, that
instance will also need to support pickling (and hence will need its
class definition available at the top level).

`BrineMethod` is entirely name-based -- it doesn't try to pickle
underlying class code.

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


## Requirements

* [Python] 2.6 or later (no support for Python 3, the underlying
  function fields differ a bit)

In addition, following tools are used in building, testing, or
generating documentation from the project sources.

* [Setuptools]
* [Coverage.py]
* [GNU Make]
* [Pandoc]
* [Sphinx]

These are all available in most linux distributions (eg. [Fedora]), and
for OSX via [MacPorts].

[setuptools]: http://pythonhosted.org/setuptools/

[coverage.py]: http://nedbatchelder.com/code/coverage/

[gnu make]: http://www.gnu.org/software/make/

[pandoc]: http://johnmacfarlane.net/pandoc/

[sphinx]: http://sphinx-doc.org/

[fedora]: http://fedoraproject.org/

[macports]: http://www.macports.org/


## Building

This module uses [setuptools], so simply run the following to build
the project.

```bash
python setup.py build
```


### Testing

Tests are written as `unittest` test cases. If you'd like to run the
tests, simply invoke:

```bash
python setup.py test
```

You may check code coverage via [coverage.py], invoked as:

```bash
# generates coverage data in .coverage
coverage run --source=brine setup.py test

# creates an html report from the above in htmlcov/index.html
coverage html
```

I've setup [travis-ci] and [coveralls.io] for this project, so tests
are run automatically, and coverage is computed then. Results are
available online:

* [python-brine on Travis-CI][brine-travis]
* [python-brine on Coveralls.io][brine-coveralls]

[travis-ci]: https://travis-ci.org

[coveralls.io]: https://coveralls.io

[brine-travis]: https://travis-ci.org/obriencj/python-brine

[brine-coveralls]: https://coveralls.io/r/obriencj/python-brine


### Documentation

Documentation is built using [Sphinx]. Invoking the following will
produce HTML documentation in the `docs/_build/html` directory.

```bash
cd docs
make html
```

Note that you will need the following installed to successfully build
the documentation:

Documentation is [also available online][docs].


## Future Enhancements

Some posibile enhancements for future minor versions

* Should we provide a wrapper for exceptions and/or stack traces?
* Should we allow users to extend `BrineObject`, in the same manner that
  pickle can be (somewhat) extended today?
* Perhaps a PKI signing step since we are in-fact sending executable
  code around? This might be better relegated to a separate project.


## Author

Christopher O'Brien <obriencj@gmail.com>

If this project interests you, you can read about more of my hacks and
ideas on [on my blog](http://obriencj.preoccupied.net).


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
