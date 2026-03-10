# Приложение А. Команды и скрипты, использованные при выполнении вычислительных экспериментов

## А.1. Подготовка программной среды

Для проведения вычислительных экспериментов использовалась среда Ubuntu, запущенная через WSL2.

### Установка Ubuntu в WSL2

```bash
wsl --install -d Ubuntu
```

### Обновление системы и установка необходимых пакетов

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y build-essential openmpi-bin libopenmpi-dev python3 python3-pip python3-venv
```

### Создание и активация Python-окружения

```bash
python3 -m venv ~/mpiomp-venv
source ~/mpiomp-venv/bin/activate
```

### Установка Python-библиотек

```bash
pip install --upgrade pip
pip install numpy numba mpi4py matplotlib pandas
pip install pyomp
```

### Проверка корректности установки PyOMP

```bash
python3 -c "from numba.openmp import njit, openmp_context; print('PyOMP OK')"
```

---

## А.2. Компиляция C++ программ

### Компиляция реализации C++ / OpenMP

```bash
g++ -O3 -fopenmp cpp_omp_pi.cpp -o cpp_omp_pi
```

### Компиляция реализации C++ / MPI

```bash
mpicxx -O3 cpp_mpi_pi.cpp -o cpp_mpi_pi
```

### Тестовый запуск

```bash
./cpp_omp_pi 1000000 1
```

### Запуск MPI-реализации с использованием логических потоков

Для корректного запуска MPI при `p = 4` использовалась следующая команда:

```bash
mpirun --use-hwthread-cpus -np 4 ./cpp_mpi_pi 1000000
```

Это связано с тем, что Open MPI по умолчанию ориентируется на число физических ядер, тогда как в данном исследовании использовался персональный компьютер с 2 физическими ядрами и 4 логическими потоками.

---

## А.3. Скрипты проведения вычислительных экспериментов

Во всех сериях экспериментов использовались значения
[
n \in {10^6, 10^7, 10^8}, \qquad p \in {1, 2, 4}.
]

Для каждого набора параметров выполнялось 5 повторов, а результаты сохранялись в текстовые файлы для последующей обработки.

### А.3.1. C++ / OpenMP

```bash
for n in 1000000 10000000 100000000; do
  for p in 1 2 4; do
    for r in 1 2 3 4 5; do
      ./cpp_omp_pi $n $p | sed "s/$/, repeat=$r, model=cpp_omp/"
    done
  done
done | tee cpp_omp_runs.txt
```

### А.3.2. C++ / MPI

```bash
for n in 1000000 10000000 100000000; do
  for p in 1 2 4; do
    for r in 1 2 3 4 5; do
      mpirun --use-hwthread-cpus -np $p ./cpp_mpi_pi $n | sed "s/$/, repeat=$r, model=cpp_mpi/"
    done
  done
done | tee cpp_mpi_runs.txt
```

### А.3.3. Python / Numba

```bash
for n in 1000000 10000000 100000000; do
  for p in 1 2 4; do
    for r in 1 2 3 4 5; do
      python3 python_numba_pi.py $n $p | sed "s/$/, repeat=$r, model=python_numba/"
    done
  done
done | tee python_numba_runs.txt
```

### А.3.4. Python / mpi4py

```bash
for n in 1000000 10000000 100000000; do
  for p in 1 2 4; do
    for r in 1 2 3 4 5; do
      mpirun --use-hwthread-cpus -np $p python3 python_mpi_pi.py $n | sed "s/$/, repeat=$r, model=python_mpi4py/"
    done
  done
done | tee python_mpi4py_runs.txt
```

### А.3.5. Python / PyOMP

```bash
for n in 1000000 10000000 100000000; do
  for p in 1 2 4; do
    for r in 1 2 3 4 5; do
      python3 python_pyomp_pi.py $n $p | sed "s/$/, repeat=$r, model=python_pyomp/"
    done
  done
done | tee python_pyomp_runs.txt
```

---

## А.4. Обработка результатов экспериментов

После завершения всех серий вычислительных экспериментов использовался Python-скрипт анализа результатов:

```bash
python3 analyze_pi_results.py
```

Данный скрипт выполнял:

* чтение файлов с результатами запусков;
* вычисление медианного времени выполнения (T_p);
* расчёт ускорения
  [
  S_p=\frac{T_1}{T_p};
  ]
* расчёт эффективности
  [
  E_p=\frac{S_p}{p};
  ]
* формирование итоговых таблиц и датасетов;
* построение графиков зависимостей (T_p), (S_p) и (E_p) от числа потоков/процессов (p) и размера задачи (n).

---

## А.5. Примечание к параметрам эксперимента

В итоговом анализе использовались только значения
[
p \in {1,2,4},
]
поскольку исследование выполнялось на персональном компьютере с 2 физическими ядрами и 4 логическими потоками. Значения `p > 4` приводили бы к переподписке вычислительных ресурсов и не отражали бы реального аппаратного параллелизма системы.
