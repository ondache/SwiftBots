#include <Python.h>

const char *FINAL_INDICATOR = "**";
PyObject *FINAL_INDICATOR_OBJ;
static PyObject *ASCII_CACHE[256];

static PyObject* search_trie(PyObject* self, PyObject* args) {
    PyObject *trie, *word, *ch_obj;

    if (!PyArg_ParseTuple(args, "OO", &trie, &word))
        return NULL;

    if (!PyDict_Check(trie)) {
        PyErr_SetString(PyExc_TypeError, "First argument must be a dictionary");
        return NULL;
    }

    const Py_ssize_t len = PyUnicode_GetLength(word);
    const int kind = PyUnicode_KIND(word);
    const void* data = PyUnicode_DATA(word);

    for (Py_ssize_t i = 0; i < len; i++) {
        const Py_UCS4 ch = PyUnicode_READ(kind, data, i);
        if (ch < 256) {
            ch_obj = ASCII_CACHE[ch];
            Py_INCREF(ch_obj);
        }
        else {
            ch_obj = PyUnicode_FromOrdinal((int)ch);
        }
        trie = PyDict_GetItem(trie, ch_obj);
        Py_DECREF(ch_obj);

        if (trie == NULL) {
            Py_RETURN_NONE;
        }
        if (PyDict_Contains(trie, FINAL_INDICATOR_OBJ) == 1) {
            Py_INCREF(trie);
            return trie;
        }
    }

    Py_RETURN_NONE;
}

static PyMethodDef Methods[] = {
    {"search_trie", search_trie, METH_VARARGS, ""},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "search_ext",
    "",
    -1,
    Methods
};

PyMODINIT_FUNC PyInit_search_ext(void) {
    FINAL_INDICATOR_OBJ = PyUnicode_FromString(FINAL_INDICATOR);
    for (int i = 0; i < 256; i++) {
        ASCII_CACHE[i] = PyUnicode_FromOrdinal(i);
    }
    return PyModule_Create(&moduledef);
}
