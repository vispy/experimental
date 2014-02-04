# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2014, Nicolas P. Rougier. All rights reserved.
# Distributed under the terms of the new BSD License.
# -----------------------------------------------------------------------------
import sys
import unittest
import numpy as np
import OpenGL.GL as gl
from buffer import Buffer, DataBuffer, VertexBuffer, IndexBuffer



# -----------------------------------------------------------------------------
class BufferTest(unittest.TestCase):

    def test_init(self):
        B = Buffer()
        assert B._target      == gl.GL_ARRAY_BUFFER
        assert B._handle      == -1
        assert B._need_create == True
        assert B._need_update == True
        assert B._need_resize == True
        assert B._need_delete == False
        assert B._nbytes      == 0
        assert B._usage       == gl.GL_DYNAMIC_DRAW
        assert B._resizeable  == True

        with self.assertRaises(ValueError):
            B = Buffer(target=-1)


    def test_set_data(self):
        data = np.zeros(100)

        B = Buffer()
        assert len(B._pending_data) == 0
        
        B = Buffer(data=data)
        assert len(B._pending_data) == 1

        B.set_data(data=data)
        assert len(B._pending_data) == 1

        # Check stored data is data
        B.set_data(data=data[:50], offset=0, copy=False)
        assert B._pending_data[-1][0].base is data

        # Check stored data is a copy
        B.set_data(data=data[:50], offset=0, copy=True)
        assert B._pending_data[-1][0].base is not data

        # Check setting the whole buffer clear pending operations
        B.set_data(data=data)
        assert len(B._pending_data) == 1

        B = Buffer(data=np.zeros(10), resizeable=False)
        with self.assertRaises(ValueError):
            B.set_data(np.ones(20))


        with self.assertRaises(ValueError):
            B.set_data(np.ones(1),offset=-1)

    def test_resize(self):

        data = np.zeros(10)
        B = Buffer(data=data)
        assert B.nbytes == data.nbytes

        data = np.zeros(20)
        B._need_resize == False
        B.set_data(data)
        assert B.nbytes == data.nbytes
        assert B._need_resize == True

        data = np.zeros(10)
        B = Buffer(data=data, resizeable=False)
        data = np.zeros(20)
        with self.assertRaises(ValueError):
            B.set_data(data)



