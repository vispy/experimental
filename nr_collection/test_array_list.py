# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2014, Nicolas P. Rougier. All rights reserved.
# Distributed under the terms of the new BSD License.
# -----------------------------------------------------------------------------
import unittest
import numpy as np
from array_list import ArrayList


class ArrayListDefault(unittest.TestCase):

    def test_init(self):
        L = ArrayList()
        assert L.dtype == float
        assert len(L) == 0

    def test_append_1(self):
        L = ArrayList()
        L.append( 1 )
        assert L[0] == 1

    def test_append_2(self):
        L = ArrayList()
        L.append( np.arange(10), 2)
        assert len(L) == 5
        assert np.allclose(L[4],[8,9])

    def test_append_3(self):
        L = ArrayList()
        L.append( np.arange(10), 1+np.arange(4) )
        assert len(L) == 4
        assert np.allclose(L[3], [6,7,8,9])

    def test_insert_1(self):
        L = ArrayList()
        L.append( 1 )
        L.insert( 0, 2 )
        assert len(L) == 2
        assert L[0] == 2

    def test_insert_2(self):
        L = ArrayList()
        L.append( 1 )
        L.insert( 0, np.arange(10), 2)
        assert len(L) == 6
        assert np.allclose(L[4],[8,9])

    def test_insert_3(self):
        L = ArrayList()
        L.append( 1 )
        L.insert( 0, np.arange(10), 1+np.arange(4) )
        assert len(L) == 5
        assert np.allclose(L[3], [6,7,8,9])

    def test_delete_1(self):
        L = ArrayList()
        L.append( 1 )
        L.append( (1, 2, 3) )
        L.append( (4, 5) )
        del L[0]
        assert np.allclose(L[0], [1,2,3])
        assert np.allclose(L[1], [4,5])

    def test_delete_2(self):
        L = ArrayList()
        L.append(np.arange(10), 1)
        del L[:-1]
        assert np.allclose(L[0], [9])

    def test_delete_3(self):
        L = ArrayList()
        L.append(np.arange(10), 1)
        del L[1:]
        assert len(L) == 1
        assert np.allclose(L[0], 0)

    def test_delete_4(self):
        L = ArrayList()
        L.append(np.arange(10), 1)
        del L[:]
        assert len(L) == 0

    def test_setitem(self):
        L = ArrayList()
        L.append(np.arange(10), 1)
        L[0] = 0
        assert L[0] == 0

    def test_getitem_ellipsis(self):
        L = ArrayList(np.arange(10),1)
        assert np.allclose(L[...], np.arange(10))

    def test_setitem_ellipsis(self):
        L = ArrayList(np.arange(10),1)
        L[...] = 0
        assert np.allclose(L.data, np.zeros(10))

    def test_sizeable(self):
        L = ArrayList(sizeable=False)
        with self.assertRaises(AttributeError):
            del L[0]

    def test_writeable(self):
        L = ArrayList([1,2,3],writeable=False)
        with self.assertRaises(AttributeError):
            L[0] = 0

    def test_data(self):
        L = ArrayList(np.empty(10))
        assert np.allclose(L[:], L.data)



# -----------------------------------------------------------------------------
if __name__ == "__main__":
    unittest.main()

