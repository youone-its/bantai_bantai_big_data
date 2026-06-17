# Scripts - Big Data Workspace Automation

Folder ini berisi bash scripts untuk mengotomasi setup dan pengecekan seluruh pipeline Big Data.

## 📋 Daftar Scripts

| Script | Fungsi |
|--------|--------|
| `01-setup-kafka.sh` | Setup Kafka topics untuk data ingestion |
| `02-check-kafka.sh` | Cek koneksi Kafka dan isi topics |
| `03-setup-hadoop.sh` | Setup HDFS directories |
| `04-check-hadoop.sh` | Cek isi HDFS per layer |
| `05-setup-medallion.sh` | Jalankan pipeline Bronze → Silver → Gold |
| `06-check-medallion.sh` | Cek isi Bronze, Silver, Gold |
| `07-run-all.sh` | Jalankan seluruh pipeline dari awal |

## 🚀 Quick Start

### Jalankan Semua (Full Pipeline)
```bash
bash scripts/07-run-all.sh
```

Script ini akan:
1. Start semua Docker containers
2. Setup Kafka topics
3. Setup HDFS directories
4. Run Producer (API → Kafka)
5. Run Consumer (Kafka → HDFS)
6. Run Medallion (Bronze → Silver → Gold)
7. Start Backend API

### Jalankan Per Step

```bash
# 1. Setup Kafka
bash scripts/01-setup-kafka.sh

# 2. Cek Kafka
bash scripts/02-check-kafka.sh

# 3. Setup Hadoop
bash scripts/03-setup-hadoop.sh

# 4. Cek Hadoop
bash scripts/04-check-hadoop.sh

# 5. Setup Medallion
bash scripts/05-setup-medallion.sh

# 6. Cek Medallion
bash scripts/06-check-medallion.sh
```

## 📊 Data Flow

```
┌─────────────┐     ┌─────────┐     ┌─────────┐     ┌──────────┐
│ CKAN API    │────▶│ Kafka   │────▶│ HDFS    │────▶│ Medallion│
│ Surabaya    │     │ Topics  │     │ /data/  │     │ Bronze   │
└─────────────┘     └─────────┘     └─────────┘     └────┬─────┘
                                                          │
                     ┌──────────┐     ┌──────────┐        │
                     │ Backend  │◀────│ Gold     │◀───────┤
                     │ API      │     │ Layer    │        │
                     └────┬─────┘     └──────────┘        │
                          │                               │
                          ▼                               │
                     ┌──────────┐                         │
                     │ Frontend │                         │
                     │ / Browser│                         │
                     └──────────┘                         │
                                                          │
┌─────────────────────────────────────────────────────────┘
│
│  Bronze → Silver → Gold
│  (Raw)    (Clean)   (Analytics)
└──────────────────────────────────────────────────────────
```

## 🔗 Access Points

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| HDFS UI | http://localhost:9870 |
| YARN UI | http://localhost:8088 |

## 🛠️ Troubleshooting

### Kafka tidak bisa connect
```bash
# Restart Kafka
docker-compose restart kafka

# Setup ulang topics
bash scripts/01-setup-kafka.sh
```

### HDFS tidak accessible
```bash
# Restart Hadoop
docker-compose restart namenode datanode

# Setup ulang directories
bash scripts/03-setup-hadoop.sh
```

### Medallion gagal
```bash
# Cek Spark container
docker logs spark-medallion

# Jalankan ulang
bash scripts/05-setup-medallion.sh
```

### Reset semua
```bash
# Stop semua containers
docker-compose down

# Hapus volumes (opsional, akan reset semua data)
docker-compose down -v

# Jalankan ulang dari awal
bash scripts/07-run-all.sh
```

## 📝 Notes

- Scripts ini harus dijalankan dari root directory project
- Pastikan Docker dan Docker Compose sudah terinstall
- Producer dan Consumer dijalankan di host (bukan di container)
- Medallion dijalankan di dalam Spark container
- Backend API akan otomatis start setelah semua pipeline selesai
