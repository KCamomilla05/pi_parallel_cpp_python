#include <mpi.h>
#include <iostream>
#include <iomanip>
#include <cstdlib>

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    long long n = 100000000;
    if (argc > 1) n = std::atoll(argv[1]);

    double step = 1.0 / static_cast<double>(n);
    double local_sum = 0.0;

    MPI_Barrier(MPI_COMM_WORLD);
    double t1 = MPI_Wtime();

    for (long long i = rank; i < n; i += size) {
        double x = (i + 0.5) * step;
        local_sum += 4.0 / (1.0 + x * x);
    }

    double global_sum = 0.0;
    MPI_Reduce(&local_sum, &global_sum, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);

    double t2 = MPI_Wtime();

    if (rank == 0) {
        double pi = step * global_sum;
        std::cout << std::setprecision(15)
                  << "pi=" << pi
                  << ", n=" << n
                  << ", procs=" << size
                  << ", time=" << (t2 - t1)
                  << std::endl;
    }

    MPI_Finalize();
    return 0;
}
