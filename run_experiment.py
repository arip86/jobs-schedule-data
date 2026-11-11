#!/usr/bin/env python3
"""Menjalankan seluruh eksperimen perbandingan GA, SA, TS, dan acak."""

import argparse
import csv
import os
import random
import time
import tracemalloc
from typing import Dict, List, Sequence, Tuple

from jssp.data import FT06
from jssp.decoder import decode
from jssp.ga import run_ga
from jssp.operators import random_chromosome
from jssp.random_search import run_random_search
from jssp.sa import run_sa
from jssp.ts import run_ts
from jssp.validator import validate_schedule

FULL_BUDGET = 3000
QUICK_BUDGET = 300

FULL_SEEDS: Dict[str, List[int]] = {
    "GA": [2026, 2027, 2028, 2029, 2030],
    "SA": [2126, 2127, 2128, 2129, 2130],
    "TS": [2226, 2227, 2228, 2229, 2230],
    "acak": [2326, 2327, 2328, 2329, 2330],
}

RUNNERS = {
    "GA": run_ga,
    "SA": run_sa,
    "TS": run_ts,
    "acak": run_random_search,
}


def run_once(
    method: str,
    seed: int,
    budget: int,
    validate_each: bool = False,
):
    """Menjalankan satu metode dengan seed dan anggaran tertentu."""
    return RUNNERS[method](
        seed=seed,
        budget=budget,
        dataset=FT06,
        validate_each=validate_each,
    )


def collect_results(
    seeds_by_method: Dict[str, Sequence[int]], budget: int
) -> Dict[str, List[dict]]:
    """Menjalankan Pass A, B, dan C untuk seluruh run."""
    all_results: Dict[str, List[dict]] = {}

    for method, seeds in seeds_by_method.items():
        seeds = list(seeds)
        print(
            f"[{method}] warm-up + {len(seeds)} run x {budget} evaluasi",
            flush=True,
        )

        run_once(method, seeds[0], budget, validate_each=False)

        method_results = []
        for seed in seeds:
            result_a = run_once(
                method, seed, budget, validate_each=True
            )
            evaluator = result_a.evaluator

            if len(evaluator.validity) != budget or not all(
                evaluator.validity
            ):
                raise RuntimeError(
                    f"Evaluasi tidak valid pada {method} seed {seed}: "
                    f"{evaluator.first_invalid}"
                )

            if tracemalloc.is_tracing():
                raise RuntimeError(
                    "tracemalloc aktif saat pengukuran waktu"
                )
            start_time = time.perf_counter()
            result_b = run_once(
                method, seed, budget, validate_each=False
            )
            elapsed = time.perf_counter() - start_time

            if result_b.evaluator.history != evaluator.history:
                raise RuntimeError(
                    f"History Pass B berbeda pada {method} seed {seed}"
                )

            tracemalloc.start()
            try:
                result_c = run_once(
                    method, seed, budget, validate_each=False
                )
                _, peak = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()

            if result_c.evaluator.history != evaluator.history:
                raise RuntimeError(
                    f"History Pass C berbeda pada {method} seed {seed}"
                )

            valid_best, errors = validate_schedule(
                evaluator.best_schedule, FT06, evaluator.best_makespan
            )
            if not valid_best:
                raise RuntimeError(
                    f"Solusi terbaik tidak valid pada {method} seed "
                    f"{seed}: {errors}"
                )

            memory_kib = peak / 1024.0
            method_results.append(
                {
                    "method": method,
                    "seed": seed,
                    "result": result_a,
                    "time_s": elapsed,
                    "memory_kib": memory_kib,
                    "valid_best": valid_best,
                }
            )
            print(
                f"  seed {seed}: best={evaluator.best_makespan}, "
                f"eval_opt={evaluator.first_opt_eval}, "
                f"time={elapsed:.4f}s, mem={memory_kib:.2f}KiB",
                flush=True,
            )

        all_results[method] = method_results

    return all_results


