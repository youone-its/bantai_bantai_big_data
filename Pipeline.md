# Pipeline Big Data — Audit Kapasitas Pendidikan & Rekomendasi USB/RKB (Open Data Surabaya)

Dokumentasi end-to-end pipeline data: dari ingestion CKAN API → Kafka → HDFS →
Medallion Lakehouse (Delta Lake) → Backend API → Frontend.

## 1. Tujuan

Mengintegrasikan dataset pendidikan Kota Surabaya untuk:
1. **Audit kapasitas** pendidikan per kecamatan.
2. **Proyeksi** kebutuhan bangku sekolah 2025–2030 (metode *cohort survival*).
3. **Estimasi** jumlah siswa yang berpotensi tidak tertampung (gap).
4. **Rekomendasi** prioritas **USB** (Unit Sekolah Baru) & **RKB** (Ruang Kelas Baru).

## 2. Arsitektur

```
 CKAN API (ckan.surabaya.go.id)          [7 resource dataset pendidikan]
        │  producer_open_data.py (host/venv)
        ▼
 Kafka (KRaft, 7 topik sby-*)            container: kafka-broker
        │  consumer_to_hdfs.py (host/venv) — docker cp + hdfs -put
        ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │  HADOOP (HDFS)            container: hadoop-namenode / datanode     │
 │                                                                     │
 │  /data/opendata-sby/      ← raw JSON dari Kafka consumer           │
 │                                                                     │
 │  MEDALLION LAKEHOUSE (Delta Lake) ← →  Spark   (2 arah, tiap step)│
 │  ┌──────────────────────────────────────────────────────────┐      │
 │  │  /lakehouse/bronze   raw + metadata                      │      │
 │  │         ↑ WRITE                  READ ↓                  │      │
 │  │  Spark (01_bronze.py) ──────────► Spark (02_silver.py)  │      │
 │  │         ↑ WRITE                  READ ↓                  │      │
 │  │  /lakehouse/silver   bersih, ternormalisasi, dedup        │      │
 │  │         ↑ WRITE                  READ ↓                  │      │
 │  │  Spark (02_silver.py) ──────────► Spark (03_gold.py)     │      │
 │  │         ↑ WRITE                  READ ↓                  │      │
 │  │  /lakehouse/gold     data mart analitik + DSS Analysis 2  │      │
 │  │         ↑ WRITE (08_analysis2.py menambah 3 tabel Gold)  │      │
 │  └──────────────────────────────────────────────────────────┘      │
 │                                                                     │
 └──────────────────┬──────────────────────────────────────────────────┘
                    │
          ┌─────────┴──────────┐
          │ WebHDFS (port 9870) │  Backend membaca Gold via pyarrow
          └─────────┬──────────┘
                    │
          ┌─────────▼──────────┐       ┌─────────────────────────────┐
          │  Backend FastAPI    │       │  Analytics Notebooks (01-06) │
          │  (:8000)           │       │  baca CSV dari exports/      │
          │  v2.1 — 8 endpoint │       │  + notebook 06: GeoPandas,   │
          └─────────┬──────────┘       │    Geopy, OSRM routing       │
                    │                  └─────────────────────────────┘
          ┌─────────▼──────────┐
          │     Frontend       │       container: etsbd-frontend (web/FE)
          └────────────────────┘
```

**Penempatan komponen (penting):**

| Komponen | Jalan di | Alasan |
|---|---|---|
| Kafka, Hadoop (NN/DN/RM/NM) | Container | layanan infrastruktur |
| Producer & Consumer | **Host** (venv) | consumer memakai `docker cp`/`docker exec` ke namenode |
| Bronze/Silver/Gold/Time-Travel/DQ | Container `spark-medallion` | runtime Spark 3.5 + Delta 3.1 |
| Backend API | Container `etsbd-backend` | baca Gold via WebHDFS |

