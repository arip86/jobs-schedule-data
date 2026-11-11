"""Dashboard Streamlit untuk hasil eksperimen JSSP FT06."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

import altair as alt
import pandas as pd
import streamlit as st

from dashboard_data import (
    METHOD_ORDER,
    average_convergence,
    downsample_convergence,
    filter_methods,
    load_dashboard_data,
)

try:
    from jssp.data import C_STAR
except ImportError:
    C_STAR = 55

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(
    os.environ.get("JSSP_DATA_DIR", BASE_DIR / "hasil")
).expanduser()
DEFAULT_OPTIMUM = C_STAR if C_STAR is not None else 55
OPTIMUM = int(os.environ.get("JSSP_OPTIMUM", str(DEFAULT_OPTIMUM)))

METHOD_COLORS = ["#2563eb", "#16a34a", "#ea580c", "#7c3aed"]
METHOD_SCALE = alt.Scale(domain=METHOD_ORDER, range=METHOD_COLORS)

RINGKASAN_RENAME = {
    "metode": "Metode",
    "best_makespan": "Best",
    "mean_makespan": "Mean",
    "stdev_makespan": "Stdev",
    "success_rate": "Success rate",
    "rpd_mean_pct": "RPD mean (%)",
    "rpd_best_pct": "RPD best (%)",
    "eval_hingga_optimum_mean": "Eval optimum (mean)",
    "run_mencapai_optimum": "Run mencapai optimum",
    "run_gagal": "Run gagal",
    "waktu_s_mean": "Waktu (s)",
    "memori_kib_mean": "Memori (KiB)",
    "conv_500": "Conv 500",
    "conv_1000": "Conv 1.000",
    "conv_2000": "Conv 2.000",
    "conv_3000": "Conv 3.000",
}

RUN_RENAME = {
    "metode": "Metode",
    "seed": "Seed",
    "best_makespan": "Best makespan",
    "eval_hingga_optimum": "Eval hingga optimum",
    "mencapai_optimum": "Mencapai optimum",
    "valid_best": "Best valid",
    "waktu_s": "Waktu (s)",
    "memori_kib": "Memori (KiB)",
}

BIG_O_RENAME = {
    "n_job": "Job",
    "n_mesin": "Mesin",
    "L": "Operasi L",
    "waktu_decode_s": "Waktu decode (s)",
    "rasio_L2logL": "Rasio L^2 log L",
}

VALIDASI_RENAME = {
    "metode": "Metode",
    "jumlah_sampel": "Jumlah sampel",
    "jumlah_valid": "Jumlah valid",
}


@st.cache_data(show_spinner="Memuat data hasil eksperimen...")
def load_cached(data_directory: str):
    return load_dashboard_data(data_directory)


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.6rem; padding-bottom: 2rem; }
        [data-testid="stMetricValue"] { font-size: 1.75rem; }
        [data-testid="stMetricLabel"] { font-size: 0.85rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def method_color(
    field: str = "metode", legend_title: str = "Metode"
) -> alt.Color:
    return alt.Color(
        f"{field}:N",
        scale=METHOD_SCALE,
        legend=alt.Legend(title=legend_title),
    )


def bar_chart(
    dataframe: pd.DataFrame,
    value_column: str,
    title: str,
    y_title: str,
    percent_axis: bool = False,
) -> alt.Chart:
    axis = alt.Axis(format="%") if percent_axis else alt.Axis()
    return (
        alt.Chart(dataframe)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("metode:N", sort=METHOD_ORDER, title="Metode"),
            y=alt.Y(f"{value_column}:Q", title=y_title, axis=axis),
            color=method_color(legend_title="Metode"),
            tooltip=[
                alt.Tooltip("metode:N", title="Metode"),
                alt.Tooltip(
                    f"{value_column}:Q",
                    title=title,
                    format=".4f" if not percent_axis else ".2%",
                ),
            ],
        )
        .properties(height=300, title=title)
    )


def render_sidebar() -> List[str]:
    with st.sidebar:
        st.header("Kontrol")
        st.caption(f"Sumber data: `{DATA_DIR}`")
        selected_methods = st.multiselect(
            "Metode",
            options=METHOD_ORDER,
            default=METHOD_ORDER,
        )
        if st.button("Muat ulang data", width="stretch"):
            st.cache_data.clear()
        st.divider()
        st.markdown(f"**Optimum acuan:** {OPTIMUM}")
        st.markdown("**Budget:** 3.000 evaluasi/run")
        st.markdown("**Seed:** 5 run per metode")
        st.divider()
        with st.expander("Catatan data"):
            st.write(
                "Waktu dan memori diambil dari ringkasan run. "
                "Nilai memori adalah puncak alokasi Python, bukan "
                "pemakaian RAM sistem."
            )
            st.write(
                "Kurva per seed ditampilkan dengan downsampling "
                "setiap 10 evaluasi agar dashboard tetap ringan."
            )
    return selected_methods


def render_overview(
    summary: pd.DataFrame,
    runs: pd.DataFrame,
    evaluasi: pd.DataFrame,
    validasi: pd.DataFrame,
) -> None:
    best = int(runs["best_makespan"].min()) if not runs.empty else None
    total_evaluations = len(evaluasi)
    valid_evaluations = int(evaluasi["valid"].sum())
    valid_percent = (
        valid_evaluations / total_evaluations * 100
        if total_evaluations
        else 0.0
    )
    valid_best = int(runs["valid_best"].sum())
    sample_total = int(validasi["jumlah_sampel"].sum())
    sample_valid = int(validasi["jumlah_valid"].sum())

    columns = st.columns(6)
    columns[0].metric("Makespan terbaik", best if best is not None else "-")
    columns[1].metric("Total run", f"{len(runs):,}")
    columns[2].metric("Total evaluasi", f"{total_evaluations:,}")
    columns[3].metric("Evaluasi valid", f"{valid_percent:.1f}%")
    columns[4].metric("Best valid", f"{valid_best}/{len(runs)}")
    columns[5].metric(
        "Sampel valid", f"{sample_valid}/{sample_total}"
    )

    st.subheader("Ringkasan per metode")
    summary_display = summary.copy()
    if "success_rate" in summary_display.columns:
        summary_display["success_rate"] = (
            summary_display["success_rate"] * 100.0
        )
    summary_display = summary_display.rename(columns=RINGKASAN_RENAME)
    st.dataframe(
        summary_display.round(3),
        width="stretch",
        hide_index=True,
    )

    ceiling_methods = summary.loc[
        summary["success_rate"] >= 1.0, "metode"
    ].tolist()
    if ceiling_methods:
        st.info(
            "Ceiling effect terdeteksi: "
            + ", ".join(ceiling_methods)
            + " mencapai success rate 100% pada budget ini."
        )
    if valid_percent == 100.0 and valid_best == len(runs):
        st.success(
            "Seluruh evaluasi dan solusi terbaik pada filter ini valid."
        )


def render_comparison(
    summary: pd.DataFrame, runs: pd.DataFrame
) -> None:
    st.subheader("Perbandingan makespan")
    makespan_long = summary.melt(
        id_vars="metode",
        value_vars=[
            "best_makespan",
            "mean_makespan",
            "stdev_makespan",
        ],
        var_name="Metrik",
        value_name="Nilai",
    )
    makespan_chart = (
        alt.Chart(makespan_long)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("metode:N", sort=METHOD_ORDER, title="Metode"),
            xOffset=alt.XOffset(
                "Metrik:N",
                sort=[
                    "best_makespan",
                    "mean_makespan",
                    "stdev_makespan",
                ],
            ),
            y=alt.Y("Nilai:Q", title="Makespan"),
            color=alt.Color(
                "Metrik:N",
                scale=alt.Scale(
                    range=["#1d4ed8", "#60a5fa", "#bfdbfe"]
                ),
                legend=alt.Legend(title="Metrik"),
            ),
            tooltip=[
                alt.Tooltip("metode:N", title="Metode"),
                alt.Tooltip("Metrik:N", title="Metrik"),
                alt.Tooltip("Nilai:Q", title="Nilai", format=".4f"),
            ],
        )
        .properties(height=320)
    )
    st.altair_chart(makespan_chart, width="stretch")

    left, right = st.columns(2)
    with left:
        st.altair_chart(
            bar_chart(
                summary,
                "success_rate",
                "Success rate per metode",
                "Success rate",
                percent_axis=True,
            ),
            width="stretch",
        )
    with right:
        st.altair_chart(
            bar_chart(
                summary,
                "rpd_mean_pct",
                "RPD mean per metode",
                "RPD mean (%)",
            ),
            width="stretch",
        )

    left, right = st.columns(2)
    with left:
        st.altair_chart(
            bar_chart(
                summary,
                "waktu_s_mean",
                "Waktu rata-rata per metode",
                "Waktu (s)",
            ),
            width="stretch",
        )
    with right:
        st.altair_chart(
            bar_chart(
                summary,
                "memori_kib_mean",
                "Memori rata-rata per metode",
                "Memori (KiB)",
            ),
            width="stretch",
        )

    st.subheader("Distribusi best makespan per run")
    scatter = (
        alt.Chart(runs)
        .mark_circle(size=130, opacity=0.85)
        .encode(
            x=alt.X("metode:N", sort=METHOD_ORDER, title="Metode"),
            y=alt.Y(
                "best_makespan:Q",
                title="Best makespan",
                scale=alt.Scale(zero=False),
            ),
            color=method_color(legend_title="Metode"),
            tooltip=[
                alt.Tooltip("metode:N", title="Metode"),
                alt.Tooltip("seed:Q", title="Seed"),
                alt.Tooltip(
                    "best_makespan:Q", title="Best makespan"
                ),
                alt.Tooltip(
                    "eval_hingga_optimum:Q",
                    title="Eval hingga optimum",
                ),
            ],
        )
        .properties(height=320)
    )
    st.altair_chart(scatter, width="stretch")


def render_convergence(
    evaluasi: pd.DataFrame, summary: pd.DataFrame
) -> None:
    st.subheader("Konvergensi rata-rata")
    show_seed_curves = st.checkbox(
        "Tampilkan kurva tiap seed", value=False
    )

    optimum_rule = (
        alt.Chart(pd.DataFrame({"optimum": [OPTIMUM]}))
        .mark_rule(strokeDash=[6, 4], color="#111827")
        .encode(y=alt.Y("optimum:Q", title="Best so far"))
    )

    if show_seed_curves:
        sampled = downsample_convergence(evaluasi, step=10)
        chart = (
            alt.Chart(sampled)
            .mark_line(opacity=0.35, strokeWidth=1)
            .encode(
                x=alt.X("evaluasi:Q", title="Evaluasi"),
                y=alt.Y("best_so_far:Q", title="Best so far"),
                color=method_color(legend_title="Metode"),
                detail=alt.Detail("seed:N"),
                tooltip=[
                    alt.Tooltip("metode:N", title="Metode"),
                    alt.Tooltip("seed:Q", title="Seed"),
                    alt.Tooltip("evaluasi:Q", title="Evaluasi"),
                    alt.Tooltip(
                        "best_so_far:Q", title="Best so far"
                    ),
                ],
            )
        )
        st.caption(
            "Kurva per seed ditampilkan setiap 10 evaluasi. "
            "Garis penuh menunjukkan nilai optimum."
        )
    else:
        convergence = average_convergence(evaluasi)
        chart = (
            alt.Chart(convergence)
            .mark_line(strokeWidth=2.5)
            .encode(
                x=alt.X("evaluasi:Q", title="Evaluasi"),
                y=alt.Y(
                    "rata_rata_best_so_far:Q",
                    title="Rata-rata best so far",
                ),
                color=method_color(legend_title="Metode"),
                tooltip=[
                    alt.Tooltip("metode:N", title="Metode"),
                    alt.Tooltip("evaluasi:Q", title="Evaluasi"),
                    alt.Tooltip(
                        "rata_rata_best_so_far:Q",
                        title="Rata-rata best so far",
                    ),
                ],
            )
        )
        st.caption(
            f"Rata-rata 5 run per metode. Garis putus-putus = "
            f"optimum {OPTIMUM}."
        )

    st.altair_chart(
        (chart + optimum_rule).properties(height=420),
        width="stretch",
    )

    checkpoint_columns = [
        "metode",
        "conv_500",
        "conv_1000",
        "conv_2000",
        "conv_3000",
    ]
    if all(column in summary for column in checkpoint_columns):
        checkpoints = summary[checkpoint_columns].rename(
            columns={
                "metode": "Metode",
                "conv_500": "Eval 500",
                "conv_1000": "Eval 1.000",
                "conv_2000": "Eval 2.000",
                "conv_3000": "Eval 3.000",
            }
        )
        st.subheader("Checkpoint konvergensi")
        st.dataframe(
            checkpoints.round(3),
            width="stretch",
            hide_index=True,
        )


def render_runs(runs: pd.DataFrame) -> None:
    st.subheader("Detail 20 run")
    display = runs.copy()
    display["mencapai_optimum"] = display[
        "eval_hingga_optimum"
    ].notna().map({True: "Ya", False: "Tidak"})
    display = display.rename(columns=RUN_RENAME)

    sort_options = [
        "Metode",
        "Seed",
        "Best makespan",
        "Eval hingga optimum",
        "Waktu (s)",
        "Memori (KiB)",
    ]
    left, right = st.columns([3, 1])
    with left:
        sort_column = st.selectbox(
            "Urutkan berdasarkan", sort_options, index=2
        )
    with right:
        ascending = st.checkbox("Urutan naik", value=True)

    display = display.sort_values(
        sort_column, ascending=ascending, na_position="last"
    )
    st.dataframe(
        display.round(3),
        width="stretch",
        hide_index=True,
    )
    st.download_button(
        "Unduh CSV run terfilter",
        data=display.to_csv(index=False).encode("utf-8"),
        file_name="ringkasan_run_filtered.csv",
        mime="text/csv",
    )


def render_big_o(big_o: pd.DataFrame) -> None:
    st.subheader("Kompleksitas empiris")
    st.caption(
        "Pengukuran memakai instance sintetis 4x4 sampai 12x12, "
        "bukan instance FT06."
    )
    left, right = st.columns(2)
    with left:
        time_chart = (
            alt.Chart(big_o)
            .mark_line(point=alt.OverlayMarkDef(size=80), color="#2563eb")
            .encode(
                x=alt.X(
                    "L:Q",
                    title="Jumlah operasi L",
                    scale=alt.Scale(type="log"),
                ),
                y=alt.Y(
                    "waktu_decode_s:Q",
                    title="Waktu decode (s)",
                    scale=alt.Scale(type="log"),
                ),
                tooltip=[
                    alt.Tooltip("n_job:Q", title="Job"),
                    alt.Tooltip("n_mesin:Q", title="Mesin"),
                    alt.Tooltip("L:Q", title="L"),
                    alt.Tooltip(
                        "waktu_decode_s:Q",
                        title="Waktu decode (s)",
                        format=".9f",
                    ),
                ],
            )
            .properties(height=340)
        )
        st.altair_chart(time_chart, width="stretch")
    with right:
        ratio_chart = (
            alt.Chart(big_o)
            .mark_line(point=alt.OverlayMarkDef(size=80), color="#7c3aed")
            .encode(
                x=alt.X(
                    "L:Q",
                    title="Jumlah operasi L",
                    scale=alt.Scale(type="log"),
                ),
                y=alt.Y(
                    "rasio_L2logL:Q",
                    title="Waktu / (L^2 log L)",
                    scale=alt.Scale(type="log"),
                ),
                tooltip=[
                    alt.Tooltip("L:Q", title="L"),
                    alt.Tooltip(
                        "rasio_L2logL:Q",
                        title="Rasio",
                        format=".3e",
                    ),
                ],
            )
            .properties(height=340)
        )
        st.altair_chart(ratio_chart, width="stretch")

    big_o_display = big_o.rename(columns=BIG_O_RENAME)
    st.dataframe(
        big_o_display,
        width="stretch",
        hide_index=True,
    )


def render_validation(
    evaluasi: pd.DataFrame,
    runs: pd.DataFrame,
    validasi: pd.DataFrame,
) -> None:
    st.subheader("Validasi")
    total_evaluations = len(evaluasi)
    valid_evaluations = int(evaluasi["valid"].sum())
    invalid = evaluasi[~evaluasi["valid"]]

    left, middle, right = st.columns(3)
    left.metric(
        "Evaluasi valid",
        f"{valid_evaluations}/{total_evaluations}",
    )
    middle.metric(
        "Best valid", f"{int(runs['valid_best'].sum())}/{len(runs)}"
    )
    right.metric(
        "Sampel valid",
        f"{int(validasi['jumlah_valid'].sum())}/"
        f"{int(validasi['jumlah_sampel'].sum())}",
    )

    if invalid.empty:
        st.success("Tidak ada evaluasi yang tidak valid.")
    else:
        st.error(
            f"Ditemukan {len(invalid)} evaluasi tidak valid."
        )
        st.dataframe(
            invalid.head(20),
            width="stretch",
            hide_index=True,
        )

    st.subheader("Validasi sampel acak")
    st.dataframe(
        validasi.rename(columns=VALIDASI_RENAME),
        width="stretch",
        hide_index=True,
    )

    st.subheader("Validitas solusi terbaik")
    best_valid = runs[["metode", "seed", "valid_best"]].rename(
        columns={
            "metode": "Metode",
            "seed": "Seed",
            "valid_best": "Best valid",
        }
    )
    st.dataframe(
        best_valid,
        width="stretch",
        hide_index=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="Dashboard JSSP FT06",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()

    st.title("Dashboard Hasil Eksperimen JSSP FT06")
    st.caption(
        "Perbandingan Genetic Algorithm, Simulated Annealing, "
        "Tabu Search, dan pencarian acak berdasarkan makespan, "
        "konvergensi, waktu, memori, dan kompleksitas empiris."
    )

    selected_methods = render_sidebar()
    if not selected_methods:
        st.warning("Pilih minimal satu metode pada sidebar.")
        st.stop()

    try:
        data = load_cached(str(DATA_DIR))
    except FileNotFoundError as error:
        st.error(str(error))
        st.info(
            "Pastikan folder hasil/ ikut diunggah ke repositori "
            "Streamlit Cloud. Jalankan run_experiment.py dan "
            "analyze.py terlebih dahulu bila file belum ada."
        )
        st.stop()
    except Exception as error:
        st.error(f"Gagal memuat data: {error}")
        st.stop()

    evaluasi = filter_methods(data["evaluasi"], selected_methods)
    runs = filter_methods(data["ringkasan_run"], selected_methods)
    summary = filter_methods(
        data["tabel_ringkasan"], selected_methods
    )
    validasi = filter_methods(
        data["validasi_sampel"], selected_methods
    )
    big_o = data["big_o"]

    if evaluasi.empty or runs.empty or summary.empty:
        st.warning(
            "Tidak ada data untuk metode yang dipilih."
        )
        st.stop()

    render_overview(summary, runs, evaluasi, validasi)

    tabs = st.tabs(
        [
            "Perbandingan",
            "Konvergensi",
            "Detail Run",
            "Big-O",
            "Validasi",
        ]
    )
    with tabs[0]:
        render_comparison(summary, runs)
    with tabs[1]:
        render_convergence(evaluasi, summary)
    with tabs[2]:
        render_runs(runs)
    with tabs[3]:
        render_big_o(big_o)
    with tabs[4]:
        render_validation(evaluasi, runs, validasi)

    st.divider()
    st.caption(
        "Sumber: evaluasi.csv, ringkasan_run.csv, "
        "tabel_ringkasan.csv, big_o_empiris.csv, dan "
        "validasi_sampel.csv. Dashboard bersifat snapshot; "
        "jalankan ulang setelah data berubah."
    )


if __name__ == "__main__":
    main()
