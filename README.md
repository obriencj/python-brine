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

```
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

To prepare a function for pickling, it must first be 'brined' which is
to say, wrapped in a class that follows the pickling API.

```python
from brine import brine, unbrine

# create a function that wouldn't normally be supported via pickle
myfun = lambda x: ("Why hello there, %s" % str(x))
myfun("Godzilla") # ==> "Why hello there, Godzilla"

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
