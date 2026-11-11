#!/usr/bin/env python3
"""Plot konvergensi opsional (membutuhkan matplotlib)."""

import argparse
import csv
import os
from typing import Dict, List

from jssp.data import C_STAR


def read_evaluation_rows(path: str) -> List[dict]:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Plot rata-rata best_so_far per metode"
    )
    parser.add_argument(
        "--input",
        default="hasil",
        help="Direktori berisi evaluasi.csv",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Path file gambar (default: <input>/konvergensi.png)",
    )
    args = parser.parse_args(argv)

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print(
            "matplotlib tidak terpasang; plot dilewati. "
            "Kode inti tetap berjalan tanpa matplotlib."
        )
        return 0

    input_path = os.path.join(args.input, "evaluasi.csv")
    if not os.path.exists(input_path):
        print(f"File tidak ditemukan: {input_path}")
        return 1

    rows = read_evaluation_rows(input_path)
    values: Dict[str, Dict[int, List[int]]] = {}
    methods: List[str] = []

    for row in rows:
        method = row["metode"]
        evaluation = int(row["evaluasi"])
        if method not in values:
            methods.append(method)
            values[method] = {}
        values[method].setdefault(evaluation, []).append(
            int(row["best_so_far"])
        )

    for method in methods:
        evaluations = sorted(values[method])
        averages = [
            sum(values[method][evaluation])
            / len(values[method][evaluation])
            for evaluation in evaluations
        ]
        plt.plot(evaluations, averages, label=method)

    plt.axhline(
        y=C_STAR, color="black", linestyle="--", linewidth=1, label="Optimum 55"
    )
    plt.xlabel("Evaluasi")
    plt.ylabel("Rata-rata best_so_far")
    plt.title("Konvergensi GA, SA, TS, dan Pencarian Acak pada FT06")
    plt.legend()
    plt.tight_layout()

    output_path = args.out or os.path.join(
        args.input, "konvergensi.png"
    )
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Plot disimpan ke {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
