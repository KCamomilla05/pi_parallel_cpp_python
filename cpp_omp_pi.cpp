#include <iostream>
#include <iomanip>
#include <chrono>
#include <cstdlib>
#ifdef _OPENMP
#include <omp.h>
#endif

int main(int argc, char** argv) {
    long long n = 100000000;
    int threads = 1;
    if (argc > 1) n = std::atoll(argv[1]);
    if (argc > 2) threads = std::atoi(argv[2]);

    double step = 1.0 / static_cast<double>(n);
    double sum = 0.0;

    auto t1 = std::chrono::high_resolution_clock::now();

    #pragma omp parallel for num_threads(threads) reduction(+:sum) schedule(static)
    for (long long i = 0; i < n; ++i) {
        double x = (i + 0.5) * step;
        sum += 4.0 / (1.0 + x * x);
    }

    double pi = step * sum;

    auto t2 = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = t2 - t1;

    std::cout << std::setprecision(15)
              << "pi=" << pi
              << ", n=" << n
              << ", threads=" << threads
              << ", time=" << elapsed.count()
              << std::endl;
    return 0;
}
