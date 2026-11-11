# ASUMSI DAN KEPUTUSAN IMPLEMENTASI

Dokumen ini mencatat asumsi yang diambil ketika spesifikasi memberi ruang
interpretasi. Parameter eksperimen tidak diubah dan tidak dituning.

## Dataset

1. Dataset utama adalah **FT06** (6 job x 6 mesin, 36 operasi) sesuai
   spesifikasi. Nilai acuan optimum `C_STAR = 55`, batas bawah sederhana 47.
2. File `10_4Jopshop` yang sudah ada di folder kerja **tidak dipakai** dalam
   pipeline utama. Baris pertamanya menyatakan `10000 10000` (job dan mesin),
   tetapi isi file hanya 100 baris x 100 angka. Untuk instance 10.000 x 10.000
   dibutuhkan 100.000.000 operasi, sehingga file tersebut tidak konsisten
   sebagai instance JSSP. File dibiarkan apa adanya.
3. Jika kelak file tersebut ingin dipakai, interpretasi cadangan yang
   didokumentasikan adalah: 100 baris = 100 job, 100 angka per baris = durasi
   pada mesin 0..99 dengan urutan kunjungan mesin tetap. Interpretasi ini tidak
   dipakai pada eksperimen sekarang.

## Representasi dan decoder

1. Kromosom adalah urutan 36 nomor job; setiap job muncul tepat 6 kali.
   Kemunculan ke-k job j adalah operasi ke-k job j.
2. Decoder membaca kromosom kiri ke kanan dan menyisipkan operasi ke **celah
   kosong paling awal** pada mesin tujuan yang muat durasi, dengan waktu mulai
   paling cepat sama dengan waktu selesai operasi sebelumnya pada job yang sama.
3. Daftar interval setiap mesin selalu dijaga terurut dan tidak tumpang tindih.
4. `makespan` adalah `max(end)` dari seluruh operasi.
5. Satu evaluasi = satu pemanggilan decoder + perhitungan makespan. Validator
   tidak dihitung sebagai evaluasi.
6. `Evaluator` memakai budget 3.000. Pemanggilan ketika `count >= budget`
   melempar `BudgetExhausted`; algoritma selalu memeriksa sisa budget sehingga
   `count` tidak pernah melebihi 3.000.
7. `first_opt_eval` adalah indeks evaluasi (mulai 1) ketika makespan pertama
   kali sama dengan 55. Jika tidak pernah tercapai, nilainya `None`.

## Validasi

1. Pass A menjalankan validator pada **setiap evaluasi**. Kolom `valid` di
   `evaluasi.csv` berisi hasil validasi jadwal evaluasi tersebut.
2. Validator juga dijalankan pada solusi terbaik setiap run dan pada 200
   kromosom acak per metode sebagai pemeriksaan tambahan.
3. Validator memeriksa: jumlah operasi, keunikan `(job, op_idx)`, kesesuaian
   mesin/durasi, durasi dan start, precedence job, tumpang tindih mesin, serta
   kesamaan makespan hasil hitung ulang dengan makespan decoder.

## Genetic Algorithm

1. Populasi awal 40 kromosom acak; setiap kromosom awal dievaluasi (40
   evaluasi).
2. Elitisme 1: elit tidak dievaluasi ulang. Satu generasi penuh menghasilkan
   39 anak, jadi 39 evaluasi.
3. Induk dipilih acak (independen) dari 50% populasi terbaik setelah sorting.
4. Crossover segmen dengan probabilitas 0,85; jika tidak, anak menyalin induk
   pertama. Mutasi swap dengan probabilitas 0,15.
5. Generasi terakhir dipotong sesuai sisa budget. Dengan budget 3.000:
   40 + 75 x 39 = 2.965 evaluasi, lalu 35 anak terakhir. Jumlah generasi yang
   dilaporkan adalah 76 (75 generasi penuh + 1 generasi parsial).
6. Crossover segmen: segmen `[a,b)` disalin dari induk pertama. Posisi di luar
   segmen diisi dengan gen dari induk kedua yang dipindai dari kiri ke kanan,
   dengan kuota kemunculan setiap job diambil dari induk pertama.

## Simulated Annealing

1. Evaluasi ke-1 adalah solusi awal. Loop berjalan untuk evaluasi ke-2 sampai
   ke-3.000.
