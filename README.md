# Perbandingan GA, SA, dan TS pada JSSP FT06

Implementasi eksperimen proposal:

**Analisis Perbandingan Kinerja Genetic Algorithm, Simulated Annealing, dan
Tabu Search pada Job Shop Scheduling Problem Berdasarkan Makespan dan
Kompleksitas Komputasi**

## Lingkungan

- Python 3.8+ (diuji dengan **Python 3.10.14**)
- Hanya standard library untuk kode inti
- Lingkungan pengujian: **macOS 26.7.1**, **Apple M5**, **16 GB RAM**, arm64
- `matplotlib` hanya opsional untuk `plot_konvergensi.py`

## Struktur

```text
jssp/                  # data, decoder, validator, operator, algoritma
tests/                 # unit test dan integration test
run_experiment.py      # eksperimen 4 metode, ekspor CSV
analyze.py             # statistik, RPD, konvergensi, Big-O empiris
plot_konvergensi.py    # plot opsional
streamlit_app.py       # dashboard Streamlit
dashboard_data.py      # pemuatan dan pengolahan data dashboard
requirements.txt       # dependensi dashboard Streamlit Cloud
.streamlit/            # tema dashboard
ASUMSI.md              # asumsi dan keputusan implementasi
hasil/                 # hasil eksperimen penuh
hasil_quick/           # hasil smoke test
```

## Menjalankan tes

Dari folder proyek:

```bash
python3 -m unittest discover -s tests -v
```

## Menjalankan eksperimen

Smoke test (budget 300, 2 seed per metode, default output `hasil_quick/`):

```bash
python3 run_experiment.py --quick
```

Eksperimen penuh (4 metode x 5 seed x 3.000 evaluasi, default output
`hasil/`):

```bash
python3 run_experiment.py --out hasil/
```

Output utama:

- `hasil/evaluasi.csv`: 60.000 baris evaluasi (20 run x 3.000).
- `hasil/ringkasan_run.csv`: 20 baris ringkasan run.
- `hasil/validasi_sampel.csv`: validasi 200 kromosom acak per metode.

`waktu_s` dan `memori_kib` di `evaluasi.csv` hanya diisi pada baris evaluasi
terakhir setiap run.

## Analisis

```bash
python3 analyze.py --input hasil/
```

Menghasilkan tabel ringkasan di layar dan `hasil/tabel_ringkasan.csv`, termasuk
RPD, success rate, evaluasi hingga optimum, konvergensi pada evaluasi
500/1.000/2.000/3.000, deteksi ceiling effect, dan cek Big-O empiris
(`hasil/big_o_empiris.csv`).

Plot opsional:

```bash
python3 plot_konvergensi.py --input hasil/
```

Jika `matplotlib` tidak terpasang, skrip akan melewati plot tanpa error.

## Dashboard Streamlit

Dashboard membaca CSV di `hasil/` dan menampilkan ringkasan, perbandingan
metode, konvergensi, detail 20 run, Big-O empiris, dan validasi.

Jalankan secara lokal:

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run streamlit_app.py
```

Deploy ke Streamlit Community Cloud:

1. Unggah repositori ini ke GitHub, termasuk folder `hasil/`.
2. Buat aplikasi baru di Streamlit Community Cloud.
3. Isi **Main file path** dengan `streamlit_app.py`.
4. Streamlit akan memasang dependensi dari `requirements.txt`.
5. Klik **Deploy**.

Lokasi data dan nilai optimum dapat diubah lewat environment variable:

```bash
JSSP_DATA_DIR=hasil JSSP_OPTIMUM=55 python3 -m streamlit run streamlit_app.py
```

Kode inti eksperimen tetap hanya memakai standard library. Dependensi
Streamlit, pandas, dan Altair hanya dipakai oleh dashboard.

## Parameter eksperimen

- FT06: 6 job x 6 mesin, 36 operasi, total durasi 197, `C* = 55`.
- Budget: 3.000 evaluasi per run; satu evaluasi = satu decoder + makespan.
- GA: populasi 40, elit 1, parent dari 50% terbaik, `pc=0.85`, `pm=0.15`.
- SA: `T0=100`, `alpha=0.997` per evaluasi.
- TS: hingga 30 tetangga unik per iterasi, tenure 12, aspirasi global.
- Seed: GA 2026–2030, SA 2126–2130, TS 2226–2230, acak 2326–2330.

## Catatan keterbatasan

- Hanya satu instance (FT06) dan 5 run per metode; tidak ada uji signifikansi.
- Hasil tidak boleh digunakan untuk menyimpulkan satu algoritma terbaik secara
  umum.
- Waktu dan memori bergantung pada mesin dan versi Python.
- File `10_4Jopshop` tidak dipakai karena tidak konsisten sebagai instance
  FT06; lihat `ASUMSI.md`.