> Folder `spark/` lama (orphan, kosong) sudah **dihapus**. Semua analitik Spark
> hidup di dalam `medallion/` dan dijalankan di container `spark-medallion`.

## 3. Dataset Raw (CKAN)

| Topik Kafka / folder HDFS | Dataset | Baris |
|---|---|---|
| `sby-penduduk-usia` | Jumlah penduduk per usia (level kelurahan, snapshot Mar 2025) | 153 |
| `sby-sekolah-akreditasi` | Profil & akreditasi per sekolah | 3.162 |
| `sby-sekolah-negeri-swasta` | Jumlah sekolah negeri/swasta per kecamatan | 1.612 |
| `sby-siswa-negeri-swasta` | Jumlah siswa negeri/swasta per kecamatan | 1.643 |
| `sby-sd-akreditasi-kecamatan` | SD per peringkat akreditasi per kecamatan | 1.581 |
| `sby-smp-akreditasi-kecamatan` | SMP per peringkat akreditasi per kecamatan | 1.581 |
| `sby-sekolah-murid-guru-rasio` | Sekolah/murid/guru/rasio per kecamatan | 1.500 |

Grain dataset per-kecamatan: `kecamatan × periode(bulan) × tahun` (2022–2026).

## 4. Medallion Architecture

### Bronze (`01_bronze.py`)
- Baca JSON mentah dari HDFS → tulis Delta apa adanya + metadata
  (`_ingested_at`, `_source`, `_hdfs_source`).
- Tidak ada transformasi (raw fidelity).

### Silver (`02_silver.py`) — pembersihan & standardisasi
- Trim semua kolom string.
- `kecamatan_norm` : buang prefix `Kec.`/`Kel.`, rapikan spasi, UPPER (untuk tampilan).
- `kecamatan_key`  : tanpa spasi — **kunci join andal** (menyatukan `ASEM ROWO` vs `ASEMROWO`).
- `periode_norm`   : standardisasi nama bulan ke Title Case (24 variasi → 12 bulan).
- Dedup pada grain yang benar:
  - per-kecamatan → `kecamatan_key + periode_norm + tahun`
  - penduduk → `kecamatan_key + nama_kelurahan + data_bulan + data_tahun`
  - akreditasi → `kode_sekolah + tahun`

### Gold (`03_gold.py`) — data mart analitik
| Tabel Gold | Isi |
|---|---|
| `gold_demand_proyeksi` | Proyeksi demand SD(7–12)/SMP(13–15) per kecamatan 2025–2030 |
| `gold_kapasitas_kecamatan` | Audit kapasitas: pagu, murid aktual, ruang kelas, rombel, jumlah sekolah |
| `gold_gap_analysis` | demand − kapasitas, siswa tak tertampung, utilisasi % |
| `gold_rekomendasi_usb_rkb` | Skor & ranking prioritas, label USB/RKB/CUKUP, estimasi RKB |
| `gold_data_quality_report` | Hasil pemeriksaan kualitas data |
| `sby_*_summary` / `sby_*_per_kecamatan` | Tabel deskriptif pendukung |

### DSS Layer — Analysis 2 (`08_analysis2.py`) — PIC: Ni'mah

Script PySpark tambahan yang mem-produce 3 tabel Gold baru + 9 CSV export:

| Tabel Gold | Isi |
|---|---|
| `gold_school_capacity_gap_index` | SCGI per kecamatan (skor komposit 0–100 defisit kapasitas sekolah) |
| `gold_cluster_priority` | K-Means clustering (K=4) prioritas intervensi per kecamatan |
| `gold_evaluation_metrics` | Evaluasi model: MAPE, Silhouette Score, Davies-Bouldin Index |

