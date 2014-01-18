# Overview of python-brine

Brine is a [Python] module that adds support for the "true" pickling of
functions. The default behavior of the [pickle] library is to reference
functions by name alone. This presents a significant problem when the
function you wish to pickle is anonymous (a lambda or an inner
function).

Brine provides a way to pickle the actual underlying code of a
function, including any captured cells, and can restore them again.

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
"pickle — Python object serialization"

[github]: https://github.com/obriencj/python-brine/
"python-brine on GitHub"


## Requirements

* [Python] 2.6 or later (no support for Python 3, I have no idea what
  it takes to pickle code over there)


## Install

This module uses setuptools, so simply run

```
python setup.py install
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
