/*
  This is just to permit me to change the values of cells conveniently,
  which is absolutely necessary in order to pickle recursive function
  definitions.
*/


#include <Python.h>
#include <cellobject.h>


static PyObject *cell_get_value(PyObject *self, PyObject *args) {
  PyObject *cell = NULL;

  if (! PyArg_ParseTuple(args, "O!", &PyCell_Type, &cell))
    return NULL;

  return PyCell_Get(cell);
}


/* this function is the only one that cannot be replicated in pure
   python. The rest of this module can be done (albeit more slowly) in
   python with some function hacking. */
static PyObject *cell_set_value(PyObject *self, PyObject *args) {
  PyObject *cell = NULL;
  PyObject *val = NULL;

  if (! PyArg_ParseTuple(args, "O!O", &PyCell_Type, &cell, &val))
    return NULL;

  PyCell_Set(cell, val);

  Py_RETURN_NONE;
}


static PyObject *cell_from_value(PyObject *self, PyObject *args) {
  PyObject *val = NULL;

  if (! PyArg_ParseTuple(args, "O", &val))
    return NULL;

  return PyCell_New(val);
}


static PyMethodDef methods[] = {
  { "cell_get_value", cell_get_value, METH_VARARGS,
    "get a cell's value" },

  { "cell_set_value", cell_set_value, METH_VARARGS,
    "set a cell's value" },

  { "cell_from_value", cell_from_value, METH_VARARGS,
    "create a new cell from a value" },

  { NULL, NULL, 0, NULL },
};


PyMODINIT_FUNC initcellwork() {
  PyObject *mod;
  PyObject *celltype;

  mod = Py_InitModule("brine.cellwork", methods);

  // may as well make a convenient spot to get a reference to the
  // CellType type while we're at it
  celltype = (PyObject *) &PyCell_Type;
  Py_INCREF(celltype);
  PyModule_AddObject(mod, "CellType", celltype);
}


/* The end. */