**Formula SCGI:**
```
SCGI = 0.50 × deficit_rate + 0.30 × utilisasi_norm + 0.20 × growth_rate

deficit_rate   = max(0, demand_2030 − kapasitas) / demand_2030
uttilisasi_norm = min(utilisasi_2030 / 200, 1.0)
growth_rate    = max(0, (demand_2030 − demand_2025) / demand_2025), cap 1.0

Kategori: KRITIS ≥70 | TINGGI ≥50 | SEDANG ≥30 | RENDAH >0 | AMAN ≤0
```

**K-Means (K=4)** menggunakan fitur: `deficit_rate`, `utilisasi_norm`, `growth_rate`, `scgi_raw`

Priority rank ditetapkan berdasarkan rata-rata fitur cluster → KRITIS/TINGGI/SEDANG/RENDAH

**CSV Exports** (dibaca Analytics Notebooks):
```
medallion/exports/
  demand_proyeksi.csv   kapasitas.csv       gap_analysis.csv
  rekomendasi.csv       scgi.csv            clusters.csv
  mape_detail.csv       elbow_data.csv      evaluation.csv
```

### Spatial & Accessibility Analysis (Notebook 06) — PIC: Ni'mah

Notebook `06_spatial_and_accessibility_analysis.ipynb` mengintegrasikan:

| Komponen | Teknologi | Output |
|---|---|---|
| Geocoding Enrichment | **Geopy** (Nominatim) | `notebooks/data/surabaya_kecamatan_coords.csv` — koordinat centroid 31 kecamatan |
| Batas Wilayah Kecamatan | **GeoPandas** + Voronoi | `notebooks/data/surabaya_kecamatan_voronoi.geojson` — polygon 31 kecamatan |
| Choropleth Map SCGI | **Folium** + `scgi.csv` | Peta interaktif gradasi warna berdasarkan SCGI score |
| Choropleth Map Cluster | **Folium** + `clusters.csv` | Peta interaktif warna per prioritas K-Means |
| Accessibility POC | **OSRM API** | Rute berkendara + jarak/durasi dari kecamatan Kritis → Aman |

**Metode proyeksi (cohort survival):** penduduk berumur `a` pada 2025 akan berumur
`a+k` pada tahun `2025+k`. Demand SD tahun `Y` = penduduk yang berumur 7–12 pada
tahun `Y` = penduduk umur `(7-k)…(12-k)` pada snapshot 2025. Asumsi: tanpa
migrasi/mortalitas (konstan).

**Definisi kapasitas (penting):** dataset akreditasi (`kapasitas_pagu_siswa`)
belum mencakup seluruh sekolah sehingga pagu undercount. Maka kapasitas
didefinisikan sebagai:
```
kapasitas = max(total_pagu, murid_aktual)
```
`murid_aktual` = jumlah siswa yang nyata dilayani sekolah di kecamatan tsb
(snapshot terbaru dari dataset rasio murid-guru). Logika: kapasitas riil
minimal sebesar jumlah siswa yang saat ini sudah tertampung. Ini menghapus
artefak utilisasi yang menggelembung akibat pagu tak lengkap.

**Logika rekomendasi (target 2030):**
```
defisit = max(0, demand_total - kapasitas)
ruang_kelas_baru = ceil(defisit / 32)            # 32 = standar siswa/rombel
rekomendasi = CUKUP  bila defisit <= 0
            = USB    bila defisit >= rata_kapasitas_sekolah   (butuh sekolah baru)
            = RKB    selain itu                                (cukup tambah kelas)
skor_prioritas = defisit  → ranking menurun
```

## 5. Delta Lake & Time Travel (`04_time_travel.py`)
- Semua tabel lakehouse = Delta (ACID, versioning, schema evolution).
- Demo: UPDATE/overwrite menghasilkan versi baru → baca versi lama via
  `option("versionAsOf", v)` → bandingkan → tampilkan `DeltaTable.history()`.

## 6. Data Quality Report (`06_data_quality.py`)
- Output: tabel `gold_data_quality_report` + `medallion/DATA_QUALITY_REPORT.md`.
- Dimensi: reconciliation (vs jumlah CKAN), completeness (null), consistency
  (kecamatan/periode), uniqueness (duplikat grain), validity (tipe/negatif),
  joinability (kecocokan kecamatan penduduk↔sekolah).
