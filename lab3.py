#! /usr/bin/env python
# -*- coding: utf-8 -*-
###-------------------------------------------------------------------
### File	: LUdecomposition.py
### Author  : Oleg Baskakov
### Description : matrix class
###
### 2011. Written for Moscow Aviation Institute.
###-------------------------------------------------------------------

from __future__ import division
import pyopencl as cl
import pyopencl.array as cl_array
import numpy as np
import numpy.linalg as la
from transpose import NaiveTranspose, TransposeWithLocal
from time import time

# example provided by Eilif Muller

## works with NxN matrix when N > block_size

def cl_init(type = 'GPU'):
	if type == 'GPU':
		my_type = cl.device_type.GPU
	elif type == 'CPU':
		my_type = cl.device_type.CPU
	
	try:
		plt = cl.get_platforms()[0]
		devices = plt.get_devices(device_type=my_type)
		ctx = cl.Context(devices = devices)
	except:
		ctx = cl.create_some_context(interactive=True)
	queue = cl.CommandQueue(ctx, properties=cl.command_queue_properties.PROFILING_ENABLE)
	return ctx, queue

block_size = 4


def test_mul(M1, M2):
	h1 = len(M1)
	w1 = len(M1[0])
	h2 = len(M2)
	w2 = len(M2[0])

	result = [ [0.0]*h2 for i in range(w1)]
	
	assert w1 == h2
	
	for i in range(w2):
		for j in range(h1):
			result[i][j] = 0
			for k in range(h2):
				result[i][j] += M1[i][k] * M2[k][j]
	return result


def matrix_to_array(A, n, m):
	h = ((n-1) // block_size + 1) * block_size
	w = ((m-1) // block_size + 1) * block_size

	# not fills array by zero
	result = np.empty((h, w), dtype=np.float32)

	for i in range(h):
		for j in range(w):
			result[i][j] = np.float32(0.0)

	for i in range(n):
		for j in range(m):
			result[i][j] = A[i][j]
	
	return result

def array_to_matrix(Arr, n, m):
	A = [[0.0] * m for i in range(n)]

	for i in range(n):
		for j in range(m):
			A[i][j] = Arr[i][j]
	return A



def LUP(A):
## check sizes here!!!
	ctx, queue = cl_init()
	n = len(A)
	m = len(A[0])
	
	a_buf = matrix_to_array(A, n, m)
	L_buf = np.empty(a_buf.shape).astype(np.float32)
#	c_buf = np.empty(a_buf.shape).astype(np.float32)
	
	print("a_buf")
	print(a_buf)
	
	print(L_buf.shape)
	
	kernel_params = {"block_size": block_size}

#	prg = cl.Program(ctx, open("LU.cl").read() % kernel_params, ).build()
	prg = cl.Program(ctx, open("LU.cl").read() ).build()

	mf = cl.mem_flags
	d_a_buf = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=a_buf)
	d_L_buf = cl.Buffer(ctx, mf.WRITE_ONLY, size=L_buf.nbytes)

	# actual benchmark ------------------------------------------------------------
	t1 = time()
	
	event = prg.kernelLUDecompose(queue, L_buf.shape, (block_size, block_size),
	                      d_L_buf, d_a_buf, np.uint32(4))
	#                      np.uint32(c_buf.shape[0]), np.uint32(c_buf.shape[1]))
                        #   np.uint32(w1), np.uint32(w2))

	event.wait()
	gpu_time = (time() - t1)

	cl.enqueue_copy(queue, L_buf, d_L_buf)
	cl.enqueue_copy(queue, a_buf, d_a_buf)
	
	print("L_buf")
	print(L_buf)
	print("a_buf")
	print(a_buf)
	
	res = array_to_matrix(L_buf, n, m)
	
	print("result:")
	print(res)
	print("origin:")
	print(np.matrix(A))







#=====================================================================
def main():
	global prg, code
	ctx = cl_init()
	prg = cl.Program(ctx, code).build()
	
	queue = cl.CommandQueue(ctx)
	
	a = np.random.rand(50000).astype(np.float32)
	b = np.random.rand(50000).astype(np.float32)
	
	mf = cl.mem_flags
	a_buf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=a)
	b_buf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=b)
	dest_buf = cl.Buffer(ctx, mf.WRITE_ONLY, b.nbytes)

	prg.sum(queue, a.shape, None, a_buf, b_buf, dest_buf)

	a_plus_b = np.empty_like(a)
	cl.enqueue_copy(queue, a_plus_b, dest_buf)

	print(la.norm(a_plus_b - (a+b)), la.norm(a_plus_b))
	print(a_plus_b[:10])


#=====================================================================
if __name__ == "__main__":
#	check_transpose()
#	benchmark_transpose()

	LUP( [[1,2,3,4],[3,4,3,4],[5,6,3,4],[5,6,3,7]] )
#	multiply( [[6,5,3],[7,4,2],[8,3,1]], [[1,2,4,5],[9,8,6,5],[1,8,6,5]] )

#=====================================================================

