import re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


# =========================
# НАСТРОЙКИ
# =========================
INPUT_FILES = {
    "C++ MPI": "cpp_mpi_runs.txt",
    "C++ OpenMP": "cpp_omp_runs.txt",
    "Python mpi4py": "python_mpi4py_runs.txt",
    "Python Numba": "python_numba_runs.txt",
    "Python PyOMP": "python_pyomp_runs.txt",
}

OUTPUT_DIR = Path("analysis_results")
OUTPUT_DIR.mkdir(exist_ok=True)


# =========================
# ПАРСИНГ ОДНОЙ СТРОКИ
# =========================
def parse_line(line: str, fallback_model: str):
    """
    Пример строки:
    pi=3.14159265358976, n=1000000, procs=1, time=0.001572782, repeat=1, model=cpp_mpi
    pi=3.14159265358976, n=1000000, threads=1, time=0.001762149, repeat=1, model=cpp_omp

    Возвращает dict или None, если строка не распознана.
    """
    line = line.strip()
    if not line or not line.startswith("pi="):
        return None

    # pi
    pi_match = re.search(r"pi=([0-9eE+\-\.]+)", line)
    # n
    n_match = re.search(r"n=(\d+)", line)
    # time
    time_match = re.search(r"time=([0-9eE+\-\.]+)", line)
    # repeat
    repeat_match = re.search(r"repeat=(\d+)", line)
    # model
    model_match = re.search(r"model=([A-Za-z0-9_+\-\.]+)", line)

    # p может быть записан как threads=... или procs=...
    threads_match = re.search(r"threads=(\d+)", line)
    procs_match = re.search(r"procs=(\d+)", line)

    if not (pi_match and n_match and time_match):
        return None

    if threads_match:
        p = int(threads_match.group(1))
        mode = "threads"
    elif procs_match:
        p = int(procs_match.group(1))
        mode = "procs"
    else:
        return None

    repeat = int(repeat_match.group(1)) if repeat_match else 1
    parsed_model = model_match.group(1) if model_match else fallback_model

    return {
        "model_name": fallback_model,
        "model_raw": parsed_model,
        "parallel_mode": mode,
        "pi": float(pi_match.group(1)),
        "n": int(n_match.group(1)),
        "p": p,
        "time": float(time_match.group(1)),
        "repeat": repeat,
        "raw_line": line,
    }


# =========================
# ЧТЕНИЕ ВСЕХ ФАЙЛОВ
# =========================
def read_all_logs(input_files: dict[str, str]) -> pd.DataFrame:
    rows = []

    for model_name, filename in input_files.items():
        path = Path(filename)
        if not path.exists():
            print(f"[WARN] Файл не найден: {filename}")
            continue

        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parsed = parse_line(line, fallback_model=model_name)
                if parsed is not None:
                    rows.append(parsed)

    if not rows:
        raise ValueError("Не удалось прочитать ни одной строки с результатами.")

    df = pd.DataFrame(rows)
    df = df.sort_values(["model_name", "n", "p", "repeat"]).reset_index(drop=True)
    return df


