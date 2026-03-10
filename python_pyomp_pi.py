"""
Требует PyOMP. На Windows запуск может быть проблемным; рекомендуем WSL2/Ubuntu.
Документация: https://pyomp.readthedocs.io/
"""
import sys
from numba.openmp import njit
from numba.openmp import openmp_context as openmp
from numba.openmp import omp_set_num_threads, omp_get_max_threads, omp_get_wtime

@njit
def pi_pyomp(n, threads):
    omp_set_num_threads(threads)
    step = 1.0 / n
    total = 0.0
    with openmp("parallel for reduction(+:total) schedule(static)"):
        for i in range(n):
            x = (i + 0.5) * step
            total += 4.0 / (1.0 + x * x)
    return step * total


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000_000
    threads = int(sys.argv[2]) if len(sys.argv) > 2 else omp_get_max_threads()

    # прогрев компиляции
    pi_pyomp(10, 1)

    t1 = omp_get_wtime()
    pi = pi_pyomp(n, threads)
    t2 = omp_get_wtime()

    print(f"pi={pi:.15f}, n={n}, threads={threads}, time={t2 - t1}")

if __name__ == "__main__":
    main()
