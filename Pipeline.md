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
 HDFS /data/opendata-sby/*  (JSON mentah) container: hadoop-namenode/datanode
        │  Spark + Delta (medallion/)
        ▼
 LAKEHOUSE (Delta Lake) — container: spark-medallion
   ├── /lakehouse/bronze   raw + metadata
   ├── /lakehouse/silver   bersih, ternormalisasi, dedup
   └── /lakehouse/gold     data mart analitik
        │  WebHDFS + pyarrow (baca file aktif dari _delta_log)
        ▼
 Backend FastAPI (:8000)                 container: etsbd-backend
        ▼
 Frontend                                container: etsbd-frontend (web/FE)
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

# 5. Medallion (container spark-medallion)
docker compose up -d spark
for s in 01_bronze 02_silver 03_gold 04_time_travel 06_data_quality; do
  docker exec -e HADOOP_USER_NAME=hadoop spark-medallion spark-submit /app/$s.py
done

# 6. Backend
docker compose up -d --build backend
curl http://localhost:8000/analysis/rekomendasi?top=5
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