- Hasil terakhir: **43 PASS / 4 WARN / 0 FAIL**.

## 7. Backend API (`web/BE/main.py`, FastAPI :8000)
Membaca Delta dari Gold via WebHDFS — **hanya file aktif** dari `_delta_log`
(menghindari salah hitung akibat file lama pasca overwrite/time-travel).

| Endpoint | Fungsi |
|---|---|
| `GET /tables` | Daftar tabel Gold |
| `GET /tables/{name}?limit&offset` | Isi tabel |
| `GET /analysis/rekomendasi?top&filter_rekom` | Ranking USB/RKB |
| `GET /analysis/gap/{kecamatan}` | Tren gap per tahun |
| `GET /analysis/proyeksi/{kecamatan}` | Proyeksi demand per tahun |
| `GET /analysis/scgi?top&category` | SCGI per kecamatan (filter: KRITIS/TINGGI/SEDANG/RENDAH/AMAN) |
| `GET /analysis/cluster?priority` | K-Means cluster + ringkasan per prioritas |
| `GET /analysis/evaluation` | Metrik evaluasi: MAPE, Silhouette, Davies-Bouldin |
| `GET /health` | Status koneksi HDFS |

## 8. Cara Menjalankan (runbook)

```bash
# 0. Setup venv host (sekali) untuk producer/consumer
python3 -m venv .venv-host
./.venv-host/bin/pip install kafka-python requests

# 1. Naikkan infrastruktur
docker compose up -d namenode datanode resourcemanager nodemanager kafka

# 2. Buat direktori HDFS (sekali)
bash store/_hadoop_setup.sh        # atau buat manual /data/opendata-sby/* & /lakehouse/*

# 3. Buat topik Kafka (sekali)
bash scripts/01-setup-kafka.sh

# 4. Ingestion (host)
./.venv-host/bin/python producer_ingest/producer_open_data.py   # CKAN -> Kafka (Ctrl-C setelah 1 siklus)
./.venv-host/bin/python producer_ingest/consumer_to_hdfs.py     # Kafka -> HDFS (Ctrl-C setelah file masuk)

# 5. Medallion — Gold Layer & Analysis 2 (container spark-medallion)
docker compose up -d spark

## 5a. Install dependencies Analysis 2 ke container (wajib, sekali)
docker exec spark-medallion pip install numpy pandas scikit-learn -q

## 5b. Jalankan urut — tunggu tiap script selesai sebelum lanjut
docker exec -e HADOOP_USER_NAME=hadoop spark-medallion spark-submit /app/01_bronze.py
docker exec -e HADOOP_USER_NAME=hadoop spark-medallion spark-submit /app/02_silver.py
docker exec -e HADOOP_USER_NAME=hadoop spark-medallion spark-submit /app/03_gold.py
docker exec -e HADOOP_USER_NAME=hadoop spark-medallion spark-submit /app/04_time_travel.py
docker exec -e HADOOP_USER_NAME=hadoop spark-medallion spark-submit /app/06_data_quality.py
docker exec -e HADOOP_USER_NAME=hadoop spark-medallion spark-submit /app/08_analysis2.py
# (opsional) demo pipeline kecil max-value:
# docker exec -e HADOOP_USER_NAME=hadoop spark-medallion spark-submit /app/05_spark_max_value.py

# Setelah selesai: CSV tersedia di medallion/exports/ + 3 tabel Gold baru terbentuk

# 6. Backend API v2.1 (Spark -> Backend)
docker compose up -d --build backend

# 7. Verifikasi semua endpoint
curl http://localhost:8000/health
curl "http://localhost:8000/analysis/scgi?top=5"
curl "http://localhost:8000/analysis/cluster?priority=KRITIS"
curl http://localhost:8000/analysis/evaluation
curl "http://localhost:8000/analysis/rekomendasi?top=10"
curl http://localhost:8000/analysis/gap/TAMBAKSARI
curl http://localhost:8000/analysis/proyeksi/SAWAHAN
# Swagger UI interaktif: http://localhost:8000/docs

# 8. Analytics Notebooks (untuk eksplorasi & presentasi)
#    Pastikan .venv sudah ada (pip install -r notebooks/requirements.txt)
.venv/bin/jupyter notebook notebooks/
# Jalankan urut: 01 → 02 → 03 → 04 → 05 → 06
# Pada notebook 06: Kernel → Restart → Run All Cells
#   (Cell pertama otomatis install geopandas, geopy, folium jika belum ada)
```

