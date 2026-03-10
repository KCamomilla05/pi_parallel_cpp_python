import os
import sys
import time
from numba import njit, prange, set_num_threads, get_num_threads

@njit(parallel=True)
def pi_numba(n):
    step = 1.0 / n
    s = 0.0
    for i in prange(n):
        x = (i + 0.5) * step
        s += 4.0 / (1.0 + x * x)
    return step * s


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000_000
    threads = int(sys.argv[2]) if len(sys.argv) > 2 else os.cpu_count()
    set_num_threads(threads)

    # прогрев JIT вне измерения
    pi_numba(10)

    t1 = time.perf_counter()
    pi = pi_numba(n)
    t2 = time.perf_counter()

    print(f"pi={pi:.15f}, n={n}, threads={get_num_threads()}, time={t2 - t1}")

if __name__ == "__main__":
    main()
