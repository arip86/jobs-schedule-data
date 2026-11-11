"""Pemuatan dan pengolahan data hasil eksperimen JSSP untuk dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

METHOD_ORDER: List[str] = ["GA", "SA", "TS", "acak"]

REQUIRED_FILES: Dict[str, str] = {
    "evaluasi": "evaluasi.csv",
    "ringkasan_run": "ringkasan_run.csv",
    "tabel_ringkasan": "tabel_ringkasan.csv",
    "big_o": "big_o_empiris.csv",
    "validasi_sampel": "validasi_sampel.csv",
}

NUMERIC_EVALUASI_COLUMNS = [
    "evaluasi",
    "makespan",
    "best_so_far",
    "waktu_s",
    "memori_kib",
]

NUMERIC_RINGKASAN_COLUMNS = [
    "seed",
    "best_makespan",
    "eval_hingga_optimum",
    "waktu_s",
    "memori_kib",
]

NUMERIC_TABEL_COLUMNS = [
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

NUMERIC_BIG_O_COLUMNS = [
    "n_job",
    "n_mesin",
    "L",
    "waktu_decode_s",
    "rasio_L2logL",
]

NUMERIC_VALIDASI_COLUMNS = [
    "jumlah_sampel",
    "jumlah_valid",
]


def _as_bool(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .isin({"true", "1", "ya", "yes"})
    )


def _sort_by_method(
    dataframe: pd.DataFrame, extra_columns: Iterable[str] = ()
) -> pd.DataFrame:
    result = dataframe.copy()
    order = {method: index for index, method in enumerate(METHOD_ORDER)}
    result["_urutan_metode"] = result["metode"].map(order).fillna(99)
    sort_columns = ["_urutan_metode", *extra_columns]
    result = result.sort_values(sort_columns, kind="mergesort")
    return result.drop(columns="_urutan_metode").reset_index(drop=True)


def load_dashboard_data(data_directory: str) -> Dict[str, pd.DataFrame]:
    """Memuat seluruh CSV hasil dan mengembalikan DataFrame yang siap dipakai."""
    base = Path(data_directory)
    missing = [
        str(base / filename)
        for filename in REQUIRED_FILES.values()
        if not (base / filename).is_file()
    ]
    if missing:
        raise FileNotFoundError(
            "File hasil tidak ditemukan: " + ", ".join(missing)
        )

    evaluasi = pd.read_csv(base / REQUIRED_FILES["evaluasi"])
    ringkasan_run = pd.read_csv(base / REQUIRED_FILES["ringkasan_run"])
    tabel_ringkasan = pd.read_csv(
        base / REQUIRED_FILES["tabel_ringkasan"]
    )
    big_o = pd.read_csv(base / REQUIRED_FILES["big_o"])
    validasi_sampel = pd.read_csv(
        base / REQUIRED_FILES["validasi_sampel"]
    )

    for dataframe in (
        evaluasi,
        ringkasan_run,
        tabel_ringkasan,
        big_o,
        validasi_sampel,
    ):
        if "metode" in dataframe.columns:
            dataframe["metode"] = dataframe["metode"].astype(str)

    for column in NUMERIC_EVALUASI_COLUMNS:
        if column in evaluasi.columns:
            evaluasi[column] = pd.to_numeric(
                evaluasi[column], errors="coerce"
            )
    if "valid" in evaluasi.columns:
        evaluasi["valid"] = _as_bool(evaluasi["valid"])

    for column in NUMERIC_RINGKASAN_COLUMNS:
        if column in ringkasan_run.columns:
            ringkasan_run[column] = pd.to_numeric(
                ringkasan_run[column], errors="coerce"
            )
    if "valid_best" in ringkasan_run.columns:
        ringkasan_run["valid_best"] = _as_bool(
            ringkasan_run["valid_best"]
        )
    if "eval_hingga_optimum" in ringkasan_run.columns:
        ringkasan_run["eval_hingga_optimum"] = pd.to_numeric(
            ringkasan_run["eval_hingga_optimum"], errors="coerce"
        ).astype("Int64")

    for column in NUMERIC_TABEL_COLUMNS:
        if column in tabel_ringkasan.columns:
            tabel_ringkasan[column] = pd.to_numeric(
                tabel_ringkasan[column], errors="coerce"
            )

    for column in NUMERIC_BIG_O_COLUMNS:
        if column in big_o.columns:
            big_o[column] = pd.to_numeric(
                big_o[column], errors="coerce"
            )

    for column in NUMERIC_VALIDASI_COLUMNS:
        if column in validasi_sampel.columns:
            validasi_sampel[column] = pd.to_numeric(
                validasi_sampel[column], errors="coerce"
            )

    return {
        "evaluasi": _sort_by_method(
            evaluasi, extra_columns=["seed", "evaluasi"]
        ),
        "ringkasan_run": _sort_by_method(
            ringkasan_run, extra_columns=["seed"]
        ),
        "tabel_ringkasan": _sort_by_method(tabel_ringkasan),
        "big_o": big_o.sort_values("n_job").reset_index(drop=True),
        "validasi_sampel": _sort_by_method(validasi_sampel),
    }


def average_convergence(evaluasi: pd.DataFrame) -> pd.DataFrame:
    """Rata-rata best_so_far per metode pada setiap evaluasi."""
    result = (
        evaluasi.groupby(["metode", "evaluasi"], as_index=False)[
            "best_so_far"
        ]
        .mean()
        .rename(columns={"best_so_far": "rata_rata_best_so_far"})
    )
    return _sort_by_method(result, extra_columns=["evaluasi"])


def filter_methods(
    dataframe: pd.DataFrame, methods: Iterable[str]
) -> pd.DataFrame:
    """Menyaring DataFrame berdasarkan metode yang dipilih."""
    selected = list(methods)
    if not selected:
        return dataframe.iloc[0:0].copy()
    return dataframe[dataframe["metode"].isin(selected)].copy()


def downsample_convergence(
    evaluasi: pd.DataFrame, step: int = 10
) -> pd.DataFrame:
    """Mengambil sebagian titik evaluasi agar grafik per seed tetap ringan."""
    if step < 1:
        raise ValueError("step harus >= 1")
    last_evaluation = int(evaluasi["evaluasi"].max())
    mask = (evaluasi["evaluasi"] % step == 0) | (
        evaluasi["evaluasi"] == last_evaluation
    )
    return evaluasi[mask].copy()