**Web UI:** HDFS http://localhost:9870 · YARN http://localhost:8088 · API docs http://localhost:8000/docs

## 9. Catatan & Asumsi
- `HADOOP_USER_NAME=hadoop` wajib di container Spark (HDFS `/lakehouse` milik user `hadoop`).
- `KAFKA_ADVERTISED_LISTENERS=localhost:9092` agar producer/consumer di host bisa connect.
- Kapasitas memakai `max(pagu, murid_aktual)` untuk menghindari undercount pagu
  (lihat bagian "Definisi kapasitas"). Sisa utilisasi >100% bersifat wajar:
  demand berbasis domisili penduduk sedangkan kapasitas berbasis lokasi sekolah,
  sehingga ada mobilitas siswa antar-kecamatan. Untuk perencanaan USB/RKB,
  membandingkan anak usia sekolah dengan daya tampung di kecamatan domisili
  tetap merupakan metrik yang relevan.
- `08_analysis2.py` wajib dijalankan **setelah** `03_gold.py` karena membaca Gold tables yang
  dihasilkan oleh Gold layer (gold_demand_proyeksi, gold_kapasitas_kecamatan, gold_gap_analysis).
- Batas wilayah kecamatan pada notebook 06 menggunakan **Voronoi Diagram** (offline, bukan
  batas administratif resmi). Akurasi batas cukup untuk tujuan visualisasi DSS.
- OSRM routing POC menggunakan `router.project-osrm.org` (public API). Jika tidak ada
  koneksi internet, visualisasi fallback ke garis lurus antar centroid.

## 10. Struktur File Penting (PIC: Ni'mah — Analysis 2)

```
bantai_bantai_big_data/
├── medallion/
│   ├── 03_gold.py                          # Gold Layer (Analysis 1 + shared)
│   ├── 08_analysis2.py                     # DSS Layer — SCGI, K-Means, Evaluasi
│   └── exports/                            # CSV output untuk notebooks
│       ├── scgi.csv, clusters.csv
│       ├── demand_proyeksi.csv, gap_analysis.csv
│       ├── rekomendasi.csv, kapasitas.csv
│       ├── evaluation.csv, mape_detail.csv
│       └── elbow_data.csv
├── notebooks/
│   ├── 01forecasting_analysis.ipynb        # Age-Cohort Shift Projection
│   ├── 02capacity_analysis.ipynb           # Capacity Audit & Gap
│   ├── 03scgi_analysis.ipynb               # SCGI Visualization
│   ├── 04clustering_analysis.ipynb         # K-Means Clustering
│   ├── 05evaluation.ipynb                  # MAPE + Silhouette + DB
│   ├── 06_spatial_and_accessibility_analysis.ipynb  # GeoPandas, Geopy, OSRM
│   ├── requirements.txt
│   └── data/
│       ├── surabaya_kecamatan_coords.csv   # Koordinat 31 kecamatan (Geopy)
│       └── surabaya_kecamatan_voronoi.geojson  # Batas wilayah (GeoPandas)
└── web/BE/
    └── main.py                             # FastAPI v2.1 — termasuk endpoint Analysis 2
```