2. Suhu pada evaluasi ke-e adalah `T(e) = 100 * 0.997^(e-1)`. Jadi suhu pada
   evaluasi 1.500 sekitar 1,1067 dan pada evaluasi 3.000 sekitar 0,01221.
3. Pendinginan diterapkan per evaluasi, bukan per epoch.
4. Tetangga dibentuk dengan menukar dua posisi yang berisi nomor job berbeda.
5. Penerimaan: `delta <= 0` atau `rng.random() < exp(-delta/T)`.

## Tabu Search

1. Satu evaluasi awal, lalu setiap iterasi membangkitkan hingga 30 pasangan
   posisi unik `(i,j)`, `i<j`, dengan gen berbeda.
2. Semua kandidat dievaluasi, lalu kandidat dipilih berdasarkan makespan
   terbaik yang tidak tabu. Kandidat tabu boleh dipilih jika makespannya lebih
   kecil dari best global sebelum iterasi (aspirasi).
3. Pasangan posisi dimasukkan ke tabu list dengan masa tabu 12 iterasi.
   Implementasi menyimpan `expiry = iterasi + 12`; pasangan dianggap tabu pada
   iterasi `t+1` sampai `t+12` inklusif.
4. Jika semua kandidat tabu dan tidak ada yang memenuhi aspirasi, kandidat
   terbaik dipilih apa adanya. Kejadian ini tidak dianggap error.
5. Iterasi terakhir memakai kandidat lebih sedikit bila sisa budget kurang dari
   30. Dengan budget 3.000, iterasi yang dilaporkan adalah 100.

## Eksperimen dan pengukuran

1. Full run: 4 metode x 5 seed = 20 run, masing-masing 3.000 evaluasi.
   Seed sesuai spesifikasi.
2. `--quick`: budget 300 dan 2 seed pertama per metode. Jika `--out` tidak
   diberikan, output quick ditulis ke `hasil_quick/` agar tidak menimpa hasil
   penuh. Jika `--out` diberikan, lokasi itu yang dipakai.
3. Pass A mengukur konvergensi, makespan, dan validitas tanpa `tracemalloc`.
4. Pass B mengukur waktu dengan `time.perf_counter()`, tanpa `tracemalloc`.
   Satu warm-up per metode dijalankan dan dibuang. Setiap seed diukur satu kali.
5. Pass C mengukur memori puncak dengan `tracemalloc` pada run terpisah.
   Angka `memori_kib` adalah puncak alokasi Python selama run, bukan total RAM
   proses atau sistem.
6. `waktu_s` dan `memori_kib` di `evaluasi.csv` hanya diisi pada baris evaluasi
   terakhir setiap run. Baris lain dikosongkan.
7. `eval_hingga_optimum` di `ringkasan_run.csv` dikosongkan bila run tidak
   mencapai 55. Pada analisis, run gagal tidak dihitung sebagai nol.
8. Semua run memakai instance `random.Random(seed)` sendiri; tidak ada
   `random.seed` global.
9. Replikasi Pass B/C memakai seed yang sama dan harus menghasilkan history
   yang identik dengan Pass A. Program akan berhenti dengan error bila tidak
   konsisten.

## Analisis

1. RPD dihitung sebagai `(Cmax - 55) / 55 * 100%`.
2. Simpangan baku memakai `statistics.stdev` (sampel).
3. Success rate adalah proporsi run dengan `best_makespan == 55`.
4. Tabel konvergensi memakai rata-rata `best_so_far` pada evaluasi 500, 1.000,
   2.000, dan 3.000. Pada mode quick, checkpoint yang tidak tersedia
   ditampilkan sebagai `-`.
5. Ceiling effect diperingatkan bila ada metode dengan success rate 100%.
6. Uji Big-O empiris memakai instance sintetis dengan `n = m` untuk
   `n = 4, 6, 8, 10, 12`. Setiap job mengunjungi semua mesin tepat sekali dalam
   urutan acak; durasi acak 1..99. Waktu satu decoding diukur setelah warm-up
   dan dibandingkan dengan `L^2 log L` hanya sebagai indikasi.

## Lain-lain

1. Bahasa implementasi Python 3.8+; lingkungan pengujian Python 3.10.14.
2. Hanya memakai standard library. Matplotlib hanya opsional di
   `plot_konvergensi.py` dan tidak dipakai di kode inti.
3. Tidak ada tuning parameter. Hasil yang tidak mencapai 55 dilaporkan apa
   adanya.
