#!/usr/bin/env python3
"""Analisis hasil eksperimen JSSP."""

import argparse
import csv
import math
import os
import random
import statistics
import time
from typing import Dict, List, Optional, Sequence, Tuple

from jssp.data import C_STAR
from jssp.decoder import decode

CHECKPOINTS = [500, 1000, 2000, 3000]


def read_csv(path: str) -> List[dict]:
    """Membaca CSV menjadi daftar dictionary."""
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean_or_none(values: Sequence[float]) -> Optional[float]:
    return statistics.mean(values) if values else None


def stdev_or_none(values: Sequence[float]) -> Optional[float]:
    return statistics.stdev(values) if len(values) >= 2 else None


def format_number(value: Optional[float], digits: int = 3) -> str:
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def compute_statistics(summary_rows: Sequence[dict]) -> Dict[str, dict]:
    """Menghitung statistik per metode dari ringkasan_run.csv."""
    methods: List[str] = []
    for row in summary_rows:
        if row["metode"] not in methods:
            methods.append(row["metode"])

    statistics_by_method: Dict[str, dict] = {}
    for method in methods:
        runs = [row for row in summary_rows if row["metode"] == method]
        best_values = [int(row["best_makespan"]) for row in runs]
        eval_values = [
            int(row["eval_hingga_optimum"])
            for row in runs
            if row["eval_hingga_optimum"].strip() != ""
        ]
        time_values = [
            float(row["waktu_s"])
            for row in runs
            if row["waktu_s"].strip() != ""
        ]
        memory_values = [
            float(row["memori_kib"])
            for row in runs
            if row["memori_kib"].strip() != ""
        ]
        rpd_values = [
            (value - C_STAR) / C_STAR * 100.0
            for value in best_values
        ]
        success_rate = (
            sum(1 for value in best_values if value == C_STAR)
            / len(best_values)
        )

        statistics_by_method[method] = {
            "runs": len(runs),
            "best": min(best_values),
            "mean": statistics.mean(best_values),
            "stdev": stdev_or_none(best_values),
            "success_rate": success_rate,
            "rpd_mean": statistics.mean(rpd_values),
            "rpd_best": (min(best_values) - C_STAR) / C_STAR * 100.0,
            "eval_optimum_mean": mean_or_none(eval_values),
            "reached": len(eval_values),
            "failed": len(runs) - len(eval_values),
            "time_mean": mean_or_none(time_values),
            "memory_mean": mean_or_none(memory_values),
        }

    return statistics_by_method


def compute_convergence(
    evaluation_rows: Sequence[dict],
) -> Tuple[Dict[str, Dict[int, Optional[float]]], int]:
    """Menghitung rata-rata best_so_far pada checkpoint evaluasi."""
    methods: List[str] = []
    values: Dict[str, Dict[int, List[int]]] = {}

    for row in evaluation_rows:
        method = row["metode"]
        if method not in methods:
            methods.append(method)
            values[method] = {checkpoint: [] for checkpoint in CHECKPOINTS}

    max_evaluation = 0
    for row in evaluation_rows:
        method = row["metode"]
        evaluation = int(row["evaluasi"])
        max_evaluation = max(max_evaluation, evaluation)
        if evaluation in CHECKPOINTS:
            values[method][evaluation].append(
                int(row["best_so_far"])
            )

    averages: Dict[str, Dict[int, Optional[float]]] = {}
    for method in methods:
        averages[method] = {
            checkpoint: mean_or_none(values[method][checkpoint])
            for checkpoint in CHECKPOINTS
        }

    return averages, max_evaluation