# =========================
# РАСЧЁТ МЕТРИК
# =========================
def compute_metrics(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Считает:
    Tp = median(time) по (model_name, n, p)
    Sp = T1 / Tp
    Ep = Sp / p
    """
    agg = (
        raw_df.groupby(["model_name", "n", "p"], as_index=False)
        .agg(
            Tp=("time", "median"),
            mean_time=("time", "mean"),
            std_time=("time", "std"),
            min_time=("time", "min"),
            max_time=("time", "max"),
            repeats=("time", "count"),
            pi_mean=("pi", "mean"),
        )
        .sort_values(["model_name", "n", "p"])
        .reset_index(drop=True)
    )

    # Внутри каждой пары (model_name, n) берём Tp при p=1
    t1_df = agg[agg["p"] == 1][["model_name", "n", "Tp"]].rename(columns={"Tp": "T1"})
    agg = agg.merge(t1_df, on=["model_name", "n"], how="left")

    agg["Sp"] = agg["T1"] / agg["Tp"]
    agg["Ep"] = agg["Sp"] / agg["p"]

    return agg


# =========================
# ВСПОМОГАТЕЛЬНЫЕ ТАБЛИЦЫ
# =========================
def make_wide_table(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    wide = df.pivot(index=["model_name", "n"], columns="p", values=value_col)
    wide.columns = [f"p={c}" for c in wide.columns]
    wide = wide.reset_index()
    return wide


# =========================
# СОХРАНЕНИЕ ТАБЛИЦ
# =========================
def save_tables(raw_df: pd.DataFrame, metrics_df: pd.DataFrame, out_dir: Path):
    raw_path = out_dir / "raw_measurements.csv"
    metrics_path = out_dir / "summary_metrics.csv"
    tp_path = out_dir / "Tp_table.csv"
    sp_path = out_dir / "Sp_table.csv"
    ep_path = out_dir / "Ep_table.csv"
    xlsx_path = out_dir / "pi_parallel_analysis.xlsx"

    raw_df.to_csv(raw_path, index=False, encoding="utf-8-sig")
    metrics_df.to_csv(metrics_path, index=False, encoding="utf-8-sig")

    tp_table = make_wide_table(metrics_df, "Tp")
    sp_table = make_wide_table(metrics_df, "Sp")
    ep_table = make_wide_table(metrics_df, "Ep")

    tp_table.to_csv(tp_path, index=False, encoding="utf-8-sig")
    sp_table.to_csv(sp_path, index=False, encoding="utf-8-sig")
    ep_table.to_csv(ep_path, index=False, encoding="utf-8-sig")

    try:
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            raw_df.to_excel(writer, sheet_name="raw_measurements", index=False)
            metrics_df.to_excel(writer, sheet_name="summary_metrics", index=False)
            tp_table.to_excel(writer, sheet_name="Tp_table", index=False)
            sp_table.to_excel(writer, sheet_name="Sp_table", index=False)
            ep_table.to_excel(writer, sheet_name="Ep_table", index=False)
        print(f"[OK] Сохранён Excel: {xlsx_path}")
    except ModuleNotFoundError:
        print("[WARN] openpyxl не установлен, Excel-файл не сохранён. CSV-файлы сохранены.")

    print(f"[OK] Сохранены таблицы в папку: {out_dir}")

# =========================
# ГРАФИКИ
# =========================
def plot_metric(metrics_df: pd.DataFrame, metric: str, ylabel: str, out_dir: Path):
    """
    Строит график metric(p) отдельно для каждого n.
    На одном графике - все реализации.
    """
    for n_value in sorted(metrics_df["n"].unique()):
        sub = metrics_df[metrics_df["n"] == n_value]

        plt.figure(figsize=(8, 5))
        for model in sorted(sub["model_name"].unique()):
            s = sub[sub["model_name"] == model].sort_values("p")
            plt.plot(s["p"], s[metric], marker="o", label=model)

        plt.xlabel("Число процессов / потоков p")
        plt.ylabel(ylabel)
        plt.title(f"{metric}(p) при n = {n_value}")
        plt.xticks(sorted(sub["p"].unique()))
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()

        filename = out_dir / f"{metric}_n{n_value}.png"
        plt.savefig(filename, dpi=200)
        plt.close()

        print(f"[OK] Сохранён график: {filename}")


def plot_all(metrics_df: pd.DataFrame, out_dir: Path):
    plot_metric(metrics_df, "Tp", "Время выполнения Tp, с", out_dir)
    plot_metric(metrics_df, "Sp", "Ускорение Sp", out_dir)
    plot_metric(metrics_df, "Ep", "Эффективность Ep", out_dir)


# =========================
# ГЛАВНАЯ ФУНКЦИЯ
# =========================
def main():
    raw_df = read_all_logs(INPUT_FILES)
    metrics_df = compute_metrics(raw_df)

    # округление только для более удобного просмотра при сохранении
    metrics_to_save = metrics_df.copy()
    numeric_cols = ["Tp", "mean_time", "std_time", "min_time", "max_time", "T1", "Sp", "Ep", "pi_mean"]
    for col in numeric_cols:
        if col in metrics_to_save.columns:
            metrics_to_save[col] = metrics_to_save[col].round(6)

    save_tables(raw_df, metrics_to_save, OUTPUT_DIR)
    plot_all(metrics_df, OUTPUT_DIR)

    print("\n===== ИТОГОВАЯ ТАБЛИЦА =====")
    print(metrics_to_save.to_string(index=False))


if __name__ == "__main__":
    main()