def write_evaluation_csv(
    path: str, all_results: Dict[str, List[dict]], budget: int
) -> None:
    """Menulis evaluasi.csv sesuai format Lampiran B."""
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "metode",
                "seed",
                "evaluasi",
                "makespan",
                "best_so_far",
                "valid",
                "waktu_s",
                "memori_kib",
            ]
        )

        for method, runs in all_results.items():
            for run in runs:
                evaluator = run["result"].evaluator
                for index in range(budget):
                    is_last = index == budget - 1
                    writer.writerow(
                        [
                            method,
                            run["seed"],
                            index + 1,
                            evaluator.history[index],
                            evaluator.best_so_far[index],
                            evaluator.validity[index],
                            f"{run['time_s']:.6f}" if is_last else "",
                            f"{run['memory_kib']:.2f}"
                            if is_last
                            else "",
                        ]
                    )


def write_summary_csv(
    path: str, all_results: Dict[str, List[dict]]
) -> None:
    """Menulis ringkasan_run.csv."""
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "metode",
                "seed",
                "best_makespan",
                "eval_hingga_optimum",
                "valid_best",
                "waktu_s",
                "memori_kib",
            ]
        )

        for method, runs in all_results.items():
            for run in runs:
                evaluator = run["result"].evaluator
                writer.writerow(
                    [
                        method,
                        run["seed"],
                        evaluator.best_makespan,
                        evaluator.first_opt_eval
                        if evaluator.first_opt_eval is not None
                        else "",
                        run["valid_best"],
                        f"{run['time_s']:.6f}",
                        f"{run['memory_kib']:.2f}",
                    ]
                )


def validate_random_samples(
    output_directory: str,
    methods: Sequence[str],
    samples_per_method: int = 200,
) -> None:
    """Memvalidasi sampel kromosom acak per metode."""
    rows: List[Tuple[str, int, int]] = []
    n_jobs = len(FT06)
    ops_per_job = len(FT06[0])

    for index, method in enumerate(methods):
        rng = random.Random(9000 + index)
        valid_count = 0
        for _ in range(samples_per_method):
            chromosome = random_chromosome(rng, n_jobs, ops_per_job)
            schedule, makespan = decode(chromosome, FT06)
            valid, _ = validate_schedule(
                schedule, FT06, makespan
            )
            if valid:
                valid_count += 1
        rows.append((method, samples_per_method, valid_count))
        print(
            f"[validasi sampel] {method}: "
            f"{valid_count}/{samples_per_method} valid",
            flush=True,
        )

    path = os.path.join(output_directory, "validasi_sampel.csv")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metode", "jumlah_sampel", "jumlah_valid"])
        writer.writerows(rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Eksperimen perbandingan GA, SA, TS pada JSSP FT06"
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Direktori keluaran CSV (default: hasil/ atau hasil_quick/)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Smoke test: budget 300 dan 2 seed per metode",
    )
    args = parser.parse_args(argv)

    budget = QUICK_BUDGET if args.quick else FULL_BUDGET
    seeds_by_method = {
        method: (seeds[:2] if args.quick else seeds)
        for method, seeds in FULL_SEEDS.items()
    }

    if args.out is None:
        output_directory = "hasil_quick" if args.quick else "hasil"
    else:
        output_directory = args.out

    os.makedirs(output_directory, exist_ok=True)

    print(
        f"Mulai eksperimen: budget={budget}, metode={list(seeds_by_method)}",
        flush=True,
    )
    all_results = collect_results(seeds_by_method, budget)

    write_evaluation_csv(
        os.path.join(output_directory, "evaluasi.csv"),
        all_results,
        budget,
    )
    write_summary_csv(
        os.path.join(output_directory, "ringkasan_run.csv"),
        all_results,
    )
    validate_random_samples(
        output_directory, list(seeds_by_method.keys())
    )

    print(
        "Selesai. CSV ditulis ke "
        f"{os.path.normpath(output_directory)}/",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