# -----------------------------------------------------------------------------
class DataBufferTest(unittest.TestCase):

    def test_init(self):
        with self.assertRaises(ValueError):
            B = DataBuffer()

        # Check default storage and copy flags
        data = np.ones(100)
        B = DataBuffer(data)
        assert B._store == True
        assert B._copy == False
        assert B.nbytes == data.nbytes
        assert B.offset == 0
        assert B.size == 100
        assert B.itemsize == data.itemsize
        assert B.stride == data.itemsize
        assert B.dtype == data.dtype
        assert B._resizeable == True

        # Check structured type
        dtype = np.dtype( [('position', np.float32, 3),
                           ('texcoord', np.float32, 2),
                           ('color',    np.float32, 4)] )
        data = np.zeros(10,dtype=dtype)
        B = DataBuffer(data)
        assert B.nbytes == data.nbytes
        assert B.offset == 0
        assert B.size == 10
        assert B.itemsize == data.itemsize
        assert B.stride == data.itemsize
        assert B.dtype == data.dtype

        # Use CPU storage and use data as storage
        data = np.ones(100)
        B = DataBuffer(data, store=True, copy=False)
        assert B.data.base is data

        # Use CPU storage but make a local copy for storage
        B = DataBuffer(data, store=True, copy=True)
        assert B.data is not None
        assert B.data is not data

        # Do not use CPU storage
        B = DataBuffer(data, store=False)
        assert B.data is None

        # Ask to have CPU storage and to use data as storage
        # Not possible since data[::2] is not contiguous
        data = np.ones(100)
        B = DataBuffer(data[::2], store=True, copy=False)
        assert B._copy == True


    def test_getitem(self):
        dtype = np.dtype( [ ('position', np.float32, 3),
                            ('texcoord', np.float32, 2),
                            ('color',    np.float32, 4) ] )
        data = np.zeros(10,dtype=dtype)
        B = DataBuffer(data)

        Z = B["position"]
        assert Z.nbytes == 10 * 3 * np.dtype(np.float32).itemsize
        assert Z.offset == 0
        assert Z.size == 10
        assert Z.itemsize == 3 * np.dtype(np.float32).itemsize
        assert Z.stride == (3+2+4) * np.dtype(np.float32).itemsize
        assert Z.dtype == (np.float32, 3)

        Z = B["texcoord"]
        assert Z.nbytes == 10 * 2 * np.dtype(np.float32).itemsize
        assert Z.offset ==  3 * np.dtype(np.float32).itemsize
        assert Z.size == 10
        assert Z.itemsize == 2 * np.dtype(np.float32).itemsize
        assert Z.stride == (3+2+4) * np.dtype(np.float32).itemsize
        assert Z.dtype == (np.float32, 2)

        Z = B["color"]
        assert Z.nbytes == 10 * 4 * np.dtype(np.float32).itemsize
        assert Z.offset ==  (2+3) * np.dtype(np.float32).itemsize
        assert Z.size == 10
        assert Z.itemsize == 4 * np.dtype(np.float32).itemsize
        assert Z.stride == (3+2+4) * np.dtype(np.float32).itemsize
        assert Z.dtype == (np.float32, 4)

        Z = B[0]
        assert Z.nbytes == 1 * (3+2+4) * np.dtype(np.float32).itemsize
        assert Z.offset == 0
        assert Z.size == 1
        assert Z.itemsize == (3+2+4) * np.dtype(np.float32).itemsize
        assert Z.stride == (3+2+4) * np.dtype(np.float32).itemsize
        assert Z.dtype == B.dtype

            
    def test_set_data(self):
        dtype = np.dtype( [ ('position', np.float32, 3),
                            ('texcoord', np.float32, 2),
                            ('color',    np.float32, 4) ] )
        data = np.zeros(10,dtype=dtype)
        B = DataBuffer(data, store=True, copy=False)

        # Set data on base buffer : ok
        B = DataBuffer(data, store=True, copy=False)
        B.set_data(data)
        assert len(B._pending_data) == 1
        
        # Set data on child buffer : not allowed
        with self.assertRaises(ValueError):
            B["position"].set_data(data)



    def test_setitem(self):
        dtype = np.dtype( [ ('position', np.float32, 3),
                            ('texcoord', np.float32, 2),
                            ('color',    np.float32, 4) ] )
        data = np.zeros(10,dtype=dtype)

        # Setting one field : ok
        B = DataBuffer(data, store=True, copy=False)
        B['position'] = 1,2,3
        assert len(B._pending_data) == 1

        # Setting the whole array : ok
        B[...] = data
        assert len(B._pending_data) == 1

        # Setting one item out of two: ok
        B[::2] = data[::2]
        assert len(B._pending_data) == 1

        # Setting half the array : ok
        B[:5] = data[:5]
        assert len(B._pending_data) == 2

        # Setting one field : error (no storage)
        B = DataBuffer(data, store=False, copy=False)
        with self.assertRaises(ValueError):
            B['position'] = 1,2,3

        # Setting the whole array : ok
        B[...] = data
        assert len(B._pending_data) == 1
        
        # Setting one item out of two: error (no storage)
        with self.assertRaises(ValueError):
            B[::2] = data[::2]

        # Setting half the array : ok
        B[:5] = data[:5]
        assert len(B._pending_data) == 2
            
    def test_resize(self):

        data = np.zeros(10)
        B = DataBuffer(data=data)
        assert B.nbytes == data.nbytes

        # Resize allowed
        data = np.zeros(20)
        B.set_data(data)
        assert B.nbytes == data.nbytes
        assert B._need_resize == True

        # Resize not allowed using indexed notation
        data = np.zeros(30)
        with self.assertRaises(ValueError):
            B[...] = data

        # Resize not allowed
        data = np.zeros(10)
        B = DataBuffer(data=data, resizeable=False)
        data = np.zeros(20)
        with self.assertRaises(ValueError):
            B.set_data(data)



# -----------------------------------------------------------------------------
class VertexBufferTest(unittest.TestCase):

    def test_init(self):

        # VertexBuffer allowed base types
        for dtype in (np.uint8, np.int8, np.uint16, np.int16, np.float32, np.float16):
            V = VertexBuffer(dtype=dtype)
            names = V.dtype.names
            assert V.dtype[names[0]].base == dtype
            assert V.dtype[names[0]].shape == ()
        
        # VertexBuffer not allowed base types
        for dtype in (np.uint32, np.int32, np.float64):
            with self.assertRaises(TypeError):
                V = VertexBuffer(dtype=dtype)

# -----------------------------------------------------------------------------
class IndexBufferTest(unittest.TestCase):

    def test_init(self):

        # IndexBuffer allowed base types
        for dtype in (np.uint8, np.uint16, np.uint32):
            V = IndexBuffer(dtype=dtype)
            assert V.dtype == dtype
        
        # VertexBuffer not allowed base types
        for dtype in (np.int8, np.int16, np.int32, np.float16, np.float32, np.float64):
            with self.assertRaises(TypeError):
                V = IndexBuffer(dtype=dtype)

if __name__ == "__main__":
    unittest.main()
