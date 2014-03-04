Module brine
============

.. automodule:: brine
  :show-inheritance:

  Functions
  ---------
  .. autofunction:: brine.brine
  .. autofunction:: brine.unbrine

  Wrapper Classes
  ---------------
  .. autoclass:: brine.BrinedObject
    :members: get,__init__,__getstate__,__setstate__
    :member-order: bysource
  .. autoclass:: brine.BrinedFunction
    :show-inheritance:
  .. autoclass:: brine.BrinedMethod
    :show-inheritance:
  .. autoclass:: brine.BrinedPartial
    :show-inheritance:

See Also
--------
:mod:`pickle`, :func:`functools.partial`