def print_summary_table(statistics_by_method: Dict[str, dict]) -> None:
    header = (
        f"{'Metode':<7} {'Best':>5} {'Mean':>8} {'SD':>7} "
        f"{'Sukses':>7} {'RPDmean':>8} {'RPDbest':>8} "
        f"{'EvalOpt':>10} {'Capai/Gagal':>12} "
        f"{'Waktu(s)':>10} {'Mem(KiB)':>10}"
    )
    print(header)
    print("-" * len(header))
    for method, stats in statistics_by_method.items():
        eval_text = (
            f"{stats['eval_optimum_mean']:.2f}"
            if stats["eval_optimum_mean"] is not None
            else "tidak tercapai"
        )
        stdev_text = format_number(stats["stdev"], 3)
        print(
            f"{method:<7} {stats['best']:>5} {stats['mean']:>8.3f} "
            f"{stdev_text:>7} "
            f"{stats['success_rate'] * 100:>6.1f}% "
            f"{stats['rpd_mean']:>8.3f} {stats['rpd_best']:>8.3f} "
            f"{eval_text:>10} "
            f"{stats['reached']}/{stats['failed']:<10} "
            f"{stats['time_mean']:>10.6f} "
            f"{stats['memory_mean']:>10.2f}"
        )


def print_convergence_table(
    convergence: Dict[str, Dict[int, Optional[float]]],
    max_evaluation: int,
) -> None:
    available = [
        checkpoint
        for checkpoint in CHECKPOINTS
        if checkpoint <= max_evaluation
    ]
    print("\nTabel konvergensi (rata-rata best_so_far):")
    if not available:
        print(
            f"  Tidak ada checkpoint 500/1000/2000/3000 "
            f"(evaluasi maksimum {max_evaluation})."
        )
        return

    header = f"{'Metode':<7} " + " ".join(
        f"{checkpoint:>10}" for checkpoint in available
    )
    print(header)
    print("-" * len(header))
    for method, values in convergence.items():
        row = f"{method:<7} "
        row += " ".join(
            f"{format_number(values[checkpoint], 3):>10}"
            for checkpoint in available
        )
        print(row)


def save_summary_table(
    path: str,
    statistics_by_method: Dict[str, dict],
    convergence: Dict[str, Dict[int, Optional[float]]],
) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "metode",
                "best_makespan",
                "mean_makespan",
                "stdev_makespan",
                "success_rate",
                "rpd_mean_pct",
                "rpd_best_pct",
                "eval_hingga_optimum_mean",
                "run_mencapai_optimum",
                "run_gagal",
                "waktu_s_mean",
                "memori_kib_mean",
                "conv_500",
                "conv_1000",
                "conv_2000",
                "conv_3000",
            ]
        )
        for method, stats in statistics_by_method.items():
            convergence_values = convergence.get(
                method, {checkpoint: None for checkpoint in CHECKPOINTS}
            )
            writer.writerow(
                [
                    method,
                    stats["best"],
                    f"{stats['mean']:.6f}",
                    ""
                    if stats["stdev"] is None
                    else f"{stats['stdev']:.6f}",
                    f"{stats['success_rate']:.6f}",
                    f"{stats['rpd_mean']:.6f}",
                    f"{stats['rpd_best']:.6f}",
                    ""
                    if stats["eval_optimum_mean"] is None
                    else f"{stats['eval_optimum_mean']:.6f}",
                    stats["reached"],
                    stats["failed"],
                    ""
                    if stats["time_mean"] is None
                    else f"{stats['time_mean']:.6f}",
                    ""
                    if stats["memory_mean"] is None
                    else f"{stats['memory_mean']:.6f}",
                    ""
                    if convergence_values[500] is None
                    else f"{convergence_values[500]:.6f}",
                    ""
                    if convergence_values[1000] is None
                    else f"{convergence_values[1000]:.6f}",
                    ""
                    if convergence_values[2000] is None
                    else f"{convergence_values[2000]:.6f}",
                    ""
                    if convergence_values[3000] is None
                    else f"{convergence_values[3000]:.6f}",
                ]
            )


def make_synthetic_instance(
    n_jobs: int, n_machines: int, rng: random.Random
) -> List[List[Tuple[int, int]]]:
    """Membuat instance JSSP sintetis dengan urutan mesin acak per job."""
    dataset = []
    for _ in range(n_jobs):
        machines = list(range(n_machines))
        rng.shuffle(machines)
        durations = [rng.randint(1, 99) for _ in range(n_machines)]
        dataset.append(
            [
                (machines[index], durations[index])
                for index in range(n_machines)
            ]
        )
    return dataset


