# Overview of python-brine

Brine is a python module that adds support for the "true" pickling of
functions. The default behavior of the pickle library is to reference
functions by name alone. This presents a significant problem when the
function you wish to pickle is anonymous (a lambda or an inner
function).

Brine provides a way to pickle the actual underlying code of a
function, including any captured cells, and can restore them again.

Brine also supports a Barrel, which allows shared resources to be
pickled while referring to each other (eg: two inner functions sharing
the same cell).
