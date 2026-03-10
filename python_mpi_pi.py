from mpi4py import MPI
import sys

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

n = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000_000
step = 1.0 / n
local_sum = 0.0

comm.Barrier()
t1 = MPI.Wtime()

for i in range(rank, n, size):
    x = (i + 0.5) * step
    local_sum += 4.0 / (1.0 + x * x)

global_sum = comm.reduce(local_sum, op=MPI.SUM, root=0)
t2 = MPI.Wtime()

if rank == 0:
    pi = step * global_sum
    print(f"pi={pi:.15f}, n={n}, procs={size}, time={t2 - t1}")