def measure_decode_time(
    dataset: Sequence[Sequence[Tuple[int, int]]], repetitions: int
) -> float:
    """Mengukur rata-rata waktu satu decoding setelah warm-up."""
    n_jobs = len(dataset)
    n_machines = len(dataset[0])
    chromosome = [
        job for job in range(n_jobs) for _ in range(n_machines)
    ]

    for _ in range(10):
        decode(chromosome, dataset)

    start = time.perf_counter()
    for _ in range(repetitions):
        decode(chromosome, dataset)
    elapsed = time.perf_counter() - start
    return elapsed / repetitions


def empirical_big_o(output_directory: str) -> List[Tuple[int, int, float, float]]:
    """Menjalankan cek Big-O empiris sederhana."""
    rng = random.Random(2026)
    results = []

    print("\nCek Big-O empiris (indikatif):")
    print(
        f"{'n=m':>4} {'L':>5} {'waktu decode (s)':>18} "
        f"{'rasio / (L^2 log L)':>22}"
    )
    print("-" * 52)

    for size in [4, 6, 8, 10, 12]:
        dataset = make_synthetic_instance(size, size, rng)
        length = size * size
        average_time = measure_decode_time(dataset, repetitions=200)
        denominator = length * length * math.log(length)
        ratio = average_time / denominator
        results.append((size, length, average_time, ratio))
        print(
            f"{size:>4} {length:>5} {average_time:>18.9f} "
            f"{ratio:>22.6e}"
        )

    path = os.path.join(output_directory, "big_o_empiris.csv")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["n_job", "n_mesin", "L", "waktu_decode_s", "rasio_L2logL"]
        )
        for size, length, average_time, ratio in results:
            writer.writerow(
                [size, size, length, f"{average_time:.12f}", f"{ratio:.12e}"]
            )

    return results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Analisis hasil eksperimen JSSP"
    )
    parser.add_argument(
        "--input",
        default="hasil",
        help="Direktori berisi evaluasi.csv dan ringkasan_run.csv",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Direktori keluaran tabel (default: sama dengan --input)",
    )
    args = parser.parse_args(argv)

    input_directory = args.input
    output_directory = args.out or input_directory
    summary_path = os.path.join(
        input_directory, "ringkasan_run.csv"
    )
    evaluation_path = os.path.join(
        input_directory, "evaluasi.csv"
    )

    if not os.path.exists(summary_path) or not os.path.exists(
        evaluation_path
    ):
        print(
            f"File hasil tidak ditemukan di {input_directory}. "
            "Jalankan run_experiment.py terlebih dahulu."
        )
        return 1

    os.makedirs(output_directory, exist_ok=True)
    summary_rows = read_csv(summary_path)
    evaluation_rows = read_csv(evaluation_path)

    statistics_by_method = compute_statistics(summary_rows)
    convergence, max_evaluation = compute_convergence(
        evaluation_rows
    )

    print("Tabel ringkasan per metode:")
    print_summary_table(statistics_by_method)
    print_convergence_table(convergence, max_evaluation)

    ceiling_methods = [
        method
        for method, stats in statistics_by_method.items()
        if stats["success_rate"] == 1.0
    ]
    if ceiling_methods:
        print(
            "\nPERINGATAN: ceiling effect terdeteksi untuk metode "
            f"{', '.join(ceiling_methods)} (success rate 100%). "
            "Pembeda utama menjadi evaluasi hingga optimum, "
            "konvergensi, waktu, dan memori."
        )
    else:
        print(
            "\nTidak ada metode dengan success rate 100%; "
            "tidak ada ceiling effect penuh."
        )

    table_path = os.path.join(
        output_directory, "tabel_ringkasan.csv"
    )
    save_summary_table(
        table_path, statistics_by_method, convergence
    )
    empirical_big_o(output_directory)

    print(f"\nTabel ringkasan disimpan ke {table_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
